# GitHub Actions CI/CD Workflows

This directory contains the CI/CD pipeline configuration for the CAD-Coder project.

## 📋 Workflow: `ci.yml`

The main CI workflow runs on every push and pull request to `main`, `master`, and `develop` branches.

### Jobs Overview

| Job | Duration | Description |
|-----|----------|-------------|
| `lint-python` | ~1 min | Python code quality checks |
| `lint-frontend` | ~2 min | TypeScript validation + build |
| `model-finetuning-tests` | ~3 min | CPU-only model tests (50% coverage) |
| `backend-tests` | ~2 min | FastAPI + MongoDB tests (40% coverage) |
| `data-versioning-tests` | ~1 min | DVC configuration validation |
| `datapipeline-tests` | ~1 min | RAG module syntax checks |
| `docker-build` | ~5 min | Docker image builds |
| `e2e-tests` | ~2 min | End-to-end API tests |
| `coverage-summary` | ~30 sec | Coverage report aggregation |

### Dependency Graph

```
                    ┌─────────────────┐
                    │   Push / PR     │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   lint-python   │ │  lint-frontend  │ │  docker-build   │
└─────────────────┘ └────────┬────────┘ └─────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ model-finetuning│ │  backend-tests  │ │datapipeline-test│
│     tests       │ └────────┬────────┘ └─────────────────┘
└─────────────────┘          │
                             │
                             ▼
                    ┌─────────────────┐
                    │    e2e-tests    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │coverage-summary │
                    └─────────────────┘
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHON_VERSION_BACKEND` | `3.11` | Python version for backend |
| `PYTHON_VERSION_FINETUNING` | `3.10` | Python version for fine-tuning |
| `NODE_VERSION` | `20` | Node.js version for frontend |

### Services

- **MongoDB**: `mongo:6.0` - Used by backend tests and E2E tests

## 📊 Coverage Requirements

| Component | Minimum | Report |
|-----------|---------|--------|
| Model Fine-tuning | 50% | `model-finetuning-coverage` artifact |
| Backend | 40% | `backend-coverage` artifact |

## 🐛 Debugging Failed Builds

### Common Issues

1. **Python Import Errors**
   - Check `PYTHONPATH` configuration
   - Verify dependencies in requirements files

2. **MongoDB Connection Failures**
   - Ensure service health check passes
   - Check `MONGO_URI` environment variable

3. **Coverage Below Threshold**
   - Add more tests or adjust `.coveragerc` omit patterns
   - Check for untested code paths

### Viewing Logs

1. Go to Actions tab in GitHub
2. Click on the failed workflow run
3. Expand the failed job
4. Review step outputs

### Local Debugging

```bash
# Reproduce CI environment locally
act -j backend-tests  # Requires 'act' tool
```

## 📁 Artifacts

The following artifacts are uploaded on each run:

- `model-finetuning-coverage/`
  - `coverage.xml` - XML coverage report
  - `htmlcov/` - HTML coverage report

- `backend-coverage/`
  - `coverage.xml` - XML coverage report
  - `htmlcov/` - HTML coverage report

## 🔄 Workflow Triggers

```yaml
on:
  push:
    branches: [main, master, develop]
  pull_request:
    branches: [main, master, develop]
```

## 📈 Status Badges

Add to your README:

```markdown
![CI](https://github.com/YOUR_ORG/cad-coder-nextgen/actions/workflows/ci.yml/badge.svg)
```

## 🚀 Manual Workflow Dispatch

To add manual triggering, add to `ci.yml`:

```yaml
on:
  workflow_dispatch:
    inputs:
      skip_tests:
        description: 'Skip test jobs'
        required: false
        default: 'false'
```
