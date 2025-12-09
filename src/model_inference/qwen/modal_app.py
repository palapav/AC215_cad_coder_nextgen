#!/usr/bin/env python3
"""
Modal deployment script for the fine-tuned Qwen-3 CAD-Coder model.

This file defines a GPU-backed Modal function that loads the local inference
stack (shared with the FastAPI backend) and exposes a remote entrypoint that
the API can call to run generation on A10G GPUs (24GB VRAM).

Typical workflow:
1. Ensure you have `modal` installed locally (`pip install modal-client`) and run `python -m modal setup`.
2. Create a persistent volume and upload the fine-tuned checkpoint:
     modal volume create cad-coder-qwen3-model
     modal volume put cad-coder-qwen3-model src/model_inference/qwen/final_model.pt:/final_model.pt
3. Deploy the app so it stays warm:
     modal deploy src/model_inference/qwen/modal_app.py
4. The FastAPI service invokes the `qwen_modal_infer` function through Modal's Python client.
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
APP_NAME = os.environ.get("QWEN_MODAL_APP", "cad-coder-qwen3")
MODEL_VOLUME_NAME = os.environ.get("QWEN_MODAL_VOLUME", "cad-coder-qwen3-model")
CHECKPOINT_FILENAME = os.environ.get("QWEN_MODAL_CHECKPOINT", "final_model.pt")
BASE_MODEL = os.environ.get("QWEN_BASE_MODEL", "Qwen/Qwen3-VL-2B-Instruct")
MAX_NEW_TOKENS_DEFAULT = int(os.environ.get("QWEN_MODAL_MAX_NEW_TOKENS", "2048"))
CHECKPOINT_PATH = f"/model/{CHECKPOINT_FILENAME}"

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

# Copy only the lightweight python sources into the container (skip giant checkpoints)
LOCAL_QWEN_DIR = Path(__file__).resolve().parent


def _ignore_runtime_file(path: Path) -> bool:
    """Modal helper to skip large artifacts while copying.
    
    Only includes Python source files - images and checkpoints are not needed
    since all images come from API/frontend and checkpoints are in Modal volumes.
    """
    if path.is_dir():
        return False
    # Include only Python files - skip images, checkpoints, and other artifacts
    if path.suffix == ".py":
        return False
    # Skip everything else (images, checkpoints, etc.)
    return True


qwen_image = (
    modal.Image.from_registry("pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel", add_python="3.11")
    .run_commands("pip install --upgrade pip")
    .pip_install(
        "transformers==4.57.1",
        "accelerate==1.8.0",
        "sentencepiece==0.2.0",
        "tokenizers==0.22.1",
        "pillow==10.3.0",
        "qwen-vl-utils==0.0.11",
        "einops==0.8.1",
        "numpy==2.2.6",
        "ninja",
    )
    .run_commands(
        "pip install --no-build-isolation --no-cache-dir flash-attn"
    )
    .add_local_dir(
        LOCAL_QWEN_DIR,
        remote_path="/app/qwen",
        ignore=_ignore_runtime_file,
        copy=True,
    )
    .env({"PYTHONPATH": "/app/qwen", "CUDA_HOME": "/usr/local/cuda", "MAX_JOBS": "1", "TORCH_CUDA_ARCH_LIST": "90"})
)


# ---------------------------------------------------------------------------
# Remote GPU function
# ---------------------------------------------------------------------------

@app.function(
    image=qwen_image,
    gpu="H100",
    timeout=900,
    scaledown_window=600,
    min_containers=1,
    max_containers=1,
    volumes={"/model": model_volume},
)
def qwen_modal_infer(
    prompt: str,
    image_bytes: Optional[bytes] = None,
    image_format: Optional[str] = None,
    max_new_tokens: int = MAX_NEW_TOKENS_DEFAULT,
    temperature: float = 0.0,
) -> str:
    """
    Remote inference entrypoint executed on a GPU worker.

    Args:
        prompt: Natural language prompt (will default internally if empty).
        image_bytes: Optional raw bytes of an RGB image (PNG/JPEG).
        image_format: Optional hint for Pillow (defaults to PNG).
        max_new_tokens: Generation cap (defaults to env-configured value).
        temperature: Sampling temperature (0 => greedy).
    """
    import time
    from inference_service import initialize_model, generate_cad_code
    from PIL import Image

    model, processor = initialize_model(
        checkpoint_path=CHECKPOINT_PATH,
        base_model=BASE_MODEL,
    )

    pil_image = None
    if image_bytes:
        buffer = io.BytesIO(image_bytes)
        pil_image = Image.open(buffer)
        if image_format:
            pil_image.format = image_format
        pil_image = pil_image.convert("RGB")

    start = time.time()
    output = generate_cad_code(
        prompt=prompt,
        image=pil_image,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
    )
    duration = time.time() - start
    try:
        print(f"[Qwen Modal] Generation time: {duration:.2f}s | max_new_tokens={max_new_tokens}")
    except Exception:
        pass
    return output


# ---------------------------------------------------------------------------
# Local helper entrypoints
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def main(
    prompt: str = "Generate the CADQuery code needed to create the CAD for the provided image.",
    image_path: Optional[str] = None,
    max_new_tokens: int = MAX_NEW_TOKENS_DEFAULT,
    temperature: float = 0.0,
):
    """Quick CLI for sanity checking Modal inference.
    
    Note: All images should be provided via API/frontend. This entrypoint
    is primarily for testing - if image_path is not provided, inference will
    run without an image (text-only generation).
    """
    image_bytes = None
    image_format = None

    if image_path:
        img_path = Path(image_path).expanduser().resolve()
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")
        image_bytes = img_path.read_bytes()
        image_format = img_path.suffix.replace(".", "").upper()

    result = qwen_modal_infer.remote(
        prompt=prompt,
        image_bytes=image_bytes,
        image_format=image_format,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
    )
    print("------ CAD-Coder (Modal) Output ------")
    print(result)
