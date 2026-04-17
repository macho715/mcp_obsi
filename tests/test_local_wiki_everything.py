import pytest

from scripts.local_wiki_everything import (
    EverythingHttpError,
    build_everything_url,
    ensure_loopback_base_url,
    parse_everything_results,
)


def test_ensure_loopback_base_url_accepts_default_localhost():
    assert ensure_loopback_base_url("http://127.0.0.1:8080") == "http://127.0.0.1:8080"


def test_ensure_loopback_base_url_rejects_non_loopback():
    with pytest.raises(ValueError, match="loopback"):
        ensure_loopback_base_url("http://192.168.0.5:8080")


def test_build_everything_url_includes_required_columns():
    url = build_everything_url("http://127.0.0.1:8080", "*.pdf", 25)
    rendered = url.geturl()
    assert "search=%2A.pdf" in rendered
    assert "json=1" in rendered
    assert "path_column=1" in rendered
    assert "size_column=1" in rendered
    assert "date_modified_column=1" in rendered


def test_parse_everything_results_normalizes_full_path():
    payload = {"results": [{"name": "Report.pdf", "path": "C:\\Docs", "size": "120"}]}
    assert parse_everything_results(payload)[0]["path"] == "C:\\Docs\\Report.pdf"


def test_parse_everything_results_formats_windows_filetime_modified_date():
    payload = {
        "results": [
            {
                "name": "Report.pdf",
                "path": "C:\\Docs",
                "date_modified": "134208816268904915",
            }
        ]
    }

    assert parse_everything_results(payload)[0]["modifiedAt"].startswith("2026-04-")


def test_parse_everything_results_rejects_bad_payload():
    with pytest.raises(EverythingHttpError):
        parse_everything_results({"not_results": []})
