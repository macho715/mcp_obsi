from pathlib import Path

from app.services.wiki_store import WikiStore


class LintService:
    def __init__(self, wiki_store: WikiStore):
        self.wiki_store = wiki_store

    def run(self) -> dict:
        issues: list[str] = []
        scanned_files = list(self._iter_markdown_files())

        for path in scanned_files:
            text = path.read_text(encoding="utf-8")
            relative = path.relative_to(self.wiki_store.root).as_posix()
            if not text.strip():
                issues.append(f"- empty: {relative}")
                continue
            if not text.lstrip().startswith("---"):
                issues.append(f"- missing_frontmatter: {relative}")
            if "#" not in text:
                issues.append(f"- missing_heading: {relative}")

        report_lines = [
            "# Wiki Lint Report",
            "",
            f"- scanned_files: {len(scanned_files)}",
            f"- issues_found: {len(issues)}",
            "",
            "## Findings",
            "",
        ]
        if issues:
            report_lines.extend(issues)
        else:
            report_lines.append("- No issues found.")

        report_path = self.wiki_store.write_text(
            "reports/latest-lint-report.md",
            "\n".join(report_lines),
        )
        return {
            "status": "completed",
            "path": str(report_path).replace("\\", "/"),
            "scanned_files": len(scanned_files),
            "issues_found": len(issues),
        }

    def _iter_markdown_files(self) -> list[Path]:
        return [
            path
            for path in self.wiki_store.root.rglob("*.md")
            if path.name not in {"index.md", "log.md"}
        ]
