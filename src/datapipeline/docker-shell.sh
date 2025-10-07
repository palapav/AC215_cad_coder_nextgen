#!/bin/bash
set -e

echo "🚀 Starting data pipeline..."
python dataloader.py
python preprocess_cv.py
python preprocess_rag.py
echo "✅ Data pipeline complete."
