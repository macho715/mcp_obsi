import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { GraphCompanionTabs } from './GraphCompanionTabs';
import { GraphDataTable } from './GraphDataTable';
import { GraphTimeline } from './GraphTimeline';
import { GraphSchemaSummary } from './GraphSchemaSummary';

describe('Graph companion views', () => {
  it('renders all companion tabs', () => {
    const markup = renderToStaticMarkup(
      <GraphCompanionTabs activeView="table" onChange={() => {}} />,
    );

    expect(markup).toContain('Graph');
    expect(markup).toContain('Table');
    expect(markup).toContain('Timeline');
    expect(markup).toContain('Schema');
  });

  it('renders table, timeline, and schema rows without card nesting', () => {
    const tableMarkup = renderToStaticMarkup(
      <GraphDataTable
        rows={[
          {
            id: 'shipment/1',
            label: 'HVDC-001',
            type: 'Shipment',
            pol: 'Le Havre',
            pod: 'Mina Zayed',
            atd: '2023-11-12',
            ata: '2023-12-01',
            degree: 3,
          },
        ]}
        selectedNodeId={null}
        onSelectNode={() => {}}
      />,
    );

    const timelineMarkup = renderToStaticMarkup(
      <GraphTimeline
        rows={[
          {
            id: 'shipment/1',
            label: 'HVDC-001',
            atd: '2023-11-12',
            ata: '2023-12-01',
            status: 'arrived',
          },
        ]}
        selectedNodeId={null}
        onSelectNode={() => {}}
      />,
    );

    const schemaMarkup = renderToStaticMarkup(
      <GraphSchemaSummary
        nodeTypes={[{ type: 'Shipment', count: 1 }]}
        edgeTypes={[{ type: 'affects', count: 1 }]}
      />,
    );

    expect(tableMarkup).toContain('Le Havre');
    expect(timelineMarkup).toContain('arrived');
    expect(schemaMarkup).toContain('Shipment');
    expect(tableMarkup).not.toContain('card card');
  });
});
