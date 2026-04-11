---
title: "HVDC Warehouse & Flow Code Ontology - Consolidated"
type: "ontology-design"
domain: "warehouse-flow-logistics"
sub-domains: ["warehouse-management", "flow-code-algorithm", "inventory-tracking", "logistics-flow"]
version: "consolidated-1.0-v3.5"
date: "2025-10-31"
tags: ["ontology", "hvdc", "warehouse", "flow-code", "logistics", "mosb", "consolidated", "agi-das"]
standards: ["RDF", "OWL", "SHACL", "SPARQL", "JSON-LD", "Turtle", "XSD", "Python-Algorithm", "Pandas", "NumPy"]
status: "active"
spine_ref: "CONSOLIDATED-00-master-ontology.md"
extension_of: "hvdc-master-ontology-v1.0"
source_files: ["1_CORE-03-hvdc-warehouse-ops.md", "1_CORE-08-flow-code.md", "FLOW_CODE_V35_ALGORITHM.md"]
version_history: ["v1.0: consolidated", "v3.5: domain-rules-extended"]
---

> **MASTER GOVERNANCE RULE**
> 1. **Flow Code is a warehouse-handling classification only.** Restricted to WarehouseHandlingProfile. No other domain may own or assign Flow Code as primary language.
> 2. **Program-wide shipment visibility shall use Journey Stage, Route Type, Milestone, and Leg.** (
oute_type, shipment_stage, leg_sequence, JourneyLeg)
> 3. **Port, Customs, Document, Cost, Marine, and Communication domains** may reference warehouse-flow *evidence*, but shall NOT own or assign Flow Code.
> 4. **MOSB is an Offshore Staging / Marine Interface Node**, not a Warehouse in the top-level logistics ontology.

> **Extension Document** — 이 문서는 [`CONSOLIDATED-00-master-ontology.md`](CONSOLIDATED-00-master-ontology.md)의 도메인 확장입니다.
> RoutingPattern Dictionary, Milestone M10~M160, Identifier Policy 정의는 CONSOLIDATED-00을 참조하세요.

# hvdc-warehouse-routing · CONSOLIDATED-02

## 📑 Table of Contents
1. [Warehouse Operations](#section-1)
2. [WarehouseHandlingProfile Algorithm](#section-2)

---

## Section 1: Warehouse Operations

### Source
- **Original File**: `1_CORE-03-hvdc-warehouse-ops.md`
- **Version**: unified-2.0
- **Date**: 2025-10-25

아래는 __HVDC 프로젝트 창고 물류 시스템(UAE 창고 네트워크)__를 __온톨로지 관점__으로 정의한 "작동 가능한 설계서"입니다.
핵심은 __Warehouse(창고)·Site(현장)·OffshoreBase(MOSB = Offshore Staging Node)__ 를 하나의 그래프(KG)로 엮고, __WarehouseHandlingProfile·재고 추적·위험물 관리·용량 제어·AGI/DAS 도메인 룰__ 같은 제약을 **Constraints**로 운영하는 것입니다.

__1) Visual — Ontology Stack (요약표)__

| __Layer__                         | __표준/근거__                                    | __범위__                                       | __HVDC 창고 업무 매핑(예)__                                        |
| --------------------------------- | ------------------------------------------------ | ---------------------------------------------- | ------------------------------------------------------------- |
| __Upper__                         | __IOF/BFO Supply Chain Ontology__, __ISO 15926__ | 상위 개념(행위자/행위/자산/이벤트)·플랜트 라이프사이클 | 창고(Indoor/Outdoor)·이벤트(Transport/Stock)·상태(WarehouseHandlingProfile) 프레임 |
| __Reference Data (Warehouse)__    | __UN/LOCODE__, __ISO 3166__                      | 창고·지역 코드 표준화                          | DSV Al Markaz, DSV Indoor, MOSB, Site 좌표             |
| __Inventory Management__          | __ISO 9001__, __ISO 14001__                      | 재고 관리, 품질 관리 시스템                   | StockSnapshot, TransportEvent, Case/Item 추적                |
| __WarehouseHandling__             | __HVDC WarehouseHandlingProfile v3.5__            | WH 처리 이력 분류(0~5)                       | WH In/Out 이벤트 기록, wh_handling_cnt, confirmedFlowCode, AGI/DAS 규칙         |
| __Dangerous Cargo__               | __IMDG Code__, __IATA DGR__                      | 위험물 보관·운송 규정                         | DangerousCargoWarehouse, 특수 보관 조건, HSE 절차                           |
| __Data Validation__               | __SHACL__, __SPARQL__                            | 데이터 검증·질의 언어                         | Flow Code 검증, 재고 정확성, PKG Accuracy ≥99%            |
| __Integration__                   | __JSON-LD__, __RDF/XML__                         | 데이터 교환·통합 표준                         | Excel→RDF 매핑, API 연동, 실시간 동기화            |

Hint: MOSB는 **Offshore Staging / Marine Interface Node**로, ADNOC L&S 운영 Yard(20,000㎡)에서 해상화물 집하·적재를 담당합니다.

__2) Domain Ontology — 클래스/관계(창고 단위 재정의)__

__핵심 클래스 (Classes)__

- __Node__(Warehouse/Site/OffshoreBase)
- __Warehouse__(IndoorWarehouse/OutdoorWarehouse/DangerousCargoWarehouse)
- __Site__(AGI/DAS/MIR/SHU)
- __OffshoreBase__(MOSB) — Offshore Staging / Marine Interface Node (**창고 분류에서 제외**)
- __TransportEvent__(노드 간 이동 및 상태 변경 이벤트)
- __StockSnapshot__(특정 시점 노드의 수량·중량·CBM 스냅샷)
- __Case__(패키지 단위 식별 개체)
- __Item__(개별 아이템 단위)
- __Invoice__(InvoiceLineItem/ChargeSummary)
- __Location__(UN/LOCODE, Warehouse Name, Storage Type)
- __WarehouseHandlingProfile__(Flow Code 유일 소유 클래스 — confirmedFlowCode 0~5, wh_handling_cnt, flowConfirmationStatus)
- __KPI__(PKG_Accuracy/WarehouseProfile_Coverage/wh_handling_cnt/Data_Quality)

**참조**: WarehouseHandlingProfile 상세 구현은 [`Section 2: WarehouseHandlingProfile Algorithm`](#section-2)을 참조하세요.


#### WarehouseHandlingProfile 클래스 정의

```turtle
hvdc:WarehouseHandlingProfile a owl:Class ;
    rdfs:label "Warehouse Handling Profile" ;
    rdfs:comment "Flow Code의 유일한 소유 클래스. WH In 이벤트 기반으로 생성·확정됨." .

hvdc:confirmedFlowCode a owl:DatatypeProperty ;
    rdfs:domain hvdc:WarehouseHandlingProfile ;
    rdfs:range xsd:integer ;
    rdfs:comment "0=Pre-Arrival, 1=WH bypass, 2=Single WH, 3=WH+Offshore, 4=Multi-WH+Offshore, 5=Mixed/Pending" .

hvdc:flowConfirmationStatus a owl:DatatypeProperty ;
    rdfs:domain hvdc:WarehouseHandlingProfile ;
    rdfs:range xsd:string ;   # "tentative" | "confirmed" | "overridden"
    rdfs:comment "WH In 이벤트 기록 전: tentative. 확정 후: confirmed." .

hvdc:flowEvidenceSource a owl:DatatypeProperty ;
    rdfs:domain hvdc:WarehouseHandlingProfile ;
    rdfs:range xsd:string ;   # TransportEvent ID
    rdfs:comment "confirmedFlowCode 결정의 근거 이벤트 ID" .

hvdc:warehouseDwellDays a owl:DatatypeProperty ;
    rdfs:domain hvdc:WarehouseHandlingProfile ;
    rdfs:range xsd:integer .
```
__대표 관계 (Object Properties)__

- TransportEvent → hasLocation → Node (이벤트 발생 위치)
- Case → transportedBy → TransportEvent (케이스 이동 이벤트)
- StockSnapshot → capturedAt → Node (재고 스냅샷 위치)
- Case/ShipmentUnit → hasWarehouseHandlingProfile → WarehouseHandlingProfile (Flow Code 유일 소유)
- Warehouse → handles → DangerousCargo (위험물 처리)
- Site → receivesFrom → Warehouse (현장 수령)
- OffshoreBase(MOSB) → receivesFrom → Warehouse (WH→MOSB 출고 경로, Offshore Staging 역할)
- WarehouseHandlingProfile → wh_handling_cnt → Integer (실제 WH In 이벤트 횟수)
- Case → hasHVDCCode → String (HVDC 식별 코드)
- Invoice → refersTo → TransportEvent (송장 연계)

__데이터 속성 (Data Properties)__

- hasCase, hasRecordId, hasHVDCCode, hasDate, hasOperationMonth, hasStartDate, hasFinishDate, hasLocation, hasWarehouseName, hasStorageType, hasQuantity, hasPackageCount, hasWeight, hasCBM, hasAmount, hasRateUSD, hasTotalUSD, hasCategory, hasVendor, hasTransactionType, hasStackStatus, hasDHLWarehouse.
**WarehouseHandlingProfile**: confirmedFlowCode (0~5), wh_handling_cnt (0~3), flowConfirmationStatus, flowEvidenceSource, warehouseDwellDays.

__3) Use-case별 제약(Constraints) = 운영 가드레일__

__3.1 Warehouse Capacity Management__

- __Rule-1__: Warehouse.storageCapacity > CurrentUtilization. 초과 시 *overflow 창고* 확보 또는 *입고 스케줄 조정*.
- __Rule-2__: IndoorWarehouse → 온도·습도 제어 필수. 미준수 시 *자재 손상 리스크 알림*.
- __Rule-3__: DangerousCargoWarehouse → IMDG Code 준수. 위험물 분류별 분리 보관 필수.

__3.2 Stock Tracking & Accuracy__

- __Rule-4__: 모든 TransportEvent는 hasCase + hasDate + hasLocation 필수. WarehouseHandlingProfile은 WH In 이벤트 발생 시 자동 생성됨. 미충족 시 *이벤트 생성 차단*.
- __Rule-5__: StockSnapshot → hasQuantity + hasWeight + hasCBM 필수. 음수 값 금지.
- __Rule-6__: PKG Accuracy ≥ 99% = 시스템 PKG / 실제수입PKG. 미달 시 *재고 실사* 필수.

__3.3 WarehouseHandlingProfile Validation__

> **[핵심]** 이 규칙들은 `WarehouseHandlingProfile` 클래스 안에서만 적용됨. 다른 도메인(Port, Document, Cost, Marine)에 직접 적용 금지.

- __Rule-7__: `WarehouseHandlingProfile.confirmedFlowCode` ∈ {0,1,2,3,4,5}. 비표준 값 감지 시 *데이터 검증 실패*.
  - **0**: Pre-Arrival — WH 입고 없음 (잠정)
  - **1**: WH bypass confirmed — 창고 미경유 확정
  - **2**: Single WH handling — WH 1회 경유
  - **3**: WH-linked offshore pattern — WH+MOSB 복합
  - **4**: Multi-WH + offshore pattern — WH 2회 이상 + MOSB
  - **5**: Mixed / pending / unresolved warehouse pattern
- __Rule-8__: `wh_handling_cnt` = 실제 WH In 이벤트 횟수(0~3). `confirmedFlowCode`와 일치 필수. 계획 경유 포함 금지.
- __Rule-8A__: **AGI/DAS 도메인 룰** — `route_type ∈ {MOSB_DIRECT, WH_MOSB, MIXED}` 필수. (Shipment 레이어에서 검증)
- __Rule-8B__: `confirmedFlowCode=5` 분류 조건: MOSB 있으나 Site 없음 OR WH 2회 이상 + MOSB 없음. 반드시 사유 플래그 필요.

__3.4 Dangerous Cargo Handling__

- __Rule-9__: 위험물 → DangerousCargoWarehouse 필수. 일반 창고 보관 금지.
- __Rule-10__: IMDG Class별 분리 보관. 호환성 없는 위험물 동시 보관 금지.
- __Rule-11__: 위험물 TransportEvent → 특수 HSE 절차 + PTW 필수.

__4) 최소 예시(표현) — JSON-LD (요지)__

```json
{
  "@context": {
    "hvdc": "http://samsung.com/project-logistics#",
    "hasCase": "hvdc:hasCase",
    "hasDate": {"@id": "hvdc:hasDate", "@type": "xsd:dateTime"},
    "hasLocation": {"@id": "hvdc:hasLocation", "@type": "@id"},
    "confirmedFlowCode": {"@id": "hvdc:confirmedFlowCode", "@type": "xsd:integer"}
  },
  "@type": "hvdc:TransportEvent",
  "id": "EVT_208221_1",
  "hasCase": "HE-208221",
  "hasDate": "2025-05-13T08:00:00",
  "hasLocation": {
    "@type": "hvdc:IndoorWarehouse",
    "name": "DSV Indoor",
    "storageType": "Indoor"
  },
  "hasQuantity": 2,
  "hasWeight": 694.00,
  "hasCBM": 12.50,
  "confirmedFlowCode": 2,
  "hasWHHandling": 1,
  "hasHVDCCode": "HE-208221"
}
```

__5) 선택지(3) — 구축 옵션 (pro/con/$·risk·time)__

1. __RDF-first (표준 우선, 완전한 온톨로지)__

- __Pro__: RDF/OWL/SHACL 완전 지원, 표준 호환성 최고, 복잡한 추론 가능.
- __Con__: 학습 곡선 가파름, Excel 사용자 접근성↓.
- __$__: 중간~높음. __Risk__: 기술 복잡성. __Time__: 12–16주 완전 구현.

2. __Hybrid (RDF+Excel 동시)__ ← *추천*

- __Pro__: RDF 온톨로지 + Excel 친화적 인터페이스, 점진적 마이그레이션 가능.
- __Con__: 두 시스템 동기화 복잡성.
- __$__: 중간. __Risk__: 데이터 일관성 관리. __Time__: 8–12주 POC→Rollout.

3. __Excel-first (현장 우선)__

- __Pro__: 기존 Excel 워크플로우 유지, 즉시 적용 가능.
- __Con__: 온톨로지 표준 준수 제한, 확장성 제약.
- __$__: 낮음. __Risk__: 기술 부채 누적. __Time__: 4–6주.

__6) Roadmap (P→Pi→B→O→S + KPI)__

- __P(Plan)__: 스코프 확정(창고: 7개, 이벤트: TransportEvent/StockSnapshot, 속성: 20개). __KPI__: 클래스 정의 완전성 ≥ 100%.
- __Pi(Pilot)__: __DSV Indoor + MOSB__ 2창고 대상 __Flow Code 검증__ 적용. __KPI__: PKG Accuracy ↑ 99%, Flow Code 오류 ↓ 90%.
- __B(Build)__: __SHACL 검증__ + __SPARQL 질의__ + __Excel→RDF 매핑__ 추가. __KPI__: 데이터 품질 오류 ↓ 95%, 질의 응답시간 ≤ 2초.
- __O(Operate)__: 실시간 재고 추적, 자동 알림, KPI 대시보드. __KPI__: 실시간 동기화 지연 ≤ 5분.
- __S(Scale)__: 7창고→글로벌 재사용, __RDF Web Vocabulary__로 공개 스키마 매핑. __KPI__: 타 프로젝트 적용 공수 ↓ 50%.

__7) Data·Sim·BI (운영 숫자 관점)__

- __Stock Clock__: StockSnapshot = (Node, DateTime, Quantity, Weight, CBM) → 노드별 __재고 시계__ 운영.
- __Flow Code Distribution__: FlowCode_t = Count(TransportEvent) by FlowCode(0~5) → 경로 효율성 분석.
- __WH Handling Efficiency__: 평균 경유 창고 횟수 추적, 최적화 기회 식별.
- __PKG Accuracy Rate__: 시스템 PKG / 실제 PKG × 100% → 99% 이상 유지.
- __Dangerous Cargo Compliance__: IMDG Code 준수율, HSE 절차 이행률 모니터링.

__8) Automation (RPA·LLM·Sheets·TG) — Slash Cmd 예시__

- __/warehouse-master --fast stock-audit__ → 7개 창고별 __재고 정확성__ 검증→PKG Accuracy 리포트.
- __/warehouse-master predict --AEDonly flow-efficiency__ → Flow Code 분포 분석 + 최적화 제안.
- __/switch_mode LATTICE RHYTHM__ → 창고 용량 알림 + Flow Code 검증 교차검증.
- __/visualize_data --type=warehouse <stock.csv>__ → 창고별 재고 현황 시각화.
- __/flow-code validate --strict__ → Flow Code(0~5) + WH Handling 일치성 검증.
- __/dangerous-cargo check --compliance__ → IMDG Code 준수 상태 일괄 체크.

__9) QA — Gap/Recheck 리스트__

- __RDF 스키마 정합성__: Turtle 문법, OWL 클래스 정의, SHACL 규칙 검증.
- __Flow Code 매핑__: 0~5 코드 정의, WH Handling 계산 로직, 비표준 값 처리.
- __Excel 매핑 규칙__: field_mappings 정확성, 데이터 타입 변환, NULL 값 처리.
- __SPARQL 질의__: 문법 검증, 성능 최적화, 결과 정확성.
- __JSON-LD 컨텍스트__: 네임스페이스 정의, 타입 매핑, 호환성 확인.

__10) Fail-safe "중단" 테이블 (ZERO 전략)__

| __트리거(중단)__                           | __ZERO 액션__                              | __재개 조건__                         |
| ------------------------------------------ | ------------------------------------------ | ------------------------------------- |
| Flow Code 비표준 값(>5) 감지               | 이벤트 생성 중단, 데이터 정규화 요청       | Flow Code 0~5 범위 내 정규화 완료     |
| PKG Accuracy < 99%                        | 재고 실사 강제 실행, 시스템 PKG 재계산     | PKG Accuracy ≥ 99% 달성               |
| 위험물 일반 창고 보관 감지                 | 즉시 격리, DangerousCargoWarehouse 이송   | IMDG Code 준수 창고로 이송 완료       |
| WH Handling ≠ Flow Code 일치              | 이벤트 검증 실패, 경로 재검토              | WH Handling과 Flow Code 일치 확인     |
| StockSnapshot 음수 값                     | 재고 조정 중단, 원인 분석 요청             | 양수 값으로 수정 완료                 |
| SHACL 검증 실패                           | 데이터 입력 중단, 스키마 위반 수정 요청    | SHACL 규칙 통과                       |
| Excel→RDF 매핑 오류                       | 변환 중단, 매핑 규칙 재검토                | 매핑 규칙 수정 완료                   |
| SPARQL 질의 타임아웃(>30초)               | 질의 중단, 인덱스 최적화 요청              | 질의 응답시간 ≤ 30초 달성             |

__11) 운영에 바로 쓰는 SHACL(요지)__

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix hvdc: <http://samsung.com/project-logistics#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# TransportEvent 검증 (핵심 4요소)
hvdc:TransportEventShape a sh:NodeShape ;
  sh:targetClass hvdc:TransportEvent ;
  sh:property [
    sh:path hvdc:hasCase ;
    sh:datatype xsd:string ;
    sh:minCount 1 ;
    sh:message "Case ID is required"
  ] ;
  sh:property [
    sh:path hvdc:hasDate ;
    sh:datatype xsd:dateTime ;
    sh:minCount 1 ;
    sh:message "Event date is required"
  ] ;
  sh:property [
    sh:path hvdc:hasLocation ;
    sh:class hvdc:Node ;
    sh:minCount 1 ;
    sh:message "Location must be a valid Node"
  ] ;
  sh:property [
    sh:path hvdc:confirmedFlowCode ;
    sh:datatype xsd:integer ;
    sh:minInclusive 0 ;
    sh:maxInclusive 5 ;
    sh:minCount 1 ;
    sh:message "Flow Code must be 0~5 (v3.5)"
  ] .

# Flow Code와 WH Handling 일치성 검증
hvdc:FlowCodeConsistencyShape a sh:NodeShape ;
  sh:targetClass hvdc:TransportEvent ;
  sh:sparql [
    sh:message "WH Handling count must match Flow Code" ;
    sh:select """
      SELECT $this
      WHERE {
        $this hvdc:confirmedFlowCode ?fc .
        $this hvdc:hasWHHandling ?wh .
        FILTER (
          (?fc = 0 && ?wh != 0) ||
          (?fc = 1 && ?wh != 0) ||
          (?fc = 2 && ?wh != 1) ||
          (?fc = 3 && (?wh < 1 || ?wh > 2)) ||
          (?fc = 4 && (?wh < 2 || ?wh > 3))
        )
      }
    """
  ] .

# 위험물 창고 검증
hvdc:DangerousCargoShape a sh:NodeShape ;
  sh:targetClass hvdc:TransportEvent ;
  sh:sparql [
    sh:message "Dangerous cargo must be stored in DangerousCargoWarehouse" ;
    sh:select """
      SELECT $this
      WHERE {
        $this hvdc:hasCategory ?category .
        $this hvdc:hasLocation ?location .
        FILTER (CONTAINS(LCASE(?category), "dangerous") ||
                CONTAINS(LCASE(?category), "hazardous"))
        FILTER NOT EXISTS { ?location a hvdc:DangerousCargoWarehouse }
      }
    """
  ] .

# 재고 정확성 검증
hvdc:StockAccuracyShape a sh:NodeShape ;
  sh:targetClass hvdc:StockSnapshot ;
  sh:property [
    sh:path hvdc:hasQuantity ;
    sh:datatype xsd:integer ;
    sh:minInclusive 0 ;
    sh:message "Quantity cannot be negative"
  ] ;
  sh:property [
    sh:path hvdc:hasWeight ;
    sh:datatype xsd:decimal ;
    sh:minInclusive 0.0 ;
    sh:message "Weight cannot be negative"
  ] ;
  sh:property [
    sh:path hvdc:hasCBM ;
    sh:datatype xsd:decimal ;
    sh:minInclusive 0.0 ;
    sh:message "CBM cannot be negative"
  ] .
```

__12) GitHub·재사용__

- 리포지토리 __macho715/hvdc-warehouse-ontology__에 __/models (TTL/JSON-LD)__, __/rules (SHACL)__, __/queries (SPARQL)__, __/mappings (Excel→RDF)__ 디렉토리 구조 권장.
- Flow Code 시스템은 __/mappings/flow-code-rules.json__으로 관리.
- 창고 인스턴스는 __/data/warehouse-instances.ttl__로 버전 관리.

__13) Assumptions & Sources__

- __가정:__ Flow Code 0~5(v3.5)는 HVDC 프로젝트 내부 표준. PKG Accuracy 99%는 운영 품질 기준. 위험물은 IMDG Code 분류 기준 따름. AGI/DAS는 MOSB 레그 필수. Excel 원본은 ETL 전용 폴더에서만 사용.
- __표준/근거:__ RDF/OWL 2.0, SHACL 1.1, SPARQL 1.1, JSON-LD 1.1, XSD 1.1, IMDG Code, IATA DGR, ISO 9001/14001, HVDC Warehouse Logistics Node Ontology v2.0.

__14) 다음 액션(짧게)__

- __/warehouse-master --fast stock-audit__ 로 7개 창고 대상 __재고 정확성__ 일괄 점검,
- __/flow-code validate --strict__ 로 __Flow Code + WH Handling__ 일치성 검증,
- __/visualize_data --type=warehouse <stock.csv>__ 로 __창고별 재고 현황__ 시각화.

원하시면, 위 스택으로 __Flow Code 검증__과 __위험물 관리__부터 SHACL/룰팩을 묶어 드리겠습니다.

---

## Section 2: WarehouseHandlingProfile Algorithm

### Source
- **Original File**: `1_CORE-08-flow-code.md`
- **Version**: unified-3.5
- **Date**: 2025-10-31

Flow Code Algorithm Ontology는 HVDC 프로젝트의 복잡한 물류 흐름을 정량화하는 핵심 시스템입니다. **6단계 Flow Code(0~5, v3.5)**를 통해 창고 경유 패턴, 직송 비율, MOSB 해상운송 활용도, AGI/DAS 도메인 룰, 혼합 케이스 등 핵심 KPI를 산출하며, 물류 최적화와 비용 효율성 분석의 기반이 됩니다.

## Visual Ontology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                 Flow Code Algorithm (v3.5)                 │
├─────────────────────────────────────────────────────────────┤
│  Part 1: Ontology System  │  Part 2: Implementation  │  Part 3: Integration  │
├─────────────────────────────────────────────────────────────┤
│  • FlowCode Classes (0~5) │  • v3.5 Algorithm       │  • Warehouse vs MOSB │
│  • Routing Path Relations    │  • AGI/DAS Domain Rules │  • KPI Applications   │
│  • Constraint Rules       │  • Data Preprocessing    │  • Event Injection    │
│  • Event-based Tracking   │  • Final Location Extract│  • Cross-references   │
└─────────────────────────────────────────────────────────────┘
```

## Part 1: Flow Code Ontology System

### Domain Ontology

#### Core Classes

```turtle
# Flow Code Ontology Classes (v3.5)
hvdc:FlowCode a owl:Class ;
    rdfs:label "Flow Code" ;
    rdfs:comment "물류 흐름 패턴을 나타내는 코드 (0~5)"@ko .

hvdc:LogisticsRoute a owl:Class ;
    rdfs:label "Logistics Flow" ;
    rdfs:comment "물류 흐름 경로"@ko .

hvdc:WarehouseHop a owl:Class ;
    rdfs:label "Warehouse Hop" ;
    rdfs:comment "창고 경유 단계"@ko .

hvdc:OffshoreTransport a owl:Class ;
    rdfs:label "Offshore Transport" ;
    rdfs:comment "MOSB 해상운송"@ko .

hvdc:PreArrival a owl:Class ;
    rdfs:label "Pre Arrival" ;
    rdfs:comment "선적 전 단계"@ko .

hvdc:MixedIncompleteRoute a owl:Class ;
    rdfs:label "Mixed/Incomplete Flow" ;
    rdfs:comment "혼합/미완료 물류 흐름 (Flow Code 5)"@ko .
```

#### Data Properties

```turtle
# Flow Code Properties (v3.5)
hvdc:hasFlowCodeRef a owl:DatatypeProperty ;
    rdfs:label "has Flow Code" ;
    rdfs:comment "물류 흐름 코드 값 (0~5)"@ko ;
    rdfs:domain hvdc:LogisticsRoute ;
    rdfs:range xsd:integer .

hvdc:hasFlowCodeOriginal a owl:DatatypeProperty ;
    rdfs:label "has Flow Code original" ;
    rdfs:comment "도메인 룰 적용 전 원본 Flow Code (v3.5 추적용)"@ko ;
    rdfs:domain hvdc:Case ;
    rdfs:range xsd:integer .

hvdc:hasRouteOverrideReason a owl:DatatypeProperty ;
    rdfs:label "has route override reason" ;
    rdfs:comment "Flow Code 오버라이드 사유 (예: AGI/DAS requires MOSB leg)"@ko ;
    rdfs:domain hvdc:Case ;
    rdfs:range xsd:string .

hvdc:hasRouteDescription a owl:DatatypeProperty ;
    rdfs:label "has route description" ;
    rdfs:comment "물류 흐름 설명 (예: Flow Code 3: Port → MOSB → Site)"@ko ;
    rdfs:domain hvdc:Case ;
    rdfs:range xsd:string .

hvdc:hasFinalLocation a owl:DatatypeProperty ;
    rdfs:label "has final location" ;
    rdfs:comment "최종 위치 (자동 추출된 값)"@ko ;
    rdfs:domain hvdc:Case ;
    rdfs:range xsd:string .

hvdc:hasWHHandling a owl:DatatypeProperty ;
    rdfs:label "has warehouse handling count" ;
    rdfs:comment "창고 처리 횟수"@ko ;
    rdfs:domain hvdc:LogisticsRoute ;
    rdfs:range xsd:integer .

hvdc:hasOffshoreFlag a owl:DatatypeProperty ;
    rdfs:label "has offshore flag" ;
    rdfs:comment "MOSB 해상운송 여부"@ko ;
    rdfs:domain hvdc:LogisticsRoute ;
    rdfs:range xsd:boolean .
```

#### Object Properties

```turtle
# Routing Relations Relations
hvdc:hasWarehouseHop a owl:ObjectProperty ;
    rdfs:label "has warehouse hop" ;
    rdfs:comment "창고 경유 관계" ;
    rdfs:domain hvdc:LogisticsRoute ;
    rdfs:range hvdc:WarehouseHop .

hvdc:hasOffshoreTransport a owl:ObjectProperty ;
    rdfs:label "has offshore transport" ;
    rdfs:comment "해상운송 관계" ;
    rdfs:domain hvdc:LogisticsRoute ;
    rdfs:range hvdc:OffshoreTransport .

hvdc:isPreArrival a owl:ObjectProperty ;
    rdfs:label "is pre arrival" ;
    rdfs:comment "선적 전 단계 여부" ;
    rdfs:domain hvdc:LogisticsRoute ;
    rdfs:range hvdc:PreArrival .
```

### Use-case별 제약

#### Rule-20: Flow Code Range Constraint (v3.5)
```turtle
hvdc:FlowCodeRangeShape a sh:NodeShape ;
    sh:targetClass hvdc:LogisticsRoute ;
    sh:property [
        sh:path hvdc:hasFlowCodeRef ;
        sh:minInclusive 0 ;
        sh:maxInclusive 5 ;
        sh:message "Flow Code는 0~5 범위 내에 있어야 함"
    ] .
```

#### Rule-20A: Flow Code 5 Constraint
```turtle
hvdc:FlowCode5MixedCaseShape a sh:NodeShape ;
    sh:targetClass hvdc:Case ;
    sh:property [
        sh:path hvdc:hasFlowCodeRef ;
        sh:hasValue "5" ;
        sh:property [
            sh:path hvdc:hasRouteDescription ;
            sh:pattern "Flow Code 5:.*Mixed.*Incomplete" ;
            sh:message "Flow Code 5는 Mixed/Incomplete 패턴을 가져야 함"
        ]
    ] .
```

#### Rule-20A2: Flow-5 예외 패턴 탐지 규칙 (Telemetry)
```turtle
hvdc:Flow5ExceptionDetectionShape a sh:NodeShape ;
    sh:targetClass hvdc:TransportEvent ;
    sh:sparql [
        sh:severity sh:Warning ;
        sh:message "Flow-5 예외 케이스 탐지: WH/MOSB 이벤트 다중 혼재 또는 순서 역전 또는 누락/중복 타임스탬프" ;
        sh:select """
            PREFIX hvdc: <http://samsung.com/project-logistics#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            SELECT $this ?reason
            WHERE {
                $this hvdc:hasFlowCodeRef "5"^^xsd:integer .
                {
                    # 패턴 1: WH 이벤트 다중 혼재
                    {
                        SELECT $this (COUNT(?wh) AS ?whCount) WHERE {
                            $this hvdc:hasLocation ?wh .
                            ?wh a hvdc:Warehouse
                        } GROUP BY $this HAVING (?whCount > 2)
                    }
                    BIND("WH_EVENTS_MULTIPLE_MIXED" AS ?reason)
                } UNION {
                    # 패턴 2: MOSB 있으나 Site 없음 또는 WH 2개 이상 + MOSB 없음
                    {
                        SELECT $this WHERE {
                            $this hvdc:hasLocation ?mosb .
                            ?mosb a hvdc:OffshoreBase .
                            OPTIONAL { $this hvdc:hasDestination ?site . }
                        } GROUP BY $this HAVING (COUNT(?site) = 0)
                    }
                    BIND("MOSB_WITHOUT_SITE" AS ?reason)
                } UNION {
                    # 패턴 3: 타임스탬프 순서 역전 또는 누락
                    {
                        SELECT $this WHERE {
                            $this hvdc:hasEventDate ?date1 .
                            ?prev hvdc:hasEventDate ?date2 .
                            FILTER(?date2 > ?date1)
                        }
                    }
                    BIND("TIMESTAMP_ORDER_VIOLATION" AS ?reason)
                }
            }
        """
    ] ;
    sh:property [
        sh:path hvdc:hasRouteOverrideReason ;
        sh:minCount 1 ;
        sh:message "Flow-5 예외 케이스는 반드시 Override Reason을 기록해야 함"
    ] .
```

#### Rule-20B: AGI/DAS Domain Rule Constraint
```turtle
hvdc:AGIDASFlowRuleShape a sh:NodeShape ;
    sh:targetClass hvdc:Case ;
    sh:sparql [
        sh:message "AGI/DAS 케이스는 Flow Code 3 이상이어야 함" ;
        sh:select """
            PREFIX hvdc: <http://samsung.com/project-logistics#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            SELECT $this
            WHERE {
                $this hvdc:hasFinalLocation ?loc .
                FILTER(?loc IN ("AGI", "DAS"))
                $this hvdc:hasFlowCodeRef ?fc .
                FILTER(xsd:integer(?fc) < 3)
            }
        """
    ] .
```

#### Rule-20C: AGI/DAS Flow-1 Explicit Ban (Hardening)
```turtle
hvdc:AGIDASFlow1BanShape a sh:NodeShape ;
    sh:targetClass hvdc:TransportEvent ;
    sh:sparql [
        sh:severity sh:Violation ;
        sh:message "AGI/DAS: Flow Code 1 (Port→Site) 금지 - MOSB 레그 필수" ;
        sh:select """
            PREFIX hvdc: <http://samsung.com/project-logistics#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            SELECT $this ?site ?flowCode
            WHERE {
                $this hvdc:hasDestination ?site .
                FILTER(?site IN ("AGI", "DAS"))
                $this hvdc:hasFlowCodeRef ?flowCode .
                FILTER(xsd:integer(?flowCode) = 1)
            }
        """
    ] .
```

#### Rule-21: Flow Code Calculation Consistency
```turtle
hvdc:FlowCodeConsistencyShape a sh:NodeShape ;
    sh:targetClass hvdc:LogisticsRoute ;
    sh:property [
        sh:path hvdc:hasFlowCodeRef ;
        sh:equals [
            sh:sparql """
                SELECT ?flowCode WHERE {
                    ?fc hvdc:hasWHHandling ?whCount .
                    ?fc hvdc:hasOffshoreFlag ?offshore .
                    BIND(IF(?offshore = true, 1, 0) + ?whCount + 1 AS ?calculated) .
                    BIND(IF(?calculated > 4, 4, ?calculated) AS ?flowCode) .
                }
            """
        ] ;
        sh:message "Flow Code 계산이 일관성 있어야 함"
    ] .
```

#### Rule-22: Pre Arrival Flow Code Constraint
```turtle
hvdc:PreArrivalFlowCodeShape a sh:NodeShape ;
    sh:targetClass hvdc:LogisticsRoute ;
    sh:property [
        sh:path hvdc:isPreArrival ;
        sh:hasValue true ;
        sh:property [
            sh:path hvdc:hasFlowCodeRef ;
            sh:hasValue 0 ;
            sh:message "Pre Arrival은 Flow Code 0이어야 함"
        ]
    ] .
```

## Part 2: Algorithm Implementation

### Flow Code 정의 (v3.5)

```python
flow_codes_v35 = {
    0: "Flow Code 0: Pre Arrival",
    1: "Flow Code 1: Port → Site",
    2: "Flow Code 2: Port → WH → Site",
    3: "Flow Code 3: Port → MOSB → Site",
    4: "Flow Code 4: Port → WH → MOSB → Site",
    5: "Flow Code 5: Mixed / Waiting / Incomplete leg",
}
```

**6가지 물류 흐름 패턴 (v3.5):**
- **Code 0**: 선적 전 단계 (Pre Arrival)
- **Code 1**: 항구에서 현장 직송 (창고 경유 없음)
- **Code 2**: 항구 → 창고 1개 이상 → 현장
- **Code 3**: 항구 → MOSB(해상운송) → 현장 (**AGI/DAS 필수**)
- **Code 4**: 항구 → 창고 1개 이상 → MOSB → 현장
- **Code 5**: 혼합/대기/미완료 케이스 (MOSB 있으나 Site 없음, 또는 WH 2개 이상 + MOSB 없음)

---

### Flow Code 계산 알고리즘 (`_override_flow_code()` - Lines 563-622)

#### 입력 데이터 전처리 (Lines 568-584)

```python
# 창고 컬럼 분류 (MOSB 제외)
WH_COLS = [w for w in self.warehouse_columns if w != "MOSB"]
MOSB_COLS = [w for w in self.warehouse_columns if w == "MOSB"]

# 0값과 빈 문자열을 NaN으로 치환 (notna() 오류 방지)
for col in WH_COLS + MOSB_COLS:
    if col in self.combined_data.columns:
        self.combined_data[col] = self.combined_data[col].replace({0: np.nan, "": np.nan})
```

**목적**: 데이터 품질 보장 및 일관성 있는 null 값 처리

#### Pre Arrival 판별 (Lines 586-594)

```python
# 명시적 Pre Arrival 판별
status_col = "Status_Location"
if status_col in self.combined_data.columns:
    is_pre_arrival = self.combined_data[status_col].str.contains(
        "Pre Arrival", case=False, na=False
    )
else:
    is_pre_arrival = pd.Series(False, index=self.combined_data.index)
```

**로직**: `Status_Location` 컬럼에서 "Pre Arrival" 문자열 포함 여부로 선적 전 단계 감지

#### 핵심 계산 로직 (Lines 596-609)

```python
# 창고 Hop 수 계산
wh_cnt = self.combined_data[WH_COLS].notna().sum(axis=1)

# Offshore 계산 (MOSB 통과 여부)
offshore = self.combined_data[MOSB_COLS].notna().any(axis=1).astype(int)

# Flow Code 계산 (Off-by-One 버그 수정)
base_step = 1  # Port → Site 기본 1스텝
flow_raw = wh_cnt + offshore + base_step  # 1~5 범위

# Pre Arrival은 무조건 0, 나머지는 1~4로 클립
self.combined_data["FLOW_CODE"] = np.where(
    is_pre_arrival,
    0,  # Pre Arrival은 Code 0
    np.clip(flow_raw, 1, 4),  # 나머지는 1~4
)
```

**계산 공식:**
```
FLOW_CODE = {
    0                           if "Pre Arrival" in Status_Location
    clip(wh_count + offshore + 1, 1, 4)  otherwise
}

where:
- wh_count = 창고 컬럼(MOSB 제외)에서 날짜가 있는 개수
- offshore = MOSB 컬럼에 날짜가 있으면 1, 없으면 0
- base_step = 1 (Port → Site 기본값)
```

**예시:**
- 창고 0개 + offshore 0 + 1 = **1** (Port → Site 직송)
- 창고 1개 + offshore 0 + 1 = **2** (Port → WH → Site)
- 창고 1개 + offshore 1 + 1 = **3** (Port → WH → MOSB → Site)
- 창고 2개 + offshore 1 + 1 = **4** (Port → WH → WH → MOSB → Site)
- 창고 3개 이상이어도 **4**로 클립 (최대값 제한)

#### 설명 매핑 및 검증 (Lines 611-620)

```python
# 설명 매핑
self.combined_data["FLOW_DESCRIPTION"] = self.combined_data["FLOW_CODE"].map(
    self.flow_codes
)

# 디버깅 정보 출력
flow_distribution = self.combined_data["FLOW_CODE"].value_counts().sort_index()
logger.info(f" Flow Code 분포: {dict(flow_distribution)}")
logger.info(f" Pre Arrival 정확 판별: {is_pre_arrival.sum()}건")
```

---

### v3.5 알고리즘 업그레이드

#### v3.4 → v3.5 주요 변경사항

| 항목 | v3.4 | v3.5 |
|------|------|------|
| **Flow Code 범위** | 0~4 | **0~5** |
| **계산 방식** | 산술 계산 + clip | **관측 기반 규칙 적용** |
| **AGI/DAS 처리** | 없음 | **도메인 룰 강제 적용** |
| **혼합 케이스** | 없음 | **Flow Code 5로 명시적 분류** |
| **원본 값 보존** | 없음 | **FLOW_CODE_ORIG 컬럼** |
| **오버라이드 추적** | 없음 | **FLOW_OVERRIDE_REASON 컬럼** |

#### v3.5 핵심 알고리즘

**단계별 처리 순서**:

1. **필드 검증 및 전처리** (컬럼명 정규화, 0→NaN)
2. **관측값 계산** (is_pre_arrival, wh_cnt, has_mosb, has_site)
3. **기본 Flow Code 계산** (0~4)
4. **AGI/DAS 도메인 오버라이드** (0/1/2 → 3)
5. **혼합 케이스 처리** (→ 5)
6. **최종 검증 및 반영**

**AGI/DAS 도메인 룰**:
> Final_Location이 "AGI" 또는 "DAS"인 경우, Flow Code 0/1/2는 무조건 3으로 승급 (MOSB 레그 필수)

**Flow Code 5 케이스**:
- MOSB 있으나 Site 없음
- WH 2개 이상 + MOSB 없음

**변환 결과** (실제 데이터 755건):
- Flow Code 0: 71건 (Pre Arrival)
- Flow Code 1: 255건 (직송)
- Flow Code 2: 152건 (창고경유)
- Flow Code 3: 131건 (MOSB경유)
- Flow Code 4: 65건 (창고+MOSB)
- Flow Code 5: 81건 (혼합/미완료)
- AGI/DAS 강제 승급: 31건

## Part 3: Operational Integration

### 창고 vs MOSB 구분 로직

**창고 컬럼 (Lines 216-227):**
```python
self.warehouse_columns = [
    "DHL WH", "DSV Indoor", "DSV Al Markaz", "Hauler Indoor",
    "DSV Outdoor", "DSV MZP", "HAULER", "JDN MZD",
    "MOSB", "AAA Storage"
]
```

**MOSB 특별 처리:**
- MOSB는 창고이지만 **offshore 해상운송** 특성으로 별도 카운트
- `wh_cnt`에서는 제외, `offshore` 변수로 독립 계산
- MOSB 통과 시 Flow Code +1 증가 효과

### Flow Code 활용 사례

#### 직접 배송 계산 (Lines 1099-1137)

```python
def calculate_direct_delivery(self, df: pd.DataFrame) -> Dict:
    """직접 배송 계산 (Port → Site)"""
    for idx, row in df.iterrows():
        # Flow Code가 1인 경우 (Port → Site)
        if row.get("FLOW_CODE") == 1:
            # 현장으로 직접 이동한 항목들
```

#### Routing Analysis 시트 (Lines 1937-1957)

```python
def create_flow_analysis_sheet(self, stats: Dict) -> pd.DataFrame:
    """Flow Code 분석 시트 생성"""
    flow_summary = df.groupby("FLOW_CODE").size().reset_index(name="Count")
    flow_summary["FLOW_DESCRIPTION"] = flow_summary["FLOW_CODE"].map(
        self.calculator.flow_codes
    )
```

#### Routing Traceability Dashboard (Lines 1739-1885)

**KPI 계산에 활용:**
- MOSB 통과율 (MOSB Pass Rate)
- 직송 비율 (Direct Flow Rate) - Flow Code 1 비율
- 창고 평균 체류 일수 (Avg WH Dwell Days)

### 알고리즘 강점 (v3.5)

1. **명확한 물류 패턴 분류**: 6단계(0~5)로 모든 물류 흐름 커버
2. **견고한 예외 처리**: null 값, 빈 문자열 사전 정규화
3. **정확한 Pre Arrival 판별**: ATA 또는 날짜 컬럼 기반 검증
4. **AGI/DAS 도메인 룰**: 해상 현장 강제 MOSB 승급 자동화
5. **혼합 케이스 분류**: Flow Code 5로 비정상 패턴 명시적 분류
6. **원본 값 보존**: FLOW_CODE_ORIG 및 FLOW_OVERRIDE_REASON 추적
7. **컬럼명 유연성**: 자동 정규화 및 다중 후보 지원
8. **추적 가능성**: 분포 로그, 검증 메커니즘, TTL 속성 내장

### 제한사항 및 가정 (v3.5)

1. **최대 Flow Code 5**: 혼합 케이스 추가로 범위 확장
2. **MOSB 특수성**: 창고이지만 offshore로 별도 처리
3. **ATA 또는 날짜 기반**: Pre Arrival 판별이 데이터 소스에 의존
4. **날짜 기반 판단**: 창고 컬럼에 날짜가 있으면 경유로 간주
5. **AGI/DAS 규칙**: Final_Location 자동 추출 시 신뢰도 의존

## JSON-LD Examples

### Example 1: 일반 창고 경유 (Flow Code 2)

```json
{
  "@context": {
    "hvdc": "http://samsung.com/project-logistics#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
  },
  "@id": "hvdc:LogisticsRoute-example-001",
  "@type": "hvdc:LogisticsRoute",
  "hvdc:hasFlowCodeRef": 2,
  "hvdc:hasWHHandling": 1,
  "hvdc:hasOffshoreFlag": false,
  "hvdc:hasRouteDescription": "Flow Code 2: Port → WH → Site",
  "hvdc:hasWarehouseHop": {
    "@type": "hvdc:WarehouseHop",
    "hvdc:warehouseName": "DSV Indoor"
  }
}
```

### Example 2: AGI 강제 승급 (Flow Code 3)

```json
{
  "@context": {
    "hvdc": "http://samsung.com/project-logistics#"
  },
  "@id": "hvdc:LogisticsRoute-example-002",
  "@type": "hvdc:Case",
  "hvdc:hasFlowCodeRef": 3,
  "hvdc:hasFlowCodeOriginal": 1,
  "hvdc:hasRouteDescription": "Flow Code 3: Port → MOSB → Site (AGI/DAS forced)",
  "hvdc:hasRouteOverrideReason": "AGI/DAS requires MOSB leg",
  "hvdc:hasFinalLocation": "AGI",
  "hvdc:hasInboundEvent": {
    "@type": "hvdc:StockEvent",
    "hvdc:hasEventDate": "2024-01-15",
    "hvdc:hasLocationAtEvent": "MOSB",
    "hvdc:hasQuantity": 1.0
  }
}
```

### Example 3: 혼합 케이스 (Flow Code 5)

```json
{
  "@context": {
    "hvdc": "http://samsung.com/project-logistics#"
  },
  "@id": "hvdc:LogisticsRoute-example-003",
  "@type": "hvdc:Case",
  "hvdc:hasFlowCodeRef": 5,
  "hvdc:hasFlowCodeOriginal": 2,
  "hvdc:hasRouteDescription": "Flow Code 5: Mixed / Waiting / Incomplete leg"
}
```

## SPARQL Queries

### Flow Code 분포 분석
```sparql
PREFIX hvdc: <https://hvdc-project.com/ontology/>

SELECT ?flowCode ?description (COUNT(?fc) AS ?count)
WHERE {
    ?fc hvdc:hasFlowCodeRef ?flowCode .
    ?fc hvdc:hasRouteDescription ?description .
}
GROUP BY ?flowCode ?description
ORDER BY ?flowCode
```

### MOSB 통과율 계산
```sparql
PREFIX hvdc: <https://hvdc-project.com/ontology/>

SELECT
    (COUNT(?offshoreRoute) AS ?offshoreCount)
    (COUNT(?totalRoute) AS ?totalCount)
    ((COUNT(?offshoreRoute) * 100.0 / COUNT(?totalRoute)) AS ?mosbPassRate)
WHERE {
    ?totalRoute a hvdc:LogisticsRoute .
    OPTIONAL {
        ?offshoreRoute hvdc:hasOffshoreFlag true .
    }
}
```

## Semantic KPI Layer (v3.5)

### Flow Code Distribution
- **Direct Flow Rate**: Flow Code 1 비율 (직송 효율성)
- **Warehouse Utilization**: Flow Code 2, 4 비율 (창고 활용도)
- **MOSB Pass Rate**: Flow Code 3, 4 비율 (해상운송 활용도)
- **Pre Arrival Ratio**: Flow Code 0 비율 (선적 전 단계 비율)
- **Mixed Case Ratio**: Flow Code 5 비율 (혼합/미완료 케이스 비율)

### Performance Metrics
- **Average Flow Complexity**: 평균 Flow Code 값
- **Flow Code Variance**: Flow Code 분산 (물류 패턴 다양성)
- **Optimization Potential**: Flow Code 4 → 1 전환 가능성
- **AGI/DAS Compliance**: AGI/DAS 케이스 중 Flow Code ≥3 비율 (도메인 룰 준수)

### AGI/DAS Domain Rule Validation (v3.5)

```sparql
PREFIX hvdc: <http://samsung.com/project-logistics#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT
    (COUNT(?agi) AS ?agiTotal)
    (COUNT(?agiCompliant) AS ?agiCompliant)
    ((COUNT(?agiCompliant) * 100.0 / COUNT(?agi)) AS ?complianceRate)
WHERE {
    ?case hvdc:hasFinalLocation "AGI" .
    ?case hvdc:hasFlowCodeRef ?fc .
    BIND(?case AS ?agi)
    OPTIONAL {
        ?case hvdc:hasFlowCodeRef ?flowComp .
        FILTER(xsd:integer(?flowComp) >= 3)
        BIND(?case AS ?agiCompliant)
    }
}
```

## 추천 명령어

- `/flow-code analyze --distribution` [Flow Code 분포 분석 (0~5)]
- `/flow-code validate --strict` [Flow Code 일관성 검증]
- `/flow-code agi-das-compliance` [AGI/DAS 도메인 룰 검증]
- `/flow-code mixed-case-analysis` [Flow Code 5 혼합 케이스 분석]
- `/mosb-pass-rate calculate` [MOSB 통과율 계산]
- `/warehouse-efficiency analyze` [창고 효율성 분석]

## Implementation Reference

### 파일 위치
- **알고리즘**: `logiontology/src/ingest/flow_code_calculator.py`
- **통합**: `logiontology/src/ingest/excel_to_ttl_with_events.py`
- **온톨로지**: `logiontology/configs/ontology/hvdc_event_schema.ttl`
- **테스트**: `tests/test_flow_code_v35.py`, `tests/test_flow_code_v35_validation.py`

### Related Documentation
- **알고리즘 상세**: `FLOW_CODE_V35_ALGORITHM.md` (프로젝트 루트)
- **구현 완료**: `FLOW_CODE_V35_IMPLEMENTATION_COMPLETE.md` (프로젝트 루트)
- **온톨로지 원본**: `core/1_CORE-08-flow-code.md`

---

이 Flow Code 알고리즘(v3.5)은 HVDC 프로젝트의 복잡한 물류 흐름을 정량화하여 창고 경유 패턴, 직송 비율, MOSB 해상운송 활용도, AGI/DAS 도메인 룰 준수, 혼합 케이스 분석 등 핵심 KPI 산출의 기반이 됩니다.


