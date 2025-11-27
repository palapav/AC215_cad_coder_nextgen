"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)


class TestAPIIntegration:
    """Integration tests for API endpoints"""

    def test_health_endpoint_integration(self):
        """Test health endpoint integration"""
        response = client.get("/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_root_endpoint_integration(self):
        """Test root endpoint integration"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    @patch('app.services.model_service.generate_cad_code')
    @patch('app.services.db_service.add_record')
    def test_generate_cad_integration(self, mock_add_record, mock_generate):
        """Test CAD generation endpoint integration"""
        mock_generate.return_value = "cube = Part.makeBox(10, 10, 10)"
        mock_add_record.return_value = None
        
        payload = {
            "prompt": "generate a cube",
            "model_choice": "llava",
            "user_id": "test_user"
        }
        
        response = client.post("/generate_cad", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "cad_code" in data
        assert data["prompt"] == "generate a cube"
        mock_generate.assert_called_once()
        mock_add_record.assert_called_once()

    @patch('app.services.db_service.get_history')
    def test_history_endpoint_integration(self, mock_get_history):
        """Test history endpoint integration"""
        mock_get_history.return_value = [
            {
                "_id": "123",
                "prompt": "test",
                "cad_code": "code",
                "timestamp": "2024-01-01T00:00:00"
            }
        ]
        
        response = client.get("/history/?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "records" in data
        assert len(data["records"]) == 1

    @patch('app.services.rag_service.retrieve_similar_context')
    def test_rag_context_integration(self, mock_retrieve):
        """Test RAG context endpoint integration"""
        mock_retrieve.return_value = [
            {"text": "similar prompt 1"},
            {"text": "similar prompt 2"}
        ]
        
        payload = {"prompt": "test prompt"}
        response = client.post("/history/context", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "context" in data
        assert len(data["context"]) == 2

    def test_history_limit_validation(self):
        """Test history endpoint limit validation"""
        response = client.get("/history/?limit=0")
        assert response.status_code == 422  # Validation error
        
        response = client.get("/history/?limit=101")
        assert response.status_code == 422  # Validation error

    @patch('app.services.db_service.add_record')
    def test_history_add_dummy_data_integration(self, mock_add_record):
        """Test adding dummy data endpoint integration"""
        mock_add_record.return_value = None
        
        response = client.post("/history/add-dummy-data")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "added_count" in data

