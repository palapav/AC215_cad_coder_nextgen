"""Unit tests for dataset classes."""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import numpy as np
import io
import base64
import json
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'CADRL'))

from DataUtils.Datasets import extract_code, CADLMDataset, MinimalImageCADDataset


class TestExtractCode:
    """Test code extraction utility."""

    def test_extract_code_with_python_block(self):
        """Should extract code from Python code block."""
        text = "Here is the code:\n```python\nimport cadquery as cq\nresult = cq.Workplane('XY').box(1, 1, 1)\n```\nThat's it."
        expected = "import cadquery as cq\nresult = cq.Workplane('XY').box(1, 1, 1)"
        assert extract_code(text) == expected

    def test_extract_code_without_block(self):
        """Should return original text if no code block."""
        text = "import cadquery as cq\nresult = cq.Workplane('XY').box(1, 1, 1)"
        assert extract_code(text) == text

    def test_extract_code_empty_block(self):
        """Should handle empty code block."""
        text = "```python\n```"
        assert extract_code(text) == ""

    def test_extract_code_multiline(self):
        """Should handle multiline code blocks."""
        text = """Some text before
```python
import cadquery as cq

def create_box():
    return cq.Workplane('XY').box(1, 1, 1)

result = create_box()
```
Some text after"""
        result = extract_code(text)
        assert "import cadquery as cq" in result
        assert "def create_box():" in result
        assert "result = create_box()" in result


class TestMinimalImageCADDataset:
    """Test MinimalImageCADDataset class."""

    @pytest.fixture
    def sample_data(self):
        """Create sample dataset data."""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        return [
            {
                'image': img,
                'code': 'import cadquery as cq\nresult = cq.Workplane("XY").box(1, 1, 1)'
            },
            {
                'image': img,
                'code': 'import cadquery as cq\nresult = cq.Workplane("XY").sphere(0.5)'
            }
        ]

    @pytest.fixture
    def mock_collate_fn(self):
        """Create mock collate function."""
        return Mock(return_value={})

    def test_dataset_length(self, sample_data, mock_collate_fn):
        """Dataset should return correct length."""
        dataset = MinimalImageCADDataset(
            data_dict=sample_data,
            collate_fn=mock_collate_fn,
            basic_image_augmentation=False
        )
        assert len(dataset) == 2

    def test_dataset_getitem_returns_dict(self, sample_data, mock_collate_fn):
        """Dataset __getitem__ should return dict with prompt."""
        dataset = MinimalImageCADDataset(
            data_dict=sample_data,
            collate_fn=mock_collate_fn,
            basic_image_augmentation=False
        )
        item = dataset[0]
        assert isinstance(item, dict)
        assert 'prompt' in item

    def test_dataset_prompt_structure(self, sample_data, mock_collate_fn):
        """Dataset prompt should have correct structure."""
        dataset = MinimalImageCADDataset(
            data_dict=sample_data,
            collate_fn=mock_collate_fn,
            basic_image_augmentation=False
        )
        item = dataset[0]
        prompt = item['prompt']
        
        # Should have system, user, assistant messages
        assert len(prompt) == 3
        assert prompt[0]['role'] == 'system'
        assert prompt[1]['role'] == 'user'
        assert prompt[2]['role'] == 'assistant'

    def test_dataset_user_message_has_image(self, sample_data, mock_collate_fn):
        """User message should contain image."""
        dataset = MinimalImageCADDataset(
            data_dict=sample_data,
            collate_fn=mock_collate_fn,
            basic_image_augmentation=False
        )
        item = dataset[0]
        user_content = item['prompt'][1]['content']
        
        # Should have image and text content
        content_types = [c['type'] for c in user_content]
        assert 'image' in content_types
        assert 'text' in content_types

    def test_dataset_assistant_has_code(self, sample_data, mock_collate_fn):
        """Assistant message should contain code."""
        dataset = MinimalImageCADDataset(
            data_dict=sample_data,
            collate_fn=mock_collate_fn,
            basic_image_augmentation=False
        )
        item = dataset[0]
        assistant_content = item['prompt'][2]['content']
        
        # Should have text content with code
        assert len(assistant_content) == 1
        assert assistant_content[0]['type'] == 'text'
        assert 'cadquery' in assistant_content[0]['text'].lower()

    def test_dataset_no_pc_by_default(self, sample_data, mock_collate_fn):
        """Dataset should not have point cloud by default."""
        dataset = MinimalImageCADDataset(
            data_dict=sample_data,
            collate_fn=mock_collate_fn,
            basic_image_augmentation=False,
            pc_input=False
        )
        item = dataset[0]
        assert item['has_pc'] is False

    def test_encode_image_returns_base64(self, sample_data, mock_collate_fn):
        """encode_image should return valid base64 string."""
        dataset = MinimalImageCADDataset(
            data_dict=sample_data,
            collate_fn=mock_collate_fn,
            basic_image_augmentation=False
        )
        img = Image.new('RGB', (50, 50), color='blue')
        encoded = dataset.encode_image(img, im_type='png')
        
        # Should be valid base64
        assert isinstance(encoded, str)
        decoded = base64.b64decode(encoded)
        assert len(decoded) > 0

    def test_dataset_with_augmentation_probability(self, sample_data, mock_collate_fn):
        """Dataset should respect augmentation probability."""
        dataset = MinimalImageCADDataset(
            data_dict=sample_data,
            collate_fn=mock_collate_fn,
            basic_image_augmentation=True,
            augmentation_probability=0.0  # Never augment
        )
        # Should not raise even with augmentation enabled
        item = dataset[0]
        assert item is not None


class TestCADLMDataset:
    """Test CADLMDataset class."""

    @pytest.fixture
    def sample_jsonl_data(self):
        """Create sample JSONL-style data."""
        return [
            {
                'Type': 'Instruct',
                'MM': True,
                'prompt': [
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': 'Generate CAD code'}
                        ]
                    },
                    {
                        'role': 'assistant',
                        'content': [
                            {'type': 'text', 'text': 'import cadquery as cq'}
                        ]
                    }
                ]
            }
        ]

    @pytest.fixture
    def mock_collate_fn(self):
        """Create mock collate function."""
        return Mock(return_value={})

    def test_dataset_from_list(self, sample_jsonl_data, mock_collate_fn):
        """Dataset should load from list of dicts."""
        dataset = CADLMDataset(
            data_dict=sample_jsonl_data,
            collate_fn=mock_collate_fn,
            pre_load_vision=False
        )
        assert len(dataset) == 1

    def test_dataset_validation_adds_defaults(self, mock_collate_fn):
        """Dataset validation should add default values."""
        data = [
            {
                'prompt': [
                    {
                        'role': 'user',
                        'content': [{'type': 'text', 'text': 'test'}]
                    }
                ]
            }
        ]
        dataset = CADLMDataset(
            data_dict=data,
            collate_fn=mock_collate_fn,
            pre_load_vision=False
        )
        # Should have added Type and MM defaults
        assert dataset.data_dict[0]['Type'] == 'Instruct'
        assert dataset.data_dict[0]['MM'] is False

    def test_dataset_getitem_returns_prompt(self, sample_jsonl_data, mock_collate_fn):
        """Dataset __getitem__ should return prompt list."""
        dataset = CADLMDataset(
            data_dict=sample_jsonl_data,
            collate_fn=mock_collate_fn,
            pre_load_vision=False
        )
        item = dataset[0]
        assert isinstance(item, list)
        assert len(item) == 2  # user and assistant

    def test_read_jsonl_static_method(self, tmp_path):
        """_read_jsonl_with_json should parse JSONL files."""
        # Create temp JSONL file
        jsonl_file = tmp_path / "test.jsonl"
        data = [
            {"id": 1, "text": "first"},
            {"id": 2, "text": "second"}
        ]
        with open(jsonl_file, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        
        result = CADLMDataset._read_jsonl_with_json(str(jsonl_file))
        assert len(result) == 2
        assert result[0]['id'] == 1
        assert result[1]['text'] == 'second'

