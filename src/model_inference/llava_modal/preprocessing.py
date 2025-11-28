#!/usr/bin/env python
"""
Preprocessing module for LLaVA CAD-Coder model.

This module provides image preprocessing functionality that prepares images
for the LLaVA model inference. It applies CLIP-like normalization and padding.
"""

import io
from typing import Optional, Tuple, Union
from PIL import Image
import base64


def expand2square(pil_img: Image.Image, background_color: Tuple[int, int, int] = (0, 0, 0)) -> Image.Image:
    """Pads image to square while keeping aspect ratio.
    
    Args:
        pil_img: PIL Image to pad
        background_color: RGB tuple for padding color (default black)
    
    Returns:
        Square PIL Image
    """
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        result = Image.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, (width - height) // 2))
        return result
    else:
        result = Image.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, ((height - width) // 2, 0))
        return result


def preprocess_image(
    image: Union[Image.Image, bytes, str],
    target_size: int = 336,
) -> Image.Image:
    """Preprocess an image for LLaVA model inference.
    
    Args:
        image: PIL Image, bytes, or base64 data URL string
        target_size: Target size for the image (default 336 for CLIP)
    
    Returns:
        Preprocessed PIL Image
    """
    # Handle different input types
    if isinstance(image, bytes):
        pil_image = Image.open(io.BytesIO(image)).convert("RGB")
    elif isinstance(image, str):
        if image.startswith("data:image"):
            # Base64 data URL
            header, encoded = image.split(",", 1)
            image_data = base64.b64decode(encoded)
            pil_image = Image.open(io.BytesIO(image_data)).convert("RGB")
        else:
            # File path
            pil_image = Image.open(image).convert("RGB")
    elif isinstance(image, Image.Image):
        pil_image = image.convert("RGB")
    else:
        raise ValueError(f"Unsupported image type: {type(image)}")
    
    # Pad to square
    pil_image = expand2square(pil_image, (0, 0, 0))
    
    # Resize to target size
    pil_image = pil_image.resize((target_size, target_size), Image.LANCZOS)
    
    return pil_image


def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """Convert PIL Image to bytes.
    
    Args:
        image: PIL Image
        format: Output format (PNG, JPEG, etc.)
    
    Returns:
        Image bytes
    """
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()


def preprocess_for_modal(
    image: Union[Image.Image, bytes, str],
    target_size: int = 336,
) -> Tuple[bytes, str]:
    """Preprocess image and return bytes for Modal transport.
    
    Args:
        image: Input image (PIL Image, bytes, or path/data URL)
        target_size: Target size for preprocessing
    
    Returns:
        Tuple of (image_bytes, format_string)
    """
    processed = preprocess_image(image, target_size)
    return image_to_bytes(processed, "PNG"), "PNG"

