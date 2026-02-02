/**
 * LuxuryProductViewer - WordPress-compatible 3D Product Viewer
 * Converted from React Three Fiber to vanilla Three.js
 *
 * Features:
 * - GLTF model loading with auto-fit camera
 * - Rose gold lighting (#B76E79 brand color)
 * - OrbitControls with auto-rotate
 * - Bloom + ToneMapping post-processing
 * - Luxury shadows and environment
 * - Mobile optimization
 * - AR button integration
 * - Responsive canvas
 *
 * Usage:
 * const viewer = new LuxuryProductViewer(container, {
 *   modelUrl: '/path/to/model.glb',
 *   productName: 'Product Name',
 *   environment: 'studio',
 *   autoRotate: true,
 *   showEffects: true,
 *   enableAR: true
 * });
 *
 * @version 1.0.0
 * @author SkyyRose Development Team
 */

(function(window) {
  'use strict';

  class LuxuryProductViewer {
    constructor(container, config = {}) {
      // Configuration
      this.container = container;
      this.config = {
        modelUrl: config.modelUrl || '',
        productName: config.productName || 'Product',
        environment: config.environment || 'studio',
        autoRotate: config.autoRotate !== false,
        showEffects: config.showEffects !== false,
        enableAR: config.enableAR !== false,
        camera: {
          fov: 45,
          near: 0.1,
          far: 1000,
          position: [0, 0, 5]
        },
        controls: {
          minDistance: 2,
          maxDistance: 10,
          minPolarAngle: Math.PI / 2.5,
          maxPolarAngle: Math.PI / 1.5,
          enablePan: false,
          enableZoom: true,
          autoRotateSpeed: 0.5,
          dampingFactor: 0.05,
          enableDamping: true
        },
        lighting: {
          ambient: 0.5,
          key: {
            color: 0xB76E79, // Rose gold
            intensity: 4,
            position: [0, 5, -9]
          },
          fill: {
            color: 0x8B5A62, // Darker rose
            intensity: 2,
            position: [-5, 1, -1]
          },
          rim: {
            color: 0xffffff,
            intensity: 2,
            position: [10, 1, 0]
          }
        },
        effects: {
          bloom: {
            threshold: 0.2,
            strength: 1.5,
            radius: 0.9
          },
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1
        }
      };

      // State
      this.scene = null;
      this.camera = null;
      this.renderer = null;
      this.controls = null;
      this.composer = null;
      this.model = null;
      this.lights = {};
      this.isLoading = true;
      this.isMobile = this.checkMobile();
      this.animationId = null;

      // Initialize
      this.init();
    }

    checkMobile() {
      return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
             window.innerWidth < 768;
    }

    init() {
      this.createLoadingUI();
      this.createScene();
      this.createCamera();
      this.createRenderer();
      this.createLights();
      this.createControls();
      this.createPostProcessing();
      this.createUI();
      this.loadModel();
      this.setupEventListeners();
      this.animate();
    }

    createLoadingUI() {
      const loading = document.createElement('div');
      loading.className = 'luxury-viewer-loading';

      const content = document.createElement('div');
      content.className = 'loading-content';

      const spinner = document.createElement('div');
      spinner.className = 'spinner';

      const text = document.createElement('p');
      text.className = 'loading-text';
      text.textContent = `Loading ${this.config.productName}...`;

      content.appendChild(spinner);
      content.appendChild(text);
      loading.appendChild(content);
      this.container.appendChild(loading);
      this.loadingUI = loading;

      // Add styles
      const style = document.createElement('style');
      style.textContent = `
        .luxury-viewer-loading {
          position: absolute;
          inset: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(15, 23, 42, 0.8);
          z-index: 10;
          transition: opacity 0.5s ease-out;
        }
        .luxury-viewer-loading.hide {
          opacity: 0;
          pointer-events: none;
        }
        .loading-content {
          text-align: center;
        }
        .spinner {
          width: 64px;
          height: 64px;
          border: 4px solid #B76E79;
          border-top-color: transparent;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 16px;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .loading-text {
          color: #B76E79;
          font-weight: 300;
          letter-spacing: 0.1em;
        }
        .luxury-viewer-ui {
          position: absolute;
          bottom: 24px;
          left: 24px;
          color: white;
          opacity: 0;
          transform: translateY(20px);
          transition: opacity 0.6s ease-out 0.3s, transform 0.6s ease-out 0.3s;
        }
        .luxury-viewer-ui.show {
          opacity: 1;
          transform: translateY(0);
        }
        .product-name {
          font-size: 28px;
          font-weight: 300;
          letter-spacing: 0.1em;
          margin-bottom: 4px;
        }
        .product-collection {
          color: #B76E79;
          font-size: 14px;
          letter-spacing: 0.15em;
        }
        .ar-button {
          position: absolute;
          top: 24px;
          right: 24px;
          padding: 12px 24px;
          background: #B76E79;
          color: white;
          border: none;
          border-radius: 9999px;
          font-weight: 300;
          letter-spacing: 0.1em;
          cursor: pointer;
          opacity: 0;
          transform: translateX(20px);
          transition: opacity 0.6s ease-out 0.4s, transform 0.6s ease-out 0.4s, background 0.3s ease;
          z-index: 5;
        }
        .ar-button.show {
          opacity: 1;
          transform: translateX(0);
        }
        .ar-button:hover {
          background: #8B5A62;
          transform: scale(1.05);
        }
        .luxury-viewer-error {
          position: absolute;
          inset: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(15, 23, 42, 0.9);
          z-index: 10;
        }
        .error-text {
          color: #ef4444;
          font-size: 18px;
          font-weight: 300;
          letter-spacing: 0.05em;
        }
      `;
      document.head.appendChild(style);
    }

    createScene() {
      this.scene = new THREE.Scene();
      this.scene.background = new THREE.Color(0x0f172a); // Slate-950
      this.scene.fog = new THREE.Fog(0x0f172a, 10, 50);
    }

    createCamera() {
      const aspect = this.container.clientWidth / this.container.clientHeight;
      this.camera = new THREE.PerspectiveCamera(
        this.config.camera.fov,
        aspect,
        this.config.camera.near,
        this.config.camera.far
      );
      this.camera.position.set(...this.config.camera.position);
    }

    createRenderer() {
      this.renderer = new THREE.WebGLRenderer({
        antialias: !this.isMobile,
        alpha: false,
        powerPreference: this.isMobile ? 'low-power' : 'high-performance',
        preserveDrawingBuffer: true
      });

      this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, this.isMobile ? 1.5 : 2));
      this.renderer.shadowMap.enabled = !this.isMobile;
      this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      this.renderer.toneMapping = this.config.effects.toneMapping;
      this.renderer.toneMappingExposure = this.config.effects.toneMappingExposure;
      this.renderer.outputColorSpace = THREE.SRGBColorSpace;

      this.container.appendChild(this.renderer.domElement);
    }

    createLights() {
      // Ambient light
      const ambient = new THREE.AmbientLight(0xffffff, this.config.lighting.ambient);
      this.scene.add(ambient);
      this.lights.ambient = ambient;

      // Key light (rose gold)
      const keyLight = new THREE.PointLight(
        this.config.lighting.key.color,
        this.config.lighting.key.intensity,
        100
      );
      keyLight.position.set(...this.config.lighting.key.position);
      keyLight.castShadow = !this.isMobile;
      if (keyLight.castShadow) {
        keyLight.shadow.mapSize.width = 1024;
        keyLight.shadow.mapSize.height = 1024;
        keyLight.shadow.camera.near = 0.5;
        keyLight.shadow.camera.far = 50;
      }
      this.scene.add(keyLight);
      this.lights.key = keyLight;

      // Fill light (darker rose)
      const fillLight = new THREE.PointLight(
        this.config.lighting.fill.color,
        this.config.lighting.fill.intensity,
        50
      );
      fillLight.position.set(...this.config.lighting.fill.position);
      this.scene.add(fillLight);
      this.lights.fill = fillLight;

      // Rim light (white)
      const rimLight = new THREE.PointLight(
        this.config.lighting.rim.color,
        this.config.lighting.rim.intensity,
        50
      );
      rimLight.position.set(...this.config.lighting.rim.position);
      this.scene.add(rimLight);
      this.lights.rim = rimLight;

      // Hemisphere light for soft fill
      const hemiLight = new THREE.HemisphereLight(0xB76E79, 0x8B5A62, 0.3);
      this.scene.add(hemiLight);
      this.lights.hemi = hemiLight;

      // Contact shadows plane
      const shadowGeometry = new THREE.PlaneGeometry(20, 20);
      const shadowMaterial = new THREE.ShadowMaterial({ opacity: 0.4 });
      const shadowPlane = new THREE.Mesh(shadowGeometry, shadowMaterial);
      shadowPlane.rotation.x = -Math.PI / 2;
      shadowPlane.position.y = -0.8;
      shadowPlane.receiveShadow = true;
      this.scene.add(shadowPlane);
      this.shadowPlane = shadowPlane;
    }

    createControls() {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = this.config.controls.enableDamping;
      this.controls.dampingFactor = this.config.controls.dampingFactor;
      this.controls.minDistance = this.config.controls.minDistance;
      this.controls.maxDistance = this.config.controls.maxDistance;
      this.controls.minPolarAngle = this.config.controls.minPolarAngle;
      this.controls.maxPolarAngle = this.config.controls.maxPolarAngle;
      this.controls.enablePan = this.config.controls.enablePan;
      this.controls.enableZoom = this.config.controls.enableZoom;
      this.controls.autoRotate = this.config.autoRotate;
      this.controls.autoRotateSpeed = this.config.controls.autoRotateSpeed;
      this.controls.target.set(0, 0, 0);
      this.controls.update();
    }

    createPostProcessing() {
      if (!this.config.showEffects || this.isMobile) {
        return; // Skip post-processing on mobile
      }

      this.composer = new THREE.EffectComposer(this.renderer);

      // Render pass
      const renderPass = new THREE.RenderPass(this.scene, this.camera);
      this.composer.addPass(renderPass);

      // Bloom pass
      const bloomPass = new THREE.UnrealBloomPass(
        new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
        this.config.effects.bloom.strength,
        this.config.effects.bloom.radius,
        this.config.effects.bloom.threshold
      );
      this.composer.addPass(bloomPass);
    }

    createUI() {
      // Product info
      const ui = document.createElement('div');
      ui.className = 'luxury-viewer-ui';

      const name = document.createElement('h3');
      name.className = 'product-name';
      name.textContent = this.config.productName;

      const collection = document.createElement('p');
      collection.className = 'product-collection';
      collection.textContent = 'THE SKYY ROSE COLLECTION';

      ui.appendChild(name);
      ui.appendChild(collection);
      this.container.appendChild(ui);
      this.ui = ui;

      // AR button
      if (this.config.enableAR) {
        const arButton = document.createElement('button');
        arButton.className = 'ar-button';
        arButton.textContent = 'View in AR';
        arButton.addEventListener('click', () => this.launchAR());
        this.container.appendChild(arButton);
        this.arButton = arButton;
      }
    }

    async loadModel() {
      if (!this.config.modelUrl) {
        console.error('LuxuryProductViewer: No model URL provided');
        this.hideLoading();
        return;
      }

      const loader = new THREE.GLTFLoader();

      // Optional: Add DRACOLoader for compressed models
      if (typeof THREE.DRACOLoader !== 'undefined') {
        const dracoLoader = new THREE.DRACOLoader();
        dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
        loader.setDRACOLoader(dracoLoader);
      }

      try {
        const gltf = await loader.loadAsync(this.config.modelUrl);
        this.model = gltf.scene;

        // Apply luxury materials
        this.model.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = !this.isMobile;
            child.receiveShadow = !this.isMobile;

            if (child.material) {
              // PBR material enhancement
              child.material.metalness = 0.9;
              child.material.roughness = 0.1;
              child.material.envMapIntensity = 1.5;

              // Ensure proper lighting
              if (child.material.map) {
                child.material.map.colorSpace = THREE.SRGBColorSpace;
              }
            }
          }
        });

        // Center and fit model
        this.centerModel();
        this.fitCameraToModel();

        this.scene.add(this.model);
        this.hideLoading();
        this.showUI();

      } catch (error) {
        console.error('LuxuryProductViewer: Error loading model', error);
        this.hideLoading();
        this.showError('Failed to load 3D model');
      }
    }

    centerModel() {
      if (!this.model) return;

      const box = new THREE.Box3().setFromObject(this.model);
      const center = box.getCenter(new THREE.Vector3());
      this.model.position.sub(center);
    }

    fitCameraToModel(fitOffset = 1.3) {
      if (!this.model) return;

      const box = new THREE.Box3().setFromObject(this.model);
      const size = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());
      const maxSize = Math.max(size.x, size.y, size.z);

      // Calculate distance
      const fitHeightDistance = maxSize / (2 * Math.atan((Math.PI * this.camera.fov) / 360));
      const distance = fitOffset * fitHeightDistance;

      // Update controls
      this.controls.maxDistance = distance * 10;
      this.controls.minDistance = distance / 10;
      this.controls.target.copy(center);

      // Update camera
      this.camera.near = distance / 100;
      this.camera.far = distance * 100;
      this.camera.updateProjectionMatrix();

      const direction = this.controls.target.clone()
        .sub(this.camera.position)
        .normalize()
        .multiplyScalar(distance);

      this.camera.position.copy(this.controls.target).sub(direction);
      this.controls.update();
    }

    hideLoading() {
      this.isLoading = false;
      if (this.loadingUI) {
        this.loadingUI.classList.add('hide');
        setTimeout(() => {
          this.loadingUI.remove();
          this.loadingUI = null;
        }, 500);
      }
    }

    showUI() {
      if (this.ui) {
        this.ui.classList.add('show');
      }
      if (this.arButton) {
        this.arButton.classList.add('show');
      }
    }

    showError(message) {
      const error = document.createElement('div');
      error.className = 'luxury-viewer-error';

      const content = document.createElement('div');
      content.className = 'error-content';

      const text = document.createElement('p');
      text.className = 'error-text';
      text.textContent = message;

      content.appendChild(text);
      error.appendChild(content);
      this.container.appendChild(error);
    }

    launchAR() {
      if (!this.config.modelUrl) {
        console.warn('LuxuryProductViewer: No model URL for AR');
        return;
      }

      // Create AR quick-look link (iOS)
      const link = document.createElement('a');
      link.rel = 'ar';
      link.href = this.config.modelUrl;

      // Add AR attributes
      const img = document.createElement('img');
      link.appendChild(img);

      // Trigger AR
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Analytics event
      if (typeof gtag !== 'undefined') {
        gtag('event', 'ar_view', {
          product_name: this.config.productName,
          model_url: this.config.modelUrl
        });
      }
    }

    setupEventListeners() {
      // Resize handler
      this.resizeHandler = () => {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();

        this.renderer.setSize(width, height);

        if (this.composer) {
          this.composer.setSize(width, height);
        }

        // Update mobile state
        const wasMobile = this.isMobile;
        this.isMobile = this.checkMobile();

        if (wasMobile !== this.isMobile) {
          // Mobile state changed, recreate some features
          this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, this.isMobile ? 1.5 : 2));
        }
      };

      window.addEventListener('resize', this.resizeHandler);

      // Visibility change (pause when hidden)
      this.visibilityHandler = () => {
        if (document.hidden) {
          this.pause();
        } else {
          this.resume();
        }
      };
      document.addEventListener('visibilitychange', this.visibilityHandler);
    }

    animate() {
      this.animationId = requestAnimationFrame(() => this.animate());

      if (this.controls) {
        this.controls.update();
      }

      if (this.composer && this.config.showEffects && !this.isMobile) {
        this.composer.render();
      } else {
        this.renderer.render(this.scene, this.camera);
      }
    }

    pause() {
      if (this.animationId) {
        cancelAnimationFrame(this.animationId);
        this.animationId = null;
      }
    }

    resume() {
      if (!this.animationId) {
        this.animate();
      }
    }

    destroy() {
      // Stop animation
      this.pause();

      // Remove event listeners
      window.removeEventListener('resize', this.resizeHandler);
      document.removeEventListener('visibilitychange', this.visibilityHandler);

      // Dispose Three.js objects
      if (this.model) {
        this.model.traverse((child) => {
          if (child.isMesh) {
            child.geometry?.dispose();
            if (Array.isArray(child.material)) {
              child.material.forEach(material => material.dispose());
            } else {
              child.material?.dispose();
            }
          }
        });
      }

      if (this.composer) {
        this.composer.dispose();
      }

      this.renderer?.dispose();
      this.controls?.dispose();

      // Remove DOM elements
      if (this.renderer?.domElement?.parentNode) {
        this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
      }

      // Clear references
      this.scene = null;
      this.camera = null;
      this.renderer = null;
      this.controls = null;
      this.composer = null;
      this.model = null;
    }

    // Public API
    setModel(url) {
      if (this.model) {
        this.scene.remove(this.model);
        this.model = null;
      }
      this.config.modelUrl = url;
      this.loadModel();
    }

    setAutoRotate(enabled) {
      this.config.autoRotate = enabled;
      if (this.controls) {
        this.controls.autoRotate = enabled;
      }
    }

    setEnvironment(environment) {
      this.config.environment = environment;
      // TODO: Implement environment switching
    }

    takeScreenshot() {
      if (!this.renderer) return null;
      return this.renderer.domElement.toDataURL('image/png');
    }
  }

  // Export to global scope
  window.LuxuryProductViewer = LuxuryProductViewer;

})(window);
