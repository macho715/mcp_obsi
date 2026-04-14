import json
import sys

payload = sys.stdin.read() or "{}"
try:
    data = json.loads(payload)
except json.JSONDecodeError:
    print(json.dumps({"permission": "allow"}))
    sys.exit(0)

command = json.dumps(data, ensure_ascii=True).lower()
blocked = [
    "rm -rf /",
    "format c:",
    "del /s /q",
    "remove-item -recurse -force",
]
if any(item in command for item in blocked):
    print(json.dumps({"permission": "deny", "message": "blocked by project shell guard"}))
else:
    print(json.dumps({"permission": "allow"}))
