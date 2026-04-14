import { readFileSync } from 'node:fs';

import { describe, expect, it } from 'vitest';

describe('kg-dashboard bundle splitting', () => {
  it('lazy-loads GraphView from App.tsx', () => {
    const source = readFileSync(new URL('../App.tsx', import.meta.url), 'utf-8');

    expect(source).toContain('lazy(() => import(\'./components/GraphView\'))');
    expect(source).toContain('<Suspense');
  });

  it('defines a dedicated chunk split for cytoscape in vite.config.ts', () => {
    const source = readFileSync(new URL('../../vite.config.ts', import.meta.url), 'utf-8');

    expect(source).toContain('manualChunks');
    expect(source).toContain('cytoscape');
    expect(source).toContain('graph-vendor');
  });
});
