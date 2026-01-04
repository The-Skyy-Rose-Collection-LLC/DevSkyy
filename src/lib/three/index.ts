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
} from '../../config/threejs.config';

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
} from '../ModelAssetLoader';

// Performance Monitoring
export {
  ThreePerformanceMonitor,
  type PerformanceMetrics,
  type PerformanceThresholds,
  type PerformanceWarning,
  type MonitorConfig,
  getPerformanceMonitor,
  resetPerformanceMonitor,
} from '../ThreePerformanceMonitor';

// Re-export Three.js for convenience
export * as THREE from 'three';

// Common Three.js addons
export { OrbitControls } from 'three/addons/controls/OrbitControls.js';
export { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
export { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
export { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
export { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
export { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
export { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
export { SSAOPass } from 'three/addons/postprocessing/SSAOPass.js';
export { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
