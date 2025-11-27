#!/usr/bin/env python
"""
Combine v1 data + user data → v2 dataset.

Takes v1 JSONL files and appends user data to create v2.

Usage:
    python create_v2.py \
        --v1-dir data_versioning/data/v1 \
        --user-data data_versioning/data/user_data.jsonl \
        --output-dir data_versioning/data/v2
"""

import json
import argparse
from pathlib import Path


def combine_v1_and_user_data(v1_dir: Path, user_data_file: Path, output_dir: Path):
    """
    Combine v1 data with user data to create v2.
    
    Args:
        v1_dir: Directory containing v1 JSONL files (train.jsonl, validation.jsonl, test.jsonl)
        user_data_file: User data JSONL file
        output_dir: Output directory for v2 JSONL files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read user data
    print(f"Reading user data from {user_data_file}...")
    user_records = []
    if user_data_file.exists():
        with open(user_data_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    user_records.append(json.loads(line))
        print(f"  Loaded {len(user_records)} user records")
    else:
        print(f"  Warning: {user_data_file} not found, proceeding without user data")
    
    # Process each split
    for split_name in ["train", "validation", "test"]:
        v1_file = v1_dir / f"{split_name}.jsonl"
        v2_file = output_dir / f"{split_name}.jsonl"
        
        if not v1_file.exists():
            print(f"Warning: {v1_file} not found, skipping {split_name}...")
            continue
        
        print(f"\nProcessing {split_name}...")
        
        # Read v1 data
        v1_records = []
        with open(v1_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    v1_records.append(json.loads(line))
        
        print(f"  V1 records: {len(v1_records)}")
        
        # Combine: v1 + user data
        v2_records = v1_records + user_records
        
        print(f"  User records added: {len(user_records)}")
        print(f"  Total V2 records: {len(v2_records)}")
        
        # Write v2 file
        with open(v2_file, 'w', encoding='utf-8') as f:
            for record in v2_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        print(f"  ✅ Written to {v2_file}")
    
    print("\n" + "=" * 60)
    print("✅ V2 dataset created successfully")
    print(f"📁 Output directory: {output_dir}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Combine v1 data + user data → v2"
    )
    parser.add_argument(
        "--v1-dir",
        type=str,
        required=True,
        help="Directory containing v1 JSONL files"
    )
    parser.add_argument(
        "--user-data",
        type=str,
        required=True,
        help="User data JSONL file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for v2 JSONL files"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Creating V2 Dataset (V1 + User Data)")
    print("=" * 60)
    
    combine_v1_and_user_data(
        Path(args.v1_dir),
        Path(args.user_data),
        Path(args.output_dir)
    )


if __name__ == "__main__":
    main()

