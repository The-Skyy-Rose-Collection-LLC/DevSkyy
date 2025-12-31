/**
 * Jest setup file for three.js mocks
 * This file explicitly mocks three.js modules for ESM compatibility
 */

const threeMock = require('./__mocks__/three.cjs');

// Mock the main three module
jest.mock('three', () => threeMock);

// Mock ModelAssetLoader with explicit implementation to avoid three.js ESM issues
jest.mock('../src/lib/ModelAssetLoader.js', () => {
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
    const scene = {
      children: [],
      position: { set: () => {}, x: 0, y: 0, z: 0 },
      scale: { set: () => {}, x: 1, y: 1, z: 1 },
      rotation: { set: () => {}, x: 0, y: 0, z: 0 },
      userData: {},
      parent: null,
      add: function(child) { this.children.push(child); },
      remove: function(child) {
        const idx = this.children.indexOf(child);
        if (idx > -1) this.children.splice(idx, 1);
      },
      traverse: function(callback) {
        callback(this);
        this.children.forEach((child) => {
          if (child.traverse) {
            child.traverse(callback);
          } else {
            callback(child);
          }
        });
      },
    };
    return scene;
  }

  class MockModelAssetLoader {
    constructor(config = {}) {
      this.config = {
        maxCacheSize: config.maxCacheSize || 100,
        enableCompression: config.enableCompression !== false,
        defaultTimeout: config.defaultTimeout || 30000,
        dracoDecoderPath: config.dracoDecoderPath || '/draco/',
      };
      this.cache = new Map();
    }

    async load(url, options = {}) {
      if (options.onProgress) {
        options.onProgress({ loaded: 50, total: 100, percent: 50 });
        options.onProgress({ loaded: 100, total: 100, percent: 100 });
      }

      const mockModel = {
        scene: createMockScene(),
        animations: [],
        url,
        vertexCount: 1000,
        triangleCount: 500,
        boundingBox: {
          min: { x: -1, y: -1, z: -1 },
          max: { x: 1, y: 1, z: 1 },
          isEmpty: () => false,
          clone: () => ({}),
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
          loadOptions.onProgress = (p) => onProgress(url, p);
        }
        const model = await this.load(url, loadOptions);
        results.set(url, model);
      }
      return results;
    }

    getCached(url) { return this.cache.get(url); }
    clearCache() { this.cache.clear(); }
    dispose() { this.cache.clear(); }
    getConfig() { return { ...this.config }; }
    getCacheSize() { return this.cache.size; }
  }

  let loaderInstance = null;

  return {
    __esModule: true,
    LoadErrorCode,
    ModelLoadError,
    ModelAssetLoader: MockModelAssetLoader,
    getModelLoader: (config) => {
      if (!loaderInstance) {
        loaderInstance = new MockModelAssetLoader(config);
      }
      return loaderInstance;
    },
    resetModelLoader: () => {
      if (loaderInstance) {
        loaderInstance.dispose();
        loaderInstance = null;
      }
    },
  };
});
