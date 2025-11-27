"""
Integration tests for database operations
"""
import pytest
from app.services.db_service import add_record, get_history, get_all_prompts
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestDBIntegration:
    """Integration tests for database service"""

    @patch('app.services.db_service.collection')
    def test_add_and_retrieve_record_integration(self, mock_collection):
        """Test adding and retrieving a record"""
        # Mock insert
        mock_collection.insert_one = MagicMock()
        
        # Add record
        add_record(
            user_id="integration_test_user",
            prompt="integration test prompt",
            cad_code="integration test code",
            input_type="text"
        )
        
        # Verify insert was called
        mock_collection.insert_one.assert_called_once()
        
        # Mock find for retrieval
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = [
            {
                "_id": "test_id",
                "user_id": "integration_test_user",
                "prompt": "integration test prompt",
                "cad_code": "integration test code",
                "timestamp": datetime.utcnow()
            }
        ]
        mock_collection.find.return_value = mock_cursor
        
        # Retrieve record
        results = get_history(limit=10, user_id="integration_test_user")
        
        assert len(results) == 1
        assert results[0]["user_id"] == "integration_test_user"
        assert results[0]["prompt"] == "integration test prompt"

    @patch('app.services.db_service.collection')
    def test_get_all_prompts_integration(self, mock_collection):
        """Test retrieving all prompts for RAG"""
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = [
            {"prompt": "prompt1", "cad_code": "code1"},
            {"prompt": "prompt2", "cad_code": "code2"},
            {"prompt": "prompt3", "cad_code": "code3"}
        ]
        mock_collection.find.return_value = mock_cursor
        
        results = get_all_prompts(limit=200)
        
        assert len(results) == 3
        assert all("prompt" in r and "response" in r for r in results)
        assert results[0]["prompt"] == "prompt1"
        assert results[0]["response"] == "code1"

    @patch('app.services.db_service.collection')
    def test_history_filtering_integration(self, mock_collection):
        """Test history filtering by user_id"""
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = [
            {
                "_id": "id1",
                "user_id": "user1",
                "prompt": "prompt1",
                "cad_code": "code1",
                "timestamp": datetime.utcnow()
            }
        ]
        mock_collection.find.return_value = mock_cursor
        
        results = get_history(limit=10, user_id="user1")
        
        # Verify find was called with user_id filter
        mock_collection.find.assert_called_once_with({"user_id": "user1"})
        assert len(results) == 1
        assert results[0]["user_id"] == "user1"

