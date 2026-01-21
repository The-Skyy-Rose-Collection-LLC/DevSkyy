/**
 * SkyyRose Black Rose Collection Scene
 *
 * Immersive rose garden 3D environment with dark elegance aesthetic.
 * Features: Rose particles, gothic atmosphere, emissive thorns, and product hotspots.
 *
 * @package SkyyRose_Immersive
 * @since 1.0.0
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

/**
 * Black Rose Collection Theme Colors
 */
const THEME = {
    crimson: 0xDC143C,
    darkRed: 0x8B0000,
    obsidian: 0x0A0505,
    silver: 0xC0C0C0,
    bloodRed: 0x660000
};

/**
 * Black Rose Garden Scene Class
 */
export class BlackRoseScene {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.options = {
            particleCount: options.particleCount || 500,
            roseCount: options.roseCount || 25,
            enableBloom: options.enableBloom !== false,
            bloomStrength: options.bloomStrength || 0.5,
            isMobile: options.isMobile || false,
            products: options.products || [],
            onProductClick: options.onProductClick || null,
            ...options
        };

        if (this.options.isMobile) {
            this.options.particleCount = Math.floor(this.options.particleCount * 0.4);
            this.options.roseCount = Math.floor(this.options.roseCount * 0.5);
        }

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.composer = null;
        this.clock = new THREE.Clock();

        this.roses = [];
        this.particles = null;
        this.thorns = [];
        this.productHotspots = [];
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        this.isAnimating = false;
        this.currentScene = 0;

        this.init();
    }

    init() {
        this.createScene();
        this.createCamera();
        this.createRenderer();
        this.createControls();
        this.createLighting();
        this.createGround();
        this.createRoseGarden();
        this.createRoseParticles();
        this.createThorns();
        this.createProductHotspots();

        if (this.options.enableBloom) {
            this.setupPostProcessing();
        }

        this.bindEvents();
    }

    createScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(THEME.obsidian);
        this.scene.fog = new THREE.FogExp2(THEME.obsidian, 0.02);
    }

    createCamera() {
        this.camera = new THREE.PerspectiveCamera(
            60,
            this.canvas.clientWidth / this.canvas.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 2, 8);
    }

    createRenderer() {
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: !this.options.isMobile,
            alpha: true,
            powerPreference: 'high-performance'
        });
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 0.8;
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    }

    createControls() {
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 3;
        this.controls.maxDistance = 20;
        this.controls.maxPolarAngle = Math.PI / 2 + 0.3;
        this.controls.target.set(0, 1, 0);
    }

    createLighting() {
        // Ambient light - very dark
        const ambient = new THREE.AmbientLight(THEME.darkRed, 0.1);
        this.scene.add(ambient);

        // Main crimson spotlight
        const mainLight = new THREE.SpotLight(THEME.crimson, 2, 30, Math.PI / 4, 0.5);
        mainLight.position.set(0, 15, 0);
        mainLight.castShadow = true;
        mainLight.shadow.mapSize.width = 1024;
        mainLight.shadow.mapSize.height = 1024;
        this.scene.add(mainLight);

        // Secondary accent lights
        const sideLight1 = new THREE.PointLight(THEME.crimson, 1, 15);
        sideLight1.position.set(-8, 3, -5);
        this.scene.add(sideLight1);

        const sideLight2 = new THREE.PointLight(THEME.silver, 0.5, 15);
        sideLight2.position.set(8, 3, -5);
        this.scene.add(sideLight2);

        // Ground bounce light
        const bounceLight = new THREE.PointLight(THEME.bloodRed, 0.3, 10);
        bounceLight.position.set(0, 0.5, 0);
        this.scene.add(bounceLight);
    }

    createGround() {
        // Dark ground plane
        const groundGeometry = new THREE.PlaneGeometry(50, 50);
        const groundMaterial = new THREE.MeshStandardMaterial({
            color: 0x050505,
            metalness: 0.8,
            roughness: 0.4
        });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        this.scene.add(ground);
    }

    createRoseGarden() {
        // Create procedural rose models
        for (let i = 0; i < this.options.roseCount; i++) {
            const rose = this.createRose();
            const angle = (i / this.options.roseCount) * Math.PI * 2;
            const radius = 3 + Math.random() * 8;

            rose.position.x = Math.cos(angle) * radius + (Math.random() - 0.5) * 3;
            rose.position.z = Math.sin(angle) * radius + (Math.random() - 0.5) * 3;
            rose.position.y = Math.random() * 0.5;
            rose.rotation.y = Math.random() * Math.PI * 2;
            rose.scale.setScalar(0.5 + Math.random() * 0.5);

            rose.userData.floatSpeed = 0.5 + Math.random() * 0.5;
            rose.userData.floatOffset = Math.random() * Math.PI * 2;
            rose.userData.baseY = rose.position.y;

            this.roses.push(rose);
            this.scene.add(rose);
        }

        // Central showcase rose (larger)
        const mainRose = this.createRose(true);
        mainRose.position.set(0, 1.5, 0);
        mainRose.scale.setScalar(1.5);
        mainRose.userData.isMain = true;
        mainRose.userData.floatSpeed = 0.3;
        mainRose.userData.floatOffset = 0;
        mainRose.userData.baseY = 1.5;
        this.roses.push(mainRose);
        this.scene.add(mainRose);
    }

    createRose(isMain = false) {
        const roseGroup = new THREE.Group();

        // Rose petals (layered toruses)
        const petalLayers = isMain ? 7 : 5;
        for (let i = 0; i < petalLayers; i++) {
            const petalGeometry = new THREE.TorusGeometry(
                0.3 + i * 0.1,
                0.06 + i * 0.01,
                8,
                24,
                Math.PI * 1.7
            );
            const petalMaterial = new THREE.MeshStandardMaterial({
                color: THEME.crimson,
                metalness: 0.1,
                roughness: 0.6,
                emissive: THEME.darkRed,
                emissiveIntensity: isMain ? 0.3 : 0.1
            });
            const petal = new THREE.Mesh(petalGeometry, petalMaterial);
            petal.rotation.x = -Math.PI / 4 + i * 0.15;
            petal.rotation.z = i * Math.PI / 5;
            petal.position.y = i * 0.08;
            roseGroup.add(petal);
        }

        // Rose center
        const centerGeometry = new THREE.SphereGeometry(0.15, 16, 16);
        const centerMaterial = new THREE.MeshStandardMaterial({
            color: THEME.darkRed,
            metalness: 0.3,
            roughness: 0.5,
            emissive: THEME.crimson,
            emissiveIntensity: isMain ? 0.4 : 0.2
        });
        const center = new THREE.Mesh(centerGeometry, centerMaterial);
        center.position.y = 0.1;
        roseGroup.add(center);

        // Stem
        const stemGeometry = new THREE.CylinderGeometry(0.03, 0.04, 1.5, 8);
        const stemMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a3300,
            metalness: 0.1,
            roughness: 0.8
        });
        const stem = new THREE.Mesh(stemGeometry, stemMaterial);
        stem.position.y = -0.75;
        roseGroup.add(stem);

        return roseGroup;
    }

    createRoseParticles() {
        const positions = new Float32Array(this.options.particleCount * 3);
        const colors = new Float32Array(this.options.particleCount * 3);
        const sizes = new Float32Array(this.options.particleCount);
        const velocities = new Float32Array(this.options.particleCount * 3);

        const crimsonColor = new THREE.Color(THEME.crimson);
        const silverColor = new THREE.Color(THEME.silver);

        for (let i = 0; i < this.options.particleCount; i++) {
            // Distribute in a dome shape
            const radius = 5 + Math.random() * 15;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.random() * Math.PI * 0.5;

            positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i * 3 + 1] = Math.abs(radius * Math.cos(phi) * 0.5) + 0.5;
            positions[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);

            // Gentle falling velocity
            velocities[i * 3] = (Math.random() - 0.5) * 0.01;
            velocities[i * 3 + 1] = -0.005 - Math.random() * 0.01;
            velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.01;

            // Mix of crimson and silver particles
            const color = Math.random() > 0.7 ? silverColor : crimsonColor;
            colors[i * 3] = color.r;
            colors[i * 3 + 1] = color.g;
            colors[i * 3 + 2] = color.b;

            sizes[i] = 0.02 + Math.random() * 0.05;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
        geometry.userData.velocities = velocities;

        const material = new THREE.PointsMaterial({
            size: 0.05,
            vertexColors: true,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending,
            sizeAttenuation: true
        });

        this.particles = new THREE.Points(geometry, material);
        this.scene.add(this.particles);
    }

    createThorns() {
        // Thorny branches around the scene
        for (let i = 0; i < 12; i++) {
            const thornBranch = this.createThornBranch();
            const angle = (i / 12) * Math.PI * 2;
            const radius = 6 + Math.random() * 4;

            thornBranch.position.x = Math.cos(angle) * radius;
            thornBranch.position.z = Math.sin(angle) * radius;
            thornBranch.rotation.y = angle + Math.PI;

            this.thorns.push(thornBranch);
            this.scene.add(thornBranch);
        }
    }

    createThornBranch() {
        const branchGroup = new THREE.Group();

        // Main branch
        const branchGeometry = new THREE.CylinderGeometry(0.02, 0.04, 2, 8);
        const branchMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a1a1a,
            metalness: 0.3,
            roughness: 0.7
        });
        const branch = new THREE.Mesh(branchGeometry, branchMaterial);
        branch.rotation.z = Math.PI / 4 + (Math.random() - 0.5) * 0.3;
        branch.position.y = 1;
        branchGroup.add(branch);

        // Thorns on the branch
        for (let i = 0; i < 5; i++) {
            const thornGeometry = new THREE.ConeGeometry(0.02, 0.1, 4);
            const thornMaterial = new THREE.MeshStandardMaterial({
                color: THEME.darkRed,
                metalness: 0.5,
                roughness: 0.3,
                emissive: THEME.crimson,
                emissiveIntensity: 0.2
            });
            const thorn = new THREE.Mesh(thornGeometry, thornMaterial);
            thorn.position.set(
                (Math.random() - 0.5) * 0.3,
                0.3 + i * 0.3,
                (Math.random() - 0.5) * 0.3
            );
            thorn.rotation.z = Math.PI / 2 * (Math.random() > 0.5 ? 1 : -1);
            branchGroup.add(thorn);
        }

        return branchGroup;
    }

    createProductHotspots() {
        this.options.products.forEach((product, index) => {
            const hotspot = this.createHotspot(product, index);
            this.productHotspots.push(hotspot);
            this.scene.add(hotspot);
        });
    }

    createHotspot(product, index) {
        const group = new THREE.Group();

        // Hotspot ring
        const ringGeometry = new THREE.TorusGeometry(0.15, 0.02, 16, 32);
        const ringMaterial = new THREE.MeshBasicMaterial({
            color: THEME.crimson,
            transparent: true,
            opacity: 0.8
        });
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.rotation.x = Math.PI / 2;
        group.add(ring);

        // Inner glow
        const glowGeometry = new THREE.CircleGeometry(0.1, 32);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: THEME.crimson,
            transparent: true,
            opacity: 0.4
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        glow.rotation.x = -Math.PI / 2;
        group.add(glow);

        // Position around the scene
        const angle = (index / Math.max(this.options.products.length, 1)) * Math.PI * 2;
        const radius = 4;
        group.position.set(
            Math.cos(angle) * radius,
            1.5,
            Math.sin(angle) * radius
        );

        group.userData.product = product;
        group.userData.isHotspot = true;

        return group;
    }

    setupPostProcessing() {
        this.composer = new EffectComposer(this.renderer);

        const renderPass = new RenderPass(this.scene, this.camera);
        this.composer.addPass(renderPass);

        const bloomPass = new UnrealBloomPass(
            new THREE.Vector2(this.canvas.clientWidth, this.canvas.clientHeight),
            this.options.bloomStrength,
            0.4,
            0.85
        );
        this.composer.addPass(bloomPass);
    }

    bindEvents() {
        window.addEventListener('resize', this.onResize.bind(this));
        this.canvas.addEventListener('click', this.onClick.bind(this));
        this.canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
    }

    onResize() {
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);

        if (this.composer) {
            this.composer.setSize(width, height);
        }
    }

    onClick(event) {
        this.updateMouse(event);
        this.raycaster.setFromCamera(this.mouse, this.camera);

        const intersects = this.raycaster.intersectObjects(this.productHotspots, true);
        if (intersects.length > 0) {
            let hotspot = intersects[0].object;
            while (hotspot && !hotspot.userData.isHotspot) {
                hotspot = hotspot.parent;
            }
            if (hotspot && hotspot.userData.product && this.options.onProductClick) {
                this.options.onProductClick(hotspot.userData.product);
            }
        }
    }

    onMouseMove(event) {
        this.updateMouse(event);
    }

    updateMouse(event) {
        const rect = this.canvas.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    }

    transitionToScene(sceneIndex) {
        this.currentScene = sceneIndex;

        const positions = [
            { x: 0, y: 2, z: 8, targetY: 1 },
            { x: -6, y: 3, z: 4, targetY: 1 },
            { x: 6, y: 4, z: -2, targetY: 0 }
        ];

        const pos = positions[sceneIndex % positions.length];
        this.tweenCamera(pos);
    }

    tweenCamera(target) {
        const start = {
            x: this.camera.position.x,
            y: this.camera.position.y,
            z: this.camera.position.z,
            targetY: this.controls.target.y
        };
        const startTime = Date.now();
        const duration = 1500;

        const update = () => {
            const elapsed = Date.now() - startTime;
            const t = Math.min(elapsed / duration, 1);
            const ease = 1 - Math.pow(1 - t, 3);

            this.camera.position.x = start.x + (target.x - start.x) * ease;
            this.camera.position.y = start.y + (target.y - start.y) * ease;
            this.camera.position.z = start.z + (target.z - start.z) * ease;
            this.controls.target.y = start.targetY + (target.targetY - start.targetY) * ease;

            if (t < 1) {
                requestAnimationFrame(update);
            }
        };
        update();
    }

    animate() {
        if (!this.isAnimating) return;

        requestAnimationFrame(this.animate.bind(this));

        const time = this.clock.getElapsedTime();

        // Animate roses
        this.roses.forEach(rose => {
            if (rose.userData.baseY !== undefined) {
                rose.position.y = rose.userData.baseY +
                    Math.sin(time * rose.userData.floatSpeed + rose.userData.floatOffset) * 0.15;
            }
            if (rose.userData.isMain) {
                rose.rotation.y = time * 0.2;
            }
        });

        // Animate particles (falling petals)
        if (this.particles) {
            const positions = this.particles.geometry.attributes.position.array;
            const velocities = this.particles.geometry.userData.velocities;

            for (let i = 0; i < positions.length; i += 3) {
                positions[i] += velocities[i];
                positions[i + 1] += velocities[i + 1];
                positions[i + 2] += velocities[i + 2];

                // Reset particles that fall too low
                if (positions[i + 1] < 0) {
                    positions[i + 1] = 8 + Math.random() * 4;
                    positions[i] = (Math.random() - 0.5) * 20;
                    positions[i + 2] = (Math.random() - 0.5) * 20;
                }
            }
            this.particles.geometry.attributes.position.needsUpdate = true;
        }

        // Animate hotspots (pulsing)
        this.productHotspots.forEach((hotspot, index) => {
            const scale = 1 + Math.sin(time * 2 + index) * 0.1;
            hotspot.scale.setScalar(scale);
        });

        this.controls.update();

        if (this.composer) {
            this.composer.render();
        } else {
            this.renderer.render(this.scene, this.camera);
        }
    }

    start() {
        this.isAnimating = true;
        this.animate();
    }

    stop() {
        this.isAnimating = false;
    }

    dispose() {
        this.stop();

        this.scene.traverse(object => {
            if (object.geometry) object.geometry.dispose();
            if (object.material) {
                if (Array.isArray(object.material)) {
                    object.material.forEach(m => m.dispose());
                } else {
                    object.material.dispose();
                }
            }
        });

        this.renderer.dispose();
        if (this.composer) this.composer.dispose();
        this.controls.dispose();

        window.removeEventListener('resize', this.onResize.bind(this));
        this.canvas.removeEventListener('click', this.onClick.bind(this));
        this.canvas.removeEventListener('mousemove', this.onMouseMove.bind(this));
    }
}

/**
 * Initialize Black Rose scene
 */
export function initBlackRoseScene(canvas, options = {}) {
    const scene = new BlackRoseScene(canvas, options);
    scene.start();
    return scene;
}

// Global exports
if (typeof window !== 'undefined') {
    window.SkyyRoseBlackRoseScene = BlackRoseScene;
    window.initBlackRoseScene = initBlackRoseScene;
}
