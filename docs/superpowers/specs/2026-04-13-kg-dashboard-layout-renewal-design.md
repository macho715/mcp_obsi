---
title: "KG Dashboard Layout Renewal"
type: "design-spec"
version: "1.0"
date: "2026-04-13"
author: "Codex brainstorming session"
status: "review-requested"
related_documents:
  - "docs/superpowers/specs/2026-04-12-kg-dashboard-usability-redesign-design.md"
  - "docs/superpowers/specs/2026-04-12-kg-dashboard-graph-visibility-alignment-design.md"
source_files:
  - "kg-dashboard/src/App.tsx"
  - "kg-dashboard/src/App.css"
  - "kg-dashboard/src/components/GraphSidebar.tsx"
  - "kg-dashboard/src/components/NodeInspector.tsx"
  - "kg-dashboard/src/components/GraphView.tsx"
  - "kg-dashboard/src/components/ui-rule-alignment.test.tsx"
decisions:
  - "The layout remains graph-first and keeps a three-pane desktop shell"
  - "Desktop side panels stay visible but become slim rails"
  - "The large hero-like top section is replaced with a thin status toolbar"
  - "Panel content is reordered by action priority and uses internal scrolling"
  - "Low-frequency sections move into collapsed sections before layout width is increased"
  - "Tablet and mobile layouts drop fixed three-column behavior in favor of graph-first stacking"
  - "This round changes layout and information hierarchy only, not graph logic or data contracts"
---

# KG Dashboard Layout Renewal

## Summary

This design renews the `kg-dashboard` layout so the graph becomes the dominant
surface again.

The current dashboard spends too much space on wide side panels and a tall top
introduction area. As a result, the first screen shows a relatively small graph
canvas even though graph exploration is the main task.

The approved direction keeps the existing application structure, but changes the
visual hierarchy:

1. desktop stays three-column, but the side panels shrink into slim rails
2. the tall top section becomes a thin status toolbar
3. the graph canvas becomes the main visual region on first load
4. panel content is prioritized, folded, and internally scrollable
5. tablet and mobile layouts stop pretending to be desktop and switch to
   graph-first stacked behavior

This design is layout-only. It does not redefine graph slicing, provenance
logic, search ranking, or the JSON data contract.

## Problem Statement

The current layout creates three user-facing problems:

1. The top section is too tall.
   The large title and summary area pushes the graph down and makes the first
   screen feel empty.

2. The side panels are too wide for their importance.
   Search and inspector content take a large percentage of the viewport even
   when the user is not actively reading all of it.

3. Information density is not prioritized.
   High-frequency controls and low-frequency details compete for the same space,
   so the screen feels visually heavy before the user even starts investigating.

The practical result is that the graph, which should be the centerpiece, looks
secondary.

## Goals

- Make the graph canvas the largest region on desktop first load
- Keep desktop search and inspector visible without letting them dominate width
- Remove the hero-like top block and replace it with a compact status toolbar
- Reorder panel content so common actions appear first
- Move long metadata and rarely used blocks behind collapsible sections
- Keep the current user workflow recognizable rather than replacing the app
  with a new navigation model

## Non-Goals

- No redesign of graph data, graph model, or Cytoscape behavior in this round
- No change to search semantics, provenance semantics, or Obsidian link logic
- No new landing page, onboarding page, or marketing shell
- No server-side data loading changes
- No replacement of the current `App.tsx` ownership model with a separate page
  architecture

## Approved Design

## 1. Desktop Shell

Desktop keeps a three-pane shell:

- left: slim control rail
- center: graph stage
- right: slim inspector rail

The shell remains familiar, but the size balance changes in favor of the
center.

### Desktop width targets

For wide desktop (`1280px` and above):

- left rail: `200px` to `220px`
- center: remaining width
- right rail: `220px` to `240px`

For medium desktop (`1024px` to `1279px`):

- left rail: `180px` to `200px`
- center: remaining width
- right rail: `200px` to `220px`

The graph stage must visually read as the dominant region in both ranges.

## 2. Top Bar Replacement

The current large top section is replaced by a thin toolbar.

The new top bar keeps only:

- dashboard title
- current view label
- a compact status summary such as visible and hidden counts

The new top area should fit in one thin row, or at most two compact rows on
smaller widths. It must not read like a hero section.

### Height targets

- toolbar height on desktop: `56px` to `64px`
- graph stage should consume the rest of the first screen after padding and the
  toolbar are applied

## 3. Left Rail Priority

The left rail changes from "everything at once" to "actions first."

### First-visible content

The top of the left rail should show:

1. search term
2. search field selection
3. immediate search results
4. view mode switching

### Deferred content

The following sections remain available, but move lower or start collapsed:

- ontology query
- saved views
- infra summary
- metrics

This keeps the most common entry actions visible without spending width on
blocks that are not needed on every interaction.

## 4. Right Rail Priority

The right rail changes from full metadata-first to selection summary-first.

### First-visible content

The top of the inspector should show:

1. selected node or edge name
2. type
3. `Why visible?`
4. evidence path or Obsidian note link
5. a compact provenance summary

### Deferred content

The following content remains available but starts lower or collapsed:

- full node metadata
- long provenance details
- related details
- long evidence-derived rows

This preserves the existing inspector role while reducing the chance that
low-priority metadata pushes useful context below the fold.

## 5. Scrolling Model

The page should stop growing vertically as the default behavior.

Instead:

- the shell shares a common viewport-driven height
- left rail scrolls internally
- center graph stage keeps its own stable height
- right rail scrolls internally

The graph must not shrink just because one side panel contains long content.

## 6. Graph Stage Rules

The center region becomes the reference area rather than leftover space.

### Required behavior

- the graph stage is visible as the main object on first render
- large unused introductory whitespace is removed
- graph canvas height is stable across selection and panel changes
- companion views still occupy the same center stage surface and do not resize
  the shell unpredictably

The main graph or companion surface must not look like a small preview embedded
between oversized side panels.

## 7. Responsive Behavior

### Tablet (`768px` to `1023px`)

The layout moves away from fixed three columns.

Structure:

- top: thin status bar
- middle: graph stage at full width
- lower area: search rail and inspector become stacked panels, tabs, or
  accordion sections

The graph remains the primary visible object.

### Mobile (`767px` and below)

The layout becomes single-focus.

Structure:

- top: thin status bar
- main: graph stage
- secondary access: bottom sheet, tabs, or slide-up surfaces for search and
  inspector

There should be no persistent left and right desktop rails on mobile.

## 8. Information Hierarchy Rules

This redesign depends on content priority, not CSS width changes alone.

### Rules

- do not keep all current sections fully expanded by default
- move low-frequency sections behind collapsible affordances before widening a
  panel
- preserve button count discipline in first-visible zones
- make labels and status pills compact
- avoid large empty copy blocks above the graph

If a section cannot justify above-the-fold space on most investigations, it
should start collapsed.

## 9. Implementation Scope

This round updates the existing screen rather than creating a new one.

### Included

- update `App.css` layout grid, heights, and responsive rules
- compress the top section into a thin toolbar
- reorder left rail section priority
- reorder right rail section priority
- add collapsed-default treatment where needed
- keep the graph stage height stable
- keep companion views aligned to the same center-stage sizing model

### Excluded

- no graph data contract changes
- no graph interaction redesign
- no search behavior redesign
- no provenance model redesign

## 10. Verification

The redesign is considered acceptable only when layout behavior is verified at
three viewport ranges.

### Desktop verification

- first screen shows the graph as the largest region
- left and right rails stay visible but visually secondary
- top toolbar is compact and does not consume hero-level height

### Tablet verification

- graph remains full-width primary content
- side panels are no longer fixed narrow columns
- controls remain reachable without collapsing the graph stage

### Mobile verification

- no persistent desktop-style side rails remain
- graph is the primary visible surface
- search and inspector are reachable through compact secondary UI

### Regression coverage

Tests should be expanded around:

- layout sizing rules
- collapsed-by-default section behavior
- responsive switch points
- stability of center-stage sizing

Existing UI alignment and component rendering tests should be extended rather
than replaced.

## Acceptance Notes

The user approved the following design direction during the brainstorming
session:

- graph-first layout
- slim default side rails
- thin top toolbar instead of the current large top section
- action-first left rail
- summary-first right rail
- internal panel scrolling
- responsive graph-first stacking on tablet and mobile
- implementation through the current page structure rather than a new page

## Open Questions Resolved

- **Desktop priority**: graph first
- **Side panel posture**: slim by default, not removed
- **Top section treatment**: compress into a thin toolbar
- **Chosen visual direction**: option `A`, slim rails plus thin toolbar

## Out of Scope Risks

- If collapsible sections are not implemented carefully, discoverability may
  drop for rarely used controls.
- If the toolbar tries to keep too many metrics, it may regrow into the same
  tall top area this redesign is trying to remove.
- If panel height is not locked to the shell, the graph can still lose visual
  priority even with narrower widths.
