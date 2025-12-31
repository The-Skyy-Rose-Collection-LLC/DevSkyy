/**
 * Mock for three.js - used in Jest tests
 */

Object.defineProperty(exports, '__esModule', { value: true });

class Vector3 {
  constructor(x = 0, y = 0, z = 0) {
    this.x = x; this.y = y; this.z = z;
  }
  set(x, y, z) { this.x = x; this.y = y; this.z = z; return this; }
  clone() { return new Vector3(this.x, this.y, this.z); }
  copy(v) { this.x = v.x; this.y = v.y; this.z = v.z; return this; }
}

class Euler {
  constructor(x = 0, y = 0, z = 0) { this.x = x; this.y = y; this.z = z; }
  set(x, y, z) { this.x = x; this.y = y; this.z = z; return this; }
}

class Color {
  constructor(r = 0, g = 0, b = 0) {
    if (typeof r === 'number' && g === undefined) {
      this.r = ((r >> 16) & 255) / 255;
      this.g = ((r >> 8) & 255) / 255;
      this.b = (r & 255) / 255;
    } else {
      this.r = r; this.g = g || 0; this.b = b || 0;
    }
  }
  set(value) { return this; }
}

class Box3 {
  constructor() { this.min = new Vector3(); this.max = new Vector3(); }
  setFromObject() { return this; }
  isEmpty() { return false; }
  union() { return this; }
  clone() { return new Box3(); }
  applyMatrix4() { return this; }
}

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
  add(child) { this.children.push(child); child.parent = this; return this; }
  remove(child) {
    const index = this.children.indexOf(child);
    if (index > -1) { this.children.splice(index, 1); child.parent = null; }
    return this;
  }
  traverse(callback) {
    callback(this);
    this.children.forEach((child) => { if (child.traverse) child.traverse(callback); });
  }
  lookAt() {}
  updateMatrixWorld() {}
}

class Group extends Object3D { constructor() { super(); this.isGroup = true; } }
class Scene extends Object3D { constructor() { super(); this.isScene = true; this.background = null; this.fog = null; } }

class BufferGeometry {
  constructor() { this.attributes = {}; this.index = null; this.boundingBox = null; }
  setAttribute(name, attribute) { this.attributes[name] = attribute; return this; }
  dispose() {}
  computeBoundingBox() { this.boundingBox = new Box3(); }
  computeVertexNormals() {}
}

class BoxGeometry extends BufferGeometry { constructor(w = 1, h = 1, d = 1) { super(); this.parameters = { width: w, height: h, depth: d }; } }
class PlaneGeometry extends BufferGeometry { constructor(w = 1, h = 1) { super(); this.parameters = { width: w, height: h }; } }
class SphereGeometry extends BufferGeometry { constructor(r = 1) { super(); this.parameters = { radius: r }; } }
class CylinderGeometry extends BufferGeometry { constructor(rt = 1, rb = 1, h = 1) { super(); this.parameters = { radiusTop: rt, radiusBottom: rb, height: h }; } }

class Material { constructor() { this.color = new Color(); this.opacity = 1; this.transparent = false; } dispose() {} }
class MeshBasicMaterial extends Material { constructor(params = {}) { super(); Object.assign(this, params); } }
class MeshStandardMaterial extends Material { constructor(params = {}) { super(); this.metalness = 0; this.roughness = 1; Object.assign(this, params); } }
class MeshPhongMaterial extends Material { constructor(params = {}) { super(); Object.assign(this, params); } }
class PointsMaterial extends Material { constructor(params = {}) { super(); this.size = 1; Object.assign(this, params); } }

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

class Points extends Object3D {
  constructor(geometry, material) {
    super();
    this.isPoints = true;
    this.geometry = geometry || new BufferGeometry();
    this.material = material || new PointsMaterial();
  }
}

class Light extends Object3D {
  constructor(color, intensity = 1) { super(); this.isLight = true; this.color = new Color(color); this.intensity = intensity; }
}
class AmbientLight extends Light { constructor(color, intensity) { super(color, intensity); } }
class DirectionalLight extends Light {
  constructor(color, intensity) {
    super(color, intensity);
    this.target = new Object3D();
    this.castShadow = false;
    this.shadow = { mapSize: { width: 512, height: 512 }, camera: { near: 0.5, far: 500 } };
  }
}
class PointLight extends Light { constructor(color, intensity, distance = 0, decay = 2) { super(color, intensity); this.distance = distance; this.decay = decay; } }
class SpotLight extends Light {
  constructor(color, intensity, distance = 0, angle = Math.PI / 3, penumbra = 0, decay = 2) {
    super(color, intensity);
    this.distance = distance; this.angle = angle; this.penumbra = penumbra; this.decay = decay;
    this.target = new Object3D(); this.castShadow = false;
  }
}

class Camera extends Object3D {
  constructor() { super(); this.isCamera = true; this.matrixWorldInverse = {}; this.projectionMatrix = {}; }
  updateProjectionMatrix() {}
}
class PerspectiveCamera extends Camera {
  constructor(fov = 50, aspect = 1, near = 0.1, far = 2000) {
    super();
    this.fov = fov; this.aspect = aspect; this.near = near; this.far = far;
  }
}

class WebGLRenderer {
  constructor(params = {}) {
    this.domElement = { style: {} };
    this.shadowMap = { enabled: false, type: 0 };
    this.toneMapping = 0;
    this.toneMappingExposure = 1;
    this.info = { render: { triangles: 0, calls: 0 }, memory: { geometries: 0, textures: 0 } };
  }
  setSize() {}
  setPixelRatio() {}
  render() {}
  dispose() {}
  forceContextLoss() {}
  getContext() { return { getExtension: () => null }; }
  setAnimationLoop() {}
}

class Fog { constructor(color, near = 1, far = 1000) { this.isFog = true; this.color = new Color(color); this.near = near; this.far = far; } }
class FogExp2 { constructor(color, density = 0.00025) { this.isFogExp2 = true; this.color = new Color(color); this.density = density; } }

class AnimationMixer {
  constructor(root) { this.root = root; }
  clipAction() { return { play: () => {}, stop: () => {}, reset: () => {} }; }
  update() {}
}
class AnimationClip { constructor(name = '', duration = -1, tracks = []) { this.name = name; this.duration = duration; this.tracks = tracks; } }

class Raycaster {
  constructor() { this.ray = { origin: new Vector3(), direction: new Vector3() }; }
  setFromCamera() {}
  intersectObjects() { return []; }
}

class Clock {
  constructor(autoStart = true) { this.autoStart = autoStart; this.startTime = 0; this.elapsedTime = 0; this.running = false; }
  start() { this.running = true; }
  stop() { this.running = false; }
  getElapsedTime() { return this.elapsedTime; }
  getDelta() { return 0.016; }
}

class Texture { constructor() { this.isTexture = true; } dispose() {} }
class TextureLoader {
  load(url, onLoad) { const texture = new Texture(); if (onLoad) setTimeout(() => onLoad(texture), 0); return texture; }
}

class BufferAttribute { constructor(array, itemSize) { this.array = array; this.itemSize = itemSize; this.count = array ? array.length / itemSize : 0; } }
class Float32BufferAttribute extends BufferAttribute { constructor(array, itemSize) { super(array, itemSize); } }

const PCFSoftShadowMap = 2;
const ACESFilmicToneMapping = 4;

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
