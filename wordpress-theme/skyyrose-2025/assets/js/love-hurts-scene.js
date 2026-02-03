/**
 * LOVE HURTS Interactive Castle Experience - WordPress Compatible
 * 
 * Gothic castle interior with multiple explorable rooms, interactive elements,
 * enchanted rose centerpiece, and product hotspots.
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

  class LoveHurtsCastleExperience {
    constructor(container, config = {}) {
      this.container = container;
      this.config = {
        backgroundColor: 0x1a0a0a,
        fogColor: 0x1a0a0a,
        fogDensity: 0.02,
        ambientIntensity: 0.3,
        enableBloom: true,
        ...config
      };

      // Three.js core
      this.scene = null;
      this.renderer = null;
      this.camera = null;
      this.controls = null;

      // Castle rooms
      this.rooms = new Map();
      this.currentRoom = 'grand-hall';
      this.roomTransitioning = false;

      // Interactive elements
      this.doors = [];
      this.candelabras = [];
      this.mirrors = [];
      this.productPedestals = [];
      this.enchantedRose = null;
      this.petals = [];

      // State
      this.animationId = null;
      this.clock = new THREE.Clock();
      this.raycaster = new THREE.Raycaster();
      this.mouse = new THREE.Vector2();
      this.hoveredObject = null;
      this.isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

      // Lighting state
      this.lightsOn = new Map();

      // UI Elements
      this.roomLabel = null;
      this.navigationArrows = null;
      this.audioToggle = null;

      // Callbacks
      this.onProductClickCallback = null;
      this.onRoomChangeCallback = null;

      this.init();
    }

    init() {
      this.createScene();
      this.createRenderer();
      this.createCamera();
      this.createControls();
      this.setupLighting();
      this.createCastleArchitecture();
      this.createEnchantedRose();
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
        antialias: !this.isMobile,
        alpha: true,
        powerPreference: 'high-performance'
      });
      this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, this.isMobile ? 1 : 2));
      this.renderer.shadowMap.enabled = !this.isMobile;
      this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 0.6;
      this.container.appendChild(this.renderer.domElement);
    }

    createCamera() {
      const aspect = this.container.clientWidth / this.container.clientHeight;
      this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 100);
      // Start in Grand Hall
      this.camera.position.set(0, 2, 8);
      this.camera.lookAt(0, 2, 0);
    }

    createControls() {
      if (typeof THREE.OrbitControls === 'undefined') {
        console.warn('OrbitControls not available');
        return;
      }

      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.05;
      this.controls.minDistance = 3;
      this.controls.maxDistance = 15;
      this.controls.maxPolarAngle = Math.PI / 2.1;
      this.controls.target.set(0, 2, 0);
      this.controls.update();
    }

    setupLighting() {
      // Dim ambient (moonlight through windows)
      const ambient = new THREE.AmbientLight(0xb76e79, this.config.ambientIntensity);
      this.scene.add(ambient);

      // Main chandelier light (center of grand hall)
      const chandelier = new THREE.PointLight(0xdc143c, 2, 20);
      chandelier.position.set(0, 5, 0);
      chandelier.castShadow = !this.isMobile;
      this.scene.add(chandelier);

      // Rim light for dramatic effect
      const rimLight = new THREE.DirectionalLight(0xb76e79, 0.5);
      rimLight.position.set(10, 8, 5);
      this.scene.add(rimLight);
    }

    createCastleArchitecture() {
      // Grand Hall (main room)
      this.createGrandHall();

      // Gallery (lookbook images)
      this.createGallery();

      // Chamber (exclusive items)
      this.createChamber();

      // Courtyard (outdoor products)
      this.createCourtyard();

      // Connect rooms with doors
      this.createDoors();

      // Add candelabras for interactive lighting
      this.createCandelabras();
    }

    createGrandHall() {
      const room = new THREE.Group();
      room.name = 'grand-hall';

      // Floor (dark stone)
      const floorGeometry = new THREE.PlaneGeometry(20, 20);
      const floorMaterial = new THREE.MeshStandardMaterial({
        color: 0x2a1a1a,
        roughness: 0.8,
        metalness: 0.1
      });
      const floor = new THREE.Mesh(floorGeometry, floorMaterial);
      floor.rotation.x = -Math.PI / 2;
      floor.receiveShadow = !this.isMobile;
      room.add(floor);

      // Walls (gothic stone)
      const wallMaterial = new THREE.MeshStandardMaterial({
        color: 0x3a2a2a,
        roughness: 0.9
      });

      // North wall
      const northWall = new THREE.Mesh(
        new THREE.BoxGeometry(20, 8, 0.5),
        wallMaterial
      );
      northWall.position.set(0, 4, -10);
      room.add(northWall);

      // South wall
      const southWall = new THREE.Mesh(
        new THREE.BoxGeometry(20, 8, 0.5),
        wallMaterial
      );
      southWall.position.set(0, 4, 10);
      room.add(southWall);

      // East wall
      const eastWall = new THREE.Mesh(
        new THREE.BoxGeometry(0.5, 8, 20),
        wallMaterial
      );
      eastWall.position.set(10, 4, 0);
      room.add(eastWall);

      // West wall
      const westWall = new THREE.Mesh(
        new THREE.BoxGeometry(0.5, 8, 20),
        wallMaterial
      );
      westWall.position.set(-10, 4, 0);
      room.add(westWall);

      // Ceiling
      const ceiling = new THREE.Mesh(
        new THREE.PlaneGeometry(20, 20),
        new THREE.MeshStandardMaterial({ 
          color: 0x1a0a0a,
          side: THREE.DoubleSide
        })
      );
      ceiling.rotation.x = Math.PI / 2;
      ceiling.position.y = 8;
      room.add(ceiling);

      this.scene.add(room);
      this.rooms.set('grand-hall', room);
    }

    createGallery() {
      const room = new THREE.Group();
      room.name = 'gallery';
      room.visible = false;

      // Floor
      const floor = new THREE.Mesh(
        new THREE.PlaneGeometry(15, 25),
        new THREE.MeshStandardMaterial({
          color: 0x2a1520,
          roughness: 0.7
        })
      );
      floor.rotation.x = -Math.PI / 2;
      floor.receiveShadow = !this.isMobile;
      room.add(floor);

      // Walls with art frames
      const wallMaterial = new THREE.MeshStandardMaterial({
        color: 0x3a2030,
        roughness: 0.8
      });

      const wall1 = new THREE.Mesh(
        new THREE.BoxGeometry(15, 8, 0.5),
        wallMaterial
      );
      wall1.position.set(0, 4, -12.5);
      room.add(wall1);

      const wall2 = new THREE.Mesh(
        new THREE.BoxGeometry(15, 8, 0.5),
        wallMaterial
      );
      wall2.position.set(0, 4, 12.5);
      room.add(wall2);

      this.scene.add(room);
      this.rooms.set('gallery', room);
    }

    createChamber() {
      const room = new THREE.Group();
      room.name = 'chamber';
      room.visible = false;

      // Smaller, more intimate space
      const floor = new THREE.Mesh(
        new THREE.PlaneGeometry(12, 12),
        new THREE.MeshStandardMaterial({
          color: 0x2a1a2a,
          roughness: 0.6,
          metalness: 0.2
        })
      );
      floor.rotation.x = -Math.PI / 2;
      floor.receiveShadow = !this.isMobile;
      room.add(floor);

      this.scene.add(room);
      this.rooms.set('chamber', room);
    }

    createCourtyard() {
      const room = new THREE.Group();
      room.name = 'courtyard';
      room.visible = false;

      // Outdoor stone floor
      const floor = new THREE.Mesh(
        new THREE.PlaneGeometry(18, 18),
        new THREE.MeshStandardMaterial({
          color: 0x3a3a2a,
          roughness: 0.9
        })
      );
      floor.rotation.x = -Math.PI / 2;
      room.add(floor);

      this.scene.add(room);
      this.rooms.set('courtyard', room);
    }

    createDoors() {
      const doorPositions = [
        { room: 'gallery', pos: [0, 2, -9.5], target: 'gallery' },
        { room: 'grand-hall', pos: [9.5, 2, 0], target: 'chamber', rotation: Math.PI / 2 },
        { room: 'grand-hall', pos: [0, 2, 9.5], target: 'courtyard' }
      ];

      doorPositions.forEach(doorData => {
        const door = this.createDoor(doorData.pos, doorData.rotation);
        door.userData = { 
          targetRoom: doorData.target,
          isOpen: false
        };
        this.doors.push(door);
        
        const room = this.rooms.get(doorData.room);
        if (room) room.add(door);
      });
    }

    createDoor(position, rotation = 0) {
      const door = new THREE.Group();
      
      // Door frame
      const frameMaterial = new THREE.MeshStandardMaterial({
        color: 0x4a3a3a,
        roughness: 0.5,
        metalness: 0.3
      });

      const leftPost = new THREE.Mesh(
        new THREE.BoxGeometry(0.3, 4, 0.3),
        frameMaterial
      );
      leftPost.position.set(-1.5, 2, 0);
      door.add(leftPost);

      const rightPost = new THREE.Mesh(
        new THREE.BoxGeometry(0.3, 4, 0.3),
        frameMaterial
      );
      rightPost.position.set(1.5, 2, 0);
      door.add(rightPost);

      const topBeam = new THREE.Mesh(
        new THREE.BoxGeometry(3, 0.3, 0.3),
        frameMaterial
      );
      topBeam.position.set(0, 4, 0);
      door.add(topBeam);

      // Door panel (clickable)
      const doorPanel = new THREE.Mesh(
        new THREE.BoxGeometry(2.8, 3.8, 0.2),
        new THREE.MeshStandardMaterial({
          color: 0x5a3a3a,
          roughness: 0.7,
          metalness: 0.2
        })
      );
      doorPanel.position.set(0, 2, 0);
      doorPanel.userData = { clickable: true, type: 'door' };
      door.add(doorPanel);

      door.position.set(...position);
      door.rotation.y = rotation;
      
      return door;
    }

    createCandelabras() {
      const positions = [
        [-8, 2, -8],
        [8, 2, -8],
        [-8, 2, 8],
        [8, 2, 8]
      ];

      positions.forEach(pos => {
        const candelabra = this.createCandelabra(pos);
        this.candelabras.push(candelabra);
        const grandHall = this.rooms.get('grand-hall');
        if (grandHall) grandHall.add(candelabra);
      });
    }

    createCandelabra(position) {
      const group = new THREE.Group();
      
      // Stand
      const standGeometry = new THREE.CylinderGeometry(0.1, 0.15, 1.5, 8);
      const standMaterial = new THREE.MeshStandardMaterial({
        color: 0x8a7a5a,
        roughness: 0.4,
        metalness: 0.8
      });
      const stand = new THREE.Mesh(standGeometry, standMaterial);
      stand.position.y = 0.75;
      group.add(stand);

      // Candle
      const candleGeometry = new THREE.CylinderGeometry(0.08, 0.08, 0.4, 8);
      const candleMaterial = new THREE.MeshStandardMaterial({
        color: 0xffeedd,
        roughness: 0.8
      });
      const candle = new THREE.Mesh(candleGeometry, candleMaterial);
      candle.position.y = 1.7;
      group.add(candle);

      // Point light (initially off)
      const light = new THREE.PointLight(0xffa500, 0, 5);
      light.position.y = 2;
      group.add(light);

      group.position.set(...position);
      group.userData = { 
        clickable: true, 
        type: 'candelabra',
        light: light,
        lit: false
      };

      this.lightsOn.set(light, false);

      return group;
    }

    createEnchantedRose() {
      const roseGroup = new THREE.Group();
      
      // Glass dome
      const domeGeometry = new THREE.SphereGeometry(1, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2);
      const domeMaterial = new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.3,
        roughness: 0.1,
        metalness: 0.1,
        transmission: 0.9,
        thickness: 0.5
      });
      const dome = new THREE.Mesh(domeGeometry, domeMaterial);
      dome.position.y = 1.5;
      roseGroup.add(dome);

      // Base pedestal
      const pedestalGeometry = new THREE.CylinderGeometry(0.8, 1, 0.5, 16);
      const pedestalMaterial = new THREE.MeshStandardMaterial({
        color: 0x3a2a2a,
        roughness: 0.5,
        metalness: 0.3
      });
      const pedestal = new THREE.Mesh(pedestalGeometry, pedestalMaterial);
      pedestal.position.y = 0.25;
      roseGroup.add(pedestal);

      // Enchanted rose (glowing)
      const rose = this.createRose(0xdc143c, true);
      rose.position.y = 1.5;
      rose.scale.setScalar(0.3);
      roseGroup.add(rose);

      // Glow light
      const glowLight = new THREE.PointLight(0xdc143c, 2, 5);
      glowLight.position.y = 1.5;
      roseGroup.add(glowLight);

      roseGroup.position.set(0, 0, 0);
      roseGroup.userData = { 
        clickable: true, 
        type: 'enchanted-rose',
        rose: rose,
        light: glowLight
      };

      const grandHall = this.rooms.get('grand-hall');
      if (grandHall) grandHall.add(roseGroup);
      
      this.enchantedRose = roseGroup;
    }

    createRose(color, withGlow = false) {
      const rose = new THREE.Group();
      const petalCount = 8;
      const petalGeometry = new THREE.SphereGeometry(0.5, 8, 6);
      const petalMaterial = new THREE.MeshStandardMaterial({
        color: color,
        roughness: 0.4,
        metalness: 0.1,
        emissive: withGlow ? color : 0x000000,
        emissiveIntensity: withGlow ? 0.3 : 0
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

      // Center
      const centerGeometry = new THREE.SphereGeometry(0.2, 8, 8);
      const centerMaterial = new THREE.MeshStandardMaterial({
        color: 0xffd700,
        roughness: 0.2,
        metalness: 0.8,
        emissive: 0xffd700,
        emissiveIntensity: 0.2
      });
      const center = new THREE.Mesh(centerGeometry, centerMaterial);
      rose.add(center);

      return rose;
    }

    createUI() {
      // Room label
      this.roomLabel = document.createElement('div');
      this.roomLabel.className = 'love-hurts-room-label';
      this.roomLabel.style.cssText = `
        position: absolute;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(183, 110, 121, 0.9);
        border: 1px solid rgba(220, 20, 60, 0.5);
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        color: #fff;
        font-size: 1rem;
        font-family: 'Playfair Display', serif;
        z-index: 999;
        letter-spacing: 2px;
        text-transform: uppercase;
      `;
      this.roomLabel.textContent = 'Grand Hall';
      this.container.appendChild(this.roomLabel);

      // Navigation arrows
      this.navigationArrows = document.createElement('div');
      this.navigationArrows.className = 'love-hurts-nav-arrows';
      this.navigationArrows.style.cssText = `
        position: absolute;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        gap: 1rem;
        z-index: 999;
      `;
      this.navigationArrows.innerHTML = `
        <button class="nav-arrow" data-direction="left" style="
          background: rgba(183, 110, 121, 0.8);
          border: 1px solid rgba(220, 20, 60, 0.5);
          border-radius: 50%;
          width: 50px;
          height: 50px;
          color: #fff;
          font-size: 1.5rem;
          cursor: pointer;
          transition: all 0.3s ease;
        ">←</button>
        <button class="nav-arrow" data-direction="right" style="
          background: rgba(183, 110, 121, 0.8);
          border: 1px solid rgba(220, 20, 60, 0.5);
          border-radius: 50%;
          width: 50px;
          height: 50px;
          color: #fff;
          font-size: 1.5rem;
          cursor: pointer;
          transition: all 0.3s ease;
        ">→</button>
      `;
      this.container.appendChild(this.navigationArrows);

      // Audio toggle
      this.audioToggle = document.createElement('button');
      this.audioToggle.className = 'love-hurts-audio-toggle';
      this.audioToggle.textContent = '🔊';
      this.audioToggle.style.cssText = `
        position: absolute;
        bottom: 20px;
        right: 20px;
        background: rgba(26, 10, 10, 0.8);
        border: 1px solid rgba(183, 110, 121, 0.3);
        border-radius: 50%;
        width: 45px;
        height: 45px;
        color: #b76e79;
        font-size: 1.2rem;
        cursor: pointer;
        z-index: 999;
        display: flex;
        align-items: center;
        justify-content: center;
      `;
      this.audioToggle.addEventListener('click', () => this.toggleAudio());
      this.container.appendChild(this.audioToggle);
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
      
      // Check all clickable objects
      const clickableObjects = [
        ...this.doors.map(d => d.children.find(c => c.userData.clickable)),
        ...this.candelabras,
        this.enchantedRose
      ].filter(Boolean);

      const intersects = this.raycaster.intersectObjects(clickableObjects, true);

      if (intersects.length > 0) {
        const object = intersects[0].object;
        const parent = this.findClickableParent(object);
        
        if (parent) {
          this.handleInteraction(parent);
        }
      }
    }

    findClickableParent(obj) {
      let current = obj;
      while (current) {
        if (current.userData && current.userData.clickable) {
          return current;
        }
        current = current.parent;
      }
      return null;
    }

    handleInteraction(object) {
      const type = object.userData.type;

      if (type === 'door') {
        const targetRoom = object.userData.targetRoom;
        if (targetRoom) {
          this.teleportToRoom(targetRoom);
        }
      } else if (type === 'candelabra') {
        this.toggleCandelabra(object);
      } else if (type === 'enchanted-rose') {
        this.triggerRosePetalAnimation();
      }
    }

    teleportToRoom(roomName) {
      if (this.roomTransitioning) return;

      const targetRoom = this.rooms.get(roomName);
      const currentRoomObj = this.rooms.get(this.currentRoom);

      if (!targetRoom || !currentRoomObj) return;

      this.roomTransitioning = true;

      // Fade transition
      currentRoomObj.visible = false;
      targetRoom.visible = true;

      // Update camera position based on room
      const roomPositions = {
        'grand-hall': [0, 2, 8],
        'gallery': [0, 2, 10],
        'chamber': [0, 2, 6],
        'courtyard': [0, 2, 8]
      };

      const newPos = roomPositions[roomName] || [0, 2, 8];
      this.camera.position.set(...newPos);
      this.controls.target.set(0, 2, 0);
      this.controls.update();

      this.currentRoom = roomName;
      this.roomLabel.textContent = roomName.replace('-', ' ').toUpperCase();

      if (this.onRoomChangeCallback) {
        this.onRoomChangeCallback(roomName);
      }

      setTimeout(() => {
        this.roomTransitioning = false;
      }, 500);

    }

    toggleCandelabra(candelabra) {
      const light = candelabra.userData.light;
      const isLit = candelabra.userData.lit;

      if (isLit) {
        light.intensity = 0;
        candelabra.userData.lit = false;
      } else {
        light.intensity = 2;
        candelabra.userData.lit = true;
      }

    }

    triggerRosePetalAnimation() {
      if (!this.enchantedRose) return;

      const rose = this.enchantedRose.userData.rose;
      
      // Animate rose petals falling
      for (let i = 0; i < 5; i++) {
        setTimeout(() => {
          const petal = this.createFallingPetal();
          petal.position.copy(this.enchantedRose.position);
          petal.position.y += 1.5;
          this.scene.add(petal);
          this.petals.push(petal);
        }, i * 500);
      }

    }

    createFallingPetal() {
      const petal = new THREE.Mesh(
        new THREE.PlaneGeometry(0.15, 0.2),
        new THREE.MeshStandardMaterial({
          color: 0xdc143c,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.9
        })
      );

      petal.userData = {
        velocity: new THREE.Vector3(
          (Math.random() - 0.5) * 0.02,
          -0.03,
          (Math.random() - 0.5) * 0.02
        ),
        rotationSpeed: (Math.random() - 0.5) * 0.05,
        lifetime: 0
      };

      return petal;
    }

    checkHover() {
      this.raycaster.setFromCamera(this.mouse, this.camera);
      
      const clickableObjects = [
        ...this.doors.map(d => d.children.find(c => c.userData.clickable)),
        ...this.candelabras,
        this.enchantedRose
      ].filter(Boolean);

      const intersects = this.raycaster.intersectObjects(clickableObjects, true);

      if (intersects.length > 0) {
        this.container.style.cursor = 'pointer';
      } else {
        this.container.style.cursor = 'default';
      }
    }

    onResize() {
      const width = this.container.clientWidth;
      const height = this.container.clientHeight;
      
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
      
      this.renderer.setSize(width, height);
    }

    toggleAudio() {
      this.audioToggle.textContent = this.audioToggle.textContent === '🔊' ? '🔇' : '🔊';
    }

    // ===========================================================================
    // Public API
    // ===========================================================================

    async loadProducts(products) {
      products.forEach(product => {
        this.createProductPedestal(product);
      });
      
    }

    createProductPedestal(product) {
      const pedestal = new THREE.Group();
      
      // Base
      const baseGeometry = new THREE.CylinderGeometry(0.4, 0.5, 1, 16);
      const baseMaterial = new THREE.MeshStandardMaterial({
        color: 0x4a3a3a,
        roughness: 0.5,
        metalness: 0.3
      });
      const base = new THREE.Mesh(baseGeometry, baseMaterial);
      pedestal.add(base);

      // Product indicator (glowing orb)
      const orbGeometry = new THREE.SphereGeometry(0.2, 16, 16);
      const orbMaterial = new THREE.MeshStandardMaterial({
        color: 0xb76e79,
        emissive: 0xb76e79,
        emissiveIntensity: 0.5
      });
      const orb = new THREE.Mesh(orbGeometry, orbMaterial);
      orb.position.y = 1.2;
      pedestal.add(orb);

      // Point light
      const light = new THREE.PointLight(0xb76e79, 1, 3);
      light.position.y = 1.2;
      pedestal.add(light);

      pedestal.position.set(...product.position);
      pedestal.userData = { 
        clickable: true, 
        type: 'product',
        product: product
      };

      const currentRoomObj = this.rooms.get(this.currentRoom);
      if (currentRoomObj) currentRoomObj.add(pedestal);
      
      this.productPedestals.push(pedestal);
    }

    setOnProductClick(handler) {
      this.onProductClickCallback = handler;
    }

    setOnRoomChange(handler) {
      this.onRoomChangeCallback = handler;
    }

    animatePetals(elapsed) {
      for (let i = this.petals.length - 1; i >= 0; i--) {
        const petal = this.petals[i];
        const userData = petal.userData;
        
        petal.position.add(userData.velocity);
        petal.rotation.z += userData.rotationSpeed;
        userData.lifetime += 0.016;

        // Remove after 5 seconds
        if (userData.lifetime > 5) {
          this.scene.remove(petal);
          this.petals.splice(i, 1);
        }
      }

      // Pulse enchanted rose
      if (this.enchantedRose) {
        const rose = this.enchantedRose.userData.rose;
        const scale = 1 + Math.sin(elapsed * 2) * 0.05;
        rose.scale.setScalar(0.3 * scale);
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

      if (this.roomLabel) this.roomLabel.remove();
      if (this.navigationArrows) this.navigationArrows.remove();
      if (this.audioToggle) this.audioToggle.remove();

    }
  }

  // Export to global scope for WordPress
  window.LoveHurtsCastleExperience = LoveHurtsCastleExperience;

})();
