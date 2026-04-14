from __future__ import annotations

from pathlib import Path

from app.models import MemoryRecord


class DailyStore:
    def __init__(self, vault_path: Path) -> None:
        self.vault_path = vault_path

    def append_memory(self, rec: MemoryRecord) -> Path:
        daily_dir = self.vault_path / "10_Daily"
        daily_dir.mkdir(parents=True, exist_ok=True)

        daily_path = daily_dir / f"{rec.updated_at.strftime('%Y-%m-%d')}.md"
        entry = (
            f"\n## AI Memory Log\n"
            f"- id: `{rec.id}`\n"
            f"- type: `{rec.memory_type.value}`\n"
            f"- title: {rec.title}\n"
            f"- path: `{rec.path}`\n"
        )

        if daily_path.exists():
            existing = daily_path.read_text(encoding="utf-8")
            if "## AI Memory Log" in existing:
                entry = (
                    f"- id: `{rec.id}` | type: `{rec.memory_type.value}` | "
                    f"title: {rec.title} | path: `{rec.path}`\n"
                )
                with daily_path.open("a", encoding="utf-8") as fh:
                    fh.write(entry)
            else:
                with daily_path.open("a", encoding="utf-8") as fh:
                    fh.write(entry)
        else:
            daily_path.write_text(f"# {rec.updated_at.strftime('%Y-%m-%d')}\n{entry}", encoding="utf-8")

        return daily_path
