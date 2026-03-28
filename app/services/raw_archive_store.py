from datetime import datetime
from pathlib import Path

import yaml

from app.models import RawConversationCreate
from app.services.schema_validator import SchemaValidator
from app.utils.integrity import sign_payload
from app.utils.sanitize import reject_sensitive_label, sanitize_free_text, sanitize_tags


class RawArchiveStore:
    def __init__(
        self,
        vault_path: Path,
        validator: SchemaValidator | None = None,
        hmac_secret: str | None = None,
    ):
        self.vault_path = vault_path
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self.validator = validator or SchemaValidator()
        self.hmac_secret = hmac_secret or None

    def raw_path(self, payload: RawConversationCreate) -> Path:
        conversation_date = payload.conversation_date or payload.created_at_utc.date()
        return (
            self.vault_path
            / "mcp_raw"
            / payload.source
            / conversation_date.isoformat()
            / f"{payload.mcp_id}.md"
        )

    def save(self, payload: RawConversationCreate) -> dict:
        created_at = payload.created_at_utc or datetime.now().astimezone()
        conversation_date = payload.conversation_date or created_at.date()
        document = {
            "schema_type": "raw_conversation",
            "mcp_id": payload.mcp_id,
            "source": reject_sensitive_label("source", payload.source),
            "created_by": reject_sensitive_label("created_by", payload.created_by),
            "created_at_utc": created_at.isoformat(),
            "conversation_date": conversation_date.isoformat(),
            "project": reject_sensitive_label("project", payload.project),
            "tags": sanitize_tags(payload.tags),
            "mcp_sig": payload.mcp_sig,
            "body_markdown": sanitize_free_text("body_markdown", payload.body_markdown),
        }
        if self.hmac_secret:
            document["mcp_sig"] = sign_payload(
                self.hmac_secret,
                {key: value for key, value in document.items() if key != "mcp_sig"},
            )
        self.validator.validate_raw(document)

        normalized_payload = payload.model_copy(
            update={
                "created_at_utc": created_at,
                "conversation_date": conversation_date,
            }
        )
        path = self.raw_path(normalized_payload)
        path.parent.mkdir(parents=True, exist_ok=True)

        frontmatter = document.copy()
        body_markdown = frontmatter.pop("body_markdown")
        text = (
            "---\n"
            + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
            + "---\n\n"
            + body_markdown
            + "\n"
        )
        path.write_text(text, encoding="utf-8")
        return {
            "status": "saved",
            "mcp_id": payload.mcp_id,
            "path": path.relative_to(self.vault_path).as_posix(),
        }
