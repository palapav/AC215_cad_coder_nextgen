from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

# ---------------------------
# Health Endpoint
# ---------------------------
def test_health_check():
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# ---------------------------
# Generation Endpoint
# ---------------------------
@pytest.mark.parametrize("model_choice", ["llava", "qwen"])
def test_generate_cad(model_choice):
    payload = {
        "prompt": "generate a cube",
        "model_choice": model_choice,
        "user_id": "test_user"
    }
    response = client.post("/generate_cad", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "cad_code" in data
    assert data["model"] == model_choice

# ---------------------------
# History / RAG Context
# ---------------------------
def test_history_context():
    payload = {"prompt": "cube"}
    response = client.post("/history/context", json=payload)
    assert response.status_code == 200
    assert "context" in response.json()

# ---------------------------
# Auth Endpoint (Mock)
# ---------------------------
def test_auth_google(monkeypatch):
    # mock the verification function
    from app.services import auth_service

    def mock_verify_google_token(token: str):
        return {"email": "test@example.com", "name": "Tester", "sub": "123"}

    monkeypatch.setattr(auth_service, "verify_google_token", mock_verify_google_token)
    response = client.post("/auth/google", json={"credential": "fake_token"})
    assert response.status_code == 200
    assert "user" in response.json()

# ---------------------------
# Pipeline Endpoint (Mock)
# ---------------------------
def test_pipeline_trigger(monkeypatch):
    from app.services import pipeline_service

    def mock_run_stage(stage: str):
        return {"stage": stage, "status": "success"}

    monkeypatch.setattr(pipeline_service, "run_stage", mock_run_stage)

    response = client.post("/pipeline/ingestion")
    assert response.status_code == 200
    assert "message" in response.json()
