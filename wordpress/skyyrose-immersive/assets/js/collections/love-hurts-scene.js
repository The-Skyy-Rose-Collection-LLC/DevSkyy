/**
 * SkyyRose Love Hurts Collection Scene
 *
 * Gothic ballroom 3D environment honoring the Hurt family legacy.
 * Features: Chandelier, hearts, velvet atmosphere, and romantic lighting.
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
 * Love Hurts Collection Theme Colors
 */
const THEME = {
    rose: 0xE91E63,
    burgundy: 0x880E4F,
    blush: 0xF8BBD9,
    purple: 0x9B59B6,
    darkPurple: 0x0a0510,
    gold: 0xD4AF37
};

/**
 * Love Hurts Castle Scene Class
 */
export class LoveHurtsScene {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.options = {
            particleCount: options.particleCount || 400,
            heartCount: options.heartCount || 20,
            enableBloom: options.enableBloom !== false,
            bloomStrength: options.bloomStrength || 0.8,
            isMobile: options.isMobile || false,
            products: options.products || [],
            onProductClick: options.onProductClick || null,
            ...options
        };

        if (this.options.isMobile) {
            this.options.particleCount = Math.floor(this.options.particleCount * 0.4);
            this.options.heartCount = Math.floor(this.options.heartCount * 0.5);
        }

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.composer = null;
        this.clock = new THREE.Clock();

        this.chandelier = null;
        this.chandelierLights = [];
        this.hearts = [];
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
        this.createBallroom();
        this.createChandelier();
        this.createFloatingHearts();
        this.createHeartParticles();
        this.createProductHotspots();

        if (this.options.enableBloom) {
            this.setupPostProcessing();
        }

        this.bindEvents();
    }

    createScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(THEME.darkPurple);
        this.scene.fog = new THREE.FogExp2(THEME.darkPurple, 0.015);
    }

    createCamera() {
        this.camera = new THREE.PerspectiveCamera(
            60,
            this.canvas.clientWidth / this.canvas.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 5, 15);
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
        this.renderer.toneMappingExposure = 0.6;
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    }

    createControls() {
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 5;
        this.controls.maxDistance = 30;
        this.controls.maxPolarAngle = Math.PI / 2 + 0.2;
        this.controls.target.set(0, 3, 0);
    }

    createBallroom() {
        // Floor - dark marble
        const floorGeometry = new THREE.PlaneGeometry(40, 40);
        const floorMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a0a1a,
            metalness: 0.9,
            roughness: 0.2
        });
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        this.scene.add(floor);

        // Decorative floor pattern
        const patternGeometry = new THREE.RingGeometry(3, 8, 8);
        const patternMaterial = new THREE.MeshStandardMaterial({
            color: THEME.burgundy,
            metalness: 0.8,
            roughness: 0.3,
            transparent: true,
            opacity: 0.3
        });
        const pattern = new THREE.Mesh(patternGeometry, patternMaterial);
        pattern.rotation.x = -Math.PI / 2;
        pattern.position.y = 0.01;
        this.scene.add(pattern);

        // Walls (backdrop)
        const wallGeometry = new THREE.PlaneGeometry(50, 20);
        const wallMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a0a1a,
            metalness: 0.2,
            roughness: 0.8
        });

        // Back wall
        const backWall = new THREE.Mesh(wallGeometry, wallMaterial);
        backWall.position.set(0, 10, -20);
        this.scene.add(backWall);

        // Side walls
        const leftWall = new THREE.Mesh(wallGeometry, wallMaterial.clone());
        leftWall.rotation.y = Math.PI / 2;
        leftWall.position.set(-20, 10, 0);
        this.scene.add(leftWall);

        const rightWall = new THREE.Mesh(wallGeometry, wallMaterial.clone());
        rightWall.rotation.y = -Math.PI / 2;
        rightWall.position.set(20, 10, 0);
        this.scene.add(rightWall);

        // Velvet curtains
        this.createCurtain(-12, 8);
        this.createCurtain(12, 8);
    }

    createCurtain(x, height) {
        const curtainGeometry = new THREE.PlaneGeometry(4, height, 10, 20);
        const positions = curtainGeometry.attributes.position;

        // Add wave effect
        for (let i = 0; i < positions.count; i++) {
            const y = positions.getY(i);
            const wave = Math.sin(y * 2) * 0.2;
            positions.setZ(i, wave);
        }
        curtainGeometry.computeVertexNormals();

        const curtainMaterial = new THREE.MeshStandardMaterial({
            color: THEME.burgundy,
            metalness: 0.1,
            roughness: 0.9,
            side: THREE.DoubleSide
        });

        const curtain = new THREE.Mesh(curtainGeometry, curtainMaterial);
        curtain.position.set(x, height / 2, -18);
        this.scene.add(curtain);
    }

    createChandelier() {
        this.chandelier = new THREE.Group();

        // Central sphere
        const centerGeometry = new THREE.SphereGeometry(0.5, 32, 32);
        const centerMaterial = new THREE.MeshStandardMaterial({
            color: THEME.gold,
            metalness: 0.9,
            roughness: 0.1,
            emissive: THEME.gold,
            emissiveIntensity: 0.2
        });
        const center = new THREE.Mesh(centerGeometry, centerMaterial);
        this.chandelier.add(center);

        // Chandelier arms and crystals
        const armCount = 8;
        for (let i = 0; i < armCount; i++) {
            const angle = (i / armCount) * Math.PI * 2;
            const arm = this.createChandelierArm(angle);
            this.chandelier.add(arm);
        }

        // Hanging chain
        const chainGeometry = new THREE.CylinderGeometry(0.02, 0.02, 4, 8);
        const chainMaterial = new THREE.MeshStandardMaterial({
            color: THEME.gold,
            metalness: 0.9,
            roughness: 0.2
        });
        const chain = new THREE.Mesh(chainGeometry, chainMaterial);
        chain.position.y = 2;
        this.chandelier.add(chain);

        // Main chandelier light
        const mainLight = new THREE.PointLight(THEME.blush, 2, 25);
        mainLight.position.y = -0.5;
        mainLight.castShadow = true;
        this.chandelier.add(mainLight);
        this.chandelierLights.push(mainLight);

        this.chandelier.position.set(0, 12, 0);
        this.scene.add(this.chandelier);

        // Ambient lighting
        const ambient = new THREE.AmbientLight(THEME.purple, 0.1);
        this.scene.add(ambient);

        // Rim lights
        const rimLight1 = new THREE.SpotLight(THEME.rose, 1, 30, Math.PI / 6, 0.5);
        rimLight1.position.set(-10, 8, 10);
        this.scene.add(rimLight1);

        const rimLight2 = new THREE.SpotLight(THEME.purple, 1, 30, Math.PI / 6, 0.5);
        rimLight2.position.set(10, 8, 10);
        this.scene.add(rimLight2);
    }

    createChandelierArm(angle) {
        const armGroup = new THREE.Group();

        // Arm
        const armGeometry = new THREE.CylinderGeometry(0.03, 0.03, 1.5, 8);
        const armMaterial = new THREE.MeshStandardMaterial({
            color: THEME.gold,
            metalness: 0.9,
            roughness: 0.2
        });
        const arm = new THREE.Mesh(armGeometry, armMaterial);
        arm.rotation.z = Math.PI / 3;
        arm.position.x = 0.5;
        arm.position.y = -0.3;
        armGroup.add(arm);

        // Crystal
        const crystalGeometry = new THREE.OctahedronGeometry(0.15);
        const crystalMaterial = new THREE.MeshStandardMaterial({
            color: 0xffffff,
            metalness: 0.1,
            roughness: 0,
            transparent: true,
            opacity: 0.8,
            emissive: THEME.blush,
            emissiveIntensity: 0.3
        });
        const crystal = new THREE.Mesh(crystalGeometry, crystalMaterial);
        crystal.position.set(1.2, -0.8, 0);
        armGroup.add(crystal);

        // Small light at crystal
        const crystalLight = new THREE.PointLight(THEME.rose, 0.5, 5);
        crystalLight.position.copy(crystal.position);
        armGroup.add(crystalLight);
        this.chandelierLights.push(crystalLight);

        armGroup.rotation.y = angle;
        return armGroup;
    }

    createFloatingHearts() {
        for (let i = 0; i < this.options.heartCount; i++) {
            const heart = this.createHeart();

            heart.position.set(
                (Math.random() - 0.5) * 30,
                2 + Math.random() * 10,
                (Math.random() - 0.5) * 30
            );

            heart.scale.setScalar(0.3 + Math.random() * 0.5);
            heart.userData.floatSpeed = 0.3 + Math.random() * 0.4;
            heart.userData.floatOffset = Math.random() * Math.PI * 2;
            heart.userData.baseY = heart.position.y;
            heart.userData.rotSpeed = (Math.random() - 0.5) * 0.02;

            this.hearts.push(heart);
            this.scene.add(heart);
        }
    }

    createHeart() {
        const heartShape = new THREE.Shape();
        const x = 0, y = 0;

        heartShape.moveTo(x + 0.25, y + 0.25);
        heartShape.bezierCurveTo(x + 0.25, y + 0.25, x + 0.2, y, x, y);
        heartShape.bezierCurveTo(x - 0.35, y, x - 0.35, y + 0.35, x - 0.35, y + 0.35);
        heartShape.bezierCurveTo(x - 0.35, y + 0.55, x - 0.2, y + 0.77, x + 0.25, y + 0.95);
        heartShape.bezierCurveTo(x + 0.7, y + 0.77, x + 0.85, y + 0.55, x + 0.85, y + 0.35);
        heartShape.bezierCurveTo(x + 0.85, y + 0.35, x + 0.85, y, x + 0.5, y);
        heartShape.bezierCurveTo(x + 0.35, y, x + 0.25, y + 0.25, x + 0.25, y + 0.25);

        const extrudeSettings = {
            depth: 0.1,
            bevelEnabled: true,
            bevelSegments: 2,
            bevelSize: 0.02,
            bevelThickness: 0.02
        };

        const geometry = new THREE.ExtrudeGeometry(heartShape, extrudeSettings);
        const material = new THREE.MeshStandardMaterial({
            color: THEME.rose,
            metalness: 0.3,
            roughness: 0.5,
            emissive: THEME.burgundy,
            emissiveIntensity: 0.2,
            transparent: true,
            opacity: 0.7
        });

        const heart = new THREE.Mesh(geometry, material);
        heart.rotation.z = Math.PI;
        return heart;
    }

    createHeartParticles() {
        const positions = new Float32Array(this.options.particleCount * 3);
        const colors = new Float32Array(this.options.particleCount * 3);
        const velocities = new Float32Array(this.options.particleCount * 3);

        const roseColor = new THREE.Color(THEME.rose);
        const blushColor = new THREE.Color(THEME.blush);
        const purpleColor = new THREE.Color(THEME.purple);

        for (let i = 0; i < this.options.particleCount; i++) {
            // Distribute throughout the ballroom
            positions[i * 3] = (Math.random() - 0.5) * 35;
            positions[i * 3 + 1] = 1 + Math.random() * 12;
            positions[i * 3 + 2] = (Math.random() - 0.5) * 35;

            // Gentle floating
            velocities[i * 3] = (Math.random() - 0.5) * 0.005;
            velocities[i * 3 + 1] = (Math.random() - 0.5) * 0.008;
            velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.005;

            // Mix of colors
            const colorChoice = Math.random();
            let color;
            if (colorChoice < 0.4) color = roseColor;
            else if (colorChoice < 0.7) color = blushColor;
            else color = purpleColor;

            colors[i * 3] = color.r;
            colors[i * 3 + 1] = color.g;
            colors[i * 3 + 2] = color.b;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.userData.velocities = velocities;

        const material = new THREE.PointsMaterial({
            size: 0.06,
            vertexColors: true,
            transparent: true,
            opacity: 0.6,
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

        // Heart-shaped hotspot
        const heart = this.createHeart();
        heart.scale.setScalar(0.3);
        heart.material = heart.material.clone();
        heart.material.emissiveIntensity = 0.5;
        group.add(heart);

        // Glow ring
        const ringGeometry = new THREE.TorusGeometry(0.2, 0.02, 16, 32);
        const ringMaterial = new THREE.MeshBasicMaterial({
            color: THEME.rose,
            transparent: true,
            opacity: 0.6
        });
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.rotation.x = Math.PI / 2;
        group.add(ring);

        // Position
        const angle = (index / Math.max(this.options.products.length, 1)) * Math.PI * 1.5 - Math.PI / 4;
        const radius = 5;
        group.position.set(
            Math.cos(angle) * radius,
            3,
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
            0.7
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

    transitionToScene(sceneIndex) {
        this.currentScene = sceneIndex;

        const positions = [
            { x: 0, y: 5, z: 15, targetY: 3 },
            { x: -10, y: 8, z: 8, targetY: 4 },
            { x: 10, y: 6, z: -5, targetY: 2 }
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

        // Animate chandelier
        if (this.chandelier) {
            this.chandelier.rotation.y = time * 0.1;
        }

        // Animate chandelier lights (flickering)
        this.chandelierLights.forEach((light, index) => {
            light.intensity = 0.4 + Math.sin(time * 3 + index) * 0.1;
        });

        // Animate hearts
        this.hearts.forEach(heart => {
            if (heart.userData.baseY !== undefined) {
                heart.position.y = heart.userData.baseY +
                    Math.sin(time * heart.userData.floatSpeed + heart.userData.floatOffset) * 0.5;
            }
            heart.rotation.y += heart.userData.rotSpeed;
        });

        // Animate particles
        if (this.particles) {
            const positions = this.particles.geometry.attributes.position.array;
            const velocities = this.particles.geometry.userData.velocities;

            for (let i = 0; i < positions.length; i += 3) {
                positions[i] += velocities[i] + Math.sin(time + i) * 0.002;
                positions[i + 1] += velocities[i + 1];
                positions[i + 2] += velocities[i + 2] + Math.cos(time + i) * 0.002;

                // Boundary wrapping
                if (positions[i] > 17) positions[i] = -17;
                if (positions[i] < -17) positions[i] = 17;
                if (positions[i + 1] > 13) positions[i + 1] = 1;
                if (positions[i + 1] < 1) positions[i + 1] = 13;
                if (positions[i + 2] > 17) positions[i + 2] = -17;
                if (positions[i + 2] < -17) positions[i + 2] = 17;
            }
            this.particles.geometry.attributes.position.needsUpdate = true;
        }

        // Animate hotspots
        this.productHotspots.forEach((hotspot, index) => {
            const scale = 1 + Math.sin(time * 2 + index) * 0.15;
            hotspot.scale.setScalar(scale);
            hotspot.rotation.y = time * 0.5;
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
 * Initialize Love Hurts scene
 */
export function initLoveHurtsScene(canvas, options = {}) {
    const scene = new LoveHurtsScene(canvas, options);
    scene.start();
    return scene;
}

// Global exports
if (typeof window !== 'undefined') {
    window.SkyyRoseLoveHurtsScene = LoveHurtsScene;
    window.initLoveHurtsScene = initLoveHurtsScene;
}
