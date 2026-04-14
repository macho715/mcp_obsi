# KG Dashboard — Node Type Ontology

> 소스 기준: `scripts/build_dashboard_graph_data.py`, `kg-dashboard/src/utils/graph-model.ts`, `kg-dashboard/src/types/graph.ts`

---

## 1. 개념 계층 (상위 → 하위)

```mermaid
graph TD
    Root["🌐 GraphNode\n모든 노드의 최상위 개념"]

    Root --> Infra["🏗️ InfrastructureEntity\n물리적 인프라"]
    Root --> LogisticsOps["🚢 LogisticsEntity\n물류 운영 실체"]
    Root --> KnowledgeEnt["💡 KnowledgeEntity\n지식·이슈"]

    Infra --> Hub["Hub\n물류 통합 거점\n예: MOSB"]
    Infra --> Warehouse["Warehouse\n창고·보관소"]
    Infra --> Site["Site\n납품 현장·설치지"]
    Infra --> Location["Location\n지리적 URI 참조"]

    LogisticsOps --> Shipment["Shipment\n운송 건\n★ 핵심 엔티티"]
    LogisticsOps --> Order["Order\nPO 번호"]
    LogisticsOps --> Vessel["Vessel\n선박 / 항공편"]
    LogisticsOps --> Vendor["Vendor\n공급업체"]

    KnowledgeEnt --> LogisticsIssue["LogisticsIssue\n물류 이슈 / 리스크"]
    KnowledgeEnt --> IncidentLesson["IncidentLesson\n사례 교훈 (Lesson Learned)"]

    style Root fill:#334155,color:#f1f5f9,stroke:#64748b
    style Infra fill:#1e3a5f,color:#bae6fd,stroke:#38bdf8
    style LogisticsOps fill:#1c3340,color:#a7f3d0,stroke:#34d399
    style KnowledgeEnt fill:#3b1f44,color:#e9d5ff,stroke:#a78bfa
    style Hub fill:#1e40af,color:#dbeafe,stroke:#3b82f6
    style Warehouse fill:#1e40af,color:#dbeafe,stroke:#3b82f6
    style Site fill:#1e40af,color:#dbeafe,stroke:#3b82f6
    style Location fill:#1e40af,color:#dbeafe,stroke:#3b82f6
    style Shipment fill:#065f46,color:#d1fae5,stroke:#10b981
    style Order fill:#166534,color:#dcfce7,stroke:#22c55e
    style Vessel fill:#166534,color:#dcfce7,stroke:#22c55e
    style Vendor fill:#166534,color:#dcfce7,stroke:#22c55e
    style LogisticsIssue fill:#7c2d12,color:#fed7aa,stroke:#f97316
    style IncidentLesson fill:#581c87,color:#ede9fe,stroke:#8b5cf6
```

---

## 2. 운영 관계 그래프 (엣지 레이블 포함)

```mermaid
graph LR
    SHP["Shipment\n운송 건"]

    SHP -->|hasOrder| ORD["Order\nPO 번호"]
    SHP -->|suppliedBy| VND["Vendor\n공급업체"]
    SHP -->|transportedBy| VSL["Vessel\n선박·항공"]
    SHP -->|consolidatedAt| HUB["Hub\n통합 거점"]
    SHP -->|storedAt| WHS["Warehouse\n창고"]
    SHP -->|deliveredTo| STE["Site\n납품 현장"]

    ISS["LogisticsIssue\n물류 이슈"] -->|affectsShipment| SHP
    ISS -->|affectsVessel| VSL
    ISS -->|affectsVendor| VND
    ISS -->|affectsHub| HUB
    ISS -->|affectsWarehouse| WHS
    ISS -->|affectsSite| STE
    ISS -->|affectsLocation| LOC["Location\nURI 위치"]

    LES["IncidentLesson\n사례 교훈"] -->|derivedFrom| ISS

    style SHP fill:#065f46,color:#d1fae5,stroke:#10b981,stroke-width:2px
    style ORD fill:#166534,color:#dcfce7,stroke:#22c55e
    style VND fill:#166534,color:#dcfce7,stroke:#22c55e
    style VSL fill:#166534,color:#dcfce7,stroke:#22c55e
    style HUB fill:#1e40af,color:#dbeafe,stroke:#3b82f6
    style WHS fill:#1e40af,color:#dbeafe,stroke:#3b82f6
    style STE fill:#1e40af,color:#dbeafe,stroke:#3b82f6
    style LOC fill:#1e3a5f,color:#bae6fd,stroke:#38bdf8
    style ISS fill:#7c2d12,color:#fed7aa,stroke:#f97316,stroke-width:2px
    style LES fill:#581c87,color:#ede9fe,stroke:#8b5cf6
```

---

## 3. 노드 타입 상세 표

| 타입 | 카테고리 | Excel 소스 컬럼 | 관계 (엣지) | 대시보드 역할 |
|---|---|---|---|---|
| **Shipment** | LogisticsEntity | `SHIP NO.` | 모든 엣지의 출발점 | Summary·Ego·Search 모든 뷰 노출 |
| **Order** | LogisticsEntity | `PO No.` | ← hasOrder | Ego·Search·Ontology 필터 시 노출 |
| **Vendor** | LogisticsEntity | `VENDOR` | ← suppliedBy | Ego·Search·Ontology 필터 시 노출 |
| **Vessel** | LogisticsEntity | `VESSEL NAME/ FLIGHT No.` | ← transportedBy | Ego·Search·Ontology 필터 시 노출 |
| **Hub** | InfrastructureEntity | `MOSB` (고정값 "MOSB") | ← consolidatedAt | Summary 뷰 포함, HOTSPOTS KPI 산정 |
| **Warehouse** | InfrastructureEntity | `WAREHOUSE_COLUMNS` 목록 | ← storedAt | Summary 뷰 포함 |
| **Site** | InfrastructureEntity | `SITE_COLUMNS` 목록 | ← deliveredTo | Summary 뷰 포함 |
| **Location** | InfrastructureEntity | 이슈 태그 URI | ← affectsLocation | 이슈 연결 시에만 등장 |
| **LogisticsIssue** | KnowledgeEntity | 메모리 노트 frontmatter | → 모든 인프라/운영 노드 | Summary 뷰 ISSUES KPI |
| **IncidentLesson** | KnowledgeEntity | 메모리 노트 (class: IncidentLesson) | → LogisticsIssue | 기본 뷰 숨김, Lesson 필터 시 노출 |

---

## 4. 대시보드 뷰별 노출 규칙

```mermaid
graph TD
    V1["Summary View\n(기본 뷰)"]
    V2["Ego View\n(노드 선택 시)"]
    V3["Search View\n(검색 결과)"]

    V1 -->|항상 포함| N1["Hub · Warehouse · Site"]
    V1 -->|이슈 존재 시| N2["LogisticsIssue"]
    V1 -->|연결된 경우| N3["Shipment (인프라 연결)"]
    V1 -->|숨김| N4["Order · Vendor · Vessel · IncidentLesson"]

    V2 -->|선택 노드 + 1-hop 이웃| N5["모든 타입 (Hub: 최대 24개 제한)"]

    V3 -->|검색어 매칭| N6["모든 타입 (label·metadata 검색)"]

    style V1 fill:#1e293b,color:#f1f5f9,stroke:#475569
    style V2 fill:#1e293b,color:#f1f5f9,stroke:#475569
    style V3 fill:#1e293b,color:#f1f5f9,stroke:#475569
```

---

## 5. 동적 속성

| 속성 | 대상 타입 | 조건 | 설명 |
|---|---|---|---|
| `isHubNode` (동적) | Hub | `degree >= 200` | 타입 무관, 연결 수 기준으로 Hub 식별 |
| `collapsedShipmentCount` | Hub | Ego 뷰에서 접힌 경우 | 그룹화된 Shipment 수 표시 |
| `collapsedVesselCount` | Hub | Ego 뷰에서 접힌 경우 | 그룹화된 Vessel 수 표시 |
| `collapsedVendorCount` | Hub | Ego 뷰에서 접힌 경우 | 그룹화된 Vendor 수 표시 |
| `analysisPath` | LogisticsIssue · IncidentLesson | 분석 노트 연결 시 | 볼트 내 분석 파일 경로 |

---

> 문서 생성: 2026-04-14  
> 소스 파일: `scripts/build_dashboard_graph_data.py` · `kg-dashboard/src/utils/graph-model.ts`
