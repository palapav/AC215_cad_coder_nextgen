#!/usr/bin/env python3
"""Patches for accelerate compatibility"""
import accelerate.utils.other
import accelerate.accelerator


def apply_accelerate_patches():
    """Apply patches to accelerate for better compatibility."""
    
    # Patch extract_model_from_parallel
    def patched_extract_model_from_parallel(model, keep_fp32_wrapper=False, keep_torch_compile=False):
        """Simple unwrap for model extraction."""
        if hasattr(model, 'module'):
            return model.module
        return model
    
    accelerate.utils.other.extract_model_from_parallel = patched_extract_model_from_parallel
    
    # Patch unwrap_model
    _original_unwrap = accelerate.accelerator.Accelerator.unwrap_model
    
    def patched_unwrap_model(self, model, keep_fp32_wrapper=False, keep_torch_compile=False):
        """Patched unwrap_model with fallback."""
        try:
            return _original_unwrap(self, model, keep_fp32_wrapper, keep_torch_compile)
        except Exception:
            if hasattr(model, 'module'):
                return model.module
            return model
    
    accelerate.accelerator.Accelerator.unwrap_model = patched_unwrap_model
