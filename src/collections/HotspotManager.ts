/**
 * Hotspot Manager for SkyyRose Collection Experiences
 *
 * Manages interactive product hotspots in 3D scenes with:
 * - Automatic hotspot rendering from JSON configs
 * - Click detection and product selection
 * - Real-time WooCommerce product data integration
 * - Product card display with add-to-cart functionality
 * - Smooth scroll-based camera transitions
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import * as THREE from 'three';
import { Logger } from '../utils/Logger.js';

// ============================================================================
// Types & Interfaces
// ============================================================================

export interface HotspotPosition {
  x: number;
  y: number;
  z: number;
}

export interface HotspotData {
  product_id: number;
  position: HotspotPosition;
  title: string;
  price: number;
  image_url: string;
  woocommerce_url: string;
  collection_slug: string;
  sku?: string;
  excerpt?: string;
}

export interface CameraWaypoint {
  scroll_percent: number;
  camera_position: HotspotPosition;
  camera_target: HotspotPosition;
  duration_ms: number;
}

export interface HotspotConfig {
  collection_type: string;
  collection_name: string;
  experience_url: string;
  hotspots: HotspotData[];
  camera_waypoints: CameraWaypoint[];
  total_products: number;
  scene_bounds: {
    min: HotspotPosition;
    max: HotspotPosition;
  };
}

export interface HotspotManagerOptions {
  configUrl?: string;
  autoLoad?: boolean;
  hotspotRadius?: number;
  hotspotColor?: number;
  emissiveColor?: number;
  emissiveIntensity?: number;
  onProductSelected?: (product: ProductCardData) => void;
  onHotspotCreated?: (hotspot: THREE.Mesh, data: HotspotData) => void;
  onProductSelect?: (product: ProductCardData) => void;
}

export interface ProductCardData extends HotspotData {
  formattedPrice: string;
}

// ============================================================================
// HotspotManager Class
// ============================================================================

export class HotspotManager {
  private logger: Logger;
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;

  // Configuration
  private config: HotspotConfig | null = null;
  private options: Required<HotspotManagerOptions>;

  // Scene objects
  private hotspots: Map<number, THREE.Mesh> = new Map();
  private hotspotData: Map<number, HotspotData> = new Map();
  private raycaster: THREE.Raycaster = new THREE.Raycaster();
  private mouse: THREE.Vector2 = new THREE.Vector2();

  // State
  private isLoaded: boolean = false;
  private isAnimating: boolean = false;

  constructor(
    scene: THREE.Scene,
    camera: THREE.PerspectiveCamera,
    renderer: THREE.WebGLRenderer,
    options: HotspotManagerOptions = {}
  ) {
    this.logger = new Logger('HotspotManager');
    this.scene = scene;
    this.camera = camera;
    this.renderer = renderer;

    // Merge options with defaults
    this.options = {
      configUrl: options.configUrl || '',
      autoLoad: options.autoLoad !== false,
      hotspotRadius: options.hotspotRadius || 0.3,
      hotspotColor: options.hotspotColor || 0xb76e79,
      emissiveColor: options.emissiveColor || 0xb76e79,
      emissiveIntensity: options.emissiveIntensity || 0.5,
      onProductSelected: options.onProductSelected || (() => {}),
      onHotspotCreated: options.onHotspotCreated || (() => {}),
      onProductSelect: options.onProductSelect || (() => {}),
    };

    this.setupEventListeners();

    if (this.options.autoLoad && this.options.configUrl) {
      this.loadConfig(this.options.configUrl);
    }
  }

  /**
   * Load hotspot configuration from JSON file
   */
  async loadConfig(configUrl: string): Promise<HotspotConfig> {
    try {
      this.logger.info(`Loading hotspot config from ${configUrl}`);

      const response = await fetch(configUrl);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      this.config = await response.json();

      // Validate configuration
      if (!this.config) {
        throw new Error('Config is null after loading');
      }

      this.validateConfig(this.config);

      // Render hotspots
      await this.renderHotspots();

      this.isLoaded = true;
      this.logger.info(`✓ Loaded ${this.config.hotspots.length} hotspots`);

      return this.config;
    } catch (error) {
      this.logger.error(`Failed to load hotspot config: ${error}`);
      throw error;
    }
  }

  /**
   * Validate hotspot configuration structure
   */
  private validateConfig(config: any): void {
    if (!config.hotspots || !Array.isArray(config.hotspots)) {
      throw new Error('Invalid config: hotspots must be an array');
    }

    if (!config.camera_waypoints || !Array.isArray(config.camera_waypoints)) {
      throw new Error('Invalid config: camera_waypoints must be an array');
    }

    // Validate each hotspot
    for (const hotspot of config.hotspots) {
      if (!hotspot.position || typeof hotspot.position.x !== 'number') {
        throw new Error(`Invalid hotspot position: ${JSON.stringify(hotspot.position)}`);
      }
      if (typeof hotspot.product_id !== 'number' || hotspot.product_id <= 0) {
        throw new Error(`Invalid product_id: ${hotspot.product_id}`);
      }
      if (typeof hotspot.price !== 'number' || hotspot.price < 0) {
        throw new Error(`Invalid price: ${hotspot.price}`);
      }
    }
  }

  /**
   * Render all hotspots in the scene
   */
  private async renderHotspots(): Promise<void> {
    if (!this.config) {
      throw new Error('Config not loaded');
    }

    for (const hotspotData of this.config.hotspots) {
      try {
        const hotspotMesh = this.createHotspotMesh(hotspotData);
        this.scene.add(hotspotMesh);

        // Store references
        this.hotspots.set(hotspotData.product_id, hotspotMesh);
        this.hotspotData.set(hotspotData.product_id, hotspotData);

        // Callback
        this.options.onHotspotCreated(hotspotMesh, hotspotData);
      } catch (error) {
        this.logger.warn(`Failed to create hotspot for product ${hotspotData.product_id}: ${error}`);
      }
    }
  }

  /**
   * Create a hotspot mesh at the given position
   */
  private createHotspotMesh(data: HotspotData): THREE.Mesh {
    const geometry = new THREE.SphereGeometry(
      this.options.hotspotRadius,
      32,
      32
    );

    const material = new THREE.MeshStandardMaterial({
      color: this.options.hotspotColor,
      emissive: this.options.emissiveColor,
      emissiveIntensity: this.options.emissiveIntensity,
      metalness: 0.5,
      roughness: 0.4,
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(data.position.x, data.position.y, data.position.z);
    mesh.userData = {
      productId: data.product_id,
      isHotspot: true,
    };

    mesh.castShadow = true;
    mesh.receiveShadow = true;

    return mesh;
  }

  /**
   * Setup event listeners for interaction
   */
  private setupEventListeners(): void {
    // Click detection
    this.renderer.domElement.addEventListener('click', (e) => {
      this.onCanvasClick(e);
    });

    // Scroll-based camera transitions
    window.addEventListener('scroll', () => {
      this.updateCameraOnScroll();
    });

    // Hover effects
    this.renderer.domElement.addEventListener('mousemove', (e) => {
      this.onMouseMove(e);
    });
  }

  /**
   * Handle canvas click - detect hotspot selection
   */
  private onCanvasClick(event: MouseEvent): void {
    if (this.hotspots.size === 0 || !this.config) return;

    // Calculate mouse position in normalized device coordinates
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    // Perform raycasting
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(Array.from(this.hotspots.values()));

    if (intersects.length > 0 && intersects[0]) {
      const selectedHotspot = intersects[0].object as THREE.Mesh;
      const productId = selectedHotspot.userData?.['productId'] as number | undefined;

      // Verify product exists in data map
      if (productId && this.hotspotData.has(productId)) {
        this.selectProduct(productId);
      }
    }
  }

  /**
   * Handle mouse move - update hover effects
   */
  private onMouseMove(event: MouseEvent): void {
    if (this.hotspots.size === 0) return;

    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(Array.from(this.hotspots.values()));

    // Reset all hotspots
    for (const hotspot of this.hotspots.values()) {
      const material = hotspot.material as THREE.MeshStandardMaterial;
      material.emissiveIntensity = this.options.emissiveIntensity;
      hotspot.scale.set(1, 1, 1);
    }

    // Highlight hovered hotspot
    if (intersects.length > 0 && intersects[0]) {
      const hoveredHotspot = intersects[0].object as THREE.Mesh;
      const material = hoveredHotspot.material as THREE.MeshStandardMaterial;
      material.emissiveIntensity = 1;
      hoveredHotspot.scale.set(1.3, 1.3, 1.3);

      this.renderer.domElement.style.cursor = 'pointer';
    } else {
      this.renderer.domElement.style.cursor = 'default';
    }
  }

  /**
   * Select a product and trigger callback
   */
  private selectProduct(productId: number): void {
    const productData = this.hotspotData.get(productId);
    if (!productData) return;

    // Highlight selected hotspot
    const hotspot = this.hotspots.get(productId);
    if (hotspot) {
      const material = hotspot.material as THREE.MeshStandardMaterial;
      material.emissiveIntensity = 1.2;
    }

    // Create properly typed product card data
    const cardData: ProductCardData = {
      ...productData,
      formattedPrice: `$${productData.price.toFixed(2)}`,
    };

    // Trigger callback with properly typed data
    this.options.onProductSelected(cardData);

    this.logger.info(`Selected product: ${productData.title}`);
  }

  /**
   * Update camera position based on scroll position
   */
  private updateCameraOnScroll(): void {
    if (!this.config || this.isAnimating) return;
    if (this.config.camera_waypoints.length === 0) return;

    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    const scrollPercent = (window.scrollY / maxScroll) * 100;

    // Find nearest waypoint
    let targetWaypoint = this.config.camera_waypoints[0];
    if (!targetWaypoint) return;

    for (let i = this.config.camera_waypoints.length - 1; i >= 0; i--) {
      const waypoint = this.config.camera_waypoints[i];
      if (waypoint && scrollPercent >= waypoint.scroll_percent) {
        targetWaypoint = waypoint;
        break;
      }
    }

    // Smoothly update camera position
    this.camera.position.lerp(
      new THREE.Vector3(
        targetWaypoint.camera_position.x,
        targetWaypoint.camera_position.y,
        targetWaypoint.camera_position.z
      ),
      0.05 // Lerp factor for smooth transition
    );

    // Look at target
    this.camera.lookAt(
      targetWaypoint.camera_target.x,
      targetWaypoint.camera_target.y,
      targetWaypoint.camera_target.z
    );
  }

  /**
   * Get current configuration
   */
  getConfig(): HotspotConfig | null {
    return this.config;
  }

  /**
   * Get hotspot data by product ID
   */
  getHotspotData(productId: number): HotspotData | undefined {
    return this.hotspotData.get(productId);
  }

  /**
   * Get all hotspot meshes
   */
  getHotspots(): Map<number, THREE.Mesh> {
    return this.hotspots;
  }

  /**
   * Check if hotspots are loaded
   */
  isHotspotsLoaded(): boolean {
    return this.isLoaded;
  }

  /**
   * Set the onProductSelect callback
   */
  setOnProductSelect(callback: (product: ProductCardData) => void): void {
    this.options.onProductSelect = callback;
  }

  /**
   * Cleanup resources
   */
  dispose(): void {
    this.hotspots.forEach((hotspot) => {
      hotspot.geometry.dispose();
      (hotspot.material as THREE.Material).dispose();
      this.scene.remove(hotspot);
    });

    this.hotspots.clear();
    this.hotspotData.clear();

    this.logger.info('HotspotManager disposed');
  }
}

export default HotspotManager;
