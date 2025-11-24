#!/usr/bin/env python3
"""Model loading utilities with memory-efficient optimizations"""
import torch
from transformers import AutoModelForImageTextToText, AutoProcessor, AutoConfig


def load_model(
    model_name: str,
    torch_dtype=torch.bfloat16,
    device_map="cpu",
    quantization_config=None,
    use_flash_attention=None,
):
    """
    Load vision-language model with automatic fallbacks.
    
    Args:
        model_name: HuggingFace model name
        torch_dtype: Data type (default: bfloat16)
        device_map: Device placement (default: "cpu" for FSDP)
        quantization_config: Optional quantization
        use_flash_attention: Flash Attention 2 (None=auto, True=try, False=disable)
    
    Returns:
        Loaded model
    """
    model_kwargs = {
        "torch_dtype": torch_dtype,
        "device_map": device_map,
    }
    
    if quantization_config is not None:
        model_kwargs["quantization_config"] = quantization_config
    
    # Handle Flash Attention (optional, won't fail if not available)
    if use_flash_attention is None:
        # Auto-detect: try to use if available, silently fallback if not
        try:
            import flash_attn
            model_kwargs["attn_implementation"] = "flash_attention_2"
            print("✓ Flash Attention 2 enabled")
        except ImportError:
            pass  # Silently use standard attention
    elif use_flash_attention:
        # Explicitly requested: try but don't fail
        try:
            import flash_attn
            model_kwargs["attn_implementation"] = "flash_attention_2"
            print("✓ Flash Attention 2 enabled")
        except ImportError:
            print("ℹ️ Flash Attention 2 not available, using standard attention")
    
    # Try to load model with automatic class detection
    try:
        # First try Qwen3VL (newest)
        from transformers import Qwen3VLForConditionalGeneration
        model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_name,
            **model_kwargs
        )
        print(f"✓ Loaded Qwen3VLForConditionalGeneration")
        return model
    except (ImportError, AttributeError, ValueError, RuntimeError) as e:
        # Try Qwen2VL
        try:
            from transformers import Qwen2VLForConditionalGeneration
            model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_name,
                **model_kwargs
            )
            print(f"✓ Loaded Qwen2VLForConditionalGeneration")
            return model
        except (ImportError, AttributeError, ValueError, RuntimeError) as e2:
            # Try generic AutoModel
            try:
                model = AutoModelForImageTextToText.from_pretrained(
                    model_name,
                    **model_kwargs
                )
                print(f"✓ Loaded AutoModelForImageTextToText")
                return model
            except Exception as e3:
                # Last resort: remove flash attention and try again
                if "attn_implementation" in model_kwargs:
                    print(f"ℹ️ Retrying without flash attention")
                    model_kwargs.pop("attn_implementation")
                    model = AutoModelForImageTextToText.from_pretrained(
                        model_name,
                        **model_kwargs
                    )
                    print(f"✓ Loaded AutoModelForImageTextToText (standard attention)")
                    return model
                raise


def freeze_vision_encoder(model):
    """Freeze vision encoder parameters (saves ~40% memory)."""
    for attr in ['visual', 'vision_model', 'vision_encoder', 'vision_tower', 'vision']:
        if hasattr(model, attr):
            getattr(model, attr).requires_grad_(False)
            print(f"✓ Froze vision encoder: {attr}")
            return
    print("⚠️  No vision encoder found")


def get_quantization_config(load_in_4bit=False, load_in_8bit=False):
    """Get BitsAndBytes quantization config."""
    if load_in_4bit:
        try:
            from transformers import BitsAndBytesConfig
            print("✓ Using 4-bit quantization (NF4)")
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        except ImportError:
            print("⚠️  bitsandbytes not available")
    elif load_in_8bit:
        try:
            from transformers import BitsAndBytesConfig
            print("✓ Using 8-bit quantization")
            return BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0
            )
        except ImportError:
            print("⚠️  bitsandbytes not available")
    return None


def load_checkpoint_into_model(model, checkpoint_path):
    """Load checkpoint state dict into model."""
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    
    if 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    elif 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']
    else:
        state_dict = checkpoint
    
    # Load state dict
    # Note: When using device_map="auto", the model is distributed across devices
    # and we shouldn't manually move it - accelerate handles device placement
    missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
    
    print(f"✓ Loaded checkpoint: {checkpoint_path}")
    if missing_keys:
        print(f"  Missing keys (first 10): {list(missing_keys)[:10]}")
    if unexpected_keys:
        print(f"  Unexpected keys (first 10): {list(unexpected_keys)[:10]}")
