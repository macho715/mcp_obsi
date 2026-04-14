---
title: "OUTLOOK Email Ontology Workbook Redesign Spec"
type: "contract-spec"
version: "1.0"
date: "2026-04-12"
status: "approved"
source_plan: "docs/superpowers/plans/2026-04-12-outlook-email-ontology-workbook-redesign-implementation.md"
related_design:
  - "docs/superpowers/specs/2026-04-12-outlook-email-ontology-workbook-redesign-design.md"
---

# OUTLOOK Email Ontology Workbook Redesign Spec

## Summary

This spec defines the contract for rebuilding the Outlook-derived workbook into
an ontology-ready and lessons-ready workbook without mutating the source Excel
file.

The approved direction is option C:

- keep the existing `raw/xref/signal` layers
- add `mail_identifier_extract`
- add `mail_message_classification`
- add `review_gates`
- add `lesson_fact_table`

The resulting workbook must support both downstream ontology export and
Lessons Learned analysis. `canonical_ontology_export` remains part of the
output, but it is no longer the primary artifact. It becomes a downstream-only
sheet derived after identifier extraction, classification, and review.

## User Scenarios & Testing

### US-001 Source workbook remains unchanged

Given the source workbook `OUTLOOK_HVDC_ALL_20250920260.xlsx`  
When the pipeline generates the redesigned workbook  
Then the source workbook bytes must remain unchanged  
And the output workbook must be written to a separate path.

### US-002 Message-level identifier extraction

Given a mail row that contains case, LPO, PO, IRN, and site references  
When the pipeline runs identifier extraction  
Then `mail_identifier_extract` must contain exactly one row for that message  
And that row must include a primary identifier, identifier count, and serialized
identifier lists.

### US-003 Single message classification

Given a mail row with extracted identifiers and evidence  
When the classification step runs  
Then exactly one `message_type` must be assigned  
And the classification result must carry an ontology target class, lesson
bucket, and root cause bucket.

### US-004 Review gate evaluation

Given a mail classified as offshore-related for `AGI` or `DAS`  
When no MOSB continuity evidence is present  
Then `review_gates` must mark the row as requiring human review  
And the row must include a stable `review_reason` code.

### US-005 Candidate stage and milestone control

Given a mail with explicit event evidence such as `BOE cleared` or
`site arrived`  
When review gates run  
Then a `candidate_stage` and, where justified, a `candidate_milestone`
may be assigned  
And milestone assignment must not occur for commercial-only or noise messages.

### US-006 Lessons Learned fact aggregation

Given classified rows and review outputs  
When lesson aggregation runs  
Then `lesson_fact_table` must group facts into `lesson_bucket` and
`root_cause_bucket`  
And it must calculate `impact_level`, `evidence_count`, and
`recommended_action`.

### US-007 Canonical export is downstream-only

Given document, event, and risk evidence  
When ontology export runs  
Then `canonical_ontology_export` must be derived from approved upstream rows  
And it must not be generated directly from raw signals alone.

### US-008 Flow Code boundary

Given any mail row in the source workbook  
When the pipeline runs  
Then it must not generate `confirmedFlowCode`, `assignedFlowCode`, or
`extractedFlowCode`  
And Flow Code must remain outside this mail-based pipeline.

### US-009 Lessons report remains optional

Given a complete lesson fact table  
When the output workbook is generated  
Then `lessons_learned_report` may be included as a final optional summary sheet  
And its absence must not block the validity of the workbook.

## Requirements

### Functional Requirements

- `FR-001` The pipeline must read `전체_데이터` as the primary source sheet.
- `FR-002` The pipeline must preserve the current base layers:
  `raw_email_message`, `raw_thread_index`, and `xref_*`.
- `FR-003` The pipeline must preserve evidence-first extraction through
  `signal_document`, `signal_event`, and `signal_risk`.
- `FR-004` The pipeline must add `mail_identifier_extract` as a message-level
  sheet with one row per message.
- `FR-005` `mail_identifier_extract` must include:
  `primary_identifier_type`, `primary_identifier_value`,
  `primary_identifier_confidence`, `mixed_identifier_flag`,
  `identifier_count`, and serialized identifier lists for cases, LPOs, POs,
  transport documents, customs documents, invoices, vessels, vehicles, drivers,
  and sites.
- `FR-006` The pipeline must add `mail_message_classification`.
- `FR-007` `mail_message_classification` must assign exactly one `message_type`
  per message.
- `FR-008` Supported `message_type` values must include:
  `permit_access`, `customs_compliance`, `marine_offshore`,
  `site_receiving`, `movement_notice`, `cost_invoice`,
  `procurement_vendor`, `exception_risk`, and `general_noise`.
- `FR-009` Classification must use identifiers, evidence hits, and site context.
  It must not rely on body keywords alone.
- `FR-010` The pipeline must add `review_gates`.
- `FR-011` `review_gates` must include:
  `candidate_stage`, `candidate_milestone`, `requires_human_review`,
  `review_severity`, `review_reason`, and `review_gate_id`.
- `FR-012` `review_reason` values must be stable codes, not ad hoc narrative
  text.
- `FR-013` The pipeline must add `lesson_fact_table`.
- `FR-014` `lesson_fact_table` must include:
  `message_type`, `lesson_bucket`, `root_cause_bucket`, `primary_site`,
  `primary_case`, `impact_level`, `evidence_count`, `lesson_statement`,
  `recommended_action`, and `ontology_anchor`.
- `FR-015` The pipeline must preserve `canonical_ontology_export`.
- `FR-016` `canonical_ontology_export` must be downstream-only and must be
  derived after identifier extraction, classification, and review.
- `FR-017` The pipeline may add `lessons_learned_report` as an optional
  workbook summary sheet.
- `FR-018` Workbook output must be written in a stable sheet order consistent
  with the approved option C flow.

### Non-Functional Requirements

- `NFR-001` The source workbook must remain immutable.
- `NFR-002` The pipeline must remain evidence-first and must not treat mail
  bodies as direct operational truth.
- `NFR-003` Identifier extraction must happen before message classification.
- `NFR-004` Candidate milestones must only be created from explicit event
  evidence.
- `NFR-005` The pipeline must not generate Flow Code fields.
- `NFR-006` The output workbook must keep list-valued fields in a stable
  serialized form suitable for Excel storage and downstream parsing.
- `NFR-007` Review gates for AGI/DAS offshore continuity must be explicit and
  testable.

## Assumptions & Dependencies

### Assumptions

- `Assumption:` The current `raw/xref/signal` implementation is valid enough to
  be preserved as the base layer.
- `Assumption:` `message_id` and `thread_id` are stable anchors for downstream
  joins.
- `Assumption:` `mail_identifier_extract` should be one row per message, not one
  row per identifier hit.
- `Assumption:` `lessons_learned_report` is optional for the first delivery.

### Dependencies

- The source workbook includes `전체_데이터` with the columns already used by
  the current pipeline.
- Existing modules remain available:
  `outlook_email_workbook_contract`,
  `outlook_email_raw_normalizer`,
  `outlook_email_signal_extractor`,
  `outlook_email_ontology_mapper`,
  `outlook_email_wiki_pointer_builder`,
  and the workbook build script.
- The lesson rules described in:
  [Lessons Learned용 Excel 정보.md](C:/Users/jichu/.config/superpowers/worktrees/mcp_obsidian/outlook-email-ontology-workbook/Lessons%20Learned%EC%9A%A9%20Excel%20%EC%A0%95%EB%B3%B4.md),
  [Lessons Learned용 Excel 정보1.md](C:/Users/jichu/.config/superpowers/worktrees/mcp_obsidian/outlook-email-ontology-workbook/Lessons%20Learned%EC%9A%A9%20Excel%20%EC%A0%95%EB%B3%B41.md),
  and
  [Lessons Learned용 Excel 정보2.md](C:/Users/jichu/.config/superpowers/worktrees/mcp_obsidian/outlook-email-ontology-workbook/Lessons%20Learned%EC%9A%A9%20Excel%20%EC%A0%95%EB%B3%B42.md)
  remain the source of truth for lesson-oriented behavior.

## Open Questions

None at this stage.

## Clarifications Log

- `2026-04-12` Option C was chosen:
  keep the current `raw/xref/signal` stack and add four new stages:
  `mail_identifier_extract`, `mail_message_classification`, `review_gates`,
  and `lesson_fact_table`.
- `2026-04-12` `canonical_ontology_export` remains in scope but is no longer
  the primary output artifact.
- `2026-04-12` Flow Code generation remains out of scope for this mail-based
  pipeline.
- `2026-04-12` The first implementation slice keeps rules in Python modules.
  External rule files such as `regex_rules.yaml`, `classification_rules.yaml`,
  and `review_gates.yaml` are deferred to a follow-up.
- `2026-04-12` `ontology_mapping_queue` is not a required persisted workbook
  sheet in the first delivery. The first delivery may keep this stage internal
  as long as downstream-only `canonical_ontology_export` behavior is preserved.
- `2026-04-12` `lessons_learned_report` is optional in the first delivery.
  `lesson_fact_table` is sufficient for approval of the first slice.

## Success Criteria

- `SC-001` The output workbook contains the preserved base sheets plus the four
  new option C sheets.
- `SC-002` Every message row produces at most one `mail_identifier_extract` row.
- `SC-003` Every message row produces exactly one `message_type`.
- `SC-004` Review gate results include stable codes for review reasons.
- `SC-005` `lesson_fact_table` contains lesson buckets, root cause buckets,
  impact levels, and recommended actions.
- `SC-006` `canonical_ontology_export` can be traced back to approved upstream
  rows rather than raw signals alone.
- `SC-007` The source workbook remains byte-identical before and after a build.
- `SC-008` No Flow Code fields are generated anywhere in the output workbook.
