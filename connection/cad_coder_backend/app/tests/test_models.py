"""
Unit tests for Pydantic models
"""
import pytest
from app.models.cad_input import CADInput
from app.models.cad_output import CADOutput
from app.models.model_choice import ModelChoice


class TestCADInput:
    """Tests for CADInput model"""

    def test_cad_input_required_fields(self):
        """Test CADInput with required fields only"""
        input_data = CADInput(prompt="create a cube")
        
        assert input_data.prompt == "create a cube"
        assert input_data.user_id == "default"
        assert input_data.model_choice == ModelChoice.llava
        assert input_data.image_path is None

    def test_cad_input_all_fields(self):
        """Test CADInput with all fields"""
        input_data = CADInput(
            prompt="create a cube",
            image_path="/path/to/image.png",
            user_id="user123",
            model_choice=ModelChoice.qwen,
            rag_context="some context"
        )
        
        assert input_data.prompt == "create a cube"
        assert input_data.image_path == "/path/to/image.png"
        assert input_data.user_id == "user123"
        assert input_data.model_choice == ModelChoice.qwen
        assert input_data.rag_context == "some context"

    def test_cad_input_validation(self):
        """Test CADInput validation"""
        with pytest.raises(Exception):  # Pydantic validation error
            CADInput()  # Missing required field 'prompt'


class TestCADOutput:
    """Tests for CADOutput model"""

    def test_cad_output_required_fields(self):
        """Test CADOutput with required fields only"""
        output_data = CADOutput(
            prompt="create a cube",
            cad_code="cube = Part.makeBox(10, 10, 10)"
        )
        
        assert output_data.prompt == "create a cube"
        assert output_data.cad_code == "cube = Part.makeBox(10, 10, 10)"
        assert output_data.model is None
        assert output_data.gcs_uri is None
        assert output_data.rag_used is False

    def test_cad_output_all_fields(self):
        """Test CADOutput with all fields"""
        output_data = CADOutput(
            prompt="create a cube",
            cad_code="cube = Part.makeBox(10, 10, 10)",
            model=ModelChoice.llava,
            gcs_uri="gs://bucket/file.step",
            rag_used=True,
            pipeline_stage="generate"
        )
        
        assert output_data.prompt == "create a cube"
        assert output_data.cad_code == "cube = Part.makeBox(10, 10, 10)"
        assert output_data.model == ModelChoice.llava
        assert output_data.gcs_uri == "gs://bucket/file.step"
        assert output_data.rag_used is True
        assert output_data.pipeline_stage == "generate"


class TestModelChoice:
    """Tests for ModelChoice enum"""

    def test_model_choice_values(self):
        """Test ModelChoice enum values"""
        assert ModelChoice.llava.value == "llava"
        assert ModelChoice.qwen.value == "qwen"

    def test_model_choice_comparison(self):
        """Test ModelChoice enum comparison"""
        assert ModelChoice.llava == ModelChoice.llava
        assert ModelChoice.llava != ModelChoice.qwen

