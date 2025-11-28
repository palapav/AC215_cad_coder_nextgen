# CI/CD Workflows

This directory contains GitHub Actions workflows for continuous integration and testing.

## Workflows

### `ci.yml` - Main CI Pipeline

Triggered on:
- Push to `main`, `master`, `develop`
- Pull requests to these branches

#### Jobs

| Job | Description | Duration |
|-----|-------------|----------|
| `model-finetuning-tests` | CPU-only tests for fine-tuning code | ~3 min |
| `backend-tests` | FastAPI backend tests with MongoDB | ~2 min |
| `data-versioning-tests` | DVC configuration validation | ~1 min |
| `lint` | Ruff and Black code quality checks | ~1 min |
| `docker-build` | Verify Docker images build successfully | ~5 min |

## Test Coverage

### Model Fine-tuning Tests

Tests cover:
- Configuration defaults validation
- Dataset class functionality
- Model utility functions
- Training argument parsing

**Coverage Target**: 50% minimum

### Backend Tests

Tests cover:
- API endpoints
- Service layer
- Pydantic models
- Database integration

**Coverage Target**: 50% minimum

## Running Locally

### Model Fine-tuning Tests

```bash
cd src/model_finetuning

# Install CPU-only dependencies
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-cpu.txt

# Run tests
pytest tests/ -v --cov=. --cov-report=term-missing
```

### Backend Tests

```bash
cd src/cad_coder_backend

# Start MongoDB
docker run -d -p 27017:27017 mongo:6.0

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio

# Run tests
pytest app/tests/ -v --cov=app
```

### Docker Builds

```bash
# Model fine-tuning
cd src/model_finetuning
docker build -t model-finetuning-test .

# Data versioning
cd src/data_versioning
docker build -t data-versioning-test .

# Backend
cd src/cad_coder_backend
docker build -t backend-test .
```

## Environment Variables

### Backend Tests

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `QWEN_INFERENCE_BACKEND` | Qwen backend (`modal` or `mock`) | `mock` |
| `LLAVA_INFERENCE_BACKEND` | LLaVA backend (`modal` or `mock`) | `mock` |
| `ENABLE_RAG` | Enable RAG context retrieval | `false` |

## Troubleshooting

### Tests Failing Due to Missing GPU

The model fine-tuning tests are designed to run on CPU only. If you see GPU-related errors:

1. Ensure you're using `requirements-cpu.txt` (not `requirements.txt`)
2. Check that PyTorch is installed with CPU-only wheels

### Docker Build Failures

Common issues:
- Large build context: Check `.dockerignore` excludes large files
- Network issues: Ensure Docker can access PyPI and PyTorch indices

### Coverage Below Threshold

If coverage drops below 50%:
1. Add more unit tests for uncovered code
2. Check that test files are being discovered (named `test_*.py`)
3. Verify `PYTHONPATH` includes all necessary directories

