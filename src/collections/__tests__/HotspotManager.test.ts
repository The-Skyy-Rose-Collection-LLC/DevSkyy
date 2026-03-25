/**
 * Unit Tests for HotspotManager
 * @jest-environment jsdom
 */

import * as THREE from 'three';
import { HotspotManager } from '../HotspotManager';

// Mock Logger
jest.mock('../../utils/Logger', () => ({
  Logger: jest.fn().mockImplementation(() => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  })),
}));

function createMockScene() {
  return {
    add: jest.fn(),
    remove: jest.fn(),
  };
}

function createMockCamera() {
  return {
    position: { lerp: jest.fn(), set: jest.fn(), x: 0, y: 0, z: 0 },
    lookAt: jest.fn(),
  };
}

function createMockRenderer() {
  const canvas = document.createElement('canvas');
  canvas.getBoundingClientRect = jest.fn().mockReturnValue({
    left: 0, top: 0, width: 800, height: 600,
  });
  return {
    domElement: canvas,
  };
}

function makeHotspotData(overrides) {
  return {
    product_id: 1,
    position: { x: 0, y: 1, z: 0 },
    title: 'Test Product',
    price: 99.99,
    image_url: '/img/test.jpg',
    woocommerce_url: '/product/test',
    collection_slug: 'black-rose',
    ...overrides,
  };
}

function makeConfig(overrides) {
  return {
    collection_type: 'black_rose',
    collection_name: 'Black Rose',
    experience_url: '/experience/black-rose',
    hotspots: [makeHotspotData()],
    camera_waypoints: [
      {
        scroll_percent: 0,
        camera_position: { x: 0, y: 5, z: 10 },
        camera_target: { x: 0, y: 0, z: 0 },
        duration_ms: 1000,
      },
    ],
    total_products: 1,
    scene_bounds: {
      min: { x: -10, y: 0, z: -10 },
      max: { x: 10, y: 10, z: 10 },
    },
    ...overrides,
  };
}

describe('HotspotManager', () => {
  let scene;
  let camera;
  let renderer;

  beforeEach(() => {
    jest.clearAllMocks();
    scene = createMockScene();
    camera = createMockCamera();
    renderer = createMockRenderer();
    global.fetch = jest.fn();
  });

  afterEach(() => {
    delete global.fetch;
  });

  describe('constructor', () => {
    it('should create with default options', () => {
      const mgr = new HotspotManager(scene, camera, renderer);
      expect(mgr).toBeDefined();
    });

    it('should create with custom options', () => {
      const onSelect = jest.fn();
      const mgr = new HotspotManager(scene, camera, renderer, {
        hotspotRadius: 0.5,
        hotspotColor: 0xff0000,
        emissiveColor: 0x00ff00,
        emissiveIntensity: 0.8,
        onProductSelected: onSelect,
      });
      expect(mgr).toBeDefined();
    });

    it('should auto-load config when configUrl and autoLoad are set', () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(makeConfig()),
      });

      const mgr = new HotspotManager(scene, camera, renderer, {
        configUrl: '/hotspots/config.json',
        autoLoad: true,
      });

      expect(global.fetch).toHaveBeenCalledWith('/hotspots/config.json');
    });

    it('should not auto-load when autoLoad is false', () => {
      const mgr = new HotspotManager(scene, camera, renderer, {
        configUrl: '/hotspots/config.json',
        autoLoad: false,
      });

      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should not auto-load when no configUrl', () => {
      const mgr = new HotspotManager(scene, camera, renderer, {
        autoLoad: true,
      });

      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  describe('loadConfig', () => {
    it('should fetch and parse config', async () => {
      const config = makeConfig();
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(config),
      });

      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      const result = await mgr.loadConfig('/hotspots/config.json');

      expect(result).toEqual(config);
      expect(mgr.isHotspotsLoaded()).toBe(true);
    });

    it('should throw on HTTP error', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      });

      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      await expect(mgr.loadConfig('/bad-url')).rejects.toThrow('HTTP 404');
    });

    it('should throw on invalid config (no hotspots)', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ camera_waypoints: [] }),
      });

      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      await expect(mgr.loadConfig('/bad-config')).rejects.toThrow('hotspots must be an array');
    });

    it('should throw on invalid config (no camera_waypoints)', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ hotspots: [] }),
      });

      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      await expect(mgr.loadConfig('/bad-config')).rejects.toThrow('camera_waypoints must be an array');
    });

    it('should throw on invalid hotspot position', async () => {
      const config = makeConfig({
        hotspots: [makeHotspotData({ position: { x: 'bad' } })],
      });
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(config),
      });

      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      await expect(mgr.loadConfig('/bad')).rejects.toThrow('Invalid hotspot position');
    });

    it('should throw on invalid product_id', async () => {
      const config = makeConfig({
        hotspots: [makeHotspotData({ product_id: -1 })],
      });
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(config),
      });

      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      await expect(mgr.loadConfig('/bad')).rejects.toThrow('Invalid product_id');
    });

    it('should throw on invalid price', async () => {
      const config = makeConfig({
        hotspots: [makeHotspotData({ price: -5 })],
      });
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(config),
      });

      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      await expect(mgr.loadConfig('/bad')).rejects.toThrow('Invalid price');
    });

    it('should render hotspots and add to scene', async () => {
      const config = makeConfig({
        hotspots: [
          makeHotspotData({ product_id: 1 }),
          makeHotspotData({ product_id: 2, position: { x: 2, y: 1, z: 0 } }),
        ],
        total_products: 2,
      });
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(config),
      });

      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      await mgr.loadConfig('/config.json');

      expect(scene.add).toHaveBeenCalledTimes(2);
      expect(mgr.getHotspots().size).toBe(2);
    });

    it('should call onHotspotCreated callback for each hotspot', async () => {
      const onCreated = jest.fn();
      const config = makeConfig();
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(config),
      });

      const mgr = new HotspotManager(scene, camera, renderer, {
        autoLoad: false,
        onHotspotCreated: onCreated,
      });
      await mgr.loadConfig('/config.json');

      expect(onCreated).toHaveBeenCalledTimes(1);
    });

    it('should handle fetch network error', async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      await expect(mgr.loadConfig('/config.json')).rejects.toThrow('Network error');
    });
  });

  describe('getConfig', () => {
    it('should return null before loading', () => {
      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      expect(mgr.getConfig()).toBeNull();
    });

    it('should return config after loading', async () => {
      const config = makeConfig();
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(config),
      });

      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      await mgr.loadConfig('/config.json');
      expect(mgr.getConfig()).toEqual(config);
    });
  });

  describe('getHotspotData', () => {
    it('should return undefined for unknown product', () => {
      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      expect(mgr.getHotspotData(999)).toBeUndefined();
    });

    it('should return hotspot data after loading', async () => {
      const config = makeConfig();
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(config),
      });

      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      await mgr.loadConfig('/config.json');

      const data = mgr.getHotspotData(1);
      expect(data).toBeDefined();
      expect(data.title).toBe('Test Product');
    });
  });

  describe('isHotspotsLoaded', () => {
    it('should return false initially', () => {
      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      expect(mgr.isHotspotsLoaded()).toBe(false);
    });
  });

  describe('setOnProductSelect', () => {
    it('should update the callback', () => {
      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      const cb = jest.fn();
      mgr.setOnProductSelect(cb);
      // No throw means success
    });
  });

  describe('dispose', () => {
    it('should not throw when no hotspots exist', () => {
      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      expect(() => mgr.dispose()).not.toThrow();
    });

    it('should dispose geometry and material for all hotspots', async () => {
      const config = makeConfig({
        hotspots: [
          makeHotspotData({ product_id: 1 }),
          makeHotspotData({ product_id: 2, position: { x: 2, y: 0, z: 0 } }),
        ],
        total_products: 2,
      });
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(config),
      });

      const mgr = new HotspotManager(scene, camera, renderer, { autoLoad: false });
      await mgr.loadConfig('/config.json');

      expect(mgr.getHotspots().size).toBe(2);

      mgr.dispose();

      expect(mgr.getHotspots().size).toBe(0);
      expect(scene.remove).toHaveBeenCalledTimes(2);
    });
  });
});
