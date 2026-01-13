/**
 * Three.js Utilities
 * ===================
 * Unified exports for all Three.js related utilities.
 *
 * @module lib/three
 */

// Configuration
export {
  type ThreeJSConfig,
  type ThreeJSRendererConfig,
  type ThreeJSShadowConfig,
  type ThreeJSCameraConfig,
  type ThreeJSLoaderConfig,
  type ThreeJSPerformanceConfig,
  type ThreeJSPostProcessingConfig,
  HIGH_QUALITY_CONFIG,
  MEDIUM_QUALITY_CONFIG,
  LOW_QUALITY_CONFIG,
  COLLECTION_CONFIGS,
  defaultThreeJSConfig,
  detectDeviceConfig,
  createRendererFromConfig,
  createCameraFromConfig,
} from '../../config/threejs.config.js';

// Model Loading
export {
  ModelAssetLoader,
  type LoadedModel,
  type ModelMetadata,
  type LoadProgress,
  type LoaderStats,
  type LoadErrorCode,
  ModelLoadError,
  getModelLoader,
  resetModelLoader,
} from '../ModelAssetLoader.js';

// Performance Monitoring
export {
  ThreePerformanceMonitor,
  type PerformanceMetrics,
  type PerformanceThresholds,
  type PerformanceWarning,
  type MonitorConfig,
  getPerformanceMonitor,
  resetPerformanceMonitor,
} from '../ThreePerformanceMonitor.js';

// Re-export Three.js for convenience
export * as THREE from 'three';

// Common Three.js addons
export { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
export { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
export { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
export { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
export { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
export { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
export { BokehPass } from 'three/examples/jsm/postprocessing/BokehPass.js';
export { SSAOPass } from 'three/examples/jsm/postprocessing/SSAOPass.js';
export { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
