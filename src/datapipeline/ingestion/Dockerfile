# -----------------------------
# Dockerfile for Data Ingestion
# -----------------------------
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies required for Pillow/datasets
RUN apt-get update && apt-get install -y git libgl1 && rm -rf /var/lib/apt/lists/*

# Copy local files into container
COPY dataloader.py .
COPY pyproject.toml .

# Install dependencies
RUN pip install --upgrade pip && pip install datasets pillow

# Default command: run ingestion script for test split
CMD ["python", "dataloader.py", "--output_dir", "./data/raw_test"]

