from scripts.local_wiki_writer import ensure_wiki_tree, safe_slug, write_wiki_note


def test_safe_slug_adds_hash():
    slug = safe_slug("WH Comprehensive Analysis Report", "C:\\x.md")

    assert len(slug.split("-")[-1]) == 8


def test_safe_slug_uses_source_hash_for_duplicate_titles():
    first = safe_slug("Example Report", "C:\\a.txt")
    second = safe_slug("Example Report", "C:\\b.txt")

    assert first != second
    assert first.startswith("example-report-")
    assert second.startswith("example-report-")


def test_ensure_wiki_tree_creates_expected_directories_and_files(tmp_path):
    wiki_root = ensure_wiki_tree(tmp_path)

    assert wiki_root == tmp_path / "wiki"
    assert (wiki_root / "sources").exists()
    assert (wiki_root / "concepts").exists()
    assert (wiki_root / "entities").exists()
    assert (wiki_root / "analyses").exists()
    assert (wiki_root / "index.md").exists()
    assert (wiki_root / "log.md").exists()


def test_write_wiki_note_creates_sources_index_and_log(tmp_path):
    note = write_wiki_note(
        vault_root=tmp_path,
        title="Example",
        source_path="C:\\file.txt",
        source_ext=".txt",
        source_size=10,
        source_modified_at="2026-04-16",
        summary="Short summary",
        key_facts=["Fact one"],
        extracted_structure=["Section one"],
        topics=["topic"],
        entities=[],
        projects=[],
        extraction_status="ok",
    )

    assert note.exists()
    assert (tmp_path / "wiki" / "sources").exists()
    assert (tmp_path / "wiki" / "index.md").exists()
    assert (tmp_path / "wiki" / "log.md").exists()

    content = note.read_text(encoding="utf-8")
    assert "type: local_file_knowledge" in content
    assert "status: draft" in content
    assert 'title: "Example"' in content
    assert 'source_path: "C:\\\\file.txt"' in content
    assert "topics:" in content
    assert "  - topic" in content
    assert "entities: []" in content
    assert "projects: []" in content
    assert "  - local-wiki" in content
    assert "  - auto-ingest" in content
    assert "## Summary" in content
    assert "Short summary" in content
    assert "## Key Facts" in content
    assert "- Fact one" in content
    assert "## Extracted Structure" in content
    assert "- Section one" in content
