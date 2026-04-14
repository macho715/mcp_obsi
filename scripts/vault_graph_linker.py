"""
vault_graph_linker.py
─────────────────────
Obsidian vault 노트의 frontmatter(project, projects, tags, entities, topics)를 읽어
허브 노트(wiki/hubs/)를 생성하고, 각 원본 노트에 wikilink 섹션을 추가합니다.

사용법:
  python vault_graph_linker.py --vault "C:/Users/SAMSUNG/Documents/Vault" --dry-run
  python vault_graph_linker.py --vault "C:/Users/SAMSUNG/Documents/Vault"
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

HUBS_DIR = "wiki/hubs"
LINK_SECTION_MARKER = "<!-- copilot-links -->"

# frontmatter에서 허브 키로 쓸 필드
HUB_FIELDS = ["project", "projects", "tags", "entities", "topics"]


def slugify(value: str) -> str:
    """허브 노트 파일명용 슬러그 생성"""
    value = value.lower().strip()
    value = re.sub(r"[^\w\s\-가-힣]", "", value)
    value = re.sub(r"\s+", "_", value)
    return value


def parse_frontmatter(text: str) -> dict:
    """--- ... --- YAML frontmatter 파싱"""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except Exception:
        return {}


def collect_hub_values(fm: dict) -> set[str]:
    """frontmatter에서 허브 값 추출"""
    values: set[str] = set()
    for field in HUB_FIELDS:
        val = fm.get(field)
        if not val:
            continue
        if isinstance(val, list):
            for v in val:
                if isinstance(v, str) and v.strip():
                    values.add(v.strip())
        elif isinstance(val, str) and val.strip():
            values.add(val.strip())
    return values


def relative_link(from_path: Path, to_path: Path) -> str:
    """Obsidian wikilink: 파일명 기준 (vault root-relative)"""
    # Obsidian은 vault root 기준 경로를 [[path/to/note]] 형태로 사용
    return str(to_path.with_suffix("")).replace("\\", "/")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True, help="Obsidian vault 경로")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 파일 수정 없이 미리보기만",
    )
    parser.add_argument(
        "--hubs-only",
        action="store_true",
        help="허브 노트만 생성, 기존 노트는 수정 안 함",
    )
    args = parser.parse_args()

    vault = Path(args.vault)
    hubs_path = vault / HUBS_DIR
    dry_run = args.dry_run

    if not vault.exists():
        print(f"[ERROR] vault 경로 없음: {vault}")
        sys.exit(1)

    print(f"Vault: {vault}")
    print(f"Hubs dir: {hubs_path}")
    print(f"Dry-run: {dry_run}\n")

    # ── 1. 모든 노트 스캔 ────────────────────────────────────────
    notes = list(vault.rglob("*.md"))
    # .obsidian, hubs 자체는 제외
    notes = [
        n for n in notes
        if ".obsidian" not in str(n)
        and HUBS_DIR not in str(n).replace("\\", "/")
    ]
    print(f"스캔 노트: {len(notes)}개")

    # ── 2. hub_name → note_paths 매핑 수집 ──────────────────────
    hub_map: dict[str, list[Path]] = {}   # hub_value → [note_path, ...]
    note_hubs: dict[Path, set[str]] = {}  # note_path → {hub_values}

    for note in notes:
        try:
            text = note.read_text(encoding="utf-8")
        except Exception:
            continue
        fm = parse_frontmatter(text)
        values = collect_hub_values(fm)
        if values:
            note_hubs[note] = values
            for v in values:
                hub_map.setdefault(v, []).append(note)

    print(f"발견된 허브 값: {len(hub_map)}개")
    print(f"링크 대상 노트: {len(note_hubs)}개\n")

    # ── 3. 허브 노트 생성/갱신 ───────────────────────────────────
    if not dry_run:
        hubs_path.mkdir(parents=True, exist_ok=True)

    created_hubs = 0
    for hub_value, linked_notes in sorted(hub_map.items()):
        slug = slugify(hub_value)
        hub_file = hubs_path / f"{slug}.md"
        rel_hub = hub_file.relative_to(vault)

        # 링크 목록
        links = sorted({
            f"[[{str(n.relative_to(vault).with_suffix('')).replace(chr(92), '/')}]]"
            for n in linked_notes
        })
        content = (
            f"---\n"
            f"hub_kind: auto\n"
            f"hub_value: \"{hub_value}\"\n"
            f"note_count: {len(links)}\n"
            f"---\n\n"
            f"# {hub_value}\n\n"
            f"_자동 생성된 허브 노트 — 이 값을 참조하는 모든 노트_\n\n"
            f"## 연결 노트 ({len(links)}개)\n\n"
            + "\n".join(f"- {lnk}" for lnk in links)
            + "\n"
        )

        action = "CREATE" if not hub_file.exists() else "UPDATE"
        print(f"  [{action}] {rel_hub} ({len(links)}개 노트)")
        created_hubs += 1

        if not dry_run:
            hub_file.write_text(content, encoding="utf-8")

    print(f"\n허브 노트: {created_hubs}개 처리\n")

    if args.hubs_only:
        print("--hubs-only 모드: 기존 노트 수정 건너뜀")
        return

    # ── 4. 기존 노트에 wikilink 섹션 추가 ───────────────────────
    modified = 0
    for note, values in sorted(note_hubs.items(), key=lambda x: str(x[0])):
        try:
            text = note.read_text(encoding="utf-8")
        except Exception:
            continue

        # 이미 섹션 있으면 갱신
        links_block = (
            f"\n{LINK_SECTION_MARKER}\n"
            "## 관련 허브\n\n"
            + "\n".join(
                f"- [[{HUBS_DIR}/{slugify(v)}|{v}]]"
                for v in sorted(values)
            )
            + "\n"
        )

        if LINK_SECTION_MARKER in text:
            # 기존 섹션 교체
            new_text = re.sub(
                rf"{re.escape(LINK_SECTION_MARKER)}.*",
                links_block.lstrip(),
                text,
                flags=re.DOTALL,
            )
        else:
            new_text = text.rstrip() + "\n" + links_block

        if new_text == text:
            continue

        rel = note.relative_to(vault)
        print(f"  [LINK] {rel} → {', '.join(sorted(values))}")
        modified += 1

        if not dry_run:
            note.write_text(new_text, encoding="utf-8")

    print(f"\n기존 노트 수정: {modified}개")
    print("\n완료! Obsidian 재시작 또는 Ctrl+Shift+G 로 그래프를 새로고침하세요.")


if __name__ == "__main__":
    main()
