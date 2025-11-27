#!/bin/bash
# Setup DVC for data versioning (local only)

set -e

echo "=========================================="
echo "Setting up DVC for Data Versioning"
echo "=========================================="

# Navigate to data_versioning directory
cd "$(dirname "$0")"

# Initialize DVC (if not already initialized)
if [ ! -d ".dvc" ]; then
    echo "Initializing DVC..."
    dvc init --no-scm
    echo "✅ DVC initialized"
else
    echo "DVC already initialized"
fi

# Add data directories to DVC
echo ""
echo "Adding data versions to DVC..."

if [ -d "data/v1" ]; then
    echo "  Adding v1 data..."
    dvc add data/v1/train.jsonl data/v1/validation.jsonl data/v1/test.jsonl
    echo "  ✅ V1 data tracked"
else
    echo "  ⚠️  V1 data not found, skipping..."
fi

if [ -d "data/v2" ]; then
    echo "  Adding v2 data..."
    dvc add data/v2/train.jsonl data/v2/validation.jsonl data/v2/test.jsonl
    echo "  ✅ V2 data tracked"
else
    echo "  ⚠️  V2 data not found, skipping..."
fi

echo ""
echo "=========================================="
echo "✅ DVC setup complete!"
echo "=========================================="
echo ""
echo "To view tracked files:"
echo "  dvc list ."
echo ""
echo "To check data status:"
echo "  dvc status"
echo ""

