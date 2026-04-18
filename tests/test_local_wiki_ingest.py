import json
import subprocess
import sys
from pathlib import Path

from scripts.local_wiki_ingest import (
    IngestResult,
    ingest_candidates,
    load_queued_candidates,
    local_wiki_has_credential_pattern,
    normalize_extraction,
    order_candidates_for_copilot,
)


def test_load_queued_candidates_filters_status(tmp_path):
    path = tmp_path / "latest.json"
    path.write_text(
        json.dumps(
            {
                "candidates": [
                    {"path": "C:\\safe.txt", "status": "queued"},
                    {"path": "C:\\bad.txt", "status": "excluded"},
                ]
            }
        ),
        encoding="utf-8",
    )

    assert load_queued_candidates(path) == [{"path": "C:\\safe.txt", "status": "queued"}]


def test_normalize_extraction_creates_summary():
    result = normalize_extraction("C:\\safe.txt", "Alpha beta gamma\nSecond line", "ok")

    assert result["summary"].startswith("Alpha beta gamma")
    assert result["topics"] == ["local-file"]


def test_ingest_candidates_dry_run_does_not_write(tmp_path):
    source = tmp_path / "safe.txt"
    source.write_text("Alpha beta gamma", encoding="utf-8")
    writes = []

    results = ingest_candidates(
        [{"path": str(source), "status": "queued"}],
        vault_root=tmp_path / "vault",
        limit=1,
        dry_run=True,
        extract_document=lambda path: {
            "text": Path(path).read_text(encoding="utf-8"),
            "status": "ok",
        },
        write_wiki_note=lambda **kwargs: writes.append(kwargs),
    )

    assert results == [
        IngestResult(path=str(source), status="dry-run", reason="would write wiki note")
    ]
    assert writes == []


def test_ingest_candidates_dry_run_does_not_require_writer(tmp_path, monkeypatch):
    source = tmp_path / "safe.txt"
    source.write_text("Alpha beta gamma", encoding="utf-8")
    monkeypatch.setattr(
        "scripts.local_wiki_ingest._load_write_wiki_note",
        lambda: (_ for _ in ()).throw(AssertionError("writer loaded")),
    )

    results = ingest_candidates(
        [{"path": str(source), "status": "queued"}],
        vault_root=tmp_path / "vault",
        limit=1,
        dry_run=True,
        extract_document=lambda path: {
            "text": Path(path).read_text(encoding="utf-8"),
            "status": "ok",
        },
    )

    assert results == [
        IngestResult(path=str(source), status="dry-run", reason="would write wiki note")
    ]


def test_local_wiki_credential_guard_blocks_tokens_but_not_business_text():
    assert local_wiki_has_credential_pattern("api_key=abc123456") is True
    assert local_wiki_has_credential_pattern("Bearer abcdefghijklmnop") is True
    assert (
        local_wiki_has_credential_pattern(
            "Customer meeting notes include phone 010-1234-5678 and internal budget."
        )
        is False
    )


def test_ingest_candidates_skips_credential_text(tmp_path):
    source = tmp_path / "secret.txt"
    source.write_text("api_key=abc123456", encoding="utf-8")
    writes = []

    results = ingest_candidates(
        [{"path": str(source), "status": "queued"}],
        vault_root=tmp_path / "vault",
        limit=1,
        dry_run=False,
        extract_document=lambda path: {
            "text": Path(path).read_text(encoding="utf-8"),
            "status": "ok",
        },
        write_wiki_note=lambda **kwargs: writes.append(kwargs),
    )

    assert results == [
        IngestResult(path=str(source), status="skipped", reason="credential pattern")
    ]
    assert writes == []


def test_ingest_candidates_uses_copilot_normalizer_when_selected(tmp_path):
    source = tmp_path / "safe.txt"
    source.write_text("Alpha beta gamma", encoding="utf-8")
    writes = []
    seen = {}

    def fake_copilot_normalize(source_path, extraction):
        seen["source_path"] = source_path
        seen["extraction"] = extraction
        return {
            "title": "AI Title",
            "summary": "AI summary",
            "key_facts": ["AI fact"],
            "extracted_structure": ["AI structure"],
            "topics": ["ai-topic"],
            "entities": ["AI entity"],
            "projects": ["AI project"],
            "extraction_status": "ok",
        }

    results = ingest_candidates(
        [{"path": str(source), "status": "queued", "size": 10}],
        vault_root=tmp_path / "vault",
        limit=1,
        dry_run=False,
        normalizer="copilot",
        extract_document=lambda path: {
            "text": Path(path).read_text(encoding="utf-8"),
            "status": "ok",
        },
        copilot_normalize=fake_copilot_normalize,
        write_wiki_note=lambda **kwargs: writes.append(kwargs) or tmp_path / "note.md",
    )

    assert results == [
        IngestResult(
            path=str(source),
            status="written",
            reason="wiki note written",
            note_path=str(tmp_path / "note.md"),
        )
    ]
    assert seen["source_path"] == source
    assert seen["extraction"]["status"] == "ok"
    assert writes[0]["title"] == "AI Title"
    assert writes[0]["summary"] == "AI summary"
    assert writes[0]["topics"] == ["ai-topic"]


def test_ingest_candidates_prefers_cleaner_candidate_for_copilot(tmp_path):
    pdf = tmp_path / "rough.pdf"
    txt = tmp_path / "clean.txt"
    pdf.write_text("rough pdf text", encoding="utf-8")
    txt.write_text("clean text", encoding="utf-8")

    ordered = order_candidates_for_copilot(
        [
            {"path": str(pdf), "status": "queued"},
            {"path": str(txt), "status": "queued"},
        ]
    )

    assert [Path(candidate["path"]).suffix for candidate in ordered] == [".txt", ".pdf"]


def test_copilot_candidate_order_prefers_markdown_before_json_config(tmp_path):
    codex_config = tmp_path / ".codex" / "models_cache.json"
    markdown = tmp_path / "docs" / "note.md"
    codex_config.parent.mkdir()
    markdown.parent.mkdir()
    codex_config.write_text("{}", encoding="utf-8")
    markdown.write_text("# Note", encoding="utf-8")

    ordered = order_candidates_for_copilot(
        [
            {"path": str(codex_config), "status": "queued"},
            {"path": str(markdown), "status": "queued"},
        ]
    )

    assert ordered[0]["path"] == str(markdown)


def test_copilot_candidate_order_pushes_tool_config_paths_last(tmp_path):
    codex_config = tmp_path / ".codex" / "models_cache.json"
    workbook = tmp_path / "report.xlsx"
    codex_config.parent.mkdir()
    codex_config.write_text("{}", encoding="utf-8")
    workbook.write_text("workbook sample", encoding="utf-8")

    ordered = order_candidates_for_copilot(
        [
            {"path": str(codex_config), "status": "queued"},
            {"path": str(workbook), "status": "queued"},
        ]
    )

    assert ordered[0]["path"] == str(workbook)


def test_copilot_ingest_uses_cleaner_candidate_before_pdf(tmp_path):
    pdf = tmp_path / "rough.pdf"
    txt = tmp_path / "clean.txt"
    pdf.write_text("rough pdf text", encoding="utf-8")
    txt.write_text("clean text", encoding="utf-8")

    seen = []

    def fake_copilot_normalize(source_path, extraction):
        seen.append(source_path)
        return {
            "title": "AI Title",
            "summary": "AI summary",
            "key_facts": [],
            "extracted_structure": [],
            "topics": ["ai-topic"],
            "entities": [],
            "projects": [],
            "extraction_status": "ok",
        }

    results = ingest_candidates(
        [
            {"path": str(pdf), "status": "queued", "size": 10},
            {"path": str(txt), "status": "queued", "size": 10},
        ],
        vault_root=tmp_path / "vault",
        limit=1,
        dry_run=True,
        normalizer="copilot",
        extract_document=lambda path: {
            "text": Path(path).read_text(encoding="utf-8"),
            "status": "ok",
        },
        copilot_normalize=fake_copilot_normalize,
    )

    assert seen == [txt]
    assert results == [
        IngestResult(
            path=str(txt),
            status="dry-run",
            reason="would write wiki note; normalizer=copilot",
        )
    ]


def test_copilot_dry_run_tries_next_candidate_when_first_falls_back(tmp_path):
    first = tmp_path / "first.md"
    second = tmp_path / "second.txt"
    first.write_text("# First", encoding="utf-8")
    second.write_text("Second", encoding="utf-8")
    seen = []

    def flaky_copilot_normalize(source_path, extraction):
        seen.append(source_path)
        if source_path == first:
            raise RuntimeError("standalone 422")
        return {
            "title": "Second",
            "summary": "AI summary",
            "key_facts": [],
            "extracted_structure": [],
            "topics": ["ai-topic"],
            "entities": [],
            "projects": [],
            "extraction_status": "ok",
        }

    results = ingest_candidates(
        [
            {"path": str(first), "status": "queued", "size": 10},
            {"path": str(second), "status": "queued", "size": 10},
        ],
        vault_root=tmp_path / "vault",
        limit=1,
        dry_run=True,
        normalizer="copilot",
        extract_document=lambda path: {
            "text": Path(path).read_text(encoding="utf-8"),
            "status": "ok",
        },
        copilot_normalize=flaky_copilot_normalize,
    )

    assert seen == [first, second]
    assert results == [
        IngestResult(
            path=str(second),
            status="dry-run",
            reason="would write wiki note; normalizer=copilot",
        )
    ]


def test_ingest_candidates_falls_back_when_copilot_normalizer_fails(tmp_path):
    source = tmp_path / "safe.txt"
    source.write_text("Alpha beta gamma", encoding="utf-8")
    writes = []

    def failing_copilot_normalize(source_path, extraction):
        raise RuntimeError("standalone unavailable")

    results = ingest_candidates(
        [{"path": str(source), "status": "queued", "size": 10}],
        vault_root=tmp_path / "vault",
        limit=1,
        dry_run=False,
        normalizer="copilot",
        extract_document=lambda path: {
            "text": Path(path).read_text(encoding="utf-8"),
            "status": "ok",
        },
        copilot_normalize=failing_copilot_normalize,
        write_wiki_note=lambda **kwargs: writes.append(kwargs) or tmp_path / "note.md",
    )

    assert results[0].status == "written"
    assert results[0].reason == "wiki note written; copilot fallback: standalone unavailable"
    assert writes[0]["title"] == "safe"
    assert writes[0]["summary"].startswith("Alpha beta gamma")


def test_ingest_script_can_run_directly():
    result = subprocess.run(
        [sys.executable, str(Path("scripts/local_wiki_ingest.py")), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
