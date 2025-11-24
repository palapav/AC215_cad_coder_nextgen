# Milestone 2.2: End-to-End Containerized Pipeline

**CAD-Coder Data Pipeline**  
*Ingestion → Preprocessing → RAG*

---

> **📊 Quick Evidence:** For proof of successful end-to-end execution, see [`PIPELINE_RUN.log`](PIPELINE_RUN.log) (591 lines, 43 KB)  
> This log shows all 5 pipeline stages completing successfully with sample data.

---

## Overview

This document describes the complete containerized data pipeline that orchestrates three core components:
1. **Data Ingestion** - Downloads CAD dataset from HuggingFace and uploads to Google Cloud Storage
2. **Data Preprocessing** - Normalizes images and structures metadata for downstream tasks
3. **RAG Pipeline** - Generates multimodal embeddings and indexes them in Vertex AI Vector Search

The entire pipeline runs with a single command (`docker-compose up`) and processes data end-to-end from raw HuggingFace datasets to production-ready vector embeddings.

---

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Validation    │─────▶│   Data Ingestion │─────▶│ Preprocessing   │
│  (Auth Check)   │      │  (HF → GCS Raw)  │      │ (GCS → GCS Proc)│
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                                             │
                                                             ▼
                         ┌─────────────────┐      ┌─────────────────┐
                         │   RAG Testing   │◀─────│  RAG Pipeline   │
                         │  (Validation)   │      │ (Embed → Vector)│
                         └─────────────────┘      └─────────────────┘
```

**Data Flow:**
- HuggingFace Dataset → GCS (`gs://bucket/raw_data/`)
- GCS Raw → GCS Processed (`gs://bucket/processed_data/`)
- GCS Processed → Vertex AI Vector Database

---

## Pipeline Components

### 1. Data Ingestion (`data_ingestion/`)

**Purpose:** Downloads CAD code and images from HuggingFace's CADCODER/GenCAD-Code dataset and uploads directly to Google Cloud Storage.

**Key Files:**
- `dataloader.py` - Main ingestion script that authenticates with HuggingFace, downloads specified splits/samples, and uploads to GCS
- `Dockerfile` - Containerizes the ingestion process using Python 3.11-slim base
- `pyproject.toml` - Declares dependencies (datasets, google-cloud-storage, Pillow, tqdm) using `uv`
- `uv.lock` - Pins exact dependency versions (75 packages) for reproducibility

**Features:**
- Supports split selection (train/test/validation or all)
- Configurable sample limits for testing (e.g., 5 samples)
- Uses temporary directories for staging before GCS upload
- No local file persistence (cloud-native design)
- HuggingFace dataset caching via Docker volume

**Configuration:**
```bash
# Environment variables (from .env)
HF_TOKEN=<your_huggingface_token>
GCS_BUCKET=cad-coder-nextgen-data
PIPELINE_SPLIT=test        # or train, validation
PIPELINE_LIMIT=5           # number of samples to process
```

---

### 2. Data Preprocessing (`data_preprocessing/`)

**Purpose:** Reads raw CAD images and code from GCS, normalizes images, and creates structured JSONL metadata for the RAG pipeline.

**Key Files:**
- `preprocess_cv.py` - Normalizes images to 224x224, pairs with code files, generates `dataset.jsonl`
- `Dockerfile` - Containerizes preprocessing with PyTorch and torchvision for image operations
- `pyproject.toml` - Declares dependencies (torch, torchvision, google-cloud-storage) using `uv`
- `uv.lock` - Pins exact dependency versions (75 packages) for reproducibility

**Process:**
1. Lists all files in `gs://bucket/raw_data/{split}/`
2. Pairs images with corresponding code files
3. Normalizes images using ImageNet statistics (mean/std)
4. Uploads processed images to `gs://bucket/processed_data/{split}/`
5. Creates `dataset.jsonl` with metadata (file paths, dimensions, split info)

**Output:**
- Processed images: `gs://bucket/processed_data/{split}/{filename}.png`
- Metadata: `gs://bucket/processed_data/{split}/dataset.jsonl`

---

### 3. RAG Pipeline (`rag/`)

**Purpose:** Generates multimodal embeddings from images and CAD code, then indexes them in Vertex AI Matching Engine for semantic search.

**Detailed documentation:** See [`rag/milestone2.3_rag.md`](rag/milestone2.3_rag.md)

**Key Files:**
- `pipeline.py` - Orchestrates embedding generation and vector upsertion
- `embedding_generator.py` - Generates multimodal embeddings using Vertex AI's multimodal model
- `storage_utils.py` - Handles GCS file operations and image loading
- `config.py` - Defines index/endpoint names and constants
- `Dockerfile` - Containerizes RAG pipeline with Vertex AI SDK
- `pyproject.toml` - Declares dependencies (google-cloud-aiplatform, Pillow) using `uv`
- `uv.lock` - Pins exact dependency versions (46 packages) for reproducibility

**Output:**
- 56 vectors (5 images + 51 CAD code chunks) → Vertex AI Vector Database
- Each vector includes metadata: CAD code, type (code/image), item ID

---

### 4. Authentication Validation (`validate_auth.py`)

**Purpose:** Pre-flight checks to ensure all required credentials and environment variables are configured before pipeline execution.

**Validates:**
- `HF_TOKEN` - HuggingFace authentication
- `GCS_BUCKET` - Target bucket name
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account key
- `key.json` - Verifies file exists and contains valid JSON

**Exit Behavior:** Fails fast with descriptive error messages if validation fails, preventing wasted compute time.

---

## Docker Configuration

### Dockerfiles

Each component has a minimal, production-ready Dockerfile following best practices:

**Common Pattern:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install build tools if needed (preprocessing needs gcc/g++ for PyTorch)
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml .

# Copy source code
COPY *.py .

# Install dependencies using uv
RUN uv pip install --system <packages>

# Default command
CMD ["python", "script.py"]
```

**Build Instructions:**
```bash
# Build individual components
docker build -t cad-ingestion data_ingestion/
docker build -t cad-preprocessing data_preprocessing/
docker build -t cad-rag rag/

# Or build all via docker-compose
docker-compose build
```

---

### Dependency Management with `uv`

Each component uses modern Python dependency management:

**`pyproject.toml`** - Declares direct dependencies
```toml
[project]
name = "cad-coder-ingestion"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "datasets>=2.19.0",
    "google-cloud-storage>=2.10.0",
    "Pillow>=10.0.0",
    "tqdm>=4.65.0",
]
```

**`uv.lock`** - Locks all transitive dependencies with SHA256 hashes
- Generated via `uv lock`
- Ensures reproducible builds across all environments
- Prevents dependency version conflicts
- Security: Verifies package integrity via hashes

**Benefits:**
- ✅ Faster installs than pip
- ✅ Deterministic builds
- ✅ Supply chain security
- ✅ Clear dependency tree

---

### Docker Compose Orchestration

**File:** `docker-compose.yml`

**Services:**

1. **`validate`** - Validates credentials before proceeding
   - Runs first, blocks pipeline on failure
   - Mounts `key.json` and loads `.env`

2. **`data_ingestion`** - Downloads from HuggingFace → GCS
   - Depends on `validate` completing successfully
   - Uses `hf_cache` volume for HuggingFace dataset caching
   - Configurable via `PIPELINE_SPLIT` and `PIPELINE_LIMIT`

3. **`preprocessing`** - Processes raw data from GCS
   - Depends on `data_ingestion` completing successfully
   - Reads from `raw_data/`, writes to `processed_data/`

4. **`rag`** - Generates embeddings and indexes to Vertex AI
   - Depends on `preprocessing` completing successfully
   - Reads from `processed_data/`
   - Upserts 56 multimodal vectors

5. **`rag_test`** - Validates RAG pipeline with test queries
   - Depends on `rag` completing successfully
   - Runs 5 test cases (metadata, single query, batch, prompt formatting, multimodal)

**Key Features:**
- Sequential execution via `depends_on` with `service_completed_successfully`
- Shared authentication via mounted `key.json` and `.env`
- Persistent HuggingFace cache via named volume
- Isolated network (`pipeline_network`)

---

## Setup Instructions

### Prerequisites

1. **Google Cloud Setup:**
   - Active GCP project with billing enabled
   - Service account with permissions for:
     - Cloud Storage (read/write)
     - Vertex AI (index/endpoint management)
   - Download service account key as `key.json`

2. **HuggingFace Setup:**
   - Account with access to CADCODER/GenCAD-Code dataset
   - Generate access token from https://huggingface.co/settings/tokens

3. **Local Setup:**
   - Docker and Docker Compose installed
   - `uv` installed (for local development): `pip install uv`

### Configuration

1. **Copy authentication files:**
   ```bash
   cd src/datapipeline
   cp rag/key.json ./key.json  # Place service account key
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   nano .env
   ```

3. **Edit `.env` with your values:**
   ```bash
   # HuggingFace
   HF_TOKEN=hf_YOUR_ACTUAL_TOKEN

   # Google Cloud
   GCS_BUCKET=cad-coder-nextgen-data
   PROJECT_ID=cad-coder-nextgen
   LOCATION=us-central1
   GOOGLE_APPLICATION_CREDENTIALS=/app/key.json
   GOOGLE_CLOUD_PROJECT=cad-coder-nextgen

   # Pipeline Configuration
   PIPELINE_SPLIT=test          # train, test, or validation
   PIPELINE_LIMIT=5             # number of samples (for testing)
   ```

---

## Running the Pipeline

### Full Pipeline Execution

```bash
cd src/datapipeline

# Clean up any previous runs
docker-compose down

# Run entire pipeline (Validation → Ingestion → Preprocessing → RAG → Testing)
docker-compose up

# First run or after code changes, rebuild images:
docker-compose up --build
```

### Expected Output

```
✅ Validation (< 1 sec)
   └─> Verifies HF_TOKEN, GCS_BUCKET, key.json

✅ Ingestion (~10 sec, ~3 sec on subsequent runs with cache)
   └─> 5 samples × 2 files = 10 files → gs://bucket/raw_data/test/

✅ Preprocessing (~15 sec)
   └─> 10 images + 1 JSONL → gs://bucket/processed_data/test/

✅ RAG Pipeline (~30 sec)
   └─> 56 vectors → Vertex AI (5 images + 51 code chunks)

✅ RAG Testing (~10 sec)
   └─> 5 test cases pass
```

**Total Time:** ~50 seconds (first run), ~45 seconds (cached HuggingFace data)

### Save Pipeline Logs

To capture complete execution logs for documentation:

```bash
# Option 1: Using helper script
./run_and_log.sh PIPELINE_RUN.log

# Option 2: Manual
docker-compose up 2>&1 | tee PIPELINE_RUN.log
```

**Generated Log:** [`PIPELINE_RUN.log`](PIPELINE_RUN.log) - 591 lines, 43 KB

---

## Evidence of End-to-End Functionality

The pipeline's successful execution is documented in [`PIPELINE_RUN.log`](PIPELINE_RUN.log), which shows:

1. **Authentication Validation** ✅
   ```
   ✅ GOOGLE_APPLICATION_CREDENTIALS: Set
   ✅ HF_TOKEN: Set
   ✅ Key file valid
   ```

2. **Data Ingestion** ✅
   ```
   ✅ Total files uploaded: 10
   ❌ Total files failed: 0
   📦 GCS Bucket: gs://cad-coder-nextgen-data/raw_data/
   ```

3. **Preprocessing** ✅
   ```
   ✅ Total images processed: 10
   📄 Total JSONL samples: 10
   📦 GCS Output: gs://cad-coder-nextgen-data/processed_data/
   ```

4. **RAG Embedding** ✅
   ```
   ✅ Embeddings generated. Total datapoints: 56
   📐 Vector dimensions: 1408
   🔢 Total vectors upserted: 56
   ```

5. **RAG Testing** ✅
   ```
   ✅ Results with CAD code: 5
   ❌ Results missing CAD code: 0
   ✅ SUCCESS: CAD code is being stored and retrieved correctly!
   All tests completed!
   ```

---

## Scaling to Full Dataset

To process larger datasets, simply adjust environment variables:

```bash
# .env configuration examples

# Process 100 samples from test split
PIPELINE_SPLIT=test
PIPELINE_LIMIT=100

# Process entire validation split (no limit)
PIPELINE_SPLIT=validation
PIPELINE_LIMIT=  # Leave empty for all samples

# Process all splits
INGESTION_SPLITS=train,test,validation
PIPELINE_LIMIT=  # Leave empty for full dataset
```

**Performance Estimates:**
- 100 samples: ~5 minutes
- 1,000 samples: ~30 minutes
- Full test split (7,355 samples): ~2-3 hours

---

## Troubleshooting

### Common Issues

**1. Authentication Failed**
```bash
# Verify credentials
cat .env | grep -E "(HF_TOKEN|GCS_BUCKET|PROJECT_ID)"
ls -la key.json
```

**2. Docker Container Name Conflicts**
```bash
# Clean up old containers
docker-compose down
docker-compose up
```

**3. Cache Issues (Old Images)**
```bash
# Force rebuild all containers
docker-compose build --no-cache
docker-compose up
```

**4. Permission Denied for GCS**
```bash
# Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount"
```

**5. HuggingFace Dataset Access**
```bash
# Verify token has access to CADCODER/GenCAD-Code
# Visit: https://huggingface.co/datasets/CADCODER/GenCAD-Code
# Ensure you've accepted dataset terms
```

---

## Component Summaries

### Python Scripts

| Script | Component | Purpose |
|--------|-----------|---------|
| `validate_auth.py` | Validation | Pre-flight credential checks |
| `dataloader.py` | Ingestion | HuggingFace → GCS upload |
| `preprocess_cv.py` | Preprocessing | Image normalization, JSONL generation |
| `pipeline.py` | RAG | Multimodal embedding generation |
| `embedding_generator.py` | RAG | Vertex AI embedding API calls |
| `storage_utils.py` | RAG | GCS file operations |
| `config.py` | RAG | Configuration constants |
| `rag_retrieval.py` | RAG | Vector search and retrieval |
| `test_rag.py` | RAG Testing | Validation test suite |

### Configuration Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Orchestrates all 5 services |
| `.env` | Environment variables (tokens, buckets, limits) |
| `.env.example` | Template for `.env` |
| `pyproject.toml` (×3) | Dependency declarations per component |
| `uv.lock` (×3) | Locked dependency versions |
| `.dockerignore` | Excludes unnecessary files from builds |

### Documentation Files

| File | Purpose |
|------|---------|
| `RUN_PIPELINE.txt` | Quick-start commands |
| `PIPELINE_RUN.log` | Evidence of successful execution |
| `run_and_log.sh` | Helper script for logging |
| `milestone2.2_endtoend.md` | This document |
| `rag/milestone2.3_rag.md` | RAG-specific documentation |

---

## Next Steps

With the containerized pipeline operational:

1. **Scale to Production:**
   - Process full dataset (21,000+ samples)
   - Deploy to Google Cloud Run for serverless execution
   - Set up Cloud Scheduler for automated data refreshes

2. **Integrate with Application:**
   - Connect RAG retrieval to backend API
   - Implement real-time embedding generation for new queries
   - Add LLM integration for code generation

3. **Optimize Performance:**
   - Batch embedding generation for faster processing
   - Implement parallel preprocessing
   - Add incremental indexing for new data

---

## Summary

This end-to-end containerized pipeline demonstrates:

✅ **Reproducibility** - Lock files ensure identical environments  
✅ **Scalability** - Cloud-native design handles datasets of any size  
✅ **Maintainability** - Modular components with clear separation of concerns  
✅ **Production-Ready** - Automated testing, error handling, comprehensive logging  
✅ **Documentation** - Clear instructions with evidence of successful execution

**Pipeline Evidence:** All 5 services completed successfully as documented in [`PIPELINE_RUN.log`](PIPELINE_RUN.log)

