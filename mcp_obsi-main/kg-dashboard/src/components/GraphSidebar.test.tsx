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
        classFilter=""
        propertyFilter=""
        relationTypeFilter=""
        classOptions={['Hub', 'Shipment']}
        propertyOptions={['occursAt']}
        relationTypeOptions={['occursAt']}
        ontologyPresets={[{ id: 'all', label: 'All ontology' }]}
        savedQueries={[]}
        hubSummaries={[]}
        viewMode="search"
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
    expect(markup).toMatch(
      /<section class="panel"><div class="panel-header"><div><div class="section-label">Selection<\/div><h2 class="section-title">Current focus<\/h2>/,
    );

    const sectionIds = Array.from(markup.matchAll(/data-section-id="([^"]+)"/g)).map(
      (match) => match[1],
    );

    expect(sectionIds).toEqual([
      'ontology-query',
      'investigation-view',
      'infra-summary',
      'metrics',
    ]);

    for (const sectionId of sectionIds) {
      expect(markup).toContain(
        `<details class="collapsible-section" data-section-id="${sectionId}">`,
      );
    }
  });

  it('omits infra summary outside summary mode or without hub summaries', () => {
    const issuesMarkup = renderToStaticMarkup(
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
        viewMode="issues"
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

    const emptySummaryMarkup = renderToStaticMarkup(
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

    expect(issuesMarkup).not.toMatch(/data-section-id="infra-summary"/);
    expect(emptySummaryMarkup).not.toMatch(/data-section-id="infra-summary"/);
  });
});
