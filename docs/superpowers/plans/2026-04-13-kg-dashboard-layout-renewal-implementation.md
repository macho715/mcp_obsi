# KG Dashboard Layout Renewal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Renew `kg-dashboard` so the graph canvas becomes the dominant first-screen surface, the side panels become slim rails with prioritized content, and tablet/mobile layouts switch to graph-first stacked behavior.

**Architecture:** Keep the current `App.tsx` page shell, but replace the large top hero with a compact toolbar, add a compact panel toggle for tablet/mobile, and introduce one reusable collapsible section primitive so low-frequency sidebar and inspector content can collapse instead of forcing wider rails. Layout work stays in `kg-dashboard/src/App.css`; behavioral wiring stays in `App.tsx`; left and right rail hierarchy changes stay inside `GraphSidebar.tsx` and `NodeInspector.tsx`.

**Tech Stack:** React 19, TypeScript, Vite, Vitest, existing CSS in `kg-dashboard/src/App.css`

---

## File Structure

### Files to create

- `kg-dashboard/src/components/CollapsibleSection.tsx`
  - reusable accessible `<details>` wrapper for low-priority content
- `kg-dashboard/src/components/DashboardToolbar.tsx`
  - compact title, active-view, compare-state, and stat summary toolbar
- `kg-dashboard/src/components/CompactPanelToggle.tsx`
  - tablet/mobile toggle between controls and inspector surfaces
- `kg-dashboard/src/components/DashboardToolbar.test.tsx`
  - focused render test for the compact toolbar

### Files to modify

- `kg-dashboard/src/App.tsx`
  - replace the current tall topbar block with `DashboardToolbar`
  - add compact panel state for tablet/mobile
  - wire compact panel toggle into the shell
- `kg-dashboard/src/App.css`
  - define new desktop widths, toolbar sizing, shared shell heights, internal scrolling, and tablet/mobile switching rules
- `kg-dashboard/src/components/GraphSidebar.tsx`
  - keep search and view mode first
  - move ontology query, saved views, infra summary, and metrics behind collapsed sections
- `kg-dashboard/src/components/NodeInspector.tsx`
  - keep summary, `Why visible?`, evidence link, and provenance preview above the fold
  - collapse long metadata and secondary sections
- `kg-dashboard/src/components/GraphSidebar.test.tsx`
  - assert left-rail section order and collapsed-default behavior
- `kg-dashboard/src/components/NodeInspector.test.tsx`
  - assert summary-first inspector layout and collapsed metadata behavior
- `kg-dashboard/src/components/ui-rule-alignment.test.tsx`
  - assert graph-first shell widths, compact toolbar sizing, and responsive compact-panel selectors

### Files intentionally not changed

- `kg-dashboard/src/utils/graph-model.ts`
  - no graph semantics change in this plan
- `kg-dashboard/public/data/*.json`
  - no data export refresh required for layout-only work

---

### Task 1: Add shared layout primitives for compact toolbar and collapsed detail blocks

**Files:**
- Create: `kg-dashboard/src/components/CollapsibleSection.tsx`
- Create: `kg-dashboard/src/components/DashboardToolbar.tsx`
- Create: `kg-dashboard/src/components/CompactPanelToggle.tsx`
- Create: `kg-dashboard/src/components/DashboardToolbar.test.tsx`
- Test: `kg-dashboard/src/components/DashboardToolbar.test.tsx`

- [ ] **Step 1: Write the failing toolbar test**

Create `kg-dashboard/src/components/DashboardToolbar.test.tsx` with:

```tsx
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { DashboardToolbar } from './DashboardToolbar';
import type { GraphMetrics } from '../types/graph';

const metrics: GraphMetrics = {
  totalNodes: 100,
  totalEdges: 200,
  visibleNodes: 20,
  visibleEdges: 30,
  hiddenNodes: 80,
  hiddenEdges: 170,
  issueCount: 5,
  hubCount: 2,
};

describe('DashboardToolbar', () => {
  it('renders compact title, current view, and stat summary without hero copy', () => {
    const markup = renderToStaticMarkup(
      <DashboardToolbar
        title="kg-dashboard"
        viewLabel="요약 뷰"
        compareLabel={null}
        metrics={metrics}
      />,
    );

    expect(markup).toContain('kg-dashboard');
    expect(markup).toContain('요약 뷰');
    expect(markup).toContain('Visible');
    expect(markup).toContain('Hidden');
    expect(markup).toContain('Hotspots');
    expect(markup).not.toContain('Knowledge graph tool');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/components/DashboardToolbar.test.tsx
```

Expected:

- FAIL because `DashboardToolbar.tsx` does not exist yet

- [ ] **Step 3: Write the minimal shared primitives**

Create `kg-dashboard/src/components/CollapsibleSection.tsx`:

```tsx
import type { PropsWithChildren, ReactNode } from 'react';

interface CollapsibleSectionProps extends PropsWithChildren {
  sectionId: string;
  title: string;
  summary?: ReactNode;
  defaultOpen?: boolean;
}

export function CollapsibleSection({
  sectionId,
  title,
  summary,
  defaultOpen = false,
  children,
}: CollapsibleSectionProps) {
  return (
    <details className="collapsible-section" data-section-id={sectionId} open={defaultOpen}>
      <summary className="collapsible-section__summary">
        <span className="collapsible-section__title">{title}</span>
        {summary ? <span className="collapsible-section__meta">{summary}</span> : null}
      </summary>
      <div className="collapsible-section__body">{children}</div>
    </details>
  );
}
```

Create `kg-dashboard/src/components/DashboardToolbar.tsx`:

```tsx
import type { GraphMetrics } from '../types/graph';

interface DashboardToolbarProps {
  title: string;
  viewLabel: string;
  compareLabel: string | null;
  metrics: GraphMetrics;
}

export function DashboardToolbar({
  title,
  viewLabel,
  compareLabel,
  metrics,
}: DashboardToolbarProps) {
  return (
    <header className="dashboard-toolbar" aria-label="Dashboard toolbar">
      <div className="dashboard-toolbar__identity">
        <strong className="dashboard-toolbar__title">{title}</strong>
        <span className="dashboard-toolbar__view">{viewLabel}</span>
        {compareLabel ? <span className="dashboard-toolbar__compare">{compareLabel}</span> : null}
      </div>
      <dl className="dashboard-toolbar__stats">
        <div>
          <dt>Visible</dt>
          <dd>{metrics.visibleNodes} / {metrics.visibleEdges}</dd>
        </div>
        <div>
          <dt>Hidden</dt>
          <dd>{metrics.hiddenNodes} / {metrics.hiddenEdges}</dd>
        </div>
        <div>
          <dt>Hotspots</dt>
          <dd>{metrics.issueCount} / {metrics.hubCount}</dd>
        </div>
      </dl>
    </header>
  );
}
```

Create `kg-dashboard/src/components/CompactPanelToggle.tsx`:

```tsx
type CompactPanelTab = 'controls' | 'inspector';

interface CompactPanelToggleProps {
  activeTab: CompactPanelTab;
  onChange: (tab: CompactPanelTab) => void;
}

export function CompactPanelToggle({
  activeTab,
  onChange,
}: CompactPanelToggleProps) {
  return (
    <div className="dashboard-compact-panel-toggle" role="tablist" aria-label="Compact panels">
      <button
        type="button"
        className={activeTab === 'controls' ? 'segmented-control__button is-active' : 'segmented-control__button'}
        onClick={() => onChange('controls')}
        aria-pressed={activeTab === 'controls'}
      >
        Controls
      </button>
      <button
        type="button"
        className={activeTab === 'inspector' ? 'segmented-control__button is-active' : 'segmented-control__button'}
        onClick={() => onChange('inspector')}
        aria-pressed={activeTab === 'inspector'}
      >
        Inspector
      </button>
    </div>
  );
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/components/DashboardToolbar.test.tsx
```

Expected:

- PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add kg-dashboard/src/components/CollapsibleSection.tsx kg-dashboard/src/components/DashboardToolbar.tsx kg-dashboard/src/components/CompactPanelToggle.tsx kg-dashboard/src/components/DashboardToolbar.test.tsx
git commit -m "feat: add compact dashboard layout primitives"
```

### Task 2: Convert the shell to a graph-first layout with a thin toolbar and compact-panel toggle

**Files:**
- Modify: `kg-dashboard/src/App.tsx`
- Modify: `kg-dashboard/src/App.css`
- Modify: `kg-dashboard/src/components/ui-rule-alignment.test.tsx`
- Test: `kg-dashboard/src/components/ui-rule-alignment.test.tsx`

- [ ] **Step 1: Write the failing shell-alignment test**

Append this test to `kg-dashboard/src/components/ui-rule-alignment.test.tsx`:

```tsx
it('uses graph-first shell widths, a thin toolbar, and compact-panel selectors', () => {
  const css = readFileSync(new URL('../App.css', import.meta.url), 'utf-8');

  expect(css).toMatch(
    /grid-template-columns:\s*minmax\(200px,\s*220px\)\s+minmax\(0,\s*1fr\)\s+minmax\(220px,\s*240px\)/,
  );
  expect(css).toMatch(/\.dashboard-toolbar\s*\{[^}]*min-height:\s*56px/);
  expect(css).toMatch(/@media\s*\(max-width:\s*1023px\)/);
  expect(css).toMatch(/data-compact-panel='controls'/);
  expect(css).toMatch(/data-compact-panel='inspector'/);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/components/ui-rule-alignment.test.tsx
```

Expected:

- FAIL because `App.css` still uses the old `260px-320px` shell widths
- FAIL because `.dashboard-toolbar` and compact-panel selectors do not exist yet

- [ ] **Step 3: Write the minimal shell implementation**

Update `kg-dashboard/src/App.tsx` near the state declarations:

```tsx
import { CompactPanelToggle } from './components/CompactPanelToggle';
import { DashboardToolbar } from './components/DashboardToolbar';

const [compactPanelTab, setCompactPanelTab] = useState<'controls' | 'inspector'>('controls');

useEffect(() => {
  if (selectedNodeId || selectedEdgeId) {
    setCompactPanelTab('inspector');
    return;
  }
  setCompactPanelTab('controls');
}, [selectedEdgeId, selectedNodeId]);
```

Replace the current `<header className="dashboard-topbar">...</header>` block with:

```tsx
<DashboardToolbar
  title="kg-dashboard"
  viewLabel={VIEW_COPY[effectiveViewMode].title}
  compareLabel={
    compareState
      ? `Compare · ${compareState.leftName} → ${compareState.rightName}`
      : null
  }
  metrics={metrics}
/>
```

Wrap the shell root and add the compact toggle:

```tsx
<div className="dashboard-shell" data-compact-panel={compactPanelTab}>
  <GraphSidebar ... />

  <main className="dashboard-main">
    <DashboardToolbar ... />
    <section className="dashboard-stage">...</section>
  </main>

  <div className="dashboard-compact-panel-slot">
    <CompactPanelToggle
      activeTab={compactPanelTab}
      onChange={setCompactPanelTab}
    />
  </div>

  <NodeInspector ... />
</div>
```

Replace the old top-level shell and stage rules in `kg-dashboard/src/App.css` with:

```css
.dashboard-shell {
  min-height: 100svh;
  display: grid;
  grid-template-columns: minmax(200px, 220px) minmax(0, 1fr) minmax(220px, 240px);
  gap: 0.75rem;
  padding: 0.75rem;
  box-sizing: border-box;
  align-items: stretch;
}

.dashboard-main,
.dashboard-sidebar,
.inspector {
  min-width: 0;
  min-height: calc(100svh - 1.5rem);
}

.dashboard-main {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 0.75rem;
}

.dashboard-toolbar {
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 0.9rem;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.dashboard-stage {
  min-height: 0;
  height: 100%;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 0.75rem;
}

.graph-canvas-shell,
.companion-surface {
  min-height: 0;
  height: 100%;
}

.dashboard-compact-panel-slot {
  display: none;
}

@media (max-width: 1023px) {
  .dashboard-shell {
    grid-template-columns: 1fr;
    grid-template-areas:
      "main"
      "compact-toggle"
      "panel";
  }

  .dashboard-main {
    grid-area: main;
    min-height: auto;
  }

  .dashboard-compact-panel-slot {
    grid-area: compact-toggle;
    display: block;
  }

  .dashboard-sidebar,
  .inspector {
    grid-area: panel;
    min-height: min(42svh, 360px);
  }

  .dashboard-shell[data-compact-panel='controls'] .inspector {
    display: none;
  }

  .dashboard-shell[data-compact-panel='inspector'] .dashboard-sidebar {
    display: none;
  }
}
```

- [ ] **Step 4: Run the focused test to verify it passes**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/components/ui-rule-alignment.test.tsx src/components/DashboardToolbar.test.tsx
```

Expected:

- PASS with the new CSS selector assertions and toolbar render assertions

- [ ] **Step 5: Commit**

```bash
git add kg-dashboard/src/App.tsx kg-dashboard/src/App.css kg-dashboard/src/components/ui-rule-alignment.test.tsx
git commit -m "feat: make kg dashboard shell graph-first"
```

### Task 3: Reorder the left rail so search and view mode stay above the fold

**Files:**
- Modify: `kg-dashboard/src/components/GraphSidebar.tsx`
- Modify: `kg-dashboard/src/components/GraphSidebar.test.tsx`
- Test: `kg-dashboard/src/components/GraphSidebar.test.tsx`

- [ ] **Step 1: Write the failing sidebar-priority test**

Append this test to `kg-dashboard/src/components/GraphSidebar.test.tsx`:

```tsx
it('keeps search and view mode ahead of collapsed secondary sections', () => {
  const markup = renderToStaticMarkup(
    <GraphSidebar
      metrics={metrics}
      searchTerm=""
      searchField="all"
      searchMatches={[]}
      classFilter=""
      propertyFilter=""
      relationTypeFilter=""
      classOptions={['Hub', 'Shipment']}
      propertyOptions={['occursAt']}
      relationTypeOptions={['occursAt']}
      ontologyPresets={[{ id: 'all', label: 'All ontology' }]}
      savedQueries={[]}
      hubSummaries={[{ id: 'hub/mosb', label: 'MOSB', type: 'Hub', shipment: 3, vessel: 1, vendor: 1 }]}
      viewMode="summary"
      onSearchTermChange={() => {}}
      onSearchFieldChange={() => {}}
      onClassFilterChange={() => {}}
      onPropertyFilterChange={() => {}}
      onRelationTypeFilterChange={() => {}}
      onApplyOntologyPreset={() => {}}
      onSaveCurrentQuery={() => {}}
      onApplySavedQuery={() => {}}
      onSelectSearchMatch={() => {}}
      onViewModeChange={() => {}}
      hubThreshold={200}
      canClearSelection={false}
      onClearSelection={() => {}}
      clearSelectionLabel="Clear"
      canPinSelection={false}
      canHideSelection={false}
      canExpandSelection={false}
      onPinSelection={() => {}}
      onHideSelection={() => {}}
      onExpandSelection={() => {}}
      onResetManualState={() => {}}
      pinnedNodes={[]}
      hiddenNodes={[]}
      expandedNodes={[]}
      onRemovePinnedNode={() => {}}
      onRemoveHiddenNode={() => {}}
      onRemoveExpandedNode={() => {}}
      onCopyCurrentStateLink={() => {}}
      onSaveCurrentView={() => {}}
      savedViews={[]}
      onLoadSavedView={() => {}}
      onDeleteSavedView={() => {}}
      compareLeftId={null}
      compareRightId={null}
      onSetCompareLeft={() => {}}
      onSetCompareRight={() => {}}
      compareEnabled={false}
    />,
  );

  expect(markup.indexOf('Find a node')).toBeLessThan(markup.indexOf('Choose the slice'));
  expect(markup.indexOf('Choose the slice')).toBeLessThan(markup.indexOf('Class + relation filters'));
  expect(markup).toMatch(/data-section-id=\"ontology-query\"/);
  expect(markup).toMatch(/data-section-id=\"investigation-view\"/);
  expect(markup).toMatch(/data-section-id=\"infra-summary\"/);
  expect(markup).toMatch(/data-section-id=\"metrics\"/);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/components/GraphSidebar.test.tsx
```

Expected:

- FAIL because the current sidebar has no `data-section-id` collapsible wrappers

- [ ] **Step 3: Write the minimal sidebar reordering**

At the top of `kg-dashboard/src/components/GraphSidebar.tsx`, add:

```tsx
import { CollapsibleSection } from './CollapsibleSection';
```

Keep the existing Search and View mode panels first. Replace the secondary lower panels with one collapsed stack:

```tsx
<section className="panel panel--rail">
  <CollapsibleSection
    sectionId="ontology-query"
    title="Ontology query"
    summary="Class, property, and relation filters"
  >
    {/* existing ontology query form */}
  </CollapsibleSection>

  <CollapsibleSection
    sectionId="investigation-view"
    title="Investigation view"
    summary={savedViews.length > 0 ? `${savedViews.length} saved views` : 'Share and compare'}
  >
    {/* existing copy-link, save-view, saved-view, compare controls */}
  </CollapsibleSection>

  <CollapsibleSection
    sectionId="infra-summary"
    title="Infra summary"
    summary={`${hubSummaries.length} infra nodes`}
  >
    {/* existing infra summary rows */}
  </CollapsibleSection>

  <CollapsibleSection
    sectionId="metrics"
    title="Metrics"
    summary={`${metrics.visibleNodes} visible / ${metrics.hiddenNodes} hidden`}
  >
    {/* existing metrics rows */}
  </CollapsibleSection>
</section>
```

Also give the left rail its own internal scroll class:

```tsx
<aside className="dashboard-sidebar dashboard-sidebar--rail">
```

And add these CSS rules to `kg-dashboard/src/App.css`:

```css
.dashboard-sidebar--rail,
.inspector {
  overflow: auto;
}

.panel--rail {
  display: grid;
  gap: 0.75rem;
}

.collapsible-section {
  border-top: 1px solid var(--border);
  padding-top: 0.75rem;
}

.collapsible-section:first-child {
  border-top: 0;
  padding-top: 0;
}

.collapsible-section__summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  cursor: pointer;
  list-style: none;
}

.collapsible-section__summary::-webkit-details-marker {
  display: none;
}

.collapsible-section__body {
  margin-top: 0.75rem;
  display: grid;
  gap: 0.75rem;
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/components/GraphSidebar.test.tsx
```

Expected:

- PASS with the new section-order and `data-section-id` assertions

- [ ] **Step 5: Commit**

```bash
git add kg-dashboard/src/components/GraphSidebar.tsx kg-dashboard/src/components/GraphSidebar.test.tsx kg-dashboard/src/App.css
git commit -m "feat: prioritize search rail content"
```

### Task 4: Make the inspector summary-first and collapse long detail blocks

**Files:**
- Modify: `kg-dashboard/src/components/NodeInspector.tsx`
- Modify: `kg-dashboard/src/components/NodeInspector.test.tsx`
- Test: `kg-dashboard/src/components/NodeInspector.test.tsx`

- [ ] **Step 1: Write the failing inspector-summary test**

Append this test to `kg-dashboard/src/components/NodeInspector.test.tsx`:

```tsx
it('keeps summary actions above collapsed metadata sections', () => {
  const markup = renderToStaticMarkup(
    <NodeInspector
      node={{
        data: {
          id: 'issue/1',
          label: 'Issue 1',
          type: 'LogisticsIssue',
          analysisVault: 'ops vault',
          analysisPath: 'wiki/analyses/issue-1.md',
          severity: 'high',
          owner: 'team-logistics',
        },
      }}
      edge={null}
      degree={2}
      visibilityReasons={[
        {
          code: 'filter-match',
          label: 'Filter match',
          detail: 'Search term matched this node.',
        },
      ]}
      onClose={() => {}}
    />,
  );

  expect(markup.indexOf('Why visible?')).toBeLessThan(markup.indexOf('Node metadata'));
  expect(markup.indexOf('Open linked Obsidian note')).toBeLessThan(markup.indexOf('Node metadata'));
  expect(markup).toMatch(/data-section-id=\"inspector-node-metadata\"/);
  expect(markup).toMatch(/data-section-id=\"inspector-related-context\"/);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/components/NodeInspector.test.tsx
```

Expected:

- FAIL because the inspector currently renders raw metadata directly with no collapsed section ids

- [ ] **Step 3: Write the minimal inspector collapse rules**

At the top of `kg-dashboard/src/components/NodeInspector.tsx`, add:

```tsx
import { CollapsibleSection } from './CollapsibleSection';
```

Keep the current title, type badge row, `Why visible?`, note link, evidence path, and provenance preview where they are. Wrap the long blocks with collapsible sections:

```tsx
{activeTab === 'node' ? (
  node ? (
    <>
      <section className="field-list" aria-label="Node summary">
        {/* existing summary rows */}
      </section>

      <CollapsibleSection
        sectionId="inspector-node-metadata"
        title="Node metadata"
        summary={extraFields.length > 0 ? `${extraFields.length} fields` : 'No extra fields'}
      >
        {extraFields.length > 0 ? (
          <section className="field-list" aria-label="Node metadata">
            {/* existing extraFields rows */}
          </section>
        ) : (
          <p className="empty-copy">This node has no extra metadata beyond the standard graph fields.</p>
        )}
      </CollapsibleSection>
    </>
  ) : (
    <p className="empty-copy">No node is selected. Choose a node to inspect node-level details.</p>
  )
) : null}
```

For the lower-priority related section:

```tsx
{activeTab === 'related' ? (
  <CollapsibleSection
    sectionId="inspector-related-context"
    title="Related context"
    summary={node ? 'Node context' : edge ? 'Edge context' : 'No selection'}
  >
    <section className="field-list" aria-label="Related context">
      {/* existing related rows */}
    </section>
  </CollapsibleSection>
) : null}
```

Add a compact inspector rule to `kg-dashboard/src/App.css`:

```css
.inspector {
  display: grid;
  align-content: start;
  overflow: auto;
}

.inspector .segmented-control {
  gap: 0.35rem;
}

.inspector .segmented-control__button {
  padding: 0.55rem 0.7rem;
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/components/NodeInspector.test.tsx
```

Expected:

- PASS with the summary-first and `data-section-id` assertions

- [ ] **Step 5: Commit**

```bash
git add kg-dashboard/src/components/NodeInspector.tsx kg-dashboard/src/components/NodeInspector.test.tsx kg-dashboard/src/App.css
git commit -m "feat: compress inspector detail hierarchy"
```

## Validation Matrix

- [ ] **Run the focused frontend test pack**

```powershell
cd kg-dashboard
npm test -- --run src/components/DashboardToolbar.test.tsx src/components/GraphSidebar.test.tsx src/components/NodeInspector.test.tsx src/components/ui-rule-alignment.test.tsx
```

Expected:

- PASS with all targeted layout tests green

- [ ] **Run the full frontend test suite**

```powershell
cd kg-dashboard
npm test
```

Expected:

- PASS with no failed component or utility tests

- [ ] **Run the production build**

```powershell
cd kg-dashboard
npm run build
```

Expected:

- PASS and Vite produces a production bundle with no TypeScript errors

- [ ] **Run browser verification at three viewport sizes**

Start the dev server:

```powershell
cd kg-dashboard
npm run dev -- --host 127.0.0.1 --port 4173
```

Then verify:

1. Desktop `1440x900`
   - graph is the largest region on first load
   - toolbar fits in one thin row
   - left and right rails are visibly narrower than before

2. Tablet `1024x768`
   - graph stays full width
   - compact panel toggle appears
   - controls and inspector switch without shrinking the graph stage

3. Mobile `390x844`
   - no permanent left/right desktop rails remain
   - graph is visible first
   - compact panel toggle still exposes search and inspector access

- [ ] **Record the final implementation commit**

Use the commit produced by the last code task if no verification fixes are required. If verification exposes layout defects, fix them first, re-run the validation matrix, then commit the final polish with:

```bash
git add kg-dashboard/src/App.tsx kg-dashboard/src/App.css kg-dashboard/src/components/GraphSidebar.tsx kg-dashboard/src/components/NodeInspector.tsx kg-dashboard/src/components/DashboardToolbar.tsx kg-dashboard/src/components/CompactPanelToggle.tsx kg-dashboard/src/components/CollapsibleSection.tsx kg-dashboard/src/components/DashboardToolbar.test.tsx kg-dashboard/src/components/GraphSidebar.test.tsx kg-dashboard/src/components/NodeInspector.test.tsx kg-dashboard/src/components/ui-rule-alignment.test.tsx
git commit -m "feat: renew kg dashboard layout"
```

## Spec Coverage Check

- Graph-first desktop shell: Task 2
- Thin toolbar replacing the tall hero: Task 2
- Slim but visible desktop rails: Task 2
- Action-first left rail: Task 3
- Summary-first right rail: Task 4
- Internal scrolling and stable graph stage: Task 2 and Task 3/4 CSS updates
- Tablet/mobile compact behavior: Task 2 and Validation Matrix
- Regression coverage: Tasks 1 through 4 plus Validation Matrix

## Execution Notes

- Keep changes scoped to layout and hierarchy. Do not alter graph data contracts.
- Do not touch `kg-dashboard/public/data/*.json`.
- If a task uncovers unrelated visual debt, log it separately rather than folding it into this implementation.
