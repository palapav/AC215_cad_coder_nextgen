#!/usr/bin/env python3
"""
Quick test script to call the deployed LLaVA Modal function.
Similar to call_qwen.py but for the LLaVA CAD-Coder model.

Usage:
    python call_llava.py
"""

import modal
from pathlib import Path

APP_NAME = "cad-coder-llava"  # must match APP_NAME in modal_app.py


def main():
    # Look up the deployed function in Modal
    llava_modal_infer = modal.Function.from_name(APP_NAME, "llava_modal_infer")

    # Use a test image (adjust path as needed)
    image_path = "src/data/15.png"
    if not Path(image_path).exists():
        # Try alternative paths
        alt_paths = [
            "src/model_inference/qwen/15.png",
            "../qwen/15.png",
            "15.png",
        ]
        for alt in alt_paths:
            if Path(alt).exists():
                image_path = alt
                break
        else:
            print(f"Error: Could not find test image. Tried: {image_path}, {alt_paths}")
            return

    img_bytes = Path(image_path).read_bytes()

    result = llava_modal_infer.remote(
        prompt="Generate the CadQuery code needed to create the CAD for the provided image. Just the code, no other words.",
        image_bytes=img_bytes,
        image_format="PNG",
        max_new_tokens=3450,
        temperature=0.0,
    )

    print("------ CAD-Coder LLaVA (Modal) Output ------")
    print(result)


if __name__ == "__main__":
    main()

