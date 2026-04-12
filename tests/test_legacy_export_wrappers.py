from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_build_knowledge_graph_cli_prints_deprecated_message():
    result = subprocess.run(
        [sys.executable, "scripts/build_knowledge_graph.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Deprecated entrypoint: use scripts/build_dashboard_graph_data.py" in result.stdout


def test_ttl_to_json_cli_supports_real_legacy_input(tmp_path: Path):
    ttl_file = tmp_path / "legacy.ttl"
    output_dir = tmp_path / "out"
    ttl_file.write_text(
        """
@prefix ex: <http://example.org/> .

ex:Shipment1 a ex:Shipment ;
    ex:hasIssue ex:Issue1 .

ex:Issue1 a ex:LogisticsIssue ;
    ex:name "Port Delay" .
""".strip(),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ttl_to_json.py",
            str(ttl_file),
            str(output_dir),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Deprecated entrypoint: use scripts/build_dashboard_graph_data.py" in result.stdout
    assert (output_dir / "nodes.json").exists()
    assert (output_dir / "edges.json").exists()
