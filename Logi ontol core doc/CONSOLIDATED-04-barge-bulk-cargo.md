---
title: "HVDC Barge Operations & Bulk Cargo Ontology"
type: "ontology-design"
domain: "bulk-cargo-operations"
sub-domains: ["bulk-cargo-operations", "seafastening", "stability-control", "barge-operations", "lifting-rigging", "flow-code"]
version: "consolidated-1.1"
date: "2025-11-01"
tags: ["ontology", "hvdc", "bulk-cargo", "barge", "lashing", "stability", "flow-code", "flow-code-v35", "mosb", "lct", "consolidated"]
standards: ["RDF", "OWL", "SHACL", "SPARQL", "JSON-LD", "Turtle", "XSD", "IMSBC", "SOLAS"]
status: "active"
spine_ref: "CONSOLIDATED-00-master-ontology.md"
extension_of: "hvdc-master-ontology-v1.0"
source_files: ["1_CORE-05-hvdc-bulk-cargo-ops.md", "docs/flow_code_v35/FLOW_CODE_V35_ALGORITHM.md"]
---

> **MASTER GOVERNANCE RULE**
> 1. **Flow Code is a warehouse-handling classification only.** Restricted to WarehouseHandlingProfile. No other domain may own or assign Flow Code as primary language.
> 2. **Program-wide shipment visibility shall use Journey Stage, Route Type, Milestone, and Leg.** (
oute_type, shipment_stage, leg_sequence, JourneyLeg)
> 3. **Port, Customs, Document, Cost, Marine, and Communication domains** may reference warehouse-flow *evidence*, but shall NOT own or assign Flow Code.
> 4. **MOSB is an Offshore Staging / Marine Interface Node**, not a Warehouse in the top-level logistics ontology.

> **Extension Document** — 이 문서는 [`CONSOLIDATED-00-master-ontology.md`](CONSOLIDATED-00-master-ontology.md)의 도메인 확장입니다.
> RoutingPattern Dictionary, Milestone M10~M160, Identifier Policy 정의는 CONSOLIDATED-00을 참조하세요.

# hvdc-barge-bulk-cargo · CONSOLIDATED-04

## Bulk Cargo Operations

### Source
- **Original File**: `1_CORE-05-hvdc-bulk-cargo-ops.md`
- **Version**: unified-1.0
- **Date**: 2025-01-23

## Executive Summary

**Bulk/Project 화물 해상 운송(적재·양하·고박·안정성·인양) 전 과정**을 **온톨로지(지식 그래프)**로 모델링하여 데이터 일관성, 추적성, 자동화 가능성을 높인다.

### Route Type in Barge & Bulk Cargo Operations

Barge and bulk cargo operations in the HVDC project primarily utilize **Flow Code 3 and 4**, as most bulk materials require **MOSB transit** for offshore delivery to AGI/DAS sites. The barge/LCT transport model inherently follows the **Port → MOSB → Site** pattern, making MOSB the critical staging and consolidation point for all offshore bulk cargo.

**Key Routing Patterns:**
- **route_type: MOSB_DIRECT**: Port → MOSB → AGI/DAS (Direct bulk cargo to offshore)
- **route_type: WH_MOSB**: Port → Warehouse → MOSB → AGI/DAS (Bulk cargo with interim storage)
- **MOSB Mandatory**: All AGI/DAS bulk shipments enforce MOSB leg (domain rule)

---

**적용 범위**: 철강 구조물, OOG, 프리캐스트(Hollow Core Slab), Breakbulk 전반
**목표 산출물**: 클래스/속성 정의, 제약, 예시 인스턴스, 검증(SHACL), 교환 스키마(CSV), 쿼리(SPARQL) 샘플
**단위**: 길이(m), 중량(t), 각도(deg), 좌표계: 선박 데크 로컬 좌표 (X fwd, Y port→stbd, Z keel→up)
**책임 경계**: 본 모델은 **데이터 표현/검증용**. 공학적 최종 판단(예: Stability 승인, 구조 검토)은 전문 SW/엔지니어 권한

**상위 개념 계층(Top Taxonomy)**:
```
Maritime Logistics
└── Cargo Operation
    ├── Bulk Cargo Operation (BULK)
    │   ├── Planning Phase
    │   ├── Loading Operation
    │   ├── Discharging Operation
    │   ├── Stowage & Lashing
    │   ├── Stability Control
    │   ├── Lifting & Transport Handling
    │   └── Post-Operation (Survey, Handover)
    ├── Documentation (Vessel Loading Plan, Lashing Plan, Stability Report, Rigging Plan)
    ├── Resources (Vessel, Equipment, Manpower)
    ├── Locations (Port, Berth, Jetty, Yard)
    └── Constraints (Safety, Compliance, Environment, Contract)
```

**Visual — 핵심 클래스/관계(요약)**

| Class | 핵심 속성 | 관계 | 근거/조인 소스 | 결과 |
|-------|-----------|------|----------------|------|
| debulk:Cargo | cargoId, cargoType, weight(t), dimL/W/H(m), cogX/Y/Z(m), stackable(boolean), hazmatClass? | placedOn→DeckArea, securedBy→LashingAssembly, handledBy→Equipment | OCR/Table Parser | 상태, 정합성 |
| debulk:Vessel | vesselName, imo?, deckStrength(t/m²), coordinateOrigin | hasDeck→DeckArea, carries→Cargo, operatedBy→Crew | Vessel Registry | 운항 상태 |
| debulk:DeckArea | areaId, usableL/W/H, maxPointLoad, maxUniformLoad | partOf→Vessel, hosts→Cargo | Deck Layout | 적재 용량 |
| debulk:LashingAssembly | requiredCapacity(t), calcTension(t), safetyFactor | appliedTo→Cargo, uses→LashingElement, verifiedBy→Engineer | Lashing Calc | 고박 강도 |
| debulk:LashingElement | wll(t), angleDeg, count, length(m) | partOf→LashingAssembly | Equipment Spec | 유효 용량 |
| debulk:StabilityCase | disp(t), vcg(m), gm(m), rollAngle(deg) | evaluates→Vessel, considers→Cargo | Stability Calc | 안정성 상태 |
| debulk:LiftingPlan | liftId, method, slingAngleDeg, estLoadShare(t) | for→Cargo, uses→RiggingGear, verifiedBy→Engineer | Rigging Design | 인양 계획 |
| debulk:RiggingGear | gearId, type, wll(t), length(m) | partOf→LiftingPlan | Gear Spec | 장비 용량 |
| debulk:Equipment | equipId, type, swl(t), radius(m)? | allocatedTo→OperationTask | Equipment List | 작업 배정 |
| debulk:Manpower | personId, role, certificateId?, contact | assignedTo→OperationTask | Crew Roster | 인력 배정 |
| debulk:OperationTask | taskId, status, start/end(DateTime), sequence | relatesCargo→Cargo, uses→Equipment | Task Planning | 작업 상태 |
| debulk:Port/Jetty/Berth | code, draught, restriction | hosts→OperationTask | Port Database | 위치 정보 |
| debulk:Environment | wind(m/s), seaState, temp, accel_g | affects→LashingAssembly/StabilityCase | Weather API | 환경 영향 |
| debulk:Document | docId, type, version, fileRef | documents→(Plan/Report), about→(Vessel/Cargo) | Document Store | 문서 관리 |

자료: Load Plan, Stability Calculator, Equipment Spec, Crew Roster

**How it works (Operation Process)**

1. **Planning Phase**: 데이터 수집·제약 정의 → Draft → Reviewed → Approved (Loading Plan, Stowage Layout, Lashing Calc Sheet)
2. **Pre-Operation**: 자원 배정·브리핑 → Ready → Mobilized (Equipment & Workforce Plan, JSA)
3. **Execution**: 적재/고박/검사 → In-Progress → Paused/Resumed → Completed (QC Checklist, Photos, Survey Report)
4. **Post-Operation**: 서류/인계 → Completed → Archived (B/L, COA Evidence, Final Report)

---

> **[Marine/Bulk Domain Rule]** Barge/LCT operations use offshoreDeliveryPattern and MOSBStagingPattern as primary descriptors.
> Marine domain does NOT assign confirmedFlowCode. MOSB is an **Offshore Staging / Marine Interface Node**, not a Warehouse.

## Route Type Integration in Barge & Bulk Cargo Operations

### Bulk Cargo Route Type Patterns

Bulk and project cargo in the HVDC logistics network predominantly follow **Flow Code 3 and 4** due to the inherent requirements of offshore transportation via MOSB.

| Flow Code | Bulk Cargo Pattern | Typical Cargo | Routing |
|-----------|-------------------|---------------|---------|
| **route_type: MOSB_DIRECT** | Direct MOSB Transit | Heavy machinery, transformers, pre-assembled structures | Zayed Port → MOSB → LCT → AGI/DAS |
| **route_type: WH_MOSB** | Warehouse + MOSB | Bulk materials requiring consolidation | Zayed Port → AAA Storage → MOSB → LCT → AGI/DAS |
| **route_type: MIXED** | Incomplete/Awaiting | Bulk cargo at MOSB pending site assignment | MOSB staging area (temporary) |

### Barge/LCT Operations and Route Type

#### LCT Transport Model

Landing Craft Tank (LCT) and barge operations are the **exclusive mode** for bulk cargo delivery to AGI/DAS offshore platforms. This transport model enforces the following Flow Code characteristics:

```
LCT Operation Process:
1. Port Arrival (shipment_stage PRE_ARRIVAL) → Pre-customs clearance
2. Port Clearance → MOSB Transit (route_type MOSB_DIRECT/WH_MOSB initiated)
3. MOSB Staging → Bulk cargo consolidation, lashing preparation
4. LCT Loading → Seafastening, stability verification
5. Sea Passage → MOSB → AGI/DAS (8-12 hour transit)
6. Offshore Discharge → Final delivery (route_type MOSB_DIRECT/WH_MOSB completed)

Flow Code Determination:
- If cargo went directly from Port to MOSB: route_type = MOSB_DIRECT
- If cargo stopped at warehouse before MOSB: route_type = WH_MOSB
```

#### MOSB as Route Type Anchor

MOSB (Mussafah Offshore Supply Base) is the **mandatory transit point** for all AGI/DAS bulk cargo, making it the **Flow Code anchor** for offshore logistics:

```
MOSB Functional Role:
- Consolidation: Aggregate bulk cargo from multiple ports/warehouses
- Staging: Prepare cargo for LCT loading (lashing, seafastening)
- Quality Control: Inspect cargo condition before offshore transport
- Compliance: Verify FANR (nuclear), ADNOC permits, gate passes

Flow Code Impact:
- MOSB presence = route_type IN (MOSB_DIRECT, WH_MOSB, MIXED) (automatic)
- AGI/DAS destination + MOSB = route_type MOSB_DIRECT or WH_MOSB (enforced)
- Non-MOSB bulk cargo = Invalid for AGI/DAS (domain rule violation)
```

### RDF/OWL Implementation

#### Route Type Properties for Bulk Cargo

```turtle
@prefix debulk: <https://hvdc-project.com/ontology/bulk-cargo/> .
@prefix hvdc: <https://hvdc-project.com/ontology/core/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Route Type for Bulk Cargo
debulk:hasRouteType a owl:DatatypeProperty ;
    rdfs:label "Bulk Cargo Route Type" ;
    rdfs:comment "Route type for bulk cargo operations (MOSB_DIRECT, WH_MOSB, MIXED)" ;
    rdfs:domain debulk:Cargo ;
    rdfs:range xsd:integer ;
    sh:minInclusive 3 ;
    sh:maxInclusive 5 ;
    sh:message "Bulk cargo to AGI/DAS must use route_type MOSB_DIRECT, WH_MOSB, or MIXED" .


debulk:offshoreDeliveryPattern a owl:DatatypeProperty ;
    rdfs:label "Offshore Delivery Pattern" ;
    rdfs:comment "Describes the offshore leg routing pattern for bulk cargo to AGI/DAS" ;
    rdfs:domain debulk:Cargo ;
    rdfs:range xsd:string .    # "DIRECT_MOSB" | "WH_THEN_MOSB" | "PENDING_ASSIGNMENT"

debulk:mosbStagingPattern a owl:DatatypeProperty ;
    rdfs:label "MOSB Staging Pattern" ;
    rdfs:comment "MOSB staging and load preparation pattern" ;
    rdfs:domain debulk:Cargo ;
    rdfs:range xsd:string .    # "DIRECT_LOAD" | "CONSOLIDATED_LOAD" | "PENDING"
debulk:requiresMOSBStaging a owl:DatatypeProperty ;
    rdfs:label "Requires MOSB Staging" ;
    rdfs:comment "Boolean flag for MOSB staging requirement" ;
    rdfs:domain debulk:Cargo ;
    rdfs:range xsd:boolean ;
    sh:minCount 1 .

debulk:hasLCTTransport a owl:ObjectProperty ;
    rdfs:label "Has LCT Transport" ;
    rdfs:comment "Links bulk cargo to LCT/barge transport event" ;
    rdfs:domain debulk:Cargo ;
    rdfs:range debulk:TransportEvent .

debulk:mosbArrivalDate a owl:DatatypeProperty ;
    rdfs:label "MOSB Arrival Date" ;
    rdfs:comment "Date cargo arrived at MOSB for staging" ;
    rdfs:domain debulk:Cargo ;
    rdfs:range xsd:date .

debulk:mosbDepartureDate a owl:DatatypeProperty ;
    rdfs:label "MOSB Departure Date" ;
    rdfs:comment "Date LCT departed MOSB with cargo" ;
    rdfs:domain debulk:Cargo ;
    rdfs:range xsd:date .

debulk:hasRouteDescription a owl:DatatypeProperty ;
    rdfs:label "Route Description" ;
    rdfs:comment "Human-readable route description for the cargo (e.g. Port → MOSB → AGI). Replaces deprecated hasRouteDescription." ;
    rdfs:domain debulk:Cargo ;
    rdfs:range xsd:string .

# SHACL Constraint: AGI/DAS Bulk Cargo Must Use MOSB
debulk:AGIDASBulkConstraint a sh:NodeShape ;
    sh:targetClass debulk:Cargo ;
    sh:sparql [
        sh:message "AGI/DAS bulk cargo must transit through MOSB (Flow Code >= 3)" ;
        sh:select """
            PREFIX debulk: <https://hvdc-project.com/ontology/bulk-cargo/>
            SELECT $this
            WHERE {
                $this debulk:finalDestination ?dest ;
                      debulk:hasRouteType ?routeType .
                FILTER(?dest IN ("AGI", "DAS") && ?routeType NOT IN ("MOSB_DIRECT","WH_MOSB","MIXED"))
            }
        """ ;
    ] .
```

#### Instance Example: Transformer to AGI via LCT

```turtle
# Bulk Cargo: 85-ton Transformer
debulk:cargo/TRANSFORMER-AGI-T1 a debulk:Cargo ;
    debulk:cargoId "TRANSFORMER-AGI-T1" ;
    debulk:cargoType "Power Transformer" ;
    debulk:weight 85000 ;  # kg
    debulk:dimensions "12.5m × 4.2m × 5.8m" ;
    debulk:finalDestination "AGI" ;
    debulk:hasRouteType "MOSB_DIRECT" ;
    debulk:hasRouteDescription "Port → MOSB → AGI (LCT direct)" ;
    debulk:requiresMOSBStaging true ;
    debulk:mosbArrivalDate "2024-11-10"^^xsd:date ;
    debulk:mosbDepartureDate "2024-11-12"^^xsd:date ;
    debulk:hasLCTTransport debulk:transport/LCT-AGI-2024-11 .

# LCT Transport Event
debulk:transport/LCT-AGI-2024-11 a debulk:TransportEvent ;
    debulk:transportId "LCT-AGI-2024-11" ;
    debulk:vesselName "LCT-ADNOC-05" ;
    debulk:origin debulk:location/MOSB ;
    debulk:destination debulk:site/AGI ;
    debulk:departureDate "2024-11-12T06:00:00"^^xsd:dateTime ;
    debulk:arrivalDate "2024-11-12T18:00:00"^^xsd:dateTime ;
    debulk:seaState "Calm (1-2m)" ;
    debulk:cargoManifest ( debulk:cargo/TRANSFORMER-AGI-T1 ) .

# MOSB Staging Operation
debulk:operation/MOSB-STAGING-T1 a debulk:OperationTask ;
    debulk:taskId "MOSB-STAGING-T1" ;
    debulk:taskType "MOSB Staging & Lashing Preparation" ;
    debulk:relatesCargo debulk:cargo/TRANSFORMER-AGI-T1 ;
    debulk:location debulk:location/MOSB ;
    debulk:startDate "2024-11-10T08:00:00"^^xsd:dateTime ;
    debulk:endDate "2024-11-11T17:00:00"^^xsd:dateTime ;
    debulk:status "Completed" ;
    debulk:lashingVerified true ;
    debulk:seafasteningApproved true .
```

### SPARQL Queries for Bulk Cargo Flow Code

#### 1. Bulk Cargo Flow Code Distribution

```sparql
PREFIX debulk: <https://hvdc-project.com/ontology/bulk-cargo/>

SELECT ?routeType (COUNT(?cargo) AS ?count) (SUM(?weight) AS ?totalWeight)
WHERE {
    ?cargo a debulk:Cargo ;
           debulk:hasRouteType ?routeType ;
           debulk:weight ?weight .
}
GROUP BY ?routeType
ORDER BY ?routeType
```

#### 2. MOSB Staging Duration Analysis

```sparql
PREFIX debulk: <https://hvdc-project.com/ontology/bulk-cargo/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?cargo ?cargoId ?arrivalDate ?departureDate
       ((?departureDate - ?arrivalDate) AS ?stagingDays)
WHERE {
    ?cargo a debulk:Cargo ;
           debulk:cargoId ?cargoId ;
           debulk:mosbArrivalDate ?arrivalDate ;
           debulk:mosbDepartureDate ?departureDate .
}
ORDER BY DESC(?stagingDays)
```

#### 3. AGI/DAS Compliance Check

```sparql
PREFIX debulk: <https://hvdc-project.com/ontology/bulk-cargo/>

SELECT ?cargo ?destination ?routeType ?mosbStaging ?compliant
WHERE {
    ?cargo a debulk:Cargo ;
           debulk:finalDestination ?destination ;
           debulk:hasRouteType ?routeType ;
           debulk:requiresMOSBStaging ?mosbStaging .
    FILTER(?destination IN ("AGI", "DAS"))
    BIND(IF(?routeType IN ("MOSB_DIRECT","WH_MOSB","MIXED") && ?mosbStaging = true, "PASS", "FAIL") AS ?compliant)
}
ORDER BY ?compliant ?destination
```

#### 4. LCT Transport Efficiency

```sparql
PREFIX debulk: <https://hvdc-project.com/ontology/bulk-cargo/>

SELECT ?lct ?origin ?destination (COUNT(?cargo) AS ?cargoCount)
       ?departureDate ?arrivalDate
WHERE {
    ?lct a debulk:TransportEvent ;
         debulk:origin ?origin ;
         debulk:destination ?destination ;
         debulk:departureDate ?departureDate ;
         debulk:arrivalDate ?arrivalDate .
    ?cargo debulk:hasLCTTransport ?lct .
}
GROUP BY ?lct ?origin ?destination ?departureDate ?arrivalDate
ORDER BY DESC(?cargoCount)
```

### Bulk Cargo KPIs with Flow Code

| KPI Metric | Target | Calculation | Flow Code Relevance |
|------------|--------|-------------|---------------------|
| **MOSB Throughput** | 90-95% | (Flow Code 3 + route_type WH_MOSB) / Total Bulk Cargo | MOSB staging efficiency |
| **MOSB_DIRECT Ratio** | 60-70% | Flow Code 3 / (Flow Code 3 + route_type WH_MOSB) | Direct MOSB transit rate |
| **WH_MOSB Ratio** | 30-40% | Flow Code 4 / (Flow Code 3 + route_type WH_MOSB) | Warehouse consolidation rate |
| **MOSB Staging Time** | <48 hours | Avg(Departure - Arrival) at MOSB | Staging efficiency |
| **AGI/DAS Compliance** | 100% | AGI/DAS with Flow Code ≥3 / Total AGI/DAS | Mandatory MOSB rule |
| **LCT Utilization** | 80-85% | LCT trips with cargo / Total LCT trips | Transport efficiency |
| **MIXED route_type Resolution** | <3 days | Avg(Site Assignment - MOSB Arrival) | Incomplete routing resolution |

### Integration with Bulk Cargo Operations

#### Stowage & Lashing (Flow Code 3, 4)
- MOSB staging area stowage planning
- Seafastening calculations for LCT transport
- route_type determines stowage priority (route_type MOSB_DIRECT = urgent offshore)

#### Stability Control (Flow Code 3, 4)
- LCT stability verification before departure
- Cargo COG (Center of Gravity) adjustments at MOSB
- route_type impacts stability calculations (route_type WH_MOSB may have multiple items)

#### Lifting & Transport Handling (Flow Code 3, 4)
- MOSB crane operations for LCT loading
- Rigging plans specific to offshore transport
- route_type defines handling sequence (route_type MOSB_DIRECT loads first)

---

**Options (설계 선택지)**

1. **OWL/SHACL 엄격형**: 모든 클래스/속성/제약을 OWL/SHACL로 엄격하게 모델링. *Pros* 의미적 추론↑ / *Cons* 초기 모델링 복잡도↑
2. **하이브리드형(권장)**: OWL + CSV 교환 + SHACL 제약, 부족 구간은 유사 패턴 추천. *Pros* 실용성↑ / *Cons* 온톨로지 일관성 유지 필요
3. **실무 간소형**: 핵심 클래스만 모델링하고 나머지는 확장 가능한 구조. *Pros* 빠른 적용↑ / *Cons* 확장성 제한

**Roadmap (P→Pi→B→O→S + KPI)**

- **Prepare**: 클래스 스키마 정의, SHACL 제약 규칙 작성, CSV 템플릿 준비
- **Pilot**: /switch_mode LATTICE + /logi-master bulk-cargo-planning --deep --stability-check로 샘플 화물 1회전. KPI: 검증정확도 ≥97%, 안전성 ≥95%
- **Build**: 라싱 계산, 안정성 검증, 인양 계획 자동화 시스템 구축
- **Operate**: 실시간 모니터링, 이상 상황 즉시 알림 + 대안 제시
- **Scale**: 3D 좌표 연동, CAD/BIM 링크, 가속도 스펙트럼 분석 추가

**Automation notes**

- **입력 감지 →** /switch_mode LATTICE + /logi-master bulk-cargo-planning (화물→적재→고박→안정성→인양 계획)
- **표준 근거**: IMSBC, SOLAS, Port Notice 등 규정 기반 제약 검증
- **감사 포맷**: SHACL Validation 결과 + Stability Report + Lashing Calculation

**QA / Gap 체크**

- Cargo CSV에 **COG/중량/치수** 누락 없음?
- DeckArea에 **허용하중(균등/점하중)** 입력 완료?
- LashingElements **WLL·각도** 기입 및 세트 매핑 완료?
- StabilityCase에 **GM/VCG/조건** 기록?
- Equipment/Manpower **작업별 배정** 완료?

가정: (i) 모든 화물은 정확한 치수/중량 정보를 보유, (ii) 선박 데크 강도 데이터가 최신으로 유지됨, (iii) 환경 조건은 실시간으로 업데이트됨.

---

# Part 2: Detailed Class Specifications

## 속성 도메인/레인지(OWL 스타일 요약)

* `securedBy (Cargo → LashingAssembly)` [0..*]
* `appliedTo (LashingAssembly → Cargo)` [1..*]
* `uses (LashingAssembly → LashingElement)` [1..*]
* `placedOn (Cargo → DeckArea)` [1]
* `hosts (DeckArea → Cargo)` [0..*]
* `relatesCargo (OperationTask → Cargo)` [0..*]
* `allocatedTo (Equipment → OperationTask)` [0..*]
* `assignedTo (Manpower → OperationTask)` [0..*]
* `evaluates (StabilityCase → Vessel)` [1]
* `considers (StabilityCase → Cargo)` [0..*]
* `documents (Document → Plan/Report/Task)` [1..*]

## 제약(Constraints) 예시

* **Deck Strength**: `sum(load_i / footprint_i) ≤ deckStrength` (균등하중·점하중 모두 고려)
* **Lashing WLL**: `Σ(WLL_effective) ≥ requiredCapacity × SF` (SF≥2.0 예시)
* **Sling Angle**: 각도 작아질수록 다리장력 증가: `T_leg = W / (2 × sin(angle))`
* **Stability Gate**: `GM ≥ GM_min`, `VCG ≤ limitVCG`, `heel ≤ 5°` (예시 기준)

---

# Part 3: Validation & Verification

## SHACL 검증 규칙(요지)

데이터 일관성/안전 최소 기준을 자동 검출

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix debulk: <http://example.com/bulk#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

debulk:CargoShape a sh:NodeShape ;
  sh:targetClass debulk:Cargo ;
  sh:property [ sh:path debulk:weight ; sh:datatype xsd:decimal ; sh:minInclusive 0.1 ] ;
  sh:property [ sh:path debulk:dimL ; sh:datatype xsd:decimal ; sh:minInclusive 0.1 ] ;
  sh:property [ sh:path debulk:placedOn ; sh:minCount 1 ; sh:class debulk:DeckArea ] .

debulk:LashingAssemblyShape a sh:NodeShape ;
  sh:targetClass debulk:LashingAssembly ;
  sh:property [ sh:path debulk:uses ; sh:minCount 2 ; sh:class debulk:LashingElement ] ;
  sh:rule [ a sh:SPARQLRule ;
    sh:prefixes ( ) ;
    sh:construct """
      CONSTRUCT { ?this debulk:status "UNDER_CAPACITY" }
      WHERE {
        ?this debulk:requiredCapacity ?req .
        {
          SELECT ?this (SUM(?effWll) AS ?sumWll)
          WHERE { ?this debulk:uses ?e . ?e debulk:wll ?w . ?e debulk:angleDeg ?a .
                  BIND( (?w) * sin(?a * 3.14159/180) AS ?effWll ) }
          GROUP BY ?this
        }
        FILTER (?sumWll < (?req * 2.0))
      }
    """ ] .
```

*해석*: 라싱 요소의 유효 WLL(각도 보정 합계)이 요구능력×안전율(2.0) 미만이면 `UNDER_CAPACITY` 플래그.

## SPARQL 질의 예시

```sparql
# Q1: Cargo별 라싱 유효용량 합계 추출
PREFIX debulk: <http://example.com/bulk#>
SELECT ?cargo (SUM(?wll*sin(?a*pi()/180)) AS ?sumEffWll)
WHERE {
  ?cargo a debulk:Cargo ; debulk:securedBy ?ls .
  ?ls debulk:uses ?e . ?e debulk:wll ?wll ; debulk:angleDeg ?a .
}
GROUP BY ?cargo
```

```sparql
# Q2: 데크 허용균등하중 대비 점검
PREFIX debulk: <http://example.com/bulk#>
SELECT ?deck ?sumWeight ?area ?uniformLoad ?maxUL
WHERE {
  ?deck a debulk:DeckArea ; debulk:usableL ?L ; debulk:usableW ?W ; debulk:maxUniformLoad ?maxUL .
  BIND((?L*?W) AS ?area)
  { SELECT ?deck (SUM(?w) AS ?sumWeight)
    WHERE { ?cargo debulk:placedOn ?deck ; debulk:weight ?w } GROUP BY ?deck }
  BIND(?sumWeight / ?area AS ?uniformLoad)
}
```

## 컴피턴시 질문(Competency Questions)

모델이 답해야 할 질의 정의(요구사항 유도용):

1. 특정 `Cargo`의 **총 라싱 유효용량**은 요구능력 대비 충분한가?
2. `DeckArea` A1에 적재된 화물들의 **평균/최대 접지하중**은 허용치 이내인가?
3. 주어진 `StabilityCase`에서 **총중량/VCG/GM 변화**는 기준을 만족하는가?
4. 반경 R에서 크레인의 **SWL ≥ 예상 훅하중**인가? 불충분 시 대체안은?
5. 야간조 작업에 필요한 **인력/자격증/연락망**은 배정되었는가?

---

# Part 4: Implementation Guide

## 교환 스키마(Operational CSV/Excel 템플릿)

### Cargo.csv

| cargoId | type | weight_t | dimL_m | dimW_m | dimH_m | cogX_m | cogY_m | cogZ_m | stackable | placedOn |
|---------|------|---------:|-------:|-------:|-------:|-------:|-------:|-------:|:---------:|----------|
| C001 | SteelStructure | 42.5 | 12.0 | 3.2 | 3.5 | 5.8 | 0.0 | 1.4 | FALSE | A1 |

### LashingElements.csv

| lashId | type | wll_t | angle_deg | length_m | assemblyId |
|--------|------|------:|----------:|---------:|------------|
| LE01 | Chain10mm | 6.0 | 45 | 8.0 | LS01 |

### DeckAreas.csv

| areaId | vessel | usableL_m | usableW_m | maxUniform_tpm2 | maxPoint_t |
|--------|--------|----------:|----------:|----------------:|-----------:|
| A1 | Vessel_ABC | 20 | 10 | 15 | 60 |

### Tasks.csv (스케줄·자원 배정)

| taskId | phase | relatesCargo | start_utc | end_utc | eq_alloc | manpower |
|--------|-------|--------------|-----------|---------|----------|----------|
| T001 | Loading | C001 | 2025-11-02T06:00 | 2025-11-02T10:00 | Crane_M80 | Rigger3,Banksman2 |

## 문서 매핑(Plans ↔ Ontology)

| 문서 | 온톨로지 매핑 | 자동 생성 포인트 |
|------|---------------|------------------|
| Vessel Loading Plan | `OperationTask`, `DeckArea`, `Cargo` | Gantt/테이블, COG 리스트, Layout 주석 |
| Seafastening/Lashing Plan | `LashingAssembly`, `LashingElement`, `Environment` | 각도·장력 표, 부족 용량 플래그 |
| Stability Report | `StabilityCase`, `Vessel`, `Cargo` | 중량/VCG 집계 표, 한계 비교 |
| Lifting/Rigging Plan | `LiftingPlan`, `RiggingGear`, `Equipment` | 다리장력 계산 표, WLL 매칭 체크 |
| Logistics Execution Plan | `OperationTask`, `Manpower`, `Equipment` | 교대별 배정표, 연락처 리스트 |

## 예시 인스턴스(직관용 Turtle)

```turtle
@prefix debulk: <http://example.com/bulk#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

debulk:Cargo_001 a debulk:Cargo ;
  debulk:cargoType "SteelStructure" ;
  debulk:weight "42.5"^^xsd:decimal ;
  debulk:dimL "12.0"^^xsd:decimal ; debulk:dimW "3.2"^^xsd:decimal ; debulk:dimH "3.5"^^xsd:decimal ;
  debulk:cogX "5.8"^^xsd:decimal ; debulk:cogY "0.0"^^xsd:decimal ; debulk:cogZ "1.4"^^xsd:decimal ;
  debulk:placedOn debulk:Deck_A1 ;
  debulk:securedBy debulk:LashSet_01 .

debulk:Deck_A1 a debulk:DeckArea ;
  debulk:areaId "A1" ; debulk:usableL "20.0"^^xsd:decimal ; debulk:usableW "10.0"^^xsd:decimal ;
  debulk:maxUniformLoad "15.0"^^xsd:decimal .

debulk:LashSet_01 a debulk:LashingAssembly ;
  debulk:requiredCapacity "1.2"^^xsd:decimal ;  # g·W / μ 등으로 산정된 필요 능력(예)
  debulk:uses debulk:Chain_10mm_1, debulk:Chain_10mm_2 .

debulk:Chain_10mm_1 a debulk:LashingElement ; debulk:wll "6.0"^^xsd:decimal ; debulk:angleDeg "45"^^xsd:decimal .
debulk:Chain_10mm_2 a debulk:LashingElement ; debulk:wll "6.0"^^xsd:decimal ; debulk:angleDeg "45"^^xsd:decimal .

debulk:Stab_LoadedCalm a debulk:StabilityCase ;
  debulk:gm "1.8"^^xsd:decimal ; debulk:vcg "4.2"^^xsd:decimal ; debulk:rollAngle "2.0"^^xsd:decimal ;
  debulk:evaluates debulk:Vessel_ABC ; debulk:considers debulk:Cargo_001 .
```

## OWL 스키마(발췌)

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix debulk: <http://example.com/bulk#> .

debulk:Cargo a owl:Class ; rdfs:label "Cargo" .
debulk:LashingAssembly a owl:Class .
debulk:LashingElement a owl:Class .
debulk:DeckArea a owl:Class .

debulk:securedBy a owl:ObjectProperty ;
  rdfs:domain debulk:Cargo ; rdfs:range debulk:LashingAssembly .
debulk:placedOn a owl:ObjectProperty ;
  rdfs:domain debulk:Cargo ; rdfs:range debulk:DeckArea .
debulk:uses a owl:ObjectProperty ;
  rdfs:domain debulk:LashingAssembly ; rdfs:range debulk:LashingElement .

debulk:weight a owl:DatatypeProperty .
debulk:dimL a owl:DatatypeProperty .
debulk:cogX a owl:DatatypeProperty .
```

---

# Part 5: Governance & Extension

## 지배 규칙(정책·규정) 표현 패턴

* `ComplianceRule` 클래스로 규정 항목 정의(예: IMSBC, SOLAS, Port Notice)
* `appliesTo`(Rule→Class/Property), `threshold`(수치), `reference`(문헌식별), `jurisdiction`
* 규정 점검은 **추론 규칙** 또는 **SHACL/SPARQL**로 구현

## 버전·추적성(Traceability)

* 모든 엔티티에 `version`, `createdAt`, `createdBy`, `sourceDoc` 부여
* 변경 기록: `supersedes`(구버전), `wasDerivedFrom`(원데이터), `approvalStatus`
* 파일 링크는 `Document.fileRef`(URI)로 관리

## 차후 확장 포인트

* 3D 좌표(모델 ID) 연동, CAD/BIM 링크 속성(`modelRef`)
* 가속도 스펙트럼/항해 구간별 `Environment` 타임시리즈
* 비용/계약(`CostItem`, `LaytimeEvent`) 추가
* 포장/방수/내식(`Packaging`, `Protection`) 속성 추가

### 결론

이 온톨로지는 **계획↔실행↔검증**을 하나의 그래프로 잇는다.
동일 데이터를 문서, 체크리스트, 계산, 리포트로 **재사용**할 수 있게 해준다.
CSV/OWL/SHACL 샘플을 기반으로 바로 파일화를 진행하면 현장 적용 속도가 빨라진다.


