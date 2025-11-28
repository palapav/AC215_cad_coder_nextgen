"""Tests for prepare_user_data.py script."""
import pytest
import json
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestPrepareUserData:
    """Test user data preparation."""

    def test_transform_creates_output(self, sample_jsonl_data, temp_dir):
        """Test that transform creates output file."""
        from prepare_user_data import transform_to_user_data
        
        input_file = sample_jsonl_data / "test.jsonl"
        output_file = temp_dir / "user_data.jsonl"
        
        count = transform_to_user_data(input_file, output_file)
        
        assert output_file.exists()
        assert count == 2

    def test_transform_correct_format(self, sample_jsonl_data, temp_dir):
        """Test that output has correct user data format."""
        from prepare_user_data import transform_to_user_data
        
        input_file = sample_jsonl_data / "test.jsonl"
        output_file = temp_dir / "user_data.jsonl"
        
        transform_to_user_data(input_file, output_file)
        
        # Read and verify output
        with open(output_file) as f:
            records = [json.loads(line) for line in f]
        
        for record in records:
            assert "question_id" in record
            assert record["question_id"].startswith("user_")
            assert "prompt" in record
            assert "llm_output" in record
            assert "source" in record
            assert record["source"] == "user"
            assert "data_version" in record
            assert record["data_version"] == "v2"

    def test_transform_preserves_content(self, sample_jsonl_data, temp_dir):
        """Test that transform preserves content."""
        from prepare_user_data import transform_to_user_data
        
        input_file = sample_jsonl_data / "test.jsonl"
        output_file = temp_dir / "user_data.jsonl"
        
        transform_to_user_data(input_file, output_file)
        
        with open(output_file) as f:
            records = [json.loads(line) for line in f]
        
        # Check that original content is preserved
        outputs = [r["llm_output"] for r in records]
        assert any("cq.box" in o for o in outputs)
        assert any("cq.sphere" in o for o in outputs)

    def test_transform_handles_empty_lines(self, temp_dir):
        """Test that transform handles empty lines."""
        from prepare_user_data import transform_to_user_data
        
        # Create input with empty lines
        input_file = temp_dir / "with_empty.jsonl"
        with open(input_file, 'w') as f:
            f.write('{"question_id": "1", "text": "test", "ground_truth": "code"}\n')
            f.write('\n')
            f.write('{"question_id": "2", "text": "test2", "ground_truth": "code2"}\n')
        
        output_file = temp_dir / "output.jsonl"
        
        count = transform_to_user_data(input_file, output_file)
        
        assert count == 2

    def test_transform_handles_invalid_json(self, temp_dir):
        """Test that transform handles invalid JSON gracefully."""
        from prepare_user_data import transform_to_user_data
        
        # Create input with invalid JSON
        input_file = temp_dir / "invalid.jsonl"
        with open(input_file, 'w') as f:
            f.write('{"question_id": "1", "text": "test", "ground_truth": "code"}\n')
            f.write('not valid json\n')
            f.write('{"question_id": "2", "text": "test2", "ground_truth": "code2"}\n')
        
        output_file = temp_dir / "output.jsonl"
        
        count = transform_to_user_data(input_file, output_file)
        
        # Should skip invalid line and process others
        assert count == 2

