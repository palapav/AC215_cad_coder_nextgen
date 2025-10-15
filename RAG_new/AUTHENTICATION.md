# Authentication & Dependency Management Guide

## Current Setup

You are using **service account authentication** with a key file.

---

## Dependency Management (pyproject.toml + uv)

### How Docker Uses pyproject.toml

The Dockerfile is configured to use **uv** (a fast Python package manager) with `pyproject.toml`:

```dockerfile
# 1. Install uv in the container
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Copy pyproject.toml and source files
COPY pyproject.toml .
COPY *.py .

# 3. Install project dependencies from pyproject.toml
RUN uv pip install --system .
```

### What Happens During Build

1. **uv reads `pyproject.toml`** to find dependencies:
   ```toml
   dependencies = [
       "google-cloud-aiplatform[rag]",
       "python-dotenv",
       "Pillow",
   ]
   ```

2. **Installs packages** into the system Python (no virtual env needed in container)

3. **Benefits of uv**:
   - 10-100x faster than pip
   - Better dependency resolution
   - Reads modern `pyproject.toml` format
   - Better caching

### Local Development

For local development, you can use either:

**Option 1: uv (recommended)**
```bash
pip install uv
uv pip install .
```

**Option 2: Traditional pip**
```bash
pip install -r requirements.txt
```

Both `pyproject.toml` and `requirements.txt` are maintained for compatibility.

---

## How It Works

### 1. Local Environment (Your Terminal)

```bash
# You have already set this
export GOOGLE_APPLICATION_CREDENTIALS="key.json"

# This tells GCP libraries to use key.json for authentication
```

### 2. Docker Environment

The `docker-compose.yml` automatically handles authentication:

```yaml
volumes:
  # Mounts your local key.json into the container
  - ./key.json:/app/key.json:ro

environment:
  # Tells container to use the mounted key file
  - GOOGLE_APPLICATION_CREDENTIALS=/app/key.json
```

## Required Files

```
RAG_new/
├── key.json          # Service account key (REQUIRED)
├── .env              # Project configuration
└── docker-compose.yml
```

## Service Account Permissions

Your service account in `key.json` needs:

| Permission | Purpose |
|------------|---------|
| `roles/aiplatform.user` | Query vector database, generate embeddings |
| `roles/storage.objectViewer` | Read GCS bucket data |

## Verification

### Check Authentication

```bash
# In your terminal
echo $GOOGLE_APPLICATION_CREDENTIALS
# Output: key.json

# Verify file exists
ls -lh key.json
# Output: -rw-r--r-- 1 user group 2.3K Oct 15 16:00 key.json
```

### Test in Docker

```bash
docker-compose run --rm rag-pipeline python -c "
from google.cloud import aiplatform
from config import load_config
config = load_config()
aiplatform.init(project=config['project_id'], location=config['location'])
print('✅ Authentication successful')
"
```

Expected output:
```
✅ Authentication successful
```

## Troubleshooting

### Error: "DefaultCredentialsError"

**Cause**: `key.json` not found or not mounted

**Fix**:
```bash
# Check file exists
ls -lh RAG_new/key.json

# Rebuild and verify
cd RAG_new
docker-compose build
docker-compose run --rm rag-pipeline ls -lh /app/key.json
```

### Error: "Permission denied"

**Cause**: Service account lacks required permissions

**Fix**:
```bash
# Grant permissions (replace PROJECT_ID and SERVICE_ACCOUNT_EMAIL)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.objectViewer"
```

### Error: "Invalid key format"

**Cause**: Corrupted or incomplete `key.json`

**Fix**:
```bash
# Re-download from GCP Console:
# IAM & Admin → Service Accounts → Create Key → JSON
```

## Security Best Practices

1. ✅ **DO**: Store `key.json` securely
2. ✅ **DO**: Add `key.json` to `.gitignore`
3. ✅ **DO**: Use least-privilege permissions
4. ❌ **DON'T**: Commit `key.json` to git
5. ❌ **DON'T**: Share `key.json` publicly

## Production Recommendations

For production deployments, consider:

1. **Workload Identity** (GKE/Cloud Run)
   - No key files needed
   - Automatic credential rotation
   - Better security

2. **Secret Manager**
   - Store keys securely
   - Audit access
   - Automatic rotation

3. **Service Accounts per Environment**
   - Separate keys for dev/staging/prod
   - Principle of least privilege

