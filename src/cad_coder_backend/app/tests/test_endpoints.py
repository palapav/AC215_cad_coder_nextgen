"""Basic endpoint tests for the FastAPI application."""
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock, MagicMock
import pytest
import importlib
import io
import base64
from PIL import Image

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


# ---------------------------
# Service coverage tests (run in integration job)
# ---------------------------
class TestServiceIntegrations:
    """Exercise key service modules to boost integration coverage."""

    def test_auth_service_success(self, monkeypatch):
        """Auth service returns user info on success."""
        from app.services import auth_service

        def mock_verify(token, request):
            return {"email": "user@example.com", "name": "Test User", "sub": "abc123"}

        monkeypatch.setattr(auth_service.id_token, "verify_oauth2_token", mock_verify)
        result = auth_service.verify_google_token("valid-token")
        assert result["email"] == "user@example.com"
        assert result["name"] == "Test User"

    def test_auth_service_invalid_token(self, monkeypatch):
        """Auth service returns error when Google token invalid."""
        from app.services import auth_service

        def mock_verify(token, request):
            raise ValueError("bad token")

        monkeypatch.setattr(auth_service.id_token, "verify_oauth2_token", mock_verify)
        result = auth_service.verify_google_token("invalid")
        assert result["error"] == "Invalid Google ID token"

    def test_auth_service_generic_error(self, monkeypatch):
        """Auth service returns generic error on unexpected exception."""
        from app.services import auth_service

        def mock_verify(token, request):
            raise RuntimeError("network down")

        monkeypatch.setattr(auth_service.id_token, "verify_oauth2_token", mock_verify)
        result = auth_service.verify_google_token("error")
        assert "network down" in result["error"]

    def test_gcs_upload_without_credentials(self, monkeypatch):
        """GCS upload should fall back to local path when creds missing."""
        from app.services import gcs_service

        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        result = gcs_service.upload_cad_code("test cube", "cad code")
        assert result.startswith("local://test_cube")

    def test_gcs_upload_with_credentials(self, tmp_path, monkeypatch):
        """GCS upload uses bucket when credentials provided."""
        from app.services import gcs_service

        creds = tmp_path / "creds.json"
        creds.write_text("{}")
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(creds))
        monkeypatch.setenv("GCS_BUCKET", "integration-bucket")

        fake_blob = MagicMock()
        fake_bucket = MagicMock()
        fake_bucket.blob.return_value = fake_blob
        fake_client = MagicMock()
        fake_client.bucket.return_value = fake_bucket
        monkeypatch.setattr(gcs_service.storage, "Client", lambda: fake_client)

        result = gcs_service.upload_cad_code("integration cube", "cad code")
        assert result == f"gs://{gcs_service.BUCKET_NAME}/generated/integration_cube.py"
        fake_bucket.blob.assert_called_once()
        fake_blob.upload_from_filename.assert_called_once()

    def test_logger_writes_file(self, tmp_path, monkeypatch):
        """Logger module writes to configured file."""
        from app.services import logger as logger_module

        log_path = tmp_path / "integration.log"
        monkeypatch.setenv("LOG_PATH", str(log_path))
        importlib.reload(logger_module)

        logger_instance = logger_module.get_logger("integration_test_logger")
        logger_instance.info("integration run")
        for handler in logger_instance.handlers:
            handler.flush()

        assert log_path.exists()
        assert "integration run" in log_path.read_text()

    def test_modal_client_serialize_image(self):
        """Modal client serializes base64 image."""
        from app.services import modal_client

        img = Image.new("RGB", (32, 32), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        data_url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

        data, mime = modal_client._serialize_image(data_url)
        assert data is not None
        assert mime.lower().replace("/", "") == "png"

    def test_modal_client_serialize_path(self, tmp_path):
        """Modal client serializes file path image."""
        from app.services import modal_client

        img_path = tmp_path / "img.png"
        img = Image.new("RGB", (16, 16), color="blue")
        img.save(img_path)

        data, mime = modal_client._serialize_image(str(img_path))
        assert data is not None
        assert mime.lower().replace("/", "") == "png"

    def test_model_service_generate_qwen(self, monkeypatch):
        """Model service returns CAD dict for Qwen with RAG context."""
        from app.services import model_service

        async def mock_run_qwen(prompt, image=None):
            return "# cad code qwen"

        def mock_retrieve_context(**kwargs):
            return {"context": "ctx", "results": [{"id": 1}], "used": True}

        monkeypatch.setattr(model_service, "_run_qwen_inference", mock_run_qwen)
        monkeypatch.setattr(model_service.rag_service, "retrieve_context", mock_retrieve_context)

        result = asyncio.get_event_loop().run_until_complete(
            model_service.generate_cad_code(prompt="p", model_choice="qwen")
        )
        assert result["cad_code"].startswith("# cad code")
        assert result["rag_used"] is True
        assert result["rag_context"] == "ctx"

    def test_model_service_generate_llava(self, monkeypatch):
        """Model service returns CAD dict for LLaVA."""
        from app.services import model_service

        async def mock_run_llava(prompt, image=None):
            return "# cad code llava"

        monkeypatch.setattr(model_service, "_run_llava_inference", mock_run_llava)

        result = asyncio.get_event_loop().run_until_complete(
            model_service.generate_cad_code(prompt="p", model_choice="llava")
        )
        assert result["cad_code"].startswith("# cad code")
        assert result["rag_used"] is False

    def test_model_service_invalid_choice_defaults_llava(self, monkeypatch):
        """Invalid model choice should fall back to LLaVA path."""
        from app.services import model_service

        async def mock_run_llava(prompt, image=None):
            return "# cad code llava"

        monkeypatch.setattr(model_service, "_run_llava_inference", mock_run_llava)

        result = asyncio.get_event_loop().run_until_complete(
            model_service.generate_cad_code(prompt="p", model_choice="invalid")
        )
        assert "cad_code" in result

    def test_rag_service_retrieve_context_basic(self, monkeypatch):
        """RAG service should handle disabled flag gracefully."""
        from app.services import rag_service

        monkeypatch.setenv("ENABLE_RAG", "false")
        import importlib
        importlib.reload(rag_service)

        res = rag_service.retrieve_context(prompt="p")
        assert res["used"] is False
        assert res["context"] == ""

    def test_gke_client_serialize_image_none(self):
        """GKE client serialize_image handles None."""
        from app.services import gke_client

        data, fmt = gke_client._serialize_image(None)
        assert data is None
        assert fmt is None

    def test_modal_client_load_pil_image(self):
        """Modal client load_pil_image handles PIL input."""
        from app.services import modal_client

        img = Image.new("RGB", (10, 10), color="red")
        loaded = modal_client._load_pil_image(img)
        assert loaded.mode == "RGB"

    def test_modal_client_preprocess_llava_none(self):
        """Modal client preprocess for LLaVA with None image."""
        from app.services import modal_client

        data, fmt = modal_client._preprocess_image_for_llava(None, target_size=64)
        assert data is not None
        assert fmt == "PNG"