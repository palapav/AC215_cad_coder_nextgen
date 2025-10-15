FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user named app and set the working directory
RUN useradd -m app
WORKDIR /app

# Install the necessary Python packages using pip
# Create a virtual environment and install packages
RUN python -m venv .venv
RUN ./.venv/bin/pip install --upgrade pip
RUN pip install pandas
# Copy uv from its official image
RUN pip install uv
RUN pip install --no-cache-dir poetry
RUN pip install scikit-learn
RUN pip install Pillow
RUN pip install torch
RUN pip install transformers
RUN pip install torchvision
RUN pip install datasets

# Copy only the necessary files (for caching purposes)
COPY pyproject.toml ./

# Install dependencies (for the first build)
RUN poetry install --no-root

COPY . ./ 

# Use a cache mount for faster rebuilds
RUN uv sync
# Set the user to the non-root user
USER app


# Use cmd to activate the virtual environment and start a new bash session
# Set the command to run your application scripts directly
CMD ["bash", "-c", "source .venv/bin/activate && python dataloader.py && python preprocess_cv.py"]  # Modify to your entry script