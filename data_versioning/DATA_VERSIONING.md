# Data Versioning and Reproducibility

## Overview

This document describes the data versioning strategy and implementation for the CAD-Coder project using DVC (Data Version Control).

## Chosen Method: DVC (Local)

**Justification:**
- **Efficient for large files**: DVC stores only diffs/changes, not full copies
- **Git-friendly**: Integrates seamlessly with Git for code + data versioning
- **Local-only setup**: No remote storage needed (keeps everything local as requested)
- **Standard tool**: Widely used in ML pipelines for data versioning
- **JSONL format**: Single file per split makes versioning efficient (vs thousands of PNG/PY files)

## Version History

### Version 1 (V1)
- **Source**: Full GenCAD-Code dataset from ingestion container
- **Content**: Complete train/validation/test splits
- **Format**: JSONL (converted from raw PNG/PY files)
- **Purpose**: Static baseline dataset for initial model training

### Version 2 (V2)
- **Source**: V1 data + incoming user data
- **Content**: All V1 data plus user-generated prompts and LLM outputs
- **Format**: JSONL (V1 format + user data format)
- **Purpose**: Extended dataset for model retraining (includes user feedback)

## Data Retrieval Instructions

### Setup DVC (One-time)

```bash
cd data_versioning
./setup_dvc.sh
```

Or manually:
```bash
dvc init --no-scm
dvc add data/v1/train.jsonl data/v1/validation.jsonl data/v1/test.jsonl
dvc add data/v2/train.jsonl data/v2/validation.jsonl data/v2/test.jsonl
```

### Check Data Status

```bash
# View current status
dvc status

# List tracked files
dvc list .
```

### Retrieve Specific Version

```bash
# Restore data to match current Git commit
dvc checkout

# View version history (via Git)
git log --oneline data/v1/train.jsonl.dvc
```

### View Version Information

DVC stores version information in `.dvc` files. Each tracked file has a corresponding `.dvc` file:
- `data/v1/train.jsonl.dvc` - Contains checksum and metadata for V1 train data
- `data/v2/train.jsonl.dvc` - Contains checksum and metadata for V2 train data

## Creating Versions

### Step 1: Create V1 from Raw Data

```bash
python scripts/convert_raw_to_jsonl.py \
    --input-dir ../datapipeline/data_ingestion/data \
    --output-dir data
```

This converts the full GenCAD-Code dataset from PNG/PY format to JSONL.

### Step 2: Prepare User Data

```bash
python scripts/prepare_user_data.py \
    --input data/v2_data/cadquery_test_data_subset100.jsonl \
    --output data/user_data.jsonl
```

Transforms the subset file into user data format with prompts and LLM outputs.

### Step 3: Create V2 (V1 + User Data)

```bash
python scripts/create_v2.py \
    --v1-dir data/v1 \
    --user-data data/user_data.jsonl \
    --output-dir data/v2
```

Combines V1 data with user data to create V2.

### Step 4: Track with DVC

```bash
./setup_dvc.sh
```

Or manually add new versions:
```bash
dvc add data/v2/train.jsonl data/v2/validation.jsonl data/v2/test.jsonl
```

## LLM Prompts and Outputs

### User Data Format (V2)

Each user data record includes:

```json
{
  "question_id": "user_137986",
  "prompt": "Generate the CADQuery code needed to create the CAD for the provided image. Just the code, no other words.",
  "llm_output": "import cadquery as cq\n...",
  "image": "00827834_0.png",
  "source": "user",
  "data_version": "v2"
}
```

**Fields:**
- `prompt`: User's input/prompt to the LLM
- `llm_output`: Generated CAD code output from the LLM
- `source`: Identifies data as user-generated
- `data_version`: Version identifier

### Original Dataset Format (V1)

```json
{
  "question_id": "uid_001",
  "image": "uid_001.png",
  "text": "Generate the CADQuery code needed to create the CAD for the provided image. Just the code, no other words.",
  "category": "default",
  "ground_truth": "import cadquery as cq\n..."
}
```

## Version Workflow

1. **Initial Setup**: Create V1 from full GenCAD-Code dataset
2. **User Data Collection**: Collect prompts and LLM outputs from production
3. **Version Update**: Combine V1 + new user data → V2
4. **DVC Tracking**: Commit new version with `dvc add`
5. **Model Retraining**: Use V2 for retraining to address model drift

## Reproducibility

- **Data Versioning**: Each version is tracked with checksums in `.dvc` files
- **Git Integration**: DVC files are committed to Git, enabling version history
- **Exact Reproducibility**: `dvc checkout` restores exact data versions
- **Lineage Tracking**: Clear separation between V1 (original) and V2 (with user data)

## Data Versioning Workflow

### Overview

The data versioning workflow follows a clear progression from raw data to versioned datasets:

```
Raw Data (PNG/PY) → V1 (JSONL) → User Data (JSONL) → V2 (JSONL)
                         ↓                              ↓
                    DVC Tracked                    DVC Tracked
```

### Step-by-Step Workflow

1. **Raw Data Ingestion**
   - Source: GenCAD-Code dataset from HuggingFace
   - Format: PNG images + Python code files
   - Location: `datapipeline/data_ingestion/data/raw_data/`
   - Contains: train/, validation/, test/ splits

2. **V1 Creation** (Baseline Dataset)
   - Convert raw PNG/PY files → JSONL format
   - Script: `scripts/convert_raw_to_jsonl.py`
   - Output: `data/v1/train.jsonl`, `validation.jsonl`, `test.jsonl`
   - Result: Full GenCAD-Code dataset in standardized format

3. **V1 Versioning**
   - Initialize DVC: `dvc init --no-scm`
   - Track files: `dvc add data/v1/*.jsonl`
   - Creates: `.dvc` tracking files with checksums
   - Status: Baseline dataset is now versioned

4. **User Data Preparation** (For V2)
   - Transform user interactions → user data format
   - Script: `scripts/prepare_user_data.py`
   - Input: User prompts and LLM outputs
   - Output: `data/user_data.jsonl` (intermediate file)

5. **V2 Creation** (Extended Dataset)
   - Combine V1 + User data
   - Script: `scripts/create_v2.py`
   - Output: `data/v2/train.jsonl`, `validation.jsonl`, `test.jsonl`
   - Result: V1 data + appended user data in each split

6. **V2 Versioning**
   - Track files: `dvc add data/v2/*.jsonl`
   - Creates: `.dvc` tracking files for V2
   - Status: Extended dataset is now versioned

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────┐
│  Raw Data (PNG/PY files)                                │
│  datapipeline/data_ingestion/data/raw_data/            │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ convert_raw_to_jsonl.py
                   ↓
┌─────────────────────────────────────────────────────────┐
│  V1 Dataset (JSONL)                                     │
│  data/v1/train.jsonl, validation.jsonl, test.jsonl     │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ dvc add
                   ↓
┌─────────────────────────────────────────────────────────┐
│  V1 Versioned (DVC tracked)                            │
│  data/v1/*.jsonl.dvc                                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  User Data (from production/API)                        │
│  Prompts + LLM outputs                                  │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ prepare_user_data.py
                   ↓
┌─────────────────────────────────────────────────────────┐
│  User Data (JSONL)                                      │
│  data/user_data.jsonl                                   │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ create_v2.py (combines V1 + user data)
                   ↓
┌─────────────────────────────────────────────────────────┐
│  V2 Dataset (JSONL)                                     │
│  data/v2/train.jsonl, validation.jsonl, test.jsonl     │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ dvc add
                   ↓
┌─────────────────────────────────────────────────────────┐
│  V2 Versioned (DVC tracked)                             │
│  data/v2/*.jsonl.dvc                                    │
└─────────────────────────────────────────────────────────┘
```

## Reproducing Dataset Versions

### Prerequisites

- Docker installed and running
- Access to raw data: `datapipeline/data_ingestion/data/raw_data/`
- Docker image built: `data-versioning`

### Reproducing V1 Dataset

**Using Docker (Recommended):**

```bash
cd data_versioning

# Build Docker image (if not already built)
docker build -t data-versioning .

# Convert raw data to V1 JSONL
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/scripts:/app/scripts \
  -v $(pwd)/../datapipeline/data_ingestion/data:/app/raw_data \
  -w /app \
  data-versioning \
  python scripts/convert_raw_to_jsonl.py \
    --input-dir /app/raw_data \
    --output-dir data

# Verify V1 files created
ls -lh data/v1/*.jsonl
```

**Expected Output:**
- `data/v1/train.jsonl` (~156 MB, ~147,289 records)
- `data/v1/validation.jsonl` (~8.8 MB, ~8,204 records)
- `data/v1/test.jsonl` (~7.9 MB, ~7,355 records)

### Reproducing V2 Dataset

**Step 1: Prepare User Data**

```bash
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/scripts:/app/scripts \
  -w /app \
  data-versioning \
  python scripts/prepare_user_data.py \
    --input data/v2_data/cadquery_test_data_subset100.jsonl \
    --output data/user_data.jsonl
```

**Step 2: Create V2 (V1 + User Data)**

```bash
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/scripts:/app/scripts \
  -w /app \
  data-versioning \
  python scripts/create_v2.py \
    --v1-dir data/v1 \
    --user-data data/user_data.jsonl \
    --output-dir data/v2
```

**Expected Output:**
- `data/v2/train.jsonl` (~156 MB, ~147,389 records = V1 + 100 user)
- `data/v2/validation.jsonl` (~8.9 MB, ~8,304 records = V1 + 100 user)
- `data/v2/test.jsonl` (~8.0 MB, ~7,455 records = V1 + 100 user)

### Reproducing with DVC Versioning

**Initialize DVC and Track Versions:**

```bash
# Initialize DVC
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd):/app/workdir \
  -w /app/workdir \
  data-versioning \
  bash -c "dvc init --no-scm"

# Track V1
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd):/app/workdir \
  -w /app/workdir \
  data-versioning \
  bash -c "dvc add data/v1/train.jsonl data/v1/validation.jsonl data/v1/test.jsonl"

# Track V2
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd):/app/workdir \
  -w /app/workdir \
  data-versioning \
  bash -c "dvc add data/v2/train.jsonl data/v2/validation.jsonl data/v2/test.jsonl"

# Verify tracking
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd):/app/workdir \
  -w /app/workdir \
  data-versioning \
  bash -c "dvc status"
```

### Verifying Reproducibility

**Check Data Integrity:**

```bash
# Check DVC status (should show "up to date" if data matches checksums)
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd):/app/workdir \
  -w /app/workdir \
  data-versioning \
  bash -c "dvc status"

# Verify file counts
wc -l data/v1/*.jsonl data/v2/*.jsonl

# Check .dvc tracking files exist
ls -la data/v1/*.dvc data/v2/*.dvc
```

**Expected Results:**
- `dvc status` shows "Data and pipelines are up to date"
- V1: 162,848 total records (147,289 + 8,204 + 7,355)
- V2: 163,148 total records (147,389 + 8,304 + 7,455)
- All `.dvc` files present with checksums

### Quick Reproduction Script

For convenience, use the master script:

```bash
cd data_versioning
./create_all_versions.sh
./setup_dvc.sh
```

This runs all steps automatically to reproduce both V1 and V2 datasets with DVC versioning.

## File Structure

```
data_versioning/
├── data/
│   ├── v1/                    # Version 1: Full GenCAD-Code dataset
│   │   ├── train.jsonl
│   │   ├── validation.jsonl
│   │   └── test.jsonl
│   ├── v2/                    # Version 2: V1 + User data
│   │   ├── train.jsonl
│   │   ├── validation.jsonl
│   │   └── test.jsonl
│   └── user_data.jsonl        # Transformed user data
├── .dvc/                      # DVC configuration and cache
└── scripts/                    # Conversion scripts
```

## Notes

- All data is stored locally (no remote DVC storage)
- Images are referenced by filename (stored separately)
- V2 includes all V1 data plus appended user data
- Each split (train/validation/test) in V2 contains V1 data + user data

## Git Integration and Large Files

### Note on Large Files

The JSONL files used for our dataset versions (v1 and v2) are intentionally not committed to Git, because GitHub does not allow files larger than 100MB and typically warns after 50MB. Some of our JSONL files exceed this size, so we track them exclusively through DVC instead of Git.

Only the corresponding `.dvc` pointer files are committed, which ensures small Git commits while still allowing full reproducibility using:

```bash
dvc pull data/v1
dvc pull data/v2
```

### What Gets Committed to Git

**Committed:**
- `.dvc/` directory (DVC configuration)
- `data/v1/*.jsonl.dvc` files (pointer files with checksums)
- `data/v2/*.jsonl.dvc` files (pointer files with checksums)
- Scripts and documentation

**Not Committed:**
- `data/v1/*.jsonl` files (large data files)
- `data/v2/*.jsonl` files (large data files)
- `.dvc/cache/` directory (DVC cache)

### Reproducing from Git Repository

When cloning the repository, you'll have the `.dvc` files but not the actual data. To retrieve the data:

```bash
# Clone repository
git clone <repository-url>
cd data_versioning

# Pull data using DVC (if remote is configured)
dvc pull data/v1
dvc pull data/v2

# Or recreate from source (if no remote)
# Follow the "Reproducing Dataset Versions" section above
```

This approach keeps the Git repository lightweight while maintaining full data versioning and reproducibility through DVC.

