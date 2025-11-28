#!/usr/bin/env python3
"""
Evaluate a trained model on the test dataset using CADRL metrics.
Computes IOU scores, VSR, and error rates.
"""
import os
import sys
import argparse
import json
import torch
import numpy as np
from collections import OrderedDict
from datasets import load_from_disk
from transformers import AutoProcessor
from tqdm import tqdm

# Add CADRL to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CADRL'))

from utils.model_utils import load_model, load_checkpoint_into_model
from utils.config import DEFAULT_MODEL, DATA_PATHS, WANDB_DEFAULTS, EVALUATION_DEFAULTS

from Inference.processors import IOUProcessor
from Inference import extract_code
from DataUtils.Collators import QwenVLCollator
from DataUtils.Datasets import MinimalImageCADDataset
from qwen_vl_utils import process_vision_info


def generate_code(model, processor, image, max_new_tokens=4096, temperature=1.0):
    """Generate code from a model given an image (single sample)."""
    return generate_code_batch(model, processor, [image], max_new_tokens, temperature)[0]


def generate_code_batch(model, processor, images, max_new_tokens=4096, temperature=1.0):
    """Generate code from a model given a batch of images."""
    # Create messages for each image
    messages_list = []
    for image in images:
        messages_list.append([
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": "Generate the CADQuery code needed to create the CAD for the provided image."}
                ]
            }
        ])
    
    # Process all messages
    texts = processor.apply_chat_template(messages_list, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages_list)
    
    # Batch process all inputs
    inputs = processor(
        text=texts,
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt"
    )
    
    # Get device from model (handle multi-GPU case)
    if hasattr(model, 'device'):
        device = model.device
    else:
        device = next(model.parameters()).device
    
    inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
    
    # Optimize generation settings
    generation_kwargs = {
        "max_new_tokens": max_new_tokens,
        "use_cache": True,  # Enable KV cache for faster generation
        "pad_token_id": processor.tokenizer.pad_token_id or processor.tokenizer.eos_token_id,
    }
    
    # Use greedy decoding for speed when temperature is 0 or very low
    if temperature <= 0.01:
        generation_kwargs["do_sample"] = False
    else:
        generation_kwargs["temperature"] = temperature
        generation_kwargs["do_sample"] = True
    
    # Use inference_mode for better performance (faster than no_grad)
    with torch.inference_mode():
        generated_ids = model.generate(
            **inputs,
            **generation_kwargs
        )
    
    # Trim input tokens from generated tokens
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)
    ]
    generated_texts = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )
    
    return generated_texts


def compute_metrics(iou_scores, status_codes, n_samples):
    """Compute evaluation metrics from IOU scores."""
    iou_scores = np.array(iou_scores).reshape(-1, n_samples)
    status_codes = np.array(status_codes).reshape(-1, n_samples)
    
    # Best of N metrics
    best_iou = iou_scores.max(axis=1)
    best_VSR = np.sum(best_iou >= 0) / len(best_iou)
    best_mean = np.mean(best_iou[best_iou >= 0]) if np.any(best_iou >= 0) else 0.0
    best_median = np.median(best_iou[best_iou >= 0]) if np.any(best_iou >= 0) else 0.0
    best_mean_adj = np.mean(np.where(best_iou >= 0, best_iou, 0))
    
    # Full set metrics
    mean_iou = np.mean(iou_scores[iou_scores >= 0]) if np.any(iou_scores >= 0) else 0.0
    median_iou = np.median(iou_scores[iou_scores >= 0]) if np.any(iou_scores >= 0) else 0.0
    mean_iou_adj = np.mean(np.where(iou_scores >= 0, iou_scores, 0))
    VSR = np.sum(iou_scores >= 0) / len(iou_scores) / n_samples
    
    # Error analysis
    total = len(status_codes) * n_samples
    errors = {
        'Failed GT (%)': np.sum(status_codes == 1) / total * 100,
        'Failed Gen (%)': np.sum(status_codes == 2) / total * 100,
        'Failed OCC (%)': np.sum(status_codes == 3) / total * 100,
        'Timeouts (%)': np.sum(status_codes == 4) / total * 100,
        'None Solids (%)': np.sum(status_codes == 5) / total * 100,
        'Failed Processing (%)': np.sum(status_codes == 6) / total * 100
    }
    
    return {
        'Best of N': {
            'Valid Sample Rate (%)': best_VSR * 100,
            'Mean IOU': float(best_mean),
            'Median IOU': float(best_median),
            'Mean IOU (Adjusted)': float(best_mean_adj)
        },
        'Full Set': {
            'Valid Sample Rate (%)': VSR * 100,
            'Mean IOU': float(mean_iou),
            'Median IOU': float(median_iou),
            'Mean IOU (Adjusted)': float(mean_iou_adj)
        },
        'Error Analysis': errors
    }


# ... (Keep your existing imports and helper functions: generate_code, compute_metrics, etc.)

def main():
    parser = argparse.ArgumentParser(description="Evaluate model on test dataset")
    
    # Model and data
    parser.add_argument("--model_path", type=str, required=False, default=None,
                       help="Path to model checkpoint or HuggingFace model")
    parser.add_argument("--base_model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--test_data_dir", type=str, default=DATA_PATHS["test"])
    
    # Performance Optimizations
    parser.add_argument("--load_in_4bit", action="store_true", help="Load model in 4-bit quantization to speed up inference and save memory")
    parser.add_argument("--no_compile", action="store_true", help="Disable torch.compile if it causes errors")
    
    # Generation parameters
    parser.add_argument("--max_new_tokens", type=int, default=EVALUATION_DEFAULTS["max_new_tokens"])
    parser.add_argument("--temperature", type=float, default=EVALUATION_DEFAULTS["temperature"])
    parser.add_argument("--n_samples", type=int, default=EVALUATION_DEFAULTS["n_samples"])
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--max_test_samples", type=int, default=None,
                        help="Limit evaluation to the first N samples for quick tests")
    
    # IOU computation
    parser.add_argument("--n_workers", type=int, default=EVALUATION_DEFAULTS["n_workers"])
    parser.add_argument("--timeout", type=int, default=EVALUATION_DEFAULTS["timeout"])
    
    # Output
    parser.add_argument("--output_path", type=str, default=None)
    
    args = parser.parse_args()
    
    # Load processor
    print(f"Loading processor from: {args.base_model}")
    processor = AutoProcessor.from_pretrained(args.base_model)
    
    print(f"Loading model from: {args.model_path}")
    
    # --- OPTIMIZATION 1: Dtype and Flash Attention Configuration ---
    # FlashAttention requires float16 or bfloat16.
    # We prefer bfloat16 for Ampere+ GPUs (A100, H100, RTX 30/40 series)
    torch_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    
    # Check if we're loading a checkpoint - if so, we can't use quantization initially
    if args.model_path is None:
        loading_checkpoint = False
    else:
        loading_checkpoint = args.model_path.endswith('.pt') and os.path.exists(args.model_path)
    
    # --- OPTIMIZATION 2: 4-bit Quantization ---
    # NOTE: Can't use quantization when loading checkpoints - weights shapes don't match
    quantization_config = None
    if args.load_in_4bit and not loading_checkpoint:
        from transformers import BitsAndBytesConfig
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch_dtype,
            bnb_4bit_quant_type="nf4",
        )
        print("⚡ Quantization enabled: Loading in 4-bit (NF4)")
    elif args.load_in_4bit and loading_checkpoint:
        print("⚠️  Warning: 4-bit quantization disabled when loading checkpoint (incompatible with checkpoint weights)")

    # Load the model using the custom loader (it handles flash attention internally)
    # use_flash_attention=True enables flash attention, None=auto-detect
    model = load_model(
        args.base_model,
        torch_dtype=torch_dtype,
        device_map="auto",
        quantization_config=quantization_config,
        use_flash_attention=True
    )

    # Load checkpoint if it's a state dict file
    # IMPORTANT: Must load checkpoint BEFORE applying quantization
    if loading_checkpoint:
        print("Loading checkpoint weights...")
        load_checkpoint_into_model(model, args.model_path)
        
        # After loading checkpoint, we can't apply quantization (weights already loaded)
        if args.load_in_4bit:
            print("⚠️  Note: Checkpoint loaded without quantization. For quantized inference, save quantized checkpoints separately.")
    
    model.eval()
    
    # Verify Flash Attention status
    if hasattr(model, 'config') and hasattr(model.config, '_attn_implementation'):
        attn_impl = getattr(model.config, '_attn_implementation', None) or getattr(model.config, 'attn_implementation', None)
        if attn_impl == "flash_attention_2":
            print("✓ Flash Attention 2 is active in model")
        else:
            print(f"ℹ️  Attention implementation: {attn_impl or 'default'}")
    
    # --- OPTIMIZATION 3: Torch Compile ---
    # This fuses kernels and speeds up the loop significantly for long sequences
    if not args.no_compile:
        print("⚡ Compiling model with torch.compile (this takes a minute at startup but speeds up generation)...")
        try:
            model = torch.compile(model, mode="max-autotune")
        except Exception as e:
            print(f"⚠️  torch.compile failed (ignoring): {e}")

    # Print model device info for debugging
    if hasattr(model, 'hf_device_map'):
        print(f"Model device map: {model.hf_device_map}")
    else:
        device = next(model.parameters()).device
        print(f"Model on device: {device}")
    
    print(f"Generation settings: max_new_tokens={args.max_new_tokens}, temperature={args.temperature}, n_samples={args.n_samples}")
    
    # Load test dataset
    print(f"Loading test dataset from: {args.test_data_dir}")
    test_data = load_from_disk(args.test_data_dir)
    
    if 'code' not in test_data.column_names and 'cadquery' in test_data.column_names:
        test_data = test_data.map(lambda x: {'code': x['cadquery']})
    
    if args.max_test_samples is not None:
        limit = min(args.max_test_samples, len(test_data))
        print(f"Limiting test dataset to {limit} samples (from {len(test_data)})")
        test_data = test_data.select(range(limit))

    print(f"Test dataset size: {len(test_data)}")
    
    # Generate code for all test samples (batched)
    print(f"Generating code with batch_size={args.batch_size}...")
    generated_texts = []
    ground_truths = []
    
    # Collect valid samples first
    valid_samples = []
    for i in range(len(test_data)):
        sample = test_data[i]
        image = sample.get('image')
        if image is not None:
            valid_samples.append((i, sample))
    
    print(f"Processing {len(valid_samples)} valid samples in batches of {args.batch_size}")
    
    # Process in batches
    for batch_start in tqdm(range(0, len(valid_samples), args.batch_size), desc="Batches"):
        batch_end = min(batch_start + args.batch_size, len(valid_samples))
        batch_samples = valid_samples[batch_start:batch_end]
        
        # For each sample in batch, generate n_samples
        batch_images = []
        batch_gt_codes = []
        batch_sample_indices = []
        
        for idx, (orig_idx, sample) in enumerate(batch_samples):
            image = sample.get('image')
            gt_code = sample.get('code', '')
            
            for _ in range(args.n_samples):
                batch_images.append(image)
                batch_gt_codes.append(gt_code)
                batch_sample_indices.append(orig_idx)
        
        # Generate for entire batch at once
        try:
            batch_generated = generate_code_batch(
                model, processor, batch_images,
                max_new_tokens=args.max_new_tokens,
                temperature=args.temperature
            )
        except Exception as e:
            print(f"Error generating for batch starting at index {batch_start}: {e}")
            # Create empty strings on failure to keep alignment
            batch_generated = [""] * len(batch_images)
        
        # Group results back by original sample
        batch_results = OrderedDict()
        for orig_idx, gt_code, gen_text in zip(batch_sample_indices, batch_gt_codes, batch_generated):
            if orig_idx not in batch_results:
                batch_results[orig_idx] = {
                    'generations': [],
                    'gt_code': gt_code
                }
            batch_results[orig_idx]['generations'].append(gen_text)
        
        for orig_idx in batch_results.keys():
            generated_texts.append(batch_results[orig_idx]['generations'])
            ground_truths.append(batch_results[orig_idx]['gt_code'])
    
    # Extract code and prepare for IOU computation
    print("Extracting code from generated text...")
    final_set = []
    for gt, gens in zip(ground_truths, generated_texts):
        for gen in gens:
            final_set.append({
                'ground_truth': gt,
                'generated': extract_code(gen)
            })
    
    # Compute IOU scores
    print("Computing IOU scores...")
    iou_processor = IOUProcessor(num_workers=args.n_workers, timeout=args.timeout)
    iou_scores, status_codes = iou_processor(final_set)
    
    # Compute metrics
    results = compute_metrics(iou_scores, status_codes, args.n_samples)
    
    # Print results
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    for section, metrics in results.items():
        print(f"\n{section}:")
        for key, value in metrics.items():
            print(f"  {key}: {value:.4f}")
    
    # Save results
    if args.output_path:
        os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
        with open(args.output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output_path}")
    
    print("\n✅ Evaluation complete!")

if __name__ == "__main__":
    main()