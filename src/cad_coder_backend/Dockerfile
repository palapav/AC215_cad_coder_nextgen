# ---------- Base Image with PyTorch and CUDA support ----------
# Using PyTorch 2.6.0 matching working environment
# Note: Using cu124 (CUDA 12.4) which is backward compatible with CUDA 12.3
# Original environment: torch 2.6.0+cu124, current machine: CUDA 12.3
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime

# Install system dependencies for image processing
RUN apt-get update && apt-get install -y \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# ---------- Working Directory ----------
WORKDIR /app

# ---------- Copy Project ----------
COPY . .

# ---------- Install Dependencies ----------
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Environment ----------
# Load Google Cloud credentials
#COPY secrets/data-service-account.json /app/secrets/data-service-account.json
#ENV GOOGLE_APPLICATION_CREDENTIALS="/app/secrets/data-service-account.json"

# Expose FastAPI port
EXPOSE 8000

# ---------- Run App ----------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]