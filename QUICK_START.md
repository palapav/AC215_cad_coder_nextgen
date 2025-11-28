# Quick Start Guide

## Start Backend (with hot reload)

```bash
cd src/cad_coder_backend
# start only the services needed for API + DB
docker compose up -d backend mongo
```

Backend runs at: http://localhost:8000
- Code changes auto-reload (--reload flag enabled)

---

## Modal GPU Inference Setup

Both models (Qwen and LLaVA) run on Modal Labs GPU workers. You need to set up Modal once per developer.

### Prerequisites

```bash
pip install modal
modal token new              # log in via browser, stores credentials locally
```

After authentication, copy your `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` from the Modal dashboard.

### Configure Qwen Model (Fine-tuned Qwen3-VL-2B)

1. **Create Modal volume and upload checkpoint**
   ```bash
   modal volume create cad-coder-qwen3-model
   modal volume put cad-coder-qwen3-model src/model_inference/qwen/final_model.pt:/final_model.pt
   ```

2. **Deploy the Qwen Modal app**
   ```bash
   modal deploy src/model_inference/qwen/modal_app.py
   ```

3. **Environment variables (`src/.env`)**
   ```
   MODAL_TOKEN_ID=your_token_id
   MODAL_TOKEN_SECRET=your_token_secret
   QWEN_INFERENCE_BACKEND=modal
   QWEN_MODAL_APP=cad-coder-qwen3
   QWEN_MODAL_FUNCTION=qwen_modal_infer
   QWEN_MODAL_MAX_NEW_TOKENS=4096
   QWEN_MODAL_TEMPERATURE=0.0
   ```

4. **Test Qwen locally (optional)**
   ```bash
   modal run src/model_inference/qwen/modal_app.py --image-path src/model_inference/qwen/15.png
   ```

### Configure LLaVA Model (CAD-Coder baseline)

The LLaVA model (`CADCODER/CAD-Coder`) is hosted on HuggingFace and will be downloaded automatically on first inference. The model cache is stored in a persistent Modal volume, so you don't need to re-download after container restarts.

1. **Create persistent volume for model cache (optional - auto-created if missing)**
   ```bash
   modal volume create cad-coder-llava-model
   ```

2. **Deploy the LLaVA Modal app**
   ```bash
   modal deploy src/model_inference/llava_modal/modal_app.py
   ```
   
   **Note:** The first inference will take ~5-10 minutes to download the ~26GB model from HuggingFace. Subsequent inferences will be fast since the model is cached in the persistent volume.

2. **Add LLaVA environment variables to `src/.env`**
   ```
   LLAVA_INFERENCE_BACKEND=modal
   LLAVA_MODAL_APP=cad-coder-llava
   LLAVA_MODAL_FUNCTION=llava_modal_infer
   LLAVA_MODAL_MAX_NEW_TOKENS=3450
   LLAVA_MODAL_TEMPERATURE=0.0
   LLAVA_MODAL_TOP_P=1.0
   ```

3. **Test LLaVA locally (optional)**
   ```bash
   modal run src/model_inference/llava_modal/modal_app.py --image-path src/data/15.png
   ```

### Rebuild Backend After Configuration

After setting up Modal and editing `.env`:

```bash
cd src/cad_coder_backend
docker compose down
docker compose up -d --build backend mongo
```

### Test via API

```bash
cd src/cad_coder_backend
bash test.sh
bash test_basic.sh
```

You should see a JSON response with real CAD code. The API supports:
- `model_choice="qwen"` - Uses fine-tuned Qwen3-VL-2B with RAG
- `model_choice="llava"` - Uses CAD-Coder LLaVA baseline (requires image)

---

## (Optional) Enable Google Cloud RAG

The backend can prepend retrieval-augmented context from the vector search index before calling Qwen.

1. Ensure `src/datapipeline/rag/key.json` contains a service-account key with Vertex AI + Matching Engine access.
2. In `src/.env`, set:
   ```
   ENABLE_RAG=true
   RAG_PROJECT_ID=<your-gcp-project>
   RAG_LOCATION=us-central1
   RAG_INDEX_NAME=<vertex-index-display-name>
   RAG_ENDPOINT_NAME=<vertex-endpoint-display-name>
   RAG_DEPLOYED_INDEX_ID=<deployed-index-id>
   ```
   (`GOOGLE_APPLICATION_CREDENTIALS` and `RAG_DIR` default to `/app/rag` inside Docker; no change needed.)
3. Confirm the Matching Engine index/endpoint referenced in `src/datapipeline/rag/config.py` are deployed.
4. Rebuild the backend so dependencies are installed:
   ```bash
   docker compose down
   docker compose up -d --build backend mongo
   ```
5. Run `bash test.sh` again—you should see `rag_used=true` in the response, and the prompt sent to Qwen will include retrieved CAD code examples.

---

## Start Frontend

### Option 1: Dev Mode (Recommended - Hot Reload)

```bash
cd src/ui
docker compose -f docker-compose.dev.yml up
```

Frontend runs at: http://localhost:3000
- Code changes auto-reload

### Option 2: Production Mode

```bash
cd src/ui
docker build -t cad-coder-ui .
docker run -d -p 8080:80 --name cad-coder-ui-container cad-coder-ui
```

Frontend runs at: http://localhost:8080

---

## Stop Services

```bash
# Backend
cd src/cad_coder_backend
docker compose down

# Frontend Dev
cd src/ui
docker compose -f docker-compose.dev.yml down

# Frontend Production
docker stop cad-coder-ui-container
docker rm cad-coder-ui-container
```

---

## Optional: Run data preprocessing / RAG (when needed)

These services are disabled by default. Run them only when you need to refresh the LLaVA baseline artifacts:

```bash
cd src/cad_coder_backend
docker compose --profile pipeline up preprocess rag
```

---

## Data Versioning (DVC)

The project uses DVC (Data Version Control) for dataset versioning. All data versioning is containerized.

### Quick Start

```bash
cd src/data_versioning

# Build the Docker image
docker compose build

# Run interactive container
docker compose run --rm dvc

# Inside container: Check DVC status
dvc status
```

### Create Dataset Versions

```bash
# Create V1 (baseline) and V2 (with user data)
docker compose run --rm dvc bash -c "./create_all_versions.sh && ./setup_dvc.sh"
```

### Verify Data

```bash
# Check tracked files
docker compose run --rm dvc dvc status

# Count records
docker compose run --rm dvc bash -c "wc -l data/v1/*.jsonl data/v2/*.jsonl"
```

For complete documentation, see `src/data_versioning/DATA_VERSIONING.md`.

---

## Run the Full Test Suite

Use one command to execute backend (unit/integration/E2E), model fine-tuning, and coverage aggregation:

```bash
# Option 1: bash helper
./scripts/run_all_tests.sh

# Option 2: Docker Compose stack
docker compose -f docker-compose.tests.yml up --build repo-tests --abort-on-container-exit
```

Both approaches enforce the global ≥50% coverage requirement by aggregating the backend and model fine-tuning reports (Modal Labs and Google Cloud APIs are mocked, so no external credentials are required).

---

## Complete `.env` Template

Here's a complete template for `src/.env`:

```bash
# MongoDB (optional - use MongoDB Atlas in production)
MONGO_URI=mongodb://mongo:27017

# Modal Authentication
MODAL_TOKEN_ID=your_modal_token_id
MODAL_TOKEN_SECRET=your_modal_token_secret

# Qwen Model Configuration
QWEN_INFERENCE_BACKEND=modal
QWEN_MODAL_APP=cad-coder-qwen3
QWEN_MODAL_FUNCTION=qwen_modal_infer
QWEN_MODAL_MAX_NEW_TOKENS=4096
QWEN_MODAL_TEMPERATURE=0.0

# LLaVA Model Configuration
LLAVA_INFERENCE_BACKEND=modal
LLAVA_MODAL_APP=cad-coder-llava
LLAVA_MODAL_FUNCTION=llava_modal_infer
LLAVA_MODAL_MAX_NEW_TOKENS=3450
LLAVA_MODAL_TEMPERATURE=0.0
LLAVA_MODAL_TOP_P=1.0

# RAG Configuration (optional)
ENABLE_RAG=true
RAG_PROJECT_ID=your-gcp-project
RAG_LOCATION=us-central1
RAG_INDEX_NAME=cadcoder-mm-index
RAG_ENDPOINT_NAME=cadcoder-mm-endpoint
RAG_DEPLOYED_INDEX_ID=your-deployed-index-id
```
