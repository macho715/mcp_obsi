import { useMemo, useState } from 'react';
import type {
  GraphMetrics,
  GraphSearchField,
  GraphViewMode,
  OntologyQueryPresetId,
  SavedGraphQuery,
  SearchMatch,
} from '../types/graph';
import { getNodeLabel } from '../utils/graph-model';

const DEFAULT_INFRA_SUMMARY_LIMIT = 5;
type InfraFilter = 'All' | 'Hub' | 'Site' | 'Warehouse';

export interface GraphSidebarProps {
  metrics: GraphMetrics;
  searchTerm: string;
  searchField: GraphSearchField;
  searchMatches: SearchMatch[];
  classFilter: string;
  propertyFilter: string;
  relationTypeFilter: string;
  classOptions: string[];
  propertyOptions: string[];
  relationTypeOptions: string[];
  ontologyPresets: Array<{ id: OntologyQueryPresetId; label: string }>;
  savedQueries: SavedGraphQuery[];
  hubSummaries: Array<{
    id: string;
    label: string;
    type: string;
    shipment: number;
    vessel: number;
    vendor: number;
  }>;
  viewMode: GraphViewMode;
  onSearchTermChange: (value: string) => void;
  onSearchFieldChange: (value: GraphSearchField) => void;
  onClassFilterChange: (value: string) => void;
  onPropertyFilterChange: (value: string) => void;
  onRelationTypeFilterChange: (value: string) => void;
  onApplyOntologyPreset: (presetId: OntologyQueryPresetId) => void;
  onSaveCurrentQuery: () => void;
  onApplySavedQuery: (queryId: string) => void;
  onSelectSearchMatch: (nodeId: string) => void;
  onViewModeChange: (mode: GraphViewMode) => void;
  selectedNodeLabel?: string;
  selectedNodeType?: string;
  hubThreshold: number;
  canClearSelection: boolean;
  onClearSelection: () => void;
  clearSelectionLabel: string;
  canPinSelection: boolean;
  canHideSelection: boolean;
  canExpandSelection: boolean;
  onPinSelection: () => void;
  onHideSelection: () => void;
  onExpandSelection: () => void;
  onResetManualState: () => void;
  pinnedNodes: Array<{ id: string; label: string }>;
  hiddenNodes: Array<{ id: string; label: string }>;
  expandedNodes: Array<{ id: string; label: string }>;
  onRemovePinnedNode: (nodeId: string) => void;
  onRemoveHiddenNode: (nodeId: string) => void;
  onRemoveExpandedNode: (nodeId: string) => void;
}

const VIEW_MODE_LABELS: Record<GraphViewMode, string> = {
  summary: 'Summary',
  issues: 'Issues',
  search: 'Search',
  ego: 'Ego',
};
const INFRA_FILTERS: InfraFilter[] = ['All', 'Hub', 'Site', 'Warehouse'];
const SEARCH_FIELDS: Array<{ value: GraphSearchField; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'coe', label: 'COE' },
  { value: 'pol', label: 'POL' },
  { value: 'pod', label: 'POD' },
  { value: 'shipMode', label: 'Mode' },
  { value: 'atd', label: 'ATD' },
  { value: 'ata', label: 'ATA' },
];

function formatCount(value: number | undefined | null): string {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '—';
  }

  return new Intl.NumberFormat('en-US').format(value);
}

export function GraphSidebar({
  metrics,
  searchTerm,
  searchField,
  searchMatches,
  classFilter,
  propertyFilter,
  relationTypeFilter,
  classOptions,
  propertyOptions,
  relationTypeOptions,
  ontologyPresets,
  savedQueries,
  hubSummaries,
  viewMode,
  onSearchTermChange,
  onSearchFieldChange,
  onClassFilterChange,
  onPropertyFilterChange,
  onRelationTypeFilterChange,
  onApplyOntologyPreset,
  onSaveCurrentQuery,
  onApplySavedQuery,
  onSelectSearchMatch,
  onViewModeChange,
  selectedNodeLabel,
  selectedNodeType,
  hubThreshold,
  canClearSelection,
  onClearSelection,
  clearSelectionLabel,
  canPinSelection,
  canHideSelection,
  canExpandSelection,
  onPinSelection,
  onHideSelection,
  onExpandSelection,
  onResetManualState,
  pinnedNodes,
  hiddenNodes,
  expandedNodes,
  onRemovePinnedNode,
  onRemoveHiddenNode,
  onRemoveExpandedNode,
}: GraphSidebarProps) {
  const [showAllInfraSummaries, setShowAllInfraSummaries] = useState(false);
  const [infraFilter, setInfraFilter] = useState<InfraFilter>('All');
  const canExpandInfraSummary = viewMode === 'summary';
  const expandedInfraSummaries = canExpandInfraSummary && showAllInfraSummaries;
  const hiddenInfraSummaries = useMemo(
    () => hubSummaries.slice(DEFAULT_INFRA_SUMMARY_LIMIT),
    [hubSummaries],
  );
  const hiddenInfraSummaryCounts = useMemo(
    () => ({
      All: hiddenInfraSummaries.length,
      Hub: hiddenInfraSummaries.filter((item) => item.type === 'Hub').length,
      Site: hiddenInfraSummaries.filter((item) => item.type === 'Site').length,
      Warehouse: hiddenInfraSummaries.filter((item) => item.type === 'Warehouse').length,
    }),
    [hiddenInfraSummaries],
  );

  const filteredHiddenInfraSummaries = useMemo(() => {
    if (infraFilter === 'All') {
      return hiddenInfraSummaries;
    }

    return hiddenInfraSummaries.filter((item) => item.type === infraFilter);
  }, [hiddenInfraSummaries, infraFilter]);

  const visibleInfraSummaries = useMemo(() => {
    return hubSummaries.slice(0, DEFAULT_INFRA_SUMMARY_LIMIT);
  }, [hubSummaries]);

  const hiddenInfraSummaryCount = Math.max(
    hubSummaries.length - DEFAULT_INFRA_SUMMARY_LIMIT,
    0,
  );

  return (
    <aside className="dashboard-sidebar">
      <section className="panel">
        <div className="panel-header">
          <div>
            <div className="section-label">Search</div>
            <h2 className="section-title">Find a node</h2>
          </div>
          <span className="pill">{searchTerm.trim() ? 'Filtered' : 'All nodes'}</span>
        </div>

        <label className="field">
          <span className="field-label">Search term</span>
          <input
            className="search-input"
            type="search"
            placeholder="Search by issue, hub, vessel, or warehouse"
            value={searchTerm}
            onChange={(event) => onSearchTermChange(event.target.value)}
          />
        </label>

        <div className="search-chip-row" role="tablist" aria-label="Search fields">
          {SEARCH_FIELDS.map((field) => (
            <button
              key={field.value}
              type="button"
              className={searchField === field.value ? 'infra-filter-chip is-active' : 'infra-filter-chip'}
              onClick={() => onSearchFieldChange(field.value)}
              aria-pressed={searchField === field.value}
            >
              {field.label}
            </button>
          ))}
        </div>

        <p className="field-help">
          Use this to drive the first render. The full graph should stay collapsed by default.
        </p>

        {searchTerm.trim() ? (
          searchMatches.length > 0 ? (
            <>
              <div className="panel-header search-result-header">
                <div>
                  <div className="section-label">Matches</div>
                  <h3 className="section-title">{searchMatches.length} quick picks</h3>
                </div>
                <span className="pill pill--soft">click to open ego</span>
              </div>
              <div className="search-result-list">
                {searchMatches.map((match) => (
                  <button
                    key={match.node.data.id}
                    type="button"
                    className="search-result-item"
                    onClick={() => onSelectSearchMatch(match.node.data.id)}
                  >
                    <strong>{getNodeLabel(match.node)}</strong>
                    <span>{match.node.data.type}</span>
                    <span>{match.reasonLabel}</span>
                  </button>
                ))}
              </div>
            </>
          ) : (
            <p className="empty-copy">No quick matches. Try another label, hub, issue, or vessel name.</p>
          )
        ) : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <div className="section-label">Ontology Query</div>
            <h2 className="section-title">Class + relation filters</h2>
          </div>
        </div>

        <label className="field">
          <span className="field-label">Class browser</span>
          <select value={classFilter} onChange={(event) => onClassFilterChange(event.target.value)}>
            <option value="">All classes</option>
            {classOptions.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span className="field-label">Property browser</span>
          <select value={propertyFilter} onChange={(event) => onPropertyFilterChange(event.target.value)}>
            <option value="">All properties</option>
            {propertyOptions.map((property) => (
              <option key={property} value={property}>
                {property}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span className="field-label">Relation type browser</span>
          <select value={relationTypeFilter} onChange={(event) => onRelationTypeFilterChange(event.target.value)}>
            <option value="">All relation types</option>
            {relationTypeOptions.map((relation) => (
              <option key={relation} value={relation}>
                {relation}
              </option>
            ))}
          </select>
        </label>

        <div className="search-chip-row" role="tablist" aria-label="Ontology query presets">
          {ontologyPresets.map((preset) => (
            <button
              key={preset.id}
              type="button"
              className="infra-filter-chip"
              onClick={() => onApplyOntologyPreset(preset.id)}
            >
              {preset.label}
            </button>
          ))}
        </div>

        <div className="manual-node-actions">
          <button type="button" className="ghost-button" onClick={onSaveCurrentQuery}>
            Save current query
          </button>
        </div>
        {savedQueries.length > 0 ? (
          <div className="manual-node-list" role="list" aria-label="Saved queries">
            {savedQueries.map((query) => (
              <button
                key={query.id}
                type="button"
                className="search-result-item"
                onClick={() => onApplySavedQuery(query.id)}
              >
                <strong>{query.name}</strong>
                <span>
                  {query.query.classFilter || 'all'} / {query.query.propertyFilter || 'all'} /{' '}
                  {query.query.relationTypeFilter || 'all'}
                </span>
              </button>
            ))}
          </div>
        ) : (
          <p className="empty-copy">No saved queries yet.</p>
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <div className="section-label">View mode</div>
            <h2 className="section-title">Choose the slice</h2>
          </div>
        </div>

        <div className="segmented-control" role="tablist" aria-label="Graph view modes">
          {(Object.keys(VIEW_MODE_LABELS) as GraphViewMode[]).map((mode) => (
            <button
              key={mode}
              type="button"
              className={mode === viewMode ? 'segmented-control__button is-active' : 'segmented-control__button'}
              onClick={() => onViewModeChange(mode)}
              aria-pressed={mode === viewMode}
            >
              {VIEW_MODE_LABELS[mode]}
            </button>
          ))}
        </div>

        <div className="metric-row">
          <span>Hub threshold</span>
          <strong>{formatCount(hubThreshold)} connections</strong>
        </div>
        <p className="field-help">
          Nodes at or above this degree should collapse into summaries before expanding.
        </p>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <div className="section-label">Selection</div>
            <h2 className="section-title">Current focus</h2>
          </div>
          {canClearSelection ? (
            <button type="button" className="ghost-button" onClick={onClearSelection}>
              {clearSelectionLabel}
            </button>
          ) : null}
        </div>

        {selectedNodeLabel ? (
          <div className="selection-summary">
            <div className="metric-row">
              <span>Selected node</span>
              <strong>{selectedNodeLabel}</strong>
            </div>
            {selectedNodeType ? (
              <div className="metric-row">
                <span>Type</span>
                <strong>{selectedNodeType}</strong>
              </div>
            ) : null}
          </div>
        ) : (
          <p className="empty-copy">
            No node selected. Click a node to inspect it or clear the focus to return to browsing.
          </p>
        )}

        <div className="manual-node-actions">
          <button
            type="button"
            className="ghost-button"
            onClick={onPinSelection}
            disabled={!canPinSelection}
          >
            Pin
          </button>
          <button
            type="button"
            className="ghost-button"
            onClick={onHideSelection}
            disabled={!canHideSelection}
          >
            Hide
          </button>
          <button
            type="button"
            className="ghost-button"
            onClick={onExpandSelection}
            disabled={!canExpandSelection}
          >
            Expand 1-hop
          </button>
          <button type="button" className="ghost-button" onClick={onResetManualState}>
            Reset
          </button>
        </div>

        {pinnedNodes.length > 0 ? (
          <div className="manual-node-list" role="list" aria-label="Pinned nodes">
            <strong>Pinned</strong>
            {pinnedNodes.map((node) => (
              <button
                key={`pinned-${node.id}`}
                type="button"
                className="search-result-item"
                onClick={() => onRemovePinnedNode(node.id)}
              >
                <strong>{node.label}</strong>
                <span>Remove</span>
              </button>
            ))}
          </div>
        ) : null}

        {hiddenNodes.length > 0 ? (
          <div className="manual-node-list" role="list" aria-label="Hidden nodes">
            <strong>Hidden</strong>
            {hiddenNodes.map((node) => (
              <button
                key={`hidden-${node.id}`}
                type="button"
                className="search-result-item"
                onClick={() => onRemoveHiddenNode(node.id)}
              >
                <strong>{node.label}</strong>
                <span>Restore</span>
              </button>
            ))}
          </div>
        ) : null}

        {expandedNodes.length > 0 ? (
          <div className="manual-node-list" role="list" aria-label="Expanded nodes">
            <strong>Expanded</strong>
            {expandedNodes.map((node) => (
              <button
                key={`expanded-${node.id}`}
                type="button"
                className="search-result-item"
                onClick={() => onRemoveExpandedNode(node.id)}
              >
                <strong>{node.label}</strong>
                <span>Collapse</span>
              </button>
            ))}
          </div>
        ) : null}
      </section>

      {viewMode === 'summary' && hubSummaries.length > 0 ? (
        <section className="panel">
          <div className="panel-header">
            <div>
              <div className="section-label">Infra summary</div>
              <h2 className="section-title">Collapsed infra counts</h2>
            </div>
            <span className="pill pill--soft">{hubSummaries.length} infra nodes</span>
          </div>

          <div className="metric-row">
            <span>Shown first</span>
            <strong>{formatCount(visibleInfraSummaries.length)}</strong>
          </div>

          <div className="hub-summary-list" role="list" aria-label="Infra summary rows">
            {visibleInfraSummaries.map((hub) => (
              <div key={hub.id} className="metric-row" role="listitem">
                <span>
                  <strong>{hub.label}</strong> <span className="hub-summary-type">{hub.type}</span>
                </span>
                <strong>
                  Ship {formatCount(hub.shipment)} · Ves {formatCount(hub.vessel)} · Ven{' '}
                  {formatCount(hub.vendor)}
                </strong>
              </div>
            ))}
          </div>

          {hiddenInfraSummaryCount > 0 ? (
            <div className="infra-summary-actions">
              <button
                type="button"
                className="ghost-button infra-summary-toggle"
                onClick={() => {
                  setShowAllInfraSummaries((current) => !current);
                  setInfraFilter('All');
                }}
                aria-expanded={expandedInfraSummaries}
              >
                {expandedInfraSummaries
                  ? 'Collapse infra summary'
                  : `Show ${formatCount(hiddenInfraSummaryCount)} more`}
              </button>
              <p className="infra-summary-help">
                {expandedInfraSummaries
                  ? 'All hidden infra rows are visible below. Collapse the list to shorten the sidebar again.'
                  : `Only the top ${DEFAULT_INFRA_SUMMARY_LIMIT} infra rows are shown first. The button below opens only the hidden remainder.`}
              </p>

              {expandedInfraSummaries ? (
                <>
                  <p className="infra-summary-help infra-summary-help-secondary">
                    These counts apply only to the hidden rows below, not to the full summary list.
                  </p>
                  <div
                    className="infra-filter-chips"
                    role="tablist"
                    aria-label="Hidden infra summary filters"
                  >
                    {INFRA_FILTERS.map((filter) => (
                      <button
                        key={filter}
                        type="button"
                        className={
                          infraFilter === filter
                            ? 'infra-filter-chip is-active'
                            : 'infra-filter-chip'
                        }
                        onClick={() => setInfraFilter(filter)}
                        aria-pressed={infraFilter === filter}
                      >
                        <span>{filter}</span>
                        <span className="infra-filter-chip__count">
                          {formatCount(hiddenInfraSummaryCounts[filter])}
                        </span>
                      </button>
                    ))}
                  </div>

                  <div className="hub-summary-list hub-summary-list--expanded" role="list">
                    {filteredHiddenInfraSummaries.length > 0 ? (
                      filteredHiddenInfraSummaries.map((hub) => (
                        <div key={hub.id} className="metric-row" role="listitem">
                          <span>
                            <strong>{hub.label}</strong>{' '}
                            <span className="hub-summary-type">{hub.type}</span>
                          </span>
                          <strong>
                            Ship {formatCount(hub.shipment)} · Ves {formatCount(hub.vessel)} · Ven{' '}
                            {formatCount(hub.vendor)}
                          </strong>
                        </div>
                      ))
                    ) : (
                      <p className="empty-copy">
                        No hidden infra rows match the current filter.
                      </p>
                    )}
                  </div>
                </>
              ) : null}
            </div>
          ) : null}
        </section>
      ) : null}

      <section className="panel">
        <div className="panel-header">
          <div>
            <div className="section-label">Metrics</div>
            <h2 className="section-title">Current slice</h2>
          </div>
          <span className="pill pill--soft">Ready</span>
        </div>

        <div className="metric-row">
          <span>Total nodes</span>
          <strong>{formatCount(metrics?.totalNodes)}</strong>
        </div>
        <div className="metric-row">
          <span>Total edges</span>
          <strong>{formatCount(metrics?.totalEdges)}</strong>
        </div>
        <div className="metric-row">
          <span>Visible nodes</span>
          <strong>{formatCount(metrics?.visibleNodes)}</strong>
        </div>
        <div className="metric-row">
          <span>Visible edges</span>
          <strong>{formatCount(metrics?.visibleEdges)}</strong>
        </div>
        <div className="metric-row">
          <span>Hidden nodes</span>
          <strong>{formatCount(metrics?.hiddenNodes)}</strong>
        </div>
        <div className="metric-row">
          <span>Hidden edges</span>
          <strong>{formatCount(metrics?.hiddenEdges)}</strong>
        </div>
        <div className="metric-row">
          <span>Logistics issues</span>
          <strong>{formatCount(metrics?.issueCount)}</strong>
        </div>
        <div className="metric-row">
          <span>Hub nodes</span>
          <strong>{formatCount(metrics?.hubCount)}</strong>
        </div>
      </section>
    </aside>
  );
}
