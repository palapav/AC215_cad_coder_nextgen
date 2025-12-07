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

# ---------- Install pip (no uv) ----------
RUN pip install --no-cache-dir --upgrade pip

# ---------- Copy requirements for caching ----------
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Copy Project Source ----------
COPY . .

# Expose FastAPI port
EXPOSE 8000

# ---------- Run App ----------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]