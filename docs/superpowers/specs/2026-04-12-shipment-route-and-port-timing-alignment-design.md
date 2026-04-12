---
title: "Shipment Route And Port Timing Alignment"
type: "design-spec"
version: "1.0"
date: "2026-04-12"
author: "Codex brainstorming session"
status: "review-requested"
source_inputs:
  - "Logi ontol core doc/HVDC STATUS.xlsx"
compatibility_targets:
  - "Logi ontol core doc/AGENTS.md"
  - "Logi ontol core doc/CONSOLIDATED-00-master-ontology.md"
  - "Logi ontol core doc/CONSOLIDATED-07-port-operations.md"
  - "Logi ontol core doc/CONSOLIDATED-09-operations.md"
  - "Logi ontol core doc/ontology.md"
  - "Logi ontol core doc/docs/ontology-rules.md"
decisions:
  - "Raw Excel columns COE, POL, POD, SHIP MODE, ATD, ATA are preserved at ingest"
  - "COE is modeled as shipment-level country of export"
  - "POL and POD are modeled as port or journey-leg endpoints, not as ambiguous flat shipment strings"
  - "POD raw column must not become canonical POD because POD is already used for Proof of Delivery in the document model"
  - "SHIP MODE is modeled on JourneyLeg or Carrier transport mode, not as a bare dashboard-only label"
  - "ATD and ATA are modeled as MilestoneEvent facts using M61 and M80"
  - "Shipment-level mirrors are optional convenience fields only; source of truth stays on leg and event structures"
---

# Shipment Route And Port Timing Alignment

## Summary

This design adds six frequently used shipment-routing columns from
`HVDC STATUS.xlsx` into the ontology in a way that matches the existing master
spine instead of flattening everything into shipment-level strings.

The approved columns are:

- `COE`
- `POL`
- `POD`
- `SHIP MODE`
- `ATD`
- `ATA`

The design keeps the raw column names and values at ingest, but the canonical
ontology maps them into shipment, journey-leg, port, and milestone structures
that already exist in `CONSOLIDATED-00`.

## Problem Statement

The input workbook contains route and timing fields that are operationally
important, but the current ontology direction distinguishes:

- shipment-level identity and route pattern
- leg-level movement structure
- milestone-level timing
- document-level `POD` meaning Proof of Delivery

If all six columns are inserted as direct shipment properties, two problems
appear immediately:

1. `ATD` and `ATA` compete with the existing milestone model
2. `POD` becomes ambiguous because the repository already uses `POD` as a
   delivery document concept

## Goals

- Make `COE`, `POL`, `POD`, `SHIP MODE`, `ATD`, and `ATA` queryable from the
  graph
- Preserve compatibility with `CONSOLIDATED-00` and the repository-wide
  semantic rules
- Keep `ATD` and `ATA` aligned with the milestone and event model
- Keep `POL` and `POD` aligned with port and leg semantics
- Avoid naming collisions between `POD` as port-of-discharge and `POD` as
  Proof of Delivery

## Non-Goals

- No redesign of the full shipment-centric ontology
- No attempt to infer missing legs from these fields alone
- No replacement of `ShipmentRoutingPattern`, `JourneyLeg`, or
  `MilestoneEvent`
- No use of these columns to reintroduce route-wide Flow Code semantics

## Source Column Mapping

## Raw Ingest Layer

At ingest time, keep the original workbook columns visible as source evidence:

| Excel column | Raw normalized field |
| --- | --- |
| `COE` | `country_of_export` |
| `POL` | `port_of_loading` |
| `POD` | `port_of_discharge` |
| `SHIP MODE` | `ship_mode` |
| `ATD` | `atd` |
| `ATA` | `ata` |

This matches the existing mapping intent already visible in
`ontology.md` and `docs/ontology-rules.md`.

## Canonical Ontology Ownership

### 1. `COE`

`COE` should become a shipment-level export-origin fact.

Recommended canonical property:

- `Shipment.countryOfExport`

Reason:

- `COE` is country-level, not a timed event
- it belongs naturally to shipment origin context
- it does not need a separate event object

### 2. `POL`

`POL` should become the loading-port side of a journey leg.

Recommended canonical ownership:

- `JourneyLeg.originPort`
- optional denormalized mirror on shipment for search convenience:
  `Shipment.portOfLoading`

Reason:

- `POL` is a movement endpoint, not just a shipment label
- `CONSOLIDATED-07` already treats port operations and `PortCall` as first-class
  routing evidence

### 3. `POD`

The raw column `POD` means Port of Discharge, but the repository already uses
`POD` in the document domain as Proof of Delivery.

Recommended canonical ownership:

- `JourneyLeg.destinationPort`
- optional denormalized mirror on shipment:
  `Shipment.portOfDischarge`

Naming rule:

- keep `POD` only as a raw ingest alias
- do **not** expose canonical ontology properties named just `POD`

Reason:

- this avoids a semantic collision with document-layer `POD / GRN / Handover`
  in `CONSOLIDATED-00`

### 4. `SHIP MODE`

`SHIP MODE` should describe transport mode on the leg or carrier relation.

Recommended canonical ownership:

- `JourneyLeg.transportMode`
- optional supporting attribute on `Carrier.mode` when the carrier instance is
  present

Reason:

- the current master spine already recognizes carrier mode
- a mode without a leg loses traversal value

### 5. `ATD`

`ATD` should be represented through milestone or event structures, not only as
  a shipment flat field.

Recommended canonical ownership:

- `MilestoneEvent` with `milestoneCode = M61`
- `actualDt = ATD`

Optional derived mirror:

- `JourneyLeg.actualDeparture`

Reason:

- `CONSOLIDATED-00` explicitly defines `M61 = ATD`
- repository rules say time-bearing facts belong to events

### 6. `ATA`

`ATA` should follow the same rule as `ATD`.

Recommended canonical ownership:

- `MilestoneEvent` with `milestoneCode = M80`
- `actualDt = ATA`

Optional derived mirror:

- `JourneyLeg.actualArrival`

Reason:

- `CONSOLIDATED-00` explicitly defines `M80 = ATA`
- this matches the event and milestone governance already adopted in the repo

## Recommended Target Model

## Shipment

Add or map these shipment-level facts:

- `countryOfExport`
- optional `portOfLoading`
- optional `portOfDischarge`

These shipment-level mirrors are allowed only as convenience fields for search,
display, or dashboard filters. They must not become the only source of truth
for movement semantics.

## JourneyLeg

Add or populate:

- `originPort`
- `destinationPort`
- `transportMode`
- optional `actualDeparture`
- optional `actualArrival`

This is the main structural home for `POL`, `POD`, and `SHIP MODE`.

## MilestoneEvent

Add or populate:

- `M61` for `ATD`
- `M80` for `ATA`
- `actualDt`
- `location`
- `objectId`

This is the source-of-truth layer for `ATD` and `ATA`.

## Port / PortCall Evidence

Where port operations context exists, connect:

- `POL` and `POD` to `Port`
- timing and routing evidence to `PortCall`

This keeps `CONSOLIDATED-07` aligned with the shipment-centric route model.

## Query and Traversal Impact

With this design, the graph can answer queries such as:

- Which shipments exported from `FRANCE` were loaded at `Le Havre`?
- Which journey legs discharge at `Mina Zayed`?
- Which shipments with `SHIP MODE = SEA` have `M61` but no `M80`?
- Which `AGI` or `DAS` shipments have `ATA` but still lack downstream MOSB or
  site milestones?

These questions become harder or ambiguous if everything is kept only as flat
shipment strings.

## Validation Rules

Add these design-level validation expectations:

1. `POD` raw input must map to `portOfDischarge` or `destinationPort`, not to a
   Proof-of-Delivery document node
2. `ATD` must create or populate `MilestoneEvent(M61)`
3. `ATA` must create or populate `MilestoneEvent(M80)`
4. `SHIP MODE` must map to a controlled transport mode vocabulary
5. If shipment-level mirrors exist for `POL`, `POD`, `ATD`, `ATA`, they are
   derived summaries, not semantic replacements

## Recommended Implementation Direction

The recommended direction is:

1. Preserve raw fields from `HVDC STATUS.xlsx`
2. Map `COE` onto shipment
3. Map `POL`, `POD`, `SHIP MODE` onto `JourneyLeg`
4. Map `ATD`, `ATA` onto milestone events `M61`, `M80`
5. Optionally mirror selected route fields back onto shipment for dashboard and
   search convenience

This is the smallest change that still respects the current ontology rules.

## Acceptance Criteria

1. The design does not collapse `ATD` and `ATA` into shipment-only flat fields
2. The design does not create canonical ontology properties named just `POD`
   for port-of-discharge
3. `COE` is represented as shipment export-origin data
4. `POL` and `POD` are represented in port or leg semantics
5. `SHIP MODE` is represented in transport or carrier semantics
6. `ATD` and `ATA` are represented through `MilestoneEvent`
7. The result remains compatible with `CONSOLIDATED-00`, `07`, and `09`
