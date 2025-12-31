/**
 * Mock for three/examples/jsm/postprocessing/BokehPass.js
 */

Object.defineProperty(exports, '__esModule', { value: true });

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

exports.BokehPass = BokehPass;
