// @vitest-environment jsdom

import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import App, { deriveCompactPanelTab } from './App';
import type { GraphEdge, GraphNode } from './types/graph';

const TEST_NODES: GraphNode[] = [
  {
    data: {
      id: 'node-1',
      label: 'Node 1',
      type: 'Shipment',
      pol: 'JEA',
      pod: 'DXB',
      atd: '2026-04-01',
      ata: '2026-04-03',
    },
  },
  {
    data: {
      id: 'hub-1',
      label: 'Hub 1',
      type: 'Hub',
    },
  },
];

const TEST_EDGES: GraphEdge[] = [
  {
    data: {
      id: 'edge-1',
      source: 'hub-1',
      target: 'node-1',
      label: 'connectedTo',
    },
  },
];

function createJsonResponse<T>(body: T): Response {
  return {
    ok: true,
    json: async () => body,
  } as Response;
}

async function flushAppUpdates() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

function getCompactPanelValue(container: HTMLElement) {
  const shell = container.querySelector('.dashboard-shell');
  expect(shell).not.toBeNull();
  return shell?.getAttribute('data-compact-panel');
}

function getButton(container: HTMLElement, label: string): HTMLButtonElement {
  const button = Array.from(container.querySelectorAll('button')).find(
    (candidate) => candidate.textContent?.trim() === label,
  );
  expect(button).toBeInstanceOf(HTMLButtonElement);
  return button as HTMLButtonElement;
}

describe('App compact panel integration', () => {
  let container: HTMLDivElement | null = null;
  let root: Root | null = null;

  beforeEach(() => {
    (
      globalThis as typeof globalThis & {
        IS_REACT_ACT_ENVIRONMENT?: boolean;
      }
    ).IS_REACT_ACT_ENVIRONMENT = true;
    document.body.innerHTML = '';
    window.localStorage.clear();
    window.history.replaceState({}, '', '/?panel=table');

    vi.stubGlobal(
      'fetch',
      vi.fn((input: string | URL | Request) => {
        const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;

        if (url.includes('/data/nodes.json')) {
          return Promise.resolve(createJsonResponse(TEST_NODES));
        }

        if (url.includes('/data/edges.json')) {
          return Promise.resolve(createJsonResponse(TEST_EDGES));
        }

        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
  });

  afterEach(async () => {
    if (root) {
      await act(async () => {
        root?.unmount();
      });
    }

    container?.remove();
    container = null;
    root = null;
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  async function renderApp(search = '?panel=table') {
    window.history.replaceState({}, '', search);
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<App />);
    });

    await flushAppUpdates();

    return container;
  }

  it('renders controls compact panel by default when no selection is present', async () => {
    const mounted = await renderApp('?panel=table');

    expect(getCompactPanelValue(mounted)).toBe('controls');
  });

  it('renders inspector compact panel when URL state has selected node', async () => {
    const mounted = await renderApp('?panel=table&node=node-1');

    expect(getCompactPanelValue(mounted)).toBe('inspector');
  });

  it('allows manual compact panel switching via CompactPanelToggle', async () => {
    const mounted = await renderApp('?panel=table');

    await act(async () => {
      getButton(mounted, 'Inspector').click();
    });

    expect(getCompactPanelValue(mounted)).toBe('inspector');

    await act(async () => {
      getButton(mounted, 'Controls').click();
    });

    expect(getCompactPanelValue(mounted)).toBe('controls');
  });
});

describe('deriveCompactPanelTab', () => {
  it('returns controls when there is no selected node or edge', () => {
    expect(deriveCompactPanelTab(null, null)).toBe('controls');
  });

  it('returns inspector when a node is selected', () => {
    expect(deriveCompactPanelTab('node-1', null)).toBe('inspector');
  });

  it('returns inspector when an edge is selected', () => {
    expect(deriveCompactPanelTab(null, 'edge-1')).toBe('inspector');
  });

  it('returns inspector when both a node and edge are selected', () => {
    expect(deriveCompactPanelTab('node-1', 'edge-1')).toBe('inspector');
  });
});
