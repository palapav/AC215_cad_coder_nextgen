FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy pyproject.toml
COPY pyproject.toml .

# Copy all files
COPY . .

# Install dependencies from pyproject.toml using uv
RUN uv pip install --system \
    "datasets>=2.19.0" \
    "google-cloud-storage>=2.10.0" \
    "Pillow>=10.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command - test with 5 samples (override in docker-compose)
CMD ["python", "dataloader.py", "--bucket", "cad-coder-nextgen-data", "--splits", "test", "--limit", "5"]
