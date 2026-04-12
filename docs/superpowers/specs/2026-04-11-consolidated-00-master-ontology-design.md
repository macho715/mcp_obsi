---
title: "HVDC Logistics Knowledge Graph — Master Ontology Design Spec"
type: "design-spec"
version: "1.0"
date: "2026-04-11"
author: "brainstorming session"
status: "approved"
source_refs:
  - "Logi ontol core doc/ROLE_PATCH.MD"
  - "Logi ontol core doc/ROLE_PATCH2.MD"
  - "Logi ontol core doc/CONSOLIDATED-01~09"
decisions:
  - "Approach 2: Full Spine selected"
  - "Option 1: Spine + Extension structure"
  - "CONSOLIDATED-00 = new master spine"
  - "CONSOLIDATED-06 = rewrite (C work)"
  - "CONSOLIDATED-08 = moved to Evidence Layer"
---

# HVDC Logistics KG — CONSOLIDATED-00 Master Ontology Design

## Purpose

Design specification for `CONSOLIDATED-00-master-ontology.md`, the canonical backbone
of the HVDC Logistics Knowledge Graph. Defines RoutingPattern, Milestone, Identifier,
Core Master Data, KG Node/Edge, SPARQL templates, and Validation rules that all
domain Extension documents (CONSOLIDATED-01~09) reference.

---

## Section 1: Overall Architecture & Document Structure

### CONSOLIDATED-00 Part Structure

```
CONSOLIDATED-00-master-ontology.md
│
├── Part 1: Governance & Dictionaries
│   ├── Master Governance Rule
│   ├── Data Classification Table (7종)
│   ├── RoutingPattern Dictionary
│   ├── Milestone Dictionary (M10~M160)
│   └── Terminology Normalization Table
│
├── Part 2: Identity & Key Policy
│   ├── Identifier Object Model
│   ├── Parent-Child Hierarchy
│   └── Matching / Resolution Rules
│
├── Part 3: Core Master Data Model
│   ├── Master Nodes (with required attributes)
│   ├── Location Nodes
│   └── Resource Nodes
│
├── Part 4: Execution Transaction Model
│   ├── E2E Process (Step 1~19 + Milestone link)
│   ├── Shipment, ShipmentLeg, PortCall
│   ├── CustomsEntry, ReleaseOrder, Delivery
│   └── WarehouseTask, SiteReceipt
│
├── Part 5: KG Node/Edge Design
│   ├── Node Family 설계 (8개 패밀리)
│   ├── Edge Grammar
│   └── SPARQL Query Templates (ETA / HVDC_CODE / Container / BOE)
│
└── Part 6: Validation Rules
    ├── Standards Alignment (GS1/DCSA/PROV-O/SKOS/DQV)
    ├── Violation Gates (VIOLATION-1, VIOLATION-2)
    ├── SHACL 패키지 (3개 Shape)
    └── Implementation Guide (Prepare/Pilot/Operate/Scale)
```

### CONSOLIDATED-01~09 관계 매핑

| 파일 | 역할 변경 | 00과의 연결 |
|---|---|---|
| 01-core-framework | Extension (인프라 노드 상세) | Part 3 Location Nodes 참조 |
| 02-warehouse-flow | Extension (WH 내부 운영) | Part 4 WarehouseTask 참조 |
| 03-document-ocr | Extension (문서/OCR 파이프라인) | Part 1 Identifier Policy 참조 |
| 04-barge-bulk | Extension (Marine/Offshore) | Part 1 RoutingPattern 참조 |
| 05-invoice-cost | Extension (비용 구조) | Part 4 InvoiceLine 참조 |
| 06-material-handling | **C 작업으로 재작성** | Part 3+4+5 전체 참조 |
| 07-port-operations | Extension (Port 도메인) | Part 4 PortCall 참조 |
| 08-communication | **Core에서 분리 → Evidence Layer** | Part 6 Evidence 참조 |
| 09-operations | Extension (운영/KPI) | Part 5 SPARQL Templates 참조 |

### CONSOLIDATED-06 재작성 계획 (C 작업)

```
CONSOLIDATED-06-material-handling.md (재작성)
│
├── Section 1: Material Handling Overview
│   └── RoutingPattern by Material Type (Flow Code 0-5 → RoutingPattern 전환)
│
├── Section 2: Customs & Port Stage (M40~M100)
│   └── MilestoneStatus 연결
│
├── Section 3: Warehouse Operations (M110~M121)
│   └── WarehouseHandlingProfile 참조 (02 Extension)
│
├── Section 4: Offshore / Marine / Heavy-lift (M115~M117)
│   └── MarineRoutingPattern 참조 (04 Extension)
│
└── Section 5: Site Receiving & Inspection (M130~M140)
    └── MRR/MRI/OSDR/POD/GRN
```

---

## Section 2: Identity Model + RoutingPattern

### 2.1 Identifier Object Model

**Core principle**: One internal object, many external identifiers.

```turtle
hvdc:Identifier a owl:Class ;
    rdfs:label "Logistics Identifier" ;
    rdfs:comment "외부 식별자 단일 모델. ShipmentUnit/CargoUnit/Document 공유" .

hvdc:identifierScheme   rdfs:range xsd:string .   # "BL"|"BOE"|"HVDC_CODE"|...
hvdc:identifierValue    rdfs:range xsd:string .
hvdc:normalizedValue    rdfs:range xsd:string .
hvdc:sourceSystem       rdfs:range xsd:string .   # "OFCO"|"SAFEEN"|"ADP"|"ERP"
hvdc:isPrimary          rdfs:range xsd:boolean .
hvdc:validFrom          rdfs:range xsd:dateTime .
hvdc:validTo            rdfs:range xsd:dateTime .
```

**식별자 패밀리 (9개)**:

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

> **규칙**: HVDC_CODE는 유일 식별자 아님 — IdentityKey로 MaterialMaster/CargoUnit/Delivery/Site demand 교차 연결 태그.

### 2.2 Parent-Child Hierarchy

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

### 2.3 Key Resolution Flow

```
[임의 키 입력]
        │
        ▼
IdentityKey.normalize()
        │
        ▼
resolvesTo → ShipmentUnit / CargoUnit / Document / Container
        │
        ▼
ShipmentUnit
  ├─ hasKey[] → IdentityKey (HVDC_CODE, BL, BOE, DO, containerNo...)
  ├─ hasCurrentStage → MilestoneEvent
  ├─ hasRoutingPattern → RoutingPattern
  ├─ hasWarehouseHandlingProfile → WarehouseHandlingProfile  ← Flow Code 유일 소유
  ├─ hasJourneyLeg[] → JourneyLeg
  ├─ hasDocument[] → Document
  ├─ hasCostItem[] → CostItem
  └─ hasException[] → Exception
```

### 2.4 RoutingPattern Dictionary

**Tier 1: ShipmentRoutingPattern (전체 여정)**

| Pattern | 구 Flow Code | 경로 | 설명 |
|---|---|---|---|
| `DIRECT` | Flow 1 | Port → Site | 직송 (창고 없음) |
| `WH_ONLY` | Flow 2 | Port → WH → Site | 창고 경유, MOSB 없음 |
| `MOSB_DIRECT` | Flow 3 | Port → MOSB → Site | MOSB 경유, 창고 없음 |
| `WH_MOSB` | Flow 4 | Port → WH → MOSB → Site | 창고 + MOSB |
| `MIXED` | Flow 5 | 복합/미확정 | 혼합 또는 미완료 |
| `PRE_ARRIVAL` | Flow 0 | — | 도착 전, 패턴 미확정 |

**Tier 2: MarineRoutingPattern (해상/오프쇼어)**

| Pattern | 설명 | 사용 도메인 |
|---|---|---|
| `DIRECT_MOSB` | Port → MOSB 직항 | 04-barge Extension |
| `WH_THEN_MOSB` | WH 경유 후 MOSB | 04-barge Extension |
| `LCT_DIRECT` | LCT 직접 하역 | 04-barge Extension |
| `OFFSHORE_PENDING` | 해상 경로 미확정 | Exception 처리 |

**Tier 3: ImportRoutingDecision (Port 도메인 전용)**

| Property | 설명 |
|---|---|
| `plannedRoutingPattern` | 통관 시 선언한 계획 경로 |
| `declaredDestination` | 신고 목적지 (AGI/DAS/MIR/SHU) |
| `offshoreTransitRequired` | MOSB 필요 여부 (boolean) |
| `importRoutingDecision` | 통관 처리 방식 결정 |

**도메인별 사용 규칙**:

| 도메인 | 허용 | 금지 |
|---|---|---|
| Shipment (core) | ShipmentRoutingPattern | — |
| Port (07) | plannedRoutingPattern, declaredDestination | assignedFlowCode |
| Document/OCR (03) | routeEvidence, destinationEvidence | extractedFlowCode |
| Cost (05) | costByRoutingPattern, routeBasedCostDriver | costByFlowCode |
| Marine/Bulk (04) | MarineRoutingPattern, offshoreDeliveryPattern | Flow Code 3/4/5 |
| Warehouse (02) | WarehouseHandlingProfile.confirmedFlowCode | 다른 도메인 적용 금지 |
| Material Handling (06) | ShipmentRoutingPattern + MilestoneStatus | Flow Code 전체 체인 |

---

## Section 3: Milestone Dictionary + E2E Process

### 3.1 Journey Stage vs Milestone 역할 분리

| 시스템 | 역할 | 타입 |
|---|---|---|
| Journey Stage (15단계) | ShipmentUnit.currentStage = 현재 상태 버킷 | 상태값 (enum) |
| Milestone (M10~M160) | 이벤트 발생 시점 기록 | 이벤트 (planned/estimated/actual) |

관계: Milestone 발생 → Journey Stage 전환 트리거
- M110 (WH Received) → currentStage = `WH_RECEIPT`
- M121 (Dispatched) → currentStage = `WH_DISPATCH`

### 3.2 MilestoneEvent 클래스

```turtle
hvdc:MilestoneEvent a owl:Class .
hvdc:milestoneCode      rdfs:range xsd:string .    # "M110", "M61"
hvdc:milestoneName      rdfs:range xsd:string .
hvdc:objectType         rdfs:range xsd:string .
hvdc:objectId           rdfs:range xsd:string .
hvdc:plannedDt          rdfs:range xsd:dateTime .
hvdc:estimatedDt        rdfs:range xsd:dateTime .
hvdc:actualDt           rdfs:range xsd:dateTime .
hvdc:location           rdfs:range hvdc:Node .
hvdc:responsibleParty   rdfs:range hvdc:Organization .
hvdc:sourceDocument     rdfs:range hvdc:Document .
hvdc:statusAfterEvent   rdfs:range xsd:string .    # Journey Stage 값
hvdc:exceptionFlag      rdfs:range xsd:boolean .
```

### 3.3 Milestone Dictionary M10~M160 (완전판)

| Milestone | 이름 | E2E Step | Journey Stage | 책임 |
|---|---|---|---|---|
| M10 | Cargo Ready | Step 2 | PLANNING | Vendor |
| M20 | Packed / Marked | Step 3 | ORIGIN_DISPATCH | Vendor |
| M30 | Pickup Completed | Step 4 | ORIGIN_DISPATCH | Forwarder |
| M40 | Export Cleared | Step 5 | ORIGIN_DISPATCH | Export Broker |
| M50 | Terminal Received | Step 6 | PORT_ENTRY | Terminal |
| M60 | Loaded On Board | Step 7 | PORT_ENTRY | Carrier |
| M61 | ATD | Step 7 | TERMINAL_HANDLING | Carrier |
| M70 | Transshipment Occurred | Step 8 | TERMINAL_HANDLING | Carrier |
| M80 | ATA | Step 9 | PORT_ENTRY | Carrier/Agent |
| M90 | BOE Submitted | Step 10 | CUSTOMS_CLEARANCE | Import Broker |
| M91 | BOE Cleared | Step 10 | CUSTOMS_CLEARANCE | Import Broker |
| M92 | DO Released | Step 11 | CUSTOMS_CLEARANCE | Carrier/Agent |
| M100 | Gate-out Completed | Step 11 | INLAND_HAULAGE | Terminal/Forwarder |
| **M110** | **Warehouse Received (WH In)** ★ | Step 13 | **WH_RECEIPT** | WH Operator |
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

★ M110 = WarehouseHandlingProfile 생성 트리거. M110 이전 flowConfirmationStatus = tentative.

### 3.4 E2E 19단계 → Milestone 매핑

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
| 13 | WH Receiving ★ | **M110** | WH_RECEIPT |
| 14 | Put-away / Storage | M111 | WH_STORAGE |
| 15 | Picking / Dispatch | M120, M121 | WH_DISPATCH |
| 16 | Offshore/Heavy-lift | M115, M116, M117 | MOSB_STAGING / OFFSHORE_TRANSIT |
| 17 | Site Delivery/Insp. | M130, M131/M132 | SITE_RECEIVING |
| 18 | POD / GRN | M140 | MATERIAL_ISSUE |
| 19 | Exception / Cost | M150, M160 | CLOSEOUT |

### 3.5 AGI/DAS + Milestone 룰

```
IF declaredDestination IN (AGI, DAS)
   AND routingPattern IN (MOSB_DIRECT, WH_MOSB, MIXED)
   AND M130.actualDt IS NOT NULL
   AND M115.actualDt IS NULL
→ VIOLATION-2
```

---

## Section 4: Core Master Data + KG Node/Edge + Validation

### 4.1 Core Master Data — 필수 속성 거버넌스

**Master Nodes**

| 클래스 | 필수 속성 | 옵션 |
|---|---|---|
| Project | projectCode, projectName, status | country, startDate |
| Package | packageNo, packageType, siteCode | scope, requiredDate |
| PurchaseOrder | poNo, vendorCode, incoterm, currency | issueDate |
| Vendor | vendorCode, vendorName, role | country |
| MaterialMaster | materialCode, description, uom | hsCode, origin |
| HVDCCodeTag | hvdcCode | engineeringArea, siteRelevance |

**Location Nodes**

| 클래스 | 필수 속성 | 비고 |
|---|---|---|
| Port | portCode, UNLOCODE, portName | UN/LOCODE 표준 |
| Terminal | terminalId, terminalName, portId | berth 포함 |
| Warehouse | warehouseId, name, type, operator | Indoor/Outdoor/DangerousCargo |
| WarehouseLocation | locationCode, zone | rack/bin/yard |
| Site | siteCode, siteName, onshoreOffshore | AGI/DAS/MIR/SHU |
| MOSB | **type: OffshoreStaging** | Warehouse 분류 금지 |

**Transaction Node Attribute Governance**

```turtle
# Shipment
shipmentId, mode, status, plannedRoutingPattern,
origin, destination, grossWeight, volume, ETD, ETA, ATD, ATA

# CargoUnit
cargoUnitId, packageNo, grossWeight, volume, dimensions, condition

# CustomsEntry (BOE 문서와 분리)
customsEntryId, boeRef, customsStatus, duty,
broker, clearanceDate, consigneeCode, hsCode

# ReleaseOrder (DO 문서와 분리)
releaseOrderId, doRef, releaseDate, terminal, freeTime, gatePassRef

# WarehouseTask
taskId, warehouseId, location, stockStatus,
storageRequirementClass, preservationStatus, availableQty

# SiteReceipt
receiptId, siteCode, receiptType,  # Good | OSD
inspectionResult, mrrRef, osdrRef, mrsRef, misRef
```

### 4.2 KG Node Family (8개)

| 패밀리 | 주요 클래스 | Primary Key |
|---|---|---|
| Master | Project, Package, PO, Vendor, MaterialMaster | 내부 URI |
| Transport | Shipment, ShipmentLeg, PortCall, CustomsEntry, ReleaseOrder, Delivery | shipmentId, blNo |
| Physical | CargoUnit, Container, EquipmentResource | packageNo, containerNo |
| Document | BL, BOE, DO, Permit, Invoice, CI, PL, MRR, OSDR, POD | documentNo |
| Event | MilestoneEvent, InspectionEvent, WarehouseEvent, MarineEvent | eventId |
| Exception | Delay, Damage, Shortage, NCR, Claim | exceptionId |
| Cost | InvoiceLine, CostTransaction, TariffRef, DEMDETClock | invoiceNo, costCode |
| Evidence | AuditRecord, CommunicationEvent, ApprovalAction | emailId, threadId |

### 4.3 Edge Grammar

```turtle
# Containment
hasPackage, coveredBy, containsCargoUnit, packedIn, hasUnit

# Movement
hasLeg, departsFrom, arrivesAt, deliveredTo, storedAt

# Evidence
evidencedBy, references, attachedTo, provenanceOf

# Status/Event
hasMilestone, hasInspection, hasException, triggeredBy

# Responsibility
issuedTo, operatedBy, approvedBy, handledBy, assignedTo

# Compliance
requiresPermit, classifiedByHS, conformsTo, governedBy

# Finance
chargesFor, mappedToCostCode, linkedToInvoice, accruesTo
```

### 4.4 SPARQL Query Templates

**Template 1: ETA → 전체 컨텍스트**
```sparql
SELECT ?unit ?stage ?location ?milestone ?boe ?do ?risk
WHERE {
  ?leg hvdc:estimatedATA ?eta .
  FILTER(?eta > NOW() && ?eta < NOW() + "P7D"^^xsd:duration)
  ?shipment hvdc:hasLeg ?leg ; hvdc:hasUnit ?unit .
  ?unit hvdc:hasCurrentStage ?stage ;
        hvdc:hasCurrentLocation ?location .
  OPTIONAL { ?unit hvdc:hasMilestone ?milestone }
  OPTIONAL { ?unit hvdc:hasCustomsEntry/hvdc:boeRef ?boe }
  OPTIONAL { ?unit hvdc:hasReleaseOrder/hvdc:doRef ?do }
  OPTIONAL { ?unit hvdc:hasException ?risk }
}
ORDER BY ?eta
```

**Template 2: HVDC_CODE → 전체 이력**
```sparql
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

**Template 3: Container No. → 추적 체인**
```sparql
SELECT ?container ?shipment ?bl ?portCall ?boe ?do ?gateOut ?wh
WHERE {
  ?container hvdc:containerNo ?containerNo .
  ?shipment hvdc:containsCargoUnit/hvdc:packedIn ?container ;
            hvdc:evidencedBy ?bl ;
            hvdc:hasPortCall ?portCall .
  OPTIONAL { ?shipment hvdc:hasCustomsEntry ?boe }
  OPTIONAL { ?shipment hvdc:hasReleaseOrder ?do }
  OPTIONAL { ?shipment hvdc:hasMilestone ?m .
             ?m hvdc:milestoneCode "M100" }
  OPTIONAL { ?shipment hvdc:hasUnit/hvdc:hasWarehouseTask ?wh }
}
```

**Template 4: BOE No. → 비용 추적**
```sparql
SELECT ?boe ?shipment ?duty ?invoice ?gateOut
WHERE {
  ?entry hvdc:boeRef ?boeNo ;
         hvdc:duty ?duty ;
         hvdc:customsStatus ?status .
  ?shipment hvdc:hasCustomsEntry ?entry ;
            hvdc:hasReleaseOrder ?release .
  ?release hvdc:doRef ?do .
  OPTIONAL { ?shipment hvdc:hasInvoice ?invoice }
  OPTIONAL { ?shipment hvdc:hasMilestone ?m .
             ?m hvdc:milestoneCode "M100" ; hvdc:actualDt ?gateOut }
}
```

### 4.5 Validation Rules

**SHACL Shape 1: ShipmentUnit 필수 속성**
```turtle
hvdc:ShipmentUnitShape a sh:NodeShape ;
  sh:targetClass hvdc:ShipmentUnit ;
  sh:property [ sh:path hvdc:hasKey ; sh:minCount 1 ] ;
  sh:property [ sh:path hvdc:hasRoutingPattern ; sh:minCount 1 ] ;
  sh:property [ sh:path hvdc:hasCurrentStage ; sh:minCount 1 ] .
```

**SHACL Shape 2: VIOLATION-1 — Flow Code WHP 경계**
```turtle
hvdc:FlowCodeBoundaryShape a sh:NodeShape ;
  sh:targetClass hvdc:ShipmentUnit ;
  sh:sparql [
    sh:message "VIOLATION-1: confirmedFlowCode must reside only in WarehouseHandlingProfile" ;
    sh:select """
      SELECT $this WHERE {
        $this hvdc:confirmedFlowCode ?fc .
        FILTER NOT EXISTS { $this a hvdc:WarehouseHandlingProfile }
      }"""
  ] .
```

**SHACL Shape 3: VIOLATION-2 — AGI/DAS MOSB Milestone 필수**
```turtle
hvdc:AGIDASStagingShape a sh:NodeShape ;
  sh:targetClass hvdc:ShipmentUnit ;
  sh:sparql [
    sh:message "VIOLATION-2: AGI/DAS shipment must have MOSB staging milestone (M115)" ;
    sh:select """
      SELECT $this WHERE {
        $this hvdc:declaredDestination ?dest .
        FILTER(?dest IN ("AGI","DAS"))
        $this hvdc:hasRoutingPattern ?rp .
        FILTER(?rp IN (hvdc:MOSB_DIRECT, hvdc:WH_MOSB, hvdc:MIXED))
        FILTER NOT EXISTS {
          $this hvdc:hasMilestone ?m .
          ?m hvdc:milestoneCode "M115" ; hvdc:actualDt ?dt .
        }
      }"""
  ] .
```

**Standards Alignment**

| 표준 | 적용 위치 | 구현 방식 |
|---|---|---|
| GS1 EPCIS/CBV | Event 노드 | what/where/when/why 이벤트 구조 |
| DCSA T&T | M10~M160 Milestone | 운영 이벤트 코드 정렬 |
| UNECE BSP-RDM | Core Master Data | 시맨틱 참조 데이터 |
| WCO DM | CustomsEntry | BOE/HS Code 필드 |
| PROV-O | Evidence 노드 | AuditRecord.provenanceOf |
| OWL-Time | MilestoneEvent | plannedDt/estimatedDt/actualDt |
| SKOS | RoutingPattern, Journey Stage | controlled vocabulary |
| DQV | IdentityKey, Document | confidence, completeness |

**Implementation Guide**

| 단계 | 핵심 작업 | KPI |
|---|---|---|
| Prepare | 00 신규 작성, 06 재작성, 01~09 Extension 연결 | Flow Code 비WH 사용 0건 |
| Pilot | Onshore 1건 + Offshore 1건 + Invoice 1건 KG 검증 | Key resolution ≥95%, Milestone ≥90% |
| Operate | SHACL 자동 검증, SPARQL query layer 운영 | VIOLATION-1/2 자동 감지 100% |
| Scale | DCSA/IATA ONE Record alignment, GLN/SSCC 확장 | Full-chain visibility ≥95% |

---

## Data Classification Table (Part 1)

| Data Class | Examples |
|---|---|
| Master Data | Project, Package, PO, Vendor, MaterialMaster, Port, Terminal, Warehouse, Site, EquipmentResource |
| Transaction Data | Shipment, ShipmentLeg, PortCall, CustomsEntry, ReleaseOrder, Delivery, WarehouseTask, SiteReceipt |
| Document Data | CI, PL, BL, BOE, DO, Permit, MRR, MRI, ITP, MAR, MRS, MIS, POD, GRN, OSDR |
| Event Data | MilestoneEvent, InspectionEvent, WarehouseEvent, MarineEvent |
| Exception Data | Delay, Damage, Shortage, NCR, Claim |
| Cost Data | Invoice, InvoiceLine, Duty, DEM/DET, PortCharge, WarehouseCharge, MarineCharge |
| Evidence Data | AuditRecord, CommunicationEvent, ApprovalAction |

---

## Terminology Normalization Table (Part 1)

| 기존 용어 | 표준 용어 | 이유 | 위험 |
|---|---|---|---|
| Flow Code (Port→WH→MOSB→Site) | ShipmentRoutingPattern | 경로는 warehouse 내부 아님 | Semantic collision |
| Flow Code 0 "Pre Arrival" | PRE_ARRIVAL | 선적 Milestone, 창고 아님 | Wrong state machine |
| Flow Code 1 "Port→Site" | DIRECT | 경로 설명자 | Broken warehouse semantics |
| Flow Code 2 "Port→WH→Site" | WH_ONLY | 경로 설명자 | Confuses route vs WH task |
| Flow Code 3 "Port→MOSB→Site" | MOSB_DIRECT | Marine/offshore 경로 | Misclassifies MOSB |
| Flow Code 4 "Port→WH→MOSB→Site" | WH_MOSB | 복합 경로 | Mixed semantics |
| Flow Code 5 "Mixed" | MIXED | Exception 상태 | Unclear closure |
| MOSB as Warehouse | MOSB as OffshoreStaging | MOSB는 창고 아님 | Location ambiguity |
| Material Storage Code | StorageRequirementClass | 보관 조건, process 아님 | Wrong data typing |
| Site Offloading | Site Unloading | 표준 물류 용어 | Inconsistency |
| MRR/MRI/OSDR | 표준 약어 유지 | 이미 표준 | — |
| assignedFlowCode (Port) | plannedRoutingPattern | Port는 WHP 소유 금지 | Ontology boundary violation |
| extractedFlowCode (OCR) | routeEvidence | 문서는 증거만 | Wrong ownership |
| costByFlowCode | costByRoutingPattern | 비용은 경로 기반 | Wrong driver |

---

## 미결 가정 및 위험 (Assumptions & Risks)

1. **Package/PO upstream chain** — 현재 CONSOLIDATED에 미형성. 신규 작성 필요.
2. **BOE/DO 트랜잭션-문서 분리** — CustomsEntry ≠ BOE문서, ReleaseOrder ≠ DO문서. 명확한 분리 필요.
3. **NCR/Claim 생명주기** — 현재 canonical 정의 없음. Exception 클래스 상세 설계 필요.
4. **Terminal/Carrier/Forwarder 역할 타입** — 내러티브 존재, 타입 정의 미완성.
5. **CONSOLIDATED-06 재작성 범위** — 3495줄. 기존 내용 보존 vs 신규 구조 균형 필요.
