from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable
from datetime import date
from pathlib import Path

WIKI_SUBDIRECTORIES = ("sources", "concepts", "entities", "analyses")
DEFAULT_TAGS = ("local-wiki", "auto-ingest")


def safe_slug(title: str, source_path: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug_base = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")
    if not slug_base:
        slug_base = "local-file"
    digest = hashlib.sha256(source_path.encode("utf-8")).hexdigest()[:8]
    return f"{slug_base}-{digest}"


def ensure_wiki_tree(vault_root: Path | str) -> Path:
    wiki_root = Path(vault_root) / "wiki"
    for name in WIKI_SUBDIRECTORIES:
        (wiki_root / name).mkdir(parents=True, exist_ok=True)

    _write_if_missing(
        wiki_root / "index.md",
        "# Local Computer Knowledge Wiki\n\n## Sources\n\n",
    )
    _write_if_missing(
        wiki_root / "log.md",
        "# Local Computer Knowledge Wiki Log\n\n",
    )
    return wiki_root


def write_wiki_note(
    *,
    vault_root: Path | str,
    title: str,
    source_path: str,
    source_ext: str,
    source_size: int,
    source_modified_at: str,
    summary: str,
    key_facts: list[str],
    extracted_structure: list[str],
    topics: list[str],
    entities: list[str],
    projects: list[str],
    extraction_status: str,
    ingested_at: str | None = None,
) -> Path:
    wiki_root = ensure_wiki_tree(vault_root)
    slug = safe_slug(title, source_path)
    note_path = wiki_root / "sources" / f"{slug}.md"
    ingested_value = ingested_at or date.today().isoformat()

    note_path.write_text(
        "\n".join(
            [
                "---",
                "type: local_file_knowledge",
                "status: draft",
                f'title: "{_escape_yaml_string(title)}"',
                f'source_path: "{_escape_yaml_string(source_path)}"',
                f'source_ext: "{_escape_yaml_string(source_ext)}"',
                f"source_size: {int(source_size)}",
                f'source_modified_at: "{_escape_yaml_string(source_modified_at)}"',
                f'ingested_at: "{_escape_yaml_string(ingested_value)}"',
                f'extraction_status: "{_escape_yaml_string(extraction_status)}"',
                _format_array("topics", topics),
                _format_array("entities", entities),
                _format_array("projects", projects),
                _format_array("tags", DEFAULT_TAGS),
                "---",
                "",
                f"# {title}",
                "",
                "## Summary",
                "",
                summary or "_No summary available._",
                "",
                "## Key Facts",
                "",
                _format_markdown_list(key_facts),
                "",
                "## Extracted Structure",
                "",
                _format_markdown_list(extracted_structure),
                "",
                "## Source",
                "",
                f"- Path: `{source_path}`",
                f"- Extension: `{source_ext}`",
                f"- Extraction status: `{extraction_status}`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    _append_index_entry(wiki_root / "index.md", title, note_path, wiki_root)
    _append_log_entry(wiki_root / "log.md", ingested_value, title, source_path)
    return note_path


def _format_array(name: str, values: Iterable[str]) -> str:
    items = [str(value) for value in values if str(value)]
    if not items:
        return f"{name}: []"
    lines = [f"{name}:"]
    lines.extend(f"  - {_escape_plain_array_item(item)}" for item in items)
    return "\n".join(lines)


def _format_markdown_list(values: Iterable[str]) -> str:
    items = [str(value) for value in values if str(value)]
    if not items:
        return "- None recorded"
    return "\n".join(f"- {item}" for item in items)


def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def _append_index_entry(index_path: Path, title: str, note_path: Path, wiki_root: Path) -> None:
    relative = note_path.relative_to(wiki_root).as_posix()
    entry = f"- [[{relative[:-3]}|{title}]]\n"
    existing = index_path.read_text(encoding="utf-8")
    if entry not in existing:
        with index_path.open("a", encoding="utf-8") as handle:
            handle.write(entry)


def _append_log_entry(log_path: Path, ingested_at: str, title: str, source_path: str) -> None:
    entry = f"- {ingested_at}: ingested {title} from `{source_path}`\n"
    existing = log_path.read_text(encoding="utf-8")
    if entry not in existing:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(entry)


def _escape_yaml_string(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _escape_plain_array_item(value: str) -> str:
    text = str(value)
    if re.search(r"[:#\[\]{},&*?|<>=!%@`]", text):
        return f'"{_escape_yaml_string(text)}"'
    return text
