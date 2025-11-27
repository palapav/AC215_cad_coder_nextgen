# Use Python base image instead of conda for faster, more reliable builds
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget \
        bzip2 \
        ca-certificates \
        curl \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy pyproject.toml first for better caching
COPY pyproject.toml ./

# Install PyTorch CPU-only version first (much smaller and faster)
RUN pip install --no-cache-dir \
    torch==2.1.2 torchvision==0.16.2 \
    --index-url https://download.pytorch.org/whl/cpu

# Install core dependencies from pyproject.toml (without train extras for faster build)
# We'll install train extras only if needed at runtime
RUN pip install --no-cache-dir \
    transformers==4.37.2 \
    tokenizers==0.15.1 \
    sentencepiece==0.1.99 \
    shortuuid \
    accelerate==0.21.0 \
    peft \
    bitsandbytes \
    pydantic \
    "markdown2[all]" \
    numpy \
    scikit-learn==1.2.2 \
    gradio==4.16.0 \
    gradio_client==0.8.1 \
    requests \
    httpx==0.24.0 \
    uvicorn \
    fastapi \
    einops==0.6.1 \
    einops-exts==0.0.4 \
    timm==0.6.13

# Copy the rest of the application
COPY . .

# Install the package in editable mode (without train extras to speed up build)
# Train extras (deepspeed, wandb) can be installed at runtime if needed
RUN pip install --no-cache-dir -e .


# Execute your custom script (ensure the script exists in the copied contents)
# Ensure you provide the required arguments correctly
# Note: Updated to use python directly instead of conda
CMD ["/bin/bash", "./scripts/v1_5/eval/test_gencadcode.sh", "CADCODER/CAD-Coder", "dataset", "python", "scripts/generate_model_cad.py", "--dataset_name", "dateset", "--model_tested", "CADCODER/CAD-Coder", "--code_language", "cadquery", "--pc_reps", "3", "--parallel"]