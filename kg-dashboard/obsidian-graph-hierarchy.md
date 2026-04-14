# Obsidian Vault — 그래프 계층 구조 문서

> 기준 날짜: 2026-04-14  
> 볼트 경로: `C:\Users\SAMSUNG\Documents\Vault`  
> 총 노트: ~560개 | 허브: 158개 | 분석: 115개 | 원문: 102개

---

## 1. 전체 계층 구조 (Top-Down)

```mermaid
graph TD
    ROOT["🌐 wiki/index.md\n루트 색인 노드\n(167개 링크 발산)"]

    ROOT --> META["📋 메타 노드\nwiki/log.md\nwiki/claude.md"]
    ROOT --> DAILY["📅 일간 노트\n10_Daily/\n4개 (2026-04-09 ~ 14)"]

    ROOT --> HUB_CORE["🔵 핵심 허브 (6개)\nwiki/hubs/ — 연결 20+"]
    ROOT --> HUB_MID["🟢 중형 허브 (14개)\nwiki/hubs/ — 연결 5-19"]
    ROOT --> HUB_SMALL["⚪ 소형 허브 (138개)\nwiki/hubs/ — 연결 1-4"]

    HUB_CORE --> ISSUE["📊 물류 이슈 분석\nwiki/analyses/logistics_issue_*\n105개"]
    HUB_CORE --> GUIDE["📄 가이드라인\nwiki/analyses/guideline_*\n6개"]
    HUB_CORE --> ARTICLE["📰 원문 아티클\nraw/articles/\n102개"]
    HUB_CORE --> MCP_RAW["🗃️ MCP 아카이브\nmcp_raw/\n25개"]

    HUB_MID --> ISSUE
    HUB_MID --> ARTICLE
    HUB_MID --> MCP_RAW

    HUB_SMALL --> ARTICLE
    HUB_SMALL --> MCP_RAW

    ROOT --> ENTITY["🏷️ 엔티티 노트\nwiki/entities/\n6개"]
    ROOT --> CONCEPT["💡 개념 노트\nwiki/concepts/\n3개"]
    ROOT --> MEMORY["🧠 메모리 포인터\nmemory/\n18개"]

    style ROOT fill:#1e40af,color:#dbeafe,stroke:#3b82f6,stroke-width:3px
    style META fill:#1e293b,color:#94a3b8,stroke:#475569
    style DAILY fill:#1e293b,color:#94a3b8,stroke:#475569
    style HUB_CORE fill:#065f46,color:#d1fae5,stroke:#10b981,stroke-width:2px
    style HUB_MID fill:#166534,color:#dcfce7,stroke:#22c55e
    style HUB_SMALL fill:#14532d,color:#bbf7d0,stroke:#4ade80
    style ISSUE fill:#7c2d12,color:#fed7aa,stroke:#f97316
    style GUIDE fill:#581c87,color:#ede9fe,stroke:#8b5cf6
    style ARTICLE fill:#1e3a5f,color:#bae6fd,stroke:#38bdf8
    style MCP_RAW fill:#1c3340,color:#a7f3d0,stroke:#34d399
    style ENTITY fill:#3b1f44,color:#e9d5ff,stroke:#a78bfa
    style CONCEPT fill:#3b1f44,color:#e9d5ff,stroke:#a78bfa
    style MEMORY fill:#422006,color:#fef3c7,stroke:#f59e0b
```

---

## 2. 핵심 허브 연결 상세 (상위 6개)

```mermaid
graph LR
    IDX["🌐 index\n(루트)"]

    IDX --> LOG["🚢 logistics\n107개 노트 연결"]
    IDX --> ANA["📊 analysis\n102개 노트 연결"]
    IDX --> ABU["🏙️ abu_dhabi\n88개 노트 연결"]
    IDX --> HUB["🔗 hub\n85개 노트 연결"]
    IDX --> CRD["⚙️ coordination\n85개 노트 연결"]
    IDX --> MCP["🧠 mcp_obsidian\n20개 노트 연결"]

    LOG --> L1["logistics_issue_abu_dhabi_*\n(~80개)"]
    LOG --> L2["raw/articles/logistics_*\n(~20개)"]

    ANA --> A1["wiki/analyses/guideline_*\n(6개)"]
    ANA --> A2["wiki/analyses/*\n(기타 분석)"]

    ABU --> AB1["abu dhabi 관련\n물류 이슈·아티클"]

    HUB --> H1["MOSB·허브 관련 노트"]

    CRD --> C1["조정·운영 관련 노트"]

    MCP --> M1["memory/*.md\n(18개 포인터)"]
    MCP --> M2["mcp_raw/**\n(25개 아카이브)"]

    style IDX fill:#1e40af,color:#dbeafe,stroke:#3b82f6,stroke-width:3px
    style LOG fill:#065f46,color:#d1fae5,stroke:#10b981,stroke-width:2px
    style ANA fill:#065f46,color:#d1fae5,stroke:#10b981,stroke-width:2px
    style ABU fill:#065f46,color:#d1fae5,stroke:#10b981,stroke-width:2px
    style HUB fill:#065f46,color:#d1fae5,stroke:#10b981,stroke-width:2px
    style CRD fill:#065f46,color:#d1fae5,stroke:#10b981,stroke-width:2px
    style MCP fill:#065f46,color:#d1fae5,stroke:#10b981,stroke-width:2px
```

---

## 3. 노드 타입 계층 정의

```mermaid
graph TD
    T0["계층 0 — Root\n1개"]
    T1["계층 1 — Navigation\n메타·일간 노트 7개"]
    T2["계층 2 — Hub\n158개 허브 노드"]
    T3["계층 3 — Content\n분석·원문·아카이브 ~250개"]
    T4["계층 4 — Memory\n메모리 포인터 18개"]

    T0 --> T1
    T0 --> T2
    T2 --> T3
    T3 --> T4

    T2 -.->|"소형 허브는\n직접 연결"| T3

    subgraph Root["계층 0"]
        R1["wiki/index.md"]
    end

    subgraph Nav["계층 1 — Navigation"]
        N1["wiki/log.md"]
        N2["wiki/claude.md"]
        N3["10_Daily/2026-04-*.md"]
    end

    subgraph Hubs["계층 2 — Hub (158개)"]
        H1["핵심 (20+)\nlogistics · analysis\nabu_dhabi · hub\ncoordination · mcp_obsidian"]
        H2["중형 (5-19)\nkb · llm · wiki\nrolefact · supply_chain\ngemma_4 · warehouse…"]
        H3["소형 (1-4)\n138개 A-Z"]
    end

    subgraph Content["계층 3 — Content (~250개)"]
        C1["wiki/analyses/logistics_issue_*\n물류 이슈 분석 105개"]
        C2["wiki/analyses/guideline_*\n가이드라인 6개"]
        C3["wiki/entities/ 6개\nwiki/concepts/ 3개"]
        C4["raw/articles/ 102개\n원문·클립"]
        C5["mcp_raw/ 25개\nMCP 아카이브"]
    end

    subgraph Mem["계층 4 — Memory (18개)"]
        M1["memory/2026/04/MEM-*.md\n포인터·요약·결정 기록"]
    end

    style R1 fill:#1e40af,color:#dbeafe,stroke:#3b82f6
    style H1 fill:#065f46,color:#d1fae5,stroke:#10b981
    style H2 fill:#166534,color:#dcfce7,stroke:#22c55e
    style H3 fill:#14532d,color:#bbf7d0,stroke:#4ade80
    style C1 fill:#7c2d12,color:#fed7aa,stroke:#f97316
    style C2 fill:#581c87,color:#ede9fe,stroke:#8b5cf6
    style C4 fill:#1e3a5f,color:#bae6fd,stroke:#38bdf8
    style C5 fill:#1c3340,color:#a7f3d0,stroke:#34d399
    style M1 fill:#422006,color:#fef3c7,stroke:#f59e0b
```

---

## 4. 링크 방향 및 연결 규칙

```mermaid
graph TD
    subgraph 연결_생성_방법["연결 생성 방법"]
        S1["vault_graph_linker.py\nfrontmatter 기반\n(project · tags · entities · topics)"]
        S2["vault_content_linker.py\n파일명·본문 키워드 기반\n(score ≥ 3, top 10)"]
        S3["수동 작성\nwiki/analyses/ 내\n[[wiki/index]] backlink"]
    end

    S1 -->|"<!-- copilot-links --> 섹션 추가"| HUB2["wiki/hubs/<slug>.md"]
    S2 -->|"<!-- copilot-links --> 섹션 추가"| HUB2
    S3 -->|"[[wiki/index]] 직접 링크"| IDX2["wiki/index.md"]

    HUB2 -->|"허브 → 원본 노트 역방향 없음\n(단방향)"| NOTE["Content 노트"]
    IDX2 -->|"index → hub 전체 연결\n(2026-04-14 추가)"| HUB2

    style S1 fill:#1e3a5f,color:#bae6fd,stroke:#38bdf8
    style S2 fill:#1e3a5f,color:#bae6fd,stroke:#38bdf8
    style S3 fill:#1e3a5f,color:#bae6fd,stroke:#38bdf8
    style HUB2 fill:#065f46,color:#d1fae5,stroke:#10b981
    style IDX2 fill:#1e40af,color:#dbeafe,stroke:#3b82f6
```

---

## 5. 폴더 구조 요약표

| 계층 | 경로 | 노트 수 | 역할 | 연결 방향 |
|---|---|---|---|---|
| **0 — Root** | `wiki/index.md` | 1 | 전체 색인, 모든 허브로 발산 | → 허브 158개 |
| **1 — Navigation** | `wiki/log.md`, `wiki/claude.md`, `10_Daily/` | 7 | 메타·일간 기록 | ← index |
| **2 — Hub (핵심)** | `wiki/hubs/` (note_count ≥ 20) | 6 | 대형 클러스터 앵커 | ↔ Content |
| **2 — Hub (중형)** | `wiki/hubs/` (5 ≤ count < 20) | 14 | 중형 토픽 집결 | ↔ Content |
| **2 — Hub (소형)** | `wiki/hubs/` (count < 5) | 138 | 단일 토픽 연결 | → Content |
| **3 — Analysis** | `wiki/analyses/logistics_issue_*` | 105 | 물류 이슈 분석 노트 | ← 허브 · → index |
| **3 — Guideline** | `wiki/analyses/guideline_*` | 6 | 가이드라인 문서 | ← 허브 · → index |
| **3 — Entity/Concept** | `wiki/entities/`, `wiki/concepts/` | 9 | 엔티티·개념 정의 | ← 허브 |
| **3 — Article** | `raw/articles/` | 102 | 원문·웹클립 | ← 허브 |
| **3 — Archive** | `mcp_raw/` | 25 | MCP 대화 아카이브 | ← 허브 |
| **4 — Memory** | `memory/2026/04/` | 18 | MCP 메모리 포인터 | ← mcp_obsidian 허브 |

---

## 6. 그래프 뷰 노드 크기 해석

Obsidian 그래프 뷰에서 노드 크기 = 백링크(연결) 수 기준:

| 노드 크기 | 해당 노드 | 연결 수 |
|---|---|---|
| **초대형** | `wiki/hubs/logistics` | 107+ |
| **대형** | `wiki/hubs/analysis`, `abu_dhabi`, `hub`, `coordination` | 85-102 |
| **중형** | `wiki/index.md` | 167 (outlink 기준) |
| **소형** | 나머지 허브·콘텐츠 노트 | 1-20 |

> **Note**: `index.md`는 outlink(발신 링크) 167개이나 backlink(수신)는 46개.  
> 허브 노드들이 `index`를 역링크하지 않아 그래프 뷰에서 index 노드 크기가 작게 표시될 수 있음.

---

> 생성: 2026-04-14  
> 관련 스크립트: `scripts/vault_graph_linker.py` · `scripts/vault_content_linker.py` · `scripts/vault_dedup.py`  
> 관련 문서: `kg-dashboard/node-type-ontology.md` · `kg-dashboard/그래프 TTL 자료 생성 관련 파일.md`
