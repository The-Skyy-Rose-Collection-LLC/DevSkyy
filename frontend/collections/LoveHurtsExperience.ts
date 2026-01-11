/**
 * LOVE HURTS Collection - 3D Immersive Experience
 *
 * Enchanted castle inspired by Beauty and the Beast aesthetic.
 * Dramatic candlelight, stained glass reflections, magical particle effects.
 *
 * Clickable Assets:
 * - Enchanted rose under glass dome (hero product)
 * - Castle mirrors revealing product lookbooks
 * - Floating candelabras as category navigation
 * - Interactive ballroom floor with product spotlights
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { Logger } from '../utils/Logger';
import { HotspotManager } from './HotspotManager';
import { getModelLoader, ModelLoadError, type LoadedModel } from '../lib/ModelAssetLoader';
import { getPerformanceMonitor, type PerformanceMetrics } from '../lib/ThreePerformanceMonitor';

// ============================================================================
// Types & Interfaces
// ============================================================================

export interface LoveHurtsProduct {
  id: string;
  name: string;
  price: number;
  modelUrl: string;
  thumbnailUrl: string;
  displayType: 'hero' | 'mirror' | 'floor';
  position?: [number, number, number];
  lookbookImages?: string[];
}

export interface LoveHurtsConfig {
  backgroundColor?: number;
  candlelightColor?: number;
  candlelightIntensity?: number;
  particleCount?: number;
  enableBloom?: boolean;
  bloomStrength?: number;
  stainedGlassColors?: number[];
}

export type HeroInteractionHandler = () => void;
export type MirrorClickHandler = (productId: string, lookbookImages: string[]) => void;
export type FloorSpotlightHandler = (productId: string) => void;

// ============================================================================
// Constants
// ============================================================================

const BRAND_COLORS = {
  roseGold: 0xd4af37,
  obsidian: 0x0d0d0d,
  crimson: 0xdc143c,
  ivory: 0xf5f5f0,
  candleGlow: 0xff9933,
  candlelight: 0xff9933,
  magicPurple: 0x9b59b6,
  enchantedBlue: 0x3498db,
};

const DEFAULT_CONFIG: Required<LoveHurtsConfig> = {
  backgroundColor: 0x0a0510,
  candlelightColor: 0xff9933,
  candlelightIntensity: 0.8,
  particleCount: 100,
  enableBloom: true,
  bloomStrength: 0.6,
  stainedGlassColors: [0x9b59b6, 0x3498db, 0xe74c3c, 0xf1c40f],
};

// ============================================================================
// Main Experience Class
// ============================================================================

export class LoveHurtsExperience {
  private logger: Logger;
  private container: HTMLElement;
  private config: Required<LoveHurtsConfig>;

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
  private enchantedRose: THREE.Group | null = null;
  private glassDome: THREE.Mesh | null = null;
  private mirrors: Map<string, THREE.Group> = new Map();
  private candelabras: THREE.Group[] = [];
  private floorSpotlights: Map<string, THREE.Group> = new Map();
  private particles: THREE.Points | null = null;
  private stainedGlass: THREE.Group[] = [];

  // State
  private animationId: number | null = null;
  private clock: THREE.Clock;
  private raycaster: THREE.Raycaster;
  private mouse: THREE.Vector2;
  private hotspotManager: HotspotManager | null = null;

  // Callbacks
  private onHeroInteraction: HeroInteractionHandler | null = null;
  private onMirrorClick: MirrorClickHandler | null = null;
  private onFloorSpotlight: FloorSpotlightHandler | null = null;

  constructor(container: HTMLElement, config: LoveHurtsConfig = {}) {
    this.logger = new Logger('LoveHurtsExperience');
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

    this.setupCastleEnvironment();
    this.setupLighting();
    this.createEnchantedRose();
    this.createMagicParticles();

    // Initialize hotspot system
    this.initializeHotspots();

    this.setupEventListeners();

    this.logger.info('LOVE HURTS experience initialized');
  }

  private createScene(): THREE.Scene {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(this.config.backgroundColor);
    scene.fog = new THREE.FogExp2(this.config.backgroundColor, 0.015);
    return scene;
  }

  private createRenderer(): THREE.WebGLRenderer {
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.7;
    this.container.appendChild(renderer.domElement);
    return renderer;
  }

  private createCamera(): THREE.PerspectiveCamera {
    const aspect = this.container.clientWidth / this.container.clientHeight;
    const camera = new THREE.PerspectiveCamera(55, aspect, 0.1, 100);
    camera.position.set(0, 4, 12);
    camera.lookAt(0, 2, 0);
    return camera;
  }

  private createControls(): OrbitControls {
    const controls = new OrbitControls(this.camera, this.renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2;
    controls.minDistance = 6;
    controls.maxDistance = 20;
    controls.target.set(0, 2, 0);
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

  private setupCastleEnvironment(): void {
    // Ballroom floor - polished marble
    const floorGeometry = new THREE.CircleGeometry(20, 64);
    const floorMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a1520,
      roughness: 0.1,
      metalness: 0.8,
    });
    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    this.scene.add(floor);

    // Floor pattern - rose gold inlay
    const inlayGeometry = new THREE.RingGeometry(5, 5.2, 64);
    const inlayMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.roseGold,
      emissive: BRAND_COLORS.roseGold,
      emissiveIntensity: 0.1,
    });
    const inlay = new THREE.Mesh(inlayGeometry, inlayMaterial);
    inlay.rotation.x = -Math.PI / 2;
    inlay.position.y = 0.01;
    this.scene.add(inlay);

    // Castle walls (curved backdrop)
    const wallGeometry = new THREE.CylinderGeometry(18, 18, 15, 32, 1, true);
    const wallMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a1018,
      side: THREE.BackSide,
      roughness: 0.9,
    });
    const walls = new THREE.Mesh(wallGeometry, wallMaterial);
    walls.position.y = 7.5;
    this.scene.add(walls);

    // Create stained glass windows
    this.createStainedGlassWindows();

    // Create candelabras
    this.createCandelabras();
  }

  private setupLighting(): void {
    // Dim ambient
    const ambient = new THREE.AmbientLight(0x1a1020, 0.2);
    this.scene.add(ambient);

    // Candlelight point lights
    const candlePositions = [
      [-6, 3, -6], [6, 3, -6], [-6, 3, 6], [6, 3, 6],
      [-8, 4, 0], [8, 4, 0], [0, 4, -8],
    ];
    candlePositions.forEach((pos) => {
      const candle = new THREE.PointLight(
        this.config.candlelightColor ?? DEFAULT_CONFIG.candlelightColor,
        this.config.candlelightIntensity ?? DEFAULT_CONFIG.candlelightIntensity,
        15,
        2
      );
      candle.position.set(pos[0] ?? 0, pos[1] ?? 0, pos[2] ?? 0);
      candle.castShadow = true;
      this.scene.add(candle);
    });

    // Spotlight on enchanted rose
    const heroSpot = new THREE.SpotLight(BRAND_COLORS.magicPurple, 2, 15, Math.PI / 8, 0.5);
    heroSpot.position.set(0, 8, 0);
    heroSpot.target.position.set(0, 2, 0);
    heroSpot.castShadow = true;
    this.scene.add(heroSpot);
    this.scene.add(heroSpot.target);
  }

  private createStainedGlassWindows(): void {
    const windowPositions = [
      { angle: 0, y: 8 },
      { angle: Math.PI / 2, y: 8 },
      { angle: Math.PI, y: 8 },
      { angle: (3 * Math.PI) / 2, y: 8 },
    ];

    windowPositions.forEach((pos, i) => {
      const window = new THREE.Group();

      // Window frame
      const frameGeometry = new THREE.RingGeometry(1.5, 1.8, 6);
      const frameMaterial = new THREE.MeshStandardMaterial({
        color: 0x2a2020,
        roughness: 0.3,
        metalness: 0.9,
      });
      const frame = new THREE.Mesh(frameGeometry, frameMaterial);
      window.add(frame);

      // Glass panels
      const glassGeometry = new THREE.CircleGeometry(1.5, 6);
      const glassColors = this.config.stainedGlassColors ?? DEFAULT_CONFIG.stainedGlassColors;
      const glassColor = glassColors[i % glassColors.length] ?? 0x9b59b6;
      const glassMaterial = new THREE.MeshStandardMaterial({
        color: glassColor,
        transparent: true,
        opacity: 0.6,
        emissive: glassColor,
        emissiveIntensity: 0.3,
        side: THREE.DoubleSide,
      });
      const glass = new THREE.Mesh(glassGeometry, glassMaterial);
      window.add(glass);

      const radius = 16;
      window.position.set(
        Math.cos(pos.angle) * radius,
        pos.y,
        Math.sin(pos.angle) * radius
      );
      window.lookAt(0, pos.y, 0);
      this.scene.add(window);
      this.stainedGlass.push(window);
    });
  }

  private createCandelabras(): void {
    const positions = [[-5, 0, -5], [5, 0, -5], [-5, 0, 5], [5, 0, 5]];

    positions.forEach(([x, y, z], i) => {
      const candelabra = new THREE.Group();

      // Stand
      const standGeometry = new THREE.CylinderGeometry(0.1, 0.2, 3, 8);
      const standMaterial = new THREE.MeshStandardMaterial({
        color: BRAND_COLORS.roseGold,
        roughness: 0.2,
        metalness: 0.9,
      });
      const stand = new THREE.Mesh(standGeometry, standMaterial);
      stand.position.y = 1.5;
      candelabra.add(stand);

      // Candle flames (emissive spheres)
      for (let j = 0; j < 3; j++) {
        const flameGeometry = new THREE.SphereGeometry(0.08, 8, 8);
        const flameMaterial = new THREE.MeshStandardMaterial({
          color: BRAND_COLORS.candleGlow,
          emissive: BRAND_COLORS.candleGlow,
          emissiveIntensity: 1.0,
        });
        const flame = new THREE.Mesh(flameGeometry, flameMaterial);
        flame.position.set((j - 1) * 0.3, 3.2, 0);
        flame.userData = { flameIndex: j, baseY: 3.2 };
        candelabra.add(flame);
      }

      candelabra.position.set(x ?? 0, y ?? 0, z ?? 0);
      candelabra.userData['category'] = ['tops', 'dresses', 'bottoms', 'accessories'][i];
      this.scene.add(candelabra);
      this.candelabras.push(candelabra);
    });
  }

  private createEnchantedRose(): void {
    this.enchantedRose = new THREE.Group();

    // Pedestal
    const pedestalGeometry = new THREE.CylinderGeometry(0.6, 0.8, 0.5, 16);
    const pedestalMaterial = new THREE.MeshStandardMaterial({
      color: 0x2a2020,
      roughness: 0.3,
      metalness: 0.8,
    });
    const pedestal = new THREE.Mesh(pedestalGeometry, pedestalMaterial);
    pedestal.position.y = 0.25;
    this.enchantedRose.add(pedestal);

    // Rose stem
    const stemGeometry = new THREE.CylinderGeometry(0.03, 0.03, 1.2, 8);
    const stemMaterial = new THREE.MeshStandardMaterial({ color: 0x2d4a2d });
    const stem = new THREE.Mesh(stemGeometry, stemMaterial);
    stem.position.y = 1.1;
    this.enchantedRose.add(stem);

    // Rose bloom
    const roseBloom = this.createMagicRose();
    roseBloom.position.y = 1.8;
    roseBloom.scale.setScalar(0.3);
    this.enchantedRose.add(roseBloom);

    // Glass dome
    const domeGeometry = new THREE.SphereGeometry(1.2, 32, 24, 0, Math.PI * 2, 0, Math.PI / 2);
    const domeMaterial = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.15,
      roughness: 0,
      metalness: 0.1,
      side: THREE.DoubleSide,
    });
    this.glassDome = new THREE.Mesh(domeGeometry, domeMaterial);
    this.glassDome.position.y = 0.5;
    this.enchantedRose.add(this.glassDome);

    this.enchantedRose.position.set(0, 0, 0);
    this.enchantedRose.userData = { type: 'hero' };
    this.scene.add(this.enchantedRose);
  }

  private createMagicRose(): THREE.Group {
    const rose = new THREE.Group();
    const petalGeometry = new THREE.SphereGeometry(0.5, 8, 6);
    const petalMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.crimson,
      roughness: 0.3,
      emissive: BRAND_COLORS.crimson,
      emissiveIntensity: 0.3,
    });

    for (let i = 0; i < 8; i++) {
      const petal = new THREE.Mesh(petalGeometry, petalMaterial);
      const angle = (i / 8) * Math.PI * 2;
      petal.position.set(Math.cos(angle) * 0.35, 0, Math.sin(angle) * 0.35);
      petal.scale.set(0.6, 0.4, 1);
      petal.rotation.y = angle;
      rose.add(petal);
    }

    const centerGeometry = new THREE.SphereGeometry(0.2, 8, 8);
    const centerMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.roseGold,
      emissive: BRAND_COLORS.roseGold,
      emissiveIntensity: 0.5,
    });
    rose.add(new THREE.Mesh(centerGeometry, centerMaterial));

    return rose;
  }

  private createMagicParticles(): void {
    const count = this.config.particleCount ?? 100;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 25;
      positions[i * 3 + 1] = Math.random() * 10;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 25;

      // Magic colors - purple/blue/gold
      const colorChoice = Math.random();
      if (colorChoice < 0.33) {
        colors[i * 3] = 0.6; colors[i * 3 + 1] = 0.35; colors[i * 3 + 2] = 0.71;
      } else if (colorChoice < 0.66) {
        colors[i * 3] = 0.2; colors[i * 3 + 1] = 0.6; colors[i * 3 + 2] = 0.85;
      } else {
        colors[i * 3] = 0.83; colors[i * 3 + 1] = 0.69; colors[i * 3 + 2] = 0.22;
      }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 0.08,
      vertexColors: true,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending,
    });

    this.particles = new THREE.Points(geometry, material);
    this.scene.add(this.particles);
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
      const configUrl = '/wp-content/uploads/hotspots/love-hurts-hotspots.json';
      await this.hotspotManager.loadConfig(configUrl);

      // Set product selection callback
      this.hotspotManager.setOnProductSelect((productData) => {
        // Find matching product in mirrors or floor spotlights
        for (const [id, mirror] of this.mirrors) {
          if (parseInt(id) === productData.product_id) {
            const lookbookImages = mirror.userData['lookbookImages'] as string[] | undefined || [];
            if (this.onMirrorClick) {
              this.onMirrorClick(id, lookbookImages);
            }
            return;
          }
        }

        for (const [id] of this.floorSpotlights) {
          if (parseInt(id) === productData.product_id) {
            if (this.onFloorSpotlight) {
              this.onFloorSpotlight(id);
            }
            return;
          }
        }
      });

      this.logger.info('Hotspots initialized for LOVE HURTS collection');
    } catch (error) {
      this.logger.warn(`Failed to initialize hotspots: ${error instanceof Error ? error.message : String(error)}`);
      // Continue without hotspots - they're optional
    }
  }

  private setupEventListeners(): void {
    this.container.addEventListener('click', this.onClick.bind(this));
    window.addEventListener('resize', this.onResize.bind(this));
  }

  private onClick(event: MouseEvent): void {
    const rect = this.container.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);

    // Check hero rose
    if (this.enchantedRose) {
      const heroIntersects = this.raycaster.intersectObject(this.enchantedRose, true);
      if (heroIntersects.length > 0 && this.onHeroInteraction) {
        this.onHeroInteraction();
        return;
      }
    }

    // Check mirrors
    const mirrorObjects = Array.from(this.mirrors.values());
    const mirrorIntersects = this.raycaster.intersectObjects(mirrorObjects, true);
    const firstMirrorIntersect = mirrorIntersects[0];
    if (firstMirrorIntersect && this.onMirrorClick) {
      let obj: THREE.Object3D | null = firstMirrorIntersect.object;
      while (obj && !obj.userData['productId']) obj = obj.parent;
      if (obj) {
        const productId = obj.userData['productId'] as string | undefined;
        if (productId) {
          const lookbookImages = (obj.userData['lookbookImages'] as string[]) || [];
          this.onMirrorClick(productId, lookbookImages);
        }
      }
    }

    // Check floor spotlights
    const floorObjects = Array.from(this.floorSpotlights.values());
    const floorIntersects = this.raycaster.intersectObjects(floorObjects, true);
    const firstFloorIntersect = floorIntersects[0];
    if (firstFloorIntersect && this.onFloorSpotlight) {
      let obj: THREE.Object3D | null = firstFloorIntersect.object;
      while (obj && !obj.userData['productId']) obj = obj.parent;
      if (obj) {
        const productId = obj.userData['productId'] as string | undefined;
        if (productId) {
          this.onFloorSpotlight(productId);
        }
      }
    }
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

  public async loadProducts(products: LoveHurtsProduct[]): Promise<void> {
    for (const product of products) {
      if (product.displayType === 'mirror') {
        this.createMirror(product);
      } else if (product.displayType === 'floor') {
        this.createFloorSpotlight(product);
      }
    }
    this.logger.info(`Loaded ${products.length} products`);
  }

  private createMirror(product: LoveHurtsProduct): void {
    const mirror = new THREE.Group();
    mirror.userData = {
      productId: product.id,
      lookbookImages: product.lookbookImages,
    };

    // Mirror frame
    const frameGeometry = new THREE.BoxGeometry(2, 3, 0.2);
    const frameMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.roseGold,
      roughness: 0.2,
      metalness: 0.9,
    });
    const frame = new THREE.Mesh(frameGeometry, frameMaterial);
    frame.position.y = 2;
    mirror.add(frame);

    // Mirror surface
    const surfaceGeometry = new THREE.PlaneGeometry(1.6, 2.6);
    const surfaceMaterial = new THREE.MeshStandardMaterial({
      color: 0x2a2030,
      roughness: 0.05,
      metalness: 1.0,
    });
    const surface = new THREE.Mesh(surfaceGeometry, surfaceMaterial);
    surface.position.set(0, 2, 0.11);
    mirror.add(surface);

    mirror.position.set(...(product.position || [0, 0, 0]));
    this.scene.add(mirror);
    this.mirrors.set(product.id, mirror);
  }

  private createFloorSpotlight(product: LoveHurtsProduct): void {
    const spotlight = new THREE.Group();
    spotlight.userData['productId'] = product.id;

    // Light ring on floor
    const ringGeometry = new THREE.RingGeometry(0.8, 1, 32);
    const ringMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.roseGold,
      emissive: BRAND_COLORS.roseGold,
      emissiveIntensity: 0.5,
      side: THREE.DoubleSide,
    });
    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.02;
    spotlight.add(ring);

    // Product placeholder
    const productGeometry = new THREE.CapsuleGeometry(0.3, 0.8, 8, 16);
    const productMaterial = new THREE.MeshStandardMaterial({
      color: BRAND_COLORS.crimson,
      roughness: 0.4,
    });
    const productMesh = new THREE.Mesh(productGeometry, productMaterial);
    productMesh.position.y = 0.7;
    productMesh.castShadow = true;
    spotlight.add(productMesh);

    spotlight.position.set(...(product.position || [0, 0, 0]));
    this.scene.add(spotlight);
    this.floorSpotlights.set(product.id, spotlight);
  }

  public setOnHeroInteraction(handler: HeroInteractionHandler): void {
    this.onHeroInteraction = handler;
  }

  public setOnMirrorClick(handler: MirrorClickHandler): void {
    this.onMirrorClick = handler;
  }

  public setOnFloorSpotlight(handler: FloorSpotlightHandler): void {
    this.onFloorSpotlight = handler;
  }

  public start(): void {
    // Initialize performance monitoring
    this.perfMonitor.attach(this.renderer, this.scene);
    this.perfMonitor.start();

    const animate = (): void => {
      this.perfMonitor.beginFrame();
      this.animationId = requestAnimationFrame(animate);
      const elapsed = this.clock.getElapsedTime();

      // Animate enchanted rose glow
      if (this.enchantedRose) {
        this.enchantedRose.rotation.y = elapsed * 0.1;
      }

      // Animate candle flames
      this.candelabras.forEach((c) => {
        c.children.forEach((child) => {
          const flameIndex = child.userData['flameIndex'] as number;
          const baseY = child.userData['baseY'] as number;
          if (flameIndex !== undefined && baseY !== undefined) {
            child.position.y = baseY + Math.sin(elapsed * 5 + flameIndex) * 0.02;
            child.scale.setScalar(0.9 + Math.sin(elapsed * 8 + flameIndex) * 0.1);
          }
        });
      });

      // Animate particles
      if (this.particles) {
        const positionAttr = this.particles.geometry.attributes['position'];
        if (positionAttr?.array) {
          const positions = positionAttr.array as Float32Array;
          const len = positions.length;
          for (let i = 0; i < len / 3; i++) {
            const idx = i * 3 + 1;
            const currentY = positions[idx];
            if (currentY !== undefined) {
              positions[idx] = currentY + 0.01;
              if (positions[idx]! > 12) positions[idx] = 0;
            }
          }
          positionAttr.needsUpdate = true;
        }
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

    // Dispose enchanted rose
    if (this.enchantedRose) {
      this.enchantedRose.traverse(disposeMesh);
      this.scene.remove(this.enchantedRose);
    }

    // Dispose mirrors (Map)
    this.mirrors.forEach((m) => {
      m.traverse(disposeMesh);
      this.scene.remove(m);
    });
    this.mirrors.clear();

    // Dispose candelabras (Array)
    this.candelabras.forEach((c) => {
      c.traverse(disposeMesh);
      this.scene.remove(c);
    });
    this.candelabras = [];

    // Dispose floor spotlights (Map of Groups, not SpotLights)
    this.floorSpotlights.forEach((s) => {
      s.traverse(disposeMesh);
      this.scene.remove(s);
    });
    this.floorSpotlights.clear();

    // Dispose stained glass (Array)
    this.stainedGlass.forEach((s) => {
      s.traverse(disposeMesh);
      this.scene.remove(s);
    });
    this.stainedGlass = [];

    // Dispose particles
    if (this.particles) {
      if (this.particles instanceof THREE.Points) {
        this.particles.geometry?.dispose();
        if (this.particles.material instanceof THREE.Material) {
          this.particles.material.dispose();
        }
      }
      this.scene.remove(this.particles);
    }

    // Dispose all remaining scene objects
    this.scene.traverse(disposeMesh);

    // Dispose controls, composer, and renderer
    this.controls.dispose();
    if (this.composer) this.composer.dispose();
    this.renderer.dispose();
    this.renderer.forceContextLoss();

    this.logger.info('LOVE HURTS experience disposed');
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

export default LoveHurtsExperience;
