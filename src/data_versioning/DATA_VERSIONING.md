# Data Versioning and Reproducibility

## Overview

This document describes the data versioning strategy and implementation for the CAD-Coder project using DVC (Data Version Control).

## Chosen Method: DVC (Data Version Control)

### Justification

We chose **DVC (diff-based versioning)** over snapshot-based approaches for the following reasons:

1. **Efficient Storage for Large Files**: DVC stores only diffs/changes between versions, not full copies. Our JSONL files can be 100+ MB, making full snapshots impractical.

2. **Git Integration**: DVC integrates seamlessly with Git, allowing us to version code and data together. The `.dvc` pointer files are small and committed to Git, while large data files are stored separately.

3. **Data Characteristics Fit**:
   - **Static Baseline (V1)**: The GenCAD-Code dataset is a static baseline that rarely changes
   - **Dynamic Extensions (V2+)**: User-generated data is appended incrementally
   - DVC handles both patterns efficiently with its diff-based approach

4. **Reproducibility**: Each version is tracked with MD5 checksums in `.dvc` files, enabling exact reproducibility via `dvc checkout`.

5. **Standard ML Tool**: DVC is widely used in ML pipelines, making it familiar to practitioners and well-documented.

6. **JSONL Format**: Converting raw PNG/PY files to JSONL reduces thousands of files to single files per split, making versioning more efficient.

## Version History

### Version 1 (V1) - Baseline Dataset
- **Source**: Full GenCAD-Code dataset from data ingestion
- **Content**: Complete train/validation/test splits
- **Format**: JSONL (converted from raw PNG/PY files)
- **Purpose**: Static baseline dataset for initial model training
- **Records**: ~162,848 total (147,289 train + 8,204 validation + 7,355 test)

### Version 2 (V2) - Extended Dataset
- **Source**: V1 data + user-generated data
- **Content**: All V1 data plus user prompts and LLM outputs
- **Format**: JSONL (V1 format + user data format)
- **Purpose**: Extended dataset for model retraining (includes user feedback)
- **Records**: ~163,148 total (V1 + 100 user samples per split)

## Data Retrieval Instructions

### Prerequisites

- Docker installed and running
- Access to the repository

### Quick Start (Docker - Recommended)

```bash
cd src/data_versioning

# Build the Docker image
docker compose build

# Start interactive container
docker compose run --rm dvc

# Inside container: Initialize DVC and check status
dvc init --no-scm
dvc status
```

### Manual Setup (Local)

```bash
cd src/data_versioning

# Install DVC
pip install dvc

# Initialize DVC (if not already initialized)
dvc init --no-scm

# Check status
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

Example `.dvc` file content:
```yaml
outs:
- md5: 4d071f194affc9574e2b635aa086eb62
  size: 163896646
  hash: md5
  path: train.jsonl
```

## Creating Dataset Versions

### Automated (Docker)

```bash
cd src/data_versioning

# Build Docker image
docker compose build

# Create all versions (V1 and V2)
docker compose run --rm dvc bash -c "./create_all_versions.sh && ./setup_dvc.sh"
```

### Step-by-Step (Manual)

#### Step 1: Create V1 from Raw Data

```bash
python scripts/convert_raw_to_jsonl.py \
    --input-dir ../datapipeline/data_ingestion/data \
    --output-dir data
```

This converts the full GenCAD-Code dataset from PNG/PY format to JSONL.

#### Step 2: Prepare User Data

```bash
python scripts/prepare_user_data.py \
    --input data/v2_data/cadquery_test_data_subset100.jsonl \
    --output data/user_data.jsonl
```

Transforms the subset file into user data format with prompts and LLM outputs.

#### Step 3: Create V2 (V1 + User Data)

```bash
python scripts/create_v2.py \
    --v1-dir data/v1 \
    --user-data data/user_data.jsonl \
    --output-dir data/v2
```

Combines V1 data with user data to create V2.

#### Step 4: Track with DVC

```bash
./setup_dvc.sh
```

Or manually:
```bash
dvc init --no-scm
dvc add data/v1/train.jsonl data/v1/validation.jsonl data/v1/test.jsonl
dvc add data/v2/train.jsonl data/v2/validation.jsonl data/v2/test.jsonl
```

## LLM Prompts and Outputs

### User Data Format (V2)

Each user data record includes both the prompt sent to the LLM and the generated output:

```json
{
  "question_id": "user_137986",
  "prompt": "Generate the CADQuery code needed to create the CAD for the provided image. Just the code, no other words.",
  "llm_output": "import cadquery as cq\n# Generating a workplane for sketch 0\nwp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.4453125, 0.0, -0.75), ...))\n...",
  "image": "00827834_0.png",
  "source": "user",
  "data_version": "v2"
}
```

**Field Descriptions:**
| Field | Description |
|-------|-------------|
| `question_id` | Unique identifier prefixed with "user_" |
| `prompt` | The exact prompt sent to the LLM |
| `llm_output` | The generated CADQuery code from the LLM |
| `image` | Reference to the input image file |
| `source` | Identifies data origin ("user" for user-generated) |
| `data_version` | Version identifier for provenance tracking |

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

### Transparency and Provenance

The data versioning system ensures transparency by:
1. **Preserving Original Prompts**: The exact prompt used for LLM generation is stored
2. **Storing Complete Outputs**: Full LLM-generated code is preserved without modification
3. **Source Tracking**: Each record includes a `source` field to identify origin
4. **Version Tracking**: The `data_version` field provides clear lineage

## Data Versioning Workflow

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────┐
│  Raw Data (PNG/PY files)                                │
│  src/datapipeline/data_ingestion/data/raw_data/         │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ convert_raw_to_jsonl.py
                   ↓
┌─────────────────────────────────────────────────────────┐
│  V1 Dataset (JSONL)                                     │
│  data/v1/train.jsonl, validation.jsonl, test.jsonl      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ dvc add
                   ↓
┌─────────────────────────────────────────────────────────┐
│  V1 Versioned (DVC tracked)                             │
│  data/v1/*.jsonl.dvc                                    │
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
│  data/v2/train.jsonl, validation.jsonl, test.jsonl      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ dvc add
                   ↓
┌─────────────────────────────────────────────────────────┐
│  V2 Versioned (DVC tracked)                             │
│  data/v2/*.jsonl.dvc                                    │
└─────────────────────────────────────────────────────────┘
```

## Reproducibility

### Exact Reproducibility

1. **Checksums**: Each `.dvc` file contains MD5 checksums for exact verification
2. **Git Integration**: DVC files are committed to Git, enabling version history
3. **Checkout**: `dvc checkout` restores exact data versions matching Git commits
4. **Lineage**: Clear separation between V1 (original) and V2 (with user data)

### Verifying Data Integrity

```bash
# Check if data matches tracked checksums
dvc status

# Verify file counts
wc -l data/v1/*.jsonl data/v2/*.jsonl

# Check .dvc tracking files exist
ls -la data/v1/*.dvc data/v2/*.dvc
```

**Expected Results:**
- `dvc status` shows "Data and pipelines are up to date"
- V1: 162,848 total records (147,289 + 8,204 + 7,355)
- V2: 163,148 total records (V1 + 300 user records)
- All `.dvc` files present with checksums

## Git Integration and Large Files

### What Gets Committed to Git

**Committed:**
- `.dvc/` directory (DVC configuration)
- `data/v1/*.jsonl.dvc` files (pointer files with checksums)
- `data/v2/*.jsonl.dvc` files (pointer files with checksums)
- Scripts and documentation

**Not Committed (tracked by DVC):**
- `data/v1/*.jsonl` files (large data files)
- `data/v2/*.jsonl` files (large data files)
- `.dvc/cache/` directory (DVC cache)

### Why This Approach

GitHub has a 100MB file size limit and warns at 50MB. Our JSONL files exceed these limits:
- `train.jsonl`: ~156 MB
- `validation.jsonl`: ~8.8 MB
- `test.jsonl`: ~7.9 MB

By tracking only `.dvc` pointer files in Git, we keep the repository lightweight while maintaining full data versioning capabilities.

## File Structure

```
src/data_versioning/
├── data/
│   ├── v1/                      # Version 1: Full GenCAD-Code dataset
│   │   ├── train.jsonl          # (tracked by DVC, not in Git)
│   │   ├── train.jsonl.dvc      # DVC pointer file (in Git)
│   │   ├── validation.jsonl
│   │   ├── validation.jsonl.dvc
│   │   ├── test.jsonl
│   │   └── test.jsonl.dvc
│   ├── v2/                      # Version 2: V1 + User data
│   │   ├── train.jsonl
│   │   ├── train.jsonl.dvc
│   │   ├── validation.jsonl
│   │   ├── validation.jsonl.dvc
│   │   ├── test.jsonl
│   │   └── test.jsonl.dvc
│   └── user_data.jsonl          # Transformed user data
├── scripts/
│   ├── convert_raw_to_jsonl.py  # Raw data → V1 conversion
│   ├── prepare_user_data.py     # User data transformation
│   └── create_v2.py             # V1 + user data → V2
├── .dvc/                        # DVC configuration
├── .dvcignore                   # Files to exclude from DVC
├── .gitignore                   # Files to exclude from Git
├── docker-compose.yml           # Container orchestration
├── Dockerfile                   # Container definition
├── setup_dvc.sh                 # DVC initialization script
├── create_all_versions.sh       # Master version creation script
├── README.md                    # Quick start guide
└── DATA_VERSIONING.md           # This documentation
```

## Docker Commands Reference

### Build and Run

```bash
# Build the Docker image
docker compose build

# Start interactive shell
docker compose run --rm dvc

# Run a specific command
docker compose run --rm dvc python scripts/convert_raw_to_jsonl.py --help
```

### Create Versions

```bash
# Create all versions automatically
docker compose run --rm dvc bash -c "./create_all_versions.sh"

# Initialize DVC tracking
docker compose run --rm dvc bash -c "./setup_dvc.sh"

# Check DVC status
docker compose run --rm dvc dvc status
```

### Verify Data

```bash
# Count records in all files
docker compose run --rm dvc bash -c "wc -l data/v1/*.jsonl data/v2/*.jsonl"

# View first record of user data
docker compose run --rm dvc bash -c "head -1 data/user_data.jsonl | python -m json.tool"
```

## Summary

| Aspect | Implementation |
|--------|----------------|
| **Tool** | DVC (Data Version Control) |
| **Approach** | Diff-based versioning |
| **Storage** | Local (no remote storage required) |
| **Format** | JSONL (single file per split) |
| **Versions** | V1 (baseline), V2 (with user data) |
| **LLM Data** | Prompts and outputs preserved |
| **Reproducibility** | MD5 checksums + Git integration |
| **Containerized** | Yes (Docker Compose) |
