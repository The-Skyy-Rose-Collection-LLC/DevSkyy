/**
 * SkyyRose Experience Base Class
 * Foundation for all immersive 3D collection experiences
 * Uses Three.js r160+ with post-processing and PBR materials
 * CDN: loaded via wp_enqueue_script in enqueue.php
 */

// Verify Three.js is loaded before proceeding
if (typeof THREE === 'undefined') {
    console.error('SkyyRose 3D: Three.js library not loaded. Check script dependencies and network connectivity.');
    window.SkyyRoseExperience = null;
} else {

class SkyyRoseExperience {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error('SkyyRose 3D: Container #' + containerId + ' not found');
        }

        // Configuration
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

        // State
        this.isLoading = true;
        this.loadProgress = 0;
        this.isRunning = true;
        this.rafId = null;
        this.clock = new THREE.Clock();
        this.mixers = [];
        this.interactiveObjects = [];
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        // Reduced motion preference
        this.prefersReducedMotion = window.matchMedia
            && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        // Initialize
        this.init();
        this.setupEventListeners();
        this.animate();
    }

    init() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(this.options.backgroundColor);

        // Camera
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(
            this.options.cameraFov,
            aspect,
            this.options.cameraNear,
            this.options.cameraFar
        );
        this.camera.position.set(0, 2, 8);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: false,
            powerPreference: 'high-performance'
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;

        if (this.options.enableShadows) {
            this.renderer.shadowMap.enabled = true;
            this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        }

        this.container.appendChild(this.renderer.domElement);

        // a11y: announce the canvas as an image with a meaningful label.
        // Screen readers otherwise see a bare <canvas> with no role or name.
        var sceneLabel = this.options.ariaLabel
            || (this.container.dataset && this.container.dataset.sceneLabel)
            || 'SkyyRose immersive 3D scene';
        this.renderer.domElement.setAttribute('role', 'img');
        this.renderer.domElement.setAttribute('aria-label', sceneLabel);

        // Controls
        if (typeof THREE.OrbitControls !== 'undefined') {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;
            this.controls.maxPolarAngle = Math.PI * 0.85;
            this.controls.minDistance = 2;
            this.controls.maxDistance = 20;
            this.controls.target.set(0, 1, 0);
        }

        // Post-processing
        if (this.options.enablePostProcessing && typeof THREE.EffectComposer !== 'undefined') {
            this.setupPostProcessing();
        }

        // Loaders
        this.loadingManager = new THREE.LoadingManager(
            () => this.onLoadComplete(),
            (url, loaded, total) => this.onLoadProgress(url, loaded, total),
            (url) => this.onLoadError(url)
        );

        if (typeof THREE.GLTFLoader !== 'undefined') {
            this.gltfLoader = new THREE.GLTFLoader(this.loadingManager);

            // DRACO compression support
            if (typeof THREE.DRACOLoader !== 'undefined') {
                const dracoLoader = new THREE.DRACOLoader();
                dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
                this.gltfLoader.setDRACOLoader(dracoLoader);
            }
        } else {
            this.gltfLoader = null;
        }

        this.textureLoader = new THREE.TextureLoader(this.loadingManager);

        if (typeof THREE.RGBELoader !== 'undefined') {
            this.rgbeLoader = new THREE.RGBELoader(this.loadingManager);
        }
    }

    setupPostProcessing() {
        this.composer = new THREE.EffectComposer(this.renderer);

        const renderPass = new THREE.RenderPass(this.scene, this.camera);
        this.composer.addPass(renderPass);

        // Bloom for ethereal glow
        if (typeof THREE.UnrealBloomPass !== 'undefined') {
            this.bloomPass = new THREE.UnrealBloomPass(
                new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
                0.5,  // strength
                0.4,  // radius
                0.85  // threshold
            );
            this.composer.addPass(this.bloomPass);
        }
    }

    setupEventListeners() {
        // Store bound references for proper cleanup in dispose()
        this._onResize = () => this.onResize();
        this._onMouseMove = (e) => {
            const rect = this.container.getBoundingClientRect();
            this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        };
        this._onClick = () => this.onClick();

        window.addEventListener('resize', this._onResize);
        this.container.addEventListener('mousemove', this._onMouseMove);
        this.container.addEventListener('click', this._onClick);
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

    onClick() {
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.interactiveObjects, true);

        if (intersects.length > 0) {
            const object = intersects[0].object;
            if (object.userData.onClick) {
                object.userData.onClick(object);
            }
        }
    }

    onLoadProgress(url, loaded, total) {
        this.loadProgress = (loaded / total) * 100;
        this.updateLoadingUI();
    }

    onLoadComplete() {
        this.isLoading = false;
        this.hideLoadingUI();
        // Reduced-motion users get a single static render after assets load
        if (this.prefersReducedMotion) {
            this.renderer.render(this.scene, this.camera);
        }
    }

    onLoadError(url) {
        console.error(`Failed to load: ${url}`);
    }

    updateLoadingUI() {
        const loader = this.container.querySelector('.skyyrose-3d-loading');
        if (loader) {
            const progressBar = loader.querySelector('.loading-progress');
            if (progressBar) {
                progressBar.style.width = `${this.loadProgress}%`;
            }
        }
    }

    hideLoadingUI() {
        const loader = this.container.querySelector('.skyyrose-3d-loading');
        if (loader) {
            loader.classList.add('loaded');
            setTimeout(() => loader.remove(), 500);
        }
    }

    // Utility: Load GLB model
    async loadModel(url, options = {}) {
        if (!this.gltfLoader) {
            console.warn('GLTFLoader not available — model loading skipped');
            return Promise.resolve(null);
        }
        return new Promise((resolve, reject) => {
            this.gltfLoader.load(
                url,
                (gltf) => {
                    const model = gltf.scene;

                    if (options.scale) {
                        model.scale.setScalar(options.scale);
                    }
                    if (options.position) {
                        model.position.copy(options.position);
                    }
                    if (options.rotation) {
                        model.rotation.set(options.rotation.x || 0, options.rotation.y || 0, options.rotation.z || 0);
                    }

                    // Enable shadows
                    model.traverse((child) => {
                        if (child.isMesh) {
                            child.castShadow = true;
                            child.receiveShadow = true;
                        }
                    });

                    // Handle animations
                    if (gltf.animations.length > 0) {
                        const mixer = new THREE.AnimationMixer(model);
                        gltf.animations.forEach((clip) => {
                            mixer.clipAction(clip).play();
                        });
                        this.mixers.push(mixer);
                    }

                    this.scene.add(model);
                    resolve({ model, gltf });
                },
                undefined,
                reject
            );
        });
    }

    // Utility: Load HDR environment
    async loadEnvironment(url) {
        if (!this.rgbeLoader) {
            console.warn('RGBELoader not available');
            return;
        }

        return new Promise((resolve, reject) => {
            this.rgbeLoader.load(
                url,
                (texture) => {
                    texture.mapping = THREE.EquirectangularReflectionMapping;
                    this.scene.environment = texture;
                    resolve(texture);
                },
                undefined,
                reject
            );
        });
    }

    // Utility: Create particle system
    createParticles(options = {}) {
        const {
            count = 1000,
            color = 0xffffff,
            size = 0.05,
            area = { x: 10, y: 10, z: 10 },
            velocity = { x: 0, y: -0.02, z: 0 }
        } = options;

        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(count * 3);
        const velocities = new Float32Array(count * 3);

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            positions[i3] = (Math.random() - 0.5) * area.x;
            positions[i3 + 1] = Math.random() * area.y;
            positions[i3 + 2] = (Math.random() - 0.5) * area.z;

            velocities[i3] = velocity.x + (Math.random() - 0.5) * 0.01;
            velocities[i3 + 1] = velocity.y;
            velocities[i3 + 2] = velocity.z + (Math.random() - 0.5) * 0.01;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.userData.velocities = velocities;
        geometry.userData.area = area;

        const material = new THREE.PointsMaterial({
            color,
            size,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending
        });

        const particles = new THREE.Points(geometry, material);
        this.scene.add(particles);

        return particles;
    }

    // Update particle positions
    updateParticles(particles, delta) {
        const positions = particles.geometry.attributes.position.array;
        const velocities = particles.geometry.userData.velocities;
        const area = particles.geometry.userData.area;

        for (let i = 0; i < positions.length; i += 3) {
            positions[i] += velocities[i] * delta * 60;
            positions[i + 1] += velocities[i + 1] * delta * 60;
            positions[i + 2] += velocities[i + 2] * delta * 60;

            // Reset particles that fall below
            if (positions[i + 1] < -1) {
                positions[i + 1] = area.y;
                positions[i] = (Math.random() - 0.5) * area.x;
                positions[i + 2] = (Math.random() - 0.5) * area.z;
            }
        }

        particles.geometry.attributes.position.needsUpdate = true;
    }

    // Utility: Create product pedestal
    createPedestal(options = {}) {
        const {
            position = new THREE.Vector3(0, 0, 0),
            radius = 0.5,
            height = 1,
            color = 0xffffff,
            emissive = 0x000000
        } = options;

        const group = new THREE.Group();

        // Base cylinder
        const baseGeometry = new THREE.CylinderGeometry(radius, radius * 1.2, height * 0.1, 32);
        const baseMaterial = new THREE.MeshStandardMaterial({
            color,
            metalness: 0.8,
            roughness: 0.2
        });
        const base = new THREE.Mesh(baseGeometry, baseMaterial);
        group.add(base);

        // Glowing ring
        const ringGeometry = new THREE.TorusGeometry(radius * 0.9, 0.02, 16, 100);
        const ringMaterial = new THREE.MeshStandardMaterial({
            color: emissive || color,
            emissive: emissive || color,
            emissiveIntensity: 0.5
        });
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.rotation.x = Math.PI / 2;
        ring.position.y = height * 0.05;
        group.add(ring);

        // Spotlight
        const spotlight = new THREE.SpotLight(0xffffff, 1, 5, Math.PI / 6, 0.5);
        spotlight.position.set(0, 3, 0);
        spotlight.target.position.set(0, 0, 0);
        spotlight.castShadow = true;
        group.add(spotlight);
        group.add(spotlight.target);

        group.position.copy(position);
        this.scene.add(group);

        return group;
    }

    // Animation loop with lifecycle control
    animate() {
        if (!this.isRunning) return;

        // Reduced motion: render once then stop the loop entirely
        if (this.prefersReducedMotion) {
            this.renderer.render(this.scene, this.camera);
            return;
        }

        this.rafId = requestAnimationFrame(() => this.animate());

        const delta = this.clock.getDelta();

        // Update controls
        if (this.controls) {
            this.controls.update();
        }

        // Update animation mixers
        this.mixers.forEach((mixer) => mixer.update(delta));

        // Custom update (override in subclass)
        this.update(delta);

        // Render
        if (this.composer && this.options.enablePostProcessing) {
            this.composer.render();
        } else {
            this.renderer.render(this.scene, this.camera);
        }
    }

    // Override in subclass for custom updates
    update(delta) {}

    // Pause the rAF loop entirely. Stops the GPU from rendering on hidden tabs.
    // Reduced-motion scenes already self-stop after one render — pause is a no-op.
    pause() {
        if (this.prefersReducedMotion) return;
        this.isRunning = false;
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
        if (this.clock) this.clock.stop();
    }

    // Resume the rAF loop without discarding accumulated time.
    //
    // THREE.Clock.start() rebases oldTime AND zeroes elapsedTime. The subclass
    // scenes (blackrose, lovehurts, signature) read clock.elapsedTime as a
    // monotonic phase variable for Math.sin/cos animations — moon glow, petal
    // drift, candelabra sway, particle motion. Resetting it to 0 produces a
    // visible snap on every tab return, exactly the bug pause/resume was
    // supposed to prevent.
    //
    // Rebase oldTime directly so the next getDelta() returns ~0 (no
    // pause-duration spike) while elapsedTime keeps growing monotonically.
    resume() {
        if (this.prefersReducedMotion) return;
        if (this.isRunning) return;
        this.isRunning = true;
        if (this.clock) {
            this.clock.oldTime = (typeof performance !== 'undefined' ? performance.now() : Date.now());
            this.clock.running = true;
        }
        this.animate();
    }

    // Cleanup — stop loop, remove listeners, free GPU resources
    dispose() {
        // Stop the animation loop
        this.isRunning = false;
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }

        // Remove event listeners with correct references
        if (this._onResize) window.removeEventListener('resize', this._onResize);
        if (this._onMouseMove) this.container.removeEventListener('mousemove', this._onMouseMove);
        if (this._onClick) this.container.removeEventListener('click', this._onClick);

        // Dispose controls
        if (this.controls && this.controls.dispose) {
            this.controls.dispose();
        }

        // Dispose all scene objects
        this.scene.traverse((object) => {
            if (object.geometry) object.geometry.dispose();
            if (object.material) {
                if (Array.isArray(object.material)) {
                    object.material.forEach((mat) => {
                        if (mat.map) mat.map.dispose();
                        mat.dispose();
                    });
                } else {
                    if (object.material.map) object.material.map.dispose();
                    object.material.dispose();
                }
            }
        });

        // Remove canvas from DOM and release GPU context
        if (this.renderer.domElement && this.renderer.domElement.parentNode) {
            this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
        }
        this.renderer.forceContextLoss();
        this.renderer.dispose();
        if (this.composer) this.composer.dispose();
    }
}

// Export for use
window.SkyyRoseExperience = SkyyRoseExperience;

} // End THREE existence check
