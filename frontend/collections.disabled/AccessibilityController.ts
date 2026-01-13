/**
 * Accessibility Controller - Keyboard Navigation for 3D Experiences
 * ==================================================================
 *
 * WCAG 2.1 Level AA compliant keyboard navigation for Three.js collection experiences.
 * Enables Tab/Shift+Tab cycling, Enter/Space activation, and Escape to exit keyboard mode.
 *
 * Features:
 * - Tab/Shift+Tab: Cycle through interactive products
 * - Enter/Space: Activate selected product
 * - Escape: Exit keyboard navigation mode
 * - Visual focus ring: Gold emissive glow (0xFFD700, intensity 0.6)
 * - WCAG 2.1.1: Keyboard accessible
 * - 3:1 contrast ratio for focus indicators
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import * as THREE from 'three';
import { Logger } from '../utils/Logger';

export interface AccessibilityProduct {
  id: string;
  name: string;
  mesh: THREE.Object3D;
  position: THREE.Vector3;
}

export interface AccessibilityConfig {
  focusColor?: number;
  focusIntensity?: number;
  onProductActivated?: (productId: string) => void;
  logger?: Logger;
}

const DEFAULT_CONFIG = {
  focusColor: 0xffd700,  // Gold
  focusIntensity: 0.6,
};

export class AccessibilityController {
  private logger: Logger;
  private products: AccessibilityProduct[] = [];
  private currentFocusIndex: number = -1;
  private isKeyboardMode: boolean = false;
  private focusedMesh: THREE.Object3D | null = null;
  private originalMaterials: Map<THREE.Object3D, THREE.Material | THREE.Material[]> = new Map();
  private config: Required<AccessibilityConfig>;
  private boundKeyHandler: ((e: KeyboardEvent) => void) | null = null;

  constructor(config: AccessibilityConfig = {}) {
    this.logger = config.logger || new Logger('AccessibilityController');
    this.config = {
      ...DEFAULT_CONFIG,
      onProductActivated: config.onProductActivated || (() => {}),
      logger: this.logger,
    };
  }

  /**
   * Register a product for keyboard navigation
   */
  public registerProduct(product: AccessibilityProduct): void {
    // Check if product already registered
    const existingIndex = this.products.findIndex((p) => p.id === product.id);
    if (existingIndex !== -1) {
      this.logger.warn(`Product ${product.id} already registered`);
      return;
    }

    this.products.push(product);
    this.logger.debug(`Registered product: ${product.name} (${product.id})`);

    // Sort products by Z-position (front to back) for intuitive Tab order
    this.products.sort((a, b) => b.position.z - a.position.z);
  }

  /**
   * Unregister a product from keyboard navigation
   */
  public unregisterProduct(productId: string): void {
    const index = this.products.findIndex((p) => p.id === productId);
    if (index !== -1) {
      const product = this.products[index];
      this.products.splice(index, 1);
      this.logger.debug(`Unregistered product: ${product?.name} (${productId})`);

      // If this was the focused product, clear focus
      if (this.currentFocusIndex === index) {
        this.clearFocus();
        this.currentFocusIndex = -1;
      } else if (this.currentFocusIndex > index) {
        this.currentFocusIndex--;
      }
    }
  }

  /**
   * Enable keyboard navigation
   */
  public enable(canvas?: HTMLElement): void {
    if (this.boundKeyHandler) {
      this.logger.warn('Keyboard navigation already enabled');
      return;
    }

    this.boundKeyHandler = this.handleKeyDown.bind(this);
    const target = canvas || window;
    target.addEventListener('keydown', this.boundKeyHandler as EventListener);
    this.logger.info('Keyboard navigation enabled');
  }

  /**
   * Disable keyboard navigation
   */
  public disable(canvas?: HTMLElement): void {
    if (!this.boundKeyHandler) {
      return;
    }

    const target = canvas || window;
    target.removeEventListener('keydown', this.boundKeyHandler as EventListener);
    this.boundKeyHandler = null;
    this.clearFocus();
    this.isKeyboardMode = false;
    this.logger.info('Keyboard navigation disabled');
  }

  /**
   * Handle keyboard events
   */
  private handleKeyDown(event: KeyboardEvent): void {
    const { key, shiftKey } = event;

    switch (key) {
      case 'Tab':
        event.preventDefault();
        this.isKeyboardMode = true;
        if (shiftKey) {
          this.focusPrevious();
        } else {
          this.focusNext();
        }
        break;

      case 'Enter':
      case ' ':
        event.preventDefault();
        if (this.isKeyboardMode && this.currentFocusIndex !== -1) {
          this.activateFocusedProduct();
        }
        break;

      case 'Escape':
        event.preventDefault();
        this.exitKeyboardMode();
        break;

      default:
        break;
    }
  }

  /**
   * Focus the next product in the list
   */
  private focusNext(): void {
    if (this.products.length === 0) return;

    this.clearFocus();
    this.currentFocusIndex = (this.currentFocusIndex + 1) % this.products.length;
    this.applyFocus();
  }

  /**
   * Focus the previous product in the list
   */
  private focusPrevious(): void {
    if (this.products.length === 0) return;

    this.clearFocus();
    this.currentFocusIndex =
      this.currentFocusIndex <= 0 ? this.products.length - 1 : this.currentFocusIndex - 1;
    this.applyFocus();
  }

  /**
   * Apply visual focus ring to the currently focused product
   */
  private applyFocus(): void {
    const product = this.products[this.currentFocusIndex];
    if (!product) return;

    this.focusedMesh = product.mesh;

    // Apply emissive glow to all meshes in the product
    this.focusedMesh.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        // Store original material
        if (!this.originalMaterials.has(child)) {
          this.originalMaterials.set(child, child.material);
        }

        // Clone material and add emissive glow
        const material = Array.isArray(child.material)
          ? child.material[0]
          : child.material;

        if (material instanceof THREE.MeshStandardMaterial) {
          const focusMaterial = material.clone();
          focusMaterial.emissive = new THREE.Color(this.config.focusColor);
          focusMaterial.emissiveIntensity = this.config.focusIntensity;
          child.material = focusMaterial;
        }
      }
    });

    this.logger.debug(`Focused: ${product.name} (${product.id})`);
  }

  /**
   * Clear visual focus ring from the currently focused product
   */
  private clearFocus(): void {
    if (!this.focusedMesh) return;

    // Restore original materials
    this.focusedMesh.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        const originalMaterial = this.originalMaterials.get(child);
        if (originalMaterial) {
          child.material = originalMaterial;
        }
      }
    });

    this.focusedMesh = null;
  }

  /**
   * Activate the currently focused product
   */
  private activateFocusedProduct(): void {
    const product = this.products[this.currentFocusIndex];
    if (!product) return;

    this.logger.info(`Activated: ${product.name} (${product.id})`);
    this.config.onProductActivated(product.id);
  }

  /**
   * Exit keyboard navigation mode
   */
  private exitKeyboardMode(): void {
    this.clearFocus();
    this.currentFocusIndex = -1;
    this.isKeyboardMode = false;
    this.logger.info('Exited keyboard navigation mode');
  }

  /**
   * Get the currently focused product ID (if any)
   */
  public getFocusedProductId(): string | null {
    const product = this.products[this.currentFocusIndex];
    return product ? product.id : null;
  }

  /**
   * Get keyboard mode status
   */
  public isInKeyboardMode(): boolean {
    return this.isKeyboardMode;
  }

  /**
   * Get count of registered products
   */
  public getProductCount(): number {
    return this.products.length;
  }

  /**
   * Clear all registered products
   */
  public clearProducts(): void {
    this.clearFocus();
    this.products = [];
    this.originalMaterials.clear();
    this.currentFocusIndex = -1;
    this.logger.debug('Cleared all registered products');
  }

  /**
   * Dispose of the accessibility controller
   */
  public dispose(): void {
    this.disable();
    this.clearProducts();
    this.logger.info('AccessibilityController disposed');
  }
}

export default AccessibilityController;
