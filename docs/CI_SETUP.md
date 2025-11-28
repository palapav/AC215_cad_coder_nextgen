# CI/CD Setup Summary

This document summarizes the Continuous Integration and Testing setup for the CAD-Coder project.

## ✅ CI Pipeline Overview

### Key Features

- **Fully Containerized**: All tests run in Docker containers for consistency
- **Full Repository Coverage**: Tests cover backend, model-finetuning, datapipeline, data-versioning, and UI
- **Reduced Token Counts**: Integration/E2E tests use 128 tokens (vs 4096 production) for speed
- **Parallel Execution**: Independent jobs run concurrently
- **50% Coverage Threshold**: Combined coverage across all components must meet 50%

### GitHub Actions Workflow

- **Location**: `.github/workflows/ci.yml`
- **Triggers**: Push and Pull Requests to `main`, `master`, `develop` branches

### Pipeline Jobs

| Job | Duration | Description |
|-----|----------|-------------|
| `lint-python` | ~1 min | Python code quality (Ruff, Black) |
| `lint-frontend` | ~2 min | TypeScript validation + build |
| `model-finetuning-tests` | ~3 min | CPU-only model tests via Docker |
| `backend-tests` | ~2 min | Unit tests via Docker Compose |
| `backend-integration-tests` | ~2 min | Integration tests with MongoDB |
| `datapipeline-tests` | ~2 min | Data pipeline tests via Docker |
| `data-versioning-tests` | ~1 min | Data versioning script tests |
| `ui-tests` | ~2 min | React component tests (Vitest) |
| `docker-build` | ~5 min | All Docker image builds |
| `e2e-tests` | ~3 min | End-to-end API tests (main branch only) |
| `coverage-summary` | ~30 sec | Aggregate coverage reports |

## 🚀 Quick Start: Run All Tests

### Single Command (Docker Compose)

```bash
# From repository root
docker compose -f docker-compose.tests.yml up --build --abort-on-container-exit repo-tests
```

### Shell Script

```bash
# From repository root
./scripts/run_all_tests.sh
```

## 🐳 Containerized Testing by Component

### Backend Tests

```bash
cd src/cad_coder_backend

# Run all unit tests
docker compose -f docker-compose.test.yml run --rm test

# Run integration tests (with MongoDB)
docker compose -f docker-compose.test.yml run --rm integration

# Run E2E tests (mocked backends)
docker compose -f docker-compose.test.yml run --rm e2e

# Run linting
docker compose -f docker-compose.test.yml run --rm lint

# Run all tests
docker compose -f docker-compose.test.yml run --rm all

# Cleanup
docker compose -f docker-compose.test.yml down -v
```

### Model Fine-tuning Tests

```bash
cd src/model_finetuning

# Run tests via Docker
docker compose run --rm test

# Cleanup
docker compose down -v
```

### Data Pipeline Tests

```bash
cd src/datapipeline

# Run tests via Docker
docker compose -f docker-compose.test.yml run --rm test

# Cleanup
docker compose -f docker-compose.test.yml down -v
```

### Data Versioning Tests

```bash
cd src/data_versioning

# Run tests via Docker
docker compose -f docker-compose.test.yml run --rm test

# Cleanup
docker compose -f docker-compose.test.yml down -v
```

### UI Tests (React/Vitest)

```bash
cd src/ui

# Run tests via Docker
docker compose -f docker-compose.test.yml run --rm test

# Or run locally
npm ci
npm run test:coverage

# Cleanup
docker compose -f docker-compose.test.yml down -v
```

## ⚡ Reduced Token Configuration

For faster integration and E2E tests, token counts are automatically reduced:

| Setting | Production | Testing |
|---------|------------|---------|
| `QWEN_MODAL_MAX_NEW_TOKENS` | 4096 | 128 |
| `LLAVA_MODAL_MAX_NEW_TOKENS` | 3450 | 128 |

This is configured in:
- `docker-compose.test.yml` (environment variables)
- `env.test.template` (template for local testing)
- GitHub Actions workflow (env section)

## 📁 Test File Structure

```
src/
├── cad_coder_backend/
│   ├── Dockerfile.test           # Test container image
│   ├── docker-compose.test.yml   # Test orchestration
│   ├── requirements-test.txt     # Test dependencies
│   ├── pyproject.toml            # pytest/coverage config
│   ├── .coveragerc               # Coverage settings
│   └── app/tests/
│       ├── conftest.py           # Shared fixtures
│       ├── test_endpoints.py     # Basic endpoint tests
│       ├── test_services.py      # Service unit tests
│       └── test_routers.py       # Router integration tests
├── model_finetuning/
│   ├── Dockerfile                # CPU-only test container
│   ├── docker-compose.yml        # Test orchestration
│   ├── requirements-cpu.txt      # CPU dependencies
│   ├── .coveragerc               # Coverage settings
│   └── tests/
│       ├── conftest.py
│       ├── test_config.py
│       ├── test_datasets.py
│       ├── test_model_utils.py
│       └── test_training_utils.py
├── datapipeline/
│   ├── Dockerfile.test           # Test container
│   ├── docker-compose.test.yml   # Test orchestration
│   ├── requirements-test.txt     # Test dependencies
│   ├── .coveragerc               # Coverage settings
│   └── tests/
│       ├── conftest.py
│       ├── test_ingestion.py
│       ├── test_preprocessing.py
│       └── test_rag.py
├── data_versioning/
│   ├── Dockerfile.test           # Test container
│   ├── docker-compose.test.yml   # Test orchestration
│   ├── requirements-test.txt     # Test dependencies
│   └── tests/
│       ├── conftest.py
│       ├── test_convert_raw.py
│       └── test_prepare_user_data.py
├── ui/
│   ├── Dockerfile.test           # Test container
│   ├── docker-compose.test.yml   # Test orchestration
│   ├── vitest.config.ts          # Vitest configuration
│   └── src/__tests__/
│       ├── setup.ts              # Test setup
│       ├── App.test.tsx          # App tests
│       ├── components.test.tsx   # Component tests
│       └── AIModelSandbox.test.tsx
└── env.test.template             # Test environment template
```

## 🧪 Test Categories

### Unit Tests
- Isolated function testing
- Mocked external dependencies
- Fast execution (~seconds)

### Integration Tests
- Real MongoDB connection
- Mocked Modal/RAG backends
- API endpoint testing

### E2E Tests
- Full application stack
- Optional real Modal (if credentials provided)
- Runs on main branch only

## 📊 Coverage Configuration

### Coverage Targets

| Component | Target | Rationale |
|-----------|--------|-----------|
| Backend | 50% | Core services and routers |
| Model Fine-tuning | 50% | Excludes GPU-only code |
| Data Pipeline | 40% | Excludes GCS-dependent code |
| Data Versioning | 50% | Script validation |
| UI | 50% | Core components (excludes shadcn/ui) |
| **Combined** | **50%** | Enforced in CI |

### Coverage Aggregation

The `scripts/aggregate_coverage.py` script combines coverage from all components:

```bash
python scripts/aggregate_coverage.py \
  --threshold 0.50 \
  src/cad_coder_backend/coverage/backend.xml \
  src/model_finetuning/coverage/model_finetuning.xml \
  src/datapipeline/coverage/datapipeline.xml \
  src/data_versioning/coverage/data_versioning.xml
```

## 🔧 Local Development

### Setup Test Environment

```bash
# Copy test environment template
cp src/env.test.template src/.env.test

# Edit with your values (optional for mocked tests)
vim src/.env.test
```

### Run Tests Locally (without Docker)

```bash
# Backend
cd src/cad_coder_backend
pip install -r requirements.txt -r requirements-test.txt
QWEN_INFERENCE_BACKEND=mock LLAVA_INFERENCE_BACKEND=mock ENABLE_RAG=false \
pytest app/tests/ -v --cov=app

# UI
cd src/ui
npm ci
npm run test:coverage
```

## 🔄 CI Pipeline Flow

```
Push/PR
   │
   ├─► lint-python ─────────────────────────────────────────────┐
   ├─► lint-frontend ───────────────────────────────────────────┤
   ├─► model-finetuning-tests (Docker) ─────────────────────────┤
   ├─► backend-tests (Docker) ──────────────────────────────────┤
   ├─► backend-integration-tests (Docker) ──────────────────────┤
   ├─► datapipeline-tests (Docker) ─────────────────────────────┤
   ├─► data-versioning-tests (Docker) ──────────────────────────┤
   ├─► ui-tests (Vitest) ───────────────────────────────────────┤
   └─► docker-build ────────────────────────────────────────────┤
                                                                │
                                                                ▼
                                                      e2e-tests (main branch only)
                                                                │
                                                                ▼
                                                      coverage-summary (≥50% enforced)
```

## 📝 Adding New Tests

### Backend Service Test

```python
# app/tests/test_services.py
class TestNewService:
    def test_feature(self):
        from app.services.new_service import feature
        result = feature()
        assert result is not None
```

### Backend Router Test

```python
# app/tests/test_routers.py
def test_new_endpoint():
    response = client.get("/new/endpoint")
    assert response.status_code == 200
```

### UI Component Test

```tsx
// src/__tests__/NewComponent.test.tsx
import { render, screen } from '@testing-library/react'
import { NewComponent } from '../components/NewComponent'

describe('NewComponent', () => {
  it('renders correctly', () => {
    render(<NewComponent />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })
})
```

### E2E Test (with marker)

```python
# app/tests/test_e2e.py
import pytest

@pytest.mark.e2e
def test_full_workflow():
    # This only runs with: pytest -m e2e
    pass
```

## 🚀 Quick Commands

```bash
# Run all tests (single command)
docker compose -f docker-compose.tests.yml up --build --abort-on-container-exit repo-tests

# Or use the shell script
./scripts/run_all_tests.sh

# Individual component tests
cd src/cad_coder_backend && docker compose -f docker-compose.test.yml run --rm test
cd src/model_finetuning && docker compose run --rm test
cd src/datapipeline && docker compose -f docker-compose.test.yml run --rm test
cd src/data_versioning && docker compose -f docker-compose.test.yml run --rm test
cd src/ui && docker compose -f docker-compose.test.yml run --rm test

# Cleanup all test containers
docker compose -f docker-compose.tests.yml down -v
```

## 🔗 Related Documentation

- [Model Fine-tuning](MODEL_FINETUNING.md)
- [Data Versioning](DATA_VERSIONING.md)
- [Application Design](APPLICATION_DESIGN.md)
- [Quick Start](../README.md)
