# CI/CD Pipeline Documentation

This directory contains GitHub Actions workflows for continuous integration and testing.

## Workflow: `ci.yml`

The CI pipeline runs automatically on:
- Push to `main`, `master`, or `develop` branches
- Pull requests targeting `main`, `master`, or `develop` branches

### Jobs

#### 1. Backend Tests
- **Purpose**: Test the FastAPI backend application
- **Services**: MongoDB (for database tests)
- **Steps**:
  - Set up Python 3.11
  - Install dependencies
  - Lint code with `ruff`
  - Format check with `black`
  - Run unit tests with `pytest`
  - Generate coverage reports (XML, HTML, terminal)
  - Check coverage threshold (50% minimum)
  - Upload coverage artifacts

#### 2. Frontend Tests
- **Purpose**: Test the React/TypeScript frontend application
- **Steps**:
  - Set up Node.js 20
  - Install dependencies
  - Lint code with ESLint
  - Type check with TypeScript
  - Build the application

#### 3. Integration Tests
- **Purpose**: Test API and database integration
- **Services**: MongoDB
- **Steps**:
  - Set up Python 3.11
  - Install dependencies
  - Run integration tests
  - Append coverage to backend coverage

#### 4. E2E Tests
- **Purpose**: Test end-to-end workflows
- **Dependencies**: Backend and Frontend tests must pass
- **Steps**:
  - Set up Python and Node.js
  - Install dependencies for both backend and frontend
  - Run end-to-end tests

#### 5. Coverage Report
- **Purpose**: Generate and display coverage reports
- **Dependencies**: Backend and Integration tests
- **Steps**:
  - Download coverage artifacts
  - Comment on PRs with coverage information
  - Minimum coverage: 50% (green), 40% (orange)

## Coverage Requirements

- **Minimum Coverage**: 50%
- **Coverage Tools**: `pytest-cov`
- **Reports Generated**:
  - XML (for CI integration)
  - HTML (for detailed viewing)
  - Terminal (for quick feedback)

## Linting

### Python
- **Black**: Code formatting
- **Ruff**: Fast Python linter (replaces flake8, isort, etc.)
- **Configuration**: `pyproject.toml` and `.ruff.toml`

### TypeScript/React
- **ESLint**: JavaScript/TypeScript linting
- **TypeScript**: Type checking
- **Configuration**: `.eslintrc.cjs` and `tsconfig.json`

## Running Tests Locally

### Backend
```bash
cd cad_coder_backend
pip install -r requirements.txt
pytest app/tests/ -v --cov=app --cov-report=term-missing
```

### Frontend
```bash
cd ui
npm install
npm run lint
npm run type-check
npm run build
```

### Integration Tests
```bash
cd cad_coder_backend
pytest app/tests/integration/ -v
```

### E2E Tests
```bash
cd cad_coder_backend
pytest app/tests/e2e/ -v
```

## Test Structure

```
app/tests/
├── test_endpoints.py      # API endpoint tests
├── test_services.py        # Service unit tests
├── test_models.py         # Model validation tests
├── integration/
│   ├── test_api_integration.py
│   └── test_db_integration.py
└── e2e/
    └── test_e2e_workflow.py
```

## Environment Variables

The CI pipeline uses the following environment variables:
- `MONGO_URI`: MongoDB connection string (default: `mongodb://localhost:27017`)
- `MONGO_DB`: Database name (default: `cad_coder_test`)

## Artifacts

Coverage reports are uploaded as artifacts:
- `backend-coverage/coverage.xml`: XML coverage report
- `backend-coverage/htmlcov/`: HTML coverage report

These can be downloaded from the GitHub Actions run page.

