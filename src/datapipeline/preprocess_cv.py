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
    Resolves Docker paths (/app/data/...) or mismatched paths
    by attempting to map them to your local dataset folder.
    """
    if os.path.exists(path):
        return path

    # Convert docker absolute -> local relative
    if path.startswith("/app/data"):
        alt = path.replace("/app/data", os.path.abspath(input_dir))
        if os.path.exists(alt):
            return alt

    # Try matching filename directly inside input_dir
    basename = os.path.basename(path)
    alt = os.path.join(input_dir, basename)
    if os.path.exists(alt):
        return alt

    # Try one directory up if input_dir is nested
    alt = os.path.join(os.path.dirname(input_dir), "raw_test", basename)
    if os.path.exists(alt):
        return alt

    # If nothing works, return None
    return None


# -----------------------------
# Main preprocessing function
# -----------------------------

def preprocess_dataset(input_dir: str, output_dir: str, img_size: int = 336):
    """Reads image/code pairs, applies normalization and cleaning, and saves aligned JSONL dataset."""
    os.makedirs(output_dir, exist_ok=True)
    transform = build_image_transform(img_size)
    index_path = os.path.join(input_dir, "index.csv")
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Missing index.csv in {input_dir}. Please run dataloader.py first.")

    jsonl_path = os.path.join(output_dir, "dataset.jsonl")
    processed_samples = []

    with open(index_path, "r") as f:
        lines = f.readlines()[1:]  # Skip header

    print(f"⚙️  Starting preprocessing for {len(lines)} samples...")
    for i, line in enumerate(tqdm(lines)):
        parts = line.strip().split(",")
        if len(parts) < 3:
            continue
        uid, img_path, code_path = parts
        # Resolve possible Docker paths or mismatched local paths
        img_path = resolve_path(img_path, input_dir)
        code_path = resolve_path(code_path, input_dir)
        # Skip if files are missing after resolving
        if img_path is None or code_path is None:
            continue
        # --- Image preprocessing ---
        out_img_path = os.path.join(output_dir, f"{uid}.png")
        try:
            preprocess_image(img_path, transform, out_img_path)
        except Exception as e:
            print(f"⚠️ Skipping {uid}: image error -> {e}")
            continue

        # --- Code cleanup ---
        try:
            with open(code_path, "r", encoding="utf-8") as f_code:
                raw_code = f_code.read()
            cleaned_code = clean_cadquery_code(raw_code)
        except Exception as e:
            print(f"⚠️ Skipping {uid}: code read error -> {e}")
            continue

        # --- Prompt ---
        prompt = (
            "Generate the CadQuery code needed to create the CAD object in the provided image. "
            "Return only executable CadQuery code, with no explanations."
        )

        processed_samples.append({
            "id": uid,
            "image_path": out_img_path,
            "prompt": prompt,
            "category": 'default',
             "code": cleaned_code
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
    parser.add_argument("--input_dir", type=str, required=True, help="Input directory from dataloader.py output")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory for processed data")
    parser.add_argument("--img_size", type=int, default=336, help="Resize dimension for CLIP preprocessing (default=336)")
    args = parser.parse_args()

    preprocess_dataset(args.input_dir, args.output_dir, args.img_size)
