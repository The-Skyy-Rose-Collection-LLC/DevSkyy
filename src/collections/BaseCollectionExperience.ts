/**
 * Base Collection Experience
 * ==========================
 * Production-grade base class for all 3D collection experiences.
 * Provides unified model loading, performance monitoring, error handling, and lifecycle management.
 *
 * @author DevSkyy Platform Team
 * @version 2.0.0
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { Logger } from '../utils/Logger';
import {
  ModelAssetLoader,
  getModelLoader,
  type LoadedModel,
  type LoadProgress,
  ModelLoadError
} from '../lib/ModelAssetLoader';
import {
  ThreePerformanceMonitor,
  getPerformanceMonitor,
  type PerformanceMetrics,
  type PerformanceWarning
} from '../lib/ThreePerformanceMonitor';
import {
  type ThreeJSConfig,
  detectDeviceConfig,
  HIGH_QUALITY_CONFIG,
  MEDIUM_QUALITY_CONFIG,
  LOW_QUALITY_CONFIG
} from '../config/threejs.config';

// ============================================================================
// TYPES
// ============================================================================

export interface BaseProduct {
  id: string;
  name: string;
  modelUrl?: string;
  position: [number, number, number];
  rotation?: [number, number, number];
  scale?: number | [number, number, number];
}

export interface BaseExperienceConfig {
  /** Background color */
  backgroundColor?: number;
  /** Enable post-processing effects */
  enablePostProcessing?: boolean;
  /** Show performance overlay (development) */
  showPerformanceOverlay?: boolean;
  /** Quality preset override */
  qualityPreset?: 'auto' | 'high' | 'medium' | 'low';
  /** Maximum concurrent model loads */
  maxConcurrentLoads?: number;
  /** Enable automatic quality adjustment */
  adaptiveQuality?: boolean;
  /** Callback when model loading starts */
  onLoadStart?: (productId: string) => void;
  /** Callback for model loading progress */
  onLoadProgress?: (productId: string, progress: LoadProgress) => void;
  /** Callback when model loading completes */
  onLoadComplete?: (productId: string, model: LoadedModel) => void;
  /** Callback when model loading fails */
  onLoadError?: (productId: string, error: ModelLoadError) => void;
  /** Callback when performance warning triggers */
  onPerformanceWarning?: (warning: PerformanceWarning) => void;
  /** Callback when WebGL context is lost */
  onContextLost?: () => void;
  /** Callback when WebGL context is restored */
  onContextRestored?: () => void;
}

export interface ExperienceState {
  isInitialized: boolean;
  isRunning: boolean;
  isDisposed: boolean;
  loadedModels: number;
  totalModels: number;
  currentFPS: number;
  qualityLevel: 'high' | 'medium' | 'low';
}

export type LifecycleEvent = 'init' | 'start' | 'stop' | 'dispose' | 'resize' | 'contextLost' | 'contextRestored';
export type LifecycleHandler = (event: LifecycleEvent) => void;

// ============================================================================
// BASE EXPERIENCE CLASS
// ============================================================================

export abstract class BaseCollectionExperience<
  TProduct extends BaseProduct = BaseProduct,
  TConfig extends BaseExperienceConfig = BaseExperienceConfig
> {
  // Core Three.js objects
  protected scene: THREE.Scene;
  protected renderer: THREE.WebGLRenderer;
  protected camera: THREE.PerspectiveCamera;
  protected controls: OrbitControls;
  protected composer: EffectComposer | null = null;

  // Utilities
  protected logger: Logger;
  protected modelLoader: ModelAssetLoader;
  protected perfMonitor: ThreePerformanceMonitor;
  protected qualityConfig: ThreeJSConfig;

  // State
  protected container: HTMLElement;
  protected config: TConfig;
  protected products: Map<string, THREE.Object3D> = new Map();
  protected loadedModels: Map<string, LoadedModel> = new Map();
  protected animationId: number | null = null;
  protected clock: THREE.Clock;
  protected raycaster: THREE.Raycaster;
  protected mouse: THREE.Vector2;

  // Lifecycle
  private lifecycleHandlers: LifecycleHandler[] = [];
  private isInitialized = false;
  private isRunning = false;
  private isDisposed = false;
  private qualityLevel: 'high' | 'medium' | 'low' = 'high';
  private frameCount = 0;
  private lastQualityCheck = 0;

  constructor(
    container: HTMLElement,
    config: TConfig,
    experienceName: string
  ) {
    this.container = container;
    this.config = config;
    this.logger = new Logger(experienceName);
    this.clock = new THREE.Clock();
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    // Determine quality level
    this.qualityConfig = this.determineQualityConfig();
    this.qualityLevel = this.getQualityLevelName();

    // Initialize model loader with config
    this.modelLoader = getModelLoader({
      maxConcurrentLoads: config.maxConcurrentLoads ?? 4,
      cacheSizeMB: this.qualityConfig.loaders.cacheSizeMB,
    });

    // Initialize performance monitor
    this.perfMonitor = getPerformanceMonitor({
      showOverlay: config.showPerformanceOverlay ?? false,
      onWarning: (warning) => {
        this.handlePerformanceWarning(warning);
        config.onPerformanceWarning?.(warning);
      },
    });

    // Initialize Three.js core
    this.scene = this.createScene();
    this.renderer = this.createRenderer();
    this.camera = this.createCamera();
    this.controls = this.createControls();

    // Setup event listeners
    this.setupEventListeners();

    // Setup post-processing if enabled
    if (config.enablePostProcessing !== false) {
      this.setupPostProcessing();
    }

    this.isInitialized = true;
    this.emitLifecycleEvent('init');
    this.logger.info(`${experienceName} initialized`, { quality: this.qualityLevel });
  }

  // ============================================================================
  // ABSTRACT METHODS - Must be implemented by subclasses
  // ============================================================================

  /** Setup scene-specific lighting */
  protected abstract setupLighting(): void;

  /** Setup scene-specific environment (floor, walls, decorations) */
  protected abstract setupEnvironment(): void;

  /** Handle product-specific loading logic */
  protected abstract onProductLoaded(product: TProduct, model: THREE.Object3D): void;

  /** Create placeholder mesh when model loading fails */
  protected abstract createPlaceholder(product: TProduct): THREE.Object3D;

  /** Scene-specific update logic called each frame */
  protected abstract onUpdate(deltaTime: number, elapsedTime: number): void;

  // ============================================================================
  // PUBLIC API
  // ============================================================================

  /**
   * Load products into the scene
   */
  public async loadProducts(products: TProduct[]): Promise<void> {
    this.logger.info(`Loading ${products.length} products`);

    const loadPromises = products.map((product) => this.loadProduct(product));
    await Promise.allSettled(loadPromises);

    this.logger.info(`Loaded ${this.products.size}/${products.length} products`);
  }

  /**
   * Start the animation loop
   */
  public start(): void {
    if (this.isRunning || this.isDisposed) return;

    this.perfMonitor.attach(this.renderer, this.scene);
    this.perfMonitor.start();
    this.clock.start();
    this.isRunning = true;

    const animate = (): void => {
      if (!this.isRunning) return;

      this.perfMonitor.beginFrame();
      this.animationId = requestAnimationFrame(animate);

      const deltaTime = this.clock.getDelta();
      const elapsedTime = this.clock.getElapsedTime();

      // Update controls
      this.controls.update();

      // Call subclass update
      this.onUpdate(deltaTime, elapsedTime);

      // Render
      if (this.composer) {
        this.composer.render();
      } else {
        this.renderer.render(this.scene, this.camera);
      }

      this.perfMonitor.endFrame();

      // Periodic quality check
      this.frameCount++;
      if (this.config.adaptiveQuality && this.frameCount % 60 === 0) {
        this.checkAndAdjustQuality();
      }
    };

    animate();
    this.emitLifecycleEvent('start');
    this.logger.info('Experience started');
  }

  /**
   * Stop the animation loop
   */
  public stop(): void {
    if (!this.isRunning) return;

    this.isRunning = false;
    this.perfMonitor.stop();
    this.clock.stop();

    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }

    this.emitLifecycleEvent('stop');
    this.logger.info('Experience stopped');
  }

  /**
   * Handle window resize
   */
  public handleResize(width: number, height: number): void {
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);

    if (this.composer) {
      this.composer.setSize(width, height);
    }

    this.emitLifecycleEvent('resize');
  }

  /**
   * Dispose of all resources
   */
  public dispose(): void {
    if (this.isDisposed) return;

    this.stop();
    this.isDisposed = true;

    // Dispose products
    this.products.forEach((obj) => {
      this.disposeObject3D(obj);
      this.scene.remove(obj);
    });
    this.products.clear();
    this.loadedModels.clear();

    // Dispose scene
    this.scene.traverse((object) => {
      this.disposeObject3D(object);
    });

    // Dispose post-processing
    if (this.composer) {
      this.composer.dispose();
    }

    // Dispose core
    this.controls.dispose();
    this.perfMonitor.dispose();
    this.renderer.dispose();
    this.renderer.forceContextLoss();

    // Remove DOM element
    if (this.renderer.domElement.parentNode) {
      this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
    }

    this.emitLifecycleEvent('dispose');
    this.logger.info('Experience disposed');
  }

  /**
   * Get current experience state
   */
  public getState(): ExperienceState {
    const metrics = this.perfMonitor.getMetrics();
    return {
      isInitialized: this.isInitialized,
      isRunning: this.isRunning,
      isDisposed: this.isDisposed,
      loadedModels: this.loadedModels.size,
      totalModels: this.products.size,
      currentFPS: metrics.fps,
      qualityLevel: this.qualityLevel,
    };
  }

  /**
   * Get performance metrics
   */
  public getPerformanceMetrics(): PerformanceMetrics {
    return this.perfMonitor.getMetrics();
  }

  /**
   * Get model loader statistics
   */
  public getLoaderStats() {
    return this.modelLoader.getStats();
  }

  /**
   * Toggle performance overlay visibility
   */
  public showPerformanceOverlay(show: boolean): void {
    this.perfMonitor.setConfig({ showOverlay: show });
  }

  /**
   * Register lifecycle event handler
   */
  public onLifecycle(handler: LifecycleHandler): () => void {
    this.lifecycleHandlers.push(handler);
    return () => {
      const index = this.lifecycleHandlers.indexOf(handler);
      if (index > -1) this.lifecycleHandlers.splice(index, 1);
    };
  }

  /**
   * Get product mesh by ID
   */
  public getProduct(productId: string): THREE.Object3D | undefined {
    return this.products.get(productId);
  }

  /**
   * Force quality level change
   */
  public setQualityLevel(level: 'high' | 'medium' | 'low'): void {
    if (level === this.qualityLevel) return;

    this.qualityLevel = level;
    this.applyQualitySettings(level);
    this.logger.info(`Quality level changed to ${level}`);
  }

  // ============================================================================
  // PROTECTED METHODS - Available to subclasses
  // ============================================================================

  /**
   * Load a single product
   */
  protected async loadProduct(product: TProduct): Promise<void> {
    this.config.onLoadStart?.(product.id);

    let mesh: THREE.Object3D;

    if (product.modelUrl) {
      try {
        const loadedModel = await this.modelLoader.load(product.modelUrl, {
          name: product.name,
          onProgress: (progress) => {
            this.config.onLoadProgress?.(product.id, progress);
          },
        });

        mesh = loadedModel.scene;
        this.loadedModels.set(product.id, loadedModel);
        this.config.onLoadComplete?.(product.id, loadedModel);

        this.logger.debug(`Loaded model: ${product.name}`, {
          triangles: loadedModel.metadata.triangleCount,
          hasAnimations: loadedModel.metadata.hasAnimations,
        });
      } catch (error) {
        const loadError = error instanceof ModelLoadError
          ? error
          : new ModelLoadError('Unknown error', 'UNKNOWN', product.modelUrl ?? '', error instanceof Error ? error : undefined);

        this.logger.warn(`Failed to load model: ${product.name}`, { error: loadError.code });
        this.config.onLoadError?.(product.id, loadError);
        mesh = this.createPlaceholder(product);
      }
    } else {
      mesh = this.createPlaceholder(product);
    }

    // Apply transform
    mesh.position.set(...product.position);

    if (product.rotation) {
      mesh.rotation.set(...product.rotation);
    }

    if (product.scale) {
      const scale = Array.isArray(product.scale)
        ? product.scale
        : [product.scale, product.scale, product.scale];
      mesh.scale.set(...(scale as [number, number, number]));
    }

    // Enable shadows
    mesh.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });

    mesh.userData = { productId: product.id, name: product.name };
    this.scene.add(mesh);
    this.products.set(product.id, mesh);

    // Notify subclass
    this.onProductLoaded(product, mesh);
  }

  /**
   * Perform raycast against products
   */
  protected raycastProducts(event: MouseEvent): THREE.Intersection[] {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    return this.raycaster.intersectObjects(Array.from(this.products.values()), true);
  }

  /**
   * Find product ID from intersected object
   */
  protected findProductId(object: THREE.Object3D): string | null {
    let current: THREE.Object3D | null = object;
    while (current) {
      const pid = current.userData['productId'] as string | undefined;
      if (pid) return pid;
      current = current.parent;
    }
    return null;
  }

  /**
   * Animate camera to position
   */
  protected animateCameraTo(
    targetPosition: THREE.Vector3,
    targetLookAt: THREE.Vector3,
    duration = 1000
  ): Promise<void> {
    return new Promise((resolve) => {
      const startPos = this.camera.position.clone();
      const startTarget = this.controls.target.clone();
      const startTime = performance.now();

      const animate = (): void => {
        const elapsed = performance.now() - startTime;
        const t = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - t, 3); // Ease out cubic

        this.camera.position.lerpVectors(startPos, targetPosition, eased);
        this.controls.target.lerpVectors(startTarget, targetLookAt, eased);

        if (t < 1) {
          requestAnimationFrame(animate);
        } else {
          resolve();
        }
      };

      animate();
    });
  }

  // ============================================================================
  // PRIVATE METHODS
  // ============================================================================

  private createScene(): THREE.Scene {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(this.config.backgroundColor ?? 0x0d0d0d);
    return scene;
  }

  private createRenderer(): THREE.WebGLRenderer {
    const config = this.qualityConfig;

    const renderer = new THREE.WebGLRenderer({
      antialias: config.renderer.antialias,
      alpha: config.renderer.alpha,
      powerPreference: config.renderer.powerPreference,
      stencil: config.renderer.stencil,
      depth: config.renderer.depth,
      preserveDrawingBuffer: config.renderer.preserveDrawingBuffer,
    });

    renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, config.performance.maxPixelRatio));
    renderer.shadowMap.enabled = config.shadows.enabled;
    renderer.shadowMap.type = config.shadows.type;
    renderer.toneMapping = config.postProcessing.toneMapping;
    renderer.toneMappingExposure = config.postProcessing.exposure;
    renderer.outputColorSpace = THREE.SRGBColorSpace;

    this.container.appendChild(renderer.domElement);

    return renderer;
  }

  private createCamera(): THREE.PerspectiveCamera {
    const config = this.qualityConfig.camera;
    const aspect = this.container.clientWidth / this.container.clientHeight;

    const camera = new THREE.PerspectiveCamera(config.fov, aspect, config.near, config.far);
    camera.position.set(config.position.x, config.position.y, config.position.z);

    return camera;
  }

  private createControls(): OrbitControls {
    const controls = new OrbitControls(this.camera, this.renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2;
    controls.minDistance = 2;
    controls.maxDistance = 50;
    return controls;
  }

  private setupPostProcessing(): void {
    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.composer.addPass(new OutputPass());
  }

  private setupEventListeners(): void {
    // Context loss handling
    this.renderer.domElement.addEventListener('webglcontextlost', (e) => {
      e.preventDefault();
      this.handleContextLost();
    });

    this.renderer.domElement.addEventListener('webglcontextrestored', () => {
      this.handleContextRestored();
    });

    // Visibility change (tab switch)
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.stop();
      } else if (this.isInitialized && !this.isDisposed) {
        this.start();
      }
    });
  }

  private handleContextLost(): void {
    this.logger.warn('WebGL context lost');
    this.stop();
    this.config.onContextLost?.();
    this.emitLifecycleEvent('contextLost');
  }

  private handleContextRestored(): void {
    this.logger.info('WebGL context restored');
    this.start();
    this.config.onContextRestored?.();
    this.emitLifecycleEvent('contextRestored');
  }

  private handlePerformanceWarning(warning: PerformanceWarning): void {
    this.logger.warn('Performance warning', {
      type: warning.type,
      severity: warning.severity
    });

    // Auto-adjust quality on critical warnings
    if (warning.severity === 'critical' && this.config.adaptiveQuality) {
      if (this.qualityLevel === 'high') {
        this.setQualityLevel('medium');
      } else if (this.qualityLevel === 'medium') {
        this.setQualityLevel('low');
      }
    }
  }

  private checkAndAdjustQuality(): void {
    const now = performance.now();
    if (now - this.lastQualityCheck < 5000) return; // Check every 5 seconds
    this.lastQualityCheck = now;

    const metrics = this.perfMonitor.getMetrics();
    const score = this.perfMonitor.getPerformanceScore();

    // Upgrade quality if performing well
    if (score > 90 && metrics.fps > 55) {
      if (this.qualityLevel === 'low') {
        this.setQualityLevel('medium');
      } else if (this.qualityLevel === 'medium') {
        this.setQualityLevel('high');
      }
    }
    // Downgrade if struggling
    else if (score < 50 || metrics.fps < 25) {
      if (this.qualityLevel === 'high') {
        this.setQualityLevel('medium');
      } else if (this.qualityLevel === 'medium') {
        this.setQualityLevel('low');
      }
    }
  }

  private determineQualityConfig(): ThreeJSConfig {
    const preset = this.config.qualityPreset ?? 'auto';

    switch (preset) {
      case 'high':
        return HIGH_QUALITY_CONFIG;
      case 'medium':
        return MEDIUM_QUALITY_CONFIG;
      case 'low':
        return LOW_QUALITY_CONFIG;
      case 'auto':
      default:
        return detectDeviceConfig();
    }
  }

  private getQualityLevelName(): 'high' | 'medium' | 'low' {
    if (this.qualityConfig === HIGH_QUALITY_CONFIG) return 'high';
    if (this.qualityConfig === MEDIUM_QUALITY_CONFIG) return 'medium';
    return 'low';
  }

  private applyQualitySettings(level: 'high' | 'medium' | 'low'): void {
    const config = level === 'high'
      ? HIGH_QUALITY_CONFIG
      : level === 'medium'
        ? MEDIUM_QUALITY_CONFIG
        : LOW_QUALITY_CONFIG;

    // Update renderer
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, config.performance.maxPixelRatio));
    this.renderer.shadowMap.enabled = config.shadows.enabled;
    this.renderer.shadowMap.type = config.shadows.type;

    // Update composer if exists
    if (this.composer && !config.postProcessing.enabled) {
      this.composer = null;
    }
  }

  private disposeObject3D(object: THREE.Object3D): void {
    if (object instanceof THREE.Mesh) {
      object.geometry?.dispose();

      const materials = Array.isArray(object.material)
        ? object.material
        : [object.material];

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
  }

  private emitLifecycleEvent(event: LifecycleEvent): void {
    this.lifecycleHandlers.forEach((handler) => {
      try {
        handler(event);
      } catch (error) {
        this.logger.error('Lifecycle handler error', { event, error });
      }
    });
  }
}

export default BaseCollectionExperience;
