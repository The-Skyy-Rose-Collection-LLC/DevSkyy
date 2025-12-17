/**
 * Runway Experience - 3D Collection Landing Template
 * 
 * A virtual fashion runway for showcasing SkyyRose collections.
 * Features:
 * - Animated model walk cycle
 * - Dynamic camera following
 * - Dramatic lighting effects
 * - Audience ambiance
 * 
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Logger } from '../utils/Logger.js';

export interface RunwayProduct {
  id: string;
  name: string;
  modelUrl: string;
  walkOrder: number;
}

export interface RunwayConfig {
  backgroundColor?: number;
  runwayLength?: number;
  runwayWidth?: number;
  spotlightColor?: number;
  ambientColor?: number;
  walkSpeed?: number;
}

const DEFAULT_CONFIG: RunwayConfig = {
  backgroundColor: 0x0a0a0a,
  runwayLength: 30,
  runwayWidth: 4,
  spotlightColor: 0xd4af37,  // Rose gold
  ambientColor: 0x1a1a2e,
  walkSpeed: 0.02,
};

export class RunwayExperience {
  private logger: Logger;
  private scene: THREE.Scene;
  private renderer: THREE.WebGLRenderer;
  private camera: THREE.PerspectiveCamera;
  private controls: OrbitControls;
  private config: RunwayConfig;
  private animationId: number | null = null;
  private models: THREE.Object3D[] = [];
  private currentModelIndex: number = 0;
  private walkProgress: number = 0;
  private isWalking: boolean = false;

  constructor(container: HTMLElement, config: RunwayConfig = {}) {
    this.logger = new Logger('RunwayExperience');
    this.config = { ...DEFAULT_CONFIG, ...config };

    // Initialize scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(this.config.backgroundColor);
    this.scene.fog = new THREE.FogExp2(this.config.backgroundColor, 0.02);

    // Initialize renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    container.appendChild(this.renderer.domElement);

    // Initialize camera - positioned at end of runway
    this.camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / container.clientHeight,
      0.1,
      100
    );
    this.camera.position.set(0, 2, this.config.runwayLength / 2 - 5);
    this.camera.lookAt(0, 1.5, 0);

    // Initialize controls
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.target.set(0, 1.5, 0);

    this.setupRunway();
    this.setupLighting();
    this.logger.info('Runway experience initialized');
  }

  private setupRunway(): void {
    const { runwayLength, runwayWidth } = this.config;

    // Runway floor
    const runwayGeometry = new THREE.PlaneGeometry(runwayWidth, runwayLength);
    const runwayMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a1a1a,
      roughness: 0.2,
      metalness: 0.8,
    });
    const runway = new THREE.Mesh(runwayGeometry, runwayMaterial);
    runway.rotation.x = -Math.PI / 2;
    runway.receiveShadow = true;
    this.scene.add(runway);

    // Runway edge lights
    const edgeLightGeometry = new THREE.BoxGeometry(0.1, 0.05, runwayLength);
    const edgeLightMaterial = new THREE.MeshBasicMaterial({ color: 0xd4af37 });
    
    const leftEdge = new THREE.Mesh(edgeLightGeometry, edgeLightMaterial);
    leftEdge.position.set(-runwayWidth / 2, 0.025, 0);
    this.scene.add(leftEdge);

    const rightEdge = new THREE.Mesh(edgeLightGeometry, edgeLightMaterial);
    rightEdge.position.set(runwayWidth / 2, 0.025, 0);
    this.scene.add(rightEdge);
  }

  private setupLighting(): void {
    // Ambient light
    const ambient = new THREE.AmbientLight(this.config.ambientColor, 0.3);
    this.scene.add(ambient);

    // Main spotlight following the runway
    const mainSpot = new THREE.SpotLight(0xffffff, 2, 50, Math.PI / 8, 0.3, 1);
    mainSpot.position.set(0, 10, 0);
    mainSpot.castShadow = true;
    mainSpot.shadow.mapSize.width = 2048;
    mainSpot.shadow.mapSize.height = 2048;
    this.scene.add(mainSpot);

    // Rose gold accent lights
    const accentPositions: [number, number, number][] = [[-3, 5, -10], [3, 5, -10], [-3, 5, 10], [3, 5, 10]];
    accentPositions.forEach(([x, y, z]) => {
      const accent = new THREE.SpotLight(this.config.spotlightColor, 1, 20, Math.PI / 6, 0.5);
      accent.position.set(x, y, z);
      accent.target.position.set(0, 0, z);
      this.scene.add(accent);
      this.scene.add(accent.target);
    });
  }

  public async loadProducts(products: RunwayProduct[]): Promise<void> {
    // Sort by walk order
    const sorted = [...products].sort((a, b) => a.walkOrder - b.walkOrder);

    for (const product of sorted) {
      // Placeholder model
      const geometry = new THREE.CapsuleGeometry(0.3, 1.2, 8, 16);
      const material = new THREE.MeshStandardMaterial({
        color: 0xd4af37,
        roughness: 0.4,
        metalness: 0.6,
      });
      const model = new THREE.Mesh(geometry, material);
      const runwayLen = this.config.runwayLength;
      model.position.set(0, 0.9, -runwayLen / 2);
      model.castShadow = true;
      model.userData['productId'] = product.id;
      model.userData['name'] = product.name;
      model.visible = false;
      this.scene.add(model);
      this.models.push(model);
    }
  }

  public startShow(): void {
    if (this.models.length === 0) return;
    this.isWalking = true;
    this.currentModelIndex = 0;
    this.walkProgress = 0;
    const firstModel = this.models[0];
    if (firstModel) firstModel.visible = true;
  }

  private updateWalk(): void {
    if (!this.isWalking || this.models.length === 0) return;

    const currentModel = this.models[this.currentModelIndex];
    if (!currentModel) return;

    const runwayLength = this.config.runwayLength;
    const walkSpeed = this.config.walkSpeed;

    // Update position along runway
    this.walkProgress += walkSpeed;
    const z = -runwayLength / 2 + this.walkProgress * runwayLength;
    currentModel.position.z = z;

    // Add subtle sway animation
    currentModel.rotation.y = Math.sin(this.walkProgress * 20) * 0.05;

    // Check if model reached end
    if (this.walkProgress >= 1) {
      currentModel.visible = false;
      this.currentModelIndex++;
      this.walkProgress = 0;

      const nextModel = this.models[this.currentModelIndex];
      if (nextModel) {
        nextModel.visible = true;
      } else {
        this.isWalking = false;
        this.logger.info('Runway show complete');
      }
    }
  }

  public start(): void {
    const animate = (): void => {
      this.animationId = requestAnimationFrame(animate);
      this.updateWalk();
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
    this.models.forEach((model) => this.scene.remove(model));
    this.renderer.dispose();
    this.logger.info('Runway experience disposed');
  }
}

export default RunwayExperience;

