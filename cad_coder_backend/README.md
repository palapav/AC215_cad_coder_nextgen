**Overall Structure:**

cad_coder_backend/
├── app/
│   ├── __init__.py
│   ├── main.py  #Entry point of the FastAPI app
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── generate.py   #takes input(prompt/image) and returns generated CAD code
│   │   ├── history.py    #retrieves or stores previous CAD generations from MongoDB
│   │   └── health.py     #simple “status check” for CI/CD and Docker health probes
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── model_service.py  #Core ML logic: loads and runs the CAD-Coder model
│   │   ├── db_service.py     #Connects to MongoDB: inserts chat history
│   │   ├── gcs_service.py    #Upload/download CAD code/assets from GCS
│   │   └── utils.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── cad_input.py   #Defines incoming requests (prompt, image path, user_id)
│   │   └── cad_output.py  #Defines responses (generated code, GCS URI)
│   │
│   └── tests/
│       ├── __init__.py
│       └── test_endpoints.py  #Uses pytest + FastAPI’s TestClient to test routes like /generate_cad and /health
│
├── .env              # local environment variables
├── pyproject.toml
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
