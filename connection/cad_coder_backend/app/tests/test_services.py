"""
Unit tests for service modules
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services import auth_service, db_service, rag_service
from datetime import datetime


class TestAuthService:
    """Tests for auth_service module"""

    @patch('app.services.auth_service.id_token.verify_oauth2_token')
    @patch('app.services.auth_service.requests.Request')
    def test_verify_google_token_success(self, mock_request, mock_verify):
        """Test successful Google token verification"""
        mock_verify.return_value = {
            "email": "test@example.com",
            "name": "Test User",
            "sub": "123456"
        }
        
        result = auth_service.verify_google_token("valid_token")
        
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"
        assert result["sub"] == "123456"

    @patch('app.services.auth_service.id_token.verify_oauth2_token')
    @patch('app.services.auth_service.requests.Request')
    def test_verify_google_token_invalid(self, mock_request, mock_verify):
        """Test invalid Google token"""
        mock_verify.side_effect = ValueError("Invalid token")
        
        result = auth_service.verify_google_token("invalid_token")
        
        assert "error" in result

    @patch('app.services.auth_service.id_token.verify_oauth2_token')
    @patch('app.services.auth_service.requests.Request')
    def test_verify_google_token_exception(self, mock_request, mock_verify):
        """Test exception during token verification"""
        mock_verify.side_effect = Exception("Network error")
        
        result = auth_service.verify_google_token("token")
        
        assert "error" in result


class TestDBService:
    """Tests for db_service module"""

    @patch('app.services.db_service.collection')
    def test_add_record(self, mock_collection):
        """Test adding a record to MongoDB"""
        mock_collection.insert_one = Mock()
        
        db_service.add_record(
            user_id="test_user",
            prompt="test prompt",
            cad_code="test code",
            gcs_uri="gs://test/uri",
            image_uri="/test/image.png",
            input_type="image"
        )
        
        mock_collection.insert_one.assert_called_once()
        call_args = mock_collection.insert_one.call_args[0][0]
        assert call_args["user_id"] == "test_user"
        assert call_args["prompt"] == "test prompt"
        assert call_args["cad_code"] == "test code"
        assert call_args["input_type"] == "image"

    @patch('app.services.db_service.collection')
    def test_get_history(self, mock_collection):
        """Test retrieving history"""
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = [
            {"_id": "123", "prompt": "test", "cad_code": "code", "timestamp": datetime.utcnow()}
        ]
        mock_collection.find.return_value = mock_cursor
        
        results = db_service.get_history(limit=10, user_id="test_user")
        
        assert len(results) == 1
        assert results[0]["prompt"] == "test"

    @patch('app.services.db_service.collection')
    def test_get_all_prompts(self, mock_collection):
        """Test retrieving all prompts for RAG"""
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = [
            {"prompt": "test1", "cad_code": "code1"},
            {"prompt": "test2", "cad_code": "code2"}
        ]
        mock_collection.find.return_value = mock_cursor
        
        results = db_service.get_all_prompts(limit=200)
        
        assert len(results) == 2
        assert results[0]["prompt"] == "test1"
        assert results[0]["response"] == "code1"


class TestRAGService:
    """Tests for rag_service module"""

    @patch('app.services.rag_service.get_all_prompts')
    def test_retrieve_similar_context_with_data(self, mock_get_prompts):
        """Test RAG context retrieval with available data"""
        mock_get_prompts.return_value = [
            {"text": "prompt1"},
            {"text": "prompt2"},
            {"text": "prompt3"},
            {"text": "prompt4"}
        ]
        
        result = rag_service.retrieve_similar_context("test prompt")
        
        assert len(result) == 3
        assert all("text" in item for item in result)

    @patch('app.services.rag_service.get_all_prompts')
    def test_retrieve_similar_context_no_data(self, mock_get_prompts):
        """Test RAG context retrieval with no data"""
        mock_get_prompts.return_value = []
        
        result = rag_service.retrieve_similar_context("test prompt")
        
        assert len(result) == 1
        assert result[0]["text"] == "No context available"

    @patch('app.services.rag_service.get_all_prompts')
    def test_retrieve_similar_context_limited_data(self, mock_get_prompts):
        """Test RAG context retrieval with limited data"""
        mock_get_prompts.return_value = [
            {"text": "prompt1"},
            {"text": "prompt2"}
        ]
        
        result = rag_service.retrieve_similar_context("test prompt")
        
        assert len(result) == 2

