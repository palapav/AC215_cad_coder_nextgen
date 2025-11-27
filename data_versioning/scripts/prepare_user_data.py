#!/usr/bin/env python
"""
Transform subset file into user data format for v2.

Takes the cadquery_test_data_subset100.jsonl file and transforms it
into user data format with minimal metadata.

Usage:
    python prepare_user_data.py \
        --input data_versioning/data/v2_data/cadquery_test_data_subset100.jsonl \
        --output data_versioning/data/user_data.jsonl
"""

import json
import argparse
from pathlib import Path
from datetime import datetime


def transform_to_user_data(input_file: Path, output_file: Path):
    """
    Transform subset file records into user data format.
    
    Args:
        input_file: Input JSONL file (subset format)
        output_file: Output JSONL file (user data format)
    """
    user_records = []
    
    print(f"Reading from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                record = json.loads(line)
                
                # Transform to user data format
                user_record = {
                    "question_id": f"user_{record.get('question_id', line_num)}",
                    "prompt": record.get("text", ""),
                    "llm_output": record.get("ground_truth", ""),
                    "image": record.get("image", ""),
                    "source": "user",
                    "data_version": "v2"
                }
                
                user_records.append(user_record)
                
            except json.JSONDecodeError as e:
                print(f"Warning: Error parsing line {line_num}: {e}")
                continue
    
    # Write user data file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in user_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"✅ Transformed {len(user_records)} records to user data format")
    print(f"📁 Output: {output_file}")
    return len(user_records)


def main():
    parser = argparse.ArgumentParser(
        description="Transform subset file to user data format"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input JSONL file (subset format)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output JSONL file (user data format)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Preparing User Data for V2")
    print("=" * 60)
    
    transform_to_user_data(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()

