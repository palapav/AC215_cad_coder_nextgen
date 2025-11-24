# Use the official Python image as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the pyproject.toml file into the container
COPY pyproject.toml .

# Install the dependencies

# Copy the rest of the application code
COPY . .

RUN dvc add ../processed_test && \
    git init && \
    git add . && \
    git commit -m "Add dataset to DVC tracking"

# Optionally, configure your DVC remote storage
# Example for AWS S3
# RUN dvc remote add -d myremote s3://my-bucket/path/to/data

# Pull the latest version of the dataset from DVC before running inference
RUN dvc pull
# Command to run your model inference script
# CMD ["python", "model_inference.py"]