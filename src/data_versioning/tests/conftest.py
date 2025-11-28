"""Pytest configuration and fixtures for data versioning tests."""
import pytest
import tempfile
from pathlib import Path
from PIL import Image


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_raw_data(temp_dir):
    """Create sample raw data structure for testing."""
    # Create directory structure
    raw_dir = temp_dir / "raw_data" / "test"
    raw_dir.mkdir(parents=True)
    
    # Create sample PNG and PY files
    for i in range(3):
        # Create image
        img = Image.new('RGB', (100, 100), color=(i * 50, i * 50, i * 50))
        img.save(raw_dir / f"test_{i}.png")
        
        # Create code file
        code = f'import cadquery as cq\nresult = cq.Workplane("XY").box({i+1}, {i+1}, {i+1})'
        (raw_dir / f"test_{i}.py").write_text(code)
    
    return temp_dir


@pytest.fixture
def sample_jsonl_data(temp_dir):
    """Create sample JSONL data for testing."""
    import json
    
    v1_dir = temp_dir / "v1"
    v1_dir.mkdir(parents=True)
    
    records = [
        {
            "question_id": "test_0",
            "image": "test_0.png",
            "text": "Generate CAD code",
            "category": "default",
            "ground_truth": "import cadquery as cq\nresult = cq.box(1,1,1)"
        },
        {
            "question_id": "test_1",
            "image": "test_1.png",
            "text": "Generate CAD code",
            "category": "default",
            "ground_truth": "import cadquery as cq\nresult = cq.sphere(1)"
        }
    ]
    
    jsonl_file = v1_dir / "test.jsonl"
    with open(jsonl_file, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
    
    return v1_dir

