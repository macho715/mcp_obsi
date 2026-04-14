import type { GraphCompanionView, GraphSearchField, GraphViewMode } from '../types/graph';

export interface GraphManualViewState {
  pinnedNodeIds: string[];
  hiddenNodeIds: string[];
  expandedNodeIds: string[];
}

export interface DashboardViewState extends GraphManualViewState {
  query: string;
  searchField: GraphSearchField;
  classFilter: string;
  propertyFilter: string;
  relationTypeFilter: string;
  viewMode: GraphViewMode;
  companionView: GraphCompanionView;
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
}

export interface DashboardUrlState extends DashboardViewState {
  compareLeftId: string | null;
  compareRightId: string | null;
}

const VIEW_MODES: GraphViewMode[] = ['summary', 'issues', 'search', 'ego'];
const COMPANION_VIEWS: GraphCompanionView[] = ['graph', 'table', 'timeline', 'schema'];
const SEARCH_FIELDS: GraphSearchField[] = ['all', 'coe', 'pol', 'pod', 'shipMode', 'atd', 'ata'];

export const DEFAULT_DASHBOARD_URL_STATE: DashboardUrlState = {
  query: '',
  searchField: 'all',
  classFilter: '',
  propertyFilter: '',
  relationTypeFilter: '',
  viewMode: 'summary',
  companionView: 'graph',
  selectedNodeId: null,
  selectedEdgeId: null,
  pinnedNodeIds: [],
  hiddenNodeIds: [],
  expandedNodeIds: [],
  compareLeftId: null,
  compareRightId: null,
};

function parseNodeIdList(value: string | null): string[] {
  if (!value) {
    return [];
  }

  return Array.from(
    new Set(
      value
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
    ),
  );
}

function serializeNodeIdList(ids: string[]): string | null {
  if (!ids.length) {
    return null;
  }

  return Array.from(new Set(ids)).sort((left, right) => left.localeCompare(right)).join(',');
}

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
    classFilter: params.get('class') ?? '',
    propertyFilter: params.get('property') ?? '',
    relationTypeFilter: params.get('relationType') ?? '',
    viewMode: VIEW_MODES.includes(viewMode as GraphViewMode)
      ? (viewMode as GraphViewMode)
      : DEFAULT_DASHBOARD_URL_STATE.viewMode,
    companionView: COMPANION_VIEWS.includes(companionView as GraphCompanionView)
      ? (companionView as GraphCompanionView)
      : DEFAULT_DASHBOARD_URL_STATE.companionView,
    selectedNodeId: params.get('node'),
    selectedEdgeId: params.get('edge'),
    pinnedNodeIds: parseNodeIdList(params.get('pin')),
    hiddenNodeIds: parseNodeIdList(params.get('hide')),
    expandedNodeIds: parseNodeIdList(params.get('expand')),
    compareLeftId: params.get('compareLeft'),
    compareRightId: params.get('compareRight'),
  };
}

export function buildDashboardUrlSearch(state: DashboardUrlState): string {
  const params = new URLSearchParams();

  if (state.query.trim()) {
    params.set('q', state.query);
  }
  if (state.searchField !== 'all') {
    params.set('field', state.searchField);
  }
  if (state.classFilter) {
    params.set('class', state.classFilter);
  }
  if (state.propertyFilter) {
    params.set('property', state.propertyFilter);
  }
  if (state.relationTypeFilter) {
    params.set('relationType', state.relationTypeFilter);
  }
  if (state.viewMode !== 'summary') {
    params.set('view', state.viewMode);
  }
  if (state.companionView !== 'graph') {
    params.set('panel', state.companionView);
  }
  if (state.selectedNodeId) {
    params.set('node', state.selectedNodeId);
  }
  if (state.selectedEdgeId) {
    params.set('edge', state.selectedEdgeId);
  }

  const pinned = serializeNodeIdList(state.pinnedNodeIds);
  if (pinned) {
    params.set('pin', pinned);
  }

  const hidden = serializeNodeIdList(state.hiddenNodeIds);
  if (hidden) {
    params.set('hide', hidden);
  }

  const expanded = serializeNodeIdList(state.expandedNodeIds);
  if (expanded) {
    params.set('expand', expanded);
  }

  if (state.compareLeftId) {
    params.set('compareLeft', state.compareLeftId);
  }

  if (state.compareRightId) {
    params.set('compareRight', state.compareRightId);
  }

  const query = params.toString();
  return query ? `?${query}` : '';
}
