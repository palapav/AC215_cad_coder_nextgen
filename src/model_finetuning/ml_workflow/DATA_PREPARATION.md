# Training Data Preparation Guide

This guide explains how to prepare training data for the ML workflow. The workflow expects data in HuggingFace dataset format, partitioned for federated learning.

## Quick Start

If you have a single JSONL file at `src/data/dataset.jsonl`:

```bash
python src/model_finetuning/prepare_training_data.py
```

This will automatically:

- Load `src/data/dataset.jsonl`
- Split into train (80%), validation (10%), and test (10%)
- Partition training data into client1 (50%) and client2 (50%)
- Save to `./data/partitioned/` in HuggingFace dataset format

## Data Sources

The preparation script supports multiple data sources:

### Option 1: Single JSONL File (Simplest)

If you have a single JSONL file (e.g., `src/data/dataset.jsonl`):

```bash
python src/model_finetuning/prepare_training_data.py \
  --train-jsonl src/data/dataset.jsonl \
  --output-dir ./data/partitioned
```

The script will automatically split the data into train/validation/test.

### Option 2: Separate Train/Validation/Test Files

If you have separate JSONL files:

```bash
python src/model_finetuning/prepare_training_data.py \
  --train-jsonl src/data/train.jsonl \
  --validation-jsonl src/data/validation.jsonl \
  --test-jsonl src/data/test.jsonl \
  --output-dir ./data/partitioned
```

### Option 3: DVC-Tracked Data

If your data is tracked by DVC (e.g., in `src/data_versioning/data/v1/`):

### Step 1: Pull data from DVC

```bash
cd src/data_versioning
docker compose run --rm dvc dvc pull data/v1/train.jsonl data/v1/validation.jsonl data/v1/test.jsonl
```

Or if you have DVC installed locally:

```bash
cd src/data_versioning
dvc pull data/v1/train.jsonl data/v1/validation.jsonl data/v1/test.jsonl
```

### Step 2: Convert to partitioned datasets

```bash
python src/model_finetuning/prepare_training_data.py \
  --train-jsonl src/data_versioning/data/v1/train.jsonl \
  --validation-jsonl src/data_versioning/data/v1/validation.jsonl \
  --test-jsonl src/data_versioning/data/v1/test.jsonl \
  --output-dir ./data/partitioned
```

## What the Script Does

1. **Loads JSONL files** - Reads your training data from JSONL format
2. **Converts to HuggingFace datasets** - Transforms data into the format expected by the training code
3. **Partitions training data** - Splits training data into client1 (50%) and client2 (50%) for federated learning
4. **Handles images** - Copies images to dataset directories and fixes image paths
5. **Saves partitioned datasets** - Creates the following structure:

   ```text
   ./data/partitioned/
   ├── client1/          # 50% of training data
   ├── client2/          # 50% of training data
   ├── validation/       # Validation set
   └── test/             # Test set
   ```

## Output Format

Each partition directory contains:

- `dataset_info.json` - Dataset metadata
- `state.json` - Dataset state
- `images/` - Directory with image files (if applicable)
- Arrow files with the actual data

## Upload to Modal Volume (Optional)

If you want to use a Modal volume instead of mounting local directories:

```bash
# Create volume (if not already created)
modal volume create cad-coder-training-data

# Upload the partitioned data
modal volume put cad-coder-training-data ./data/partitioned /data/partitioned
```

Then update paths in `config.py` to use `/data/partitioned/...` instead of `./data/partitioned/...`

## Next Steps

After preparing the data, you can run the ML workflow. See the main [README.md](./README.md) for complete workflow instructions.

## Troubleshooting

### Error: "Directory ./data/partitioned/client1 not found"

**Solution**: Run the data preparation script first to create the partitioned data.

### Error: "JSONL files not found"

**Solution**:

- Check that your JSONL file exists at the specified path
- If using DVC, pull the data first (see Option 3 above)
- Verify the path with: `ls -la src/data/dataset.jsonl`

### Error: "No such file or directory" when uploading to Modal

**Solution**: Make sure the data directory exists locally before uploading:

```bash
ls -la ./data/partitioned/client1
# Should show dataset_info.json and state.json
```

### Error: "Image not found" warnings

**Solution**: The script will try to find images automatically. If images are missing:

- Ensure image files are in the same directory as the JSONL file, or
- Update image paths in your JSONL file to point to the correct locations

## Data Format Requirements

The training code expects HuggingFace datasets with:

- `code` or `cadquery` field containing CAD code
- `image` field with image paths (optional, for vision-language models)
- Other fields as needed by your training pipeline

The preparation script handles the conversion automatically and will add placeholder code if the `code` field is missing (with a warning).

## Advanced Options

### Custom Client Split Ratio

Change the client1/client2 split ratio:

```bash
python src/model_finetuning/prepare_training_data.py \
  --train-jsonl src/data/dataset.jsonl \
  --client1-ratio 0.6  # 60% to client1, 40% to client2
```

### Custom Train/Val/Test Split

If using a single file, the default split is 80/10/10. The script automatically handles this, but you can modify the ratios in `prepare_training_data.py` if needed.
