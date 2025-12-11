<!-- CAD-Coder NextGen README -->

# CAD-Coder NextGen

AI-assisted CAD code generation with multimodal (text/image) prompts. Frontend and backend run on GKE; model inference can run on GKE GPUs or Modal Labs GPUs (default). CI enforces ≥60% coverage with unit, integration, and E2E tests (current combined: ~61.4%).

---

## Architecture & Flow
- Frontend (React/TypeScript) on GKE → Backend (FastAPI on GKE) → Inference (Modal GPU or GKE GPU)
- Persistence: MongoDB (chat history); optional GCS for CAD code uploads
- RAG (optional): Vertex AI Matching Engine / local mock
- CI/CD: GitHub Actions (`ci.yml`); deploy is dispatch-only (`deploy.yml`) after CI success

Request Flow:
```
Browser → GKE Frontend → GKE Backend → (Modal GPU | GKE GPU) → stream tokens → UI
```

---

## Prerequisites & Setup

### Tooling
- Git, Docker, Docker Compose
- Python 3.11 (backend), Python 3.10 (model_finetuning)
- Node 20 (frontend)
- GCloud CLI, kubectl (for GKE), Pulumi (optional IaC)
- Modal CLI (`pip install modal-client`)

### Environment
```bash
git clone https://github.com/palapav/AC215_cad_coder_nextgen.git

# Backend (optional local venv)
cd src/cad_coder_backend
python -m venv env && source env/bin/activate
pip install -r requirements.txt

# Frontend
cd ../ui
npm ci
```

### Required Secrets / Env (examples)
- Modal: `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, `QWEN_MODAL_APP`, `QWEN_MODAL_STREAM_FUNCTION`, `LLAVA_MODAL_APP`, `LLAVA_MODAL_STREAM_FUNCTION`
- Backend: `MONGO_URI`, `MONGO_DB`, `QWEN_INFERENCE_BACKEND`, `LLAVA_INFERENCE_BACKEND`, `QWEN_SERVICE_URL`, `LLAVA_SERVICE_URL`, `ENABLE_RAG`
- GCP: `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_ZONE`, `GKE_CLUSTER`, `GCP_WORKLOAD_IDENTITY_PROVIDER`, optional `GOOGLE_APPLICATION_CREDENTIALS`

Env Tables (common):
- Inference backend: `QWEN_INFERENCE_BACKEND=modal|gke|mock`, `LLAVA_INFERENCE_BACKEND=modal|gke|mock`
- Modal tokens: `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`
- GKE inference endpoints: `QWEN_SERVICE_URL`, `LLAVA_SERVICE_URL`
- Token limits: `QWEN_MODAL_MAX_NEW_TOKENS=4096`, `LLAVA_MODAL_MAX_NEW_TOKENS=4096`
- RAG: `ENABLE_RAG=true|false`, Vertex config if enabled (see `docs/TESTING.md`)

---

## Deployment

### Architecture
- Frontend: React/TypeScript on GKE
- Backend: FastAPI on GKE
- Inference: Choose **Modal (default)** or **GKE GPU** via config/env (see ConfigMap)
- CI: `.github/workflows/ci.yml` (tests + coverage); deploy only after CI success
- CD: `.github/workflows/deploy.yml` (dispatch-only, triggered from CI when all checks pass)

### GKE (frontend/backend; optional GPU inference)
1) Build & push images (example):
```bash
docker build -t gcr.io/$GCP_PROJECT_ID/cad-backend:latest src/cad_coder_backend
docker build -t gcr.io/$GCP_PROJECT_ID/cad-frontend:latest src/ui
docker push gcr.io/$GCP_PROJECT_ID/cad-backend:latest
docker push gcr.io/$GCP_PROJECT_ID/cad-frontend:latest
```
2) Apply manifests:
```bash
kubectl apply -f infrastructure/kubernetes/configmap.yaml
kubectl apply -f infrastructure/kubernetes/backend-deployment.yaml
kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml
# GPU inference (optional):
kubectl apply -f infrastructure/kubernetes/qwen-inference-deployment.yaml
kubectl apply -f infrastructure/kubernetes/llava-inference-deployment.yaml
```
3) Expose via ingress/service per manifests.

### Modal Labs (default inference)
- Deploy Modal apps (CLI):
```bash
modal deploy src/model_inference/qwen/modal_app.py
modal deploy src/model_inference/llava_modal/modal_app.py
```
- Ensure ConfigMap sets `QWEN_INFERENCE_BACKEND=modal`, `LLAVA_INFERENCE_BACKEND=modal`, app/function names, and tokens in secrets.

### CI/CD Flow
- CI runs on push/PR; enforces coverage ≥60%.
- Deploy workflow is dispatch-only and triggered from CI after all jobs succeed on `main`.

---

## Usage

### API (Backend on GKE)
- `POST /api/generate_cad` — body: `{ "prompt": "...", "model_choice": "llava|qwen", "image_path": "<base64 or URL>" }`
- Streaming: `POST /api/generate_cad_stream` (SSE) for token streaming.
- History/RAG: `/api/history/*`, `/api/history/context`
- Health: `/api/health/`

#### Curl example (streaming)
```bash
curl -N -X POST http://<backend>/api/generate_cad_stream \
  -H "Content-Type: application/json" \
  -d '{"prompt":"make a cube","model_choice":"llava"}'
```

### Frontend
- Access the deployed frontend URL (Ingress). Select model (Qwen/LLaVA), enter prompt, optionally upload/reference an image. Streaming responses appear in the chat pane.

### Switching inference backend
- Set in ConfigMap or env:
  - `QWEN_INFERENCE_BACKEND=modal|gke|mock`
  - `LLAVA_INFERENCE_BACKEND=modal|gke|mock`
- Modal paths require Modal tokens + app/function names.
- GKE paths require service URLs (`QWEN_SERVICE_URL`, `LLAVA_SERVICE_URL`) and GPU nodes.

### ML Workflow (GKE or Modal, mocked for CI)
- Orchestrator: `src/model_finetuning/ml_workflow/orchestrator.py`
- Triggers (mock): `gcp_trigger_mock.py`
- Deployment (mock): `deployment.py`
- CI tests cover control-flow; heavy GPU train/eval is mocked.

### Quick local dev (Docker)
- Backend dev stack (hot reload, Mongo):
```bash
cd src/cad_coder_backend
docker compose up -d backend mongo
```
- Frontend dev:
```bash
cd src/ui
docker compose -f docker-compose.dev.yml up
```
- Data versioning tests:
```bash
cd src/data_versioning
docker compose -f docker-compose.test.yml run --rm test
```

---

## Testing
- Backend: `docker compose -f docker-compose.test.yml run --rm test` (unit); `integration`; `e2e` (mocked by default)
- Frontend: `npm test -- --coverage`
- Model finetuning: `cd src/model_finetuning && docker compose run --rm test`
- Data versioning: `cd src/data_versioning && docker compose -f docker-compose.test.yml run --rm test`
- Coverage aggregation enforced at 60% in CI (current ~61.4%).

---

## Known Issues / Limitations
- GPU-heavy code paths (`centralized_train.py`, `evaluate_model.py`, CADRL) are mocked in CI; real training/eval requires GPUs.
- Modal deploy/build requires network and Modal credentials; GKE GPU availability depends on quotas.
- Auth router may be disabled by config; tests focus on auth_service logic.
- `.env` loading is skipped on permission-restricted environments; rely on env vars in CI/CD.
- E2E tests default to mocked inference; real Modal/GKE inference requires credentials/endpoints.

---

## Configuration Quick Reference
- ConfigMap keys (see `infrastructure/kubernetes/configmap.yaml`):
  - `QWEN_INFERENCE_BACKEND`, `LLAVA_INFERENCE_BACKEND`
  - Modal: `QWEN_MODAL_APP`, `QWEN_MODAL_STREAM_FUNCTION`, `LLAVA_MODAL_APP`, `LLAVA_MODAL_STREAM_FUNCTION`, token refs in secrets
  - Max tokens: `QWEN_MODAL_MAX_NEW_TOKENS=4096`, `LLAVA_MODAL_MAX_NEW_TOKENS=4096`
- Backend env (examples):
  - `MONGO_URI`, `MONGO_DB`
  - `QWEN_SERVICE_URL`, `LLAVA_SERVICE_URL` (for GKE inference)
  - `ENABLE_RAG` (true/false)

---

## Troubleshooting
- Docker Hub/network timeouts: rerun with `docker compose ... --pull` or add retries.
- Modal auth errors: ensure `MODAL_TOKEN_ID/SECRET` are set; `modal token set ...`.
- GKE GPU pending: check quotas (`gcloud compute project-info describe`) and node pool taints/labels.
- `.env` permission denied in CI: benign; env vars are provided via ConfigMap/secrets.
- E2E mocked by default; real inference requires setting Modal/GKE endpoints + tokens.

---

## Key Docs
- Testing & coverage: `docs/TESTING.md`
- Model finetuning/workflow: `docs/MODEL_FINETUNING.md`, `src/model_finetuning/ml_workflow/*`
- Data versioning: `src/data_versioning/DATA_VERSIONING.md`
- Infrastructure: `infrastructure/README.md`, Kubernetes manifests under `infrastructure/kubernetes/`
- CI/CD: `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`

---

## Support / Contributions
- CI must pass with coverage ≥60%.
- Follow existing patterns for mocks in tests to avoid external calls.
- Prefer Modal for inference (easier to setup) unless GKE GPUs are available.

