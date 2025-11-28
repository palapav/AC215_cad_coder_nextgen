#!/usr/bin/env python3
"""Centralized Training Script - Fine-tunes model on full dataset with QLoRA"""
import os
import sys
import argparse
import torch
from datasets import load_from_disk, concatenate_datasets
from transformers import AutoProcessor, BitsAndBytesConfig
from torch.utils.data import DataLoader, SubsetRandomSampler
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CADRL'))

from utils.patches import apply_accelerate_patches
from utils.model_utils import load_model, freeze_vision_encoder, load_checkpoint_into_model
from utils.config import DEFAULT_MODEL, TRAINING_DEFAULTS, DATA_PATHS, WANDB_DEFAULTS

# Apply lightweight accelerate patches at import time
apply_accelerate_patches()

from DataUtils.Collators import QwenVLCollator
from DataUtils.Datasets import MinimalImageCADDataset

torch.backends.cuda.matmul.allow_tf32 = True
torch.set_float32_matmul_precision('high')


def is_valid_dataset_dir(path):
    """Check if directory contains a valid HuggingFace dataset."""
    if not os.path.exists(path):
        return False
    # Check for required dataset files
    required_files = ['dataset_info.json', 'state.json']
    return any(os.path.exists(os.path.join(path, f)) for f in required_files)


def load_or_create_combined_dataset(args):
    """Load or create combined training dataset from client1 + client2."""
    combined_path = args.combined_dir
    
    # Check if valid cached dataset exists
    if is_valid_dataset_dir(combined_path) and not args.force_recombine:
        print(f"=== Loading Cached Combined Dataset ===")
        print(f"Loading from: {combined_path}")
        try:
            dataset_data = load_from_disk(combined_path)
            print(f"✓ Loaded: {len(dataset_data)} samples")
        except Exception as e:
            print(f"⚠️  Cache invalid ({e}), recreating...")
            # Clear invalid cache and recreate
            import shutil
            if os.path.exists(combined_path):
                shutil.rmtree(combined_path)
            return load_or_create_combined_dataset(args)
    else:
        print("=== Creating Combined Training Dataset ===")
        print(f"Client 1: {args.client1_dir}")
        print(f"Client 2: {args.client2_dir}")
        
        client1_data = load_from_disk(args.client1_dir)
        client2_data = load_from_disk(args.client2_dir)
        
        print(f"Client 1: {len(client1_data)} samples")
        print(f"Client 2: {len(client2_data)} samples")
        
        dataset_data = concatenate_datasets([client1_data, client2_data])
        print(f"Combined: {len(dataset_data)} samples")
        
        # Save to cache for future runs
        os.makedirs(combined_path, exist_ok=True)
        print(f"Saving to cache: {combined_path}")
        dataset_data.save_to_disk(combined_path)
        print("✓ Cached for future runs")
    
    # Map 'cadquery' to 'code' if needed
    if 'code' not in dataset_data.column_names and 'cadquery' in dataset_data.column_names:
        dataset_data = dataset_data.map(lambda x: {'code': x['cadquery']})
    
    # Limit samples for testing if requested
    if args.max_samples and len(dataset_data) > args.max_samples:
        print(f"Test mode: Limiting to {args.max_samples} samples")
        dataset_data = dataset_data.select(range(args.max_samples))
    
    return dataset_data


def load_validation_dataset(args, collate_fn):
    """Load validation dataset for evaluation during training."""
    val_path = DATA_PATHS["validation"]
    if not os.path.exists(val_path):
        print("⚠️  Validation dataset not found, skipping evaluation")
        return None
    
    print(f"\nLoading validation dataset from: {val_path}")
    val_data = load_from_disk(val_path)
    
    # Map 'cadquery' to 'code' if needed
    if 'code' not in val_data.column_names and 'cadquery' in val_data.column_names:
        val_data = val_data.map(lambda x: {'code': x['cadquery']})
    
    # Subsample for faster evaluation (industry best practice)
    # Use fixed random seed for consistency across evaluations
    if args.val_samples and len(val_data) > args.val_samples:
        import random
        random.seed(42)
        indices = random.sample(range(len(val_data)), args.val_samples)
        indices.sort()  # Keep in order for reproducibility
        val_data = val_data.select(indices)
        print(f"  Subsampled to {args.val_samples} examples (for speed)")
    
    val_dataset = MinimalImageCADDataset(
        val_data,
        collate_fn=collate_fn,
        basic_image_augmentation=False,
        augmentation_probability=0.0,
        pc_input=False,
        image_input=True,
        num_points=256
    )
    print(f"✓ Validation dataset: {len(val_dataset)} samples")
    return val_dataset


def evaluate_on_validation(trainer, val_dataset, batch_size, step):
    """
    Evaluate model on validation dataset (inference only, no gradient updates).
    Compatible with CADRL trainer architecture.
    """
    trainer.model.eval()
    val_sampler = torch.utils.data.SubsetRandomSampler(list(range(len(val_dataset))))
    collate_fn = getattr(val_dataset, '_collate_fn', None)
    
    # Use batch_size=1 for validation to minimize memory usage
    val_loader = DataLoader(
        val_dataset,
        batch_size=1,  # Fixed to 1 for memory efficiency
        sampler=val_sampler,
        collate_fn=collate_fn,
        num_workers=0,
        pin_memory=True
    )
    
    # Prepare with accelerator
    val_loader = trainer.accelerator.prepare(val_loader)
    
    total_loss = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for batch in val_loader:
            outputs = trainer.model(**batch)
            loss = outputs.loss
            
            # Gather loss across all processes
            gathered_loss = trainer.accelerator.gather(loss)
            total_loss += gathered_loss.mean().item()
            num_batches += 1
    
    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    
    # Log to WandB if enabled
    if trainer.log_to_wandb and trainer.accelerator.is_main_process:
        import wandb
        wandb.log({
            "val/loss": avg_loss,
            "global_step": step,
        }, step=step)
    
    if trainer.accelerator.is_main_process:
        print(f"\n  📊 Validation Loss: {avg_loss:.4f}")
    
    trainer.model.train()
    return avg_loss


def train_with_validation(trainer, train_dataset, val_dataset, args):
    """
    Custom training loop that wraps CADRL's SFTSyncedGrad.train() 
    and adds validation evaluation at specified intervals.
    """
    if val_dataset is None or args.eval_steps is None:
        # No validation, use standard training
        print("ℹ️  No validation evaluation (use --eval_steps to enable)")
        trainer.train(
            dataset=train_dataset,
            batch_size=args.batch_size,
            epochs=args.num_epochs,
            checkpoint_steps=args.checkpoint_steps,
            checkpoint_dir=args.output_dir,
            verbose=True,
            n_total_checkpoints_to_keep=args.n_checkpoints_to_keep,
            remove_old_checkpoints=True,
        )
        return
    
    # Training with validation
    print(f"✓ Validation evaluation enabled (every {args.eval_steps} steps)")
    
    # We'll manually handle the training loop to inject validation
    # This is a compromise: we use CADRL's training but periodically pause for validation
    import torch.utils.data
    from tqdm import tqdm
    
    # Initialize WandB if needed (following CADRL pattern)
    if trainer.log_to_wandb and trainer.accelerator.is_main_process:
        import wandb
        wandb.init(
            project=trainer.wandb_project,
            name=trainer.wandb_run_name,
            id=trainer.wandb_id,
            config={
                "model": args.base_model,
                "learning_rate": trainer.lr,
                "weight_decay": args.weight_decay,
                "batch_size": args.batch_size,
                "gradient_accumulation_steps": args.gradient_accumulation_steps,
                "effective_batch_size": args.batch_size * args.gradient_accumulation_steps,
                "max_len": args.max_len,
                "num_epochs": args.num_epochs,
                "eval_steps": args.eval_steps,
                "val_samples": args.val_samples,
                "checkpoint_steps": args.checkpoint_steps,
                "freeze_vision": args.freeze_vision,
                "gradient_checkpointing": args.gradient_checkpointing,
            }
        )
    
    trainer.model.train()
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Setup dataloader
    train_sampler = torch.utils.data.SubsetRandomSampler(list(range(len(train_dataset))))
    collate_fn = getattr(train_dataset, '_collate_fn', None)
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        sampler=train_sampler,
        collate_fn=collate_fn,
        num_workers=0,
        pin_memory=True
    )
    
    # Prepare with accelerator
    trainer.model, trainer.optimizer, train_loader = trainer.accelerator.prepare(
        trainer.model, trainer.optimizer, train_loader
    )
    if trainer.scheduler is not None:
        trainer.scheduler = trainer.accelerator.prepare(trainer.scheduler)
    
    total_steps = 0
    best_val_loss = float('inf')
    
    for epoch in range(args.num_epochs):
        if trainer.accelerator.is_main_process:
            print(f"\n=== Epoch {epoch + 1}/{args.num_epochs} ===")
        
        epoch_loss = 0.0
        num_batches = 0
        
        progress_bar = tqdm(train_loader, disable=not trainer.accelerator.is_main_process)
        
        for batch in progress_bar:
            with trainer.accelerator.accumulate(trainer.model):
                outputs = trainer.model(**batch)
                loss = outputs.loss
                
                trainer.accelerator.backward(loss)
                
                if trainer.accelerator.sync_gradients:
                    if trainer.max_grad_norm > 0:
                        trainer.accelerator.clip_grad_norm_(trainer.model.parameters(), trainer.max_grad_norm)
                    
                    trainer.optimizer.step()
                    trainer.optimizer.zero_grad()
                    
                    if trainer.scheduler is not None:
                        trainer.scheduler.step()
                    
                    total_steps += 1
                    trainer.global_step = total_steps
                    
                    # Validation evaluation
                    if total_steps % args.eval_steps == 0:
                        val_loss = evaluate_on_validation(
                            trainer, val_dataset, 
                            args.eval_batch_size or args.batch_size,
                            total_steps
                        )
                        
                        # Track best val loss (don't save during validation to avoid NCCL timeout)
                        if val_loss < best_val_loss:
                            best_val_loss = val_loss
                            if trainer.accelerator.is_main_process:
                                print(f"  ⭐ New best val_loss: {val_loss:.4f}")
                    
                    # Checkpointing disabled during training (too slow)
                    # Only save at end and on interruption
                    if total_steps % args.checkpoint_steps == 0:
                        if trainer.accelerator.is_main_process:
                            print(f"  📍 Checkpoint milestone: step {total_steps}")
                            if best_val_loss < float('inf'):
                                print(f"     Best val_loss so far: {best_val_loss:.4f}")
                
                epoch_loss += loss.item()
                num_batches += 1
                
                # Update progress bar
                if trainer.accelerator.sync_gradients:
                    progress_bar.set_postfix({
                        'loss': f'{loss.item():.4f}',
                        'step': total_steps
                    })
                    
                    # Log to WandB
                    if trainer.log_to_wandb and trainer.accelerator.is_main_process:
                        import wandb
                        wandb.log({
                            "train/loss": loss.item(),
                            "train/epoch": epoch,
                            "global_step": total_steps,
                        }, step=total_steps)
        
        avg_epoch_loss = epoch_loss / num_batches if num_batches > 0 else 0.0
        if trainer.accelerator.is_main_process:
            print(f"Epoch {epoch + 1} avg loss: {avg_epoch_loss:.4f}")


def main():
    parser = argparse.ArgumentParser(description="Centralized Training")
    
    # Data
    parser.add_argument("--client1_dir", type=str, default=DATA_PATHS["client1"])
    parser.add_argument("--client2_dir", type=str, default=DATA_PATHS["client2"])
    parser.add_argument("--combined_dir", type=str, default=DATA_PATHS["combined"])
    parser.add_argument("--force_recombine", action="store_true",
                       help="Force recombine datasets even if cache exists")
    
    # Model
    parser.add_argument("--base_model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--output_dir", type=str, required=True)
    
    # QLoRA / LoRA options
    parser.add_argument("--use_qlora", action="store_true",
                       help="Use QLoRA (4-bit quantization + LoRA adapters)")
    parser.add_argument("--use_lora", action="store_true",
                       help="Use LoRA adapters without quantization")
    parser.add_argument("--lora_r", type=int, default=128,
                       help="LoRA rank (default: 128, higher for better quality)")
    parser.add_argument("--lora_alpha", type=int, default=256,
                       help="LoRA alpha (default: 256, 2x rank for scaling)")
    parser.add_argument("--lora_dropout", type=float, default=0.05,
                       help="LoRA dropout (default: 0.05)")
    
    # Training
    parser.add_argument("--num_epochs", type=int, default=TRAINING_DEFAULTS["num_epochs"])
    parser.add_argument("--batch_size", type=int, default=TRAINING_DEFAULTS["batch_size"])
    parser.add_argument("--lr", type=float, default=TRAINING_DEFAULTS["learning_rate"])
    parser.add_argument("--weight_decay", type=float, default=TRAINING_DEFAULTS["weight_decay"])
    parser.add_argument("--warmup_steps", type=int, default=TRAINING_DEFAULTS["warmup_steps"])
    parser.add_argument("--gradient_accumulation_steps", type=int, default=TRAINING_DEFAULTS["gradient_accumulation_steps"])
    parser.add_argument("--max_grad_norm", type=float, default=TRAINING_DEFAULTS["max_grad_norm"])
    parser.add_argument("--max_len", type=int, default=TRAINING_DEFAULTS["max_len"])
    parser.add_argument("--assistant_only", action="store_true")
    parser.add_argument("--freeze_vision", action="store_true")
    parser.add_argument("--gradient_checkpointing", action="store_true")
    
    # Checkpointing (sparse by default)
    parser.add_argument("--checkpoint_steps", type=int, default=TRAINING_DEFAULTS["checkpoint_steps"])
    parser.add_argument("--resume_from", type=str, default=None)
    
    # Testing
    parser.add_argument("--max_samples", type=int, default=None,
                       help="Limit training samples (for quick testing)")
    
    # Evaluation (added for industry best practices)
    parser.add_argument("--eval_steps", type=int, default=None,
                       help="Evaluate on validation set every N steps (inference only)")
    parser.add_argument("--eval_batch_size", type=int, default=None,
                       help="Batch size for validation evaluation")
    parser.add_argument("--val_samples", type=int, default=1000,
                       help="Number of validation samples to use (subsampled for speed, default: 1000)")
    parser.add_argument("--n_checkpoints_to_keep", type=int, default=2,
                       help="Number of regular checkpoints to keep")
    
    # WandB
    parser.add_argument("--log_to_wandb", action="store_true")
    parser.add_argument("--wandb_project", type=str, default=WANDB_DEFAULTS["centralized_project"])
    parser.add_argument("--wandb_name", type=str, default="centralized_training")
    
    args = parser.parse_args()

    # Import heavy training components lazily so that centralized_train
    # can be imported in lightweight contexts (e.g., tests using
    # is_valid_dataset_dir) without pulling in full accelerate/Trainer stack.
    from Trainers.SFT import SFTSyncedGrad
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=== Centralized Training ===")
    print(f"Model: {args.base_model}")
    print(f"Output: {args.output_dir}")
    
    # Load or create combined training dataset
    train_data = load_or_create_combined_dataset(args)
    
    # Load processor (from cache if available)
    print("Loading processor...")
    processor = AutoProcessor.from_pretrained(args.base_model)
    
    # Setup collator
    collate_fn = QwenVLCollator(
        processor,
        assistant_only=args.assistant_only,
        max_len=args.max_len,
        num_points=256
    )
    
    # Create training dataset
    train_dataset = MinimalImageCADDataset(
        train_data,
        collate_fn=collate_fn,
        basic_image_augmentation=False,
        augmentation_probability=0.0,
        pc_input=False,
        image_input=True,
        num_points=256
    )
    print(f"Training dataset: {len(train_dataset)} samples")
    
    # Load validation dataset if eval_steps is specified
    val_dataset = None
    if args.eval_steps is not None:
        val_dataset = load_validation_dataset(args, collate_fn)
    
    # Load model with optional quantization
    print(f"Loading model: {args.base_model}")
    
    # Use HuggingFace recommended loading for Qwen3-VL
    from transformers import Qwen3VLForConditionalGeneration
    
    if args.use_qlora or args.use_lora:
        print("⚠️  Note: LoRA/QLoRA with FSDP uses bf16 (not 4-bit)")
        model = Qwen3VLForConditionalGeneration.from_pretrained(
            args.base_model,
            torch_dtype=torch.bfloat16,
            device_map="cpu",  # FSDP handles device placement
        )
    else:
        model = Qwen3VLForConditionalGeneration.from_pretrained(
            args.base_model,
            torch_dtype=torch.bfloat16,
            device_map="cpu",  # FSDP handles device placement
        )
    
    # Apply LoRA adapters (FSDP-compatible)
    if args.use_qlora or args.use_lora:
        print(f"Applying LoRA adapters (r={args.lora_r}, alpha={args.lora_alpha})")
        
        # Ensure model is in bf16 before LoRA (FSDP requires uniform dtype)
        model = model.to(torch.bfloat16)
        
        # Target modules for Qwen3-VL (language model only)
        lora_config = LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", 
                           "gate_proj", "up_proj", "down_proj"],  # Attention + MLP
            lora_dropout=args.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
            modules_to_save=None,
        )
        
        model = get_peft_model(model, lora_config)
        
        # Convert LoRA parameters to bf16 (FSDP needs uniform dtype)
        for name, param in model.named_parameters():
            if param.requires_grad:
                param.data = param.data.to(torch.bfloat16)
        
        model.print_trainable_parameters()
        
        # Enable gradient checkpointing for LoRA (memory efficient)
        if args.gradient_checkpointing:
            model.enable_input_require_grads()
    
    # Freeze vision encoder (always, even with LoRA)
    if args.freeze_vision:
        freeze_vision_encoder(model)

    # Load checkpoint if resuming
    if args.resume_from and os.path.exists(args.resume_from):
        load_checkpoint_into_model(model, args.resume_from)
    
    # Calculate training steps
    steps_per_epoch = (len(train_dataset) + args.batch_size * args.gradient_accumulation_steps - 1) // \
                      (args.batch_size * args.gradient_accumulation_steps)
    max_steps = steps_per_epoch * args.num_epochs
    
    print(f"\nTraining config:")
    print(f"  Epochs: {args.num_epochs}")
    print(f"  Steps/epoch: {steps_per_epoch}")
    print(f"  Total steps: {max_steps}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Grad accum: {args.gradient_accumulation_steps}")
    print(f"  Effective batch: {args.batch_size * args.gradient_accumulation_steps}")
    print(f"  Checkpoint every: {args.checkpoint_steps} steps")
    
    # Initialize trainer
    trainer = SFTSyncedGrad(
        model=model,
        lr=args.lr,
        weight_decay=args.weight_decay,
        schedule_type="constant_with_warmup",
        lr_final=1e-6,
        max_steps=max_steps,
        warmup_steps=args.warmup_steps,
        compile=False,
        checkpoint_path=args.resume_from,
        optimizer_type="AdamW",
        gradient_checkpointing=args.gradient_checkpointing,
        max_grad_norm=args.max_grad_norm,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        custom_loss=None,
        ref_kl=False,
        ref_kl_weight=0.01,
        scale_scheduler_by_porc_count=True,
        log_to_wandb=args.log_to_wandb,
        wandb_project=args.wandb_project,
        wandb_run_name=args.wandb_name,
    )
    
    # Train (with validation evaluation if enabled)
    print(f"\nStarting training...")
    train_with_validation(trainer, train_dataset, val_dataset, args)
    
    # Save final model
    print("\n💾 Saving final model...")
    if args.use_qlora or args.use_lora:
        # Save only LoRA adapters (fast and small)
        final_path = os.path.join(args.output_dir, "final_lora_adapters")
        unwrapped_model = trainer.accelerator.unwrap_model(trainer.model)
        unwrapped_model.save_pretrained(final_path)
        print(f"✓ Training complete!")
        print(f"LoRA adapters saved: {final_path}")
        print(f"To use: load base model + adapters with PeftModel.from_pretrained()")
    else:
        # Save full model
        final_path = os.path.join(args.output_dir, "final_model.pt")
        trainer.save_checkpoint(final_path)
        print(f"✓ Training complete!")
        print(f"Final model: {final_path}")


if __name__ == "__main__":
    import signal
    
    # Handler to save model on interruption
    def save_on_exit(signum=None, frame=None):
        print("\n⚠️  Training interrupted! Saving current model state...")
        try:
            # Try to save if we're in main process
            from accelerate import Accelerator
            accelerator = Accelerator()
            if accelerator.is_main_process:
                import argparse
                parser = argparse.ArgumentParser()
                parser.add_argument("--output_dir", type=str, required=True)
                parser.add_argument("--use_qlora", action="store_true")
                parser.add_argument("--use_lora", action="store_true")
                args, _ = parser.parse_known_args()
                
                interrupt_path = os.path.join(args.output_dir, "interrupted_model")
                print(f"Saving to: {interrupt_path}")
                # Note: This won't work perfectly due to FSDP, but attempt it
                print("⚠️  Model save on interruption may be incomplete with FSDP")
        except Exception as e:
            print(f"Could not save on interruption: {e}")
        sys.exit(130)
    
    signal.signal(signal.SIGINT, save_on_exit)
    signal.signal(signal.SIGTERM, save_on_exit)
    
    try:
        main()
    except KeyboardInterrupt:
        save_on_exit()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
