#!/usr/bin/env python
"""
dataloader.py
--------------
Data Ingestion Script for CAD-Coder / GenCAD-Code dataset

Loads data from HuggingFace and uploads directly to Google Cloud Storage.

Features:
- Select specific splits (train, validation, test, or all)
- Limit number of samples per split (for testing)
- Direct upload to GCS (no local storage needed)

Usage:
    # Test with 5 samples from test split
    python dataloader.py --bucket cad-coder-nextgen-data --splits test --limit 5
    
    # Full train split
    python dataloader.py --bucket cad-coder-nextgen-data --splits train
    
    # All splits, 100 samples each
    python dataloader.py --bucket cad-coder-nextgen-data --splits all --limit 100
"""

import os
import argparse
import tempfile
import logging
from datasets import load_dataset
from google.cloud import storage
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def upload_to_gcs(bucket_name, source_file_path, destination_blob_name):
    """Uploads a file to GCS bucket."""
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_path)
        return True
    except Exception as e:
        logging.error(f"Failed to upload {destination_blob_name}: {e}")
        return False


def ingest_dataset_to_gcs(
    bucket_name: str,
    splits: list = None,
    limit: int = None
):
    """
    Load CAD-Coder dataset from HuggingFace and upload directly to GCS.
    
    Args:
        bucket_name: GCS bucket name
        splits: List of splits to process (e.g., ['train', 'test']) or ['all']
        limit: Maximum samples per split (None = all samples)
    
    Returns:
        dict: Statistics about uploaded data
    """
    
    logging.info("=" * 60)
    logging.info("🚀 CAD-CODER DATA INGESTION PIPELINE")
    logging.info("=" * 60)
    
    # Check for HF_TOKEN
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        logging.info("🔑 Using HF_TOKEN for authentication")
    else:
        logging.warning("⚠️  HF_TOKEN not set - may need interactive login")
    
    # Load dataset from HuggingFace
    logging.info("📥 Loading dataset from HuggingFace: CADCODER/GenCAD-Code")
    
    try:
        ds_dict = load_dataset("CADCODER/GenCAD-Code", token=hf_token)
    except Exception as e:
        logging.error(f"Failed to load dataset: {e}")
        raise
    
    # Determine which splits to process
    available_splits = list(ds_dict.keys())
    if splits is None or 'all' in splits:
        selected_splits = available_splits
    else:
        selected_splits = [s for s in splits if s in available_splits]
    
    logging.info(f"📊 Available splits: {available_splits}")
    logging.info(f"✅ Processing splits: {selected_splits}")
    if limit:
        logging.info(f"⚠️  LIMIT: {limit} samples per split")
    
    stats = {
        'total_uploaded': 0,
        'total_failed': 0,
        'splits': {}
    }
    
    # Process each split
    for split_name in selected_splits:
        logging.info(f"\n{'='*60}")
        logging.info(f"Processing split: {split_name.upper()}")
        logging.info(f"{'='*60}")
        
        ds = ds_dict[split_name]
        total_samples = len(ds)
        
        # Apply limit
        if limit and limit < total_samples:
            ds = ds.select(range(limit))
            logging.info(f"📉 Limited to {limit} samples (from {total_samples} total)")
        else:
            logging.info(f"📈 Processing all {total_samples} samples")
        
        split_stats = {'uploaded': 0, 'failed': 0}
        
        # Use temporary directory for staging files before GCS upload
        with tempfile.TemporaryDirectory() as temp_dir:
            logging.info(f"📁 Using temp directory: {temp_dir}")
            
            for i, record in enumerate(ds):
                img = record.get("image")
                code = record.get("cadquery") or record.get("cad_code")
                uid = record.get("uid", f"{split_name}_{i}")
                
                # Create temp file paths
                temp_img = os.path.join(temp_dir, f"{uid}.png")
                temp_code = os.path.join(temp_dir, f"{uid}.py")
                
                try:
                    # Save image temporarily
                    if img is not None:
                        img.save(temp_img)
                        
                        # Upload to GCS
                        gcs_img_path = f"raw_data/{split_name}/{uid}.png"
                        if upload_to_gcs(bucket_name, temp_img, gcs_img_path):
                            split_stats['uploaded'] += 1
                        else:
                            split_stats['failed'] += 1
                    
                    # Save code temporarily
                    if code is not None:
                        with open(temp_code, "w", encoding="utf-8") as f:
                            f.write(code)
                        
                        # Upload to GCS
                        gcs_code_path = f"raw_data/{split_name}/{uid}.py"
                        if upload_to_gcs(bucket_name, temp_code, gcs_code_path):
                            split_stats['uploaded'] += 1
                        else:
                            split_stats['failed'] += 1
                    
                    # Progress logging
                    if (i + 1) % 10 == 0 or (i + 1) == len(ds):
                        logging.info(f"   ✅ Progress: {i + 1}/{len(ds)} samples processed")
                
                except Exception as e:
                    logging.error(f"❌ Error processing {uid}: {e}")
                    split_stats['failed'] += 2  # Both image and code
        
        logging.info(f"✅ Split '{split_name}' complete:")
        logging.info(f"   - Uploaded: {split_stats['uploaded']} files")
        logging.info(f"   - Failed: {split_stats['failed']} files")
        
        stats['splits'][split_name] = split_stats
        stats['total_uploaded'] += split_stats['uploaded']
        stats['total_failed'] += split_stats['failed']
    
    # Final summary
    logging.info(f"\n{'='*60}")
    logging.info("🎯 INGESTION COMPLETE")
    logging.info(f"{'='*60}")
    logging.info(f"✅ Total files uploaded: {stats['total_uploaded']}")
    logging.info(f"❌ Total files failed: {stats['total_failed']}")
    logging.info(f"📦 GCS Bucket: gs://{bucket_name}/raw_data/")
    
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest CAD-Coder dataset from HuggingFace to Google Cloud Storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with 5 samples from test split
  python dataloader.py --bucket cad-coder-nextgen-data --splits test --limit 5
  
  # Full train split
  python dataloader.py --bucket cad-coder-nextgen-data --splits train
  
  # All splits with 100 samples each
  python dataloader.py --bucket cad-coder-nextgen-data --splits all --limit 100
  
  # Multiple specific splits
  python dataloader.py --bucket cad-coder-nextgen-data --splits train validation --limit 50
        """
    )
    
    parser.add_argument(
        "--bucket",
        type=str,
        required=True,
        help="GCS bucket name (e.g., cad-coder-nextgen-data)"
    )
    
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["all"],
        choices=["all", "train", "validation", "test"],
        help="Which splits to process (default: all)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit samples per split (for testing, e.g., --limit 10)"
    )
    
    args = parser.parse_args()
    
    # Run ingestion
    try:
        stats = ingest_dataset_to_gcs(
            bucket_name=args.bucket,
            splits=args.splits,
            limit=args.limit
        )
        
        # Exit with success
        exit(0 if stats['total_failed'] == 0 else 1)
        
    except Exception as e:
        logging.error(f"❌ Ingestion failed: {e}")
        exit(1)
