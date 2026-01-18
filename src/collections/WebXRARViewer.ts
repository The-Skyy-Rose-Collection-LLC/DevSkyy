/**
 * WebXRARViewer - Native WebXR AR for SkyyRose Collections
 *
 * Provides immersive AR experience on supported devices (ARCore/ARKit).
 * Features hit-testing for surface detection and 3D product placement.
 * Falls back to ARTryOnViewer (webcam) on unsupported devices.
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

export interface WebXRProduct {
  id: string;
  name: string;
  modelUrl: string;
  scale?: number;
  collection: 'black_rose' | 'love_hurts' | 'signature';
}

export interface WebXRConfig {
  container: HTMLElement;
  collection: 'black_rose' | 'love_hurts' | 'signature';
  onProductPlaced?: (product: WebXRProduct, position: THREE.Vector3) => void;
  onSessionStart?: () => void;
  onSessionEnd?: () => void;
  onError?: (error: Error) => void;
}

interface CollectionStyle {
  reticleColor: number;
  lightColor: number;
  ambientIntensity: number;
}

const COLLECTION_STYLES: Record<string, CollectionStyle> = {
  black_rose: {
    reticleColor: 0x8b0000,
    lightColor: 0xffcccc,
    ambientIntensity: 0.4,
  },
  love_hurts: {
    reticleColor: 0xff1493,
    lightColor: 0xffc0cb,
    ambientIntensity: 0.5,
  },
  signature: {
    reticleColor: 0xb76e79,
    lightColor: 0xfff8dc,
    ambientIntensity: 0.6,
  },
};

export class WebXRARViewer {
  private config: WebXRConfig;
  private style: CollectionStyle;
  private container: HTMLElement;

  private renderer: THREE.WebGLRenderer | null = null;
  private scene: THREE.Scene | null = null;
  private camera: THREE.PerspectiveCamera | null = null;

  private reticle: THREE.Mesh | null = null;
  private hitTestSource: XRHitTestSource | null = null;
  private hitTestSourceRequested = false;

  private currentProduct: WebXRProduct | null = null;
  private loadedModel: THREE.Group | null = null;
  private placedModels: THREE.Group[] = [];

  private gltfLoader: GLTFLoader;
  private isSessionActive = false;

  constructor(config: WebXRConfig) {
    this.config = config;
    this.style = (COLLECTION_STYLES[config.collection] ?? COLLECTION_STYLES['signature']) as CollectionStyle;
    this.container = config.container;
    this.gltfLoader = new GLTFLoader();
  }

  /**
   * Check if WebXR AR is supported on this device
   */
  static async isSupported(): Promise<boolean> {
    if (!navigator.xr) {
      return false;
    }
    try {
      return await navigator.xr.isSessionSupported('immersive-ar');
    } catch {
      return false;
    }
  }

  /**
   * Initialize the WebXR AR viewer
   */
  async initialize(): Promise<void> {
    const supported = await WebXRARViewer.isSupported();
    if (!supported) {
      throw new Error('WebXR AR not supported on this device');
    }

    this.createRenderer();
    this.createScene();
    this.createReticle();
    this.createLighting();
  }

  private createRenderer(): void {
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
    });
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.xr.enabled = true;
    this.container.appendChild(this.renderer.domElement);
  }

  private createScene(): void {
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(
      70,
      window.innerWidth / window.innerHeight,
      0.01,
      20
    );
  }

  private createReticle(): void {
    if (!this.scene) return;

    const geometry = new THREE.RingGeometry(0.15, 0.2, 32).rotateX(-Math.PI / 2);
    const material = new THREE.MeshBasicMaterial({
      color: this.style.reticleColor,
      transparent: true,
      opacity: 0.8,
    });

    this.reticle = new THREE.Mesh(geometry, material);
    this.reticle.matrixAutoUpdate = false;
    this.reticle.visible = false;
    this.scene.add(this.reticle);
  }

  private createLighting(): void {
    if (!this.scene) return;

    const hemisphereLight = new THREE.HemisphereLight(
      this.style.lightColor,
      0x444444,
      this.style.ambientIntensity
    );
    hemisphereLight.position.set(0.5, 1, 0.25);
    this.scene.add(hemisphereLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(1, 1, 1);
    this.scene.add(directionalLight);
  }

  /**
   * Create AR button for entering immersive AR mode
   */
  createARButton(): HTMLButtonElement {
    const button = document.createElement('button');
    button.textContent = 'Enter AR';
    button.style.cssText = `
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      padding: 16px 32px;
      font-size: 16px;
      font-weight: bold;
      background: linear-gradient(135deg, ${this.hexToRgb(this.style.reticleColor)}, #1a1a1a);
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      z-index: 1000;
      font-family: 'Playfair Display', serif;
      text-transform: uppercase;
      letter-spacing: 2px;
    `;

    button.addEventListener('click', () => this.startSession());

    return button;
  }

  private hexToRgb(hex: number): string {
    const r = (hex >> 16) & 255;
    const g = (hex >> 8) & 255;
    const b = hex & 255;
    return `rgb(${r}, ${g}, ${b})`;
  }

  /**
   * Start WebXR AR session
   */
  async startSession(): Promise<void> {
    if (!navigator.xr || !this.renderer) {
      this.config.onError?.(new Error('WebXR not available'));
      return;
    }

    try {
      const session = await navigator.xr.requestSession('immersive-ar', {
        requiredFeatures: ['hit-test'],
        optionalFeatures: ['dom-overlay'],
      });

      session.addEventListener('end', () => this.onSessionEnd());

      await this.renderer.xr.setSession(session);
      this.isSessionActive = true;

      this.renderer.setAnimationLoop((timestamp, frame) => {
        this.onAnimationFrame(timestamp, frame);
      });

      this.config.onSessionStart?.();
      console.log('[WebXRARViewer] AR session started');
    } catch (error) {
      console.error('[WebXRARViewer] Failed to start AR session:', error);
      this.config.onError?.(error instanceof Error ? error : new Error('Failed to start AR'));
    }
  }

  /**
   * Set the product to place in AR
   */
  async setProduct(product: WebXRProduct): Promise<void> {
    this.currentProduct = product;

    if (this.loadedModel && this.scene) {
      this.scene.remove(this.loadedModel);
      this.loadedModel = null;
    }

    try {
      const gltf = await this.gltfLoader.loadAsync(product.modelUrl);
      this.loadedModel = gltf.scene;

      const scale = product.scale || 0.5;
      this.loadedModel.scale.set(scale, scale, scale);

      console.log('[WebXRARViewer] Product model loaded:', product.name);
    } catch (error) {
      console.error('[WebXRARViewer] Failed to load product model:', error);
      this.config.onError?.(new Error(`Failed to load model: ${product.name}`));
    }
  }

  private onAnimationFrame(_timestamp: number, frame: XRFrame | null): void {
    if (!frame || !this.renderer || !this.scene || !this.camera) return;

    const referenceSpace = this.renderer.xr.getReferenceSpace();
    const session = this.renderer.xr.getSession();

    if (!referenceSpace || !session) return;

    // Request hit test source on first frame
    if (!this.hitTestSourceRequested) {
      session.requestReferenceSpace('viewer').then((viewerSpace) => {
        session.requestHitTestSource?.({ space: viewerSpace })?.then((source) => {
          this.hitTestSource = source;
        });
      });

      session.addEventListener('end', () => {
        this.hitTestSourceRequested = false;
        this.hitTestSource = null;
      });

      this.hitTestSourceRequested = true;
    }

    // Update reticle position based on hit test results
    if (this.hitTestSource && this.reticle) {
      const hitTestResults = frame.getHitTestResults(this.hitTestSource);

      if (hitTestResults.length > 0) {
        const hit = hitTestResults[0]!;
        const pose = hit.getPose(referenceSpace);

        if (pose) {
          this.reticle.visible = true;
          this.reticle.matrix.fromArray(pose.transform.matrix);
        }
      } else {
        this.reticle.visible = false;
      }
    }

    this.renderer.render(this.scene, this.camera);
  }

  /**
   * Place the current product at the reticle position
   */
  placeProduct(): void {
    if (!this.loadedModel || !this.reticle || !this.reticle.visible || !this.scene) {
      console.warn('[WebXRARViewer] Cannot place product - no model loaded or surface detected');
      return;
    }

    const clone = this.loadedModel.clone();
    clone.position.setFromMatrixPosition(this.reticle.matrix);
    clone.quaternion.setFromRotationMatrix(this.reticle.matrix);

    this.scene.add(clone);
    this.placedModels.push(clone);

    const position = new THREE.Vector3();
    position.setFromMatrixPosition(this.reticle.matrix);

    if (this.currentProduct) {
      this.config.onProductPlaced?.(this.currentProduct, position);
    }

    console.log('[WebXRARViewer] Product placed at:', position);
  }

  /**
   * Remove all placed products
   */
  clearPlacedProducts(): void {
    if (!this.scene) return;

    for (const model of this.placedModels) {
      this.scene.remove(model);
    }
    this.placedModels = [];
  }

  /**
   * Remove the last placed product
   */
  undoLastPlacement(): void {
    if (!this.scene || this.placedModels.length === 0) return;

    const lastModel = this.placedModels.pop();
    if (lastModel) {
      this.scene.remove(lastModel);
    }
  }

  private onSessionEnd(): void {
    this.isSessionActive = false;
    this.hitTestSourceRequested = false;
    this.hitTestSource = null;

    if (this.renderer) {
      this.renderer.setAnimationLoop(null);
    }

    this.config.onSessionEnd?.();
    console.log('[WebXRARViewer] AR session ended');
  }

  /**
   * End the AR session
   */
  async endSession(): Promise<void> {
    if (!this.renderer) return;

    const session = this.renderer.xr.getSession();
    if (session) {
      await session.end();
    }
  }

  /**
   * Check if AR session is active
   */
  get isActive(): boolean {
    return this.isSessionActive;
  }

  /**
   * Get the Three.js scene for custom additions
   */
  getScene(): THREE.Scene | null {
    return this.scene;
  }

  /**
   * Dispose of all resources
   */
  dispose(): void {
    this.endSession();
    this.clearPlacedProducts();

    if (this.loadedModel && this.scene) {
      this.scene.remove(this.loadedModel);
    }

    if (this.reticle && this.scene) {
      this.scene.remove(this.reticle);
    }

    if (this.renderer) {
      this.renderer.dispose();
      this.container.removeChild(this.renderer.domElement);
    }

    this.renderer = null;
    this.scene = null;
    this.camera = null;
    this.reticle = null;
    this.loadedModel = null;
  }
}

/**
 * Factory function to create the best AR viewer for the current device
 */
export async function createBestARViewer(
  config: WebXRConfig
): Promise<WebXRARViewer | null> {
  const webxrSupported = await WebXRARViewer.isSupported();

  if (webxrSupported) {
    const viewer = new WebXRARViewer(config);
    await viewer.initialize();
    return viewer;
  }

  // Return null - caller should fall back to ARTryOnViewer
  console.log('[AR] WebXR not supported, use ARTryOnViewer for webcam-based AR');
  return null;
}
