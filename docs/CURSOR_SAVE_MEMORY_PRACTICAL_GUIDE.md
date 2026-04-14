# Cursor — ChatGPT/Claude 복붙 → `save_memory` 실전 가이드

> 목적: 외부 채팅을 Cursor에서 수동으로 정리해 production memory vault에 올리고, 이후 `search` → `fetch`로 재사용한다.  
> 자동 ingest는 필수 아님.  
> 계약 근거: `AGENTS.md`, `app/mcp_server.py`, `app/models.py`

---

## 운영 흐름

| 단계 | 담당 | 동작 |
|------|------|------|
| 1 | 사용자 | ChatGPT/Claude 대화 내용을 복사해 Cursor에 붙여 넣음 |
| 2 | Cursor 에이전트 / 사용자 | `save_memory`로 요약·사실·결정 형태로 저장 |
| 3 | (이후) ChatGPT/Claude | `search` → `fetch`로 저장본 조회 |

저장 위치·경로 규칙은 `AGENTS.md`의 Data Contracts를 따른다. 현재 신규 memory write는 `memory/YYYY/MM/...`에 저장되고, legacy `20_AI_Memory/...`는 read support로 유지된다.

---

## `memory_type` 값 (코드 enum)

`app/models.py`의 `MemoryType`과 동일하게 문자열로 넘긴다.

| 값 | 용도 |
|----|------|
| `conversation_summary` | 대화 전체를 한 건으로 묶을 때 |
| `decision` | “앞으로 이렇게 한다” 등 결정 |
| `project_fact` | 스택·경로·버전·검증된 사실 |
| `preference` | 톤·형식 등 사용자 선호 |
| `person` | 사람·연락·역할 등 (민감도 주의) |
| `todo` | 후속 작업만 분리해 둘 때 |

한 번에 여러 성격이 섞이면 **여러 번 `save_memory`** 하는 편이 검색에 유리하다.

---

## 도구 인자 정리 습관

- **title**: 검색에 걸리도록 짧고 구체적으로 (명사구 권장).
- **project**: 좁게 고정 (예: `mcp_obsidian`).
- **tags**: 3~7개 정도; 난립 방지.
- **source**: 모델·날짜·주제 힌트 (예: `chatgpt / 2026-03-28 / deploy-topic`).
- **content**: 아래 템플릿으로 **요약 중심** (원문 통째 장문은 피할 것).

민감 정보는 원문 그대로 넣지 말고 마스킹하거나 `AGENTS.md` 보안 경계를 따른다.

---

## 복붙 후 채울 본문 템플릿 (Markdown)

`save_memory`의 `content`에 그대로 넣어 쓴다.

```markdown
## 한 줄 요약
( title과 비슷하지만 맥락 한 줄 더 )

## 결정 (Decision)
- …

## 사실 (Facts)
- …

## 할 일 (Todo) — 해당할 때만
- …

## 가정 / 미확인 (Assumption)
- …

## 원문 발췌 (선택, 짧게)
필요할 때만 10~40줄 이내
```

---

## 옵션 비교 (운영 강도)

| 옵션 | 방식 | 비고 |
|------|------|------|
| A 보수 | `conversation_summary` 1건만 | 빠름; 세부 검색은 약함 |
| B 중간 | 요약 1건 + `decision` / `project_fact` 분리 저장 | 실전에 균형 좋음 |
| C 공격 | 스레드별·주제별 세분화 + 태그 많음 | 관리 부담 증가 |

---

## 리스크

- 원문을 길게 그대로 넣으면 이후 **검색 효율·스캔 가독성**이 떨어진다.
- **요약 + 핵심 사실 + 결정**이 중심이 되도록 유지한다.

---

## 읽기 측 (호환)

- `search` / `fetch`: 호환 래퍼 (`AGENTS.md` Tool Contract).
- 직접 도구명을 쓸 경우: `search_memory`, `get_memory` 등.

---

## 관련 문서

- `AGENTS.md` — 도구 이름, 경로 계약, Ask Before Changing
- `docs/plans/PLAN_MANUAL_MEMORY_WORKFLOW.md` — project-plan 산출: A~K 플랜, Evidence, 리스크, 30/60/90
- `docs/plans/PLAN_MEMORY_V2_MIGRATION.md` — `입력.MD` 기반 v1→v2 metadata migration 계획
- `docs/PROJECT_UPGRADE_20260328.md` — 스택/아키텍처 업그레이드 스카우트 (별도 주제)

---

*Last updated: 2026-03-28*
