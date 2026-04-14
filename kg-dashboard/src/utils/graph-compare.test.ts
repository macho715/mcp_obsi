import { describe, expect, it } from 'vitest';

import type { GraphEdge, GraphNode, GraphSlice } from '../types/graph';
import { buildCompareUnionSlice, buildGraphCompareDiff } from './graph-compare';

function node(id: string, type: string, label: string): GraphNode {
  return { data: { id, type, label } };
}

function edge(source: string, target: string, label: string): GraphEdge {
  return { data: { source, target, label } };
}

describe('graph-compare', () => {
  it('returns added, removed, and changed node/edge ids', () => {
    const left: GraphSlice = {
      nodes: [node('n-1', 'Hub', 'A'), node('n-2', 'Shipment', 'B')],
      edges: [edge('n-1', 'n-2', 'connected')],
    };
    const right: GraphSlice = {
      nodes: [node('n-1', 'Hub', 'A (updated)'), node('n-3', 'Shipment', 'C')],
      edges: [edge('n-1', 'n-2', 'connected-updated'), edge('n-1', 'n-3', 'new')],
    };

    const diff = buildGraphCompareDiff(left, right);

    expect(Array.from(diff.addedNodeIds)).toEqual(['n-3']);
    expect(Array.from(diff.removedNodeIds)).toEqual(['n-2']);
    expect(Array.from(diff.changedNodeIds)).toEqual(['n-1']);
    expect(Array.from(diff.addedEdgeIds)).toEqual(['n-1|n-3']);
    expect(Array.from(diff.removedEdgeIds)).toEqual([]);
    expect(Array.from(diff.changedEdgeIds)).toEqual(['n-1|n-2']);
  });

  it('builds union slice from both compare sides', () => {
    const left: GraphSlice = {
      nodes: [node('n-1', 'Hub', 'A')],
      edges: [],
    };
    const right: GraphSlice = {
      nodes: [node('n-2', 'Shipment', 'B')],
      edges: [edge('n-1', 'n-2', 'link')],
    };

    const union = buildCompareUnionSlice(left, right);

    expect(union.nodes.map((item) => item.data.id).sort()).toEqual(['n-1', 'n-2']);
    expect(union.edges.map((item) => item.data.label)).toEqual(['link']);
  });
});
