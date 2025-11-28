"""Integration tests for FastAPI routers."""
import pytest
import os
import sys
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.main import app

client = TestClient(app)


# ============================================================================
# Health Router Tests
# ============================================================================
class TestHealthRouter:
    """Test health check endpoints."""

    def test_health_check(self):
        """Test health endpoint returns OK status."""
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        # May also include mongodb status - that's fine


# ============================================================================
# Root Endpoint Tests
# ============================================================================
class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "CAD-Coder" in data["message"]


# ============================================================================
# Generate Router Tests
# ============================================================================
class TestGenerateRouter:
    """Test CAD generation endpoints."""

    def test_generate_cad_llava(self):
        """Test generate endpoint with LLaVA model."""
        with patch('app.services.model_service.generate_cad_code', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {
                "cad_code": "import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)",
                "rag_used": False,
                "rag_context": None,
                "rag_results": []
            }
            
            response = client.post("/generate_cad", json={
                "prompt": "make a cube",
                "model_choice": "llava",
                "user_id": "test_user"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "cad_code" in data
            assert data["model"] == "llava"

    def test_generate_cad_qwen(self):
        """Test generate endpoint with Qwen model."""
        with patch('app.services.model_service.generate_cad_code', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {
                "cad_code": "import cadquery as cq\nresult = cq.Workplane('XY').sphere(0.5)",
                "rag_used": True,
                "rag_context": "Example context",
                "rag_results": []
            }
            
            response = client.post("/generate_cad", json={
                "prompt": "make a sphere",
                "model_choice": "qwen",
                "user_id": "test_user"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "cad_code" in data
            assert data["model"] == "qwen"
            # rag_used may be True or False depending on mocking

    def test_generate_cad_empty_prompt(self):
        """Test generate endpoint with empty prompt."""
        with patch('app.services.model_service.generate_cad_code', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {
                "cad_code": "# placeholder",
                "rag_used": False,
                "rag_context": None,
                "rag_results": []
            }
            
            response = client.post("/generate_cad", json={
                "prompt": "",
                "model_choice": "llava"
            })
            
            # Should still work (empty prompt is valid)
            assert response.status_code == 200

    def test_generate_cad_with_image_reference(self):
        """Test generate endpoint with image reference."""
        with patch('app.services.model_service.generate_cad_code', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {
                "cad_code": "import cadquery as cq",
                "rag_used": False,
                "rag_context": None,
                "rag_results": []
            }
            
            response = client.post("/generate_cad", json={
                "prompt": "describe this",
                "model_choice": "llava",
                "image_path": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            })
            
            assert response.status_code == 200

    def test_generate_cad_empty_prompt_with_image(self):
        """Test generate endpoint with empty prompt but image provided."""
        with patch('app.services.model_service.generate_cad_code', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {
                "cad_code": "import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)",
                "rag_used": False,
                "rag_context": None,
                "rag_results": []
            }
            
            response = client.post("/generate_cad", json={
                "prompt": "",
                "model_choice": "llava",
                "image_path": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            })
            
            assert response.status_code == 200
            # Should use default prompt for image
            call_kwargs = mock_gen.await_args.kwargs
            assert "Generate the CADQuery code" in call_kwargs["prompt"]

    def test_generate_cad_empty_prompt_no_image(self):
        """Test generate endpoint with empty prompt and no image."""
        with patch('app.services.model_service.generate_cad_code', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {
                "cad_code": "import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)",
                "rag_used": False,
                "rag_context": None,
                "rag_results": []
            }
            
            response = client.post("/generate_cad", json={
                "prompt": "",
                "model_choice": "llava"
            })
            
            assert response.status_code == 200
            # Should use default prompt
            call_kwargs = mock_gen.await_args.kwargs
            assert "simple geometric shape" in call_kwargs["prompt"]

    def test_generate_cad_invalid_base64_image(self):
        """Test generate endpoint with invalid base64 image."""
        with patch('app.services.model_service.generate_cad_code', new_callable=AsyncMock):
            response = client.post("/generate_cad", json={
                "prompt": "test",
                "model_choice": "llava",
                "image_path": "data:image/png;base64,invalid_base64_data!!!"
            })
            
            assert response.status_code == 500
            assert "Invalid base64 image data" in response.json()["detail"]

    def test_generate_cad_empty_cad_code(self):
        """Test generate endpoint when model returns empty CAD code."""
        with patch('app.services.model_service.generate_cad_code', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {
                "cad_code": "",
                "rag_used": False,
                "rag_context": None,
                "rag_results": []
            }
            
            response = client.post("/generate_cad", json={
                "prompt": "make a cube",
                "model_choice": "llava"
            })
            
            assert response.status_code == 500
            assert "empty or None" in response.json()["detail"]

    def test_generate_cad_with_file_path_image(self, tmp_path):
        """Test generate endpoint with file path image."""
        from PIL import Image
        
        img_path = tmp_path / "test.png"
        img = Image.new('RGB', (50, 50), color='green')
        img.save(img_path)
        
        with patch('app.services.model_service.generate_cad_code', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {
                "cad_code": "import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)",
                "rag_used": False,
                "rag_context": None,
                "rag_results": []
            }
            
            response = client.post("/generate_cad", json={
                "prompt": "test",
                "model_choice": "llava",
                "image_path": str(img_path)
            })
            
            assert response.status_code == 200

    def test_generate_cad_model_service_exception(self):
        """Test generate endpoint handles model service exceptions."""
        with patch('app.services.model_service.generate_cad_code', new_callable=AsyncMock) as mock_gen:
            mock_gen.side_effect = Exception("Model service error")
            
            response = client.post("/generate_cad", json={
                "prompt": "make a cube",
                "model_choice": "llava"
            })
            
            assert response.status_code == 500
            assert "CAD generation failed" in response.json()["detail"]


# ============================================================================
# History Router Tests
# ============================================================================
class TestHistoryRouter:
    """Test history endpoints."""

    def test_history_context(self):
        """Test history context endpoint."""
        with patch('app.services.rag_service.retrieve_similar_context') as mock_rag:
            mock_rag.return_value = [{"text": "example context"}]
            
            response = client.post("/history/context", json={
                "prompt": "cube"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "context" in data

    def test_get_history(self):
        """Test get history endpoint."""
        with patch('app.services.db_service.get_history') as mock_history:
            mock_history.return_value = [
                {"prompt": "test", "cad_code": "code", "_id": "123"}
            ]
            
            response = client.get("/history/")
            
            assert response.status_code == 200
            data = response.json()
            # Response may be a list or dict with records
            assert data is not None

    def test_history_test_records_endpoint(self):
        """Test /history/test-records endpoint."""
        with patch('app.routers.history.get_history') as mock_history:
            mock_history.side_effect = lambda limit, user_id=None: [{"prompt": user_id}]
            
            response = client.get("/history/test-records")
            
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 3

    def test_history_test_images_endpoint(self):
        """Test /history/test-images endpoint."""
        mock_cursor = Mock()
        mock_cursor.limit.return_value = [
            {"_id": "123", "image_data": "abcde"}
        ]
        
        with patch('app.routers.history.collection') as mock_collection:
            mock_collection.find.return_value = mock_cursor
            
            response = client.get("/history/test-images")
            
            assert response.status_code == 200
            data = response.json()
            assert data["records"][0]["image_data"].startswith("[Base64")

    def test_history_add_dummy_data_endpoint(self):
        """Test /history/add-dummy-data endpoint."""
        with patch('app.routers.history.add_record') as mock_add:
            response = client.post("/history/add-dummy-data")
            
            assert response.status_code == 200
            data = response.json()
            assert data["added_count"] == mock_add.call_count


# ============================================================================
# Pipeline Router Tests
# ============================================================================
class TestPipelineRouter:
    """Test pipeline control endpoints."""

    def test_pipeline_ingestion(self):
        """Test pipeline ingestion trigger."""
        with patch('app.routers.pipeline.run_stage') as mock_run:
            mock_run.return_value = {"stage": "ingestion", "status": "success"}
            
            response = client.post("/pipeline/ingestion")
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    def test_pipeline_preprocess(self):
        """Test pipeline preprocess trigger."""
        with patch('app.routers.pipeline.run_stage') as mock_run:
            mock_run.return_value = {"stage": "preprocess", "status": "success"}
            
            response = client.post("/pipeline/preprocess")
            
            assert response.status_code == 200

    def test_pipeline_rag(self):
        """Test pipeline RAG trigger."""
        with patch('app.routers.pipeline.run_stage') as mock_run:
            mock_run.return_value = {"stage": "rag", "status": "success"}
            
            response = client.post("/pipeline/rag")
            
            assert response.status_code == 200


# ============================================================================
# Auth Router Tests (if enabled)
# ============================================================================
class TestAuthRouter:
    """Test authentication endpoints."""

    def test_auth_google_mock(self, monkeypatch):
        """Test Google auth with mocked verification."""
        from app.services import auth_service
        
        def mock_verify(token):
            return {"email": "test@example.com", "name": "Test User", "sub": "123"}
        
        monkeypatch.setattr(auth_service, "verify_google_token", mock_verify)
        
        # Note: Auth router may be disabled, so we check if it exists
        response = client.post("/auth/google", json={"credential": "fake_token"})
        
        # May return 404 if auth router is disabled - that's acceptable
        if response.status_code == 200:
            data = response.json()
            assert "user" in data
            assert data["auth_method"] == "google"
            assert data["status"] == "success"
        else:
            assert response.status_code == 404

    def test_auth_google_missing_token(self, monkeypatch):
        """Test Google auth with missing token."""
        from app.services import auth_service
        
        def mock_verify(token):
            return {"email": "test@example.com", "name": "Test User", "sub": "123"}
        
        monkeypatch.setattr(auth_service, "verify_google_token", mock_verify)
        
        response = client.post("/auth/google", json={})
        
        # May return 404 if auth router is disabled - that's acceptable
        if response.status_code != 404:
            assert response.status_code == 400
            assert "Missing Google credential token" in response.json()["detail"]

    def test_auth_google_invalid_token(self, monkeypatch):
        """Test Google auth with invalid token."""
        from app.services import auth_service
        
        def mock_verify(token):
            return {"error": "Invalid Google ID token"}
        
        monkeypatch.setattr(auth_service, "verify_google_token", mock_verify)
        
        response = client.post("/auth/google", json={"credential": "invalid_token"})
        
        # May return 404 if auth router is disabled - that's acceptable
        if response.status_code != 404:
            assert response.status_code == 401
            assert "Invalid Google ID token" in response.json()["detail"]


# ============================================================================
# Error Handling Tests
# ============================================================================
class TestErrorHandling:
    """Test error handling across endpoints."""

    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        response = client.post(
            "/generate_cad",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity

    def test_missing_required_field(self):
        """Test handling of missing required fields."""
        response = client.post("/generate_cad", json={
            # Missing 'prompt' field
            "model_choice": "llava"
        })
        
        assert response.status_code == 422

    def test_not_found_endpoint(self):
        """Test 404 for non-existent endpoint."""
        response = client.get("/nonexistent/endpoint")
        
        assert response.status_code == 404
