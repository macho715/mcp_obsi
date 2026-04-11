import { readFileSync } from 'node:fs';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { GraphSidebar } from './GraphSidebar';
import { NodeInspector } from './NodeInspector';
import type { GraphMetrics, GraphNode } from '../types/graph';

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

const searchMatch: GraphNode = {
  data: {
    id: 'hub/mosb',
    label: 'MOSB',
    type: 'Hub',
  },
};

describe('kg-dashboard UI rule alignment', () => {
  it('does not render a hero-style sidebar panel for the graph tool', () => {
    const markup = renderToStaticMarkup(
      <GraphSidebar
        metrics={metrics}
        searchTerm=""
        searchMatches={[searchMatch]}
        hubSummaries={[]}
        viewMode="summary"
        onSearchTermChange={() => {}}
        onSelectSearchMatch={() => {}}
        onViewModeChange={() => {}}
        hubThreshold={200}
        canClearSelection={false}
        onClearSelection={() => {}}
        clearSelectionLabel="Clear"
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
        searchMatches={[searchMatch]}
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
        onSelectSearchMatch={() => {}}
        onViewModeChange={() => {}}
        selectedNodeLabel="MOSB"
        selectedNodeType="Hub"
        hubThreshold={200}
        canClearSelection={true}
        onClearSelection={() => {}}
        clearSelectionLabel="Clear"
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
});
