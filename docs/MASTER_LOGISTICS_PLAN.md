# UAE HVDC Logistics - WhatsApp 지식화 통합 마스터 플랜 (Great Plan)

**Version:** v4.2 (Knowledge Wiki & Graph Centric)  
**Date:** 2026-04-09  
**Scope:** 6개 주요 물류 WhatsApp 채널 통합 및 Obsidian 지식 베이스(Wiki) + 지식 그래프(Knowledge Graph) 설계  

---

## 1. 목적 및 핵심 개요 (Executive Summary)

본 마스터 플랜의 궁극적인 목적은 **분산된 6개의 WhatsApp 물류 그룹챗 대화를 통합하여, 영구적이고 검색 가능한 '옵시디언 지식 베이스(Obsidian Knowledge Wiki)'로 자산화하는 것**입니다.

물류 현장에서 발생하는 수만 건의 메시지들은 단순한 일회성 알림이 아니라, 지연(Delay), 사고(Damage), 통관 이슈(Customs Hold) 등의 원인과 해결책이 담긴 핵심 데이터입니다. 본 계획은 각 채널의 역할을 명확히 하고 대화 규약을 표준화하여, **LLM(gemma4)이 대화 로그를 읽고 스스로 '이슈-조치-교훈' 형태의 위키 노트를 작성하도록 하는 자동화 파이프라인**을 구축함과 동시에, 엑셀 관리를 탈피한 **온톨로지 지식 그래프(Knowledge Graph)** 체계를 설계합니다.

---

## 2. 지식 추출을 위한 6대 채널 역할 (6-Channel Knowledge Sources)

각 채널은 단순히 화물이 이동하는 경로일 뿐만 아니라, **특정 도메인의 이슈와 해결(Lessons Learned) 지식이 생산되는 소스(Source)**입니다.

| 채널명 (WhatsApp) | 지식 소스 역할 (Knowledge Domain) | 주요 추출 대상 (Key Extraction Targets) |
| :--- | :--- | :--- |
| **Abu Dhabi Logistics** | **중앙 통제 및 거점 조율 지식** | 다중 현장 간 장비 경합 해결 사례, 전역(Program) 우선순위 조율 결과 |
| **DSV Delivery** | **육상 운송 및 현장 하역 지식** | 트레일러 대기(Detention) 발생 원인, 통관 서류(MSDS/FANR) 누락 대처법 |
| **[HVDC] Project Lightning** | **해상 운송 프로그램 지식** | 선박 운항 지연(SITREP) 사유, 빈 컨테이너(CCU) 체화 원인, OSDR 처리 이력 |
| **Jopetwil 71 Group** | **바지선 및 항만 특화 지식** | 날씨/조수간만(Tide)에 따른 하역 중단 사례, 특수화물(HCS) 고박/양하 이슈 |
| **MIR Logistics** | **MIR 현장 수령 및 공간 지식** | 하역 순서(Sequence) 꼬임 사례, Indoor 창고 포화(Full) 시 조치 이력 |
| **SHU Logistics** | **SHU 현장 수령 및 검수 지식** | 현장 검수(IRN/Test Report) 지연 사유, 자재 불출 시 타 부서와의 분쟁 조정 사례 |

---

## 3. 고품질 지식 생성을 위한 표준 운영 절차 (SOP for Data Quality)

LLM(gemma4)이 채팅 로그에서 정확한 이슈와 원인을 분석해 내려면, 대화의 패턴이 어느 정도 정규화되어 있어야 합니다. 이를 위해 6개 채널에 다음의 규칙을 공통 적용합니다.

### 3.1. 통합 태그 시스템 (Standardized Tagging)
모든 주요 이슈 발생 및 조치 시 첫 줄에 태그를 사용하여, 파이썬 스크립트가 해당 메시지를 즉시 '위험 이벤트'로 캡처할 수 있게 합니다.
*   **[URGENT]**, **[ACTION]**, **[FYI]**, **[ETA]**
*   **[RISK]**, **[COST]** (추가 비용 발생 및 지연 경보)
*   **[GATE]**, **[CRANE]**, **[MANIFEST]** (출입, 장비, 서류 이슈)

### 3.2. 사전 제약(Constraint) 기반 일정 공유
사후 변명이 아닌 사전 제약 조건이 대화에 남아 있어야, LLM이 '예측 가능한 지연'이었는지 판별할 수 있습니다.
*   **D-1 16:00 Planning**: 익일 배송/운항 계획 사전 확정 (대상 현장, 수량, 장비, 서류 상태 포함).
*   **날씨/조수간만**: 해상 하역 시 Tide/Fog 등을 사전에 명시.
*   **공간/장비**: 현장 하역 장비 미비 또는 창고 Full 시 출발 전 **"Hold at DSV"** 선언.

### 3.3. 시간순 이력 보고 (2-Track Dates)
이중 계산 오류가 위키에 기록되는 것을 막기 위해, "창고 처리일"과 "현장 하역일"을 명확히 구분하여 보고합니다.

### 3.4. Flow Code v3.5 (비강제성 권고 지표)
물류 동선의 효율성을 평가하기 위해 Flow Code(0~5) 체계를 참조합니다.
> **⚠️ 주의 (No Hard Constraint)**: Flow Code 3.5는 물류 흐름 패턴을 분석하기 위한 **권고적 추적 지표(Advisory Metric)**입니다. 시스템 데이터 정합성을 위한 기준일 뿐이며, **이 코드를 지키기 위해 현장의 물리적인 긴급 화물 운송을 강제로 중단(Blocking)해서는 절대 안 됩니다.**

---

## 4. 지식 그래프(Knowledge Graph) 데이터 모델 설계 (HVDC STATUS 기준)

단순한 텍스트 지식(Wiki)을 넘어, `HVDC STATUS.xlsx`에 담긴 방대한 물류 이동 이력 데이터를 유기적인 지식 그래프(온톨로지)로 변환합니다. 모든 물류의 이동은 개별 엑셀 행이 아닌 **SCT SHIP NO.**를 중심 노드로 하는 네트워크로 연결됩니다.

### 4.1. 핵심 노드(Nodes) 식별자
| 엔티티 (Class) | 설명 및 데이터 인스턴스 예시 |
| :--- | :--- |
| **Shipment** | 물류 배송의 핵심 추적 단위 (예: `SCT SHIP NO: hvdc-adopt-xxx-0000`) |
| **Order** | 구매 및 발주 계약 단위 (예: `LPO NO`) |
| **Vendor** | 자재 공급업체 (예: `Hitachi`, `Siemens`, `Prysmian`) |
| **Vessel** | 해상 운송 수단 및 바지선 (예: `LCT 선박`, `JPT71`, `Thuraya`) |
| **Hub** | 중앙 물류 집하 거점 (예: `MOSB`) |
| **Warehouse** | 육상 보관 창고 (예: `DSV Indoor`, `Al Markaz`, `AAA Storage`) |
| **Site** | 최종 도착 육상/해상 4개 현장 (예: `AGI`, `DAS`, `MIR`, `SHU`) |
| **LogisticsIssue** | 물류 운영 중 발생한 지연/사고/이슈 이벤트 |

### 4.2. 관계 연결망 (Relationships / Edges)
중심 노드인 **Shipment (SCT SHIP NO.)**를 기준으로 다음과 같이 데이터가 방향성(Directed Graph)을 갖고 연결됩니다.

*   `[Shipment]` **hasOrder** `[LPO NO]`
    *   해당 선적이 어떤 구매 발주 번호에 속하는지 연결.
*   `[Shipment]` **suppliedBy** `[Vendor]`
    *   이 화물을 공급한 벤더(Vendor) 연결.
*   `[Shipment]` **storedAt** `[Warehouse]`
    *   입항 후 어떤 창고(들)를 거치고 보관되었는지 이력 연결.
*   `[Shipment]` **consolidatedAt** `[Hub (MOSB)]`
    *   해상 출하 전 MOSB를 경유하고 집하되었는지 여부 연결.
*   `[Shipment]` **transportedBy** `[Vessel (LCT 선박)]`
    *   해상 운송 시 어떤 LCT 선박에 적재되어 이동했는지 연결.
*   `[Shipment]` **deliveredTo** `[Site (AGI/DAS/MIR/SHU)]`
    *   최종적으로 도착한 현장 4곳 중 하나로 연결.
*   `[LogisticsIssue]` **occursAt** `[Site/Warehouse/Hub]`
    *   해당 물류 이슈가 어느 장소(현장/창고/허브)에서 발생했는지 연결.
*   `[LogisticsIssue]` **relatedTo** `[Vessel/Vendor]`
    *   해당 이슈가 어떤 선박이나 벤더와 연관되어 있는지 연결.

### 4.3. 지식 그래프 활용 방안 (Graph Queries)
엑셀의 한계를 벗어나, 다차원적인 물류 추적 및 시맨틱 검색(SPARQL/RAG)이 가능해집니다.
*   *"Vendor A가 공급한 화물 중, MOSB를 거쳐 AGI로 간 물량은 몇 개이며 주로 어떤 LCT 선박을 이용했는가?"*
*   *"특정 LPO NO에 묶인 화물들이 현재 어느 창고(Warehouse)와 어느 현장(Site)에 분산되어 있는가?"*
*   *"어느 항만/현장(Site)에서 어떤 종류의 지연(LogisticsIssue)이 가장 자주 발생했는가?"*

---

## 5. WhatsApp → Obsidian Wiki 자동화 파이프라인 통합 완료 결과

위의 SOP를 바탕으로 수집된 채팅 로그는 다음의 과정을 거쳐 옵시디언 위키 문서로 영구 저장됩니다. 

**📊 6개 채널 통합 지식 추출 및 병렬 서브에이전트 연동 결과:**
1. **전체 채널 파이프라인 통합**
   * Abu Dhabi Logistics, DSV Delivery, Project Lightning, Jopetwil 71, MIR Logistics, SHU Logistics 등 6개 전체 채널이 병렬 서브에이전트를 통해 성공적으로 연동되었습니다.
2. **개인정보 비식별화 및 추출 완료**
   * 개인정보(전화번호 등)를 안전하게 마스킹 및 제거한 후, 20+개 이상의 핵심 물류 이슈(Logistics Issues)가 성공적으로 압축 추출되었습니다.
3. **Obsidian Sync (지식 베이스 저장 및 통합 완료)**
   * 생성된 분석 문서들은 `vault/wiki/analyses/*.md` 형태로 옵시디언에 모두 자동 저장되어, 언제든 시맨틱 검색(RAG)과 지식 그래프 연동이 가능한 상태로 통합이 완료되었습니다.

---

## 6. 실행 계획 및 가이드 (Action Items)

1. **SOP 공지**: 6개 그룹챗의 Description(설명란)에 통합 태그 규약 및 D-1 16:00 보고 룰을 고정.
2. **지식 그래프 연동 준비**: `HVDC STATUS.xlsx` 데이터의 핵심 컬럼들을 4장에서 정의한 온톨로지(Shipment, LPO, Vendor, Vessel, Hub, Warehouse, Site) 스키마에 맞춰 JSON/RDF 형태로 변환할 파이프라인 개발.
3. **가이드 문서 활용**: 저장소 내 **`docs/web-clipping-setup.md` (WhatsApp 물류 그룹챗 지식화 자동화 가이드)**를 참조하여, 대상 채널별로 키워드와 페르소나를 조정하여 파이프라인을 복제 및 구축.
4. **과거 데이터 지식화 (Full Run)**: 스크립트의 `MAX_TO_PROCESS` 제한을 해제하고, DSV, Project Lightning 등 다른 거대 채널의 로그 파일들을 백그라운드에서 일괄 변환하여 초기 지식 베이스(Wiki)를 대량 생성.