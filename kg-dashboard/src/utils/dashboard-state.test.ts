import { describe, expect, it } from 'vitest';

import {
  DEFAULT_DASHBOARD_URL_STATE,
  buildDashboardUrlSearch,
  parseDashboardUrlState,
} from './dashboard-state';

describe('dashboard-state', () => {
  it('restores search, selection, and companion view from query string', () => {
    const restored = parseDashboardUrlState(
      '?q=POL&field=pol&view=search&panel=timeline&node=shipment%2F1&edge=shipment%2F1%7Chub%2F1%7CloadedAt',
    );

    expect(restored).toEqual({
      query: 'POL',
      searchField: 'pol',
      viewMode: 'search',
      companionView: 'timeline',
      selectedNodeId: 'shipment/1',
      selectedEdgeId: 'shipment/1|hub/1|loadedAt',
    });
  });

  it('drops invalid values and falls back to defaults', () => {
    const restored = parseDashboardUrlState('?field=unknown&view=broken&panel=nope');

    expect(restored).toEqual(DEFAULT_DASHBOARD_URL_STATE);
  });

  it('serializes only active values into a stable query string', () => {
    const serialized = buildDashboardUrlSearch({
      query: 'Mina Zayed',
      searchField: 'pod',
      viewMode: 'search',
      companionView: 'table',
      selectedNodeId: 'shipment/2',
      selectedEdgeId: null,
    });

    expect(serialized).toBe('?q=Mina+Zayed&field=pod&view=search&panel=table&node=shipment%2F2');
  });
});
