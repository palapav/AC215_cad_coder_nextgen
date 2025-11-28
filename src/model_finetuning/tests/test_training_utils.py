"""Unit tests for training utilities and argument parsing."""
import pytest
import sys
import os
import argparse
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import TRAINING_DEFAULTS, DATA_PATHS


class TestTrainingArgumentDefaults:
    """Test that training script argument defaults are valid."""

    def test_batch_size_default_matches_config(self):
        """Batch size default should match config."""
        assert TRAINING_DEFAULTS["batch_size"] == 2

    def test_gradient_accumulation_default_matches_config(self):
        """Gradient accumulation default should match config."""
        assert TRAINING_DEFAULTS["gradient_accumulation_steps"] == 4

    def test_effective_batch_size_calculation(self):
        """Effective batch size should be batch_size * grad_accum."""
        effective = TRAINING_DEFAULTS["batch_size"] * TRAINING_DEFAULTS["gradient_accumulation_steps"]
        # With 4 GPUs, effective batch = 2 * 4 * 4 = 32 per step
        assert effective == 8  # Per GPU, without multi-GPU

    def test_learning_rate_is_reasonable(self):
        """Learning rate should be in reasonable range for fine-tuning."""
        lr = TRAINING_DEFAULTS["learning_rate"]
        assert 1e-6 <= lr <= 1e-4  # Typical fine-tuning range


class TestDataPathValidation:
    """Test data path configuration."""

    def test_client_paths_are_subdirs_of_partitioned(self):
        """Client paths should be under partitioned directory."""
        assert DATA_PATHS["client1"].startswith(DATA_PATHS["partitioned"])
        assert DATA_PATHS["client2"].startswith(DATA_PATHS["partitioned"])

    def test_combined_path_is_under_partitioned(self):
        """Combined path should be under partitioned directory."""
        assert DATA_PATHS["combined"].startswith(DATA_PATHS["partitioned"])

    def test_validation_path_is_under_partitioned(self):
        """Validation path should be under partitioned directory."""
        assert DATA_PATHS["validation"].startswith(DATA_PATHS["partitioned"])


class TestIsValidDatasetDir:
    """Test dataset directory validation function."""

    def test_nonexistent_path_is_invalid(self, tmp_path):
        """Non-existent path should be invalid."""
        # Import the function
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from centralized_train import is_valid_dataset_dir
        
        assert is_valid_dataset_dir(str(tmp_path / "nonexistent")) is False

    def test_empty_directory_is_invalid(self, tmp_path):
        """Empty directory should be invalid."""
        from centralized_train import is_valid_dataset_dir
        
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        assert is_valid_dataset_dir(str(empty_dir)) is False

    def test_directory_with_dataset_info_is_valid(self, tmp_path):
        """Directory with dataset_info.json should be valid."""
        from centralized_train import is_valid_dataset_dir
        
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()
        (valid_dir / "dataset_info.json").write_text("{}")
        
        assert is_valid_dataset_dir(str(valid_dir)) is True

    def test_directory_with_state_json_is_valid(self, tmp_path):
        """Directory with state.json should be valid."""
        from centralized_train import is_valid_dataset_dir
        
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()
        (valid_dir / "state.json").write_text("{}")
        
        assert is_valid_dataset_dir(str(valid_dir)) is True


class TestTrainingConfigConsistency:
    """Test training configuration consistency."""

    def test_max_len_sufficient_for_cad_code(self):
        """Max length should be sufficient for typical CAD code."""
        # Typical CAD code is 500-2000 tokens
        assert TRAINING_DEFAULTS["max_len"] >= 2048

    def test_checkpoint_steps_reasonable(self):
        """Checkpoint steps should be reasonable for training."""
        # Should checkpoint at least every 1000 steps
        assert TRAINING_DEFAULTS["checkpoint_steps"] >= 500
        assert TRAINING_DEFAULTS["checkpoint_steps"] <= 5000

    def test_warmup_steps_less_than_checkpoint(self):
        """Warmup should complete before first checkpoint."""
        assert TRAINING_DEFAULTS["warmup_steps"] < TRAINING_DEFAULTS["checkpoint_steps"]

