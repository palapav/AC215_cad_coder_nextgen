"""
End-to-end tests for complete workflows
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)


class TestE2EWorkflow:
    """End-to-end tests for complete user workflows"""

    @patch('app.services.model_service.generate_cad_code')
    @patch('app.services.db_service.add_record')
    @patch('app.services.db_service.get_history')
    def test_complete_generation_workflow(self, mock_get_history, mock_add_record, mock_generate):
        """Test complete workflow: generate CAD -> save to DB -> retrieve history"""
        # Step 1: Generate CAD code
        mock_generate.return_value = "cube = Part.makeBox(10, 10, 10)"
        mock_add_record.return_value = None
        
        generate_payload = {
            "prompt": "create a cube",
            "model_choice": "llava",
            "user_id": "e2e_test_user"
        }
        
        generate_response = client.post("/generate_cad", json=generate_payload)
        assert generate_response.status_code == 200
        assert "cad_code" in generate_response.json()
        
        # Step 2: Retrieve history
        mock_get_history.return_value = [
            {
                "_id": "123",
                "user_id": "e2e_test_user",
                "prompt": "create a cube",
                "cad_code": "cube = Part.makeBox(10, 10, 10)",
                "timestamp": "2024-01-01T00:00:00"
            }
        ]
        
        history_response = client.get("/history/?limit=10")
        assert history_response.status_code == 200
        assert len(history_response.json()["records"]) == 1

    @patch('app.services.rag_service.retrieve_similar_context')
    @patch('app.services.model_service.generate_cad_code')
    @patch('app.services.db_service.add_record')
    def test_rag_enhanced_generation_workflow(self, mock_add_record, mock_generate, mock_rag):
        """Test workflow with RAG context retrieval"""
        # Step 1: Get RAG context
        mock_rag.return_value = [
            {"text": "similar prompt: create a box"},
            {"text": "similar prompt: make a cube"}
        ]
        
        rag_response = client.post("/history/context", json={"prompt": "create a cube"})
        assert rag_response.status_code == 200
        assert "context" in rag_response.json()
        
        # Step 2: Generate with context
        mock_generate.return_value = "cube = Part.makeBox(10, 10, 10)"
        mock_add_record.return_value = None
        
        generate_payload = {
            "prompt": "create a cube",
            "model_choice": "llava",
            "user_id": "e2e_test_user",
            "rag_context": "similar prompts found"
        }
        
        generate_response = client.post("/generate_cad", json=generate_payload)
        assert generate_response.status_code == 200
        assert "cad_code" in generate_response.json()

    @patch('app.services.db_service.add_record')
    def test_multiple_generations_workflow(self, mock_add_record):
        """Test multiple CAD generations in sequence"""
        mock_add_record.return_value = None
        
        prompts = [
            {"prompt": "create a cube", "model_choice": "llava"},
            {"prompt": "create a sphere", "model_choice": "qwen"},
            {"prompt": "create a cylinder", "model_choice": "llava"}
        ]
        
        with patch('app.services.model_service.generate_cad_code') as mock_generate:
            mock_generate.side_effect = [
                "cube = Part.makeBox(10, 10, 10)",
                "sphere = Part.makeSphere(5)",
                "cylinder = Part.makeCylinder(3, 10)"
            ]
            
            for prompt_data in prompts:
                payload = {
                    **prompt_data,
                    "user_id": "e2e_test_user"
                }
                response = client.post("/generate_cad", json=payload)
                assert response.status_code == 200
                assert "cad_code" in response.json()
        
        # Verify all records were added
        assert mock_add_record.call_count == 3

    def test_error_handling_workflow(self):
        """Test error handling in complete workflow"""
        # Test invalid endpoint
        response = client.get("/invalid_endpoint")
        assert response.status_code == 404
        
        # Test invalid payload
        response = client.post("/generate_cad", json={"invalid": "data"})
        assert response.status_code in [422, 500]  # Validation or server error
        
        # Test invalid limit parameter
        response = client.get("/history/?limit=-1")
        assert response.status_code == 422

