from pathlib import Path


class WikiStore:
    def __init__(self, vault_path: Path, overlay_dirname: str = "wiki"):
        self.vault_path = vault_path
        self.root = vault_path / overlay_dirname
        self.ensure_structure()

    def ensure_structure(self) -> None:
        for folder in ["topics", "entities", "conflicts", "reports"]:
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        self.root.mkdir(parents=True, exist_ok=True)
        for filename, title in [("index.md", "# Wiki Index\n"), ("log.md", "# Wiki Log\n")]:
            path = self.root / filename
            if not path.exists():
                path.write_text(title, encoding="utf-8")

    def write_text(self, relative_path: str, content: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        return path

    def append_text(self, relative_path: str, content: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            if not content.endswith("\n"):
                handle.write("\n")
        return path

    def read_text(self, relative_path: str) -> str | None:
        path = self.root / relative_path
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def overlay_path(self, relative_path: str) -> Path:
        return self.root / relative_path

    def write_page(
        self,
        section: str,
        slug: str,
        title: str,
        content: str,
        source_memory_ids: list[str] | None = None,
    ) -> Path:
        safe_section = self._safe_section(section)
        safe_slug = self._safe_slug(slug)
        frontmatter_lines = [
            "---",
            "compiled_layer: true",
            f"section: {safe_section}",
            f"slug: {safe_slug}",
        ]
        if source_memory_ids:
            frontmatter_lines.append("source_memory_ids:")
            frontmatter_lines.extend(f"  - {memory_id}" for memory_id in source_memory_ids)
        frontmatter_lines.extend(["---", "", f"# {title}", "", content.strip(), ""])
        return self.write_text(f"{safe_section}/{safe_slug}.md", "\n".join(frontmatter_lines))

    @staticmethod
    def _safe_section(section: str) -> str:
        allowed = {"topics", "entities", "conflicts", "reports"}
        normalized = section.strip().lower()
        if normalized not in allowed:
            raise ValueError(f"unsupported wiki section: {section}")
        return normalized

    @staticmethod
    def _safe_slug(slug: str) -> str:
        normalized = slug.strip().replace("\\", "/").strip("/")
        if not normalized or "/" in normalized or ".." in normalized:
            raise ValueError(f"invalid wiki slug: {slug}")
        return normalized
