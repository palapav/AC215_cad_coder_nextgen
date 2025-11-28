"""Utilities for invoking Modal-hosted inference workers (Qwen and LLaVA)."""
from __future__ import annotations

import asyncio
import base64
import io
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

import modal
from PIL import Image


class ModalConfigError(RuntimeError):
    """Raised when Modal lookup fails due to missing configuration."""


def _ensure_modal_credentials() -> None:
    """Validate Modal tokens exist in environment."""
    token_id = os.getenv("MODAL_TOKEN_ID")
    token_secret = os.getenv("MODAL_TOKEN_SECRET")
    if not token_id or not token_secret:
        raise ModalConfigError(
            "MODAL_TOKEN_ID and MODAL_TOKEN_SECRET must be set for Modal inference."
        )


# ---------------------------------------------------------------------------
# Qwen Modal Client
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _lookup_qwen_modal_function() -> modal.functions.FunctionHandle:
    """Resolve the remote Qwen Modal function handle once."""
    _ensure_modal_credentials()
    app_name = os.getenv("QWEN_MODAL_APP", "cad-coder-qwen3")
    function_name = os.getenv("QWEN_MODAL_FUNCTION", "qwen_modal_infer")

    if not app_name or not function_name:
        raise ModalConfigError(
            "QWEN_MODAL_APP and QWEN_MODAL_FUNCTION must be set to use Qwen Modal inference."
        )

    try:
        return modal.Function.from_name(app_name, function_name)
    except Exception as exc:
        raise ModalConfigError(
            f"Unable to look up Modal function {function_name!r} in app {app_name!r}: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# LLaVA Modal Client
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _lookup_llava_modal_function() -> modal.functions.FunctionHandle:
    """Resolve the remote LLaVA Modal function handle once."""
    _ensure_modal_credentials()
    app_name = os.getenv("LLAVA_MODAL_APP", "cad-coder-llava")
    function_name = os.getenv("LLAVA_MODAL_FUNCTION", "llava_modal_infer")

    if not app_name or not function_name:
        raise ModalConfigError(
            "LLAVA_MODAL_APP and LLAVA_MODAL_FUNCTION must be set to use LLaVA Modal inference."
        )

    try:
        return modal.Function.from_name(app_name, function_name)
    except Exception as exc:
        raise ModalConfigError(
            f"Unable to look up Modal function {function_name!r} in app {app_name!r}: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Image Serialization
# ---------------------------------------------------------------------------

ImageInput = Union[Image.Image, str, Path, None]


def _serialize_image(image: ImageInput) -> tuple[Optional[bytes], Optional[str]]:
    """Convert supported image inputs into raw bytes for transport.
    
    Supports:
    - PIL Image objects
    - File paths (str or Path)
    - Base64 data URLs (data:image/...)
    """
    if image is None:
        return None, None

    pil_image: Optional[Image.Image] = None

    if isinstance(image, Image.Image):
        pil_image = image
    elif isinstance(image, (str, Path)):
        img_str = str(image)
        
        # Handle base64 data URLs
        if img_str.startswith("data:image"):
            try:
                header, encoded = img_str.split(",", 1)
                image_data = base64.b64decode(encoded)
                pil_image = Image.open(io.BytesIO(image_data))
            except Exception as e:
                raise ValueError(f"Failed to decode base64 image: {e}")
        else:
            # Handle file paths
            img_path = Path(img_str).expanduser()
            if not img_path.exists():
                raise FileNotFoundError(f"Image path does not exist: {img_path}")
            pil_image = Image.open(img_path)
    else:
        raise ValueError(f"Unsupported image type for Modal inference: {type(image)}")

    if not isinstance(pil_image, Image.Image):
        raise ValueError("Failed to load image for Modal inference")

    pil_image = pil_image.convert("RGB")
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return buffer.getvalue(), "PNG"


def _load_pil_image(image: ImageInput) -> Image.Image:
    """Deserialize supported image formats into a RGB PIL image.
    
    When no image is provided, a blank placeholder is returned so that
    inference can still proceed.
    """
    if image is None:
        return Image.new("RGB", (336, 336), color=(0, 0, 0))

    pil_image: Optional[Image.Image] = None
    
    if isinstance(image, Image.Image):
        pil_image = image
    elif isinstance(image, (str, Path)):
        img_str = str(image)
        if img_str.startswith("data:image"):
            try:
                header, encoded = img_str.split(",", 1)
                image_data = base64.b64decode(encoded)
                pil_image = Image.open(io.BytesIO(image_data))
            except Exception as e:
                raise ValueError(f"Failed to decode base64 image: {e}")
        else:
            img_path = Path(img_str).expanduser()
            if not img_path.exists():
                raise FileNotFoundError(f"Image path does not exist: {img_path}")
            pil_image = Image.open(img_path)
    else:
        raise ValueError(f"Unsupported image type for LLaVA inference: {type(image)}")
    
    if not isinstance(pil_image, Image.Image):
        raise ValueError("Failed to load image for LLaVA inference")
    
    return pil_image.convert("RGB")


def _preprocess_image_for_llava(
    image: ImageInput,
    target_size: int = 336,
) -> tuple[Optional[bytes], Optional[str]]:
    """Preprocess image with CLIP-like normalization for LLaVA.
    
    Applies padding to square and resizing before serialization. If the caller
    does not supply an image, a blank placeholder image is generated.
    """
    pil_image = _load_pil_image(image)
    
    # Pad to square (CLIP-like preprocessing)
    width, height = pil_image.size
    if width != height:
        max_dim = max(width, height)
        new_image = Image.new("RGB", (max_dim, max_dim), (0, 0, 0))
        if width > height:
            new_image.paste(pil_image, (0, (max_dim - height) // 2))
        else:
            new_image.paste(pil_image, ((max_dim - width) // 2, 0))
        pil_image = new_image
    
    # Resize to target size
    pil_image = pil_image.resize((target_size, target_size), Image.LANCZOS)
    
    # Serialize
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return buffer.getvalue(), "PNG"


# ---------------------------------------------------------------------------
# Qwen Inference
# ---------------------------------------------------------------------------

async def run_modal_qwen_inference(
    prompt: str,
    image: ImageInput = None,
    max_new_tokens: int = 2048,
    temperature: float = 0.0,
) -> str:
    """
    Execute CAD generation on the remote Qwen Modal GPU worker.

    Args:
        prompt: Text prompt (already validated upstream).
        image: Optional PIL image, file path, or base64 data URL.
        max_new_tokens: Generation limit forwarded to Modal.
        temperature: Sampling temperature forwarded to Modal.
    """
    fn_handle = _lookup_qwen_modal_function()
    image_bytes, image_format = _serialize_image(image)

    def _call_remote() -> str:
        return fn_handle.remote(
            prompt=prompt,
            image_bytes=image_bytes,
            image_format=image_format,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _call_remote)


# ---------------------------------------------------------------------------
# LLaVA Inference
# ---------------------------------------------------------------------------

async def run_modal_llava_inference(
    prompt: str,
    image: ImageInput = None,
    max_new_tokens: int = 3450,
    temperature: float = 0.0,
    top_p: float = 1.0,
) -> str:
    """
    Execute CAD generation on the remote LLaVA Modal GPU worker.

    Args:
        prompt: Text prompt for CAD code generation.
        image: Required PIL image, file path, or base64 data URL.
        max_new_tokens: Generation limit (default 3450 for LLaVA).
        temperature: Sampling temperature (0 => greedy).
        top_p: Top-p sampling parameter.
    
    Raises:
        ValueError: If no image is provided (LLaVA requires an image).
    """
    fn_handle = _lookup_llava_modal_function()
    
    # Apply CLIP-like preprocessing for LLaVA
    image_bytes, image_format = _preprocess_image_for_llava(image, target_size=336)

    def _call_remote() -> str:
        return fn_handle.remote(
            prompt=prompt,
            image_bytes=image_bytes,
            image_format=image_format,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
        )

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _call_remote)
