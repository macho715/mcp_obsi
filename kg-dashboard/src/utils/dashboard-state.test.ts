import { describe, expect, it } from 'vitest';

import {
  DEFAULT_DASHBOARD_URL_STATE,
  buildDashboardUrlSearch,
  parseDashboardUrlState,
} from './dashboard-state';

describe('dashboard-state', () => {
  it('restores search, selection, manual controls, and companion view from query string', () => {
    const restored = parseDashboardUrlState(
      '?q=POL&field=pol&view=search&panel=timeline&node=shipment%2F1&edge=shipment%2F1%7Chub%2F1%7CloadedAt&pin=hub%2F1%2Cshipment%2F1&hide=shipment%2F9&expand=hub%2F1&compareLeft=alpha&compareRight=beta',
    );

    expect(restored).toEqual({
      query: 'POL',
      searchField: 'pol',
      viewMode: 'search',
      companionView: 'timeline',
      selectedNodeId: 'shipment/1',
      selectedEdgeId: 'shipment/1|hub/1|loadedAt',
      pinnedNodeIds: ['hub/1', 'shipment/1'],
      hiddenNodeIds: ['shipment/9'],
      expandedNodeIds: ['hub/1'],
      compareLeftId: 'alpha',
      compareRightId: 'beta',
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
      pinnedNodeIds: ['hub/1', 'shipment/2'],
      hiddenNodeIds: ['shipment/8'],
      expandedNodeIds: ['hub/1'],
      compareLeftId: 'view-1',
      compareRightId: 'view-2',
    });

    expect(serialized).toBe(
      '?q=Mina+Zayed&field=pod&view=search&panel=table&node=shipment%2F2&pin=hub%2F1%2Cshipment%2F2&hide=shipment%2F8&expand=hub%2F1&compareLeft=view-1&compareRight=view-2',
    );
  });
});
