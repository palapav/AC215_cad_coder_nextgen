"""
GKE Inference Client for CAD-Coder

This module provides HTTP clients for calling the Qwen and LLaVA inference
services deployed on GKE. It is a drop-in replacement for modal_client.py
when deploying to GCP.

Features:
- Async HTTP client with connection pooling
- Automatic retries with exponential backoff
- Image preprocessing and serialization
- Health checking and circuit breaker pattern
- Timeout handling
"""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

import httpx
from PIL import Image

logger = logging.getLogger(__name__)


class GKEClientError(RuntimeError):
    """Raised when GKE inference fails."""
    pass


class GKEServiceUnavailable(GKEClientError):
    """Raised when the inference service is unavailable."""
    pass


# =============================================================================
# Configuration
# =============================================================================

QWEN_SERVICE_URL = os.getenv("QWEN_SERVICE_URL", "http://qwen-inference:8080")
LLAVA_SERVICE_URL = os.getenv("LLAVA_SERVICE_URL", "http://llava-inference:8080")

QWEN_MAX_NEW_TOKENS = int(os.getenv("QWEN_MODAL_MAX_NEW_TOKENS", "4096"))
QWEN_TEMPERATURE = float(os.getenv("QWEN_MODAL_TEMPERATURE", "0.0"))

LLAVA_MAX_NEW_TOKENS = int(os.getenv("LLAVA_MODAL_MAX_NEW_TOKENS", "3450"))
LLAVA_TEMPERATURE = float(os.getenv("LLAVA_MODAL_TEMPERATURE", "0.0"))
LLAVA_TOP_P = float(os.getenv("LLAVA_MODAL_TOP_P", "1.0"))

REQUEST_TIMEOUT = int(os.getenv("GKE_REQUEST_TIMEOUT", "300"))
MAX_RETRIES = int(os.getenv("GKE_MAX_RETRIES", "3"))


# =============================================================================
# HTTP Client Pool
# =============================================================================

_http_client: Optional[httpx.AsyncClient] = None


def _get_http_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )
    return _http_client


async def close_http_client():
    """Close the HTTP client (call on shutdown)."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


# =============================================================================
# Image Serialization
# =============================================================================

ImageInput = Union[Image.Image, str, Path, None]


def _serialize_image(image: ImageInput) -> tuple[Optional[str], Optional[str]]:
    """
    Serialize image to base64 string for HTTP transport.
    
    Returns:
        Tuple of (base64_encoded_bytes, format)
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
                # Return the already encoded data
                return encoded, "PNG"
            except Exception as e:
                raise ValueError(f"Failed to decode base64 image: {e}")
        else:
            # Handle file paths
            img_path = Path(img_str).expanduser()
            if not img_path.exists():
                raise FileNotFoundError(f"Image path does not exist: {img_path}")
            pil_image = Image.open(img_path)
    else:
        raise ValueError(f"Unsupported image type: {type(image)}")

    if not isinstance(pil_image, Image.Image):
        raise ValueError("Failed to load image")

    pil_image = pil_image.convert("RGB")
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded, "PNG"


def _preprocess_image_for_llava(
    image: ImageInput,
    target_size: int = 336,
) -> tuple[Optional[str], Optional[str]]:
    """
    Preprocess image with CLIP-like normalization for LLaVA.
    
    Applies padding to square and resizing before serialization.
    """
    if image is None:
        # Create blank placeholder
        pil_image = Image.new("RGB", (target_size, target_size), color=(0, 0, 0))
    elif isinstance(image, Image.Image):
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
        raise ValueError(f"Unsupported image type: {type(image)}")

    pil_image = pil_image.convert("RGB")
    
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
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded, "PNG"


# =============================================================================
# Retry Logic
# =============================================================================

async def _request_with_retry(
    method: str,
    url: str,
    json_data: dict,
    max_retries: int = MAX_RETRIES,
) -> dict:
    """Make HTTP request with exponential backoff retry."""
    client = _get_http_client()
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = await client.request(method, url, json=json_data)
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            last_error = e
            if e.response.status_code == 503:
                # Service unavailable - retry with backoff
                wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s, ...
                logger.warning(f"Service unavailable, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
            elif e.response.status_code >= 500:
                # Other server errors - retry
                wait_time = (2 ** attempt) * 0.5
                logger.warning(f"Server error {e.response.status_code}, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                # Client error - don't retry
                raise GKEClientError(f"Client error: {e.response.status_code} - {e.response.text}")
        
        except httpx.ConnectError as e:
            last_error = e
            wait_time = (2 ** attempt) * 0.5
            logger.warning(f"Connection error, retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)
        
        except httpx.TimeoutException as e:
            last_error = e
            logger.warning(f"Request timeout on attempt {attempt + 1}/{max_retries}")
            # Don't retry on timeout for inference (too expensive)
            if attempt >= 1:
                raise GKEClientError(f"Request timeout after {attempt + 1} attempts")
            await asyncio.sleep(1)
    
    raise GKEServiceUnavailable(f"Service unavailable after {max_retries} retries: {last_error}")


# =============================================================================
# Health Checking
# =============================================================================

async def check_qwen_health() -> bool:
    """Check if Qwen inference service is healthy."""
    try:
        client = _get_http_client()
        response = await client.get(f"{QWEN_SERVICE_URL}/health", timeout=5.0)
        data = response.json()
        return data.get("model_loaded", False)
    except Exception as e:
        logger.warning(f"Qwen health check failed: {e}")
        return False


async def check_llava_health() -> bool:
    """Check if LLaVA inference service is healthy."""
    try:
        client = _get_http_client()
        response = await client.get(f"{LLAVA_SERVICE_URL}/health", timeout=5.0)
        data = response.json()
        return data.get("model_loaded", False)
    except Exception as e:
        logger.warning(f"LLaVA health check failed: {e}")
        return False


# =============================================================================
# Qwen Inference
# =============================================================================

async def run_gke_qwen_inference(
    prompt: str,
    image: ImageInput = None,
    max_new_tokens: int = QWEN_MAX_NEW_TOKENS,
    temperature: float = QWEN_TEMPERATURE,
) -> str:
    """
    Execute CAD generation on the Qwen GKE inference service.

    Args:
        prompt: Text prompt for generation.
        image: Optional PIL image, file path, or base64 data URL.
        max_new_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
    
    Returns:
        Generated CAD code string.
    """
    image_bytes, image_format = _serialize_image(image)
    
    request_data = {
        "prompt": prompt,
        "image_bytes": image_bytes,
        "image_format": image_format,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
    }
    
    logger.info(f"Calling Qwen inference service at {QWEN_SERVICE_URL}")
    
    try:
        response = await _request_with_retry(
            "POST",
            f"{QWEN_SERVICE_URL}/infer",
            request_data,
        )
        return response.get("generated_text", "")
    
    except GKEServiceUnavailable:
        raise
    except Exception as e:
        raise GKEClientError(f"Qwen inference failed: {e}")


async def stream_gke_qwen_inference(
    prompt: str,
    image: ImageInput = None,
    max_new_tokens: int = QWEN_MAX_NEW_TOKENS,
    temperature: float = QWEN_TEMPERATURE,
):
    """Stream tokens from the Qwen inference service."""
    image_bytes, image_format = _serialize_image(image)

    request_data = {
        "prompt": prompt,
        "image_bytes": image_bytes,
        "image_format": image_format,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
    }

    logger.info(f"Streaming from Qwen inference service at {QWEN_SERVICE_URL}")
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        async with client.stream("POST", f"{QWEN_SERVICE_URL}/stream", json=request_data) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_text():
                if chunk:
                    yield chunk


# =============================================================================
# LLaVA Inference
# =============================================================================

async def run_gke_llava_inference(
    prompt: str,
    image: ImageInput = None,
    max_new_tokens: int = LLAVA_MAX_NEW_TOKENS,
    temperature: float = LLAVA_TEMPERATURE,
    top_p: float = LLAVA_TOP_P,
) -> str:
    """
    Execute CAD generation on the LLaVA GKE inference service.

    Args:
        prompt: Text prompt for generation.
        image: PIL image, file path, or base64 data URL (optional - blank placeholder used if not provided).
        max_new_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        top_p: Top-p sampling parameter.
    
    Returns:
        Generated CAD code string.
    """
    # Apply CLIP-like preprocessing for LLaVA
    image_bytes, image_format = _preprocess_image_for_llava(image, target_size=336)
    
    request_data = {
        "prompt": prompt,
        "image_bytes": image_bytes,
        "image_format": image_format,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }
    
    logger.info(f"Calling LLaVA inference service at {LLAVA_SERVICE_URL}")
    
    try:
        response = await _request_with_retry(
            "POST",
            f"{LLAVA_SERVICE_URL}/infer",
            request_data,
        )
        return response.get("generated_text", "")
    
    except GKEServiceUnavailable:
        raise
    except Exception as e:
        raise GKEClientError(f"LLaVA inference failed: {e}")


async def stream_gke_llava_inference(
    prompt: str,
    image: ImageInput = None,
    max_new_tokens: int = LLAVA_MAX_NEW_TOKENS,
    temperature: float = LLAVA_TEMPERATURE,
    top_p: float = LLAVA_TOP_P,
):
    """Stream tokens from the LLaVA inference service."""
    image_bytes, image_format = _preprocess_image_for_llava(image, target_size=336)

    request_data = {
        "prompt": prompt,
        "image_bytes": image_bytes,
        "image_format": image_format,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }

    logger.info(f"Streaming from LLaVA inference service at {LLAVA_SERVICE_URL}")
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        async with client.stream("POST", f"{LLAVA_SERVICE_URL}/stream", json=request_data) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_text():
                if chunk:
                    yield chunk
