"""Tests for RAG module components."""
import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfig:
    """Test RAG configuration."""

    def test_config_defaults(self):
        """Test that config has default values."""
        from rag.config import RETRY_ATTEMPTS, RETRY_DELAY, CHUNK_SIZE, CHUNK_OVERLAP
        
        assert RETRY_ATTEMPTS >= 1
        assert RETRY_DELAY >= 1
        assert CHUNK_SIZE > 0
        assert CHUNK_OVERLAP >= 0
        assert CHUNK_OVERLAP < CHUNK_SIZE

    def test_config_from_env(self, monkeypatch):
        """Test config reads from environment."""
        monkeypatch.setenv("RAG_RETRY_ATTEMPTS", "5")
        monkeypatch.setenv("RAG_CHUNK_SIZE", "1000")
        
        # Reload module to pick up env changes
        import importlib
        from rag import config
        importlib.reload(config)
        
        assert config.RETRY_ATTEMPTS == 5
        assert config.CHUNK_SIZE == 1000


class TestProcessingUtils:
    """Test processing utility functions."""

    def test_chunk_code_text_empty(self):
        """Test chunking empty text."""
        from rag.processing_utils import chunk_code_text
        
        result = chunk_code_text("")
        
        assert result == []

    def test_chunk_code_text_short(self):
        """Test chunking short text that fits in one chunk."""
        from rag.processing_utils import chunk_code_text
        
        text = "import cadquery as cq\nresult = cq.box(1,1,1)"
        result = chunk_code_text(text, chunk_size=500)
        
        assert len(result) == 1
        assert "import cadquery" in result[0]

    def test_chunk_code_text_long(self):
        """Test chunking long text into multiple chunks."""
        from rag.processing_utils import chunk_code_text
        
        # Create a long text
        lines = [f"line_{i} = value_{i}" for i in range(100)]
        text = "\n".join(lines)
        
        result = chunk_code_text(text, chunk_size=100, overlap=10)
        
        assert len(result) > 1

    def test_chunk_code_text_preserves_content(self):
        """Test that chunking preserves code content."""
        from rag.processing_utils import chunk_code_text
        
        text = "def foo():\n    return 42"
        result = chunk_code_text(text, chunk_size=500)
        
        assert "def foo():" in result[0]
        assert "return 42" in result[0]

    def test_retry_with_backoff_success(self):
        """Test retry succeeds on first attempt."""
        from rag.processing_utils import retry_with_backoff
        
        def successful_func():
            return "success"
        
        result = retry_with_backoff(successful_func, max_attempts=3, base_delay=0)
        
        assert result == "success"

    def test_retry_with_backoff_eventual_success(self):
        """Test retry succeeds after failures."""
        from rag.processing_utils import retry_with_backoff
        
        call_count = [0]
        
        def flaky_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = retry_with_backoff(flaky_func, max_attempts=3, base_delay=0)
        
        assert result == "success"
        assert call_count[0] == 3

    def test_retry_with_backoff_all_failures(self):
        """Test retry raises after all attempts fail."""
        from rag.processing_utils import retry_with_backoff
        
        def failing_func():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            retry_with_backoff(failing_func, max_attempts=2, base_delay=0)


class TestStorageUtils:
    """Test storage utility functions."""

    def test_storage_utils_import(self):
        """Test that storage_utils can be imported."""
        from rag import storage_utils
        
        assert storage_utils is not None


class TestEmbeddingGenerator:
    """Test embedding generator (mocked)."""

    def test_embedding_generator_import(self):
        """Test that embedding_generator can be imported."""
        from rag import embedding_generator
        
        assert embedding_generator is not None

