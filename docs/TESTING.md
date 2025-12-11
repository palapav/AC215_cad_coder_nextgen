# Testing Documentation

This document provides comprehensive documentation for the CAD-Coder testing infrastructure, including unit tests, integration tests, and end-to-end tests.

## Overview

CAD-Coder maintains a minimum **60% code coverage** threshold across all components. The testing infrastructure supports both local development and CI/CD pipelines via GitHub Actions. Current combined coverage (CI): **61.4%**.

### Test Categories

| Category | Description | Runs In |
|----------|-------------|---------|
| **Unit Tests** | Test individual functions and classes in isolation | Docker containers |
| **Integration Tests** | Test component interactions with real databases | Docker Compose with MongoDB |
| **End-to-End Tests** | Test full request/response flows | Docker Compose with all services |

## Running Tests

### Backend Tests

```bash
cd src/cad_coder_backend

# Unit tests (with coverage)
docker compose -f docker-compose.test.yml run --rm test

# Integration tests (with MongoDB)
docker compose -f docker-compose.test.yml run --rm integration

# E2E tests (requires Modal credentials for real inference)
docker compose -f docker-compose.test.yml run --rm e2e

# All tests
docker compose -f docker-compose.test.yml run --rm all
```

### Model Fine-tuning Tests

```bash
cd src/model_finetuning

# Run all tests including ML workflow
docker compose run --rm test
```

### Data Versioning Tests

```bash
cd src/data_versioning

# Run data versioning tests
docker compose -f docker-compose.test.yml run --rm test
```

### Frontend Tests

```bash
cd src/ui

# Run Jest tests with coverage
npm test -- --coverage
```

### Data Pipeline (RAG) Tests

```bash
cd src/datapipeline

# Run RAG tests
docker compose -f docker-compose.test.yml run --rm test
```

## CI/CD Pipeline

Tests run automatically on:
- Push to `main` or `aditya-milestone5` branches
- Pull requests to `main`

### GitHub Actions Workflow

The CI pipeline (`.github/workflows/ci.yml`) runs:

1. **Linting**: Python (Ruff, Black) and TypeScript type checking
2. **Model Fine-tuning Tests**: CPU-only tests for training utilities and ML workflow
3. **Backend Tests**: Unit and integration tests with mocked inference
4. **Data Versioning Tests**: Data pipeline and conversion tests
5. **UI Tests**: React component and hook tests
6. **Coverage Aggregation**: Combines all coverage reports and enforces 60% threshold

## Test Coverage by Component (latest CI)

### Backend (`src/cad_coder_backend`)

#### Covered Modules (>80%)

| Module | Coverage | Description |
|--------|----------|-------------|
| `services/model_service.py` | ~69% | Model inference routing and RAG integration |
| `services/modal_client.py` | ~69% | Modal Labs client with image serialization/streaming |
| `services/gke_client.py` | ~59% | GKE inference client with HTTP pooling |
| `services/rag_service.py` | ~41% | RAG retrieval and context prep (disabled/edge paths covered) |
| `services/db_service.py` | ~86% | MongoDB operations |
| `services/auth_service.py` | ~100% | Google OAuth token verification |
| `services/utils.py` | ~43% | Env/logging utilities |
| `routers/*.py` | ~54–94% | FastAPI endpoint handlers (health/generate/history/pipeline/auth) |

#### Streaming Inference Tests

Both GKE and Modal Labs streaming inference are tested:

```python
# Modal streaming test
async def test_stream_modal_qwen_inference_mocked():
    """Test Qwen Modal streaming with mocked function."""
    ...

# GKE streaming test  
async def test_stream_gke_qwen_inference():
    """Test Qwen GKE streaming with mocked HTTP client."""
    ...
```

#### Partially Covered / Not-Critical (<60%)

| Module | Coverage | Reason why not critical to exceed 60% |
|--------|----------|---------------------------------------|
| `main.py` | ~40% | Startup wiring/CORS; exercised indirectly by router tests; low business logic risk |
| `routers/auth.py` | ~50% | OAuth flow depends on external Google credentials; core path validated via auth_service tests |

### Model Fine-tuning (`src/model_finetuning`)

#### Covered Modules (key ones; overall ~47%)

| Module | Coverage | Description |
|--------|----------|-------------|
| `ml_workflow/config.py` | ~100% | Configuration constants |
| `ml_workflow/validation.py` | ~95% | Model performance validation |
| `ml_workflow/deployment.py` | ~100% | Deployment to GKE/Modal Labs (mocked) |
| `ml_workflow/gcp_trigger_mock.py` | ~93% | GCP trigger simulation |
| `ml_workflow/orchestrator.py` | ~40% | Workflow orchestration; core control flow covered, heavy/train steps mocked |
| `tests/test_config.py` | N/A | Config validation tests |
| `tests/test_datasets.py` | N/A | Dataset loading tests |
| `tests/test_training_utils.py` | N/A | Training utility tests |

#### Not Covered / Low-Criticality (requires GPU or heavy runtime)

| Module | Reason why not critical beyond current threshold |
|--------|-----------------------------------------------|
| `centralized_train.py` | GPU training pipeline; unsafe/slow in CI; validated indirectly via orchestrator mocks |
| `evaluate_model.py` | GPU inference; CI exercises validation logic via mocks instead |
| `CADRL/*.py` | Model architecture/loading; GPU-bound; outside CI scope |
| `modal_workflow.py` | Modal deployment image build; integration validated by mocks in tests; real run is external |

### Data Versioning (`src/data_versioning`)

#### Covered Modules (now ~95%)

| Module | Coverage | Description |
|--------|----------|-------------|
| `scripts/convert_raw_to_jsonl.py` | ~99% | Raw data conversion (incl. CLI) |
| `scripts/prepare_user_data.py` | ~99% | User data preparation (incl. CLI) |
| `scripts/create_v2.py` | ~100% | Combine v1 + user data (incl. CLI) |

### Data Pipeline (`src/datapipeline`)

#### Covered Modules

| Module | Coverage | Description |
|--------|----------|-------------|
| `rag/config.py` | ~100% | RAG configuration |
| `rag/processing_utils.py` | ~90% | Text chunking and retry logic |
| `rag/storage_utils.py` | ~70% | GCS storage operations |

#### Partially Covered

| Module | Coverage | Reason |
|--------|----------|--------|
| `rag/embedding_generator.py` | ~50% | Requires Google Cloud credentials |
| `rag/multimodal_rag.py` | ~40% | Requires Vertex AI access |

### Frontend (`src/ui`)

#### Covered Components

| Component | Coverage | Description |
|-----------|----------|-------------|
| `App.tsx` | ~80% | Main application component |
| `AIModelSandbox.tsx` | ~85% | CAD generation interface |
| `ChatInput.tsx` | ~90% | User input handling |
| `ChatMessage.tsx` | ~90% | Message display |
| `ChatHistory.tsx` | ~85% | History management |
| `ModelSelector.tsx` | ~90% | Model selection (Qwen/LLaVA) |

## Untested Code Summary

### Requires External Services

| File | Service Required |
|------|-----------------|
| `src/model_inference/qwen/modal_app.py` | Modal Labs runtime |
| `src/model_inference/llava_modal/modal_app.py` | Modal Labs runtime |
| `src/datapipeline/rag/multimodal_rag.py` | Google Vertex AI |

### Requires GPU

| File | Description |
|------|-------------|
| `src/model_finetuning/centralized_train.py` | Model training script |
| `src/model_finetuning/evaluate_model.py` | Model evaluation |
| `src/model_finetuning/CADRL/*.py` | Model architecture and loading |

### Infrastructure Code

| File | Description |
|------|-------------|
| `infrastructure/pulumi/__main__.py` | IaC definitions (tested via `pulumi preview`) |
| `infrastructure/kubernetes/*.yaml` | K8s manifests (tested via `kubectl --dry-run`) |

## Test Fixtures and Mocking

### Backend Test Fixtures

```python
# conftest.py provides:
@pytest.fixture
def mock_collection():
    """Mock MongoDB collection."""
    ...

@pytest.fixture
def sample_image():
    """Create a sample PIL image for testing."""
    ...
```

### Mocking External Services

```python
# Mock Modal Labs inference
with patch('app.services.modal_client._lookup_qwen_modal_function', return_value=mock_fn):
    result = await run_modal_qwen_inference(prompt="test")

# Mock GKE HTTP client
with patch('app.services.gke_client._get_http_client', return_value=mock_client):
    result = await run_gke_qwen_inference(prompt="test")
```

## Coverage Enforcement

The CI pipeline enforces a **60% minimum coverage** threshold:

```yaml
# .github/workflows/ci.yml
- name: Aggregate coverage and enforce threshold
  run: |
    python scripts/aggregate_coverage.py \
      --threshold 0.60 \
      --ignore-missing \
      $COVERAGE_FILES
```

## Adding New Tests

### Backend Test Template

```python
# app/tests/test_new_feature.py
import pytest
from unittest.mock import Mock, patch, AsyncMock

class TestNewFeature:
    """Test new feature functionality."""

    def test_basic_functionality(self):
        """Test basic feature behavior."""
        from app.services.new_feature import my_function
        
        result = my_function("input")
        assert result == "expected"

    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async feature behavior."""
        from app.services.new_feature import my_async_function
        
        result = await my_async_function("input")
        assert result == "expected"
```

### ML Workflow Test Template

```python
# tests/test_new_workflow.py
import pytest
from unittest.mock import Mock, patch

class TestNewWorkflow:
    """Test new workflow functionality."""

    def test_workflow_step(self):
        """Test individual workflow step."""
        from ml_workflow.new_module import workflow_step
        
        result = workflow_step(input_data)
        assert result["status"] == "success"
```

## Troubleshooting

### Common Issues

1. **Docker not running**: Ensure Docker Desktop is running before executing tests
2. **Port conflicts**: Stop any services using ports 27017 (MongoDB) or 8080 (backend)
3. **Coverage not generated**: Ensure `coverage/` directory exists with write permissions

### Debug Mode

```bash
# Run tests with verbose output
docker compose -f docker-compose.test.yml run --rm test pytest -v -s --tb=long

# Run specific test file
docker compose -f docker-compose.test.yml run --rm test pytest app/tests/test_services.py -v
```

## Platform Support

### GKE (Google Kubernetes Engine)

- All GKE client functions are tested with mocked HTTP responses
- Streaming inference is tested with async generators
- Health checks are tested for failure scenarios

### Modal Labs

- Modal client functions are tested with mocked function handles
- Streaming functions use `remote_gen()` mocking
- Credential validation is tested for missing/partial credentials

Both platforms are treated equally in the test suite to maintain deployment flexibility.

