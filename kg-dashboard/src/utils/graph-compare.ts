import type { GraphEdge, GraphNode, GraphSlice } from '../types/graph';

function getEdgeCompareKey(edge: GraphEdge): string {
  return `${edge.data.source}|${edge.data.target}`;
}

export interface GraphCompareDiff {
  addedNodeIds: Set<string>;
  removedNodeIds: Set<string>;
  changedNodeIds: Set<string>;
  addedEdgeIds: Set<string>;
  removedEdgeIds: Set<string>;
  changedEdgeIds: Set<string>;
}

export function buildCompareUnionSlice(left: GraphSlice, right: GraphSlice): GraphSlice {
  const nodeById = new Map<string, GraphNode>();
  [...left.nodes, ...right.nodes].forEach((node) => {
    nodeById.set(node.data.id, node);
  });

  const edgeById = new Map<string, GraphEdge>();
  [...left.edges, ...right.edges].forEach((edge) => {
    edgeById.set(getEdgeCompareKey(edge), edge);
  });

  return {
    nodes: Array.from(nodeById.values()),
    edges: Array.from(edgeById.values()),
  };
}

export function buildGraphCompareDiff(left: GraphSlice, right: GraphSlice): GraphCompareDiff {
  const leftNodesById = new Map(left.nodes.map((node) => [node.data.id, node]));
  const rightNodesById = new Map(right.nodes.map((node) => [node.data.id, node]));

  const leftEdgesById = new Map(left.edges.map((edge) => [getEdgeCompareKey(edge), edge]));
  const rightEdgesById = new Map(right.edges.map((edge) => [getEdgeCompareKey(edge), edge]));

  const addedNodeIds = new Set<string>();
  const removedNodeIds = new Set<string>();
  const changedNodeIds = new Set<string>();

  Array.from(rightNodesById.keys()).forEach((nodeId) => {
    if (!leftNodesById.has(nodeId)) {
      addedNodeIds.add(nodeId);
      return;
    }

    const leftSerialized = JSON.stringify(leftNodesById.get(nodeId)?.data ?? {});
    const rightSerialized = JSON.stringify(rightNodesById.get(nodeId)?.data ?? {});
    if (leftSerialized !== rightSerialized) {
      changedNodeIds.add(nodeId);
    }
  });

  Array.from(leftNodesById.keys()).forEach((nodeId) => {
    if (!rightNodesById.has(nodeId)) {
      removedNodeIds.add(nodeId);
    }
  });

  const addedEdgeIds = new Set<string>();
  const removedEdgeIds = new Set<string>();
  const changedEdgeIds = new Set<string>();

  Array.from(rightEdgesById.keys()).forEach((edgeId) => {
    if (!leftEdgesById.has(edgeId)) {
      addedEdgeIds.add(edgeId);
      return;
    }

    const leftSerialized = JSON.stringify(leftEdgesById.get(edgeId)?.data ?? {});
    const rightSerialized = JSON.stringify(rightEdgesById.get(edgeId)?.data ?? {});
    if (leftSerialized !== rightSerialized) {
      changedEdgeIds.add(edgeId);
    }
  });

  Array.from(leftEdgesById.keys()).forEach((edgeId) => {
    if (!rightEdgesById.has(edgeId)) {
      removedEdgeIds.add(edgeId);
    }
  });

  return {
    addedNodeIds,
    removedNodeIds,
    changedNodeIds,
    addedEdgeIds,
    removedEdgeIds,
    changedEdgeIds,
  };
}
