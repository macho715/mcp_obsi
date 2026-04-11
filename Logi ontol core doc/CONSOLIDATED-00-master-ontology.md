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

### 1.4 MilestoneEvent Class

MilestoneEvent는 물류 이벤트의 발생 시점을 기록하는 1등급 클래스입니다.
Journey Stage(현재 상태 버킷)와 달리, Milestone은 계획/추정/실적 시점을 모두 포함합니다.

```turtle
@prefix hvdc: <http://samsung.com/project-logistics#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

hvdc:MilestoneEvent a owl:Class ;
    rdfs:label "Logistics Milestone Event" .

hvdc:milestoneCode      a owl:DatatypeProperty ; rdfs:domain hvdc:MilestoneEvent ; rdfs:range xsd:string .
hvdc:milestoneName      a owl:DatatypeProperty ; rdfs:domain hvdc:MilestoneEvent ; rdfs:range xsd:string .
hvdc:objectType         a owl:DatatypeProperty ; rdfs:domain hvdc:MilestoneEvent ; rdfs:range xsd:string .
hvdc:objectId           a owl:DatatypeProperty ; rdfs:domain hvdc:MilestoneEvent ; rdfs:range xsd:string .
hvdc:plannedDt          a owl:DatatypeProperty ; rdfs:domain hvdc:MilestoneEvent ; rdfs:range xsd:dateTime .
hvdc:estimatedDt        a owl:DatatypeProperty ; rdfs:domain hvdc:MilestoneEvent ; rdfs:range xsd:dateTime .
hvdc:actualDt           a owl:DatatypeProperty ; rdfs:domain hvdc:MilestoneEvent ; rdfs:range xsd:dateTime .
hvdc:location           a owl:ObjectProperty  ; rdfs:domain hvdc:MilestoneEvent ; rdfs:range hvdc:Node .
hvdc:responsibleParty   a owl:ObjectProperty  ; rdfs:domain hvdc:MilestoneEvent ; rdfs:range hvdc:Organization .
hvdc:sourceDocument     a owl:ObjectProperty  ; rdfs:domain hvdc:MilestoneEvent ; rdfs:range hvdc:Document .
hvdc:sourceSystem       a owl:DatatypeProperty ; rdfs:domain hvdc:MilestoneEvent ; rdfs:range xsd:string .
hvdc:statusAfterEvent   a owl:DatatypeProperty ; rdfs:domain hvdc:MilestoneEvent ; rdfs:range xsd:string .
hvdc:exceptionFlag      a owl:DatatypeProperty ; rdfs:domain hvdc:MilestoneEvent ; rdfs:range xsd:boolean .
```

> **Journey Stage ↔ Milestone 관계**: Milestone 발생이 Journey Stage 전환을 트리거합니다.
> - M110 (WH Received) → `currentStage = "WH_RECEIPT"` → `WarehouseHandlingProfile` 생성 시작
> - M121 (Dispatched) → `currentStage = "WH_DISPATCH"`
> - `confirmedFlowCode`는 **M110 이후에만** 설정 가능. M110 이전 = `flowConfirmationStatus: "tentative"`

### 1.5 Milestone Dictionary M10~M160

| Milestone | 이름 | E2E Step | Journey Stage | 책임 도메인 |
|---|---|---|---|---|
| M10 | Cargo Ready | Step 2 | PLANNING | Vendor/Expeditor |
| M20 | Packed / Marked | Step 3 | ORIGIN_DISPATCH | Vendor |
| M30 | Pickup Completed | Step 4 | ORIGIN_DISPATCH | Forwarder |
| M40 | Export Cleared | Step 5 | ORIGIN_DISPATCH | Export Broker |
| M50 | Terminal Received | Step 6 | PORT_ENTRY | Terminal |
| M60 | Loaded On Board | Step 7 | PORT_ENTRY | Carrier |
| M61 | ATD (Actual Time of Departure) | Step 7 | TERMINAL_HANDLING | Carrier |
| M70 | Transshipment Occurred | Step 8 | TERMINAL_HANDLING | Carrier |
| M80 | ATA (Actual Time of Arrival) | Step 9 | PORT_ENTRY | Carrier/Agent |
| M90 | BOE Submitted | Step 10 | CUSTOMS_CLEARANCE | Import Broker |
| M91 | BOE Cleared | Step 10 | CUSTOMS_CLEARANCE | Import Broker |
| M92 | DO Released | Step 11 | CUSTOMS_CLEARANCE | Carrier/Agent |
| M100 | Gate-out Completed | Step 11 | INLAND_HAULAGE | Terminal/Forwarder |
| **M110** ★ | **Warehouse Received (WH In)** | Step 13 | **WH_RECEIPT** | WH Operator |
| M111 | Put-away Completed | Step 14 | WH_STORAGE | WH Operator |
| M115 | MOSB Staged | Step 16 | MOSB_STAGING | Marine Contractor |
| M116 | LCT/Barge Loaded | Step 16 | OFFSHORE_TRANSIT | Marine Contractor |
| M117 | Sail-away Approved | Step 16 | OFFSHORE_TRANSIT | ALS/Marine |
| M120 | Picked / Staged | Step 15 | WH_DISPATCH | WH Operator |
| M121 | Dispatched | Step 15 | WH_DISPATCH | WH/Site Logistics |
| M130 | Site Arrived | Step 17 | SITE_RECEIVING | Site Logistics |
| M131 | Site Inspected — Good | Step 17 | SITE_RECEIVING | QA/QC |
| M132 | Site Inspected — OSD | Step 17 | SITE_RECEIVING | QA/QC |
| M140 | POD / GRN / Handover | Step 18 | MATERIAL_ISSUE | Site Stores |
| M150 | Claim Opened | Step 19 | CLOSEOUT | Claims |
| M160 | Cost Closed | Step 19 | CLOSEOUT | Cost Control |

★ **M110 = WarehouseHandlingProfile 생성 트리거.**
M110 WH In 이벤트 발생 전: `flowConfirmationStatus = "tentative"`.
M110 발생 후: `flowConfirmationStatus = "confirmed"`.

#### AGI/DAS 도메인 룰 (VIOLATION-2 연동)

```
IF declaredDestination IN (AGI, DAS)
   AND routingPattern IN (MOSB_DIRECT, WH_MOSB, MIXED)
   AND M130.actualDt IS NOT NULL
   AND M115.actualDt IS NULL
→ VIOLATION-2: AGI/DAS 화물에 MOSB Milestone M115 누락
```

→ SHACL 구현: Part 6 `hvdc:AGIDASStagingShape` 참조

---

## Part 2: Identity & Key Policy {#part-2}

### 2.1 Identifier Object Model

**핵심 원칙**: One internal object, many external identifiers.

```turtle
hvdc:Identifier a owl:Class ;
    rdfs:label "Logistics Identifier" ;
    rdfs:comment "외부 식별자 단일 모델. ShipmentUnit/CargoUnit/Document 공유" .

hvdc:identifierScheme  a owl:DatatypeProperty ; rdfs:domain hvdc:Identifier ; rdfs:range xsd:string .
hvdc:identifierValue   a owl:DatatypeProperty ; rdfs:domain hvdc:Identifier ; rdfs:range xsd:string .
hvdc:normalizedValue   a owl:DatatypeProperty ; rdfs:domain hvdc:Identifier ; rdfs:range xsd:string .
hvdc:sourceSystem      a owl:DatatypeProperty ; rdfs:domain hvdc:Identifier ; rdfs:range xsd:string .
hvdc:isPrimary         a owl:DatatypeProperty ; rdfs:domain hvdc:Identifier ; rdfs:range xsd:boolean .
hvdc:validFrom         a owl:DatatypeProperty ; rdfs:domain hvdc:Identifier ; rdfs:range xsd:dateTime .
hvdc:validTo           a owl:DatatypeProperty ; rdfs:domain hvdc:Identifier ; rdfs:range xsd:dateTime .

hvdc:resolvesTo a owl:ObjectProperty ;
    rdfs:domain hvdc:Identifier ;
    rdfs:comment "IdentityKey → ShipmentUnit / CargoUnit / Document / Container" .
```

### 2.2 Identifier Families (9개)

| 패밀리 | 식별자 종류 | 연결 대상 |
|---|---|---|
| Project | projectCode | Project |
| Procurement | packageNo, poNo, vendorCode | Package, PO, Vendor |
| Material | materialCode, mfgPartNo, serialNo, **HVDC_CODE** | MaterialMaster, CargoUnit |
| Shipment | shipmentId, bookingNo, **blNo**, voyageNo | Shipment, BL |
| Container | **containerNo**, sealNo | Container |
| Customs | **boeNo**, declarationLineRef | CustomsEntry |
| Release | **doNo**, gatePassRef | ReleaseOrder |
| Warehouse | whReceiptNo, locationCode | WarehouseTask |
| Exception/Cost | exceptionId, claimRef, invoiceNo, costCode | Exception, Invoice |

> **HVDC_CODE 규칙**: HVDC_CODE는 유일 식별자가 아님. `IdentityKey`로 MaterialMaster/CargoUnit/Delivery/Site demand를 교차 연결하는 태그임.

### 2.3 Parent-Child Hierarchy

```
Project
  └─ hasPackage → Package
       └─ coveredBy → PurchaseOrder
            └─ issuedTo → Vendor
                 └─ supplies → MaterialMaster
                      ├─ tagged → HVDCCodeTag
                      └─ unitizedAs → CargoUnit
                           ├─ packedIn → Container
                           └─ belongsTo → Shipment
```

### 2.4 Key Resolution Flow (ShipmentUnit 중심)

```
[임의 키 입력: HVDC_CODE / BL / BOE / containerNo / ...]
        │
        ▼
hvdc:Identifier.normalize()
        │
        ▼
hvdc:resolvesTo → ShipmentUnit / CargoUnit / Document / Container
        │
        ▼
ShipmentUnit
  ├─ hasKey[]                    → Identifier (N개 외부 식별자)
  ├─ hasCurrentStage             → Journey Stage (enum)
  ├─ hasRoutingPattern           → ShipmentRoutingPattern
  ├─ hasWarehouseHandlingProfile → WarehouseHandlingProfile  ← Flow Code 유일 소유
  ├─ hasJourneyLeg[]             → JourneyLeg
  ├─ hasMilestone[]              → MilestoneEvent
  ├─ hasDocument[]               → Document
  ├─ hasCostItem[]               → CostItem
  └─ hasException[]              → Exception
```

---

## Part 3: Core Master Data Model {#part-3}

### 3.1 Master Nodes — Required Attribute Governance

| 클래스 | 필수 속성 | 옵션 속성 |
|---|---|---|
| `Project` | projectCode, projectName, status | country, startDate, endDate |
| `Package` | packageNo, packageType, siteCode | scope, requiredDate |
| `PurchaseOrder` | poNo, vendorCode, incoterm, currency | issueDate, deliveryTerms |
| `Vendor` | vendorCode, vendorName, role | country, contactRef |
| `MaterialMaster` | materialCode, description, uom | hsCode, origin, serialNo |
| `HVDCCodeTag` | hvdcCode | engineeringArea, siteRelevance |

### 3.2 Location Nodes

| 클래스 | 필수 속성 | 비고 |
|---|---|---|
| `Port` | portCode, UNLOCODE, portName | UN/LOCODE 표준 |
| `Terminal` | terminalId, terminalName, portId | berth 포함 |
| `Warehouse` | warehouseId, name, type, operator | Indoor/Outdoor/DangerousCargo |
| `WarehouseLocation` | locationCode, zone | rack/bin/yard, capacityClass |
| `Site` | siteCode, siteName, onshoreOffshore | AGI/DAS/MIR/SHU |
| `MOSB` | type: **OffshoreStaging** | ⚠️ Warehouse 분류 금지 |

### 3.3 Resource Nodes

| 클래스 | 필수 속성 | 비고 |
|---|---|---|
| `Carrier` | carrierCode, carrierName, mode | SCAC 또는 자체코드 |
| `Forwarder` | forwarderCode, name, serviceRole | 3PL 포함 |
| `EquipmentResource` | equipId, equipType, SWL | certificateRef 포함 |

---

## Part 4: Execution Transaction Model {#part-4}

### 4.1 Transaction Node Attribute Governance

```turtle
# Shipment: 운송 단위 (required attributes)
# shipmentId, mode, status, plannedRoutingPattern,
# origin, destination, grossWeight, volume, ETD, ETA, ATD, ATA

# CargoUnit: 물리적 화물 단위
# cargoUnitId, packageNo, grossWeight, volume, dimensions, condition

# CustomsEntry: 통관 트랜잭션 (BOE 문서와 분리)
# customsEntryId, boeRef, customsStatus, duty, broker, clearanceDate, consigneeCode, hsCode

# ReleaseOrder: 화물 Release 트랜잭션 (DO 문서와 분리)
# releaseOrderId, doRef, releaseDate, terminal, freeTime, gatePassRef

# WarehouseTask: WH 내부 작업
# taskId, warehouseId, location, stockStatus, storageRequirementClass, preservationStatus

# SiteReceipt: 현장 수령
# receiptId, siteCode, receiptType (Good|OSD), inspectionResult, mrrRef, osdrRef, mrsRef, misRef
```

### 4.2 E2E 19단계 프로세스 → Milestone 매핑

| Step | 이름 | Milestone | Journey Stage |
|---|---|---|---|
| 1 | PO Release | — | PLANNING |
| 2 | Vendor Readiness | M10 | PLANNING |
| 3 | Packing | M20 | ORIGIN_DISPATCH |
| 4 | Pickup | M30 | ORIGIN_DISPATCH |
| 5 | Export Clearance | M40 | ORIGIN_DISPATCH |
| 6 | Terminal Receiving | M50 | PORT_ENTRY |
| 7 | Vessel Loading/ATD | M60, M61 | TERMINAL_HANDLING |
| 8 | Ocean / Transship | M70 | TERMINAL_HANDLING |
| 9 | ATA / Pre-arrival | M80 | PORT_ENTRY |
| 10 | Import BOE | M90, M91 | CUSTOMS_CLEARANCE |
| 11 | DO / Gate-out | M92, M100 | INLAND_HAULAGE |
| 12 | Inland Transport | (leg event) | INLAND_HAULAGE |
| 13 | **WH Receiving** ★ | **M110** | **WH_RECEIPT** |
| 14 | Put-away / Storage | M111 | WH_STORAGE |
| 15 | Picking / Dispatch | M120, M121 | WH_DISPATCH |
| 16 | Offshore/Heavy-lift | M115, M116, M117 | MOSB_STAGING / OFFSHORE_TRANSIT |
| 17 | Site Delivery/Insp. | M130, M131/M132 | SITE_RECEIVING |
| 18 | POD / GRN | M140 | MATERIAL_ISSUE |
| 19 | Exception / Cost | M150, M160 | CLOSEOUT |

★ Step 13 = WarehouseHandlingProfile 생성 트리거

---

## Part 5: KG Node/Edge Design {#part-5}

### 5.1 Node Family (8개)

| 패밀리 | 주요 클래스 | Primary Key |
|---|---|---|
| **Master** | Project, Package, PO, Vendor, MaterialMaster | 내부 URI |
| **Transport** | Shipment, ShipmentLeg, PortCall, CustomsEntry, ReleaseOrder, Delivery | shipmentId, blNo |
| **Physical** | CargoUnit, Container, EquipmentResource | packageNo, containerNo |
| **Document** | BL, BOE, DO, Permit, Invoice, CI, PL, MRR, OSDR, POD | documentNo |
| **Event** | MilestoneEvent, InspectionEvent, WarehouseEvent, MarineEvent | eventId |
| **Exception** | Delay, Damage, Shortage, NCR, Claim | exceptionId, claimRef |
| **Cost** | InvoiceLine, CostTransaction, TariffRef, DEMDETClock | invoiceNo, costCode |
| **Evidence** | AuditRecord, CommunicationEvent, ApprovalAction | emailId, threadId |

### 5.2 Edge Grammar

```turtle
# Containment / Hierarchy
hvdc:hasPackage, hvdc:coveredBy, hvdc:containsCargoUnit, hvdc:packedIn, hvdc:hasUnit

# Movement
hvdc:hasLeg, hvdc:departsFrom, hvdc:arrivesAt, hvdc:deliveredTo, hvdc:storedAt

# Evidence
hvdc:evidencedBy, hvdc:references, hvdc:attachedTo, hvdc:provenanceOf

# Status / Event
hvdc:hasMilestone, hvdc:hasInspection, hvdc:hasException, hvdc:triggeredBy

# Responsibility
hvdc:issuedTo, hvdc:operatedBy, hvdc:approvedBy, hvdc:handledBy, hvdc:assignedTo

# Compliance
hvdc:requiresPermit, hvdc:classifiedByHS, hvdc:conformsTo, hvdc:governedBy

# Finance
hvdc:chargesFor, hvdc:mappedToCostCode, hvdc:linkedToInvoice, hvdc:accruesTo
```

### 5.3 SPARQL Query Templates

#### Template 1: ETA → 전체 컨텍스트 (7일 이내 도착 예정)

```sparql
PREFIX hvdc: <http://samsung.com/project-logistics#>
SELECT ?unit ?stage ?location ?boe ?do ?risk
WHERE {
  ?leg hvdc:estimatedATA ?eta .
  FILTER(?eta > NOW() && ?eta < NOW() + "P7D"^^xsd:duration)
  ?shipment hvdc:hasLeg ?leg ; hvdc:hasUnit ?unit .
  ?unit hvdc:hasCurrentStage ?stage ;
        hvdc:hasCurrentLocation ?location .
  OPTIONAL { ?unit hvdc:hasCustomsEntry/hvdc:boeRef ?boe }
  OPTIONAL { ?unit hvdc:hasReleaseOrder/hvdc:doRef ?do }
  OPTIONAL { ?unit hvdc:hasException ?risk }
}
ORDER BY ?eta
```

#### Template 2: HVDC_CODE → 전체 이력

```sparql
PREFIX hvdc: <http://samsung.com/project-logistics#>
SELECT ?unit ?stage ?vendor ?shipment ?whp ?site ?cost
WHERE {
  ?key hvdc:identifierScheme "HVDC_CODE" ;
       hvdc:identifierValue ?hvdcCode ;
       hvdc:resolvesTo ?unit .
  ?unit hvdc:hasCurrentStage ?stage ;
        hvdc:hasVendor ?vendor .
  OPTIONAL { ?unit hvdc:belongsTo ?shipment }
  OPTIONAL { ?unit hvdc:hasWarehouseHandlingProfile ?whp }
  OPTIONAL { ?unit hvdc:hasSiteReceipt ?site }
  OPTIONAL { ?unit hvdc:hasCostItem ?cost }
}
```

#### Template 3: Container No. → 추적 체인

```sparql
PREFIX hvdc: <http://samsung.com/project-logistics#>
SELECT ?container ?shipment ?bl ?portCall ?boe ?do ?wh
WHERE {
  ?container hvdc:containerNo ?containerNo .
  ?shipment hvdc:containsCargoUnit/hvdc:packedIn ?container ;
            hvdc:evidencedBy ?bl ;
            hvdc:hasPortCall ?portCall .
  OPTIONAL { ?shipment hvdc:hasCustomsEntry ?boe }
  OPTIONAL { ?shipment hvdc:hasReleaseOrder ?do }
  OPTIONAL { ?shipment hvdc:hasUnit/hvdc:hasWarehouseTask ?wh }
}
```

#### Template 4: BOE No. → 비용 추적

```sparql
PREFIX hvdc: <http://samsung.com/project-logistics#>
SELECT ?entry ?shipment ?duty ?invoice ?gateOut
WHERE {
  ?entry hvdc:boeRef ?boeNo ;
         hvdc:duty ?duty ;
         hvdc:customsStatus ?status .
  ?shipment hvdc:hasCustomsEntry ?entry ;
            hvdc:hasReleaseOrder ?release .
  OPTIONAL { ?shipment hvdc:hasInvoice ?invoice }
  OPTIONAL { ?shipment hvdc:hasMilestone ?m .
             ?m hvdc:milestoneCode "M100" ; hvdc:actualDt ?gateOut }
}
```

---

## Part 6: Validation Rules {#part-6}

### 6.1 SHACL Shape 1 — ShipmentUnit 필수 속성

```turtle
@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix hvdc: <http://samsung.com/project-logistics#> .

hvdc:ShipmentUnitShape a sh:NodeShape ;
  sh:targetClass hvdc:ShipmentUnit ;
  sh:property [
    sh:path hvdc:hasKey ; sh:minCount 1 ;
    sh:message "ShipmentUnit must have at least one IdentityKey"
  ] ;
  sh:property [
    sh:path hvdc:hasRoutingPattern ; sh:minCount 1 ;
    sh:message "ShipmentUnit must have a RoutingPattern"
  ] ;
  sh:property [
    sh:path hvdc:hasCurrentStage ; sh:minCount 1 ;
    sh:message "ShipmentUnit must have a current Journey Stage"
  ] .
```

### 6.2 SHACL Shape 2 — VIOLATION-1: Flow Code WHP 경계

```turtle
hvdc:FlowCodeBoundaryShape a sh:NodeShape ;
  sh:targetSubjectsOf hvdc:confirmedFlowCode ;
  sh:sparql [
    sh:message "VIOLATION-1: confirmedFlowCode found outside WarehouseHandlingProfile — immediate block" ;
    sh:select """
      PREFIX hvdc: <http://samsung.com/project-logistics#>
      SELECT $this WHERE {
        $this hvdc:confirmedFlowCode ?fc .
        FILTER NOT EXISTS { $this a hvdc:WarehouseHandlingProfile }
      }"""
  ] .
```

### 6.3 SHACL Shape 3 — VIOLATION-2: AGI/DAS MOSB Milestone 필수

```turtle
hvdc:AGIDASStagingShape a sh:NodeShape ;
  sh:targetClass hvdc:ShipmentUnit ;
  sh:sparql [
    sh:message "VIOLATION-2: AGI/DAS shipment missing MOSB staging milestone M115 — immediate block" ;
    sh:select """
      PREFIX hvdc: <http://samsung.com/project-logistics#>
      SELECT $this WHERE {
        $this hvdc:declaredDestination ?dest .
        FILTER(?dest IN ("AGI","DAS"))
        $this hvdc:hasRoutingPattern ?rp .
        FILTER(?rp IN (hvdc:MOSB_DIRECT, hvdc:WH_MOSB, hvdc:MIXED))
        $this hvdc:hasMilestone ?m130 .
        ?m130 hvdc:milestoneCode "M130" ; hvdc:actualDt ?arrived .
        FILTER NOT EXISTS {
          $this hvdc:hasMilestone ?m .
          ?m hvdc:milestoneCode "M115" ; hvdc:actualDt ?staged .
        }
      }"""
  ] .
```

### 6.4 Standards Alignment

| 표준 | 역할 | 적용 위치 |
|---|---|---|
| GS1 EPCIS/CBV | 이벤트 가시성 모델 (what/where/when/why) | Part 5 Event Node |
| DCSA T&T | 컨테이너 운영 Milestone 표준화 | Part 1 M10~M160 |
| UNECE BSP-RDM | 시맨틱 참조 데이터 | Part 3 Master Data |
| WCO DM | 통관 데이터 모델 | Part 4 CustomsEntry |
| PROV-O | 증거·출처 추적 | Part 5 Evidence Node |
| OWL-Time | ETA/ETD/ATA/ATD 시간 모델 | Part 4 MilestoneEvent |
| SKOS | RoutingPattern, Journey Stage 통제어 | Part 1 Dictionaries |
| DQV | 데이터 품질 메타데이터 | Part 2 Identifier |

### 6.5 Implementation Guide

| 단계 | 핵심 작업 | KPI |
|---|---|---|
| **Prepare** | CONSOLIDATED-00 완성, 01~09 Extension 패치, 06 재작성 | Flow Code 비WH 사용 0건 |
| **Pilot** | Onshore 1건 + Offshore(AGI/DAS) 1건 + Invoice 1건 KG 검증 | Key resolution ≥95%, Milestone ≥90% |
| **Operate** | SHACL 자동 검증, SPARQL query layer 운영 | VIOLATION-1/2 자동 감지 100% |
| **Scale** | DCSA/IATA ONE Record alignment, GLN/SSCC 확장 | Full-chain visibility ≥95% |

### 6.6 Assumptions & Risks

| # | 가정/위험 | 영향 | 처리 방향 |
|---|---|---|---|
| 1 | Package/PO upstream chain 미형성 | Part 3 불완전 | 후속 Task에서 보완 |
| 2 | CustomsEntry ≠ BOE 문서 분리 | 03, 07 파일 혼용 잔존 | Extension 패치 시 주의 |
| 3 | NCR/Claim lifecycle 미정의 | Exception 상세 부재 | Part 6 후속 패치 |
| 4 | MarineEvent/InspectionEvent 상세 미정의 | Part 5 Event 노드 불완전 | 04/06 Extension에서 보완 |
