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
import {
  buildEgoView,
  buildGraphIndex,
  buildIssueView,
  buildSearchView,
  buildSummaryView,
  deriveMetrics,
  findSearchMatches,
  getCollapsedCountSummary,
  getEdgeId,
  getNodeLabel,
} from './utils/graph-model';

const HUB_THRESHOLD = 200;
const GraphView = lazy(() => import('./components/GraphView'));

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
  const [searchTerm, setSearchTerm] = useState(initialUrlState.query);
  const [searchField, setSearchField] = useState<GraphSearchField>(initialUrlState.searchField);

  const deferredSearch = useDeferredValue(searchTerm);

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

  const index = useMemo(() => buildGraphIndex(allNodes, allEdges), [allNodes, allEdges]);
  const searchMatches = useMemo(
    () => findSearchMatches(allNodes, deferredSearch, searchField, 6),
    [allNodes, deferredSearch, searchField],
  );

  const visibleGraph = useMemo(() => {
    if (!allNodes.length) {
      return { nodes: [], edges: [] };
    }

    if (selectedNodeId && viewMode === 'ego') {
      return buildEgoView(allNodes, allEdges, selectedNodeId);
    }

    if (deferredSearch.trim()) {
      return buildSearchView(allNodes, allEdges, deferredSearch, {
        hubThreshold: HUB_THRESHOLD,
        searchField,
      });
    }

    switch (viewMode) {
      case 'issues':
        return buildIssueView(allNodes, allEdges);
      case 'ego':
        return buildSummaryView(allNodes, allEdges);
      case 'search':
        return { nodes: [], edges: [] };
      case 'summary':
      default:
        return buildSummaryView(allNodes, allEdges);
    }
  }, [allEdges, allNodes, deferredSearch, searchField, selectedNodeId, viewMode]);

  const selectedNode = selectedNodeId ? index.nodeById.get(selectedNodeId) ?? null : null;
  const selectedNodeLabel = selectedNode ? getNodeLabel(selectedNode) : undefined;
  const selectedNodeType = selectedNode?.data.type;
  const selectedNodeDegree = selectedNodeId ? (index.degreeById.get(selectedNodeId) ?? 0) : null;
  const selectedEdge = selectedEdgeId
    ? visibleGraph.edges.find((edge) => getEdgeId(edge) === selectedEdgeId) ?? null
    : null;
  const effectiveViewMode: GraphViewMode =
    selectedNodeId && viewMode === 'ego' ? 'ego' : deferredSearch.trim() ? 'search' : viewMode;
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

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

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

  const handleSearchTermChange = (value: string) => {
    setSearchTerm(value);

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

  const handleSearchFieldChange = (value: GraphSearchField) => {
    setSearchField(value);
    setSelectedEdgeId(null);

    if (searchTerm.trim()) {
      setViewMode('search');
      setSelectedNodeId(null);
    }
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

  return (
    <div className="dashboard-shell">
      <GraphSidebar
        metrics={metrics}
        viewMode={effectiveViewMode}
        searchTerm={searchTerm}
        searchField={searchField}
        searchMatches={searchMatches}
        hubSummaries={hubSummaries}
        onSearchTermChange={handleSearchTermChange}
        onSearchFieldChange={handleSearchFieldChange}
        onSelectSearchMatch={handleSearchMatchSelect}
        onViewModeChange={handleViewModeChange}
        selectedNodeLabel={selectedNodeLabel}
        selectedNodeType={selectedNodeType}
        hubThreshold={HUB_THRESHOLD}
        canClearSelection={Boolean(selectedNode || selectedEdge)}
        onClearSelection={handleClearSelection}
        clearSelectionLabel={deferredSearch.trim() ? 'Back to search' : 'Clear'}
      />

      <main className="dashboard-main">
        <header className="dashboard-topbar">
          <div className="dashboard-topbar__copy">
            <p className="dashboard-kicker">Knowledge graph tool</p>
            <h1>kg-dashboard</h1>
            <p className="dashboard-view-label">{VIEW_COPY[effectiveViewMode].title}</p>
            <p className="dashboard-description">{VIEW_COPY[effectiveViewMode].description}</p>
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
        onClose={handleClearSelection}
      />
    </div>
  );
}

export default App;

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
