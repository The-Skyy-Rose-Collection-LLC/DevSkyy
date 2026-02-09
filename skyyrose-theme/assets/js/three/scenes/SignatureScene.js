/**
 * SignatureScene - Luxury Rose Garden Pavilion with Glass Architecture
 *
 * Context7 Queries Used:
 * - /mrdoob/three.js - MeshPhysicalMaterial glass transmission (ior=1.5, transmission=0.9)
 * - /mrdoob/three.js - HDR environment mapping with PMREM
 * - /greensock/gsap - Camera animations with power2.inOut easing
 *
 * Scene Description:
 * Modern glass pavilion with floor-to-ceiling windows, golden hour lighting,
 * featuring the Signature Collection products displayed on pedestals.
 *
 * Performance Targets (Documented):
 * - <100 draw calls for 60fps
 * - HDR environment for photorealistic reflections
 * - Glass materials with proper IOR (Index of Refraction)
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

import * as THREE from 'three';
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import gsap from 'gsap';
import BaseScene from '../utils/BaseScene.js';
import ProductLoader from '../utils/ProductLoader.js';

export default class SignatureScene extends BaseScene {
  constructor(container) {
    super(container, {
      enableOrbitControls: true,
      enableDamping: true,
      dampingFactor: 0.05,
      autoRotate: false,
      minDistance: 3,
      maxDistance: 15,
      maxPolarAngle: Math.PI / 2.1,
      toneMapping: THREE.ACESFilmicToneMapping,
      toneMappingExposure: 1.2, // Brighter for golden hour
      shadowMapEnabled: true,
      shadowMapType: THREE.PCFSoftShadowMap,
    });

    this.productLoader = new ProductLoader();
    this.hdrEnvironment = null;
    this.glassMaterials = [];
    this.productPedestals = [];
  }

  /**
   * Override setupScene to configure golden hour environment
   */
  setupScene() {
    this.scene = new THREE.Scene();
    // Will be replaced by HDR environment
    this.scene.background = new THREE.Color(0xfff5e6); // Warm golden color as fallback
    this.scene.fog = new THREE.Fog(0xfff5e6, 15, 40);
  }

  /**
   * Override setupLights for golden hour lighting
   * Pattern from Context7: Directional light simulating sun at golden hour
   */
  setupLights() {
    // Ambient light for base illumination (golden tint)
    const ambientLight = new THREE.AmbientLight(0xfff5e6, 0.4);
    this.scene.add(ambientLight);

    // Golden hour sun (directional light at low angle)
    const sunLight = new THREE.DirectionalLight(0xffd9a6, 2.0);
    sunLight.position.set(10, 5, 10);
    sunLight.castShadow = true;

    // Shadow configuration for sharp, realistic shadows
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    sunLight.shadow.camera.near = 0.5;
    sunLight.shadow.camera.far = 50;
    sunLight.shadow.camera.left = -15;
    sunLight.shadow.camera.right = 15;
    sunLight.shadow.camera.top = 15;
    sunLight.shadow.camera.bottom = -15;
    sunLight.shadow.bias = -0.0001;

    this.scene.add(sunLight);

    // Warm fill light (opposite side, subtle)
    const fillLight = new THREE.DirectionalLight(0xffcc99, 0.5);
    fillLight.position.set(-5, 3, -5);
    this.scene.add(fillLight);

    // Hemisphere light for sky/ground gradient
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x8d6e63, 0.6);
    hemiLight.position.set(0, 20, 0);
    this.scene.add(hemiLight);
  }

  /**
   * Load HDR environment map for photorealistic reflections
   * Pattern from Context7: PMREM with equirectangular HDR
   */
  async loadHDREnvironment() {
    return new Promise((resolve, reject) => {
      const rgbeLoader = new RGBELoader(this.loadingManager);

      // Note: In production, you'd use an actual HDR file
      // For now, we'll use Three.js built-in environment
      const pmremGenerator = new THREE.PMREMGenerator(this.renderer);
      pmremGenerator.compileEquirectangularShader();

      // Create procedural environment as fallback
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0xfff5e6);

      this.hdrEnvironment = pmremGenerator.fromScene(scene).texture;
      this.scene.environment = this.hdrEnvironment;
      this.scene.background = this.hdrEnvironment;

      pmremGenerator.dispose();
      resolve();
    });
  }

  /**
   * Create glass pavilion architecture
   * Pattern from Context7: MeshPhysicalMaterial with transmission
   */
  createGlassPavilion() {
    // Glass material configuration from Context7 documentation
    const glassMaterial = new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      metalness: 0.0,
      roughness: 0.1,
      transmission: 0.9, // High transparency
      thickness: 0.5,    // Glass thickness
      ior: 1.5,          // Index of refraction for glass
      envMapIntensity: 1.0,
      clearcoat: 1.0,
      clearcoatRoughness: 0.1,
      transparent: true,
      side: THREE.DoubleSide,
    });

    this.glassMaterials.push(glassMaterial);

    // Create glass walls (4 walls of pavilion)
    const wallHeight = 4;
    const wallWidth = 12;
    const wallGeometry = new THREE.PlaneGeometry(wallWidth, wallHeight);

    // Front glass wall
    const frontWall = new THREE.Mesh(wallGeometry, glassMaterial);
    frontWall.position.set(0, wallHeight / 2, -6);
    this.scene.add(frontWall);

    // Back glass wall
    const backWall = new THREE.Mesh(wallGeometry, glassMaterial);
    backWall.position.set(0, wallHeight / 2, 6);
    backWall.rotation.y = Math.PI;
    this.scene.add(backWall);

    // Left glass wall
    const leftWall = new THREE.Mesh(wallGeometry, glassMaterial);
    leftWall.position.set(-6, wallHeight / 2, 0);
    leftWall.rotation.y = Math.PI / 2;
    this.scene.add(leftWall);

    // Right glass wall
    const rightWall = new THREE.Mesh(wallGeometry, glassMaterial);
    rightWall.position.set(6, wallHeight / 2, 0);
    rightWall.rotation.y = -Math.PI / 2;
    this.scene.add(rightWall);

    // Golden frame material for window frames
    const frameMaterial = new THREE.MeshStandardMaterial({
      color: 0xffd700,
      metalness: 1.0,
      roughness: 0.3,
    });

    // Create window frames (thin golden bars)
    const frameGeometry = new THREE.BoxGeometry(0.1, wallHeight, 0.1);
    const positions = [
      [-6, wallHeight / 2, -6],   // Front-left corner
      [6, wallHeight / 2, -6],    // Front-right corner
      [-6, wallHeight / 2, 6],    // Back-left corner
      [6, wallHeight / 2, 6],     // Back-right corner
    ];

    positions.forEach((pos) => {
      const frame = new THREE.Mesh(frameGeometry, frameMaterial);
      frame.position.set(...pos);
      frame.castShadow = true;
      this.scene.add(frame);
    });
  }

  /**
   * Create floor with marble-like material
   */
  createFloor() {
    const floorGeometry = new THREE.PlaneGeometry(20, 20);
    const floorMaterial = new THREE.MeshStandardMaterial({
      color: 0xf5f5dc, // Beige marble
      roughness: 0.2,
      metalness: 0.1,
    });

    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = 0;
    floor.receiveShadow = true;
    this.scene.add(floor);
  }

  /**
   * Create product hotspots with glowing markers
   * Pattern from implementation plan: Product hotspot system
   */
  createProductHotspot(productData) {
    // Glowing sphere marker (documented pattern from plan)
    const geometry = new THREE.SphereGeometry(0.3, 32, 32);
    const material = new THREE.MeshStandardMaterial({
      color: 0xffd700,
      emissive: 0xffd700,
      emissiveIntensity: 2,
      transparent: true,
      opacity: 0.8,
      metalness: 0.5,
      roughness: 0.3,
    });

    const marker = new THREE.Mesh(geometry, material);
    marker.position.set(
      productData.position.x,
      productData.position.y,
      productData.position.z
    );

    // Store product data for interaction
    marker.userData = {
      productId: productData.id,
      productName: productData.name,
      productPrice: productData.price,
      productImage: productData.image,
      productUrl: productData.url,
    };

    // GSAP pulsing animation (documented from Context7)
    gsap.to(marker.scale, {
      x: 1.2,
      y: 1.2,
      z: 1.2,
      duration: 1,
      repeat: -1,
      yoyo: true,
      ease: 'power2.inOut',
    });

    this.productHotspots.push(marker);
    this.scene.add(marker);

    // Create pedestal for product
    this.createPedestal(productData.position);
  }

  /**
   * Create display pedestal
   */
  createPedestal(position) {
    const pedestalGeometry = new THREE.CylinderGeometry(0.5, 0.6, 1.5, 32);
    const pedestalMaterial = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      roughness: 0.2,
      metalness: 0.1,
    });

    const pedestal = new THREE.Mesh(pedestalGeometry, pedestalMaterial);
    pedestal.position.set(position.x, 0.75, position.z);
    pedestal.castShadow = true;
    pedestal.receiveShadow = true;
    this.scene.add(pedestal);
    this.productPedestals.push(pedestal);
  }

  /**
   * Load and display products
   */
  async loadProducts() {
    try {
      const products = await this.productLoader.loadCollectionProducts('signature-collection');
      console.log(`[SignatureScene] Loaded ${products.length} products`);

      products.forEach((product) => {
        this.createProductHotspot(product);
      });
    } catch (error) {
      console.error('[SignatureScene] Error loading products:', error);
    }
  }

  /**
   * Navigate camera to section with smooth GSAP animation
   * Pattern from Context7: GSAP camera animations with power2.inOut
   *
   * @param {string} section - Section name ('entrance', 'center', 'products')
   */
  navigateToSection(section) {
    const positions = {
      entrance: { x: 0, y: 3, z: 10, targetY: 2 },
      center: { x: 0, y: 4, z: 8, targetY: 1.5 },
      products: { x: 5, y: 3, z: 5, targetY: 1.5 },
    };

    const targetPos = positions[section] || positions.center;

    // Smooth camera animation with GSAP
    gsap.to(this.camera.position, {
      x: targetPos.x,
      y: targetPos.y,
      z: targetPos.z,
      duration: 2,
      ease: 'power2.inOut',
      onUpdate: () => {
        this.controls.target.set(0, targetPos.targetY, 0);
        this.controls.update();
      },
    });
  }

  /**
   * Override onLoadComplete to initialize scene elements
   */
  onLoadComplete() {
    console.log('[SignatureScene] All assets loaded, building scene...');

    // Build scene elements
    this.createGlassPavilion();
    this.createFloor();

    // Load HDR environment
    this.loadHDREnvironment().then(() => {
      console.log('[SignatureScene] HDR environment loaded');

      // Load products
      this.loadProducts();

      // Animate camera to entrance
      this.navigateToSection('entrance');
    });
  }

  /**
   * Override update for custom animations
   */
  update(delta) {
    // Animate glass materials slightly for shimmer effect
    this.glassMaterials.forEach((material) => {
      // Subtle transmission variation for glass shimmer
      if (material.transmission) {
        material.transmission = 0.9 + Math.sin(Date.now() * 0.001) * 0.05;
      }
    });
  }

  /**
   * Override dispose to clean up custom resources
   */
  dispose() {
    // Dispose glass materials
    this.glassMaterials.forEach((material) => material.dispose());
    this.glassMaterials = [];

    // Dispose HDR environment
    if (this.hdrEnvironment) {
      this.hdrEnvironment.dispose();
    }

    // Call parent dispose
    super.dispose();
  }
}
