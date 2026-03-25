/**
 * Mock for three.js - used in Jest tests
 * Provides stub implementations of commonly used THREE classes
 */

// Enable ESM interop for TypeScript imports
Object.defineProperty(exports, '__esModule', { value: true });

// Mock Vector2
class Vector2 {
  constructor(x = 0, y = 0) {
    this.x = x;
    this.y = y;
  }
  set(x, y) {
    this.x = x;
    this.y = y;
    return this;
  }
  clone() {
    return new Vector2(this.x, this.y);
  }
  copy(v) {
    this.x = v.x;
    this.y = v.y;
    return this;
  }
}

// Mock Vector3
class Vector3 {
  constructor(x = 0, y = 0, z = 0) {
    this.x = x;
    this.y = y;
    this.z = z;
  }
  set(x, y, z) {
    this.x = x;
    this.y = y;
    this.z = z;
    return this;
  }
  clone() {
    return new Vector3(this.x, this.y, this.z);
  }
  copy(v) {
    this.x = v.x;
    this.y = v.y;
    this.z = v.z;
    return this;
  }
  toArray() {
    return [this.x, this.y, this.z];
  }
  project() {
    return this;
  }
  lerpVectors(a, b, t) {
    this.x = a.x + (b.x - a.x) * t;
    this.y = a.y + (b.y - a.y) * t;
    this.z = a.z + (b.z - a.z) * t;
    return this;
  }
  multiplyScalar(s) {
    this.x *= s;
    this.y *= s;
    this.z *= s;
    return this;
  }
  lerp(v, t) {
    this.x += (v.x - this.x) * t;
    this.y += (v.y - this.y) * t;
    this.z += (v.z - this.z) * t;
    return this;
  }
}

// Mock Euler
class Euler {
  constructor(x = 0, y = 0, z = 0) {
    this.x = x;
    this.y = y;
    this.z = z;
  }
  set(x, y, z) {
    this.x = x;
    this.y = y;
    this.z = z;
    return this;
  }
}

// Mock Color
class Color {
  constructor(r = 0, g = 0, b = 0) {
    if (typeof r === 'string') {
      this.r = 0; this.g = 0; this.b = 0;
    } else if (typeof r === 'number' && g === undefined) {
      this.r = ((r >> 16) & 255) / 255;
      this.g = ((r >> 8) & 255) / 255;
      this.b = (r & 255) / 255;
    } else {
      this.r = r;
      this.g = g || 0;
      this.b = b || 0;
    }
  }
  set(value) {
    return this;
  }
  copy(c) {
    this.r = c.r; this.g = c.g; this.b = c.b;
    return this;
  }
  setHex(hex) {
    return this;
  }
  clone() {
    const c = new Color();
    c.r = this.r; c.g = this.g; c.b = this.b;
    return c;
  }
}

// Mock Box3
class Box3 {
  constructor() {
    this.min = new Vector3();
    this.max = new Vector3();
  }
  setFromObject() {
    return this;
  }
  isEmpty() {
    return false;
  }
  union() {
    return this;
  }
  clone() {
    return new Box3();
  }
  applyMatrix4() {
    return this;
  }
}

// Mock Object3D
class Object3D {
  constructor() {
    this.position = new Vector3();
    this.rotation = new Euler();
    this.scale = new Vector3(1, 1, 1);
    this.userData = {};
    this.children = [];
    this.parent = null;
    this.matrixWorld = { clone: () => ({}) };
  }
  add(child) {
    this.children.push(child);
    child.parent = this;
    return this;
  }
  remove(child) {
    const index = this.children.indexOf(child);
    if (index > -1) {
      this.children.splice(index, 1);
      child.parent = null;
    }
    return this;
  }
  traverse(callback) {
    callback(this);
    this.children.forEach((child) => {
      if (child.traverse) child.traverse(callback);
    });
  }
  lookAt() {}
  updateMatrixWorld() {}
}

// Mock Group
class Group extends Object3D {
  constructor() {
    super();
    this.isGroup = true;
  }
}

// Mock Scene
class Scene extends Object3D {
  constructor() {
    super();
    this.isScene = true;
    this.background = null;
    this.fog = null;
  }
}

// Mock BufferGeometry
class BufferGeometry {
  constructor() {
    this.attributes = {};
    this.index = null;
    this.boundingBox = null;
  }
  setAttribute(name, attribute) {
    this.attributes[name] = attribute;
    return this;
  }
  dispose() {}
  computeBoundingBox() {
    this.boundingBox = new Box3();
  }
  computeVertexNormals() {}
}

class BoxGeometry extends BufferGeometry {
  constructor(width = 1, height = 1, depth = 1) {
    super();
    this.parameters = { width, height, depth };
  }
}

class PlaneGeometry extends BufferGeometry {
  constructor(width = 1, height = 1) {
    super();
    this.parameters = { width, height };
  }
}

class SphereGeometry extends BufferGeometry {
  constructor(radius = 1) {
    super();
    this.parameters = { radius };
  }
}

class CylinderGeometry extends BufferGeometry {
  constructor(radiusTop = 1, radiusBottom = 1, height = 1) {
    super();
    this.parameters = { radiusTop, radiusBottom, height };
  }
}

// Mock Material
class Material {
  constructor() {
    this.color = new Color();
    this.opacity = 1;
    this.transparent = false;
    this.needsUpdate = false;
  }
  dispose() {}
  clone() {
    const m = new this.constructor();
    Object.assign(m, this);
    m.color = this.color.clone();
    return m;
  }
}

class MeshBasicMaterial extends Material {
  constructor(params = {}) {
    super();
    Object.assign(this, params);
  }
}

class MeshStandardMaterial extends Material {
  constructor(params = {}) {
    super();
    this.metalness = 0;
    this.roughness = 1;
    Object.assign(this, params);
  }
}

class MeshPhongMaterial extends Material {
  constructor(params = {}) {
    super();
    Object.assign(this, params);
  }
}

class PointsMaterial extends Material {
  constructor(params = {}) {
    super();
    this.size = 1;
    Object.assign(this, params);
  }
}

// Mock Mesh
class Mesh extends Object3D {
  constructor(geometry, material) {
    super();
    this.isMesh = true;
    this.geometry = geometry || new BufferGeometry();
    this.material = material || new Material();
    this.castShadow = false;
    this.receiveShadow = false;
  }
}

// Mock Points
class Points extends Object3D {
  constructor(geometry, material) {
    super();
    this.isPoints = true;
    this.geometry = geometry || new BufferGeometry();
    this.material = material || new PointsMaterial();
  }
}

// Mock Light classes
class Light extends Object3D {
  constructor(color, intensity = 1) {
    super();
    this.isLight = true;
    this.color = new Color(color);
    this.intensity = intensity;
  }
}

class AmbientLight extends Light {
  constructor(color, intensity) {
    super(color, intensity);
  }
}

class DirectionalLight extends Light {
  constructor(color, intensity) {
    super(color, intensity);
    this.target = new Object3D();
    this.castShadow = false;
    this.shadow = {
      mapSize: { width: 512, height: 512 },
      camera: { near: 0.5, far: 500 },
    };
  }
}

class PointLight extends Light {
  constructor(color, intensity, distance = 0, decay = 2) {
    super(color, intensity);
    this.distance = distance;
    this.decay = decay;
  }
}

class SpotLight extends Light {
  constructor(color, intensity, distance = 0, angle = Math.PI / 3, penumbra = 0, decay = 2) {
    super(color, intensity);
    this.distance = distance;
    this.angle = angle;
    this.penumbra = penumbra;
    this.decay = decay;
    this.target = new Object3D();
    this.castShadow = false;
  }
}

// Mock Camera
class Camera extends Object3D {
  constructor() {
    super();
    this.isCamera = true;
    this.matrixWorldInverse = {};
    this.projectionMatrix = {};
  }
  updateProjectionMatrix() {}
}

class PerspectiveCamera extends Camera {
  constructor(fov = 50, aspect = 1, near = 0.1, far = 2000) {
    super();
    this.fov = fov;
    this.aspect = aspect;
    this.near = near;
    this.far = far;
  }
}

// Mock Renderer
class WebGLRenderer {
  constructor(params = {}) {
    this.domElement = { style: {} };
    this.shadowMap = { enabled: false, type: 0 };
    this.toneMapping = 0;
    this.toneMappingExposure = 1;
    this.info = {
      render: { triangles: 0, calls: 0 },
      memory: { geometries: 0, textures: 0 },
    };
  }
  setSize() {}
  setPixelRatio() {}
  render() {}
  dispose() {}
  forceContextLoss() {}
  getContext() {
    return { getExtension: () => null };
  }
  setAnimationLoop() {}
}

// Mock Fog
class Fog {
  constructor(color, near = 1, far = 1000) {
    this.isFog = true;
    this.color = new Color(color);
    this.near = near;
    this.far = far;
  }
}

class FogExp2 {
  constructor(color, density = 0.00025) {
    this.isFogExp2 = true;
    this.color = new Color(color);
    this.density = density;
  }
}

// Mock AnimationMixer
class AnimationMixer {
  constructor(root) {
    this.root = root;
  }
  clipAction() {
    return {
      play: () => {},
      stop: () => {},
      reset: () => {},
    };
  }
  update() {}
}

class AnimationClip {
  constructor(name = '', duration = -1, tracks = []) {
    this.name = name;
    this.duration = duration;
    this.tracks = tracks;
  }
}

// Mock Raycaster
class Raycaster {
  constructor() {
    this.ray = { origin: new Vector3(), direction: new Vector3() };
  }
  setFromCamera() {}
  intersectObjects() {
    return [];
  }
}

// Mock Clock
class Clock {
  constructor(autoStart = true) {
    this.autoStart = autoStart;
    this.startTime = 0;
    this.elapsedTime = 0;
    this.running = false;
  }
  start() {
    this.running = true;
  }
  stop() {
    this.running = false;
  }
  getElapsedTime() {
    return this.elapsedTime;
  }
  getDelta() {
    return 0.016; // ~60fps
  }
}

// Mock Texture
class Texture {
  constructor() {
    this.isTexture = true;
    this.needsUpdate = false;
  }
  dispose() {}
}

class CanvasTexture extends Texture {
  constructor(canvas) {
    super();
    this.image = canvas;
  }
}

class SpriteMaterial extends Material {
  constructor(params = {}) {
    super();
    this.map = params.map || null;
    this.transparent = params.transparent || false;
  }
}

class Sprite extends Object3D {
  constructor(material) {
    super();
    this.isSprite = true;
    this.material = material || new SpriteMaterial();
  }
}

class TextureLoader {
  load(url, onLoad) {
    const texture = new Texture();
    if (onLoad) setTimeout(() => onLoad(texture), 0);
    return texture;
  }
}

// Mock BufferAttribute
class BufferAttribute {
  constructor(array, itemSize) {
    this.array = array;
    this.itemSize = itemSize;
    this.count = array ? array.length / itemSize : 0;
  }
}

class Float32BufferAttribute extends BufferAttribute {
  constructor(array, itemSize) {
    super(array, itemSize);
  }
}

// Constants
const PCFSoftShadowMap = 2;
const ACESFilmicToneMapping = 4;
const SRGBColorSpace = 'srgb';
const RepeatWrapping = 1000;

// Export each class individually for proper ESM named import compatibility
exports.Vector2 = Vector2;
exports.Vector3 = Vector3;
exports.Euler = Euler;
exports.Color = Color;
exports.Box3 = Box3;
exports.Object3D = Object3D;
exports.Group = Group;
exports.Scene = Scene;
exports.BufferGeometry = BufferGeometry;
exports.BoxGeometry = BoxGeometry;
exports.PlaneGeometry = PlaneGeometry;
exports.SphereGeometry = SphereGeometry;
exports.CylinderGeometry = CylinderGeometry;
exports.Material = Material;
exports.MeshBasicMaterial = MeshBasicMaterial;
exports.MeshStandardMaterial = MeshStandardMaterial;
exports.MeshPhongMaterial = MeshPhongMaterial;
exports.PointsMaterial = PointsMaterial;
exports.Mesh = Mesh;
exports.Points = Points;
exports.Light = Light;
exports.AmbientLight = AmbientLight;
exports.DirectionalLight = DirectionalLight;
exports.PointLight = PointLight;
exports.SpotLight = SpotLight;
exports.Camera = Camera;
exports.PerspectiveCamera = PerspectiveCamera;
exports.WebGLRenderer = WebGLRenderer;
exports.Fog = Fog;
exports.FogExp2 = FogExp2;
exports.AnimationMixer = AnimationMixer;
exports.AnimationClip = AnimationClip;
exports.Raycaster = Raycaster;
exports.Clock = Clock;
exports.Texture = Texture;
exports.TextureLoader = TextureLoader;
exports.BufferAttribute = BufferAttribute;
exports.Float32BufferAttribute = Float32BufferAttribute;
exports.PCFSoftShadowMap = PCFSoftShadowMap;
exports.ACESFilmicToneMapping = ACESFilmicToneMapping;
exports.CanvasTexture = CanvasTexture;
exports.SpriteMaterial = SpriteMaterial;
exports.Sprite = Sprite;
exports.SRGBColorSpace = SRGBColorSpace;
exports.RepeatWrapping = RepeatWrapping;
