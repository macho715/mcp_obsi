import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { NodeInspector } from './NodeInspector';
import type { GraphNode } from '../types/graph';

function renderInspector(node: GraphNode | null): string {
  return renderToStaticMarkup(<NodeInspector node={node} degree={3} onClose={() => {}} />);
}

describe('NodeInspector', () => {
  it('opens an exported issue note using the provided external vault and an encoded path', () => {
    const markup = renderInspector({
      data: {
        id: 'issue/exported-123',
        label: 'Exported issue',
        type: 'LogisticsIssue',
        analysisVault: 'ops vault',
        analysisPath: 'analysis/issues/exported issue #123.md',
      },
    });

    expect(markup).toContain(
      'href="obsidian://open?vault=ops%20vault&amp;file=analysis%2Fissues%2Fexported%20issue%20%23123.md"',
    );
  });

  it('opens an exported lesson note using the provided external vault and an encoded path', () => {
    const markup = renderInspector({
      data: {
        id: 'lesson/exported-456',
        label: 'Exported lesson',
        type: 'IncidentLesson',
        analysisVault: 'ops vault',
        analysisPath: 'analysis/lessons/exported lesson #456.md',
      },
    });

    expect(markup).toContain(
      'href="obsidian://open?vault=ops%20vault&amp;file=analysis%2Flessons%2Fexported%20lesson%20%23456.md"',
    );
  });

  it('keeps the inspector metadata-only when no export path exists', () => {
    const markup = renderInspector({
      data: {
        id: 'issue/no-link',
        label: 'No link issue',
        type: 'LogisticsIssue',
      },
    });

    expect(markup).not.toContain('obsidian://open?');
    expect(markup).toContain('This node has no extra metadata beyond the standard graph fields.');
  });
});
