"""Utilities for invoking the Modal-hosted Qwen inference worker."""
from __future__ import annotations

import asyncio
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


@lru_cache(maxsize=1)
def _lookup_modal_function() -> modal.functions.FunctionHandle:
    """Resolve the remote Modal function handle once."""
    _ensure_modal_credentials()
    app_name = os.getenv("QWEN_MODAL_APP", "cad-coder-qwen3")
    function_name = os.getenv("QWEN_MODAL_FUNCTION", "qwen_modal_infer")

    if not app_name or not function_name:
        raise ModalConfigError(
            "QWEN_MODAL_APP and QWEN_MODAL_FUNCTION must be set to use Modal inference."
        )

    try:
        return modal.Function.from_name(app_name, function_name)
    except Exception as exc:  # pragma: no cover - network errors bubble up
        raise ModalConfigError(
            f"Unable to look up Modal function {function_name!r} in app {app_name!r}: {exc}"
        ) from exc


ImageInput = Union[Image.Image, str, Path, None]


def _serialize_image(image: ImageInput) -> tuple[Optional[bytes], Optional[str]]:
    """Convert supported image inputs into raw bytes for transport."""
    if image is None:
        return None, None

    pil_image: Optional[Image.Image] = None

    if isinstance(image, Image.Image):
        pil_image = image
    elif isinstance(image, (str, Path)):
        img_path = Path(image).expanduser()
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


async def run_modal_qwen_inference(
    prompt: str,
    image: ImageInput = None,
    max_new_tokens: int = 2048,
    temperature: float = 0.0,
) -> str:
    """
    Execute CAD generation on the remote Modal GPU worker.

    Args:
        prompt: Text prompt (already validated upstream).
        image: Optional PIL image (will be serialized to PNG bytes).
        max_new_tokens: Generation limit forwarded to Modal.
        temperature: Sampling temperature forwarded to Modal.
    """
    fn_handle = _lookup_modal_function()
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

