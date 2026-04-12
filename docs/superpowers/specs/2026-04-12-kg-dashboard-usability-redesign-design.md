---
title: "KG Dashboard Usability Redesign"
type: "design-spec"
version: "1.0"
date: "2026-04-12"
author: "Codex research and design session"
status: "review-requested"
related_documents:
  - "docs/superpowers/specs/2026-04-12-kg-dashboard-graph-visibility-alignment-design.md"
  - "kg-dashboard/plan-2026-04-12-ui-rule-alignment.md"
source_files:
  - "kg-dashboard/src/App.tsx"
  - "kg-dashboard/src/components/GraphSidebar.tsx"
  - "kg-dashboard/src/components/GraphView.tsx"
  - "kg-dashboard/src/components/NodeInspector.tsx"
  - "kg-dashboard/src/utils/graph-model.ts"
external_benchmarks_verified_on:
  - "2026-04-12"
external_benchmark_references:
  - "https://github.com/aws/graph-explorer"
  - "https://github.com/sparna-git/Sparnatural"
  - "https://github.com/opensemanticsearch/open-semantic-visual-graph-explorer"
  - "https://github.com/zazuko/blueprint"
  - "https://medium.com/@visrow/a2ui-protocol-tutorial-building-dynamic-agentic-knowledge-graphs-for-real-time-fraud-investigation-c408b08ddb3c"
  - "https://medium.com/@varun.pratap.bhardwaj/superlocalmemory-local-first-ai-memory-for-claude-cursor-and-16-tools-ab01589ed286"
decisions:
  - "The dashboard remains graph-first, but becomes an investigation surface rather than a passive graph viewer"
  - "Structured search is first-class and must expose route and timing fields directly"
  - "Graph, table, timeline, and schema views are companion views over the same visible slice"
  - "Evidence drill-down is a first-class workflow for both node and edge inspection"
  - "Static JSON data remains the primary runtime source in this redesign round"
  - "URL state persistence is required so users can return to the same investigation context"
---

# KG Dashboard Usability Redesign

## Summary

This design turns `kg-dashboard` from a graph viewer into a workflow-friendly
investigation surface for logistics users.

Today the dashboard can render the graph, switch slices, and inspect node
metadata. However, key operational tasks still require too much mental work:

- route and timing search intent is hidden inside free-text search
- time-based shipment reading is hard because the graph is the only main view
- evidence is node-biased and not centered on relationships
- users cannot easily preserve or share the exact context they are viewing

The approved redesign keeps the existing graph model and static JSON data
contract, but adds a usability layer around it:

1. structured search for route and timing fields
2. synchronized companion views for graph, table, timeline, and schema
3. inspector tabs for node, edge, evidence, and related context
4. persistent investigation state in the URL

This spec covers user-facing behavior only. It does not define code structure
or implementation sequencing.

## Problem Statement

The current layout is effective for technical exploration but weak for
day-to-day operational use.

Observed limits in the current application state:

- the main entry point is a generic search box with no typed query guidance
- `summary`, `issues`, `search`, and `ego` are available, but users still need
  to infer where route, milestone, and evidence details live
- the inspector is primarily node metadata and does not treat edges or evidence
  as first-class investigation objects
- there is no table view for sorting visible records
- there is no timeline view for `ATD`, `ATA`, or related milestone reading
- there is no schema summary that explains which node and edge types are
  present in the current slice
- the dashboard state is not treated as a reusable investigation context

The practical outcome is that the user can find a node, but still needs extra
steps to answer common logistics questions such as:

- Which shipments loaded at a specific port are still open?
- Which journeys have `ATD` but not `ATA`?
- Which visible issue is supported by which lesson or analysis note?
- Why is this node visible in the current slice?

## Goals

- Reduce the number of actions needed to find shipments by `COE`, `POL`, `POD`,
  `SHIP MODE`, `ATD`, and `ATA`
- Make graph context and time context readable together
- Make evidence and relationship inspection explicit rather than implicit
- Preserve the current summary-first rendering posture
- Keep the redesign compatible with the current static export flow and
  `kg-dashboard/public/data/*.json`

## Non-Goals

- No full replacement of Cytoscape or the current graph slice builder
- No move from static JSON to live backend queries in this round
- No multi-user collaboration workflow in this round
- No ontology or exporter redesign beyond what is needed to surface existing
  data better
- No introduction of a landing page or marketing shell

## Benchmark Principles

The redesign is grounded in the following external patterns verified on
`2026-04-12`:

- GitHub `aws/graph-explorer`: graph exploration works better when graph view,
  data exploration, and schema exploration are treated as separate but linked
  surfaces
- GitHub `Sparnatural`: typed widgets such as autocomplete, date range,
  numeric, and boolean filters reduce ambiguity in graph search
- GitHub `open-semantic-visual-graph-explorer`: edges should lead to document
  or evidence drill-down, not only visual relations
- GitHub `zazuko/blueprint`: visibility and detail-panel navigation should be
  deliberate and configurable
- Medium `A2UI Protocol Tutorial`, published `2026-01-15`: investigation
  interfaces benefit from progressive disclosure, persistent surfaces, and
  preserving zoom/pan state during updates
- Medium `SuperLocalMemory`, published `2026-02-12`: graph explorer and
  timeline become more useful when they are companion views over the same data

These are benchmark inputs, not adoption requirements.

## User Scenarios & Testing

### US-001 Route-first search

**User story**

As a logistics operator, I want to search by explicit route fields so that I do
not have to guess whether `POL`, `POD`, or `COE` are searchable.

**Acceptance scenario**

- Given the dashboard is loaded with the current graph dataset
- When the user opens the search controls
- Then the UI exposes field-aware search entry points for `COE`, `POL`, `POD`,
  `SHIP MODE`, `ATD`, and `ATA`
- And the result list shows which field matched for each result

**Test notes**

- Manual browser test
- UI component test for search controls
- graph-model test for field-aware matching and ranking

### US-002 Time-based shipment reading

**User story**

As a shipment coordinator, I want to see visible shipments in a timeline view
so that I can quickly identify missing arrivals, late movements, and open
journeys.

**Acceptance scenario**

- Given the current visible slice contains shipment and milestone data
- When the user opens the timeline companion view
- Then the UI shows shipment rows with available `ATD`, `ATA`, and related
  timing markers
- And selecting a row syncs selection back to the graph and inspector

**Test notes**

- Manual browser test
- component test for timeline rendering with partial dates

### US-003 Evidence-centered inspection

**User story**

As an analyst, I want to inspect the evidence behind a visible node or edge so
that I can understand why it is on screen and which source note supports it.

**Acceptance scenario**

- Given a node or edge with linked analysis or metadata evidence exists
- When the user selects that node or edge
- Then the inspector exposes a dedicated evidence view
- And the evidence view shows linked note path or a clear no-evidence state

**Test notes**

- Manual browser test
- component test for inspector tabs and evidence state

### US-004 Reopen the same investigation context

**User story**

As a returning user, I want the current search, slice, and selection state to
survive a reload or shared link so that I can resume the same investigation
without rebuilding context.

**Acceptance scenario**

- Given the user has a current search term, view mode, and selected node
- When the page reloads from the encoded URL
- Then the dashboard restores the same visible context
- And the graph, companion view, and inspector stay synchronized

**Test notes**

- Manual browser test
- URL state unit test

## Requirements

### Functional Requirements

- **FR-001** The dashboard must keep the current three-pane base layout:
  left control rail, center graph canvas, right inspector.

- **FR-002** The dashboard must add a companion view switcher that exposes
  `Graph`, `Table`, `Timeline`, and `Schema` over the same current visible
  slice.

- **FR-003** The primary search experience must support field-aware entry for
  `COE`, `POL`, `POD`, `SHIP MODE`, `ATD`, and `ATA` in addition to free-text
  search.

- **FR-004** Search results must show the matched field or match reason for
  each quick result item.

- **FR-005** The dashboard must preserve the existing slice modes
  `summary`, `issues`, `search`, and `ego`.

- **FR-006** Selecting a search result must focus the graph and synchronize the
  selection into the inspector and active companion view.

- **FR-007** The `Table` view must show the currently visible slice in sortable
  row form with at least label, type, key route fields, and timing fields when
  present.

- **FR-008** The `Timeline` view must show currently visible shipment timing in
  a form that makes missing `ATA`, available `ATD`, and comparable milestone
  timing easy to scan.

- **FR-009** The `Schema` view must summarize the current slice by node type,
  edge type, and counts.

- **FR-010** The inspector must support at least four tabs:
  `Node`, `Edge`, `Evidence`, and `Related`.

- **FR-011** Edge selection must be a first-class interaction and must display
  source, target, label, and any available supporting evidence.

- **FR-012** When evidence metadata exists, the inspector must expose the
  linked analysis note or source path. When it does not exist, the UI must show
  a clear empty state instead of hiding the section silently.

- **FR-013** The dashboard must explain why a node is visible in the current
  slice through either relation breadcrumbs, visible path summary, or match
  reason text.

- **FR-014** The dashboard must persist current search, active view, active
  companion view, and selected node in the URL so the context can be restored.

- **FR-015** Empty, loading, and error states must remain readable and specific
  to the active surface rather than falling back to a generic graph-only
  message.

### Non-Functional Requirements

- **NFR-001** The default entry state must remain progressive-disclosure-first.
  The dashboard must not render the full graph as the default first screen.

- **NFR-002** On the current static dataset in `kg-dashboard/public/data`,
  visible-slice switching must feel immediate to the user and should complete
  within `500 ms` on a standard local development machine for common slice
  changes that do not rebuild the whole dataset.

- **NFR-003** Search interactions should show updated quick results within
  `300 ms` after the debounced or deferred query value changes on the current
  static dataset.

- **NFR-004** The redesign must continue to satisfy the repository UI rules:
  no hero, no nested cards, no decorative frame around the main graph, radius
  at or below `8px`, and no layout shift caused by dynamic content.

- **NFR-005** Companion views must stay synchronized with the same source slice
  and selection state. A user must not be able to inspect stale data in table,
  timeline, or schema after the graph has changed.

- **NFR-006** URL state restore must not require network calls beyond the
  existing static asset loading path.

## Assumptions & Dependencies

- The redesign continues to read from static JSON exports under
  `kg-dashboard/public/data`.
- Route and timing fields such as `countryOfExport`, `portOfLoading`,
  `portOfDischarge`, `shipMode`, `actualDeparture`, and `actualArrival` are
  already present or will remain present in dashboard node data.
- Existing graph slice helpers in `kg-dashboard/src/utils/graph-model.ts`
  remain the source of truth for visible-slice construction.
- Linked analysis behavior remains dependent on node metadata such as
  `analysisVault` and `analysisPath`.
- Cytoscape remains the graph rendering engine in this round.
- External benchmark references are guidance for UX direction only; they do not
  require adopting their backend, query language, or component stack.

## Success Criteria

- **SC-001** A user can start from the default screen and reach a shipment
  result using one of `COE`, `POL`, `POD`, `SHIP MODE`, `ATD`, or `ATA`
  without guessing field names from hidden metadata.

- **SC-002** In usability review, each quick result clearly shows why it
  matched, including the matched field or equivalent reason label.

- **SC-003** `Graph`, `Table`, `Timeline`, and `Schema` remain synchronized for
  the same current visible slice and selected entity across manual verification.

- **SC-004** A selected node or edge with evidence metadata exposes at least one
  visible evidence path or linked note action in the inspector.

- **SC-005** Reloading a copied URL restores search term, view mode, selected
  node, and companion view in manual verification.

- **SC-006** The redesigned surfaces pass the existing `kg-dashboard` build,
  lint, and UI rule test gates plus new tests added for structured search,
  synchronized views, and URL state restore.

## Reviewer Checklist

- Does the scope stay inside usability redesign rather than backend redesign?
- Are route and timing fields explicit enough for non-technical users?
- Is the evidence workflow strong enough for issue and lesson investigation?
- Are `Table`, `Timeline`, and `Schema` justified as linked surfaces rather
  than separate dashboards?
- Are the success criteria measurable enough to approve implementation planning?

## Clarifications Log

- `2026-04-12`: Interpreted "user convenience" as operator and analyst workflow
  efficiency, not executive reporting.
- `2026-04-12`: Interpreted "GitHub, Medium" benchmark request as external UX
  pattern grounding, not direct feature copying.

