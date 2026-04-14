# KG Dashboard Usability Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `kg-dashboard` into a user-friendly investigation surface with field-aware search, synchronized `Graph / Table / Timeline / Schema` views, edge-aware inspection, and URL-restorable context.

**Architecture:** Keep the existing static JSON graph contract and current Cytoscape-based graph slice engine. Add a thin state and derived-view layer around it: a URL state helper, a richer search-match model, companion-view data builders, and an inspector that can switch between node, edge, evidence, and related context. Keep rendering logic decomposed into small focused React components so `App.tsx` coordinates state instead of owning every detail.

**Tech Stack:** React 19, TypeScript, Vite, Vitest, react-dom/server, Cytoscape.js

---

## File Structure

### Existing files to modify

- `kg-dashboard/src/App.tsx`
  - top-level dashboard state orchestration
  - URL restore and URL sync
  - companion view switching
  - shared selection wiring between graph and companion views
- `kg-dashboard/src/App.css`
  - companion view layout
  - field-aware search controls
  - inspector tab layout
  - table, timeline, and schema surface styling
- `kg-dashboard/src/types/graph.ts`
  - companion-view and search-match types
- `kg-dashboard/src/utils/graph-model.ts`
  - field-aware search result model
  - match-reason generation
- `kg-dashboard/src/utils/graph-model.test.ts`
  - search-match reason and ranking regression coverage
- `kg-dashboard/src/components/GraphSidebar.tsx`
  - structured search controls
  - quick-result reason labels
  - companion view switcher
- `kg-dashboard/src/components/GraphView.tsx`
  - edge selection
  - selected edge highlighting
- `kg-dashboard/src/components/NodeInspector.tsx`
  - tabbed inspector
  - node vs edge detail
  - evidence and related panels
- `kg-dashboard/src/components/NodeInspector.test.tsx`
  - inspector tab and edge/evidence coverage
- `kg-dashboard/src/components/ui-rule-alignment.test.tsx`
  - UI rule regression coverage for new surfaces

### New files to create

- `kg-dashboard/src/utils/dashboard-state.ts`
  - parse and serialize URL-backed dashboard state
- `kg-dashboard/src/utils/dashboard-state.test.ts`
  - URL state restore and serialization tests
- `kg-dashboard/src/utils/graph-companion-data.ts`
  - table rows
  - timeline rows
  - schema summary rows
- `kg-dashboard/src/utils/graph-companion-data.test.ts`
  - pure derived-view tests
- `kg-dashboard/src/components/GraphSidebar.test.tsx`
  - structured search UI tests
- `kg-dashboard/src/components/GraphCompanionTabs.tsx`
  - `Graph / Table / Timeline / Schema` switcher
- `kg-dashboard/src/components/GraphDataTable.tsx`
  - visible-slice row rendering
- `kg-dashboard/src/components/GraphTimeline.tsx`
  - shipment timing surface
- `kg-dashboard/src/components/GraphSchemaSummary.tsx`
  - node-type and edge-type counts
- `kg-dashboard/src/components/GraphCompanionViews.test.tsx`
  - static markup tests for companion surfaces

### Existing files to reference while implementing

- `docs/superpowers/specs/2026-04-12-kg-dashboard-usability-redesign-design.md`
- `docs/superpowers/specs/2026-04-12-kg-dashboard-graph-visibility-alignment-design.md`
- `kg-dashboard/src/components/GraphView.tsx`
- `kg-dashboard/src/components/GraphSidebar.tsx`
- `kg-dashboard/src/components/NodeInspector.tsx`
- `kg-dashboard/src/utils/graph-model.ts`

---

### Task 1: Add URL-backed dashboard state helpers

**Files:**
- Create: `kg-dashboard/src/utils/dashboard-state.ts`
- Create: `kg-dashboard/src/utils/dashboard-state.test.ts`
- Modify: `kg-dashboard/src/types/graph.ts`
- Test: `kg-dashboard/src/utils/dashboard-state.test.ts`

- [ ] **Step 1: Write the failing URL state tests**

Create `kg-dashboard/src/utils/dashboard-state.test.ts`:

```ts
import { describe, expect, it } from 'vitest';

import {
  DEFAULT_DASHBOARD_URL_STATE,
  buildDashboardUrlSearch,
  parseDashboardUrlState,
} from './dashboard-state';

describe('dashboard-state', () => {
  it('restores search, selection, and companion view from query string', () => {
    const restored = parseDashboardUrlState(
      '?q=POL&field=pol&view=search&panel=timeline&node=shipment%2F1&edge=shipment%2F1%7Chub%2F1%7CloadedAt',
    );

    expect(restored).toEqual({
      query: 'POL',
      searchField: 'pol',
      viewMode: 'search',
      companionView: 'timeline',
      selectedNodeId: 'shipment/1',
      selectedEdgeId: 'shipment/1|hub/1|loadedAt',
    });
  });

  it('drops invalid values and falls back to defaults', () => {
    const restored = parseDashboardUrlState('?field=unknown&view=broken&panel=nope');

    expect(restored).toEqual(DEFAULT_DASHBOARD_URL_STATE);
  });

  it('serializes only active values into a stable query string', () => {
    const serialized = buildDashboardUrlSearch({
      query: 'Mina Zayed',
      searchField: 'pod',
      viewMode: 'search',
      companionView: 'table',
      selectedNodeId: 'shipment/2',
      selectedEdgeId: null,
    });

    expect(serialized).toBe(
      '?q=Mina+Zayed&field=pod&view=search&panel=table&node=shipment%2F2',
    );
  });
});
```

- [ ] **Step 2: Run the new test file and confirm it fails**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/utils/dashboard-state.test.ts
```

Expected:

- FAIL because `dashboard-state.ts` does not exist yet

- [ ] **Step 3: Implement typed URL state helpers**

Update `kg-dashboard/src/types/graph.ts`:

```ts
export type GraphCompanionView = 'graph' | 'table' | 'timeline' | 'schema';

export type GraphSearchField =
  | 'all'
  | 'coe'
  | 'pol'
  | 'pod'
  | 'shipMode'
  | 'atd'
  | 'ata';
```

Create `kg-dashboard/src/utils/dashboard-state.ts`:

```ts
import type { GraphCompanionView, GraphSearchField, GraphViewMode } from '../types/graph';

export interface DashboardUrlState {
  query: string;
  searchField: GraphSearchField;
  viewMode: GraphViewMode;
  companionView: GraphCompanionView;
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
}

const VIEW_MODES: GraphViewMode[] = ['summary', 'issues', 'search', 'ego'];
const COMPANION_VIEWS: GraphCompanionView[] = ['graph', 'table', 'timeline', 'schema'];
const SEARCH_FIELDS: GraphSearchField[] = ['all', 'coe', 'pol', 'pod', 'shipMode', 'atd', 'ata'];

export const DEFAULT_DASHBOARD_URL_STATE: DashboardUrlState = {
  query: '',
  searchField: 'all',
  viewMode: 'summary',
  companionView: 'graph',
  selectedNodeId: null,
  selectedEdgeId: null,
};

export function parseDashboardUrlState(search: string): DashboardUrlState {
  const params = new URLSearchParams(search);
  const viewMode = params.get('view');
  const companionView = params.get('panel');
  const searchField = params.get('field');

  return {
    query: params.get('q') ?? '',
    searchField: SEARCH_FIELDS.includes(searchField as GraphSearchField)
      ? (searchField as GraphSearchField)
      : DEFAULT_DASHBOARD_URL_STATE.searchField,
    viewMode: VIEW_MODES.includes(viewMode as GraphViewMode)
      ? (viewMode as GraphViewMode)
      : DEFAULT_DASHBOARD_URL_STATE.viewMode,
    companionView: COMPANION_VIEWS.includes(companionView as GraphCompanionView)
      ? (companionView as GraphCompanionView)
      : DEFAULT_DASHBOARD_URL_STATE.companionView,
    selectedNodeId: params.get('node'),
    selectedEdgeId: params.get('edge'),
  };
}

export function buildDashboardUrlSearch(state: DashboardUrlState): string {
  const params = new URLSearchParams();

  if (state.query.trim()) params.set('q', state.query);
  if (state.searchField !== 'all') params.set('field', state.searchField);
  if (state.viewMode !== 'summary') params.set('view', state.viewMode);
  if (state.companionView !== 'graph') params.set('panel', state.companionView);
  if (state.selectedNodeId) params.set('node', state.selectedNodeId);
  if (state.selectedEdgeId) params.set('edge', state.selectedEdgeId);

  const query = params.toString();
  return query ? `?${query}` : '';
}
```

- [ ] **Step 4: Re-run the URL state tests**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/utils/dashboard-state.test.ts
```

Expected:

- PASS for all three tests in `dashboard-state.test.ts`

- [ ] **Step 5: Commit the URL state helper layer**

```powershell
git add -- ^
  kg-dashboard/src/types/graph.ts ^
  kg-dashboard/src/utils/dashboard-state.ts ^
  kg-dashboard/src/utils/dashboard-state.test.ts
git commit -m "feat: add kg-dashboard url state helpers"
```

---

### Task 2: Upgrade search to field-aware matches with visible reason labels

**Files:**
- Modify: `kg-dashboard/src/utils/graph-model.ts`
- Modify: `kg-dashboard/src/utils/graph-model.test.ts`
- Modify: `kg-dashboard/src/components/GraphSidebar.tsx`
- Create: `kg-dashboard/src/components/GraphSidebar.test.tsx`
- Test: `kg-dashboard/src/utils/graph-model.test.ts`
- Test: `kg-dashboard/src/components/GraphSidebar.test.tsx`

- [ ] **Step 1: Write failing search-match and sidebar tests**

Add to `kg-dashboard/src/utils/graph-model.test.ts`:

```ts
it('returns search matches with explicit matched field labels', () => {
  const nodes: GraphNode[] = [
    node('shipment/1', 'HVDC-001', 'Shipment', {
      portOfLoading: 'Le Havre',
      portOfDischarge: 'Mina Zayed',
      countryOfExport: 'FRANCE',
      actualDeparture: '2023-11-12',
    }),
  ];

  const matches = findSearchMatches(nodes, 'Le Havre', 'pol', 5);

  expect(matches).toHaveLength(1);
  expect(matches[0]).toMatchObject({
    node: { data: { id: 'shipment/1' } },
    matchedField: 'portOfLoading',
    reasonLabel: 'Matched in POL',
  });
});
```

Create `kg-dashboard/src/components/GraphSidebar.test.tsx`:

```tsx
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { GraphSidebar } from './GraphSidebar';
import type { GraphMetrics, SearchMatch } from '../types/graph';

const metrics: GraphMetrics = {
  totalNodes: 100,
  totalEdges: 200,
  visibleNodes: 12,
  visibleEdges: 18,
  hiddenNodes: 88,
  hiddenEdges: 182,
  issueCount: 3,
  hubCount: 1,
};

const matches: SearchMatch[] = [
  {
    node: {
      data: {
        id: 'shipment/1',
        label: 'HVDC-001',
        type: 'Shipment',
      },
    },
    matchedField: 'portOfLoading',
    reasonLabel: 'Matched in POL',
  },
];

describe('GraphSidebar search controls', () => {
  it('renders route and timing field chips plus match reasons', () => {
    const markup = renderToStaticMarkup(
      <GraphSidebar
        metrics={metrics}
        searchTerm="Le Havre"
        searchField="pol"
        searchMatches={matches}
        hubSummaries={[]}
        viewMode="search"
        companionView="graph"
        onSearchTermChange={() => {}}
        onSearchFieldChange={() => {}}
        onSelectSearchMatch={() => {}}
        onViewModeChange={() => {}}
        onCompanionViewChange={() => {}}
        hubThreshold={200}
        canClearSelection={false}
        onClearSelection={() => {}}
        clearSelectionLabel="Clear"
      />,
    );

    expect(markup).toContain('POL');
    expect(markup).toContain('POD');
    expect(markup).toContain('ATD');
    expect(markup).toContain('Matched in POL');
  });
});
```

- [ ] **Step 2: Run the targeted tests and confirm failure**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/utils/graph-model.test.ts src/components/GraphSidebar.test.tsx
```

Expected:

- FAIL because `findSearchMatches`, `SearchMatch`, `searchField`, and `companionView` are not implemented yet

- [ ] **Step 3: Implement field-aware search results and sidebar controls**

Update `kg-dashboard/src/types/graph.ts`:

```ts
export interface SearchMatch {
  node: GraphNode;
  matchedField: string;
  reasonLabel: string;
}
```

Update `kg-dashboard/src/utils/graph-model.ts`:

```ts
import type { GraphSearchField, SearchMatch } from '../types/graph';

const SEARCH_FIELD_MAP: Record<GraphSearchField, string[]> = {
  all: ['label', 'rdf-schema#label', 'id', 'countryOfExport', 'portOfLoading', 'portOfDischarge', 'shipMode', 'actualDeparture', 'actualArrival'],
  coe: ['countryOfExport'],
  pol: ['portOfLoading'],
  pod: ['portOfDischarge'],
  shipMode: ['shipMode'],
  atd: ['actualDeparture'],
  ata: ['actualArrival'],
};

const SEARCH_REASON_LABELS: Record<string, string> = {
  label: 'Matched in label',
  'rdf-schema#label': 'Matched in resolved label',
  id: 'Matched in id',
  countryOfExport: 'Matched in COE',
  portOfLoading: 'Matched in POL',
  portOfDischarge: 'Matched in POD',
  shipMode: 'Matched in Ship mode',
  actualDeparture: 'Matched in ATD',
  actualArrival: 'Matched in ATA',
};

export function findSearchMatches(
  nodes: GraphNode[],
  query: string,
  searchField: GraphSearchField = 'all',
  limit = 6,
): SearchMatch[] {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) {
    return [];
  }

  return nodes
    .map((node) => {
      const candidates = SEARCH_FIELD_MAP[searchField]
        .map((field) => {
          const rawValue = node.data[field];
          if (typeof rawValue !== 'string') {
            return null;
          }

          const normalizedValue = rawValue.toLowerCase();
          if (!normalizedValue.includes(normalizedQuery)) {
            return null;
          }

          return {
            node,
            matchedField: field,
            reasonLabel: SEARCH_REASON_LABELS[field],
            score: normalizedValue === normalizedQuery ? 10_000 : 1_000 - rawValue.length,
          };
        })
        .filter((item): item is SearchMatch & { score: number } => Boolean(item))
        .sort((left, right) => right.score - left.score);

      return candidates[0] ?? null;
    })
    .filter((item): item is SearchMatch & { score: number } => Boolean(item))
    .sort((left, right) => right.score - left.score)
    .slice(0, limit)
    .map(({ score: _score, ...match }) => match);
}

export function findMatchingNodes(nodes: GraphNode[], query: string, limit = 6): GraphNode[] {
  return findSearchMatches(nodes, query, 'all', limit).map((match) => match.node);
}
```

Update `kg-dashboard/src/components/GraphSidebar.tsx` to accept `searchField`, `companionView`, `onSearchFieldChange`, and `onCompanionViewChange`, then render search-field chips and quick-result reason labels.

- [ ] **Step 4: Re-run the search tests**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/utils/graph-model.test.ts src/components/GraphSidebar.test.tsx
```

Expected:

- PASS for the new field-aware search tests
- existing `graph-model.test.ts` coverage remains green

- [ ] **Step 5: Commit the structured search layer**

```powershell
git add -- ^
  kg-dashboard/src/types/graph.ts ^
  kg-dashboard/src/utils/graph-model.ts ^
  kg-dashboard/src/utils/graph-model.test.ts ^
  kg-dashboard/src/components/GraphSidebar.tsx ^
  kg-dashboard/src/components/GraphSidebar.test.tsx
git commit -m "feat: add field-aware dashboard search"
```

---

### Task 3: Add synchronized companion views for graph, table, timeline, and schema

**Files:**
- Create: `kg-dashboard/src/utils/graph-companion-data.ts`
- Create: `kg-dashboard/src/utils/graph-companion-data.test.ts`
- Create: `kg-dashboard/src/components/GraphCompanionTabs.tsx`
- Create: `kg-dashboard/src/components/GraphDataTable.tsx`
- Create: `kg-dashboard/src/components/GraphTimeline.tsx`
- Create: `kg-dashboard/src/components/GraphSchemaSummary.tsx`
- Create: `kg-dashboard/src/components/GraphCompanionViews.test.tsx`
- Modify: `kg-dashboard/src/types/graph.ts`
- Test: `kg-dashboard/src/utils/graph-companion-data.test.ts`
- Test: `kg-dashboard/src/components/GraphCompanionViews.test.tsx`

- [ ] **Step 1: Write failing derived-view tests**

Create `kg-dashboard/src/utils/graph-companion-data.test.ts`:

```ts
import { describe, expect, it } from 'vitest';

import { buildSchemaSummaryRows, buildTableRows, buildTimelineRows } from './graph-companion-data';
import type { GraphEdge, GraphNode } from '../types/graph';

const nodes: GraphNode[] = [
  {
    data: {
      id: 'shipment/1',
      label: 'HVDC-001',
      type: 'Shipment',
      portOfLoading: 'Le Havre',
      portOfDischarge: 'Mina Zayed',
      actualDeparture: '2023-11-12',
      actualArrival: '2023-12-01',
    },
  },
  {
    data: {
      id: 'issue/1',
      label: 'Crane delay',
      type: 'LogisticsIssue',
    },
  },
];

const edges: GraphEdge[] = [
  { data: { id: 'issue/1|shipment/1|affects', source: 'issue/1', target: 'shipment/1', label: 'affects' } },
];

describe('graph-companion-data', () => {
  it('builds sortable table rows from visible nodes', () => {
    const degreeById = new Map([
      ['shipment/1', 3],
      ['issue/1', 1],
    ]);

    expect(buildTableRows(nodes, degreeById)[0]).toMatchObject({
      id: 'shipment/1',
      label: 'HVDC-001',
      type: 'Shipment',
      pol: 'Le Havre',
      pod: 'Mina Zayed',
      atd: '2023-11-12',
      ata: '2023-12-01',
      degree: 3,
    });
  });

  it('builds timeline rows only for shipment-like timing records', () => {
    expect(buildTimelineRows(nodes)).toEqual([
      {
        id: 'shipment/1',
        label: 'HVDC-001',
        atd: '2023-11-12',
        ata: '2023-12-01',
        status: 'arrived',
      },
    ]);
  });

  it('builds schema summary counts for node and edge types', () => {
    expect(buildSchemaSummaryRows(nodes, edges)).toEqual({
      nodeTypes: [
        { type: 'LogisticsIssue', count: 1 },
        { type: 'Shipment', count: 1 },
      ],
      edgeTypes: [{ type: 'affects', count: 1 }],
    });
  });
});
```

Create `kg-dashboard/src/components/GraphCompanionViews.test.tsx`:

```tsx
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { GraphCompanionTabs } from './GraphCompanionTabs';
import { GraphDataTable } from './GraphDataTable';
import { GraphTimeline } from './GraphTimeline';
import { GraphSchemaSummary } from './GraphSchemaSummary';

describe('Graph companion views', () => {
  it('renders all companion tabs', () => {
    const markup = renderToStaticMarkup(
      <GraphCompanionTabs activeView="table" onChange={() => {}} />,
    );

    expect(markup).toContain('Graph');
    expect(markup).toContain('Table');
    expect(markup).toContain('Timeline');
    expect(markup).toContain('Schema');
  });

  it('renders table, timeline, and schema rows without card nesting', () => {
    const tableMarkup = renderToStaticMarkup(
      <GraphDataTable
        rows={[
          {
            id: 'shipment/1',
            label: 'HVDC-001',
            type: 'Shipment',
            pol: 'Le Havre',
            pod: 'Mina Zayed',
            atd: '2023-11-12',
            ata: '2023-12-01',
            degree: 3,
          },
        ]}
        selectedNodeId={null}
        onSelectNode={() => {}}
      />,
    );

    const timelineMarkup = renderToStaticMarkup(
      <GraphTimeline
        rows={[
          {
            id: 'shipment/1',
            label: 'HVDC-001',
            atd: '2023-11-12',
            ata: '2023-12-01',
            status: 'arrived',
          },
        ]}
        selectedNodeId={null}
        onSelectNode={() => {}}
      />,
    );

    const schemaMarkup = renderToStaticMarkup(
      <GraphSchemaSummary
        nodeTypes={[{ type: 'Shipment', count: 1 }]}
        edgeTypes={[{ type: 'affects', count: 1 }]}
      />,
    );

    expect(tableMarkup).toContain('Le Havre');
    expect(timelineMarkup).toContain('arrived');
    expect(schemaMarkup).toContain('Shipment');
    expect(tableMarkup).not.toContain('card card');
  });
});
```

- [ ] **Step 2: Run the new derived-view tests and confirm failure**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/utils/graph-companion-data.test.ts src/components/GraphCompanionViews.test.tsx
```

Expected:

- FAIL because the new utility and component files do not exist yet

- [ ] **Step 3: Implement the companion data builders and presentational components**

Update `kg-dashboard/src/types/graph.ts` with helper row types:

```ts
export interface GraphTableRow {
  id: string;
  label: string;
  type: GraphNodeType;
  pol: string;
  pod: string;
  atd: string;
  ata: string;
  degree: number;
}

export interface GraphTimelineRow {
  id: string;
  label: string;
  atd: string;
  ata: string;
  status: 'unknown' | 'departed' | 'arrived';
}
```

Create `kg-dashboard/src/utils/graph-companion-data.ts`:

```ts
import type { GraphEdge, GraphNode, GraphTableRow, GraphTimelineRow } from '../types/graph';

function asText(value: string | number | boolean | undefined): string {
  return typeof value === 'string' ? value : '';
}

export function buildTableRows(
  nodes: GraphNode[],
  degreeById: Map<string, number>,
): GraphTableRow[] {
  return nodes
    .map((node) => ({
      id: node.data.id,
      label: node.data['rdf-schema#label'] ?? node.data.label,
      type: node.data.type,
      pol: asText(node.data.portOfLoading),
      pod: asText(node.data.portOfDischarge),
      atd: asText(node.data.actualDeparture),
      ata: asText(node.data.actualArrival),
      degree: degreeById.get(node.data.id) ?? 0,
    }))
    .sort((left, right) => right.degree - left.degree || left.label.localeCompare(right.label));
}

export function buildTimelineRows(nodes: GraphNode[]): GraphTimelineRow[] {
  return nodes
    .filter((node) => node.data.type === 'Shipment')
    .map((node) => {
      const atd = asText(node.data.actualDeparture);
      const ata = asText(node.data.actualArrival);
      return {
        id: node.data.id,
        label: node.data['rdf-schema#label'] ?? node.data.label,
        atd,
        ata,
        status: ata ? 'arrived' : atd ? 'departed' : 'unknown',
      };
    })
    .sort((left, right) => left.label.localeCompare(right.label));
}

export function buildSchemaSummaryRows(nodes: GraphNode[], edges: GraphEdge[]) {
  const nodeTypeCounts = new Map<string, number>();
  const edgeTypeCounts = new Map<string, number>();

  nodes.forEach((node) => {
    nodeTypeCounts.set(node.data.type, (nodeTypeCounts.get(node.data.type) ?? 0) + 1);
  });

  edges.forEach((edge) => {
    const type = edge.data.label ?? 'unlabeled';
    edgeTypeCounts.set(type, (edgeTypeCounts.get(type) ?? 0) + 1);
  });

  return {
    nodeTypes: [...nodeTypeCounts.entries()]
      .map(([type, count]) => ({ type, count }))
      .sort((left, right) => left.type.localeCompare(right.type)),
    edgeTypes: [...edgeTypeCounts.entries()]
      .map(([type, count]) => ({ type, count }))
      .sort((left, right) => left.type.localeCompare(right.type)),
  };
}
```

Create `kg-dashboard/src/components/GraphCompanionTabs.tsx`:

```tsx
import type { GraphCompanionView } from '../types/graph';

const TABS: GraphCompanionView[] = ['graph', 'table', 'timeline', 'schema'];

export function GraphCompanionTabs({
  activeView,
  onChange,
}: {
  activeView: GraphCompanionView;
  onChange: (view: GraphCompanionView) => void;
}) {
  return (
    <div className="segmented-control companion-tabs" role="tablist" aria-label="Companion views">
      {TABS.map((tab) => (
        <button
          key={tab}
          type="button"
          className={tab === activeView ? 'segmented-control__button is-active' : 'segmented-control__button'}
          onClick={() => onChange(tab)}
          aria-pressed={tab === activeView}
        >
          {tab[0].toUpperCase() + tab.slice(1)}
        </button>
      ))}
    </div>
  );
}
```

Create `GraphDataTable.tsx`, `GraphTimeline.tsx`, and `GraphSchemaSummary.tsx` as simple table/list surfaces that accept the derived rows and render empty-copy messages when rows are empty.

- [ ] **Step 4: Re-run the companion-view tests**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/utils/graph-companion-data.test.ts src/components/GraphCompanionViews.test.tsx
```

Expected:

- PASS for derived rows and static markup rendering

- [ ] **Step 5: Commit the companion-view building blocks**

```powershell
git add -- ^
  kg-dashboard/src/types/graph.ts ^
  kg-dashboard/src/utils/graph-companion-data.ts ^
  kg-dashboard/src/utils/graph-companion-data.test.ts ^
  kg-dashboard/src/components/GraphCompanionTabs.tsx ^
  kg-dashboard/src/components/GraphDataTable.tsx ^
  kg-dashboard/src/components/GraphTimeline.tsx ^
  kg-dashboard/src/components/GraphSchemaSummary.tsx ^
  kg-dashboard/src/components/GraphCompanionViews.test.tsx
git commit -m "feat: add kg-dashboard companion views"
```

---

### Task 4: Make the inspector edge-aware and expose node, edge, evidence, and related tabs

**Files:**
- Modify: `kg-dashboard/src/components/GraphView.tsx`
- Modify: `kg-dashboard/src/components/NodeInspector.tsx`
- Modify: `kg-dashboard/src/components/NodeInspector.test.tsx`
- Modify: `kg-dashboard/src/types/graph.ts`
- Test: `kg-dashboard/src/components/NodeInspector.test.tsx`

- [ ] **Step 1: Write failing inspector and edge tests**

Replace `kg-dashboard/src/components/NodeInspector.test.tsx` with:

```tsx
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { NodeInspector } from './NodeInspector';
import type { GraphEdge, GraphNode } from '../types/graph';

function renderInspector(node: GraphNode | null, edge: GraphEdge | null): string {
  return renderToStaticMarkup(
    <NodeInspector
      node={node}
      edge={edge}
      degree={3}
      onClose={() => {}}
    />,
  );
}

describe('NodeInspector', () => {
  it('renders node, edge, evidence, and related tabs', () => {
    const markup = renderInspector(
      {
        data: {
          id: 'shipment/1',
          label: 'HVDC-001',
          type: 'Shipment',
          analysisVault: 'ops vault',
          analysisPath: 'wiki/analyses/shipment-1.md',
          portOfLoading: 'Le Havre',
        },
      },
      null,
    );

    expect(markup).toContain('Node');
    expect(markup).toContain('Edge');
    expect(markup).toContain('Evidence');
    expect(markup).toContain('Related');
  });

  it('renders edge details when an edge is selected', () => {
    const markup = renderInspector(null, {
      data: {
        id: 'shipment/1|hub/1|loadedAt',
        source: 'shipment/1',
        target: 'hub/1',
        label: 'loadedAt',
        evidencePath: 'wiki/analyses/edge-loaded-at.md',
      },
    });

    expect(markup).toContain('loadedAt');
    expect(markup).toContain('shipment/1');
    expect(markup).toContain('hub/1');
    expect(markup).toContain('wiki/analyses/edge-loaded-at.md');
  });

  it('shows an explicit no-evidence message when no evidence metadata exists', () => {
    const markup = renderInspector(
      {
        data: {
          id: 'issue/no-link',
          label: 'No link issue',
          type: 'LogisticsIssue',
        },
      },
      null,
    );

    expect(markup).toContain('No linked evidence is available for this selection.');
  });
});
```

- [ ] **Step 2: Run the inspector test and confirm failure**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/components/NodeInspector.test.tsx
```

Expected:

- FAIL because `NodeInspector` does not accept `edge` or render tabs yet

- [ ] **Step 3: Implement edge selection and tabbed inspector rendering**

Update `kg-dashboard/src/types/graph.ts` so edges can carry stable ids and optional evidence metadata:

```ts
export interface GraphEdgeData {
  id?: string;
  source: string;
  target: string;
  label?: string;
  evidencePath?: string;
  [key: string]: string | number | boolean | undefined;
}
```

Update `kg-dashboard/src/components/GraphView.tsx` props:

```tsx
interface GraphViewProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  viewMode: GraphViewMode;
  hubThreshold: number;
  degreeById: Map<string, number>;
  onSelectNode: (nodeId: string | null) => void;
  onSelectEdge: (edgeId: string | null) => void;
}
```

Attach edge tap handling:

```tsx
const handleEdgeTap = (event: cytoscape.EventObject) => {
  const tappedEdgeId = event.target.data('id') as string | undefined;
  onSelectEdge(tappedEdgeId ?? null);
};

cy.on('tap', 'edge', handleEdgeTap);
```

Update `kg-dashboard/src/components/NodeInspector.tsx`:

```tsx
import { useMemo, useState } from 'react';
import type { GraphEdge, GraphNode } from '../types/graph';

type InspectorTab = 'node' | 'edge' | 'evidence' | 'related';

export interface NodeInspectorProps {
  node: GraphNode | null;
  edge: GraphEdge | null;
  degree: number | null;
  onClose: () => void;
}

const TABS: Array<{ id: InspectorTab; label: string }> = [
  { id: 'node', label: 'Node' },
  { id: 'edge', label: 'Edge' },
  { id: 'evidence', label: 'Evidence' },
  { id: 'related', label: 'Related' },
];
```

Then render a tab row plus panels:

```tsx
const [activeTab, setActiveTab] = useState<InspectorTab>(edge ? 'edge' : 'node');

const evidenceItems = useMemo(() => {
  const items: string[] = [];
  if (typeof node?.data.analysisPath === 'string') items.push(node.data.analysisPath);
  if (typeof edge?.data.evidencePath === 'string') items.push(edge.data.evidencePath);
  return items;
}, [edge, node]);
```

Render an explicit empty evidence state:

```tsx
{activeTab === 'evidence' ? (
  evidenceItems.length > 0 ? (
    <section className="field-list" aria-label="Selection evidence">
      {evidenceItems.map((item) => (
        <div className="field-list__row" key={item}>
          <span className="field-list__key">Path</span>
          <span className="field-list__value">{item}</span>
        </div>
      ))}
    </section>
  ) : (
    <p className="empty-copy">No linked evidence is available for this selection.</p>
  )
) : null}
```

- [ ] **Step 4: Re-run the inspector test**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/components/NodeInspector.test.tsx
```

Expected:

- PASS with the new tabbed inspector coverage

- [ ] **Step 5: Commit the edge-aware inspector**

```powershell
git add -- ^
  kg-dashboard/src/types/graph.ts ^
  kg-dashboard/src/components/GraphView.tsx ^
  kg-dashboard/src/components/NodeInspector.tsx ^
  kg-dashboard/src/components/NodeInspector.test.tsx
git commit -m "feat: add edge-aware dashboard inspector"
```

---

### Task 5: Wire companion views, URL sync, and UI-rule-safe integration in App

**Files:**
- Modify: `kg-dashboard/src/App.tsx`
- Modify: `kg-dashboard/src/App.css`
- Modify: `kg-dashboard/src/components/ui-rule-alignment.test.tsx`
- Test: `kg-dashboard/src/components/ui-rule-alignment.test.tsx`
- Test: `kg-dashboard/src/utils/dashboard-state.test.ts`
- Test: `kg-dashboard/src/utils/graph-model.test.ts`
- Test: `kg-dashboard/src/utils/graph-companion-data.test.ts`
- Test: `kg-dashboard/src/components/GraphSidebar.test.tsx`
- Test: `kg-dashboard/src/components/GraphCompanionViews.test.tsx`
- Test: `kg-dashboard/src/components/NodeInspector.test.tsx`

- [ ] **Step 1: Write failing UI rule tests for companion tabs and non-graph surfaces**

Append to `kg-dashboard/src/components/ui-rule-alignment.test.tsx`:

```tsx
import { GraphCompanionTabs } from './GraphCompanionTabs';
import { GraphDataTable } from './GraphDataTable';

it('keeps companion tabs and table surface within the same card and radius rules', () => {
  const tabsMarkup = renderToStaticMarkup(
    <GraphCompanionTabs activeView="table" onChange={() => {}} />,
  );
  const tableMarkup = renderToStaticMarkup(
    <GraphDataTable
      rows={[
        {
          id: 'shipment/1',
          label: 'HVDC-001',
          type: 'Shipment',
          pol: 'Le Havre',
          pod: 'Mina Zayed',
          atd: '2023-11-12',
          ata: '2023-12-01',
          degree: 3,
        },
      ]}
      selectedNodeId={null}
      onSelectNode={() => {}}
    />,
  );

  expect(tabsMarkup).not.toContain('hero');
  expect(tableMarkup).not.toContain('card card');
});
```

- [ ] **Step 2: Run the full frontend suite and confirm at least one failure before integration**

Run:

```powershell
cd kg-dashboard
npm test
```

Expected:

- FAIL because `App.tsx` does not yet pass the new props through to sidebar, graph, or inspector

- [ ] **Step 3: Integrate URL state, search field state, companion view state, and shared selection in `App.tsx`**

Update `kg-dashboard/src/App.tsx` imports:

```tsx
import type {
  GraphCompanionView,
  GraphEdge,
  GraphNode,
  GraphSearchField,
  GraphViewMode,
} from './types/graph';
import {
  DEFAULT_DASHBOARD_URL_STATE,
  buildDashboardUrlSearch,
  parseDashboardUrlState,
} from './utils/dashboard-state';
import {
  buildSchemaSummaryRows,
  buildTableRows,
  buildTimelineRows,
} from './utils/graph-companion-data';
import { GraphCompanionTabs } from './components/GraphCompanionTabs';
import { GraphDataTable } from './components/GraphDataTable';
import { GraphTimeline } from './components/GraphTimeline';
import { GraphSchemaSummary } from './components/GraphSchemaSummary';
```

Initialize state from URL:

```tsx
const initialUrlState =
  typeof window === 'undefined'
    ? DEFAULT_DASHBOARD_URL_STATE
    : parseDashboardUrlState(window.location.search);

const [viewMode, setViewMode] = useState<GraphViewMode>(initialUrlState.viewMode);
const [companionView, setCompanionView] = useState<GraphCompanionView>(initialUrlState.companionView);
const [selectedNodeId, setSelectedNodeId] = useState<string | null>(initialUrlState.selectedNodeId);
const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(initialUrlState.selectedEdgeId);
const [searchTerm, setSearchTerm] = useState(initialUrlState.query);
const [searchField, setSearchField] = useState<GraphSearchField>(initialUrlState.searchField);
```

Build search matches and companion rows:

```tsx
const searchMatches = useMemo(
  () => findSearchMatches(allNodes, deferredSearch, searchField, 6),
  [allNodes, deferredSearch, searchField],
);

const tableRows = useMemo(
  () => buildTableRows(visibleGraph.nodes, index.degreeById),
  [index.degreeById, visibleGraph.nodes],
);

const timelineRows = useMemo(
  () => buildTimelineRows(visibleGraph.nodes),
  [visibleGraph.nodes],
);

const schemaSummary = useMemo(
  () => buildSchemaSummaryRows(visibleGraph.nodes, visibleGraph.edges),
  [visibleGraph.edges, visibleGraph.nodes],
);

const selectedEdge = selectedEdgeId
  ? visibleGraph.edges.find((edge) => edge.data.id === selectedEdgeId) ?? null
  : null;
```

Sync URL on state changes:

```tsx
useEffect(() => {
  const search = buildDashboardUrlSearch({
    query: searchTerm,
    searchField,
    viewMode: effectiveViewMode,
    companionView,
    selectedNodeId,
    selectedEdgeId,
  });

  window.history.replaceState({}, '', `${window.location.pathname}${search}`);
}, [companionView, effectiveViewMode, searchField, searchTerm, selectedEdgeId, selectedNodeId]);
```

Render the companion tabs inside the main stage header and switch content:

```tsx
<GraphCompanionTabs activeView={companionView} onChange={setCompanionView} />
{companionView === 'graph' ? (
  <GraphView
    nodes={visibleGraph.nodes}
    edges={visibleGraph.edges}
    selectedNodeId={selectedNodeId}
    selectedEdgeId={selectedEdgeId}
    viewMode={effectiveViewMode}
    hubThreshold={HUB_THRESHOLD}
    degreeById={index.degreeById}
    onSelectNode={(nodeId) => {
      setSelectedEdgeId(null);
      handleNodeSelect(nodeId);
    }}
    onSelectEdge={(edgeId) => {
      setSelectedNodeId(null);
      setSelectedEdgeId(edgeId);
    }}
  />
) : companionView === 'table' ? (
  <GraphDataTable
    rows={tableRows}
    selectedNodeId={selectedNodeId}
    onSelectNode={handleSearchMatchSelect}
  />
) : companionView === 'timeline' ? (
  <GraphTimeline
    rows={timelineRows}
    selectedNodeId={selectedNodeId}
    onSelectNode={handleSearchMatchSelect}
  />
) : (
  <GraphSchemaSummary
    nodeTypes={schemaSummary.nodeTypes}
    edgeTypes={schemaSummary.edgeTypes}
  />
)}
```

Pass `edge={selectedEdge}` into `NodeInspector`.

Update `kg-dashboard/src/App.css` with companion surface selectors:

```css
.companion-tabs {
  margin-top: 0.75rem;
}

.companion-surface {
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid var(--border);
  border-radius: 8px;
  min-height: min(78svh, 920px);
  overflow: auto;
}

.companion-table,
.timeline-list,
.schema-grid {
  display: grid;
  gap: 0;
}

.companion-table__row,
.timeline-row,
.schema-row {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 0.75rem;
  padding: 0.8rem 1rem;
  border-top: 1px solid var(--border);
}
```

- [ ] **Step 4: Run the full frontend verification set and confirm it passes**

Run:

```powershell
cd kg-dashboard
npm test
npm run lint
npm run build
```

Expected:

- `npm test` PASS
- `npm run lint` PASS
- `npm run build` PASS

Then run manual browser verification:

```powershell
cd kg-dashboard
npm run build
python -m http.server 4177 --bind 127.0.0.1 --directory dist
```

Manual checks:

- Search `POL` and switch to `Table`
- Search `ATD` and switch to `Timeline`
- Select a graph edge and confirm `Edge` plus `Evidence` tabs render in the inspector
- Reload the page and confirm search term, companion tab, and selection restore from the URL

- [ ] **Step 5: Commit the integrated usability redesign**

```powershell
git add -- ^
  kg-dashboard/src/App.tsx ^
  kg-dashboard/src/App.css ^
  kg-dashboard/src/components/ui-rule-alignment.test.tsx
git add -- ^
  kg-dashboard/src/components/GraphCompanionTabs.tsx ^
  kg-dashboard/src/components/GraphDataTable.tsx ^
  kg-dashboard/src/components/GraphTimeline.tsx ^
  kg-dashboard/src/components/GraphSchemaSummary.tsx ^
  kg-dashboard/src/components/GraphSidebar.tsx ^
  kg-dashboard/src/components/GraphSidebar.test.tsx ^
  kg-dashboard/src/components/GraphView.tsx ^
  kg-dashboard/src/components/NodeInspector.tsx ^
  kg-dashboard/src/components/NodeInspector.test.tsx ^
  kg-dashboard/src/components/GraphCompanionViews.test.tsx
git add -- ^
  kg-dashboard/src/utils/dashboard-state.ts ^
  kg-dashboard/src/utils/dashboard-state.test.ts ^
  kg-dashboard/src/utils/graph-model.ts ^
  kg-dashboard/src/utils/graph-model.test.ts ^
  kg-dashboard/src/utils/graph-companion-data.ts ^
  kg-dashboard/src/utils/graph-companion-data.test.ts ^
  kg-dashboard/src/types/graph.ts
git commit -m "feat: redesign kg-dashboard for investigation workflows"
```

---

## Self-Review

### Spec coverage

- `FR-001`, `FR-005`, `FR-015` are covered by Task 5 integration in `App.tsx`
- `FR-002`, `FR-007`, `FR-008`, `FR-009` are covered by Task 3 companion-view utilities and components plus Task 5 wiring
- `FR-003`, `FR-004`, `SC-001`, `SC-002` are covered by Task 2
- `FR-010`, `FR-011`, `FR-012`, `FR-013`, `SC-004` are covered by Task 4 plus Task 5
- `FR-014`, `SC-005`, `NFR-006` are covered by Task 1 plus Task 5
- `NFR-001`, `NFR-004`, `SC-006` are guarded in Task 5 tests and verification
- `NFR-002`, `NFR-003` are handled as manual verification expectations in Task 5

### Placeholder scan

- No unresolved placeholder markers remain in the task steps
- Every task has explicit file paths, tests, commands, and commit scopes

### Type consistency

- `GraphCompanionView`, `GraphSearchField`, and `SearchMatch` are introduced first and reused consistently
- The plan keeps `NodeInspector.tsx` as the inspector entrypoint instead of renaming the component mid-plan
- URL state uses the same field names throughout:
  `query`, `searchField`, `viewMode`, `companionView`, `selectedNodeId`, `selectedEdgeId`
