"""Pytest configuration and fixtures for model_finetuning tests."""
import pytest
import sys
import os
from unittest.mock import Mock, MagicMock
from PIL import Image
import numpy as np

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'CADRL'))


@pytest.fixture
def sample_image():
    """Create a sample PIL Image for testing."""
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
def sample_dataset_entry(sample_image, sample_cad_code):
    """Create a sample dataset entry."""
    return {
        'image': sample_image,
        'code': sample_cad_code
    }


@pytest.fixture
def mock_processor():
    """Create a mock Qwen processor."""
    processor = Mock()
    processor.tokenizer = Mock()
    processor.tokenizer.pad_token_id = 0
    processor.tokenizer.unk_token_id = 1
    processor.tokenizer.convert_tokens_to_ids = Mock(return_value=100)
    processor.apply_chat_template = Mock(return_value=["<|im_start|>system\nYou are helpful.<|im_end|>"])
    processor.return_value = {
        'input_ids': MagicMock(),
        'attention_mask': MagicMock(),
        'pixel_values': MagicMock()
    }
    return processor


@pytest.fixture
def mock_model():
    """Create a mock model for testing."""
    model = Mock()
    model.visual = Mock()
    model.config = Mock()
    model.named_parameters = Mock(return_value=[])
    return model


# Skip GPU-dependent tests
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "gpu: mark test as requiring GPU"
    )


def pytest_collection_modifyitems(config, items):
    """Skip GPU tests when running on CPU."""
    import torch
    
    skip_gpu = pytest.mark.skip(reason="GPU not available")
    for item in items:
        if "gpu" in item.keywords:
            if not torch.cuda.is_available():
                item.add_marker(skip_gpu)

