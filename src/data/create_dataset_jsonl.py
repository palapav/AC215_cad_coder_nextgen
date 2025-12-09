#!/usr/bin/env python3
"""
Create dataset.jsonl from train_*.py and train_*.png files.

This script scans the data directory for train_*.png files, finds their
corresponding train_*.py files, and creates a dataset.jsonl file with
all the training samples.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any


def create_dataset_jsonl(data_dir: Path, output_file: Path):
    """
    Create dataset.jsonl from train_*.py and train_*.png files.
    
    Args:
        data_dir: Directory containing train_*.py and train_*.png files
        output_file: Output JSONL file path
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise ValueError(f"Data directory not found: {data_dir}")
    
    # Find all train_*.png files
    png_files = sorted(data_path.glob("train_*.png"))
    
    if len(png_files) == 0:
        print(f"⚠️  No train_*.png files found in {data_dir}")
        return 0
    
    print(f"Found {len(png_files)} PNG files")
    
    records = []
    skipped = 0
    
    for png_file in png_files:
        # Get base name (e.g., "train_0" from "train_0.png")
        base_name = png_file.stem
        
        # Find corresponding Python file
        py_file = data_path / f"{base_name}.py"
        
        if not py_file.exists():
            print(f"⚠️  Warning: No corresponding .py file for {png_file.name}, skipping...")
            skipped += 1
            continue
        
        # Read Python code
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                code = f.read().strip()
        except Exception as e:
            print(f"⚠️  Error reading {py_file}: {e}, skipping...")
            skipped += 1
            continue
        
        # Extract question_id from filename (e.g., "train_0" -> "0" or "train_1087" -> "1087")
        question_id = base_name.replace("train_", "")
        try:
            question_id = int(question_id)
        except ValueError:
            # If not a number, use the full base_name
            question_id = base_name
        
        # Create record matching the expected format
        # Training code expects 'code' or 'cadquery' field
        record = {
            "question_id": question_id,
            "image": png_file.name,  # Just the filename, will be resolved relative to dataset
            "text": "Generate the CADQuery code needed to create the CAD for the provided image. Just the code, no other words.",
            "category": "default",
            "code": code  # Use 'code' field as expected by training code
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
    
    print(f"\n✅ Created dataset.jsonl with {len(records)} records")
    if skipped > 0:
        print(f"⚠️  Skipped {skipped} files (missing .py files or read errors)")
    print(f"📁 Output: {output_file}")
    
    return len(records)


def main():
    parser = argparse.ArgumentParser(
        description="Create dataset.jsonl from train_*.py and train_*.png files"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./src/data",
        help="Directory containing train_*.py and train_*.png files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./src/data/dataset.jsonl",
        help="Output JSONL file path"
    )
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    output_file = Path(args.output)
    
    print("=" * 60)
    print("Creating dataset.jsonl from training files")
    print("=" * 60)
    print(f"Data directory: {data_dir}")
    print(f"Output file: {output_file}")
    print()
    
    count = create_dataset_jsonl(data_dir, output_file)
    
    print("=" * 60)
    print(f"✅ Complete: {count} records written")
    print("=" * 60)


if __name__ == "__main__":
    main()

