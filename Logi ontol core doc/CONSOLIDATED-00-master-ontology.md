---
title: "HVDC Logistics Knowledge Graph — Master Ontology"
type: "master-ontology-spine"
domain: "hvdc-logistics"
version: "1.0"
date: "2026-04-11"
status: "active"
standards: ["RDF","OWL","SHACL","SPARQL","JSON-LD","GS1-EPCIS","DCSA-T&T","WCO-DM","PROV-O","OWL-Time","SKOS","DQV"]
replaces: []
extended_by: ["CONSOLIDATED-01","CONSOLIDATED-02","CONSOLIDATED-03","CONSOLIDATED-04",
              "CONSOLIDATED-05","CONSOLIDATED-06","CONSOLIDATED-07","CONSOLIDATED-09"]
evidence_layer: ["CONSOLIDATED-08"]
---

# hvdc-master-ontology · CONSOLIDATED-00

## 📑 Table of Contents
1. [Governance & Dictionaries](#part-1)
2. [Identity & Key Policy](#part-2)
3. [Core Master Data Model](#part-3)
4. [Execution Transaction Model](#part-4)
5. [KG Node/Edge Design](#part-5)
6. [Validation Rules](#part-6)

---

> **MASTER GOVERNANCE RULE**
> 1. **Flow Code is a warehouse-handling classification only.**
>    Restricted to `WarehouseHandlingProfile`. No other domain may own or assign Flow Code.
> 2. **Program-wide shipment visibility shall use Journey Stage, RoutingPattern, Milestone, and Leg.**
>    (`routingPattern`, `currentStage`, `leg_sequence`, `JourneyLeg`)
> 3. **Port, Customs, Document, Cost, Marine, and Communication domains**
>    may reference warehouse-flow *evidence*, but shall NOT own or assign Flow Code.
> 4. **MOSB is an Offshore Staging / Marine Interface Node**, not a Warehouse.

---

## Part 1: Governance & Dictionaries {#part-1}

### 1.1 Data Classification

| Data Class | Examples |
|---|---|
| Master Data | Project, Package, PO, Vendor, MaterialMaster, Port, Terminal, Warehouse, Site, EquipmentResource |
| Transaction Data | Shipment, ShipmentLeg, PortCall, CustomsEntry, ReleaseOrder, Delivery, WarehouseTask, SiteReceipt |
| Document Data | CI, PL, BL, BOE, DO, Permit, MRR, MRI, ITP, MAR, MRS, MIS, POD, GRN, OSDR |
| Event Data | MilestoneEvent, InspectionEvent, WarehouseEvent, MarineEvent |
| Exception Data | Delay, Damage, Shortage, NCR, Claim |
| Cost Data | Invoice, InvoiceLine, Duty, DEM/DET, PortCharge, WarehouseCharge, MarineCharge |
| Evidence Data | AuditRecord, CommunicationEvent, ApprovalAction |

### 1.2 RoutingPattern Dictionary

> RoutingPattern은 Flow Code 0~5 숫자 코드를 대체하는 named pattern 시스템입니다.
> `WarehouseHandlingProfile.confirmedFlowCode` (0~5) 는 창고 내부 용도로만 유지됩니다.

#### Tier 1: ShipmentRoutingPattern (전체 여정 분류)

| Pattern | 구 Flow Code | 경로 | 설명 |
|---|---|---|---|
| `DIRECT` | Flow 1 | Port → Site | 직송 (창고 없음) |
| `WH_ONLY` | Flow 2 | Port → WH → Site | 창고 경유, MOSB 없음 |
| `MOSB_DIRECT` | Flow 3 | Port → MOSB → Site | MOSB 경유, 창고 없음 |
| `WH_MOSB` | Flow 4 | Port → WH → MOSB → Site | 창고 + MOSB |
| `MIXED` | Flow 5 | 복합/미확정 | 혼합 또는 미완료 |
| `PRE_ARRIVAL` | Flow 0 | — | 도착 전, 패턴 미확정 |

#### Tier 2: MarineRoutingPattern (해상/오프쇼어 전용)

| Pattern | 설명 | 사용 도메인 |
|---|---|---|
| `DIRECT_MOSB` | Port → MOSB 직항 | CONSOLIDATED-04 (Marine/Bulk) |
| `WH_THEN_MOSB` | WH 경유 후 MOSB | CONSOLIDATED-04 (Marine/Bulk) |
| `LCT_DIRECT` | LCT 직접 하역 | CONSOLIDATED-04 (Marine/Bulk) |
| `OFFSHORE_PENDING` | 해상 경로 미확정 | Exception 처리 |

#### Tier 3: ImportRoutingDecision (Port 도메인 전용 properties)

| Property | 설명 | 사용 파일 |
|---|---|---|
| `plannedRoutingPattern` | 통관 시 선언한 계획 경로 | CONSOLIDATED-07 |
| `declaredDestination` | 신고 목적지 (AGI/DAS/MIR/SHU) | CONSOLIDATED-07 |
| `offshoreTransitRequired` | MOSB 필요 여부 (boolean) | CONSOLIDATED-07 |
| `importRoutingDecision` | 통관 처리 방식 결정 | CONSOLIDATED-07 |

#### 도메인별 사용 규칙

| 도메인 | 허용 용어 | 금지 용어 |
|---|---|---|
| Shipment (core) | `ShipmentRoutingPattern` 값들 | — |
| Port (07) | `plannedRoutingPattern`, `declaredDestination`, `offshoreTransitRequired` | `assignedFlowCode` |
| Document/OCR (03) | `routeEvidence`, `destinationEvidence`, `mosbLegIndicator` | `extractedFlowCode` |
| Cost (05) | `costByRoutingPattern`, `routeBasedCostDriver` | `costByFlowCode` |
| Marine/Bulk (04) | `MarineRoutingPattern`, `offshoreDeliveryPattern` | `Flow Code 3/4/5` |
| Warehouse (02) | `WarehouseHandlingProfile.confirmedFlowCode` | 다른 도메인 적용 금지 |
| Material Handling (06) | `ShipmentRoutingPattern` + `MilestoneStatus` | `Flow Code` 전체 체인 사용 |

---

### 1.3 Terminology Normalization

| 기존 용어 | 표준 용어 | 이유 | 위험 |
|---|---|---|---|
| Flow Code (Port→WH→MOSB→Site) | `ShipmentRoutingPattern` | 경로는 warehouse 내부 아님 | Semantic collision |
| Flow Code 0 "Pre Arrival" | `PRE_ARRIVAL` | 선적 Milestone, 창고 아님 | Wrong state machine |
| Flow Code 1 "Port→Site" | `DIRECT` | 경로 설명자 | Broken warehouse semantics |
| Flow Code 2 "Port→WH→Site" | `WH_ONLY` | 경로 설명자 | Confuses route vs WH task |
| Flow Code 3 "Port→MOSB→Site" | `MOSB_DIRECT` | Marine/offshore 경로 | Misclassifies MOSB |
| Flow Code 4 "Port→WH→MOSB→Site" | `WH_MOSB` | 복합 경로 | Mixed semantics |
| Flow Code 5 "Mixed" | `MIXED` | Exception 상태 | Unclear closure |
| MOSB (as Warehouse) | MOSB as `OffshoreStaging` Node | MOSB는 창고 아님 | Location ambiguity |
| assignedFlowCode (Port) | `plannedRoutingPattern` | Port는 WHP 소유 금지 | Ontology boundary violation |
| extractedFlowCode (OCR) | `routeEvidence` | 문서는 증거만 제공 | Wrong ownership |
| costByFlowCode | `costByRoutingPattern` | 비용은 경로 기반 | Wrong cost driver |
| Material Storage Code | `StorageRequirementClass` | 보관 조건, process 아님 | Wrong data typing |
| Site Offloading | Site Unloading | 표준 물류 용어 | Terminology inconsistency |
| Site delivery status by Flow Code | `DeliveryStatus` / `SiteReceiptStatus` | Milestone 로직임 | Query failure |

---
