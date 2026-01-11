/**
 * Mock for ModelAssetLoader - used in Jest tests
 * This is a manual mock that Jest will automatically use
 */

'use strict';

Object.defineProperty(exports, '__esModule', { value: true });

const LoadErrorCode = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  PARSE_ERROR: 'PARSE_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
};

class ModelLoadError extends Error {
  constructor(message, code, url, cause) {
    super(message);
    this.name = 'ModelLoadError';
    this.code = code;
    this.url = url;
    if (cause) this.cause = cause;
  }
}

// Create a mock scene with proper traverse function
function createMockScene() {
  return {
    children: [],
    position: { set: function() {}, x: 0, y: 0, z: 0 },
    scale: { set: function() {}, x: 1, y: 1, z: 1 },
    rotation: { set: function() {}, x: 0, y: 0, z: 0 },
    userData: {},
    parent: null,
    add: function(child) { this.children.push(child); },
    remove: function(child) {
      const idx = this.children.indexOf(child);
      if (idx > -1) this.children.splice(idx, 1);
    },
    traverse: function(callback) {
      callback(this);
      for (const child of this.children) {
        if (child && typeof child.traverse === 'function') {
          child.traverse(callback);
        } else if (child) {
          callback(child);
        }
      }
    },
  };
}

class MockModelAssetLoader {
  constructor(config) {
    config = config || {};
    this.config = {
      maxCacheSize: config.maxCacheSize || 100,
      enableCompression: config.enableCompression !== false,
      defaultTimeout: config.defaultTimeout || 30000,
      dracoDecoderPath: config.dracoDecoderPath || '/draco/',
    };
    this.cache = new Map();
  }

  async load(url, options) {
    options = options || {};
    if (options.onProgress) {
      options.onProgress({ loaded: 50, total: 100, percent: 50 });
      options.onProgress({ loaded: 100, total: 100, percent: 100 });
    }

    const mockModel = {
      scene: createMockScene(),
      animations: [],
      url: url,
      vertexCount: 1000,
      triangleCount: 500,
      boundingBox: {
        min: { x: -1, y: -1, z: -1 },
        max: { x: 1, y: 1, z: 1 },
        isEmpty: function() { return false; },
        clone: function() { return {}; },
      },
      loadTime: 100,
    };

    this.cache.set(url, mockModel);
    return mockModel;
  }

  async loadMany(urls, onProgress) {
    const results = new Map();
    for (const url of urls) {
      const loadOptions = {};
      if (onProgress) {
        loadOptions.onProgress = function(p) { onProgress(url, p); };
      }
      const model = await this.load(url, loadOptions);
      results.set(url, model);
    }
    return results;
  }

  getCached(url) { return this.cache.get(url); }
  clearCache() { this.cache.clear(); }
  dispose() { this.cache.clear(); }
  getConfig() { return Object.assign({}, this.config); }
  getCacheSize() { return this.cache.size; }
  getStats() { return { cached: this.cache.size, loaded: this.cache.size }; }
}

let loaderInstance = null;

function getModelLoader(config) {
  if (!loaderInstance) {
    loaderInstance = new MockModelAssetLoader(config);
  }
  return loaderInstance;
}

function resetModelLoader() {
  if (loaderInstance) {
    loaderInstance.dispose();
    loaderInstance = null;
  }
}

exports.LoadErrorCode = LoadErrorCode;
exports.ModelLoadError = ModelLoadError;
exports.ModelAssetLoader = MockModelAssetLoader;
exports.getModelLoader = getModelLoader;
exports.resetModelLoader = resetModelLoader;
