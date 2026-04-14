from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from app.config import settings
from app.models import MemoryCreate, MemoryPatch, RawConversationCreate
from app.services.memory_store import MemoryStore
from app.utils.integrity import verify_payload


@contextmanager
def hmac_secret(secret: str):
    original = settings.mcp_hmac_secret
    settings.mcp_hmac_secret = secret
    try:
        yield
    finally:
        settings.mcp_hmac_secret = original


def read_raw_document(vault: Path, rel_path: str) -> dict:
    text = (vault / rel_path).read_text(encoding="utf-8")
    parts = text.split("\n---\n", 1)
    assert len(parts) == 2
    frontmatter = yaml.safe_load(parts[0][4:]) or {}
    frontmatter["body_markdown"] = parts[1].lstrip("\n").rstrip("\n")
    return frontmatter


def assert_signed_document(document: dict, secret: str) -> None:
    signature = document.get("mcp_sig")
    assert signature is not None
    signed_payload = {key: value for key, value in document.items() if key != "mcp_sig"}
    assert verify_payload(secret, signed_payload, signature) is True


def test_save_signs_memory_when_hmac_secret_configured(tmp_path: Path):
    with hmac_secret("phase-2-secret"):
        store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
        result = store.save(
            MemoryCreate(
                memory_type="decision",
                title="Signed decision",
                content="Signed memory content",
                source="manual",
                created_by="tester",
                append_daily=False,
            )
        )

        document = store.md.read_memory_document(result["path"])
        assert document is not None
        assert document["mcp_sig"].startswith("hmac-sha256:")
        assert_signed_document(document, "phase-2-secret")


def test_update_rejects_tampered_signed_memory_when_hmac_enabled(tmp_path: Path):
    with hmac_secret("phase-2-secret"):
        store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
        result = store.save(
            MemoryCreate(
                memory_type="decision",
                title="Tamper check",
                content="Original signed content",
                source="manual",
                created_by="tester",
                append_daily=False,
            )
        )

        note_path = tmp_path / "vault" / result["path"]
        tampered = note_path.read_text(encoding="utf-8").replace(
            "Original signed content",
            "Tampered signed content",
        )
        note_path.write_text(tampered, encoding="utf-8")

        with pytest.raises(ValueError, match="stored memory integrity check failed"):
            store.update(
                MemoryPatch(
                    memory_id=result["id"],
                    content="Should not be written",
                )
            )


def test_update_unsigned_legacy_memory_gets_signed_when_hmac_enabled(tmp_path: Path):
    with hmac_secret(""):
        unsigned_store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
        result = unsigned_store.save(
            MemoryCreate(
                memory_type="decision",
                title="Legacy unsigned",
                content="Unsigned content",
                source="manual",
                created_by="tester",
                append_daily=False,
            )
        )
        unsigned_document = unsigned_store.md.read_memory_document(result["path"])
        assert unsigned_document is not None
        assert unsigned_document["mcp_sig"] is None

    with hmac_secret("phase-2-secret"):
        signed_store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
        update_result = signed_store.update(
            MemoryPatch(
                memory_id=result["id"],
                content="Unsigned content updated and signed",
            )
        )

        signed_document = signed_store.md.read_memory_document(update_result["path"])
        assert signed_document is not None
        assert signed_document["mcp_sig"].startswith("hmac-sha256:")
        assert_signed_document(signed_document, "phase-2-secret")


def test_save_rejects_mixed_secret_for_p2_sensitivity(tmp_path: Path):
    with hmac_secret(""):
        store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")

        with pytest.raises(
            ValueError,
            match="content contains sensitive fragments disallowed for sensitivity p2",
        ):
            store.save(
                MemoryCreate(
                    memory_type="decision",
                    title="P2 note",
                    content="Normal sentence with token=supersecret inside it",
                    source="manual",
                    created_by="tester",
                    sensitivity="p2",
                    append_daily=False,
                )
            )


def test_raw_archive_adds_signature_when_hmac_secret_configured(tmp_path: Path):
    with hmac_secret("phase-2-secret"):
        store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
        result = store.archive_raw_conversation(
            RawConversationCreate(
                mcp_id="convo-hmac-phase-2",
                source="manual",
                created_by="tester",
                created_at_utc=datetime(2026, 3, 28, 12, 0, tzinfo=UTC),
                conversation_date=datetime(2026, 3, 28, 12, 0, tzinfo=UTC).date(),
                body_markdown="Signed raw body",
            )
        )

        document = read_raw_document(tmp_path / "vault", result["path"])
        assert document["mcp_sig"].startswith("hmac-sha256:")
        assert_signed_document(document, "phase-2-secret")
