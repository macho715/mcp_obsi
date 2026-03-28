import json
import re
import sys
from pathlib import Path


def _sanitize_text(value: str, project_root: str, home_dir: str) -> str:
    sanitized = value
    if project_root:
        sanitized = sanitized.replace(project_root, "$PROJECT_ROOT")
    if home_dir:
        sanitized = sanitized.replace(home_dir, "$HOME")
    sanitized = re.sub(r"Bearer\s+\S+", "Bearer $REDACTED", sanitized)
    sanitized = re.sub(r"(MCP_API_TOKEN=)\S+", r"\1$REDACTED", sanitized)
    return sanitized


def _sanitize_value(value, project_root: str, home_dir: str):
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if key in {"user_email", "transcript_path", "workspace_roots"}:
                continue
            if key == "output":
                cleaned["output_summary"] = {
                    "present": bool(item.strip()) if isinstance(item, str) else bool(item),
                    "chars": len(item) if isinstance(item, str) else None,
                }
                continue
            cleaned[key] = _sanitize_value(item, project_root, home_dir)
        return cleaned
    if isinstance(value, list):
        return [_sanitize_value(item, project_root, home_dir) for item in value]
    if isinstance(value, str):
        return _sanitize_text(value, project_root, home_dir)
    return value


root = Path(".cursor/hooks/logs")
root.mkdir(parents=True, exist_ok=True)
log_path = root / "shell-events.jsonl"
payload = sys.stdin.read() or "{}"

project_root = str(Path.cwd().resolve())
home_dir = str(Path.home().resolve())

try:
    parsed = json.loads(payload)
except json.JSONDecodeError:
    parsed = {
        "hook_event_name": "afterShellExecution",
        "raw_payload_summary": {
            "present": bool(payload.strip()),
            "chars": len(payload),
        },
    }

sanitized = _sanitize_value(parsed, project_root, home_dir)

with log_path.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(sanitized, ensure_ascii=False) + "\n")

print(json.dumps({"continue": True}))
