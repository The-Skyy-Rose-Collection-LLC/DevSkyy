/**
 * SkyyRose Experience Base Class - ES Module Version
 * Foundation for all immersive 3D collection experiences
 * Uses Three.js r160 with post-processing and PBR materials
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

class SkyyRoseExperience {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container #${containerId} not found`);
            return;
        }

        this.options = {
            enablePostProcessing: true,
            enableParticles: true,
            enableShadows: true,
            backgroundColor: 0x0a0a0a,
            cameraFov: 60,
            cameraNear: 0.1,
            cameraFar: 1000,
            ...options
        };

        this.isLoading = true;
        this.loadProgress = 0;
        this.clock = new THREE.Clock();
        this.mixers = [];
        this.interactiveObjects = [];
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        this.init();
        this.setupEventListeners();
        this.animate();
    }

    init() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(this.options.backgroundColor);

        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(
            this.options.cameraFov,
            aspect,
            this.options.cameraNear,
            this.options.cameraFar
        );
        this.camera.position.set(0, 2, 8);

        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true,
            powerPreference: 'high-performance'
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = this.options.enableShadows;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        this.container.appendChild(this.renderer.domElement);

        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.maxPolarAngle = Math.PI * 0.85;
        this.controls.minDistance = 2;
        this.controls.maxDistance = 20;

        if (this.options.enablePostProcessing) {
            this.setupPostProcessing();
        }

        this.gltfLoader = new GLTFLoader();
        this.rgbeLoader = new RGBELoader();
    }

    setupPostProcessing() {
        this.composer = new EffectComposer(this.renderer);
        const renderPass = new RenderPass(this.scene, this.camera);
        this.composer.addPass(renderPass);

        this.bloomPass = new UnrealBloomPass(
            new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
            0.3, 0.4, 0.85
        );
        this.composer.addPass(this.bloomPass);
    }

    setupEventListeners() {
        window.addEventListener('resize', () => this.onResize());
        this.container.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.container.addEventListener('click', (e) => this.onClick(e));
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

    onMouseMove(event) {
        const rect = this.container.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    }

    onClick(event) {
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.interactiveObjects, true);
        if (intersects.length > 0) {
            const object = intersects[0].object;
            if (object.userData.productId) {
                this.onProductClick(object.userData.productId);
            }
        }
    }

    onProductClick(productId) {
        window.dispatchEvent(new CustomEvent('skyyrose:product-click', {
            detail: { productId }
        }));
    }

    createParticleSystem(count, options = {}) {
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(count * 3);
        const colors = new Float32Array(count * 3);
        const sizes = new Float32Array(count);

        const color = new THREE.Color(options.color || 0xffffff);
        const spread = options.spread || 10;

        for (let i = 0; i < count; i++) {
            positions[i * 3] = (Math.random() - 0.5) * spread;
            positions[i * 3 + 1] = Math.random() * spread;
            positions[i * 3 + 2] = (Math.random() - 0.5) * spread;
            colors[i * 3] = color.r;
            colors[i * 3 + 1] = color.g;
            colors[i * 3 + 2] = color.b;
            sizes[i] = Math.random() * (options.maxSize || 0.1) + (options.minSize || 0.02);
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        const material = new THREE.PointsMaterial({
            size: options.size || 0.05,
            vertexColors: true,
            transparent: true,
            opacity: options.opacity || 0.8,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        return new THREE.Points(geometry, material);
    }

    createProductPedestal(position, options = {}) {
        const group = new THREE.Group();
        const pedestalGeometry = new THREE.CylinderGeometry(
            options.radius || 0.5,
            options.radius || 0.5,
            options.height || 0.1,
            32
        );
        const pedestalMaterial = new THREE.MeshStandardMaterial({
            color: options.color || 0x1a1a1a,
            metalness: 0.8,
            roughness: 0.2
        });
        const pedestal = new THREE.Mesh(pedestalGeometry, pedestalMaterial);
        pedestal.castShadow = true;
        pedestal.receiveShadow = true;
        group.add(pedestal);
        group.position.copy(position);
        return group;
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        const delta = this.clock.getDelta();
        this.controls.update();
        this.mixers.forEach(mixer => mixer.update(delta));
        this.update(delta);
        if (this.composer && this.options.enablePostProcessing) {
            this.composer.render();
        } else {
            this.renderer.render(this.scene, this.camera);
        }
    }

    update(delta) {
        // Override in subclasses
    }

    setLoading(loading, progress = 0) {
        this.isLoading = loading;
        this.loadProgress = progress;
        window.dispatchEvent(new CustomEvent('skyyrose:loading', {
            detail: { loading, progress }
        }));
    }

    dispose() {
        this.renderer.dispose();
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
        if (this.composer) this.composer.dispose();
    }
}

// Export for ES modules
export { SkyyRoseExperience, THREE };

// Also expose globally for non-module scripts
window.SkyyRoseExperience = SkyyRoseExperience;
window.THREE = THREE;
