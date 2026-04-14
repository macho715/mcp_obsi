import type { GraphEdge, GraphNode, GraphSlice } from '../types/graph';
import { buildGraphIndex, getEdgeId } from './graph-model';

export interface ManualGraphState {
  pinnedNodeIds: Set<string>;
  hiddenNodeIds: Set<string>;
  expandedNodeIds: Set<string>;
}

function dedupeEdges(edges: GraphEdge[]): GraphEdge[] {
  const seen = new Set<string>();

  return edges.filter((edge) => {
    const edgeId = getEdgeId(edge);
    if (seen.has(edgeId)) {
      return false;
    }
    seen.add(edgeId);
    return true;
  });
}

export function applyManualGraphState(
  allNodes: GraphNode[],
  allEdges: GraphEdge[],
  baseSlice: GraphSlice,
  state: ManualGraphState,
): GraphSlice {
  const index = buildGraphIndex(allNodes, allEdges);
  const visibleNodeIds = new Set(baseSlice.nodes.map((node) => node.data.id));

  state.pinnedNodeIds.forEach((nodeId) => {
    visibleNodeIds.add(nodeId);
  });

  state.expandedNodeIds.forEach((nodeId) => {
    visibleNodeIds.add(nodeId);
    for (const neighborId of index.adjacency.get(nodeId) ?? []) {
      visibleNodeIds.add(neighborId);
    }
  });

  state.hiddenNodeIds.forEach((nodeId) => {
    visibleNodeIds.delete(nodeId);
  });

  const nodes = allNodes.filter((node) => visibleNodeIds.has(node.data.id));
  const edges = dedupeEdges(
    allEdges.filter(
      (edge) => visibleNodeIds.has(edge.data.source) && visibleNodeIds.has(edge.data.target),
    ),
  );

  return { nodes, edges };
}
