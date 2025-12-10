#!/usr/bin/env python3
"""
Prepare training data for ML workflow.

Converts JSONL files to HuggingFace datasets and partitions them for federated learning.
"""

import os
import json
import argparse
import shutil
from pathlib import Path
from datasets import Dataset, load_dataset
from typing import List, Dict, Any


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSONL file into list of dictionaries."""
    data = []
    jsonl_dir = file_path.parent  # Directory containing the JSONL file
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                
                # Fix image paths - convert absolute paths to relative or fix them
                if 'image' in item:
                    image_path = item['image']
                    # If it's an absolute path from another machine, try to find the image locally
                    if image_path.startswith('/') and not Path(image_path).exists():
                        # Extract filename from path
                        image_filename = Path(image_path).name
                        # Try to find it in the same directory as the JSONL file
                        local_image_path = jsonl_dir / image_filename
                        if local_image_path.exists():
                            # Use relative path from JSONL file location
                            # When dataset is saved, paths will be relative to dataset location
                            item['image'] = str(image_filename)  # Just the filename, will be resolved relative to dataset
                        else:
                            print(f"⚠️  Warning: Image not found at {image_path} or {local_image_path}")
                    # If it's already a relative path or exists, keep it
                    elif not Path(image_path).exists() and not image_path.startswith('./'):
                        # Try to find it relative to JSONL file
                        local_image_path = jsonl_dir / image_path
                        if local_image_path.exists():
                            item['image'] = Path(image_path).name  # Use just filename
                
                # Ensure required fields exist for training
                # Training expects 'code' or 'cadquery' field
                if 'code' not in item and 'cadquery' not in item:
                    # Add placeholder code if missing (user should provide real CAD code)
                    if 'text' in item:
                        # Use text as a placeholder, but this won't be valid CAD code
                        item['code'] = f"# Placeholder code for: {item.get('text', 'unknown')}\nimport cadquery as cq\nresult = cq.Workplane().box(1, 1, 1)"
                    else:
                        item['code'] = "import cadquery as cq\nresult = cq.Workplane().box(1, 1, 1)"
                    print(f"⚠️  Warning: Sample missing 'code' field, added placeholder. Real training data needs actual CAD code.")
                # Map 'cadquery' to 'code' if needed (training code does this too, but do it here for consistency)
                if 'cadquery' in item and 'code' not in item:
                    item['code'] = item['cadquery']
                data.append(item)
    return data


def create_partitioned_datasets(
    train_jsonl: Path,
    validation_jsonl: Path,
    test_jsonl: Path,
    output_dir: Path,
    client1_ratio: float = 0.5,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1
):
    """
    Create partitioned datasets for federated learning.
    
    Args:
        train_jsonl: Path to training JSONL file (or combined dataset)
        validation_jsonl: Path to validation JSONL file (optional)
        test_jsonl: Path to test JSONL file (optional)
        output_dir: Output directory for partitioned datasets
        client1_ratio: Ratio of data for client1 (default: 0.5, i.e., 50/50 split)
        train_ratio: Ratio of data for training if splitting from single file (default: 0.8)
        val_ratio: Ratio of data for validation if splitting from single file (default: 0.1)
    """
    print("=" * 60)
    print("Preparing Partitioned Training Data")
    print("=" * 60)
    
    # Load JSONL files
    print(f"\nLoading data from JSONL files...")
    print(f"  Train: {train_jsonl}")
    train_data = load_jsonl(train_jsonl) if train_jsonl and train_jsonl.exists() else []
    print(f"    Loaded {len(train_data)} training samples")
    
    val_data = []
    if validation_jsonl and validation_jsonl.exists():
        print(f"  Validation: {validation_jsonl}")
        val_data = load_jsonl(validation_jsonl)
        print(f"    Loaded {len(val_data)} validation samples")
    
    test_data = []
    if test_jsonl and test_jsonl.exists():
        print(f"  Test: {test_jsonl}")
        test_data = load_jsonl(test_jsonl)
        print(f"    Loaded {len(test_data)} test samples")
    
    # If only train data provided, split it into train/val/test
    if train_data and not val_data and not test_data:
        print(f"\n⚠️  Only training data provided. Splitting into train/val/test...")
        n_total = len(train_data)
        
        # For very small datasets, put everything in training
        if n_total <= 2:
            print(f"  ⚠️  Dataset too small ({n_total} samples). Using all for training.")
            val_data = []
            test_data = []
        else:
            n_train = max(1, int(n_total * train_ratio))  # At least 1 sample for training
            n_val = max(0, int(n_total * val_ratio))
            n_test = n_total - n_train - n_val  # Remaining goes to test
            
            # Shuffle data before splitting
            import random
            random.seed(42)  # For reproducibility
            shuffled = train_data.copy()
            random.shuffle(shuffled)
            
            train_data = shuffled[:n_train]
            val_data = shuffled[n_train:n_train + n_val] if n_val > 0 else []
            test_data = shuffled[n_train + n_val:] if n_test > 0 else []
        
        print(f"  Split: {len(train_data)} train, {len(val_data)} val, {len(test_data)} test")
    
    if not train_data:
        raise ValueError(f"No training data found at {train_jsonl}")
    
    # Convert to HuggingFace datasets
    print(f"\nConverting to HuggingFace datasets...")
    train_dataset = Dataset.from_list(train_data)
    val_dataset = Dataset.from_list(val_data) if val_data else None
    test_dataset = Dataset.from_list(test_data) if test_data else None
    
    # Partition training data into client1 and client2
    print(f"\nPartitioning training data (client1: {client1_ratio*100:.0f}%, client2: {(1-client1_ratio)*100:.0f}%)...")
    n_train = len(train_dataset)
    n_client1 = int(n_train * client1_ratio)
    
    client1_train = train_dataset.select(range(n_client1))
    client2_train = train_dataset.select(range(n_client1, n_train))
    
    print(f"  Client1: {len(client1_train)} samples")
    print(f"  Client2: {len(client2_train)} samples")
    
    # Create output directories
    client1_dir = output_dir / "client1"
    client2_dir = output_dir / "client2"
    validation_dir = output_dir / "validation"
    test_dir = output_dir / "test"
    
    for dir_path in [client1_dir, client2_dir, validation_dir, test_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Copy images to dataset directories and fix image paths
    print(f"\n📸 Copying images and fixing image paths...")
    def copy_images_and_fix_paths(dataset, dataset_dir: Path, source_dir: Path):
        """Copy images to dataset directory and update paths to be relative."""
        images_dir = dataset_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        def fix_item(item):
            if 'image' in item:
                image_path = item['image']
                # If it's a string path, try to find and copy the image
                if isinstance(image_path, str):
                    # Try to find the image file
                    potential_paths = [
                        Path(image_path),  # Original path
                        source_dir / Path(image_path).name,  # Same directory as JSONL
                        source_dir.parent / Path(image_path).name,  # Parent directory  
                    ]
                    
                    image_file = None
                    for path in potential_paths:
                        if path.exists() and path.is_file():
                            image_file = path
                            break
                    
                    if image_file:
                        # Copy image to dataset images directory
                        image_filename = image_file.name
                        dest_image = images_dir / image_filename
                        if not dest_image.exists():
                            shutil.copy2(image_file, dest_image)
                            print(f"    Copied image: {image_file.name}")
                        
                        # Store absolute path that will work in Modal
                        # Dataset will be at /data/data/partitioned/client1 when loaded in Modal
                        # So image path should be /data/data/partitioned/client1/images/27.png
                        # Convert local path to Modal path
                        dataset_path_str = str(dataset_dir)
                        if "data/partitioned" in dataset_path_str:
                            # Replace local path with Modal volume path
                            modal_dataset_path = dataset_path_str.replace("data/partitioned", "/data/data/partitioned")
                            item['image'] = f"{modal_dataset_path}/images/{image_filename}"
                        else:
                            # Fallback: use relative path (won't work but better than nothing)
                            item['image'] = f"images/{image_filename}"
                    else:
                        print(f"    ⚠️  Warning: Image not found: {image_path}")
                        print(f"       Searched in: {[str(p) for p in potential_paths]}")
            return item
        
        # Apply fix to all items
        fixed_data = []
        for item in dataset:
            try:
                fixed_item = fix_item(item.copy())
                fixed_data.append(fixed_item)
            except Exception as e:
                print(f"    ⚠️  Warning: Failed to process item: {e}")
                continue
        
        return Dataset.from_list(fixed_data) if fixed_data else dataset
    
    # Copy images and fix paths for all datasets
    if len(client1_train) > 0:
        client1_train = copy_images_and_fix_paths(client1_train, client1_dir, train_jsonl.parent)
    if len(client2_train) > 0:
        client2_train = copy_images_and_fix_paths(client2_train, client2_dir, train_jsonl.parent)
    if val_dataset and len(val_dataset) > 0:
        val_dataset = copy_images_and_fix_paths(val_dataset, validation_dir, train_jsonl.parent)
    if test_dataset and len(test_dataset) > 0:
        test_dataset = copy_images_and_fix_paths(test_dataset, test_dir, train_jsonl.parent)
    
    # Save datasets
    print(f"\nSaving datasets...")
    print(f"  Client1: {client1_dir}")
    client1_train.save_to_disk(str(client1_dir))
    print(f"    ✓ Saved {len(client1_train)} samples")
    
    print(f"  Client2: {client2_dir}")
    client2_train.save_to_disk(str(client2_dir))
    print(f"    ✓ Saved {len(client2_train)} samples")
    
    if val_dataset:
        print(f"  Validation: {validation_dir}")
        val_dataset.save_to_disk(str(validation_dir))
        print(f"    ✓ Saved {len(val_dataset)} samples")
    
    if test_dataset:
        print(f"  Test: {test_dir}")
        test_dataset.save_to_disk(str(test_dir))
        print(f"    ✓ Saved {len(test_dataset)} samples")
    
    print(f"\n✅ Partitioned datasets created successfully!")
    print(f"   Output directory: {output_dir}")
    print(f"   Client1: {client1_dir}")
    print(f"   Client2: {client2_dir}")
    if val_dataset:
        print(f"   Validation: {validation_dir}")
    if test_dataset:
        print(f"   Test: {test_dir}")


def main():
    parser = argparse.ArgumentParser(description="Prepare partitioned training data")
    parser.add_argument(
        "--train-jsonl",
        type=str,
        default="./src/data/dataset.jsonl",
        help="Path to training JSONL file (or combined dataset)"
    )
    parser.add_argument(
        "--validation-jsonl",
        type=str,
        default=None,
        help="Path to validation JSONL file (optional, will split from train if not provided)"
    )
    parser.add_argument(
        "--test-jsonl",
        type=str,
        default=None,
        help="Path to test JSONL file (optional, will split from train if not provided)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data/partitioned",
        help="Output directory for partitioned datasets"
    )
    parser.add_argument(
        "--client1-ratio",
        type=float,
        default=0.5,
        help="Ratio of training data for client1 (default: 0.5)"
    )
    
    args = parser.parse_args()
    
    # Convert to Path objects
    train_jsonl = Path(args.train_jsonl)
    validation_jsonl = Path(args.validation_jsonl) if args.validation_jsonl else None
    test_jsonl = Path(args.test_jsonl) if args.test_jsonl else None
    output_dir = Path(args.output_dir)
    
    # Check if JSONL files exist
    if not train_jsonl.exists():
        print(f"⚠️  Training JSONL not found at {train_jsonl}")
        print(f"   Please check the path or provide --train-jsonl argument")
        return
    
    create_partitioned_datasets(
        train_jsonl=train_jsonl,
        validation_jsonl=validation_jsonl if validation_jsonl else None,
        test_jsonl=test_jsonl if test_jsonl else None,
        output_dir=output_dir,
        client1_ratio=args.client1_ratio
    )


if __name__ == "__main__":
    main()

