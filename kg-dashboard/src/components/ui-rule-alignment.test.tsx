import { readFileSync } from 'node:fs';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { GraphCompanionTabs } from './GraphCompanionTabs';
import { GraphDataTable } from './GraphDataTable';
import { GraphSidebar } from './GraphSidebar';
import { NodeInspector } from './NodeInspector';
import type { GraphMetrics, SearchMatch } from '../types/graph';

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

const searchMatch: SearchMatch = {
  node: {
    data: {
      id: 'hub/mosb',
      label: 'MOSB',
      type: 'Hub',
    },
  },
  matchedField: 'label',
  reasonLabel: 'Matched in label',
};

describe('kg-dashboard UI rule alignment', () => {
  it('does not render a hero-style sidebar panel for the graph tool', () => {
    const markup = renderToStaticMarkup(
      <GraphSidebar
        metrics={metrics}
        searchTerm=""
        searchField="all"
        searchMatches={[searchMatch]}
        classFilter=""
        propertyFilter=""
        relationTypeFilter=""
        classOptions={['Hub', 'Shipment']}
        propertyOptions={['occursAt']}
        relationTypeOptions={['occursAt']}
        ontologyPresets={[{ id: 'all', label: 'All ontology' }]}
        savedQueries={[]}
        hubSummaries={[]}
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

    expect(markup).not.toContain('panel--hero');
    expect(markup).not.toContain('Search first, not everything at once');
  });

  it('does not render nested card classes inside sidebar and inspector sections', () => {
    const sidebarMarkup = renderToStaticMarkup(
      <GraphSidebar
        metrics={metrics}
        searchTerm=""
        searchField="all"
        searchMatches={[searchMatch]}
        classFilter=""
        propertyFilter=""
        relationTypeFilter=""
        classOptions={['Hub', 'Shipment']}
        propertyOptions={['occursAt']}
        relationTypeOptions={['occursAt']}
        ontologyPresets={[{ id: 'all', label: 'All ontology' }]}
        savedQueries={[]}
        hubSummaries={[
          {
            id: 'hub/mosb',
            label: 'MOSB',
            type: 'Hub',
            shipment: 10,
            vessel: 2,
            vendor: 1,
          },
        ]}
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
        selectedNodeLabel="MOSB"
        selectedNodeType="Hub"
        hubThreshold={200}
        canClearSelection={true}
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
    const inspectorMarkup = renderToStaticMarkup(
      <NodeInspector
        node={{
          data: {
            id: 'hub/mosb',
            label: 'MOSB',
            type: 'Hub',
          },
        }}
        edge={null}
        degree={10}
        onClose={() => {}}
      />,
    );

    expect(sidebarMarkup).not.toContain('metric-card');
    expect(sidebarMarkup).not.toContain('hub-summary-card');
    expect(sidebarMarkup).not.toContain('selection-card');
    expect(inspectorMarkup).not.toContain('detail-card');
  });

  it('keeps border radius at 8px or less and avoids negative letter-spacing in App.css', () => {
    const css = readFileSync(new URL('../App.css', import.meta.url), 'utf-8');
    const radiusValues = [...css.matchAll(/border-radius:\s*(\d+)px/g)].map((match) =>
      Number(match[1]),
    );

    expect(css).not.toMatch(/letter-spacing:\s*-/);
    expect(radiusValues.length).toBeGreaterThan(0);
    expect(radiusValues.every((value) => value <= 8)).toBe(true);
  });

  it('does not style the main graph shell as a decorative preview frame', () => {
    const css = readFileSync(new URL('../App.css', import.meta.url), 'utf-8');
    const graphShellBlock = css.match(/\.graph-canvas-shell\s*\{[^}]+\}/)?.[0] ?? '';

    expect(graphShellBlock).not.toContain('radial-gradient');
    expect(graphShellBlock).not.toContain('box-shadow');
  });

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

  it('uses graph-first shell widths, a thin toolbar, and compact-panel selectors', () => {
    const css = readFileSync(new URL('../App.css', import.meta.url), 'utf-8');

    expect(css).toMatch(
      /grid-template-columns:\s*minmax\(200px,\s*220px\)\s+minmax\(0,\s*1fr\)\s+minmax\(220px,\s*240px\)/,
    );
    expect(css).toMatch(/\.dashboard-main\s*\{[^}]*min-width:\s*0/);
    expect(css).toMatch(/\.dashboard-toolbar\s*\{[^}]*min-height:\s*56px/);
    expect(css).toMatch(/@media\s*\(max-width:\s*1023px\)/);
    expect(css).toMatch(/data-compact-panel='controls'/);
    expect(css).toMatch(/data-compact-panel='inspector'/);
    expect(css).toMatch(
      /@media\s*\(max-width:\s*1023px\)\s*\{[\s\S]*\.dashboard-stage,\s*\.graph-canvas-shell,\s*\.companion-surface\s*\{[^}]*min-height:\s*68svh/,
    );
  });

  it('caps desktop graph box height and keeps companion tabs compact', () => {
    const css = readFileSync(new URL('../App.css', import.meta.url), 'utf-8');

    expect(css).toMatch(/\.dashboard-shell\s*\{[^}]*height:\s*calc\(100svh\s*-\s*1\.5rem\)/);
    expect(css).toMatch(/\.companion-tabs\s*\{[^}]*grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\)/);
    expect(css).toMatch(/\.graph-canvas-shell\s*\{[^}]*height:\s*min\(62svh,\s*680px\)/);
    expect(css).toMatch(/\.companion-surface\s*\{[^}]*height:\s*min\(62svh,\s*680px\)/);
  });
});
