#!/usr/bin/env python
"""
preprocess_cv.py
----------------
Data Preprocessing for CAD-Coder dataset.

Reads raw data from GCS, processes images and code, uploads to GCS.

Features:
- Read raw data from GCS bucket
- CLIP-like image preprocessing (336x336)
- CAD code cleaning and normalization
- Generate multimodal JSONL
- Upload processed data to GCS

Usage:
    python preprocess_cv.py --bucket cad-coder-nextgen-data --splits test
"""

import os
import json
import re
import argparse
import tempfile
import logging
from PIL import Image
import torch
from torchvision import transforms
from google.cloud import storage
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# ============================================
# Helper Functions
# ============================================

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
    """Clean CadQuery code by removing comments, extra lines."""
    code = re.sub(r"#.*", "", code)
    code = re.sub(r"print\(.*?\)", "", code)
    lines = [line.rstrip() for line in code.splitlines() if line.strip()]
    code = "\n".join(lines)
    code = re.sub(r"\t", "    ", code)
    return code.strip()


def build_image_transform(img_size=336):
    """Create CLIP-like image preprocessing transform."""
    return transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])


def preprocess_image(pil_img, transform):
    """Preprocess PIL image and return as tensor."""
    pil_img = expand2square(pil_img, (0, 0, 0))
    tensor_img = transform(pil_img)
    return tensor_img


# ============================================
# GCS Functions
# ============================================

def download_from_gcs(bucket_name, blob_name):
    """Download file from GCS and return bytes."""
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.download_as_bytes()
    except Exception as e:
        logging.error(f"Failed to download {blob_name}: {e}")
        return None


def upload_to_gcs(bucket_name, source_file_path, destination_blob_name):
    """Upload file to GCS."""
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_path)
        return True
    except Exception as e:
        logging.error(f"Failed to upload {destination_blob_name}: {e}")
        return False


def list_gcs_files(bucket_name, prefix):
    """List all files in GCS bucket with given prefix."""
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]
    except Exception as e:
        logging.error(f"Failed to list files in gs://{bucket_name}/{prefix}: {e}")
        return []


# ============================================
# Main Preprocessing
# ============================================

def preprocess_split(
    bucket_name: str,
    split_name: str,
    img_size: int = 336
):
    """
    Preprocess one split from GCS.
    
    Args:
        bucket_name: GCS bucket name
        split_name: Split name (train/validation/test)
        img_size: Target image size
    
    Returns:
        dict: Statistics
    """
    
    logging.info(f"\n{'='*60}")
    logging.info(f"Processing split: {split_name.upper()}")
    logging.info(f"{'='*60}")
    
    # List raw files from GCS
    raw_prefix = f"raw_data/{split_name}/"
    logging.info(f"📥 Reading from: gs://{bucket_name}/{raw_prefix}")
    
    all_files = list_gcs_files(bucket_name, raw_prefix)
    image_files = [f for f in all_files if f.endswith('.png')]
    code_files = [f for f in all_files if f.endswith('.py')]
    
    logging.info(f"📊 Found {len(image_files)} images, {len(code_files)} code files")
    
    if not image_files or not code_files:
        logging.warning(f"⚠️  No data found in gs://{bucket_name}/{raw_prefix}")
        return {'processed': 0, 'failed': 0, 'jsonl_samples': 0}
    
    # Setup preprocessing
    transform = build_image_transform(img_size)
    stats = {'processed': 0, 'failed': 0, 'jsonl_samples': 0}
    jsonl_data = []
    
    # Process each image-code pair
    with tempfile.TemporaryDirectory() as temp_dir:
        logging.info(f"📁 Using temp directory: {temp_dir}")
        
        for img_blob in image_files:
            # Extract UID (e.g., "raw_data/test/test_0.png" -> "test_0")
            uid = img_blob.split('/')[-1].replace('.png', '')
            code_blob = f"raw_data/{split_name}/{uid}.py"
            
            if code_blob not in code_files:
                logging.warning(f"⚠️  No code file for {uid}, skipping")
                continue
            
            try:
                # Download image from GCS
                img_bytes = download_from_gcs(bucket_name, img_blob)
                if not img_bytes:
                    stats['failed'] += 1
                    continue
                
                # Download code from GCS
                code_bytes = download_from_gcs(bucket_name, code_blob)
                if not code_bytes:
                    stats['failed'] += 1
                    continue
                
                # Process image
                pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")
                tensor_img = preprocess_image(pil_img, transform)
                
                # Save processed image to temp
                processed_img = transforms.ToPILImage()(tensor_img)
                temp_img_path = os.path.join(temp_dir, f"{uid}.png")
                processed_img.save(temp_img_path)
                
                # Upload processed image to GCS
                gcs_img_path = f"processed_data/{split_name}/{uid}.png"
                if upload_to_gcs(bucket_name, temp_img_path, gcs_img_path):
                    stats['processed'] += 1
                else:
                    stats['failed'] += 1
                    continue
                
                # Process code
                raw_code = code_bytes.decode('utf-8')
                cleaned_code = clean_cadquery_code(raw_code)
                
                # Add to JSONL
                jsonl_data.append({
                    "id": uid,
                    "image_path": f"gs://{bucket_name}/{gcs_img_path}",
                    "prompt": "Generate the CadQuery code needed to create the CAD object in the provided image. Return only executable CadQuery code, with no explanations.",
                    "category": "default",
                    "code": cleaned_code
                })
                stats['jsonl_samples'] += 1
                
                if (stats['processed'] + stats['failed']) % 5 == 0:
                    logging.info(f"   ✅ Progress: {stats['processed']} processed, {stats['failed']} failed")
            
            except Exception as e:
                logging.error(f"❌ Error processing {uid}: {e}")
                stats['failed'] += 1
        
        # Save and upload JSONL
        if jsonl_data:
            jsonl_path = os.path.join(temp_dir, "dataset.jsonl")
            with open(jsonl_path, 'w', encoding='utf-8') as f:
                for sample in jsonl_data:
                    json.dump(sample, f)
                    f.write('\n')
            
            gcs_jsonl_path = f"processed_data/{split_name}/dataset.jsonl"
            if upload_to_gcs(bucket_name, jsonl_path, gcs_jsonl_path):
                logging.info(f"✅ Uploaded JSONL: gs://{bucket_name}/{gcs_jsonl_path}")
    
    logging.info(f"✅ Split '{split_name}' complete:")
    logging.info(f"   - Processed: {stats['processed']} images")
    logging.info(f"   - Failed: {stats['failed']} items")
    logging.info(f"   - JSONL samples: {stats['jsonl_samples']}")
    
    return stats


def preprocess_dataset(
    bucket_name: str,
    splits: list = None,
    img_size: int = 336
):
    """
    Preprocess CAD-Coder dataset from GCS.
    
    Args:
        bucket_name: GCS bucket name
        splits: List of splits to process
        img_size: Target image size
    
    Returns:
        dict: Overall statistics
    """
    
    logging.info("=" * 60)
    logging.info("🔧 CAD-CODER DATA PREPROCESSING PIPELINE")
    logging.info("=" * 60)
    
    # Determine splits
    if splits is None or 'all' in splits:
        selected_splits = ['train', 'validation', 'test']
    else:
        selected_splits = splits
    
    logging.info(f"✅ Processing splits: {selected_splits}")
    
    overall_stats = {
        'total_processed': 0,
        'total_failed': 0,
        'total_jsonl_samples': 0,
        'splits': {}
    }
    
    # Process each split
    for split_name in selected_splits:
        stats = preprocess_split(bucket_name, split_name, img_size)
        overall_stats['splits'][split_name] = stats
        overall_stats['total_processed'] += stats['processed']
        overall_stats['total_failed'] += stats['failed']
        overall_stats['total_jsonl_samples'] += stats['jsonl_samples']
    
    # Final summary
    logging.info(f"\n{'='*60}")
    logging.info("🎯 PREPROCESSING COMPLETE")
    logging.info(f"{'='*60}")
    logging.info(f"✅ Total images processed: {overall_stats['total_processed']}")
    logging.info(f"❌ Total failed: {overall_stats['total_failed']}")
    logging.info(f"📄 Total JSONL samples: {overall_stats['total_jsonl_samples']}")
    logging.info(f"📦 GCS Output: gs://{bucket_name}/processed_data/")
    
    return overall_stats


# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Preprocess CAD-Coder dataset from GCS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process test split
  python preprocess_cv.py --bucket cad-coder-nextgen-data --splits test
  
  # Process multiple splits
  python preprocess_cv.py --bucket cad-coder-nextgen-data --splits train validation
  
  # Process all splits
  python preprocess_cv.py --bucket cad-coder-nextgen-data --splits all
        """
    )
    
    parser.add_argument(
        "--bucket",
        type=str,
        required=True,
        help="GCS bucket name"
    )
    
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["test"],
        choices=["all", "train", "validation", "test"],
        help="Which splits to process (default: test)"
    )
    
    parser.add_argument(
        "--img_size",
        type=int,
        default=336,
        help="Target image size (default: 336)"
    )
    
    args = parser.parse_args()
    
    # Run preprocessing
    try:
        stats = preprocess_dataset(
            bucket_name=args.bucket,
            splits=args.splits,
            img_size=args.img_size
        )
        
        # Exit with success
        exit(0 if stats['total_failed'] == 0 else 1)
        
    except Exception as e:
        logging.error(f"❌ Preprocessing failed: {e}")
        exit(1)
