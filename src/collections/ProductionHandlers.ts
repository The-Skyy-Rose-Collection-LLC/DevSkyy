/**
 * Production Handlers Mixin
 * =========================
 * Shared production-grade functionality for all collection experiences.
 *
 * Usage:
 * 1. Import the handlers
 * 2. Call setupProductionHandlers in your constructor
 * 3. Call the update/dispose handlers in your lifecycle methods
 *
 * @module collections/ProductionHandlers
 */

import * as THREE from 'three';
import type { LoadedModel, LoadProgress, ModelAssetLoader } from '../lib/ModelAssetLoader.js';
import { ModelLoadError } from '../lib/ModelAssetLoader.js';
import type { ThreePerformanceMonitor, PerformanceWarning } from '../lib/ThreePerformanceMonitor.js';
import { Logger } from '../utils/Logger.js';

// ============================================================================
// TYPES
// ============================================================================

export interface ProductionConfig {
  /** Show performance overlay */
  showPerformanceOverlay?: boolean;
  /** Enable adaptive quality */
  adaptiveQuality?: boolean;
  /** Callback on context lost */
  onContextLost?: () => void;
  /** Callback on context restored */
  onContextRestored?: () => void;
  /** Callback on performance warning */
  onPerformanceWarning?: (warning: PerformanceWarning) => void;
  /** Callback on model load progress */
  onLoadProgress?: (productId: string, progress: LoadProgress) => void;
  /** Callback on model load error */
  onLoadError?: (productId: string, error: ModelLoadError) => void;
}

export interface ProductionState {
  isContextLost: boolean;
  qualityLevel: 'high' | 'medium' | 'low';
  frameCount: number;
  lastQualityCheck: number;
}

// ============================================================================
// PRODUCTION HANDLERS
// ============================================================================

/**
 * Setup WebGL context loss/restore handlers
 */
export function setupContextHandlers(
  renderer: THREE.WebGLRenderer,
  logger: Logger,
  state: ProductionState,
  onStop: () => void,
  onStart: () => void,
  config?: ProductionConfig
): void {
  renderer.domElement.addEventListener('webglcontextlost', (event) => {
    event.preventDefault();
    state.isContextLost = true;
    logger.warn('WebGL context lost - stopping render loop');
    onStop();
    config?.onContextLost?.();
  });

  renderer.domElement.addEventListener('webglcontextrestored', () => {
    state.isContextLost = false;
    logger.info('WebGL context restored - resuming render loop');
    onStart();
    config?.onContextRestored?.();
  });
}

/**
 * Setup visibility change handler (pause on tab switch)
 */
export function setupVisibilityHandler(
  logger: Logger,
  onStop: () => void,
  onStart: () => void
): void {
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      logger.debug('Tab hidden - pausing render');
      onStop();
    } else {
      logger.debug('Tab visible - resuming render');
      onStart();
    }
  });
}

/**
 * Load a 3D model with production error handling
 */
export async function loadModelProduction(
  modelLoader: ModelAssetLoader,
  productId: string,
  modelUrl: string,
  productName: string,
  logger: Logger,
  loadedModels: Map<string, LoadedModel>,
  config?: ProductionConfig
): Promise<THREE.Object3D | null> {
  try {
    const loadedModel = await modelLoader.load(modelUrl, {
      name: productName,
      onProgress: (progress) => {
        config?.onLoadProgress?.(productId, progress);
        logger.debug(`Loading ${productName}: ${progress.percent}%`);
      },
    });

    loadedModels.set(productId, loadedModel);
    logger.info(`Loaded model: ${productName}`, {
      triangles: loadedModel.metadata.triangleCount,
      meshes: loadedModel.metadata.meshCount,
      hasAnimations: loadedModel.metadata.hasAnimations,
    });

    return loadedModel.scene;
  } catch (error) {
    const loadError = error instanceof ModelLoadError
      ? error
      : new ModelLoadError('Unknown error', 'UNKNOWN', modelUrl, error instanceof Error ? error : undefined);

    logger.warn(`Failed to load model: ${productName}`, {
      code: loadError.code,
      url: loadError.url,
    });

    config?.onLoadError?.(productId, loadError);
    return null;
  }
}

/**
 * Check and adjust quality based on performance
 */
export function checkAdaptiveQuality(
  perfMonitor: ThreePerformanceMonitor,
  renderer: THREE.WebGLRenderer,
  state: ProductionState,
  logger: Logger,
  config?: ProductionConfig
): void {
  if (!config?.adaptiveQuality) return;

  const now = performance.now();
  if (now - state.lastQualityCheck < 5000) return; // Check every 5 seconds
  state.lastQualityCheck = now;

  const metrics = perfMonitor.getMetrics();
  const score = perfMonitor.getPerformanceScore();

  // Upgrade if performing well
  if (score > 90 && metrics.fps > 55) {
    if (state.qualityLevel === 'low') {
      setQualityLevel('medium', renderer, state, logger);
    } else if (state.qualityLevel === 'medium') {
      setQualityLevel('high', renderer, state, logger);
    }
  }
  // Downgrade if struggling
  else if (score < 50 || metrics.fps < 25) {
    if (state.qualityLevel === 'high') {
      setQualityLevel('medium', renderer, state, logger);
    } else if (state.qualityLevel === 'medium') {
      setQualityLevel('low', renderer, state, logger);
    }
  }
}

/**
 * Set quality level
 */
export function setQualityLevel(
  level: 'high' | 'medium' | 'low',
  renderer: THREE.WebGLRenderer,
  state: ProductionState,
  logger: Logger
): void {
  if (state.qualityLevel === level) return;

  state.qualityLevel = level;

  switch (level) {
    case 'high':
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      break;
    case 'medium':
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFShadowMap;
      break;
    case 'low':
      renderer.setPixelRatio(1);
      renderer.shadowMap.enabled = false;
      break;
  }

  logger.info(`Quality level changed to: ${level}`);
}

/**
 * Handle performance warning
 */
export function handlePerformanceWarning(
  warning: PerformanceWarning,
  renderer: THREE.WebGLRenderer,
  state: ProductionState,
  logger: Logger,
  config?: ProductionConfig
): void {
  logger.warn('Performance warning', {
    type: warning.type,
    severity: warning.severity,
    value: warning.value,
    threshold: warning.threshold,
  });

  config?.onPerformanceWarning?.(warning);

  // Auto-downgrade on critical warnings
  if (warning.severity === 'critical' && config?.adaptiveQuality) {
    if (state.qualityLevel === 'high') {
      setQualityLevel('medium', renderer, state, logger);
    } else if (state.qualityLevel === 'medium') {
      setQualityLevel('low', renderer, state, logger);
    }
  }
}

/**
 * Dispose of all loaded models
 */
export function disposeLoadedModels(
  loadedModels: Map<string, LoadedModel>,
  scene: THREE.Scene
): void {
  loadedModels.forEach((model) => {
    scene.remove(model.scene);
    model.scene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.geometry?.dispose();
        const materials = Array.isArray(child.material) ? child.material : [child.material];
        materials.forEach((mat) => {
          for (const key in mat) {
            const value = (mat as Record<string, unknown>)[key];
            if (value instanceof THREE.Texture) {
              value.dispose();
            }
          }
          mat.dispose();
        });
      }
    });
  });
  loadedModels.clear();
}

/**
 * Create default placeholder mesh
 */
export function createDefaultPlaceholder(color = 0xd4af37): THREE.Mesh {
  const geometry = new THREE.BoxGeometry(1, 1.5, 0.5);
  const material = new THREE.MeshStandardMaterial({
    color,
    roughness: 0.3,
    metalness: 0.8,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  return mesh;
}

/**
 * Enable shadows on all meshes in an object
 */
export function enableShadows(object: THREE.Object3D): void {
  object.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.castShadow = true;
      child.receiveShadow = true;
    }
  });
}

// ============================================================================
// EXPORT PRODUCTION STATE FACTORY
// ============================================================================

export function createProductionState(): ProductionState {
  return {
    isContextLost: false,
    qualityLevel: 'high',
    frameCount: 0,
    lastQualityCheck: 0,
  };
}
