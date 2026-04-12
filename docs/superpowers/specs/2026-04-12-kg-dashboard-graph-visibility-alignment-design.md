---
title: "KG Dashboard Graph Visibility Alignment"
type: "design-spec"
version: "1.0"
date: "2026-04-12"
author: "Codex brainstorming session"
status: "implemented-and-verified"
related_documents:
  - "kg-dashboard/plan-2026-04-12-graph-visibility-alignment.md"
source_files:
  - "scripts/build_dashboard_graph_data.py"
  - "tests/test_dashboard_graph_export.py"
  - "kg-dashboard/src/utils/graph-model.ts"
  - "kg-dashboard/src/utils/graph-model.test.ts"
  - "kg-dashboard/src/components/NodeInspector.tsx"
decisions:
  - "External analyses directory is primary: C:/Users/jichu/Downloads/valut/wiki/analyses"
  - "Repo-local vault/wiki/analyses is fallback only"
  - "Exporter contract tests and UI slice tests are separated by responsibility"
  - "Summary and issues views show issue-context lessons, not every lesson node"
  - "Ego view shows lessons directly connected to the selected node"
  - "Issue and lesson nodes carry explicit analysis note metadata for inspector links"
  - "kg-dashboard/src/types/graph.ts stays unchanged in this round"
---

# KG Dashboard Graph Visibility Alignment

## Summary

This design fixes the mismatch between regenerated graph data and what the
dashboard actually exposes on screen.

The current system already exports `IncidentLesson` nodes and
`relatedToLesson` edges, but the default dashboard slices remove most of them
before rendering. At the same time, the exporter still defaults to the
repo-local `vault/wiki/analyses` path, so the approved external analyses corpus
is not used unless passed manually.

The design keeps Option B, but tightens it into two separate responsibilities:

1. `scripts/build_dashboard_graph_data.py` must resolve the analyses source
   deterministically and report the chosen path in audit output.
2. `kg-dashboard/src/utils/graph-model.ts` must expose lessons through
   issue-context slices and selected-node slices without expanding every lesson
   node into the default view.

## Problem Statement

### Current mismatch

1. The exporter reads from `vault/wiki/analyses` by default.
2. The approved corpus is `C:\Users\jichu\Downloads\valut\wiki\analyses`.
3. The dashboard summary and issues views keep only `LogisticsIssue`,
   `Hub`, `Site`, and `Warehouse`.
4. `IncidentLesson` nodes are currently anchored to shipment, location,
   carrier, or pattern nodes via `relatedToLesson`.
5. `NodeInspector` only opens linked notes for `LogisticsIssue`.

### User-visible outcome

- Data can regenerate correctly while the default dashboard still looks almost
  unchanged.
- A lesson node can exist in JSON but not appear in summary or issues view.
- Even if a lesson node becomes visible, it is not yet guaranteed to open its
  linked analysis note.

## Goals

- Use the external analyses directory first and fall back to repo-local
  analyses only when the external path is absent.
- Preserve the existing nodes/edges consumer contract in
  `kg-dashboard/public/data/*.json`.
- Make lesson visibility deterministic in `summary`, `issues`, and `ego`
  views.
- Keep the default graph readable by showing only issue-context lessons rather
  than all lesson nodes.
- Make issue and lesson nodes open their linked analysis notes in the correct
  Obsidian vault.
- Split verification so exporter behavior is tested in Python and view-slice
  behavior is tested in TypeScript.

## Non-Goals

- No redesign of the dashboard layout, sidebar structure, or visual styling.
- No change to the canonical TTL schema or the dashboard JSON contract shape.
- No default exposure of `Guide`, `Rule`, or `RecurringPattern` nodes in the
  main graph view.
- No change to `kg-dashboard/src/types/graph.ts` unless a later bug proves it
  necessary.

## Approved Design

## 1. Analyses Source Selection

### Candidate order

The exporter must resolve analyses input in this order:

1. `C:\Users\jichu\Downloads\valut\wiki\analyses`
2. `vault/wiki/analyses`

### Selection rule

- Use the first existing directory in that order.
- If neither directory exists, continue without crashing and load zero analysis
  notes.

### Required audit fields

`runtime/audits/hvdc_ttl_source_audit.json` must preserve the current fields
and add:

- `selected_analyses_dir`: absolute path string or `null`
- `analyses_dir_fallback_used`: boolean

This gives the user one clear answer to "which corpus did the exporter
actually use?"

## 2. Exporter Responsibility Boundary

The exporter is responsible for:

- choosing the analyses source directory
- reading notes
- building `IncidentLesson` nodes and `relatedToLesson` edges
- attaching analysis note metadata needed by the inspector
- writing audit evidence about source selection and note counts

The exporter is not responsible for:

- deciding which lesson nodes remain visible in dashboard slices
- deciding whether a lesson should appear in summary or issues view

That visibility logic belongs in the TypeScript graph model.

## 3. Lesson Visibility Model

### Current graph reality

`IncidentLesson` nodes are not currently attached directly to
`LogisticsIssue` nodes. They are attached to shipment, location, carrier, or
pattern anchors through `relatedToLesson`.

Because of that, the dashboard must expose lessons through anchor context, not
by assuming a direct `LogisticsIssue -> IncidentLesson` edge.

### Summary view

`summary` must keep:

- all `LogisticsIssue` nodes
- all `Hub`, `Site`, and `Warehouse` nodes already used by the current summary
- only `IncidentLesson` nodes whose anchor node is:
  - visible in the summary slice, and
  - connected to at least one visible `LogisticsIssue`

This creates an issue-context lesson layer without turning the default screen
into a full lesson dump.

### Issues view

`issues` must keep the same issue-context lesson rule as `summary`, but still
behave as an issue-centered slice.

The view should preserve issue-to-anchor and anchor-to-lesson relationships
that belong to the issue context. It should not expand unrelated lesson nodes
just because they exist elsewhere in the graph.

### Ego view

`ego` must keep lessons directly connected to the selected node.

Examples:

- selected shipment -> show shipment-attached lessons
- selected site or warehouse -> show location-attached lessons
- selected carrier or pattern -> show directly attached lessons

No special issue-context rule is needed here because `ego` is already a
selected-node slice.

### Search view

`search` already expands through adjacency and does not need a new
lesson-specific rule in this round.

## 4. Inspector Behavior

`NodeInspector` must open linked analyses for both:

- `LogisticsIssue`
- `IncidentLesson`

### Metadata rule

The exporter must attach note metadata to issue and lesson nodes that originate
from analysis markdown files.

Required fields on node data:

- `analysisPath`: path to the markdown file relative to the selected Obsidian
  vault root, for example `wiki/analyses/delay-at-agi.md`
- `analysisVault`: Obsidian vault name derived from the selected analyses root

The vault name is resolved by walking upward from the selected analyses
directory until a directory containing `.obsidian` is found. The vault name is
the final directory name of that root.

### Inspector link rule

- `NodeInspector` must use `analysisVault` and `analysisPath` when they are
  present.
- `NodeInspector` must not hard-code `vault=mcp_obsidian` for notes sourced
  from the external analyses vault.
- If analysis metadata is absent, the inspector may fall back to the current
  metadata-only behavior.

If a selected node is neither issue nor lesson, the inspector keeps its current
behavior and shows metadata only.

## 5. Testing Boundary

### Python tests

`tests/test_dashboard_graph_export.py` must verify:

- external analyses path wins when present
- repo-local path is used when external is absent
- `selected_analyses_dir` and `analyses_dir_fallback_used` are written
  correctly
- issue and lesson nodes sourced from analyses carry correct `analysisPath` and
  `analysisVault` metadata
- lesson nodes and `relatedToLesson` edges still export correctly
- legacy dashboard id alignment still holds

### TypeScript tests

`kg-dashboard/src/utils/graph-model.test.ts` must verify:

- `summary` keeps issue-context lessons only
- `issues` keeps issue-context lessons only
- `ego` keeps lessons directly attached to the selected node
- unrelated lessons stay hidden from these slices

### Manual verification

After implementation:

- regenerate `kg-dashboard/public/data/nodes.json`
- regenerate `kg-dashboard/public/data/edges.json`
- regenerate `runtime/audits/hvdc_ttl_source_audit.json`
- regenerate `runtime/audits/hvdc_ttl_mapping_audit.json`
- open the local dashboard
- confirm that summary and issues views now expose lesson changes in issue
  context
- confirm that clicking an issue node or lesson node opens the linked analysis
  note in the correct Obsidian vault

## Error Handling

- Missing external analyses directory is not an error if repo-local fallback
  exists.
- Missing both analyses directories is not fatal; exporter completes with
  `loaded_notes = 0` and `selected_analyses_dir = null`.
- Unmapped lessons remain part of `unmapped_lessons` audit output and must not
  crash the export.

## Acceptance Criteria

1. The exporter chooses analyses input deterministically and records the chosen
   directory in source audit output.
2. The dashboard JSON export still contains valid `IncidentLesson` nodes and
   `relatedToLesson` edges.
3. Issue and lesson nodes sourced from analyses carry correct vault/path
   metadata for linked note navigation.
4. Summary and issues views expose only issue-context lessons.
5. Ego view exposes lessons directly connected to the selected node.
6. Issue and lesson nodes can open their linked analysis notes from the
   inspector.
7. No change is required to `kg-dashboard/src/types/graph.ts` in this round.

## Implementation Update (2026-04-12)

The implementation is now present in the current workspace and the dashboard
contract is verified end to end.

### Actual files involved

- `scripts/build_dashboard_graph_data.py`
  - exporter entrypoint and audit writer
  - `ttl_path=None` now remains the default CLI path
  - malformed YAML frontmatter no longer aborts analysis note parsing
  - external analyses selection now drives the export path
- `kg-dashboard/src/utils/graph-model.ts`
  - projection and visibility logic for summary, issues, and ego views
  - analysis metadata is preserved through the projection layer
  - issue-context lesson slicing is implemented here
- `kg-dashboard/src/components/NodeInspector.tsx`
  - metadata-based Obsidian link construction for issue and lesson nodes
- `tests/test_dashboard_graph_export.py`
  - exporter contract coverage for source selection, metadata, and audits
- `kg-dashboard/src/utils/graph-model.test.ts`
  - slice visibility regression coverage
- `kg-dashboard/src/components/NodeInspector.test.tsx`
  - metadata link regression coverage

### Accepted implementation notes

- The exporter CLI now defaults to `ttl_path=None`, which keeps the dashboard
  export path aligned with the current workspace contract.
- Analysis note parsing is resilient to malformed YAML frontmatter, so a bad
  note no longer crashes the export pass.
- The projection layer preserves `analysisPath` and `analysisVault` so the UI
  can open the correct Obsidian note without reconstructing that context.
- Issue-context lesson slicing is implemented and verified. Summary and issues
  views now keep the relevant lesson nodes for visible issue anchors instead of
  exposing every lesson node.
- `NodeInspector` now uses exported metadata for Obsidian links. This was
  verified for both issue nodes and lesson nodes.

### Verification evidence

- Python contract test run: `5 passed`
- Dashboard test run: `18 passed`
- Lint/build: passed
- Browser preview: `http://127.0.0.1:4175` loaded successfully
- Playwright observation: switching from Summary to Issues reduced visible node
  count from `227` to `216`
- Source audit observation: external analyses path was selected and
  `loaded_notes = 115`
- Exported metadata counts:
  - `113` issue nodes with metadata
  - `102` lesson nodes with metadata

### Resulting state

The dashboard data now reflects the external analyses corpus, the graph model
shows only the intended lesson context in the main slices, and the inspector
opens the correct linked note for both issue and lesson nodes.
