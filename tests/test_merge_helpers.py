import re
from datetime import UTC, datetime

from app.mcp_server import build_fetch_wrapper_response, build_search_wrapper_response
from app.utils.ids import make_memory_id
from app.utils.sanitize import clean_tag, clean_text


def test_make_memory_id_matches_contract():
    memory_id = make_memory_id(datetime(2026, 3, 28, 10, 11, 12, tzinfo=UTC))
    assert re.fullmatch(r"MEM-\d{8}-\d{6}-[0-9A-F]{6}", memory_id)


def test_clean_text_and_clean_tag_normalize_without_changing_meaning():
    assert clean_text("Line one\r\n\r\n\r\nLine two  ") == "Line one\n\nLine two"
    assert clean_tag("  HVDC Alert Rule  ") == "hvdc-alert-rule"


def test_search_wrapper_shape_stays_compatible():
    response = build_search_wrapper_response(
        [{"id": "MEM-1", "title": "Decision", "path": "20_AI_Memory/decision/2026/03/MEM-1.md"}]
    )

    assert response == {
        "results": [
            {
                "id": "MEM-1",
                "title": "Decision",
                "url": "obsidian://open?vault=mcp_obsidian_vault&file=20_AI_Memory/decision/2026/03/MEM-1.md",
            }
        ]
    }


def test_fetch_wrapper_shape_stays_compatible():
    found = build_fetch_wrapper_response(
        "MEM-1",
        {
            "id": "MEM-1",
            "title": "Decision",
            "content": "Stored body",
            "path": "20_AI_Memory/decision/2026/03/MEM-1.md",
            "type": "decision",
            "project": "HVDC",
            "source": "manual",
            "tags": ["hvdc", "decision"],
        },
    )
    missing = build_fetch_wrapper_response("MEM-404", None)

    assert found == {
        "id": "MEM-1",
        "title": "Decision",
        "text": "Stored body",
        "url": "obsidian://open?vault=mcp_obsidian_vault&file=20_AI_Memory/decision/2026/03/MEM-1.md",
        "metadata": {
            "type": "decision",
            "project": "HVDC",
            "source": "manual",
            "tags": ["hvdc", "decision"],
        },
    }
    assert missing == {
        "id": "MEM-404",
        "title": "Not found",
        "text": "",
        "url": "",
        "metadata": {"status": "not_found"},
    }
