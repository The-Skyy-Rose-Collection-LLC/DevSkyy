/**
 * Three.js Configuration Module
 * =============================
 * Centralized configuration for 3D rendering, loaders, and performance settings.
 *
 * @module config/threejs
 */

import * as THREE from 'three';

// ============================================================================
// TYPES
// ============================================================================

export interface ThreeJSRendererConfig {
  /** Enable antialiasing */
  antialias: boolean;
  /** Enable alpha (transparency) */
  alpha: boolean;
  /** Power preference for GPU selection */
  powerPreference: 'high-performance' | 'low-power' | 'default';
  /** Enable stencil buffer */
  stencil: boolean;
  /** Enable depth buffer */
  depth: boolean;
  /** Preserve drawing buffer for screenshots */
  preserveDrawingBuffer: boolean;
  /** Fail silently if WebGL context cannot be created */
  failIfMajorPerformanceCaveat: boolean;
}

export interface ThreeJSShadowConfig {
  /** Enable shadow maps */
  enabled: boolean;
  /** Shadow map type */
  type: THREE.ShadowMapType;
  /** Shadow map resolution */
  mapSize: number;
  /** Auto-update shadows each frame */
  autoUpdate: boolean;
}

export interface ThreeJSCameraConfig {
  /** Field of view in degrees */
  fov: number;
  /** Near clipping plane */
  near: number;
  /** Far clipping plane */
  far: number;
  /** Default camera position */
  position: { x: number; y: number; z: number };
  /** Default look-at target */
  target: { x: number; y: number; z: number };
}

export interface ThreeJSLoaderConfig {
  /** Path to Draco decoder files */
  dracoDecoderPath: string;
  /** Enable mesh optimization */
  meshOptEnabled: boolean;
  /** Maximum concurrent model loads */
  maxConcurrentLoads: number;
  /** Model cache size limit in MB */
  cacheSizeMB: number;
  /** Timeout for model loading in ms */
  loadTimeoutMs: number;
  /** Retry attempts on load failure */
  retryAttempts: number;
  /** Retry delay in ms */
  retryDelayMs: number;
}

export interface ThreeJSPerformanceConfig {
  /** Target frames per second */
  targetFPS: number;
  /** Maximum pixel ratio */
  maxPixelRatio: number;
  /** Enable level of detail */
  enableLOD: boolean;
  /** Distance thresholds for LOD */
  lodDistances: number[];
  /** Enable frustum culling */
  frustumCulling: boolean;
  /** Enable automatic quality adjustment */
  adaptiveQuality: boolean;
  /** Memory limit in MB before cleanup */
  memoryLimitMB: number;
}

export interface ThreeJSPostProcessingConfig {
  /** Enable post-processing */
  enabled: boolean;
  /** Enable bloom effect */
  bloom: {
    enabled: boolean;
    strength: number;
    radius: number;
    threshold: number;
  };
  /** Enable ambient occlusion */
  ao: {
    enabled: boolean;
    radius: number;
    intensity: number;
  };
  /** Enable depth of field */
  dof: {
    enabled: boolean;
    focus: number;
    aperture: number;
    maxBlur: number;
  };
  /** Tone mapping */
  toneMapping: THREE.ToneMapping;
  /** Exposure value */
  exposure: number;
}

export interface ThreeJSConfig {
  renderer: ThreeJSRendererConfig;
  shadows: ThreeJSShadowConfig;
  camera: ThreeJSCameraConfig;
  loaders: ThreeJSLoaderConfig;
  performance: ThreeJSPerformanceConfig;
  postProcessing: ThreeJSPostProcessingConfig;
}

// ============================================================================
// CONFIGURATION PRESETS
// ============================================================================

/**
 * High-quality configuration for desktop/powerful devices
 */
export const HIGH_QUALITY_CONFIG: ThreeJSConfig = {
  renderer: {
    antialias: true,
    alpha: true,
    powerPreference: 'high-performance',
    stencil: true,
    depth: true,
    preserveDrawingBuffer: false,
    failIfMajorPerformanceCaveat: false,
  },
  shadows: {
    enabled: true,
    type: THREE.PCFSoftShadowMap,
    mapSize: 2048,
    autoUpdate: true,
  },
  camera: {
    fov: 60,
    near: 0.1,
    far: 1000,
    position: { x: 0, y: 2, z: 10 },
    target: { x: 0, y: 0, z: 0 },
  },
  loaders: {
    dracoDecoderPath: '/draco/',
    meshOptEnabled: true,
    maxConcurrentLoads: 4,
    cacheSizeMB: 512,
    loadTimeoutMs: 30000,
    retryAttempts: 3,
    retryDelayMs: 1000,
  },
  performance: {
    targetFPS: 60,
    maxPixelRatio: 2,
    enableLOD: true,
    lodDistances: [10, 25, 50, 100],
    frustumCulling: true,
    adaptiveQuality: true,
    memoryLimitMB: 1024,
  },
  postProcessing: {
    enabled: true,
    bloom: {
      enabled: true,
      strength: 0.5,
      radius: 0.4,
      threshold: 0.85,
    },
    ao: {
      enabled: true,
      radius: 0.5,
      intensity: 0.5,
    },
    dof: {
      enabled: false,
      focus: 10,
      aperture: 0.025,
      maxBlur: 0.01,
    },
    toneMapping: THREE.ACESFilmicToneMapping,
    exposure: 1.0,
  },
};

/**
 * Medium-quality configuration for mid-range devices
 */
export const MEDIUM_QUALITY_CONFIG: ThreeJSConfig = {
  ...HIGH_QUALITY_CONFIG,
  shadows: {
    enabled: true,
    type: THREE.PCFShadowMap,
    mapSize: 1024,
    autoUpdate: true,
  },
  performance: {
    targetFPS: 30,
    maxPixelRatio: 1.5,
    enableLOD: true,
    lodDistances: [8, 20, 40],
    frustumCulling: true,
    adaptiveQuality: true,
    memoryLimitMB: 512,
  },
  postProcessing: {
    ...HIGH_QUALITY_CONFIG.postProcessing,
    ao: { enabled: false, radius: 0, intensity: 0 },
    dof: { enabled: false, focus: 0, aperture: 0, maxBlur: 0 },
  },
};

/**
 * Low-quality configuration for mobile/low-power devices
 */
export const LOW_QUALITY_CONFIG: ThreeJSConfig = {
  renderer: {
    antialias: false,
    alpha: true,
    powerPreference: 'low-power',
    stencil: false,
    depth: true,
    preserveDrawingBuffer: false,
    failIfMajorPerformanceCaveat: true,
  },
  shadows: {
    enabled: false,
    type: THREE.BasicShadowMap,
    mapSize: 512,
    autoUpdate: false,
  },
  camera: {
    fov: 60,
    near: 0.1,
    far: 500,
    position: { x: 0, y: 2, z: 10 },
    target: { x: 0, y: 0, z: 0 },
  },
  loaders: {
    dracoDecoderPath: '/draco/',
    meshOptEnabled: false,
    maxConcurrentLoads: 2,
    cacheSizeMB: 128,
    loadTimeoutMs: 45000,
    retryAttempts: 2,
    retryDelayMs: 2000,
  },
  performance: {
    targetFPS: 30,
    maxPixelRatio: 1,
    enableLOD: true,
    lodDistances: [5, 15, 30],
    frustumCulling: true,
    adaptiveQuality: true,
    memoryLimitMB: 256,
  },
  postProcessing: {
    enabled: false,
    bloom: { enabled: false, strength: 0, radius: 0, threshold: 0 },
    ao: { enabled: false, radius: 0, intensity: 0 },
    dof: { enabled: false, focus: 0, aperture: 0, maxBlur: 0 },
    toneMapping: THREE.LinearToneMapping,
    exposure: 1.0,
  },
};

// ============================================================================
// COLLECTION-SPECIFIC CONFIGURATIONS
// ============================================================================

export const COLLECTION_CONFIGS = {
  black_rose: {
    ...HIGH_QUALITY_CONFIG,
    postProcessing: {
      ...HIGH_QUALITY_CONFIG.postProcessing,
      bloom: {
        enabled: true,
        strength: 0.8, // Gothic glow
        radius: 0.6,
        threshold: 0.7,
      },
    },
    scene: {
      background: 0x0a0a0a, // Near black
      fog: { color: 0x1a1a1a, near: 10, far: 50 },
      ambient: { color: 0x404060, intensity: 0.3 },
    },
  },
  signature: {
    ...HIGH_QUALITY_CONFIG,
    postProcessing: {
      ...HIGH_QUALITY_CONFIG.postProcessing,
      dof: {
        enabled: true,
        focus: 8,
        aperture: 0.02,
        maxBlur: 0.008,
      },
    },
    scene: {
      background: 0xf5f0e6, // Warm cream
      fog: { color: 0xfaf5eb, near: 20, far: 80 },
      ambient: { color: 0xffeedd, intensity: 0.6 },
    },
  },
  love_hurts: {
    ...HIGH_QUALITY_CONFIG,
    postProcessing: {
      ...HIGH_QUALITY_CONFIG.postProcessing,
      bloom: {
        enabled: true,
        strength: 1.0, // Magical enchanted glow
        radius: 0.8,
        threshold: 0.6,
      },
    },
    scene: {
      background: 0x1a0a20, // Deep purple
      fog: { color: 0x2a1a35, near: 5, far: 40 },
      ambient: { color: 0x604080, intensity: 0.4 },
    },
  },
  showroom: {
    ...HIGH_QUALITY_CONFIG,
    scene: {
      background: 0x1c1c1c, // Gallery dark
      fog: null,
      ambient: { color: 0xffffff, intensity: 0.2 },
    },
  },
  runway: {
    ...HIGH_QUALITY_CONFIG,
    scene: {
      background: 0x0f0f0f, // Stage black
      fog: { color: 0x0f0f0f, near: 30, far: 100 },
      ambient: { color: 0xffffff, intensity: 0.1 },
    },
  },
} as const;

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Detect device capabilities and return appropriate config
 */
export function detectDeviceConfig(): ThreeJSConfig {
  // Check for WebGL2 support
  const canvas = document.createElement('canvas');
  const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');

  if (!gl) {
    console.warn('WebGL not supported, using low quality config');
    return LOW_QUALITY_CONFIG;
  }

  // Check device memory (if available)
  const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory;

  // Check for mobile
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    navigator.userAgent
  );

  // Check hardware concurrency
  const cores = navigator.hardwareConcurrency || 2;

  if (isMobile || (memory && memory < 4) || cores < 4) {
    return LOW_QUALITY_CONFIG;
  }

  if ((memory && memory >= 8) && cores >= 8) {
    return HIGH_QUALITY_CONFIG;
  }

  return MEDIUM_QUALITY_CONFIG;
}

/**
 * Create Three.js renderer with config
 */
export function createRendererFromConfig(
  config: ThreeJSConfig,
  canvas?: HTMLCanvasElement
): THREE.WebGLRenderer {
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: config.renderer.antialias,
    alpha: config.renderer.alpha,
    powerPreference: config.renderer.powerPreference,
    stencil: config.renderer.stencil,
    depth: config.renderer.depth,
    preserveDrawingBuffer: config.renderer.preserveDrawingBuffer,
    failIfMajorPerformanceCaveat: config.renderer.failIfMajorPerformanceCaveat,
  });

  // Configure pixel ratio
  renderer.setPixelRatio(
    Math.min(window.devicePixelRatio, config.performance.maxPixelRatio)
  );

  // Configure shadows
  renderer.shadowMap.enabled = config.shadows.enabled;
  renderer.shadowMap.type = config.shadows.type;
  renderer.shadowMap.autoUpdate = config.shadows.autoUpdate;

  // Configure tone mapping
  renderer.toneMapping = config.postProcessing.toneMapping;
  renderer.toneMappingExposure = config.postProcessing.exposure;

  // Output encoding for correct colors
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  return renderer;
}

/**
 * Create camera from config
 */
export function createCameraFromConfig(
  config: ThreeJSConfig,
  aspect: number
): THREE.PerspectiveCamera {
  const camera = new THREE.PerspectiveCamera(
    config.camera.fov,
    aspect,
    config.camera.near,
    config.camera.far
  );

  camera.position.set(
    config.camera.position.x,
    config.camera.position.y,
    config.camera.position.z
  );

  camera.lookAt(
    config.camera.target.x,
    config.camera.target.y,
    config.camera.target.z
  );

  return camera;
}

// ============================================================================
// DEFAULT EXPORT
// ============================================================================

export const defaultThreeJSConfig = HIGH_QUALITY_CONFIG;

export default {
  HIGH_QUALITY: HIGH_QUALITY_CONFIG,
  MEDIUM_QUALITY: MEDIUM_QUALITY_CONFIG,
  LOW_QUALITY: LOW_QUALITY_CONFIG,
  COLLECTIONS: COLLECTION_CONFIGS,
  detectDeviceConfig,
  createRendererFromConfig,
  createCameraFromConfig,
};
