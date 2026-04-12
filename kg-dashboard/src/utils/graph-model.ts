import type {
  GraphEdge,
  GraphIndex,
  GraphMetrics,
  GraphNode,
  GraphNodeType,
  ProvenanceChain,
  GraphSearchField,
  GraphSlice,
  SearchViewOptions,
  SearchMatch,
} from '../types/graph';

const INFRA_TYPES = new Set<GraphNodeType>(['Hub', 'Site', 'Warehouse']);
const ISSUE_TYPE: GraphNodeType = 'LogisticsIssue';
const LESSON_TYPE: GraphNodeType = 'IncidentLesson';
type CollapsedNeighborType = 'Shipment' | 'Vessel' | 'Vendor';
const COLLAPSED_TYPES: CollapsedNeighborType[] = ['Shipment', 'Vessel', 'Vendor'];
const SEARCHABLE_METADATA_ALIASES: Array<[string, string[]]> = [
  ['countryOfExport', ['coe', 'country of export']],
  ['portOfLoading', ['pol', 'port of loading']],
  ['portOfDischarge', ['pod', 'port of discharge']],
  ['shipMode', ['ship mode', 'shipping mode', 'mode']],
  ['actualDeparture', ['atd', 'actual departure']],
  ['actualArrival', ['ata', 'actual arrival']],
];
const SEARCH_FIELD_MAP: Record<GraphSearchField, string[]> = {
  all: [
    'id',
    'label',
    'rdf-schema#label',
    'countryOfExport',
    'portOfLoading',
    'portOfDischarge',
    'shipMode',
    'actualDeparture',
    'actualArrival',
  ],
  coe: ['countryOfExport'],
  pol: ['portOfLoading'],
  pod: ['portOfDischarge'],
  shipMode: ['shipMode'],
  atd: ['actualDeparture'],
  ata: ['actualArrival'],
};
const SEARCH_REASON_LABELS: Record<string, string> = {
  id: 'Matched in id',
  label: 'Matched in label',
  'rdf-schema#label': 'Matched in resolved label',
  countryOfExport: 'Matched in COE',
  portOfLoading: 'Matched in POL',
  portOfDischarge: 'Matched in POD',
  shipMode: 'Matched in Ship mode',
  actualDeparture: 'Matched in ATD',
  actualArrival: 'Matched in ATA',
};

function dedupeEdges(edges: GraphEdge[]): GraphEdge[] {
  const seen = new Set<string>();
  return edges.filter((edge) => {
    const key = `${edge.data.source}|${edge.data.target}|${edge.data.label ?? ''}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

export function getNodeLabel(node: GraphNode): string {
  return node.data['rdf-schema#label'] ?? node.data.label ?? node.data.id;
}

export function buildGraphIndex(nodes: GraphNode[], edges: GraphEdge[]): GraphIndex {
  const nodeById = new Map(nodes.map((node) => [node.data.id, node]));
  const adjacency = new Map<string, Set<string>>();
  const degreeById = new Map<string, number>();
  const edgesByNodeId = new Map<string, GraphEdge[]>();

  nodes.forEach((node) => {
    adjacency.set(node.data.id, new Set());
    degreeById.set(node.data.id, 0);
    edgesByNodeId.set(node.data.id, []);
  });

  edges.forEach((edge) => {
    const { source, target } = edge.data;
    if (!nodeById.has(source) || !nodeById.has(target)) {
      return;
    }

    adjacency.get(source)?.add(target);
    adjacency.get(target)?.add(source);
    degreeById.set(source, (degreeById.get(source) ?? 0) + 1);
    degreeById.set(target, (degreeById.get(target) ?? 0) + 1);
    edgesByNodeId.get(source)?.push(edge);
    edgesByNodeId.get(target)?.push(edge);
  });

  return { adjacency, degreeById, nodeById, edgesByNodeId };
}

export function computeDegrees(nodes: GraphNode[], edges: GraphEdge[]): Record<string, number> {
  return Object.fromEntries(buildGraphIndex(nodes, edges).degreeById.entries());
}

export function isHubNode(node: GraphNode, index: GraphIndex, hubThreshold = 200): boolean {
  return (index.degreeById.get(node.data.id) ?? 0) >= hubThreshold;
}

export function buildSummaryView(nodes: GraphNode[], edges: GraphEdge[]): GraphSlice {
  const baseNodes = nodes.filter(
    (node) => node.data.type === ISSUE_TYPE || INFRA_TYPES.has(node.data.type),
  );
  const index = buildGraphIndex(nodes, edges);
  const keptNodes = addIssueContextLessons(nodes, baseNodes, index);
  const keptIds = new Set(keptNodes.map((node) => node.data.id));
  const keptEdges = edges.filter(
    (edge) => keptIds.has(edge.data.source) && keptIds.has(edge.data.target),
  );
  const enrichedNodes = keptNodes.map((node) => {
    if (!INFRA_TYPES.has(node.data.type)) {
      return node;
    }

    const collapsedCounts = computeCollapsedCounts(node.data.id, keptIds, index);
    return {
      ...node,
      data: {
        ...node.data,
        collapsedShipmentCount: collapsedCounts.Shipment,
        collapsedVesselCount: collapsedCounts.Vessel,
        collapsedVendorCount: collapsedCounts.Vendor,
      },
    };
  });

  return {
    nodes: enrichedNodes,
    edges: dedupeEdges(keptEdges),
  };
}

export function buildIssueView(nodes: GraphNode[], edges: GraphEdge[]): GraphSlice {
  const baseNodes = nodes.filter(
    (node) => node.data.type === ISSUE_TYPE || INFRA_TYPES.has(node.data.type),
  );
  const index = buildGraphIndex(nodes, edges);
  const visibleIssueIds = collectVisibleIssueIds(baseNodes);
  const issueContextInfraIds = collectIssueContextInfraIds(baseNodes, index);
  const issueContextLessonIds = new Set(
    nodesConnectedToInfra(nodes, index, issueContextInfraIds).map((node) => node.data.id),
  );
  const keptNodeIds = new Set([
    ...visibleIssueIds,
    ...issueContextInfraIds,
    ...issueContextLessonIds,
  ]);
  const keptNodes = nodes.filter((node) => keptNodeIds.has(node.data.id));
  const keptEdges = edges.filter(
    (edge) =>
      keptNodeIds.has(edge.data.source) &&
      keptNodeIds.has(edge.data.target) &&
      (nodeHasType(edge.data.source, ISSUE_TYPE, keptNodes) ||
        nodeHasType(edge.data.target, ISSUE_TYPE, keptNodes) ||
        nodeHasType(edge.data.source, LESSON_TYPE, keptNodes) ||
        nodeHasType(edge.data.target, LESSON_TYPE, keptNodes)),
  );

  return {
    nodes: keptNodes,
    edges: dedupeEdges(keptEdges),
  };
}

export function buildEgoView(
  nodes: GraphNode[],
  edges: GraphEdge[],
  focusNodeId: string,
  maxNeighborsPerHub = 24,
): GraphSlice {
  const index = buildGraphIndex(nodes, edges);
  const nodeById = index.nodeById;
  const focusNode = nodeById.get(focusNodeId);

  if (!focusNode) {
    return buildSummaryView(nodes, edges);
  }

  const selectedNodeIds = new Set<string>([focusNodeId]);
  const firstHop = [...(index.adjacency.get(focusNodeId) ?? [])];

  firstHop.forEach((neighborId) => {
    selectedNodeIds.add(neighborId);
  });

  firstHop.forEach((neighborId) => {
    const neighborNode = nodeById.get(neighborId);
    if (!neighborNode) {
      return;
    }

    const neighborIsHub = isHubNode(neighborNode, index);
    if (neighborIsHub && focusNode.data.type !== ISSUE_TYPE) {
      return;
    }

    const secondHop = [...(index.adjacency.get(neighborId) ?? [])];
    const limitedSecondHop = secondHop
      .filter((candidateId) => candidateId !== focusNodeId)
      .filter((candidateId) => nodeById.get(candidateId)?.data.type !== LESSON_TYPE)
      .slice(0, neighborIsHub ? Math.min(6, maxNeighborsPerHub) : maxNeighborsPerHub);

    limitedSecondHop.forEach((candidateId) => {
      selectedNodeIds.add(candidateId);
    });
  });

  const keptNodes = nodes.filter((node) => selectedNodeIds.has(node.data.id));
  const keptEdges = edges.filter(
    (edge) => selectedNodeIds.has(edge.data.source) && selectedNodeIds.has(edge.data.target),
  );

  return {
    nodes: keptNodes,
    edges: dedupeEdges(keptEdges),
  };
}

export function buildSearchView(
  nodes: GraphNode[],
  edges: GraphEdge[],
  query: string,
  options: SearchViewOptions = {},
): GraphSlice {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) {
    return buildSummaryView(nodes, edges);
  }

  const index = buildGraphIndex(nodes, edges);
  const hubThreshold = options.hubThreshold ?? 200;
  const maxNeighborsPerHub = options.maxNeighborsPerHub ?? 18;
  const matchingIds = findSearchMatches(nodes, query, options.searchField ?? 'all', 24).map(
    (match) => match.node.data.id,
  );

  if (matchingIds.length === 0) {
    return { nodes: [], edges: [] };
  }

  const selectedNodeIds = new Set<string>(matchingIds);

  matchingIds.forEach((matchId) => {
    const matchingNode = index.nodeById.get(matchId);
    const neighbors = prioritizeCandidates([...(index.adjacency.get(matchId) ?? [])], index);
    const directNeighbors =
      matchingNode && isHubNode(matchingNode, index, hubThreshold)
        ? limitHubExpansion(neighbors, index, maxNeighborsPerHub)
        : neighbors;

    directNeighbors.forEach((neighborId) => {
      selectedNodeIds.add(neighborId);
    });

    directNeighbors.forEach((neighborId) => {
      const neighborNode = index.nodeById.get(neighborId);
      if (!neighborNode) {
        return;
      }

      const secondHop = prioritizeCandidates(
        [...(index.adjacency.get(neighborId) ?? [])].filter((candidateId) => candidateId !== matchId),
        index,
      ).slice(0, isHubNode(neighborNode, index, hubThreshold) ? maxNeighborsPerHub : 8);

      secondHop.forEach((candidateId) => {
        selectedNodeIds.add(candidateId);
      });
    });
  });

  const keptNodes = nodes.filter((node) => selectedNodeIds.has(node.data.id));
  const keptEdges = edges.filter(
    (edge) => selectedNodeIds.has(edge.data.source) && selectedNodeIds.has(edge.data.target),
  );

  return {
    nodes: keptNodes,
    edges: dedupeEdges(keptEdges),
  };
}

export function deriveMetrics(
  allNodes: GraphNode[],
  allEdges: GraphEdge[],
  visibleNodes: GraphNode[],
  visibleEdges: GraphEdge[],
): GraphMetrics {
  const issueCount = allNodes.filter((node) => node.data.type === ISSUE_TYPE).length;
  const hubCount = allNodes.filter((node) => node.data.type === 'Hub').length;

  return {
    totalNodes: allNodes.length,
    totalEdges: allEdges.length,
    visibleNodes: visibleNodes.length,
    visibleEdges: visibleEdges.length,
    hiddenNodes: allNodes.length - visibleNodes.length,
    hiddenEdges: allEdges.length - visibleEdges.length,
    issueCount,
    hubCount,
  };
}

export function getIssueSlug(nodeId: string): string | null {
  const marker = '/issue/';
  const markerIndex = nodeId.indexOf(marker);
  if (markerIndex === -1) {
    return null;
  }

  return nodeId.slice(markerIndex + marker.length) || null;
}

export function getCollapsedCountSummary(node: GraphNode): {
  shipment: number;
  vessel: number;
  vendor: number;
} | null {
  if (!INFRA_TYPES.has(node.data.type)) {
    return null;
  }

  return {
    shipment: getNumericField(node, 'collapsedShipmentCount'),
    vessel: getNumericField(node, 'collapsedVesselCount'),
    vendor: getNumericField(node, 'collapsedVendorCount'),
  };
}

export function getCollapsedCountLabel(node: GraphNode): string | null {
  const counts = getCollapsedCountSummary(node);
  if (!counts) {
    return null;
  }

  return `ship ${counts.shipment} · ves ${counts.vessel} · ven ${counts.vendor}`;
}

function nodeHasType(nodeId: string, type: GraphNodeType, nodes: GraphNode[]): boolean {
  return nodes.some((node) => node.data.id === nodeId && node.data.type === type);
}

function collectVisibleIssueIds(baseNodes: GraphNode[]): Set<string> {
  return new Set(
    baseNodes.filter((node) => node.data.type === ISSUE_TYPE).map((node) => node.data.id),
  );
}

function collectIssueContextInfraIds(baseNodes: GraphNode[], index: GraphIndex): Set<string> {
  const visibleIssueIds = collectVisibleIssueIds(baseNodes);
  const issueConnectedInfraIds = new Set<string>();

  if (visibleIssueIds.size === 0) {
    return issueConnectedInfraIds;
  }

  baseNodes.forEach((node) => {
    if (!INFRA_TYPES.has(node.data.type)) {
      return;
    }

    for (const neighborId of index.adjacency.get(node.data.id) ?? []) {
      if (visibleIssueIds.has(neighborId)) {
        issueConnectedInfraIds.add(node.data.id);
        break;
      }
    }
  });

  return issueConnectedInfraIds;
}

function addIssueContextLessons(
  allNodes: GraphNode[],
  baseNodes: GraphNode[],
  index: GraphIndex,
): GraphNode[] {
  const visibleIssueIds = collectVisibleIssueIds(baseNodes);

  if (visibleIssueIds.size === 0) {
    return baseNodes;
  }

  const issueConnectedInfraIds = collectIssueContextInfraIds(baseNodes, index);

  if (issueConnectedInfraIds.size === 0) {
    return baseNodes;
  }

  const lessonNodes = nodesConnectedToInfra(allNodes, index, issueConnectedInfraIds);
  if (lessonNodes.length === 0) {
    return baseNodes;
  }

  const seen = new Set(baseNodes.map((node) => node.data.id));
  return [...baseNodes, ...lessonNodes.filter((node) => !seen.has(node.data.id))];
}

function nodesConnectedToInfra(
  nodes: GraphNode[],
  index: GraphIndex,
  infraIds: Set<string>,
): GraphNode[] {
  return nodes.filter((node) => {
    if (node.data.type !== LESSON_TYPE) {
      return false;
    }

    for (const neighborId of index.adjacency.get(node.data.id) ?? []) {
      if (infraIds.has(neighborId)) {
        return true;
      }
    }

    return false;
  });
}

function computeCollapsedCounts(
  nodeId: string,
  keptIds: Set<string>,
  index: GraphIndex,
): Record<CollapsedNeighborType, number> {
  const counts = {
    Shipment: 0,
    Vessel: 0,
    Vendor: 0,
  };

  for (const neighborId of index.adjacency.get(nodeId) ?? []) {
    if (keptIds.has(neighborId)) {
      continue;
    }

    const neighborType = index.nodeById.get(neighborId)?.data.type as CollapsedNeighborType | undefined;
    if (!neighborType || !COLLAPSED_TYPES.includes(neighborType)) {
      continue;
    }

    counts[neighborType] += 1;
  }

  return counts;
}

export function findMatchingNodes(
  nodes: GraphNode[],
  query: string,
  limit = 8,
): GraphNode[] {
  return findSearchMatches(nodes, query, 'all', limit).map((match) => match.node);
}

export function findSearchMatches(
  nodes: GraphNode[],
  query: string,
  searchField: GraphSearchField = 'all',
  limit = 8,
): SearchMatch[] {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) {
    return [];
  }

  return nodes
    .map((node) => getBestSearchMatch(node, normalizedQuery, searchField))
    .filter((match): match is SearchMatch & { score: number } => Boolean(match))
    .sort((leftMatch, rightMatch) => {
      const scoreDelta = rightMatch.score - leftMatch.score;
      if (scoreDelta !== 0) {
        return scoreDelta;
      }

      return getNodeLabel(leftMatch.node).localeCompare(getNodeLabel(rightMatch.node));
    })
    .slice(0, limit);
}

export function getEdgeId(edge: GraphEdge): string {
  return edge.data.id ?? `${edge.data.source}|${edge.data.target}|${edge.data.label ?? ''}`;
}

export function deriveProvenanceChain(
  node: GraphNode | null,
  edge: GraphEdge | null,
  index: GraphIndex,
): ProvenanceChain {
  const issueOrLesson =
    node?.data.type === ISSUE_TYPE || node?.data.type === LESSON_TYPE ? node : null;
  const edgeSourceNode = edge ? (index.nodeById.get(edge.data.source) ?? null) : null;
  const edgeTargetNode = edge ? (index.nodeById.get(edge.data.target) ?? null) : null;
  const claim =
    issueOrLesson ??
    edgeTargetNode ??
    edgeSourceNode ??
    node ??
    null;

  const source =
    edgeSourceNode ??
    (claim
      ? [...(index.adjacency.get(claim.data.id) ?? [])]
          .map((neighborId) => index.nodeById.get(neighborId) ?? null)
          .find((neighbor) => Boolean(neighbor && neighbor.data.type !== ISSUE_TYPE && neighbor.data.type !== LESSON_TYPE)) ??
        null
      : null);

  return {
    source,
    claim,
    issueOrLesson,
  };
}

function limitHubExpansion(
  candidateIds: string[],
  index: GraphIndex,
  maxNeighborsPerHub: number,
): string[] {
  const keepAlways: string[] = [];
  const overflow: string[] = [];

  candidateIds.forEach((candidateId) => {
    const candidate = index.nodeById.get(candidateId);
    if (!candidate) {
      return;
    }

    if (candidate.data.type === ISSUE_TYPE || INFRA_TYPES.has(candidate.data.type)) {
      keepAlways.push(candidateId);
      return;
    }

    overflow.push(candidateId);
  });

  return [...keepAlways, ...overflow.slice(0, maxNeighborsPerHub)];
}

function prioritizeCandidates(candidateIds: string[], index: GraphIndex): string[] {
  return [...candidateIds].sort((leftId, rightId) => {
    const leftNode = index.nodeById.get(leftId);
    const rightNode = index.nodeById.get(rightId);
    const priorityDelta = getPriority(leftNode) - getPriority(rightNode);
    if (priorityDelta !== 0) {
      return priorityDelta;
    }

    return (index.degreeById.get(rightId) ?? 0) - (index.degreeById.get(leftId) ?? 0);
  });
}

function getPriority(node: GraphNode | undefined): number {
  if (!node) {
    return 99;
  }

  if (node.data.type === ISSUE_TYPE) {
    return 0;
  }

  if (INFRA_TYPES.has(node.data.type)) {
    return 1;
  }

  if (node.data.type === 'Vessel') {
    return 2;
  }

  if (node.data.type === 'Vendor') {
    return 3;
  }

  if (node.data.type === 'Shipment') {
    return 4;
  }

  return 5;
}

function getBestSearchMatch(
  node: GraphNode,
  normalizedQuery: string,
  searchField: GraphSearchField,
): (SearchMatch & { score: number }) | null {
  const candidateFields = SEARCH_FIELD_MAP[searchField];
  let bestMatch: (SearchMatch & { score: number }) | null = null;

  candidateFields.forEach((field) => {
    const value = node.data[field];
    if (typeof value !== 'string' || !value.trim()) {
      return;
    }

    const normalizedValue = value.toLowerCase();
    if (!normalizedValue.includes(normalizedQuery)) {
      return;
    }

    const exactBonus = normalizedValue === normalizedQuery ? 10_000 : normalizedValue.startsWith(normalizedQuery) ? 5_000 : 1_000;
    const nextMatch: SearchMatch & { score: number } = {
      node,
      matchedField: field,
      reasonLabel: SEARCH_REASON_LABELS[field] ?? `Matched in ${field}`,
      score: exactBonus - getPriority(node),
    };

    if (!bestMatch || nextMatch.score > bestMatch.score) {
      bestMatch = nextMatch;
    }
  });

  if (bestMatch) {
    return bestMatch;
  }

  if (searchField === 'all') {
    for (const [field, aliases] of SEARCHABLE_METADATA_ALIASES) {
      const value = node.data[field];
      if (typeof value !== 'string' || !value.trim()) {
        continue;
      }

      if (aliases.some((alias) => alias.includes(normalizedQuery))) {
        return {
          node,
          matchedField: field,
          reasonLabel: SEARCH_REASON_LABELS[field] ?? `Matched in ${field}`,
          score: 2_000 - getPriority(node),
        };
      }
    }
  }

  if (searchField !== 'all') {
    const aliasHit = getAliasReason(node, normalizedQuery, searchField);
    if (aliasHit) {
      return aliasHit;
    }
  }

  return null;
}

function getAliasReason(
  node: GraphNode,
  normalizedQuery: string,
  searchField: GraphSearchField,
): (SearchMatch & { score: number }) | null {
  const aliasSource = SEARCHABLE_METADATA_ALIASES.find(([field]) => {
    if (searchField === 'coe') return field === 'countryOfExport';
    if (searchField === 'pol') return field === 'portOfLoading';
    if (searchField === 'pod') return field === 'portOfDischarge';
    if (searchField === 'shipMode') return field === 'shipMode';
    if (searchField === 'atd') return field === 'actualDeparture';
    if (searchField === 'ata') return field === 'actualArrival';
    return false;
  });

  if (!aliasSource) {
    return null;
  }

  const [field, aliases] = aliasSource;
  const value = node.data[field];
  if (typeof value !== 'string' || !value.trim()) {
    return null;
  }

  if (!aliases.some((alias) => alias.includes(normalizedQuery))) {
    return null;
  }

  return {
    node,
    matchedField: field,
    reasonLabel: SEARCH_REASON_LABELS[field] ?? `Matched in ${field}`,
    score: 2_000 - getPriority(node),
  };
}

function getNumericField(node: GraphNode, field: string): number {
  const value = node.data[field];
  return typeof value === 'number' ? value : 0;
}
