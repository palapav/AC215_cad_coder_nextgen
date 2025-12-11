"""CLI entry tests for data_versioning scripts to boost coverage."""
import sys
import json
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestCLIScripts:
    """Exercise CLI mains for coverage."""

    def test_convert_raw_main(self, tmp_path, monkeypatch):
        """Invoke convert_raw_to_jsonl.main with temp data."""
        from convert_raw_to_jsonl import main

        # Create raw data structure
        raw_dir = tmp_path / "data" / "raw_data" / "train"
        raw_dir.mkdir(parents=True)
        # Create one image/code pair
        img_path = raw_dir / "sample.png"
        code_path = raw_dir / "sample.py"
        img_path.write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal header; Pillow not required for this branch
        code_path.write_text("import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)")

        output_dir = tmp_path / "out"

        # Patch argv and run main
        monkeypatch.setattr(sys, "argv", ["convert_raw_to_jsonl.py", "--input-dir", str(tmp_path / "data"), "--output-dir", str(output_dir)])
        main()

        # Verify output exists
        assert (output_dir / "v1" / "train.jsonl").exists()

    def test_prepare_user_data_main(self, tmp_path, monkeypatch):
        """Invoke prepare_user_data.main to cover CLI path."""
        from prepare_user_data import main

        input_file = tmp_path / "subset.jsonl"
        output_file = tmp_path / "user_data.jsonl"

        with open(input_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "question_id": "q1",
                "text": "prompt",
                "ground_truth": "code",
                "image": "img.png"
            }) + "\n")

        monkeypatch.setattr(sys, "argv", ["prepare_user_data.py", "--input", str(input_file), "--output", str(output_file)])
        main()

        assert output_file.exists()
        lines = output_file.read_text().strip().splitlines()
        assert len(lines) == 1
        rec = json.loads(lines[0])
        assert rec["question_id"].startswith("user_")

    def test_create_v2_main(self, tmp_path, monkeypatch):
        """Invoke create_v2.main to cover CLI path."""
        from create_v2 import main

        v1_dir = tmp_path / "v1"
        v1_dir.mkdir()
        # Create simple v1 train file
        train_file = v1_dir / "train.jsonl"
        train_file.write_text(json.dumps({"question_id": "q1", "text": "p", "ground_truth": "c"}) + "\n")

        user_data = tmp_path / "user_data.jsonl"
        user_data.write_text(json.dumps({"question_id": "u1", "prompt": "p2", "llm_output": "c2"}) + "\n")

        output_dir = tmp_path / "v2"

        monkeypatch.setattr(sys, "argv", [
            "create_v2.py",
            "--v1-dir", str(v1_dir),
            "--user-data", str(user_data),
            "--output-dir", str(output_dir),
        ])
        main()

        # Verify v2 train exists and includes user record
        v2_train = output_dir / "train.jsonl"
        assert v2_train.exists()
        lines = v2_train.read_text().strip().splitlines()
        assert len(lines) == 2  # v1 + user

