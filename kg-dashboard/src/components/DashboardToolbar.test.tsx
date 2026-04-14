import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { CollapsibleSection } from './CollapsibleSection';
import { CompactPanelToggle } from './CompactPanelToggle';
import { DashboardToolbar } from './DashboardToolbar';
import type { GraphMetrics } from '../types/graph';

const metrics: GraphMetrics = {
  totalNodes: 100,
  totalEdges: 200,
  visibleNodes: 20,
  visibleEdges: 30,
  hiddenNodes: 80,
  hiddenEdges: 170,
  issueCount: 5,
  hubCount: 2,
};

describe('DashboardToolbar', () => {
  it('renders compact title, current view, and stat summary without hero copy', () => {
    const markup = renderToStaticMarkup(
      <DashboardToolbar
        title="kg-dashboard"
        viewLabel="요약 뷰"
        metrics={metrics}
      />,
    );

    expect(markup).toContain('kg-dashboard');
    expect(markup).toContain('요약 뷰');
    expect(markup).toContain('Visible');
    expect(markup).toContain('Hidden');
    expect(markup).toContain('Hotspots');
    expect(markup).not.toContain('Knowledge graph tool');
  });

  it('renders compare label and the metric values when compare mode is enabled', () => {
    const markup = renderToStaticMarkup(
      <DashboardToolbar
        title="kg-dashboard"
        viewLabel="요약 뷰"
        compareLabel="Compare mode"
        metrics={metrics}
      />,
    );

    expect(markup).toContain('Compare mode');
    expect(markup).toContain('20 / 30');
    expect(markup).toContain('80 / 170');
    expect(markup).toContain('5 / 2');
  });

  it('renders the compact panel toggle with the active button state', () => {
    const markup = renderToStaticMarkup(
      <CompactPanelToggle activeTab="controls" onChange={() => {}} />,
    );

    expect(markup).toContain('Controls');
    expect(markup).toContain('Inspector');
    expect(markup).toContain('is-active');
  });

  it('renders a collapsed section shell with open state when requested', () => {
    const markup = renderToStaticMarkup(
      <CollapsibleSection
        sectionId="ontology-query"
        title="Ontology query"
        summary="Filters"
        defaultOpen={true}
      >
        <span>Body content</span>
      </CollapsibleSection>,
    );

    expect(markup).toContain('data-section-id="ontology-query"');
    expect(markup).toContain('Ontology query');
    expect(markup).toContain('Filters');
    expect(markup).toContain('<details');
    expect(markup).toContain('open');
  });
});