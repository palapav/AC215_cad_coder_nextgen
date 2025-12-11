# cad-coder-nextgen: Fine-tuning and Deploying Large-Scale Vision Language Models for CAD Code Generation

## Milestone2: AC215 CAD-Coder Project MS2 Documentation: Please see the detailed markdown file located in the src/datapipeline folder titled "milestone2.md" as your starting point.

## Milestone3: AC215 CAD-Coder Project MS3 Documentation: Please see the detailed markdown file located in the src/ui folder titled "ui.md" to learn about the additional modifications (added a containerized React UI) we made from Milestone2. Additionally, you can find our midterm MS3 presentation slides here: [https://drive.google.com/file/d/1zJa326zX9a0zp4HBTscuqiaStooRAZat/view?usp=sharing](https://drive.google.com/file/d/1zJa326zX9a0zp4HBTscuqiaStooRAZat/view?usp=sharing)


## Milestone4: Development and Deployment Preparation

###Deliverables:
- Application Design Document can be found in docs/APPLICATION_DESIGN.md
- Data Versioning documentation can be found in DATA_VERSIONING.md (code folder with tests is in src/data_versioning)
- Model Training/Fine-Tuning summary can be found in docs/MODEL_FINETUNING.md (code folder with tests is in src/model_finetuning). Fine-tuning results can be found in /src/model_finetuning/results for both training and eval.
- All source code (APIs, frontend, models, tests) with tests (unit, integration, and e2e) can be found in the src/ folder with proper organization and automated testing for CI setup found in the scripts/ folder
- CI/CD configuration file can be found in .github/workflows/ci.yml (do note that while we have test cases for the data_pipeline folder, they are not executed as part of ci.yml since its core workflow is not used in the application as is. Code is still important to review and is reused in different components in minor capacities).
- README with setup and running instructions for code and test cases can be found below after the evidence section

###Evidence:
- To make things easier, we included screenshots of our app components along with CI evidence. All screenshots can be found in the docs/screenshots folder. 
- milestone4_ci_code_coverage.png: >50% code coverage across unit, integration, and E2E testing for UI, backend, integrations, data versioning, and model fine-tuning
- milestone4_ci_setup.png: Successful build and linting along with other automated checks in our CI setup
- milestone4_llava_ui_text.png: text-only prompt passed as input for llava-based model with response (support is also there for images -> please see milestone4_qwen_ui_image_text.png)
- milestone4_modal_labs_model_inference_containers.png: Running deployed modal labs containers for our 2 models: LLaVa and Qwen3 (own fine-tuning). For ease of use and due to abundance of credits, we deployed models to Modal Labs. This will eventually be migrated to GCP for better scalability and overall app integration.
- milestone4_mongodb.png: MongoDB database entry that stores our chat history
- milestone4_qwen_rag_backend_only.png: partial API response screenshot of the RAG component in use prior to accessing the finetuned Qwen3 model weights we deployed to Modal Labs.
- milestone4_qwen_ui_image_text.png: text-with-image prompt passed as input for qwen-based model with response
- milestone4_ui.png: overall UI shown for our CAD-Coder AI Model Sandbox.

### Quick Start Guide

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
- `model_choice="llava"` - Uses CAD-Coder LLaVA baseline (no RAG by default)

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

Both approaches enforce the global ≥50% coverage requirement by aggregating the backend and model fine-tuning reports (Modal Labs and Google Cloud APIs are mocked, so no external credentials are required). Test suite is also run via CI setup when code is merged into the main branch.

---

## Complete `.env` Template
Note: additional Google Credentials required and provided via key.json that is stored in our template as datapipeline/key.json via GOOGLE_APPLICATION_CREDENTIALS=datapipeline/key.json.
Please reference GCP CLI docs on obtaining a key.json for ease of use.

Here's a complete template for `src/.env`:

```bash
# MongoDB (optional - use MongoDB Atlas in production)
MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>/<database-name>?

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
LLAVA_MODAL_MAX_NEW_TOKENS=4096
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

## Milestone5: Final Project Delivery
Here, we will document all final project delivery deliverables. 



Project Team Members: Yuyan Fan, Jing Xu, Frank Chen, Aditya Palaparthi
Group Name: CAD-Coder

Project:

Computer-Aided Design (CAD) is essential to engineering and
manufacturing, yet creating CAD models remains slow and expertise-driven. Recent advances in
vision-language models (VLMs) offer a chance to accelerate and democratize CAD workflows. Our
project builds on CAD-Coder, an open-source model that converts text and images into CadQuery
Python code. While promising, CAD-Coder has not been systematically evaluated across model scales or
deployed in an accessible interface. We will close this gap by fine-tuning scaled variants, analyzing
performance trends, and deploying them in a chatbot that enables engineers, students, and hobbyists to
generate CAD code interactively. Compared to manual modeling, proprietary CAD tools, or limited AI
plugins, our system lowers barriers to entry, speeds iteration, and contributes new insights into
multimodal model scaling. Our team brings strong data science expertise, including research experience at
MIT on generative AI and 3D engineering design, positioning us well to execute this project.

We aim to design and deploy a scalable chatbot system that generates CAD code from text and/or image inputs, while studying how performance scales across model sizes.

Scope and Objectives: Our project scope is to deploy a research-informed CAD chatbot. Namely:
1. Scaling Analysis
- Fine-tune Qwen-2.5 models (3B, 7B, 14B, 32B, 72B) on the GenCAD dataset and analyze scaling trends in accuracy, efficiency, and robustness.
2. Deployment
- Deploy two models on Google Cloud VertexAI: Original CAD-Coder (LLaV A baseline) and best fine-tuned Qwen-2.5 variant
3. Chatbot Interface
- Build a ChatGPT-style interface with text input + image upload, model selection dropdown, chat history, and Retrieval-Augmented Generation (RAG)
4. Efficient Inference
- Implement optimized pipelines (quantization, FlashAttention, continuous batching,
multi-GPU scheduling) to ensure practical latency and scalability.

Users will include mechanical engineers for rapidly prototyping CAD components, students &
educators for having an accessible entry point for learning CAD, and makers & hobbyists for
generating parts without mastering complex CAD software. Benefits over Alternatives: Unlike
commercial CAD tools or plugins, our system automates code generation directly from natural inputs (text/images), provides open, reproducible research into model scaling, and offers a flexible,
cloud-deployed interface for broader accessibility.
