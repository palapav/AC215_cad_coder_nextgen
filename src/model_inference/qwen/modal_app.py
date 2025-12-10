#!/usr/bin/env python3
"""
Modal deployment script for the fine-tuned Qwen-3 CAD-Coder model.

This deployment uses:
- A10G GPU (24GB VRAM) for fast inference
- Flash Attention 2 for memory-efficient attention
- Token streaming for real-time output to frontend

Supports both GCP (GKE) and Modal Labs deployments.
The backend automatically routes to the appropriate infrastructure.

Typical workflow:
1. Ensure you have `modal` installed locally (`pip install modal`) and run `python -m modal setup`.
2. Create a persistent volume and upload the fine-tuned checkpoint:
     modal volume create cad-coder-qwen3-model
     modal volume put cad-coder-qwen3-model src/model_inference/qwen/final_model.pt:/final_model.pt
3. Deploy the app:
     modal deploy src/model_inference/qwen/modal_app.py
4. The FastAPI service invokes the functions through Modal's Python client.
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
APP_NAME = os.environ.get("QWEN_MODAL_APP", "cad-coder-qwen3")
MODEL_VOLUME_NAME = os.environ.get("QWEN_MODAL_VOLUME", "cad-coder-qwen3-model")
CHECKPOINT_FILENAME = os.environ.get("QWEN_MODAL_CHECKPOINT", "final_model.pt")
BASE_MODEL = os.environ.get("QWEN_BASE_MODEL", "Qwen/Qwen3-VL-2B-Instruct")
# Production default: 4096 tokens for full CAD code generation
MAX_NEW_TOKENS_DEFAULT = int(os.environ.get("QWEN_MODAL_MAX_NEW_TOKENS", "4096"))
CHECKPOINT_PATH = f"/model/{CHECKPOINT_FILENAME}"

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

# Copy only the lightweight python sources into the container
LOCAL_QWEN_DIR = Path(__file__).resolve().parent


def _ignore_runtime_file(path: Path) -> bool:
    """Modal helper to skip large artifacts while copying."""
    if path.is_dir():
        return False
    if path.suffix == ".py":
        return False
    return True


# Build image with Flash Attention for fast inference
qwen_image = (
    modal.Image.from_registry("pytorch/pytorch:2.4.0-cuda12.4-cudnn9-devel", add_python="3.11")
    .run_commands("pip install --upgrade pip")
    # Install Flash Attention 2 (requires CUDA dev tools)
    .run_commands(
        "pip install ninja packaging",
        "pip install flash-attn --no-build-isolation",
    )
    .pip_install(
        # Core ML dependencies
        "transformers==4.57.1",
        "accelerate==1.8.0",
        "sentencepiece==0.2.0",
        "tokenizers==0.22.1",
        "pillow==10.3.0",
        "qwen-vl-utils==0.0.11",
        "einops==0.8.1",
        "numpy==2.2.6",
    )
    .add_local_dir(
        LOCAL_QWEN_DIR,
        remote_path="/app/qwen",
        ignore=_ignore_runtime_file,
        copy=True,
    )
    .env({
        "PYTHONPATH": "/app/qwen",
        "FLASH_ATTENTION_FORCE_BUILD": "FALSE",
    })
)


# ---------------------------------------------------------------------------
# Model Caching (initialized once per container)
# ---------------------------------------------------------------------------

_model_state = {
    "model": None,
    "processor": None,
    "initialized": False,
}


def _initialize_model():
    """Initialize Qwen model once per container with Flash Attention."""
    global _model_state
    
    if _model_state["initialized"]:
        return _model_state["model"], _model_state["processor"]
    
    import torch
    from transformers import AutoProcessor
    from model_utils import load_model, load_checkpoint_into_model
    
    print("[Qwen Modal] Initializing model with Flash Attention...")
    
    processor = AutoProcessor.from_pretrained(BASE_MODEL)
    
    torch_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    print(f"[Qwen Modal] Using dtype: {torch_dtype}")
    
    # Load model with Flash Attention enabled
    model = load_model(
        BASE_MODEL,
        torch_dtype=torch_dtype,
        device_map="auto",
        quantization_config=None,
        use_flash_attention=True,  # Enable Flash Attention 2
    )
    
    # Load fine-tuned checkpoint if available
    if os.path.exists(CHECKPOINT_PATH):
        print(f"[Qwen Modal] Loading checkpoint from: {CHECKPOINT_PATH}")
        load_checkpoint_into_model(model, CHECKPOINT_PATH)
    else:
        print(f"[Qwen Modal] No checkpoint at {CHECKPOINT_PATH}, using base model")
    
    model.eval()
    
    _model_state["model"] = model
    _model_state["processor"] = processor
    _model_state["initialized"] = True
    
    print("[Qwen Modal] ✓ Model initialized with Flash Attention")
    return model, processor


# ---------------------------------------------------------------------------
# GPU Function - Streaming Only (keeps 1 warm container)
# ---------------------------------------------------------------------------

@app.function(
    image=qwen_image,
    gpu="A10G",  # 24 GB VRAM - optimal for Qwen 2B
    timeout=900,
    scaledown_window=600,  # Keep container warm for 10 minutes
    min_containers=1,      # Always keep 1 container warm for fast response
    max_containers=1,      # Single container handles all requests
    volumes={"/model": model_volume},
)
def qwen_modal_infer_stream(
    prompt: str,
    image_bytes: Optional[bytes] = None,
    image_format: Optional[str] = None,
    max_new_tokens: int = MAX_NEW_TOKENS_DEFAULT,
    temperature: float = 0.0,
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
    from qwen_vl_utils import process_vision_info
    
    model, processor = _initialize_model()
    
    # Process image if provided (Qwen preprocessing)
    pil_image = None
    if image_bytes:
        buffer = io.BytesIO(image_bytes)
        pil_image = Image.open(buffer).convert("RGB")
    
    # Build messages in Qwen format
    if pil_image is not None:
        messages = [[{
            "role": "user",
            "content": [
                {"type": "image", "image": pil_image},
                {"type": "text", "text": prompt}
            ]
        }]]
    else:
        messages = [[{
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
        }]]
    
    # Process inputs using Qwen's native preprocessing
    texts = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    
    processor_kwargs = {"text": texts, "padding": True, "return_tensors": "pt"}
    if image_inputs:
        processor_kwargs["images"] = image_inputs
    if video_inputs:
        processor_kwargs["videos"] = video_inputs
    
    inputs = processor(**processor_kwargs)
    device = model.device if hasattr(model, "device") else next(model.parameters()).device
    inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
    
    # Set up streaming
    streamer = TextIteratorStreamer(
        processor.tokenizer,
        skip_prompt=True,
        skip_special_tokens=True,
    )
    
    generation_kwargs = {
        "max_new_tokens": max_new_tokens,
        "use_cache": True,
        "pad_token_id": processor.tokenizer.pad_token_id or processor.tokenizer.eos_token_id,
        "do_sample": temperature > 0,
        "streamer": streamer,
    }
    if temperature > 0:
        generation_kwargs["temperature"] = temperature
    
    # Run generation in background thread
    def _generate():
        with torch.inference_mode():
            model.generate(**inputs, **generation_kwargs)
    
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
    prompt: str = "Generate the CADQuery code needed to create the CAD for the provided image.",
    image_path: Optional[str] = None,
    max_new_tokens: int = MAX_NEW_TOKENS_DEFAULT,
    temperature: float = 0.0,
):
    """CLI for testing Modal inference."""
    image_bytes = None
    image_format = None

    if image_path:
        img_path = Path(image_path).expanduser().resolve()
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")
        image_bytes = img_path.read_bytes()
        image_format = img_path.suffix.replace(".", "").upper()

    print("------ CAD-Coder Qwen (GCP/Modal Labs) Output ------")
    
    for chunk in qwen_modal_infer_stream.remote_gen(
        prompt=prompt,
        image_bytes=image_bytes,
        image_format=image_format,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
    ):
        print(chunk, end="", flush=True)
    print()
