"""
dataloader.py
--------------
Data Ingestion Script for CAD-Coder / GenCAD-Code dataset (Test Split Only)

This script loads ONLY the test split from the Hugging Face dataset
`CADCODER/GenCAD-Code`, saves the image and CadQuery code locally,
and builds an index CSV for downstream preprocessing.

Usage:
    python dataloader.py --output_dir ./data/raw_test
"""

import os
import argparse
from datasets import load_dataset

def load_gencad_test_dataset(output_dir: str = "./data/raw_test"):
    """
    Loads only the TEST split from the GenCAD-Code dataset and saves locally.
    """

    print("🔹 Loading TEST split from Hugging Face...")
    # Requires login: `huggingface-cli login`
    ds = load_dataset("CADCODER/GenCAD-Code", split="test")

    os.makedirs(output_dir, exist_ok=True)
    print(f"📂 Saving {len(ds)} samples to {output_dir}")

    # Create a simple CSV index to track image/script paths
    index_file = os.path.join(output_dir, "index.csv")
    with open(index_file, "w", encoding="utf-8") as f:
        f.write("id,image_path,script_path\n")

    # Loop through all records in test split
    for i, record in enumerate(ds):
        img = record.get("image")
        code = record.get("cadquery") or record.get("cad_code")
        uid = record.get("uid", f"test_{i}")

        # Define output file paths
        img_path = os.path.join(output_dir, f"{uid}.png")
        code_path = os.path.join(output_dir, f"{uid}.py")

        # Save image
        if img is not None:
            img.save(img_path)

        # Save code text
        if code is not None:
            with open(code_path, "w", encoding="utf-8") as f_code:
                f_code.write(code)

        # Log file paths in CSV
        with open(index_file, "a", encoding="utf-8") as f:
            f.write(f"{uid},{img_path},{code_path}\n")

        # Print progress occasionally
        if (i + 1) % 1000 == 0:
            print(f"   ✅ Processed {i + 1} samples...")

    print(f"🎯 Completed ingestion for TEST split. Total samples: {len(ds)}")
    print(f"📑 Index file saved at: {index_file}")
    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load only the test split from GenCAD-Code dataset")
    parser.add_argument("--output_dir", type=str, default="./data/raw_test", help="Directory to save test data")
    args = parser.parse_args()

    load_gencad_test_dataset(args.output_dir)
