from pathlib import Path

from scripts.local_research_tools import LocalResearchToolExecutor, ToolLimits


def test_extract_file_allows_selected_candidate_path(tmp_path):
    source = tmp_path / "selected.md"
    source.write_text("selected evidence", encoding="utf-8")
    executor = LocalResearchToolExecutor(
        selected_candidates=[{"path": str(source)}],
        extract=lambda path: {"status": "ok", "text": Path(path).read_text(encoding="utf-8")},
    )

    result = executor.extract_file(str(source))

    assert result["status"] == "ok"
    assert result["text"] == "selected evidence"


def test_extract_file_rejects_unauthorized_path(tmp_path):
    source = tmp_path / "outside.md"
    source.write_text("outside", encoding="utf-8")
    executor = LocalResearchToolExecutor(selected_candidates=[])

    result = executor.extract_file(str(source))

    assert result["status"] == "rejected"
    assert "not approved" in result["reason"]


def test_extract_file_rejects_secret_looking_path(tmp_path):
    source = tmp_path / "api-token.md"
    source.write_text("secret", encoding="utf-8")
    executor = LocalResearchToolExecutor(selected_candidates=[{"path": str(source)}])

    result = executor.extract_file(str(source))

    assert result["status"] == "rejected"
    assert "blocked path" in result["reason"]


def test_everything_search_registers_same_request_results(tmp_path):
    source = tmp_path / "found.md"
    source.write_text("found evidence", encoding="utf-8")
    executor = LocalResearchToolExecutor(
        search=lambda query, limit=20: [{"path": str(source), "name": source.name}],
        extract=lambda path: {"status": "ok", "text": Path(path).read_text(encoding="utf-8")},
    )

    search_result = executor.everything_search("found")
    extract_result = executor.extract_file(search_result["results"][0]["path"])

    assert extract_result["status"] == "ok"
    assert extract_result["text"] == "found evidence"


def test_extract_file_enforces_char_limit(tmp_path):
    source = tmp_path / "long.md"
    source.write_text("abcdef", encoding="utf-8")
    executor = LocalResearchToolExecutor(
        selected_candidates=[{"path": str(source)}],
        limits=ToolLimits(max_chars_per_file=3, max_total_chars=10),
        extract=lambda path: {"status": "ok", "text": Path(path).read_text(encoding="utf-8")},
    )

    result = executor.extract_file(str(source))

    assert result["text"] == "abc"
    assert result["truncated"] is True


def test_extract_file_enforces_max_files(tmp_path):
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")
    executor = LocalResearchToolExecutor(
        selected_candidates=[{"path": str(first)}, {"path": str(second)}],
        limits=ToolLimits(max_extract_files=1),
        extract=lambda path: {"status": "ok", "text": Path(path).read_text(encoding="utf-8")},
    )

    assert executor.extract_file(str(first))["status"] == "ok"
    assert executor.extract_file(str(second))["status"] == "rejected"


def test_build_citation_does_not_read_files():
    executor = LocalResearchToolExecutor(selected_candidates=[])

    result = executor.build_citation("C:\\Docs\\a.md", "evidence")

    assert result == {"source_path": "C:\\Docs\\a.md", "evidence": "evidence"}
