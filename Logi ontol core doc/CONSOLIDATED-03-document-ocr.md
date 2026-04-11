---
title: "HVDC Document Guardian & OCR Pipeline Ontology - Consolidated"
type: "ontology-design"
domain: "document-processing"
sub-domains: ["document-guardian", "trust-ontology", "semantic-verification", "ocr-extraction", "data-refinement", "validation-framework", "cost-guard", "flow-code"]
version: "consolidated-1.1"
date: "2025-11-01"
tags: ["ontology", "hvdc", "ldg", "trust-layer", "semantic-reasoning", "knowledge-graph", "ocr", "document-processing", "validation", "cost-guard", "regtech", "flow-code", "consolidated"]
standards: ["RDF", "OWL", "SHACL", "SPARQL", "JSON-LD", "Turtle", "XSD"]
status: "active"
spine_ref: "CONSOLIDATED-00-master-ontology.md"
extension_of: "hvdc-master-ontology-v1.0"
source_files: ["1_CORE-06-hvdc-doc-guardian.md", "1_CORE-07-hvdc-ocr-pipeline.md", "docs/flow_code_v35/FLOW_CODE_V35_ALGORITHM.md"]
---

> **MASTER GOVERNANCE RULE**
> 1. **Flow Code is a warehouse-handling classification only.** Restricted to WarehouseHandlingProfile. No other domain may own or assign Flow Code as primary language.
> 2. **Program-wide shipment visibility shall use Journey Stage, Route Type, Milestone, and Leg.** (
oute_type, shipment_stage, leg_sequence, JourneyLeg)
> 3. **Port, Customs, Document, Cost, Marine, and Communication domains** may reference warehouse-flow *evidence*, but shall NOT own or assign Flow Code.
> 4. **MOSB is an Offshore Staging / Marine Interface Node**, not a Warehouse in the top-level logistics ontology.

> **Extension Document** — 이 문서는 [`CONSOLIDATED-00-master-ontology.md`](CONSOLIDATED-00-master-ontology.md)의 도메인 확장입니다.
> RoutingPattern Dictionary, Milestone M10~M160, Identifier Policy 정의는 CONSOLIDATED-00을 참조하세요.

# hvdc-document-ocr · CONSOLIDATED-03

## 📑 Table of Contents
1. [Route & Destination Evidence Extraction](#route-evidence-extraction)
2. [Logistics Document Guardian (LDG)](#section-1)
3. [LDG High-Precision OCR Pipeline](#section-2)

---

## Route & Destination Evidence Extraction {#route-evidence-extraction}

### Document Route Evidence Relationship

Logistics documents (Invoice, BOL, Packing List, Customs Declaration) contain **route and destination evidence** that must be extracted and validated during OCR processing. Evidence fields extracted from documents include:

1. **Destination Fields**: Final delivery location (MIR/SHU/AGI/DAS) → `destinationEvidence`
2. **Route Information**: Port → Warehouse → MOSB → Site path indicators → `routeEvidence`
3. **MOSB References**: Explicit MOSB leg mentioned in shipping instructions → `mosbLegIndicator`
4. **Site Codes**: AGI/DAS codes trigger mandatory MOSB leg evidence check

> **[Document/OCR Domain Rule — Clarified]**: OCR pipelines extract routing and destination *evidence* only.
> `routeEvidence` (port routing indicators), `destinationEvidence` (site codes), `mosbLegIndicator` (MOSB leg present).
> These evidence fields feed into `WarehouseHandlingProfile` after WH In (M110) — not as confirmedFlowCode directly.
> The document layer does NOT assign `confirmedFlowCode`.

### OCR Extraction Fields for Route Evidence

| Document Type | Route/Destination Evidence Fields | Extraction Priority | Validation Rule |
|---------------|---------------------------|---------------------|-----------------|
| **Bill of Lading (BOL)** | Final Destination, Consignee Site | HIGH | Site code → route_type assignment |
| **Commercial Invoice** | Delivery Address, Project Site | HIGH | AGI/DAS → route_type MOSB_DIRECT/WH_MOSB/MIXED required |
| **Packing List** | Destination Site, MOSB Transit Flag | MEDIUM | MOSB flag → route_type MOSB_DIRECT or WH_MOSB |
| **Customs Declaration** | Final Location, Transport Route | MEDIUM | Customs destination → route_type validation |
| **Delivery Order** | Site Code, Routing Instructions | HIGH | Explicit route_type field |

### Route Type Validation in LDG Pipeline

```
OCR Pipeline with Route Type:
1. Document Ingestion → Extract text/tables
2. Field Classification → Identify destination/route fields
3. Route Type Extraction → Parse Final_Location, MOSB flags
4. Business Rule Validation:
   - IF destination = AGI/DAS AND route_type NOT IN (MOSB_DIRECT,WH_MOSB,MIXED) → FAIL
   - IF MOSB_Transit = TRUE AND route_type NOT IN (MOSB_DIRECT,WH_MOSB,MIXED) → FAIL
   - IF destination = MIR/SHU AND route_type IN (MOSB_DIRECT,WH_MOSB) → WARNING
5. Cross-Document Verification:
   - Invoice route_type = BOL route_type (must match)
   - Packing List destination = Invoice destination
6. Trust Layer Update:
   - route evidence confidence score
   - Cross-Document route evidence consistency check

KPI Gates for Route Type OCR:
- Field Extraction Accuracy: ≥98% for destination fields
- Route Type Inference Accuracy: ≥95%
- Cross-Document Consistency: 100% (strict)
```

### RDF/OWL Properties for Document StreamCODE_GUARD

```turtle
@prefix ldg: <https://hvdc-project.com/ontology/document-guardian/> .
@prefix hvdc: <https://hvdc-project.com/ontology/core/> .

ldg:routeEvidence a owl:DatatypeProperty ;
    rdfs:label "Route Evidence Extracted from Document" ;
    rdfs:comment "Route evidence (destination, MOSB flag, route indicator) extracted via OCR" ;
    rdfs:domain ldg:Document ;
    rdfs:range xsd:integer .

ldg:routeEvidenceConfidence a owl:DatatypeProperty ;
    rdfs:label "Route Evidence Confidence" ;
    rdfs:comment "OCR confidence for route evidence fields (0-1)" ;
    rdfs:domain ldg:Document ;
    rdfs:range xsd:decimal .

ldg:destinationExtracted a owl:DatatypeProperty ;
    rdfs:label "Extracted Destination" ;
    rdfs:comment "Final destination extracted from document" ;
    rdfs:domain ldg:Document ;
    rdfs:range xsd:string .

ldg:mosbTransitFlag a owl:DatatypeProperty ;
    rdfs:label "MOSB Transit Flag Extracted" ;
    rdfs:comment "Boolean MOSB transit indicator from document" ;
    rdfs:domain ldg:Document ;
    rdfs:range xsd:boolean .

# SHACL: AGI/DAS Documents Must Have route_type MOSB_DIRECT+
ldg:DocumentRouteEvidenceConstraint a sh:NodeShape ;
    sh:targetClass ldg:Document ;
    sh:sparql [
        sh:message "Documents for AGI/DAS must provide route evidence indicating MOSB leg requirement" ;
        sh:select """
            PREFIX ldg: <https://hvdc-project.com/ontology/document-guardian/>
            SELECT $this
            WHERE {
                $this ldg:destinationExtracted ?dest ;
                      ldg:routeEvidence ?routeEvidence .
                FILTER(?dest IN ("AGI", "DAS") && ?routeEvidence NOT IN ("MOSB_DIRECT","WH_MOSB","MIXED","offshore","MOSB"))
            }
        """ ;
    ] .
```

### SPARQL Query: Cross-Document Route Evidence Verification

```sparql
PREFIX ldg: <https://hvdc-project.com/ontology/document-guardian/>

# Verify route evidence consistency across Invoice, BOL, Packing List
SELECT ?shipment ?invoice ?bol ?pl
       ?invoiceRE ?bolRE ?plRE ?consistent
WHERE {
    ?shipment ldg:hasInvoice ?invoice ;
              ldg:hasBOL ?bol ;
              ldg:hasPackingList ?pl .
    ?invoice ldg:routeEvidence ?invoiceRE .
    ?bol ldg:routeEvidence ?bolRE .
    ?pl ldg:routeEvidence ?plRE .
    BIND(IF(?invoiceRE = ?bolRE && ?bolRE = ?plRE, "PASS", "FAIL") AS ?consistent)
}
ORDER BY ?consistent
```

### Integration with Document Guardian

**LDG Route Type Checks**:
- **Extraction Phase**: OCR identifies route evidence fields in documents
- **Validation Phase**: Cross-reference route_type with destination
- **Trust Layer**: route evidence consistency across documents = higher trust score
- **Audit Trail**: route evidence mismatches flagged for manual review

**Cost Guard Integration**:
- route_type impacts logistics costs
- Invoice verification includes route-evidence-based rate validation
- route_type MOSB_DIRECT/WH_MOSB has additional MOSB handling charges

---

## Section 1: Logistics Document Guardian (LDG)

### Source
- **Original File**: `1_CORE-06-hvdc-doc-guardian.md`
- **Version**: unified-1.0
- **Date**: 2025-01-23

## Executive Summary

**온톨로지 관점에서 Logistics Document Guardian (LDG)**은 "문서 인식·검증 자동화 시스템"이 아니라, **지식 그래프 기반의 신뢰 체계(Trust Ontology System)**로 보는 게 정확하다.

LDG는 각 문서(CIPL, BL, PL, Invoice 등)를 **객체(Entity)**로 보고, 그 속성(Shipper, BL_No, HS_Code, Weight 등)을 **관계(Relation)**로 연결한다. 즉 "한 송장의 무게 필드가 B/L과 일치한다"는 것은 **데이터 일치가 아니라 관계의 정합성**을 의미한다.

이런 삼중 구조는 단순 데이터베이스가 아닌 **지식 기반(knowledge base)**이 되며, 문서 간 의미적 추론(Semantic Reasoning)이 가능하다.

**Visual — 핵심 클래스/관계(요약)**

| Class | 핵심 속성 | 관계 | 근거/조인 소스 | 결과 |
|-------|-----------|------|----------------|------|
| hvdc:Document | docId, docType, docHash | hasEntity → DocumentEntity | OCR/Table Parser | 상태, 정합성 |
| hvdc:DocumentEntity | entityType, value, confidence | linkedTo → CrossDocEntity | Field Tagger | URI 연결 |
| hvdc:TrustLayer | evidence, provenance, kpi | validates → DocumentGraph | SHACL Validation | PASS/FAIL |
| hvdc:LDGPayload | cascadedData, auditTrail | contains → VerificationResult | Knowledge Serialization | JSON/RDF |
| hvdc:CrossDocLink | sourceDoc, targetDoc, relation | crossReferences → Document | Entity Linking | 그래프 관계 |
| hvdc:VerificationResult | status, confidence, discrepancy | validates → Document | Auto-Verification | 검증 상태 |

자료: RDF 삼중 구조, SHACL 제약, 지식 그래프 기반 신뢰 체계.

**How it works (flow)**

1. **Data Acquisition**: 문서 이미지 → OCR → 디지털 트리플화 시작점 (관찰 노드 생성)
2. **Schema Alignment**: 문서별 속성을 온톨로지 클래스 구조에 맞춰 정규화
3. **Semantic Normalization**: 단위, 통화, 수량 등 의미 정규화 — "동일 의미 다른 표현"을 하나의 속성으로 매핑
4. **Entity Linking**: BL_No, Invoice_No 등을 URI로 연결 — 문서 간 그래프 관계 생성
5. **Knowledge Serialization**: LDG_PAYLOAD(JSON) = RDF 그래프의 직렬화 표현 (doc_hash는 Identity Anchor)
6. **SHACL Validation**: LDG_AUDIT은 그래프 제약 검증 결과 — 불일치 시 ZERO Fail-safe 트리거

**Options (설계 선택지)**

1. **RDF 삼중 기반 엄격형**: 모든 문서 관계를 RDF 삼중으로 모델링. *Pros* 의미적 추론↑ / *Cons* 초기 모델링 복잡도↑
2. **하이브리드형(권장)**: RDF + JSON 직렬화 + SHACL 제약, 부족 구간은 유사 문서 추천. *Pros* 실용성↑ / *Cons* 온톨로지 일관성 유지 필요
3. **지식 그래프 확장형**: FANR, MOIAT, Customs API 등 외부 규정도 동일한 URI 체계로 연결. *Pros* 확장성↑ / *Cons* 외부 데이터 동기화 필요

**Roadmap (P→Pi→B→O→S + KPI)**

- **Prepare**: 문서 타입별 RDF 스키마 정의, SHACL 제약 규칙 작성
- **Pilot**: /switch_mode LATTICE + /logi-master document-guardian --deep --trust-validation으로 샘플 문서 1회전. KPI: 검증정확도 ≥97%, 신뢰도 ≥95%
- **Build**: CrossDoc 관계 매핑, Trust Layer 증빙 시스템 구축, KPI 실시간 추적
- **Operate**: 불일치 감지 시 즉시 ZERO 모드 전환 + 감사 로그 생성
- **Scale**: 문서 그래프 스냅샷/변동 추적, 분기별 신뢰도 임계치 튜닝

**Automation notes**

- **입력 감지 →** /switch_mode LATTICE + /logi-master document-guardian (OCR→정규화→링킹→검증→신뢰도 측정)
- **신뢰 근거**: evidence[]와 doc_hash는 데이터의 provenance(출처·무결성)를 RDF 형태로 기록
- **감사 포맷**: SHACL Validation 결과 + Trust Layer KPI + CrossDoc 관계 맵

**QA / Gap 체크**

- 문서 간 관계 매핑이 **RDF 삼중 형태**로 올바르게 모델링되었는가?
- **SHACL 제약** 규칙이 모든 문서 타입에 대해 정의되었는가?
- Trust Layer의 **provenance 추적**이 완전한가?
- CrossDoc 링크의 **URI 연결**이 일관성 있게 유지되는가?

가정: (i) 모든 문서는 RDF 스키마에 따라 정규화됨, (ii) SHACL 제약은 내부 표준에 따라 배포됨, (iii) Trust Layer KPI는 실시간으로 업데이트됨.

---

## Section 2: LDG High-Precision OCR Pipeline

### Source
- **Original File**: `1_CORE-07-hvdc-ocr-pipeline.md`
- **Version**: unified-2.4
- **Date**: 2025-01-23

## Executive Summary

**고정밀 OCR·구조화 지침 v2.4 – LDG Ready**를 온톨로지 관점으로 보면, 단순 파이프라인이 아니라 "문서→추출→정제→검증→감사"로 이어지는 **의미 그래프**다. 핵심은 각 단계가 **명시적 클래스와 관계**로 연결되고, KPI와 Fail-safe가 **제약(Constraint)**으로 모델에 박혀 있다는 점이다.

**상위 개념 계층(Top Taxonomy)**:
```
Document Processing Pipeline
└── LDG OCR Pipeline
    ├── Document Input (CI/PL/BL/Invoice 등)
    ├── OCR Processing (Vision OCR, Smart Table Parser)
    ├── Data Refinement (NLP Refine, Field Tagger)
    ├── Validation Framework (Auto-Validation 5단계)
    ├── Cost Guard (표준요율 대비, FX 잠금)
    ├── RegTech Integration (MOIAT/FANR/IMDG/Dual-Use)
    └── Audit & Reporting (LDG_AUDIT, Cross-Doc Links)
```

**Visual — 핵심 클래스/관계(요약)**

| Class | 핵심 속성 | 관계 | 근거/조인 소스 | 결과 |
|-------|-----------|------|----------------|------|
| ldg:Document | docType, docId, fileHash | hasPage→Page, hasImage→Image | Document Registry | 처리 상태 |
| ldg:Page | pageNumber, imageRef | partOf→Document | OCR Engine | 추출 결과 |
| ldg:Image | imageHash, resolution | contains→OCRBlock | Vision OCR | 신뢰도 점수 |
| ldg:OCRBlock/OCRToken | text, confidence, position | extractedFrom→Image | OCR Processing | 정제 텍스트 |
| ldg:Table | schema, type, footnote | parsedFrom→OCRBlock | Smart Table Parser | 구조화 데이터 |
| ldg:RefinedText | formatted, unit, currency | refines→OCRToken | NLP Refine | 정규화 텍스트 |
| ldg:EntityTag | entityType, value, confidence | tags→RefinedText | Field Tagger | 엔티티 매핑 |
| ldg:Payload | version, trade, logistics | buildsFrom→EntityTag | Payload Builder | LDG_PAYLOAD |
| ldg:Validation | stage, result, percentage | validates→Payload | Auto-Validation | 검증 상태 |
| ldg:Metric | meanConf, tableAcc, numericIntegrity, entityMatch | measures→Validation | KPI Calculation | 성능 지표 |
| ldg:Audit | selfCheck, totalsCheck, crossDocCheck, hashConsistency | audits→Payload | LDG_AUDIT | 감사 결과 |
| ldg:CrossLink | sourceDoc, targetDoc, relation | links→Document | Cross-Doc Analysis | 문서 연관 |
| ldg:RegTechFlag | flagType, severity, jurisdiction | triggeredBy→EntityTag | RegTech Analysis | 규제 플래그 |
| ldg:HSCandidate | hsCode, confidence, source | proposedBy→EntityTag | HS Classification | HS 코드 후보 |
| ldg:CostGuardCheck | standardRate, draftRate, exceedPct, verdict | evaluates→Payload | Cost Guard | 비용 검증 |

자료: LDG Pipeline 단계별 처리 결과, KPI 임계값, 제약 조건.

**How it works (flow)**

1. **Document Input**: CI/PL/BL/Invoice 등 문서 업로드 → Document 객체 생성 → Page/Image 분할
2. **OCR Processing**: Vision OCR → OCRBlock/OCRToken 추출 (confidence 포함) → Smart Table Parser → Table 구조화
3. **Data Refinement**: NLP Refine → RefinedText 생성 (형식·단위 보정) → Field Tagger → EntityTag 자동 태깅
4. **Validation Framework**: Payload Builder → LDG_PAYLOAD 생성 → Auto-Validation 5단계 → Validation 결과
5. **Cost Guard**: 표준요율 대비 초과율 계산 → FX 잠금 정책 적용 → CostGuardCheck 판정
6. **RegTech Integration**: HS 후보/키워드 분석 → MOIAT/FANR/IMDG/Dual-Use 플래그 설정 → RegTechFlag 생성
7. **Audit & Reporting**: Cross-Doc Links 분석 → LDG_AUDIT 생성 → HITL 승인 → Report Lock

**Options (설계 선택지)**

1. **엄격형**: 모든 단계를 OWL/SHACL로 엄격하게 모델링. *Pros* 의미적 추론↑ / *Cons* 초기 모델링 복잡도↑
2. **하이브리드형(권장)**: OWL + JSON-LD + SHACL 제약, 부족 구간은 유사 패턴 추천. *Pros* 실용성↑ / *Cons* 온톨로지 일관성 유지 필요
3. **실무형**: 핵심 클래스만 모델링하고 나머지는 확장 가능한 구조. *Pros* 빠른 적용↑ / *Cons* 확장성 제한

**Roadmap (P→Pi→B→O→S + KPI)**

- **Prepare**: 네임스페이스/컨텍스트 확정, 클래스 스키마 정의, SHACL 제약 규칙 작성
- **Pilot**: /switch_mode LATTICE + /logi-master document-guardian --deep --ocr-precision으로 샘플 문서 1회전. KPI: OCR 정확도 ≥97%, 검증 성공률 ≥95%
- **Build**: KPI 게이트, Fail-safe 시스템, HITL 승인 프로세스 구축
- **Operate**: 실시간 모니터링, 이상 상황 즉시 ZERO 모드 전환 + 중단 로그
- **Scale**: 다중 문서 타입 지원, RegTech 규정 업데이트 자동화, Cost Guard 임계값 동적 조정

**Automation notes**

- **입력 감지 →** /switch_mode LATTICE + /logi-master document-guardian (OCR→정제→검증→감사→보고서)
- **표준 근거**: LDG Pipeline 단계별 KPI 임계값, HallucinationBan/Deterministic 규칙
- **감사 포맷**: LDG_AUDIT JSON + 해시/서명/타임스탬프 + Changelog

**QA / Gap 체크**

- OCR 신뢰도가 **임계값 이상**인가?
- NumericIntegrity가 **100%**인가?
- EntityMatch가 **기준 이상**인가?
- HashConsistency가 **PASS**인가?
- KPI 게이트를 **모두 통과**했는가?

가정: (i) 모든 문서는 표준 형식을 따름, (ii) OCR 엔진이 최신 버전으로 유지됨, (iii) KPI 임계값이 사전에 정의됨.

---

## 통합 온톨로지 시스템

### Domain Ontology

#### Core Classes

```turtle
# Document Guardian Classes
hvdc:Document a owl:Class ;
    rdfs:label "Document" ;
    rdfs:comment "물류 문서" .

hvdc:DocumentEntity a owl:Class ;
    rdfs:label "Document Entity" ;
    rdfs:comment "문서 내 엔티티" .

hvdc:TrustLayer a owl:Class ;
    rdfs:label "Trust Layer" ;
    rdfs:comment "신뢰 계층" .

hvdc:LDGPayload a owl:Class ;
    rdfs:label "LDG Payload" ;
    rdfs:comment "LDG 페이로드" .

hvdc:CrossDocLink a owl:Class ;
    rdfs:label "Cross Document Link" ;
    rdfs:comment "문서 간 연결" .

hvdc:VerificationResult a owl:Class ;
    rdfs:label "Verification Result" ;
    rdfs:comment "검증 결과" .

# OCR Pipeline Classes
ldg:Page a owl:Class ;
    rdfs:label "Page" ;
    rdfs:comment "문서 페이지" .

ldg:Image a owl:Class ;
    rdfs:label "Image" ;
    rdfs:comment "이미지" .

ldg:OCRBlock a owl:Class ;
    rdfs:label "OCR Block" ;
    rdfs:comment "OCR 블록" .

ldg:OCRToken a owl:Class ;
    rdfs:label "OCR Token" ;
    rdfs:comment "OCR 토큰" .

ldg:Table a owl:Class ;
    rdfs:label "Table" ;
    rdfs:comment "테이블" .

ldg:RefinedText a owl:Class ;
    rdfs:label "Refined Text" ;
    rdfs:comment "정제된 텍스트" .

ldg:EntityTag a owl:Class ;
    rdfs:label "Entity Tag" ;
    rdfs:comment "엔티티 태그" .

ldg:Payload a owl:Class ;
    rdfs:label "Payload" ;
    rdfs:comment "페이로드" .

ldg:Validation a owl:Class ;
    rdfs:label "Validation" ;
    rdfs:comment "검증" .

ldg:Metric a owl:Class ;
    rdfs:label "Metric" ;
    rdfs:comment "메트릭" .

ldg:Audit a owl:Class ;
    rdfs:label "Audit" ;
    rdfs:comment "감사" .

ldg:CrossLink a owl:Class ;
    rdfs:label "Cross Link" ;
    rdfs:comment "교차 링크" .

ldg:RegTechFlag a owl:Class ;
    rdfs:label "RegTech Flag" ;
    rdfs:comment "규제 기술 플래그" .

ldg:HSCandidate a owl:Class ;
    rdfs:label "HS Candidate" ;
    rdfs:comment "HS 코드 후보" .

ldg:CostGuardCheck a owl:Class ;
    rdfs:label "Cost Guard Check" ;
    rdfs:comment "비용 가드 검사" .
```

#### Data Properties

```turtle
# Document Guardian Properties
hvdc:hasDocId a owl:DatatypeProperty ;
    rdfs:label "has document ID" ;
    rdfs:domain hvdc:Document ;
    rdfs:range xsd:string .

hvdc:hasDocType a owl:DatatypeProperty ;
    rdfs:label "has document type" ;
    rdfs:domain hvdc:Document ;
    rdfs:range xsd:string .

hvdc:hasDocHash a owl:DatatypeProperty ;
    rdfs:label "has document hash" ;
    rdfs:domain hvdc:Document ;
    rdfs:range xsd:string .

hvdc:hasEntityType a owl:DatatypeProperty ;
    rdfs:label "has entity type" ;
    rdfs:domain hvdc:DocumentEntity ;
    rdfs:range xsd:string .

hvdc:hasValue a owl:DatatypeProperty ;
    rdfs:label "has value" ;
    rdfs:domain hvdc:DocumentEntity ;
    rdfs:range xsd:string .

hvdc:hasConfidence a owl:DatatypeProperty ;
    rdfs:label "has confidence" ;
    rdfs:domain hvdc:DocumentEntity ;
    rdfs:range xsd:decimal .

hvdc:hasEvidence a owl:DatatypeProperty ;
    rdfs:label "has evidence" ;
    rdfs:domain hvdc:TrustLayer ;
    rdfs:range xsd:string .

hvdc:hasProvenance a owl:DatatypeProperty ;
    rdfs:label "has provenance" ;
    rdfs:domain hvdc:TrustLayer ;
    rdfs:range xsd:string .

hvdc:hasKPI a owl:DatatypeProperty ;
    rdfs:label "has KPI" ;
    rdfs:domain hvdc:TrustLayer ;
    rdfs:range xsd:decimal .

hvdc:hasCascadedData a owl:DatatypeProperty ;
    rdfs:label "has cascaded data" ;
    rdfs:domain hvdc:LDGPayload ;
    rdfs:range xsd:string .

hvdc:hasAuditTrail a owl:DatatypeProperty ;
    rdfs:label "has audit trail" ;
    rdfs:domain hvdc:LDGPayload ;
    rdfs:range xsd:string .

hvdc:hasSourceDoc a owl:DatatypeProperty ;
    rdfs:label "has source document" ;
    rdfs:domain hvdc:CrossDocLink ;
    rdfs:range xsd:string .

hvdc:hasTargetDoc a owl:DatatypeProperty ;
    rdfs:label "has target document" ;
    rdfs:domain hvdc:CrossDocLink ;
    rdfs:range xsd:string .

hvdc:hasRelation a owl:DatatypeProperty ;
    rdfs:label "has relation" ;
    rdfs:domain hvdc:CrossDocLink ;
    rdfs:range xsd:string .

hvdc:hasStatus a owl:DatatypeProperty ;
    rdfs:label "has status" ;
    rdfs:domain hvdc:VerificationResult ;
    rdfs:range xsd:string .

hvdc:hasDiscrepancy a owl:DatatypeProperty ;
    rdfs:label "has discrepancy" ;
    rdfs:domain hvdc:VerificationResult ;
    rdfs:range xsd:string .

# OCR Pipeline Properties
ldg:hasPageNumber a owl:DatatypeProperty ;
    rdfs:label "has page number" ;
    rdfs:domain ldg:Page ;
    rdfs:range xsd:integer .

ldg:hasImageRef a owl:DatatypeProperty ;
    rdfs:label "has image reference" ;
    rdfs:domain ldg:Page ;
    rdfs:range xsd:string .

ldg:hasImageHash a owl:DatatypeProperty ;
    rdfs:label "has image hash" ;
    rdfs:domain ldg:Image ;
    rdfs:range xsd:string .

ldg:hasResolution a owl:DatatypeProperty ;
    rdfs:label "has resolution" ;
    rdfs:domain ldg:Image ;
    rdfs:range xsd:string .

ldg:hasText a owl:DatatypeProperty ;
    rdfs:label "has text" ;
    rdfs:domain ldg:OCRBlock ;
    rdfs:range xsd:string .

ldg:hasPosition a owl:DatatypeProperty ;
    rdfs:label "has position" ;
    rdfs:domain ldg:OCRBlock ;
    rdfs:range xsd:string .

ldg:hasSchema a owl:DatatypeProperty ;
    rdfs:label "has schema" ;
    rdfs:domain ldg:Table ;
    rdfs:range xsd:string .

ldg:hasType a owl:DatatypeProperty ;
    rdfs:label "has type" ;
    rdfs:domain ldg:Table ;
    rdfs:range xsd:string .

ldg:hasFootnote a owl:DatatypeProperty ;
    rdfs:label "has footnote" ;
    rdfs:domain ldg:Table ;
    rdfs:range xsd:string .

ldg:hasFormatted a owl:DatatypeProperty ;
    rdfs:label "has formatted text" ;
    rdfs:domain ldg:RefinedText ;
    rdfs:range xsd:string .

ldg:hasUnit a owl:DatatypeProperty ;
    rdfs:label "has unit" ;
    rdfs:domain ldg:RefinedText ;
    rdfs:range xsd:string .

ldg:hasCurrency a owl:DatatypeProperty ;
    rdfs:label "has currency" ;
    rdfs:domain ldg:RefinedText ;
    rdfs:range xsd:string .

ldg:hasEntityType a owl:DatatypeProperty ;
    rdfs:label "has entity type" ;
    rdfs:domain ldg:EntityTag ;
    rdfs:range xsd:string .

ldg:hasValue a owl:DatatypeProperty ;
    rdfs:label "has value" ;
    rdfs:domain ldg:EntityTag ;
    rdfs:range xsd:string .

ldg:hasConfidence a owl:DatatypeProperty ;
    rdfs:label "has confidence" ;
    rdfs:domain ldg:EntityTag ;
    rdfs:range xsd:decimal .

ldg:hasVersion a owl:DatatypeProperty ;
    rdfs:label "has version" ;
    rdfs:domain ldg:Payload ;
    rdfs:range xsd:string .

ldg:hasTrade a owl:DatatypeProperty ;
    rdfs:label "has trade" ;
    rdfs:domain ldg:Payload ;
    rdfs:range xsd:string .

ldg:hasLogistics a owl:DatatypeProperty ;
    rdfs:label "has logistics" ;
    rdfs:domain ldg:Payload ;
    rdfs:range xsd:string .

ldg:hasStage a owl:DatatypeProperty ;
    rdfs:label "has stage" ;
    rdfs:domain ldg:Validation ;
    rdfs:range xsd:string .

ldg:hasResult a owl:DatatypeProperty ;
    rdfs:label "has result" ;
    rdfs:domain ldg:Validation ;
    rdfs:range xsd:string .

ldg:hasPercentage a owl:DatatypeProperty ;
    rdfs:label "has percentage" ;
    rdfs:domain ldg:Validation ;
    rdfs:range xsd:decimal .

ldg:hasMeanConf a owl:DatatypeProperty ;
    rdfs:label "has mean confidence" ;
    rdfs:domain ldg:Metric ;
    rdfs:range xsd:decimal .

ldg:hasTableAcc a owl:DatatypeProperty ;
    rdfs:label "has table accuracy" ;
    rdfs:domain ldg:Metric ;
    rdfs:range xsd:decimal .

ldg:hasNumericIntegrity a owl:DatatypeProperty ;
    rdfs:label "has numeric integrity" ;
    rdfs:domain ldg:Metric ;
    rdfs:range xsd:decimal .

ldg:hasEntityMatch a owl:DatatypeProperty ;
    rdfs:label "has entity match" ;
    rdfs:domain ldg:Metric ;
    rdfs:range xsd:decimal .

ldg:hasSelfCheck a owl:DatatypeProperty ;
    rdfs:label "has self check" ;
    rdfs:domain ldg:Audit ;
    rdfs:range xsd:string .

ldg:hasTotalsCheck a owl:DatatypeProperty ;
    rdfs:label "has totals check" ;
    rdfs:domain ldg:Audit ;
    rdfs:range xsd:string .

ldg:hasCrossDocCheck a owl:DatatypeProperty ;
    rdfs:label "has cross document check" ;
    rdfs:domain ldg:Audit ;
    rdfs:range xsd:string .

ldg:hasHashConsistency a owl:DatatypeProperty ;
    rdfs:label "has hash consistency" ;
    rdfs:domain ldg:Audit ;
    rdfs:range xsd:string .

ldg:hasSourceDoc a owl:DatatypeProperty ;
    rdfs:label "has source document" ;
    rdfs:domain ldg:CrossLink ;
    rdfs:range xsd:string .

ldg:hasTargetDoc a owl:DatatypeProperty ;
    rdfs:label "has target document" ;
    rdfs:domain ldg:CrossLink ;
    rdfs:range xsd:string .

ldg:hasRelation a owl:DatatypeProperty ;
    rdfs:label "has relation" ;
    rdfs:domain ldg:CrossLink ;
    rdfs:range xsd:string .

ldg:hasFlagType a owl:DatatypeProperty ;
    rdfs:label "has flag type" ;
    rdfs:domain ldg:RegTechFlag ;
    rdfs:range xsd:string .

ldg:hasSeverity a owl:DatatypeProperty ;
    rdfs:label "has severity" ;
    rdfs:domain ldg:RegTechFlag ;
    rdfs:range xsd:string .

ldg:hasJurisdiction a owl:DatatypeProperty ;
    rdfs:label "has jurisdiction" ;
    rdfs:domain ldg:RegTechFlag ;
    rdfs:range xsd:string .

ldg:hasHsCode a owl:DatatypeProperty ;
    rdfs:label "has HS code" ;
    rdfs:domain ldg:HSCandidate ;
    rdfs:range xsd:string .

ldg:hasSource a owl:DatatypeProperty ;
    rdfs:label "has source" ;
    rdfs:domain ldg:HSCandidate ;
    rdfs:range xsd:string .

ldg:hasStandardRate a owl:DatatypeProperty ;
    rdfs:label "has standard rate" ;
    rdfs:domain ldg:CostGuardCheck ;
    rdfs:range xsd:decimal .

ldg:hasDraftRate a owl:DatatypeProperty ;
    rdfs:label "has draft rate" ;
    rdfs:domain ldg:CostGuardCheck ;
    rdfs:range xsd:decimal .

ldg:hasExceedPct a owl:DatatypeProperty ;
    rdfs:label "has exceed percentage" ;
    rdfs:domain ldg:CostGuardCheck ;
    rdfs:range xsd:decimal .

ldg:hasVerdict a owl:DatatypeProperty ;
    rdfs:label "has verdict" ;
    rdfs:domain ldg:CostGuardCheck ;
    rdfs:range xsd:string .
```

#### Object Properties

```turtle
# Document Guardian Relations
hvdc:hasEntity a owl:ObjectProperty ;
    rdfs:label "has document entity" ;
    rdfs:domain hvdc:Document ;
    rdfs:range hvdc:DocumentEntity .

hvdc:linkedTo a owl:ObjectProperty ;
    rdfs:label "linked to cross document entity" ;
    rdfs:domain hvdc:DocumentEntity ;
    rdfs:range hvdc:DocumentEntity .

hvdc:validates a owl:ObjectProperty ;
    rdfs:label "validates document graph" ;
    rdfs:domain hvdc:TrustLayer ;
    rdfs:range hvdc:Document .

hvdc:contains a owl:ObjectProperty ;
    rdfs:label "contains verification result" ;
    rdfs:domain hvdc:LDGPayload ;
    rdfs:range hvdc:VerificationResult .

hvdc:crossReferences a owl:ObjectProperty ;
    rdfs:label "cross references document" ;
    rdfs:domain hvdc:CrossDocLink ;
    rdfs:range hvdc:Document .

hvdc:validates a owl:ObjectProperty ;
    rdfs:label "validates document" ;
    rdfs:domain hvdc:VerificationResult ;
    rdfs:range hvdc:Document .

# OCR Pipeline Relations
ldg:hasPage a owl:ObjectProperty ;
    rdfs:label "has page" ;
    rdfs:domain ldg:Document ;
    rdfs:range ldg:Page .

ldg:hasImage a owl:ObjectProperty ;
    rdfs:label "has image" ;
    rdfs:domain ldg:Document ;
    rdfs:range ldg:Image .

ldg:partOf a owl:ObjectProperty ;
    rdfs:label "part of document" ;
    rdfs:domain ldg:Page ;
    rdfs:range ldg:Document .

ldg:contains a owl:ObjectProperty ;
    rdfs:label "contains OCR block" ;
    rdfs:domain ldg:Image ;
    rdfs:range ldg:OCRBlock .

ldg:extractedFrom a owl:ObjectProperty ;
    rdfs:label "extracted from image" ;
    rdfs:domain ldg:OCRBlock ;
    rdfs:range ldg:Image .

ldg:parsedFrom a owl:ObjectProperty ;
    rdfs:label "parsed from OCR block" ;
    rdfs:domain ldg:Table ;
    rdfs:range ldg:OCRBlock .

ldg:refines a owl:ObjectProperty ;
    rdfs:label "refines OCR token" ;
    rdfs:domain ldg:RefinedText ;
    rdfs:range ldg:OCRToken .

ldg:tags a owl:ObjectProperty ;
    rdfs:label "tags refined text" ;
    rdfs:domain ldg:EntityTag ;
    rdfs:range ldg:RefinedText .

ldg:buildsFrom a owl:ObjectProperty ;
    rdfs:label "builds from entity tag" ;
    rdfs:domain ldg:Payload ;
    rdfs:range ldg:EntityTag .

ldg:validates a owl:ObjectProperty ;
    rdfs:label "validates payload" ;
    rdfs:domain ldg:Validation ;
    rdfs:range ldg:Payload .

ldg:measures a owl:ObjectProperty ;
    rdfs:label "measures validation" ;
    rdfs:domain ldg:Metric ;
    rdfs:range ldg:Validation .

ldg:audits a owl:ObjectProperty ;
    rdfs:label "audits payload" ;
    rdfs:domain ldg:Audit ;
    rdfs:range ldg:Payload .

ldg:links a owl:ObjectProperty ;
    rdfs:label "links documents" ;
    rdfs:domain ldg:CrossLink ;
    rdfs:range ldg:Document .

ldg:triggeredBy a owl:ObjectProperty ;
    rdfs:label "triggered by entity tag" ;
    rdfs:domain ldg:RegTechFlag ;
    rdfs:range ldg:EntityTag .

ldg:proposedBy a owl:ObjectProperty ;
    rdfs:label "proposed by entity tag" ;
    rdfs:domain ldg:HSCandidate ;
    rdfs:range ldg:EntityTag .

ldg:evaluates a owl:ObjectProperty ;
    rdfs:label "evaluates payload" ;
    rdfs:domain ldg:CostGuardCheck ;
    rdfs:range ldg:Payload .
```

### Use-case별 제약

#### Document Guardian Constraints

```turtle
# Document Validation
hvdc:DocumentShape a sh:NodeShape ;
    sh:targetClass hvdc:Document ;
    sh:property [
        sh:path hvdc:hasDocId ;
        sh:minCount 1 ;
        sh:message "Document must have ID"
    ] ;
    sh:property [
        sh:path hvdc:hasDocType ;
        sh:minCount 1 ;
        sh:message "Document must have type"
    ] ;
    sh:property [
        sh:path hvdc:hasDocHash ;
        sh:minCount 1 ;
        sh:message "Document must have hash"
    ] .

# Document Entity Validation
hvdc:DocumentEntityShape a sh:NodeShape ;
    sh:targetClass hvdc:DocumentEntity ;
    sh:property [
        sh:path hvdc:hasEntityType ;
        sh:minCount 1 ;
        sh:message "Entity must have type"
    ] ;
    sh:property [
        sh:path hvdc:hasValue ;
        sh:minCount 1 ;
        sh:message "Entity must have value"
    ] ;
    sh:property [
        sh:path hvdc:hasConfidence ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
        sh:message "Confidence must be between 0 and 1"
    ] .

# Trust Layer Validation
hvdc:TrustLayerShape a sh:NodeShape ;
    sh:targetClass hvdc:TrustLayer ;
    sh:property [
        sh:path hvdc:hasEvidence ;
        sh:minCount 1 ;
        sh:message "Trust layer must have evidence"
    ] ;
    sh:property [
        sh:path hvdc:hasProvenance ;
        sh:minCount 1 ;
        sh:message "Trust layer must have provenance"
    ] ;
    sh:property [
        sh:path hvdc:hasKPI ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
        sh:message "KPI must be between 0 and 1"
    ] .
```

#### OCR Pipeline Constraints

```turtle
# OCR Block Validation
ldg:OCRBlockShape a sh:NodeShape ;
    sh:targetClass ldg:OCRBlock ;
    sh:property [
        sh:path ldg:hasText ;
        sh:minCount 1 ;
        sh:message "OCR block must have text"
    ] ;
    sh:property [
        sh:path ldg:hasConfidence ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
        sh:message "Confidence must be between 0 and 1"
    ] ;
    sh:property [
        sh:path ldg:hasPosition ;
        sh:minCount 1 ;
        sh:message "OCR block must have position"
    ] .

# Table Validation
ldg:TableShape a sh:NodeShape ;
    sh:targetClass ldg:Table ;
    sh:property [
        sh:path ldg:hasSchema ;
        sh:minCount 1 ;
        sh:message "Table must have schema"
    ] ;
    sh:property [
        sh:path ldg:hasType ;
        sh:minCount 1 ;
        sh:message "Table must have type"
    ] .

# Entity Tag Validation
ldg:EntityTagShape a sh:NodeShape ;
    sh:targetClass ldg:EntityTag ;
    sh:property [
        sh:path ldg:hasEntityType ;
        sh:minCount 1 ;
        sh:message "Entity tag must have type"
    ] ;
    sh:property [
        sh:path ldg:hasValue ;
        sh:minCount 1 ;
        sh:message "Entity tag must have value"
    ] ;
    sh:property [
        sh:path ldg:hasConfidence ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
        sh:message "Confidence must be between 0 and 1"
    ] .

# Validation Constraints
ldg:ValidationShape a sh:NodeShape ;
    sh:targetClass ldg:Validation ;
    sh:property [
        sh:path ldg:hasStage ;
        sh:minCount 1 ;
        sh:message "Validation must have stage"
    ] ;
    sh:property [
        sh:path ldg:hasResult ;
        sh:in ("PASS", "FAIL", "WARN") ;
        sh:message "Result must be PASS, FAIL, or WARN"
    ] ;
    sh:property [
        sh:path ldg:hasPercentage ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 100.0 ;
        sh:message "Percentage must be between 0 and 100"
    ] .

# Metric Validation
ldg:MetricShape a sh:NodeShape ;
    sh:targetClass ldg:Metric ;
    sh:property [
        sh:path ldg:hasMeanConf ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
        sh:message "Mean confidence must be between 0 and 1"
    ] ;
    sh:property [
        sh:path ldg:hasTableAcc ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
        sh:message "Table accuracy must be between 0 and 1"
    ] ;
    sh:property [
        sh:path ldg:hasNumericIntegrity ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
        sh:message "Numeric integrity must be between 0 and 1"
    ] ;
    sh:property [
        sh:path ldg:hasEntityMatch ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
        sh:message "Entity match must be between 0 and 1"
    ] .

# OCR KPI Gate Policy (Standard Thresholds - Hardening)
ldg:OCRKPIGateShape a sh:NodeShape ;
    sh:targetClass ldg:Metric ;
    sh:sparql [
        sh:severity sh:Violation ;
        sh:message "OCR KPI Gate 미달: MeanConf≥0.92, TableAcc≥0.98, NumericIntegrity=1.00, EntityMatch≥0.98 미달 시 ZERO-fail-safe 전환" ;
        sh:select """
            PREFIX ldg: <http://example.com/ldg#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            SELECT $this ?violation
            WHERE {
                $this a ldg:Metric .
                $this ldg:hasMeanConf ?meanConf .
                $this ldg:hasTableAcc ?tableAcc .
                $this ldg:hasNumericIntegrity ?numInt .
                $this ldg:hasEntityMatch ?entityMatch .
                {
                    FILTER(?meanConf < 0.92)
                    BIND("MEAN_CONF_BELOW_THRESHOLD" AS ?violation)
                } UNION {
                    FILTER(?tableAcc < 0.98)
                    BIND("TABLE_ACC_BELOW_THRESHOLD" AS ?violation)
                } UNION {
                    FILTER(?numInt != 1.00)
                    BIND("NUMERIC_INTEGRITY_NOT_PERFECT" AS ?violation)
                } UNION {
                    FILTER(?entityMatch < 0.98)
                    BIND("ENTITY_MATCH_BELOW_THRESHOLD" AS ?violation)
                }
            }
        """
    ] .
```

# Audit Validation
ldg:AuditShape a sh:NodeShape ;
    sh:targetClass ldg:Audit ;
    sh:property [
        sh:path ldg:hasSelfCheck ;
        sh:in ("PASS", "FAIL") ;
        sh:message "Self check must be PASS or FAIL"
    ] ;
    sh:property [
        sh:path ldg:hasTotalsCheck ;
        sh:in ("PASS", "FAIL") ;
        sh:message "Totals check must be PASS or FAIL"
    ] ;
    sh:property [
        sh:path ldg:hasCrossDocCheck ;
        sh:in ("PASS", "FAIL") ;
        sh:message "Cross document check must be PASS or FAIL"
    ] ;
    sh:property [
        sh:path ldg:hasHashConsistency ;
        sh:in ("PASS", "FAIL") ;
        sh:message "Hash consistency must be PASS or FAIL"
    ] .

# Cost Guard Check Validation
ldg:CostGuardCheckShape a sh:NodeShape ;
    sh:targetClass ldg:CostGuardCheck ;
    sh:property [
        sh:path ldg:hasStandardRate ;
        sh:minInclusive 0.01 ;
        sh:message "Standard rate must be positive"
    ] ;
    sh:property [
        sh:path ldg:hasDraftRate ;
        sh:minInclusive 0.01 ;
        sh:message "Draft rate must be positive"
    ] ;
    sh:property [
        sh:path ldg:hasExceedPct ;
        sh:minInclusive 0.0 ;
        sh:message "Exceed percentage must be non-negative"
    ] ;
    sh:property [
        sh:path ldg:hasVerdict ;
        sh:in ("PASS", "WARN", "HIGH", "CRITICAL") ;
        sh:message "Verdict must be PASS, WARN, HIGH, or CRITICAL"
    ] .
```

### JSON-LD Examples

#### Document Guardian Example

```json
{
  "@context": {
    "hvdc": "https://hvdc-project.com/ontology/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
  },
  "@id": "hvdc:document-001",
  "@type": "hvdc:Document",
  "hvdc:hasDocId": "DOC-2025-001",
  "hvdc:hasDocType": "CIPL",
  "hvdc:hasDocHash": "sha256:abc123...",
  "hvdc:hasEntity": {
    "@type": "hvdc:DocumentEntity",
    "hvdc:hasEntityType": "Shipper",
    "hvdc:hasValue": "ABC Company Ltd",
    "hvdc:hasConfidence": 0.98
  },
  "hvdc:hasEntity": {
    "@type": "hvdc:DocumentEntity",
    "hvdc:hasEntityType": "BL_No",
    "hvdc:hasValue": "BL123456",
    "hvdc:hasConfidence": 0.95
  }
}
```

#### OCR Pipeline Example

```json
{
  "@context": {
    "ldg": "https://hvdc-project.com/ontology/ldg/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
  },
  "@id": "ldg:document-001",
  "@type": "ldg:Document",
  "ldg:hasDocType": "CIPL",
  "ldg:hasDocId": "DOC-2025-001",
  "ldg:hasFileHash": "sha256:def456...",
  "ldg:hasPage": {
    "@type": "ldg:Page",
    "ldg:hasPageNumber": 1,
    "ldg:hasImageRef": "page1.jpg"
  },
  "ldg:hasImage": {
    "@type": "ldg:Image",
    "ldg:hasImageHash": "sha256:ghi789...",
    "ldg:hasResolution": "300x300",
    "ldg:contains": {
      "@type": "ldg:OCRBlock",
      "ldg:hasText": "Shipper: ABC Company Ltd",
      "ldg:hasConfidence": 0.97,
      "ldg:hasPosition": "x:100,y:200,w:300,h:50"
    }
  },
  "ldg:hasPayload": {
    "@type": "ldg:Payload",
    "ldg:hasVersion": "2.4",
    "ldg:hasTrade": "Import",
    "ldg:hasLogistics": "Container"
  },
  "ldg:hasValidation": {
    "@type": "ldg:Validation",
    "ldg:hasStage": "Auto-Validation",
    "ldg:hasResult": "PASS",
    "ldg:hasPercentage": 95.5
  },
  "ldg:hasMetric": {
    "@type": "ldg:Metric",
    "ldg:hasMeanConf": 0.97,
    "ldg:hasTableAcc": 0.95,
    "ldg:hasNumericIntegrity": 1.0,
    "ldg:hasEntityMatch": 0.92
  },
  "ldg:hasAudit": {
    "@type": "ldg:Audit",
    "ldg:hasSelfCheck": "PASS",
    "ldg:hasTotalsCheck": "PASS",
    "ldg:hasCrossDocCheck": "PASS",
    "ldg:hasHashConsistency": "PASS"
  }
}
```

### SPARQL Queries

#### Document Analysis Query

```sparql
PREFIX hvdc: <https://hvdc-project.com/ontology/>

SELECT
    ?docType
    (COUNT(?document) AS ?docCount)
    (AVG(?confidence) AS ?avgConfidence)
    (COUNT(?entity) AS ?entityCount)
WHERE {
    ?document hvdc:hasDocType ?docType .
    ?document hvdc:hasEntity ?entity .
    ?entity hvdc:hasConfidence ?confidence .
}
GROUP BY ?docType
ORDER BY DESC(?docCount)
```

#### OCR Performance Query

```sparql
PREFIX ldg: <https://hvdc-project.com/ontology/ldg/>

SELECT
    ?docType
    (AVG(?meanConf) AS ?avgMeanConf)
    (AVG(?tableAcc) AS ?avgTableAcc)
    (AVG(?numericIntegrity) AS ?avgNumericIntegrity)
    (AVG(?entityMatch) AS ?avgEntityMatch)
WHERE {
    ?document ldg:hasDocType ?docType .
    ?document ldg:hasValidation ?validation .
    ?validation ldg:hasMetric ?metric .
    ?metric ldg:hasMeanConf ?meanConf .
    ?metric ldg:hasTableAcc ?tableAcc .
    ?metric ldg:hasNumericIntegrity ?numericIntegrity .
    ?metric ldg:hasEntityMatch ?entityMatch .
}
GROUP BY ?docType
ORDER BY DESC(?avgMeanConf)
```

#### Cost Guard Analysis Query

```sparql
PREFIX ldg: <https://hvdc-project.com/ontology/ldg/>

SELECT
    ?verdict
    (COUNT(?check) AS ?checkCount)
    (AVG(?exceedPct) AS ?avgExceedPct)
    (MAX(?exceedPct) AS ?maxExceedPct)
WHERE {
    ?check ldg:hasVerdict ?verdict .
    ?check ldg:hasExceedPct ?exceedPct .
}
GROUP BY ?verdict
ORDER BY DESC(?avgExceedPct)
```

### Semantic KPI Layer

#### Document Guardian KPIs

- **Trust Layer Compliance**: 신뢰 계층 준수율
- **Cross-Document Consistency**: 문서 간 일관성
- **Entity Recognition Accuracy**: 엔티티 인식 정확도
- **Verification Success Rate**: 검증 성공률

#### OCR Pipeline KPIs

- **OCR Accuracy**: OCR 정확도
- **Table Parsing Success**: 테이블 파싱 성공률
- **Numeric Integrity**: 수치 무결성
- **Entity Matching Rate**: 엔티티 매칭률
- **Cost Guard Compliance**: 비용 가드 준수율

#### OCR KPI Gate Policy (Standard Thresholds)

**정책 선언**: 다음 표준 임계값 미달 시 **ZERO-fail-safe 모드 자동 전환**

| KPI Metric | 표준 Gate (Standard Threshold) | Fail-Safe 액션 |
|------------|--------------------------------|----------------|
| **MeanConf** (평균 신뢰도) | ≥ 0.92 | 미달 시 ZERO 모드 전환 + 수동 검토 요청 |
| **TableAcc** (테이블 정확도) | ≥ 0.98 | 미달 시 ZERO 모드 전환 + 수동 검토 요청 |
| **NumericIntegrity** (수치 무결성) | = 1.00 | 미달 시 ZERO 모드 전환 + 수동 검토 요청 |
| **EntityMatch** (엔티티 매칭률) | ≥ 0.98 | 미달 시 ZERO 모드 전환 + 수동 검토 요청 |

**SHACL 강제**: `ldg:OCRKPIGateShape` 규칙으로 자동 검증 및 위반 시 Violation 리포트 생성

**텔레메트리**: KPI Gate 위반 건은 실시간 대시보드에 집계되며, 연속 3회 미달 시 운영팀 알림 발송

### 추천 명령어

- `/document-guardian --deep --trust-validation` [문서 가디언 신뢰 검증]
- `/ocr-pipeline --precision --validation` [OCR 파이프라인 정밀 검증]
- `/cross-doc-analysis --consistency-check` [문서 간 일관성 분석]
- `/cost-guard --rate-check --fx-lock` [비용 가드 요율 검사]
- `/regtech-analysis --hs-classification` [규제 기술 분석]

이 통합 온톨로지는 HVDC 프로젝트의 문서 가디언과 OCR 파이프라인을 하나의 지식 그래프로 연결하여 문서 처리의 신뢰성, 정확성, 추적성을 높입니다.


