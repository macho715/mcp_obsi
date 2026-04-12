import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { NodeInspector } from './NodeInspector';
import type { GraphEdge, GraphNode, VisibilityReason } from '../types/graph';

function renderInspector(
  node: GraphNode | null,
  edge: GraphEdge | null,
  visibilityReasons: VisibilityReason[] = [],
): string {
  return renderToStaticMarkup(
    <NodeInspector
      node={node}
      edge={edge}
      degree={3}
      visibilityReasons={visibilityReasons}
      onClose={() => {}}
    />,
  );
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

  it('hides vessel and flight raw metadata fields from node details', () => {
    const markup = renderInspector(
      {
        data: {
          id: 'shipment/with-hidden-fields',
          label: 'Shipment with hidden fields',
          type: 'Shipment',
          'VESSEL NAME/ FLIGHT No.': 'MSC_SAMPLE',
          vesselName: 'MSC_SAMPLE',
          flightNo: 'EY123',
          portOfLoading: 'Le Havre',
        },
      },
      null,
    );

    expect(markup).not.toContain('VESSEL NAME/ FLIGHT No.');
    expect(markup).not.toContain('vesselName');
    expect(markup).not.toContain('flightNo');
    expect(markup).toContain('portOfLoading');
  });

  it('renders provenance chain links for evidence drill-down', () => {
    const markup = renderToStaticMarkup(
      <NodeInspector
        node={{
          data: {
            id: 'issue/1',
            label: 'Issue 1',
            type: 'LogisticsIssue',
            analysisVault: 'ops vault',
            analysisPath: 'wiki/analyses/issue-1.md',
          },
        }}
        edge={null}
        degree={2}
        provenance={{
          source: {
            data: {
              id: 'shipment/1',
              label: 'Shipment 1',
              type: 'Shipment',
              analysisVault: 'ops vault',
              analysisPath: 'wiki/analyses/shipment-1.md',
            },
          },
          claim: {
            data: {
              id: 'claim/1',
              label: 'Claim 1',
              type: 'Unknown',
              analysisVault: 'ops vault',
              analysisPath: 'wiki/analyses/claim-1.md',
            },
          },
          issueOrLesson: {
            data: {
              id: 'issue/1',
              label: 'Issue 1',
              type: 'LogisticsIssue',
              analysisVault: 'ops vault',
              analysisPath: 'wiki/analyses/issue-1.md',
            },
          },
        }}
        onClose={() => {}}
      />,
    );

    expect(markup).toContain('Source');
    expect(markup).toContain('Claim');
    expect(markup).toContain('Issue / Lesson');
    expect(markup).toContain('obsidian://open?vault=ops%20vault');
  });
});
