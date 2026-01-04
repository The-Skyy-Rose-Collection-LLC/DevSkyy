/**
 * SIGNATURE Collection - 3D Immersive Experience
 *
 * Classic luxury rose garden with red, gold, and ivory roses.
 * Warm golden hour lighting, soft depth of field.
 *
 * Clickable Assets:
 * - Garden pedestals showcasing products
 * - Interactive fountain centerpiece with collection video
 * - Rose-lined pathways leading to product categories
 * - Floating brand logo as navigation anchor
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { Logger } from '../utils/Logger';
import { HotspotManager } from './HotspotManager';
import { getModelLoader, ModelLoadError, type LoadedModel } from '../lib/ModelAssetLoader';
import { getPerformanceMonitor, type PerformanceMetrics } from '../lib/ThreePerformanceMonitor';

// ============================================================================
// Types & Interfaces
// ============================================================================

export interface SignatureProduct {
  id: string;
  name: string;
  price: number;
  category: 'tops' | 'bottoms' | 'dresses' | 'accessories';
  modelUrl: string;
  thumbnailUrl: string;
  pedestalPosition: [number, number, number];
}

export interface SignatureConfig {
  backgroundColor?: number;
  sunlightColor?: number;
  sunlightIntensity?: number;
  ambientColor?: number;
  enableDepthOfField?: boolean;
  focusDistance?: number;
}

export type CategorySelectHandler = (category: string) => void;
export type ProductSelectHandler = (product: SignatureProduct) => void;

// ============================================================================
// Constants
// ============================================================================

const BRAND_COLORS = {
  roseGold: 0xd4af37,
  ivory: 0xf5f5f0,
  crimson: 0xdc143c,
  gold: 0xffd700,
  warmWhite: 0xfff8e7,
};

const DEFAULT_CONFIG: Required<SignatureConfig> = {
  backgroundColor: 0xfff8e7,
  sunlightColor: 0xffd700,
  sunlightIntensity: 1.2,
  ambientColor: 0xffe4c4,
  enableDepthOfField: true,
  focusDistance: 10,
};

// Category pathway angles (radial from fountain)
const CATEGORY_ANGLES: Record<string, number> = {
  tops: 0,
  dresses: Math.PI / 2,
  bottoms: Math.PI,
  accessories: (3 * Math.PI) / 2,
};

// ============================================================================
// Main Experience Class
// ============================================================================

export class SignatureExperience {
  private logger: Logger;
  private container: HTMLElement;
  private config: Required<SignatureConfig>;

  // Production handlers
  private modelLoader = getModelLoader({ cacheSizeMB: 256 });
  private perfMonitor = getPerformanceMonitor({ showOverlay: false });
  private loadedModels: Map<string, LoadedModel> = new Map();
  private _isContextLost = false;

  // Three.js core
  private scene: THREE.Scene;
  private renderer: THREE.WebGLRenderer;
  private camera: THREE.PerspectiveCamera;
  private controls: OrbitControls;
  private composer: EffectComposer | null = null;

  // Scene objects
  private pedestals: Map<string, THREE.Group> = new Map();
  private fountain: THREE.Group | null = null;
  private pathways: THREE.Group[] = [];
  private brandLogo: THREE.Group | null = null;
  private roses: THREE.Object3D[] = [];

  // State
  private animationId: number | null = null;
  private clock: THREE.Clock;
  private raycaster: THREE.Raycaster;
  private mouse: THREE.Vector2;
  private hotspotManager: HotspotManager | null = null;

  // Callbacks
  private onProductSelect: ProductSelectHandler | null = null;
  private onCategorySelect: CategorySelectHandler | null = null;

  constructor(container: HTMLElement, config: SignatureConfig = {}) {
    this.logger = new Logger('SignatureExperience');
    this.container = container;
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.clock = new THREE.Clock();
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    // Initialize Three.js
    this.scene = this.createScene();
    this.renderer = this.createRenderer();
    this.camera = this.createCamera();
    this.controls = this.createControls();

    if (this.config.enableDepthOfField) {
      this.setupPostProcessing();
    }

    this.setupEnvironment();
    this.setupLighting();
    this.createFountain();
    this.createBrandLogo();

    // Initialize hotspot system
    this.initializeHotspots();

    this.setupEventListeners();

    this.logger.info('SIGNATURE experience initialized');
  }

  private createScene(): THREE.Scene {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(this.config.backgroundColor);
    scene.fog = new THREE.Fog(this.config.backgroundColor, 20, 50);
    return scene;
  }

  private createRenderer(): THREE.WebGLRenderer {
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    this.container.appendChild(renderer.domElement);
    return renderer;
  }

  private createCamera(): THREE.PerspectiveCamera {
    const aspect = this.container.clientWidth / this.container.clientHeight;
    const camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 100);
    camera.position.set(0, 5, 15);
    camera.lookAt(0, 0, 0);
    return camera;
  }

  private createControls(): OrbitControls {
    const controls = new OrbitControls(this.camera, this.renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2.2;
    controls.minDistance = 8;
    controls.maxDistance = 30;
    controls.target.set(0, 1, 0);
    return controls;
  }

  private setupPostProcessing(): void {
    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));

    const bokehPass = new BokehPass(this.scene, this.camera, {
      focus: this.config.focusDistance,
      aperture: 0.0001,
      maxblur: 0.005,
    });
    this.composer.addPass(bokehPass);
  }

  private setupEnvironment(): void {
    // Ground - lush green grass
    const groundGeometry = new THREE.CircleGeometry(25, 64);
    const groundMaterial = new THREE.MeshStandardMaterial({
      color: 0x3d5c3d,
      roughness: 0.9,
    });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.scene.add(ground);

    // Create four pathways for categories
    Object.entries(CATEGORY_ANGLES).forEach(([category, angle]) => {
      this.createPathway(angle, category);
    });

    // Add decorative rose bushes
    this.createRoseBushes();
  }

  private setupLighting(): void {
    // Golden hour sunlight
    const sunlight = new THREE.DirectionalLight(
      this.config.sunlightColor,
      this.config.sunlightIntensity
    );
    sunlight.position.set(10, 15, 10);
    sunlight.castShadow = true;
    sunlight.shadow.mapSize.width = 2048;
    sunlight.shadow.mapSize.height = 2048;
    this.scene.add(sunlight);

    // Warm ambient fill
    const ambient = new THREE.AmbientLight(this.config.ambientColor, 0.4);
    this.scene.add(ambient);

    // Secondary fill light
    const fillLight = new THREE.DirectionalLight(BRAND_COLORS.warmWhite, 0.3);
    fillLight.position.set(-5, 8, -5);
    this.scene.add(fillLight);
  }

  private createPathway(angle: number, category: string): void {
    const pathway = new THREE.Group();

    // Stone pathway
    const pathGeometry = new THREE.PlaneGeometry(2, 10);
    const pathMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.ivory,
      roughness: 0.7,
    });
    const path = new THREE.Mesh(pathGeometry, pathMaterial);
    path.rotation.x = -Math.PI / 2;
    path.position.set(0, 0.01, 5);
    path.receiveShadow = true;
    pathway.add(path);

    // Rose hedges along pathway
    const hedgeGeometry = new THREE.BoxGeometry(0.5, 1, 10);
    const hedgeMaterial = new THREE.MeshStandardMaterial({ color: 0x2d4a2d });

    const leftHedge = new THREE.Mesh(hedgeGeometry, hedgeMaterial);
    leftHedge.position.set(-1.5, 0.5, 5);
    pathway.add(leftHedge);

    const rightHedge = new THREE.Mesh(hedgeGeometry, hedgeMaterial);
    rightHedge.position.set(1.5, 0.5, 5);
    pathway.add(rightHedge);

    // Category label
    pathway.userData = { category };
    pathway.rotation.y = angle;
    this.scene.add(pathway);
    this.pathways.push(pathway);
  }

  private createRoseBushes(): void {
    const positions: [number, number, number][] = [
      [-8, 0, -8], [8, 0, -8], [-8, 0, 8], [8, 0, 8],
      [-12, 0, 0], [12, 0, 0], [0, 0, -12], [0, 0, 12],
    ];

    positions.forEach(([x, y, z]) => {
      const bush = this.createRoseBush();
      bush.position.set(x, y, z);
      this.scene.add(bush);
      this.roses.push(bush);
    });
  }

  private createRoseBush(): THREE.Group {
    const bush = new THREE.Group();

    // Bush base
    const baseGeometry = new THREE.SphereGeometry(1.2, 12, 10);
    const baseMaterial = new THREE.MeshStandardMaterial({
      color: 0x2d4a2d,
      roughness: 0.8,
    });
    const base = new THREE.Mesh(baseGeometry, baseMaterial);
    base.scale.y = 0.7;
    base.position.y = 0.6;
    bush.add(base);

    // Red roses
    for (let i = 0; i < 5; i++) {
      const rose = this.createRose(BRAND_COLORS.crimson);
      rose.position.set(
        (Math.random() - 0.5) * 1.5,
        0.8 + Math.random() * 0.5,
        (Math.random() - 0.5) * 1.5
      );
      rose.scale.setScalar(0.2);
      bush.add(rose);
    }

    // Gold accent roses
    for (let i = 0; i < 2; i++) {
      const rose = this.createRose(BRAND_COLORS.gold);
      rose.position.set(
        (Math.random() - 0.5) * 1.2,
        1.0 + Math.random() * 0.3,
        (Math.random() - 0.5) * 1.2
      );
      rose.scale.setScalar(0.18);
      bush.add(rose);
    }

    bush.castShadow = true;
    return bush;
  }

  private createRose(color: number): THREE.Group {
    const rose = new THREE.Group();
    const petalGeometry = new THREE.SphereGeometry(0.5, 8, 6);
    const petalMaterial = new THREE.MeshStandardMaterial({
      color,
      roughness: 0.4,
    });

    for (let i = 0; i < 8; i++) {
      const petal = new THREE.Mesh(petalGeometry, petalMaterial);
      const angle = (i / 8) * Math.PI * 2;
      petal.position.set(Math.cos(angle) * 0.3, 0, Math.sin(angle) * 0.3);
      petal.scale.set(0.5, 0.3, 0.8);
      petal.rotation.y = angle;
      rose.add(petal);
    }

    const centerGeometry = new THREE.SphereGeometry(0.15, 8, 8);
    const centerMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.gold,
      emissive: BRAND_COLORS.gold,
      emissiveIntensity: 0.2,
    });
    rose.add(new THREE.Mesh(centerGeometry, centerMaterial));

    return rose;
  }

  private createFountain(): void {
    this.fountain = new THREE.Group();

    // Base
    const baseGeometry = new THREE.CylinderGeometry(2, 2.5, 0.8, 32);
    const baseMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.ivory,
      roughness: 0.3,
    });
    const base = new THREE.Mesh(baseGeometry, baseMaterial);
    base.position.y = 0.4;
    this.fountain.add(base);

    // Bowl
    const bowlGeometry = new THREE.CylinderGeometry(1.8, 1.5, 0.5, 32);
    const bowl = new THREE.Mesh(bowlGeometry, baseMaterial);
    bowl.position.y = 1.0;
    this.fountain.add(bowl);

    // Center column
    const columnGeometry = new THREE.CylinderGeometry(0.3, 0.4, 2, 16);
    const column = new THREE.Mesh(columnGeometry, baseMaterial);
    column.position.y = 2.0;
    this.fountain.add(column);

    // Water particles (simplified)
    const waterGeometry = new THREE.SphereGeometry(0.05, 8, 8);
    const waterMaterial = new THREE.MeshStandardMaterial({
      color: 0x87ceeb,
      transparent: true,
      opacity: 0.6,
    });
    for (let i = 0; i < 20; i++) {
      const drop = new THREE.Mesh(waterGeometry, waterMaterial);
      drop.position.set(
        (Math.random() - 0.5) * 1.5,
        2.5 + Math.random() * 0.5,
        (Math.random() - 0.5) * 1.5
      );
      drop.userData = { initialY: drop.position.y, speed: Math.random() * 2 + 1 };
      this.fountain.add(drop);
    }

    this.fountain.userData = { type: 'fountain' };
    this.scene.add(this.fountain);
  }

  private createBrandLogo(): void {
    this.brandLogo = new THREE.Group();

    // Floating "S" monogram (simplified)
    const logoGeometry = new THREE.TorusGeometry(0.5, 0.1, 8, 32);
    const logoMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.roseGold,
      roughness: 0.2,
      metalness: 0.9,
      emissive: BRAND_COLORS.roseGold,
      emissiveIntensity: 0.3,
    });
    const logo = new THREE.Mesh(logoGeometry, logoMaterial);
    this.brandLogo.add(logo);

    this.brandLogo.position.set(0, 6, 0);
    this.brandLogo.userData = { type: 'logo', initialY: 6 };
    this.scene.add(this.brandLogo);
  }

  private async initializeHotspots(): Promise<void> {
    try {
      // Create hotspot manager
      this.hotspotManager = new HotspotManager(
        this.scene,
        this.camera,
        this.renderer
      );

      // Load hotspot configuration from WordPress
      const configUrl = '/wp-content/uploads/hotspots/signature-hotspots.json';
      await this.hotspotManager.loadConfig(configUrl);

      // Set product selection callback
      this.hotspotManager.setOnProductSelect((productData) => {
        // Find matching product in pedestals
        for (const [id, pedestal] of this.pedestals) {
          if (parseInt(id) === productData.product_id) {
            const product = pedestal.userData['product'] as SignatureProduct;
            if (product && this.onProductSelect) {
              this.onProductSelect(product);
            }
            break;
          }
        }
      });

      this.logger.info('Hotspots initialized for SIGNATURE collection');
    } catch (error) {
      this.logger.warn(`Failed to initialize hotspots: ${error instanceof Error ? error.message : String(error)}`);
      // Continue without hotspots - they're optional
    }
  }

  private setupEventListeners(): void {
    this.container.addEventListener('click', this.onClick.bind(this));
    window.addEventListener('resize', this.onResize.bind(this));
  }

  private onClick(_event: MouseEvent): void {
    const rect = this.container.getBoundingClientRect();
    this.mouse.x = ((_event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((_event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);

    // Check pedestals
    const pedestalObjects = Array.from(this.pedestals.values());
    const intersects = this.raycaster.intersectObjects(pedestalObjects, true);
    const firstIntersect = intersects[0];
    if (firstIntersect && this.onProductSelect) {
      const product = this.findProductInAncestors(firstIntersect.object);
      if (product) this.onProductSelect(product);
    }

    // Check pathways
    const pathwayIntersects = this.raycaster.intersectObjects(this.pathways, true);
    const firstPathwayIntersect = pathwayIntersects[0];
    if (firstPathwayIntersect && this.onCategorySelect) {
      let obj: THREE.Object3D | null = firstPathwayIntersect.object;
      while (obj && !obj.userData['category']) obj = obj.parent;
      if (obj) {
        const category = obj.userData['category'] as string | undefined;
        if (category) this.onCategorySelect(category);
      }
    }
  }

  private findProductInAncestors(obj: THREE.Object3D): SignatureProduct | null {
    let current: THREE.Object3D | null = obj;
    while (current) {
      const product = current.userData['product'] as SignatureProduct | undefined;
      if (product) return product;
      current = current.parent;
    }
    return null;
  }

  private onResize(): void {
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
    this.composer?.setSize(w, h);
  }

  // ===========================================================================
  // Public API
  // ===========================================================================

  public async loadProducts(products: SignatureProduct[]): Promise<void> {
    for (const product of products) {
      this.createPedestal(product);
    }
    this.logger.info(`Loaded ${products.length} products`);
  }

  private createPedestal(product: SignatureProduct): void {
    const pedestal = new THREE.Group();
    pedestal.userData = { productId: product.id, product };

    // Column pedestal
    const columnGeometry = new THREE.CylinderGeometry(0.4, 0.5, 1.5, 16);
    const columnMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.ivory,
      roughness: 0.3,
    });
    const column = new THREE.Mesh(columnGeometry, columnMaterial);
    column.position.y = 0.75;
    column.castShadow = true;
    pedestal.add(column);

    // Product placeholder
    const productGeometry = new THREE.BoxGeometry(0.6, 0.8, 0.4);
    const productMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.roseGold,
      roughness: 0.3,
      metalness: 0.7,
    });
    const productMesh = new THREE.Mesh(productGeometry, productMaterial);
    productMesh.position.y = 1.9;
    productMesh.castShadow = true;
    pedestal.add(productMesh);

    pedestal.position.set(...product.pedestalPosition);
    this.scene.add(pedestal);
    this.pedestals.set(product.id, pedestal);
  }

  public setOnProductSelect(handler: ProductSelectHandler): void {
    this.onProductSelect = handler;
  }

  public setOnCategorySelect(handler: CategorySelectHandler): void {
    this.onCategorySelect = handler;
  }

  public start(): void {
    // Initialize performance monitoring
    this.perfMonitor.attach(this.renderer, this.scene);
    this.perfMonitor.start();

    const animate = (): void => {
      this.perfMonitor.beginFrame();
      this.animationId = requestAnimationFrame(animate);
      const elapsed = this.clock.getElapsedTime();

      // Animate brand logo float
      if (this.brandLogo) {
        this.brandLogo.position.y = 6 + Math.sin(elapsed * 0.5) * 0.3;
        this.brandLogo.rotation.y = elapsed * 0.2;
      }

      // Animate fountain water
      if (this.fountain) {
        this.fountain.children.forEach((child) => {
          const speed = child.userData['speed'] as number;
          const initialY = child.userData['initialY'] as number;
          if (speed !== undefined && initialY !== undefined) {
            const t = (elapsed * speed) % 1;
            child.position.y = initialY - t * 1.5;
          }
        });
      }

      this.controls.update();
      this.composer ? this.composer.render() : this.renderer.render(this.scene, this.camera);
      this.perfMonitor.endFrame();
    };
    animate();
    this.logger.info('Animation started');
  }

  public stop(): void {
    this.perfMonitor.stop();
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  public dispose(): void {
    this.stop();
    window.removeEventListener('resize', this.onResize.bind(this));

    // Cleanup hotspots
    if (this.hotspotManager) {
      this.hotspotManager.dispose();
      this.hotspotManager = null;
    }

    // Helper to dispose mesh resources
    const disposeMesh = (obj: THREE.Object3D): void => {
      if (obj instanceof THREE.Mesh) {
        obj.geometry?.dispose();
        if (obj.material instanceof THREE.Material) {
          obj.material.dispose();
        } else if (Array.isArray(obj.material)) {
          obj.material.forEach((mat) => mat.dispose());
        }
      }
    };

    // Dispose pedestals (Map)
    this.pedestals.forEach((p) => {
      p.traverse(disposeMesh);
      this.scene.remove(p);
    });
    this.pedestals.clear();

    // Dispose pathways
    this.pathways.forEach((p) => {
      disposeMesh(p);
      this.scene.remove(p);
    });
    this.pathways = [];

    // Dispose roses
    this.roses.forEach((r) => {
      r.traverse(disposeMesh);
      this.scene.remove(r);
    });
    this.roses = [];

    // Dispose fountain
    if (this.fountain) {
      this.fountain.traverse(disposeMesh);
      this.scene.remove(this.fountain);
    }

    // Dispose brand logo
    if (this.brandLogo) {
      this.brandLogo.traverse(disposeMesh);
      this.scene.remove(this.brandLogo);
    }

    // Dispose all remaining scene objects
    this.scene.traverse(disposeMesh);

    // Dispose controls, composer, and renderer
    this.controls.dispose();
    if (this.composer) this.composer.dispose();
    this.renderer.dispose();
    this.renderer.forceContextLoss();

    this.logger.info('SIGNATURE experience disposed');
  }

  /**
   * Handle WebGL context loss - prevents crashes on mobile/low-memory devices
   */
  public handleContextLoss(): void {
    this._isContextLost = true;
    this.logger.warn('WebGL context lost - attempting recovery');
    this.stop();
  }

  /**
   * Handle WebGL context restoration
   */
  public handleContextRestored(): void {
    this._isContextLost = false;
    this.logger.info('WebGL context restored');
    this.start();
  }

  // ============================================================================
  // PRODUCTION API
  // ============================================================================

  /**
   * Check if WebGL context is currently lost
   */
  public get isContextLost(): boolean {
    return this._isContextLost;
  }

  /**
   * Get current performance metrics
   */
  public getPerformanceMetrics(): PerformanceMetrics {
    return this.perfMonitor.getMetrics();
  }

  /**
   * Toggle performance overlay visibility
   */
  public showPerformanceOverlay(show: boolean): void {
    this.perfMonitor.setConfig({ showOverlay: show });
  }

  /**
   * Get model loader statistics
   */
  public getLoaderStats() {
    return this.modelLoader.getStats();
  }

  /**
   * Preload models for faster rendering
   */
  public async preloadModels(urls: string[]): Promise<void> {
    await this.modelLoader.preload(urls);
    this.logger.info(`Preloaded ${urls.length} models`);
  }

  /**
   * Load a GLB model with production error handling
   */
  protected async loadGLBModel(
    productId: string,
    modelUrl: string,
    productName: string
  ): Promise<THREE.Object3D | null> {
    try {
      const loadedModel = await this.modelLoader.load(modelUrl, {
        name: productName,
        onProgress: (progress) => {
          this.logger.debug(`Loading ${productName}: ${progress.percent}%`);
        },
      });
      this.loadedModels.set(productId, loadedModel);
      this.logger.info(`Loaded model: ${productName}`, {
        triangles: loadedModel.metadata.triangleCount,
      });
      return loadedModel.scene;
    } catch (error) {
      if (error instanceof ModelLoadError) {
        this.logger.warn(`Failed to load ${productName}: ${error.code}`);
      }
      return null;
    }
  }

  public getScene(): THREE.Scene { return this.scene; }
  public getCamera(): THREE.PerspectiveCamera { return this.camera; }
}

export default SignatureExperience;
