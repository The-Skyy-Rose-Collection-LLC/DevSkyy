/**
 * SkyyRose Signature Collection Scene
 *
 * Luxury fashion runway 3D environment with premium aesthetics.
 * Features: Spotlights, runway, gold accents, and professional lighting.
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
 * Signature Collection Theme Colors
 */
const THEME = {
    gold: 0xD4AF37,
    roseGold: 0xB76E79,
    champagne: 0xF7E7CE,
    black: 0x0A0A0A,
    platinum: 0xE5E4E2
};

/**
 * Signature Runway Scene Class
 */
export class SignatureScene {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.options = {
            particleCount: options.particleCount || 300,
            enableBloom: options.enableBloom !== false,
            bloomStrength: options.bloomStrength || 0.6,
            isMobile: options.isMobile || false,
            products: options.products || [],
            onProductClick: options.onProductClick || null,
            ...options
        };

        if (this.options.isMobile) {
            this.options.particleCount = Math.floor(this.options.particleCount * 0.4);
        }

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.composer = null;
        this.clock = new THREE.Clock();

        this.spotlights = [];
        this.displayModel = null;
        this.particles = null;
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
        this.createRunway();
        this.createStudioLighting();
        this.createDisplayPedestal();
        this.createBackdrop();
        this.createGoldParticles();
        this.createProductHotspots();

        if (this.options.enableBloom) {
            this.setupPostProcessing();
        }

        this.bindEvents();
    }

    createScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(THEME.black);
    }

    createCamera() {
        this.camera = new THREE.PerspectiveCamera(
            50,
            this.canvas.clientWidth / this.canvas.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 3, 20);
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
        this.renderer.toneMappingExposure = 1.0;
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    }

    createControls() {
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 5;
        this.controls.maxDistance = 40;
        this.controls.maxPolarAngle = Math.PI / 2 + 0.1;
        this.controls.target.set(0, 2, 0);
    }

    createRunway() {
        // Main runway floor
        const runwayGeometry = new THREE.PlaneGeometry(8, 60);
        const runwayMaterial = new THREE.MeshStandardMaterial({
            color: THEME.black,
            metalness: 0.8,
            roughness: 0.2
        });
        const runway = new THREE.Mesh(runwayGeometry, runwayMaterial);
        runway.rotation.x = -Math.PI / 2;
        runway.receiveShadow = true;
        this.scene.add(runway);

        // Gold edge strips
        const stripMaterial = new THREE.MeshStandardMaterial({
            color: THEME.gold,
            metalness: 0.9,
            roughness: 0.1,
            emissive: THEME.gold,
            emissiveIntensity: 0.3
        });

        [-4, 4].forEach(x => {
            const stripGeometry = new THREE.PlaneGeometry(0.1, 60);
            const strip = new THREE.Mesh(stripGeometry, stripMaterial);
            strip.rotation.x = -Math.PI / 2;
            strip.position.set(x, 0.01, 0);
            this.scene.add(strip);
        });

        // Center line (subtle gold)
        const centerGeometry = new THREE.PlaneGeometry(0.05, 60);
        const centerMaterial = new THREE.MeshStandardMaterial({
            color: THEME.gold,
            emissive: THEME.gold,
            emissiveIntensity: 0.5,
            transparent: true,
            opacity: 0.5
        });
        const center = new THREE.Mesh(centerGeometry, centerMaterial);
        center.rotation.x = -Math.PI / 2;
        center.position.y = 0.01;
        this.scene.add(center);

        // Audience silhouettes
        const seatMaterial = new THREE.MeshStandardMaterial({ color: 0x080808 });
        for (let side of [-1, 1]) {
            for (let row = 0; row < 3; row++) {
                for (let i = 0; i < 12; i++) {
                    const seatGeometry = new THREE.BoxGeometry(0.6, 1, 0.4);
                    const seat = new THREE.Mesh(seatGeometry, seatMaterial);
                    seat.position.set(
                        side * (6 + row * 1.5),
                        0.5,
                        -20 + i * 3
                    );
                    this.scene.add(seat);
                }
            }
        }
    }

    createStudioLighting() {
        // Ambient (very subtle)
        const ambient = new THREE.AmbientLight(0x1a1a1a, 0.3);
        this.scene.add(ambient);

        // Key light
        const keyLight = new THREE.SpotLight(0xffffff, 10, 50, Math.PI / 8, 0.5);
        keyLight.position.set(0, 15, 10);
        keyLight.castShadow = true;
        keyLight.shadow.mapSize.width = 1024;
        keyLight.shadow.mapSize.height = 1024;
        this.scene.add(keyLight);
        this.spotlights.push({ light: keyLight, phase: 0 });

        // Runway spotlights
        const spotPositions = [
            { x: -6, z: -15 }, { x: 6, z: -15 },
            { x: -6, z: 0 }, { x: 6, z: 0 },
            { x: -6, z: 15 }, { x: 6, z: 15 },
            { x: 0, z: -25 }, { x: 0, z: 20 }
        ];

        spotPositions.forEach((pos, i) => {
            const isGold = i % 2 === 1;
            const spotlight = new THREE.SpotLight(
                isGold ? THEME.gold : 0xffffff,
                8,
                40,
                Math.PI / 10,
                0.5
            );
            spotlight.position.set(pos.x, 12, pos.z);
            spotlight.castShadow = true;
            this.scene.add(spotlight);
            this.spotlights.push({ light: spotlight, phase: i * 0.5 });

            // Spotlight housing
            const housingGeometry = new THREE.CylinderGeometry(0.3, 0.2, 0.5, 8);
            const housingMaterial = new THREE.MeshStandardMaterial({
                color: 0x1a1a1a,
                metalness: 0.9,
                roughness: 0.3
            });
            const housing = new THREE.Mesh(housingGeometry, housingMaterial);
            housing.position.set(pos.x, 12, pos.z);
            this.scene.add(housing);
        });

        // Gold accent lights
        const accentLight1 = new THREE.PointLight(THEME.gold, 1, 15);
        accentLight1.position.set(-10, 5, 5);
        this.scene.add(accentLight1);

        const accentLight2 = new THREE.PointLight(THEME.roseGold, 1, 15);
        accentLight2.position.set(10, 5, 5);
        this.scene.add(accentLight2);
    }

    createDisplayPedestal() {
        // Central display pedestal
        const pedestalGroup = new THREE.Group();

        // Base
        const baseGeometry = new THREE.CylinderGeometry(1.5, 1.8, 0.3, 32);
        const baseMaterial = new THREE.MeshStandardMaterial({
            color: THEME.black,
            metalness: 0.9,
            roughness: 0.1
        });
        const base = new THREE.Mesh(baseGeometry, baseMaterial);
        base.position.y = 0.15;
        base.receiveShadow = true;
        pedestalGroup.add(base);

        // Gold ring
        const ringGeometry = new THREE.TorusGeometry(1.6, 0.05, 16, 64);
        const ringMaterial = new THREE.MeshStandardMaterial({
            color: THEME.gold,
            metalness: 0.9,
            roughness: 0.1,
            emissive: THEME.gold,
            emissiveIntensity: 0.3
        });
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.rotation.x = Math.PI / 2;
        ring.position.y = 0.3;
        pedestalGroup.add(ring);

        // Display model (placeholder geometric form)
        const displayGeometry = new THREE.OctahedronGeometry(1.5);
        const displayMaterial = new THREE.MeshStandardMaterial({
            color: THEME.gold,
            metalness: 0.9,
            roughness: 0.1,
            emissive: THEME.gold,
            emissiveIntensity: 0.2
        });
        this.displayModel = new THREE.Mesh(displayGeometry, displayMaterial);
        this.displayModel.position.y = 2;
        this.displayModel.castShadow = true;
        pedestalGroup.add(this.displayModel);

        pedestalGroup.position.set(0, 0, 0);
        this.scene.add(pedestalGroup);
    }

    createBackdrop() {
        // Main backdrop
        const backdropGeometry = new THREE.PlaneGeometry(30, 15);
        const backdropMaterial = new THREE.MeshStandardMaterial({
            color: THEME.black,
            metalness: 0.1,
            roughness: 0.9
        });
        const backdrop = new THREE.Mesh(backdropGeometry, backdropMaterial);
        backdrop.position.set(0, 7.5, -30);
        this.scene.add(backdrop);

        // SKYYROSE logo (letter boxes)
        const logoMaterial = new THREE.MeshStandardMaterial({
            color: THEME.gold,
            metalness: 0.9,
            roughness: 0.1,
            emissive: THEME.gold,
            emissiveIntensity: 0.2
        });

        const letters = 'SKYYROSE';
        letters.split('').forEach((char, i) => {
            const letterGeometry = new THREE.BoxGeometry(0.8, 2, 0.2);
            const letter = new THREE.Mesh(letterGeometry, logoMaterial);
            letter.position.set(-5 + i * 1.3, 8, -29.5);
            this.scene.add(letter);
        });

        // Logo spotlight
        const logoLight = new THREE.SpotLight(THEME.gold, 5, 20, Math.PI / 6, 0.3);
        logoLight.position.set(0, 12, -20);
        this.scene.add(logoLight);
    }

    createGoldParticles() {
        const positions = new Float32Array(this.options.particleCount * 3);
        const colors = new Float32Array(this.options.particleCount * 3);
        const velocities = new Float32Array(this.options.particleCount * 3);

        const goldColor = new THREE.Color(THEME.gold);
        const champagneColor = new THREE.Color(THEME.champagne);

        for (let i = 0; i < this.options.particleCount; i++) {
            // Distribute throughout the venue
            positions[i * 3] = (Math.random() - 0.5) * 30;
            positions[i * 3 + 1] = 1 + Math.random() * 12;
            positions[i * 3 + 2] = (Math.random() - 0.5) * 50;

            // Gentle drift
            velocities[i * 3] = (Math.random() - 0.5) * 0.003;
            velocities[i * 3 + 1] = -0.002 - Math.random() * 0.003;
            velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.003;

            // Mix of gold and champagne
            const color = Math.random() > 0.3 ? goldColor : champagneColor;
            colors[i * 3] = color.r;
            colors[i * 3 + 1] = color.g;
            colors[i * 3 + 2] = color.b;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.userData.velocities = velocities;

        const material = new THREE.PointsMaterial({
            size: 0.04,
            vertexColors: true,
            transparent: true,
            opacity: 0.7,
            blending: THREE.AdditiveBlending,
            sizeAttenuation: true
        });

        this.particles = new THREE.Points(geometry, material);
        this.scene.add(this.particles);
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

        // Diamond shape
        const diamondGeometry = new THREE.OctahedronGeometry(0.15);
        const diamondMaterial = new THREE.MeshBasicMaterial({
            color: THEME.gold,
            transparent: true,
            opacity: 0.8,
            wireframe: true
        });
        const diamond = new THREE.Mesh(diamondGeometry, diamondMaterial);
        group.add(diamond);

        // Outer ring
        const ringGeometry = new THREE.TorusGeometry(0.2, 0.015, 16, 32);
        const ringMaterial = new THREE.MeshBasicMaterial({
            color: THEME.gold,
            transparent: true,
            opacity: 0.6
        });
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.rotation.x = Math.PI / 2;
        group.add(ring);

        // Position along the runway
        const zPos = -15 + (index * 8);
        group.position.set(0, 2, zPos);

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
            0.3,
            0.9
        );
        this.composer.addPass(bloomPass);
    }

    bindEvents() {
        window.addEventListener('resize', this.onResize.bind(this));
        this.canvas.addEventListener('click', this.onClick.bind(this));
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
        const rect = this.canvas.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

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

    animateCameraAlongRunway() {
        const path = [
            { x: 0, y: 2, z: 25 },
            { x: 0, y: 2, z: 15 },
            { x: 0, y: 2, z: 5 },
            { x: 0, y: 2, z: -5 },
            { x: 0, y: 3, z: 20 }
        ];

        let i = 0;
        const next = () => {
            if (i < path.length) {
                this.tweenCamera(path[i++]);
                setTimeout(next, 1800);
            }
        };
        next();
    }

    transitionToScene(sceneIndex) {
        this.currentScene = sceneIndex;

        const positions = [
            { x: 0, y: 3, z: 20 },
            { x: -12, y: 6, z: 5 },
            { x: 12, y: 8, z: -10 }
        ];

        const pos = positions[sceneIndex % positions.length];
        this.tweenCamera(pos);
    }

    tweenCamera(target) {
        const start = {
            x: this.camera.position.x,
            y: this.camera.position.y,
            z: this.camera.position.z
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

        // Animate display model
        if (this.displayModel) {
            this.displayModel.rotation.y = time * 0.3;
        }

        // Animate spotlights
        this.spotlights.forEach(({ light, phase }) => {
            light.intensity = 6 + Math.sin(time * 2 + phase) * 2;
        });

        // Animate particles
        if (this.particles) {
            const positions = this.particles.geometry.attributes.position.array;
            const velocities = this.particles.geometry.userData.velocities;

            for (let i = 0; i < positions.length; i += 3) {
                positions[i] += velocities[i];
                positions[i + 1] += velocities[i + 1];
                positions[i + 2] += velocities[i + 2];

                // Reset fallen particles
                if (positions[i + 1] < 0) {
                    positions[i + 1] = 12;
                    positions[i] = (Math.random() - 0.5) * 30;
                    positions[i + 2] = (Math.random() - 0.5) * 50;
                }
            }
            this.particles.geometry.attributes.position.needsUpdate = true;
        }

        // Animate hotspots
        this.productHotspots.forEach((hotspot, index) => {
            hotspot.rotation.y = time * 0.8;
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
    }
}

/**
 * Initialize Signature scene
 */
export function initSignatureScene(canvas, options = {}) {
    const scene = new SignatureScene(canvas, options);
    scene.start();
    return scene;
}

// Global exports
if (typeof window !== 'undefined') {
    window.SkyyRoseSignatureScene = SignatureScene;
    window.initSignatureScene = initSignatureScene;
}
