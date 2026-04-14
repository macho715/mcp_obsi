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
        header = f"# {rec.updated_at.strftime('%Y-%m-%d')}\n"
        section = "## AI Memory Log\n"
        compact_line = (
            f"- id: `{rec.id}` | type: `{rec.memory_type.value}` | "
            f"title: {rec.title} | path: `{rec.path}`\n"
        )

        if not daily_path.exists():
            daily_path.write_text(f"{header}\n{section}{compact_line}", encoding="utf-8")
            return daily_path

        existing = daily_path.read_text(encoding="utf-8")
        if "## AI Memory Log" in existing:
            with daily_path.open("a", encoding="utf-8") as handle:
                if not existing.endswith("\n"):
                    handle.write("\n")
                handle.write(compact_line)
            return daily_path

        with daily_path.open("a", encoding="utf-8") as handle:
            if not existing.endswith("\n"):
                handle.write("\n")
            handle.write(f"\n{section}{compact_line}")
        return daily_path
