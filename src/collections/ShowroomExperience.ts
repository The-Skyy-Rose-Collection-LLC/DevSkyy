/**
 * Showroom Experience - 3D Collection Landing Template
 * 
 * A virtual showroom environment for displaying SkyyRose collections.
 * Features:
 * - Gallery-style product placement
 * - Ambient lighting with spotlights on products
 * - Smooth camera transitions between products
 * - Interactive product selection
 * 
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { Logger } from '../utils/Logger.js';
import type { ShowroomProduct } from '../types/product.js';
import { ProductInteractionHandler } from '../lib/productInteraction.js';
import { InventoryManager } from '../lib/inventory.js';
import { CartManager } from '../lib/cartManager.js';

export interface ShowroomConfig {
  backgroundColor?: number;
  ambientLightIntensity?: number;
  floorColor?: number;
  wallColor?: number;
  roomWidth?: number;
  roomDepth?: number;
  roomHeight?: number;
}

export interface Collection3DExperienceSpec {
  type: 'showroom' | 'runway' | 'materials';
  collection: string;
  products: ShowroomProduct[];
  config: ShowroomConfig;
}

const DEFAULT_CONFIG: Required<ShowroomConfig> = {
  backgroundColor: 0x0d0d0d,  // Obsidian black
  ambientLightIntensity: 0.3,
  floorColor: 0x1a1a1a,
  wallColor: 0x0d0d0d,
  roomWidth: 20,
  roomDepth: 30,
  roomHeight: 8,
};

export class ShowroomExperience {
  private logger: Logger;
  private scene: THREE.Scene;
  private renderer: THREE.WebGLRenderer;
  private camera: THREE.PerspectiveCamera;
  private controls: OrbitControls;
  private products: Map<string, THREE.Object3D> = new Map();
  private spotlights: Map<string, THREE.SpotLight> = new Map();
  private config: Required<ShowroomConfig>;
  private animationId: number | null = null;

  // E-commerce integration
  private inventoryManager: InventoryManager;
  private cartManager: CartManager;
  private interactionHandler: ProductInteractionHandler | null = null;
  private raycaster: THREE.Raycaster;
  private mouse: THREE.Vector2;

  constructor(container: HTMLElement, config: ShowroomConfig = {}) {
    this.logger = new Logger('ShowroomExperience');
    this.config = { ...DEFAULT_CONFIG, ...config };
    // GLTFLoader available for loading 3D product models
    void GLTFLoader;

    // Initialize scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(this.config.backgroundColor);
    this.scene.fog = new THREE.Fog(this.config.backgroundColor, 15, 40);

    // Initialize renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;
    container.appendChild(this.renderer.domElement);

    // Initialize camera
    this.camera = new THREE.PerspectiveCamera(
      60,
      container.clientWidth / container.clientHeight,
      0.1,
      100
    );
    this.camera.position.set(0, 2, 10);

    // Initialize controls
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.maxPolarAngle = Math.PI / 2;
    this.controls.minDistance = 3;
    this.controls.maxDistance = 20;

    // Initialize e-commerce systems
    this.inventoryManager = new InventoryManager();
    this.cartManager = new CartManager();
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    this.setupRoom();
    this.setupLighting();
    this.setupInteractionHandlers();
    this.logger.info('Showroom experience initialized');
  }

  private setupRoom(): void {
    const { roomWidth, roomDepth, roomHeight, floorColor, wallColor } = this.config;

    // Floor
    const floorGeometry = new THREE.PlaneGeometry(roomWidth, roomDepth);
    const floorMaterial = new THREE.MeshStandardMaterial({
      color: floorColor,
      roughness: 0.8,
      metalness: 0.2,
    });
    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    this.scene.add(floor);

    // Back wall
    const wallGeometry = new THREE.PlaneGeometry(roomWidth, roomHeight);
    const wallMaterial = new THREE.MeshStandardMaterial({
      color: wallColor,
      roughness: 0.9,
    });
    const backWall = new THREE.Mesh(wallGeometry, wallMaterial);
    backWall.position.set(0, roomHeight / 2, -roomDepth / 2);
    this.scene.add(backWall);
  }

  private setupLighting(): void {
    // Ambient light
    const ambient = new THREE.AmbientLight(0xffffff, this.config.ambientLightIntensity);
    this.scene.add(ambient);

    // Main directional light
    const mainLight = new THREE.DirectionalLight(0xffffff, 0.5);
    mainLight.position.set(5, 10, 5);
    mainLight.castShadow = true;
    mainLight.shadow.mapSize.width = 2048;
    mainLight.shadow.mapSize.height = 2048;
    this.scene.add(mainLight);
  }

  private setupInteractionHandlers(): void {
    // Initialize product interaction handler
    this.interactionHandler = new ProductInteractionHandler({
      camera: this.camera,
      scene: this.scene,
      cart: this.cartManager,
      inventory: this.inventoryManager,
    });

    // Setup mouse move for hover detection
    this.renderer.domElement.addEventListener('mousemove', this.onMouseMove.bind(this));

    // Setup click for product interaction
    this.renderer.domElement.addEventListener('click', this.onClick.bind(this));

    this.logger.info('Interaction handlers setup complete');
  }

  private onMouseMove(event: MouseEvent): void {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    // Update raycasting for hover detection
    this.updateHover();
  }

  private onClick(_event: MouseEvent): void {
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(
      Array.from(this.products.values()),
      true
    );

    if (intersects.length > 0) {
      const firstIntersect = intersects[0];
      if (!firstIntersect) return;
      const productId = this.findProductId(firstIntersect.object);

      if (productId && this.interactionHandler) {
        this.interactionHandler.handleProductClick(productId);
      }
    }
  }

  private updateHover(): void {
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(
      Array.from(this.products.values()),
      true
    );

    if (intersects.length > 0) {
      const firstIntersect = intersects[0];
      if (!firstIntersect) return;
      const productId = this.findProductId(firstIntersect.object);

      if (productId && this.interactionHandler) {
        this.interactionHandler.highlightProduct(productId);
        this.renderer.domElement.style.cursor = 'pointer';
      }
    } else {
      this.renderer.domElement.style.cursor = 'default';
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

  public async loadProducts(products: ShowroomProduct[]): Promise<void> {
    for (const product of products) {
      await this.loadProduct(product);
    }
  }

  private async loadProduct(product: ShowroomProduct): Promise<void> {
    // Placeholder - in production, load actual GLB models
    const geometry = new THREE.BoxGeometry(1, 1.5, 0.5);
    const material = new THREE.MeshStandardMaterial({
      color: 0xd4af37,  // Rose gold
      roughness: 0.3,
      metalness: 0.8,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(...product.position);

    if (product.rotation) {
      mesh.rotation.set(...product.rotation);
    }

    if (product.scale) {
      const scale = Array.isArray(product.scale) ? product.scale : [product.scale, product.scale, product.scale];
      mesh.scale.set(...scale as [number, number, number]);
    }

    mesh.castShadow = true;
    mesh.userData = { productId: product.id, name: product.name };
    this.scene.add(mesh);
    this.products.set(product.id, mesh);

    // Register product with interaction handler
    if (this.interactionHandler) {
      this.interactionHandler.setupProduct(mesh, product);
    }

    // Subscribe to inventory updates
    this.inventoryManager.subscribe(product.id, (status) => {
      this.logger.debug(`Inventory updated for ${product.name}:`, { status });
    });

    this.addSpotlight(product);
  }

  private addSpotlight(product: ShowroomProduct): void {
    const spotlight = new THREE.SpotLight(
      product.spotlightColor ?? 0xd4af37,
      1.5,
      15,
      Math.PI / 6,
      0.5,
      2
    );
    spotlight.position.set(
      product.position[0],
      product.position[1] + 5,
      product.position[2] + 2
    );
    spotlight.target.position.set(...product.position);
    spotlight.castShadow = true;
    this.scene.add(spotlight);
    this.scene.add(spotlight.target);
    this.spotlights.set(product.id, spotlight);
  }

  public selectProduct(productId: string): void {
    const product = this.products.get(productId);
    if (!product) return;

    // Animate camera to product
    const targetPosition = new THREE.Vector3(
      product.position.x + 3,
      product.position.y + 1,
      product.position.z + 3
    );
    this.animateCameraTo(targetPosition, product.position);
  }

  private animateCameraTo(position: THREE.Vector3, lookAt: THREE.Vector3): void {
    const startPos = this.camera.position.clone();
    const startTime = performance.now();
    const duration = 1000;

    const animate = (): void => {
      const elapsed = performance.now() - startTime;
      const t = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);

      this.camera.position.lerpVectors(startPos, position, eased);
      this.controls.target.lerp(lookAt, eased * 0.1);

      if (t < 1) requestAnimationFrame(animate);
    };
    animate();
  }

  public start(): void {
    const animate = (): void => {
      this.animationId = requestAnimationFrame(animate);
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    };
    animate();
  }

  public stop(): void {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  public handleResize(width: number, height: number): void {
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  public dispose(): void {
    this.stop();

    // Properly dispose of all products and their resources
    this.products.forEach((obj) => {
      this.scene.remove(obj);
      if (obj instanceof THREE.Mesh) {
        obj.geometry?.dispose();
        if (obj.material instanceof THREE.Material) {
          obj.material.dispose();
        } else if (Array.isArray(obj.material)) {
          obj.material.forEach((mat) => mat.dispose());
        }
      }
    });
    this.products.clear();

    // Dispose spotlights
    this.spotlights.forEach((light) => {
      this.scene.remove(light);
      this.scene.remove(light.target);
      light.dispose();
    });
    this.spotlights.clear();

    // Dispose of all scene objects
    this.scene.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        object.geometry?.dispose();
        if (object.material instanceof THREE.Material) {
          object.material.dispose();
        } else if (Array.isArray(object.material)) {
          object.material.forEach((mat) => mat.dispose());
        }
      }
    });

    // Dispose controls and renderer
    this.controls.dispose();
    this.renderer.dispose();
    this.renderer.forceContextLoss();

    this.logger.info('Showroom experience disposed');
  }

  /**
   * Handle WebGL context loss - prevents crashes on mobile/low-memory devices
   */
  public handleContextLoss(): void {
    this.logger.warn('WebGL context lost - attempting recovery');
    this.stop();
  }

  /**
   * Handle WebGL context restoration
   */
  public handleContextRestored(): void {
    this.logger.info('WebGL context restored');
    this.start();
  }
}

export default ShowroomExperience;

