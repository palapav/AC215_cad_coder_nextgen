"""Tests for convert_raw_to_jsonl.py script."""
import pytest
import json
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestConvertRawToJsonl:
    """Test raw data to JSONL conversion."""

    def test_convert_split_creates_jsonl(self, sample_raw_data, temp_dir):
        """Test that conversion creates JSONL file."""
        from convert_raw_to_jsonl import convert_split_to_jsonl
        
        output_file = temp_dir / "output" / "test.jsonl"
        input_dir = sample_raw_data / "raw_data" / "test"
        
        count = convert_split_to_jsonl(input_dir, output_file, "test")
        
        assert output_file.exists()
        assert count == 3  # We created 3 samples

    def test_convert_split_correct_format(self, sample_raw_data, temp_dir):
        """Test that JSONL has correct format."""
        from convert_raw_to_jsonl import convert_split_to_jsonl
        
        output_file = temp_dir / "output" / "test.jsonl"
        input_dir = sample_raw_data / "raw_data" / "test"
        
        convert_split_to_jsonl(input_dir, output_file, "test")
        
        # Read and verify JSONL
        with open(output_file) as f:
            records = [json.loads(line) for line in f]
        
        assert len(records) == 3
        
        for record in records:
            assert "question_id" in record
            assert "image" in record
            assert "text" in record
            assert "category" in record
            assert "ground_truth" in record

    def test_convert_split_empty_dir(self, temp_dir):
        """Test conversion with empty directory."""
        from convert_raw_to_jsonl import convert_split_to_jsonl
        
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        output_file = temp_dir / "output" / "empty.jsonl"
        
        count = convert_split_to_jsonl(empty_dir, output_file, "empty")
        
        assert count == 0

    def test_convert_split_missing_py_file(self, temp_dir):
        """Test conversion handles missing .py files."""
        from convert_raw_to_jsonl import convert_split_to_jsonl
        from PIL import Image
        
        # Create directory with only PNG (no corresponding .py)
        input_dir = temp_dir / "incomplete"
        input_dir.mkdir()
        
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_dir / "orphan.png")
        
        output_file = temp_dir / "output" / "incomplete.jsonl"
        
        count = convert_split_to_jsonl(input_dir, output_file, "incomplete")
        
        assert count == 0  # Should skip orphan PNG

    def test_convert_split_nonexistent_dir(self, temp_dir):
        """Test conversion with non-existent directory."""
        from convert_raw_to_jsonl import convert_split_to_jsonl
        
        nonexistent = temp_dir / "does_not_exist"
        output_file = temp_dir / "output" / "none.jsonl"
        
        count = convert_split_to_jsonl(nonexistent, output_file, "none")
        
        assert count == 0

