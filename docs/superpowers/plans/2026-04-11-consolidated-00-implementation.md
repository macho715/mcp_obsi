# HVDC Master Ontology Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `CONSOLIDATED-00-master-ontology.md`를 신규 작성하여 HVDC Logistics KG의 단일 Spine을 확립하고, `CONSOLIDATED-06`을 RoutingPattern + Milestone 기반으로 재작성하며, `CONSOLIDATED-01~09`에 Extension 참조를 추가한다.

**Architecture:** CONSOLIDATED-00 = Governance + Identity + Master Data + E2E Process + KG + Validation의 6-Part Spine. 기존 CONSOLIDATED-01~09는 Extension으로 00을 참조. CONSOLIDATED-06은 3495줄을 5개 Section으로 재구성하여 Flow Code 0~5 → RoutingPattern + MilestoneStatus 전환.

**Tech Stack:** Markdown, Turtle (RDF/OWL), SPARQL, SHACL, JSON-LD. 검증: PowerShell Select-String, 수동 일관성 검사.

**Spec:** `docs/superpowers/specs/2026-04-11-consolidated-00-master-ontology-design.md`

---

## 실행 순서

```
Plan A: CONSOLIDATED-00 신규 작성 (Task 1~6)
    ↓
Plan B: CONSOLIDATED-01~09 Extension 패치 (Task 7~8)
    ↓
Plan C: CONSOLIDATED-06 재작성 (Task 9~13)
```

---

## Plan A: CONSOLIDATED-00 신규 작성

**출력 파일:** `Logi ontol core doc/CONSOLIDATED-00-master-ontology.md`

---

### Task 1: 파일 스캐폴드 + YAML Frontmatter + Part 1 Governance

**Files:**
- Create: `Logi ontol core doc/CONSOLIDATED-00-master-ontology.md`

- [ ] **Step 1: 파일 생성 — YAML Frontmatter 작성**

```yaml
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
```

- [ ] **Step 2: Master Governance Rule 블록 작성**

다음 4개 룰을 문서 최상단 (YAML 다음)에 삽입:

```markdown
> **MASTER GOVERNANCE RULE**
> 1. **Flow Code is a warehouse-handling classification only.**
>    Restricted to `WarehouseHandlingProfile`. No other domain may own or assign Flow Code.
> 2. **Program-wide shipment visibility shall use Journey Stage, RoutingPattern, Milestone, and Leg.**
>    (`routingPattern`, `currentStage`, `leg_sequence`, `JourneyLeg`)
> 3. **Port, Customs, Document, Cost, Marine, and Communication domains**
>    may reference warehouse-flow *evidence*, but shall NOT own or assign Flow Code.
> 4. **MOSB is an Offshore Staging / Marine Interface Node**, not a Warehouse.
```

- [ ] **Step 3: Data Classification Table (7종) 작성**

```markdown
## Part 1: Governance & Dictionaries

### 1.1 Data Classification

| Data Class | Examples |
|---|---|
| Master Data | Project, Package, PO, Vendor, MaterialMaster, Port, Terminal, Warehouse, Site |
| Transaction Data | Shipment, ShipmentLeg, PortCall, CustomsEntry, ReleaseOrder, Delivery, WarehouseTask, SiteReceipt |
| Document Data | CI, PL, BL, BOE, DO, Permit, MRR, MRI, ITP, MAR, MRS, MIS, POD, GRN, OSDR |
| Event Data | MilestoneEvent, InspectionEvent, WarehouseEvent, MarineEvent |
| Exception Data | Delay, Damage, Shortage, NCR, Claim |
| Cost Data | Invoice, InvoiceLine, Duty, DEM/DET, PortCharge, WarehouseCharge, MarineCharge |
| Evidence Data | AuditRecord, CommunicationEvent, ApprovalAction |
```

- [ ] **Step 4: RoutingPattern Dictionary 작성 (3 Tier)**

Spec Section 2.4의 Tier 1/2/3 표 그대로 작성.
Tier 1 = ShipmentRoutingPattern (6개 값: DIRECT/WH_ONLY/MOSB_DIRECT/WH_MOSB/MIXED/PRE_ARRIVAL).
Tier 2 = MarineRoutingPattern (4개).
Tier 3 = ImportRoutingDecision (Port 전용 properties 4개).

- [ ] **Step 5: Terminology Normalization Table 작성**

Spec 하단 "Terminology Normalization Table" 14행 그대로 삽입.

- [ ] **Step 6: 검증 — Part 1 완전성 확인**

```powershell
Select-String -Path "Logi ontol core doc\CONSOLIDATED-00-master-ontology.md" `
  -Pattern "MASTER GOVERNANCE RULE|Data Classification|RoutingPattern|Terminology Normalization" `
  | Select-Object LineNumber, Line
```

기대값: 4개 패턴 모두 매칭.

- [ ] **Step 7: Git commit**

```bash
git add "Logi ontol core doc/CONSOLIDATED-00-master-ontology.md"
git commit -m "docs: scaffold CONSOLIDATED-00 Part 1 — Governance and Dictionaries"
```

---

### Task 2: Part 1 계속 — Milestone Dictionary M10~M160

**Files:**
- Modify: `Logi ontol core doc/CONSOLIDATED-00-master-ontology.md`

- [ ] **Step 1: MilestoneEvent 클래스 Turtle 블록 작성**

```turtle
hvdc:MilestoneEvent a owl:Class ;
    rdfs:label "Logistics Milestone Event" .

hvdc:milestoneCode      a owl:DatatypeProperty ; rdfs:range xsd:string .
hvdc:milestoneName      a owl:DatatypeProperty ; rdfs:range xsd:string .
hvdc:objectType         a owl:DatatypeProperty ; rdfs:range xsd:string .
hvdc:objectId           a owl:DatatypeProperty ; rdfs:range xsd:string .
hvdc:plannedDt          a owl:DatatypeProperty ; rdfs:range xsd:dateTime .
hvdc:estimatedDt        a owl:DatatypeProperty ; rdfs:range xsd:dateTime .
hvdc:actualDt           a owl:DatatypeProperty ; rdfs:range xsd:dateTime .
hvdc:location           a owl:ObjectProperty  ; rdfs:range hvdc:Node .
hvdc:responsibleParty   a owl:ObjectProperty  ; rdfs:range hvdc:Organization .
hvdc:sourceDocument     a owl:ObjectProperty  ; rdfs:range hvdc:Document .
hvdc:statusAfterEvent   a owl:DatatypeProperty ; rdfs:range xsd:string .
hvdc:exceptionFlag      a owl:DatatypeProperty ; rdfs:range xsd:boolean .
```

- [ ] **Step 2: Milestone Dictionary 전체 표 작성 (M10~M160 + M115~M117)**

Spec Section 3.3의 24행 테이블 전체 삽입.
Journey Stage, E2E Step, 책임 도메인 컬럼 포함.
M110 행에 ★ 표시 및 "WarehouseHandlingProfile 생성 트리거" 노트 추가.

- [ ] **Step 3: Journey Stage ↔ Milestone 관계 규칙 작성**

```markdown
> **규칙**: `WarehouseHandlingProfile.confirmedFlowCode`는
> M110(WH_RECEIPT) 발생 후에만 설정 가능.
> M110 이전 `flowConfirmationStatus = "tentative"`.
```

- [ ] **Step 4: 검증 — Milestone 코드 완전성 확인**

```powershell
$doc = Get-Content "Logi ontol core doc\CONSOLIDATED-00-master-ontology.md" -Raw
$codes = @("M10","M20","M30","M40","M50","M60","M61","M70","M80","M90","M91","M92",
           "M100","M110","M111","M115","M116","M117","M120","M121","M130","M131",
           "M132","M140","M150","M160")
$missing = $codes | Where-Object { $doc -notmatch $_ }
if ($missing) { Write-Host "Missing: $missing" } else { Write-Host "All milestones present" }
```

기대값: "All milestones present"

- [ ] **Step 5: Git commit**

```bash
git add "Logi ontol core doc/CONSOLIDATED-00-master-ontology.md"
git commit -m "docs: add Milestone Dictionary M10~M160 to CONSOLIDATED-00 Part 1"
```

---

### Task 3: Part 2 — Identity & Key Policy

**Files:**
- Modify: `Logi ontol core doc/CONSOLIDATED-00-master-ontology.md`

- [ ] **Step 1: Identifier 클래스 Turtle 블록 작성**

```turtle
hvdc:Identifier a owl:Class ;
    rdfs:label "Logistics Identifier" ;
    rdfs:comment "외부 식별자 단일 모델. 모든 ShipmentUnit/CargoUnit/Document 공유" .

hvdc:identifierScheme  a owl:DatatypeProperty ; rdfs:range xsd:string .
hvdc:identifierValue   a owl:DatatypeProperty ; rdfs:range xsd:string .
hvdc:normalizedValue   a owl:DatatypeProperty ; rdfs:range xsd:string .
hvdc:sourceSystem      a owl:DatatypeProperty ; rdfs:range xsd:string .
hvdc:isPrimary         a owl:DatatypeProperty ; rdfs:range xsd:boolean .
hvdc:validFrom         a owl:DatatypeProperty ; rdfs:range xsd:dateTime .
hvdc:validTo           a owl:DatatypeProperty ; rdfs:range xsd:dateTime .

hvdc:resolvesTo a owl:ObjectProperty ;
    rdfs:domain hvdc:Identifier ;
    rdfs:comment "IdentityKey → ShipmentUnit/CargoUnit/Document/Container" .
```

- [ ] **Step 2: 식별자 패밀리 표 작성 (9개)**

Spec Section 2.1의 9-row 테이블 삽입.
HVDC_CODE 강조 표시 + "유일 식별자 아님" 규칙 노트 추가.

- [ ] **Step 3: Parent-Child Hierarchy 작성**

```markdown
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
```

- [ ] **Step 4: ShipmentUnit Key Resolution Flow 작성**

Spec Section 2.3의 ASCII 다이어그램 + ShipmentUnit 속성 목록 전체 삽입.
특히 `hasWarehouseHandlingProfile → WarehouseHandlingProfile ← Flow Code 유일 소유` 주석 포함.

- [ ] **Step 5: 검증 — Identity 규칙 확인**

```powershell
Select-String -Path "Logi ontol core doc\CONSOLIDATED-00-master-ontology.md" `
  -Pattern "hvdc:Identifier|resolvesTo|identifierScheme|Parent-Child|ShipmentUnit" `
  | Measure-Object | Select-Object Count
```

기대값: Count ≥ 10

- [ ] **Step 6: Git commit**

```bash
git add "Logi ontol core doc/CONSOLIDATED-00-master-ontology.md"
git commit -m "docs: add Part 2 Identity and Key Policy to CONSOLIDATED-00"
```

---

### Task 4: Part 3 + Part 4 — Core Master Data + Execution Transactions

**Files:**
- Modify: `Logi ontol core doc/CONSOLIDATED-00-master-ontology.md`

- [ ] **Step 1: Master Nodes 속성 거버넌스 테이블 작성 (6개 클래스)**

Spec Section 4.1의 Master Nodes 표 삽입:
Project, Package, PurchaseOrder, Vendor, MaterialMaster, HVDCCodeTag — 필수/옵션 속성 포함.

- [ ] **Step 2: Location Nodes 테이블 작성**

Spec Section 4.1의 Location Nodes 표 삽입.
MOSB 행에 `type: OffshoreStaging — Warehouse 분류 금지` 명시.

- [ ] **Step 3: Transaction Node Attribute Governance Turtle 블록 작성**

```turtle
# Shipment
hvdc:Shipment rdfs:comment "Required: shipmentId, mode, status, plannedRoutingPattern,
  origin, destination, grossWeight, volume, ETD, ETA, ATD, ATA" .

# CustomsEntry — BOE 문서와 분리
hvdc:CustomsEntry rdfs:comment "Required: customsEntryId, boeRef, customsStatus,
  duty, broker, clearanceDate, consigneeCode, hsCode" .

# ReleaseOrder — DO 문서와 분리
hvdc:ReleaseOrder rdfs:comment "Required: releaseOrderId, doRef, releaseDate,
  terminal, freeTime, gatePassRef" .

# WarehouseTask
hvdc:WarehouseTask rdfs:comment "Required: taskId, warehouseId, location, stockStatus,
  storageRequirementClass, preservationStatus, availableQty" .

# SiteReceipt
hvdc:SiteReceipt rdfs:comment "Required: receiptId, siteCode, receiptType,
  inspectionResult, mrrRef, osdrRef, mrsRef, misRef" .
```

- [ ] **Step 4: E2E 19단계 프로세스 테이블 작성**

Spec Section 3.4의 19-row E2E 테이블 삽입.
Step, 이름, Milestone, Journey Stage 4개 컬럼.
Step 13 (WH Receiving) ★ 강조 표시.

- [ ] **Step 5: 검증 — 19단계 + Transaction 클래스 존재 확인**

```powershell
$doc = Get-Content "Logi ontol core doc\CONSOLIDATED-00-master-ontology.md" -Raw
$checks = @("Step 13","WH Receiving","CustomsEntry","ReleaseOrder","SiteReceipt","WarehouseTask")
$missing = $checks | Where-Object { $doc -notmatch $_ }
if ($missing) { Write-Host "Missing: $($missing -join ', ')" } else { Write-Host "Part 3+4 OK" }
```

기대값: "Part 3+4 OK"

- [ ] **Step 6: Git commit**

```bash
git add "Logi ontol core doc/CONSOLIDATED-00-master-ontology.md"
git commit -m "docs: add Part 3 Core Master Data and Part 4 Execution Transactions to CONSOLIDATED-00"
```

---

### Task 5: Part 5 — KG Node/Edge + SPARQL Templates

**Files:**
- Modify: `Logi ontol core doc/CONSOLIDATED-00-master-ontology.md`

- [ ] **Step 1: KG Node Family 8개 테이블 작성**

Spec Section 4.2의 8-row 테이블 삽입.
Master / Transport / Physical / Document / Event / Exception / Cost / Evidence 패밀리.

- [ ] **Step 2: Edge Grammar 블록 작성**

```turtle
# Containment
hvdc:hasPackage, hvdc:coveredBy, hvdc:containsCargoUnit, hvdc:packedIn, hvdc:hasUnit

# Movement
hvdc:hasLeg, hvdc:departsFrom, hvdc:arrivesAt, hvdc:deliveredTo, hvdc:storedAt

# Evidence
hvdc:evidencedBy, hvdc:references, hvdc:attachedTo, hvdc:provenanceOf

# Status/Event
hvdc:hasMilestone, hvdc:hasInspection, hvdc:hasException, hvdc:triggeredBy

# Responsibility
hvdc:issuedTo, hvdc:operatedBy, hvdc:approvedBy, hvdc:handledBy, hvdc:assignedTo

# Compliance
hvdc:requiresPermit, hvdc:classifiedByHS, hvdc:conformsTo, hvdc:governedBy

# Finance
hvdc:chargesFor, hvdc:mappedToCostCode, hvdc:linkedToInvoice, hvdc:accruesTo
```

- [ ] **Step 3: SPARQL Template 1 작성 — ETA → 전체 컨텍스트**

Spec Section 4.4 Template 1 쿼리 그대로 삽입.
`FILTER(?eta > NOW() && ?eta < NOW() + "P7D"^^xsd:duration)` 포함.

- [ ] **Step 4: SPARQL Template 2 작성 — HVDC_CODE → 전체 이력**

Spec Section 4.4 Template 2 쿼리 그대로 삽입.
`hvdc:identifierScheme "HVDC_CODE"` + `hvdc:resolvesTo ?unit` 패턴 포함.

- [ ] **Step 5: SPARQL Template 3 작성 — Container No. → 추적 체인**

Spec Section 4.4 Template 3 쿼리 그대로 삽입.

- [ ] **Step 6: SPARQL Template 4 작성 — BOE No. → 비용 추적**

Spec Section 4.4 Template 4 쿼리 그대로 삽입.

- [ ] **Step 7: 검증 — SPARQL 4개 + Edge Grammar 존재 확인**

```powershell
Select-String -Path "Logi ontol core doc\CONSOLIDATED-00-master-ontology.md" `
  -Pattern "Template 1|Template 2|Template 3|Template 4|hvdc:chargesFor|hvdc:provenanceOf" `
  | Measure-Object | Select-Object Count
```

기대값: Count = 6

- [ ] **Step 8: Git commit**

```bash
git add "Logi ontol core doc/CONSOLIDATED-00-master-ontology.md"
git commit -m "docs: add Part 5 KG Node/Edge design and SPARQL query templates to CONSOLIDATED-00"
```

---

### Task 6: Part 6 — Validation Rules + VIOLATION Gates + Standards

**Files:**
- Modify: `Logi ontol core doc/CONSOLIDATED-00-master-ontology.md`

- [ ] **Step 1: SHACL Shape 1 작성 — ShipmentUnit 필수 속성**

```turtle
hvdc:ShipmentUnitShape a sh:NodeShape ;
  sh:targetClass hvdc:ShipmentUnit ;
  sh:property [ sh:path hvdc:hasKey ; sh:minCount 1 ;
                sh:message "ShipmentUnit must have at least one IdentityKey" ] ;
  sh:property [ sh:path hvdc:hasRoutingPattern ; sh:minCount 1 ;
                sh:message "ShipmentUnit must have a RoutingPattern" ] ;
  sh:property [ sh:path hvdc:hasCurrentStage ; sh:minCount 1 ;
                sh:message "ShipmentUnit must have a current Journey Stage" ] .
```

- [ ] **Step 2: SHACL Shape 2 작성 — VIOLATION-1 Flow Code 경계**

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

- [ ] **Step 3: SHACL Shape 3 작성 — VIOLATION-2 AGI/DAS MOSB Milestone**

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

- [ ] **Step 4: Standards Alignment 테이블 작성**

Spec Section 4.5의 8-row Standards 표 삽입 (GS1/DCSA/UNECE/WCO/PROV-O/OWL-Time/SKOS/DQV).

- [ ] **Step 5: Implementation Guide 테이블 작성 (Prepare/Pilot/Operate/Scale)**

Spec Section 4.5의 4-row Implementation Guide 표 삽입. KPI 컬럼 포함.

- [ ] **Step 6: 검증 — VIOLATION Gates + Standards 존재 확인**

```powershell
$doc = Get-Content "Logi ontol core doc\CONSOLIDATED-00-master-ontology.md" -Raw
$checks = @("VIOLATION-1","VIOLATION-2","FlowCodeBoundaryShape","AGIDASStagingShape",
            "GS1 EPCIS","PROV-O","OWL-Time","Prepare","Pilot","Operate","Scale")
$missing = $checks | Where-Object { $doc -notmatch [regex]::Escape($_) }
if ($missing) { Write-Host "Missing: $($missing -join ', ')" } else { Write-Host "Part 6 OK" }
```

기대값: "Part 6 OK"

- [ ] **Step 7: 전체 Flow Code 비WH 사용 검사 (CONSOLIDATED-00 자체)**

```powershell
# CONSOLIDATED-00 안에 WarehouseHandlingProfile 외부에서 confirmedFlowCode 사용 없어야 함
Select-String -Path "Logi ontol core doc\CONSOLIDATED-00-master-ontology.md" `
  -Pattern "confirmedFlowCode" | ForEach-Object {
    Write-Host "Line $($_.LineNumber): $($_.Line)"
}
```

기대값: confirmedFlowCode는 SHACL Shape 정의 내에만 존재.

- [ ] **Step 8: Git commit**

```bash
git add "Logi ontol core doc/CONSOLIDATED-00-master-ontology.md"
git commit -m "docs: add Part 6 Validation Rules, VIOLATION Gates, and Standards to CONSOLIDATED-00"
```

---

## Plan B: CONSOLIDATED-01~09 Extension 패치

**전제조건**: Plan A (Task 1~6) 완료 후 실행.

---

### Task 7: 01~05, 07, 09 — Extension 참조 헤더 패치

**Files:**
- Modify: `Logi ontol core doc/CONSOLIDATED-01-core-framework-infra.md`
- Modify: `Logi ontol core doc/CONSOLIDATED-02-warehouse-flow.md`
- Modify: `Logi ontol core doc/CONSOLIDATED-03-document-ocr.md`
- Modify: `Logi ontol core doc/CONSOLIDATED-04-barge-bulk-cargo.md`
- Modify: `Logi ontol core doc/CONSOLIDATED-05-invoice-cost.md`
- Modify: `Logi ontol core doc/CONSOLIDATED-07-port-operations.md`
- Modify: `Logi ontol core doc/CONSOLIDATED-09-operations.md`

- [ ] **Step 1: 각 파일 YAML에 spine_ref 필드 추가**

7개 파일 각각의 YAML frontmatter `status: "active"` 행 아래에 추가:

```yaml
spine_ref: "CONSOLIDATED-00-master-ontology.md"
extension_of: "hvdc-master-ontology-v1.0"
```

- [ ] **Step 2: 각 파일 MASTER GOVERNANCE RULE 블록 직후에 Extension 선언 추가**

MASTER GOVERNANCE RULE 블록 바로 아래에 다음 1줄 삽입:

```markdown
> **Extension Document** — 이 문서는 `CONSOLIDATED-00-master-ontology.md`의 도메인 확장입니다.
> RoutingPattern, Milestone, Identifier 정의는 00을 참조하세요.
```

- [ ] **Step 3: 01 파일 — ShipmentUnit/JourneyLeg/WarehouseHandlingProfile 클래스 링크 확인**

```powershell
Select-String -Path "Logi ontol core doc\CONSOLIDATED-01-core-framework-infra.md" `
  -Pattern "ShipmentUnit|CONSOLIDATED-00|spine_ref" | Select-Object LineNumber, Line
```

기대값: 3개 이상 매칭.

- [ ] **Step 4: 02 파일 — WarehouseHandlingProfile이 spine_ref 참조 확인**

```powershell
Select-String -Path "Logi ontol core doc\CONSOLIDATED-02-warehouse-flow.md" `
  -Pattern "spine_ref|CONSOLIDATED-00|WarehouseHandlingProfile Algorithm" `
  | Select-Object LineNumber, Line
```

기대값: 3개 이상 매칭.

- [ ] **Step 5: 07 파일 — plannedRoutingPattern 사용, assignedFlowCode 없음 확인**

```powershell
$match07 = Select-String -Path "Logi ontol core doc\CONSOLIDATED-07-port-operations.md" `
  -Pattern "assignedFlowCode"
if ($match07) {
  Write-Host "WARN: assignedFlowCode still present in 07:"
  $match07 | ForEach-Object { Write-Host "  Line $($_.LineNumber): $($_.Line)" }
} else { Write-Host "07 OK — no assignedFlowCode" }
```

기대값: "07 OK — no assignedFlowCode"

- [ ] **Step 6: Git commit**

```bash
git add "Logi ontol core doc/CONSOLIDATED-01-core-framework-infra.md" \
        "Logi ontol core doc/CONSOLIDATED-02-warehouse-flow.md" \
        "Logi ontol core doc/CONSOLIDATED-03-document-ocr.md" \
        "Logi ontol core doc/CONSOLIDATED-04-barge-bulk-cargo.md" \
        "Logi ontol core doc/CONSOLIDATED-05-invoice-cost.md" \
        "Logi ontol core doc/CONSOLIDATED-07-port-operations.md" \
        "Logi ontol core doc/CONSOLIDATED-09-operations.md"
git commit -m "docs: add spine_ref and Extension declaration to CONSOLIDATED-01~09"
```

---

### Task 8: CONSOLIDATED-08 — Evidence Layer 분리

**Files:**
- Modify: `Logi ontol core doc/CONSOLIDATED-08-communication.md`

- [ ] **Step 1: YAML frontmatter 변경**

`type: "ontology-design"` → `type: "evidence-layer-extension"` 로 변경.
`spine_ref: "CONSOLIDATED-00-master-ontology.md"` 추가.
`layer: "evidence"` 추가.

- [ ] **Step 2: 문서 상단 Executive Summary 앞에 Evidence Layer 선언 추가**

```markdown
> **Evidence Layer Document**
> CONSOLIDATED-08은 HVDC Logistics Core Ontology의 **Evidence/Communication Layer**입니다.
> 이 문서의 이메일/채팅 온톨로지는 Core Master Model의 일부가 아니며,
> `AuditRecord`, `CommunicationEvent`, `ApprovalAction` Evidence 클래스로만 연결됩니다.
> Core 물류 쿼리에서 직접 참조하지 마십시오.
```

- [ ] **Step 3: 검증**

```powershell
Select-String -Path "Logi ontol core doc\CONSOLIDATED-08-communication.md" `
  -Pattern "evidence-layer-extension|Evidence Layer Document|AuditRecord" `
  | Select-Object LineNumber, Line
```

기대값: 3개 매칭.

- [ ] **Step 4: Git commit**

```bash
git add "Logi ontol core doc/CONSOLIDATED-08-communication.md"
git commit -m "docs: reclassify CONSOLIDATED-08 as Evidence Layer extension"
```

---

## Plan C: CONSOLIDATED-06 재작성

**전제조건**: Plan A (Task 1~6) 완료 후 실행. Plan B와 병렬 가능.
**현재 파일**: 3495줄. 5개 Section으로 재구성.

---

### Task 9: 06 파일 백업 + 스캐폴드 재작성

**Files:**
- Modify: `Logi ontol core doc/CONSOLIDATED-06-material-handling.md`

- [ ] **Step 1: 기존 파일 백업**

```powershell
Copy-Item "Logi ontol core doc\CONSOLIDATED-06-material-handling.md" `
          "Logi ontol core doc\CONSOLIDATED-06-material-handling.bak.md"
Write-Host "Backup created"
```

- [ ] **Step 2: 새 YAML Frontmatter 작성**

```yaml
---
title: "HVDC Material Handling — Consolidated (v2.0)"
type: "ontology-design"
domain: "material-handling"
sub-domains: ["customs","storage","offshore","receiving","transformer","bulk-cargo"]
version: "consolidated-2.0"
date: "2026-04-11"
spine_ref: "CONSOLIDATED-00-master-ontology.md"
extension_of: "hvdc-master-ontology-v1.0"
status: "active"
source_files: [
  "2_EXT-08A~08G-hvdc-material-handling.md",
  "Logi ontol core doc/CONSOLIDATED-06-material-handling.bak.md"
]
---
```

- [ ] **Step 3: MASTER GOVERNANCE RULE + Extension 선언 삽입**

Task 7 Step 2와 동일한 Extension 선언 삽입.

- [ ] **Step 4: Table of Contents 작성**

```markdown
## Table of Contents
1. [Material Handling Overview & RoutingPattern Map](#section-1)
2. [Customs & Port Stage (M40~M100)](#section-2)
3. [Warehouse Operations (M110~M121)](#section-3)
4. [Offshore / Marine / Heavy-lift (M115~M117)](#section-4)
5. [Site Receiving & Inspection (M130~M140)](#section-5)
```

- [ ] **Step 5: Git commit**

```bash
git add "Logi ontol core doc/CONSOLIDATED-06-material-handling.md" \
        "Logi ontol core doc/CONSOLIDATED-06-material-handling.bak.md"
git commit -m "docs: scaffold CONSOLIDATED-06 v2.0 with new 5-section structure"
```

---

### Task 10: Section 1 — Material Handling Overview + RoutingPattern Map

**Files:**
- Modify: `Logi ontol core doc/CONSOLIDATED-06-material-handling.md`

- [ ] **Step 1: Section 1 헤더 + 개요 작성**

```markdown
## Section 1: Material Handling Overview & RoutingPattern Map

> **참조**: RoutingPattern 정의 전체는 `CONSOLIDATED-00` Part 1을 참조하세요.

이 섹션은 HVDC 프로젝트의 자재 카테고리별 기본 RoutingPattern을 정의합니다.
```

- [ ] **Step 2: 자재 카테고리별 RoutingPattern 테이블 작성**

기존 06의 "Flow Code Distribution by Material Type" 표를 RoutingPattern으로 전환:

| Material Category | Primary RoutingPattern | 경로 | 이유 |
|---|---|---|---|
| Container Cargo | WH_ONLY, WH_MOSB | Port→WH→(MOSB)→Site | 표준 컨테이너 |
| Bulk Cargo | MOSB_DIRECT, WH_MOSB | Port→(WH→)MOSB→Site | 대형 자재 MOSB 집하 필요 |
| Transformer/OOG | WH_MOSB, MOSB_DIRECT | Port→WH→MOSB→Site | 특수 취급 필수 |
| MIR/SHU Cargo | WH_ONLY, DIRECT | Port→WH→Site | MOSB 불필요 |
| AGI/DAS Cargo | MOSB_DIRECT, WH_MOSB, MIXED | MOSB 경유 필수 | VIOLATION-2 적용 |

- [ ] **Step 3: AGI/DAS 도메인 룰 블록 작성**

```markdown
> **AGI/DAS Domain Rule**: `declaredDestination IN (AGI, DAS)` 화물은
> `routingPattern IN (MOSB_DIRECT, WH_MOSB, MIXED)` 필수.
> M115 (MOSB Staged) milestone 없이 M130 (Site Arrived) 기록 시 VIOLATION-2 발동.
> → 참조: `CONSOLIDATED-00` Part 6, SHACL `hvdc:AGIDASStagingShape`
```

- [ ] **Step 4: 검증**

```powershell
Select-String -Path "Logi ontol core doc\CONSOLIDATED-06-material-handling.md" `
  -Pattern "RoutingPattern Map|AGI/DAS Domain Rule|VIOLATION-2|WH_MOSB|MOSB_DIRECT" `
  | Measure-Object | Select-Object Count
```

기대값: Count ≥ 5

- [ ] **Step 5: Git commit**

```bash
git add "Logi ontol core doc/CONSOLIDATED-06-material-handling.md"
git commit -m "docs: add Section 1 RoutingPattern Map to CONSOLIDATED-06 v2.0"
```

---

### Task 11: Section 2 + 3 — Customs/Port Stage + Warehouse Operations

**Files:**
- Modify: `Logi ontol core doc/CONSOLIDATED-06-material-handling.md`

- [ ] **Step 1: Section 2 — Customs & Port Stage (M40~M100) 작성**

기존 06의 "Customs Clearance" 섹션 내용 보존하되:
- 모든 "Flow Code" 참조 → MilestoneStatus 또는 RoutingPattern으로 교체
- M40/M50/M60/M61/M80/M90/M91/M92/M100 Milestone 참조 추가
- CustomsEntry 트랜잭션 클래스 참조 (`CONSOLIDATED-00 Part 4`)

- [ ] **Step 2: Section 3 — Warehouse Operations (M110~M121) 작성**

기존 06의 "Storage & Inland Transportation" 섹션 내용 보존하되:
- `WarehouseHandlingProfile` 참조를 `CONSOLIDATED-02` Extension으로 링크
- M110/M111/M120/M121 Milestone 연결
- `flowConfirmationStatus: tentative → confirmed` 전환 조건 명시
- `confirmedFlowCode` 언급 시 반드시 `WarehouseHandlingProfile` 소유임을 명시

```markdown
> **WH Flow Code 규칙**: `confirmedFlowCode`는 `WarehouseHandlingProfile` 클래스 안에서만
> 설정됩니다. 이 섹션의 WH 작업 기록은 M110 이벤트를 통해 WarehouseHandlingProfile을
> 생성·확정합니다. → 상세: `CONSOLIDATED-02 Section 2: WarehouseHandlingProfile Algorithm`
```

- [ ] **Step 3: 검증 — Section 2/3 Flow Code 직접 사용 없음 확인**

```powershell
# Section 3 범위에서 "Flow Code [0-5]" 패턴 없어야 함
$lines = Get-Content "Logi ontol core doc\CONSOLIDATED-06-material-handling.md"
$section3Start = ($lines | Select-String "Section 3").LineNumber[0]
$section4Start = ($lines | Select-String "Section 4").LineNumber[0]
$section3Content = $lines[($section3Start-1)..($section4Start-2)] -join "`n"
$violations = [regex]::Matches($section3Content, "Flow Code [0-5]")
if ($violations.Count -gt 0) {
  Write-Host "WARN: $($violations.Count) Flow Code [0-5] references in Section 3"
} else { Write-Host "Section 3 OK — no Flow Code [0-5]" }
```

기대값: "Section 3 OK — no Flow Code [0-5]"

- [ ] **Step 4: Git commit**

```bash
git add "Logi ontol core doc/CONSOLIDATED-06-material-handling.md"
git commit -m "docs: add Section 2 Customs/Port and Section 3 WH Operations to CONSOLIDATED-06 v2.0"
```

---

### Task 12: Section 4 + 5 — Offshore/Heavy-lift + Site Receiving

**Files:**
- Modify: `Logi ontol core doc/CONSOLIDATED-06-material-handling.md`

- [ ] **Step 1: Section 4 — Offshore / Marine / Heavy-lift 작성**

기존 06의 "Offshore Marine Transportation" + "Transformer Handling" + "Bulk Cargo" 섹션 통합:
- `MarineRoutingPattern` (DIRECT_MOSB/WH_THEN_MOSB/LCT_DIRECT) 참조 추가
- M115/M116/M117 Milestone 연결
- PTW/FRA/Tide Table/Lashing/Stability 기존 내용 보존
- MOSB = `OffshoreStaging Node` 명시, "창고" 용어 제거

```markdown
> **Marine Domain Rule**: Offshore/LCT 작업은 `MarineRoutingPattern`과
> `offshoreDeliveryPattern`을 사용합니다. Marine 도메인은 `confirmedFlowCode`를
> 할당하지 않습니다. → 상세: `CONSOLIDATED-04 Marine/Bulk Domain Rule`
```

- [ ] **Step 2: Section 5 — Site Receiving & Inspection 작성**

기존 06의 "Site Receiving" 섹션 내용 최대한 보존:
- M130/M131/M132/M140 Milestone 연결
- MRR/MRI/OSDR/POD/GRN 문서 클래스 참조
- `SiteReceipt` 트랜잭션 클래스 참조 (`CONSOLIDATED-00 Part 4`)
- OSD(Overage-Shortage-Damage) 처리 → Exception 클래스 연결

- [ ] **Step 3: 전체 06 파일 최종 검증 — 3대 원칙**

```powershell
$doc = Get-Content "Logi ontol core doc\CONSOLIDATED-06-material-handling.md" -Raw

# 검사 1: "Flow Code v3.5 Integration" 제목 없어야 함
if ($doc -match "Flow Code v3\.5 Integration") {
  Write-Host "FAIL: Old Flow Code v3.5 section title still present"
} else { Write-Host "CHECK 1 PASS" }

# 검사 2: "assignedFlowCode" 없어야 함
if ($doc -match "assignedFlowCode") {
  Write-Host "FAIL: assignedFlowCode found"
} else { Write-Host "CHECK 2 PASS" }

# 검사 3: 5개 Section 모두 존재
$sections = @("Section 1:","Section 2:","Section 3:","Section 4:","Section 5:")
$missing = $sections | Where-Object { $doc -notmatch [regex]::Escape($_) }
if ($missing) { Write-Host "FAIL: Missing sections: $($missing -join ', ')" }
else { Write-Host "CHECK 3 PASS" }
```

기대값: 3개 CHECK PASS

- [ ] **Step 4: Git commit**

```bash
git add "Logi ontol core doc/CONSOLIDATED-06-material-handling.md"
git commit -m "docs: add Section 4 Offshore and Section 5 Site Receiving to CONSOLIDATED-06 v2.0"
```

---

### Task 13: 최종 통합 검증

**Files:**
- `Logi ontol core doc/CONSOLIDATED-00-master-ontology.md`
- `Logi ontol core doc/CONSOLIDATED-01~09-*.md`

- [ ] **Step 1: 전체 corpus Flow Code 비WH 사용 검사**

```powershell
$files = Get-ChildItem "Logi ontol core doc\CONSOLIDATED-*.md" | 
  Where-Object { $_.Name -ne "CONSOLIDATED-02-warehouse-flow.md" }

foreach ($f in $files) {
  $hits = Select-String -Path $f.FullName -Pattern "confirmedFlowCode|assignedFlowCode"
  if ($hits) {
    Write-Host "WARN $($f.Name):"
    $hits | ForEach-Object { Write-Host "  L$($_.LineNumber): $($_.Line.Trim())" }
  }
}
Write-Host "Scan complete"
```

기대값: WARN 없음 (02 제외).

- [ ] **Step 2: 전체 corpus MASTER GOVERNANCE RULE 존재 확인**

```powershell
$files = Get-ChildItem "Logi ontol core doc\CONSOLIDATED-*.md"
foreach ($f in $files) {
  $hit = Select-String -Path $f.FullName -Pattern "MASTER GOVERNANCE RULE"
  if (-not $hit) { Write-Host "MISSING MASTER RULE: $($f.Name)" }
  else { Write-Host "OK: $($f.Name)" }
}
```

기대값: 전체 OK.

- [ ] **Step 3: CONSOLIDATED-00 spine_ref 참조 완전성 확인**

```powershell
$files = Get-ChildItem "Logi ontol core doc\CONSOLIDATED-0[1-9]*.md"
foreach ($f in $files) {
  $hit = Select-String -Path $f.FullName -Pattern "spine_ref"
  if (-not $hit) { Write-Host "MISSING spine_ref: $($f.Name)" }
  else { Write-Host "OK: $($f.Name)" }
}
```

기대값: 전체 OK.

- [ ] **Step 4: 최종 커밋**

```bash
git add "Logi ontol core doc/"
git commit -m "docs: complete HVDC Master Ontology implementation — CONSOLIDATED-00 spine + 06 rewrite + 01~09 extension patches"
```

- [ ] **Step 5: 백업 파일 삭제 (검증 후)**

```powershell
Remove-Item "Logi ontol core doc\CONSOLIDATED-06-material-handling.bak.md"
git add "Logi ontol core doc/CONSOLIDATED-06-material-handling.bak.md"
git commit -m "chore: remove CONSOLIDATED-06 backup after successful rewrite"
```

---

## 미결 가정 / 위험 (Spec에서 이월)

| # | 가정/위험 | 영향 | 권장 처리 |
|---|---|---|---|
| 1 | Package/PO upstream chain 미형성 | CONSOLIDATED-00 Part 3 Master Nodes 불완전 | 별도 Task 추가 또는 "Gap" 노트로 표시 |
| 2 | CustomsEntry ≠ BOE 문서 분리 | 03, 07 파일에 트랜잭션/문서 혼용 잔존 가능 | Task 7 패치 시 주의 |
| 3 | NCR/Claim lifecycle 미정의 | Exception 클래스 상세 부재 | CONSOLIDATED-00 Part 6 후속 패치 |
| 4 | CONSOLIDATED-06 기존 내용 3495줄 보존 vs 재구성 균형 | 섹션 재작성 시 유효 내용 누락 위험 | 백업 활용, 단계별 diff 확인 |
| 5 | MarineEvent/InspectionEvent 클래스 상세 미정의 | Part 5 Event 노드 불완전 | Task 5 이후 보완 가능 |
