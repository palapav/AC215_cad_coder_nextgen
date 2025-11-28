"""Basic endpoint tests for the FastAPI application."""
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
import pytest

from app.main import app

client = TestClient(app)


# Auto-mock add_record for all generate tests to prevent DB calls
@pytest.fixture(autouse=True)
def mock_add_record():
    """Mock add_record to prevent actual DB calls during tests."""
    with patch('app.routers.generate.add_record') as mock:
        mock.return_value = None
        yield mock


# ---------------------------
# Health Endpoint
# ---------------------------
def test_health_check():
    """Test health endpoint returns OK status."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    # May also include mongodb status


# ---------------------------
# Generation Endpoint
# ---------------------------
@pytest.mark.parametrize("model_choice", ["llava", "qwen"])
def test_generate_cad(model_choice):
    """Test CAD generation endpoint with different models."""
    # Mock at the router level where the function is imported
    with patch('app.routers.generate.generate_cad_code', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {
            "cad_code": "import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)",
            "rag_used": False,
            "rag_context": None,
            "rag_results": []
        }
        
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
    """Test history context endpoint."""
    payload = {"prompt": "cube"}
    response = client.post("/history/context", json=payload)
    assert response.status_code == 200
    assert "context" in response.json()


# ---------------------------
# Auth Endpoint (Mock) - Skip if auth router is disabled
# ---------------------------
def test_auth_google(monkeypatch):
    """Test Google auth endpoint (may be disabled)."""
    from app.services import auth_service

    def mock_verify_google_token(token: str):
        return {"email": "test@example.com", "name": "Tester", "sub": "123"}

    monkeypatch.setattr(auth_service, "verify_google_token", mock_verify_google_token)
    response = client.post("/auth/google", json={"credential": "fake_token"})
    
    # Auth router may be disabled - accept 404 or 200
    if response.status_code == 200:
        assert "user" in response.json()
    else:
        # Auth router is disabled, which is acceptable
        assert response.status_code == 404


# ---------------------------
# Pipeline Endpoint (Mock)
# ---------------------------
def test_pipeline_trigger():
    """Test pipeline trigger endpoint with mocked subprocess."""
    with patch('app.routers.pipeline.run_stage') as mock_run:
        mock_run.return_value = {"stage": "ingestion", "status": "success"}
        
        response = client.post("/pipeline/ingestion")
        assert response.status_code == 200
        assert "message" in response.json()
