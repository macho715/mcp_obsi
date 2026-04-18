import pytest

from scripts.local_research_schemas import validate_research_result


def test_validate_ask_result_normalizes_string_findings():
    result = validate_research_result(
        {
            "short_answer": "answer",
            "findings": ["plain finding"],
            "gaps": "gap",
            "next_actions": ["act"],
        },
        mode="ask",
    )

    assert result["short_answer"] == "answer"
    assert result["findings"] == [{"text": "plain finding"}]
    assert result["gaps"] == ["gap"]
    assert result["next_actions"] == ["act"]


def test_validate_bundle_result_normalizes_file_roles():
    result = validate_research_result(
        {
            "bundle_title": "bundle",
            "core_files": ["C:\\Docs\\a.md"],
            "supporting_files": [{"path": "C:\\Docs\\b.md"}],
            "duplicates_or_versions": [],
            "missing_or_gap_hints": ["missing invoice"],
            "next_actions": [],
        },
        mode="find-bundle",
    )

    assert result["core_files"] == [{"path": "C:\\Docs\\a.md"}]
    assert result["supporting_files"] == [{"path": "C:\\Docs\\b.md"}]
    assert result["missing_or_gap_hints"] == [{"hint": "missing invoice"}]


def test_validate_ask_result_rejects_missing_short_answer():
    with pytest.raises(ValueError, match="short_answer"):
        validate_research_result({"findings": []}, mode="ask")
