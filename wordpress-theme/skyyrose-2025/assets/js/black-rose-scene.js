/**
 * BLACK ROSE Interactive Experience - WordPress Compatible
 * 
 * Gothic rose garden with clickable roses, draggable camera, product hotspots.
 * Vanilla Three.js implementation for WordPress integration.
 * 
 * @package SkyyRose_2025
 * @version 1.0.0
 */

(function() {
  'use strict';

  // Wait for DOM and Three.js to load
  if (typeof THREE === 'undefined') {
    console.error('THREE.js not loaded');
    return;
  }

  class BlackRoseExperience {
    constructor(container, config = {}) {
      this.container = container;
      this.config = {
        backgroundColor: 0x0d0d0d,
        fogColor: 0x0a0a0a,
        fogDensity: 0.03,
        moonlightColor: 0xc0c0c0,
        moonlightIntensity: 0.8,
        petalCount: 50,
        enableBloom: true,
        bloomStrength: 0.4,
        ...config
      };

      // Three.js core
      this.scene = null;
      this.renderer = null;
      this.camera = null;
      this.controls = null;
      this.composer = null;

      // Scene objects
      this.roseBushes = new Map();
      this.petals = [];
      this.clouds = [];
      this.productHotspots = [];

      // State
      this.animationId = null;
      this.clock = new THREE.Clock();
      this.raycaster = new THREE.Raycaster();
      this.mouse = new THREE.Vector2();
      this.hoveredProduct = null;
      this.isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

      // UI Elements
      this.productCard = null;
      this.minimap = null;
      this.progressIndicator = null;
      this.exploreToggle = null;
      this.muteToggle = null;

      // Callbacks
      this.onProductClickCallback = null;
      this.onProductHoverCallback = null;

      this.init();
    }

    init() {
      this.createScene();
      this.createRenderer();
      this.createCamera();
      this.createControls();
      
      if (this.config.enableBloom && typeof THREE.EffectComposer !== 'undefined') {
        this.setupPostProcessing();
      }

      this.setupEnvironment();
      this.setupLighting();
      this.createUI();
      this.setupEventListeners();

    }

    createScene() {
      this.scene = new THREE.Scene();
      this.scene.background = new THREE.Color(this.config.backgroundColor);
      this.scene.fog = new THREE.FogExp2(this.config.fogColor, this.config.fogDensity);
    }

    createRenderer() {
      this.renderer = new THREE.WebGLRenderer({ 
        antialias: !this.isMobile, // Disable on mobile for performance
        alpha: true,
        powerPreference: 'high-performance'
      });
      this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, this.isMobile ? 1 : 2));
      this.renderer.shadowMap.enabled = !this.isMobile;
      this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 0.8;
      this.container.appendChild(this.renderer.domElement);
    }

    createCamera() {
      const aspect = this.container.clientWidth / this.container.clientHeight;
      this.camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 100);
      this.camera.position.set(0, 3, 12);
    }

    createControls() {
      if (typeof THREE.OrbitControls === 'undefined') {
        console.warn('OrbitControls not available');
        return;
      }

      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.05;
      this.controls.maxPolarAngle = Math.PI / 2.1;
      this.controls.minDistance = 5;
      this.controls.maxDistance = this.isMobile ? 20 : 25;
      this.controls.target.set(0, 1, 0);
      this.controls.update();

      // Mobile: Disable rotation on touch (allow pan only)
      if (this.isMobile) {
        this.controls.enableRotate = true;
        this.controls.touches = {
          ONE: THREE.TOUCH.ROTATE,
          TWO: THREE.TOUCH.DOLLY_PAN
        };
      }
    }

    setupPostProcessing() {
      if (typeof THREE.EffectComposer === 'undefined') return;

      this.composer = new THREE.EffectComposer(this.renderer);
      const renderPass = new THREE.RenderPass(this.scene, this.camera);
      this.composer.addPass(renderPass);

      if (typeof THREE.UnrealBloomPass !== 'undefined') {
        const bloomPass = new THREE.UnrealBloomPass(
          new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
          this.config.bloomStrength,
          0.4,
          0.85
        );
        this.composer.addPass(bloomPass);
      }
    }

    setupEnvironment() {
      // Night sky gradient
      this.createNightSky();

      // Moving clouds (reduced count for mobile)
      this.createMovingClouds(this.isMobile ? 6 : 12);

      // Obsidian pathway
      const pathGeometry = new THREE.PlaneGeometry(4, 30);
      const pathMaterial = new THREE.MeshStandardMaterial({
        color: 0x1a1a1a,
        roughness: 0.2,
        metalness: 0.9,
      });
      const path = new THREE.Mesh(pathGeometry, pathMaterial);
      path.rotation.x = -Math.PI / 2;
      path.receiveShadow = !this.isMobile;
      this.scene.add(path);

      // Ground plane
      const groundGeometry = new THREE.PlaneGeometry(50, 50);
      const groundMaterial = new THREE.MeshStandardMaterial({
        color: 0x0a0a0a,
        roughness: 0.9,
      });
      const ground = new THREE.Mesh(groundGeometry, groundMaterial);
      ground.rotation.x = -Math.PI / 2;
      ground.position.y = -0.01;
      ground.receiveShadow = !this.isMobile;
      this.scene.add(ground);

      // Floating silver petals
      this.createFloatingPetals();
    }

    setupLighting() {
      // Silver moonlight (main directional)
      const moonlight = new THREE.DirectionalLight(
        this.config.moonlightColor,
        this.config.moonlightIntensity
      );
      moonlight.position.set(-10, 15, -10);
      moonlight.castShadow = !this.isMobile;
      
      if (!this.isMobile) {
        moonlight.shadow.mapSize.width = 2048;
        moonlight.shadow.mapSize.height = 2048;
        moonlight.shadow.camera.near = 0.5;
        moonlight.shadow.camera.far = 50;
      }
      
      this.scene.add(moonlight);

      // Dim ambient
      const ambient = new THREE.AmbientLight(0x1a1a2e, 0.2);
      this.scene.add(ambient);

      // Silver rim light
      const rimLight = new THREE.DirectionalLight(0xc0c0c0, 0.3);
      rimLight.position.set(10, 5, 10);
      this.scene.add(rimLight);
    }

    createNightSky() {
      const skyGeo = new THREE.SphereGeometry(500, 32, 15);
      const skyMat = new THREE.ShaderMaterial({
        vertexShader: `
          varying vec3 vWorldPosition;
          void main() {
            vec4 worldPosition = modelMatrix * vec4(position, 1.0);
            vWorldPosition = worldPosition.xyz;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `,
        fragmentShader: `
          uniform vec3 topColor;
          uniform vec3 bottomColor;
          uniform float offset;
          uniform float exponent;
          varying vec3 vWorldPosition;
          void main() {
            float h = normalize(vWorldPosition + offset).y;
            gl_FragColor = vec4(mix(bottomColor, topColor, max(pow(max(h, 0.0), exponent), 0.0)), 1.0);
          }
        `,
        uniforms: {
          topColor: { value: new THREE.Color(0x0a0a1a) },
          bottomColor: { value: new THREE.Color(0x000000) },
          offset: { value: 400 },
          exponent: { value: 0.6 }
        },
        side: THREE.BackSide
      });
      
      const sky = new THREE.Mesh(skyGeo, skyMat);
      this.scene.add(sky);
    }

    createMovingClouds(count) {
      const canvas = document.createElement('canvas');
      canvas.width = 128;
      canvas.height = 128;
      const ctx = canvas.getContext('2d');

      if (!ctx) return;

      // Create cloud texture
      const gradient = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
      gradient.addColorStop(0, 'rgba(30, 30, 40, 0.8)');
      gradient.addColorStop(0.5, 'rgba(20, 20, 30, 0.4)');
      gradient.addColorStop(1, 'rgba(10, 10, 20, 0)');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, 128, 128);

      const cloudTexture = new THREE.CanvasTexture(canvas);

      for (let i = 0; i < count; i++) {
        const cloudMaterial = new THREE.SpriteMaterial({
          map: cloudTexture,
          transparent: true,
          opacity: 0.3,
          depthWrite: false
        });

        const cloud = new THREE.Sprite(cloudMaterial);
        cloud.position.set(
          (Math.random() - 0.5) * 100,
          20 + Math.random() * 30,
          (Math.random() - 0.5) * 100
        );

        const scale = 15 + Math.random() * 20;
        cloud.scale.set(scale, scale * 0.5, 1);

        cloud.userData = {
          speedX: Math.random() * 0.2 + 0.1,
          speedZ: Math.random() * 0.1,
          initialX: cloud.position.x,
          initialZ: cloud.position.z
        };

        this.scene.add(cloud);
        this.clouds.push(cloud);
      }
    }

    createFloatingPetals() {
      // Reduce petal count on mobile
      const count = this.isMobile ? Math.floor(this.config.petalCount / 2) : this.config.petalCount;
      
      const petalGeometry = new THREE.PlaneGeometry(0.15, 0.2);
      const petalMaterial = new THREE.MeshStandardMaterial({
        color: 0xc0c0c0,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.7,
        emissive: 0xc0c0c0,
        emissiveIntensity: 0.2
      });

      for (let i = 0; i < count; i++) {
        const petal = new THREE.Mesh(petalGeometry, petalMaterial.clone());
        petal.position.set(
          (Math.random() - 0.5) * 20,
          Math.random() * 8 + 1,
          (Math.random() - 0.5) * 20
        );
        petal.rotation.set(
          Math.random() * Math.PI,
          Math.random() * Math.PI,
          Math.random() * Math.PI
        );
        petal.userData = {
          initialY: petal.position.y,
          speed: Math.random() * 0.5 + 0.2,
          rotationSpeed: Math.random() * 0.02 - 0.01
        };
        this.scene.add(petal);
        this.petals.push(petal);
      }
    }

    createUI() {
      // Product card popup
      this.productCard = document.createElement('div');
      this.productCard.className = 'black-rose-product-card';
      this.productCard.style.cssText = `
        position: absolute;
        display: none;
        background: rgba(10, 10, 10, 0.95);
        border: 1px solid rgba(192, 192, 192, 0.3);
        border-radius: 8px;
        padding: 1rem;
        max-width: 300px;
        backdrop-filter: blur(10px);
        z-index: 1000;
        pointer-events: none;
      `;
      this.container.appendChild(this.productCard);

      // Minimap
      this.minimap = document.createElement('div');
      this.minimap.className = 'black-rose-minimap';
      this.minimap.style.cssText = `
        position: absolute;
        bottom: 20px;
        right: 20px;
        width: 150px;
        height: 150px;
        background: rgba(10, 10, 10, 0.8);
        border: 1px solid rgba(192, 192, 192, 0.3);
        border-radius: 8px;
        z-index: 999;
      `;
      this.container.appendChild(this.minimap);

      // Progress indicator
      this.progressIndicator = document.createElement('div');
      this.progressIndicator.className = 'black-rose-progress';
      this.progressIndicator.style.cssText = `
        position: absolute;
        top: 20px;
        right: 20px;
        background: rgba(10, 10, 10, 0.8);
        border: 1px solid rgba(192, 192, 192, 0.3);
        border-radius: 20px;
        padding: 0.5rem 1rem;
        color: #c0c0c0;
        font-size: 0.9rem;
        z-index: 999;
      `;
      this.progressIndicator.textContent = '0 of 0 discovered';
      this.container.appendChild(this.progressIndicator);

      // Explore mode toggle
      this.exploreToggle = document.createElement('button');
      this.exploreToggle.className = 'black-rose-explore-toggle';
      this.exploreToggle.textContent = 'Free Roam';
      this.exploreToggle.style.cssText = `
        position: absolute;
        top: 20px;
        left: 20px;
        background: rgba(139, 0, 0, 0.8);
        border: 1px solid rgba(220, 20, 60, 0.5);
        border-radius: 20px;
        padding: 0.5rem 1rem;
        color: #fff;
        font-size: 0.9rem;
        cursor: pointer;
        z-index: 999;
        transition: all 0.3s ease;
      `;
      this.exploreToggle.addEventListener('click', () => this.toggleExploreMode());
      this.container.appendChild(this.exploreToggle);

      // Mute toggle
      this.muteToggle = document.createElement('button');
      this.muteToggle.className = 'black-rose-mute-toggle';
      this.muteToggle.textContent = '🔊';
      this.muteToggle.style.cssText = `
        position: absolute;
        bottom: 20px;
        left: 20px;
        background: rgba(10, 10, 10, 0.8);
        border: 1px solid rgba(192, 192, 192, 0.3);
        border-radius: 50%;
        width: 40px;
        height: 40px;
        color: #c0c0c0;
        font-size: 1.2rem;
        cursor: pointer;
        z-index: 999;
        display: flex;
        align-items: center;
        justify-content: center;
      `;
      this.muteToggle.addEventListener('click', () => this.toggleMute());
      this.container.appendChild(this.muteToggle);
    }

    setupEventListeners() {
      this.container.addEventListener('mousemove', this.onMouseMove.bind(this));
      this.container.addEventListener('click', this.onClick.bind(this));
      
      // Touch events for mobile
      if (this.isMobile) {
        this.container.addEventListener('touchstart', this.onTouchStart.bind(this), { passive: false });
        this.container.addEventListener('touchmove', this.onTouchMove.bind(this), { passive: false });
      }

      window.addEventListener('resize', this.onResize.bind(this));
      
      // Keyboard controls
      document.addEventListener('keydown', this.onKeyDown.bind(this));
    }

    onMouseMove(event) {
      const rect = this.container.getBoundingClientRect();
      this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      this.checkHover();
    }

    onTouchStart(event) {
      if (event.touches.length === 1) {
        const touch = event.touches[0];
        const rect = this.container.getBoundingClientRect();
        this.mouse.x = ((touch.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((touch.clientY - rect.top) / rect.height) * 2 + 1;
      }
    }

    onTouchMove(event) {
      if (event.touches.length === 1) {
        const touch = event.touches[0];
        const rect = this.container.getBoundingClientRect();
        this.mouse.x = ((touch.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((touch.clientY - rect.top) / rect.height) * 2 + 1;
        this.checkHover();
      }
    }

    onClick(event) {
      this.raycaster.setFromCamera(this.mouse, this.camera);
      const objects = Array.from(this.roseBushes.values());
      const intersects = this.raycaster.intersectObjects(objects, true);

      if (intersects.length > 0) {
        const firstIntersect = intersects[0];
        const productId = this.findProductId(firstIntersect.object);
        
        if (productId) {
          const product = this.getProductById(productId);
          if (product && this.onProductClickCallback) {
            this.onProductClickCallback(product);
          }
        }
      }
    }

    onKeyDown(event) {
      if (!this.controls) return;

      const moveSpeed = 0.5;
      switch(event.key) {
        case 'ArrowUp':
        case 'w':
        case 'W':
          this.camera.position.z -= moveSpeed;
          break;
        case 'ArrowDown':
        case 's':
        case 'S':
          this.camera.position.z += moveSpeed;
          break;
        case 'ArrowLeft':
        case 'a':
        case 'A':
          this.camera.position.x -= moveSpeed;
          break;
        case 'ArrowRight':
        case 'd':
        case 'D':
          this.camera.position.x += moveSpeed;
          break;
      }
    }

    checkHover() {
      this.raycaster.setFromCamera(this.mouse, this.camera);
      const objects = Array.from(this.roseBushes.values());
      const intersects = this.raycaster.intersectObjects(objects, true);

      if (intersects.length > 0) {
        const productId = this.findProductId(intersects[0].object);
        
        if (productId !== this.hoveredProduct) {
          this.hoveredProduct = productId;
          this.container.style.cursor = 'pointer';
          
          const product = this.getProductById(productId);
          if (product) {
            this.showProductCard(product);
            if (this.onProductHoverCallback) {
              this.onProductHoverCallback(product);
            }
          }
        }
      } else {
        if (this.hoveredProduct) {
          this.hoveredProduct = null;
          this.container.style.cursor = 'default';
          this.hideProductCard();
          if (this.onProductHoverCallback) {
            this.onProductHoverCallback(null);
          }
        }
      }
    }

    findProductId(obj) {
      let current = obj;
      while (current) {
        if (current.userData && current.userData.productId) {
          return current.userData.productId;
        }
        current = current.parent;
      }
      return null;
    }

    getProductById(id) {
      for (const [productId, bush] of this.roseBushes) {
        if (productId === id) {
          return bush.userData.product;
        }
      }
      return null;
    }

    showProductCard(product) {
      this.productCard.innerHTML = `
        <h3 style="color: #fff; margin: 0 0 0.5rem 0; font-size: 1.1rem;">${product.name}</h3>
        <p style="color: #c0c0c0; margin: 0 0 0.5rem 0; font-size: 0.9rem;">$${product.price}</p>
        <button style="
          width: 100%;
          padding: 0.5rem;
          background: linear-gradient(90deg, transparent, rgba(139, 0, 0, 0.3), transparent);
          border: 1px solid #8b0000;
          color: #fff;
          cursor: pointer;
          border-radius: 4px;
        ">Quick View</button>
      `;
      this.productCard.style.display = 'block';
      this.productCard.style.left = '50%';
      this.productCard.style.top = '50%';
      this.productCard.style.transform = 'translate(-50%, -50%)';
    }

    hideProductCard() {
      this.productCard.style.display = 'none';
    }

    onResize() {
      const width = this.container.clientWidth;
      const height = this.container.clientHeight;
      
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
      
      this.renderer.setSize(width, height);
      
      if (this.composer) {
        this.composer.setSize(width, height);
      }
    }

    toggleExploreMode() {
      // Toggle between guided tour and free roam
      this.exploreToggle.textContent = 
        this.exploreToggle.textContent === 'Free Roam' ? 'Guided Tour' : 'Free Roam';
    }

    toggleMute() {
      this.muteToggle.textContent = this.muteToggle.textContent === '🔊' ? '🔇' : '🔊';
    }

    // ===========================================================================
    // Public API
    // ===========================================================================

    async loadProducts(products) {
      for (const product of products) {
        await this.createRoseBush(product);
      }
      
      // Update progress indicator
      this.progressIndicator.textContent = `0 of ${products.length} discovered`;
      
    }

    async createRoseBush(product) {
      const bush = new THREE.Group();
      bush.userData = { 
        productId: product.id, 
        product: product 
      };

      // Rose bush base
      const baseGeometry = new THREE.SphereGeometry(0.8, 16, 12);
      const baseMaterial = new THREE.MeshStandardMaterial({
        color: 0x1a1a1a,
        roughness: 0.7
      });
      const base = new THREE.Mesh(baseGeometry, baseMaterial);
      base.scale.y = 0.6;
      bush.add(base);

      // Black roses (3-5 per bush)
      const roseCount = 3 + Math.floor(Math.random() * 3);
      for (let i = 0; i < roseCount; i++) {
        const rose = this.createRose(0x0d0d0d);
        rose.position.set(
          (Math.random() - 0.5) * 0.6,
          0.3 + Math.random() * 0.4,
          (Math.random() - 0.5) * 0.6
        );
        rose.scale.setScalar(0.15 + Math.random() * 0.1);
        bush.add(rose);
      }

      // Silver accent rose
      const silverRose = this.createRose(0xc0c0c0);
      silverRose.position.set(0, 0.6, 0);
      silverRose.scale.setScalar(0.2);
      bush.add(silverRose);

      bush.position.set(...product.position);
      bush.castShadow = !this.isMobile;
      this.scene.add(bush);
      this.roseBushes.set(product.id, bush);
    }

    createRose(color) {
      const rose = new THREE.Group();
      const petalCount = 8;
      const petalGeometry = new THREE.SphereGeometry(0.5, 8, 6);
      const petalMaterial = new THREE.MeshStandardMaterial({
        color: color,
        roughness: 0.4,
        metalness: 0.1
      });

      for (let i = 0; i < petalCount; i++) {
        const petal = new THREE.Mesh(petalGeometry, petalMaterial);
        const angle = (i / petalCount) * Math.PI * 2;
        const radius = 0.3;
        petal.position.set(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
        petal.scale.set(0.5, 0.3, 0.8);
        petal.rotation.y = angle;
        rose.add(petal);
      }

      // Center (rose gold accent)
      const centerGeometry = new THREE.SphereGeometry(0.2, 8, 8);
      const centerMaterial = new THREE.MeshStandardMaterial({
        color: 0xd4af37,
        roughness: 0.2,
        metalness: 0.8,
        emissive: 0xd4af37,
        emissiveIntensity: 0.1
      });
      const center = new THREE.Mesh(centerGeometry, centerMaterial);
      rose.add(center);

      return rose;
    }

    setOnProductClick(handler) {
      this.onProductClickCallback = handler;
    }

    setOnProductHover(handler) {
      this.onProductHoverCallback = handler;
    }

    animatePetals(elapsed) {
      for (const petal of this.petals) {
        const initialY = petal.userData.initialY;
        const speed = petal.userData.speed;
        const rotationSpeed = petal.userData.rotationSpeed;
        
        petal.position.y = initialY + Math.sin(elapsed * speed) * 0.5;
        petal.rotation.x += rotationSpeed;
        petal.rotation.z += rotationSpeed * 0.5;
      }

      // Animate clouds
      for (const cloud of this.clouds) {
        const speedX = cloud.userData.speedX;
        const speedZ = cloud.userData.speedZ;
        cloud.position.x += speedX * 0.01;
        cloud.position.z += speedZ * 0.01;

        // Wrap around
        if (cloud.position.x > 50) cloud.position.x = -50;
        if (cloud.position.x < -50) cloud.position.x = 50;
        if (cloud.position.z > 50) cloud.position.z = -50;
        if (cloud.position.z < -50) cloud.position.z = 50;
      }
    }

    start() {
      const animate = () => {
        this.animationId = requestAnimationFrame(animate);
        const elapsed = this.clock.getElapsedTime();
        
        this.animatePetals(elapsed);
        
        if (this.controls) {
          this.controls.update();
        }

        if (this.composer) {
          this.composer.render();
        } else {
          this.renderer.render(this.scene, this.camera);
        }
      };
      
      animate();
    }

    stop() {
      if (this.animationId) {
        cancelAnimationFrame(this.animationId);
        this.animationId = null;
      }
    }

    dispose() {
      this.stop();
      
      // Remove event listeners
      window.removeEventListener('resize', this.onResize.bind(this));
      document.removeEventListener('keydown', this.onKeyDown.bind(this));
      
      // Dispose Three.js objects
      this.scene.traverse((object) => {
        if (object.geometry) object.geometry.dispose();
        if (object.material) {
          if (Array.isArray(object.material)) {
            object.material.forEach(material => material.dispose());
          } else {
            object.material.dispose();
          }
        }
      });

      if (this.controls) this.controls.dispose();
      if (this.composer) this.composer.dispose();
      this.renderer.dispose();

      // Remove UI elements
      if (this.productCard) this.productCard.remove();
      if (this.minimap) this.minimap.remove();
      if (this.progressIndicator) this.progressIndicator.remove();
      if (this.exploreToggle) this.exploreToggle.remove();
      if (this.muteToggle) this.muteToggle.remove();

    }
  }

  // Export to global scope for WordPress
  window.BlackRoseExperience = BlackRoseExperience;

})();
