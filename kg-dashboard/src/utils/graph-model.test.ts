import { describe, expect, it } from 'vitest';

import {
  buildEgoView,
  buildIssueView,
  buildSearchView,
  buildSummaryView,
  computeDegrees,
  findMatchingNodes,
  getCollapsedCountSummary,
} from './graph-model';
import type { GraphEdge, GraphNode } from '../types/graph';

function node(
  id: string,
  label: string,
  type: GraphNode['data']['type'],
  extra: Record<string, string> = {},
): GraphNode {
  return {
    data: {
      id,
      label,
      type,
      ...extra,
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

function edgeKey(graphEdge: GraphEdge): string {
  return `${graphEdge.data.source}|${graphEdge.data.target}|${graphEdge.data.label ?? ''}`;
}

describe('graph-model helpers', () => {
  it('computes degrees and ignores edges with missing endpoints', () => {
    const nodes = [
      node('issue/a', 'Alpha request', 'LogisticsIssue'),
      node('hub/1', 'MOSB', 'Hub'),
      node('site/1', 'Abu Dhabi', 'Site'),
      node('warehouse/1', 'Main Warehouse', 'Warehouse'),
      node('shipment/1', 'Outbound shipment', 'Shipment'),
    ];
    const edges = [
      edge('issue/a', 'hub/1'),
      edge('hub/1', 'site/1'),
      edge('hub/1', 'site/1'),
      edge('hub/1', 'warehouse/1'),
      edge('issue/a', 'missing/1'),
    ];

    expect(computeDegrees(nodes, edges)).toEqual({
      'issue/a': 1,
      'hub/1': 4,
      'site/1': 2,
      'warehouse/1': 1,
      'shipment/1': 0,
    });
  });

  it('builds a summary view with infra nodes and deduped edges only', () => {
    const nodes = [
      node('issue/a', 'Alpha request', 'LogisticsIssue'),
      node('issue/b', 'Beta request', 'LogisticsIssue'),
      node('hub/1', 'MOSB', 'Hub'),
      node('site/1', 'Abu Dhabi', 'Site'),
      node('warehouse/1', 'Main Warehouse', 'Warehouse'),
      node('shipment/1', 'Outbound shipment', 'Shipment'),
      node('vendor/1', 'Vendor', 'Vendor'),
    ];
    const edges = [
      edge('issue/a', 'hub/1', 'to hub'),
      edge('hub/1', 'site/1', 'to site'),
      edge('hub/1', 'site/1', 'to site'),
      edge('hub/1', 'warehouse/1', 'to warehouse'),
      edge('issue/a', 'site/1', 'to site'),
      edge('shipment/1', 'hub/1', 'ignored'),
      edge('vendor/1', 'issue/b', 'ignored'),
    ];

    const summary = buildSummaryView(nodes, edges);

    expect(summary.nodes.map((item) => item.data.id)).toEqual([
      'issue/a',
      'issue/b',
      'hub/1',
      'site/1',
      'warehouse/1',
    ]);
    expect(getCollapsedCountSummary(summary.nodes[2])).toEqual({
      shipment: 1,
      vessel: 0,
      vendor: 0,
    });
    expect(getCollapsedCountSummary(summary.nodes[3])).toEqual({
      shipment: 0,
      vessel: 0,
      vendor: 0,
    });
    expect(getCollapsedCountSummary(summary.nodes[4])).toEqual({
      shipment: 0,
      vessel: 0,
      vendor: 0,
    });
    expect(summary.edges.map(edgeKey).sort()).toEqual([
      'hub/1|site/1|to site',
      'hub/1|warehouse/1|to warehouse',
      'issue/a|hub/1|to hub',
      'issue/a|site/1|to site',
    ]);
  });

  it('summary keeps issue-context lesson and hides unrelated lesson', () => {
    const nodes = [
      node('issue/a', 'Alpha request', 'LogisticsIssue'),
      node('hub/1', 'MOSB', 'Hub'),
      node('hub/2', 'Unused hub', 'Hub'),
      node('lesson/1', 'Lesson for MOSB', 'IncidentLesson'),
      node('lesson/2', 'Unrelated lesson', 'IncidentLesson'),
    ];
    const edges = [
      edge('issue/a', 'hub/1', 'affects'),
      edge('hub/1', 'lesson/1', 'relatedToLesson'),
      edge('hub/2', 'lesson/2', 'relatedToLesson'),
    ];

    const summary = buildSummaryView(nodes, edges);

    expect(summary.nodes.map((item) => item.data.id).sort()).toEqual([
      'hub/1',
      'hub/2',
      'issue/a',
      'lesson/1',
    ]);
    expect(summary.nodes.map((item) => item.data.id)).not.toContain('lesson/2');
    expect(summary.edges.map(edgeKey).sort()).toEqual([
      'hub/1|lesson/1|relatedToLesson',
      'issue/a|hub/1|affects',
    ]);
  });

  it('attaches collapsed counts to site and warehouse infra nodes as well', () => {
    const nodes = [
      node('issue/a', 'Alpha request', 'LogisticsIssue'),
      node('site/1', 'DAS', 'Site'),
      node('warehouse/1', 'DSV Indoor', 'Warehouse'),
      node('shipment/1', 'Outbound shipment', 'Shipment'),
      node('vendor/1', 'Vendor', 'Vendor'),
      node('vessel/1', 'Bushra', 'Vessel'),
    ];
    const edges = [
      edge('issue/a', 'site/1', 'occursAt'),
      edge('shipment/1', 'site/1', 'deliveredTo'),
      edge('vendor/1', 'warehouse/1', 'suppliedBy'),
      edge('vessel/1', 'warehouse/1', 'transportedBy'),
    ];

    const summary = buildSummaryView(nodes, edges);
    const siteNode = summary.nodes.find((item) => item.data.id === 'site/1');
    const warehouseNode = summary.nodes.find((item) => item.data.id === 'warehouse/1');

    expect(siteNode && getCollapsedCountSummary(siteNode)).toEqual({
      shipment: 1,
      vessel: 0,
      vendor: 0,
    });
    expect(warehouseNode && getCollapsedCountSummary(warehouseNode)).toEqual({
      shipment: 0,
      vessel: 1,
      vendor: 1,
    });
  });

  it('issues keeps issue-context lesson and hides unrelated lesson', () => {
    const nodes = [
      node('issue/a', 'Alpha request', 'LogisticsIssue'),
      node('hub/1', 'MOSB', 'Hub'),
      node('hub/2', 'Unused hub', 'Hub'),
      node('lesson/1', 'Lesson for MOSB', 'IncidentLesson'),
      node('lesson/2', 'Unrelated lesson', 'IncidentLesson'),
    ];
    const edges = [
      edge('issue/a', 'hub/1', 'affects'),
      edge('hub/1', 'lesson/1', 'relatedToLesson'),
      edge('hub/2', 'lesson/2', 'relatedToLesson'),
    ];

    const issues = buildIssueView(nodes, edges);

    expect(issues.nodes.map((item) => item.data.id).sort()).toEqual(['hub/1', 'issue/a', 'lesson/1']);
    expect(issues.nodes.map((item) => item.data.id)).not.toContain('lesson/2');
    expect(issues.nodes.map((item) => item.data.id)).not.toContain('hub/2');
    expect(issues.edges.map(edgeKey).sort()).toEqual([
      'hub/1|lesson/1|relatedToLesson',
      'issue/a|hub/1|affects',
    ]);
  });

  it('builds a limited ego view around an issue-focused hub graph', () => {
    const nodes: GraphNode[] = [
      node('issue/a', 'Alpha request', 'LogisticsIssue'),
      node('hub/1', 'MOSB', 'Hub'),
      ...Array.from({ length: 205 }, (_, index) =>
        node(`leaf/${index + 1}`, `Leaf ${index + 1}`, 'Shipment'),
      ),
    ];
    const edges: GraphEdge[] = [
      edge('issue/a', 'hub/1', 'focus'),
      ...Array.from({ length: 205 }, (_, index) =>
        edge('hub/1', `leaf/${index + 1}`, `leaf-${index + 1}`),
      ),
    ];

    const ego = buildEgoView(nodes, edges, 'issue/a', 10);
    const egoNodeIds = ego.nodes.map((item) => item.data.id);

    expect(egoNodeIds).toEqual([
      'issue/a',
      'hub/1',
      'leaf/1',
      'leaf/2',
      'leaf/3',
      'leaf/4',
      'leaf/5',
      'leaf/6',
    ]);
    expect(ego.edges.map(edgeKey)).toEqual([
      'issue/a|hub/1|focus',
      'hub/1|leaf/1|leaf-1',
      'hub/1|leaf/2|leaf-2',
      'hub/1|leaf/3|leaf-3',
      'hub/1|leaf/4|leaf-4',
      'hub/1|leaf/5|leaf-5',
      'hub/1|leaf/6|leaf-6',
    ]);
  });

  it('ego keeps directly attached lesson for selected node and hides unrelated lesson', () => {
    const nodes = [
      node('issue/a', 'Alpha request', 'LogisticsIssue'),
      node('hub/1', 'MOSB', 'Hub'),
      node('hub/2', 'Unused hub', 'Hub'),
      node('lesson/1', 'Direct lesson', 'IncidentLesson'),
      node('lesson/2', 'Unrelated lesson', 'IncidentLesson'),
    ];
    const edges = [
      edge('issue/a', 'hub/1', 'focus'),
      edge('hub/1', 'lesson/1', 'relatedToLesson'),
      edge('hub/2', 'lesson/2', 'relatedToLesson'),
    ];

    const ego = buildEgoView(nodes, edges, 'hub/1', 10);

    expect(ego.nodes.map((item) => item.data.id).sort()).toEqual([
      'hub/1',
      'issue/a',
      'lesson/1',
    ]);
    expect(ego.nodes.map((item) => item.data.id)).not.toContain('lesson/2');
    expect(ego.edges.map(edgeKey).sort()).toEqual([
      'hub/1|lesson/1|relatedToLesson',
      'issue/a|hub/1|focus',
    ]);
  });

  it('builds a search view from MOSB and limits hub expansion', () => {
    const nodes: GraphNode[] = [
      node('issue/a', 'Alpha request', 'LogisticsIssue', {
        'rdf-schema#label': 'Canonical Alpha',
      }),
      node('hub/1', 'MOSB', 'Hub'),
      node('site/1', 'Abu Dhabi', 'Site'),
      node('leaf/1', 'Leaf 1', 'Shipment'),
      node('leaf/2', 'Leaf 2', 'Shipment'),
      node('leaf/3', 'Leaf 3', 'Shipment'),
      node('leaf/4', 'Leaf 4', 'Shipment'),
    ];
    const edges: GraphEdge[] = [
      edge('issue/a', 'hub/1', 'focus'),
      edge('issue/a', 'site/1', 'site'),
      edge('hub/1', 'leaf/1', 'leaf-1'),
      edge('hub/1', 'leaf/2', 'leaf-2'),
      edge('hub/1', 'leaf/3', 'leaf-3'),
      edge('hub/1', 'leaf/4', 'leaf-4'),
    ];

    const search = buildSearchView(nodes, edges, 'MOSB', {
      hubThreshold: 1,
      maxNeighborsPerHub: 2,
    });

    expect(search.nodes.map((item) => item.data.id)).toEqual([
      'issue/a',
      'hub/1',
      'site/1',
      'leaf/1',
      'leaf/2',
    ]);
    expect(search.nodes).toHaveLength(5);
    expect(search.nodes.map((item) => item.data.id)).not.toContain('leaf/3');
    expect(search.nodes.map((item) => item.data.id)).not.toContain('leaf/4');
    expect(search.edges.map(edgeKey).sort()).toEqual([
      'hub/1|leaf/1|leaf-1',
      'hub/1|leaf/2|leaf-2',
      'issue/a|hub/1|focus',
      'issue/a|site/1|site',
    ]);
  });

  it('returns ranked search matches with exact hits first', () => {
    const nodes: GraphNode[] = [
      node('hub/1', 'MOSB', 'Hub'),
      node('issue/1', 'MOSB crane delay', 'LogisticsIssue'),
      node('shipment/1', 'Shipment to MOSB', 'Shipment'),
    ];

    expect(findMatchingNodes(nodes, 'MOSB', 3).map((item) => item.data.id)).toEqual([
      'hub/1',
      'issue/1',
      'shipment/1',
    ]);
  });
});
