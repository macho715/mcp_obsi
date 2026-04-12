import type { GraphCompanionView, GraphSearchField, GraphViewMode } from '../types/graph';

export interface DashboardUrlState {
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

  const query = params.toString();
  return query ? `?${query}` : '';
}
