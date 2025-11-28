"""Pytest configuration and fixtures for backend tests."""
import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Set test environment variables BEFORE importing app modules
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB", "test_cad_coder")
os.environ.setdefault("QWEN_INFERENCE_BACKEND", "mock")
os.environ.setdefault("LLAVA_INFERENCE_BACKEND", "mock")
os.environ.setdefault("ENABLE_RAG", "false")


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set default environment variables for all tests."""
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGO_DB", "test_cad_coder")
    monkeypatch.setenv("QWEN_INFERENCE_BACKEND", "mock")
    monkeypatch.setenv("LLAVA_INFERENCE_BACKEND", "mock")
    monkeypatch.setenv("ENABLE_RAG", "false")
    # Reduced token counts for faster tests
    monkeypatch.setenv("QWEN_MODAL_MAX_NEW_TOKENS", "128")
    monkeypatch.setenv("LLAVA_MODAL_MAX_NEW_TOKENS", "128")


@pytest.fixture
def sample_image():
    """Create a sample PIL Image for testing."""
    from PIL import Image
    return Image.new('RGB', (224, 224), color='red')


@pytest.fixture
def sample_cad_code():
    """Sample CADQuery code for testing."""
    return """import cadquery as cq

# Create a simple box
result = cq.Workplane("XY").box(10, 10, 5)

# Add a hole
result = result.faces(">Z").workplane().hole(3)

solid = result
"""


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB collection."""
    mock_collection = Mock()
    mock_collection.insert_one = Mock(return_value=Mock(inserted_id="test_id"))
    mock_collection.find = Mock(return_value=Mock(
        sort=Mock(return_value=Mock(
            limit=Mock(return_value=[])
        ))
    ))
    return mock_collection


@pytest.fixture
def mock_modal_function():
    """Mock Modal function for inference."""
    mock_fn = Mock()
    mock_fn.remote = Mock(return_value="import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)")
    return mock_fn


# Configure pytest markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Skip E2E tests unless explicitly requested."""
    # Check if we're running E2E tests by checking marker expression
    # getoption returns None if not set, or the value if set
    marker_expr = config.getoption("-m", default=None)
    run_e2e = marker_expr is not None and "e2e" in str(marker_expr).lower()
    
    if not run_e2e:
        skip_e2e = pytest.mark.skip(reason="E2E tests skipped (use -m e2e to run)")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)
