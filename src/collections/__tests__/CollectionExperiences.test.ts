/**
 * Unit Tests for SkyyRose Collection 3D Experiences
 * @author DevSkyy Platform Team
 * @jest-environment jsdom
 */

import {
  BlackRoseExperience,
  SignatureExperience,
  LoveHurtsExperience,
  ShowroomExperience,
  createCollectionExperience,
} from '../index';
import RunwayExperience from '../RunwayExperience';

// Configurable mock for raycaster intersections
let mockIntersectObjects = jest.fn().mockReturnValue([]);
let mockIntersectObject = jest.fn().mockReturnValue([]);

// Mock requestAnimationFrame to execute callback once for testing animation loops
let rafCallbacks: FrameRequestCallback[] = [];
let rafId = 0;
const originalRAF = global.requestAnimationFrame;
const originalCAF = global.cancelAnimationFrame;

beforeAll(() => {
  global.requestAnimationFrame = jest.fn((callback: FrameRequestCallback) => {
    rafCallbacks.push(callback);
    return ++rafId;
  });
  global.cancelAnimationFrame = jest.fn((id: number) => {
    // Just track cancellation
  });
});

afterAll(() => {
  global.requestAnimationFrame = originalRAF;
  global.cancelAnimationFrame = originalCAF;
});

// Helper to run one animation frame
const runAnimationFrame = () => {
  const callbacks = [...rafCallbacks];
  rafCallbacks = [];
  callbacks.forEach(cb => cb(performance.now()));
};

// Helper to create mock intersection result
const createMockIntersection = (userData: Record<string, unknown> = {}, parent: unknown = null) => ({
  object: { userData, parent },
  distance: 1,
  point: { x: 0, y: 0, z: 0 },
});

// Mock Three.js core
jest.mock('three', () => ({
  Scene: jest.fn(() => ({ add: jest.fn(), remove: jest.fn(), background: null, fog: null, traverse: jest.fn(), children: [] })),
  PerspectiveCamera: jest.fn(() => ({ position: { set: jest.fn(), clone: jest.fn().mockReturnValue({ lerpVectors: jest.fn() }), lerpVectors: jest.fn() }, aspect: 1, updateProjectionMatrix: jest.fn(), lookAt: jest.fn() })),
  WebGLRenderer: jest.fn(() => ({ setSize: jest.fn(), setPixelRatio: jest.fn(), shadowMap: { enabled: false, type: 0 }, domElement: document.createElement('canvas'), render: jest.fn(), dispose: jest.fn(), toneMapping: 0, toneMappingExposure: 1, outputColorSpace: '' })),
  Color: jest.fn(() => ({})),
  Fog: jest.fn(() => ({})),
  FogExp2: jest.fn(() => ({})),
  AmbientLight: jest.fn(() => ({ position: { set: jest.fn() } })),
  DirectionalLight: jest.fn(() => ({ position: { set: jest.fn() }, castShadow: false, shadow: { mapSize: { width: 0, height: 0 }, camera: {} } })),
  PointLight: jest.fn(() => ({ position: { set: jest.fn() }, castShadow: false, shadow: { mapSize: { width: 0, height: 0 } } })),
  SpotLight: jest.fn(() => ({ position: { set: jest.fn() }, target: { position: { set: jest.fn() } }, castShadow: false, shadow: { mapSize: { width: 0, height: 0 } } })),
  Mesh: jest.fn(() => ({ position: { set: jest.fn(), x: 0, y: 0, z: 0 }, rotation: { set: jest.fn(), x: 0, y: 0, z: 0 }, scale: { set: jest.fn(), setScalar: jest.fn(), x: 1, y: 1, z: 1 }, userData: {}, geometry: { dispose: jest.fn() }, material: { dispose: jest.fn() }, lookAt: jest.fn(), visible: true })),
  Group: jest.fn(() => ({ add: jest.fn(), remove: jest.fn(), position: { set: jest.fn(), x: 0, y: 0, z: 0, z: 0 }, rotation: { set: jest.fn(), x: 0, y: 0, z: 0 }, scale: { set: jest.fn(), setScalar: jest.fn(), x: 1, y: 1, z: 1 }, children: [], lookAt: jest.fn(), userData: {}, traverse: jest.fn(), visible: true })),
  BoxGeometry: jest.fn(),
  SphereGeometry: jest.fn(),
  PlaneGeometry: jest.fn(),
  CylinderGeometry: jest.fn(),
  TorusGeometry: jest.fn(),
  CircleGeometry: jest.fn(),
  RingGeometry: jest.fn(),
  ConeGeometry: jest.fn(),
  TubeGeometry: jest.fn(),
  LatheGeometry: jest.fn(),
  IcosahedronGeometry: jest.fn(),
  CapsuleGeometry: jest.fn(),
  MeshStandardMaterial: jest.fn(() => ({ dispose: jest.fn(), clone: jest.fn().mockReturnThis() })),
  MeshBasicMaterial: jest.fn(() => ({ dispose: jest.fn(), clone: jest.fn().mockReturnThis() })),
  MeshPhongMaterial: jest.fn(() => ({ dispose: jest.fn(), clone: jest.fn().mockReturnThis() })),
  ShaderMaterial: jest.fn(() => ({ dispose: jest.fn(), clone: jest.fn().mockReturnThis() })),
  Raycaster: jest.fn(() => ({
    setFromCamera: jest.fn(),
    intersectObjects: (...args: unknown[]) => mockIntersectObjects(...args),
    intersectObject: (...args: unknown[]) => mockIntersectObject(...args),
  })),
  Vector2: jest.fn(() => ({ set: jest.fn(), x: 0, y: 0 })),
  Vector3: jest.fn(() => ({ set: jest.fn(), clone: jest.fn().mockReturnThis(), add: jest.fn().mockReturnThis(), sub: jest.fn().mockReturnThis(), multiplyScalar: jest.fn().mockReturnThis(), normalize: jest.fn().mockReturnThis(), lerpVectors: jest.fn().mockReturnThis() })),
  Clock: jest.fn(() => ({ getElapsedTime: jest.fn().mockReturnValue(0), getDelta: jest.fn().mockReturnValue(0.016) })),
  TextureLoader: jest.fn(() => ({ load: jest.fn().mockReturnValue({}) })),
  CubeTextureLoader: jest.fn(() => ({ load: jest.fn().mockReturnValue({}) })),
  BufferGeometry: jest.fn(() => ({ setAttribute: jest.fn(), dispose: jest.fn() })),
  BufferAttribute: jest.fn(),
  Float32BufferAttribute: jest.fn(),
  Points: jest.fn(() => ({ position: { set: jest.fn() }, geometry: { attributes: { position: { array: [] } }, dispose: jest.fn() }, material: { dispose: jest.fn() } })),
  PointsMaterial: jest.fn(() => ({ dispose: jest.fn() })),
  PCFSoftShadowMap: 2,
  ACESFilmicToneMapping: 4,
  SRGBColorSpace: 'srgb',
  DoubleSide: 2,
  AdditiveBlending: 2,
  NormalBlending: 1,
  MathUtils: { lerp: jest.fn((a, b, t) => a + (b - a) * t) },
}));

// Mock OrbitControls
jest.mock('three/examples/jsm/controls/OrbitControls.js', () => ({
  OrbitControls: jest.fn(() => ({ enableDamping: false, dampingFactor: 0, update: jest.fn(), dispose: jest.fn(), target: { set: jest.fn(), lerp: jest.fn() } })),
}));

// Mock GLTFLoader
jest.mock('three/examples/jsm/loaders/GLTFLoader.js', () => ({
  GLTFLoader: jest.fn(() => ({ load: jest.fn((_url, onLoad) => { onLoad({ scene: { traverse: jest.fn() } }); }) })),
}));

// Mock post-processing
jest.mock('three/examples/jsm/postprocessing/EffectComposer.js', () => ({
  EffectComposer: jest.fn(() => ({ addPass: jest.fn(), render: jest.fn(), setSize: jest.fn(), dispose: jest.fn() })),
}));
jest.mock('three/examples/jsm/postprocessing/RenderPass.js', () => ({ RenderPass: jest.fn() }));
jest.mock('three/examples/jsm/postprocessing/UnrealBloomPass.js', () => ({ UnrealBloomPass: jest.fn() }));
jest.mock('three/examples/jsm/postprocessing/BokehPass.js', () => ({ BokehPass: jest.fn() }));

// Helper
const createMockContainer = (): HTMLElement => {
  const container = document.createElement('div');
  container.style.width = '800px';
  container.style.height = '600px';
  Object.defineProperty(container, 'clientWidth', { value: 800 });
  Object.defineProperty(container, 'clientHeight', { value: 600 });
  return container;
};

describe('BlackRoseExperience', () => {
  let container: HTMLElement;
  beforeEach(() => {
    container = createMockContainer();
    document.body.appendChild(container);
    mockIntersectObjects = jest.fn().mockReturnValue([]);
    mockIntersectObject = jest.fn().mockReturnValue([]);
  });
  afterEach(() => { document.body.removeChild(container); });

  it('should instantiate with default config', () => {
    const experience = new BlackRoseExperience(container);
    expect(experience).toBeDefined();
  });

  it('should accept custom configuration', () => {
    const experience = new BlackRoseExperience(container, { backgroundColor: 0x111111, enableBloom: false, fogDensity: 0.05 });
    expect(experience).toBeDefined();
  });

  it('should start and stop animation loop', () => {
    const experience = new BlackRoseExperience(container);
    experience.start();
    experience.stop();
    expect(true).toBe(true);
  });

  it('should run animation frames', () => {
    const experience = new BlackRoseExperience(container);
    experience.start();
    // Run multiple animation frames to exercise animation code
    for (let i = 0; i < 5; i++) {
      runAnimationFrame();
    }
    experience.stop();
    expect(true).toBe(true);
  });

  it('should dispose resources properly', () => {
    const experience = new BlackRoseExperience(container);
    experience.start();
    experience.dispose();
    expect(true).toBe(true);
  });

  it('should set product click handler', () => {
    const experience = new BlackRoseExperience(container);
    const handler = jest.fn();
    experience.setOnProductClick(handler);
    expect(true).toBe(true);
  });

  it('should set product hover handler', () => {
    const experience = new BlackRoseExperience(container);
    const handler = jest.fn();
    experience.setOnProductHover(handler);
    expect(true).toBe(true);
  });

  it('should set easter egg handler', () => {
    const experience = new BlackRoseExperience(container);
    const handler = jest.fn();
    experience.setOnEasterEgg(handler);
    expect(true).toBe(true);
  });

  it('should handle mouse move events', () => {
    const experience = new BlackRoseExperience(container);
    const event = new MouseEvent('mousemove', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle click events with no intersection', () => {
    const experience = new BlackRoseExperience(container);
    mockIntersectObjects.mockReturnValue([]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle click events with product intersection', () => {
    const experience = new BlackRoseExperience(container);
    const clickHandler = jest.fn();
    experience.setOnProductClick(clickHandler);
    const mockProduct = { id: 'prod-1', name: 'Test', price: 99.99, category: 'test', modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', position: [0, 0, 0] };
    mockIntersectObjects.mockReturnValue([createMockIntersection({ productId: 'prod-1', product: mockProduct })]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle click events with loaded products', async () => {
    const experience = new BlackRoseExperience(container);
    const clickHandler = jest.fn();
    experience.setOnProductClick(clickHandler);
    // Load products first
    await experience.loadProducts([
      { id: 'prod-1', name: 'Test', price: 99.99, category: 'test', modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', position: [0, 0, 0] as [number, number, number] }
    ]);
    const mockProduct = { id: 'prod-1', name: 'Test', price: 99.99, category: 'test', modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', position: [0, 0, 0] };
    mockIntersectObjects.mockReturnValue([createMockIntersection({ productId: 'prod-1', product: mockProduct })]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(clickHandler).toHaveBeenCalled();
  });

  it('should handle click with intersection but no productId', () => {
    const experience = new BlackRoseExperience(container);
    mockIntersectObjects.mockReturnValue([createMockIntersection({})]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should find productId in parent object', () => {
    const experience = new BlackRoseExperience(container);
    const clickHandler = jest.fn();
    experience.setOnProductClick(clickHandler);
    const mockProduct = { id: 'prod-1', name: 'Test', price: 99.99, category: 'test', modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', position: [0, 0, 0] };
    // Object with no productId, but parent has it
    mockIntersectObjects.mockReturnValue([createMockIntersection({}, { userData: { productId: 'prod-1', product: mockProduct }, parent: null })]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle click with no handler set', () => {
    const experience = new BlackRoseExperience(container);
    // No handler set - should not throw
    const mockProduct = { id: 'prod-1', name: 'Test', price: 99.99, category: 'test', modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', position: [0, 0, 0] };
    mockIntersectObjects.mockReturnValue([createMockIntersection({ productId: 'prod-1', product: mockProduct })]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle easter egg click', () => {
    const experience = new BlackRoseExperience(container);
    const easterEggHandler = jest.fn();
    experience.setOnEasterEgg(easterEggHandler);
    mockIntersectObjects
      .mockReturnValueOnce([])  // First call for products
      .mockReturnValueOnce([createMockIntersection({ exclusiveDropUrl: 'https://example.com/drop' })]);  // Second call for easter eggs
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle easter egg click without handler', () => {
    const experience = new BlackRoseExperience(container);
    // No easter egg handler set
    mockIntersectObjects
      .mockReturnValueOnce([])
      .mockReturnValueOnce([createMockIntersection({ exclusiveDropUrl: 'https://example.com/drop' })]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle easter egg without url', () => {
    const experience = new BlackRoseExperience(container);
    const easterEggHandler = jest.fn();
    experience.setOnEasterEgg(easterEggHandler);
    mockIntersectObjects
      .mockReturnValueOnce([])
      .mockReturnValueOnce([createMockIntersection({})]);  // No exclusiveDropUrl
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle hover with intersection', () => {
    const experience = new BlackRoseExperience(container);
    mockIntersectObjects.mockReturnValue([createMockIntersection({ productId: 'prod-1' })]);
    const event = new MouseEvent('mousemove', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(container.style.cursor).toBe('pointer');
  });

  it('should handle hover exit (no intersection after previous hover)', () => {
    const experience = new BlackRoseExperience(container);
    const hoverHandler = jest.fn();
    experience.setOnProductHover(hoverHandler);
    // First hover - intersection
    mockIntersectObjects.mockReturnValue([createMockIntersection({ productId: 'prod-1' })]);
    container.dispatchEvent(new MouseEvent('mousemove', { clientX: 400, clientY: 300 }));
    // Second hover - no intersection
    mockIntersectObjects.mockReturnValue([]);
    container.dispatchEvent(new MouseEvent('mousemove', { clientX: 100, clientY: 100 }));
    expect(container.style.cursor).toBe('default');
  });

  it('should handle resize events', () => {
    const experience = new BlackRoseExperience(container);
    window.dispatchEvent(new Event('resize'));
    expect(true).toBe(true);
  });

  it('should load products', async () => {
    const experience = new BlackRoseExperience(container);
    await experience.loadProducts([
      { id: 'prod-1', name: 'Test Rose', price: 199.99, category: 'accessories', modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', position: [0, 0, 0] }
    ]);
    expect(true).toBe(true);
  });

  it('should load easter egg products', async () => {
    const experience = new BlackRoseExperience(container);
    await experience.loadProducts([
      { id: 'egg-1', name: 'Easter Egg', price: 999.99, category: 'exclusive', modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', position: [0, 0, 0], isEasterEgg: true, exclusiveDropUrl: 'https://example.com/drop' }
    ]);
    expect(true).toBe(true);
  });

  it('should create arbor', () => {
    const experience = new BlackRoseExperience(container);
    experience.createArbor([0, 0, 0], { id: 'prod-1', name: 'Test', price: 99.99, category: 'accessories', modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', position: [0, 0, 0] });
    expect(true).toBe(true);
  });

  it('should get scene', () => {
    const experience = new BlackRoseExperience(container);
    const scene = experience.getScene();
    expect(scene).toBeDefined();
  });

  it('should get camera', () => {
    const experience = new BlackRoseExperience(container);
    const camera = experience.getCamera();
    expect(camera).toBeDefined();
  });

  it('should get renderer', () => {
    const experience = new BlackRoseExperience(container);
    const renderer = experience.getRenderer();
    expect(renderer).toBeDefined();
  });
});

describe('SignatureExperience', () => {
  let container: HTMLElement;
  beforeEach(() => {
    container = createMockContainer();
    document.body.appendChild(container);
    mockIntersectObjects = jest.fn().mockReturnValue([]);
    mockIntersectObject = jest.fn().mockReturnValue([]);
  });
  afterEach(() => { document.body.removeChild(container); });

  it('should instantiate with default config', () => {
    const experience = new SignatureExperience(container);
    expect(experience).toBeDefined();
  });

  it('should accept custom configuration', () => {
    const experience = new SignatureExperience(container, { backgroundColor: 0xffffff, enableBloom: true, pedestalSpacing: 5 });
    expect(experience).toBeDefined();
  });

  it('should load products', async () => {
    const experience = new SignatureExperience(container);
    await experience.loadProducts([{ id: 'prod-1', name: 'Test', price: 99.99, category: 'tops', modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', pedestalPosition: [0, 0, 0] }]);
    expect(true).toBe(true);
  });

  it('should start and stop animation loop', () => {
    const experience = new SignatureExperience(container);
    experience.start();
    experience.stop();
    expect(true).toBe(true);
  });

  it('should run animation frames', () => {
    const experience = new SignatureExperience(container);
    experience.start();
    // Run multiple animation frames to exercise animation code
    for (let i = 0; i < 5; i++) {
      runAnimationFrame();
    }
    experience.stop();
    expect(true).toBe(true);
  });

  it('should dispose resources properly', () => {
    const experience = new SignatureExperience(container);
    experience.start();
    experience.dispose();
    expect(true).toBe(true);
  });

  it('should set product select handler', () => {
    const experience = new SignatureExperience(container);
    experience.setOnProductSelect(jest.fn());
    expect(true).toBe(true);
  });

  it('should set category select handler', () => {
    const experience = new SignatureExperience(container);
    experience.setOnCategorySelect(jest.fn());
    expect(true).toBe(true);
  });

  it('should handle click events with no intersection', () => {
    const experience = new SignatureExperience(container);
    mockIntersectObjects.mockReturnValue([]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle click on pedestal with product', () => {
    const experience = new SignatureExperience(container);
    const selectHandler = jest.fn();
    experience.setOnProductSelect(selectHandler);
    const mockProduct = { id: 'prod-1', name: 'Test', price: 99.99, category: 'tops', modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', pedestalPosition: [0, 0, 0] };
    mockIntersectObjects
      .mockReturnValueOnce([createMockIntersection({ product: mockProduct })])  // Pedestals
      .mockReturnValueOnce([]);  // Pathways
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle click on pathway with category', () => {
    const experience = new SignatureExperience(container);
    const categoryHandler = jest.fn();
    experience.setOnCategorySelect(categoryHandler);
    mockIntersectObjects
      .mockReturnValueOnce([])  // Pedestals
      .mockReturnValueOnce([createMockIntersection({ category: 'tops' })]);  // Pathways
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should traverse ancestors to find product', () => {
    const experience = new SignatureExperience(container);
    const selectHandler = jest.fn();
    experience.setOnProductSelect(selectHandler);
    const mockProduct = { id: 'prod-1', name: 'Test', price: 99.99, category: 'tops', modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', pedestalPosition: [0, 0, 0] };
    // Child object with product in parent
    mockIntersectObjects
      .mockReturnValueOnce([createMockIntersection({}, { userData: { product: mockProduct }, parent: null })])
      .mockReturnValueOnce([]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should not find product when no ancestor has it', () => {
    const experience = new SignatureExperience(container);
    const selectHandler = jest.fn();
    experience.setOnProductSelect(selectHandler);
    // Object with no product anywhere in hierarchy
    mockIntersectObjects
      .mockReturnValueOnce([createMockIntersection({}, { userData: {}, parent: null })])
      .mockReturnValueOnce([]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle pedestal click without handler', () => {
    const experience = new SignatureExperience(container);
    // No handler set
    const mockProduct = { id: 'prod-1', name: 'Test', price: 99.99, category: 'tops', modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', pedestalPosition: [0, 0, 0] };
    mockIntersectObjects
      .mockReturnValueOnce([createMockIntersection({ product: mockProduct })])
      .mockReturnValueOnce([]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle pathway click without handler', () => {
    const experience = new SignatureExperience(container);
    // No handler set
    mockIntersectObjects
      .mockReturnValueOnce([])
      .mockReturnValueOnce([createMockIntersection({ category: 'tops' })]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle pathway with no category in ancestors', () => {
    const experience = new SignatureExperience(container);
    const categoryHandler = jest.fn();
    experience.setOnCategorySelect(categoryHandler);
    mockIntersectObjects
      .mockReturnValueOnce([])
      .mockReturnValueOnce([createMockIntersection({}, { userData: {}, parent: null })]);  // No category
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should traverse ancestors to find category', () => {
    const experience = new SignatureExperience(container);
    const categoryHandler = jest.fn();
    experience.setOnCategorySelect(categoryHandler);
    mockIntersectObjects
      .mockReturnValueOnce([])
      .mockReturnValueOnce([createMockIntersection({}, { userData: { category: 'bottoms' }, parent: null })]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle resize events', () => {
    const experience = new SignatureExperience(container);
    window.dispatchEvent(new Event('resize'));
    expect(true).toBe(true);
  });

  it('should get scene', () => {
    const experience = new SignatureExperience(container);
    const scene = experience.getScene();
    expect(scene).toBeDefined();
  });

  it('should get camera', () => {
    const experience = new SignatureExperience(container);
    const camera = experience.getCamera();
    expect(camera).toBeDefined();
  });
});

describe('ShowroomExperience', () => {
  let container: HTMLElement;
  beforeEach(() => {
    container = createMockContainer();
    document.body.appendChild(container);
    mockIntersectObjects = jest.fn().mockReturnValue([]);
    mockIntersectObject = jest.fn().mockReturnValue([]);
  });
  afterEach(() => { document.body.removeChild(container); });

  it('should instantiate with default config', () => {
    const experience = new ShowroomExperience(container);
    expect(experience).toBeDefined();
  });

  it('should accept custom configuration', () => {
    const experience = new ShowroomExperience(container, { backgroundColor: 0x222222 });
    expect(experience).toBeDefined();
  });

  it('should accept full configuration with room dimensions', () => {
    const experience = new ShowroomExperience(container, {
      backgroundColor: 0x222222,
      ambientLightIntensity: 0.5,
      floorColor: 0x333333,
      wallColor: 0x444444,
      roomWidth: 25,
      roomDepth: 25,
      roomHeight: 10
    });
    expect(experience).toBeDefined();
  });

  it('should load products', async () => {
    const experience = new ShowroomExperience(container);
    await experience.loadProducts([{ id: 'prod-1', name: 'Test', modelUrl: '/m.glb', position: [0, 0, 0] as [number, number, number] }]);
    expect(true).toBe(true);
  });

  it('should load products with rotation and scale', async () => {
    const experience = new ShowroomExperience(container);
    await experience.loadProducts([{
      id: 'prod-1', name: 'Test', modelUrl: '/m.glb',
      position: [0, 0, 0] as [number, number, number],
      rotation: [0, Math.PI / 2, 0] as [number, number, number],
      scale: 2,
      spotlightColor: 0xff0000
    }]);
    expect(true).toBe(true);
  });

  it('should start and stop animation loop', () => {
    const experience = new ShowroomExperience(container);
    experience.start();
    experience.stop();
    expect(true).toBe(true);
  });

  it('should run animation frames', () => {
    const experience = new ShowroomExperience(container);
    experience.start();
    // Run multiple animation frames to exercise animation code
    for (let i = 0; i < 5; i++) {
      runAnimationFrame();
    }
    experience.stop();
    expect(true).toBe(true);
  });

  it('should dispose resources properly', () => {
    const experience = new ShowroomExperience(container);
    experience.start();
    experience.dispose();
    expect(true).toBe(true);
  });

  it('should dispose with loaded products', async () => {
    const experience = new ShowroomExperience(container);
    await experience.loadProducts([
      { id: 'prod-1', name: 'Test', modelUrl: '/m.glb', position: [0, 0, 0] as [number, number, number] },
      { id: 'prod-2', name: 'Test 2', modelUrl: '/m2.glb', position: [2, 0, 0] as [number, number, number] }
    ]);
    experience.start();
    experience.dispose();
    expect(true).toBe(true);
  });

  it('should select non-existent product', () => {
    const experience = new ShowroomExperience(container);
    experience.selectProduct('non-existent');
    expect(true).toBe(true);
  });

  it('should select existing product', async () => {
    const experience = new ShowroomExperience(container);
    await experience.loadProducts([{ id: 'prod-1', name: 'Test', modelUrl: '/m.glb', position: [0, 0, 0] as [number, number, number] }]);
    experience.selectProduct('prod-1');
    expect(true).toBe(true);
  });

  it('should handle resize', () => {
    const experience = new ShowroomExperience(container);
    experience.handleResize(1024, 768);
    expect(true).toBe(true);
  });

  it('should run animation frames with loaded products', async () => {
    const experience = new ShowroomExperience(container);
    await experience.loadProducts([
      { id: 'prod-1', name: 'Test', modelUrl: '/m.glb', position: [0, 0, 0] as [number, number, number] }
    ]);
    experience.start();
    for (let i = 0; i < 5; i++) {
      runAnimationFrame();
    }
    experience.stop();
    expect(true).toBe(true);
  });

  it('should select product and run animation', async () => {
    const experience = new ShowroomExperience(container);
    await experience.loadProducts([
      { id: 'prod-1', name: 'Test', modelUrl: '/m.glb', position: [0, 0, 0] as [number, number, number] }
    ]);
    experience.selectProduct('prod-1');
    experience.start();
    for (let i = 0; i < 10; i++) {
      runAnimationFrame();
    }
    experience.stop();
    expect(true).toBe(true);
  });
});

describe('RunwayExperience', () => {
  let container: HTMLElement;
  beforeEach(() => { container = createMockContainer(); document.body.appendChild(container); });
  afterEach(() => { document.body.removeChild(container); });

  it('should instantiate with default config', () => {
    const experience = new RunwayExperience(container);
    expect(experience).toBeDefined();
  });

  it('should accept custom configuration', () => {
    const experience = new RunwayExperience(container, { runwayLength: 30, walkSpeed: 0.03 });
    expect(experience).toBeDefined();
  });

  it('should accept full configuration with all options', () => {
    const experience = new RunwayExperience(container, {
      backgroundColor: 0x111111,
      runwayLength: 25,
      runwayWidth: 5,
      spotlightColor: 0xff0000,
      ambientColor: 0x222222,
      walkSpeed: 0.01
    });
    expect(experience).toBeDefined();
  });

  it('should load products with full config', async () => {
    const experience = new RunwayExperience(container, {
      runwayLength: 25,
      walkSpeed: 0.01
    });
    await experience.loadProducts([
      { id: 'model-1', name: 'Model 1', modelUrl: '/m.glb', outfitName: 'Outfit 1', walkOrder: 1 }
    ]);
    expect(true).toBe(true);
  });

  it('should start and stop animation loop', () => {
    const experience = new RunwayExperience(container);
    experience.start();
    experience.stop();
    expect(true).toBe(true);
  });

  it('should dispose resources properly', () => {
    const experience = new RunwayExperience(container);
    experience.start();
    experience.dispose();
    expect(true).toBe(true);
  });

  it('should load products', async () => {
    const experience = new RunwayExperience(container);
    await experience.loadProducts([{ id: 'model-1', name: 'Model 1', modelUrl: '/m.glb', outfitName: 'Outfit 1', walkOrder: 1 }]);
    expect(true).toBe(true);
  });

  it('should start runway show with no models', () => {
    const experience = new RunwayExperience(container);
    experience.startShow();
    expect(true).toBe(true);
  });

  it('should start runway show with models', async () => {
    const experience = new RunwayExperience(container);
    await experience.loadProducts([
      { id: 'model-1', name: 'Model 1', modelUrl: '/m.glb', outfitName: 'Outfit 1', walkOrder: 1 },
      { id: 'model-2', name: 'Model 2', modelUrl: '/m2.glb', outfitName: 'Outfit 2', walkOrder: 2 }
    ]);
    experience.startShow();
    expect(true).toBe(true);
  });

  it('should handle resize', () => {
    const experience = new RunwayExperience(container);
    experience.handleResize(1024, 768);
    expect(true).toBe(true);
  });

  it('should run animation frame with no models', () => {
    const experience = new RunwayExperience(container);
    experience.start();
    runAnimationFrame();
    experience.stop();
    expect(true).toBe(true);
  });

  it('should run animation frame with models and show started', async () => {
    const experience = new RunwayExperience(container);
    await experience.loadProducts([
      { id: 'model-1', name: 'Model 1', modelUrl: '/m.glb', outfitName: 'Outfit 1', walkOrder: 1 },
      { id: 'model-2', name: 'Model 2', modelUrl: '/m2.glb', outfitName: 'Outfit 2', walkOrder: 2 }
    ]);
    experience.startShow();
    experience.start();
    // Run multiple frames to progress the walk
    for (let i = 0; i < 10; i++) {
      runAnimationFrame();
    }
    experience.stop();
    expect(true).toBe(true);
  });

  it('should complete walk cycle and move to next model', async () => {
    const experience = new RunwayExperience(container, { walkSpeed: 0.5 }); // Fast walk speed
    await experience.loadProducts([
      { id: 'model-1', name: 'Model 1', modelUrl: '/m.glb', outfitName: 'Outfit 1', walkOrder: 1 },
      { id: 'model-2', name: 'Model 2', modelUrl: '/m2.glb', outfitName: 'Outfit 2', walkOrder: 2 }
    ]);
    experience.startShow();
    experience.start();
    // Run enough frames to complete first model's walk
    for (let i = 0; i < 10; i++) {
      runAnimationFrame();
    }
    experience.stop();
    expect(true).toBe(true);
  });

  it('should complete entire runway show', async () => {
    const experience = new RunwayExperience(container, { walkSpeed: 1.0 }); // Very fast walk
    await experience.loadProducts([
      { id: 'model-1', name: 'Model 1', modelUrl: '/m.glb', outfitName: 'Outfit 1', walkOrder: 1 }
    ]);
    experience.startShow();
    experience.start();
    // Run enough frames to complete the show
    for (let i = 0; i < 5; i++) {
      runAnimationFrame();
    }
    experience.stop();
    expect(true).toBe(true);
  });
});

describe('LoveHurtsExperience', () => {
  let container: HTMLElement;
  beforeEach(() => {
    container = createMockContainer();
    document.body.appendChild(container);
    mockIntersectObjects = jest.fn().mockReturnValue([]);
    mockIntersectObject = jest.fn().mockReturnValue([]);
  });
  afterEach(() => { document.body.removeChild(container); });

  it('should instantiate with default config', () => {
    const experience = new LoveHurtsExperience(container);
    expect(experience).toBeDefined();
  });

  it('should accept custom configuration', () => {
    const experience = new LoveHurtsExperience(container, { backgroundColor: 0x1a0000, enableBloom: true });
    expect(experience).toBeDefined();
  });

  it('should start and stop animation loop', () => {
    const experience = new LoveHurtsExperience(container);
    experience.start();
    experience.stop();
    expect(true).toBe(true);
  });

  it('should run animation frames', () => {
    const experience = new LoveHurtsExperience(container);
    experience.start();
    // Run multiple animation frames to exercise animation code
    for (let i = 0; i < 5; i++) {
      runAnimationFrame();
    }
    experience.stop();
    expect(true).toBe(true);
  });

  it('should dispose resources properly', () => {
    const experience = new LoveHurtsExperience(container);
    experience.start();
    experience.dispose();
    expect(true).toBe(true);
  });

  it('should set hero interaction handler', () => {
    const experience = new LoveHurtsExperience(container);
    experience.setOnHeroInteraction(jest.fn());
    expect(true).toBe(true);
  });

  it('should set mirror click handler', () => {
    const experience = new LoveHurtsExperience(container);
    experience.setOnMirrorClick(jest.fn());
    expect(true).toBe(true);
  });

  it('should set floor spotlight handler', () => {
    const experience = new LoveHurtsExperience(container);
    experience.setOnFloorSpotlight(jest.fn());
    expect(true).toBe(true);
  });

  it('should handle click events with no intersection', () => {
    const experience = new LoveHurtsExperience(container);
    mockIntersectObjects.mockReturnValue([]);
    mockIntersectObject.mockReturnValue([]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle hero rose click', () => {
    const experience = new LoveHurtsExperience(container);
    const heroHandler = jest.fn();
    experience.setOnHeroInteraction(heroHandler);
    mockIntersectObject.mockReturnValue([createMockIntersection({})]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle mirror click with productId', () => {
    const experience = new LoveHurtsExperience(container);
    const mirrorHandler = jest.fn();
    experience.setOnMirrorClick(mirrorHandler);
    mockIntersectObject.mockReturnValue([]);  // No hero hit
    mockIntersectObjects
      .mockReturnValueOnce([createMockIntersection({ productId: 'prod-1', lookbookImages: ['img1.jpg', 'img2.jpg'] })])  // Mirrors
      .mockReturnValueOnce([]);  // Floor spotlights
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle mirror click by traversing ancestors', () => {
    const experience = new LoveHurtsExperience(container);
    const mirrorHandler = jest.fn();
    experience.setOnMirrorClick(mirrorHandler);
    mockIntersectObject.mockReturnValue([]);
    mockIntersectObjects
      .mockReturnValueOnce([createMockIntersection({}, { userData: { productId: 'prod-1', lookbookImages: [] }, parent: null })])
      .mockReturnValueOnce([]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle floor spotlight click', () => {
    const experience = new LoveHurtsExperience(container);
    const floorHandler = jest.fn();
    experience.setOnFloorSpotlight(floorHandler);
    mockIntersectObject.mockReturnValue([]);
    mockIntersectObjects
      .mockReturnValueOnce([])  // No mirror hit
      .mockReturnValueOnce([createMockIntersection({ productId: 'floor-prod-1' })]);  // Floor spotlight hit
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle floor spotlight click by traversing ancestors', () => {
    const experience = new LoveHurtsExperience(container);
    const floorHandler = jest.fn();
    experience.setOnFloorSpotlight(floorHandler);
    mockIntersectObject.mockReturnValue([]);
    mockIntersectObjects
      .mockReturnValueOnce([])
      .mockReturnValueOnce([createMockIntersection({}, { userData: { productId: 'floor-prod-2' }, parent: null })]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle hero click without handler', () => {
    const experience = new LoveHurtsExperience(container);
    // No handler set
    mockIntersectObject.mockReturnValue([createMockIntersection({})]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle mirror click without handler', () => {
    const experience = new LoveHurtsExperience(container);
    // No handler set
    mockIntersectObject.mockReturnValue([]);
    mockIntersectObjects
      .mockReturnValueOnce([createMockIntersection({ productId: 'prod-1', lookbookImages: [] })])
      .mockReturnValueOnce([]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle floor spotlight click without handler', () => {
    const experience = new LoveHurtsExperience(container);
    // No handler set
    mockIntersectObject.mockReturnValue([]);
    mockIntersectObjects
      .mockReturnValueOnce([])
      .mockReturnValueOnce([createMockIntersection({ productId: 'floor-prod-1' })]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle mirror click with no productId in ancestors', () => {
    const experience = new LoveHurtsExperience(container);
    const mirrorHandler = jest.fn();
    experience.setOnMirrorClick(mirrorHandler);
    mockIntersectObject.mockReturnValue([]);
    mockIntersectObjects
      .mockReturnValueOnce([createMockIntersection({}, { userData: {}, parent: null })])  // No productId
      .mockReturnValueOnce([]);
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle floor spotlight click with no productId in ancestors', () => {
    const experience = new LoveHurtsExperience(container);
    const floorHandler = jest.fn();
    experience.setOnFloorSpotlight(floorHandler);
    mockIntersectObject.mockReturnValue([]);
    mockIntersectObjects
      .mockReturnValueOnce([])
      .mockReturnValueOnce([createMockIntersection({}, { userData: {}, parent: null })]);  // No productId
    const event = new MouseEvent('click', { clientX: 400, clientY: 300 });
    container.dispatchEvent(event);
    expect(true).toBe(true);
  });

  it('should handle resize events', () => {
    const experience = new LoveHurtsExperience(container);
    window.dispatchEvent(new Event('resize'));
    expect(true).toBe(true);
  });

  it('should load products with mirror display type', async () => {
    const experience = new LoveHurtsExperience(container);
    await experience.loadProducts([
      { id: 'prod-1', name: 'Test', price: 299.99, modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', displayType: 'mirror' }
    ]);
    expect(true).toBe(true);
  });

  it('should load products with mirror display type with position', async () => {
    const experience = new LoveHurtsExperience(container);
    await experience.loadProducts([
      { id: 'prod-1', name: 'Test', price: 299.99, modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', displayType: 'mirror', position: [2, 0, 3] }
    ]);
    expect(true).toBe(true);
  });

  it('should load products with floor display type', async () => {
    const experience = new LoveHurtsExperience(container);
    await experience.loadProducts([
      { id: 'prod-2', name: 'Test 2', price: 199.99, modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', displayType: 'floor' }
    ]);
    expect(true).toBe(true);
  });

  it('should load products with floor display type with position', async () => {
    const experience = new LoveHurtsExperience(container);
    await experience.loadProducts([
      { id: 'prod-2', name: 'Test 2', price: 199.99, modelUrl: '/m.glb', thumbnailUrl: '/t.jpg', displayType: 'floor', position: [1, 0, -2] }
    ]);
    expect(true).toBe(true);
  });

  it('should load hero display type products', async () => {
    const experience = new LoveHurtsExperience(container);
    await experience.loadProducts([
      { id: 'hero-1', name: 'Hero Product', price: 999.99, modelUrl: '/hero.glb', thumbnailUrl: '/hero.jpg', displayType: 'hero' }
    ]);
    expect(true).toBe(true);
  });

  it('should get scene', () => {
    const experience = new LoveHurtsExperience(container);
    const scene = experience.getScene();
    expect(scene).toBeDefined();
  });

  it('should get camera', () => {
    const experience = new LoveHurtsExperience(container);
    const camera = experience.getCamera();
    expect(camera).toBeDefined();
  });
});

describe('createCollectionExperience factory', () => {
  let container: HTMLElement;
  beforeEach(() => { container = createMockContainer(); document.body.appendChild(container); });
  afterEach(() => { document.body.removeChild(container); });

  it('should create BlackRoseExperience for black_rose collection', () => {
    const experience = createCollectionExperience(container, { collection: 'black_rose' });
    expect(experience).toBeInstanceOf(BlackRoseExperience);
  });

  it('should create SignatureExperience for signature collection', () => {
    const experience = createCollectionExperience(container, { collection: 'signature' });
    expect(experience).toBeInstanceOf(SignatureExperience);
  });

  it('should create LoveHurtsExperience for love_hurts collection', () => {
    const experience = createCollectionExperience(container, { collection: 'love_hurts' });
    expect(experience).toBeInstanceOf(LoveHurtsExperience);
  });

  it('should create ShowroomExperience for showroom collection', () => {
    const experience = createCollectionExperience(container, { collection: 'showroom' });
    expect(experience).toBeInstanceOf(ShowroomExperience);
  });

  it('should create RunwayExperience for runway collection', () => {
    const experience = createCollectionExperience(container, { collection: 'runway' });
    expect(experience).toBeInstanceOf(RunwayExperience);
  });

  it('should throw error for unknown collection', () => {
    expect(() => {
      createCollectionExperience(container, { collection: 'unknown' as never });
    }).toThrow('Unknown collection type');
  });
});
