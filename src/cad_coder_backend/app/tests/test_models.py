"""Tests for Pydantic models."""
import pytest
from app.models.cad_input import CADInput
from app.models.model_choice import ModelChoice


class TestCADInput:
    """Test CADInput model validation."""

    def test_cad_input_basic(self):
        """Test basic CAD input creation."""
        input_data = CADInput(
            prompt="make a cube",
            model_choice="llava"
        )
        assert input_data.prompt == "make a cube"
        assert input_data.model_choice == ModelChoice.llava

    def test_cad_input_with_qwen(self):
        """Test CAD input with Qwen model."""
        input_data = CADInput(
            prompt="make a sphere",
            model_choice="qwen"
        )
        assert input_data.model_choice == ModelChoice.qwen

    def test_cad_input_with_enum(self):
        """Test CAD input with ModelChoice enum."""
        input_data = CADInput(
            prompt="test",
            model_choice=ModelChoice.llava
        )
        assert input_data.model_choice == ModelChoice.llava

    def test_cad_input_invalid_model_defaults_to_llava(self):
        """Test invalid model choice defaults to llava."""
        input_data = CADInput(
            prompt="test",
            model_choice="invalid_model"
        )
        assert input_data.model_choice == ModelChoice.llava

    def test_cad_input_case_insensitive(self):
        """Test model choice is case insensitive."""
        input_data = CADInput(
            prompt="test",
            model_choice="QWEN"
        )
        assert input_data.model_choice == ModelChoice.qwen

    def test_cad_input_with_image_path(self):
        """Test CAD input with image path."""
        input_data = CADInput(
            prompt="describe this",
            model_choice="llava",
            image_path="data:image/png;base64,test"
        )
        assert input_data.image_path == "data:image/png;base64,test"

    def test_cad_input_with_user_id(self):
        """Test CAD input with user ID."""
        input_data = CADInput(
            prompt="test",
            model_choice="llava",
            user_id="user123"
        )
        assert input_data.user_id == "user123"

    def test_cad_input_default_user_id(self):
        """Test CAD input defaults user_id."""
        input_data = CADInput(
            prompt="test",
            model_choice="llava"
        )
        assert input_data.user_id == "default"

    def test_cad_input_with_rag_context(self):
        """Test CAD input with RAG context."""
        input_data = CADInput(
            prompt="test",
            model_choice="llava",
            rag_context="Example context"
        )
        assert input_data.rag_context == "Example context"

    def test_cad_input_unexpected_type_defaults(self):
        """Test CAD input with unexpected type defaults to llava."""
        input_data = CADInput(
            prompt="test",
            model_choice=12345  # Invalid type
        )
        assert input_data.model_choice == ModelChoice.llava
