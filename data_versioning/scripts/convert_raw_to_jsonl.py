#!/usr/bin/env python
"""
Convert raw PNG/PY files to JSONL format for data versioning.

Converts the GenCAD-Code dataset from raw format (PNG images + Python code files)
to JSONL format matching the subset file structure.

Usage:
    python convert_raw_to_jsonl.py \
        --input-dir datapipeline/data_ingestion/data/raw_data \
        --output-dir data_versioning/data/v1
"""

import os
import json
import argparse
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO


def convert_split_to_jsonl(input_dir: Path, output_file: Path, split_name: str):
    """
    Convert a split (train/validation/test) from PNG/PY format to JSONL.
    
    Args:
        input_dir: Directory containing PNG and PY files (e.g., raw_data/train/)
        output_file: Output JSONL file path
        split_name: Name of the split (train/validation/test)
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Warning: {input_path} does not exist, skipping...")
        return 0
    
    # Find all PNG files
    png_files = sorted(input_path.glob("*.png"))
    
    if len(png_files) == 0:
        print(f"Warning: No PNG files found in {input_path}")
        return 0
    
    print(f"Processing {split_name}: {len(png_files)} images found")
    
    records = []
    for png_file in png_files:
        # Get base name (without extension)
        base_name = png_file.stem
        
        # Find corresponding Python file
        py_file = input_path / f"{base_name}.py"
        
        if not py_file.exists():
            print(f"Warning: No corresponding .py file for {png_file.name}, skipping...")
            continue
        
        # Read Python code
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            print(f"Error reading {py_file}: {e}, skipping...")
            continue
        
        # Create record matching the subset file format
        record = {
            "question_id": base_name,  # Use filename as ID
            "image": png_file.name,
            "text": "Generate the CADQuery code needed to create the CAD for the provided image. Just the code, no other words.",
            "category": "default",
            "ground_truth": code
        }
        
        records.append(record)
        
        # Progress indicator
        if len(records) % 100 == 0:
            print(f"  Processed {len(records)} records...")
    
    # Write JSONL file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"✅ {split_name}: {len(records)} records written to {output_file}")
    return len(records)


def main():
    parser = argparse.ArgumentParser(
        description="Convert raw PNG/PY files to JSONL format"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Input directory containing raw_data/ with train/validation/test subdirectories"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for JSONL files (will create v1/ subdirectory)"
    )
    
    args = parser.parse_args()
    
    input_base = Path(args.input_dir)
    output_base = Path(args.output_dir)
    v1_dir = output_base / "v1"
    v1_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Converting Raw Data to JSONL Format (V1)")
    print("=" * 60)
    
    total_records = 0
    
    # Process each split
    for split_name in ["train", "validation", "test"]:
        input_split_dir = input_base / "raw_data" / split_name
        output_file = v1_dir / f"{split_name}.jsonl"
        
        count = convert_split_to_jsonl(input_split_dir, output_file, split_name)
        total_records += count
    
    print("=" * 60)
    print(f"✅ Conversion complete: {total_records} total records")
    print(f"📁 Output directory: {v1_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()

