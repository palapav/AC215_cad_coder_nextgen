# ---------- Base Image ----------
    FROM python:3.11-slim

    # ---------- Working Directory ----------
    WORKDIR /app
    
    # ---------- Copy Project ----------
    COPY . .
    
    # ---------- Install Dependencies ----------
    RUN pip install --no-cache-dir -r requirements.txt
    
    # ---------- Environment ----------
    # Load Google Cloud credentials
    #COPY secrets/data-service-account.json /app/secrets/data-service-account.json
    #ENV GOOGLE_APPLICATION_CREDENTIALS="/app/secrets/data-service-account.json"
    
    # Expose FastAPI port
    EXPOSE 8000
    
    # ---------- Run App ----------
    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    