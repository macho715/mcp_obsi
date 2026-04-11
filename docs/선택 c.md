판정: **C안이 맞습니다.** `wiki`는 **직접 파일 쓰기**로 canonical KB를 유지하고, **완성된 분석 결과만** `save_memory`로 등록하는 하이브리드가 가장 덜 깨집니다. 이유는 현재 `vault/memory/`와 `vault/mcp_raw/`가 **대화/기록 중심 스키마**이고, 제안하신 `vault/wiki/`는 **장기 지식 스키마**이기 때문입니다. 둘을 같은 저장 규칙으로 합치면 탐색·정규화·수정 책임이 섞입니다. 업로드하신 정리도 `Obsidian = 영구 지식층`, `Cursor Skills = ingest/query/lint 절차층`, `memory = 기록층` 방향으로 잡고 있습니다.  또한 Obsidian은 내부 링크 네트워크를 전제로 지식을 조직하고, Local REST API 계열은 노트 전체뿐 아니라 heading/frontmatter 단위 patch도 지원하므로 `wiki/`를 별도 트리로 유지하는 쪽이 구조적으로 자연스럽습니다. ([Obsidian][1])

근거: **A안**은 기존 `save_memory / archive_raw`의 일일 append·인덱스 혜택은 좋지만, `wiki note`가 `memory/<YYYY>/<MM>/` 아래로 들어가면 **시간축 기록**과 **주제축 KB**가 섞여 canonical note를 잡기 어려워집니다. 반대로 **B안**은 KB 스키마가 가장 깨끗하지만, 현재 memory 인덱스에서 얻는 회수성과 세션 가시성을 잃습니다. 그래서 **C안**처럼 `wiki/`는 주제 기반으로 직접 관리하고, 그중 재사용 가치가 검증된 분석 노트만 `save_memory`로 등록해 memory 인덱스에 “포인터”를 남기는 구성이 가장 균형적입니다. Cursor도 Skills는 재사용 workflow, Rules/AGENTS.md는 지속 규칙으로 분리하므로, 저장 경로 역시 workflow와 storage semantics를 분리하는 편이 맞습니다. ([Cursor][2])

다음행동: 운영 규칙을 아래처럼 고정하십시오. **원문/대화기록은 `memory`·`mcp_raw`**, **정제된 지식은 `wiki`**, **승인된 분석 요약만 `memory`에 재등록**입니다. 이렇게 두면 Obsidian의 링크·backlink 구조는 `wiki`에서 유지되고, memory는 “최근 처리 이력 + 검색 진입점” 역할만 맡게 됩니다.  ([Obsidian][1])

## 최종 권고

### 왜 C안인가

| No | 안  | 판정     | 이유                                   | Risk                | Evidence       |
| -: | -- | ------ | ------------------------------------ | ------------------- | -------------- |
|  1 | A안 | 비추천    | memory chronology와 wiki taxonomy가 섞임 | canonical KB 붕괴     |                |
|  2 | B안 | 조건부    | KB는 가장 깨끗함                           | 기존 memory 인덱스 이점 상실 | ([GitHub][3])  |
|  3 | C안 | **추천** | KB와 memory 역할을 분리하면서도 인덱스 진입점 유지     | 동기화 규칙 필요           |  ([Cursor][2]) |

## 최종 저장 규칙

```text
vault/
  memory/          # 대화/작업 이력, 최근 분석 포인터, daily append
  mcp_raw/         # 원문/수집 로그/비정제 기록
  wiki/            # 장기 KB canonical notes
    index.md
    log.md
    sources/
    concepts/
    entities/
    analyses/
```

* `save_memory` 대상: **완성된 분석 요약, 승인된 결론, wiki note로 가는 포인터**
* `archive_raw` 대상: **원문, 임시 추출, ingest 전 자료**
* 직접 파일 쓰기 대상: **`wiki/sources/*`, `wiki/concepts/*`, `wiki/entities/*`, `wiki/analyses/*`**
* `memory`에는 **full canonical note를 중복 저장하지 않고**, `[[wiki/...]]` 링크 또는 파일 경로 포인터만 남김

이 방식은 Obsidian의 내부 링크 기반 KB 운영과 가장 잘 맞습니다. Obsidian은 note 간 internal links를 중심으로 지식 네트워크를 만들고, rename 시 링크 업데이트도 지원하므로 canonical page를 주제 트리로 고정하는 편이 유리합니다. ([Obsidian][1])

## 운영 플로우

### ingest

1. raw 수집 → `mcp_raw/` 또는 `raw/`
2. Gemma Skill이 분석
3. `wiki/sources/` 생성 또는 patch
4. 관련 `concepts/entities` patch
5. `wiki/index.md`, `wiki/log.md` 갱신
6. 최종 요약 3~10줄만 `save_memory`

### query

1. 먼저 `wiki/`에서 검색/독해
2. 답변 생성
3. 재사용 가치가 있으면 `wiki/analyses/` 저장
4. 그 note의 포인터만 `save_memory`

### lint

1. `wiki/` 전체 검사
2. contradiction / stale / orphan / evidence gap 도출
3. patch plan 생성
4. 승인 후 `wiki/` 수정
5. lint 결과 요약만 `save_memory`

Local REST API 계열이 note CRUD와 부분 patch를 지원하므로, 이 플로우는 직접 파일 쓰기보다도 “정밀 patch” 운영에 적합합니다. ([GitHub][3])

## A/B/C를 한 문장으로 정리

* **A안**은 “기록 시스템을 KB처럼 쓰는 것”
* **B안**은 “KB는 맞지만 회수 인덱스를 포기하는 것”
* **C안**은 “KB는 KB답게 두고, memory는 색인/타임라인으로만 쓰는 것”

현재 구조 설명 기준으로는 **C안이 가장 일관적**입니다. 

## 구현 규칙 5개

1. **`wiki`는 canonical only**
   같은 내용을 `memory`에 전문 복제하지 않음.

2. **`memory`는 pointer + summary only**
   예:
   `2026-04-07 | created [[wiki/analyses/karpathy-llm-wiki-operating-model]] | why: reusable synthesis`

3. **`mcp_raw`는 immutable 성격 유지**
   원문·중간 추출은 보관하되, KB 정제는 `wiki`에서만 수행.

4. **Skill은 storage-agnostic, route-aware**
   `obsidian-ingest/query/lint`는 내용 종류에 따라 `memory/raw/wiki` 중 목적지를 결정.

5. **승인 게이트는 wiki에만 강하게 적용**
   `lint`와 `analysis`는 `patch plan → 승인 → write`가 안전함.

Cursor의 Skills가 workflow 층이고 Rules가 상위 정책층이므로, 이 라우팅 규칙은 `AGENTS.md` 또는 Rules에 고정하는 편이 맞습니다. ([Cursor][2])

## 최종 문구

**최종안:**

* **A안 채택 안 함**
* **B안 단독도 안 함**
* **C안 채택**

  * `wiki = 직접 파일 쓰기`
  * `memory = save_memory로 요약/포인터만 등록`
  * `raw = archive_raw 유지`

## ZERO log

* **AMBER:** 현재 `save_memory / archive_raw`의 내부 인덱싱 규칙 자체는 사용 중인 MCP 구현 상세에 따라 다를 수 있습니다. 다만 질문의 핵심은 **정보 구조 설계**이므로, 경로 결정 원칙은 C안으로 고정해도 무방합니다. 
* **확정:** `wiki`를 `memory` 하위 chronology에 넣는 A안은 장기 KB 스키마를 약화시킬 가능성이 큽니다. 이는 현재 분리된 역할 정의와 충돌합니다. 

원하시면 다음 답변에서 바로 **`AGENTS.md용 라우팅 규칙 블록`**과 **`save_memory에 남길 포인터 템플릿`**까지 최종본으로 드리겠습니다.

[1]: https://obsidian.md/help/links?utm_source=chatgpt.com "Internal links - Obsidian Help"
[2]: https://cursor.com/docs/skills?utm_source=chatgpt.com "Agent Skills | Cursor Docs"
[3]: https://github.com/coddingtonbear/obsidian-local-rest-api?utm_source=chatgpt.com "coddingtonbear/obsidian-local-rest-api"
