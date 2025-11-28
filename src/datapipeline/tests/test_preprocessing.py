"""Tests for data preprocessing module."""
import pytest
from PIL import Image
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPreprocessingHelpers:
    """Test preprocessing helper functions."""

    def test_expand2square_already_square(self):
        """Test expand2square with already square image."""
        from data_preprocessing.preprocess_cv import expand2square
        
        img = Image.new('RGB', (100, 100), color='red')
        result = expand2square(img)
        
        assert result.size == (100, 100)
        assert result.mode == 'RGB'

    def test_expand2square_landscape(self):
        """Test expand2square with landscape image."""
        from data_preprocessing.preprocess_cv import expand2square
        
        img = Image.new('RGB', (200, 100), color='blue')
        result = expand2square(img)
        
        assert result.size == (200, 200)
        assert result.mode == 'RGB'

    def test_expand2square_portrait(self):
        """Test expand2square with portrait image."""
        from data_preprocessing.preprocess_cv import expand2square
        
        img = Image.new('RGB', (100, 200), color='green')
        result = expand2square(img)
        
        assert result.size == (200, 200)
        assert result.mode == 'RGB'

    def test_clean_cadquery_code_removes_comments(self, sample_code):
        """Test that clean_cadquery_code removes comments."""
        from data_preprocessing.preprocess_cv import clean_cadquery_code
        
        result = clean_cadquery_code(sample_code)
        
        assert "# Create a simple box" not in result
        assert "# Add a hole" not in result

    def test_clean_cadquery_code_removes_print(self, sample_code):
        """Test that clean_cadquery_code removes print statements."""
        from data_preprocessing.preprocess_cv import clean_cadquery_code
        
        result = clean_cadquery_code(sample_code)
        
        assert "print(" not in result

    def test_clean_cadquery_code_preserves_code(self):
        """Test that clean_cadquery_code preserves actual code."""
        from data_preprocessing.preprocess_cv import clean_cadquery_code
        
        code = 'result = cq.Workplane("XY").box(10, 10, 10)'
        result = clean_cadquery_code(code)
        
        assert 'cq.Workplane("XY").box(10, 10, 10)' in result

    def test_clean_cadquery_code_replaces_tabs(self):
        """Test that clean_cadquery_code replaces tabs with spaces."""
        from data_preprocessing.preprocess_cv import clean_cadquery_code
        
        code = "def foo():\n\treturn 1"
        result = clean_cadquery_code(code)
        
        assert "\t" not in result

    def test_build_image_transform(self):
        """Test image transform creation."""
        from data_preprocessing.preprocess_cv import build_image_transform
        
        transform = build_image_transform(336)
        
        assert transform is not None

    def test_preprocess_image(self):
        """Test image preprocessing."""
        from data_preprocessing.preprocess_cv import preprocess_image, build_image_transform
        
        img = Image.new('RGB', (100, 100), color='red')
        transform = build_image_transform(336)
        
        result = preprocess_image(img, transform)
        
        # Result should be a tensor
        assert result is not None
        assert result.shape[0] == 3  # RGB channels
        assert result.shape[1] == 336
        assert result.shape[2] == 336


class TestGCSFunctions:
    """Test GCS-related functions (mocked)."""

    def test_list_gcs_files_empty(self, mock_gcs_client, monkeypatch):
        """Test listing files from empty bucket."""
        from data_preprocessing import preprocess_cv
        from unittest.mock import patch
        
        with patch.object(preprocess_cv.storage, 'Client', return_value=mock_gcs_client):
            result = preprocess_cv.list_gcs_files("test-bucket", "test/")
        
        assert isinstance(result, list)

