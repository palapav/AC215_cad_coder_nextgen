"""Pytest configuration and fixtures for datapipeline tests."""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock
from PIL import Image


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample test image."""
    img = Image.new('RGB', (100, 100), color='red')
    img_path = temp_dir / "test_image.png"
    img.save(img_path)
    return img_path


@pytest.fixture
def sample_code():
    """Sample CadQuery code for testing."""
    return """
import cadquery as cq

# Create a simple box
result = cq.Workplane("XY").box(10, 10, 10)

# Add a hole
result = result.faces(">Z").hole(3)

print("Done!")
"""


@pytest.fixture
def mock_gcs_client():
    """Mock Google Cloud Storage client."""
    mock_client = Mock()
    mock_bucket = Mock()
    mock_blob = Mock()
    
    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    mock_bucket.list_blobs.return_value = []
    
    mock_blob.upload_from_filename.return_value = None
    mock_blob.download_as_bytes.return_value = b"test content"
    
    return mock_client


@pytest.fixture
def mock_hf_dataset():
    """Mock HuggingFace dataset."""
    mock_record = {
        "image": Image.new('RGB', (100, 100), color='blue'),
        "cadquery": "import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)",
        "uid": "test_001"
    }
    
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = Mock(return_value=iter([mock_record]))
    mock_dataset.__len__ = Mock(return_value=1)
    mock_dataset.select = Mock(return_value=mock_dataset)
    
    return {"test": mock_dataset}


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Set test environment variables."""
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    monkeypatch.setenv("HF_TOKEN", "test_token")

