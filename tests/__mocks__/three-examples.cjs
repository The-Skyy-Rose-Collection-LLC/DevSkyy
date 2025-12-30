/**
 * Mock for three/examples/jsm/* - used in Jest tests
 * Provides stub implementations of three.js addons
 */

// Enable ESM interop for TypeScript imports
Object.defineProperty(exports, '__esModule', { value: true });

// Mock OrbitControls
class OrbitControls {
  constructor(camera, domElement) {
    this.camera = camera;
    this.domElement = domElement;
    this.enabled = true;
    this.enableDamping = false;
    this.dampingFactor = 0.05;
    this.target = { set: () => {}, x: 0, y: 0, z: 0 };
    this.minDistance = 0;
    this.maxDistance = Infinity;
    this.maxPolarAngle = Math.PI;
  }
  update() {}
  dispose() {}
  addEventListener() {}
  removeEventListener() {}
}

// Mock EffectComposer
class EffectComposer {
  constructor(renderer) {
    this.renderer = renderer;
    this.passes = [];
  }
  addPass(pass) {
    this.passes.push(pass);
  }
  render() {}
  setSize() {}
  dispose() {}
}

// Mock RenderPass
class RenderPass {
  constructor(scene, camera) {
    this.scene = scene;
    this.camera = camera;
    this.enabled = true;
  }
}

// Mock UnrealBloomPass
class UnrealBloomPass {
  constructor(resolution, strength, radius, threshold) {
    this.resolution = resolution;
    this.strength = strength;
    this.radius = radius;
    this.threshold = threshold;
    this.enabled = true;
  }
}

// Mock BokehPass
class BokehPass {
  constructor(scene, camera, params = {}) {
    this.scene = scene;
    this.camera = camera;
    this.uniforms = {
      focus: { value: params.focus || 1 },
      aperture: { value: params.aperture || 0.025 },
      maxblur: { value: params.maxblur || 0.01 },
    };
    this.enabled = true;
  }
}

// Mock OutputPass
class OutputPass {
  constructor() {
    this.enabled = true;
  }
}

// Mock GLTFLoader
class GLTFLoader {
  constructor() {
    this.dracoLoader = null;
  }
  setDRACOLoader(loader) {
    this.dracoLoader = loader;
  }
  setMeshoptDecoder() {}
  load(url, onLoad, onProgress, onError) {
    const mockGLTF = {
      scene: {
        traverse: (callback) => callback({}),
        children: [],
        position: { set: () => {} },
        scale: { set: () => {} },
      },
      animations: [],
    };
    if (onLoad) setTimeout(() => onLoad(mockGLTF), 0);
  }
  loadAsync(url, onProgress) {
    return Promise.resolve({
      scene: {
        traverse: (callback) => callback({}),
        children: [],
        position: { set: () => {} },
        scale: { set: () => {} },
      },
      animations: [],
    });
  }
}

// Mock DRACOLoader
class DRACOLoader {
  constructor() {}
  setDecoderPath() {}
  setDecoderConfig() {}
  preload() {}
  dispose() {}
}

// Mock MeshoptDecoder
const MeshoptDecoder = {
  ready: Promise.resolve(),
};

// Export each class individually for proper ESM named import compatibility
exports.OrbitControls = OrbitControls;
exports.EffectComposer = EffectComposer;
exports.RenderPass = RenderPass;
exports.UnrealBloomPass = UnrealBloomPass;
exports.BokehPass = BokehPass;
exports.OutputPass = OutputPass;
exports.GLTFLoader = GLTFLoader;
exports.DRACOLoader = DRACOLoader;
exports.MeshoptDecoder = MeshoptDecoder;
