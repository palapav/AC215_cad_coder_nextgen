FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

# Google Cloud credentials
COPY secrets/data-service-account.json /app/secrets/data-service-account.json
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/secrets/data-service-account.json"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
