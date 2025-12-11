# Locust Load Testing Container
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test files
COPY locustfile.py .

# Expose Locust web UI port
EXPOSE 8089

# Default command - run Locust web UI
CMD ["locust", "-f", "locustfile.py", "--web-host=0.0.0.0"]
