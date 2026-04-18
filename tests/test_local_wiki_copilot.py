import json

import pytest

from scripts.local_wiki_copilot import (
    CopilotNormalizationError,
    build_copilot_packet,
    build_copilot_request,
    parse_copilot_normalization,
)


def test_build_copilot_packet_keeps_bounded_excerpt():
    packet = build_copilot_packet(
        source_path="C:\\safe.txt",
        source_ext=".txt",
        extraction={"status": "ok", "text": "alpha " * 5000},
    )

    assert packet["source_ext"] == ".txt"
    assert len(packet["excerpt"]) <= 4000
    assert packet["text_length"] > len(packet["excerpt"])


def test_build_copilot_packet_keeps_structure_hints_compact():
    packet = build_copilot_packet(
        source_path="C:\\safe.md",
        source_ext=".md",
        extraction={"status": "ok", "text": "\n".join(f"# Heading {i}" for i in range(30))},
    )

    assert len(packet["structure_hints"]) <= 10


def test_build_copilot_request_uses_internal_sensitivity():
    body = build_copilot_request({"source_ext": ".txt", "excerpt": "alpha"})

    assert body["model"] == "github-copilot/gpt-5-mini"
    assert body["sensitivity"] == "internal"
    assert body["messages"][0]["role"] == "system"


def test_build_copilot_request_rejects_secret_sensitivity():
    with pytest.raises(ValueError, match="secret"):
        build_copilot_request({"excerpt": "alpha"}, sensitivity="secret")


def test_parse_copilot_normalization_requires_json_object():
    parsed = parse_copilot_normalization(
        json.dumps(
            {
                "title": "A",
                "summary": "B",
                "topics": ["local-file"],
            }
        )
    )

    assert parsed["title"] == "A"
    assert parsed["summary"] == "B"
    assert parsed["topics"] == ["local-file"]
    assert parsed["entities"] == []
    assert "local-wiki" in parsed["tags"]
    assert "auto-ingest" in parsed["tags"]


def test_parse_copilot_normalization_accepts_json_code_fence():
    parsed = parse_copilot_normalization(
        '```json\n{"title":"A","summary":"B","key_facts":["C"]}\n```'
    )

    assert parsed["key_facts"] == ["C"]


def test_parse_copilot_normalization_rejects_non_json():
    with pytest.raises(CopilotNormalizationError):
        parse_copilot_normalization("not json")
