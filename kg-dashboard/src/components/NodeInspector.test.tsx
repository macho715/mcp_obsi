import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { NodeInspector } from './NodeInspector';
import type { GraphEdge, GraphNode } from '../types/graph';

function renderInspector(node: GraphNode | null, edge: GraphEdge | null): string {
  return renderToStaticMarkup(<NodeInspector node={node} edge={edge} degree={3} onClose={() => {}} />);
}

describe('NodeInspector', () => {
  it('renders node, edge, evidence, and related tabs', () => {
    const markup = renderInspector(
      {
        data: {
          id: 'shipment/1',
          label: 'HVDC-001',
          type: 'Shipment',
          analysisVault: 'ops vault',
          analysisPath: 'wiki/analyses/shipment-1.md',
          portOfLoading: 'Le Havre',
        },
      },
      null,
    );

    expect(markup).toContain('Node');
    expect(markup).toContain('Edge');
    expect(markup).toContain('Evidence');
    expect(markup).toContain('Related');
  });

  it('renders edge details when an edge is selected', () => {
    const markup = renderInspector(null, {
      data: {
        id: 'shipment/1|hub/1|loadedAt',
        source: 'shipment/1',
        target: 'hub/1',
        label: 'loadedAt',
        evidencePath: 'wiki/analyses/edge-loaded-at.md',
      },
    });

    expect(markup).toContain('loadedAt');
    expect(markup).toContain('shipment/1');
    expect(markup).toContain('hub/1');
    expect(markup).toContain('wiki/analyses/edge-loaded-at.md');
  });

  it('shows an explicit no-evidence message when no evidence metadata exists', () => {
    const markup = renderInspector(
      {
        data: {
          id: 'issue/no-link',
          label: 'No link issue',
          type: 'LogisticsIssue',
        },
      },
      null,
    );

    expect(markup).toContain('No linked evidence is available for this selection.');
  });

  it('opens an exported lesson note using the provided external vault and an encoded path', () => {
    const markup = renderInspector(
      {
        data: {
          id: 'lesson/exported-456',
          label: 'Exported lesson',
          type: 'IncidentLesson',
          analysisVault: 'ops vault',
          analysisPath: 'analysis/lessons/exported lesson #456.md',
        },
      },
      null,
    );

    expect(markup).toContain(
      'href="obsidian://open?vault=ops%20vault&amp;file=analysis%2Flessons%2Fexported%20lesson%20%23456.md"',
    );
  });
});
