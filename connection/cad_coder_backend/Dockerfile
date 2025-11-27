# ---------- Base Image ----------
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# ---------- Working Directory ----------
WORKDIR /app

# ---------- System Dependencies ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libjpeg-dev \
    zlib1g-dev \
    ca-certificates \
    openssh-client \
 && rm -rf /var/lib/apt/lists/*

# ---------- Copy Project ----------
COPY . .

# ---------- Install Dependencies ----------
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu
ENV PIP_DEFAULT_TIMEOUT=300

# Install PyTorch CPU first (large package, install separately for better caching)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Environment ----------
#COPY secrets/data-service-account.json /app/secrets/data-service-account.json
#ENV GOOGLE_APPLICATION_CREDENTIALS="/app/secrets/data-service-account.json"

# Expose FastAPI port
EXPOSE 8000

# ---------- Run App ----------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    