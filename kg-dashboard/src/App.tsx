import {
  Suspense,
  lazy,
  startTransition,
  useDeferredValue,
  useEffect,
  useMemo,
  useState,
} from 'react';
import './App.css';
import { GraphCompanionTabs } from './components/GraphCompanionTabs';
import { GraphDataTable } from './components/GraphDataTable';
import { GraphSchemaSummary } from './components/GraphSchemaSummary';
import { GraphSidebar } from './components/GraphSidebar';
import { GraphTimeline } from './components/GraphTimeline';
import { NodeInspector } from './components/NodeInspector';
import type {
  GraphCompanionView,
  GraphEdge,
  GraphNode,
  GraphQueryState,
  GraphSlice,
  OntologyQueryPresetId,
  GraphViewMode,
  ProvenanceChain,
  SavedGraphQuery,
  VisibilityReason,
} from './types/graph';
import {
  DEFAULT_DASHBOARD_URL_STATE,
  buildDashboardUrlSearch,
  parseDashboardUrlState,
  type DashboardViewState,
} from './utils/dashboard-state';
import { buildCompareUnionSlice, buildGraphCompareDiff } from './utils/graph-compare';
import {
  buildSchemaSummaryRows,
  buildTableRows,
  buildTimelineRows,
} from './utils/graph-companion-data';
import { applyManualGraphState } from './utils/graph-manual-controls';
import {
  buildEgoView,
  buildGraphIndex,
  buildIssueView,
  buildSearchView,
  buildSummaryView,
  deriveMetrics,
  deriveProvenanceChain,
  findSearchMatches,
  getCollapsedCountSummary,
  getEdgeId,
  getNodeLabel,
} from './utils/graph-model';

const HUB_THRESHOLD = 200;
const SAVED_QUERY_STORAGE_KEY = 'kg-dashboard:saved-queries';
const SAVED_VIEWS_STORAGE_KEY = 'kg-dashboard/saved-investigation-views/v1';
const GraphView = lazy(() => import('./components/GraphView'));
const ONTOLOGY_QUERY_PRESETS: Array<{
  id: OntologyQueryPresetId;
  label: string;
  query: Pick<GraphQueryState, 'classFilter' | 'propertyFilter' | 'relationTypeFilter'>;
}> = [
  {
    id: 'all',
    label: 'All ontology',
    query: { classFilter: '', propertyFilter: '', relationTypeFilter: '' },
  },
  {
    id: 'issue_location',
    label: 'Issue + location',
    query: { classFilter: 'LogisticsIssue', propertyFilter: 'occursAt', relationTypeFilter: '' },
  },
  {
    id: 'shipment_route',
    label: 'Shipment route',
    query: { classFilter: 'Shipment', propertyFilter: 'deliveredTo', relationTypeFilter: '' },
  },
  {
    id: 'vendor_network',
    label: 'Vendor network',
    query: { classFilter: 'Vendor', propertyFilter: 'suppliedBy', relationTypeFilter: '' },
  },
];

interface SavedInvestigationView {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  viewState: DashboardViewState;
}

const VIEW_COPY: Record<GraphViewMode, { title: string; description: string }> = {
  summary: {
    title: '요약 뷰',
    description: '이슈와 핵심 인프라만 남겨 전체 관계를 빠르게 읽는 기본 화면입니다.',
  },
  issues: {
    title: '이슈 중심 뷰',
    description: 'LogisticsIssue와 연결된 핵심 위치만 남겨 문제 흐름을 좁혀 봅니다.',
  },
  search: {
    title: '검색 뷰',
    description: '검색된 노드와 가까운 이웃만 펼쳐 전체 그래프 대신 관련 맥락만 보여줍니다.',
  },
  ego: {
    title: '선택 노드 뷰',
    description: '선택한 노드 주변 1~2 hop만 남겨 허브를 읽을 수 있는 크기로 줄입니다.',
  },
};

function App() {
  const initialUrlState =
    typeof window === 'undefined'
      ? DEFAULT_DASHBOARD_URL_STATE
      : parseDashboardUrlState(window.location.search);

  const [allNodes, setAllNodes] = useState<GraphNode[]>([]);
  const [allEdges, setAllEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<GraphViewMode>(initialUrlState.viewMode);
  const [companionView, setCompanionView] = useState<GraphCompanionView>(
    initialUrlState.companionView,
  );
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(initialUrlState.selectedNodeId);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(initialUrlState.selectedEdgeId);
  const [queryState, setQueryState] = useState<GraphQueryState>({
    term: initialUrlState.query,
    searchField: initialUrlState.searchField,
    classFilter: initialUrlState.classFilter,
    propertyFilter: initialUrlState.propertyFilter,
    relationTypeFilter: initialUrlState.relationTypeFilter,
  });
  const [savedQueries, setSavedQueries] = useState<SavedGraphQuery[]>([]);
  const [pinnedNodeIds, setPinnedNodeIds] = useState<string[]>(initialUrlState.pinnedNodeIds);
  const [hiddenNodeIds, setHiddenNodeIds] = useState<string[]>(initialUrlState.hiddenNodeIds);
  const [expandedNodeIds, setExpandedNodeIds] = useState<string[]>(
    initialUrlState.expandedNodeIds,
  );
  const [savedViews, setSavedViews] = useState<SavedInvestigationView[]>([]);
  const [compareLeftId, setCompareLeftId] = useState<string | null>(
    initialUrlState.compareLeftId,
  );
  const [compareRightId, setCompareRightId] = useState<string | null>(
    initialUrlState.compareRightId,
  );

  const deferredSearch = useDeferredValue(queryState.term);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      const raw = window.localStorage.getItem(SAVED_QUERY_STORAGE_KEY);
      if (!raw) {
        return;
      }
      const parsed = JSON.parse(raw) as SavedGraphQuery[];
      if (!Array.isArray(parsed)) {
        return;
      }
      setSavedQueries(parsed);
    } catch {
      setSavedQueries([]);
    }
  }, []);

  const persistSavedQueries = (next: SavedGraphQuery[]) => {
    setSavedQueries(next);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(SAVED_QUERY_STORAGE_KEY, JSON.stringify(next));
    }
  };

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      const raw = window.localStorage.getItem(SAVED_VIEWS_STORAGE_KEY);
      if (!raw) {
        return;
      }
      const parsed = JSON.parse(raw) as SavedInvestigationView[];
      if (!Array.isArray(parsed)) {
        return;
      }
      setSavedViews(
        parsed.filter(
          (item) =>
            item &&
            typeof item.id === 'string' &&
            typeof item.name === 'string' &&
            item.viewState != null,
        ),
      );
    } catch {
      setSavedViews([]);
    }
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    window.localStorage.setItem(SAVED_VIEWS_STORAGE_KEY, JSON.stringify(savedViews));
  }, [savedViews]);

  useEffect(() => {
    let active = true;

    async function loadGraph() {
      try {
        const [nodesResponse, edgesResponse] = await Promise.all([
          fetch('/data/nodes.json'),
          fetch('/data/edges.json'),
        ]);

        if (!nodesResponse.ok || !edgesResponse.ok) {
          throw new Error('그래프 자산을 불러오지 못했습니다.');
        }

        const [nodesData, edgesData] = (await Promise.all([
          nodesResponse.json(),
          edgesResponse.json(),
        ])) as [GraphNode[], GraphEdge[]];

        if (!active) {
          return;
        }

        startTransition(() => {
          setAllNodes(nodesData);
          setAllEdges(edgesData);
          setLoading(false);
          setError(null);
        });
      } catch (loadError) {
        if (!active) {
          return;
        }

        setLoading(false);
        setError(
          loadError instanceof Error
            ? loadError.message
            : '그래프 자산을 읽는 중 알 수 없는 오류가 발생했습니다.',
        );
      }
    }

    void loadGraph();

    return () => {
      active = false;
    };
  }, []);

  const activeViewState = useMemo<DashboardViewState>(
    () => ({
      query: queryState.term,
      searchField: queryState.searchField,
      classFilter: queryState.classFilter,
      propertyFilter: queryState.propertyFilter,
      relationTypeFilter: queryState.relationTypeFilter,
      viewMode,
      companionView,
      selectedNodeId,
      selectedEdgeId,
      pinnedNodeIds,
      hiddenNodeIds,
      expandedNodeIds,
    }),
    [
      companionView,
      expandedNodeIds,
      hiddenNodeIds,
      pinnedNodeIds,
      queryState.classFilter,
      queryState.propertyFilter,
      queryState.relationTypeFilter,
      queryState.searchField,
      queryState.term,
      selectedEdgeId,
      selectedNodeId,
      viewMode,
    ],
  );

  const index = useMemo(() => buildGraphIndex(allNodes, allEdges), [allNodes, allEdges]);
  const searchMatches = useMemo(
    () => findSearchMatches(allNodes, deferredSearch, queryState.searchField, 6),
    [allNodes, deferredSearch, queryState.searchField],
  );
  const classOptions = useMemo(
    () => [...new Set(allNodes.map((node) => node.data.type))].sort((left, right) => left.localeCompare(right)),
    [allNodes],
  );
  const propertyOptions = useMemo(
    () =>
      [...new Set(allEdges.map((edge) => edge.data.label).filter((label): label is string => Boolean(label)))]
        .sort((left, right) => left.localeCompare(right)),
    [allEdges],
  );
  const relationTypeOptions = useMemo(
    () =>
      [...new Set(allEdges.map((edge) => String(edge.data.relationType ?? edge.data.label ?? '')).filter(Boolean))]
        .sort((left, right) => left.localeCompare(right)),
    [allEdges],
  );
  const activeSlice = useMemo(
    () => buildSliceForState(allNodes, allEdges, activeViewState),
    [activeViewState, allEdges, allNodes],
  );
  const leftCompareView = useMemo(
    () => savedViews.find((item) => item.id === compareLeftId) ?? null,
    [compareLeftId, savedViews],
  );
  const rightCompareView = useMemo(
    () => savedViews.find((item) => item.id === compareRightId) ?? null,
    [compareRightId, savedViews],
  );
  const compareEnabled = Boolean(
    leftCompareView && rightCompareView && leftCompareView.id !== rightCompareView.id,
  );
  const compareState = useMemo(() => {
    if (!compareEnabled || !leftCompareView || !rightCompareView) {
      return null;
    }

    const leftSlice = buildSliceForState(allNodes, allEdges, leftCompareView.viewState);
    const rightSlice = buildSliceForState(allNodes, allEdges, rightCompareView.viewState);

    return {
      unionSlice: buildCompareUnionSlice(leftSlice, rightSlice),
      diff: buildGraphCompareDiff(leftSlice, rightSlice),
      leftName: leftCompareView.name,
      rightName: rightCompareView.name,
    };
  }, [allEdges, allNodes, compareEnabled, leftCompareView, rightCompareView]);

  const visibleGraph = compareState?.unionSlice ?? activeSlice;
  const compareDiff = compareState?.diff ?? null;

  const selectedNode = selectedNodeId ? index.nodeById.get(selectedNodeId) ?? null : null;
  const selectedNodeLabel = selectedNode ? getNodeLabel(selectedNode) : undefined;
  const selectedNodeType = selectedNode?.data.type;
  const selectedNodeDegree = selectedNodeId ? (index.degreeById.get(selectedNodeId) ?? 0) : null;
  const selectedEdge = selectedEdgeId
    ? visibleGraph.edges.find((edge) => getEdgeId(edge) === selectedEdgeId) ?? null
    : null;
  const effectiveViewMode: GraphViewMode =
    selectedNodeId && viewMode === 'ego' ? 'ego' : deferredSearch.trim() ? 'search' : viewMode;
  const selectedProvenance: ProvenanceChain = useMemo(
    () => deriveProvenanceChain(selectedNode, selectedEdge, index),
    [index, selectedEdge, selectedNode],
  );
  const selectedVisibilityReasons: VisibilityReason[] = useMemo(() => {
    const reasons: VisibilityReason[] = [];
    const query = queryState.term.trim();
    if (selectedNodeId && query) {
      const matched = searchMatches.some((item) => item.node.data.id === selectedNodeId);
      reasons.push({
        code: matched ? 'filter-match' : 'view-slice',
        label: matched ? 'Filter match' : 'Search slice context',
        detail: matched
          ? `Search term "${query}" matched this node${queryState.searchField === 'all' ? '' : ` in ${queryState.searchField.toUpperCase()}`}.`
          : 'This node is visible as search-neighbor context around matched results.',
      });
    } else {
      reasons.push({
        code: 'view-slice',
        label: 'Current view slice',
        detail: `Visible in ${effectiveViewMode} view.`,
      });
    }

    if (selectedNodeId && pinnedNodeIds.includes(selectedNodeId)) {
      reasons.push({
        code: 'manual-pin',
        label: 'Pinned manually',
        detail: 'You pinned this node in the sidebar.',
      });
    }

    if (selectedNodeId && expandedNodeIds.includes(selectedNodeId)) {
      reasons.push({
        code: 'manual-expand',
        label: '1-hop expansion',
        detail: 'This node is expanded with one-hop neighbors.',
      });
    }

    if (selectedNodeId && hiddenNodeIds.includes(selectedNodeId)) {
      reasons.push({
        code: 'manual-hidden-excluded',
        label: 'Hidden manually',
        detail: 'This node is hidden and should disappear after state refresh.',
      });
    }

    if (selectedEdgeId && selectedEdge) {
      reasons.push({
        code: 'view-slice',
        label: 'Visible relation',
        detail: `Edge ${getEdgeId(selectedEdge)} is inside the current rendered slice.`,
      });
    }

    return reasons;
  }, [
    effectiveViewMode,
    expandedNodeIds,
    hiddenNodeIds,
    pinnedNodeIds,
    queryState.searchField,
    queryState.term,
    searchMatches,
    selectedEdge,
    selectedEdgeId,
    selectedNodeId,
  ]);
  const metrics = useMemo(
    () => deriveMetrics(allNodes, allEdges, visibleGraph.nodes, visibleGraph.edges),
    [allEdges, allNodes, visibleGraph.edges, visibleGraph.nodes],
  );
  const hubSummaries = useMemo(
    () =>
      visibleGraph.nodes
        .filter((node) => node.data.type === 'Hub' || node.data.type === 'Site' || node.data.type === 'Warehouse')
        .map((node) => {
          const counts = getCollapsedCountSummary(node);
          return {
            id: node.data.id,
            label: getNodeLabel(node),
            type: node.data.type,
            shipment: counts?.shipment ?? 0,
            vessel: counts?.vessel ?? 0,
            vendor: counts?.vendor ?? 0,
          };
        })
        .sort((left, right) => {
          const shipmentDelta = right.shipment - left.shipment;
          if (shipmentDelta !== 0) {
            return shipmentDelta;
          }

          const typeRank = getInfraPriority(left.type) - getInfraPriority(right.type);
          if (typeRank !== 0) {
            return typeRank;
          }

          return left.label.localeCompare(right.label);
        }),
    [visibleGraph.nodes],
  );
  const tableRows = useMemo(
    () => buildTableRows(visibleGraph.nodes, index.degreeById),
    [index.degreeById, visibleGraph.nodes],
  );
  const timelineRows = useMemo(() => buildTimelineRows(visibleGraph.nodes), [visibleGraph.nodes]);
  const schemaSummary = useMemo(
    () => buildSchemaSummaryRows(visibleGraph.nodes, visibleGraph.edges),
    [visibleGraph.edges, visibleGraph.nodes],
  );
  const pinnedNodes = useMemo(
    () =>
      pinnedNodeIds.map((id) => ({
        id,
        label: index.nodeById.get(id) ? getNodeLabel(index.nodeById.get(id)!) : id,
      })),
    [pinnedNodeIds, index.nodeById],
  );
  const hiddenNodes = useMemo(
    () =>
      hiddenNodeIds.map((id) => ({
        id,
        label: index.nodeById.get(id) ? getNodeLabel(index.nodeById.get(id)!) : id,
      })),
    [hiddenNodeIds, index.nodeById],
  );
  const expandedNodes = useMemo(
    () =>
      expandedNodeIds.map((id) => ({
        id,
        label: index.nodeById.get(id) ? getNodeLabel(index.nodeById.get(id)!) : id,
      })),
    [expandedNodeIds, index.nodeById],
  );

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const search = buildDashboardUrlSearch({
      ...activeViewState,
      viewMode: effectiveViewMode,
      compareLeftId,
      compareRightId,
    });

    window.history.replaceState({}, '', `${window.location.pathname}${search}`);
  }, [activeViewState, compareLeftId, compareRightId, effectiveViewMode]);

  useEffect(() => {
    if (selectedNodeId && !index.nodeById.has(selectedNodeId)) {
      setSelectedNodeId(null);
    }
  }, [index.nodeById, selectedNodeId]);

  useEffect(() => {
    if (selectedEdgeId && !visibleGraph.edges.some((edge) => getEdgeId(edge) === selectedEdgeId)) {
      setSelectedEdgeId(null);
    }
  }, [selectedEdgeId, visibleGraph.edges]);

  useEffect(() => {
    if (compareLeftId && !savedViews.some((item) => item.id === compareLeftId)) {
      setCompareLeftId(null);
    }

    if (compareRightId && !savedViews.some((item) => item.id === compareRightId)) {
      setCompareRightId(null);
    }
  }, [compareLeftId, compareRightId, savedViews]);

  const handleSearchTermChange = (value: string) => {
    setQueryState((current) => ({ ...current, term: value }));

    startTransition(() => {
      setSelectedEdgeId(null);
      if (value.trim()) {
        setSelectedNodeId(null);
        setViewMode('search');
        return;
      }

      setViewMode(selectedNodeId ? 'ego' : 'summary');
    });
  };

  const handleSearchFieldChange = (value: GraphQueryState['searchField']) => {
    setQueryState((current) => ({ ...current, searchField: value }));
    setSelectedEdgeId(null);

    if (queryState.term.trim()) {
      setViewMode('search');
      setSelectedNodeId(null);
    }
  };

  const handleClassFilterChange = (value: string) => {
    setQueryState((current) => ({ ...current, classFilter: value }));
    setSelectedEdgeId(null);
  };
  const handlePropertyFilterChange = (value: string) => {
    setQueryState((current) => ({ ...current, propertyFilter: value }));
    setSelectedEdgeId(null);
  };
  const handleRelationTypeFilterChange = (value: string) => {
    setQueryState((current) => ({ ...current, relationTypeFilter: value }));
    setSelectedEdgeId(null);
  };
  const handlePresetApply = (presetId: OntologyQueryPresetId) => {
    const preset = ONTOLOGY_QUERY_PRESETS.find((item) => item.id === presetId);
    if (!preset) {
      return;
    }
    setQueryState((current) => ({ ...current, ...preset.query }));
    setSelectedEdgeId(null);
  };
  const handleSaveCurrentQuery = () => {
    const name = `${queryState.term.trim() || 'query'} · ${new Date().toISOString().slice(0, 19)}`;
    const nextQuery: SavedGraphQuery = {
      id: `query-${Date.now()}`,
      name,
      query: { ...queryState },
    };
    persistSavedQueries([nextQuery, ...savedQueries].slice(0, 10));
  };
  const handleApplySavedQuery = (queryId: string) => {
    const savedQuery = savedQueries.find((item) => item.id === queryId);
    if (!savedQuery) {
      return;
    }
    setQueryState(savedQuery.query);
    setPinnedNodeIds([]);
    setHiddenNodeIds([]);
    setExpandedNodeIds([]);
    setSelectedEdgeId(null);
    setSelectedNodeId(null);
    setViewMode(savedQuery.query.term.trim() ? 'search' : 'summary');
  };

  const handleViewModeChange = (mode: GraphViewMode) => {
    setViewMode(mode);
    setSelectedEdgeId(null);

    if (mode !== 'ego' && !deferredSearch.trim()) {
      setSelectedNodeId(null);
    }
  };

  const handleNodeSelect = (nodeId: string | null) => {
    setSelectedEdgeId(null);
    setSelectedNodeId(nodeId);

    if (nodeId) {
      setViewMode('ego');
      return;
    }

    setViewMode(deferredSearch.trim() ? 'search' : 'summary');
  };

  const handleEdgeSelect = (edgeId: string | null) => {
    setSelectedNodeId(null);
    setSelectedEdgeId(edgeId);
  };

  const handleClearSelection = () => {
    setSelectedNodeId(null);
    setSelectedEdgeId(null);
    setViewMode(deferredSearch.trim() ? 'search' : 'summary');
  };

  const handleSearchMatchSelect = (nodeId: string) => {
    setSelectedEdgeId(null);
    setSelectedNodeId(nodeId);
    setViewMode('ego');
  };

  const addUniqueNodeId = (current: string[], nodeId: string): string[] =>
    current.includes(nodeId) ? current : [...current, nodeId];

  const removeNodeId = (current: string[], nodeId: string): string[] =>
    current.filter((value) => value !== nodeId);

  const handlePinSelection = () => {
    if (!selectedNodeId) {
      return;
    }

    setPinnedNodeIds((current) => addUniqueNodeId(current, selectedNodeId));
    setHiddenNodeIds((current) => removeNodeId(current, selectedNodeId));
  };

  const handleHideSelection = () => {
    if (!selectedNodeId) {
      return;
    }

    setPinnedNodeIds((current) => removeNodeId(current, selectedNodeId));
    setExpandedNodeIds((current) => removeNodeId(current, selectedNodeId));
    setHiddenNodeIds((current) => addUniqueNodeId(current, selectedNodeId));
    setSelectedNodeId(null);
    setSelectedEdgeId(null);
    setViewMode(deferredSearch.trim() ? 'search' : 'summary');
  };

  const handleExpandSelection = () => {
    if (!selectedNodeId) {
      return;
    }

    setHiddenNodeIds((current) => removeNodeId(current, selectedNodeId));
    setExpandedNodeIds((current) => addUniqueNodeId(current, selectedNodeId));
  };

  const handleResetManualState = () => {
    setPinnedNodeIds([]);
    setHiddenNodeIds([]);
    setExpandedNodeIds([]);
  };

  const handleCopyCurrentStateLink = async () => {
    if (typeof window === 'undefined') {
      return;
    }

    const shareUrl = `${window.location.origin}${window.location.pathname}${buildDashboardUrlSearch({
      ...activeViewState,
      viewMode: effectiveViewMode,
      compareLeftId,
      compareRightId,
    })}`;

    if (window.navigator?.clipboard?.writeText) {
      await window.navigator.clipboard.writeText(shareUrl);
      return;
    }

    window.prompt('Copy this investigation URL', shareUrl);
  };

  const handleSaveCurrentView = () => {
    if (typeof window === 'undefined') {
      return;
    }

    const name = window.prompt('Saved view name', `View ${savedViews.length + 1}`)?.trim();
    if (!name) {
      return;
    }

    const description = window.prompt('Saved view description', '')?.trim() ?? '';
    const createdAt = new Date().toISOString();
    const nextViewState: DashboardViewState = {
      ...activeViewState,
      viewMode: effectiveViewMode,
    };

    const next: SavedInvestigationView = {
      id: `view-${createdAt}-${Math.random().toString(16).slice(2, 8)}`,
      name,
      description,
      createdAt,
      viewState: nextViewState,
    };

    setSavedViews((current) => [next, ...current].slice(0, 30));
    if (!compareLeftId) {
      setCompareLeftId(next.id);
    } else if (!compareRightId) {
      setCompareRightId(next.id);
    }
  };

  const handleLoadSavedView = (viewId: string) => {
    const target = savedViews.find((item) => item.id === viewId);
    if (!target) {
      return;
    }

    const state = target.viewState;
    setQueryState({
      term: state.query,
      searchField: state.searchField,
      classFilter: state.classFilter,
      propertyFilter: state.propertyFilter,
      relationTypeFilter: state.relationTypeFilter,
    });
    setViewMode(state.viewMode);
    setCompanionView(state.companionView);
    setSelectedNodeId(state.selectedNodeId);
    setSelectedEdgeId(state.selectedEdgeId);
    setPinnedNodeIds(state.pinnedNodeIds);
    setHiddenNodeIds(state.hiddenNodeIds);
    setExpandedNodeIds(state.expandedNodeIds);
  };

  const handleDeleteSavedView = (viewId: string) => {
    setSavedViews((current) => current.filter((item) => item.id !== viewId));
  };

  return (
    <div className="dashboard-shell">
      <GraphSidebar
        metrics={metrics}
        viewMode={effectiveViewMode}
        searchTerm={queryState.term}
        searchField={queryState.searchField}
        searchMatches={searchMatches}
        hubSummaries={hubSummaries}
        classFilter={queryState.classFilter}
        propertyFilter={queryState.propertyFilter}
        relationTypeFilter={queryState.relationTypeFilter}
        classOptions={classOptions}
        propertyOptions={propertyOptions}
        relationTypeOptions={relationTypeOptions}
        ontologyPresets={ONTOLOGY_QUERY_PRESETS}
        savedQueries={savedQueries}
        onSearchTermChange={handleSearchTermChange}
        onSearchFieldChange={handleSearchFieldChange}
        onClassFilterChange={handleClassFilterChange}
        onPropertyFilterChange={handlePropertyFilterChange}
        onRelationTypeFilterChange={handleRelationTypeFilterChange}
        onApplyOntologyPreset={handlePresetApply}
        onSaveCurrentQuery={handleSaveCurrentQuery}
        onApplySavedQuery={handleApplySavedQuery}
        onSelectSearchMatch={handleSearchMatchSelect}
        onViewModeChange={handleViewModeChange}
        selectedNodeLabel={selectedNodeLabel}
        selectedNodeType={selectedNodeType}
        hubThreshold={HUB_THRESHOLD}
        canClearSelection={Boolean(selectedNode || selectedEdge)}
        onClearSelection={handleClearSelection}
        clearSelectionLabel={deferredSearch.trim() ? 'Back to search' : 'Clear'}
        canPinSelection={Boolean(selectedNodeId)}
        canHideSelection={Boolean(selectedNodeId)}
        canExpandSelection={Boolean(selectedNodeId)}
        onPinSelection={handlePinSelection}
        onHideSelection={handleHideSelection}
        onExpandSelection={handleExpandSelection}
        onResetManualState={handleResetManualState}
        pinnedNodes={pinnedNodes}
        hiddenNodes={hiddenNodes}
        expandedNodes={expandedNodes}
        onRemovePinnedNode={(nodeId) => setPinnedNodeIds((current) => removeNodeId(current, nodeId))}
        onRemoveHiddenNode={(nodeId) => setHiddenNodeIds((current) => removeNodeId(current, nodeId))}
        onRemoveExpandedNode={(nodeId) => setExpandedNodeIds((current) => removeNodeId(current, nodeId))}
        onCopyCurrentStateLink={() => void handleCopyCurrentStateLink()}
        onSaveCurrentView={handleSaveCurrentView}
        savedViews={savedViews}
        onLoadSavedView={handleLoadSavedView}
        onDeleteSavedView={handleDeleteSavedView}
        compareLeftId={compareLeftId}
        compareRightId={compareRightId}
        onSetCompareLeft={setCompareLeftId}
        onSetCompareRight={setCompareRightId}
        compareEnabled={compareEnabled}
      />

      <main className="dashboard-main">
        <header className="dashboard-topbar">
          <div className="dashboard-topbar__copy">
            <p className="dashboard-kicker">Knowledge graph tool</p>
            <h1>kg-dashboard</h1>
            <p className="dashboard-view-label">{VIEW_COPY[effectiveViewMode].title}</p>
            <p className="dashboard-description">{VIEW_COPY[effectiveViewMode].description}</p>
            {compareState ? (
              <p className="dashboard-description">
                Compare mode · Added (green), Removed (red), Changed (amber) · {compareState.leftName} →{' '}
                {compareState.rightName}
              </p>
            ) : null}
          </div>
          <dl className="dashboard-stat-grid">
            <div className="dashboard-stat">
              <dt>Visible</dt>
              <dd>
                {metrics.visibleNodes} nodes / {metrics.visibleEdges} edges
              </dd>
            </div>
            <div className="dashboard-stat">
              <dt>Hidden</dt>
              <dd>
                {metrics.hiddenNodes} nodes / {metrics.hiddenEdges} edges
              </dd>
            </div>
            <div className="dashboard-stat">
              <dt>Hotspots</dt>
              <dd>
                {metrics.issueCount} issues / {metrics.hubCount} hubs
              </dd>
            </div>
          </dl>
        </header>

        {loading ? (
          <section className="dashboard-stage">
            <div className="dashboard-status-card">
              <p className="dashboard-status-label">Loading</p>
              <h2>그래프 자산을 읽는 중입니다.</h2>
              <p>정적 JSON을 불러와 summary-first 뷰를 준비하고 있습니다.</p>
            </div>
          </section>
        ) : error ? (
          <section className="dashboard-stage">
            <div className="dashboard-status-card dashboard-status-card-error">
              <p className="dashboard-status-label">Error</p>
              <h2>그래프를 불러오지 못했습니다.</h2>
              <p>{error}</p>
            </div>
          </section>
        ) : (
          <section className="dashboard-stage">
            <GraphCompanionTabs activeView={companionView} onChange={setCompanionView} />

            {visibleGraph.nodes.length === 0 ? (
              <div className="dashboard-status-card">
                <p className="dashboard-status-label">No match</p>
                <h2>검색 결과가 없습니다.</h2>
                <p>다른 키워드를 입력하거나 요약 뷰로 돌아가 전체 구조를 좁혀 보세요.</p>
              </div>
            ) : companionView === 'graph' ? (
              <Suspense
                fallback={
                  <div className="dashboard-status-card">
                    <p className="dashboard-status-label">Loading</p>
                    <h2>그래프 엔진을 준비하고 있습니다.</h2>
                    <p>시각화 모듈을 나눠서 불러오는 중입니다.</p>
                  </div>
                }
              >
                <GraphView
                  nodes={visibleGraph.nodes}
                  edges={visibleGraph.edges}
                  selectedNodeId={selectedNodeId}
                  selectedEdgeId={selectedEdgeId}
                  viewMode={effectiveViewMode}
                  hubThreshold={HUB_THRESHOLD}
                  degreeById={index.degreeById}
                  onSelectNode={handleNodeSelect}
                  onSelectEdge={handleEdgeSelect}
                  compareDiff={compareDiff}
                />
              </Suspense>
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
          </section>
        )}
      </main>

      <NodeInspector
        key={`${selectedNodeId ?? 'none'}:${selectedEdgeId ?? 'none'}`}
        node={selectedNode}
        edge={selectedEdge}
        degree={selectedNodeDegree}
        provenance={selectedProvenance}
        visibilityReasons={selectedVisibilityReasons}
        onClose={handleClearSelection}
      />
    </div>
  );
}

export default App;

function buildSliceForState(
  allNodes: GraphNode[],
  allEdges: GraphEdge[],
  state: DashboardViewState,
): GraphSlice {
  if (!allNodes.length) {
    return { nodes: [], edges: [] };
  }

  const query = state.query.trim();
  let baseSlice: GraphSlice;

  if (state.selectedNodeId && state.viewMode === 'ego') {
    baseSlice = buildEgoView(allNodes, allEdges, state.selectedNodeId);
  } else if (query) {
    baseSlice = buildSearchView(allNodes, allEdges, query, {
      hubThreshold: HUB_THRESHOLD,
      searchField: state.searchField,
    });
  } else {
    switch (state.viewMode) {
      case 'issues':
        baseSlice = buildIssueView(allNodes, allEdges);
        break;
      case 'search':
        baseSlice = { nodes: [], edges: [] };
        break;
      case 'ego':
      case 'summary':
      default:
        baseSlice = buildSummaryView(allNodes, allEdges);
        break;
    }
  }

  const filteredSlice = filterSliceByState(baseSlice, state);

  return applyManualGraphState(allNodes, allEdges, filteredSlice, {
    pinnedNodeIds: new Set(state.pinnedNodeIds),
    hiddenNodeIds: new Set(state.hiddenNodeIds),
    expandedNodeIds: new Set(state.expandedNodeIds),
  });
}

function filterSliceByState(
  slice: GraphSlice,
  state: Pick<DashboardViewState, 'classFilter' | 'propertyFilter' | 'relationTypeFilter'>,
): GraphSlice {
  const classFilter = state.classFilter.trim();
  const propertyFilter = state.propertyFilter.trim();
  const relationTypeFilter = state.relationTypeFilter.trim();

  if (!classFilter && !propertyFilter && !relationTypeFilter) {
    return slice;
  }

  const nodeById = new Map(slice.nodes.map((node) => [node.data.id, node]));
  const filteredEdges = slice.edges.filter((edge) => {
    const sourceNode = nodeById.get(edge.data.source);
    const targetNode = nodeById.get(edge.data.target);
    const edgeProperty = edge.data.label ?? '';
    const edgeRelationType = String(edge.data.relationType ?? edge.data.label ?? '');

    const classMatch =
      !classFilter ||
      sourceNode?.data.type === classFilter ||
      targetNode?.data.type === classFilter;
    const propertyMatch = !propertyFilter || edgeProperty === propertyFilter;
    const relationTypeMatch =
      !relationTypeFilter || edgeRelationType === relationTypeFilter;

    return classMatch && propertyMatch && relationTypeMatch;
  });

  if (filteredEdges.length === 0) {
    return { nodes: [], edges: [] };
  }

  const includedNodeIds = new Set<string>();
  filteredEdges.forEach((edge) => {
    includedNodeIds.add(edge.data.source);
    includedNodeIds.add(edge.data.target);
  });

  return {
    nodes: slice.nodes.filter((node) => includedNodeIds.has(node.data.id)),
    edges: filteredEdges,
  };
}

function getInfraPriority(type: string): number {
  if (type === 'Hub') {
    return 0;
  }

  if (type === 'Site') {
    return 1;
  }

  if (type === 'Warehouse') {
    return 2;
  }

  return 3;
}
