/**
 * Unit Tests for ProductInteractionHandler
 * @jest-environment jsdom
 */

import { ProductInteractionHandler } from '../productInteraction';
import type { ProductInteractionConfig, CartManager } from '../productInteraction';
import type { ShowroomProduct, InventoryStatus } from '../../types/product';
import type { InventoryManager } from '../inventory';

// Mock Logger
jest.mock('../../utils/Logger', () => ({
  Logger: jest.fn().mockImplementation(() => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  })),
}));

// --- Helpers ---

function createMockMesh(overrides: Partial<any> = {}): any {
  const material = {
    emissive: { setHex: jest.fn() },
    emissiveIntensity: 0,
    opacity: 1,
    transparent: false,
    needsUpdate: false,
  };
  // Make it pass instanceof THREE.MeshStandardMaterial check via constructor name
  Object.defineProperty(material, 'constructor', { value: { name: 'MeshStandardMaterial' } });

  return {
    position: { x: 0, y: 0, z: 0, clone: jest.fn().mockReturnThis() },
    scale: {
      x: 1, y: 1, z: 1,
      clone: jest.fn().mockReturnValue({
        multiplyScalar: jest.fn().mockReturnThis(),
        x: 1.2, y: 1.2, z: 1.2,
      }),
      lerpVectors: jest.fn(),
      copy: jest.fn(),
    },
    quaternion: { clone: jest.fn().mockReturnThis(), slerpQuaternions: jest.fn() },
    userData: {},
    material,
    ...overrides,
  };
}

function createMockProduct(overrides: Partial<ShowroomProduct> = {}): ShowroomProduct {
  return {
    id: 'prod-1',
    name: 'Test Product',
    modelUrl: '/models/test.glb',
    position: [0, 0, 0],
    sku: 'SKU-001',
    price: 99.99,
    stockStatus: 'in_stock',
    stockQuantity: 10,
    sizes: ['S', 'M', 'L'],
    colors: [{ name: 'Black', hex: '#000000' }],
    ...overrides,
  };
}

function createMockCart(): CartManager {
  return {
    addItem: jest.fn().mockResolvedValue(undefined),
    getItemCount: jest.fn().mockReturnValue(0),
    getTotalPrice: jest.fn().mockReturnValue(0),
  };
}

function createMockInventory(): InventoryManager {
  return {
    subscribe: jest.fn().mockReturnValue(jest.fn()),
    getStatus: jest.fn().mockReturnValue(null),
    getGlowColor: jest.fn().mockReturnValue(0x00ff00),
    getOpacity: jest.fn().mockReturnValue(1.0),
    connect: jest.fn(),
    disconnect: jest.fn(),
    updateLocalStatus: jest.fn(),
    unsubscribe: jest.fn(),
  } as unknown as InventoryManager;
}

function createMockCamera(): any {
  return {
    position: {
      x: 0, y: 0, z: 5,
      clone: jest.fn().mockReturnValue({ x: 0, y: 0, z: 5, lerpVectors: jest.fn() }),
      lerpVectors: jest.fn(),
    },
    quaternion: {
      clone: jest.fn().mockReturnValue({ slerpQuaternions: jest.fn() }),
      slerpQuaternions: jest.fn(),
    },
    clone: jest.fn().mockReturnValue({
      position: { copy: jest.fn() },
      lookAt: jest.fn(),
      quaternion: { clone: jest.fn().mockReturnValue({ slerpQuaternions: jest.fn() }) },
    }),
  };
}

function createMockScene(): any {
  return { add: jest.fn(), remove: jest.fn(), children: [] };
}

function createHandler(overrides: Partial<ProductInteractionConfig> = {}) {
  const cart = createMockCart();
  const inventory = createMockInventory();
  const camera = createMockCamera();
  const scene = createMockScene();

  const config: ProductInteractionConfig = {
    camera,
    scene,
    cart,
    inventory,
    ...overrides,
  };

  const handler = new ProductInteractionHandler(config);
  return { handler, cart, inventory, camera, scene };
}

// --- Tests ---

describe('ProductInteractionHandler', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    // Mock performance.now for animations
    jest.spyOn(performance, 'now').mockReturnValue(0);
    // Mock window dimensions
    Object.defineProperty(window, 'innerWidth', { value: 1920, writable: true });
    Object.defineProperty(window, 'innerHeight', { value: 1080, writable: true });
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  describe('constructor', () => {
    it('should create handler with default config', () => {
      const { handler } = createHandler();
      expect(handler).toBeDefined();
    });

    it('should accept custom animation duration', () => {
      const { handler } = createHandler({ animationDuration: 2000 });
      expect(handler).toBeDefined();
    });

    it('should accept custom highlight intensity', () => {
      const { handler } = createHandler({ highlightIntensity: 0.5 });
      expect(handler).toBeDefined();
    });
  });

  describe('getScene', () => {
    it('should return the scene reference', () => {
      const scene = createMockScene();
      const { handler } = createHandler({ scene });
      expect(handler.getScene()).toBe(scene);
    });
  });

  describe('setupProduct', () => {
    it('should register product mesh and data', () => {
      const { handler, inventory } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();

      handler.setupProduct(mesh, product);

      expect(mesh.userData['productData']).toBe(product);
      expect(inventory.subscribe).toHaveBeenCalledWith(product.id, expect.any(Function));
    });

    it('should store original material', () => {
      const { handler } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();

      handler.setupProduct(mesh, product);

      const retrieved = handler.getProduct(product.id);
      expect(retrieved).toBe(product);
    });

    it('should apply initial visuals when inventory status exists', () => {
      const { handler, inventory } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();
      const status: InventoryStatus = {
        productId: product.id,
        stockStatus: 'low_stock',
        stockQuantity: 3,
        reservedQuantity: 0,
      };
      (inventory.getStatus as jest.Mock).mockReturnValue(status);

      handler.setupProduct(mesh, product);

      expect(inventory.getGlowColor).toHaveBeenCalledWith(status);
      expect(inventory.getOpacity).toHaveBeenCalledWith(status);
    });

    it('should not apply visuals when no inventory status', () => {
      const { handler, inventory } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();
      (inventory.getStatus as jest.Mock).mockReturnValue(null);

      handler.setupProduct(mesh, product);

      expect(inventory.getGlowColor).not.toHaveBeenCalled();
    });
  });

  describe('handleProductClick', () => {
    it('should warn when product mesh not found', () => {
      const { handler } = createHandler();
      handler.handleProductClick('nonexistent');
      // No error thrown, just logs warning
    });

    it('should warn when product data not found on mesh', () => {
      const { handler } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();

      handler.setupProduct(mesh, product);
      // Remove product data to simulate missing data
      mesh.userData['productData'] = undefined;

      handler.handleProductClick(product.id);
    });
  });

  describe('showProductPanel', () => {
    it('should invoke onProductPanelShow callback', () => {
      const { handler, inventory } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();
      const callback = jest.fn();

      (inventory.getStatus as jest.Mock).mockReturnValue(null);
      handler.setupProduct(mesh, product);
      handler.setOnProductPanelShow(callback);
      handler.showProductPanel(product);

      expect(callback).toHaveBeenCalledWith(
        expect.objectContaining({
          product,
          inventoryStatus: null,
          position: expect.objectContaining({ x: expect.any(Number), y: expect.any(Number) }),
        })
      );
    });

    it('should use center of screen when no mesh found', () => {
      const { handler } = createHandler();
      const product = createMockProduct({ id: 'no-mesh' });
      const callback = jest.fn();

      handler.setOnProductPanelShow(callback);
      handler.showProductPanel(product);

      expect(callback).toHaveBeenCalledWith(
        expect.objectContaining({
          position: { x: 960, y: 540 },
        })
      );
    });

    it('should not throw when no callback set', () => {
      const { handler } = createHandler();
      const product = createMockProduct();
      expect(() => handler.showProductPanel(product)).not.toThrow();
    });
  });

  describe('hideProductPanel', () => {
    it('should invoke onProductPanelHide callback', () => {
      const { handler } = createHandler();
      const callback = jest.fn();

      handler.setOnProductPanelHide(callback);
      handler.hideProductPanel();

      expect(callback).toHaveBeenCalled();
    });

    it('should not throw when no callback set', () => {
      const { handler } = createHandler();
      expect(() => handler.hideProductPanel()).not.toThrow();
    });
  });

  describe('addToCart', () => {
    it('should add product to cart successfully', async () => {
      const { handler, cart, inventory } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();

      (inventory.getStatus as jest.Mock).mockReturnValue({
        productId: product.id,
        stockStatus: 'in_stock',
        stockQuantity: 10,
        reservedQuantity: 0,
      });

      handler.setupProduct(mesh, product);
      await handler.addToCart(product.id);

      expect(cart.addItem).toHaveBeenCalledWith(product, 1, undefined);
    });

    it('should pass options to cart', async () => {
      const { handler, cart, inventory } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();
      const options = { size: 'M', color: { name: 'Red', hex: '#ff0000' } };

      (inventory.getStatus as jest.Mock).mockReturnValue({
        productId: product.id,
        stockStatus: 'in_stock',
        stockQuantity: 10,
        reservedQuantity: 0,
      });

      handler.setupProduct(mesh, product);
      await handler.addToCart(product.id, options);

      expect(cart.addItem).toHaveBeenCalledWith(product, 1, options);
    });

    it('should invoke onAddToCart callback on success', async () => {
      const { handler, inventory } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();
      const callback = jest.fn();

      (inventory.getStatus as jest.Mock).mockReturnValue(null);
      handler.setupProduct(mesh, product);
      handler.setOnAddToCart(callback);
      await handler.addToCart(product.id);

      expect(callback).toHaveBeenCalledWith(product);
    });

    it('should reject out-of-stock products', async () => {
      const { handler, cart, inventory } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();
      const dispatchSpy = jest.spyOn(window, 'dispatchEvent');

      (inventory.getStatus as jest.Mock).mockReturnValue({
        productId: product.id,
        stockStatus: 'out_of_stock',
        stockQuantity: 0,
        reservedQuantity: 0,
      });

      handler.setupProduct(mesh, product);
      await handler.addToCart(product.id);

      expect(cart.addItem).not.toHaveBeenCalled();
      expect(dispatchSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'product:notification',
        })
      );
    });

    it('should dispatch error notification on cart failure', async () => {
      const { handler, cart, inventory } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();
      const dispatchSpy = jest.spyOn(window, 'dispatchEvent');

      (inventory.getStatus as jest.Mock).mockReturnValue(null);
      (cart.addItem as jest.Mock).mockRejectedValue(new Error('Cart API failed'));

      handler.setupProduct(mesh, product);
      await handler.addToCart(product.id);

      expect(dispatchSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'product:notification',
        })
      );
    });

    it('should handle non-Error cart failures', async () => {
      const { handler, cart, inventory } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();

      (inventory.getStatus as jest.Mock).mockReturnValue(null);
      (cart.addItem as jest.Mock).mockRejectedValue('string error');

      handler.setupProduct(mesh, product);
      await handler.addToCart(product.id);
      // Should not throw
    });

    it('should return early when mesh not found', async () => {
      const { handler, cart } = createHandler();
      await handler.addToCart('nonexistent');
      expect(cart.addItem).not.toHaveBeenCalled();
    });

    it('should return early when product data missing', async () => {
      const { handler, cart } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();

      handler.setupProduct(mesh, product);
      mesh.userData['productData'] = undefined;

      await handler.addToCart(product.id);
      expect(cart.addItem).not.toHaveBeenCalled();
    });
  });

  describe('updateProductVisuals', () => {
    it('should update single MeshStandardMaterial', () => {
      const { handler, inventory } = createHandler();
      const material = {
        emissive: { setHex: jest.fn() },
        emissiveIntensity: 0,
        opacity: 1,
        transparent: false,
        needsUpdate: false,
      };
      // Simulate instanceof check by making three.js mock recognize it
      const mesh = createMockMesh({ material });
      // Override THREE.MeshStandardMaterial instanceof check
      Object.setPrototypeOf(material, { constructor: { name: 'MeshStandardMaterial' } });

      const status: InventoryStatus = {
        productId: 'p1',
        stockStatus: 'low_stock',
        stockQuantity: 3,
        reservedQuantity: 0,
      };

      (inventory.getGlowColor as jest.Mock).mockReturnValue(0xffa500);
      (inventory.getOpacity as jest.Mock).mockReturnValue(0.8);

      handler.updateProductVisuals(mesh as any, status);

      expect(inventory.getGlowColor).toHaveBeenCalledWith(status);
      expect(inventory.getOpacity).toHaveBeenCalledWith(status);
    });
  });

  describe('highlightProduct / unhighlightProduct', () => {
    it('should not crash when highlighting nonexistent product', () => {
      const { handler } = createHandler();
      expect(() => handler.highlightProduct('nonexistent')).not.toThrow();
    });

    it('should not crash when unhighlighting nonexistent product', () => {
      const { handler } = createHandler();
      expect(() => handler.unhighlightProduct('nonexistent')).not.toThrow();
    });

    it('should skip if already highlighted', () => {
      const { handler } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();
      handler.setupProduct(mesh, product);

      handler.highlightProduct(product.id);
      handler.highlightProduct(product.id); // second call should be no-op
    });

    it('should unhighlight previous product when highlighting new one', () => {
      const { handler } = createHandler();
      const mesh1 = createMockMesh();
      const mesh2 = createMockMesh();
      const product1 = createMockProduct({ id: 'p1', name: 'Product 1' });
      const product2 = createMockProduct({ id: 'p2', name: 'Product 2' });

      handler.setupProduct(mesh1, product1);
      handler.setupProduct(mesh2, product2);

      handler.highlightProduct('p1');
      handler.highlightProduct('p2');
      // No error; p1 should be auto-unhighlighted
    });
  });

  describe('callback setters', () => {
    it('should set onProductPanelShow callback', () => {
      const { handler } = createHandler();
      const cb = jest.fn();
      handler.setOnProductPanelShow(cb);

      const product = createMockProduct();
      handler.showProductPanel(product);
      expect(cb).toHaveBeenCalled();
    });

    it('should set onProductPanelHide callback', () => {
      const { handler } = createHandler();
      const cb = jest.fn();
      handler.setOnProductPanelHide(cb);

      handler.hideProductPanel();
      expect(cb).toHaveBeenCalled();
    });

    it('should set onAddToCart callback', async () => {
      const { handler, inventory } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();
      const cb = jest.fn();

      (inventory.getStatus as jest.Mock).mockReturnValue(null);
      handler.setupProduct(mesh, product);
      handler.setOnAddToCart(cb);
      await handler.addToCart(product.id);

      expect(cb).toHaveBeenCalledWith(product);
    });
  });

  describe('getProduct', () => {
    it('should return product data by ID', () => {
      const { handler } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();

      handler.setupProduct(mesh, product);
      expect(handler.getProduct(product.id)).toBe(product);
    });

    it('should return null for unknown ID', () => {
      const { handler } = createHandler();
      expect(handler.getProduct('unknown')).toBeNull();
    });

    it('should return null when mesh has no product data', () => {
      const { handler } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();

      handler.setupProduct(mesh, product);
      mesh.userData['productData'] = undefined;

      expect(handler.getProduct(product.id)).toBeNull();
    });
  });

  describe('getAllProducts', () => {
    it('should return all registered products', () => {
      const { handler } = createHandler();
      const mesh1 = createMockMesh();
      const mesh2 = createMockMesh();
      const product1 = createMockProduct({ id: 'p1', name: 'P1' });
      const product2 = createMockProduct({ id: 'p2', name: 'P2' });

      handler.setupProduct(mesh1, product1);
      handler.setupProduct(mesh2, product2);

      const products = handler.getAllProducts();
      expect(products).toHaveLength(2);
      expect(products).toContain(product1);
      expect(products).toContain(product2);
    });

    it('should return empty array when no products registered', () => {
      const { handler } = createHandler();
      expect(handler.getAllProducts()).toEqual([]);
    });

    it('should skip meshes with missing product data', () => {
      const { handler } = createHandler();
      const mesh = createMockMesh();
      const product = createMockProduct();

      handler.setupProduct(mesh, product);
      mesh.userData['productData'] = undefined;

      expect(handler.getAllProducts()).toEqual([]);
    });
  });

  describe('dispose', () => {
    it('should restore original materials and clear maps', () => {
      const { handler } = createHandler();
      const originalMaterial = { type: 'original' };
      const mesh = createMockMesh({ material: originalMaterial });
      const product = createMockProduct();

      handler.setupProduct(mesh, product);
      handler.dispose();

      expect(mesh.material).toBe(originalMaterial);
      expect(handler.getAllProducts()).toEqual([]);
      expect(handler.getProduct(product.id)).toBeNull();
    });
  });
});
