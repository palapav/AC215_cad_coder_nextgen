#!/usr/bin/env python3
"""
Modal deployment script for the CAD-Coder LLaVA model (CADCODER/CAD-Coder).

This deployment uses:
- A100 40GB GPU for the 13B parameter model (~26GB VRAM)
- Flash Attention 2 for memory-efficient attention (via xformers)
- Token streaming for real-time output to frontend

Supports both GCP (GKE) and Modal Labs deployments.
The backend automatically routes to the appropriate infrastructure.

Typical workflow:
1. Ensure you have `modal` installed locally (`pip install modal`) and run `python -m modal setup`.
2. Create a persistent volume for the model cache:
     modal volume create cad-coder-llava-model
3. Deploy the app:
     modal deploy src/model_inference/llava_modal/modal_app.py
4. On first inference, the model will be downloaded from HuggingFace and cached.
5. The FastAPI service invokes the functions through Modal's Python client.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Optional, Generator

import modal


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
APP_NAME = os.environ.get("LLAVA_MODAL_APP", "cad-coder-llava")
HF_MODEL_PATH = os.environ.get("LLAVA_HF_MODEL", "CADCODER/CAD-Coder")
# Production default: 4096 tokens for full CAD code generation
MAX_NEW_TOKENS_DEFAULT = int(os.environ.get("LLAVA_MODAL_MAX_NEW_TOKENS", "4096"))
CONV_MODE = os.environ.get("LLAVA_CONV_MODE", "vicuna_v1")
MODEL_VOLUME_NAME = os.environ.get("LLAVA_MODAL_VOLUME", "cad-coder-llava-model")

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

# Copy the llava module and inference code into the container
LOCAL_LLAVA_DIR = Path(__file__).resolve().parent.parent  # model_inference directory


def _ignore_runtime_file(path: Path) -> bool:
    """Modal helper to skip large artifacts while copying."""
    if path.is_dir():
        skip_dirs = {"__pycache__", ".git", "docs", "docs_images", "inference", 
                     "test100_images", "test100_gt_steps", "qwen", "SolidAlign",
                     "model_inference"}
        if path.name in skip_dirs:
            return True
        return False
    if path.suffix == ".py":
        return False
    return True


# Build image with xformers for memory-efficient attention (Flash Attention alternative)
llava_image = (
    modal.Image.from_registry("pytorch/pytorch:2.1.2-cuda12.1-cudnn8-devel", add_python="3.10")
    .run_commands("pip install --upgrade pip")
    # Install xformers for memory-efficient attention (easier to install than flash-attn)
    .pip_install("xformers==0.0.23.post1")
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
        # Enable xformers memory efficient attention
        "XFORMERS_ENABLE_TRITON": "1",
    })
)


# ---------------------------------------------------------------------------
# Model Caching (initialized once per container)
# ---------------------------------------------------------------------------

_model_state = {
    "tokenizer": None,
    "model": None,
    "image_processor": None,
    "context_len": None,
    "initialized": False,
}


def _initialize_llava_model():
    """Initialize LLaVA model once per container with memory-efficient attention."""
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
    
    print("[LLaVA Modal] Initializing model with memory-efficient attention...")
    disable_torch_init()
    
    model_path = HF_MODEL_PATH
    model_name = model_path.split("/")[-1]
    
    # Ensure cache directory exists
    os.makedirs("/model_cache/hub", exist_ok=True)
    
    # Load model - will use xformers memory efficient attention if available
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
    
    print("[LLaVA Modal] ✓ Model initialized and cached")
    return tokenizer, model, image_processor, context_len


# ---------------------------------------------------------------------------
# GPU Function - Streaming Only (keeps 1 warm container)
# ---------------------------------------------------------------------------

@app.function(
    image=llava_image,
    gpu="A100",  # 40GB VRAM for LLaVA 13B
    timeout=900,
    scaledown_window=600,  # Keep container warm for 10 minutes
    min_containers=1,      # Always keep 1 container warm for fast response
    max_containers=1,      # Single container handles all requests
    volumes={"/model_cache": model_volume},
)
def llava_modal_infer_stream(
    prompt: str,
    image_bytes: Optional[bytes] = None,
    image_format: Optional[str] = None,
    max_new_tokens: int = MAX_NEW_TOKENS_DEFAULT,
    temperature: float = 0.0,
    top_p: float = 1.0,
) -> Generator[str, None, None]:
    """
    Streaming inference entrypoint (PRIMARY).
    Yields tokens as they are generated for real-time streaming to frontend.
    
    This is the preferred method for production use as it provides
    immediate feedback to users while the model generates.
    """
    import torch
    import threading
    from PIL import Image
    from transformers import TextIteratorStreamer
    
    from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN
    from llava.conversation import conv_templates
    from llava.mm_utils import tokenizer_image_token, process_images

    tokenizer, model, image_processor, context_len = _initialize_llava_model()
    
    # Process image (LLaVA preprocessing - CLIP-like)
    if image_bytes:
        buffer = io.BytesIO(image_bytes)
        pil_image = Image.open(buffer).convert("RGB")
    else:
        pil_image = Image.new("RGB", (336, 336), color=(0, 0, 0))

    image_tensor = process_images([pil_image], image_processor, model.config)[0]
    image_tensor = image_tensor.to(dtype=torch.float16, device="cuda")
    
    # Build conversation prompt
    conv = conv_templates[CONV_MODE].copy()
    
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
    
    # Set up streaming
    streamer = TextIteratorStreamer(
        tokenizer,
        skip_prompt=True,
        skip_special_tokens=True,
    )
    
    # Run generation in background thread
    def _generate():
        with torch.inference_mode():
            model.generate(
                input_ids,
                images=image_tensor.unsqueeze(0),
                image_sizes=[pil_image.size],
                do_sample=temperature > 0,
                temperature=temperature if temperature > 0 else None,
                top_p=top_p if temperature > 0 else None,
                max_new_tokens=max_new_tokens,
                use_cache=True,
                streamer=streamer,
            )
    
    thread = threading.Thread(target=_generate, daemon=True)
    thread.start()
    
    # Yield tokens as they're generated
    for text in streamer:
        yield text


# ---------------------------------------------------------------------------
# Local Entrypoint for Testing
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def main(
    prompt: str = "Generate the CadQuery code needed to create the CAD for the provided image. Just the code, no other words.",
    image_path: Optional[str] = None,
    max_new_tokens: int = MAX_NEW_TOKENS_DEFAULT,
    temperature: float = 0.0,
):
    """CLI for testing Modal inference."""
    if not image_path:
        print("Error: --image-path is required for LLaVA inference")
        return
    
    img_path = Path(image_path).expanduser().resolve()
    if not img_path.exists():
        raise FileNotFoundError(f"Image not found: {img_path}")
    
    image_bytes = img_path.read_bytes()
    image_format = img_path.suffix.replace(".", "").upper()

    print("------ CAD-Coder LLaVA (GCP/Modal Labs) Output ------")
    
    for chunk in llava_modal_infer_stream.remote_gen(
        prompt=prompt,
        image_bytes=image_bytes,
        image_format=image_format,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
    ):
        print(chunk, end="", flush=True)
    print()
