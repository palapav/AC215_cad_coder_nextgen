#!/bin/bash
set -e

echo "🚀 Starting model training..."
python train_model.py
python infer_model.py
echo "✅ Model pipeline complete."
