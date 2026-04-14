---
title: "OUTLOOK HVDC Email Ontology Workbook Redesign"
type: "design-spec"
version: "1.0"
date: "2026-04-12"
author: "Codex brainstorming session"
status: "approved"
source_inputs:
  - "Logi ontol core doc/OUTLOOK_HVDC_ALL_20250920260.xlsx"
related_specs:
  - "docs/superpowers/specs/2026-04-12-shipment-centric-hvdc-ttl-redesign-design.md"
  - "docs/superpowers/specs/2026-04-12-kg-dashboard-graph-visibility-alignment-design.md"
compatibility_targets:
  - "Logi ontol core doc/TTL CLASS.MD"
  - "Logi ontol core doc/TTL 매핑 초안.MD"
  - "Logi ontol core doc/ROLE_PATCH2.MD"
  - "Logi ontol core doc/온톨리지  TTL 설계.MD"
decisions:
  - "The source workbook remains immutable"
  - "The ontology workbook is produced as a separate structured workbook"
  - "PlainTextBody is parsed into signals before ontology export"
  - "canonical_ontology_export uses one row per statement"
  - "wiki/analyses content is linked by pointer rows, not duplicated into the workbook"
  - "Thread, message, link, signal, ontology, and audit layers remain separate"
---

# OUTLOOK HVDC Email Ontology Workbook Redesign

## Summary

This design restructures the Outlook-derived HVDC email workbook into an
ontology-ready workbook without treating the raw email sheet as the final graph
model.

The source workbook stays unchanged. A new workbook is produced with separate
sheets for raw message identity, thread structure, case and site links, text
extraction signals, ontology export statements, wiki pointers, and audit review.

The main goal is to make email evidence usable for ontology and wiki pipelines
without mixing raw text, inferred meaning, and canonical graph statements in one
table.

## Current Workbook Facts

Source workbook: `Logi ontol core doc/OUTLOOK_HVDC_ALL_20250920260.xlsx`

### Confirmed source shape

- Primary raw sheet: `전체_데이터`
- Aggregate sheets:
  - `월별_요약`
  - `케이스별_통계`
  - `사이트별_통계`
  - `LPO별_통계`
  - `단계별_통계`

### Confirmed raw-sheet characteristics

- Total rows: `19,927`
- `PlainTextBody` present on `19,905` rows
- `LinkKey` present on all rows and usable as thread grouping key
- Duplicate semantic columns exist:
  - `site = sites = primary_site`
  - `lpo = lpo_numbers`
  - `phase = stage`
  - `hvdc_cases = case_numbers`
- `primary_case` is not a duplicate of `hvdc_cases`; it is the representative
  case when multiple cases appear in one email
- Multi-value fields already exist and must be normalized rather than kept as a
  single CSV string:
  - `hvdc_cases`
  - `case_numbers`
  - `lpo_numbers`
  - `phase`

### Observed evidence density

The workbook contains enough text to justify a signal layer before ontology
mapping.

Frequent email signals observed from subject and body:

- `gate pass`
- `vessel` or `voyage`
- `permit` or `approval`
- `inspection`
- `manifest`
- `invoice`
- `customs`
- `arrival`
- `departure`
- `delay`
- `damage`

## Goal

Rebuild the Outlook workbook into a staged ontology workbook that supports:

1. reproducible message-level traceability
2. deterministic relation tables for case, site, LPO, and phase
3. structured signal extraction from `PlainTextBody`
4. export into shipment-centric ontology statements
5. stable pointers to `wiki/analyses`
6. audit-friendly review before TTL generation

## Non-Goals

- Do not overwrite the original Outlook workbook
- Do not convert every email body directly into canonical ontology classes
- Do not copy full wiki note bodies into the workbook
- Do not use aggregate sheets as source-of-truth inputs for ontology export

## Recommended Approach

Three approaches were considered.

### Approach A. Directly reshape the raw sheet

Keep one wide sheet and add more ontology columns.

Tradeoff:
- fast to start
- becomes hard to validate
- raw values and inferred values mix together

### Approach B. Direct body-to-ontology conversion

Parse `PlainTextBody` and emit ontology rows immediately.

Tradeoff:
- fast ontology output
- high risk of false positives
- weak audit trail

### Approach C. Layered ontology workbook

Use a staged workbook:

- raw message layer
- xref link layer
- signal extraction layer
- ontology statement export layer
- wiki pointer layer
- audit layer

Tradeoff:
- more sheets
- safer review
- easier TTL export and debugging

Recommendation: Approach C.

## Output Workbook Contract

The implementation should generate a new workbook instead of editing the source
file in place.

Recommended output path:

- `output/spreadsheet/outlook_hvdc_email_ontology_workbook.xlsx`

Optional mirrored deliverable for domain users:

- `Logi ontol core doc/OUTLOOK_HVDC_ALL_20250920260.ontology-workbook.xlsx`

## Sheet Model

The output workbook should contain the following sheets.

### 1. `raw_email_message`

Purpose:
- preserve the message-level raw evidence contract

Grain:
- one row per source email row

Required columns:
- `message_id`
- `source_row_no`
- `month_key`
- `thread_id`
- `subject_raw`
- `sender_name_raw`
- `sender_email_raw`
- `company_name_raw`
- `recipient_to_raw`
- `delivery_time_raw`
- `creation_time_raw`
- `site_raw`
- `lpo_raw`
- `phase_raw`
- `hvdc_cases_raw`
- `primary_case_raw`
- `primary_site_raw`
- `body_raw`
- `raw_hash`

Rules:
- `message_id` is derived from source `no`
- no ontology inference is stored here
- normalized copies belong in other sheets

### 2. `raw_thread_index`

Purpose:
- represent thread structure separately from individual messages

Grain:
- one row per `LinkKey`

Required columns:
- `thread_id`
- `message_count`
- `first_delivery_time`
- `last_delivery_time`
- `reply_like_subject_ratio`
- `canonical_subject_guess`
- `thread_status`
- `review_note`

Rules:
- `thread_id` comes from `LinkKey`
- this sheet is for grouping, not ontology export

### 3. `xref_message_case`

Purpose:
- normalize one-to-many case links from raw emails

Grain:
- one row per `message_id x case_no`

Required columns:
- `xref_id`
- `message_id`
- `thread_id`
- `case_no`
- `is_primary_case`
- `source_column`
- `parse_status`

### 4. `xref_message_site`

Purpose:
- normalize site references

Grain:
- one row per `message_id x site_code`

Required columns:
- `xref_id`
- `message_id`
- `thread_id`
- `site_code`
- `is_primary_site`
- `source_column`
- `parse_status`

### 5. `xref_message_lpo`

Purpose:
- normalize LPO references

Grain:
- one row per `message_id x lpo_no`

Required columns:
- `xref_id`
- `message_id`
- `thread_id`
- `lpo_no`
- `source_column`
- `parse_status`

### 6. `xref_message_phase`

Purpose:
- normalize single or multi-phase assignments

Grain:
- one row per `message_id x phase_name`

Required columns:
- `xref_id`
- `message_id`
- `thread_id`
- `phase_name`
- `is_primary_phase`
- `source_column`
- `parse_status`

### 7. `xref_message_party`

Purpose:
- separate participant identity from free-form sender and recipient text

Grain:
- one row per `message_id x party`

Required columns:
- `xref_id`
- `message_id`
- `thread_id`
- `party_role`
- `party_name_raw`
- `party_email_raw`
- `organization_guess`
- `parse_status`

### 8. `signal_document`

Purpose:
- store document-like signals extracted from subject and body

Grain:
- one row per extracted document signal

Typical document signals:
- `IRN`
- `Invoice`
- `TaxInvoice`
- `Manifest`
- `PackingList`
- `GatePass`
- `BillOfEntry`
- `ApprovalLetter`

Required columns:
- `signal_id`
- `message_id`
- `thread_id`
- `signal_type`
- `document_ref_raw`
- `document_subtype`
- `shipment_no_guess`
- `case_no_guess`
- `site_code_guess`
- `matched_pattern`
- `evidence_text`
- `confidence`
- `review_status`

### 9. `signal_event`

Purpose:
- store event-like signals extracted from subject and body

Grain:
- one row per extracted event signal

Typical event signals:
- `ArrivalEvent`
- `DepartureEvent`
- `InspectionEvent`
- `MobilizationEvent`
- `CustomsStep`
- `TransferEvent`
- `DeliveryEvent`

Required columns:
- `signal_id`
- `message_id`
- `thread_id`
- `event_type`
- `event_date_raw`
- `location_raw`
- `shipment_no_guess`
- `case_no_guess`
- `carrier_guess`
- `matched_pattern`
- `evidence_text`
- `confidence`
- `review_status`

### 10. `signal_risk`

Purpose:
- store risk, issue, and exception signals extracted from subject and body

Grain:
- one row per extracted risk signal

Typical risk signals:
- `DelayIncident`
- `DamageIncident`
- `PermitIssue`
- `CustomsHold`
- `DocumentGap`

Required columns:
- `signal_id`
- `message_id`
- `thread_id`
- `risk_type`
- `severity_guess`
- `shipment_no_guess`
- `case_no_guess`
- `site_code_guess`
- `carrier_guess`
- `matched_pattern`
- `evidence_text`
- `confidence`
- `review_status`

### 11. `canonical_ontology_export`

Purpose:
- store ontology-ready statements in a graph-friendly table

Grain:
- one row per statement

This sheet is intentionally narrow and long-form. It must not be a wide sheet
with one block of columns per class.

Required columns:
- `statement_id`
- `subject_id`
- `subject_class`
- `predicate`
- `object_kind`
- `object_value`
- `object_class`
- `literal_datatype`
- `source_sheet`
- `source_row_no`
- `source_message_id`
- `source_thread_id`
- `created_from_signal`
- `evidence_text`
- `confidence`
- `review_status`
- `wiki_pointer_id`

Object rules:
- `object_kind = iri` when `object_value` is an ontology resource id
- `object_kind = literal` when `object_value` is a scalar value
- `object_class` is empty when `object_kind = literal`
- `literal_datatype` is empty when `object_kind = iri`

Expected classes from this workbook:
- `CommunicationEvent`
- `Shipment`
- `Case`
- `TransportDocument`
- `ArrivalEvent`
- `DepartureEvent`
- `InspectionEvent`
- `IssueEvent`
- `OperationalLocation`
- `OperationCarrier`
- `CommunicationEvidence`
- `IncidentLesson`
- `RecurringPattern`

Expected predicates from this workbook:
- `relatesToShipment`
- `relatesToCase`
- `relatedToLocation`
- `relatedToCarrier`
- `documentsShipment`
- `documentsCase`
- `supportedBy`
- `exemplifiesPattern`
- `hasEvent`
- `hasDocumentRef`
- `hasEvidence`
- `hasRiskSignal`

### 12. `wiki_pointer`

Purpose:
- link ontology entities to `wiki/analyses` notes without duplicating note bodies

Grain:
- one row per pointer

Required columns:
- `wiki_pointer_id`
- `pointer_kind`
- `anchor_entity_id`
- `anchor_class`
- `wiki_vault`
- `wiki_path`
- `wiki_slug`
- `title`
- `status`
- `summary`
- `source_message_id`
- `source_thread_id`
- `evidence_level`
- `updated_at`

Pointer-kind rules:
- `guide` -> `GroupGuide`
- `lesson` -> `IncidentLesson`
- `pattern` -> `RecurringPattern`
- `evidence` -> `CommunicationEvidence`

Storage rules:
- full note body remains in `wiki/analyses`
- workbook stores pointer metadata only

### 13. `ontology_audit`

Purpose:
- store review and validation outcomes

Grain:
- one row per audit issue or review item

Required columns:
- `audit_id`
- `audit_stage`
- `entity_type`
- `entity_id`
- `severity`
- `issue_code`
- `issue_message`
- `source_sheet`
- `source_row_no`
- `resolution_status`
- `resolution_note`

## Mapping Rules From Source Columns

### Raw message identity

Source mapping:

- `no` -> `raw_email_message.message_id`
- `LinkKey` -> `raw_email_message.thread_id`
- `Month` -> `raw_email_message.month_key`
- `Subject` -> `raw_email_message.subject_raw`
- `PlainTextBody` -> `raw_email_message.body_raw`

### Duplicate semantic fields

Rules:

- `site`, `sites`, and `primary_site` must not remain as three separate semantic
  columns in the ontology workbook
- `lpo` and `lpo_numbers` must be normalized into `xref_message_lpo`
- `phase` and `stage` must be normalized into `xref_message_phase`
- `hvdc_cases` and `case_numbers` must be normalized into `xref_message_case`
- `primary_case` remains as a flag on the normalized case link rows

### Multi-value splitting

Rules:

- split comma-separated case values into multiple rows
- split comma-separated LPO values into multiple rows
- split comma-separated phase values into multiple rows
- preserve the original raw string in the raw sheet
- record parse failures in `ontology_audit`

## PlainTextBody Extraction Rules

`PlainTextBody` must not be mapped directly into ontology classes.

The required sequence is:

1. raw message preservation
2. regex and deterministic extraction into signal sheets
3. review or threshold-based filtering
4. ontology statement generation
5. optional wiki pointer linkage

### Deterministic extraction-first policy

Start with deterministic patterns for:

- shipment numbers
- case numbers
- LPO numbers
- IRN references
- invoice references
- manifest references
- gate pass references
- arrival and departure phrases
- inspection phrases
- customs and BOE phrases
- delay and damage phrases

### Confidence policy

- `high`: exact reference or explicit phrase with anchor
- `medium`: strong phrase but missing one anchor
- `low`: ambiguous phrase or incomplete anchor

Review rule:

- only `high` and approved `medium` signals can flow into
  `canonical_ontology_export`
- `low` stays in signal sheets until manual review

## Ontology Alignment Rules

The workbook must align to the shipment-centric ontology and the knowledge-layer
rules already adopted in the repository.

### Main separation rule

- email evidence is not the shipment spine
- email evidence supports shipment, case, document, event, and lesson entities

### Event rule

Time-bearing email facts become event statements first.

Examples:
- departure notice -> `DepartureEvent`
- arrival notice -> `ArrivalEvent`
- inspection request or result -> `InspectionEvent`
- customs clearance email -> `CustomsStep` or `IssueEvent`, depending on signal certainty

### Knowledge rule

Email-derived operational issues must not become guide or lesson nodes
automatically.

Required path:

- message evidence
- issue or risk signal
- reviewed grouping
- `IncidentLesson` or `RecurringPattern` creation
- pointer to `wiki/analyses`

## `wiki/analyses` Pointer Rules

### Pointer purpose

Pointers connect ontology export rows and dashboard nodes to the canonical wiki
note path.

### Pointer creation rules

- one wiki note gets one primary pointer row
- pointer rows never store full markdown body
- the pointer row must include stable vault and relative path fields

### Required pointer anchors

At least one of the following must exist:

- `anchor_entity_id`
- `source_message_id`
- `source_thread_id`

### Pointer status rules

- `draft` for extracted but unreviewed note links
- `review` for human-checked but not final
- `final` for approved canonical note links
- `superseded` when the note path remains but should no longer be used as the
  active pointer

### Dashboard compatibility rule

`wiki_pointer_id`, `wiki_vault`, and `wiki_path` must be sufficient to generate
future `analysisPath` and `analysisVault` metadata for dashboard nodes.

## Validation Gates

The workbook redesign is not complete until the following checks pass.

### Structural checks

- source workbook remains unchanged
- output workbook contains all required sheets
- each required sheet contains the required columns

### Normalization checks

- every raw email row appears once in `raw_email_message`
- every multi-value case, LPO, and phase field is split deterministically
- duplicate semantic columns are not duplicated in downstream sheets

### Signal checks

- every signal row links back to `message_id`
- confidence and review fields are populated
- ambiguous signals are not silently promoted into ontology statements

### Ontology checks

- every `canonical_ontology_export` row links back to source evidence
- `subject_id` is deterministic
- `object_kind` rules are respected
- no statement mixes literal and IRI semantics in the same row

### Pointer checks

- every pointer has a stable `wiki_path`
- no full note body is stored in the pointer sheet
- pointer rows can be joined back to ontology export rows through
  `wiki_pointer_id`

## Implementation Sequence

Recommended sequence:

1. read the source workbook and create `raw_email_message`
2. build `raw_thread_index`
3. normalize case, site, LPO, phase, and party links
4. extract deterministic document, event, and risk signals from subject and body
5. review thresholds and produce `canonical_ontology_export`
6. create `wiki_pointer`
7. create `ontology_audit`
8. validate counts and traceability

## Success Criteria

The redesign is successful when:

- the original Outlook workbook remains untouched
- the output workbook can be traced from ontology statements back to raw message
  rows
- `PlainTextBody` signals are separated from reviewed ontology statements
- `wiki/analyses` links are carried by pointers rather than duplicated content
- the resulting workbook is ready to feed a later TTL export step without
  reinterpreting raw message text from scratch
