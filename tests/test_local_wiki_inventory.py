import json
import subprocess
import sys
from pathlib import Path

from scripts.local_wiki_inventory import (
    build_extension_queries,
    classify_candidate,
    write_inventory,
)


def test_build_extension_queries_contains_requested_formats():
    assert "*.pdf" in build_extension_queries()
    assert "*.docx" in build_extension_queries()
    assert "*.xlsx" in build_extension_queries()
    assert "*.md" in build_extension_queries()


def test_classify_candidate_excludes_appdata():
    status = classify_candidate({"path": "C:\\Users\\SAMSUNG\\AppData\\x.txt", "extension": ".txt"})
    assert status == {"status": "excluded", "reason": "high-risk path"}


def test_classify_candidate_queues_safe_pdf():
    status = classify_candidate(
        {
            "path": "C:\\Users\\SAMSUNG\\Documents\\a.pdf",
            "extension": ".pdf",
            "size": 100,
        }
    )
    assert status == {"status": "queued", "reason": "safe candidate"}


def test_write_inventory_outputs_latest_and_run(tmp_path):
    latest, run = write_inventory(
        {"candidates": []},
        output_root=tmp_path,
        timestamp="20260416-120000",
    )
    assert latest.exists()
    assert run.exists()
    assert json.loads(latest.read_text(encoding="utf-8")) == {"candidates": []}


def test_inventory_script_can_run_directly():
    result = subprocess.run(
        [sys.executable, str(Path("scripts/local_wiki_inventory.py")), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
