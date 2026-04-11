import re
from datetime import date, datetime
from pathlib import Path

import yaml


class WikiSearchService:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path

    def search(self, query: str, path_prefix: str = "wiki/analyses", limit: int = 8) -> dict:
        terms = [term.casefold() for term in query.split() if term.strip()]
        prefix = self.vault_path / Path(path_prefix)
        if not prefix.exists():
            return {"results": []}

        results: list[dict] = []
        for path in prefix.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            frontmatter, body = self._split_frontmatter(text)
            title = self._extract_title(body, frontmatter.get("title"), path.stem)
            haystack = "\n".join(
                [
                    title,
                    body,
                    " ".join(frontmatter.get("tags", [])),
                    path.stem,
                ]
            ).casefold()
            score = sum(1 for term in terms if term in haystack)
            if score <= 0:
                continue

            rel_path = path.relative_to(self.vault_path).as_posix()
            path_parts = rel_path.split("/")
            results.append(
                {
                    "source": "wiki",
                    "id": f"wiki:{rel_path.removesuffix('.md')}",
                    "title": title,
                    "slug": path.stem,
                    "path": rel_path,
                    "category": path_parts[1] if len(path_parts) > 1 else None,
                    "tags": frontmatter.get("tags", []),
                    "snippet": body[:240].strip(),
                    "score": float(score),
                    "fetch_route": "fetch_wiki",
                    "related_memory_id": frontmatter.get("related_memory_id"),
                }
            )

        results.sort(key=lambda item: (-item["score"], item["title"]))
        return {"results": results[:limit]}

    def fetch(self, path: str | None = None, slug: str | None = None) -> dict:
        note_path = self._resolve_path(path=path, slug=slug)
        if note_path is None or not note_path.exists():
            return {"status": "not_found", "source": "wiki"}

        text = note_path.read_text(encoding="utf-8")
        frontmatter, body = self._split_frontmatter(text)
        rel_path = note_path.relative_to(self.vault_path).as_posix()
        path_parts = rel_path.split("/")
        return {
            "source": "wiki",
            "id": f"wiki:{rel_path.removesuffix('.md')}",
            "title": self._extract_title(body, frontmatter.get("title"), note_path.stem),
            "slug": note_path.stem,
            "path": rel_path,
            "category": path_parts[1] if len(path_parts) > 1 else None,
            "frontmatter": frontmatter,
            "body": body.strip(),
            "related_memory_id": frontmatter.get("related_memory_id"),
        }

    def _resolve_path(self, path: str | None, slug: str | None) -> Path | None:
        if path:
            clean = path.strip().strip("/")
            candidate = self.vault_path / clean
            return candidate if candidate.suffix == ".md" else candidate.with_suffix(".md")
        if slug:
            matches = list((self.vault_path / "wiki" / "analyses").rglob(f"{slug}.md"))
            return matches[0] if matches else None
        return None

    def _split_frontmatter(self, text: str) -> tuple[dict, str]:
        normalized = text.lstrip("\ufeff")
        if normalized.startswith("---\n"):
            _, raw_frontmatter, body = normalized.split("---\n", 2)
            try:
                return self._json_safe(yaml.safe_load(raw_frontmatter) or {}), body
            except yaml.YAMLError:
                return {}, normalized
        return {}, normalized

    def _extract_title(self, body: str, frontmatter_title: str | None, fallback: str) -> str:
        match = re.search(r"^#\s+(.+)$", body, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
        if isinstance(frontmatter_title, str) and frontmatter_title.strip():
            return frontmatter_title.strip()
        return fallback

    def _json_safe(self, value):
        if isinstance(value, dict):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._json_safe(item) for item in value]
        if isinstance(value, tuple):
            return [self._json_safe(item) for item in value]
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value
