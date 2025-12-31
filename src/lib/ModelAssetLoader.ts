/**
 * Model Asset Loader
 * ===================
 * Centralized 3D model loading with Draco compression, caching, and error handling.
 *
 * @module lib/ModelAssetLoader
 */

import * as THREE from 'three';
import { GLTFLoader, type GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import type { ThreeJSLoaderConfig } from '../config/threejs.config.js';

// ============================================================================
// TYPES
// ============================================================================

export interface LoadedModel {
  /** Unique identifier for cache */
  id: string;
  /** The loaded GLTF scene */
  scene: THREE.Group;
  /** All animations in the model */
  animations: THREE.AnimationClip[];
  /** Original GLTF data */
  gltf: GLTF;
  /** Model metadata */
  metadata: ModelMetadata;
  /** Timestamp when loaded */
  loadedAt: number;
  /** Size in bytes (estimated) */
  sizeBytes: number;
}

export interface ModelMetadata {
  /** Model name */
  name: string;
  /** Source URL */
  url: string;
  /** Bounding box dimensions */
  boundingBox: THREE.Box3;
  /** Total vertex count */
  vertexCount: number;
  /** Total triangle count */
  triangleCount: number;
  /** Number of materials */
  materialCount: number;
  /** Number of meshes */
  meshCount: number;
  /** Has animations */
  hasAnimations: boolean;
  /** Animation names */
  animationNames: string[];
}

export interface LoadProgress {
  /** Model URL being loaded */
  url: string;
  /** Bytes loaded */
  loaded: number;
  /** Total bytes */
  total: number;
  /** Progress percentage (0-100) */
  percent: number;
}

export interface LoaderStats {
  /** Total models in cache */
  cachedModels: number;
  /** Total cache size in MB */
  cacheSizeMB: number;
  /** Models currently loading */
  activeLoads: number;
  /** Total models loaded this session */
  totalLoaded: number;
  /** Total load failures this session */
  totalFailed: number;
  /** Average load time in ms */
  avgLoadTimeMs: number;
}

export type LoadErrorCode =
  | 'NETWORK_ERROR'
  | 'TIMEOUT'
  | 'DECODE_ERROR'
  | 'NOT_FOUND'
  | 'INVALID_FORMAT'
  | 'UNKNOWN';

export class ModelLoadError extends Error {
  public readonly code: LoadErrorCode;
  public readonly url: string;

  constructor(
    message: string,
    code: LoadErrorCode,
    url: string,
    cause?: Error
  ) {
    super(message, cause ? { cause } : undefined);
    this.name = 'ModelLoadError';
    this.code = code;
    this.url = url;
  }
}

// ============================================================================
// MODEL ASSET LOADER
// ============================================================================

export class ModelAssetLoader {
  private gltfLoader: GLTFLoader;
  private dracoLoader: DRACOLoader;
  private cache: Map<string, LoadedModel> = new Map();
  private loadingPromises: Map<string, Promise<LoadedModel>> = new Map();
  private config: ThreeJSLoaderConfig;

  // Stats tracking
  private stats = {
    totalLoaded: 0,
    totalFailed: 0,
    loadTimes: [] as number[],
  };

  constructor(config: Partial<ThreeJSLoaderConfig> = {}) {
    // Default configuration
    this.config = {
      dracoDecoderPath: '/draco/',
      meshOptEnabled: true,
      maxConcurrentLoads: 4,
      cacheSizeMB: 512,
      loadTimeoutMs: 30000,
      retryAttempts: 3,
      retryDelayMs: 1000,
      ...config,
    };

    // Initialize Draco decoder
    this.dracoLoader = new DRACOLoader();
    this.dracoLoader.setDecoderPath(this.config.dracoDecoderPath);
    this.dracoLoader.setDecoderConfig({ type: 'js' }); // Use JS decoder (no WASM required)
    this.dracoLoader.preload();

    // Initialize GLTF loader with Draco
    this.gltfLoader = new GLTFLoader();
    this.gltfLoader.setDRACOLoader(this.dracoLoader);

    // Enable MeshOpt if configured
    if (this.config.meshOptEnabled) {
      this.gltfLoader.setMeshoptDecoder(MeshoptDecoder);
    }
  }

  // ============================================================================
  // PUBLIC METHODS
  // ============================================================================

  /**
   * Load a 3D model from URL
   *
   * @param url - URL of the GLB/GLTF file
   * @param options - Loading options
   * @returns Promise resolving to loaded model
   */
  async load(
    url: string,
    options: {
      name?: string;
      useCache?: boolean;
      onProgress?: (progress: LoadProgress) => void;
    } = {}
  ): Promise<LoadedModel> {
    const { name, useCache = true, onProgress } = options;
    const cacheKey = this.getCacheKey(url);

    // Return cached model if available
    if (useCache && this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey)!;
      // Clone the scene to avoid sharing issues
      return {
        ...cached,
        scene: cached.scene.clone(),
      };
    }

    // Return existing loading promise if already loading
    if (this.loadingPromises.has(cacheKey)) {
      return this.loadingPromises.get(cacheKey)!;
    }

    // Create loading promise
    const loadPromise = this.loadWithRetry(url, name, onProgress);
    this.loadingPromises.set(cacheKey, loadPromise);

    try {
      const model = await loadPromise;

      if (useCache) {
        this.addToCache(cacheKey, model);
      }

      return model;
    } finally {
      this.loadingPromises.delete(cacheKey);
    }
  }

  /**
   * Load multiple models in parallel
   */
  async loadMany(
    urls: string[],
    options: {
      onProgress?: (url: string, progress: LoadProgress) => void;
      onModelLoaded?: (url: string, model: LoadedModel) => void;
      onError?: (url: string, error: ModelLoadError) => void;
    } = {}
  ): Promise<Map<string, LoadedModel | ModelLoadError>> {
    const results = new Map<string, LoadedModel | ModelLoadError>();
    const { onProgress, onModelLoaded, onError } = options;

    // Limit concurrent loads
    const chunks = this.chunkArray(urls, this.config.maxConcurrentLoads);

    for (const chunk of chunks) {
      const promises = chunk.map(async (url) => {
        try {
          const loadOptions: { onProgress?: (progress: LoadProgress) => void } = {};
          if (onProgress) {
            loadOptions.onProgress = (p) => onProgress(url, p);
          }
          const model = await this.load(url, loadOptions);
          results.set(url, model);
          onModelLoaded?.(url, model);
        } catch (error) {
          const loadError = error instanceof ModelLoadError
            ? error
            : new ModelLoadError(
                `Failed to load model: ${url}`,
                'UNKNOWN',
                url,
                error instanceof Error ? error : undefined
              );
          results.set(url, loadError);
          onError?.(url, loadError);
        }
      });

      await Promise.all(promises);
    }

    return results;
  }

  /**
   * Preload models without returning them
   */
  async preload(urls: string[]): Promise<void> {
    await this.loadMany(urls);
  }

  /**
   * Get model from cache
   */
  getCached(url: string): LoadedModel | undefined {
    const cacheKey = this.getCacheKey(url);
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return {
        ...cached,
        scene: cached.scene.clone(),
      };
    }
    return undefined;
  }

  /**
   * Check if model is cached
   */
  isCached(url: string): boolean {
    return this.cache.has(this.getCacheKey(url));
  }

  /**
   * Clear specific model from cache
   */
  clearFromCache(url: string): boolean {
    const cacheKey = this.getCacheKey(url);
    const model = this.cache.get(cacheKey);
    if (model) {
      this.disposeModel(model);
      return this.cache.delete(cacheKey);
    }
    return false;
  }

  /**
   * Clear entire cache
   */
  clearCache(): void {
    for (const model of this.cache.values()) {
      this.disposeModel(model);
    }
    this.cache.clear();
  }

  /**
   * Get loader statistics
   */
  getStats(): LoaderStats {
    let cacheSizeMB = 0;
    for (const model of this.cache.values()) {
      cacheSizeMB += model.sizeBytes / (1024 * 1024);
    }

    const avgLoadTimeMs = this.stats.loadTimes.length > 0
      ? this.stats.loadTimes.reduce((a, b) => a + b, 0) / this.stats.loadTimes.length
      : 0;

    return {
      cachedModels: this.cache.size,
      cacheSizeMB: Math.round(cacheSizeMB * 100) / 100,
      activeLoads: this.loadingPromises.size,
      totalLoaded: this.stats.totalLoaded,
      totalFailed: this.stats.totalFailed,
      avgLoadTimeMs: Math.round(avgLoadTimeMs),
    };
  }

  /**
   * Dispose of loader and free resources
   */
  dispose(): void {
    this.clearCache();
    this.dracoLoader.dispose();
  }

  // ============================================================================
  // PRIVATE METHODS
  // ============================================================================

  private async loadWithRetry(
    url: string,
    name?: string,
    onProgress?: (progress: LoadProgress) => void
  ): Promise<LoadedModel> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt < this.config.retryAttempts; attempt++) {
      try {
        const model = await this.loadSingle(url, name, onProgress);
        this.stats.totalLoaded++;
        return model;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));

        // Don't retry on 404
        if (lastError.message.includes('404')) {
          break;
        }

        // Wait before retry
        if (attempt < this.config.retryAttempts - 1) {
          await this.delay(this.config.retryDelayMs * (attempt + 1));
        }
      }
    }

    this.stats.totalFailed++;
    throw new ModelLoadError(
      `Failed to load model after ${this.config.retryAttempts} attempts: ${url}`,
      this.categorizeError(lastError),
      url,
      lastError
    );
  }

  private loadSingle(
    url: string,
    name?: string,
    onProgress?: (progress: LoadProgress) => void
  ): Promise<LoadedModel> {
    return new Promise((resolve, reject) => {
      const startTime = performance.now();

      // Create timeout
      const timeoutId = setTimeout(() => {
        reject(new ModelLoadError(
          `Model load timed out after ${this.config.loadTimeoutMs}ms`,
          'TIMEOUT',
          url
        ));
      }, this.config.loadTimeoutMs);

      this.gltfLoader.load(
        url,
        // Success
        (gltf) => {
          clearTimeout(timeoutId);
          const loadTime = performance.now() - startTime;
          this.stats.loadTimes.push(loadTime);

          // Keep last 100 load times for averaging
          if (this.stats.loadTimes.length > 100) {
            this.stats.loadTimes.shift();
          }

          const metadata = this.extractMetadata(gltf, url, name);
          const sizeBytes = this.estimateSize(gltf.scene);

          resolve({
            id: this.getCacheKey(url),
            scene: gltf.scene,
            animations: gltf.animations,
            gltf,
            metadata,
            loadedAt: Date.now(),
            sizeBytes,
          });
        },
        // Progress
        (event) => {
          if (onProgress && event.lengthComputable) {
            onProgress({
              url,
              loaded: event.loaded,
              total: event.total,
              percent: Math.round((event.loaded / event.total) * 100),
            });
          }
        },
        // Error
        (error) => {
          clearTimeout(timeoutId);
          reject(error);
        }
      );
    });
  }

  private extractMetadata(gltf: GLTF, url: string, name?: string): ModelMetadata {
    let vertexCount = 0;
    let triangleCount = 0;
    let materialCount = 0;
    let meshCount = 0;
    const materials = new Set<THREE.Material>();
    const boundingBox = new THREE.Box3();

    gltf.scene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        meshCount++;
        const geometry = child.geometry as THREE.BufferGeometry;

        const positionAttr = geometry.attributes['position'];
        if (positionAttr) {
          vertexCount += positionAttr.count;
        }

        if (geometry.index) {
          triangleCount += geometry.index.count / 3;
        } else if (positionAttr) {
          triangleCount += positionAttr.count / 3;
        }

        const meshMaterials = Array.isArray(child.material)
          ? child.material
          : [child.material];
        meshMaterials.forEach((m) => materials.add(m));

        // Expand bounding box
        if (geometry.boundingBox === null) {
          geometry.computeBoundingBox();
        }
        if (geometry.boundingBox) {
          const worldBox = geometry.boundingBox.clone();
          worldBox.applyMatrix4(child.matrixWorld);
          boundingBox.union(worldBox);
        }
      }
    });

    materialCount = materials.size;

    // Compute scene bounding box if needed
    if (boundingBox.isEmpty()) {
      boundingBox.setFromObject(gltf.scene);
    }

    return {
      name: name || this.extractNameFromUrl(url),
      url,
      boundingBox,
      vertexCount,
      triangleCount: Math.round(triangleCount),
      materialCount,
      meshCount,
      hasAnimations: gltf.animations.length > 0,
      animationNames: gltf.animations.map((a) => a.name),
    };
  }

  private estimateSize(object: THREE.Object3D): number {
    let size = 0;

    object.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        const geometry = child.geometry as THREE.BufferGeometry;

        for (const key in geometry.attributes) {
          const attribute = geometry.attributes[key];
          if (attribute) {
            size += attribute.array.byteLength;
          }
        }

        if (geometry.index) {
          size += geometry.index.array.byteLength;
        }
      }
    });

    return size;
  }

  private addToCache(key: string, model: LoadedModel): void {
    // Check if we need to evict old entries
    this.evictIfNeeded(model.sizeBytes);
    this.cache.set(key, model);
  }

  private evictIfNeeded(incomingBytes: number): void {
    const limitBytes = this.config.cacheSizeMB * 1024 * 1024;

    // Skip caching if single model exceeds cache limit to prevent infinite loop
    if (incomingBytes > limitBytes) {
      console.warn(
        `Model size (${(incomingBytes / 1024 / 1024).toFixed(2)}MB) exceeds cache limit ` +
        `(${this.config.cacheSizeMB}MB), skipping cache`
      );
      return;
    }

    let currentSize = 0;

    for (const model of this.cache.values()) {
      currentSize += model.sizeBytes;
    }

    // Evict oldest entries if over limit
    while (currentSize + incomingBytes > limitBytes && this.cache.size > 0) {
      const oldestKey = this.cache.keys().next().value;
      if (oldestKey) {
        const model = this.cache.get(oldestKey);
        if (model) {
          currentSize -= model.sizeBytes;
          this.disposeModel(model);
        }
        this.cache.delete(oldestKey);
      }
    }
  }

  private disposeModel(model: LoadedModel): void {
    model.scene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.geometry.dispose();

        const materials = Array.isArray(child.material)
          ? child.material
          : [child.material];

        materials.forEach((material) => {
          // Dispose textures
          for (const key in material) {
            const value = (material as Record<string, unknown>)[key];
            if (value instanceof THREE.Texture) {
              value.dispose();
            }
          }
          material.dispose();
        });
      }
    });
  }

  private getCacheKey(url: string): string {
    // Normalize URL for caching
    try {
      const parsed = new URL(url, window.location.origin);
      return parsed.pathname + parsed.search;
    } catch {
      return url;
    }
  }

  private extractNameFromUrl(url: string): string {
    const parts = url.split('/');
    const filename = parts[parts.length - 1] || 'model';
    return filename.replace(/\.(glb|gltf)$/i, '');
  }

  private categorizeError(error?: Error): LoadErrorCode {
    if (!error) return 'UNKNOWN';
    const message = error.message.toLowerCase();

    if (message.includes('404') || message.includes('not found')) return 'NOT_FOUND';
    if (message.includes('network') || message.includes('fetch')) return 'NETWORK_ERROR';
    if (message.includes('timeout')) return 'TIMEOUT';
    if (message.includes('decode') || message.includes('parse')) return 'DECODE_ERROR';
    if (message.includes('invalid') || message.includes('format')) return 'INVALID_FORMAT';

    return 'UNKNOWN';
  }

  private chunkArray<T>(array: T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// ============================================================================
// SINGLETON INSTANCE
// ============================================================================

let defaultLoader: ModelAssetLoader | null = null;

/**
 * Get the default model loader instance
 */
export function getModelLoader(config?: Partial<ThreeJSLoaderConfig>): ModelAssetLoader {
  if (!defaultLoader) {
    defaultLoader = new ModelAssetLoader(config);
  }
  return defaultLoader;
}

/**
 * Reset the default loader (useful for testing)
 */
export function resetModelLoader(): void {
  if (defaultLoader) {
    defaultLoader.dispose();
    defaultLoader = null;
  }
}

export default ModelAssetLoader;
