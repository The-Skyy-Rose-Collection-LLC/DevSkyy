/**
 * DevSkyy Three.js Service
 * 3D graphics and visualization utilities
 */

import * as THREE from 'three';
import { threejsConfig } from '../config/index.js';
import { Logger } from '../utils/Logger.js';

export interface SceneConfig {
  enableShadows?: boolean;
  backgroundColor?: number;
  fog?: {
    color: number;
    near: number;
    far: number;
  };
}

export interface RendererConfig {
  antialias?: boolean;
  alpha?: boolean;
  preserveDrawingBuffer?: boolean;
  powerPreference?: 'default' | 'high-performance' | 'low-power';
}

export interface CameraConfig {
  fov?: number;
  aspect?: number;
  near?: number;
  far?: number;
  position?: [number, number, number];
}

export class ThreeJSService {
  private logger: Logger;
  private scene: THREE.Scene | null = null;
  private renderer: THREE.WebGLRenderer | null = null;
  private camera: THREE.PerspectiveCamera | null = null;
  private animationId: number | null = null;

  constructor() {
    this.logger = new Logger('ThreeJSService');
  }

  /**
   * Initialize Three.js scene
   */
  public initializeScene(
    container: HTMLElement,
    sceneConfig: SceneConfig = {},
    rendererConfig: RendererConfig = {},
    cameraConfig: CameraConfig = {}
  ): void {
    try {
      // Create scene
      this.scene = new THREE.Scene();

      if (sceneConfig.backgroundColor !== undefined) {
        this.scene.background = new THREE.Color(sceneConfig.backgroundColor);
      }

      if (sceneConfig.fog) {
        this.scene.fog = new THREE.Fog(sceneConfig.fog.color, sceneConfig.fog.near, sceneConfig.fog.far);
      }

      // Create renderer
      this.renderer = new THREE.WebGLRenderer({
        antialias: rendererConfig.antialias ?? threejsConfig.antialias,
        alpha: rendererConfig.alpha ?? true,
        preserveDrawingBuffer: rendererConfig.preserveDrawingBuffer ?? false,
        powerPreference: rendererConfig.powerPreference ?? 'high-performance',
      });

      this.renderer.setSize(container.clientWidth, container.clientHeight);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, threejsConfig.pixelRatio));

      if (sceneConfig.enableShadows ?? threejsConfig.enableShadows) {
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      }

      container.appendChild(this.renderer.domElement);

      // Create camera
      this.camera = new THREE.PerspectiveCamera(
        cameraConfig.fov ?? 75,
        cameraConfig.aspect ?? container.clientWidth / container.clientHeight,
        cameraConfig.near ?? 0.1,
        cameraConfig.far ?? 1000
      );

      if (cameraConfig.position) {
        this.camera.position.set(...cameraConfig.position);
      } else {
        this.camera.position.set(0, 0, 5);
      }

      // Add basic lighting
      this.addBasicLighting();

      this.logger.info('Three.js scene initialized successfully');
    } catch (error) {
      this.logger.error('Failed to initialize Three.js scene', error);
      throw error;
    }
  }

  /**
   * Add basic lighting to the scene
   */
  private addBasicLighting(): void {
    if (!this.scene) return;

    // Ambient light
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    this.scene.add(ambientLight);

    // Directional light
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 10, 5);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    this.scene.add(directionalLight);
  }

  /**
   * Create a basic cube mesh
   */
  public createCube(
    size: number = 1,
    color: number = 0x00ff00,
    position: [number, number, number] = [0, 0, 0]
  ): THREE.Mesh {
    const geometry = new THREE.BoxGeometry(size, size, size);
    const material = new THREE.MeshLambertMaterial({ color });
    const cube = new THREE.Mesh(geometry, material);

    cube.position.set(...position);
    cube.castShadow = true;
    cube.receiveShadow = true;

    return cube;
  }

  /**
   * Create a sphere mesh
   */
  public createSphere(
    radius: number = 1,
    color: number = 0xff0000,
    position: [number, number, number] = [0, 0, 0]
  ): THREE.Mesh {
    const geometry = new THREE.SphereGeometry(radius, 32, 32);
    const material = new THREE.MeshLambertMaterial({ color });
    const sphere = new THREE.Mesh(geometry, material);

    sphere.position.set(...position);
    sphere.castShadow = true;
    sphere.receiveShadow = true;

    return sphere;
  }

  /**
   * Create a plane mesh
   */
  public createPlane(
    width: number = 10,
    height: number = 10,
    color: number = 0x808080,
    position: [number, number, number] = [0, -2, 0]
  ): THREE.Mesh {
    const geometry = new THREE.PlaneGeometry(width, height);
    const material = new THREE.MeshLambertMaterial({ color });
    const plane = new THREE.Mesh(geometry, material);

    plane.rotation.x = -Math.PI / 2;
    plane.position.set(...position);
    plane.receiveShadow = true;

    return plane;
  }

  /**
   * Add object to scene
   */
  public addToScene(object: THREE.Object3D): void {
    if (!this.scene) {
      throw new Error('Scene not initialized');
    }
    this.scene.add(object);
  }

  /**
   * Remove object from scene
   */
  public removeFromScene(object: THREE.Object3D): void {
    if (!this.scene) return;
    this.scene.remove(object);
  }

  /**
   * Start animation loop
   */
  public startAnimation(animationCallback?: () => void): void {
    if (!this.scene || !this.camera || !this.renderer) {
      throw new Error('Scene, camera, or renderer not initialized');
    }

    const animate = (): void => {
      this.animationId = requestAnimationFrame(animate);

      if (animationCallback) {
        animationCallback();
      }

      this.renderer!.render(this.scene!, this.camera!);
    };

    animate();
    this.logger.info('Animation loop started');
  }

  /**
   * Stop animation loop
   */
  public stopAnimation(): void {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
      this.logger.info('Animation loop stopped');
    }
  }

  /**
   * Handle window resize
   */
  public handleResize(width: number, height: number): void {
    if (!this.camera || !this.renderer) return;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  /**
   * Get scene statistics
   */
  public getSceneStats(): Record<string, unknown> {
    if (!this.scene || !this.renderer) {
      return { error: 'Scene not initialized' };
    }

    return {
      objects: this.scene.children.length,
      triangles: this.renderer.info.render.triangles,
      geometries: this.renderer.info.memory.geometries,
      textures: this.renderer.info.memory.textures,
      programs: this.renderer.info.programs?.length || 0,
    };
  }

  /**
   * Dispose of resources
   */
  public dispose(): void {
    this.stopAnimation();

    if (this.renderer) {
      this.renderer.dispose();
      this.renderer = null;
    }

    if (this.scene) {
      this.scene.clear();
      this.scene = null;
    }

    this.camera = null;
    this.logger.info('Three.js resources disposed');
  }

  /**
   * Get current scene
   */
  public getScene(): THREE.Scene | null {
    return this.scene;
  }

  /**
   * Get current camera
   */
  public getCamera(): THREE.PerspectiveCamera | null {
    return this.camera;
  }

  /**
   * Get current renderer
   */
  public getRenderer(): THREE.WebGLRenderer | null {
    return this.renderer;
  }
}

// Export singleton instance
export const threeJSService = new ThreeJSService();
