# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy pyproject.toml and poetry.lock (if available)
COPY pyproject.toml .
# Optionally copy poetry.lock if you use it
COPY poetry.lock .

# Install dependencies via Poetry
RUN poetry install --no-interaction --no-ansi

# Copy the scripts for model inference
COPY ./scripts /app/scripts

# Set the default command to run the inference script (this can be overridden in docker-compose)
CMD ["bash"]