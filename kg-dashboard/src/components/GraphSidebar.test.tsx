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
        onSearchTermChange={() => {}}
        onSearchFieldChange={() => {}}
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

    expect(markup).toContain('POL');
    expect(markup).toContain('POD');
    expect(markup).toContain('ATD');
    expect(markup).toContain('Matched in POL');
  });

  it('renders manual node controls and current override lists', () => {
    const markup = renderToStaticMarkup(
      <GraphSidebar
        metrics={metrics}
        searchTerm=""
        searchField="all"
        searchMatches={[]}
        hubSummaries={[]}
        viewMode="summary"
        onSearchTermChange={() => {}}
        onSearchFieldChange={() => {}}
        onSelectSearchMatch={() => {}}
        onViewModeChange={() => {}}
        hubThreshold={200}
        canClearSelection={true}
        onClearSelection={() => {}}
        clearSelectionLabel="Clear"
        canPinSelection={true}
        canHideSelection={true}
        canExpandSelection={true}
        onPinSelection={() => {}}
        onHideSelection={() => {}}
        onExpandSelection={() => {}}
        onResetManualState={() => {}}
        pinnedNodes={[{ id: 'hub/mosb', label: 'MOSB' }]}
        hiddenNodes={[{ id: 'shipment/1', label: 'HVDC-001' }]}
        expandedNodes={[{ id: 'shipment/a', label: 'Shipment A' }]}
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

    expect(markup).toContain('Pin');
    expect(markup).toContain('Hide');
    expect(markup).toContain('Expand 1-hop');
    expect(markup).toContain('Reset');
    expect(markup).toContain('MOSB');
    expect(markup).toContain('HVDC-001');
    expect(markup).toContain('Shipment A');
  });
});
