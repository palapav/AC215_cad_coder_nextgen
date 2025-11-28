"""Unit tests for configuration module."""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    DEFAULT_MODEL,
    TRAINING_DEFAULTS,
    FEDERATED_DEFAULTS,
    DATA_PATHS,
    WANDB_DEFAULTS,
    EVALUATION_DEFAULTS,
)


class TestTrainingDefaults:
    """Test training configuration defaults."""

    def test_batch_size_positive(self):
        """Batch size should be positive."""
        assert TRAINING_DEFAULTS["batch_size"] > 0

    def test_gradient_accumulation_positive(self):
        """Gradient accumulation steps should be positive."""
        assert TRAINING_DEFAULTS["gradient_accumulation_steps"] > 0

    def test_learning_rate_reasonable(self):
        """Learning rate should be in reasonable range."""
        lr = TRAINING_DEFAULTS["learning_rate"]
        assert 1e-7 < lr < 1e-2

    def test_weight_decay_non_negative(self):
        """Weight decay should be non-negative."""
        assert TRAINING_DEFAULTS["weight_decay"] >= 0

    def test_warmup_steps_non_negative(self):
        """Warmup steps should be non-negative."""
        assert TRAINING_DEFAULTS["warmup_steps"] >= 0

    def test_max_grad_norm_positive(self):
        """Max gradient norm should be positive."""
        assert TRAINING_DEFAULTS["max_grad_norm"] > 0

    def test_max_len_positive(self):
        """Max sequence length should be positive."""
        assert TRAINING_DEFAULTS["max_len"] > 0

    def test_num_epochs_positive(self):
        """Number of epochs should be positive."""
        assert TRAINING_DEFAULTS["num_epochs"] > 0

    def test_checkpoint_steps_positive(self):
        """Checkpoint steps should be positive."""
        assert TRAINING_DEFAULTS["checkpoint_steps"] > 0


class TestFederatedDefaults:
    """Test federated learning configuration defaults."""

    def test_num_rounds_positive(self):
        """Number of rounds should be positive."""
        assert FEDERATED_DEFAULTS["num_rounds"] > 0

    def test_client_epochs_positive(self):
        """Client epochs should be positive."""
        assert FEDERATED_DEFAULTS["client_epochs"] > 0


class TestDataPaths:
    """Test data path configuration."""

    def test_all_paths_are_strings(self):
        """All data paths should be strings."""
        for key, path in DATA_PATHS.items():
            assert isinstance(path, str), f"Path {key} is not a string"

    def test_required_paths_exist(self):
        """Required path keys should exist."""
        required_keys = ["partitioned", "client1", "client2", "combined", "validation", "test"]
        for key in required_keys:
            assert key in DATA_PATHS, f"Missing required path: {key}"


class TestWandBDefaults:
    """Test WandB configuration defaults."""

    def test_project_names_are_strings(self):
        """All WandB project names should be strings."""
        for key, name in WANDB_DEFAULTS.items():
            assert isinstance(name, str), f"Project {key} is not a string"
            assert len(name) > 0, f"Project {key} is empty"


class TestEvaluationDefaults:
    """Test evaluation configuration defaults."""

    def test_n_samples_positive(self):
        """Number of samples should be positive."""
        assert EVALUATION_DEFAULTS["n_samples"] > 0

    def test_n_workers_positive(self):
        """Number of workers should be positive."""
        assert EVALUATION_DEFAULTS["n_workers"] > 0

    def test_timeout_positive(self):
        """Timeout should be positive."""
        assert EVALUATION_DEFAULTS["timeout"] > 0

    def test_temperature_non_negative(self):
        """Temperature should be non-negative."""
        assert EVALUATION_DEFAULTS["temperature"] >= 0

    def test_max_new_tokens_positive(self):
        """Max new tokens should be positive."""
        assert EVALUATION_DEFAULTS["max_new_tokens"] > 0


class TestDefaultModel:
    """Test default model configuration."""

    def test_model_name_is_string(self):
        """Default model should be a string."""
        assert isinstance(DEFAULT_MODEL, str)

    def test_model_name_not_empty(self):
        """Default model should not be empty."""
        assert len(DEFAULT_MODEL) > 0

    def test_model_name_format(self):
        """Default model should have HuggingFace format (org/model)."""
        assert "/" in DEFAULT_MODEL

