# Quick Start Guide

## Start Backend (with hot reload)

```bash
cd src/cad_coder_backend
# start only the services needed for API + DB
docker compose up -d backend mongo
```

Backend runs at: http://localhost:8000
- Code changes auto-reload (--reload flag enabled)

### Configure Modal GPU inference (Qwen)
1. **Modal CLI setup (once per developer)**
   ```bash
   pip install modal
   modal token new              # log in via browser, stores credentials locally
   modal volume put cad-coder-qwen3-model src/model_inference/qwen/final_model.pt:/final_model.pt
   modal deploy src/model_inference/qwen/modal_app.py
   ```
2. **Environment variables (`src/.env`)**
   ```
   MODAL_TOKEN_ID=...
   MODAL_TOKEN_SECRET=...
   QWEN_INFERENCE_BACKEND=modal
   QWEN_MODAL_APP=cad-coder-qwen3
   QWEN_MODAL_FUNCTION=qwen_modal_infer
   QWEN_MODAL_MAX_NEW_TOKENS=4096
   QWEN_MODAL_TEMPERATURE=0.0
   ```
3. **Rebuild backend after editing `.env`**
   ```bash
   docker compose down
   docker compose up -d --build backend mongo
   ```
4. **Sanity check (from `src/cad_coder_backend`)**
   ```bash
   bash test.sh
   ```
   You should see a JSON response with real CAD code generated via Modal. The frontend/API now uses Modal GPUs automatically when `model_choice="qwen"`.

### (Optional) Enable Google Cloud RAG
The backend can prepend retrieval-augmented context from the vector search index before calling Qwen.

1. Ensure `src/datapipeline/rag/key.json` contains a service-account key with Vertex AI + Matching Engine access.
2. In `src/.env`, set:
   ```
   ENABLE_RAG=true
   RAG_PROJECT_ID=<your-gcp-project>
   RAG_LOCATION=us-central1
   ```
   (`GOOGLE_APPLICATION_CREDENTIALS` and `RAG_DIR` default to `/app/rag` inside Docker; no change needed.)
3. Confirm the Matching Engine index/endpoint referenced in `src/datapipeline/rag/config.py` are deployed.
4. Rebuild the backend so dependencies are installed:
   ```bash
   docker compose down
   docker compose up -d --build backend mongo
   ```
5. Run `bash test.sh` again—you should see `rag_used=true` in the response, and the prompt sent to Qwen will include retrieved CAD code examples.

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

## Optional: Run data preprocessing / RAG (when needed)
These services are disabled by default. Run them only when you need to refresh the LLaVA baseline artifacts:

```bash
cd src/cad_coder_backend
docker compose --profile pipeline up preprocess rag
```

