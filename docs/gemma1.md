판정: **예, 제가 섞어서 답해서 결과가 달랐습니다.** 충돌 원인은 `Obsidian MCP 구현 가정`, `Skill 이름 기준`, `runtime 위치`, `Gemma를 구조에 넣는 방식`을 한 답변 안에서 분리하지 않았기 때문입니다. Cursor는 `Skills`와 `Rules/AGENTS.md`를 별도 층으로 두고, Obsidian 쪽도 `Local REST API 기반 MCP`와 `직접 vault 접근 MCP`가 공존합니다. ([Cursor][1])

근거: 업로드하신 안은 `Gemma 4 = 로컬 추론`, `Obsidian = 영구 지식층`, `Cursor Skills = ingest/query/lint 절차층`이라는 방향 자체는 맞습니다. 다만 그 안은 `Local REST API 기반 MCP`를 전제로 쓴 것이고, 제가 다른 답변에서는 `MCP 구현 일반론`까지 섞어 말해 구조가 흔들렸습니다.  ([GitHub][2])

다음행동: 아래 **충돌 정리표 기준으로 하나로 고정**하면 됩니다. 결론만 먼저 말하면, **최종안은 `Skill은 모델 비종속 이름`, `runtime은 vault 밖`, `v1은 3 Skills`, `Obsidian 접근층은 capability 기준`**입니다. ([Cursor][1])

## 충돌 정리표

| No | 충돌 항목                                        | 왜 달랐나                                                                                     | 최종 확정                                                                                                                                                                                  |
| -: | -------------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|  1 | `Obsidian MCP = Local REST API`인가            | 일부 MCP 서버는 Local REST API를 브리지로 쓰고, 일부는 플러그인 없이 vault를 직접 다룹니다.                           | **특정 구현명에 묶지 말고 `Obsidian Access Layer`로 추상화**. Skill은 `read/search/create/update/frontmatter` capability 기준으로 작성. ([GitHub][3])                                                       |
|  2 | `obsidian-ingest-gemma` vs `obsidian-ingest` | Gemma를 **엔진**으로 볼지, Skill을 **절차**로 볼지 섞였습니다. Cursor Skills는 재사용 capability/workflow 층입니다. | **Skill 이름에서 `-gemma` 제거**. 모델은 Rules/env에서 고정. ([Cursor][1])                                                                                                                          |
|  3 | `runtime/`을 vault 안에 둘지 밖에 둘지                | Obsidian search/graph에 운영 부산물이 섞이면 KB가 오염됩니다.                                             | **`runtime/`은 vault 밖**. 단일 루트만 가능하면 Excluded files로 숨김. Excluded files는 Search와 Unlinked mentions에서 제외되고, internal links는 vault 로컬 기준이라 vault 안에 vault를 두는 것도 비권장입니다. ([Obsidian][4]) |
|  4 | 3 Skills vs 4 Skills                         | `watch`를 초기부터 넣을지, 안정화 후 넣을지 설계 판단이 섞였습니다.                                                | **v1 = 3 Skills**, `watch`는 v1.5 옵션.                                                                                                                                                   |
|  5 | Gemma를 구조에 포함할지                              | 업로드안은 Gemma 4를 로컬 엔진으로 전제했고, 다른 답변은 모델 비종속 구조를 강조했습니다.                                    | **둘 다 맞지만 층이 다름**. 구조는 모델 비종속으로 설계하고, 기본 엔진만 Gemma 4로 둡니다. 업로드안의 방향은 유지.  ([Google AI for Developers][5])                                                                              |

## 최종안

**한 줄 정의:**
`Obsidian vault = KB SSOT` / `Cursor Rules+Skills = 운영 절차` / `Obsidian Access Layer = MCP 또는 REST/CLI` / `Gemma 4 = 기본 로컬 추론 엔진` / `runtime = vault 밖 작업 큐`

이 구성이 가장 일관됩니다. Cursor는 Skills와 Rules/AGENTS.md를 별도 레이어로 두고, Obsidian은 internal links·Backlinks·Graph view·Bases로 탐색층을 제공하며, Gemma 4는 텍스트·이미지 입력, thinking, system instructions, 긴 context를 제공하므로 로컬 KB 컴파일 엔진으로 넣기 좋습니다. ([Cursor][1])

## 최종 디렉터리

```text
workspace/
  AGENTS.md
  .cursor/
    rules/
      kb-core.mdc
      kb-style.mdc
    skills/
      obsidian-ingest/
        SKILL.md
      obsidian-query/
        SKILL.md
      obsidian-lint/
        SKILL.md
      obsidian-watch/          # optional, v1.5

  vault/
    raw/
      inbox/
      articles/
      pdf/
      notes/
      images/
    wiki/
      index.md
      log.md
      sources/
      concepts/
      entities/
      analyses/

  runtime/
    queue/
    patches/
    audits/
```

`runtime/`을 vault 밖으로 빼는 이유는 Search/Unlinked mentions/graph 오염을 피하기 위해서입니다. Obsidian은 internal links가 vault 로컬 기준이므로 `vault 안에 vault` 같은 중첩도 권장하지 않습니다. ([Obsidian][4])

## 최종 Skill 세트

### v1 필수

1. **`obsidian-ingest`**
   `raw/` source → `wiki/sources/` 생성 → `concepts/entities` patch → `index.md`·`log.md` 갱신

2. **`obsidian-query`**
   `index.md` → vault search → 관련 note read → 답변/분석 → 재사용 가치 있으면 `analyses/` 저장

3. **`obsidian-lint`**
   contradiction / stale claim / orphan page / missing cross-reference / evidence gap 점검 → **patch-plan만 생성** → 승인 후 반영

### v1.5 선택

4. **`obsidian-watch`**
   `raw/inbox/` triage → `runtime/queue/` 적재 → 승인 전까지는 직접 write 금지

여기서 핵심은 **Skill = workflow**, **Gemma = engine**으로 분리하는 것입니다. 그래서 Skill 이름에는 모델명을 넣지 않는 쪽이 최종적으로 맞습니다. Cursor의 Skills가 재사용 capability 층이기 때문입니다. ([Cursor][1])

## Obsidian 접근층 최종 규칙

이 부분이 이전 답변들을 하나로 합치는 핵심입니다.

* **원칙:** Skill은 `특정 MCP tool명`이 아니라 `기능` 기준으로 작성

  * `list/browse`
  * `search`
  * `read`
  * `create/update`
  * `frontmatter/heading patch`
* **이유:** Obsidian MCP 서버 구현이 여러 갈래입니다. Local REST API 기반도 있고, direct-vault/CLI 기반도 있습니다. 따라서 문서와 Skill은 **capability 기준**으로 고정해야 재사용성이 유지됩니다. ([GitHub][3])

## Gemma 4 위치 정정

여기서도 결과 차이가 났던 이유가 있었습니다.
**Gemma 4는 “구조”가 아니라 “기본 엔진”**입니다.

업로드안처럼 `Gemma 4 = 로컬 추론/컴파일 엔진`으로 두는 것은 타당합니다. 공식 문서 기준으로 Gemma 4는 E2B, E4B, 31B, 26B A4B 크기를 제공하고, thinking 및 multimodal 입력을 지원합니다. EmbeddingGemma는 retrieval·semantic similarity·classification·clustering용 별도 모델입니다.  ([Google AI for Developers][5])

업로드안의 하드웨어 전제인 `RTX 4060 Laptop 8GB / RAM 32GB`를 그대로 쓴다면, Gemma 4 공식 Q4_0 메모리 표상 `E2B 3.2GB`, `E4B 5.0GB`, `31B 17.4GB`, `26B A4B 15.6GB`이므로 **E4B 주력 + E2B 보조** 판단은 일관됩니다. 이 부분은 업로드안 전제가 유지될 때만 유효합니다.  ([Google AI for Developers][5])

## 그래서 최종 결론은 이것 하나입니다

* **KB의 단일 SSOT:** `vault/wiki/*.md`
* **원문 보관:** `vault/raw/*`는 immutable
* **절차층:** `Cursor Skills`
* **정책층:** `AGENTS.md + .cursor/rules`
* **접근층:** `Obsidian Access Layer`

  * REST-MCP든 direct-vault MCP든 가능
* **기본 엔진:** `Gemma 4`
* **운영 부산물:** `runtime/`에 분리
* **초기 범위:** `ingest/query/lint`만
* **확장 시점:** recall miss가 쌓일 때만 EmbeddingGemma

## ZERO log

* **정정:** 이전 답변 차이는 `구현 전제`와 `설계 권고`를 섞은 제 쪽 정리 문제였습니다.
* **AMBER:** `Local REST API 기반 MCP`는 매우 흔하지만 유일한 방식은 아닙니다. direct-vault/CLI 계열도 확인됩니다. ([GitHub][3])
* **AMBER:** Gemma 모델 추천은 업로드안의 장비 전제 의존입니다.  ([Google AI for Developers][5])

이제 기준은 하나로 고정하면 됩니다: **`obsidian-ingest / obsidian-query / obsidian-lint` 3종을 유지하고, Skill 문서는 capability 기반으로, 모델은 Gemma 4 기본값으로 분리**.

[1]: https://cursor.com/docs/skills?utm_source=chatgpt.com "Agent Skills | Cursor Docs"
[2]: https://github.com/coddingtonbear/obsidian-local-rest-api?utm_source=chatgpt.com "coddingtonbear/obsidian-local-rest-api"
[3]: https://github.com/punkpeye/obsidian-mcp?utm_source=chatgpt.com "punkpeye/obsidian-mcp: MCP Server for Obsidian"
[4]: https://obsidian.md/help/plugins/search?utm_source=chatgpt.com "Search - Obsidian Help"
[5]: https://ai.google.dev/gemma/docs/core?utm_source=chatgpt.com "Gemma 4 model overview | Google AI for Developers"
