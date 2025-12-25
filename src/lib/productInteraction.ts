/**
 * Product Interaction Handler for Three.js Collections
 * Handles product clicks, camera animations, and visual effects based on inventory
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import * as THREE from 'three';
import { Logger } from '../utils/Logger.js';
import type { ShowroomProduct, InventoryStatus } from '../types/product.js';
import type { InventoryManager } from './inventory.js';

/**
 * Cart manager interface (to be implemented separately)
 */
export interface CartManager {
  addItem(product: ShowroomProduct, quantity: number, options?: AddToCartOptions): Promise<void>;
  getItemCount(): number;
  getTotalPrice(): number;
}

/**
 * Add to cart options
 */
export interface AddToCartOptions {
  size?: string;
  color?: { name: string; hex: string };
}

/**
 * Product panel data
 */
export interface ProductPanelData {
  product: ShowroomProduct;
  inventoryStatus: InventoryStatus | null;
  position: { x: number; y: number };
}

/**
 * Product interaction configuration
 */
export interface ProductInteractionConfig {
  camera: THREE.Camera;
  scene: THREE.Scene;
  cart: CartManager;
  inventory: InventoryManager;
  animationDuration?: number;
  highlightIntensity?: number;
}

/**
 * Product visual effects configuration
 */
export interface ProductVisualEffects {
  glowColor: number;
  glowIntensity: number;
  opacity: number;
  pulseSpeed?: number;
}

/**
 * Default configuration
 */
const DEFAULT_CONFIG = {
  animationDuration: 1000,  // 1 second
  highlightIntensity: 0.3,
};

/**
 * Product interaction handler for Three.js scenes
 */
export class ProductInteractionHandler {
  private logger: Logger;
  private camera: THREE.Camera;
  // Scene stored for future raycasting extensions
  private sceneRef: THREE.Scene;
  private cart: CartManager;
  private inventory: InventoryManager;
  private config: Required<ProductInteractionConfig>;

  // Interaction state
  private productMeshes: Map<string, THREE.Mesh> = new Map();
  private originalMaterials: Map<string, THREE.Material | THREE.Material[]> = new Map();
  private highlightedProduct: string | null = null;
  private isAnimating = false;

  // Callbacks
  private onProductPanelShow: ((data: ProductPanelData) => void) | null = null;
  private onProductPanelHide: (() => void) | null = null;
  private onAddToCart: ((product: ShowroomProduct) => void) | null = null;

  constructor(config: ProductInteractionConfig) {
    this.logger = new Logger('ProductInteractionHandler');
    this.camera = config.camera;
    this.sceneRef = config.scene;
    this.cart = config.cart;
    this.inventory = config.inventory;
    this.config = {
      ...config,
      animationDuration: config.animationDuration || DEFAULT_CONFIG.animationDuration,
      highlightIntensity: config.highlightIntensity || DEFAULT_CONFIG.highlightIntensity,
    };
  }

  /**
   * Get the scene reference for advanced raycasting operations
   */
  public getScene(): THREE.Scene {
    return this.sceneRef;
  }

  /**
   * Setup a product mesh for interaction
   */
  public setupProduct(mesh: THREE.Mesh, productData: ShowroomProduct): void {
    // Store product reference
    mesh.userData['productData'] = productData;
    this.productMeshes.set(productData.id, mesh);

    // Store original material for restoration
    this.originalMaterials.set(productData.id, mesh.material);

    // Subscribe to inventory updates
    this.inventory.subscribe(productData.id, (status) => {
      this.updateProductVisuals(mesh, status);
    });

    // Apply initial visual state based on inventory
    const inventoryStatus = this.inventory.getStatus(productData.id);
    if (inventoryStatus) {
      this.updateProductVisuals(mesh, inventoryStatus);
    }

    this.logger.debug(`Setup product: ${productData.name} (${productData.id})`);
  }

  /**
   * Handle product click
   */
  public handleProductClick(productId: string): void {
    const mesh = this.productMeshes.get(productId);
    if (!mesh) {
      this.logger.warn(`Product mesh not found: ${productId}`);
      return;
    }

    const productData = mesh.userData['productData'] as ShowroomProduct;
    if (!productData) {
      this.logger.warn(`Product data not found: ${productId}`);
      return;
    }

    // Animate camera to product
    this.animateToProduct(mesh).then(() => {
      // Show product panel after animation
      this.showProductPanel(productData);
    }).catch((error) => {
      this.logger.error('Failed to animate to product', error);
    });
  }

  /**
   * Animate camera to focus on product
   */
  public async animateToProduct(mesh: THREE.Mesh): Promise<void> {
    if (this.isAnimating) {
      this.logger.warn('Animation already in progress');
      return;
    }

    this.isAnimating = true;

    return new Promise<void>((resolve) => {
      const startPosition = this.camera.position.clone();
      const startRotation = this.camera.quaternion.clone();

      // Calculate target position (slightly in front and above the product)
      const targetPosition = new THREE.Vector3(
        mesh.position.x + 2,
        mesh.position.y + 1,
        mesh.position.z + 2
      );

      // Calculate target look-at
      const targetLookAt = mesh.position.clone();

      // Create temporary camera for calculating target rotation
      const tempCamera = this.camera.clone();
      tempCamera.position.copy(targetPosition);
      tempCamera.lookAt(targetLookAt);
      const targetRotation = tempCamera.quaternion.clone();

      const startTime = performance.now();
      const duration = this.config.animationDuration;

      const animate = (): void => {
        const elapsed = performance.now() - startTime;
        const t = Math.min(elapsed / duration, 1);

        // Ease-in-out cubic
        const eased = t < 0.5
          ? 4 * t * t * t
          : 1 - Math.pow(-2 * t + 2, 3) / 2;

        // Interpolate position
        this.camera.position.lerpVectors(startPosition, targetPosition, eased);

        // Interpolate rotation
        this.camera.quaternion.slerpQuaternions(startRotation, targetRotation, eased);

        if (t < 1) {
          requestAnimationFrame(animate);
        } else {
          this.isAnimating = false;
          resolve();
        }
      };

      animate();
    });
  }

  /**
   * Show product panel with details
   */
  public showProductPanel(productData: ShowroomProduct): void {
    const inventoryStatus = this.inventory.getStatus(productData.id);

    // Calculate screen position for panel
    const mesh = this.productMeshes.get(productData.id);
    const position = mesh
      ? this.worldToScreen(mesh.position)
      : { x: window.innerWidth / 2, y: window.innerHeight / 2 };

    const panelData: ProductPanelData = {
      product: productData,
      inventoryStatus,
      position,
    };

    if (this.onProductPanelShow) {
      this.onProductPanelShow(panelData);
    }

    this.logger.info(`Showing product panel: ${productData.name}`);
  }

  /**
   * Hide product panel
   */
  public hideProductPanel(): void {
    if (this.onProductPanelHide) {
      this.onProductPanelHide();
    }
    this.logger.info('Hiding product panel');
  }

  /**
   * Add product to cart
   */
  public async addToCart(productId: string, options?: AddToCartOptions): Promise<void> {
    const mesh = this.productMeshes.get(productId);
    if (!mesh) {
      this.logger.warn(`Product mesh not found: ${productId}`);
      return;
    }

    const productData = mesh.userData['productData'] as ShowroomProduct;
    if (!productData) {
      this.logger.warn(`Product data not found: ${productId}`);
      return;
    }

    // Check inventory
    const inventoryStatus = this.inventory.getStatus(productId);
    if (inventoryStatus && inventoryStatus.stockStatus === 'out_of_stock') {
      this.logger.warn(`Product out of stock: ${productData.name}`);
      // Dispatch out-of-stock notification event
      this.dispatchNotification('out_of_stock', {
        productId,
        productName: productData.name,
        message: `${productData.name} is currently out of stock`,
      });
      return;
    }

    try {
      // Add to cart
      await this.cart.addItem(productData, 1, options);

      // Trigger callback
      if (this.onAddToCart) {
        this.onAddToCart(productData);
      }

      // Play success animation
      this.playAddToCartAnimation(mesh);

      this.logger.info(`Added to cart: ${productData.name}`);
    } catch (error) {
      this.logger.error('Failed to add product to cart', error);
      // Dispatch error notification event
      this.dispatchNotification('error', {
        productId,
        productName: productData.name,
        message: `Failed to add ${productData.name} to cart`,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  /**
   * Dispatch notification event for UI components to handle
   */
  private dispatchNotification(
    type: 'out_of_stock' | 'error' | 'success' | 'info',
    detail: Record<string, unknown>
  ): void {
    const event = new CustomEvent('product:notification', {
      detail: {
        type,
        timestamp: Date.now(),
        ...detail,
      },
    });
    window.dispatchEvent(event);
  }

  /**
   * Update product visuals based on inventory status
   */
  public updateProductVisuals(mesh: THREE.Mesh, inventoryStatus: InventoryStatus): void {
    const glowColor = this.inventory.getGlowColor(inventoryStatus);
    const opacity = this.inventory.getOpacity(inventoryStatus);

    // Update material properties
    if (mesh.material instanceof THREE.MeshStandardMaterial) {
      mesh.material.emissive.setHex(glowColor);
      mesh.material.emissiveIntensity = this.config.highlightIntensity;
      mesh.material.opacity = opacity;
      mesh.material.transparent = opacity < 1.0;
      mesh.material.needsUpdate = true;
    } else if (Array.isArray(mesh.material)) {
      for (const material of mesh.material) {
        if (material instanceof THREE.MeshStandardMaterial) {
          material.emissive.setHex(glowColor);
          material.emissiveIntensity = this.config.highlightIntensity;
          material.opacity = opacity;
          material.transparent = opacity < 1.0;
          material.needsUpdate = true;
        }
      }
    }

    this.logger.debug(`Updated visuals for product: ${inventoryStatus.productId}`, {
      stockStatus: inventoryStatus.stockStatus,
      glowColor,
      opacity,
    });
  }

  /**
   * Highlight product on hover
   */
  public highlightProduct(productId: string): void {
    if (this.highlightedProduct === productId) return;

    // Unhighlight previous
    if (this.highlightedProduct) {
      this.unhighlightProduct(this.highlightedProduct);
    }

    const mesh = this.productMeshes.get(productId);
    if (!mesh) return;

    // Apply highlight effect
    if (mesh.material instanceof THREE.MeshStandardMaterial) {
      mesh.material.emissiveIntensity = this.config.highlightIntensity * 2;
      mesh.material.needsUpdate = true;
    }

    this.highlightedProduct = productId;
  }

  /**
   * Remove highlight from product
   */
  public unhighlightProduct(productId: string): void {
    const mesh = this.productMeshes.get(productId);
    if (!mesh) return;

    // Restore normal emissive intensity
    if (mesh.material instanceof THREE.MeshStandardMaterial) {
      mesh.material.emissiveIntensity = this.config.highlightIntensity;
      mesh.material.needsUpdate = true;
    }

    if (this.highlightedProduct === productId) {
      this.highlightedProduct = null;
    }
  }

  /**
   * Play add-to-cart success animation
   */
  private playAddToCartAnimation(mesh: THREE.Mesh): void {
    const startScale = mesh.scale.clone();
    const targetScale = startScale.clone().multiplyScalar(1.2);
    const duration = 300;
    const startTime = performance.now();

    const animate = (): void => {
      const elapsed = performance.now() - startTime;
      const t = Math.min(elapsed / duration, 1);

      // Bounce effect
      const bounce = Math.sin(t * Math.PI);
      mesh.scale.lerpVectors(startScale, targetScale, bounce);

      if (t < 1) {
        requestAnimationFrame(animate);
      } else {
        mesh.scale.copy(startScale);
      }
    };

    animate();
  }

  /**
   * Convert world position to screen position
   */
  private worldToScreen(position: THREE.Vector3): { x: number; y: number } {
    const vector = position.clone();
    vector.project(this.camera);

    const x = (vector.x * 0.5 + 0.5) * window.innerWidth;
    const y = (vector.y * -0.5 + 0.5) * window.innerHeight;

    return { x, y };
  }

  /**
   * Set product panel show callback
   */
  public setOnProductPanelShow(callback: (data: ProductPanelData) => void): void {
    this.onProductPanelShow = callback;
  }

  /**
   * Set product panel hide callback
   */
  public setOnProductPanelHide(callback: () => void): void {
    this.onProductPanelHide = callback;
  }

  /**
   * Set add-to-cart callback
   */
  public setOnAddToCart(callback: (product: ShowroomProduct) => void): void {
    this.onAddToCart = callback;
  }

  /**
   * Get product by ID
   */
  public getProduct(productId: string): ShowroomProduct | null {
    const mesh = this.productMeshes.get(productId);
    if (!mesh) return null;
    return mesh.userData['productData'] as ShowroomProduct || null;
  }

  /**
   * Get all registered products
   */
  public getAllProducts(): ShowroomProduct[] {
    const products: ShowroomProduct[] = [];
    for (const mesh of this.productMeshes.values()) {
      const productData = mesh.userData['productData'] as ShowroomProduct;
      if (productData) {
        products.push(productData);
      }
    }
    return products;
  }

  /**
   * Dispose and cleanup
   */
  public dispose(): void {
    // Restore original materials
    for (const [productId, material] of this.originalMaterials.entries()) {
      const mesh = this.productMeshes.get(productId);
      if (mesh) {
        mesh.material = material;
      }
    }

    this.productMeshes.clear();
    this.originalMaterials.clear();
    this.logger.info('ProductInteractionHandler disposed');
  }
}

export default ProductInteractionHandler;
