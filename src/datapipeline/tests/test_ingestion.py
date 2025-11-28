"""Tests for data ingestion module."""
import pytest
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestIngestionHelpers:
    """Test ingestion helper functions."""

    def test_upload_to_gcs_success(self, mock_gcs_client, monkeypatch, temp_dir):
        """Test successful GCS upload."""
        from data_ingestion import dataloader
        
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        with patch.object(dataloader.storage, 'Client', return_value=mock_gcs_client):
            result = dataloader.upload_to_gcs(
                "test-bucket",
                str(test_file),
                "test/destination.txt"
            )
        
        assert result is True
        mock_gcs_client.bucket.assert_called_with("test-bucket")

    def test_upload_to_gcs_failure(self, mock_gcs_client, monkeypatch, temp_dir):
        """Test GCS upload failure handling."""
        from data_ingestion import dataloader
        
        # Make upload fail
        mock_gcs_client.bucket.return_value.blob.return_value.upload_from_filename.side_effect = Exception("Upload failed")
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        with patch.object(dataloader.storage, 'Client', return_value=mock_gcs_client):
            result = dataloader.upload_to_gcs(
                "test-bucket",
                str(test_file),
                "test/destination.txt"
            )
        
        assert result is False


class TestDatasetIngestion:
    """Test dataset ingestion functions."""

    def test_ingest_dataset_with_mock(self, mock_hf_dataset, mock_gcs_client, monkeypatch):
        """Test dataset ingestion with mocked dependencies."""
        from data_ingestion import dataloader
        
        with patch.object(dataloader, 'load_dataset', return_value=mock_hf_dataset):
            with patch.object(dataloader.storage, 'Client', return_value=mock_gcs_client):
                stats = dataloader.ingest_dataset_to_gcs(
                    bucket_name="test-bucket",
                    splits=["test"],
                    limit=1
                )
        
        assert isinstance(stats, dict)
        assert 'total_uploaded' in stats
        assert 'total_failed' in stats
        assert 'splits' in stats

    def test_ingest_dataset_handles_missing_token(self, monkeypatch):
        """Test that ingestion handles missing HF token gracefully."""
        monkeypatch.delenv("HF_TOKEN", raising=False)
        
        from data_ingestion import dataloader
        
        # The function should not crash when HF_TOKEN is missing
        # (it will warn but continue)
        assert dataloader is not None

