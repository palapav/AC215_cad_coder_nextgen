import os
from platform import processor
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["VLLM_LOGGING_LEVEL"] = "ERROR" 

from PIL import Image
import json
import numpy as np
from tqdm.auto import trange
from qwen_vl_utils import process_vision_info
import torch
from transformers import Qwen2VLProcessor
from typing import Optional, Tuple, List, Dict, Any, Union, Callable
import re
import multiprocessing as mp
import asyncio

# Lazy import for pytorch3d (only needed for point cloud processing)
_sample_farthest_points = None

def _get_sample_farthest_points():
    """Lazy import of sample_farthest_points from pytorch3d."""
    global _sample_farthest_points
    if _sample_farthest_points is None:
        try:
            from pytorch3d.ops import sample_farthest_points
            _sample_farthest_points = sample_farthest_points
        except (ImportError, ModuleNotFoundError):
            def _stub(*args, **kwargs):
                raise RuntimeError(
                    "pytorch3d is required for point cloud downsampling. Install "
                    "pytorch3d before running point-cloud-dependent code."
                )
            _sample_farthest_points = _stub
    return _sample_farthest_points

def normalize_like_cadrille_eval(pc):
    """
    Normalize a batch of point clouds.
    Args:
        pc: tensor of shape [batch_size, num_points, 3]
    Returns:
        normalized pc of same shape
    """
    # Find min/max per sample in the batch
    min_vals = pc.min(dim=1, keepdim=True)[0]  # [batch_size, 1, 3]
    max_vals = pc.max(dim=1, keepdim=True)[0]  # [batch_size, 1, 3]
    
    center = (min_vals + max_vals) / 2.0
    pc = pc - center
    
    # Scale by largest extent per sample
    extents = (max_vals - min_vals).max(dim=-1, keepdim=True)[0]  # [batch_size, 1, 1]
    
    # Handle degenerate cases where all points are identical
    valid_mask = extents > 1e-7
    pc = torch.where(valid_mask, pc / extents, torch.zeros_like(pc))
    
    # Shift to [0, 1] cube
    pc = pc + 0.5
    
    return pc

# def normalize_like_cadrille_eval(pc):
#     min_vals = pc.min(dim=-1, keepdim=True)[0]
#     max_vals = pc.max(dim=-1, keepdim=True)[0]
#     center = (min_vals + max_vals) / 2.0
    
#     pc = pc - center
    
#     extent = (max_vals - min_vals).max(dim=-1, keepdim=True)[0]
    
#     # Handle degenerate cases
#     valid_mask = extent > 1e-7
#     pc[valid_mask] = pc[valid_mask] / extent[valid_mask]
#     pc[~valid_mask] = 0  # Degenerate point clouds become zeros
    
#     pc = pc + 0.5
    
#     return pc

def extract_code(text):
    # Use regex to find the code block
    match = re.search(r'```python(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return text
    
class QwenVLCollator: ## TODO: fix so it uses has_pc and can run without pc input
    def __init__(self, processor: Qwen2VLProcessor, assistant_only: bool = True, max_len: Optional[int] = 4096, num_points: int = 256):
        self.processor = processor
        self.assistant_only = assistant_only
        self.max_len = max_len
        self.num_points = num_points
        self.special_tokens = processor.tokenizer("<|im_start|>assistant<|im_end|>")['input_ids']

    def __call__(self, samples):

        has_pc_list = [s['has_pc'] for s in samples]
        # print("HAS PC LIST")
        # print(has_pc_list)
        
        # Pull out the conversations (your "prompt" lists)
        conversations = [s["prompt"] for s in samples]
        
        texts = self.processor.apply_chat_template(conversations, tokenize=False)
        
        # print("FULL TEXT")
        # print(texts)
        
        image_inputs = process_vision_info(conversations)[0]
        
        # print("IMAGE INPUTS")
        # print(image_inputs)

        # Tokenize the texts and process the images
        if self.max_len is None:
            batch = self.processor(
                text=texts, images=image_inputs, return_tensors="pt", padding=True
            )
        else:
            batch = self.processor(
                text=texts, images=image_inputs, return_tensors="pt", padding='max_length', truncation=True, max_length=self.max_len
            )
        
        labels = batch["input_ids"].clone()

        labels[labels == self.processor.tokenizer.pad_token_id] = -100
        if isinstance(self.processor, Qwen2VLProcessor):
            image_tokens = [151652, 151653, 151655]
        else: #TODO: figure out why Qwen processor is hitting this instead of above
            # image_tokens = [self.processor.tokenizer.convert_tokens_to_ids(self.processor.image_token)]
            image_tokens = [151652, 151653, 151655]

        # Mask image token IDs in the labels
        for image_token_id in image_tokens:
            labels[labels == image_token_id] = -100
        
        if has_pc_list[0]:
            # print("HAS PC")
            pc_id = self.processor.tokenizer.convert_tokens_to_ids("<pc>")
            
            if pc_id is not None and pc_id != self.processor.tokenizer.unk_token_id:
                labels[labels == pc_id] = -100

        if self.assistant_only:
            # Only keep the assistant's response in the labels only
            # since all samples have the same length user prompt we just find the start of the assistant response
            for i in range(len(labels)):
                starts = torch.where(labels[i] == self.special_tokens[0])[0]
                ends = torch.where(labels[i] == self.special_tokens[2])[0]
                
                if len(ends)< len(starts):
                    print("inside ends fix")
                    ends_ = torch.zeros_like(starts)
                    ends_[:len(ends)] = ends
                    ends_[len(ends):] = len(labels[i]) - 1
                    ends = ends_

                # Looks at all <im_start> and <im_end> pairs and only keeps the assistant response
                for j in range(len(starts)):
                    if labels[i][starts[j]+1] != self.special_tokens[1]:
                        labels[i][starts[j]:ends[j]+2] = -100

        batch["labels"] = labels  # Add labels to the batch
        
        if has_pc_list[0]:
            # Pass the point cloud embeddings along for the batch
            pc = torch.stack([torch.as_tensor(s["pc"], dtype=torch.float32) for s in samples], dim=0)
            
            # Diagnostic to check original point cloud for anything weird
            if torch.isnan(pc).any():
                print("⚠️ NaN detected in INPUT point clouds (before FPS)!")
                nan_batches = torch.isnan(pc).any(dim=[1,2]).nonzero().squeeze()
                print(f"Batch indices with NaN in input: {nan_batches}")
                for idx in nan_batches:
                    print(f"  Sample {idx}: {torch.isnan(pc[idx]).sum()} NaN values")
                raise ValueError("NaN in input point clouds")

            # Check for degenerate cases
            for i in range(pc.shape[0]):
                n_unique = torch.unique(pc[i], dim=0).shape[0]
                if n_unique < 10:  # Arbitrary threshold
                    print(f"⚠️ Sample {i}: Only {n_unique} unique points")

            # Downsample point cloud to self.num_points points
            try:
                sample_farthest_points = _get_sample_farthest_points()
                pc_downsampled = sample_farthest_points(pc, K=self.num_points)[0]
            except Exception as e:
                print(f"Error during FPS: {e}")
                print(f"PC shape: {pc.shape}")
                raise

            # Diagnostic to check downsampled point cloud for anything weird
            if torch.isnan(pc_downsampled).any():
                print("⚠️ NaN detected AFTER FPS!")
            
            # Checks for weird point clouds
            if torch.isnan(pc_downsampled).any():
                print("NaN detected in normalized point clouds!")
                print(f"Batch indices with NaN: {torch.isnan(pc_downsampled).any(dim=[1,2]).nonzero().squeeze()}")
                # You can either skip these samples or raise an error
                raise ValueError("NaN values found in point cloud batch")

            if torch.isinf(pc_downsampled).any():
                print("Inf detected in downsampled point clouds!")
                raise ValueError("Inf values found in point cloud batch")
            
            # Optional: Check reasonable range
            if (pc_downsampled < -10).any() or (pc_downsampled > 10).any():
                print(f"Warning: Point cloud values outside expected range")
                print(f"Min: {pc_downsampled.min()}, Max: {pc_downsampled.max()}")

            batch["point_clouds"] = pc_downsampled
            batch["pc_token_id"] = pc_id
            
        else:
            # print("NO PC")
            batch["point_clouds"] = None
            batch["pc_token_id"] = None

        return batch
    
class QwenVLRLCollator:
    def __init__(self,
                 processor: Qwen2VLProcessor,
                 vllm_client: Any,
                 iou_client: Any,
                 max_batch_size: int = 8,
                 n : int = 8,
                 max_tokens: int = 4096,
                 temperature: float = 0.5,
                 top_p: float = 0.9,
                 assistant_only: bool = True,
                 system_prompt: Optional[str] = "You are a helpful assistant.",
                 user_prompt: Optional[str] = "Generate the CADQuery code needed to create the CAD for the provided image.",
                 max_len: Optional[int] = 4096,
                 reward_type: Optional[str] = "iou"
                 ):
        
        self.processor = processor
        self.max_batch_size = max_batch_size
        self.n = n
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.client = vllm_client
        self.client.set_sampling_params(
            n=n,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )
        self.n = n
        self.assistant_only = assistant_only
        self.max_len = max_len
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.special_tokens = processor.tokenizer("<|im_start|>assistant<|im_end|>")['input_ids']
        self.iouclient = iou_client
        self.reward_type = reward_type

    def __call__(self, _batch):
        
        prompts = [item["vllm_prompt"] for item in _batch]
        completions = asyncio.run(self.client.chat(prompts))
        
        responses = []
        
        for i in range(len(completions)):
            code = _batch[i]['code']
            for completion in completions[i]:
                responses.append({
                    "ground_truth": code,
                    "generated": extract_code(completion)
                })
        
        
        samples = []
        for i in range(len(_batch)):
            code = _batch[i]['code']
            image = _batch[i]['image']
            
            for completion in completions[i]:
                prompt = [
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": self.system_prompt}]
                    },
                    {
                        "role": "user",
                        "content": [{"type": "image", "image": image},
                                    {"type": "text", "text": self.user_prompt}]
                    },
                    {
                        "role": "assistant",
                        "content": [{"type": "text", "text": completion}]
                    }
                ]
                samples.append(prompt)

        batch_size = len(_batch)
        iou, status_codes = asyncio.run(self.iouclient.main(responses))
        
        if self.reward_type == "iou":
            rewards = np.array(iou)
        elif self.reward_type == "syntax":
            rewards = np.where(status_codes == 0 , 1.0, -1.0)
        
        advantage = rewards.reshape(batch_size, -1)
        advantage = (advantage - advantage.mean(axis=1, keepdims=True)) / (advantage.std(axis=1, keepdims=True) + 1e-6)
        advantage = advantage.reshape(-1)
        
        n_samples = len(samples)
        n_batches = (n_samples + self.max_batch_size - 1) // self.max_batch_size
        
        batches = []
        for i in range(n_batches):
            texts = self.processor.apply_chat_template(samples[i*self.max_batch_size:(i+1)*self.max_batch_size], tokenize=False)
            image_inputs = process_vision_info(samples[i*self.max_batch_size:(i+1)*self.max_batch_size])[0]

            # Tokenize the texts and process the images
            if self.max_len is None:
                batch = self.processor(
                    text=texts, images=image_inputs, return_tensors="pt", padding=True
                )
            else:
                batch = self.processor(
                    text=texts, images=image_inputs, return_tensors="pt", padding='max_length', truncation=True, max_length=self.max_len
                )

            labels = batch["input_ids"].clone()

            labels[labels == self.processor.tokenizer.pad_token_id] = -100
            if isinstance(self.processor, Qwen2VLProcessor):
                image_tokens = [151652, 151653, 151655]
            else:
                image_tokens = [self.processor.tokenizer.convert_tokens_to_ids(self.processor.image_token)]

            # Mask image token IDs in the labels
            for image_token_id in image_tokens:
                labels[labels == image_token_id] = -100

            if self.assistant_only:
                # Only keep the assistant's response in the labels only
                # since all samples have the same length user prompt we just find the start of the assistant response
                for i_ in range(len(labels)):
                    starts = torch.where(labels[i_] == self.special_tokens[0])[0]
                    ends = torch.where(labels[i_] == self.special_tokens[2])[0]

                    if len(ends)< len(starts):
                        ends_ = torch.zeros_like(starts)
                        ends_[:len(ends)] = ends
                        ends_[len(ends):] = len(labels[i_]) - 1
                        ends = ends_

                    for j in range(len(starts)):
                        if labels[i_][starts[j]+1] != self.special_tokens[1]:
                            labels[i_][starts[j]:ends[j]+2] = -100

            batch["labels"] = labels.clone()  # Add labels to the batch
            batch["advantage"] = torch.tensor(advantage[i*self.max_batch_size:(i+1)*self.max_batch_size], dtype=torch.float32)
            batch['rewards'] = torch.tensor(rewards[i*self.max_batch_size:(i+1)*self.max_batch_size], dtype=torch.float32)
            batches.append(batch)
        return batches

_spawn_context = mp

class NoDaemonProcess(_spawn_context.Process):
    @property
    def daemon(self):
        return False
    @daemon.setter
    def daemon(self, value):
        pass

class NoDaemonContext(type(mp.get_context())):
    Process = NoDaemonProcess
