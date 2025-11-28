# Data Versioning and Reproducibility

## Methodology

### Tool: DVC (Data Version Control)

We use **DVC** for data versioning, a Git-like version control system designed for machine learning projects.

### Approach: Diff-Based Versioning

DVC tracks changes incrementally rather than storing full copies of each version:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   V1 Dataset    │────▶│   Diff (V1→V2)  │────▶│   V2 Dataset    │
│   (156 MB)      │     │   (+300 records)│     │   (157 MB)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Justification

### Why DVC Over Alternatives?

| Criterion | DVC | Git LFS | Full Snapshots |
|-----------|-----|---------|----------------|
| **Storage Efficiency** | ✅ Diff-based | ⚠️ Full copies | ❌ Full copies |
| **Git Integration** | ✅ Native | ✅ Native | ❌ Manual |
| **Large Files** | ✅ Optimized | ✅ Optimized | ❌ Slow |
| **ML Workflow** | ✅ Designed for ML | ⚠️ Generic | ❌ Not designed |
| **Checksums** | ✅ MD5 verification | ✅ SHA256 | ⚠️ Manual |

### Why Diff-Based for This Project?

1. **Data Characteristics**:
   - **Static Baseline (V1)**: Original GenCAD-Code dataset (147K+ samples) rarely changes
   - **Dynamic Extensions (V2+)**: User-generated data appended incrementally
   - Diff-based is ideal for append-heavy workloads

2. **File Sizes**:
   - `train.jsonl`: ~156 MB (exceeds GitHub's 100MB limit)
   - Full snapshots would require 300+ MB per version
   - DVC stores only the delta between versions

3. **Reproducibility**:
   - Each version has MD5 checksum in `.dvc` files
   - `dvc checkout` restores exact data state
   - Enables precise experiment reproduction

### Why JSONL Format?

| Format | Files per Split | Versioning Complexity |
|--------|-----------------|----------------------|
| Raw (PNG/PY) | ~150,000 files | High (many small files) |
| **JSONL** | 3 files | Low (single file per split) |

Converting to JSONL reduces versioning overhead from thousands of file operations to three.

## Version History

### V1: Baseline Dataset (Static)

- **Source**: Full GenCAD-Code dataset from data ingestion pipeline
- **Records**: 162,848 total
  - Train: 147,289 samples
  - Validation: 8,204 samples
  - Test: 7,355 samples
- **Purpose**: Initial model training baseline
- **Status**: Frozen (no modifications)

### V2: Extended Dataset (Dynamic)

- **Source**: V1 + user-generated data from production
- **Records**: 163,148 total (V1 + 300 user samples)
- **Purpose**: Model retraining with user feedback
- **Status**: Active (accepts new user data)

### Version Tracking

```bash
# View version history
git log --oneline data/v1/train.jsonl.dvc

# Example output:
# a1b2c3d Add V1 baseline dataset
# e4f5g6h Initial DVC setup
```

## Usage Instructions

### Prerequisites

- Docker and Docker Compose installed
- Repository cloned locally

### Quick Start (Docker)

```bash
cd src/data_versioning

# Build the container
docker compose build

# Start interactive shell
docker compose run --rm dvc

# Inside container:
dvc status          # Check data status
dvc list .          # List tracked files
```

### Create Dataset Versions

```bash
# Automated: Create all versions
docker compose run --rm dvc bash -c "./create_all_versions.sh"

# Initialize DVC tracking
docker compose run --rm dvc bash -c "./setup_dvc.sh"
```

### Retrieve Data

```bash
# Restore data to match current Git commit
dvc checkout

# Pull from remote storage (if configured)
dvc pull
```

### Verify Data Integrity

```bash
# Check if data matches tracked checksums
dvc status

# Expected output: "Data and pipelines are up to date"

# Verify file counts
wc -l data/v1/*.jsonl data/v2/*.jsonl
```

### Manual Setup (Without Docker)

```bash
cd src/data_versioning

# Install DVC
pip install dvc

# Initialize
dvc init --no-scm

# Track files
dvc add data/v1/train.jsonl data/v1/validation.jsonl data/v1/test.jsonl
dvc add data/v2/train.jsonl data/v2/validation.jsonl data/v2/test.jsonl
```

## LLM Prompts and Outputs

### Transparency for LLM-Generated Data

V2 includes user data with preserved prompts and outputs for provenance:

```json
{
  "question_id": "user_137986",
  "prompt": "Generate the CADQuery code needed to create the CAD for the provided image. Just the code, no other words.",
  "llm_output": "import cadquery as cq\n# Generating a workplane...\n...",
  "image": "00827834_0.png",
  "source": "user",
  "data_version": "v2"
}
```

### Field Descriptions

| Field | Description |
|-------|-------------|
| `question_id` | Unique identifier (prefixed with "user_" for user data) |
| `prompt` | Exact prompt sent to the LLM |
| `llm_output` | Complete LLM-generated CADQuery code |
| `image` | Reference to input image file |
| `source` | Data origin ("user" for user-generated) |
| `data_version` | Version identifier for lineage tracking |

## File Structure

```
src/data_versioning/
├── data/
│   ├── v1/                      # Version 1: Baseline
│   │   ├── train.jsonl          # Training data (DVC tracked)
│   │   ├── train.jsonl.dvc      # DVC pointer (Git tracked)
│   │   ├── validation.jsonl
│   │   ├── validation.jsonl.dvc
│   │   ├── test.jsonl
│   │   └── test.jsonl.dvc
│   ├── v2/                      # Version 2: Extended
│   │   └── (same structure)
│   └── user_data.jsonl          # Transformed user data
├── scripts/
│   ├── convert_raw_to_jsonl.py  # Raw → V1 conversion
│   ├── prepare_user_data.py     # User data transformation
│   └── create_v2.py             # V1 + user → V2
├── .dvc/                        # DVC configuration
├── docker-compose.yml           # Container orchestration
├── Dockerfile                   # Container definition
├── setup_dvc.sh                 # DVC initialization
└── create_all_versions.sh       # Version creation script
```

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Raw Data (PNG/PY files)                                    │
│  src/datapipeline/data_ingestion/data/raw_data/             │
└──────────────────┬──────────────────────────────────────────┘
                   │ convert_raw_to_jsonl.py
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  V1 Dataset (JSONL) ──────────────────────────────────────▶ │
│  data/v1/train.jsonl, validation.jsonl, test.jsonl         │
│                                                    dvc add  │
│  data/v1/*.jsonl.dvc (Git tracked)                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  User Data (from production API)                            │
│  Prompts + LLM outputs                                      │
└──────────────────┬──────────────────────────────────────────┘
                   │ prepare_user_data.py
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  User Data (JSONL)                                          │
│  data/user_data.jsonl                                       │
└──────────────────┬──────────────────────────────────────────┘
                   │ create_v2.py (V1 + user data)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  V2 Dataset (JSONL) ──────────────────────────────────────▶ │
│  data/v2/train.jsonl, validation.jsonl, test.jsonl         │
│                                                    dvc add  │
│  data/v2/*.jsonl.dvc (Git tracked)                         │
└─────────────────────────────────────────────────────────────┘
```

## Git Integration

### What Gets Committed

**In Git:**
- `.dvc/` directory (DVC configuration)
- `*.jsonl.dvc` files (pointer files with checksums)
- Scripts and documentation

**Not in Git (DVC tracked):**
- `*.jsonl` files (large data files)
- `.dvc/cache/` (local cache)

### Example .dvc File

```yaml
outs:
- md5: 4d071f194affc9574e2b635aa086eb62
  size: 163896646
  hash: md5
  path: train.jsonl
```

## Summary

| Aspect | Implementation |
|--------|----------------|
| **Tool** | DVC (Data Version Control) |
| **Approach** | Diff-based versioning |
| **Format** | JSONL (single file per split) |
| **Versions** | V1 (baseline), V2 (+ user data) |
| **LLM Data** | Prompts and outputs preserved |
| **Reproducibility** | MD5 checksums + Git integration |
| **Container** | Docker Compose |

