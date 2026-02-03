/**
 * SIGNATURE Interactive Oakland/SF Tour - WordPress Compatible
 * 
 * 3D map of Oakland and San Francisco with 8 clickable landmarks,
 * teleportation, golden hour lighting, and product billboards.
 * 
 * @package SkyyRose_2025
 * @version 1.0.0
 */

(function() {
  'use strict';

  if (typeof THREE === 'undefined') {
    console.error('THREE.js not loaded');
    return;
  }

  // TWEEN.js fallback (simple implementation if not loaded)
  const TWEEN = window.TWEEN || {
    Tween: function(obj) {
      this.target = obj;
      this.to = function() { return this; };
      this.easing = function() { return this; };
      this.onUpdate = function() { return this; };
      this.onComplete = function() { return this; };
      this.start = function() { return this; };
    },
    Easing: {
      Quadratic: { Out: function(t) { return t * (2 - t); } }
    },
    update: function() {}
  };

  class SignatureLandmarksTour {
    constructor(container, config = {}) {
      this.container = container;
      this.config = {
        backgroundColor: 0xf5f5f0,
        fogColor: 0xf5f5f0,
        fogNear: 10,
        fogFar: 200,
        goldenHourColor: 0xffb347,
        timeOfDay: 'golden-hour', // 'day', 'golden-hour', 'sunset', 'night'
        ...config
      };

      // Three.js core
      this.scene = null;
      this.renderer = null;
      this.camera = null;
      this.controls = null;

      // Landmarks (8 locations)
      this.landmarks = new Map();
      this.currentLandmark = null;
      this.productBillboards = [];

      // State
      this.animationId = null;
      this.clock = new THREE.Clock();
      this.raycaster = new THREE.Raycaster();
      this.mouse = new THREE.Vector2();
      this.hoveredObject = null;
      this.isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
      this.isTeleporting = false;

      // Lighting
      this.sunLight = null;
      this.ambientLight = null;

      // UI Elements
      this.minimap = null;
      this.timeSlider = null;
      this.fogSlider = null;
      this.tourModeToggle = null;
      this.landmarkInfo = null;

      // Callbacks
      this.onProductClickCallback = null;
      this.onLandmarkChangeCallback = null;

      this.init();
    }

    init() {
      this.createScene();
      this.createRenderer();
      this.createCamera();
      this.createControls();
      this.setupLighting();
      this.createLandmarks();
      this.createSkyDome();
      this.createUI();
      this.setupEventListeners();

    }

    createScene() {
      this.scene = new THREE.Scene();
      this.scene.background = new THREE.Color(this.config.backgroundColor);
      this.scene.fog = new THREE.Fog(
        this.config.fogColor,
        this.config.fogNear,
        this.config.fogFar
      );
    }

    createRenderer() {
      this.renderer = new THREE.WebGLRenderer({ 
        antialias: !this.isMobile,
        alpha: true,
        powerPreference: 'high-performance'
      });
      this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, this.isMobile ? 1 : 2));
      this.renderer.shadowMap.enabled = !this.isMobile;
      this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 1.2;
      this.container.appendChild(this.renderer.domElement);
    }

    createCamera() {
      const aspect = this.container.clientWidth / this.container.clientHeight;
      this.camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 500);
      // Start with overview position
      this.camera.position.set(0, 50, 80);
      this.camera.lookAt(0, 0, 0);
    }

    createControls() {
      if (typeof THREE.OrbitControls === 'undefined') {
        console.warn('OrbitControls not available');
        return;
      }

      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.05;
      this.controls.minDistance = 20;
      this.controls.maxDistance = 150;
      this.controls.maxPolarAngle = Math.PI / 2.2;
      this.controls.target.set(0, 0, 0);
      this.controls.update();
    }

    setupLighting() {
      // Golden hour sun (directional light)
      this.sunLight = new THREE.DirectionalLight(0xffb347, 2.5);
      this.sunLight.position.set(50, 40, 30);
      this.sunLight.castShadow = !this.isMobile;
      
      if (!this.isMobile) {
        this.sunLight.shadow.mapSize.width = 2048;
        this.sunLight.shadow.mapSize.height = 2048;
        this.sunLight.shadow.camera.near = 0.5;
        this.sunLight.shadow.camera.far = 200;
        this.sunLight.shadow.camera.left = -100;
        this.sunLight.shadow.camera.right = 100;
        this.sunLight.shadow.camera.top = 100;
        this.sunLight.shadow.camera.bottom = -100;
      }
      
      this.scene.add(this.sunLight);

      // Ambient light (fill)
      this.ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
      this.scene.add(this.ambientLight);

      // Hemisphere light for realistic color from sky
      const hemisphereLight = new THREE.HemisphereLight(0xffffbb, 0x8b7355, 0.5);
      this.scene.add(hemisphereLight);
    }

    createSkyDome() {
      const skyGeometry = new THREE.SphereGeometry(400, 32, 15);
      const skyMaterial = new THREE.ShaderMaterial({
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
          topColor: { value: new THREE.Color(0x87CEEB) }, // Sky blue
          bottomColor: { value: new THREE.Color(0xfff8dc) }, // Cornsilk (horizon)
          offset: { value: 400 },
          exponent: { value: 0.6 }
        },
        side: THREE.BackSide
      });

      const sky = new THREE.Mesh(skyGeometry, skyMaterial);
      this.scene.add(sky);
    }

    createLandmarks() {
      // Base ground (Bay Area terrain)
      const groundGeometry = new THREE.PlaneGeometry(200, 200);
      const groundMaterial = new THREE.MeshStandardMaterial({
        color: 0x8fbc8f,
        roughness: 0.9
      });
      const ground = new THREE.Mesh(groundGeometry, groundMaterial);
      ground.rotation.x = -Math.PI / 2;
      ground.receiveShadow = !this.isMobile;
      this.scene.add(ground);

      // Define 8 landmarks with positions
      const landmarkData = [
        { name: 'Golden Gate Bridge', pos: [-40, 0, -30], color: 0xff6347, height: 25 },
        { name: 'Bay Bridge', pos: [40, 0, -20], color: 0x708090, height: 20 },
        { name: 'Lake Merritt', pos: [20, 0, 30], color: 0x4682b4, height: 5 },
        { name: 'Fox Theater', pos: [15, 0, 35], color: 0xffd700, height: 15 },
        { name: 'Jack London Square', pos: [25, 0, 40], color: 0x8b4513, height: 10 },
        { name: 'Alcatraz', pos: [-30, 0, -40], color: 0x696969, height: 12 },
        { name: 'Coit Tower', pos: [-35, 0, -25], color: 0xf0e68c, height: 18 },
        { name: 'Painted Ladies', pos: [-25, 0, -15], color: 0xffb6c1, height: 8 }
      ];

      landmarkData.forEach(data => {
        const landmark = this.createLandmark(data);
        this.landmarks.set(data.name, landmark);
        this.scene.add(landmark);
      });

    }

    createLandmark(data) {
      const group = new THREE.Group();
      group.name = data.name;
      
      // Low-poly landmark (simple geometric shapes)
      const mainStructure = this.createLowPolyStructure(data);
      group.add(mainStructure);

      // Clickable beacon (glowing marker)
      const beaconGeometry = new THREE.SphereGeometry(1, 8, 6);
      const beaconMaterial = new THREE.MeshStandardMaterial({
        color: 0xd4af37,
        emissive: 0xd4af37,
        emissiveIntensity: 0.5,
        roughness: 0.3,
        metalness: 0.8
      });
      const beacon = new THREE.Mesh(beaconGeometry, beaconMaterial);
      beacon.position.y = data.height + 2;
      beacon.userData = { 
        clickable: true, 
        type: 'landmark',
        landmarkName: data.name
      };
      group.add(beacon);

      // Point light for beacon
      const beaconLight = new THREE.PointLight(0xd4af37, 1.5, 10);
      beaconLight.position.y = data.height + 2;
      group.add(beaconLight);

      group.position.set(...data.pos);
      group.userData = {
        landmarkName: data.name,
        beacon: beacon,
        light: beaconLight
      };

      return group;
    }

    createLowPolyStructure(data) {
      const group = new THREE.Group();
      
      // Simple low-poly representation based on landmark type
      const material = new THREE.MeshStandardMaterial({
        color: data.color,
        flatShading: true,
        roughness: 0.7,
        metalness: 0.2
      });

      if (data.name.includes('Bridge')) {
        // Bridge structure (two towers + deck)
        const towerGeometry = new THREE.BoxGeometry(2, data.height, 2);
        const tower1 = new THREE.Mesh(towerGeometry, material);
        tower1.position.set(-5, data.height / 2, 0);
        tower1.castShadow = !this.isMobile;
        group.add(tower1);

        const tower2 = new THREE.Mesh(towerGeometry, material);
        tower2.position.set(5, data.height / 2, 0);
        tower2.castShadow = !this.isMobile;
        group.add(tower2);

        // Deck
        const deckGeometry = new THREE.BoxGeometry(12, 0.5, 3);
        const deck = new THREE.Mesh(deckGeometry, material);
        deck.position.y = data.height * 0.6;
        deck.castShadow = !this.isMobile;
        group.add(deck);

      } else if (data.name.includes('Tower')) {
        // Tower (cylinder)
        const towerGeometry = new THREE.CylinderGeometry(1, 2, data.height, 6);
        const tower = new THREE.Mesh(towerGeometry, material);
        tower.position.y = data.height / 2;
        tower.castShadow = !this.isMobile;
        group.add(tower);

      } else if (data.name.includes('Lake')) {
        // Lake (flat disc)
        const lakeGeometry = new THREE.CylinderGeometry(8, 8, 0.2, 16);
        const lake = new THREE.Mesh(lakeGeometry, material);
        lake.position.y = 0.1;
        group.add(lake);

      } else {
        // Generic building
        const buildingGeometry = new THREE.BoxGeometry(4, data.height, 4);
        const building = new THREE.Mesh(buildingGeometry, material);
        building.position.y = data.height / 2;
        building.castShadow = !this.isMobile;
        group.add(building);
      }

      return group;
    }

    createUI() {
      // Minimap (top-right corner)
      this.minimap = document.createElement('canvas');
      this.minimap.width = 200;
      this.minimap.height = 200;
      this.minimap.style.cssText = `
        position: absolute;
        top: 20px;
        right: 20px;
        width: 200px;
        height: 200px;
        background: rgba(26, 10, 10, 0.8);
        border: 2px solid rgba(212, 175, 55, 0.5);
        border-radius: 8px;
        z-index: 999;
      `;
      this.container.appendChild(this.minimap);
      this.drawMinimap();

      // Time of day slider
      this.timeSlider = document.createElement('div');
      this.timeSlider.className = 'signature-time-slider';
      this.timeSlider.innerHTML = `
        <label style="color: #d4af37; font-size: 0.9rem; display: block; margin-bottom: 0.5rem;">Time of Day</label>
        <input type="range" min="0" max="3" value="1" step="1" style="width: 100%;">
        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: rgba(212, 175, 55, 0.7); margin-top: 0.25rem;">
          <span>Day</span>
          <span>Golden</span>
          <span>Sunset</span>
          <span>Night</span>
        </div>
      `;
      this.timeSlider.style.cssText = `
        position: absolute;
        bottom: 80px;
        left: 20px;
        background: rgba(26, 10, 10, 0.9);
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 8px;
        padding: 1rem;
        width: 250px;
        z-index: 999;
      `;
      this.container.appendChild(this.timeSlider);

      const timeInput = this.timeSlider.querySelector('input');
      timeInput.addEventListener('input', (e) => {
        const times = ['day', 'golden-hour', 'sunset', 'night'];
        this.setTimeOfDay(times[parseInt(e.target.value)]);
      });

      // Fog slider
      this.fogSlider = document.createElement('div');
      this.fogSlider.className = 'signature-fog-slider';
      this.fogSlider.innerHTML = `
        <label style="color: #d4af37; font-size: 0.9rem; display: block; margin-bottom: 0.5rem;">Fog Density</label>
        <input type="range" min="10" max="200" value="50" step="10" style="width: 100%;">
      `;
      this.fogSlider.style.cssText = `
        position: absolute;
        bottom: 20px;
        left: 20px;
        background: rgba(26, 10, 10, 0.9);
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 8px;
        padding: 1rem;
        width: 250px;
        z-index: 999;
      `;
      this.container.appendChild(this.fogSlider);

      const fogInput = this.fogSlider.querySelector('input');
      fogInput.addEventListener('input', (e) => {
        this.scene.fog.far = parseInt(e.target.value);
      });

      // Tour mode toggle
      this.tourModeToggle = document.createElement('button');
      this.tourModeToggle.textContent = 'Free Roam';
      this.tourModeToggle.style.cssText = `
        position: absolute;
        top: 20px;
        left: 20px;
        background: rgba(212, 175, 55, 0.9);
        border: 1px solid rgba(255, 215, 0, 0.5);
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        color: #1a1a1a;
        font-size: 0.9rem;
        font-weight: 600;
        cursor: pointer;
        z-index: 999;
        transition: all 0.3s ease;
      `;
      this.tourModeToggle.addEventListener('click', () => this.toggleTourMode());
      this.container.appendChild(this.tourModeToggle);

      // Landmark info card
      this.landmarkInfo = document.createElement('div');
      this.landmarkInfo.className = 'signature-landmark-info';
      this.landmarkInfo.style.cssText = `
        position: absolute;
        bottom: 20px;
        right: 20px;
        background: rgba(26, 10, 10, 0.95);
        border: 2px solid rgba(212, 175, 55, 0.5);
        border-radius: 8px;
        padding: 1rem;
        max-width: 300px;
        color: #f5f5f0;
        font-size: 0.9rem;
        z-index: 999;
        display: none;
      `;
      this.container.appendChild(this.landmarkInfo);
    }

    drawMinimap() {
      const ctx = this.minimap.getContext('2d');
      const width = this.minimap.width;
      const height = this.minimap.height;
      const scale = 1.5;

      // Clear
      ctx.fillStyle = 'rgba(26, 10, 10, 0.9)';
      ctx.fillRect(0, 0, width, height);

      // Draw landmarks
      this.landmarks.forEach((landmark, name) => {
        const x = (landmark.position.x + 50) * scale + width / 2 - 75;
        const z = (landmark.position.z + 50) * scale + height / 2 - 75;

        // Landmark dot
        ctx.fillStyle = '#d4af37';
        ctx.beginPath();
        ctx.arc(x, z, 5, 0, Math.PI * 2);
        ctx.fill();

        // Label (small)
        ctx.fillStyle = '#f5f5f0';
        ctx.font = '8px Arial';
        ctx.fillText(name.split(' ')[0], x + 8, z + 3);
      });

      // Camera position indicator
      const camX = (this.camera.position.x + 50) * scale + width / 2 - 75;
      const camZ = (this.camera.position.z + 50) * scale + height / 2 - 75;
      ctx.strokeStyle = '#ff6347';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(camX, camZ, 8, 0, Math.PI * 2);
      ctx.stroke();
    }

    setupEventListeners() {
      this.container.addEventListener('mousemove', this.onMouseMove.bind(this));
      this.container.addEventListener('click', this.onClick.bind(this));
      
      if (this.isMobile) {
        this.container.addEventListener('touchstart', this.onTouchStart.bind(this), { passive: false });
      }

      window.addEventListener('resize', this.onResize.bind(this));
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

    onClick(event) {
      this.raycaster.setFromCamera(this.mouse, this.camera);
      
      // Check clickable beacons
      const clickableObjects = [];
      this.landmarks.forEach(landmark => {
        const beacon = landmark.userData.beacon;
        if (beacon) clickableObjects.push(beacon);
      });

      const intersects = this.raycaster.intersectObjects(clickableObjects, true);

      if (intersects.length > 0) {
        const object = intersects[0].object;
        const landmarkName = object.userData.landmarkName;
        
        if (landmarkName) {
          this.teleportToLandmark(landmarkName);
        }
      }
    }

    checkHover() {
      this.raycaster.setFromCamera(this.mouse, this.camera);
      
      const clickableObjects = [];
      this.landmarks.forEach(landmark => {
        const beacon = landmark.userData.beacon;
        if (beacon) clickableObjects.push(beacon);
      });

      const intersects = this.raycaster.intersectObjects(clickableObjects, true);

      if (intersects.length > 0) {
        const landmarkName = intersects[0].object.userData.landmarkName;
        this.container.style.cursor = 'pointer';
        this.showLandmarkInfo(landmarkName);
      } else {
        this.container.style.cursor = 'default';
        this.hideLandmarkInfo();
      }
    }

    teleportToLandmark(landmarkName) {
      if (this.isTeleporting) return;

      const landmark = this.landmarks.get(landmarkName);
      if (!landmark) return;

      this.isTeleporting = true;
      this.currentLandmark = landmarkName;

      // Calculate camera target (close-up view)
      const targetPos = landmark.position.clone();
      targetPos.y += 15;
      targetPos.z += 20;

      // Animate camera using TWEEN.js
      const currentPos = this.camera.position.clone();
      const duration = 2000;

      if (this.controls) {
        this.controls.enabled = false;
      }

      new TWEEN.Tween(currentPos)
        .to({
          x: targetPos.x,
          y: targetPos.y,
          z: targetPos.z
        }, duration)
        .easing(TWEEN.Easing.Quadratic.Out)
        .onUpdate(() => {
          this.camera.position.copy(currentPos);
          this.camera.lookAt(landmark.position);
        })
        .onComplete(() => {
          if (this.controls) {
            this.controls.target.copy(landmark.position);
            this.controls.enabled = true;
            this.controls.update();
          }
          this.isTeleporting = false;

          if (this.onLandmarkChangeCallback) {
            this.onLandmarkChangeCallback(landmarkName);
          }
        })
        .start();

    }

    showLandmarkInfo(landmarkName) {
      this.landmarkInfo.innerHTML = `
        <h3 style="margin: 0 0 0.5rem 0; color: #d4af37; font-family: 'Playfair Display', serif;">${landmarkName}</h3>
        <p style="margin: 0; font-size: 0.85rem; line-height: 1.5;">Click to visit this landmark and explore SkyyRose products.</p>
      `;
      this.landmarkInfo.style.display = 'block';
    }

    hideLandmarkInfo() {
      this.landmarkInfo.style.display = 'none';
    }

    setTimeOfDay(time) {
      const times = {
        'day': { 
          sunColor: 0xffffff, 
          sunIntensity: 3, 
          ambientIntensity: 0.8,
          skyTop: 0x87CEEB,
          skyBottom: 0xfff8dc
        },
        'golden-hour': { 
          sunColor: 0xffb347, 
          sunIntensity: 2.5, 
          ambientIntensity: 0.6,
          skyTop: 0xffa07a,
          skyBottom: 0xffe4b5
        },
        'sunset': { 
          sunColor: 0xff6347, 
          sunIntensity: 2, 
          ambientIntensity: 0.4,
          skyTop: 0xff4500,
          skyBottom: 0xffd700
        },
        'night': { 
          sunColor: 0x4682b4, 
          sunIntensity: 0.5, 
          ambientIntensity: 0.2,
          skyTop: 0x000033,
          skyBottom: 0x1a1a2e
        }
      };

      const settings = times[time] || times['golden-hour'];
      
      this.sunLight.color.setHex(settings.sunColor);
      this.sunLight.intensity = settings.sunIntensity;
      this.ambientLight.intensity = settings.ambientIntensity;

    }

    toggleTourMode() {
      const isGuidedTour = this.tourModeToggle.textContent === 'Free Roam';
      this.tourModeToggle.textContent = isGuidedTour ? 'Guided Tour' : 'Free Roam';
      
      if (isGuidedTour) {
        // Start guided tour (auto-play through landmarks)
      }
    }

    onResize() {
      const width = this.container.clientWidth;
      const height = this.container.clientHeight;
      
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
      
      this.renderer.setSize(width, height);
    }

    // ===========================================================================
    // Public API
    // ===========================================================================

    async loadProducts(products) {
      products.forEach(product => {
        this.createProductBillboard(product);
      });
      
    }

    createProductBillboard(product) {
      const billboard = new THREE.Group();
      
      // Billboard post
      const postGeometry = new THREE.CylinderGeometry(0.1, 0.1, 3, 8);
      const postMaterial = new THREE.MeshStandardMaterial({
        color: 0x8b7355,
        roughness: 0.7
      });
      const post = new THREE.Mesh(postGeometry, postMaterial);
      post.position.y = 1.5;
      billboard.add(post);

      // Billboard sign
      const signGeometry = new THREE.PlaneGeometry(2, 1.5);
      const signMaterial = new THREE.MeshStandardMaterial({
        color: 0xd4af37,
        side: THREE.DoubleSide
      });
      const sign = new THREE.Mesh(signGeometry, signMaterial);
      sign.position.y = 4;
      sign.userData = { 
        clickable: true, 
        type: 'product',
        product: product
      };
      billboard.add(sign);

      billboard.position.set(...product.position);
      this.scene.add(billboard);
      this.productBillboards.push(billboard);
    }

    setOnProductClick(handler) {
      this.onProductClickCallback = handler;
    }

    setOnLandmarkChange(handler) {
      this.onLandmarkChangeCallback = handler;
    }

    start() {
      const animate = () => {
        this.animationId = requestAnimationFrame(animate);
        
        TWEEN.update();
        
        if (this.controls) {
          this.controls.update();
        }

        // Update minimap periodically
        if (Math.floor(this.clock.getElapsedTime() * 2) % 10 === 0) {
          this.drawMinimap();
        }

        this.renderer.render(this.scene, this.camera);
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
      
      window.removeEventListener('resize', this.onResize.bind(this));
      
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
      this.renderer.dispose();

      if (this.minimap) this.minimap.remove();
      if (this.timeSlider) this.timeSlider.remove();
      if (this.fogSlider) this.fogSlider.remove();
      if (this.tourModeToggle) this.tourModeToggle.remove();
      if (this.landmarkInfo) this.landmarkInfo.remove();

    }
  }

  // Export to global scope for WordPress
  window.SignatureLandmarksTour = SignatureLandmarksTour;

})();
