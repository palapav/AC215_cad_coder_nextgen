# Dockerfile for Data Versioning with DVC
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    dvc \
    Pillow

# Copy scripts
COPY scripts/ /app/scripts/
COPY setup_dvc.sh /app/
COPY create_all_versions.sh /app/
COPY .dvcignore /app/

# Make scripts executable
RUN chmod +x /app/scripts/*.py /app/*.sh

# Default command (can be overridden)
CMD ["/bin/bash"]

