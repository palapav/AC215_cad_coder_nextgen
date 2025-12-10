"""
Utilities for invoking Modal-hosted inference workers (Qwen and LLaVA).

Supports both GCP (GKE) and Modal Labs deployments.
Modal provides instant GPU access without quota limitations.
"""
from __future__ import annotations

import asyncio
import base64
import io
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union, AsyncGenerator

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


@lru_cache(maxsize=1)
def _lookup_qwen_modal_stream_function() -> modal.functions.FunctionHandle:
    """Resolve the remote Qwen streaming Modal function handle once."""
    _ensure_modal_credentials()
    app_name = os.getenv("QWEN_MODAL_APP", "cad-coder-qwen3")
    function_name = os.getenv("QWEN_MODAL_STREAM_FUNCTION", "qwen_modal_infer_stream")

    try:
        return modal.Function.from_name(app_name, function_name)
    except Exception as exc:
        raise ModalConfigError(
            f"Unable to look up Modal streaming function {function_name!r} in app {app_name!r}: {exc}"
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


@lru_cache(maxsize=1)
def _lookup_llava_modal_stream_function() -> modal.functions.FunctionHandle:
    """Resolve the remote LLaVA streaming Modal function handle once."""
    _ensure_modal_credentials()
    app_name = os.getenv("LLAVA_MODAL_APP", "cad-coder-llava")
    function_name = os.getenv("LLAVA_MODAL_STREAM_FUNCTION", "llava_modal_infer_stream")

    try:
        return modal.Function.from_name(app_name, function_name)
    except Exception as exc:
        raise ModalConfigError(
            f"Unable to look up Modal streaming function {function_name!r} in app {app_name!r}: {exc}"
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
    """Deserialize supported image formats into a RGB PIL image."""
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
    """Preprocess image with CLIP-like normalization for LLaVA."""
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
    Non-streaming version - returns complete response.
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


async def stream_modal_qwen_inference(
    prompt: str,
    image: ImageInput = None,
    max_new_tokens: int = 2048,
    temperature: float = 0.0,
) -> AsyncGenerator[str, None]:
    """
    Stream CAD generation tokens from the remote Qwen Modal GPU worker.
    Yields tokens as they are generated for real-time frontend updates.
    """
    fn_handle = _lookup_qwen_modal_stream_function()
    image_bytes, image_format = _serialize_image(image)

    def _stream_remote():
        """Generator that yields tokens from Modal."""
        for chunk in fn_handle.remote_gen(
            prompt=prompt,
            image_bytes=image_bytes,
            image_format=image_format,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        ):
            yield chunk

    # Run the streaming in a thread to avoid blocking
    loop = asyncio.get_running_loop()
    
    # Use a queue to pass tokens from the sync generator to async
    import queue
    token_queue: queue.Queue = queue.Queue()
    done_sentinel = object()
    
    def _run_stream():
        try:
            for chunk in _stream_remote():
                token_queue.put(chunk)
        finally:
            token_queue.put(done_sentinel)
    
    # Start streaming in background
    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_run_stream)
    
    try:
        while True:
            # Check for tokens with a small timeout
            try:
                token = await loop.run_in_executor(
                    None, 
                    lambda: token_queue.get(timeout=0.1)
                )
                if token is done_sentinel:
                    break
                yield token
            except queue.Empty:
                # Check if the future is done with an exception
                if future.done() and future.exception():
                    raise future.exception()
                continue
    finally:
        executor.shutdown(wait=False)


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
    Non-streaming version - returns complete response.
    """
    fn_handle = _lookup_llava_modal_function()
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


async def stream_modal_llava_inference(
    prompt: str,
    image: ImageInput = None,
    max_new_tokens: int = 3450,
    temperature: float = 0.0,
    top_p: float = 1.0,
) -> AsyncGenerator[str, None]:
    """
    Stream CAD generation tokens from the remote LLaVA Modal GPU worker.
    Yields tokens as they are generated for real-time frontend updates.
    """
    fn_handle = _lookup_llava_modal_stream_function()
    image_bytes, image_format = _preprocess_image_for_llava(image, target_size=336)

    def _stream_remote():
        """Generator that yields tokens from Modal."""
        for chunk in fn_handle.remote_gen(
            prompt=prompt,
            image_bytes=image_bytes,
            image_format=image_format,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
        ):
            yield chunk

    # Run the streaming in a thread to avoid blocking
    loop = asyncio.get_running_loop()
    
    import queue
    token_queue: queue.Queue = queue.Queue()
    done_sentinel = object()
    
    def _run_stream():
        try:
            for chunk in _stream_remote():
                token_queue.put(chunk)
        finally:
            token_queue.put(done_sentinel)
    
    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_run_stream)
    
    try:
        while True:
            try:
                token = await loop.run_in_executor(
                    None, 
                    lambda: token_queue.get(timeout=0.1)
                )
                if token is done_sentinel:
                    break
                yield token
            except queue.Empty:
                if future.done() and future.exception():
                    raise future.exception()
                continue
    finally:
        executor.shutdown(wait=False)
