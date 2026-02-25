/**
 * Unit Tests for InventoryManager
 * @jest-environment jsdom
 */

import { InventoryManager, INVENTORY_COLORS } from '../inventory';

// Mock Logger
jest.mock('../../utils/Logger', () => ({
  Logger: jest.fn().mockImplementation(() => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  })),
}));

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
  let manager: InventoryManager;

  beforeEach(() => {
    manager = new InventoryManager({ wsUrl: 'ws://test/inventory' });
  });

  afterEach(() => {
    manager.disconnect();
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
  });

  describe('getGlowColor', () => {
    it('should return green for in_stock', () => {
      const status = { productId: 'p1', stockStatus: 'in_stock' as const, stockQuantity: 10, reservedQuantity: 0 };
      expect(manager.getGlowColor(status)).toBe(INVENTORY_COLORS.in_stock);
    });

    it('should return orange for low_stock', () => {
      const status = { productId: 'p1', stockStatus: 'low_stock' as const, stockQuantity: 3, reservedQuantity: 0 };
      expect(manager.getGlowColor(status)).toBe(INVENTORY_COLORS.low_stock);
    });

    it('should return red for out_of_stock', () => {
      const status = { productId: 'p1', stockStatus: 'out_of_stock' as const, stockQuantity: 0, reservedQuantity: 0 };
      expect(manager.getGlowColor(status)).toBe(INVENTORY_COLORS.out_of_stock);
    });
  });

  describe('getOpacity', () => {
    it('should return 1.0 for in_stock', () => {
      const status = { productId: 'p1', stockStatus: 'in_stock' as const, stockQuantity: 10, reservedQuantity: 0 };
      expect(manager.getOpacity(status)).toBe(1.0);
    });

    it('should return reduced opacity for out_of_stock', () => {
      const status = { productId: 'p1', stockStatus: 'out_of_stock' as const, stockQuantity: 0, reservedQuantity: 0 };
      expect(manager.getOpacity(status)).toBeLessThan(1.0);
    });
  });

  describe('disconnect', () => {
    it('should not throw when called multiple times', () => {
      expect(() => {
        manager.disconnect();
        manager.disconnect();
      }).not.toThrow();
    });
  });
});
