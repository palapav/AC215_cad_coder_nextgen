# Overall Structure:
cad_coder_backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # Entry point of the FastAPI app — sets up CORS, logging, loads .env, and registers routers
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── generate.py              # Accepts JSON requests from React; supports model_choice (LLaVA/Qwen) and RAG context
│   │   ├── history.py               # Handles history retrieval and RAG context endpoint (/history/context)
│   │   ├── health.py                # Basic system status check for Docker & CI/CD probes
│   │   ├── auth.py                  # Verifies Google OAuth tokens from frontend login (via google-auth)
│   │   └── pipeline.py              # Allows triggering of ingestion/preprocessing/RAG containers via API (/pipeline/{stage})
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── model_service.py         # Core ML logic — generates CAD code using either LLaVA or Qwen model
│   │   ├── db_service.py            # Connects to MongoDB; inserts/retrieves user history; adds get_all_prompts() for RAG
│   │   ├── gcs_service.py           # Handles upload/download of CAD code or assets to Google Cloud Storage (GCS)
│   │   ├── auth_service.py          # Validates Google OAuth tokens and extracts verified user info
│   │   ├── rag_service.py           # Retrieves similar past prompts or context (RAG-based contextual augmentation)
│   │   ├── pipeline_service.py      # Triggers Docker containers for ingestion/preprocess/RAG pipeline using subprocess
│   │   ├── logger.py                # Centralized logging utility — writes backend + pipeline logs to PIPELINE_RUN.log
│   │   └── utils.py                 # Common utilities: environment checks, logging setup, dotenv loading, helper functions
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── cad_input.py             # Defines the input schema (prompt, user_id, image path, model_choice, rag_context)
│   │   ├── cad_output.py            # Defines output schema (prompt, generated code, model, gcs_uri, pipeline_stage)
│   │   └── model_choice.py          # Enum model listing valid model options (llava, qwen)
│   │
│   └── tests/
│       ├── __init__.py
│       └── test_endpoints.py        # Pytest-based endpoint tests (health, generate_cad, history/context, auth, pipeline)
│
├── .env                             # Local environment file — defines MongoDB, GCS, Google Auth, and frontend origin
├── pyproject.toml                   # Project metadata and dependencies (FastAPI, google-auth, pytest, etc.)
├── requirements.txt                 # Dependency export for Docker image installation
├── Dockerfile                       # Builds backend container; loads env vars and Google credentials; exposes port 8000
└── docker-compose.yml               # Orchestrates backend + MongoDB + optional pipeline containers (ingestion, preprocess, RAG)



# 🧠 CAD-Coder Backend

A FastAPI-based backend for the CAD-Coder project, supporting:
- Multi-model CAD code generation (LLaVA / Qwen)
- RAG-based context retrieval
- Google authentication
- MongoDB + GCS integration
- Containerized pipeline orchestration (ingestion, preprocessing, RAG)

---

## 🚀 Run Locally
```bash
# start all services
docker compose up --build

#Then visit:
FastAPI Docs → http://localhost:8000/docs

MongoDB UI → localhost:27017 (if needed)

Trigger Pipelines
curl -X POST http://localhost:8000/pipeline/preprocess
