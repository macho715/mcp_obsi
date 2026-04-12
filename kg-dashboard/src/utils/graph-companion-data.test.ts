import { describe, expect, it } from 'vitest';

import { buildSchemaSummaryRows, buildTableRows, buildTimelineRows } from './graph-companion-data';
import type { GraphEdge, GraphNode } from '../types/graph';

const nodes: GraphNode[] = [
  {
    data: {
      id: 'shipment/1',
      label: 'HVDC-001',
      type: 'Shipment',
      portOfLoading: 'Le Havre',
      portOfDischarge: 'Mina Zayed',
      actualDeparture: '2023-11-12',
      actualArrival: '2023-12-01',
    },
  },
  {
    data: {
      id: 'issue/1',
      label: 'Crane delay',
      type: 'LogisticsIssue',
    },
  },
];

const edges: GraphEdge[] = [
  {
    data: {
      id: 'issue/1|shipment/1|affects',
      source: 'issue/1',
      target: 'shipment/1',
      label: 'affects',
    },
  },
];

describe('graph-companion-data', () => {
  it('builds sortable table rows from visible nodes', () => {
    const degreeById = new Map([
      ['shipment/1', 3],
      ['issue/1', 1],
    ]);

    expect(buildTableRows(nodes, degreeById)[0]).toMatchObject({
      id: 'shipment/1',
      label: 'HVDC-001',
      type: 'Shipment',
      pol: 'Le Havre',
      pod: 'Mina Zayed',
      atd: '2023-11-12',
      ata: '2023-12-01',
      degree: 3,
    });
  });

  it('builds timeline rows only for shipment-like timing records', () => {
    expect(buildTimelineRows(nodes)).toEqual([
      {
        id: 'shipment/1',
        label: 'HVDC-001',
        atd: '2023-11-12',
        ata: '2023-12-01',
        status: 'arrived',
      },
    ]);
  });

  it('builds schema summary counts for node and edge types', () => {
    expect(buildSchemaSummaryRows(nodes, edges)).toEqual({
      nodeTypes: [
        { type: 'LogisticsIssue', count: 1 },
        { type: 'Shipment', count: 1 },
      ],
      edgeTypes: [{ type: 'affects', count: 1 }],
    });
  });
});
