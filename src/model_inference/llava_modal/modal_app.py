#!/usr/bin/env python3
"""
Modal deployment script for the CAD-Coder LLaVA model (CADCODER/CAD-Coder).

This file defines a GPU-backed Modal function that loads the LLaVA model
and exposes a remote entrypoint for CAD code generation.

The CAD-Coder model is a fine-tuned LLaVA-v1.5-13b model hosted on HuggingFace.
It requires approximately 26GB VRAM, so we use an A100 40GB GPU.

Typical workflow:
1. Ensure you have `modal` installed locally (`pip install modal`) and run `python -m modal setup`.
2. Create a persistent volume for the model cache (optional - will be created automatically):
     modal volume create cad-coder-llava-model
3. Deploy the app:
     modal deploy src/model_inference/llava_modal/modal_app.py
4. On first inference, the model will be downloaded from HuggingFace and cached in the volume.
   Subsequent inferences will use the cached model, even after container restarts.
5. The FastAPI service invokes the `llava_modal_infer` function through Modal's Python client.

Note: The model cache is stored in a persistent Modal volume, so you don't need to
re-download the model after redeploying containers. The first inference will take
longer (~5-10 minutes) to download the ~26GB model, but subsequent calls will be fast.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Optional

import modal


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
APP_NAME = os.environ.get("LLAVA_MODAL_APP", "cad-coder-llava")
# The CAD-Coder model is hosted on HuggingFace
HF_MODEL_PATH = os.environ.get("LLAVA_HF_MODEL", "CADCODER/CAD-Coder")
MAX_NEW_TOKENS_DEFAULT = int(os.environ.get("LLAVA_MODAL_MAX_NEW_TOKENS", "3450"))
CONV_MODE = os.environ.get("LLAVA_CONV_MODE", "vicuna_v1")
MODEL_VOLUME_NAME = os.environ.get("LLAVA_MODAL_VOLUME", "cad-coder-llava-model")

app = modal.App(APP_NAME)
# Create persistent volume for HuggingFace model cache
model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

# Copy the llava module and inference code into the container
LOCAL_LLAVA_DIR = Path(__file__).resolve().parent.parent  # model_inference directory


def _ignore_runtime_file(path: Path) -> bool:
    """Modal helper to skip large artifacts while copying.
    
    Only includes Python source files - images and checkpoints are not needed
    since all images come from API/frontend.
    """
    if path.is_dir():
        # Skip specific directories we don't need
        skip_dirs = {"__pycache__", ".git", "docs", "docs_images", "inference", 
                     "test100_images", "test100_gt_steps", "qwen", "SolidAlign"}
        if path.name in skip_dirs:
            return True
        return False
    # Include only Python files
    if path.suffix == ".py":
        return False
    # Skip everything else
    return True


llava_image = (
    modal.Image.from_registry("pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime", add_python="3.10")
    .run_commands("pip install --upgrade pip")
    .pip_install(
        # Core ML dependencies
        "torch==2.1.2",
        "torchvision==0.16.2",
        "transformers==4.37.2",
        "tokenizers==0.15.1",
        "sentencepiece==0.1.99",
        "accelerate==0.21.0",
        "peft",
        "bitsandbytes",
        # LLaVA specific
        "einops==0.6.1",
        "einops-exts==0.0.4",
        "timm==0.6.13",
        "shortuuid",
        # Utilities
        "pillow",
        "numpy",
        "pydantic",
        "requests",
        "httpx==0.24.0",
    )
    .add_local_dir(
        LOCAL_LLAVA_DIR,
        remote_path="/app/model_inference",
        ignore=_ignore_runtime_file,
        copy=True,
    )
    .env({
        "PYTHONPATH": "/app/model_inference",
        "HF_HOME": "/model_cache",
        "TRANSFORMERS_CACHE": "/model_cache",
        "HF_HUB_CACHE": "/model_cache/hub",
    })
)


# ---------------------------------------------------------------------------
# Model caching (module-level globals - initialized once per container)
# ---------------------------------------------------------------------------

# Global model state (initialized once per container)
_model_state = {
    "tokenizer": None,
    "model": None,
    "image_processor": None,
    "context_len": None,
    "initialized": False,
}


def _initialize_llava_model():
    """Initialize LLaVA model once per container (cached in module-level globals)."""
    global _model_state
    
    if _model_state["initialized"]:
        return (
            _model_state["tokenizer"],
            _model_state["model"],
            _model_state["image_processor"],
            _model_state["context_len"],
        )
    
    import torch
    from llava.model.builder import load_pretrained_model
    from llava.utils import disable_torch_init
    
    print("[LLaVA Modal] Initializing model (first call in this container)...")
    disable_torch_init()
    
    model_path = HF_MODEL_PATH
    model_name = model_path.split("/")[-1]
    
    # Ensure cache directory exists in volume
    os.makedirs("/model_cache/hub", exist_ok=True)
    
    # Load model - will download to /model_cache on first call, then use cached version
    # Modal volumes automatically persist changes, so the model cache will survive container restarts
    tokenizer, model, image_processor, context_len = load_pretrained_model(
        model_path=model_path,
        model_base=None,
        model_name=model_name,
        load_8bit=False,
        load_4bit=False,
    )
    
    # Cache the model state
    _model_state["tokenizer"] = tokenizer
    _model_state["model"] = model
    _model_state["image_processor"] = image_processor
    _model_state["context_len"] = context_len
    _model_state["initialized"] = True
    
    print("[LLaVA Modal] ✓ Model initialized and cached (will reuse for subsequent calls)")
    
    return tokenizer, model, image_processor, context_len


# ---------------------------------------------------------------------------
# Remote GPU function
# ---------------------------------------------------------------------------

@app.function(
    image=llava_image,
    gpu="A100",  # LLaVA 13B requires ~26GB VRAM
    timeout=900,
    scaledown_window=600,
    min_containers=1,
    max_containers=1,
    volumes={"/model_cache": model_volume},
)
def llava_modal_infer(
    prompt: str,
    image_bytes: Optional[bytes] = None,
    image_format: Optional[str] = None,
    max_new_tokens: int = MAX_NEW_TOKENS_DEFAULT,
    temperature: float = 0.0,
    top_p: float = 1.0,
) -> str:
    """
    Remote inference entrypoint executed on a GPU worker.

    The model is initialized once per container on the first call and cached
    in module-level globals for subsequent calls.

    Args:
        prompt: Natural language prompt for CAD code generation.
        image_bytes: Raw bytes of an RGB image (PNG/JPEG).
        image_format: Optional hint for Pillow (defaults to PNG).
        max_new_tokens: Generation cap (defaults to 3450).
        temperature: Sampling temperature (0 => greedy).
        top_p: Top-p sampling parameter.
    """
    import torch
    from PIL import Image
    
    from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN
    from llava.conversation import conv_templates, SeparatorStyle
    from llava.mm_utils import tokenizer_image_token, process_images

    # Get cached model (initialized once per container)
    tokenizer, model, image_processor, context_len = _initialize_llava_model()
    
    # Process image if provided
    if image_bytes:
        buffer = io.BytesIO(image_bytes)
        pil_image = Image.open(buffer).convert("RGB")
        image_tensor = process_images([pil_image], image_processor, model.config)[0]
        image_tensor = image_tensor.to(dtype=torch.float16, device="cuda")
    else:
        # No image provided - return error
        return "Error: CAD-Coder LLaVA requires an image input."
    
    # Build conversation prompt
    conv = conv_templates[CONV_MODE].copy()
    
    # Prepend image token
    if model.config.mm_use_im_start_end:
        from llava.constants import DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN
        inp = DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN + "\n" + prompt
    else:
        inp = DEFAULT_IMAGE_TOKEN + "\n" + prompt
    
    conv.append_message(conv.roles[0], inp)
    conv.append_message(conv.roles[1], None)
    full_prompt = conv.get_prompt()
    
    # Tokenize
    input_ids = tokenizer_image_token(
        full_prompt, 
        tokenizer, 
        IMAGE_TOKEN_INDEX, 
        return_tensors="pt"
    ).unsqueeze(0).cuda()
    
    # Generate
    with torch.inference_mode():
        output_ids = model.generate(
            input_ids,
            images=image_tensor.unsqueeze(0),
            image_sizes=[pil_image.size],
            do_sample=True if temperature > 0 else False,
            temperature=temperature if temperature > 0 else None,
            top_p=top_p if temperature > 0 else None,
            max_new_tokens=max_new_tokens,
            use_cache=True,
        )
    
    # Decode output
    outputs = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
    
    return outputs


# ---------------------------------------------------------------------------
# Local helper entrypoints
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def main(
    prompt: str = "Generate the CadQuery code needed to create the CAD for the provided image. Just the code, no other words.",
    image_path: Optional[str] = None,
    max_new_tokens: int = MAX_NEW_TOKENS_DEFAULT,
    temperature: float = 0.0,
):
    """Quick CLI for sanity checking Modal inference."""
    if not image_path:
        print("Error: --image-path is required for LLaVA inference")
        return
    
    img_path = Path(image_path).expanduser().resolve()
    if not img_path.exists():
        raise FileNotFoundError(f"Image not found: {img_path}")
    
    image_bytes = img_path.read_bytes()
    image_format = img_path.suffix.replace(".", "").upper()

    result = llava_modal_infer.remote(
        prompt=prompt,
        image_bytes=image_bytes,
        image_format=image_format,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
    )
    print("------ CAD-Coder LLaVA (Modal) Output ------")
    print(result)

