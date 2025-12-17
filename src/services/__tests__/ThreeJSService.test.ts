/**
 * Unit Tests for ThreeJSService
 * @jest-environment jsdom
 */

import { ThreeJSService } from '../ThreeJSService';

// Mock Logger
jest.mock('../../utils/Logger', () => ({
  Logger: jest.fn().mockImplementation(() => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  })),
}));

// Mock config
jest.mock('../../config/index', () => ({
  threejsConfig: {
    enableWebGL2: true,
    enableShadows: true,
    antialias: true,
    pixelRatio: 1,
    maxTextureSize: 2048,
  },
}));

// Mock Three.js
const mockScene = {
  add: jest.fn(),
  remove: jest.fn(),
  clear: jest.fn(),
  background: null,
  fog: null,
  children: [],
};

const mockRenderer = {
  setSize: jest.fn(),
  setPixelRatio: jest.fn(),
  render: jest.fn(),
  dispose: jest.fn(),
  domElement: document.createElement('canvas'),
  shadowMap: { enabled: false, type: 0 },
  info: {
    render: { triangles: 100 },
    memory: { geometries: 5, textures: 3 },
    programs: [1, 2, 3],
  },
};

const mockCamera = {
  position: { set: jest.fn(), x: 0, y: 0, z: 5 },
  aspect: 1,
  updateProjectionMatrix: jest.fn(),
};

jest.mock('three', () => ({
  Scene: jest.fn(() => mockScene),
  WebGLRenderer: jest.fn(() => mockRenderer),
  PerspectiveCamera: jest.fn(() => mockCamera),
  Color: jest.fn(),
  Fog: jest.fn(),
  AmbientLight: jest.fn(() => ({ position: { set: jest.fn() } })),
  DirectionalLight: jest.fn(() => ({
    position: { set: jest.fn() },
    castShadow: false,
    shadow: { mapSize: { width: 0, height: 0 } },
  })),
  BoxGeometry: jest.fn(),
  SphereGeometry: jest.fn(),
  PlaneGeometry: jest.fn(),
  MeshLambertMaterial: jest.fn(() => ({ dispose: jest.fn() })),
  Mesh: jest.fn(() => ({
    position: { set: jest.fn() },
    rotation: { x: 0 },
    castShadow: false,
    receiveShadow: false,
  })),
  PCFSoftShadowMap: 2,
}));

// Mock requestAnimationFrame
let animationCallback: FrameRequestCallback | null = null;
global.requestAnimationFrame = jest.fn((cb: FrameRequestCallback) => {
  animationCallback = cb;
  return 1;
});
global.cancelAnimationFrame = jest.fn();

describe('ThreeJSService', () => {
  let service: ThreeJSService;
  let container: HTMLElement;

  beforeEach(() => {
    jest.clearAllMocks();
    service = new ThreeJSService();
    container = document.createElement('div');
    Object.defineProperty(container, 'clientWidth', { value: 800 });
    Object.defineProperty(container, 'clientHeight', { value: 600 });
    document.body.appendChild(container);
  });

  afterEach(() => {
    service.dispose();
    document.body.removeChild(container);
  });

  describe('constructor', () => {
    it('should create service instance', () => {
      expect(service).toBeDefined();
    });

    it('should not have scene initialized before initializeScene', () => {
      expect(service.getScene()).toBeNull();
      expect(service.getCamera()).toBeNull();
      expect(service.getRenderer()).toBeNull();
    });
  });

  describe('initializeScene', () => {
    it('should initialize scene, camera, and renderer', () => {
      service.initializeScene(container);

      expect(service.getScene()).toBeDefined();
      expect(service.getCamera()).toBeDefined();
      expect(service.getRenderer()).toBeDefined();
    });

    it('should set background color when provided', () => {
      service.initializeScene(container, { backgroundColor: 0x000000 });
      expect(service.getScene()).toBeDefined();
    });

    it('should set fog when provided', () => {
      service.initializeScene(container, {
        fog: { color: 0xffffff, near: 1, far: 100 },
      });
      expect(service.getScene()).toBeDefined();
    });

    it('should enable shadows when configured', () => {
      service.initializeScene(container, { enableShadows: true });
      expect(mockRenderer.shadowMap.enabled).toBe(true);
    });

    it('should append renderer to container', () => {
      service.initializeScene(container);
      expect(container.contains(mockRenderer.domElement)).toBe(true);
    });

    it('should set camera position from config', () => {
      service.initializeScene(container, {}, {}, { position: [1, 2, 3] });
      expect(mockCamera.position.set).toHaveBeenCalledWith(1, 2, 3);
    });

    it('should handle initialization errors', () => {
      const THREE = require('three');
      const originalScene = THREE.Scene;
      THREE.Scene = jest.fn(() => {
        throw new Error('Scene initialization failed');
      });

      const errorService = new ThreeJSService();
      expect(() => errorService.initializeScene(container)).toThrow('Scene initialization failed');

      THREE.Scene = originalScene;
    });
  });

  describe('createCube', () => {
    it('should create a cube mesh', () => {
      const cube = service.createCube();
      expect(cube).toBeDefined();
    });

    it('should create cube with custom parameters', () => {
      const cube = service.createCube(2, 0xff0000, [1, 2, 3]);
      expect(cube).toBeDefined();
    });
  });

  describe('createSphere', () => {
    it('should create a sphere mesh', () => {
      const sphere = service.createSphere();
      expect(sphere).toBeDefined();
    });

    it('should create sphere with custom parameters', () => {
      const sphere = service.createSphere(2, 0x00ff00, [1, 2, 3]);
      expect(sphere).toBeDefined();
    });
  });

  describe('createPlane', () => {
    it('should create a plane mesh', () => {
      const plane = service.createPlane();
      expect(plane).toBeDefined();
    });

    it('should create plane with custom parameters', () => {
      const plane = service.createPlane(20, 20, 0x808080, [0, -5, 0]);
      expect(plane).toBeDefined();
    });
  });

  describe('addToScene', () => {
    it('should add object to scene', () => {
      service.initializeScene(container);
      const cube = service.createCube();
      service.addToScene(cube);
      expect(mockScene.add).toHaveBeenCalledWith(cube);
    });

    it('should throw error if scene not initialized', () => {
      const cube = service.createCube();
      expect(() => service.addToScene(cube)).toThrow('Scene not initialized');
    });
  });

  describe('removeFromScene', () => {
    it('should remove object from scene', () => {
      service.initializeScene(container);
      const cube = service.createCube();
      service.addToScene(cube);
      service.removeFromScene(cube);
      expect(mockScene.remove).toHaveBeenCalledWith(cube);
    });

    it('should not throw if scene not initialized', () => {
      const cube = service.createCube();
      expect(() => service.removeFromScene(cube)).not.toThrow();
    });
  });

  describe('startAnimation', () => {
    it('should start animation loop', () => {
      service.initializeScene(container);
      service.startAnimation();
      expect(global.requestAnimationFrame).toHaveBeenCalled();
    });

    it('should throw error if scene not initialized', () => {
      expect(() => service.startAnimation()).toThrow('Scene, camera, or renderer not initialized');
    });

    it('should call animation callback if provided', () => {
      service.initializeScene(container);
      const callback = jest.fn();
      service.startAnimation(callback);

      // Simulate animation frame
      if (animationCallback) {
        animationCallback(performance.now());
      }

      expect(callback).toHaveBeenCalled();
    });
  });

  describe('stopAnimation', () => {
    it('should stop animation loop', () => {
      service.initializeScene(container);
      service.startAnimation();
      service.stopAnimation();
      expect(global.cancelAnimationFrame).toHaveBeenCalled();
    });

    it('should not throw if animation not started', () => {
      expect(() => service.stopAnimation()).not.toThrow();
    });
  });

  describe('handleResize', () => {
    it('should update camera and renderer on resize', () => {
      service.initializeScene(container);
      service.handleResize(1024, 768);

      expect(mockCamera.updateProjectionMatrix).toHaveBeenCalled();
      expect(mockRenderer.setSize).toHaveBeenCalledWith(1024, 768);
    });

    it('should not throw if not initialized', () => {
      expect(() => service.handleResize(1024, 768)).not.toThrow();
    });
  });

  describe('getSceneStats', () => {
    it('should return scene statistics', () => {
      service.initializeScene(container);
      const stats = service.getSceneStats();

      expect(stats['objects']).toBeDefined();
      expect(stats['triangles']).toBe(100);
      expect(stats['geometries']).toBe(5);
      expect(stats['textures']).toBe(3);
    });

    it('should return error if scene not initialized', () => {
      const stats = service.getSceneStats();
      expect(stats['error']).toBe('Scene not initialized');
    });
  });

  describe('dispose', () => {
    it('should dispose all resources', () => {
      service.initializeScene(container);
      service.startAnimation();
      service.dispose();

      expect(mockRenderer.dispose).toHaveBeenCalled();
      expect(mockScene.clear).toHaveBeenCalled();
      expect(service.getScene()).toBeNull();
      expect(service.getCamera()).toBeNull();
      expect(service.getRenderer()).toBeNull();
    });

    it('should stop animation on dispose', () => {
      service.initializeScene(container);
      service.startAnimation();
      service.dispose();

      expect(global.cancelAnimationFrame).toHaveBeenCalled();
    });
  });

  describe('getters', () => {
    it('should return scene after initialization', () => {
      service.initializeScene(container);
      expect(service.getScene()).toBe(mockScene);
    });

    it('should return camera after initialization', () => {
      service.initializeScene(container);
      expect(service.getCamera()).toBe(mockCamera);
    });

    it('should return renderer after initialization', () => {
      service.initializeScene(container);
      expect(service.getRenderer()).toBe(mockRenderer);
    });
  });
});
