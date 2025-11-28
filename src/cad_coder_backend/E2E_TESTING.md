# End-to-End (E2E) Testing Guide

This guide explains how to run end-to-end tests for the CAD-Coder backend, including tests that interact with real services (Modal, MongoDB, GCS) and UI integration tests.

## Overview

E2E tests verify that the entire system works together:
- Backend API endpoints (`test_basic.sh`, `test.sh`)
- UI integration (React frontend → FastAPI backend)
- Real service integration (Modal Labs, MongoDB, GCS)

## Test Types

### 1. **Unit Tests** (No Credentials Needed)
- All services mocked
- Fast execution
- Run via: `docker compose -f docker-compose.test.yml run --rm test`

### 2. **Integration Tests** (Test MongoDB Only)
- Real MongoDB, mocked Modal/GCS
- Run via: `docker compose -f docker-compose.test.yml run --rm integration`

### 3. **E2E Tests** (Real Services)
- Real Modal Labs inference
- Real MongoDB
- Optional: Real GCS
- Run via: `docker compose -f docker-compose.test.yml run --rm e2e`

## Local E2E Testing Setup

### Prerequisites

1. **Virtual Environment** (already set up):
   ```bash
   source env/bin/activate
   pip list  # Should show gcs, modal dependencies
   ```

2. **Environment Variables**:
   - Your `.env` file in `src/` contains production credentials
   - For E2E testing, create `src/.env.test` with test credentials

### Step 1: Create Test Environment File

```bash
# Copy the example template
cp src/.env.test.example src/.env.test

# Edit src/.env.test with your test credentials
# Use separate test databases/buckets, not production!
```

**Important**: `.env.test` is in `.gitignore` - it will NOT be committed.

### Step 2: Start Backend Services

```bash
cd src/cad_coder_backend

# Start MongoDB (if not using Docker)
# Or use Docker Compose:
docker compose -f docker-compose.test.yml up -d mongo-test

# Start the backend server
source ../../env/bin/activate  # Activate your virtual environment
uvicorn app.main:app --reload --port 8000
```

### Step 3: Run E2E Tests

#### Option A: Using Docker Compose (Recommended)

```bash
cd src/cad_coder_backend

# Run E2E tests with real Modal (if .env.test exists)
docker compose -f docker-compose.test.yml run --rm e2e

# Or run with mocked backends (no credentials needed)
QWEN_INFERENCE_BACKEND=mock LLAVA_INFERENCE_BACKEND=mock \
  docker compose -f docker-compose.test.yml run --rm e2e
```

#### Option B: Using Shell Scripts (Manual Testing)

```bash
cd src/cad_coder_backend

# Make sure backend is running on localhost:8000
# Then run test scripts:

# Test 1: Basic text generation (LLaVA)
./test_basic.sh

# Test 2: Image + text generation (Qwen)
./test.sh
```

#### Option C: UI Integration Testing

```bash
# Terminal 1: Start backend
cd src/cad_coder_backend
source ../../env/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start frontend
cd src/ui
npm run dev

# Open browser: http://localhost:3000
# Test the UI manually:
# 1. Enter a prompt
# 2. Upload an image (optional)
# 3. Select a model
# 4. Generate CAD code
# 5. Verify response appears correctly
```

## CI/CD E2E Testing

### GitHub Actions Setup

The CI workflow (`ci.yml`) handles E2E tests automatically:

1. **Without Credentials** (Default):
   - Uses mocked backends
   - No secrets needed
   - Tests still verify integration flow

2. **With Credentials** (Optional):
   - Add secrets to GitHub repository:
     - `MODAL_TOKEN_ID`
     - `MODAL_TOKEN_SECRET`
     - `QWEN_MODAL_APP` (optional)
     - `QWEN_MODAL_FUNCTION` (optional)
     - `LLAVA_MODAL_APP` (optional)
     - `LLAVA_MODAL_FUNCTION` (optional)
   - CI will create `.env.test` dynamically
   - Tests run with real Modal inference

### Adding GitHub Secrets

1. Go to: `Settings → Secrets and variables → Actions`
2. Click "New repository secret"
3. Add each secret:
   - `MODAL_TOKEN_ID`: Your Modal token ID
   - `MODAL_TOKEN_SECRET`: Your Modal token secret
   - (Optional) Other Modal config secrets

## Test Scripts Explained

### `test_basic.sh`
- Tests LLaVA model with text-only prompt
- No image required
- Verifies basic CAD generation

### `test.sh`
- Tests Qwen model with image + text
- Requires image file: `../model_inference/qwen/15.png`
- Verifies multimodal CAD generation

## Environment Variables Reference

### Required for Real E2E Testing

```bash
# Modal Labs (for real inference)
MODAL_TOKEN_ID=your_token_id
MODAL_TOKEN_SECRET=your_token_secret
QWEN_MODAL_APP=cad-coder-qwen3
QWEN_MODAL_FUNCTION=qwen_modal_infer
LLAVA_MODAL_APP=cad-coder-llava
LLAVA_MODAL_FUNCTION=llava_modal_infer

# MongoDB (test database)
MONGO_URI=mongodb://localhost:27017
MONGO_DB=test_cad_coder

# Optional: GCS (for upload testing)
GOOGLE_APPLICATION_CREDENTIALS=path/to/test-service-account.json
GCS_BUCKET=test-cad-coder-bucket

# Optional: RAG (for retrieval testing)
ENABLE_RAG=false  # Set to true if testing RAG
RAG_PROJECT_ID=your-project-id
RAG_LOCATION=us-central1
```

### Test-Specific Settings

```bash
# Reduced tokens for faster tests
QWEN_MODAL_MAX_NEW_TOKENS=128
LLAVA_MODAL_MAX_NEW_TOKENS=128
QWEN_MODAL_TEMPERATURE=0.0
LLAVA_MODAL_TEMPERATURE=0.0
```

## Troubleshooting

### Issue: `.env.test` not found
**Solution**: The file is optional. If missing, tests use mocked backends. Create it from `.env.test.example` if you want real E2E testing.

### Issue: Modal authentication fails
**Solution**: 
- Check `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` are correct
- Verify tokens haven't expired
- Ensure Modal apps are deployed

### Issue: MongoDB connection fails
**Solution**:
- Ensure MongoDB is running: `docker compose -f docker-compose.test.yml up -d mongo-test`
- Check `MONGO_URI` points to correct host/port
- Verify database name doesn't conflict

### Issue: Tests timeout
**Solution**:
- Reduce `*_MODAL_MAX_NEW_TOKENS` in `.env.test`
- Use mocked backends for faster iteration
- Check network connectivity to Modal Labs

## Best Practices

1. **Separate Test Credentials**: Never use production credentials for testing
2. **Isolated Test Database**: Use separate MongoDB database for tests
3. **Mocked by Default**: Use mocked backends for fast iteration, real services for final verification
4. **CI/CD Safety**: CI uses mocked backends unless secrets are explicitly provided
5. **Local Development**: Use `.env` for development, `.env.test` for E2E testing

## Next Steps

- [ ] Create `src/.env.test` from template
- [ ] Run `test_basic.sh` to verify setup
- [ ] Run `test.sh` to test image generation
- [ ] Test UI integration manually
- [ ] (Optional) Add GitHub Secrets for CI E2E testing
