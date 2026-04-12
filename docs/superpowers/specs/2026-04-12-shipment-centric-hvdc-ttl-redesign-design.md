---
title: "Shipment-Centric HVDC TTL Redesign"
type: "design-spec"
version: "1.0"
date: "2026-04-12"
author: "Codex brainstorming session"
status: "approved"
source_inputs:
  - "Logi ontol core doc/HVDC STATUS.xlsx"
  - "Logi ontol core doc/HVDC WAREHOUSE STATUS.xlsx"
  - "Logi ontol core doc/JPT-reconciled_v6.0.xlsx"
  - "Logi ontol core doc/HVDC Logistics cost(inland,domestic).xlsx"
compatibility_targets:
  - "Logi ontol core doc/CONSOLIDATED-00-master-ontology.md"
  - "Logi ontol core doc/CONSOLIDATED-01-core-framework-infra.md"
  - "Logi ontol core doc/CONSOLIDATED-02-warehouse-flow.md"
  - "Logi ontol core doc/CONSOLIDATED-03-document-ocr.md"
  - "Logi ontol core doc/CONSOLIDATED-04-barge-bulk-cargo.md"
  - "Logi ontol core doc/CONSOLIDATED-05-invoice-cost.md"
  - "Logi ontol core doc/CONSOLIDATED-06-material-handling.md"
  - "Logi ontol core doc/CONSOLIDATED-07-port-operations.md"
  - "Logi ontol core doc/CONSOLIDATED-08-communication.md"
  - "Logi ontol core doc/CONSOLIDATED-09-operations.md"
knowledge_sources:
  - "C:/Users/jichu/Downloads/valut/wiki/analyses"
  - "whatsapp groupchat/00_WhatsApp_Group_Master_Policy.md"
  - "whatsapp groupchat/Guideline_*.txt"
decisions:
  - "Shipment is the primary spine"
  - "Case is the warehouse tracking unit"
  - "Time-bearing facts are modeled as events"
  - "JPT-reconciled_v6.0.xlsx is an LCT operations source"
  - "LCT is modeled as an operation carrier, not as the ontology spine"
  - "Locations use core plus operational location expansion"
  - "Scope includes transport, document, and settlement"
  - "Compatibility is semantic mapping, not name cloning"
  - "WhatsApp content enters as lesson, incident, rule, and evidence layers"
---

# Shipment-Centric HVDC TTL Redesign

## Summary

This design replaces the old flat graph idea with a shipment-centric TTL model
that preserves route chronology, warehouse traceability, LCT execution context,
document and settlement linkage, and lesson-learned knowledge from WhatsApp and
Obsidian analyses.

The new TTL must be driven primarily by four Excel workbooks and must remain
semantically compatible with `CONSOLIDATED-00~09` through a mapping layer rather
than by copying old class and property names verbatim.

## Approved Scope

- Primary spine: `Shipment`
- Warehouse unit: `Case`
- Time model: event-driven
- Marine execution source: `JPT-reconciled_v6.0.xlsx`
- LCT model: `OperationCarrier`
- Location taxonomy: core locations plus operational location expansion
- Functional scope: transport, document, settlement
- Knowledge scope: guide, lesson learned, incident, rule, evidence
- Compatibility mode: semantic mapping to `CONSOLIDATED-00~09`

## Source of Truth

### Primary source precedence

1. `HVDC STATUS.xlsx`
   - shipment identity
   - high-level route and document facts
2. `HVDC WAREHOUSE STATUS.xlsx`
   - case identity
   - warehouse, site, and physical package facts
3. `JPT-reconciled_v6.0.xlsx`
   - LCT operations
   - port calls
   - marine execution
   - voyage-level reconciliation
4. `HVDC Logistics cost(inland,domestic).xlsx`
   - inland and domestic invoice facts
   - charge summaries
   - shipment and event cost attribution

### Knowledge source precedence

1. `C:/Users/jichu/Downloads/valut/wiki/analyses`
   - `guideline_*.md` as guide and rule sources
   - `logistics_issue_*.md` as incident and lesson sources
2. `whatsapp groupchat` raw exports and guidelines
   - evidence source only
   - raw message history does not become the main ontology structure

## Architecture

The ontology is organized as seven layers.

### 1. Shipment spine

This is the main anchor for all execution and traceability.

- `Shipment`
- `Case`
- `CargoItem`
- `DocumentRef`
- `StatusSnapshot`

### 2. Location layer

This layer separates canonical logistics locations from narrower operating areas.

- `PortLocation`
- `HubLocation`
- `WarehouseLocation`
- `SiteLocation`
- `OperationalLocation`
- `Jetty`
- `AnchorageArea`
- `YardArea`
- `GateArea`

### 3. Event layer

Any fact with time belongs here.

- `RouteEvent`
- `ArrivalEvent`
- `DepartureEvent`
- `StorageEvent`
- `TransferEvent`
- `CargoHandlingEvent`
- `DeliveryEvent`
- `InspectionEvent`
- `DetentionEvent`
- `IssueEvent`

### 4. Marine and LCT operations layer

This layer is dedicated to `CONSOLIDATED-04` compatible marine execution.

- `OperationCarrier`
- `LCTOperation`
- `PortCall`
- `MarineLeg`
- `CargoManifest`
- `CarrierReadiness`
- `BunkeringEvent`
- `FreshWaterSupplyEvent`

### 5. Document and settlement layer

- `TransportDocument`
- `Invoice`
- `ChargeCategory`
- `ChargeSummary`
- `SettlementRecord`
- `ReconciliationRecord`
- `CostAttribution`

### 6. Knowledge layer

WhatsApp and analyses are represented here as structured operational knowledge.

- `GroupGuide`
- `OperatingRule`
- `ReportingRule`
- `EscalationRule`
- `DocumentAuthorityRule`
- `IncidentLesson`
- `RecurringPattern`
- `CommunicationEvidence`

### 7. Compatibility mapping layer

- `ConceptMapping`
- `PropertyMapping`
- `LegacyConcept`
- `LegacyRelation`

## Core Modeling Rules

### Rule 1. Shipment is the program spine

`Shipment` is the anchor for route, case, document, settlement, and lesson
relationships.

### Rule 2. Case is the warehouse execution unit

Warehouse and laydown status are linked directly to `Case`, not only to
`Shipment`.

### Rule 3. Time-bearing facts are events

A location date does not become a timeless edge. It becomes an event first and
is flattened later only for downstream projections.

### Rule 4. LCT is an operation carrier

`Jopetwil 71`, `JPT62`, `Thuraya`, and similar assets are modeled as
`OperationCarrier`. A dated voyage instance becomes `LCTOperation`.

### Rule 5. WhatsApp is knowledge, not the spine

WhatsApp groups do not define the main logistics graph. They contribute
structured lessons, incidents, rules, and evidence.

### Rule 6. Compatibility is semantic

The new TTL does not clone old names. It publishes mappings showing how new
classes and properties correspond to `CONSOLIDATED-00~09`.

## Identifier Rules

All identifiers must be deterministic and reproducible.

### Instance URI base

- `res:` -> `https://hvdc.logistics/resource/`

### Schema namespace bases

- `hvdc:` -> `https://hvdc.logistics/ontology/core/`
- `hvdce:` -> `https://hvdc.logistics/ontology/event/`
- `hvdco:` -> `https://hvdc.logistics/ontology/ops/`
- `hvdcd:` -> `https://hvdc.logistics/ontology/document/`
- `hvdck:` -> `https://hvdc.logistics/ontology/knowledge/`
- `hvdcm:` -> `https://hvdc.logistics/ontology/mapping/`

### Entity URI patterns

- `Shipment` -> `res:shipment/{sct_ship_no}`
- `Case` -> `res:case/{sct_ship_no}/{case_no}`
- `CargoItem` -> `res:cargo/{sct_ship_no}/{case_no}/{item_or_pkg}`
- `PortLocation` -> `res:port/{normalized_name}`
- `HubLocation` -> `res:hub/{normalized_name}`
- `WarehouseLocation` -> `res:warehouse/{normalized_name}`
- `SiteLocation` -> `res:site/{normalized_name}`
- `OperationalLocation` -> `res:oploc/{parent}/{normalized_name}`
- `OperationCarrier` -> `res:carrier/{normalized_name}`
- `LCTOperation` -> `res:lct-op/{carrier}/{normalized_voyage_or_batch}/{date}`
- `PortCall` -> `res:portcall/{carrier}/{location}/{datetime}`
- `TransportDocument` -> `res:doc/{doc_type}/{normalized_ref}`
- `Invoice` -> `res:invoice/{invoice_no}`
- `ChargeSummary` -> `res:charge/{invoice_no}/{charge_type}`
- `SettlementRecord` -> `res:settlement/{invoice_no}`
- `ReconciliationRecord` -> `res:recon/{normalized_voyage_id}`
- `IncidentLesson` -> `res:lesson/{group_slug}/{date}/{sequence}`
- `GroupGuide` -> `res:guide/{group_slug}`
- `CommunicationEvidence` -> `res:evidence/{group_slug}/{date}/{window_hash}`

### Event URI patterns

- `ArrivalEvent` -> `res:arrival/{subject_id}/{location}/{date}`
- `DepartureEvent` -> `res:departure/{subject_id}/{location}/{date}`
- `StorageEvent` -> `res:storage/{subject_id}/{warehouse}/{date}`
- `TransferEvent` -> `res:transfer/{subject_id}/{from}_{to}/{date}`
- `CargoHandlingEvent` -> `res:handling/{carrier_or_site}/{cargo_type}/{date}`
- `IssueEvent` -> `res:issue/{group_or_context}/{date}/{slug}`
- `InspectionEvent` -> `res:inspection/{subject_id}/{location}/{date}`
- `DetentionEvent` -> `res:detention/{subject_id}/{location}/{date}`

### Missing-time policy

If a time-bearing source value has no usable date or datetime, the event is not
minted as canonical truth. The source row is recorded in audit output instead.

## Class and Property Groups

### Shipment and case properties

#### `Shipment`

- `shipmentNo`
- `commercialInvoiceNo`
- `invoiceDate`
- `vendorName`
- `category`
- `mainDescription`
- `subDescription`
- `incoterms`
- `currency`
- `invoiceValue`
- `freightValue`
- `insuranceValue`
- `cifValue`
- `pol`
- `pod`
- `blOrAwbNo`
- `currentStatus`

#### `Case`

- `caseNo`
- `shipmentNo`
- `site`
- `eqNo`
- `pkgCount`
- `storageCode`
- `description`
- `lengthCm`
- `widthCm`
- `heightCm`
- `cbm`
- `netWeightKg`
- `grossWeightKg`
- `stackable`
- `hsCode`
- `price`
- `vesselName`
- `etaAta`
- `etdAtd`

### Location properties

- `locationCode`
- `locationName`
- `locationType`
- `parentLocation`
- `isOperationalLocation`

### Carrier and operation properties

#### `OperationCarrier`

- `carrierName`
- `carrierType`
- `charterer`
- `opsArea`
- `callToPort`
- `crewPax`
- `vesselFlag`
- `operatingStatus`

#### `LCTOperation`

- `voyageNo`
- `loadingDate`
- `subContractor`
- `cargoDescription`
- `sizeSpec`
- `deliveryQtyTon`
- `operationStatus`
- `eta`
- `etd`
- `startDateTime`
- `endDateTime`

#### `PortCall`

- `callLocation`
- `callType`
- `arrivalTime`
- `departureTime`
- `berthStatus`
- `tideCondition`
- `weatherCondition`

### Document and settlement properties

#### `TransportDocument`

- `documentType`
- `documentRef`
- `documentDate`
- `issuedBy`
- `documentStatus`

#### `Invoice`

- `invoiceNo`
- `invoiceDate`
- `amount`
- `vat`
- `grossTotal`
- `currency`
- `matchStatus`
- `mismatchFlag`
- `notes`

#### `ChargeSummary`

- `chargeType`
- `chargeAmount`
- `chargeCurrency`

### Knowledge properties

#### `IncidentLesson`

- `incidentTitle`
- `groupName`
- `incidentDate`
- `issueType`
- `rootCauseText`
- `actionTakenText`
- `lessonLearnedText`
- `severity`
- `relatedPattern`

#### `GroupGuide`

- `groupName`
- `groupType`
- `scope`
- `ssotRule`
- `reportingWindow`
- `escalationRule`
- `documentAuthority`
- `version`

## Core Object Properties

### Shipment and case

- `hvdc:hasCase`
- `hvdc:containsCargoItem`
- `hvdc:hasDocumentRef`
- `hvdc:hasStatusSnapshot`

### Event

- `hvdce:occurredAt`
- `hvdce:hasStartTime`
- `hvdce:hasEndTime`
- `hvdce:relatesToShipment`
- `hvdce:relatesToCase`
- `hvdce:hasEventStatus`
- `hvdce:hasSequenceNo`

### LCT and marine ops

- `hvdco:executesOperation`
- `hvdco:hasPortCall`
- `hvdco:hasMarineLeg`
- `hvdco:carriesShipment`
- `hvdco:hasCargoManifest`
- `hvdco:hasReadiness`
- `hvdco:hasTideCondition`
- `hvdco:hasWeatherCondition`

### Document and settlement

- `hvdcd:documentedBy`
- `hvdcd:invoicedAs`
- `hvdcd:hasChargeSummary`
- `hvdcd:hasChargeCategory`
- `hvdcd:settledBy`
- `hvdcd:reconciledBy`
- `hvdcd:attributedToShipment`
- `hvdcd:attributedToEvent`
- `hvdcd:attributedToLocation`

### Knowledge

- `hvdck:definesRule`
- `hvdck:supportedByEvidence`
- `hvdck:followsRule`
- `hvdck:violatesRule`
- `hvdck:relatedToShipment`
- `hvdck:relatedToLocation`
- `hvdck:relatedToCarrier`
- `hvdck:exemplifiesPattern`

### Compatibility mapping

- `hvdcm:mapsClassTo`
- `hvdcm:mapsPropertyTo`
- `hvdcm:mapsRuleTo`
- `hvdcm:mapsPatternTo`

## Workbook Mapping

### `HVDC STATUS.xlsx`

Purpose:

- shipment identity
- route chronology source
- document metadata source

Key mappings:

- `SCT SHIP NO.` -> `Shipment.shipmentNo`
- `COMMERCIAL INVOICE No.` -> `Shipment.commercialInvoiceNo`
- `PO No.` -> `DocumentRef` or shipment-linked document key
- `VENDOR` -> `Shipment.vendorName`
- `CATEGORY` -> `Shipment.category`
- `MAIN DESCRIPTION (PO)` -> `Shipment.mainDescription`
- `SUB DESCRIPTION` -> `Shipment.subDescription`
- `COE` / `POL` / `POD` -> `TransportDocument` and `Location`
- `B/L No./ AWB No.` -> `TransportDocument`
- `VESSEL NAME/ FLIGHT No.` -> carrier reference
- dated location columns such as `MOSB`, `SHU`, `MIR`, `DAS`, `AGI`, and
  warehouse date columns -> route or storage events

### `HVDC WAREHOUSE STATUS.xlsx`

Purpose:

- case identity
- warehouse and site tracking
- physical package metadata

Key mappings:

- `SCT SHIP NO.` -> `Shipment`
- `Case No.` -> `Case.caseNo`
- `Pkg` -> `Case.pkgCount`
- `Storage` -> `WarehouseLocation` or storage code
- `Site` -> `SiteLocation`
- `Description` -> `Case.description`
- dimensions and weights -> `Case` physical attributes
- `HS Code` -> `Case.hsCode`
- `Vessel` -> linked `OperationCarrier`
- `ETA/ATA`, `ETD/ATD` -> case-linked event times

### `JPT-reconciled_v6.0.xlsx`

Purpose:

- LCT execution facts
- decklog and port calls
- marine operation rollups
- reconciliation facts

Recommended sheet mapping:

- `1_Decklog`
  - `OperationCarrier`
  - `PortCall`
  - `CargoHandlingEvent`
  - `BunkeringEvent`
  - `FreshWaterSupplyEvent`
  - weather and tide context
- `3_Voyage_Master`
  - `LCTOperation`
  - cargo manifest summary
- `4_Voyage_Rollup`
  - normalized `LCTOperation` summary
- `6_Reconciliation`
  - `ReconciliationRecord`
  - `SettlementRecord`
- `7_Exceptions`
  - exception lesson candidates
- `8_Decklog_Context`
  - carrier context snapshots

### `HVDC Logistics cost(inland,domestic).xlsx`

Purpose:

- inland and domestic cost facts
- invoice linkage
- event and location cost attribution

Key mappings:

- `Invoice No` -> `Invoice.invoiceNo`
- `Invoice Date` -> `Invoice.invoiceDate`
- `Shipment No` -> `Shipment`
- `Job Description` -> attribution evidence
- `Inland`, `THC`, `Inspection`, `Detention`, `Storage`, `Others` ->
  `ChargeSummary`
- `TOTAL`, `VAT`, `G. TOTAL` -> `Invoice`

Preferred attribution:

- `Inland` -> `TransferEvent`
- `Storage` -> `StorageEvent`
- `Detention` -> `DetentionEvent`
- `Inspection` -> `InspectionEvent`

## WhatsApp and Analyses Mapping

### Accepted role of WhatsApp data

WhatsApp group content is retained as lesson and evidence, not as the main
transactional graph.

### Mapping rules

- `guideline_*.md` -> `GroupGuide`
- `logistics_issue_*.md` -> `IncidentLesson`
- raw chat excerpt -> `CommunicationEvidence`
- guide rule blocks -> `OperatingRule`, `ReportingRule`, `EscalationRule`
- repeated operational themes -> `RecurringPattern`

### Recommended wiki logic

The Obsidian side should keep two document families:

1. group handbook pages
2. incident and lesson pages

The TTL should link nodes to the most relevant lessons so that a node click can
open major incidents, rules, and evidence in a dashboard or wiki companion.

## Compatibility Mapping Principles

### Principle 1. Semantic compatibility first

The new TTL keeps new class and property structure and publishes explicit
mapping to `CONSOLIDATED-00~09`.

### Principle 2. One old concept may map to multiple new concepts

For example, an older "vessel movement" idea may split into:

- `OperationCarrier`
- `PortCall`
- `ArrivalEvent`
- `DepartureEvent`

### Principle 3. `CONSOLIDATED-04` has priority for marine meaning

The new LCT and barge semantics must align first with:

- marine routing meaning
- MOSB staging meaning
- LCT transport meaning
- operational location meaning for port, jetty, and anchorage

### Principle 4. Knowledge layer does not rewrite execution core

Guides and lessons link to the execution graph but do not become the execution
source of truth.

## Validation and Audit Principles

The redesign assumes the following gate behavior.

### Source contract

- required columns must exist
- date-bearing event source values must parse
- missing event dates do not silently mint canonical events

### Canonical integrity

- no dangling shipment, case, event, or invoice links
- no duplicate deterministic IDs
- no event without subject and time policy

### Knowledge integrity

- each `IncidentLesson` must link to at least one shipment, location, carrier,
  or recurring pattern
- each `GroupGuide` must define at least one rule

### Audit output

Audit files should capture:

- dropped rows
- unresolved attribution
- weak cost attribution confidence
- unmapped lessons
- unresolved compatibility mappings

## Optional Enhancements

These are recommended but not required for the first implementation plan.

### Node drilldown bundle

Allow one node query to return:

- recent events
- top incident lessons
- governing rules
- linked invoice or reconciliation objects

### Pattern-first navigation

Add `RecurringPattern` nodes such as:

- `HighTideDelay`
- `ManifestLag`
- `GatePassMissing`
- `ForkliftShortage`

### Confidence scoring

Allow:

- `hvdck:confidenceScore`
- `hvdcd:attributionConfidence`

to distinguish high-confidence automated links from review-needed links.

## Out of Scope

- raw message-by-message WhatsApp graphing
- replacing `CONSOLIDATED-00~09` documents themselves
- copying legacy names as the main namespace strategy
- line-item accounting ontology at the first rollout

