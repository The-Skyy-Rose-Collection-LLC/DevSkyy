/**
 * Mock for three/examples/jsm/controls/OrbitControls.js
 */

Object.defineProperty(exports, '__esModule', { value: true });

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

exports.OrbitControls = OrbitControls;
