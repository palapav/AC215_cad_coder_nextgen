## 1. Solution Architecture

This document describes how CAD‑Coder transforms multimodal inputs (text and images) into editable parametric CAD code, and how the repository is structured to support this flow.

### High‑Level Overview

The current system is implemented as a set of containerized services plus remote GPU workers:

1. **User Experience Layer (`ui/`)**
   - React + Vite SPA that provides:
     - A multimodal chat interface (Text‑to‑CAD, Image‑to‑CAD).
     - An editor for generated `cadquery` Python code.
     - A browser‑side CAD preview panel.
   - Communicates only with the FastAPI backend via HTTP/JSON.

2. **Application & API Layer (`src/cad_coder_backend/`)**
   - FastAPI backend that:
     - Exposes `/generate_cad`, `/history`, `/pipeline/*`, `/health`, and auth endpoints.
     - Validates requests, manages authentication, and logs interactions.
     - Orchestrates retrieval‑augmented generation (RAG) and calls out to remote model workers on Modal Labs.

3. **Model Inference & Retrieval Layer**
   - **Modal‑hosted models (`src/model_inference/`):**
     - A fine‑tuned **Qwen3‑VL** model and a fine‑tuned **CAD‑Coder LLaVA** model run as separate Modal apps.
     - Each Modal worker lazily initializes its model once per container and uses a persistent volume to cache Hugging Face weights.
   - **RAG service (`src/datapipeline/rag/` + backend `rag_service.py`):**
     - Uses Google Cloud’s **Vertex AI Matching Engine** to retrieve similar CAD examples/documentation.
     - Injects retrieved context into the Qwen prompt path before inference, improving faithfulness and code quality.

4. **Data, Training, and Versioning Layer**
   - **Fine‑tuning (`src/model_finetuning/`):**
     - CADRL‑based centralized training scripts for Qwen3‑VL 2B/4B/8B models on the GenCAD‑Code dataset (run on an external H100 cluster).
   - **Data pipelines (`src/datapipeline/`):**
     - Ingestion and preprocessing workflows for constructing training datasets and RAG indices.
   - **Data versioning (`src/data_versioning/`):**
     - DVC‑backed dataset versions:
       - **V1** – Original, static GenCAD‑Code dataset (used for full fine‑tuning).
       - **V2** – V1 plus curated user/LLM‑generated data.

### Milestone 4 vs. Milestone 5 Model Serving

- **Milestone 4 (Current): Modal Labs**
  - Both the fine‑tuned **Qwen3‑VL** model and the **CAD‑Coder LLaVA** baseline are deployed on **Modal Labs**.
  - This provides:
    - **Fast iteration and low operational overhead** for GPU serving during active development.
    - **Cost efficiency** by leveraging approximately **$500 of existing Modal credits**.
    - **Simple integration** with the Python backend via the Modal SDK, keeping the backend container CPU‑only.

- **Milestone 5 (Planned): Migration to Google Cloud Platform**
  - The model serving layer will be migrated from Modal to **GCP** (e.g., **Vertex AI** or **GKE with GPU node pools**) to:
    - Align inference with the existing GCP footprint (Vertex AI Matching Engine, GCS, IAM).
    - Gain **hyperscaler‑grade scalability**, autoscaling, and SLO‑driven operations.
    - Centralize security, monitoring, and cost governance within one cloud environment.
  - Modal is thus treated as a pragmatic, credit‑backed deployment for rapid experimentation in Milestone 4, with GCP as the long‑term production‑grade serving platform in Milestone 5.

### Component Interactions & Data Flow

1. **User request (UI → Backend)**  
   The React UI sends a JSON payload to FastAPI with the prompt, optional image (base64 or reference), and selected model (`llava` or `qwen`).

2. **Backend orchestration (FastAPI)**  
   - Validates the request with Pydantic models.  
   - For Qwen:
     - Calls into the RAG service to fetch relevant CAD examples from Vertex AI Matching Engine.
     - Augments the prompt with retrieved context.  
   - For LLaVA:
     - Sends the raw prompt and image to the LLaVA Modal worker (no RAG).

3. **Remote model inference (Modal Labs)**  
   - Modal workers preprocess the image, run the appropriate VLM on GPU, and stream back generated CADQuery code to the backend.

4. **Response and persistence**  
   - The backend wraps the generated code and RAG metadata into a `CADOutput` schema and stores the interaction in MongoDB.
   - The UI displays the code and updates the 3D preview.

5. **Offline pipelines and dataset versioning**  
   - Batch jobs under `src/datapipeline/` and `src/data_versioning/`:
     - Export curated interaction data from MongoDB.
     - Convert raw data to JSONL and build DVC‑tracked dataset versions (V1, V2, …).  
   - The backend **does not** auto‑append online data to training sets; versioning is performed offline for reproducibility.

---

## 2. Technical Architecture

This section outlines the concrete technologies, frameworks, and design patterns actually used in the current implementation.

### Technologies & Frameworks

- **Frontend (`ui/`):**
  - React, Vite, TypeScript.

- **Backend API (`src/cad_coder_backend/`):**
  - FastAPI, Pydantic, Uvicorn/Gunicorn.
  - MongoDB (via Docker Compose).
  - Google Cloud client libraries (Vertex AI, GCS, auth).

- **Model Inference (`src/model_inference/`):**
  - PyTorch, Transformers, Qwen3‑VL, CAD‑Coder (LLaVA‑based).
  - Modal Labs for GPU‑backed inference workers and volumes.

- **RAG (`src/datapipeline/rag/` + `rag_service.py`):**
  - Vertex AI Matching Engine for vector search.
  - Custom retrieval and embedding utilities for CAD code and documentation.

- **Data Versioning (`src/data_versioning/`):**
  - DVC for diff‑based dataset versioning.
  - JSONL train/val/test splits tracked via `.dvc` pointer files.

- **Fine‑tuning (`src/model_finetuning/`):**
  - CADRL library, Accelerate, PEFT/LoRA.
  - External H100 GPU cluster for long‑running training jobs.

- **CI/CD and Tooling:**
  - GitHub Actions workflows for backend, RAG, and model‑finetuning tests.
  - Dockerfiles and docker‑compose files for backend, pipelines, and data versioning.

### Design Patterns

- **Layered Architecture:**  
  UI, API, model inference, RAG, and data pipelines are separated cleanly, allowing each to evolve independently.

- **Service‑oriented decomposition inside a monorepo:**  
  Each major concern (backend, inference, pipelines, finetuning, data versioning) lives in its own top‑level `src/*` subtree.

- **Retrieval‑Augmented Generation (RAG):**  
  The Qwen path explicitly calls RAG before inference, treating retrieved CAD examples as first‑class context rather than an afterthought.

- **Lazy initialization and remote execution:**  
  Modal workers initialize models only once per container, and the backend remains lightweight by delegating all heavy GPU work to Modal.

- **Offline, versioned data management:**  
  All large datasets are tracked with DVC; user‑generated data is incorporated into new versions via offline batch jobs, not real‑time mutation.

---

## 3. Code Organization

The repository is organized by concern and lifecycle stage to keep runtime services, pipelines, and research code clearly separated.

- **`/ui/`** – React + Vite frontend
  - `src/components/` – Chat UI, image upload, CAD preview components.
  - `src/services/` – API client hooks for calling the FastAPI backend.

- **`/src/cad_coder_backend/`** – FastAPI backend
  - `app/main.py` – Backend entrypoint.
  - `app/routers/` – Route handlers (`generate.py`, `history.py`, `health.py`, `auth.py`, `pipeline.py`).
  - `app/services/` – Business logic and integrations (`model_service.py`, `modal_client.py`, `rag_service.py`, `db_service.py`, etc.).
  - `app/models/` – Pydantic schemas (`cad_input.py`, `cad_output.py`, `model_choice.py`).
  - `app/tests/` – Backend tests.
  - `Dockerfile`, `docker-compose.yml` – Backend + MongoDB + optional pipeline services.

- **`/src/model_inference/`** – Model inference and evaluation
  - `qwen/` – Qwen3‑VL Modal app, evaluation scripts, and utilities.
  - `llava_modal/` – CAD‑Coder LLaVA Modal app and preprocessing utilities.
  - `llava/`, `SolidAlign/`, `docs/`, `scripts/` – Upstream CAD‑Coder/LLaVA and evaluation code.

- **`/src/datapipeline/`** – Data pipelines and RAG
  - `data_ingestion/` – Raw data ingestion utilities and containers.
  - `data_preprocessing/` – Computer‑vision preprocessing for dataset creation.
  - `rag/` – RAG pipeline and Vertex AI Matching Engine integration (`rag_retrieval.py`, `vector_search.py`, etc.).

- **`/src/model_finetuning/`** – Qwen3‑VL fine‑tuning
  - `centralized_train.py`, `evaluate_model.py` – Training and evaluation entrypoints.
  - `CADRL/` – Dataset, collator, trainer, and inference utilities.
  - `results/` – Training and evaluation outputs.
  - `tests/` – CPU‑only unit tests for configuration and training utilities.

- **`/src/data_versioning/`** – DVC‑based dataset versioning
  - `create_all_versions.sh`, `setup_dvc.sh`, `scripts/` – Automation for building V1/V2 JSONL datasets.
  - `data/v1/`, `data/v2/` – DVC‑tracked dataset splits.
  - `Dockerfile`, `docker-compose.yml` – Containerized DVC workflow.

- **`/docs/`** – Project documentation
  - `APPLICATION_DESIGN.md` – Overall architecture and organization (this document).
  - `MODEL_FINETUNING.md` – Fine‑tuning process, results, and deployment implications.
  - `DATA_VERSIONING.md` – Data versioning methodology and usage.

This organization supports the goals of the project: a production‑grade, containerized system with clean separation between user‑facing services, remote model serving (Modal now, GCP later), robust RAG integration, and reproducible data and training pipelines.***