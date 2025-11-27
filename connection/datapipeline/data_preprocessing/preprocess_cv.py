#!/usr/bin/env python
"""
preprocess_cv.py
----------------
Step 2: Data Preprocessing for the GenCAD-Code dataset.

This script performs preprocessing on the CAD-Coder dataset:
- Standardizes and pads CAD images (CLIP-like normalization)
- Cleans and normalizes CadQuery scripts
- Generates a multimodal JSONL file linking image, prompt, and code.

Usage:
    python preprocess_cv.py \
        --input_dir ./data/raw_test \
        --output_dir ./data/processed_test
        --uid "your_user_id" \
        --prompt "your prompt here"
"""

import os
import json
import re
import argparse
from PIL import Image
from tqdm import tqdm
import torch
from torchvision import transforms
import numpy as np



# -----------------------------
# Helper functions
# -----------------------------

def expand2square(pil_img, background_color=(0, 0, 0)):
    """Pads image to square while keeping aspect ratio."""
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


def clean_cadquery_code(code: str) -> str:
    """Clean CadQuery code by removing comments, extra lines, and inconsistent indentation."""
    code = re.sub(r"#.*", "", code)
    code = re.sub(r"print\(.*?\)", "", code)
    lines = [line.rstrip() for line in code.splitlines() if line.strip()]
    code = "\n".join(lines)
    code = re.sub(r"\t", "    ", code)
    return code.strip()


def build_image_transform(img_size=336):
    """Create CLIP-like image preprocessing transform."""
    re = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5],
                             std=[0.5, 0.5, 0.5])
    ])
    return re


def preprocess_image(img_path: str, transform, save_path: str):
    """Load, pad, and transform image, then save a processed copy."""
    img = Image.open(img_path).convert("RGB")
    img = expand2square(img, (0, 0, 0))
    tensor_img = transform(img)
    transforms.ToPILImage()(tensor_img).save(save_path)
    return tensor_img


def resolve_path(path, input_dir):
    """
    Resolves Docker paths (/app/data/..., /workspace/...) or host paths
    by attempting to map them to accessible paths in the container.
    """
    print(f"Resolving path: {path}")
    
    # If path exists as-is, use it
    if os.path.exists(path):
        print(f"Path exists: {path}")
        return path

    # Convert /workspace paths (mounted project root)
    if path.startswith("/workspace"):
        if os.path.exists(path):
            return path
        # Try relative to current working directory
        rel_path = path.replace("/workspace/", "")
        if os.path.exists(rel_path):
            return rel_path

    # Convert docker /app/data paths
    if path.startswith("/app/data"):
        alt = path.replace("/app/data", os.path.abspath(input_dir))
        if os.path.exists(alt):
            return alt

    # Try matching filename directly inside input_dir
    basename = os.path.basename(path)
    alt = os.path.join(input_dir, basename)
    if os.path.exists(alt):
        return alt

    # Try in /workspace if it's a host absolute path
    # Extract relative path from absolute host path
    if os.path.isabs(path) and not path.startswith("/app") and not path.startswith("/workspace"):
        # Try to find it in /workspace
        # This handles paths like /Users/.../connection/model_inference/...
        workspace_path = f"/workspace{path}" if not path.startswith("/workspace") else path
        # Or try to extract the relative part after "connection"
        if "connection" in path:
            rel_part = path.split("connection", 1)[1].lstrip("/")
            workspace_path = f"/workspace/{rel_part}"
            if os.path.exists(workspace_path):
                print(f"Found in workspace: {workspace_path}")
                return workspace_path

    # Try one directory up if input_dir is nested
    alt = os.path.join(os.path.dirname(input_dir), "raw_test", basename)
    if os.path.exists(alt):
        return alt

    # If nothing works, return None
    print(f"Could not resolve path: {path}")
    return None


# -----------------------------
# Main preprocessing function
# -----------------------------

def preprocess_dataset(input_dir: str, output_dir: str, uid: str, prompt: str, img_size: int = 336):
    """Reads image/code pairs, applies normalization and cleaning, and saves aligned JSONL dataset.
    
    Args:
        input_dir: Path to the input image file (or directory containing images)
        output_dir: Directory where processed images and JSONL will be saved
        uid: User ID for the processed sample
        prompt: User prompt/command
        img_size: Target image size for preprocessing
    """
    os.makedirs(output_dir, exist_ok=True)
    transform = build_image_transform(img_size)
    
    jsonl_path = os.path.join(output_dir, "dataset.jsonl")
    processed_samples = []

    # Check if input_dir is a file or directory
    if os.path.isfile(input_dir):
        # Single image file
        image_files = [input_dir]
        base_dir = os.path.dirname(input_dir) or "."
    elif os.path.isdir(input_dir):
        # Directory containing images
        image_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        base_dir = input_dir
    else:
        raise FileNotFoundError(f"Input path does not exist: {input_dir}")

    print(f"⚙️  Starting preprocessing for {len(image_files)} image(s)...")
    
    for img_path in image_files:
        # Resolve possible Docker paths or mismatched local paths
        resolved_img_path = resolve_path(img_path, base_dir)
        
        if resolved_img_path is None or not os.path.exists(resolved_img_path):
            print(f"⚠️ Skipping {img_path}: file not found")
            continue
        
        # --- Image preprocessing ---
        out_img_path = os.path.join(output_dir, f"{uid}.png")
        try:
            preprocess_image(resolved_img_path, transform, out_img_path)
            print(f"✅ Processed image: {resolved_img_path} -> {out_img_path}")
        except Exception as e:
            print(f"⚠️ Skipping {uid}: image error -> {e}")
            continue

        # --- Create sample entry ---
        processed_samples.append({
            "question_id": str(uid),
            "image": out_img_path,
            "text": prompt,
            "category": 'default',
        })

    # Save all processed samples to JSONL
    with open(jsonl_path, "w", encoding="utf-8") as f_out:
        for s in processed_samples:
            json.dump(s, f_out)
            f_out.write("\n")

    print(f"✅ Preprocessing complete. {len(processed_samples)} samples saved to {jsonl_path}")
    return jsonl_path


# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess GenCAD-Code dataset for CAD-Coder pipeline")
    parser.add_argument("--input_dir", type=str, required=True, help="Input directory from user as image or text")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory for processed data")
    parser.add_argument("--uid", type=str, default="0", help="user_id")
    parser.add_argument("--prompt", type=str, required=True, help="Command from User")
    parser.add_argument("--img_size", type=int, default=336, help="Resize dimension for CLIP preprocessing (default=336)")
    args = parser.parse_args()

    preprocess_dataset(args.input_dir, args.output_dir, args.uid, args.prompt, args.img_size)
