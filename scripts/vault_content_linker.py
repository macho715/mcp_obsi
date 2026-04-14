"""
vault_content_linker.py
───────────────────────
고립된 Obsidian 노트를 내용(파일명 + frontmatter + 본문) 기반으로
wiki/hubs/ 허브 노트에 자동 연결합니다.

점수 기준:
  파일명(stem) 패턴 일치  × 5
  frontmatter 값 일치     × 3
  본문 패턴 일치(건수)    × 1
  ───────────────────────────
  점수 ≥ 3 이고 상위 10개 허브만 연결

사용법:
  python scripts/vault_content_linker.py --vault "C:/Users/SAMSUNG/Documents/Vault" --dry-run
  python scripts/vault_content_linker.py --vault "C:/Users/SAMSUNG/Documents/Vault"
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

HUBS_DIR = "wiki/hubs"
LINK_SECTION_MARKER = "<!-- copilot-links -->"

# 연결 제외 폴더
EXCLUDE_DIRS = {".obsidian", "10_Daily", HUBS_DIR.replace("/", "\\")}

# 점수 가중치
W_STEM = 5
W_FM   = 3
W_BODY = 1

# 최소 연결 점수 / 최대 허브 수
MIN_SCORE    = 3
MAX_HUBS     = 10

# frontmatter에서 허브 매칭에 쓸 필드
FM_FIELDS = ["project", "projects", "tags", "entities", "topics"]


# ── 허브 패턴 빌드 ────────────────────────────────────────────────────────────

def hub_to_patterns(slug: str) -> list[re.Pattern]:
    """
    hub 슬러그를 검색 패턴 목록으로 변환.
    예) abu_dhabi  →  [re.compile(r"abu[\s_\-]?dhabi", re.I),
                       re.compile(r"abu_dhabi", re.I)]
    단일 토큰(구분자 없음)은 패턴 1개만 반환.
    """
    # 구분자(_,-) 위치 찾기
    tokens = re.split(r"[_\-]", slug)
    tokens = [t for t in tokens if t]

    patterns = []
    if len(tokens) >= 2:
        # 복합어: 구분자 사이를 [\s_\-]? 로 허용
        joined = r"[\s_\-]?".join(re.escape(t) for t in tokens)
        patterns.append(re.compile(joined, re.IGNORECASE))
    # 슬러그 자체도 그대로 패턴으로
    patterns.append(re.compile(re.escape(slug), re.IGNORECASE))
    return patterns


def build_hub_index(hubs_path: Path) -> dict[str, list[re.Pattern]]:
    """slug → [patterns] 딕셔너리"""
    index: dict[str, list[re.Pattern]] = {}
    for f in hubs_path.glob("*.md"):
        slug = f.stem
        index[slug] = hub_to_patterns(slug)
    return index


# ── frontmatter 파싱 ──────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except Exception:
        return {}


def fm_values(fm: dict) -> set[str]:
    """frontmatter에서 project/tags/entities/topics 값 추출"""
    vals: set[str] = set()
    for field in FM_FIELDS:
        v = fm.get(field)
        if not v:
            continue
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    vals.add(item.strip().lower())
        elif isinstance(v, str):
            vals.add(v.strip().lower())
    return vals


# ── 점수 계산 ─────────────────────────────────────────────────────────────────

def score_note(
    stem: str,
    fm_vals: set[str],
    body: str,
    slug: str,
    patterns: list[re.Pattern],
) -> int:
    score = 0

    # 1. 파일명(stem) 매칭
    for pat in patterns:
        if pat.search(stem):
            score += W_STEM
            break  # 한 번만 가산

    # 2. frontmatter 값 매칭
    slug_lower = slug.lower()
    for val in fm_vals:
        # 정확 일치 또는 슬러그가 값 안에 포함
        if slug_lower == val or slug_lower in val.replace("-", "_"):
            score += W_FM
            break

    # 3. 본문 매칭 (매칭 건수 × W_BODY, 최대 5회)
    body_hits = 0
    for pat in patterns:
        body_hits += len(pat.findall(body))
    score += min(body_hits, 5) * W_BODY

    return score


# ── 대상 노트 수집 ────────────────────────────────────────────────────────────

def is_excluded(path: Path, vault: Path) -> bool:
    rel = str(path.relative_to(vault)).replace("\\", "/")
    for ex in EXCLUDE_DIRS:
        if ex.replace("\\", "/") in rel:
            return True
    return False


def is_isolated(text: str) -> bool:
    """wikilink가 전혀 없으면 고립 노트"""
    return "[[" not in text


# ── wikilink 섹션 갱신 ───────────────────────────────────────────────────────

def build_links_block(hub_slugs: list[str]) -> str:
    lines = "\n".join(
        f"- [[{HUBS_DIR}/{slug}|{slug}]]" for slug in hub_slugs
    )
    return f"\n{LINK_SECTION_MARKER}\n## 관련 허브\n\n{lines}\n"


def update_note(text: str, hub_slugs: list[str]) -> str:
    block = build_links_block(hub_slugs)
    if LINK_SECTION_MARKER in text:
        return re.sub(
            rf"{re.escape(LINK_SECTION_MARKER)}.*",
            block.lstrip(),
            text,
            flags=re.DOTALL,
        )
    return text.rstrip() + "\n" + block


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True)
    parser.add_argument("--dry-run", action="store_true",
                        help="파일 수정 없이 연결 목록만 출력")
    parser.add_argument("--min-score", type=int, default=MIN_SCORE,
                        help=f"최소 연결 점수 (기본 {MIN_SCORE})")
    parser.add_argument("--max-hubs", type=int, default=MAX_HUBS,
                        help=f"노트당 최대 허브 연결 수 (기본 {MAX_HUBS})")
    args = parser.parse_args()

    vault    = Path(args.vault)
    hubs_path = vault / HUBS_DIR.replace("/", "\\")

    if not vault.exists():
        print(f"[ERROR] vault 경로 없음: {vault}")
        sys.exit(1)
    if not hubs_path.exists():
        print("[ERROR] wiki/hubs 폴더 없음. vault_graph_linker.py 먼저 실행하세요.")
        sys.exit(1)

    print(f"Vault   : {vault}")
    print(f"Dry-run : {args.dry_run}")
    print(f"Min score / Max hubs : {args.min_score} / {args.max_hubs}\n")

    # 허브 인덱스 로드
    hub_index = build_hub_index(hubs_path)
    print(f"허브 인덱스: {len(hub_index)}개\n")

    # 대상 노트 수집 (고립 노트만)
    all_notes = [
        f for f in vault.rglob("*.md")
        if not is_excluded(f, vault)
    ]
    isolated = []
    for f in all_notes:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
            if is_isolated(text):
                isolated.append(f)
        except Exception:
            pass

    print(f"전체 노트: {len(all_notes)}개 / 고립 노트: {len(isolated)}개\n")

    # 각 고립 노트 처리
    processed = 0
    skipped   = 0

    for note in sorted(isolated, key=lambda x: x.name):
        try:
            text = note.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        stem    = note.stem
        fm      = parse_frontmatter(text)
        fmv     = fm_values(fm)
        # frontmatter 이후 본문만 스캔 (속도 + 정확도)
        body_match = re.sub(r"^---.*?---\s*\n", "", text, flags=re.DOTALL)

        # 허브별 점수 계산
        scored: list[tuple[int, str]] = []
        for slug, patterns in hub_index.items():
            s = score_note(stem, fmv, body_match, slug, patterns)
            if s >= args.min_score:
                scored.append((s, slug))

        if not scored:
            skipped += 1
            continue

        # 점수 내림차순 정렬 → 상위 N개
        scored.sort(key=lambda x: -x[0])
        top_slugs = [slug for _, slug in scored[: args.max_hubs]]

        rel = note.relative_to(vault)
        hubs_str = ", ".join(f"{slug}({sc})" for sc, slug in scored[:args.max_hubs])
        print(f"  [LINK] {rel}")
        print(f"         → {hubs_str}")

        if not args.dry_run:
            new_text = update_note(text, top_slugs)
            note.write_text(new_text, encoding="utf-8")

        processed += 1

    print(f"\n처리: {processed}개 / 연결 대상 없음(건너뜀): {skipped}개")
    if args.dry_run:
        print("\n[Dry-run] 실제 파일 수정 없음. --dry-run 제거 후 재실행하면 적용됩니다.")
    else:
        print("\n완료! Obsidian Ctrl+Shift+G 로 그래프 새로고침")


if __name__ == "__main__":
    main()
