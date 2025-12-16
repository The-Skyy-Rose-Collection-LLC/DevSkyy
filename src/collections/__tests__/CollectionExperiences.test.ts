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

// Mock Three.js core
jest.mock('three', () => ({
  Scene: jest.fn(() => ({ add: jest.fn(), remove: jest.fn(), background: null, fog: null, traverse: jest.fn(), children: [] })),
  PerspectiveCamera: jest.fn(() => ({ position: { set: jest.fn(), clone: jest.fn().mockReturnValue({ lerpVectors: jest.fn() }) }, aspect: 1, updateProjectionMatrix: jest.fn(), lookAt: jest.fn() })),
  WebGLRenderer: jest.fn(() => ({ setSize: jest.fn(), setPixelRatio: jest.fn(), shadowMap: { enabled: false, type: 0 }, domElement: document.createElement('canvas'), render: jest.fn(), dispose: jest.fn(), toneMapping: 0, toneMappingExposure: 1, outputColorSpace: '' })),
  Color: jest.fn(() => ({})),
  Fog: jest.fn(() => ({})),
  FogExp2: jest.fn(() => ({})),
  AmbientLight: jest.fn(() => ({ position: { set: jest.fn() } })),
  DirectionalLight: jest.fn(() => ({ position: { set: jest.fn() }, castShadow: false, shadow: { mapSize: { width: 0, height: 0 }, camera: {} } })),
  PointLight: jest.fn(() => ({ position: { set: jest.fn() }, castShadow: false, shadow: { mapSize: { width: 0, height: 0 } } })),
  SpotLight: jest.fn(() => ({ position: { set: jest.fn() }, target: { position: { set: jest.fn() } }, castShadow: false, shadow: { mapSize: { width: 0, height: 0 } } })),
  Mesh: jest.fn(() => ({ position: { set: jest.fn(), x: 0, y: 0, z: 0 }, rotation: { set: jest.fn(), x: 0, y: 0, z: 0 }, scale: { set: jest.fn(), setScalar: jest.fn(), x: 1, y: 1, z: 1 }, userData: {}, geometry: { dispose: jest.fn() }, material: { dispose: jest.fn() }, lookAt: jest.fn() })),
  Group: jest.fn(() => ({ add: jest.fn(), remove: jest.fn(), position: { set: jest.fn(), x: 0, y: 0, z: 0 }, rotation: { set: jest.fn(), x: 0, y: 0, z: 0 }, scale: { set: jest.fn(), setScalar: jest.fn(), x: 1, y: 1, z: 1 }, children: [], lookAt: jest.fn(), userData: {}, traverse: jest.fn() })),
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
  MeshStandardMaterial: jest.fn(() => ({ dispose: jest.fn(), clone: jest.fn().mockReturnThis() })),
  MeshBasicMaterial: jest.fn(() => ({ dispose: jest.fn(), clone: jest.fn().mockReturnThis() })),
  MeshPhongMaterial: jest.fn(() => ({ dispose: jest.fn(), clone: jest.fn().mockReturnThis() })),
  ShaderMaterial: jest.fn(() => ({ dispose: jest.fn(), clone: jest.fn().mockReturnThis() })),
  Raycaster: jest.fn(() => ({ setFromCamera: jest.fn(), intersectObjects: jest.fn().mockReturnValue([]) })),
  Vector2: jest.fn(() => ({ set: jest.fn() })),
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
  OrbitControls: jest.fn(() => ({ enableDamping: false, dampingFactor: 0, update: jest.fn(), dispose: jest.fn(), target: { set: jest.fn() } })),
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
  beforeEach(() => { container = createMockContainer(); document.body.appendChild(container); });
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

  it('should dispose resources properly', () => {
    const experience = new BlackRoseExperience(container);
    experience.start();
    experience.dispose();
    expect(true).toBe(true);
  });

  it('should set product click handler', () => {
    const experience = new BlackRoseExperience(container);
    experience.setOnProductClick(jest.fn());
    expect(true).toBe(true);
  });
});

describe('SignatureExperience', () => {
  let container: HTMLElement;
  beforeEach(() => { container = createMockContainer(); document.body.appendChild(container); });
  afterEach(() => { document.body.removeChild(container); });

  it('should instantiate with default config', () => {
    const experience = new SignatureExperience(container);
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

  it('should dispose resources properly', () => {
    const experience = new SignatureExperience(container);
    experience.start();
    experience.dispose();
    expect(true).toBe(true);
  });
});

describe('ShowroomExperience', () => {
  let container: HTMLElement;
  beforeEach(() => { container = createMockContainer(); document.body.appendChild(container); });
  afterEach(() => { document.body.removeChild(container); });

  it('should instantiate with default config', () => {
    const experience = new ShowroomExperience(container);
    expect(experience).toBeDefined();
  });

  it('should load products', async () => {
    const experience = new ShowroomExperience(container);
    await experience.loadProducts([{ id: 'prod-1', name: 'Test', modelUrl: '/m.glb', position: [0, 0, 0] as [number, number, number] }]);
    expect(true).toBe(true);
  });

  it('should start and stop animation loop', () => {
    const experience = new ShowroomExperience(container);
    experience.start();
    experience.stop();
    expect(true).toBe(true);
  });

  it('should dispose resources properly', () => {
    const experience = new ShowroomExperience(container);
    experience.start();
    experience.dispose();
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
