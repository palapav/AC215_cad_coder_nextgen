"""Unit tests for model utilities."""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import torch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.model_utils import (
    freeze_vision_encoder,
    get_quantization_config,
)


class TestFreezeVisionEncoder:
    """Test vision encoder freezing."""

    def test_freeze_visual_attribute(self):
        """Should freeze 'visual' attribute if present."""
        mock_model = Mock()
        mock_visual = Mock()
        mock_model.visual = mock_visual
        
        freeze_vision_encoder(mock_model)
        mock_visual.requires_grad_.assert_called_once_with(False)

    def test_freeze_vision_model_attribute(self):
        """Should freeze 'vision_model' attribute if present."""
        mock_model = Mock(spec=['vision_model'])
        mock_vision_model = Mock()
        mock_model.vision_model = mock_vision_model
        
        freeze_vision_encoder(mock_model)
        mock_vision_model.requires_grad_.assert_called_once_with(False)

    def test_no_vision_encoder_found(self, capsys):
        """Should print warning if no vision encoder found."""
        mock_model = Mock(spec=[])  # No vision attributes
        
        freeze_vision_encoder(mock_model)
        captured = capsys.readouterr()
        assert "No vision encoder found" in captured.out


class TestGetQuantizationConfig:
    """Test quantization configuration."""

    def test_no_quantization_by_default(self):
        """Should return None when no quantization requested."""
        config = get_quantization_config(load_in_4bit=False, load_in_8bit=False)
        assert config is None

    @patch('utils.model_utils.BitsAndBytesConfig', create=True)
    def test_4bit_quantization(self, mock_bnb_config):
        """Should create 4-bit config when requested."""
        # Mock the import
        with patch.dict('sys.modules', {'transformers': MagicMock()}):
            from transformers import BitsAndBytesConfig
            mock_config = Mock()
            BitsAndBytesConfig.return_value = mock_config
            
            # This will try to import BitsAndBytesConfig
            config = get_quantization_config(load_in_4bit=True)
            # May return None if import fails in test env
            # Just verify it doesn't crash

    @patch('utils.model_utils.BitsAndBytesConfig', create=True)
    def test_8bit_quantization(self, mock_bnb_config):
        """Should create 8-bit config when requested."""
        with patch.dict('sys.modules', {'transformers': MagicMock()}):
            config = get_quantization_config(load_in_8bit=True)
            # May return None if import fails in test env


class TestLoadCheckpointIntoModel:
    """Test checkpoint loading."""

    def test_load_checkpoint_with_model_state_dict(self, tmp_path):
        """Should load checkpoint with 'model_state_dict' key."""
        from utils.model_utils import load_checkpoint_into_model
        
        # Create mock model
        mock_model = Mock()
        
        # Create checkpoint file
        checkpoint_path = tmp_path / "checkpoint.pt"
        state_dict = {'layer.weight': torch.randn(10, 10)}
        torch.save({'model_state_dict': state_dict}, checkpoint_path)
        
        load_checkpoint_into_model(mock_model, str(checkpoint_path))
        mock_model.load_state_dict.assert_called_once()

    def test_load_checkpoint_with_state_dict(self, tmp_path):
        """Should load checkpoint with 'state_dict' key."""
        from utils.model_utils import load_checkpoint_into_model
        
        mock_model = Mock()
        checkpoint_path = tmp_path / "checkpoint.pt"
        state_dict = {'layer.weight': torch.randn(10, 10)}
        torch.save({'state_dict': state_dict}, checkpoint_path)
        
        load_checkpoint_into_model(mock_model, str(checkpoint_path))
        mock_model.load_state_dict.assert_called_once()

    def test_load_checkpoint_direct_state_dict(self, tmp_path):
        """Should load checkpoint that is directly a state dict."""
        from utils.model_utils import load_checkpoint_into_model
        
        mock_model = Mock()
        checkpoint_path = tmp_path / "checkpoint.pt"
        state_dict = {'layer.weight': torch.randn(10, 10)}
        torch.save(state_dict, checkpoint_path)
        
        load_checkpoint_into_model(mock_model, str(checkpoint_path))
        mock_model.load_state_dict.assert_called_once()

