/**
 * Unit Tests for InventoryManager
 * @jest-environment jsdom
 */

// Mock WebSocket before anything imports it
function createMockWebSocket() {
  return {
    send: jest.fn(),
    close: jest.fn(),
    readyState: 0, // CONNECTING
    onopen: null,
    onmessage: null,
    onerror: null,
    onclose: null,
    CONNECTING: 0,
    OPEN: 1,
    CLOSING: 2,
    CLOSED: 3,
  };
}

// Replace the global WebSocket with our mock factory
const MockWebSocketClass = jest.fn().mockImplementation(() => createMockWebSocket());
// Preserve static constants
MockWebSocketClass.CONNECTING = 0;
MockWebSocketClass.OPEN = 1;
MockWebSocketClass.CLOSING = 2;
MockWebSocketClass.CLOSED = 3;

const originalWebSocket = global.WebSocket;
global.WebSocket = MockWebSocketClass;

import { InventoryManager, INVENTORY_COLORS, getInventoryManager } from '../inventory';

// Mock Logger
jest.mock('../../utils/Logger', () => ({
  Logger: jest.fn().mockImplementation(() => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  })),
}));

// Helper to build an InventoryStatus object without TS annotations
function makeStatus(productId, stockStatus, stockQuantity, reservedQuantity) {
  return { productId, stockStatus, stockQuantity, reservedQuantity };
}

afterAll(() => {
  global.WebSocket = originalWebSocket;
});

describe('INVENTORY_COLORS', () => {
  it('should have green for in_stock', () => {
    expect(INVENTORY_COLORS.in_stock).toBe(0x00ff00);
  });

  it('should have orange for low_stock', () => {
    expect(INVENTORY_COLORS.low_stock).toBe(0xffa500);
  });

  it('should have red for out_of_stock', () => {
    expect(INVENTORY_COLORS.out_of_stock).toBe(0xff0000);
  });

  it('should have rose gold default', () => {
    expect(INVENTORY_COLORS.default).toBe(0xd4af37);
  });
});

describe('InventoryManager', () => {
  let manager;

  beforeEach(() => {
    jest.useFakeTimers();
    MockWebSocketClass.mockClear();
    MockWebSocketClass.mockImplementation(() => createMockWebSocket());
    manager = new InventoryManager({ wsUrl: 'ws://test/inventory' });
  });

  afterEach(() => {
    manager.disconnect();
    jest.useRealTimers();
  });

  describe('constructor', () => {
    it('should create with default config', () => {
      const mgr = new InventoryManager();
      expect(mgr).toBeDefined();
      mgr.disconnect();
    });

    it('should accept custom config', () => {
      const mgr = new InventoryManager({
        reconnectDelay: 5000,
        heartbeatInterval: 60000,
        lowStockThreshold: 5,
      });
      expect(mgr).toBeDefined();
      mgr.disconnect();
    });
  });

  describe('getStatus', () => {
    it('should return null for unknown product', () => {
      expect(manager.getStatus('unknown')).toBeNull();
    });

    it('should return status after updateInventory', () => {
      const status = makeStatus('prod-1', 'in_stock', 10, 0);
      manager.updateInventory(status);
      expect(manager.getStatus('prod-1')).toEqual(status);
    });
  });

  describe('subscribe', () => {
    it('should return unsubscribe function', () => {
      const cb = jest.fn();
      const unsub = manager.subscribe('prod-1', cb);
      expect(typeof unsub).toBe('function');
      unsub();
    });

    it('should allow multiple subscribers per product', () => {
      const cb1 = jest.fn();
      const cb2 = jest.fn();
      manager.subscribe('prod-1', cb1);
      manager.subscribe('prod-1', cb2);
      // Both should not throw
    });

    it('should send subscribe message when connected', () => {
      // Connect and simulate open
      manager.connect();
      const ws = manager['ws'];
      ws.readyState = WebSocket.OPEN;
      ws.onopen();

      ws.send.mockClear();
      manager.subscribe('prod-sub-1', jest.fn());

      expect(ws.send).toHaveBeenCalled();
      const sentMsg = JSON.parse(ws.send.mock.calls[0][0]);
      expect(sentMsg.type).toBe('subscribe');
      expect(sentMsg.productId).toBe('prod-sub-1');
    });

    it('should notify subscriber when inventory updates', () => {
      const cb = jest.fn();
      manager.subscribe('prod-1', cb);

      const status = makeStatus('prod-1', 'low_stock', 3, 0);
      manager.updateInventory(status);

      expect(cb).toHaveBeenCalledWith(status);
    });

    it('should notify multiple subscribers on update', () => {
      const cb1 = jest.fn();
      const cb2 = jest.fn();
      manager.subscribe('prod-1', cb1);
      manager.subscribe('prod-1', cb2);

      const status = makeStatus('prod-1', 'in_stock', 20, 0);
      manager.updateInventory(status);

      expect(cb1).toHaveBeenCalledWith(status);
      expect(cb2).toHaveBeenCalledWith(status);
    });

    it('should handle callback errors without breaking other subscribers', () => {
      const errorCb = jest.fn().mockImplementation(() => { throw new Error('boom'); });
      const goodCb = jest.fn();
      manager.subscribe('prod-1', errorCb);
      manager.subscribe('prod-1', goodCb);

      const status = makeStatus('prod-1', 'in_stock', 10, 0);
      manager.updateInventory(status);

      expect(errorCb).toHaveBeenCalled();
      expect(goodCb).toHaveBeenCalled();
    });
  });

  describe('unsubscribe', () => {
    it('should stop receiving updates after unsubscribe', () => {
      const cb = jest.fn();
      const unsub = manager.subscribe('prod-1', cb);
      unsub();

      const status = makeStatus('prod-1', 'in_stock', 10, 0);
      manager.updateInventory(status);

      expect(cb).not.toHaveBeenCalled();
    });

    it('should send unsubscribe message when connected and last subscriber removed', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.readyState = WebSocket.OPEN;
      ws.onopen();

      const cb = jest.fn();
      const unsub = manager.subscribe('prod-unsub-1', cb);

      ws.send.mockClear();

      unsub();

      expect(ws.send).toHaveBeenCalled();
      const sentMsg = JSON.parse(ws.send.mock.calls[0][0]);
      expect(sentMsg.type).toBe('unsubscribe');
      expect(sentMsg.productId).toBe('prod-unsub-1');
    });

    it('should not send unsubscribe if other subscribers remain', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.readyState = WebSocket.OPEN;
      ws.onopen();

      const cb1 = jest.fn();
      const cb2 = jest.fn();
      const unsub1 = manager.subscribe('prod-1', cb1);
      manager.subscribe('prod-1', cb2);

      ws.send.mockClear();

      unsub1();

      // Should NOT have sent an unsubscribe message since cb2 is still subscribed
      const calls = ws.send.mock.calls.map(c => JSON.parse(c[0]));
      const unsubCalls = calls.filter(m => m.type === 'unsubscribe');
      expect(unsubCalls).toHaveLength(0);
    });

    it('should handle unsubscribe for non-existent product gracefully', () => {
      // Subscribe and immediately unsubscribe twice (second is a no-op)
      const cb = jest.fn();
      const unsub = manager.subscribe('prod-1', cb);
      unsub();
      // Calling unsub again should not throw
      expect(() => unsub()).not.toThrow();
    });
  });

  describe('connect', () => {
    it('should create a WebSocket connection', () => {
      manager.connect();
      expect(manager['ws']).toBeDefined();
      expect(manager['ws']).not.toBeNull();
    });

    it('should use custom URL when provided', () => {
      manager.connect('ws://custom/url');
      // Should not throw and ws should be created
      expect(manager['ws']).toBeDefined();
    });

    it('should set up event handlers on WebSocket', () => {
      manager.connect();
      const ws = manager['ws'];
      expect(ws.onopen).toBeDefined();
      expect(ws.onmessage).toBeDefined();
      expect(ws.onerror).toBeDefined();
      expect(ws.onclose).toBeDefined();
    });

    it('should handle WebSocket constructor failure', () => {
      // Override mock to throw
      MockWebSocketClass.mockImplementation(() => { throw new Error('Connection refused'); });

      expect(() => manager.connect()).not.toThrow();

      // Restore normal mock behavior
      MockWebSocketClass.mockImplementation(() => createMockWebSocket());
    });
  });

  describe('disconnect', () => {
    it('should not throw when called multiple times', () => {
      expect(() => {
        manager.disconnect();
        manager.disconnect();
      }).not.toThrow();
    });

    it('should close the WebSocket', () => {
      manager.connect();
      const ws = manager['ws'];

      manager.disconnect();

      expect(ws.close).toHaveBeenCalled();
      expect(manager['ws']).toBeNull();
    });

    it('should clear reconnect timeout', () => {
      // Trigger a reconnect by simulating close
      manager.connect();
      const ws = manager['ws'];
      ws.onclose({ code: 1000, reason: 'test' });
      // Now reconnectTimeout should be set
      expect(manager['reconnectTimeout']).not.toBeNull();

      manager.disconnect();
      expect(manager['reconnectTimeout']).toBeNull();
    });

    it('should clear heartbeat interval', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.onopen();
      // handleOpen starts heartbeat
      expect(manager['heartbeatInterval']).not.toBeNull();

      manager.disconnect();
      expect(manager['heartbeatInterval']).toBeNull();
    });

    it('should set isConnected to false', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.onopen();
      expect(manager.isConnectedToServer()).toBe(true);

      manager.disconnect();
      expect(manager.isConnectedToServer()).toBe(false);
    });
  });

  describe('handleOpen (via ws.onopen)', () => {
    it('should set isConnected to true', () => {
      manager.connect();
      manager['ws'].onopen();
      expect(manager.isConnectedToServer()).toBe(true);
    });

    it('should start heartbeat', () => {
      manager.connect();
      manager['ws'].onopen();
      expect(manager['heartbeatInterval']).not.toBeNull();
    });

    it('should resubscribe to all existing subscriptions', () => {
      // Subscribe before connecting
      manager.subscribe('prod-1', jest.fn());
      manager.subscribe('prod-2', jest.fn());

      manager.connect();
      const ws = manager['ws'];
      ws.readyState = WebSocket.OPEN;

      ws.onopen();

      const sentMsgs = ws.send.mock.calls.map(c => JSON.parse(c[0]));
      const subscribeMsgs = sentMsgs.filter(m => m.type === 'subscribe');
      expect(subscribeMsgs).toHaveLength(2);
      const productIds = subscribeMsgs.map(m => m.productId).sort();
      expect(productIds).toEqual(['prod-1', 'prod-2']);
    });
  });

  describe('handleMessage (via ws.onmessage)', () => {
    it('should handle update messages and update inventory', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.onopen();

      const status = makeStatus('prod-1', 'in_stock', 10, 0);
      ws.onmessage({ data: JSON.stringify({ type: 'update', data: status, timestamp: Date.now() }) });

      expect(manager.getStatus('prod-1')).toEqual(status);
    });

    it('should notify subscribers on update message', () => {
      const cb = jest.fn();
      manager.subscribe('prod-1', cb);

      manager.connect();
      const ws = manager['ws'];
      ws.onopen();

      const status = makeStatus('prod-1', 'low_stock', 5, 0);
      ws.onmessage({ data: JSON.stringify({ type: 'update', data: status, timestamp: Date.now() }) });

      expect(cb).toHaveBeenCalledWith(status);
    });

    it('should ignore update messages without data', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.onopen();

      // No data field
      expect(() => {
        ws.onmessage({ data: JSON.stringify({ type: 'update', timestamp: Date.now() }) });
      }).not.toThrow();
    });

    it('should handle heartbeat messages silently', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.onopen();

      expect(() => {
        ws.onmessage({ data: JSON.stringify({ type: 'heartbeat', timestamp: Date.now() }) });
      }).not.toThrow();
    });

    it('should warn on unknown message types', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.onopen();

      ws.onmessage({ data: JSON.stringify({ type: 'unknown_type', timestamp: Date.now() }) });
      // Should not throw, logger.warn is called (mocked)
    });

    it('should handle invalid JSON gracefully', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.onopen();

      expect(() => {
        ws.onmessage({ data: 'not valid json{{{' });
      }).not.toThrow();
    });
  });

  describe('handleError (via ws.onerror)', () => {
    it('should handle error events without throwing', () => {
      manager.connect();
      const ws = manager['ws'];

      expect(() => {
        ws.onerror(new Event('error'));
      }).not.toThrow();
    });
  });

  describe('handleClose (via ws.onclose)', () => {
    it('should set isConnected to false', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.onopen();
      expect(manager.isConnectedToServer()).toBe(true);

      ws.onclose({ code: 1000, reason: 'Normal' });
      expect(manager.isConnectedToServer()).toBe(false);
    });

    it('should clear heartbeat interval', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.onopen();
      expect(manager['heartbeatInterval']).not.toBeNull();

      ws.onclose({ code: 1000, reason: 'test' });
      expect(manager['heartbeatInterval']).toBeNull();
    });

    it('should schedule reconnection', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.onclose({ code: 1006, reason: 'Abnormal' });

      expect(manager['reconnectTimeout']).not.toBeNull();
    });
  });

  describe('scheduleReconnect', () => {
    it('should reconnect after delay', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.onclose({ code: 1006, reason: 'Abnormal' });

      // Spy on connect to verify it gets called
      const connectSpy = jest.spyOn(manager, 'connect');

      jest.advanceTimersByTime(3000); // default reconnectDelay

      expect(connectSpy).toHaveBeenCalled();
    });

    it('should not schedule multiple reconnects', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.onclose({ code: 1006, reason: 'Abnormal' });

      const timeoutRef = manager['reconnectTimeout'];

      // Manually call scheduleReconnect again
      manager['scheduleReconnect']();

      // Should be the same timeout reference (no duplicate)
      expect(manager['reconnectTimeout']).toBe(timeoutRef);
    });
  });

  describe('startHeartbeat', () => {
    it('should send heartbeat messages at configured interval', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.readyState = WebSocket.OPEN;

      ws.onopen();
      ws.send.mockClear();

      // Advance timer to trigger heartbeat
      jest.advanceTimersByTime(30000); // default heartbeatInterval

      const sent = ws.send.mock.calls.map(c => JSON.parse(c[0]));
      const heartbeats = sent.filter(m => m.type === 'heartbeat');
      expect(heartbeats.length).toBeGreaterThanOrEqual(1);
    });

    it('should clear previous heartbeat before starting new one', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.readyState = WebSocket.OPEN;

      ws.onopen();
      const firstInterval = manager['heartbeatInterval'];

      // Call handleOpen again (simulating reconnect)
      ws.onopen();
      const secondInterval = manager['heartbeatInterval'];

      // The intervals should be different (old one cleared, new one created)
      expect(secondInterval).not.toBe(firstInterval);
    });
  });

  describe('sendMessage', () => {
    it('should warn when WebSocket is not connected', () => {
      // Without connecting, sendMessage should not throw
      // We test this indirectly through subscribe when not connected
      const cb = jest.fn();
      manager.subscribe('prod-1', cb);
      // subscribe without connecting should not crash
    });

    it('should handle send failure gracefully', () => {
      manager.connect();
      const ws = manager['ws'];
      ws.readyState = WebSocket.OPEN;
      ws.onopen();
      ws.send.mockImplementation(() => { throw new Error('Send failed'); });

      // Should not throw when send fails
      expect(() => {
        manager.subscribe('prod-send-fail', jest.fn());
      }).not.toThrow();
    });
  });

  describe('getGlowColor', () => {
    it('should return green for in_stock', () => {
      const status = makeStatus('p1', 'in_stock', 10, 0);
      expect(manager.getGlowColor(status)).toBe(INVENTORY_COLORS.in_stock);
    });

    it('should return orange for low_stock', () => {
      const status = makeStatus('p1', 'low_stock', 3, 0);
      expect(manager.getGlowColor(status)).toBe(INVENTORY_COLORS.low_stock);
    });

    it('should return red for out_of_stock', () => {
      const status = makeStatus('p1', 'out_of_stock', 0, 0);
      expect(manager.getGlowColor(status)).toBe(INVENTORY_COLORS.out_of_stock);
    });
  });

  describe('getOpacity', () => {
    it('should return 1.0 for in_stock', () => {
      const status = makeStatus('p1', 'in_stock', 10, 0);
      expect(manager.getOpacity(status)).toBe(1.0);
    });

    it('should return 0.8 for low_stock', () => {
      const status = makeStatus('p1', 'low_stock', 3, 0);
      expect(manager.getOpacity(status)).toBe(0.8);
    });

    it('should return 0.4 for out_of_stock', () => {
      const status = makeStatus('p1', 'out_of_stock', 0, 0);
      expect(manager.getOpacity(status)).toBe(0.4);
    });

    it('should return 1.0 for unknown status (default)', () => {
      const status = makeStatus('p1', 'some_unknown_status', 10, 0);
      expect(manager.getOpacity(status)).toBe(1.0);
    });
  });

  describe('getBadgeText', () => {
    it('should return quantity message for low_stock', () => {
      const status = makeStatus('p1', 'low_stock', 3, 0);
      expect(manager.getBadgeText(status)).toBe('Only 3 left');
    });

    it('should return "Out of Stock" for out_of_stock', () => {
      const status = makeStatus('p1', 'out_of_stock', 0, 0);
      expect(manager.getBadgeText(status)).toBe('Out of Stock');
    });

    it('should return null for in_stock', () => {
      const status = makeStatus('p1', 'in_stock', 50, 0);
      expect(manager.getBadgeText(status)).toBeNull();
    });

    it('should return null for unknown status (default)', () => {
      const status = makeStatus('p1', 'some_other_status', 10, 0);
      expect(manager.getBadgeText(status)).toBeNull();
    });
  });

  describe('determineStockStatus', () => {
    it('should return out_of_stock for zero quantity', () => {
      expect(manager.determineStockStatus(0)).toBe('out_of_stock');
    });

    it('should return low_stock at threshold boundary', () => {
      expect(manager.determineStockStatus(10)).toBe('low_stock');
    });

    it('should return low_stock below threshold', () => {
      expect(manager.determineStockStatus(1)).toBe('low_stock');
    });

    it('should return in_stock above threshold', () => {
      expect(manager.determineStockStatus(11)).toBe('in_stock');
    });

    it('should respect custom lowStockThreshold', () => {
      const customMgr = new InventoryManager({ lowStockThreshold: 5 });
      expect(customMgr.determineStockStatus(5)).toBe('low_stock');
      expect(customMgr.determineStockStatus(6)).toBe('in_stock');
      customMgr.disconnect();
    });
  });

  describe('updateInventory', () => {
    it('should update local cache', () => {
      const status = makeStatus('prod-1', 'in_stock', 10, 0);
      manager.updateInventory(status);
      expect(manager.getStatus('prod-1')).toEqual(status);
    });

    it('should notify subscribers', () => {
      const cb = jest.fn();
      manager.subscribe('prod-1', cb);

      const status = makeStatus('prod-1', 'out_of_stock', 0, 0);
      manager.updateInventory(status);

      expect(cb).toHaveBeenCalledWith(status);
    });

    it('should not notify subscribers for other products', () => {
      const cb = jest.fn();
      manager.subscribe('prod-1', cb);

      const status = makeStatus('prod-2', 'in_stock', 10, 0);
      manager.updateInventory(status);

      expect(cb).not.toHaveBeenCalled();
    });
  });

  describe('isConnectedToServer', () => {
    it('should return false initially', () => {
      expect(manager.isConnectedToServer()).toBe(false);
    });

    it('should return true after connection opens', () => {
      manager.connect();
      manager['ws'].onopen();
      expect(manager.isConnectedToServer()).toBe(true);
    });

    it('should return false after disconnect', () => {
      manager.connect();
      manager['ws'].onopen();
      manager.disconnect();
      expect(manager.isConnectedToServer()).toBe(false);
    });
  });

  describe('getAllInventory', () => {
    it('should return empty map initially', () => {
      const inv = manager.getAllInventory();
      expect(inv.size).toBe(0);
    });

    it('should return copy of inventory map', () => {
      const status = makeStatus('prod-1', 'in_stock', 10, 0);
      manager.updateInventory(status);

      const inv = manager.getAllInventory();
      expect(inv.size).toBe(1);
      expect(inv.get('prod-1')).toEqual(status);

      // Verify it is a copy (modifying returned map does not affect internal state)
      inv.delete('prod-1');
      expect(manager.getStatus('prod-1')).toEqual(status);
    });

    it('should reflect multiple inventory updates', () => {
      manager.updateInventory(makeStatus('prod-1', 'in_stock', 10, 0));
      manager.updateInventory(makeStatus('prod-2', 'low_stock', 3, 0));
      manager.updateInventory(makeStatus('prod-3', 'out_of_stock', 0, 0));

      const inv = manager.getAllInventory();
      expect(inv.size).toBe(3);
    });
  });

  describe('clearCache', () => {
    it('should clear all inventory entries', () => {
      manager.updateInventory(makeStatus('prod-1', 'in_stock', 10, 0));
      manager.updateInventory(makeStatus('prod-2', 'low_stock', 3, 0));

      expect(manager.getAllInventory().size).toBe(2);

      manager.clearCache();

      expect(manager.getAllInventory().size).toBe(0);
      expect(manager.getStatus('prod-1')).toBeNull();
    });
  });
});

describe('getInventoryManager', () => {
  // Reset the singleton between tests
  beforeEach(() => {
    jest.resetModules();
    // Re-register Logger mock after module reset
    jest.mock('../../utils/Logger', () => ({
      Logger: jest.fn().mockImplementation(() => ({
        info: jest.fn(),
        warn: jest.fn(),
        error: jest.fn(),
        debug: jest.fn(),
      })),
    }));
  });

  it('should return an InventoryManager instance', () => {
    const mod = require('../inventory');
    const instance = mod.getInventoryManager();
    expect(instance).toBeDefined();
    expect(instance).toBeInstanceOf(mod.InventoryManager);
    instance.disconnect();
  });

  it('should return the same instance on subsequent calls', () => {
    const mod = require('../inventory');
    const first = mod.getInventoryManager();
    const second = mod.getInventoryManager();
    expect(first).toBe(second);
    first.disconnect();
  });

  it('should accept config on first call', () => {
    const mod = require('../inventory');
    const instance = mod.getInventoryManager({ lowStockThreshold: 20 });
    expect(instance).toBeDefined();
    instance.disconnect();
  });
});
