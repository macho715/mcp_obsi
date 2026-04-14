import { describe, expect, it } from 'vitest';

import type { GraphEdge, GraphNode, GraphSlice } from '../types/graph';
import { applyManualGraphState } from './graph-manual-controls';

function node(id: string, label: string, type: string): GraphNode {
  return {
    data: {
      id,
      label,
      type,
    },
  };
}

function edge(source: string, target: string, label?: string): GraphEdge {
  return {
    data: {
      source,
      target,
      ...(label ? { label } : {}),
    },
  };
}

describe('graph-manual-controls', () => {
  const allNodes: GraphNode[] = [
    node('hub/1', 'MOSB', 'Hub'),
    node('shipment/1', 'HVDC-001', 'Shipment'),
    node('shipment/2', 'HVDC-002', 'Shipment'),
    node('vessel/1', 'MSC Example', 'Vessel'),
  ];
  const allEdges: GraphEdge[] = [
    edge('hub/1', 'shipment/1', 'contains'),
    edge('shipment/1', 'shipment/2', 'related'),
    edge('shipment/1', 'vessel/1', 'transportedBy'),
  ];
  const baseSlice: GraphSlice = {
    nodes: [allNodes[0], allNodes[1]],
    edges: [allEdges[0]],
  };

  it('pins nodes outside the base slice', () => {
    const result = applyManualGraphState(allNodes, allEdges, baseSlice, {
      pinnedNodeIds: new Set(['shipment/2']),
      hiddenNodeIds: new Set<string>(),
      expandedNodeIds: new Set<string>(),
    });

    expect(result.nodes.map((item) => item.data.id).sort()).toEqual([
      'hub/1',
      'shipment/1',
      'shipment/2',
    ]);
    expect(result.edges.map((item) => item.data.label).sort()).toEqual(['contains', 'related']);
  });

  it('hides nodes even when they are in the base slice or pinned', () => {
    const result = applyManualGraphState(allNodes, allEdges, baseSlice, {
      pinnedNodeIds: new Set(['shipment/2']),
      hiddenNodeIds: new Set(['shipment/1']),
      expandedNodeIds: new Set<string>(),
    });

    expect(result.nodes.map((item) => item.data.id).sort()).toEqual(['hub/1', 'shipment/2']);
    expect(result.edges).toEqual([]);
  });

  it('expands one hop from a selected node', () => {
    const result = applyManualGraphState(allNodes, allEdges, baseSlice, {
      pinnedNodeIds: new Set<string>(),
      hiddenNodeIds: new Set<string>(),
      expandedNodeIds: new Set(['shipment/1']),
    });

    expect(result.nodes.map((item) => item.data.id).sort()).toEqual([
      'hub/1',
      'shipment/1',
      'shipment/2',
      'vessel/1',
    ]);
    expect(result.edges.map((item) => item.data.label).sort()).toEqual([
      'contains',
      'related',
      'transportedBy',
    ]);
  });
});
