from app.services.wiki_store import WikiStore


class ConflictService:
    def __init__(self, wiki_store: WikiStore):
        self.wiki_store = wiki_store

    def reconcile(
        self,
        topic_slug: str,
        claim_a: str,
        claim_b: str,
        source_a: str | None = None,
        source_b: str | None = None,
    ) -> dict:
        content_lines = [
            "## Claim A",
            claim_a.strip(),
            "",
        ]
        if source_a:
            content_lines.extend(["Source A:", source_a.strip(), ""])

        content_lines.extend(
            [
                "## Claim B",
                claim_b.strip(),
                "",
            ]
        )
        if source_b:
            content_lines.extend(["Source B:", source_b.strip(), ""])

        content_lines.extend(
            [
                "## Reconciliation Guidance",
                "- Preserve both claims until evidence resolves the conflict.",
                "- Update compiled wiki pages only after reconciliation is approved.",
            ]
        )

        path = self.wiki_store.write_page(
            section="conflicts",
            slug=topic_slug,
            title=f"Conflict: {topic_slug}",
            content="\n".join(content_lines),
        )
        return {"status": "written", "path": str(path).replace("\\", "/")}
