/**
 * BaseScene - Foundation class for all 3D collection scenes
 *
 * Context7 Queries Used:
 * - /mrdoob/three.js - Three.js r161 scene setup, renderer configuration, tone mapping
 * - /mrdoob/three.js - OrbitControls touch support, damping, constraints
 *
 * Based on production-proven patterns from drakerelated.com analysis:
 * - WebGLRenderer with ACESFilmicToneMapping for photorealistic rendering
 * - OrbitControls with damping for smooth camera movement
 * - Responsive canvas sizing with proper pixel ratio handling
 * - Loading manager for accurate progress tracking
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export default class BaseScene {
  /**
   * Constructor
   *
   * @param {HTMLElement} container - DOM element to render scene into
   * @param {Object} options - Configuration options
   */
  constructor(container, options = {}) {
    this.container = container;
    this.options = {
      enableOrbitControls: true,
      enableDamping: true,
      dampingFactor: 0.05,
      autoRotate: false,
      autoRotateSpeed: 0.5,
      minDistance: 2,
      maxDistance: 20,
      maxPolarAngle: Math.PI / 1.5, // Limit vertical rotation
      toneMapping: THREE.ACESFilmicToneMapping,
      toneMappingExposure: 1.0,
      shadowMapEnabled: true,
      shadowMapType: THREE.PCFSoftShadowMap,
      ...options,
    };

    // Core Three.js components
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.loadingManager = null;

    // Animation state
    this.clock = new THREE.Clock();
    this.animationId = null;
    this.isRunning = false;

    // Product hotspots
    this.productHotspots = [];
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    // Bind methods
    this.animate = this.animate.bind(this);
    this.onWindowResize = this.onWindowResize.bind(this);
    this.onMouseMove = this.onMouseMove.bind(this);
    this.onClick = this.onClick.bind(this);

    // Initialize
    this.init();
  }

  /**
   * Initialize the scene
   * Pattern from Context7: /mrdoob/three.js - webgl_tonemapping.html
   */
  init() {
    // Setup loading manager
    this.setupLoadingManager();

    // Setup renderer - Pattern from Three.js r161 docs
    this.setupRenderer();

    // Setup scene
    this.setupScene();

    // Setup camera
    this.setupCamera();

    // Setup controls
    if (this.options.enableOrbitControls) {
      this.setupControls();
    }

    // Setup lights (override in child classes)
    this.setupLights();

    // Add window event listeners
    window.addEventListener('resize', this.onWindowResize);
    this.container.addEventListener('mousemove', this.onMouseMove);
    this.container.addEventListener('click', this.onClick);

    // Start animation loop
    this.start();
  }

  /**
   * Setup loading manager for accurate progress tracking
   */
  setupLoadingManager() {
    this.loadingManager = new THREE.LoadingManager();

    this.loadingManager.onStart = (url, itemsLoaded, itemsTotal) => {
      console.log(`Started loading: ${url}`);
      this.onLoadStart(url, itemsLoaded, itemsTotal);
    };

    this.loadingManager.onProgress = (url, itemsLoaded, itemsTotal) => {
      const progress = (itemsLoaded / itemsTotal) * 100;
      console.log(`Loading progress: ${progress.toFixed(2)}%`);
      this.onLoadProgress(url, itemsLoaded, itemsTotal, progress);
    };

    this.loadingManager.onLoad = () => {
      console.log('All assets loaded');
      this.onLoadComplete();
    };

    this.loadingManager.onError = (url) => {
      console.error(`Error loading: ${url}`);
      this.onLoadError(url);
    };
  }

  /**
   * Setup WebGL renderer with production-ready configuration
   * Pattern from Context7: /mrdoob/three.js - ACESFilmicToneMapping
   */
  setupRenderer() {
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    });

    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Cap at 2 for performance
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.toneMapping = this.options.toneMapping;
    this.renderer.toneMappingExposure = this.options.toneMappingExposure;

    // Shadow configuration
    if (this.options.shadowMapEnabled) {
      this.renderer.shadowMap.enabled = true;
      this.renderer.shadowMap.type = this.options.shadowMapType;
    }

    // Output encoding for correct color space
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    this.container.appendChild(this.renderer.domElement);
  }

  /**
   * Setup scene with background
   */
  setupScene() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0a0a0a); // Dark background
    this.scene.fog = new THREE.Fog(0x0a0a0a, 10, 50); // Atmospheric fog
  }

  /**
   * Setup perspective camera
   */
  setupCamera() {
    const aspect = this.container.clientWidth / this.container.clientHeight;
    this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 100);
    this.camera.position.set(0, 2, 5);
    this.camera.lookAt(0, 1, 0);
  }

  /**
   * Setup OrbitControls with touch support
   * Pattern from Context7: /mrdoob/three.js - OrbitControls touch configuration
   */
  setupControls() {
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);

    // Damping for smooth movement
    this.controls.enableDamping = this.options.enableDamping;
    this.controls.dampingFactor = this.options.dampingFactor;

    // Auto-rotate
    this.controls.autoRotate = this.options.autoRotate;
    this.controls.autoRotateSpeed = this.options.autoRotateSpeed;

    // Distance constraints
    this.controls.minDistance = this.options.minDistance;
    this.controls.maxDistance = this.options.maxDistance;

    // Vertical rotation limit (prevent camera going upside down)
    this.controls.maxPolarAngle = this.options.maxPolarAngle;

    // Touch controls - Pattern from Three.js OrbitControls docs
    this.controls.touches = {
      ONE: THREE.TOUCH.ROTATE,
      TWO: THREE.TOUCH.DOLLY_PAN,
    };

    // Mouse button mapping
    this.controls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.DOLLY,
      RIGHT: THREE.MOUSE.PAN,
    };

    // Set target to look at center
    this.controls.target.set(0, 1, 0);
    this.controls.update();
  }

  /**
   * Setup basic lighting (override in child classes for custom lighting)
   */
  setupLights() {
    // Ambient light for base illumination
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    this.scene.add(ambientLight);

    // Directional light for shadows
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 10, 5);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    directionalLight.shadow.camera.near = 0.5;
    directionalLight.shadow.camera.far = 50;
    this.scene.add(directionalLight);
  }

  /**
   * Window resize handler
   */
  onWindowResize() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();

    this.renderer.setSize(width, height);
  }

  /**
   * Mouse move handler for hotspot hover detection
   */
  onMouseMove(event) {
    const rect = this.container.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    // Raycast for hotspot hover (implemented in child classes)
    this.checkHotspotHover();
  }

  /**
   * Click handler for hotspot interaction
   */
  onClick(event) {
    const rect = this.container.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    // Raycast for hotspot click
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.productHotspots, true);

    if (intersects.length > 0) {
      const hotspot = intersects[0].object;
      if (hotspot.userData && hotspot.userData.productId) {
        this.onHotspotClick(hotspot.userData);
      }
    }
  }

  /**
   * Check for hotspot hover (override in child classes)
   */
  checkHotspotHover() {
    // Override in child classes for custom hover effects
  }

  /**
   * Handle hotspot click
   */
  onHotspotClick(productData) {
    // Dispatch custom event for product modal
    const event = new CustomEvent('productHotspotClick', {
      detail: productData,
    });
    window.dispatchEvent(event);
  }

  /**
   * Loading callbacks (override in child classes)
   */
  onLoadStart(url, itemsLoaded, itemsTotal) {}
  onLoadProgress(url, itemsLoaded, itemsTotal, progress) {}
  onLoadComplete() {}
  onLoadError(url) {}

  /**
   * Animation loop
   */
  animate() {
    if (!this.isRunning) return;

    this.animationId = requestAnimationFrame(this.animate);

    const delta = this.clock.getDelta();

    // Update controls
    if (this.controls && this.controls.enableDamping) {
      this.controls.update();
    }

    // Custom update logic (override in child classes)
    this.update(delta);

    // Render
    this.renderer.render(this.scene, this.camera);
  }

  /**
   * Update method (override in child classes)
   */
  update(delta) {
    // Override in child classes for custom animations
  }

  /**
   * Start animation loop
   */
  start() {
    if (this.isRunning) return;
    this.isRunning = true;
    this.animate();
  }

  /**
   * Stop animation loop
   */
  stop() {
    if (!this.isRunning) return;
    this.isRunning = false;
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
  }

  /**
   * Clean up resources
   */
  dispose() {
    this.stop();

    // Remove event listeners
    window.removeEventListener('resize', this.onWindowResize);
    this.container.removeEventListener('mousemove', this.onMouseMove);
    this.container.removeEventListener('click', this.onClick);

    // Dispose geometries and materials
    this.scene.traverse((object) => {
      if (object.geometry) {
        object.geometry.dispose();
      }
      if (object.material) {
        if (Array.isArray(object.material)) {
          object.material.forEach((material) => material.dispose());
        } else {
          object.material.dispose();
        }
      }
    });

    // Dispose renderer
    if (this.renderer) {
      this.renderer.dispose();
      if (this.container && this.renderer.domElement) {
        this.container.removeChild(this.renderer.domElement);
      }
    }
  }
}
