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

    def test_serialize_image_base64_invalid(self):
        """Test serializing invalid base64 data URL raises error."""
        from app.services.modal_client import _serialize_image
        
        with pytest.raises(ValueError):
            _serialize_image("data:image/png;base64,invalid_base64_data!!!")

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

    def test_serialize_image_file_path_pathlib(self, tmp_path):
        """Test serializing image from Path object."""
        from PIL import Image
        from app.services.modal_client import _serialize_image
        
        img_path = tmp_path / "test.png"
        img = Image.new('RGB', (50, 50), color='green')
        img.save(img_path)
        
        result, fmt = _serialize_image(img_path)
        
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

    def test_load_pil_image_base64(self):
        """Test loading PIL image from base64 data URL."""
        from PIL import Image
        from app.services.modal_client import _load_pil_image
        
        img = Image.new('RGB', (50, 50), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        b64_data = base64.b64encode(buffer.getvalue()).decode()
        data_url = f"data:image/png;base64,{b64_data}"
        
        result = _load_pil_image(data_url)
        
        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"

    def test_load_pil_image_file_path(self, tmp_path):
        """Test loading PIL image from file path."""
        from PIL import Image
        from app.services.modal_client import _load_pil_image
        
        img_path = tmp_path / "test.png"
        img = Image.new('RGB', (50, 50), color='green')
        img.save(img_path)
        
        result = _load_pil_image(str(img_path))
        
        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"

    def test_load_pil_image_invalid_base64(self):
        """Test loading invalid base64 raises error."""
        from app.services.modal_client import _load_pil_image
        
        with pytest.raises(ValueError):
            _load_pil_image("data:image/png;base64,invalid!!!")

    def test_load_pil_image_file_not_found(self):
        """Test loading non-existent file raises error."""
        from app.services.modal_client import _load_pil_image
        
        with pytest.raises(FileNotFoundError):
            _load_pil_image("/nonexistent/path/image.png")

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

    def test_preprocess_image_for_llava_wide_image(self):
        """Test LLaVA preprocessing pads wide images."""
        from PIL import Image
        from app.services.modal_client import _preprocess_image_for_llava
        
        # Wide image (width > height)
        img = Image.new('RGB', (300, 150), color='yellow')
        result, fmt = _preprocess_image_for_llava(img, target_size=336)
        
        assert result is not None
        assert isinstance(result, bytes)

    def test_preprocess_image_for_llava_tall_image(self):
        """Test LLaVA preprocessing pads tall images."""
        from PIL import Image
        from app.services.modal_client import _preprocess_image_for_llava
        
        # Tall image (height > width)
        img = Image.new('RGB', (150, 300), color='purple')
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

    def test_ensure_modal_credentials_partial(self, monkeypatch):
        """Test credential check raises error when only one token present."""
        from app.services.modal_client import _ensure_modal_credentials, ModalConfigError
        
        monkeypatch.setenv("MODAL_TOKEN_ID", "test_id")
        monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
        
        with pytest.raises(ModalConfigError):
            _ensure_modal_credentials()

    @pytest.mark.asyncio
    async def test_run_modal_qwen_inference_mocked(self, monkeypatch):
        """Test Qwen Modal inference with mocked function."""
        from app.services.modal_client import run_modal_qwen_inference
        
        mock_fn_handle = MagicMock()
        mock_fn_handle.remote.return_value = "import cadquery as cq\nresult = cq.Workplane('XY').sphere(0.5)"
        
        monkeypatch.setenv("MODAL_TOKEN_ID", "test_id")
        monkeypatch.setenv("MODAL_TOKEN_SECRET", "test_secret")
        monkeypatch.setenv("QWEN_MODAL_APP", "test-app")
        monkeypatch.setenv("QWEN_MODAL_FUNCTION", "test-fn")
        
        with patch('app.services.modal_client._lookup_qwen_modal_function', return_value=mock_fn_handle):
            result = await run_modal_qwen_inference(
                prompt="make a sphere",
                image=None,
                max_new_tokens=128,
                temperature=0.0
            )
            
            assert isinstance(result, str)
            assert "cadquery" in result.lower()

    @pytest.mark.asyncio
    async def test_run_modal_llava_inference_mocked(self, monkeypatch):
        """Test LLaVA Modal inference with mocked function."""
        from PIL import Image
        from app.services.modal_client import run_modal_llava_inference
        
        mock_fn_handle = MagicMock()
        mock_fn_handle.remote.return_value = "import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)"
        
        monkeypatch.setenv("MODAL_TOKEN_ID", "test_id")
        monkeypatch.setenv("MODAL_TOKEN_SECRET", "test_secret")
        monkeypatch.setenv("LLAVA_MODAL_APP", "test-app")
        monkeypatch.setenv("LLAVA_MODAL_FUNCTION", "test-fn")
        
        test_image = Image.new('RGB', (100, 100), color='red')
        
        with patch('app.services.modal_client._lookup_llava_modal_function', return_value=mock_fn_handle):
            result = await run_modal_llava_inference(
                prompt="make a cube",
                image=test_image,
                max_new_tokens=128,
                temperature=0.0,
                top_p=1.0
            )
            
            assert isinstance(result, str)
            assert "cadquery" in result.lower()

    def test_lookup_qwen_modal_function_missing_credentials(self, monkeypatch):
        """Test Qwen Modal lookup raises error when credentials missing."""
        from app.services.modal_client import _lookup_qwen_modal_function, ModalConfigError
        
        # Remove Modal credentials to trigger ModalConfigError
        monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
        monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
        
        # Clear cache if it exists
        try:
            _lookup_qwen_modal_function.cache_clear()
        except AttributeError:
            pass  # Cache may not exist yet
        
        with pytest.raises(ModalConfigError):
            _lookup_qwen_modal_function()

    def test_lookup_llava_modal_function_missing_credentials(self, monkeypatch):
        """Test LLaVA Modal lookup raises error when credentials missing."""
        from app.services.modal_client import _lookup_llava_modal_function, ModalConfigError
        
        # Remove Modal credentials to trigger ModalConfigError
        monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
        monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
        
        # Clear cache if it exists
        try:
            _lookup_llava_modal_function.cache_clear()
        except AttributeError:
            pass  # Cache may not exist yet
        
        with pytest.raises(ModalConfigError):
            _lookup_llava_modal_function()


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

    def test_retrieve_similar_context_with_prompts(self, monkeypatch):
        """Test retrieve_similar_context with database prompts."""
        monkeypatch.setenv("ENABLE_RAG", "false")
        
        import importlib
        from app.services import rag_service
        importlib.reload(rag_service)
        
        mock_prompts = [
            {"prompt": "make a cube"},
            {"prompt": "create a sphere"},
            {"prompt": "build a cylinder"}
        ]
        
        with patch.object(rag_service, 'get_all_prompts', return_value=mock_prompts):
            result = rag_service.retrieve_similar_context("test", top_k=2)
            
            assert isinstance(result, list)
            assert len(result) <= 2
            assert "text" in result[0]

    def test_retrieve_context_with_image(self, monkeypatch):
        """Test retrieve_context with PIL image."""
        from PIL import Image
        monkeypatch.setenv("ENABLE_RAG", "false")
        
        import importlib
        from app.services import rag_service
        importlib.reload(rag_service)
        
        img = Image.new('RGB', (100, 100), color='red')
        result = rag_service.retrieve_context(prompt="test query", image=img)
        
        assert isinstance(result, dict)
        assert result["used"] is False
        assert result["context"] == ""
        assert result["results"] == []

    def test_retrieve_context_with_image_reference(self, monkeypatch):
        """Test retrieve_context with image reference."""
        monkeypatch.setenv("ENABLE_RAG", "false")
        
        import importlib
        from app.services import rag_service
        importlib.reload(rag_service)
        
        result = rag_service.retrieve_context(
            prompt="test query",
            image_reference="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        assert isinstance(result, dict)
        assert result["used"] is False

    def test_retrieve_context_with_file_path(self, tmp_path, monkeypatch):
        """Test retrieve_context with file path."""
        from PIL import Image
        monkeypatch.setenv("ENABLE_RAG", "false")
        
        import importlib
        from app.services import rag_service
        importlib.reload(rag_service)
        
        img_path = tmp_path / "test.png"
        img = Image.new('RGB', (50, 50), color='green')
        img.save(img_path)
        
        result = rag_service.retrieve_context(
            prompt="test query",
            image_reference=str(img_path)
        )
        
        assert isinstance(result, dict)
        assert result["used"] is False

    def test_write_temp_image_from_pil(self):
        """Test _write_temp_image_from_pil creates temp file."""
        from PIL import Image
        from app.services.rag_service import _write_temp_image_from_pil
        
        img = Image.new('RGB', (100, 100), color='red')
        temp_path, cleanup = _write_temp_image_from_pil(img)
        
        assert os.path.exists(temp_path)
        assert cleanup is not None
        
        # Cleanup
        cleanup()
        assert not os.path.exists(temp_path)

    def test_write_temp_image_from_base64(self):
        """Test _write_temp_image_from_base64 creates temp file."""
        from PIL import Image
        from app.services.rag_service import _write_temp_image_from_base64
        
        img = Image.new('RGB', (50, 50), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        b64_data = base64.b64encode(buffer.getvalue()).decode()
        data_url = f"data:image/png;base64,{b64_data}"
        
        temp_path, cleanup = _write_temp_image_from_base64(data_url)
        
        assert os.path.exists(temp_path)
        assert cleanup is not None
        
        # Cleanup
        cleanup()
        assert not os.path.exists(temp_path)

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

    def test_find_rag_dir_from_env(self, tmp_path, monkeypatch):
        """Test _find_rag_dir uses RAG_DIR environment variable."""
        from app.services import rag_service
        
        test_dir = tmp_path / "custom_rag"
        test_dir.mkdir()
        monkeypatch.setenv("RAG_DIR", str(test_dir))
        
        # Reload module to pick up env var
        import importlib
        importlib.reload(rag_service)
        
        result = rag_service._find_rag_dir()
        assert result == test_dir

    def test_get_retriever_rag_enabled_with_import_error(self, monkeypatch):
        """Test _get_retriever when RAG enabled but import fails."""
        from app.services import rag_service
        
        monkeypatch.setenv("ENABLE_RAG", "true")
        monkeypatch.setattr(rag_service, "MultimodalRAGRetriever", None)
        monkeypatch.setattr(rag_service, "_IMPORT_ERROR", Exception("Import failed"))
        
        import importlib
        importlib.reload(rag_service)
        
        result = rag_service._get_retriever()
        assert result is None

    def test_get_retriever_rag_dir_not_found(self, monkeypatch):
        """Test _get_retriever when RAG_DIR is None."""
        from app.services import rag_service
        
        monkeypatch.setenv("ENABLE_RAG", "true")
        monkeypatch.setattr(rag_service, "RAG_DIR", None)
        
        result = rag_service._get_retriever()
        assert result is None

    def test_prepare_image_source_with_pil_image(self):
        """Test _prepare_image_source with PIL Image."""
        from PIL import Image
        from app.services.rag_service import _prepare_image_source
        
        img = Image.new('RGB', (100, 100), color='red')
        path, cleanup = _prepare_image_source(img, None)
        
        assert path is not None
        assert cleanup is not None
        assert os.path.exists(path)
        
        # Cleanup
        cleanup()
        assert not os.path.exists(path)

    def test_prepare_image_source_with_base64_reference(self):
        """Test _prepare_image_source with base64 data URL."""
        from PIL import Image
        from app.services.rag_service import _prepare_image_source
        
        img = Image.new('RGB', (50, 50), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        b64_data = base64.b64encode(buffer.getvalue()).decode()
        data_url = f"data:image/png;base64,{b64_data}"
        
        path, cleanup = _prepare_image_source(None, data_url)
        
        assert path is not None
        assert cleanup is not None
        assert os.path.exists(path)
        
        # Cleanup
        cleanup()
        assert not os.path.exists(path)

    def test_prepare_image_source_with_file_path(self, tmp_path):
        """Test _prepare_image_source with existing file path."""
        from PIL import Image
        from app.services.rag_service import _prepare_image_source
        
        img_path = tmp_path / "test.png"
        img = Image.new('RGB', (50, 50), color='green')
        img.save(img_path)
        
        path, cleanup = _prepare_image_source(None, str(img_path))
        
        assert path == str(img_path)
        assert cleanup is None

    def test_prepare_image_source_with_remote_path(self):
        """Test _prepare_image_source with remote/GCS path."""
        from app.services.rag_service import _prepare_image_source
        
        path, cleanup = _prepare_image_source(None, "gs://bucket/path/to/image.png")
        
        assert path == "gs://bucket/path/to/image.png"
        assert cleanup is None

    def test_retrieve_similar_context_with_rag_enabled(self, monkeypatch):
        """Test retrieve_similar_context when RAG is enabled."""
        from app.services import rag_service
        
        mock_retriever = Mock()
        mock_result = Mock()
        mock_result.to_dict.return_value = {"text": "Example CAD code"}
        mock_retriever.query_text.return_value = [mock_result]
        mock_retriever.get_rag_context.return_value = "Example context"
        
        monkeypatch.setenv("ENABLE_RAG", "true")
        monkeypatch.setattr(rag_service, "_get_retriever", lambda: mock_retriever)
        
        result = rag_service.retrieve_similar_context("test prompt", top_k=3)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["text"] == "Example CAD code"

    def test_retrieve_similar_context_fallback_to_db(self, monkeypatch):
        """Test retrieve_similar_context falls back to DB when RAG disabled."""
        from app.services import rag_service
        
        monkeypatch.setenv("ENABLE_RAG", "false")
        
        with patch('app.services.rag_service.get_all_prompts') as mock_db:
            mock_db.return_value = [
                {"prompt": "make a cube"},
                {"prompt": "create a sphere"},
                {"prompt": "build a cylinder"}
            ]
            
            result = rag_service.retrieve_similar_context("test", top_k=2)
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert all("text" in item for item in result)

    def test_retrieve_similar_context_empty_db(self, monkeypatch):
        """Test retrieve_similar_context with empty database."""
        from app.services import rag_service
        
        monkeypatch.setenv("ENABLE_RAG", "false")
        
        with patch('app.services.rag_service.get_all_prompts') as mock_db:
            mock_db.return_value = []
            
            result = rag_service.retrieve_similar_context("test")
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["text"] == "No context available"

    def test_retrieve_context_exception_handling(self, monkeypatch):
        """Test retrieve_context handles exceptions gracefully."""
        from app.services import rag_service
        
        mock_retriever = Mock()
        mock_retriever.query_text.side_effect = Exception("RAG query failed")
        mock_retriever.get_rag_context.return_value = None
        
        monkeypatch.setenv("ENABLE_RAG", "true")
        monkeypatch.setattr(rag_service, "_get_retriever", lambda: mock_retriever)
        
        result = rag_service.retrieve_context("test prompt")
        
        assert isinstance(result, dict)
        assert result["used"] is False
        assert result["context"] == ""
        assert result["results"] == []

    def test_retrieve_context_with_multimodal_query(self, monkeypatch):
        """Test retrieve_context with image uses multimodal query."""
        from PIL import Image
        from app.services import rag_service
        
        mock_retriever = Mock()
        mock_result = Mock()
        mock_result.to_dict.return_value = {"text": "Example"}
        mock_retriever.query_multimodal.return_value = [mock_result]
        mock_retriever.get_rag_context.return_value = "Context"
        
        monkeypatch.setenv("ENABLE_RAG", "true")
        monkeypatch.setattr(rag_service, "_get_retriever", lambda: mock_retriever)
        
        img = Image.new('RGB', (100, 100), color='red')
        result = rag_service.retrieve_context("test", image=img)
        
        assert result["used"] is True
        assert result["context"] == "Context"
        mock_retriever.query_multimodal.assert_called_once()


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

    def test_verify_google_token_success(self, monkeypatch):
        """Test verifying valid Google token."""
        from app.services.auth_service import verify_google_token
        
        mock_idinfo = {
            "email": "test@example.com",
            "name": "Test User",
            "sub": "123456789"
        }
        
        with patch('app.services.auth_service.id_token.verify_oauth2_token', return_value=mock_idinfo):
            result = verify_google_token("valid_token")
            
            assert isinstance(result, dict)
            assert result["email"] == "test@example.com"
            assert result["name"] == "Test User"
            assert result["sub"] == "123456789"
            assert "error" not in result

    def test_verify_google_token_value_error(self, monkeypatch):
        """Test verifying token raises ValueError."""
        from app.services.auth_service import verify_google_token
        
        with patch('app.services.auth_service.id_token.verify_oauth2_token', side_effect=ValueError("Invalid token")):
            result = verify_google_token("invalid_token")
            
            assert isinstance(result, dict)
            assert "error" in result
            assert "Invalid Google ID token" in result["error"]

    def test_verify_google_token_generic_exception(self, monkeypatch):
        """Test verifying token raises generic exception."""
        from app.services.auth_service import verify_google_token
        
        with patch('app.services.auth_service.id_token.verify_oauth2_token', side_effect=Exception("Network error")):
            result = verify_google_token("token")
            
            assert isinstance(result, dict)
            assert "error" in result
            assert "Network error" in result["error"]


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

    def test_ensure_env_vars_multiple_present(self, monkeypatch):
        """Test ensure_env_vars with multiple vars present."""
        from app.services.utils import ensure_env_vars
        
        monkeypatch.setenv("VAR1", "value1")
        monkeypatch.setenv("VAR2", "value2")
        
        # Should not raise
        ensure_env_vars("VAR1", "VAR2")

    def test_ensure_env_vars_missing(self, monkeypatch):
        """Test ensure_env_vars raises when vars missing."""
        from app.services.utils import ensure_env_vars
        
        monkeypatch.delenv("MISSING_VAR", raising=False)
        
        with pytest.raises(EnvironmentError):
            ensure_env_vars("MISSING_VAR")

    def test_ensure_env_vars_multiple_missing(self, monkeypatch):
        """Test ensure_env_vars raises when multiple vars missing."""
        from app.services.utils import ensure_env_vars
        
        monkeypatch.delenv("MISSING_VAR1", raising=False)
        monkeypatch.delenv("MISSING_VAR2", raising=False)
        
        with pytest.raises(EnvironmentError) as exc_info:
            ensure_env_vars("MISSING_VAR1", "MISSING_VAR2")
        
        assert "MISSING_VAR1" in str(exc_info.value)
        assert "MISSING_VAR2" in str(exc_info.value)

    def test_ensure_env_vars_partial_missing(self, monkeypatch):
        """Test ensure_env_vars raises when some vars missing."""
        from app.services.utils import ensure_env_vars
        
        monkeypatch.setenv("PRESENT_VAR", "value")
        monkeypatch.delenv("MISSING_VAR", raising=False)
        
        with pytest.raises(EnvironmentError) as exc_info:
            ensure_env_vars("PRESENT_VAR", "MISSING_VAR")
        
        assert "MISSING_VAR" in str(exc_info.value)

    def test_init_environment(self):
        """Test init_environment runs without error."""
        from app.services.utils import init_environment
        
        # Should not raise
        init_environment()

    def test_setup_logging_configures_logger(self):
        """Test setup_logging configures logging correctly."""
        import logging
        from app.services.utils import setup_logging
        
        # Clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers = []
        
        setup_logging()
        
        # Check that logging is configured
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) > 0

    def test_ensure_env_vars_empty_list(self):
        """Test ensure_env_vars with empty list."""
        from app.services.utils import ensure_env_vars
        
        # Should not raise
        ensure_env_vars()

    def test_ensure_env_vars_none_value(self, monkeypatch):
        """Test ensure_env_vars when env var is set to empty string."""
        from app.services.utils import ensure_env_vars
        
        monkeypatch.setenv("TEST_VAR", "")
        
        with pytest.raises(EnvironmentError):
            ensure_env_vars("TEST_VAR")


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

    def test_upload_cad_code_without_credentials_none_path(self, monkeypatch):
        """Should fall back to local path when creds path is None."""
        from app.services import gcs_service

        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        monkeypatch.setattr(gcs_service.os, "getenv", lambda key, default: "" if key == "GOOGLE_APPLICATION_CREDENTIALS" else default)
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

    def test_upload_cad_code_upload_exception(self, tmp_path, monkeypatch):
        """Should fall back to local path when upload fails."""
        from app.services import gcs_service

        cred_path = tmp_path / "creds.json"
        cred_path.write_text("{}")

        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(cred_path))
        monkeypatch.setattr(gcs_service, "BUCKET_NAME", "unit-test-bucket")
        monkeypatch.setattr(gcs_service.os.path, "exists", lambda path: Path(path).exists())

        mock_blob = MagicMock()
        mock_blob.upload_from_filename.side_effect = Exception("Upload failed")
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_client = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        mock_storage = MagicMock()
        mock_storage.Client.return_value = mock_client
        monkeypatch.setattr(gcs_service, "storage", mock_storage)

        result = gcs_service.upload_cad_code("test prompt", "import cadquery as cq")

        assert result.startswith("local://test_prompt")

    def test_upload_cad_code_client_exception(self, tmp_path, monkeypatch):
        """Should fall back to local path when client creation fails."""
        from app.services import gcs_service

        cred_path = tmp_path / "creds.json"
        cred_path.write_text("{}")

        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(cred_path))
        monkeypatch.setattr(gcs_service, "BUCKET_NAME", "unit-test-bucket")
        monkeypatch.setattr(gcs_service.os.path, "exists", lambda path: Path(path).exists())

        mock_storage = MagicMock()
        mock_storage.Client.side_effect = Exception("Client creation failed")
        monkeypatch.setattr(gcs_service, "storage", mock_storage)

        result = gcs_service.upload_cad_code("test prompt", "import cadquery as cq")

        assert result.startswith("local://test_prompt")


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

    def test_get_logger_default_name(self, tmp_path, monkeypatch):
        """Test logger with default name."""
        monkeypatch.setenv("LOG_PATH", str(tmp_path / "test.log"))
        from app.services import logger as logger_module

        importlib.reload(logger_module)

        logger_instance = logger_module.get_logger()
        logger_instance.info("test message")

        log_file = tmp_path / "test.log"
        assert log_file.exists()
        contents = log_file.read_text()
        assert "test message" in contents

    def test_get_logger_multiple_loggers(self, tmp_path, monkeypatch):
        """Test multiple logger instances."""
        monkeypatch.setenv("LOG_PATH", str(tmp_path / "test.log"))
        from app.services import logger as logger_module

        importlib.reload(logger_module)

        logger1 = logger_module.get_logger("logger1")
        logger2 = logger_module.get_logger("logger2")
        
        logger1.info("message1")
        logger2.info("message2")

        log_file = tmp_path / "test.log"
        assert log_file.exists()
        contents = log_file.read_text()
        assert "message1" in contents
        assert "message2" in contents

    def test_get_logger_different_levels(self, tmp_path, monkeypatch):
        """Test logger with different log levels."""
        log_file = tmp_path / "test_levels.log"
        monkeypatch.setenv("LOG_PATH", str(log_file))
        from app.services import logger as logger_module

        importlib.reload(logger_module)

        logger_instance = logger_module.get_logger("test_logger_levels")
        logger_instance.debug("debug message")
        logger_instance.info("info message")
        logger_instance.warning("warning message")
        logger_instance.error("error message")
        
        # Flush handlers to ensure all logs are written
        for handler in logger_instance.handlers:
            handler.flush()

        # File should be created after logging
        assert log_file.exists(), f"Log file not found at {log_file}"
        contents = log_file.read_text()
        assert "info message" in contents
        assert "warning message" in contents
        assert "error message" in contents

    def test_get_logger_no_duplicate_handlers(self, tmp_path, monkeypatch):
        """Test that calling get_logger multiple times doesn't add duplicate handlers."""
        monkeypatch.setenv("LOG_PATH", str(tmp_path / "test.log"))
        from app.services import logger as logger_module

        importlib.reload(logger_module)

        logger1 = logger_module.get_logger("test_logger")
        handler_count_1 = len(logger1.handlers)
        
        logger2 = logger_module.get_logger("test_logger")
        handler_count_2 = len(logger2.handlers)
        
        assert handler_count_1 == handler_count_2
        assert logger1 is logger2  # Should return same logger instance
