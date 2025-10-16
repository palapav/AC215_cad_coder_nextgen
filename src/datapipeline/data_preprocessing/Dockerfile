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

# Copy Python source files
COPY *.py .

# Install dependencies from pyproject.toml using uv
RUN uv pip install --system \
    "torch>=2.0.0" \
    "torchvision>=0.15.0" \
    "Pillow>=10.0.0" \
    "google-cloud-storage>=2.10.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "preprocess_cv.py", "--bucket", "cad-coder-nextgen-data", "--splits", "test"]
