#!/usr/bin/env python
"""
dataloader.py
--------------
Data Ingestion Script for CAD-Coder / GenCAD-Code dataset (All Splits)

This script loads the TRAIN, VALIDATION, and TEST splits from the
`CADCODER/GenCAD-Code` dataset, saves all locally, and builds
CSV indices for downstream preprocessing.

Usage:
    python dataloader.py --output_dir ./data/raw_all
"""

import os
import argparse
from datasets import load_dataset
from google.cloud import storage

def upload_to_gcs(bucket_name, source_file_path, destination_blob_name):
    """Uploads a local file to a GCS bucket."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_path)
    print(f"☁️ Uploaded to gs://{bucket_name}/{destination_blob_name}")

def load_gencad_full_dataset(output_dir: str = "./data/raw_all"):
    """
    Loads all splits (train, validation, test) from the GenCAD-Code dataset and saves locally.
    """

    print("🔹 Loading ALL splits (train, validation, test) from Hugging Face...")
    # Requires login: `huggingface-cli login`
    ds_dict = load_dataset("CADCODER/GenCAD-Code")

    for split_name, ds in ds_dict.items():
        split_dir = os.path.join(output_dir, split_name)
        os.makedirs(split_dir, exist_ok=True)
        print(f"📂 Saving {len(ds)} samples from {split_name} split to {split_dir}")

        # Create a simple CSV index to track image/script paths
        index_file = os.path.join(split_dir, "index.csv")
        with open(index_file, "w", encoding="utf-8") as f:
            f.write("id,image_path,script_path\n")

        # Loop through all records in each split
        for i, record in enumerate(ds):
            img = record.get("image")
            code = record.get("cadquery") or record.get("cad_code")
            uid = record.get("uid", f"{split_name}_{i}")

            # Define output file paths
            img_path = os.path.join(split_dir, f"{uid}.png")
            code_path = os.path.join(split_dir, f"{uid}.py")

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
                print(f"   ✅ Processed {i + 1} samples from {split_name}...")

            #Upload to GCS
            try:
                upload_to_gcs(
                    bucket_name="cad-coder-nextgen-data",
                    source_file_path=img_path,
                    destination_blob_name=f"raw_data/{split_name}/{uid}.png"
                )
                upload_to_gcs(
                    bucket_name="cad-coder-nextgen-data",
                    source_file_path=code_path,
                    destination_blob_name=f"raw_data/{split_name}/{uid}.py"
                )
            except Exception as e:
                print(f"⚠️ GCS upload failed for {uid}: {e}")

    print(f"🎯 Completed ingestion for all splits.")
    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load all splits from GenCAD-Code dataset")
    parser.add_argument("--output_dir", type=str, default="./data/raw_all", help="Directory to save all data")
    args = parser.parse_args()

    load_gencad_full_dataset(args.output_dir)
