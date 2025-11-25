# ---------- Base Image ----------
# Using Python slim image - no PyTorch/CUDA needed since model inference runs on Modal
FROM python:3.11-slim

# Install system dependencies
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