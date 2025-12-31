/**
 * Mock for three/examples/jsm/postprocessing/EffectComposer.js
 */

Object.defineProperty(exports, '__esModule', { value: true });

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

exports.EffectComposer = EffectComposer;
