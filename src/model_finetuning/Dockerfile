# Dockerfile for model_finetuning testing (CPU-only)
# Used for CI/CD automated testing without GPU requirements

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements-cpu.txt .

# Install CPU-only PyTorch and dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements-cpu.txt

# Copy source code
COPY . .

# Set Python path
ENV PYTHONPATH=/app:/app/CADRL

# Default command: run tests
CMD ["pytest", "tests/", "-v", "--cov=.", "--cov-report=term-missing"]

