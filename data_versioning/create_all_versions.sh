#!/bin/bash
# Master script to create V1 and V2 datasets

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Creating Data Versions V1 and V2"
echo "=========================================="

# Step 1: Convert raw data to V1
echo ""
echo "Step 1: Converting raw data to V1 (JSONL)..."
python scripts/convert_raw_to_jsonl.py \
    --input-dir ../datapipeline/data_ingestion/data \
    --output-dir data

# Step 2: Prepare user data
echo ""
echo "Step 2: Preparing user data from subset file..."
python scripts/prepare_user_data.py \
    --input data/v2_data/cadquery_test_data_subset100.jsonl \
    --output data/user_data.jsonl

# Step 3: Create V2
echo ""
echo "Step 3: Creating V2 (V1 + User data)..."
python scripts/create_v2.py \
    --v1-dir data/v1 \
    --user-data data/user_data.jsonl \
    --output-dir data/v2

echo ""
echo "=========================================="
echo "✅ All versions created successfully!"
echo "=========================================="
echo ""
echo "Next step: Run ./setup_dvc.sh to initialize DVC versioning"
echo ""

