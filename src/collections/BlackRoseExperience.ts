/**
 * BLACK ROSE Collection - 3D Immersive Experience
 *
 * Gothic rose garden with black, white, and silver roses.
 * Dark ambient lighting with silver moonlight, fog effects, obsidian pathways.
 *
 * Clickable Assets:
 * - 3D rose bushes revealing product cards on hover/click
 * - Floating silver petals as navigation hints
 * - Interactive rose arbors displaying featured items
 * - Hidden "Easter egg" assets (thorns, gates) linking to exclusive drops
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { Logger } from '../utils/Logger.js';
import { HotspotManager } from './HotspotManager.js';
import { getModelLoader, ModelLoadError, type LoadedModel } from '../lib/ModelAssetLoader.js';
import { getPerformanceMonitor, type PerformanceMetrics } from '../lib/ThreePerformanceMonitor.js';

// ============================================================================
// Types & Interfaces
// ============================================================================

export interface BlackRoseProduct {
  id: string;
  name: string;
  price: number;
  modelUrl: string;
  thumbnailUrl: string;
  position: [number, number, number];
  isEasterEgg?: boolean;
  exclusiveDropUrl?: string;
}

export interface BlackRoseConfig {
  backgroundColor?: number;
  fogColor?: number;
  fogDensity?: number;
  moonlightColor?: number;
  moonlightIntensity?: number;
  petalCount?: number;
  enableBloom?: boolean;
  bloomStrength?: number;
}

export interface ProductCardData {
  productId: string;
  name: string;
  price: number;
  thumbnailUrl: string;
  position: { x: number; y: number };
}

export type ProductClickHandler = (product: BlackRoseProduct) => void;
export type EasterEggHandler = (url: string) => void;

// ============================================================================
// Constants
// ============================================================================

const BRAND_COLORS = {
  obsidian: 0x0d0d0d,
  silver: 0xc0c0c0,
  ivory: 0xf5f5f0,
  roseGold: 0xd4af37,
  black: 0x000000,
  white: 0xffffff,
};

const DEFAULT_CONFIG: Required<BlackRoseConfig> = {
  backgroundColor: BRAND_COLORS.obsidian,
  fogColor: 0x0a0a0a,
  fogDensity: 0.03,
  moonlightColor: BRAND_COLORS.silver,
  moonlightIntensity: 0.8,
  petalCount: 50,
  enableBloom: true,
  bloomStrength: 0.4,
};

// ============================================================================
// Main Experience Class
// ============================================================================

export class BlackRoseExperience {
  private logger: Logger;
  private container: HTMLElement;
  private config: Required<BlackRoseConfig>;

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
  private roseBushes: Map<string, THREE.Group> = new Map();
  private petals: THREE.Object3D[] = [];
  private arbors: THREE.Group[] = [];
  private easterEggs: Map<string, THREE.Object3D> = new Map();
  private nightSky: THREE.Mesh | null = null;
  private clouds: THREE.Sprite[] = [];

  // State
  private animationId: number | null = null;
  private clock: THREE.Clock;
  private raycaster: THREE.Raycaster;
  private mouse: THREE.Vector2;
  private hoveredProduct: string | null = null;
  private hotspotManager: HotspotManager | null = null;

  // Callbacks
  private onProductClick: ProductClickHandler | null = null;
  private onEasterEgg: EasterEggHandler | null = null;
  private onProductHover: ((data: ProductCardData | null) => void) | null = null;

  constructor(container: HTMLElement, config: BlackRoseConfig = {}) {
    this.logger = new Logger('BlackRoseExperience');
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

    if (this.config.enableBloom) {
      this.setupPostProcessing();
    }

    this.setupEnvironment();
    this.setupLighting();

    // Initialize hotspot system
    this.initializeHotspots();

    this.setupEventListeners();

    this.logger.info('BLACK ROSE experience initialized');
  }

  private createScene(): THREE.Scene {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(this.config.backgroundColor);
    scene.fog = new THREE.FogExp2(this.config.fogColor, this.config.fogDensity);
    return scene;
  }

  private createRenderer(): THREE.WebGLRenderer {
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.8;
    this.container.appendChild(renderer.domElement);
    return renderer;
  }

  private createCamera(): THREE.PerspectiveCamera {
    const aspect = this.container.clientWidth / this.container.clientHeight;
    const camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 100);
    camera.position.set(0, 3, 12);
    return camera;
  }

  private createControls(): OrbitControls {
    const controls = new OrbitControls(this.camera, this.renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2.1;
    controls.minDistance = 5;
    controls.maxDistance = 25;
    controls.target.set(0, 1, 0);
    return controls;
  }

  private setupPostProcessing(): void {
    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));

    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
      this.config.bloomStrength,
      0.4,
      0.85
    );
    this.composer.addPass(bloomPass);
  }

  private setupEnvironment(): void {
    // Night sky with shader
    this.createNightSky();

    // Moving clouds
    this.createMovingClouds();

    // Obsidian pathway
    const pathGeometry = new THREE.PlaneGeometry(4, 30);
    const pathMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a1a1a,
      roughness: 0.2,
      metalness: 0.9,
    });
    const path = new THREE.Mesh(pathGeometry, pathMaterial);
    path.rotation.x = -Math.PI / 2;
    path.receiveShadow = true;
    this.scene.add(path);

    // Ground plane (dark grass/earth)
    const groundGeometry = new THREE.PlaneGeometry(50, 50);
    const groundMaterial = new THREE.MeshStandardMaterial({
      color: 0x0a0a0a,
      roughness: 0.9,
    });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.01;
    ground.receiveShadow = true;
    this.scene.add(ground);

    // Create floating silver petals
    this.createFloatingPetals();
  }

  private setupLighting(): void {
    // Silver moonlight (main directional)
    const moonlight = new THREE.DirectionalLight(
      this.config.moonlightColor,
      this.config.moonlightIntensity
    );
    moonlight.position.set(-10, 15, -10);
    moonlight.castShadow = true;
    moonlight.shadow.mapSize.width = 2048;
    moonlight.shadow.mapSize.height = 2048;
    moonlight.shadow.camera.near = 0.5;
    moonlight.shadow.camera.far = 50;
    this.scene.add(moonlight);

    // Dim ambient
    const ambient = new THREE.AmbientLight(0x1a1a2e, 0.2);
    this.scene.add(ambient);

    // Silver rim light
    const rimLight = new THREE.DirectionalLight(BRAND_COLORS.silver, 0.3);
    rimLight.position.set(10, 5, 10);
    this.scene.add(rimLight);
  }

  private createFloatingPetals(): void {
    const petalGeometry = new THREE.PlaneGeometry(0.15, 0.2);
    const petalMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.silver,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.7,
      emissive: BRAND_COLORS.silver,
      emissiveIntensity: 0.2,
    });

    for (let i = 0; i < this.config.petalCount; i++) {
      const petal = new THREE.Mesh(petalGeometry, petalMaterial.clone());
      petal.position.set(
        (Math.random() - 0.5) * 20,
        Math.random() * 8 + 1,
        (Math.random() - 0.5) * 20
      );
      petal.rotation.set(
        Math.random() * Math.PI,
        Math.random() * Math.PI,
        Math.random() * Math.PI
      );
      petal.userData = {
        initialY: petal.position.y,
        speed: Math.random() * 0.5 + 0.2,
        rotationSpeed: Math.random() * 0.02 - 0.01,
      };
      this.scene.add(petal);
      this.petals.push(petal);
    }
  }

  /**
   * Creates night sky with shader material (dark gradient from bottom to top)
   */
  private createNightSky(): void {
    // Vertex shader for sky
    const vertexShader = `
      varying vec3 vWorldPosition;
      void main() {
        vec4 worldPosition = modelMatrix * vec4(position, 1.0);
        vWorldPosition = worldPosition.xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `;

    // Fragment shader for night sky gradient
    const fragmentShader = `
      uniform vec3 topColor;
      uniform vec3 bottomColor;
      uniform float offset;
      uniform float exponent;
      varying vec3 vWorldPosition;
      void main() {
        float h = normalize(vWorldPosition + offset).y;
        gl_FragColor = vec4(mix(bottomColor, topColor, max(pow(max(h, 0.0), exponent), 0.0)), 1.0);
      }
    `;

    const uniforms = {
      topColor: { value: new THREE.Color(0x0a0a1a) },    // Deep dark blue (night)
      bottomColor: { value: new THREE.Color(0x000000) }, // Pure black (horizon)
      offset: { value: 400 },
      exponent: { value: 0.6 },
    };

    const skyGeo = new THREE.SphereGeometry(500, 32, 15);
    const skyMat = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms,
      side: THREE.BackSide,
    });

    this.nightSky = new THREE.Mesh(skyGeo, skyMat);
    this.scene.add(this.nightSky);
  }

  /**
   * Creates moving cloud sprites (animated particles)
   */
  private createMovingClouds(): void {
    const cloudCount = 12;
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');

    if (!ctx) return;

    // Create cloud texture (soft gradient)
    const gradient = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
    gradient.addColorStop(0, 'rgba(30, 30, 40, 0.8)');
    gradient.addColorStop(0.5, 'rgba(20, 20, 30, 0.4)');
    gradient.addColorStop(1, 'rgba(10, 10, 20, 0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 128, 128);

    const cloudTexture = new THREE.CanvasTexture(canvas);
    const cloudMaterial = new THREE.SpriteMaterial({
      map: cloudTexture,
      transparent: true,
      opacity: 0.3,
      depthWrite: false,
    });

    for (let i = 0; i < cloudCount; i++) {
      const cloud = new THREE.Sprite(cloudMaterial.clone());

      // Random position in sky
      cloud.position.set(
        (Math.random() - 0.5) * 100,
        20 + Math.random() * 30,
        (Math.random() - 0.5) * 100
      );

      // Random size
      const scale = 15 + Math.random() * 20;
      cloud.scale.set(scale, scale * 0.5, 1);

      // Movement data
      cloud.userData = {
        speedX: Math.random() * 0.2 + 0.1,
        speedZ: Math.random() * 0.1,
        initialX: cloud.position.x,
        initialZ: cloud.position.z,
      };

      this.scene.add(cloud);
      this.clouds.push(cloud);
    }
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
      const configUrl = '/wp-content/uploads/hotspots/black-rose-hotspots.json';
      await this.hotspotManager.loadConfig(configUrl);

      // Set product selection callback
      this.hotspotManager.setOnProductSelect((productData) => {
        // Find matching product in rose bushes
        for (const [id, bush] of this.roseBushes) {
          if (parseInt(id) === productData.product_id) {
            const product = bush.userData['product'] as BlackRoseProduct;
            if (product && this.onProductClick) {
              this.onProductClick(product);
            }
            break;
          }
        }
      });

      this.logger.info('Hotspots initialized for BLACK ROSE collection');
    } catch (error) {
      this.logger.warn(`Failed to initialize hotspots: ${error instanceof Error ? error.message : String(error)}`);
      // Continue without hotspots - they're optional
    }
  }

  private setupEventListeners(): void {
    this.container.addEventListener('mousemove', this.onMouseMove.bind(this));
    this.container.addEventListener('click', this.onClick.bind(this));
    window.addEventListener('resize', this.onResize.bind(this));
  }

  private onMouseMove(event: MouseEvent): void {
    const rect = this.container.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    this.checkHover();
  }

  private onClick(_event: MouseEvent): void {
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const objects = Array.from(this.roseBushes.values());
    const intersects = this.raycaster.intersectObjects(objects, true);

    const firstIntersect = intersects[0];
    if (firstIntersect) {
      const productId = this.findProductId(firstIntersect.object);
      if (productId && this.onProductClick) {
        const product = this.getProductById(productId);
        if (product) this.onProductClick(product);
      }
    }

    // Check easter eggs
    const easterEggObjects = Array.from(this.easterEggs.values());
    const eggIntersects = this.raycaster.intersectObjects(easterEggObjects, true);
    const firstEggIntersect = eggIntersects[0];
    if (firstEggIntersect && this.onEasterEgg) {
      const url = firstEggIntersect.object.userData['exclusiveDropUrl'] as string | undefined;
      if (url) this.onEasterEgg(url);
    }
  }

  private checkHover(): void {
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const objects = Array.from(this.roseBushes.values());
    const intersects = this.raycaster.intersectObjects(objects, true);

    const firstIntersect = intersects[0];
    if (firstIntersect) {
      const productId = this.findProductId(firstIntersect.object);
      if (productId !== this.hoveredProduct) {
        this.hoveredProduct = productId;
        this.container.style.cursor = 'pointer';
      }
    } else {
      if (this.hoveredProduct) {
        this.hoveredProduct = null;
        this.container.style.cursor = 'default';
        if (this.onProductHover) this.onProductHover(null);
      }
    }
  }

  private findProductId(obj: THREE.Object3D): string | null {
    let current: THREE.Object3D | null = obj;
    while (current) {
      const pid = current.userData['productId'] as string | undefined;
      if (pid) return pid;
      current = current.parent;
    }
    return null;
  }

  private getProductById(id: string): BlackRoseProduct | null {
    for (const [productId, bush] of this.roseBushes) {
      if (productId === id) return bush.userData['product'] as BlackRoseProduct;
    }
    return null;
  }

  private onResize(): void {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
    this.composer?.setSize(width, height);
  }

  // ===========================================================================
  // Public API
  // ===========================================================================

  public async loadProducts(products: BlackRoseProduct[]): Promise<void> {
    for (const product of products) {
      await this.createRoseBush(product);
    }
    this.logger.info(`Loaded ${products.length} products`);
  }

  private async createRoseBush(product: BlackRoseProduct): Promise<void> {
    const bush = new THREE.Group();
    bush.userData = { productId: product.id, product };

    // Rose bush base (stylized)
    const baseGeometry = new THREE.SphereGeometry(0.8, 16, 12);
    const baseMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a1a1a,
      roughness: 0.7,
    });
    const base = new THREE.Mesh(baseGeometry, baseMaterial);
    base.scale.y = 0.6;
    bush.add(base);

    // Black roses (3-5 per bush)
    const roseCount = 3 + Math.floor(Math.random() * 3);
    for (let i = 0; i < roseCount; i++) {
      const rose = this.createRose(product.isEasterEgg ? 0x1a1a1a : 0x0d0d0d);
      rose.position.set(
        (Math.random() - 0.5) * 0.6,
        0.3 + Math.random() * 0.4,
        (Math.random() - 0.5) * 0.6
      );
      rose.scale.setScalar(0.15 + Math.random() * 0.1);
      bush.add(rose);
    }

    // Silver accent rose
    const silverRose = this.createRose(BRAND_COLORS.silver);
    silverRose.position.set(0, 0.6, 0);
    silverRose.scale.setScalar(0.2);
    bush.add(silverRose);

    bush.position.set(...product.position);
    bush.castShadow = true;
    this.scene.add(bush);
    this.roseBushes.set(product.id, bush);

    if (product.isEasterEgg) {
      bush.userData['exclusiveDropUrl'] = product.exclusiveDropUrl;
      this.easterEggs.set(product.id, bush);
    }
  }

  private createRose(color: number): THREE.Group {
    const rose = new THREE.Group();
    const petalCount = 8;
    const petalGeometry = new THREE.SphereGeometry(0.5, 8, 6);
    const petalMaterial = new THREE.MeshStandardMaterial({
      color,
      roughness: 0.4,
      metalness: 0.1,
    });

    for (let i = 0; i < petalCount; i++) {
      const petal = new THREE.Mesh(petalGeometry, petalMaterial);
      const angle = (i / petalCount) * Math.PI * 2;
      const radius = 0.3;
      petal.position.set(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
      petal.scale.set(0.5, 0.3, 0.8);
      petal.rotation.y = angle;
      rose.add(petal);
    }

    // Center
    const centerGeometry = new THREE.SphereGeometry(0.2, 8, 8);
    const centerMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.roseGold,
      roughness: 0.2,
      metalness: 0.8,
      emissive: BRAND_COLORS.roseGold,
      emissiveIntensity: 0.1,
    });
    const center = new THREE.Mesh(centerGeometry, centerMaterial);
    rose.add(center);

    return rose;
  }

  public createArbor(position: [number, number, number], featuredProduct: BlackRoseProduct): void {
    const arbor = new THREE.Group();

    // Arbor frame
    const frameGeometry = new THREE.TorusGeometry(2, 0.05, 8, 32, Math.PI);
    const frameMaterial = new THREE.MeshStandardMaterial({
      color: 0x2a2a2a,
      roughness: 0.3,
      metalness: 0.9,
    });
    const frame = new THREE.Mesh(frameGeometry, frameMaterial);
    frame.rotation.x = Math.PI / 2;
    frame.position.y = 3;
    arbor.add(frame);

    // Pillars
    const pillarGeometry = new THREE.CylinderGeometry(0.05, 0.05, 3, 8);
    const leftPillar = new THREE.Mesh(pillarGeometry, frameMaterial);
    leftPillar.position.set(-2, 1.5, 0);
    arbor.add(leftPillar);

    const rightPillar = new THREE.Mesh(pillarGeometry, frameMaterial);
    rightPillar.position.set(2, 1.5, 0);
    arbor.add(rightPillar);

    arbor.position.set(...position);
    arbor.userData = { productId: featuredProduct.id, product: featuredProduct };
    this.scene.add(arbor);
    this.arbors.push(arbor);
  }

  public setOnProductClick(handler: ProductClickHandler): void {
    this.onProductClick = handler;
  }

  public setOnEasterEgg(handler: EasterEggHandler): void {
    this.onEasterEgg = handler;
  }

  public setOnProductHover(handler: (data: ProductCardData | null) => void): void {
    this.onProductHover = handler;
  }

  private animatePetals(elapsed: number): void {
    for (const petal of this.petals) {
      const initialY = petal.userData['initialY'] as number;
      const speed = petal.userData['speed'] as number;
      const rotationSpeed = petal.userData['rotationSpeed'] as number;
      petal.position.y = initialY + Math.sin(elapsed * speed) * 0.5;
      petal.rotation.x += rotationSpeed;
      petal.rotation.z += rotationSpeed * 0.5;
    }

    // Animate clouds (slow drift across sky)
    for (const cloud of this.clouds) {
      const speedX = cloud.userData['speedX'] as number;
      const speedZ = cloud.userData['speedZ'] as number;
      cloud.position.x += speedX * 0.01;
      cloud.position.z += speedZ * 0.01;

      // Wrap around when clouds move too far
      if (cloud.position.x > 50) cloud.position.x = -50;
      if (cloud.position.x < -50) cloud.position.x = 50;
      if (cloud.position.z > 50) cloud.position.z = -50;
      if (cloud.position.z < -50) cloud.position.z = 50;
    }
  }

  public start(): void {
    // Initialize performance monitoring
    this.perfMonitor.attach(this.renderer, this.scene);
    this.perfMonitor.start();

    const animate = (): void => {
      this.perfMonitor.beginFrame();
      this.animationId = requestAnimationFrame(animate);
      const elapsed = this.clock.getElapsedTime();
      this.animatePetals(elapsed);
      this.controls.update();

      // Composer is always initialized when enableBloom is true (set in constructor)
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

    // Dispose rose bushes (Map)
    this.roseBushes.forEach((bush) => {
      bush.traverse(disposeMesh);
      this.scene.remove(bush);
    });
    this.roseBushes.clear();

    // Dispose petals
    this.petals.forEach((petal) => {
      disposeMesh(petal);
      this.scene.remove(petal);
    });
    this.petals = [];

    // Dispose arbors
    this.arbors.forEach((arbor) => {
      arbor.traverse(disposeMesh);
      this.scene.remove(arbor);
    });
    this.arbors = [];

    // Dispose night sky
    if (this.nightSky) {
      disposeMesh(this.nightSky);
      this.scene.remove(this.nightSky);
      this.nightSky = null;
    }

    // Dispose clouds
    this.clouds.forEach((cloud) => {
      if (cloud.material) {
        cloud.material.dispose();
        if (cloud.material.map) cloud.material.map.dispose();
      }
      this.scene.remove(cloud);
    });
    this.clouds = [];

    // Dispose all remaining scene objects
    this.scene.traverse(disposeMesh);

    // Dispose controls, composer, and renderer
    this.controls.dispose();
    if (this.composer) this.composer.dispose();
    this.renderer.dispose();
    this.renderer.forceContextLoss();

    this.logger.info('BLACK ROSE experience disposed');
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
  public getRenderer(): THREE.WebGLRenderer { return this.renderer; }
}

export default BlackRoseExperience;
