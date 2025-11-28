import os
import torch
import numpy as np
from tqdm.auto import tqdm
from typing import Dict, List, Optional, Union, Any, Tuple
from transformers import (
    get_linear_schedule_with_warmup,
    get_cosine_schedule_with_warmup,
    get_constant_schedule_with_warmup
)
from accelerate import Accelerator, DistributedDataParallelKwargs
from accelerate.utils import DistributedType, DummyOptim
from copy import deepcopy
import torch.nn.functional as F
from accelerate.utils.fsdp_utils import fsdp2_prepare_model
import wandb

def selective_log_softmax(logits, index) -> torch.Tensor:
    """
    A memory-efficient implementation of the common `log_softmax -> gather` operation.

    This function is equivalent to the following naive implementation:
    ```python
    logps = torch.gather(logits.log_softmax(-1), dim=-1, index=index.unsqueeze(-1)).squeeze(-1)
    ```

    Args:
        logits (`torch.Tensor`):
            Logits tensor of shape `(..., num_classes)`.
        index (`torch.Tensor`):
            Index tensor of shape `(...)`, specifying the positions to gather from the log-softmax output.

    Returns:
        `torch.Tensor`:
            Gathered log probabilities with the same shape as `index`.
    """
    if logits.dtype in [torch.float32, torch.float64]:
        selected_logits = torch.gather(logits, dim=-1, index=index.unsqueeze(-1)).squeeze(-1)
        # loop to reduce peak mem consumption
        logsumexp_values = torch.stack([torch.logsumexp(lg, dim=-1) for lg in logits])
        per_token_logps = selected_logits - logsumexp_values  # log_softmax(x_i) = x_i - logsumexp(x)
    else:
        # logsumexp approach is unstable with bfloat16, fall back to slightly less efficient approach
        per_token_logps = []
        for row_logits, row_labels in zip(logits, index):  # loop to reduce peak mem consumption
            row_logps = F.log_softmax(row_logits, dim=-1)
            row_per_token_logps = row_logps.gather(dim=-1, index=row_labels.unsqueeze(-1)).squeeze(-1)
            per_token_logps.append(row_per_token_logps)
        per_token_logps = torch.stack(per_token_logps)
    return per_token_logps

class SFT:
    def __init__(
        self,
        model: torch.nn.Module,
        lr: float = 2e-5,
        weight_decay: float = 0.01,
        schedule_type: str = "cosine_with_warmup",
        lr_final: float = 1e-6,
        max_steps: int = 1000,
        warmup_steps: int = 100,
        compile: bool = False,
        checkpoint_path: Optional[str] = None,
        optimizer_type: str = "AdamW",
        gradient_checkpointing: bool = True,
        max_grad_norm: float = 1.0,
        gradient_accumulation_steps: int = 1,
        custom_loss: Optional[callable] = None,
        ref_kl: bool = False,
        ref_kl_weight: float = 0.01,
        scale_scheduler_by_porc_count: bool = True
    ):
        """
        Initialize the SFT trainer for transformer models.
        """
        self.optimizer_type = optimizer_type
        self.gradient_checkpointing = gradient_checkpointing
        self.max_grad_norm = max_grad_norm
        self.custom_loss = custom_loss
        self.ref_kl = ref_kl
        self.ref_kl_weight = ref_kl_weight

        # Initialize accelerator with gradient accumulation config
        self.accelerator = Accelerator(
            gradient_accumulation_steps=gradient_accumulation_steps,
            kwargs_handlers=[DistributedDataParallelKwargs(find_unused_parameters=True)]
        )
        
        if scale_scheduler_by_porc_count:
            np = self.accelerator.state.num_processes
            max_steps = (max_steps + np - 1) // np
        
        # Setup model
        self.model = model
        
        # if ref_kl is True, make a copy of the model for reference KL loss
        if self.ref_kl:
            print("Using reference KL loss, creating a copy of the model for reference.")
            self.ref_model = deepcopy(model)
            self.ref_model.eval()  # Ensure reference model is in eval mode
            self.ref_model.requires_grad_(False)  # Disable gradients for reference model
            self.ref_accelerator = Accelerator(
                kwargs_handlers=[DistributedDataParallelKwargs(find_unused_parameters=True)]
            )
            
            if self.ref_accelerator.distributed_type == DistributedType.DEEPSPEED:
                if self.ref_accelerator.deepspeed_plugin.deepspeed_config["zero_optimization"]["stage"] != 3:
                    self.ref_accelerator.deepspeed_plugin.deepspeed_config["zero_optimization"]["stage"] = 0
        
        # Enable gradient checkpointing if requested
        if self.gradient_checkpointing and hasattr(self.model, "gradient_checkpointing_enable"):
            self.model.gradient_checkpointing_enable()
        
        # Apply torch.compile if requested (requires PyTorch 2.0+)
        if hasattr(torch, 'compile') and compile:
            self.model = torch.compile(self.model)
            if self.ref_kl:
                self.ref_model = torch.compile(self.ref_model)
        
        # Set up optimizer
        self.lr = lr
        self.weight_decay = weight_decay
        self.setup_optimizer()
        
        # Set up learning rate scheduler
        self.schedule_type = schedule_type
        self.lr_final = lr_final
        self.max_steps = max_steps
        self.warmup_steps = warmup_steps
        self.setup_scheduler()
        
        self.current_epoch = 0
        self.global_step = 0
        
        # Load checkpoint if provided
        if checkpoint_path:
            self.load_checkpoint(checkpoint_path)
        
        # Clear CUDA cache
        torch.cuda.empty_cache()
    
    def setup_optimizer(self):
        """Set up the optimizer for training."""
        param_list = [p for p in self.model.parameters() if p.requires_grad]
        
        if self.optimizer_type == "Adam":
            self.optimizer = torch.optim.Adam(param_list, lr=self.lr, weight_decay=self.weight_decay)
        elif self.optimizer_type == "AdamW":
            self.optimizer = torch.optim.AdamW(param_list, lr=self.lr, weight_decay=self.weight_decay)
        elif self.optimizer_type == "SGD":
            self.optimizer = torch.optim.SGD(param_list, lr=self.lr, weight_decay=self.weight_decay)
        elif self.optimizer_type == "Lion":
            try:
                import lion_pytorch
                self.optimizer = lion_pytorch.Lion(param_list, lr=self.lr, weight_decay=self.weight_decay)
            except ImportError:
                print("Lion optimizer not available. Falling back to AdamW.")
                self.optimizer = torch.optim.AdamW(param_list, lr=self.lr, weight_decay=self.weight_decay)
        else:
            # Default to AdamW
            self.optimizer = torch.optim.AdamW(param_list, lr=self.lr, weight_decay=self.weight_decay)
    
    def setup_scheduler(self):
        """Set up the learning rate scheduler."""
        if self.schedule_type == "linear_with_warmup":
            self.scheduler = get_linear_schedule_with_warmup(
                self.optimizer,
                num_warmup_steps=self.warmup_steps,
                num_training_steps=self.max_steps
            )
        elif self.schedule_type == "cosine_with_warmup":
            self.scheduler = get_cosine_schedule_with_warmup(
                self.optimizer,
                num_warmup_steps=self.warmup_steps,
                num_training_steps=self.max_steps,
                num_cycles=0.5
            )
        elif self.schedule_type == "constant_with_warmup":
            self.scheduler = get_constant_schedule_with_warmup(
                self.optimizer,
                num_warmup_steps=self.warmup_steps
            )
        else:
            self.scheduler = None
    
    def save_checkpoint(self, path):
        """Save a checkpoint."""
        
        if self.accelerator.distributed_type == DistributedType.DEEPSPEED and self.accelerator.deepspeed_config["zero_optimization"]["stage"] == 3:
            # obtain state dict from DeepSpeed engine
            model_state_dict = self.accelerator.get_state_dict(self.model)
            checkpoint = {
                    'model_state_dict': model_state_dict,
                    'current_epoch': self.current_epoch,
                    'global_step': self.global_step
                }
            self.accelerator.wait_for_everyone()
            if self.accelerator.is_main_process:
                self.accelerator.save(checkpoint, path)
                
            # release memory
            del model_state_dict
            torch.cuda.empty_cache()
        elif self.accelerator.distributed_type == DistributedType.FSDP:
            # Save FSDP model state dict
            model_state_dict = self.accelerator.get_state_dict(self.model)
            checkpoint = {
                'model_state_dict': model_state_dict,
                'current_epoch': self.current_epoch,
                'global_step': self.global_step
            }
            self.accelerator.wait_for_everyone()
            if self.accelerator.is_main_process:
                # Save the checkpoint
                self.accelerator.save(checkpoint, path)
                
        elif self.accelerator.is_main_process:
            # Get unwrapped model
            unwrapped_model = self.accelerator.unwrap_model(self.model)
            
            checkpoint = {
                'model_state_dict': unwrapped_model.state_dict(),
                'current_epoch': self.current_epoch,
                'global_step': self.global_step
            }
            
            # Use accelerator to save the checkpoint
            self.accelerator.save(checkpoint, path)
    
    def load_checkpoint(self, path):
        """Load a checkpoint."""
        checkpoint = self.accelerator.load(path)
        
        # Load model state dict
        if hasattr(self.model, "load_state_dict"):
            try:
                self.model.load_state_dict(checkpoint['model_state_dict'], strict=False)
            except:
                print("Model state dict not found in checkpoint or incompatible.")
        
        self.current_epoch = checkpoint.get('current_epoch', 0)
        self.global_step = checkpoint.get('global_step', 0)
    
    def reset_optimizer(self):
        """Reset the optimizer and scheduler."""
        self.setup_optimizer()
        self.setup_scheduler()
        
        # Prepare model, optimizer and scheduler with accelerator
        self.model, self.optimizer, self.scheduler = self.accelerator.prepare(
            self.model, self.optimizer, self.scheduler
        )
    
    def train(self, dataset, train_indices=None, batch_size=8, epochs=3, continue_loop=True, verbose=True, 
              checkpoint_steps=1000, checkpoint_dir='checkpoints', 
              eval_dataset=None, eval_indices=None, eval_batch_size=None, eval_steps=None, max_steps=None,
              save_best_only=False, early_stopping_patience=None, dataloader_num_workers=4, remove_old_checkpoints=True,
              n_total_checkpoints_to_keep=3):
        """
        Train the model using Accelerate.
        
        Args:
            dataset: The full dataset to train on
            train_indices: Optional specific indices to use from dataset (if None, uses all)
            batch_size: Batch size
            epochs: Number of epochs to train
            continue_loop: Whether to continue from the last epoch or reset
            verbose: Whether to show progress during training
            checkpoint_steps: Save checkpoint every N steps
            checkpoint_dir: Directory to save checkpoints
            eval_dataset: Dataset for evaluation (if None, no evaluation is performed)
            eval_indices: Optional specific indices for evaluation dataset
            eval_batch_size: Batch size for evaluation (defaults to train batch_size if None)
            eval_steps: How often to run evaluation (in steps)
            max_steps: Maximum number of steps to train for (overrides epochs if provided)
            save_best_only: Only save checkpoints when evaluation loss improves
            early_stopping_patience: Number of evaluations with no improvement after which to stop
            dataloader_num_workers: Number of workers for data loading
        """
        if not continue_loop:
            self.model.train()
            self.current_epoch = 0
            self.global_step = 0
            self.reset_optimizer()
        
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Set up indices for training
        if train_indices is None:
            train_indices = list(range(len(dataset)))
        
        # Setup dataloaders
        collate_fn = getattr(dataset, '_collate_fn', None)
        train_sampler = torch.utils.data.SubsetRandomSampler(train_indices)
        
        dataloader = torch.utils.data.DataLoader(
            dataset,
            batch_size=batch_size,
            sampler=train_sampler,
            num_workers=dataloader_num_workers,
            collate_fn=collate_fn,
            pin_memory=False,
        )
        
        # Set up evaluation dataloader if needed
        eval_dataloader = None
        if eval_dataset is not None and eval_steps is not None:
            if eval_indices is None and eval_dataset is dataset:
                # If using same dataset for eval, use different indices
                eval_indices = train_indices  # For simplicity, use same indices but could use a validation split
            elif eval_indices is None:
                eval_indices = list(range(len(eval_dataset)))
            
            eval_sampler = torch.utils.data.SubsetRandomSampler(eval_indices)
            eval_batch_size = eval_batch_size or batch_size
            
            eval_dataloader = torch.utils.data.DataLoader(
                eval_dataset,
                batch_size=eval_batch_size,
                sampler=eval_sampler,
                num_workers=dataloader_num_workers,
                collate_fn=getattr(eval_dataset, '_collate_fn', None),
                pin_memory=False,
            )
        
        # Prepare model, optimizer, scheduler, and dataloaders with accelerator
        self.model, self.optimizer, self.scheduler, dataloader = self.accelerator.prepare(
            self.model, self.optimizer, self.scheduler, dataloader
        )
        if self.ref_kl:
            if self.accelerator.distributed_type == DistributedType.FSDP:
                # self.ref_model = self.prepare_fsdp(self.ref_model, self.ref_accelerator)
                self.ref_model = self.accelerator.prepare_model(self.ref_model)
                self.ref_model.eval()
                self.ref_model.requires_grad_(False)
            else:
                self.ref_model = self.ref_accelerator.prepare(self.ref_model)
                self.ref_model.eval()
                self.ref_model.requires_grad_(False)
        
        if eval_dataloader is not None:
            eval_dataloader = self.accelerator.prepare(eval_dataloader)
        
        # Store initial loss value for averaging
        running_loss = 0.0
        best_eval_loss = float('inf')
        no_improvement_count = 0
        
        # Set up step tracking
        epoch = self.current_epoch
        total_steps_done = self.global_step
        steps_per_epoch = len(dataloader)
        
        if verbose and self.accelerator.is_main_process:
            print(f"Training with {len(train_indices)} samples in {steps_per_epoch} steps per epoch")
            if max_steps:
                print(f"Training for max {max_steps} steps (overrides {epochs} epochs setting)")
            else:
                print(f"Training for {epochs} epochs ({epochs * steps_per_epoch} steps)")

        loss_fct = torch.nn.CrossEntropyLoss()
        
        self.accelerator.register_for_checkpointing(self.scheduler)
                
        while (max_steps is None and epoch < self.current_epoch + epochs) or \
              (max_steps is not None and total_steps_done < max_steps):
            
            if verbose and self.accelerator.is_main_process:
                print(f"Epoch {epoch + 1}")
                if max_steps:
                    print(f"Step {total_steps_done}/{max_steps}")
                prog = tqdm(dataloader, total=len(dataloader), disable=not self.accelerator.is_main_process)
            else:
                prog = dataloader
            
            accumulated_loss = 0.0
            num_batches = 0
            
            self.model.train()
            for step, batch in enumerate(prog):
                # Check if we've reached max_steps
                if max_steps is not None and total_steps_done >= max_steps:
                    break

                with self.accelerator.accumulate(self.model):
                    # Forward pass
                    if self.custom_loss is not None:
                        # Use custom loss function if provided
                        loss = self.custom_loss(self.model, **batch)
                    else:
                        labels = batch.pop('labels', None)
                        
                        outputs = self.model(**batch)
                        # loss = outputs.loss
                        shift_logits = outputs.logits[..., :-1, :].contiguous()
                        shift_labels = labels[..., 1:].contiguous()
                        
                        # Flatten the tokens
                        shift_labels = shift_labels.view(-1)
                        B = shift_labels.size(0)
                        shift_logits = shift_logits.view(B, -1)
                        loss = loss_fct(shift_logits, shift_labels)
                    
                    # If using reference KL loss, compute it
                    if self.ref_kl:
                        with torch.no_grad():
                            ref_outputs = self.ref_model(**batch)
                            ref_logits_shift = ref_outputs.logits.detach()[..., :-1, :].contiguous()
                        current_logits_shift = outputs.logits[..., :-1, :].contiguous()
                        log_probs_current = F.log_softmax(current_logits_shift, dim=-1)
                        probs_initial = F.log_softmax(ref_logits_shift, dim=-1)
                        mask = (batch['labels'][..., 1:].contiguous() != -100)
                        log_probs_current = log_probs_current[mask]
                        probs_initial = probs_initial[mask]
                        
                        kl_div = F.kl_div(log_probs_current, probs_initial, reduction='batchmean', log_target=True)
                        full_loss = loss + self.ref_kl_weight * kl_div
                        
                        # Backward pass handled by accelerator
                        self.accelerator.backward(full_loss)
                    
                    else:
                        # Backward pass handled by accelerator
                        self.accelerator.backward(loss)
                        
                    # === ADD GRADIENT MONITORING HERE ===
                    if self.accelerator.sync_gradients:
                        # Calculate gradient norm
                        total_norm = 0.0
                        for p in self.model.parameters():
                            if p.grad is not None:
                                param_norm = p.grad.data.norm(2)
                                total_norm += param_norm.item() ** 2
                        total_norm = total_norm ** 0.5
                        
                        # Log it
                        if verbose and self.accelerator.is_main_process:
                            if total_norm > 100:  # Warning threshold
                                print(f"\n⚠️ WARNING: Large gradient norm at step {total_steps_done}: {total_norm:.2f}")
                            
                            # Can also add to progress bar
                            # prog.set_postfix({..., 'grad_norm': f"{total_norm:.2f}"})
                    # === END GRADIENT MONITORING ===
                    
                    # Accumulate loss for reporting
                    accumulated_loss += loss.item()
                    num_batches += 1
                    running_loss += loss.item()
                    
                    # Clip gradients and optimizer step handled by accelerator
                    if self.accelerator.sync_gradients:
                        if self.max_grad_norm > 0:
                            self.accelerator.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)
                        
                        # Step optimizer
                        self.optimizer.step()
                        self.optimizer.zero_grad()
                        
                        # Step scheduler if we're using it
                        if self.scheduler is not None:
                            self.scheduler.step()
                        
                        # Increment global step counter
                        total_steps_done += 1
                        self.global_step = total_steps_done
                
                # Progress is synced with optimizer steps, which happens every gradient_accumulation_steps
                if self.accelerator.sync_gradients:
                    # Step-based checkpoint saving
                    should_save = (total_steps_done % checkpoint_steps == 0)
                    
                    # Evaluation
                    current_eval_loss = None
                    if eval_dataloader is not None and eval_steps is not None and total_steps_done % eval_steps == 0:
                        current_eval_loss = self.evaluate(eval_dataloader)
                        
                        if verbose and self.accelerator.is_main_process:
                            print(f"\nStep {total_steps_done}, Eval Loss: {current_eval_loss:.5f}")
                            
                            # Check for improvement
                            if current_eval_loss < best_eval_loss:
                                improvement = best_eval_loss - current_eval_loss
                                best_eval_loss = current_eval_loss
                                no_improvement_count = 0
                                print(f"Best eval loss improved by {improvement:.5f}. New best: {best_eval_loss:.5f}")
                                
                                # Save best model if requested
                                if save_best_only:
                                    best_model_path = os.path.join(checkpoint_dir, 'best_model.pt')
                                    self.save_checkpoint(best_model_path)
                                    print(f"Saved best model to {best_model_path}")
                            else:
                                no_improvement_count += 1
                                print(f"No improvement in eval loss for {no_improvement_count} evaluations.")
                        
                        # Early stopping check
                        if  early_stopping_patience and no_improvement_count >= early_stopping_patience:
                            if self.accelerator.is_main_process and verbose:
                                print(f"Early stopping triggered after {no_improvement_count} evaluations without improvement")

                            # Save final state before early stopping
                            final_path = os.path.join(checkpoint_dir, 'final_model_early_stopped.pt')
                            self.save_checkpoint(final_path)
                            
                            # Signal all processes to stop
                            self.accelerator.end_training()
                            return running_loss / (num_batches * epoch + step + 1)
                            
                        # Return to training mode
                        self.model.train()
                    
                    # Save checkpoint based on steps - only main process saves
                    if should_save and (not save_best_only or current_eval_loss is None):
                        checkpoint_path = os.path.join(checkpoint_dir, f'checkpoint_step_{total_steps_done}.pt')
                        self.save_checkpoint(checkpoint_path)
                        
                        if verbose and self.accelerator.is_main_process:
                            print(f"\nSaved checkpoint at step {total_steps_done} to {checkpoint_path}")
                            
                        # Optional: Remove older checkpoints to save disk space
                        if remove_old_checkpoints and self.accelerator.is_main_process:
                            old_checkpoint = os.path.join(checkpoint_dir, f'checkpoint_step_{total_steps_done - (n_total_checkpoints_to_keep * checkpoint_steps)}.pt')
                            if os.path.exists(old_checkpoint):
                                os.remove(old_checkpoint)
                
                # Update progress bar
                if verbose and self.accelerator.is_main_process:
                    current_lr = self.optimizer.param_groups[0]['lr']
                    avg_loss = accumulated_loss / num_batches
                    prog.set_postfix({
                        'epoch loss': f"{avg_loss:.5f}",
                        'loss': f"{loss.item():.5f}",
                        'lr': f"{current_lr:.7f}",
                        'step': total_steps_done,
                        'kl loss': f"{kl_div.item():.5f}" if self.ref_kl else 'N/A'
                    })
            
            # Increment epoch counter
            epoch += 1
            self.current_epoch = epoch
            
            # Print epoch summary
            if verbose and self.accelerator.is_main_process:
                print(f"Epoch {epoch} completed. Average loss: {accumulated_loss / num_batches:.5f}")
            
            # save epoch checkpoint
            epoch_checkpoint_path = os.path.join(checkpoint_dir, f'checkpoint_epoch_{epoch}.pt')
            self.save_checkpoint(epoch_checkpoint_path)
        
        # Save final model
        final_path = os.path.join(checkpoint_dir, 'final_model.pt')
        self.save_checkpoint(final_path)
        
        if verbose and self.accelerator.is_main_process:
            print(f"Training completed. Final model saved to {final_path}")
        
        # Make sure all processes reach here
        self.accelerator.wait_for_everyone()
        
        return running_loss / (num_batches * epoch)
    
    def evaluate(self, eval_dataloader):
        """
        Evaluate the model on the provided dataloader.
        
        Args:
            eval_dataloader: DataLoader for evaluation
            
        Returns:
            Average loss on the evaluation dataset
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in eval_dataloader:
                # Forward pass
                outputs = self.model(**batch)
                loss = outputs.loss
                
                # Gather loss from all processes
                loss = self.accelerator.gather(loss).mean().item()
                
                total_loss += loss
                num_batches += 1
        
        # Compute average loss
        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        
        # Make sure all processes have the same average loss
        avg_loss_tensor = torch.tensor([avg_loss], device=self.accelerator.device)
        self.accelerator.broadcast(avg_loss_tensor, src=0)
        
        return avg_loss_tensor.item()

class SFTSyncedGrad:
    def __init__(
        self,
        model: torch.nn.Module,
        lr: float = 2e-5,
        weight_decay: float = 0.01,
        schedule_type: str = "cosine_with_warmup",
        lr_final: float = 1e-6,
        max_steps: int = 1000,
        warmup_steps: int = 100,
        compile: bool = False,
        checkpoint_path: Optional[str] = None,
        optimizer_type: str = "AdamW",
        gradient_checkpointing: bool = True,
        max_grad_norm: float = 1.0,
        gradient_accumulation_steps: int = 1,
        custom_loss: Optional[callable] = None,
        ref_kl: bool = False,
        ref_kl_weight: float = 0.01,
        scale_scheduler_by_porc_count: bool = True,
        log_to_wandb: bool = False,
        wandb_project: str = "SFT-CADCoder",
        wandb_run_name: str = "SFT_Experiment",
        wandb_id: Optional[str] = None
    ):
        """
        Initialize the SFT trainer for transformer models.
        """
        self.optimizer_type = optimizer_type
        self.gradient_checkpointing = gradient_checkpointing
        self.max_grad_norm = max_grad_norm
        self.custom_loss = custom_loss
        self.ref_kl = ref_kl
        self.ref_kl_weight = ref_kl_weight
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.log_to_wandb = log_to_wandb
        self.wandb_project = wandb_project
        self.wandb_run_name = wandb_run_name
        self.wandb_id = wandb_id

        # Initialize accelerator with gradient accumulation config
        # Note: When using DeepSpeed, the DeepSpeed config file controls gradient accumulation,
        # but we still pass the parameter for non-DeepSpeed cases
        self.accelerator = Accelerator(
            gradient_accumulation_steps=gradient_accumulation_steps,
            kwargs_handlers=[DistributedDataParallelKwargs(find_unused_parameters=True)]
        )
        
        if scale_scheduler_by_porc_count:
            np = self.accelerator.state.num_processes
            max_steps = (max_steps + np - 1) // np
        
        # Setup model
        self.model = model
        
        # if ref_kl is True, make a copy of the model for reference KL loss
        if self.ref_kl:
            print("Using reference KL loss, creating a copy of the model for reference.")
            self.ref_model = deepcopy(model)
            self.ref_model.eval()  # Ensure reference model is in eval mode
            self.ref_model.requires_grad_(False)  # Disable gradients for reference model
            self.ref_accelerator = Accelerator(
                kwargs_handlers=[DistributedDataParallelKwargs(find_unused_parameters=True)]
            )
            
            if self.ref_accelerator.distributed_type == DistributedType.DEEPSPEED:
                if self.ref_accelerator.deepspeed_plugin.deepspeed_config["zero_optimization"]["stage"] != 3:
                    self.ref_accelerator.deepspeed_plugin.deepspeed_config["zero_optimization"]["stage"] = 0
        
        # Enable gradient checkpointing if requested
        if self.gradient_checkpointing and hasattr(self.model, "gradient_checkpointing_enable"):
            self.model.gradient_checkpointing_enable()
        
        # Apply torch.compile if requested (requires PyTorch 2.0+)
        if hasattr(torch, 'compile') and compile:
            self.model = torch.compile(self.model)
            if self.ref_kl:
                self.ref_model = torch.compile(self.ref_model)
        
        # Set up optimizer
        self.lr = lr
        self.weight_decay = weight_decay
        self.setup_optimizer()
        
        # Set up learning rate scheduler
        self.schedule_type = schedule_type
        self.lr_final = lr_final
        self.max_steps = max_steps
        self.warmup_steps = warmup_steps
        self.setup_scheduler()
        
        self.current_epoch = 0
        self.global_step = 0
        
        # Load checkpoint if provided
        if checkpoint_path:
            self.load_checkpoint(checkpoint_path)
        
        # Clear CUDA cache
        torch.cuda.empty_cache()
    
    def setup_optimizer(self):
        """Set up the optimizer for training."""
        param_list = [p for p in self.model.parameters() if p.requires_grad]
        
        if self.optimizer_type == "Adam":
            self.optimizer = torch.optim.Adam(param_list, lr=self.lr, weight_decay=self.weight_decay)
        elif self.optimizer_type == "AdamW":
            self.optimizer = torch.optim.AdamW(param_list, lr=self.lr, weight_decay=self.weight_decay)
        elif self.optimizer_type == "SGD":
            self.optimizer = torch.optim.SGD(param_list, lr=self.lr, weight_decay=self.weight_decay)
        elif self.optimizer_type == "Lion":
            try:
                import lion_pytorch
                self.optimizer = lion_pytorch.Lion(param_list, lr=self.lr, weight_decay=self.weight_decay)
            except ImportError:
                print("Lion optimizer not available. Falling back to AdamW.")
                self.optimizer = torch.optim.AdamW(param_list, lr=self.lr, weight_decay=self.weight_decay)
        else:
            # Default to AdamW
            self.optimizer = torch.optim.AdamW(param_list, lr=self.lr, weight_decay=self.weight_decay)
    
    def setup_scheduler(self):
        """Set up the learning rate scheduler."""
        if self.schedule_type == "linear_with_warmup":
            self.scheduler = get_linear_schedule_with_warmup(
                self.optimizer,
                num_warmup_steps=self.warmup_steps,
                num_training_steps=self.max_steps
            )
        elif self.schedule_type == "cosine_with_warmup":
            self.scheduler = get_cosine_schedule_with_warmup(
                self.optimizer,
                num_warmup_steps=self.warmup_steps,
                num_training_steps=self.max_steps,
                num_cycles=0.5
            )
        elif self.schedule_type == "constant_with_warmup":
            self.scheduler = get_constant_schedule_with_warmup(
                self.optimizer,
                num_warmup_steps=self.warmup_steps
            )
        else:
            self.scheduler = None
    
    def save_checkpoint(self, path):
        """Save a checkpoint."""
        
        if self.accelerator.distributed_type == DistributedType.DEEPSPEED and self.accelerator.deepspeed_config["zero_optimization"]["stage"] == 3:
            # obtain state dict from DeepSpeed engine
            model_state_dict = self.accelerator.get_state_dict(self.model)
            checkpoint = {
                    'model_state_dict': model_state_dict,
                    'current_epoch': self.current_epoch,
                    'global_step': self.global_step
                }
            self.accelerator.wait_for_everyone()
            if self.accelerator.is_main_process:
                self.accelerator.save(checkpoint, path)
                
            # release memory
            del model_state_dict
            torch.cuda.empty_cache()
        elif self.accelerator.distributed_type == DistributedType.FSDP:
            # Save FSDP model state dict
            model_state_dict = self.accelerator.get_state_dict(self.model)
            checkpoint = {
                'model_state_dict': model_state_dict,
                'current_epoch': self.current_epoch,
                'global_step': self.global_step
            }
            self.accelerator.wait_for_everyone()
            if self.accelerator.is_main_process:
                # Save the checkpoint
                self.accelerator.save(checkpoint, path)
                
        elif self.accelerator.is_main_process:
            # Get unwrapped model
            unwrapped_model = self.accelerator.unwrap_model(self.model)
            
            checkpoint = {
                'model_state_dict': unwrapped_model.state_dict(),
                'current_epoch': self.current_epoch,
                'global_step': self.global_step
            }
            
            # Use accelerator to save the checkpoint
            self.accelerator.save(checkpoint, path)
    
    def load_checkpoint(self, path):
        """Load a checkpoint."""
        checkpoint = torch.load(path)
        
        # Load model state dict
        if hasattr(self.model, "load_state_dict"):
            try:
                self.model.load_state_dict(checkpoint['model_state_dict'], strict=True)
            except:
                print("Model state dict not found in checkpoint or incompatible.")
        
        self.current_epoch = checkpoint.get('current_epoch', 0)
        self.global_step = checkpoint.get('global_step', 0)
    
    def reset_optimizer(self):
        """Reset the optimizer and scheduler."""
        self.setup_optimizer()
        self.setup_scheduler()
        
        # Prepare model, optimizer and scheduler with accelerator
        self.model, self.optimizer, self.scheduler = self.accelerator.prepare(
            self.model, self.optimizer, self.scheduler
        )
    
    def train(self, dataset, train_indices=None, batch_size=8, epochs=3, continue_loop=True, verbose=True, 
              checkpoint_steps=1000, checkpoint_dir='checkpoints', dataloader_num_workers=4, remove_old_checkpoints=True,
              n_total_checkpoints_to_keep=3):
        """
        Train the model using Accelerate.
        
        Args:
            dataset: The full dataset to train on
            train_indices: Optional specific indices to use from dataset (if None, uses all)
            batch_size: Batch size
            epochs: Number of epochs to train
            continue_loop: Whether to continue from the last epoch or reset
            verbose: Whether to show progress during training
            checkpoint_steps: Save checkpoint every N steps
            checkpoint_dir: Directory to save checkpoints
            eval_dataset: Dataset for evaluation (if None, no evaluation is performed)
            eval_indices: Optional specific indices for evaluation dataset
            eval_batch_size: Batch size for evaluation (defaults to train batch_size if None)
            eval_steps: How often to run evaluation (in steps)
            max_steps: Maximum number of steps to train for (overrides epochs if provided)
            save_best_only: Only save checkpoints when evaluation loss improves
            early_stopping_patience: Number of evaluations with no improvement after which to stop
            dataloader_num_workers: Number of workers for data loading
        """
        if not continue_loop:
            self.model.train()
            self.current_epoch = 0
            self.global_step = 0
            self.reset_optimizer()
        
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Set up indices for training
        if train_indices is None:
            train_indices = list(range(len(dataset)))
        
        # Setup dataloaders
        collate_fn = getattr(dataset, '_collate_fn', None)
        train_sampler = torch.utils.data.SubsetRandomSampler(train_indices)
        
        dataloader = torch.utils.data.DataLoader(
            dataset,
            batch_size=batch_size,
            sampler=train_sampler,
            num_workers=dataloader_num_workers,
            collate_fn=collate_fn,
            pin_memory=False
        )
        data_iterator = iter(dataloader)
        
        # Prepare model, optimizer, scheduler, and dataloaders with accelerator
        self.model, self.optimizer, self.scheduler, dataloader = self.accelerator.prepare(
            self.model, self.optimizer, self.scheduler, dataloader
        )
        if self.ref_kl:
            if self.accelerator.distributed_type == DistributedType.FSDP:
                self.ref_model.eval()
                self.ref_model.requires_grad_(False)
                self.ref_model = fsdp2_prepare_model(self.accelerator, self.ref_model)
                self.ref_model.eval()
                self.ref_model.requires_grad_(False)
            else:
                self.ref_model = self.ref_accelerator.prepare(self.ref_model)
                self.ref_model.eval()
                self.ref_model.requires_grad_(False)
        
        # Set up step tracking
        epoch = self.current_epoch
        total_steps_done = self.global_step
        steps_per_epoch = (len(dataloader) + self.gradient_accumulation_steps - 1) // self.gradient_accumulation_steps
        
        if self.accelerator.is_main_process:
            if verbose:
                print(f"Training with {len(train_indices)} samples in {steps_per_epoch} steps per epoch")
                print(f"Training for {epochs} epochs ({epochs * steps_per_epoch} steps)")
            if self.log_to_wandb:
                wandb.init(project=self.wandb_project, name=self.wandb_run_name, id=self.wandb_id,
                           config={
                    "learning_rate": self.lr
                })

        loss_fct = torch.nn.CrossEntropyLoss(reduction='sum')
        
        self.accelerator.register_for_checkpointing(self.scheduler)
                
        while epoch < epochs:
            
            if verbose and self.accelerator.is_main_process:
                print(f"Epoch {epoch + 1}")
                # prog = tqdm(dataloader, total=len(dataloader), disable=not self.accelerator.is_main_process)
                prog = tqdm(range(steps_per_epoch), total=steps_per_epoch, disable=not self.accelerator.is_main_process)
            else:
                # prog = dataloader
                prog = range(steps_per_epoch)
            
            accumulated_loss = 0.0
            
            self.model.train()
            for step in prog:
                step_loss = 0.0
                step_kl_loss = 0.0
                batches = []
                total_num_items_in_batch = 0
                for b_i in range(self.gradient_accumulation_steps):
                    if b_i + step * self.gradient_accumulation_steps >= len(dataloader):
                        break
                    batch = next(data_iterator)
                    batch = batch.to(self.accelerator.device)
                    local_num_items_in_batch = batch['labels'].ne(-100).sum()
                    total_num_items_in_batch += self.accelerator.gather(local_num_items_in_batch).sum().item()
                    batches.append(batch)

                for batch in batches:
                    labels = batch.pop('labels', None)
                
                    outputs = self.model(**batch)
                    
                    # raise NotImplementedError(f"Current outputs are: {outputs}")
                
                
                    # loss = outputs.loss
                    shift_logits = outputs.logits[..., :-1, :].contiguous()
                    shift_labels = labels[..., 1:].contiguous()
                    
                    # Flatten the tokens
                    shift_labels = shift_labels.view(-1)
                    B = shift_labels.size(0)
                    shift_logits = shift_logits.view(B, -1)
                    loss = loss_fct(shift_logits, shift_labels)/total_num_items_in_batch * self.accelerator.num_processes
                    
                    if self.ref_kl:
                        shift_logits_extracted = shift_logits[shift_labels != -100]
                        shift_labels_extracted = shift_labels[shift_labels != -100]
                        per_token_logps = selective_log_softmax(shift_logits_extracted, shift_labels_extracted)
                        with torch.no_grad():
                            ref_outputs = self.ref_model(**batch)
                            ref_shift_logits = ref_outputs.logits[..., :-1, :].contiguous()
                            ref_shift_logits = ref_shift_logits.view(B, -1)
                            ref_shift_logits_extracted = ref_shift_logits[shift_labels != -100]
                            ref_per_token_logps = selective_log_softmax(ref_shift_logits_extracted, shift_labels_extracted)
                        
                        per_token_kl = (
                            torch.exp(ref_per_token_logps - per_token_logps) - (ref_per_token_logps - per_token_logps) - 1
                        )
                        
                        kl_loss = per_token_kl.sum() / total_num_items_in_batch * self.accelerator.num_processes
                        
                        full_loss = loss + self.ref_kl_weight * kl_loss
                        
                        step_kl_loss += self.accelerator.gather(kl_loss).sum().item()
                        
                        # Backward pass handled by accelerator
                        self.accelerator.backward(full_loss)
                    else:
                        # Backward pass handled by accelerator
                        self.accelerator.backward(loss)

                    gathered_loss = self.accelerator.gather(loss).sum().item()
                    accumulated_loss += gathered_loss
                    step_loss += gathered_loss

                if self.max_grad_norm > 0:
                    self.accelerator.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)
                    
                # Step optimizer
                self.optimizer.step()
                self.optimizer.zero_grad()
                
                # Step scheduler if we're using it
                if self.scheduler is not None:
                    self.scheduler.step()
                
                # Increment global step counter
                total_steps_done += 1
                self.global_step = total_steps_done
                
                # Step-based checkpoint saving
                should_save = (total_steps_done % checkpoint_steps == 0)
                
                if should_save:
                    checkpoint_path = os.path.join(checkpoint_dir, f'checkpoint_step_{total_steps_done}.pt')
                    self.save_checkpoint(checkpoint_path)
                    
                    if verbose and self.accelerator.is_main_process:
                        print(f"\nSaved checkpoint at step {total_steps_done} to {checkpoint_path}")
                        
                    # Optional: Remove older checkpoints to save disk space
                    if remove_old_checkpoints and self.accelerator.is_main_process:
                        old_checkpoint = os.path.join(checkpoint_dir, f'checkpoint_step_{total_steps_done - (n_total_checkpoints_to_keep * checkpoint_steps)}.pt')
                        if os.path.exists(old_checkpoint):
                            os.remove(old_checkpoint)
                            
                # Update progress bar
                if self.accelerator.is_main_process:
                    if verbose:
                        current_lr = self.optimizer.param_groups[0]['lr']
                        avg_loss = accumulated_loss / (step + 1)
                        prog.set_postfix({
                            'epoch loss': f"{avg_loss:.5f}",
                            'loss': f"{step_loss:.5f}",
                            'lr': f"{current_lr:.7f}",
                            'step': total_steps_done,
                            'kl loss': f"{step_kl_loss:.5f}" if self.ref_kl else 'N/A'
                        })
                    if self.log_to_wandb:
                        wandb.log({
                        "loss": step_loss,
                        "kl_loss": step_kl_loss if self.ref_kl else None,
                        "step": total_steps_done,
                        'lr': current_lr
                    })
                        
            # Increment epoch counter
            epoch += 1
            self.current_epoch = epoch
            
            # Print epoch summary
            if verbose and self.accelerator.is_main_process:
                print(f"Epoch {epoch} completed. Average loss: {accumulated_loss / steps_per_epoch:.5f}")
            
            # save epoch checkpoint
            epoch_checkpoint_path = os.path.join(checkpoint_dir, f'checkpoint_epoch_{epoch}.pt')
            self.save_checkpoint(epoch_checkpoint_path)
        
        # Save final model
        final_path = os.path.join(checkpoint_dir, 'final_model.pt')
        self.save_checkpoint(final_path)
        
        if verbose and self.accelerator.is_main_process:
            print(f"Training completed. Final model saved to {final_path}")
        
        # Make sure all processes reach here
        self.accelerator.wait_for_everyone()
        
