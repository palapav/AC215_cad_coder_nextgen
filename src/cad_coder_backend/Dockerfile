# ---------- Base Image ----------
# Using Python slim image - no PyTorch/CUDA needed since model inference runs on Modal/GKE
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# ---------- Working Directory ----------
WORKDIR /app

# ---------- Install uv (modern resolver/installer) ----------
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir uv

# ---------- Copy lockfiles first for better caching ----------
COPY pyproject.toml uv.lock* ./

# Install dependencies (prefers uv.lock; falls back to resolve if lock missing)
RUN uv sync --no-dev --no-editable --compile-bytecode

# ---------- Copy Project Source ----------
COPY . .

# Expose FastAPI port
EXPOSE 8000

# ---------- Run App ----------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]