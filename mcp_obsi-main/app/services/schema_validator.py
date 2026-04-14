import json
from pathlib import Path

from jsonschema import Draft202012Validator


class SchemaValidator:
    def __init__(self, schema_root: Path | None = None):
        self.schema_root = schema_root or Path(__file__).resolve().parents[2] / "schemas"
        self._validators = {
            "raw_conversation": Draft202012Validator(
                self._read_schema("raw-conversation.schema.json")
            ),
            "memory_item": Draft202012Validator(self._read_schema("memory-item.schema.json")),
            "memory_item_v2": Draft202012Validator(self._read_schema("memory-item-v2.schema.json")),
        }

    def _read_schema(self, filename: str) -> dict:
        return json.loads((self.schema_root / filename).read_text(encoding="utf-8"))

    def validate_raw(self, payload: dict) -> None:
        self._validators["raw_conversation"].validate(payload)

    def validate_memory(self, payload: dict) -> None:
        if payload.get("schema_version") == "2.0" or "roles" in payload:
            self._validators["memory_item_v2"].validate(payload)
            return
        self._validators["memory_item"].validate(payload)
