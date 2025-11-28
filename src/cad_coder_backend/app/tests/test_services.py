"""Unit tests for backend services."""
import pytest
import asyncio
import os
import sys
import importlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import io
import base64

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# ============================================================================
# Model Service Tests
# ============================================================================
class TestModelService:
    """Test model service functionality."""

    def test_model_choice_enum(self):
        """Test ModelChoice enum values."""
        from app.services.model_service import ModelChoice
        
        assert ModelChoice.LLAVA.value == "llava"
        assert ModelChoice.QWEN.value == "qwen"

    def test_llava_placeholder(self):
        """Test LLaVA placeholder response."""
        from app.services.model_service import _llava_placeholder
        
        result = _llava_placeholder()
        assert "cadquery" in result.lower()
        assert "box" in result.lower()

    def test_qwen_placeholder(self):
        """Test Qwen placeholder response."""
        from app.services.model_service import _qwen_placeholder
        
        result = _qwen_placeholder()
        assert "cadquery" in result.lower()
        assert "sphere" in result.lower()

    @pytest.mark.asyncio
    async def test_generate_cad_code_returns_dict(self):
        """Test that generate_cad_code returns expected dict structure."""
        from app.services import model_service
        
        # Mock the Modal inference functions
        with patch.object(model_service, '_run_llava_via_modal', new_callable=AsyncMock) as mock_llava:
            mock_llava.return_value = "import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)"
            
            result = await model_service.generate_cad_code(
                prompt="make a cube",
                model_choice="llava"
            )
            
            assert isinstance(result, dict)
            assert "cad_code" in result
            assert "rag_used" in result
            assert "rag_context" in result
            assert "rag_results" in result

    @pytest.mark.asyncio
    async def test_generate_cad_code_normalizes_model_choice(self):
        """Test model choice normalization."""
        from app.services import model_service
        
        with patch.object(model_service, '_run_llava_via_modal', new_callable=AsyncMock) as mock_llava:
            mock_llava.return_value = "# test code"
            
            # Test with enum
            result = await model_service.generate_cad_code(
                prompt="test",
                model_choice=model_service.ModelChoice.LLAVA
            )
            assert "cad_code" in result

    @pytest.mark.asyncio
    async def test_generate_cad_code_invalid_choice_defaults_to_llava(self):
        """Test that invalid model choice defaults to LLaVA."""
        from app.services import model_service
        
        with patch.object(model_service, '_run_llava_via_modal', new_callable=AsyncMock) as mock_llava:
            mock_llava.return_value = "# llava code"
            
            result = await model_service.generate_cad_code(
                prompt="test",
                model_choice="invalid_model"
            )
            
            # Should have called LLaVA, not Qwen
            mock_llava.assert_called()

    @pytest.mark.asyncio
    async def test_generate_cad_code_qwen_with_rag_context(self, monkeypatch):
        """Test Qwen path uses RAG context when available."""
        from app.services import model_service

        async_mock = AsyncMock(return_value="# generated code")
        monkeypatch.setattr(model_service, "_run_qwen_via_modal", async_mock)

        def mock_retrieve_context(**kwargs):
            return {
                "context": "Example CAD context",
                "results": [{"id": "example"}],
                "used": True,
            }

        monkeypatch.setattr(model_service.rag_service, "retrieve_context", mock_retrieve_context)

        result = await model_service.generate_cad_code(
            prompt="make a sphere",
            model_choice="qwen",
        )

        assert result["rag_used"] is True
        assert "Example CAD context" in async_mock.await_args.kwargs["prompt"]
        async_mock.assert_awaited_once()


# ============================================================================
# Modal Client Tests
# ============================================================================
class TestModalClient:
    """Test Modal client utilities."""

    def test_modal_config_error(self):
        """Test ModalConfigError is defined."""
        from app.services.modal_client import ModalConfigError
        
        error = ModalConfigError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, RuntimeError)

    def test_serialize_image_none(self):
        """Test serializing None image."""
        from app.services.modal_client import _serialize_image
        
        result, fmt = _serialize_image(None)
        assert result is None
        assert fmt is None

    def test_serialize_image_pil(self):
        """Test serializing PIL image."""
        from PIL import Image
        from app.services.modal_client import _serialize_image
        
        img = Image.new('RGB', (100, 100), color='red')
        result, fmt = _serialize_image(img)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert fmt == "PNG"
        assert len(result) > 0

    def test_serialize_image_base64(self):
        """Test serializing base64 data URL."""
        from PIL import Image
        from app.services.modal_client import _serialize_image
        
        # Create a base64 data URL
        img = Image.new('RGB', (50, 50), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        b64_data = base64.b64encode(buffer.getvalue()).decode()
        data_url = f"data:image/png;base64,{b64_data}"
        
        result, fmt = _serialize_image(data_url)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert fmt == "PNG"

    def test_serialize_image_file_path(self, tmp_path):
        """Test serializing image from file path."""
        from PIL import Image
        from app.services.modal_client import _serialize_image
        
        # Create temp image file
        img_path = tmp_path / "test.png"
        img = Image.new('RGB', (50, 50), color='green')
        img.save(img_path)
        
        result, fmt = _serialize_image(str(img_path))
        
        assert result is not None
        assert isinstance(result, bytes)
        assert fmt == "PNG"

    def test_serialize_image_file_not_found(self):
        """Test serializing non-existent file raises error."""
        from app.services.modal_client import _serialize_image
        
        with pytest.raises(FileNotFoundError):
            _serialize_image("/nonexistent/path/image.png")

    def test_serialize_image_invalid_type(self):
        """Test serializing invalid type raises error."""
        from app.services.modal_client import _serialize_image
        
        with pytest.raises(ValueError):
            _serialize_image(12345)  # Invalid type

    def test_load_pil_image_none_returns_placeholder(self):
        """Test loading None returns placeholder image."""
        from PIL import Image
        from app.services.modal_client import _load_pil_image
        
        result = _load_pil_image(None)
        
        assert isinstance(result, Image.Image)
        assert result.size == (336, 336)
        assert result.mode == "RGB"

    def test_load_pil_image_pil(self):
        """Test loading PIL image returns same image."""
        from PIL import Image
        from app.services.modal_client import _load_pil_image
        
        img = Image.new('RGB', (100, 100), color='red')
        result = _load_pil_image(img)
        
        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"

    def test_preprocess_image_for_llava(self):
        """Test LLaVA image preprocessing."""
        from PIL import Image
        from app.services.modal_client import _preprocess_image_for_llava
        
        img = Image.new('RGB', (100, 100), color='red')
        result, fmt = _preprocess_image_for_llava(img, target_size=336)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert fmt == "PNG"

    def test_preprocess_image_for_llava_non_square(self):
        """Test LLaVA preprocessing pads non-square images."""
        from PIL import Image
        from app.services.modal_client import _preprocess_image_for_llava
        
        # Non-square image
        img = Image.new('RGB', (200, 100), color='blue')
        result, fmt = _preprocess_image_for_llava(img, target_size=336)
        
        assert result is not None
        assert isinstance(result, bytes)

    def test_preprocess_image_for_llava_none_input(self):
        """Test LLaVA preprocessing with None creates placeholder."""
        from app.services.modal_client import _preprocess_image_for_llava
        
        result, fmt = _preprocess_image_for_llava(None, target_size=336)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert fmt == "PNG"

    def test_ensure_modal_credentials_missing(self, monkeypatch):
        """Test credential check raises error when missing."""
        from app.services.modal_client import _ensure_modal_credentials, ModalConfigError
        
        monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
        monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
        
        with pytest.raises(ModalConfigError):
            _ensure_modal_credentials()

    def test_ensure_modal_credentials_present(self, monkeypatch):
        """Test credential check passes when present."""
        from app.services.modal_client import _ensure_modal_credentials
        
        monkeypatch.setenv("MODAL_TOKEN_ID", "test_id")
        monkeypatch.setenv("MODAL_TOKEN_SECRET", "test_secret")
        
        # Should not raise
        _ensure_modal_credentials()


# ============================================================================
# RAG Service Tests
# ============================================================================
class TestRAGService:
    """Test RAG service functionality."""

    def test_retrieve_context_rag_disabled(self, monkeypatch):
        """Test retrieve_context returns empty when RAG disabled."""
        monkeypatch.setenv("ENABLE_RAG", "false")
        
        # Need to reload module to pick up env change
        import importlib
        from app.services import rag_service
        importlib.reload(rag_service)
        
        result = rag_service.retrieve_context(prompt="test query")
        
        assert isinstance(result, dict)
        assert result["used"] is False
        assert result["context"] == ""
        assert result["results"] == []

    def test_prepare_image_source_none(self):
        """Test _prepare_image_source with no image."""
        from app.services.rag_service import _prepare_image_source
        
        source, cleanup = _prepare_image_source(None, None)
        
        assert source is None
        assert cleanup is None

    def test_prepare_image_source_pil_image(self):
        """Test _prepare_image_source with PIL image."""
        from PIL import Image
        from app.services.rag_service import _prepare_image_source
        
        img = Image.new('RGB', (100, 100), color='red')
        source, cleanup = _prepare_image_source(img, None)
        
        assert source is not None
        assert os.path.exists(source)
        assert cleanup is not None
        
        # Cleanup
        if cleanup:
            cleanup()

    def test_prepare_image_source_base64(self):
        """Test _prepare_image_source with base64 data URL."""
        from PIL import Image
        from app.services.rag_service import _prepare_image_source
        
        # Create base64 data URL
        img = Image.new('RGB', (50, 50), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        b64_data = base64.b64encode(buffer.getvalue()).decode()
        data_url = f"data:image/png;base64,{b64_data}"
        
        source, cleanup = _prepare_image_source(None, data_url)
        
        assert source is not None
        assert os.path.exists(source)
        
        # Cleanup
        if cleanup:
            cleanup()

    def test_prepare_image_source_file_path(self, tmp_path):
        """Test _prepare_image_source with file path."""
        from PIL import Image
        from app.services.rag_service import _prepare_image_source
        
        # Create temp image
        img_path = tmp_path / "test.png"
        img = Image.new('RGB', (50, 50), color='green')
        img.save(img_path)
        
        source, cleanup = _prepare_image_source(None, str(img_path))
        
        assert source == str(img_path)
        assert cleanup is None

    def test_retrieve_similar_context_fallback(self, monkeypatch):
        """Test retrieve_similar_context fallback behavior."""
        monkeypatch.setenv("ENABLE_RAG", "false")
        
        import importlib
        from app.services import rag_service
        importlib.reload(rag_service)
        
        with patch.object(rag_service, 'get_all_prompts', return_value=[]):
            result = rag_service.retrieve_similar_context("test")
            
            assert isinstance(result, list)
            assert len(result) > 0
            assert "text" in result[0]

    def test_ensure_google_credentials_uses_fallback(self, tmp_path, monkeypatch):
        """Test _ensure_google_credentials uses RAG key fallback."""
        from app.services import rag_service

        key_file = tmp_path / "key.json"
        key_file.write_text("{}")

        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        monkeypatch.setattr(rag_service, "RAG_DIR", tmp_path)

        creds_path = rag_service._ensure_google_credentials()
        assert creds_path == str(key_file)

    def test_ensure_google_credentials_missing_raises(self, monkeypatch):
        """Test _ensure_google_credentials raises when no creds available."""
        from app.services import rag_service

        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        monkeypatch.setattr(rag_service, "RAG_DIR", None)

        with pytest.raises(RuntimeError):
            rag_service._ensure_google_credentials()


# ============================================================================
# DB Service Tests
# ============================================================================
class TestDBService:
    """Test database service functionality."""

    @pytest.fixture
    def mock_collection(self):
        """Mock MongoDB collection."""
        mock_coll = Mock()
        mock_coll.insert_one = Mock()
        mock_coll.find = Mock(return_value=Mock(
            sort=Mock(return_value=Mock(
                limit=Mock(return_value=[])
            ))
        ))
        return mock_coll

    def test_add_record(self, mock_collection, monkeypatch):
        """Test adding a record to database."""
        from app.services import db_service
        
        # Patch the collection
        monkeypatch.setattr(db_service, 'collection', mock_collection)
        
        db_service.add_record(
            user_id="test_user",
            prompt="make a cube",
            cad_code="import cadquery as cq",
            gcs_uri=None,
            image_uri=None,
            input_type="text"
        )
        
        mock_collection.insert_one.assert_called_once()
        call_args = mock_collection.insert_one.call_args[0][0]
        assert call_args["user_id"] == "test_user"
        assert call_args["prompt"] == "make a cube"
        assert call_args["input_type"] == "text"

    def test_get_history(self, mock_collection, monkeypatch):
        """Test getting history from database."""
        from app.services import db_service
        
        # Setup mock to return sample data
        mock_cursor = Mock()
        mock_cursor.sort = Mock(return_value=mock_cursor)
        mock_cursor.limit = Mock(return_value=[
            {"_id": Mock(__str__=lambda x: "123"), "prompt": "test", "cad_code": "code"}
        ])
        mock_collection.find = Mock(return_value=mock_cursor)
        
        monkeypatch.setattr(db_service, 'collection', mock_collection)
        
        result = db_service.get_history(limit=5)
        
        assert isinstance(result, list)
        mock_collection.find.assert_called_once()

    def test_get_all_prompts(self, mock_collection, monkeypatch):
        """Test getting all prompts from database."""
        from app.services import db_service
        
        mock_cursor = Mock()
        mock_cursor.sort = Mock(return_value=mock_cursor)
        mock_cursor.limit = Mock(return_value=[
            {"prompt": "test prompt", "cad_code": "test code"}
        ])
        mock_collection.find = Mock(return_value=mock_cursor)
        
        monkeypatch.setattr(db_service, 'collection', mock_collection)
        
        result = db_service.get_all_prompts(limit=100)
        
        assert isinstance(result, list)

    def test_get_history_images(self, mock_collection, monkeypatch):
        """Test getting image history from database."""
        from app.services import db_service
        
        mock_cursor = Mock()
        mock_cursor.sort = Mock(return_value=mock_cursor)
        mock_cursor.limit = Mock(return_value=[])
        mock_collection.find = Mock(return_value=mock_cursor)
        
        monkeypatch.setattr(db_service, 'collection', mock_collection)
        
        result = db_service.get_history_images(limit=10)
        
        assert isinstance(result, list)
        # Should filter by image_uri not None
        call_args = mock_collection.find.call_args[0][0]
        assert "image_uri" in call_args


# ============================================================================
# Auth Service Tests
# ============================================================================
class TestAuthService:
    """Test authentication service."""

    def test_verify_google_token_invalid(self):
        """Test verifying invalid Google token."""
        from app.services.auth_service import verify_google_token
        
        # Should return error dict for invalid token
        result = verify_google_token("invalid_token")
        
        # Returns dict with error key for invalid tokens
        assert isinstance(result, dict)
        assert "error" in result


# ============================================================================
# Utils Tests
# ============================================================================
class TestUtils:
    """Test utility functions."""

    def test_setup_logging(self):
        """Test logging setup."""
        from app.services.utils import setup_logging
        
        # Should not raise
        setup_logging()

    def test_ensure_env_vars_present(self, monkeypatch):
        """Test ensure_env_vars passes when vars present."""
        from app.services.utils import ensure_env_vars
        
        monkeypatch.setenv("TEST_VAR", "value")
        
        # Should not raise
        ensure_env_vars("TEST_VAR")

    def test_ensure_env_vars_missing(self, monkeypatch):
        """Test ensure_env_vars raises when vars missing."""
        from app.services.utils import ensure_env_vars
        
        monkeypatch.delenv("MISSING_VAR", raising=False)
        
        with pytest.raises(EnvironmentError):
            ensure_env_vars("MISSING_VAR")

    def test_init_environment(self):
        """Test init_environment runs without error."""
        from app.services.utils import init_environment
        
        # Should not raise
        init_environment()


# ============================================================================
# Pipeline Service Tests
# ============================================================================
class TestPipelineService:
    """Test pipeline service functionality."""

    def test_run_stage_returns_dict(self):
        """Test run_stage returns expected structure."""
        from app.services.pipeline_service import run_stage
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout="success output", returncode=0)
            result = run_stage("test_stage")
        
        assert isinstance(result, dict)
        assert "stage" in result
        assert "status" in result

    def test_run_stage_error_handling(self):
        """Test run_stage handles subprocess errors."""
        from app.services.pipeline_service import run_stage
        import subprocess
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1, cmd="test", stderr="error message"
            )
            result = run_stage("test_stage")
        
        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "error" in result


# ============================================================================
# GCS Service Tests
# ============================================================================
class TestGCSService:
    """Test Google Cloud Storage helper."""

    def test_upload_cad_code_without_credentials(self, monkeypatch):
        """Should fall back to local path when creds missing."""
        from app.services import gcs_service

        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        monkeypatch.setattr(gcs_service.os.path, "exists", lambda _: False)

        result = gcs_service.upload_cad_code("test prompt", "print('hi')")
        assert result.startswith("local://test_prompt")

    def test_upload_cad_code_with_credentials(self, tmp_path, monkeypatch):
        """Should attempt upload when credentials exist."""
        from app.services import gcs_service

        cred_path = tmp_path / "creds.json"
        cred_path.write_text("{}")

        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(cred_path))
        monkeypatch.setattr(gcs_service, "BUCKET_NAME", "unit-test-bucket")
        monkeypatch.setattr(gcs_service.os.path, "exists", lambda path: Path(path).exists())

        mock_blob = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_client = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        mock_storage = MagicMock()
        mock_storage.Client.return_value = mock_client
        monkeypatch.setattr(gcs_service, "storage", mock_storage)

        result = gcs_service.upload_cad_code("test prompt", "import cadquery as cq")

        assert result.startswith("gs://unit-test-bucket/generated/test_prompt.py")
        mock_bucket.blob.assert_called_once()
        mock_blob.upload_from_filename.assert_called_once()


# ============================================================================
# Logger Service Tests
# ============================================================================
class TestLoggerService:
    """Test logger utility."""

    def test_get_logger_writes_file(self, tmp_path, monkeypatch):
        """Ensure logger writes to configured log file without duplicate handlers."""
        monkeypatch.setenv("LOG_PATH", str(tmp_path / "test.log"))
        from app.services import logger as logger_module

        importlib.reload(logger_module)

        logger_instance = logger_module.get_logger("test_logger")
        logger_instance.info("hello world")

        log_file = tmp_path / "test.log"
        assert log_file.exists()
        contents = log_file.read_text()
        assert "hello world" in contents

        second_instance = logger_module.get_logger("test_logger")
        assert len(logger_instance.handlers) == len(second_instance.handlers)
