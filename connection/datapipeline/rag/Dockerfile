FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv using pip (simpler and more reliable in Docker)
RUN pip install --no-cache-dir uv

# Copy pyproject.toml
COPY pyproject.toml .

# Install dependencies from pyproject.toml using uv
# Note: We install dependencies directly, matching pyproject.toml
RUN uv pip install --system \
    "google-cloud-aiplatform[rag]>=1.38.0" \
    "python-dotenv>=1.0.0" \
    "Pillow>=10.0.0"

# Copy remaining files (config, keys, etc.)
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["python", "test_rag.py"]

