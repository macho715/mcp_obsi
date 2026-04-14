"""
vault_dedup.py
──────────────
1. hub prefix 중복 제거: topic*/project*/entity* prefix 허브를 기본 허브로 병합
2. 빈 노트 목록 표시 (삭제는 선택적)
3. 기존 노트의 wikilink 섹션에서 prefix 중복 링크 정리

사용법:
  python scripts/vault_dedup.py --vault "C:/Users/SAMSUNG/Documents/Vault" --dry-run
  python scripts/vault_dedup.py --vault "C:/Users/SAMSUNG/Documents/Vault"
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

HUBS_DIR = "wiki/hubs"
LINK_SECTION_MARKER = "<!-- copilot-links -->"
PREFIX_PATTERN = re.compile(r"^(topic|project|entity)(.+)$")


def parse_frontmatter(text: str) -> dict:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except Exception:
        return {}


def extract_links_from_hub(text: str) -> set[str]:
    """허브 노트에서 [[...]] 링크 추출"""
    return set(re.findall(r"\[\[([^\]]+)\]\]", text))


def build_hub_content(hub_value: str, links: set[str], note_count: int) -> str:
    sorted_links = sorted(links)
    return (
        f"---\n"
        f"hub_kind: auto\n"
        f"hub_value: \"{hub_value}\"\n"
        f"note_count: {note_count}\n"
        f"---\n\n"
        f"# {hub_value}\n\n"
        f"_자동 생성된 허브 노트 — 이 값을 참조하는 모든 노트_\n\n"
        f"## 연결 노트 ({len(sorted_links)}개)\n\n"
        + "\n".join(f"- [[{lnk}]]" for lnk in sorted_links)
        + "\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--delete-empty", action="store_true",
                        help="빈 노트(valut/ 폴더) 삭제 포함")
    args = parser.parse_args()

    vault = Path(args.vault)
    hubs_path = vault / HUBS_DIR
    dry_run = args.dry_run

    print(f"Vault: {vault}")
    print(f"Dry-run: {dry_run}\n")

    if not hubs_path.exists():
        print("[ERROR] wiki/hubs 폴더 없음. vault_graph_linker.py 먼저 실행하세요.")
        sys.exit(1)

    # ── 1. prefix 중복 허브 병합 ─────────────────────────────────
    print("=" * 50)
    print("[ 1단계: prefix 중복 허브 병합 ]")
    print("=" * 50)

    hub_files = {f.stem: f for f in hubs_path.glob("*.md")}

    # base → [prefix_stems] 그룹핑
    groups: dict[str, list[str]] = defaultdict(list)
    for stem in hub_files:
        m = PREFIX_PATTERN.match(stem)
        if m:
            base = m.group(2)
            if base in hub_files:
                groups[base].append(stem)

    merged = 0
    deleted = 0

    for base_stem, prefix_stems in sorted(groups.items()):
        base_file = hub_files[base_stem]
        base_text = base_file.read_text(encoding="utf-8")
        base_fm = parse_frontmatter(base_text)
        base_links = extract_links_from_hub(base_text)

        extra_links: set[str] = set()
        to_delete: list[Path] = []

        for ps in prefix_stems:
            pf = hub_files[ps]
            pt = pf.read_text(encoding="utf-8")
            extra_links |= extract_links_from_hub(pt)
            to_delete.append(pf)

        new_links = base_links | extra_links
        if new_links != base_links:
            hub_value = base_fm.get("hub_value", base_stem)
            new_content = build_hub_content(hub_value, new_links, len(new_links))
            print(f"  [MERGE] {base_stem}.md ← {[p+'.md' for p in prefix_stems]}"
                  f"  ({len(base_links)} → {len(new_links)}개 링크)")
            if not dry_run:
                base_file.write_text(new_content, encoding="utf-8")
            merged += 1
        else:
            print(f"  [SKIP]  {base_stem}.md (추가 링크 없음) → {[p+'.md' for p in prefix_stems]} 삭제만")

        for pf in to_delete:
            print(f"  [DELETE] {pf.name}")
            if not dry_run:
                pf.unlink()
            deleted += 1

    # prefix 없이 단독으로 존재하는 중복(base 없는 prefix)도 정리
    # (base가 없는 경우는 그대로 둠)

    print(f"\n병합: {merged}개, 삭제: {deleted}개\n")

    # ── 2. 기존 노트 wikilink 섹션 업데이트 ─────────────────────
    print("=" * 50)
    print("[ 2단계: 노트 내 중복 hub 링크 정리 ]")
    print("=" * 50)

    # prefix → base 매핑 구성
    prefix_to_base: dict[str, str] = {}
    for base_stem, prefix_stems in groups.items():
        for ps in prefix_stems:
            prefix_to_base[f"{HUBS_DIR}/{ps}".replace("\\", "/")] = \
                f"{HUBS_DIR}/{base_stem}".replace("\\", "/")

    all_notes = [n for n in vault.rglob("*.md")
                 if ".obsidian" not in str(n)
                 and HUBS_DIR not in str(n).replace("\\", "/")]

    fixed = 0
    for note in sorted(all_notes):
        try:
            text = note.read_text(encoding="utf-8")
        except Exception:
            continue
        if LINK_SECTION_MARKER not in text:
            continue

        new_text = text
        changed = False
        for old_path, new_path in prefix_to_base.items():
            if old_path in new_text:
                new_text = new_text.replace(old_path, new_path)
                changed = True

        if changed:
            rel = note.relative_to(vault)
            print(f"  [FIX] {rel}")
            fixed += 1
            if not dry_run:
                note.write_text(new_text, encoding="utf-8")

    # 동일한 hub 링크 중복 라인 제거 (같은 [[path]] 두 번 이상 나오는 경우)
    for note in sorted(all_notes):
        try:
            text = note.read_text(encoding="utf-8")
        except Exception:
            continue
        if LINK_SECTION_MARKER not in text:
            continue

        parts = text.split(LINK_SECTION_MARKER)
        if len(parts) < 2:
            continue
        section = parts[1]
        lines = section.split("\n")
        seen = set()
        deduped = []
        for line in lines:
            if line.startswith("- [[") and line in seen:
                continue
            seen.add(line)
            deduped.append(line)
        new_section = "\n".join(deduped)
        if new_section != section:
            new_text = LINK_SECTION_MARKER.join([parts[0], new_section])
            rel = note.relative_to(vault)
            print(f"  [DEDUP-LINKS] {rel}")
            if not dry_run:
                note.write_text(new_text, encoding="utf-8")

    print(f"\n노트 링크 수정: {fixed}개\n")

    # ── 3. 빈 노트 목록 ─────────────────────────────────────────
    print("=" * 50)
    print("[ 3단계: 빈 노트 감지 ]")
    print("=" * 50)

    import hashlib
    from collections import defaultdict as dd2
    hash_map: dict[str, list[Path]] = dd2(list)
    for f in vault.rglob("*.md"):
        if ".obsidian" in str(f):
            continue
        try:
            content = f.read_bytes()
            h = hashlib.md5(content).hexdigest()
            hash_map[h].append(f)
        except Exception:
            continue

    empty_groups = {k: v for k, v in hash_map.items() if len(v) > 1}
    empty_deleted = 0

    for h, files in empty_groups.items():
        sample = files[0].read_text(encoding="utf-8", errors="replace").strip()
        print(f"\n  [중복 그룹] ({len(files)}개) - 내용: {repr(sample[:60])}")
        # keep 기준: 가장 긴 경로(깊은 경로), 나머지 삭제 후보
        keep = sorted(files, key=lambda x: len(x.parts))[-1]
        for f in files:
            marker = "KEEP" if f == keep else "DELETE"
            print(f"    [{marker}] {f.relative_to(vault)}")

        if args.delete_empty and not dry_run:
            for f in files:
                if f != keep and "valut" in str(f).lower():
                    f.unlink()
                    empty_deleted += 1
                    print(f"    → 삭제됨")

    if not args.delete_empty:
        print("\n  ※ 빈 노트 삭제하려면 --delete-empty 옵션 추가")

    print(f"\n빈 노트 삭제: {empty_deleted}개")
    print("\n완료! Obsidian Ctrl+Shift+G 로 그래프 새로고침")


if __name__ == "__main__":
    main()
