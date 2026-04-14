from pathlib import Path

from app.services.wiki_search_service import WikiSearchService


def test_search_wiki_limits_to_analyses_prefix(tmp_path: Path):
    vault = tmp_path / "vault"
    analyses = vault / "wiki" / "analyses"
    concepts = vault / "wiki" / "concepts"
    analyses.mkdir(parents=True)
    concepts.mkdir(parents=True)

    (analyses / "logistics_issue_shu_2025-11-26_3.md").write_text(
        "---\n"
        "tags:\n"
        "  - analysis\n"
        "  - hazmat\n"
        "---\n\n"
        "# [SHU Issue] 2025-11-26 Event #3\n\n"
        "hazmat delivery hold at SHU\n",
        encoding="utf-8",
    )
    (concepts / "shu-hazmat.md").write_text(
        "# SHU Hazmat Concept\n\nhazmat concept only\n",
        encoding="utf-8",
    )

    service = WikiSearchService(vault)
    result = service.search(
        query="hazmat shu 2025-11-26",
        path_prefix="wiki/analyses",
        limit=5,
    )

    assert [item["path"] for item in result["results"]] == [
        "wiki/analyses/logistics_issue_shu_2025-11-26_3.md"
    ]
    assert result["results"][0]["fetch_route"] == "fetch_wiki"


def test_fetch_wiki_prefers_path_and_falls_back_to_slug(tmp_path: Path):
    vault = tmp_path / "vault"
    analyses = vault / "wiki" / "analyses"
    analyses.mkdir(parents=True)
    note_path = analyses / "logistics_issue_shu_2025-11-26_3.md"
    note_path.write_text(
        "---\n"
        "tags:\n"
        "  - analysis\n"
        "  - hazmat\n"
        "---\n\n"
        "# [SHU Issue] 2025-11-26 Event #3\n\n"
        "hazmat delivery hold at SHU\n",
        encoding="utf-8",
    )

    service = WikiSearchService(vault)

    by_path = service.fetch(path="wiki/analyses/logistics_issue_shu_2025-11-26_3")
    by_slug = service.fetch(slug="logistics_issue_shu_2025-11-26_3")

    assert by_path["path"] == "wiki/analyses/logistics_issue_shu_2025-11-26_3.md"
    assert by_slug["slug"] == "logistics_issue_shu_2025-11-26_3"
    assert "hazmat delivery hold" in by_slug["body"]


def test_search_wiki_uses_frontmatter_title_when_heading_is_missing(tmp_path: Path):
    vault = tmp_path / "vault"
    analyses = vault / "wiki" / "analyses"
    analyses.mkdir(parents=True)
    (analyses / "frontmatter-only.md").write_text(
        "---\ntitle: Frontmatter Title\ntags:\n  - hazmat\n---\n\nBody without markdown heading\n",
        encoding="utf-8",
    )

    service = WikiSearchService(vault)
    result = service.search(query="hazmat", path_prefix="wiki/analyses", limit=5)

    assert result["results"][0]["title"] == "Frontmatter Title"
