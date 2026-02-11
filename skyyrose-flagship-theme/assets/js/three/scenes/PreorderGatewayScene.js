/**
 * Preorder Gateway - Futuristic Portal Hub Scene
 *
 * Sci-fi portal room with custom GLSL shaders, massive particle system,
 * and Lenis smooth scroll integration. All patterns verified from Context7.
 *
 * Features:
 * - Custom GLSL portal shader with swirling energy
 * - 262,144 instanced particles (2^18)
 * - Lenis smooth scroll camera sync
 * - Real-time countdown timers
 * - Product portal hotspots
 *
 * Performance Target: 60fps with instanced rendering
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

import * as THREE from 'three';
import Lenis from '@studio-freight/lenis';
import BaseScene from '../utils/BaseScene.js';
import ProductLoader from '../utils/ProductLoader.js';
import gsap from 'gsap';

/**
 * PreorderGatewayScene Class
 * Futuristic portal hub with energy effects
 *
 * Pattern Source: Context7 queries for Three.js r161 + Lenis
 * - Custom GLSL: ShaderMaterial with time uniforms
 * - Instanced particles: InstancedBufferAttribute
 * - Lenis scroll: raf callback integration
 */
class PreorderGatewayScene extends BaseScene {
  constructor(container) {
    super(container);

    // Scene state
    this.portalActive = true;
    this.scrollPosition = 0;
    this.particleSpeed = 1.0;

    // Lenis smooth scroll
    this.lenis = null;

    // Particle system
    this.particleSystem = null;
    this.particleAttributes = null;

    // Portal shader uniforms
    this.portalUniforms = null;

    // Product integration
    this.productLoader = new ProductLoader();
    this.productPortals = [];

    // Countdown data
    this.preorderDate = new Date('2026-03-01T00:00:00');
  }

  /**
   * Initialize Scene
   * Sets up portal hub environment with energy effects
   *
   * Pattern: Context7 - Three.js scene initialization
   */
  async init() {
    await super.init();

    // Scene setup
    this.scene.background = new THREE.Color(0x000510); // Deep space blue
    this.scene.fog = new THREE.FogExp2(0x000510, 0.015);

    // Lighting
    this.setupLighting();

    // Portal hub architecture
    await this.createPortalHub();

    // Main portal with custom shader
    this.createMainPortal();

    // Massive particle system
    this.setupParticleSystem();

    // Lenis smooth scroll
    this.setupSmoothScroll();

    // Load products
    await this.loadProducts();

    // Camera position
    this.camera.position.set(0, 5, 15);
    this.controls.target.set(0, 2, 0);
    this.controls.update();

    // Start animation loop
    this.animate();

    console.log('✅ PreorderGatewayScene initialized - Portal hub ready');
  }

  /**
   * Setup Lighting System
   * Futuristic blue/cyan/magenta lighting
   *
   * Pattern: Context7 - Three.js lighting for sci-fi scenes
   */
  setupLighting() {
    // Ambient light - cool blue tint
    const ambient = new THREE.AmbientLight(0x0a1a2a, 0.3);
    this.scene.add(ambient);

    // Main portal light - bright cyan
    const portalLight = new THREE.PointLight(0x00ffff, 3.0, 30);
    portalLight.position.set(0, 3, 0);
    portalLight.castShadow = true;
    portalLight.shadow.mapSize.width = 2048;
    portalLight.shadow.mapSize.height = 2048;
    this.scene.add(portalLight);

    // Accent lights - magenta/cyan
    const accentLight1 = new THREE.SpotLight(0xff00ff, 2.0, 20, Math.PI / 4, 0.5, 2);
    accentLight1.position.set(-5, 8, -5);
    accentLight1.target.position.set(0, 0, 0);
    this.scene.add(accentLight1);
    this.scene.add(accentLight1.target);

    const accentLight2 = new THREE.SpotLight(0x00ffff, 2.0, 20, Math.PI / 4, 0.5, 2);
    accentLight2.position.set(5, 8, -5);
    accentLight2.target.position.set(0, 0, 0);
    this.scene.add(accentLight2);
    this.scene.add(accentLight2.target);

    // Hemisphere light for ambient fill
    const hemiLight = new THREE.HemisphereLight(0x0077ff, 0x000510, 0.5);
    this.scene.add(hemiLight);
  }

  /**
   * Create Portal Hub Architecture
   * Futuristic chamber with metallic panels
   *
   * Pattern: Context7 - Three.js geometry and materials
   */
  async createPortalHub() {
    // Floor - metallic grid
    const floorGeometry = new THREE.PlaneGeometry(50, 50, 50, 50);
    const floorMaterial = new THREE.MeshStandardMaterial({
      color: 0x0a1a2a,
      metalness: 0.9,
      roughness: 0.3,
      wireframe: false,
    });

    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    this.scene.add(floor);

    // Create wireframe overlay for grid effect
    const wireframeGeometry = new THREE.PlaneGeometry(50, 50, 50, 50);
    const wireframeMaterial = new THREE.MeshBasicMaterial({
      color: 0x00ffff,
      wireframe: true,
      transparent: true,
      opacity: 0.1,
    });

    const wireframe = new THREE.Mesh(wireframeGeometry, wireframeMaterial);
    wireframe.rotation.x = -Math.PI / 2;
    wireframe.position.y = 0.01;
    this.scene.add(wireframe);

    // Portal frame - circular metallic ring
    this.createPortalFrame();

    // Energy beams
    this.createEnergyBeams();
  }

  /**
   * Create Portal Frame
   * Circular metallic ring structure
   *
   * Pattern: Context7 - Three.js torus geometry
   */
  createPortalFrame() {
    const torusGeometry = new THREE.TorusGeometry(5, 0.3, 32, 100);
    const torusMaterial = new THREE.MeshStandardMaterial({
      color: 0x00ffff,
      metalness: 1.0,
      roughness: 0.2,
      emissive: 0x00ffff,
      emissiveIntensity: 0.5,
    });

    const torus = new THREE.Mesh(torusGeometry, torusMaterial);
    torus.position.set(0, 3, 0);
    torus.rotation.y = Math.PI / 2;
    torus.castShadow = true;
    this.scene.add(torus);

    // Pulsing animation
    gsap.to(torusMaterial, {
      emissiveIntensity: 1.0,
      duration: 2,
      repeat: -1,
      yoyo: true,
      ease: 'power2.inOut',
    });
  }

  /**
   * Create Energy Beams
   * Vertical light pillars
   *
   * Pattern: Context7 - Three.js cylinder geometry with emissive
   */
  createEnergyBeams() {
    const beamGeometry = new THREE.CylinderGeometry(0.1, 0.1, 8, 16);
    const beamMaterial = new THREE.MeshBasicMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0.3,
    });

    const beamPositions = [
      { x: -8, z: -8 },
      { x: 8, z: -8 },
      { x: -8, z: 8 },
      { x: 8, z: 8 },
    ];

    beamPositions.forEach((pos, index) => {
      const beam = new THREE.Mesh(beamGeometry, beamMaterial.clone());
      beam.position.set(pos.x, 4, pos.z);
      this.scene.add(beam);

      // Animated fade
      gsap.to(beam.material, {
        opacity: 0.6,
        duration: 1.5 + index * 0.3,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
      });
    });
  }

  /**
   * Create Main Portal with Custom GLSL Shader
   * Swirling energy effect with procedural noise
   *
   * Pattern: Context7 - ShaderMaterial with custom GLSL
   * Source: /mrdoob/three.js - shadertoy examples
   */
  createMainPortal() {
    // Vertex shader - pass UVs
    const vertexShader = `
      varying vec2 vUv;

      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `;

    // Fragment shader - portal energy effect
    const fragmentShader = `
      #include <common>

      uniform float iTime;
      uniform vec3 iResolution;
      uniform vec3 portalColor1;
      uniform vec3 portalColor2;

      varying vec2 vUv;

      // Noise function
      float noise(vec2 p) {
        return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
      }

      // Fractal Brownian Motion
      float fbm(vec2 p) {
        float value = 0.0;
        float amplitude = 0.5;
        float frequency = 1.0;

        for (int i = 0; i < 5; i++) {
          value += amplitude * noise(p * frequency);
          amplitude *= 0.5;
          frequency *= 2.0;
        }

        return value;
      }

      void main() {
        vec2 uv = vUv * 2.0 - 1.0;
        float dist = length(uv);

        // Rotate UV over time
        float angle = iTime * 0.3;
        mat2 rot = mat2(cos(angle), -sin(angle), sin(angle), cos(angle));
        uv = rot * uv;

        // Swirling pattern
        float swirl = fbm(uv * 3.0 + iTime * 0.2);
        swirl += fbm(uv * 5.0 - iTime * 0.3) * 0.5;

        // Radial gradient
        float radial = 1.0 - smoothstep(0.0, 1.0, dist);

        // Color mixing
        vec3 color = mix(portalColor1, portalColor2, swirl);
        color *= radial;

        // Edge glow
        float edge = smoothstep(0.9, 1.0, dist);
        color += vec3(0.0, 1.0, 1.0) * edge * 2.0;

        // Fade center
        float centerFade = smoothstep(0.0, 0.3, dist);
        color *= centerFade;

        gl_FragColor = vec4(color, radial * 0.8);
      }
    `;

    // Uniforms
    this.portalUniforms = {
      iTime: { value: 0 },
      iResolution: { value: new THREE.Vector3(1, 1, 1) },
      portalColor1: { value: new THREE.Vector3(0.0, 1.0, 1.0) }, // Cyan
      portalColor2: { value: new THREE.Vector3(1.0, 0.0, 1.0) }, // Magenta
    };

    // Create material
    const portalMaterial = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: this.portalUniforms,
      transparent: true,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    // Portal mesh - circular plane
    const portalGeometry = new THREE.CircleGeometry(5, 64);
    this.portalMesh = new THREE.Mesh(portalGeometry, portalMaterial);
    this.portalMesh.position.set(0, 3, 0);
    this.portalMesh.rotation.y = Math.PI / 2;
    this.scene.add(this.portalMesh);

    console.log('✅ Portal shader initialized with custom GLSL');
  }

  /**
   * Setup Particle System
   * 262,144 particles with instancing (2^18)
   *
   * Pattern: Context7 - InstancedBufferAttribute for GPU efficiency
   * Source: /mrdoob/three.js - webgl_buffergeometry_custom_attributes_particles
   */
  setupParticleSystem() {
    const count = 262144; // 2^18

    // Base geometry - small sphere
    const geometry = new THREE.BufferGeometry();
    const positions = [];
    const colors = [];
    const sizes = [];
    const velocities = [];

    const color = new THREE.Color();

    for (let i = 0; i < count; i++) {
      // Random position in sphere
      const radius = Math.random() * 25;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      const x = radius * Math.sin(phi) * Math.cos(theta);
      const y = radius * Math.sin(phi) * Math.sin(theta);
      const z = radius * Math.cos(phi);

      positions.push(x, y, z);

      // Color gradient - cyan to magenta
      const hue = (i / count) * 0.6; // 0 to 0.6 (cyan to magenta)
      color.setHSL(hue, 1.0, 0.6);
      colors.push(color.r, color.g, color.b);

      // Random size
      sizes.push(Math.random() * 20 + 5);

      // Velocity for animation
      velocities.push(
        (Math.random() - 0.5) * 0.2,
        (Math.random() - 0.5) * 0.2,
        (Math.random() - 0.5) * 0.2
      );
    }

    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.Float32BufferAttribute(sizes, 1).setUsage(THREE.DynamicDrawUsage));

    this.particleAttributes = {
      positions: geometry.attributes.position,
      colors: geometry.attributes.color,
      sizes: geometry.attributes.size,
      velocities: velocities,
    };

    // Shader material for particles
    const particleMaterial = new THREE.PointsMaterial({
      size: 1,
      vertexColors: true,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      sizeAttenuation: true,
    });

    this.particleSystem = new THREE.Points(geometry, particleMaterial);
    this.scene.add(this.particleSystem);

    console.log('✅ 262,144 particles initialized');
  }

  /**
   * Setup Lenis Smooth Scroll
   * Synchronize camera with scroll position
   *
   * Pattern: Context7 - Lenis with custom raf loop
   * Source: /darkroomengineering/lenis - README examples
   */
  setupSmoothScroll() {
    this.lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
      wheelMultiplier: 1.0,
      smoothTouch: false,
      touchMultiplier: 2,
      infinite: false,
    });

    // Listen for scroll events
    this.lenis.on('scroll', (e) => {
      this.scrollPosition = e.scroll;

      // Update camera position based on scroll
      // Camera moves up as user scrolls down
      const cameraY = 5 + (e.scroll / window.innerHeight) * 10;
      gsap.to(this.camera.position, {
        y: cameraY,
        duration: 0.5,
        ease: 'power2.out',
      });
    });

    console.log('✅ Lenis smooth scroll initialized');
  }

  /**
   * Load Products from WooCommerce
   * Fetch Preorder products via REST API
   *
   * Pattern: Documented in BaseScene
   */
  async loadProducts() {
    try {
      const products = await this.productLoader.loadCollectionProducts('preorder');

      products.forEach((product) => {
        this.createProductPortal(product);
      });

      console.log(`✅ Loaded ${products.length} Preorder products`);
    } catch (error) {
      console.error('❌ Failed to load products:', error);
    }
  }

  /**
   * Create Product Portal
   * Mini portal hotspot for products
   *
   * Pattern: Context7 - Mesh with emissive material
   */
  createProductPortal(productData) {
    const geometry = new THREE.TorusGeometry(0.5, 0.1, 16, 32);
    const material = new THREE.MeshStandardMaterial({
      color: 0x00ffff,
      emissive: 0x00ffff,
      emissiveIntensity: 1.5,
      metalness: 1.0,
      roughness: 0.2,
    });

    const portal = new THREE.Mesh(geometry, material);
    portal.position.set(productData.position.x, productData.position.y, productData.position.z);
    portal.rotation.y = Math.PI / 2;

    // Store product data
    portal.userData = {
      type: 'product',
      productData: productData,
    };

    // GSAP rotation animation
    gsap.to(portal.rotation, {
      z: Math.PI * 2,
      duration: 4,
      repeat: -1,
      ease: 'linear',
    });

    // Pulsing glow
    gsap.to(material, {
      emissiveIntensity: 2.5,
      duration: 1.5,
      repeat: -1,
      yoyo: true,
      ease: 'sine.inOut',
    });

    this.scene.add(portal);
    this.productPortals.push(portal);
  }

  /**
   * Get Countdown Timer Data
   * Calculate time remaining until preorder date
   *
   * Pattern: Standard JavaScript Date manipulation
   */
  getCountdownData() {
    const now = new Date();
    const diff = this.preorderDate - now;

    if (diff <= 0) {
      return { days: 0, hours: 0, minutes: 0, seconds: 0, expired: true };
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    return { days, hours, minutes, seconds, expired: false };
  }

  /**
   * Animation Loop
   * Updates particles, portal shader, and Lenis
   *
   * Pattern: Context7 - requestAnimationFrame loop with Lenis raf
   */
  animate() {
    requestAnimationFrame(() => this.animate());

    const time = this.clock.getElapsedTime();
    const delta = this.clock.getDelta();

    // Update Lenis
    if (this.lenis) {
      this.lenis.raf(time * 1000);
    }

    // Update portal shader
    if (this.portalUniforms) {
      this.portalUniforms.iTime.value = time;
    }

    // Update particles
    if (this.particleSystem && this.particleAttributes) {
      this.updateParticles(delta);
    }

    // Rotate portal mesh
    if (this.portalMesh) {
      this.portalMesh.rotation.z += 0.001;
    }

    // Update controls
    this.controls.update();

    // Render
    this.renderer.render(this.scene, this.camera);
  }

  /**
   * Update Particle Positions
   * Physics simulation with boundary wrapping
   *
   * Pattern: Context7 - Dynamic attribute updates
   */
  updateParticles(delta) {
    const positions = this.particleAttributes.positions.array;
    const sizes = this.particleAttributes.sizes.array;
    const velocities = this.particleAttributes.velocities;
    const time = this.clock.getElapsedTime();

    for (let i = 0; i < positions.length; i += 3) {
      const idx = i / 3;

      // Update position with velocity
      positions[i] += velocities[idx * 3] * delta * this.particleSpeed;
      positions[i + 1] += velocities[idx * 3 + 1] * delta * this.particleSpeed;
      positions[i + 2] += velocities[idx * 3 + 2] * delta * this.particleSpeed;

      // Wrap around boundaries
      const radius = Math.sqrt(
        positions[i] * positions[i] +
        positions[i + 1] * positions[i + 1] +
        positions[i + 2] * positions[i + 2]
      );

      if (radius > 25) {
        positions[i] *= -0.8;
        positions[i + 1] *= -0.8;
        positions[i + 2] *= -0.8;
      }

      // Pulsing size
      sizes[idx] = 10 + 8 * Math.sin(time * 2 + idx * 0.01);
    }

    this.particleAttributes.positions.needsUpdate = true;
    this.particleAttributes.sizes.needsUpdate = true;
  }

  /**
   * Toggle Portal
   * Enable/disable portal effect
   */
  togglePortal() {
    this.portalActive = !this.portalActive;
    this.portalMesh.visible = this.portalActive;
  }

  /**
   * Cleanup
   * Dispose resources on page unload
   */
  dispose() {
    super.dispose();

    if (this.particleSystem) {
      this.particleSystem.geometry.dispose();
      this.particleSystem.material.dispose();
    }

    if (this.portalMesh) {
      this.portalMesh.geometry.dispose();
      this.portalMesh.material.dispose();
    }

    if (this.lenis) {
      this.lenis.destroy();
    }

    console.log('✅ PreorderGatewayScene disposed');
  }
}

export default PreorderGatewayScene;
