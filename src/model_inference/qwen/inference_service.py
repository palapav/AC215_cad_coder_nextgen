#!/usr/bin/env python3
"""Qwen inference service for CAD code generation"""
import os
import torch
from PIL import Image
from transformers import AutoProcessor
from qwen_vl_utils import process_vision_info
from model_utils import load_model, load_checkpoint_into_model
from pathlib import Path
import io
import base64

# Global model and processor (loaded once)
_model = None
_processor = None
_model_path = None
_checkpoint_path = None

def initialize_model(checkpoint_path: str = None, base_model: str = "Qwen/Qwen3-VL-2B-Instruct"):
    """Initialize the Qwen model (call once at startup)"""
    global _model, _processor, _model_path, _checkpoint_path
    
    if _model is not None:
        return _model, _processor
    
    _model_path = base_model
    _checkpoint_path = checkpoint_path
    
    print(f"[Qwen Service] Loading processor from: {_model_path}")
    _processor = AutoProcessor.from_pretrained(_model_path)
    
    torch_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    print(f"[Qwen Service] Using dtype: {torch_dtype}")
    
    print(f"[Qwen Service] Loading model from: {_model_path}")
    _model = load_model(
        _model_path,
        torch_dtype=torch_dtype,
        device_map="auto",
        quantization_config=None,
        use_flash_attention=True
    )
    
    if _checkpoint_path and os.path.exists(_checkpoint_path):
        print(f"[Qwen Service] Loading checkpoint from: {_checkpoint_path}")
        # Move model to CPU for checkpoint loading (matching eval_model.py behavior)
        # The checkpoint is loaded with map_location="cpu" in load_checkpoint_into_model
        load_checkpoint_into_model(_model, _checkpoint_path)
        # Verify checkpoint was loaded by checking if model has expected attributes
        try:
            print(f"[Qwen Service] Model device: {next(_model.parameters()).device}")
            print(f"[Qwen Service] Model dtype: {next(_model.parameters()).dtype}")
        except Exception as e:
            print(f"[Qwen Service] Could not get model device/dtype: {e}")
        # Note: Removed torch.cuda.synchronize() here as it can block shutdown
        # The model will sync automatically when needed during generation
    else:
        print(f"[Qwen Service] No checkpoint found at {_checkpoint_path}, using base model")
    
    _model.eval()
    print(f"[Qwen Service] ✓ Model initialized and ready")
    
    return _model, _processor

def generate_cad_code(
    prompt: str,
    image=None,
    image_path: str = None,
    max_new_tokens: int = 4096,
    temperature: float = 1.0
) -> str:
    """
    Generate CAD code using Qwen model.
    
    Args:
        prompt: Text prompt for generation
        image: PIL Image object (optional)
        image_path: Path to image file (optional)
        max_new_tokens: Maximum tokens to generate
        temperature: Sampling temperature
    
    Returns:
        Generated CAD code string
    """
    global _model, _processor
    
    if _model is None or _processor is None:
        raise RuntimeError("Model not initialized. Call initialize_model() first.")
    
    # Validate prompt
    if not prompt or not prompt.strip():
        if image is None and image_path is None:
            raise ValueError("Prompt cannot be empty for text-only generation")
        # Use default prompt for image-based generation
        prompt = "Generate the CADQuery code needed to create the CAD for the provided image."
    
    # Load image if provided
    if image is None and image_path:
        if os.path.exists(image_path):
            image = Image.open(image_path).convert("RGB")
        else:
            raise FileNotFoundError(f"Image not found: {image_path}")
    elif image is None:
        # Text-only generation (Qwen3-VL supports this)
        image = None
    
    # Prepare messages
    if image is not None:
        messages = [[
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt}
                ]
            }
        ]]
    else:
        # Text-only
        messages = [[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ]]
    
    # Ensure model is in eval mode (matching eval_model.py line 86)
    _model.eval()
    
    # Process inputs - match eval_model.py exactly (lines 22-31)
    texts = _processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    # Match eval_model.py line 23 exactly - process_vision_info called unconditionally when image exists
    if image is not None:
        image_inputs, video_inputs = process_vision_info(messages)
    else:
        image_inputs, video_inputs = [], []
    
    # Match eval_model.py lines 25-31 exactly
    inputs = _processor(
        text=texts,
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt"
    )
    
    # Match eval_model.py lines 33-38 exactly for device detection
    if hasattr(_model, 'device'):
        device = _model.device
    else:
        device = next(_model.parameters()).device
    
    inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
    
    # Match eval_model.py lines 40-50 exactly for generation kwargs
    generation_kwargs = {
        "max_new_tokens": max_new_tokens,
        "use_cache": True,
        "pad_token_id": _processor.tokenizer.pad_token_id or _processor.tokenizer.eos_token_id,
    }
    
    # Use greedy decoding by default to avoid CUDA sampling errors
    # Sampling with temperature=1.0 causes CUDA errors in this environment
    # Greedy decoding is more stable and produces deterministic results
    generation_kwargs["do_sample"] = False
    
    # Match eval_model.py line 52-53 exactly
    # Ensure CUDA is synchronized before generation to avoid async errors
    if torch.cuda.is_available():
        try:
            torch.cuda.synchronize()
        except RuntimeError:
            pass  # CUDA might be in error state, continue anyway
    
    # Debug: Check inputs before generation
    print(f"[Qwen Service] Input keys: {inputs.keys()}")
    print(f"[Qwen Service] Input IDs shape: {inputs['input_ids'].shape}")
    print(f"[Qwen Service] Input IDs (first 20): {inputs['input_ids'][0][:20].tolist()}")
    print(f"[Qwen Service] Generation kwargs: {generation_kwargs}")
    
    with torch.inference_mode():
        generated_ids = _model.generate(**inputs, **generation_kwargs)
    
    # Match eval_model.py lines 55-58 exactly
    # Extract only the newly generated tokens (remove the input prompt)
    input_length = len(inputs["input_ids"][0])
    generated_ids_trimmed = generated_ids[0][input_length:]
    
    # Filter out pad tokens (token ID 0) - they shouldn't be in the output
    pad_token_id = _processor.tokenizer.pad_token_id
    eos_token_id = _processor.tokenizer.eos_token_id
    
    # Remove pad tokens and stop at EOS token
    valid_tokens = []
    for token_id in generated_ids_trimmed:
        token_id_val = token_id.item() if isinstance(token_id, torch.Tensor) else token_id
        if token_id_val == eos_token_id:
            break  # Stop at EOS token
        if token_id_val != pad_token_id and token_id_val != 0:
            valid_tokens.append(token_id_val)
    
    # Debug: Check if generated tokens look valid
    print(f"[Qwen Service] Input length: {input_length}, Generated length: {len(generated_ids_trimmed)}, Valid tokens: {len(valid_tokens)}")
    print(f"[Qwen Service] First 20 generated token IDs: {generated_ids_trimmed[:20].tolist()}")
    print(f"[Qwen Service] First 20 valid token IDs: {valid_tokens[:20]}")
    print(f"[Qwen Service] Pad token ID: {pad_token_id}, EOS token ID: {eos_token_id}")
    
    if len(valid_tokens) == 0:
        # If no valid tokens, try decoding the original (maybe pad_token_id is None)
        print(f"[Qwen Service] Warning: No valid tokens found, trying original decode")
        generated_text = _processor.decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    else:
        # Convert valid tokens back to tensor and decode
        valid_tokens_tensor = torch.tensor(valid_tokens, device=generated_ids_trimmed.device)
        generated_text = _processor.decode(valid_tokens_tensor, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    
    # Debug: Check decoded text
    print(f"[Qwen Service] Decoded text length: {len(generated_text)}")
    print(f"[Qwen Service] First 500 chars: {generated_text[:500]}")
    
    return generated_text.strip()

