#!/bin/bash
# Master script to create V1 and V2 datasets

# Don't exit on error - we want to handle missing files gracefully
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Creating Data Versions V1 and V2"
echo "=========================================="

# Step 1: Convert raw data to V1 (skip if V1 already exists)
echo ""
echo "Step 1: Converting raw data to V1 (JSONL)..."
if [ -f "data/v1/train.jsonl" ] && [ -f "data/v1/validation.jsonl" ] && [ -f "data/v1/test.jsonl" ]; then
    echo "  ⚠️  V1 files already exist, skipping conversion..."
    echo "  To recreate V1, delete data/v1/*.jsonl first"
else
    python scripts/convert_raw_to_jsonl.py \
        --input-dir ../datapipeline/data_ingestion/data \
        --output-dir data
fi

# Step 2: Prepare user data (skip if user_data.jsonl already exists)
echo ""
echo "Step 2: Preparing user data from subset file..."
if [ -f "data/user_data.jsonl" ]; then
    echo "  ⚠️  user_data.jsonl already exists, skipping preparation..."
    echo "  To recreate user data, delete data/user_data.jsonl first"
else
    # Try multiple possible locations for the subset file
    SUBSET_FILE=""
    for path in \
        "model_inference_data/cadquery_test_data_subset100.jsonl" \
        "../model_inference/inference/cadquery_test_data_subset100.jsonl" \
        "data/v2_data/cadquery_test_data_subset100.jsonl"; do
        if [ -f "$path" ]; then
            SUBSET_FILE="$path"
            break
        fi
    done
    
    if [ -z "$SUBSET_FILE" ]; then
        echo "  ⚠️  Subset file not found, skipping user data preparation..."
        echo "  Expected locations:"
        echo "    - model_inference_data/cadquery_test_data_subset100.jsonl"
        echo "    - ../model_inference/inference/cadquery_test_data_subset100.jsonl"
        echo "    - data/v2_data/cadquery_test_data_subset100.jsonl"
    else
        echo "  Using subset file: $SUBSET_FILE"
        python scripts/prepare_user_data.py \
            --input "$SUBSET_FILE" \
            --output data/user_data.jsonl
    fi
fi

# Step 3: Create V2 (skip if V2 already exists)
echo ""
echo "Step 3: Creating V2 (V1 + User data)..."
if [ -f "data/v2/train.jsonl" ] && [ -f "data/v2/validation.jsonl" ] && [ -f "data/v2/test.jsonl" ]; then
    echo "  ⚠️  V2 files already exist, skipping creation..."
    echo "  To recreate V2, delete data/v2/*.jsonl first"
else
    if [ ! -f "data/user_data.jsonl" ]; then
        echo "  ⚠️  user_data.jsonl not found, creating V2 without user data (V2 = V1)..."
        # Create V2 as a copy of V1 if no user data
        mkdir -p data/v2
        cp data/v1/train.jsonl data/v2/train.jsonl 2>/dev/null || echo "  ⚠️  V1 train.jsonl not found"
        cp data/v1/validation.jsonl data/v2/validation.jsonl 2>/dev/null || echo "  ⚠️  V1 validation.jsonl not found"
        cp data/v1/test.jsonl data/v2/test.jsonl 2>/dev/null || echo "  ⚠️  V1 test.jsonl not found"
    else
        python scripts/create_v2.py \
            --v1-dir data/v1 \
            --user-data data/user_data.jsonl \
            --output-dir data/v2
    fi
fi

echo ""
echo "=========================================="
echo "✅ All versions created successfully!"
echo "=========================================="
echo ""
echo "Next step: Run ./setup_dvc.sh to initialize DVC versioning"
echo ""

