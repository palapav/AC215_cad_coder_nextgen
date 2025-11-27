FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy pyproject.toml
COPY pyproject.toml .

# Copy Python source files (use . to copy all files, or be more specific)
COPY . .

# Install dependencies from pyproject.toml using uv
RUN export UV_HTTP_TIMEOUT=300
ENV UV_HTTP_TIMEOUT=300

RUN uv pip install --system "torch" --extra-index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --system "torchvision>=0.15.0" --extra-index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --system "Pillow>=10.0.0"
RUN uv pip install --system "google-cloud-storage>=2.10.0"
RUN uv pip install --system "tqdm"

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "preprocess_cv.py", "--bucket", "cad-coder-nextgen-data", "--splits", "test"]
