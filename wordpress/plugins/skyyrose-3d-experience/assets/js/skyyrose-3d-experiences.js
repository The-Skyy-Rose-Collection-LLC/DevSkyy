/**
 * SkyyRose 3D Experiences - WordPress Integration
 *
 * Production-grade 3D model viewer with fidelity validation.
 * Ensures all models meet 95% fidelity threshold before display.
 *
 * @version 2.0.0
 * @author SkyyRose LLC
 */

(function() {
    'use strict';

    // ============================================================================
    // Constants
    // ============================================================================

    const MINIMUM_FIDELITY_SCORE = 95.0;
    const SKYYROSE_BRAND_COLOR = 0xB76E79;
    const DARK_BACKGROUND = 0x1A1A1A;

    const COLLECTIONS = {
        black_rose: { name: 'BLACK ROSE Collection', theme: 'dark' },
        signature: { name: 'Signature Collection', theme: 'elegant' },
        love_hurts: { name: 'Love Hurts Collection', theme: 'dramatic' },
        showroom: { name: 'Virtual Showroom', theme: 'immersive' },
        runway: { name: 'Fashion Runway', theme: 'dynamic' }
    };

    // ============================================================================
    // SkyyRose3D Namespace
    // ============================================================================

    window.SkyyRose3D = window.SkyyRose3D || {};

    /**
     * Model Fidelity Validator
     * Validates 3D models against 95% fidelity threshold
     */
    class FidelityValidator {
        constructor(apiBase) {
            this.apiBase = apiBase;
            this.cache = new Map();
        }

        /**
         * Validate a 3D model's fidelity score
         * @param {string} modelUrl - URL of the 3D model
         * @returns {Promise<{passed: boolean, score: number, report: object}>}
         */
        async validate(modelUrl) {
            // Check cache
            if (this.cache.has(modelUrl)) {
                return this.cache.get(modelUrl);
            }

            try {
                const response = await fetch(`${this.apiBase}/elementor-3d/validate`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-WP-Nonce': window.SkyyRose3DConfig?.nonce || ''
                    },
                    body: JSON.stringify({ model_url: modelUrl })
                });

                if (!response.ok) {
                    throw new Error(`Validation failed: ${response.status}`);
                }

                const result = await response.json();
                const validation = {
                    passed: result.fidelity_score >= MINIMUM_FIDELITY_SCORE,
                    score: result.fidelity_score,
                    report: result.report || {}
                };

                // Cache successful validations
                this.cache.set(modelUrl, validation);
                return validation;
            } catch (error) {
                console.error('[SkyyRose3D] Fidelity validation error:', error);
                // Return failed validation on error - don't display unverified models
                return {
                    passed: false,
                    score: 0,
                    report: { error: error.message }
                };
            }
        }

        /**
         * Clear validation cache
         */
        clearCache() {
            this.cache.clear();
        }
    }

    /**
     * 3D Experience Manager
     * Manages collection 3D experiences with model verification
     */
    class Experience3DManager {
        constructor(container, config) {
            this.container = container;
            this.config = config;
            this.scene = null;
            this.camera = null;
            this.renderer = null;
            this.controls = null;
            this.models = new Map();
            this.animationId = null;
            this.isRunning = false;
            this.validator = new FidelityValidator(
                window.SkyyRose3DConfig?.apiBase || '/wp-json/skyyrose-3d/v1'
            );

            this.init();
        }

        /**
         * Initialize the 3D experience
         */
        init() {
            // Check for Three.js
            if (typeof THREE === 'undefined') {
                this.showError('Three.js library not loaded');
                return;
            }

            // Setup scene
            this.scene = new THREE.Scene();
            this.scene.background = new THREE.Color(
                this.config.backgroundColor || DARK_BACKGROUND
            );

            // Setup camera
            const aspect = this.container.clientWidth / this.container.clientHeight;
            this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
            this.camera.position.set(0, 2, 8);

            // Setup renderer
            this.renderer = new THREE.WebGLRenderer({
                antialias: true,
                alpha: true,
                powerPreference: 'high-performance'
            });
            this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            this.renderer.shadowMap.enabled = true;
            this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
            this.renderer.toneMappingExposure = 1;
            this.renderer.outputColorSpace = THREE.SRGBColorSpace;

            this.container.appendChild(this.renderer.domElement);

            // Setup controls (if OrbitControls available)
            if (THREE.OrbitControls) {
                this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
                this.controls.enableDamping = true;
                this.controls.dampingFactor = 0.05;
                this.controls.maxPolarAngle = Math.PI / 2;
                this.controls.minDistance = 2;
                this.controls.maxDistance = 20;
            }

            // Setup lighting
            this.setupLighting();

            // Setup environment
            this.setupEnvironment();

            // Handle resize
            window.addEventListener('resize', () => this.handleResize());

            // Hide loader
            this.hideLoader();

            // Start animation
            this.start();

            // Load collection products
            this.loadCollectionProducts();
        }

        /**
         * Setup scene lighting
         */
        setupLighting() {
            // Ambient light
            const ambient = new THREE.AmbientLight(0xffffff, 0.4);
            this.scene.add(ambient);

            // Key light (SkyyRose brand color tint)
            const keyLight = new THREE.DirectionalLight(0xffffff, 1);
            keyLight.position.set(5, 10, 5);
            keyLight.castShadow = true;
            keyLight.shadow.mapSize.width = 2048;
            keyLight.shadow.mapSize.height = 2048;
            keyLight.shadow.camera.near = 0.5;
            keyLight.shadow.camera.far = 50;
            this.scene.add(keyLight);

            // Fill light (subtle rose tint)
            const fillLight = new THREE.DirectionalLight(SKYYROSE_BRAND_COLOR, 0.3);
            fillLight.position.set(-5, 5, -5);
            this.scene.add(fillLight);

            // Rim light
            const rimLight = new THREE.DirectionalLight(0xffffff, 0.5);
            rimLight.position.set(0, 5, -10);
            this.scene.add(rimLight);
        }

        /**
         * Setup environment (floor, backdrop)
         */
        setupEnvironment() {
            // Floor
            const floorGeometry = new THREE.PlaneGeometry(50, 50);
            const floorMaterial = new THREE.MeshStandardMaterial({
                color: 0x111111,
                roughness: 0.8,
                metalness: 0.2
            });
            const floor = new THREE.Mesh(floorGeometry, floorMaterial);
            floor.rotation.x = -Math.PI / 2;
            floor.receiveShadow = true;
            this.scene.add(floor);

            // Grid helper (subtle)
            const grid = new THREE.GridHelper(50, 50, 0x222222, 0x222222);
            grid.position.y = 0.01;
            this.scene.add(grid);

            // Optional particles based on collection
            if (this.config.particleCount > 0) {
                this.createParticles();
            }
        }

        /**
         * Create ambient particles
         */
        createParticles() {
            const count = Math.min(this.config.particleCount || 1000, 5000);
            const geometry = new THREE.BufferGeometry();
            const positions = new Float32Array(count * 3);

            for (let i = 0; i < count * 3; i += 3) {
                positions[i] = (Math.random() - 0.5) * 30;
                positions[i + 1] = Math.random() * 15;
                positions[i + 2] = (Math.random() - 0.5) * 30;
            }

            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

            const material = new THREE.PointsMaterial({
                color: SKYYROSE_BRAND_COLOR,
                size: 0.02,
                transparent: true,
                opacity: 0.6,
                sizeAttenuation: true
            });

            this.particles = new THREE.Points(geometry, material);
            this.scene.add(this.particles);
        }

        /**
         * Load products for the collection
         */
        async loadCollectionProducts() {
            try {
                // Fetch products from API
                const response = await fetch(
                    `${window.SkyyRose3DConfig?.apiBase || '/wp-json/skyyrose-3d/v1'}/experiences?collection=${this.config.collection}`,
                    {
                        headers: {
                            'X-WP-Nonce': window.SkyyRose3DConfig?.nonce || ''
                        }
                    }
                );

                if (!response.ok) {
                    throw new Error(`Failed to fetch products: ${response.status}`);
                }

                const data = await response.json();
                const products = data.products || [];

                // Load each product with fidelity validation
                for (const product of products) {
                    await this.loadVerifiedModel(product);
                }
            } catch (error) {
                console.error('[SkyyRose3D] Failed to load collection products:', error);
                // Show placeholder content on failure
                this.showPlaceholderContent();
            }
        }

        /**
         * Load a model only if it passes fidelity validation
         * @param {object} product - Product data with modelUrl
         */
        async loadVerifiedModel(product) {
            if (!product.modelUrl) {
                console.warn(`[SkyyRose3D] Product ${product.id} has no model URL`);
                return;
            }

            // Validate fidelity first
            const validation = await this.validator.validate(product.modelUrl);

            if (!validation.passed) {
                console.warn(
                    `[SkyyRose3D] Model ${product.id} failed fidelity check: ` +
                    `${validation.score.toFixed(1)}% < ${MINIMUM_FIDELITY_SCORE}% required`
                );
                // Create placeholder instead
                this.createPlaceholder(product);
                return;
            }

            console.log(
                `[SkyyRose3D] Model ${product.id} passed fidelity: ${validation.score.toFixed(1)}%`
            );

            // Load verified model
            try {
                await this.loadGLTFModel(product);
            } catch (error) {
                console.error(`[SkyyRose3D] Failed to load model ${product.id}:`, error);
                this.createPlaceholder(product);
            }
        }

        /**
         * Load a GLTF/GLB model
         * @param {object} product - Product data
         */
        async loadGLTFModel(product) {
            return new Promise((resolve, reject) => {
                if (!THREE.GLTFLoader) {
                    reject(new Error('GLTFLoader not available'));
                    return;
                }

                const loader = new THREE.GLTFLoader();

                // Add Draco decoder if available
                if (THREE.DRACOLoader) {
                    const dracoLoader = new THREE.DRACOLoader();
                    dracoLoader.setDecoderPath('https://www.gstatic.com/draco/v1/decoders/');
                    loader.setDRACOLoader(dracoLoader);
                }

                loader.load(
                    product.modelUrl,
                    (gltf) => {
                        const model = gltf.scene;

                        // Apply position
                        if (product.position) {
                            const pos = Array.isArray(product.position)
                                ? product.position
                                : [product.position.x, product.position.y, product.position.z];
                            model.position.set(pos[0], pos[1], pos[2]);
                        }

                        // Enable shadows
                        model.traverse((child) => {
                            if (child.isMesh) {
                                child.castShadow = true;
                                child.receiveShadow = true;
                            }
                        });

                        // Store reference
                        model.userData = { productId: product.id, name: product.name };
                        this.models.set(product.id, model);
                        this.scene.add(model);

                        resolve(model);
                    },
                    (progress) => {
                        // Progress callback
                        const percent = (progress.loaded / progress.total * 100).toFixed(0);
                        console.log(`[SkyyRose3D] Loading ${product.name}: ${percent}%`);
                    },
                    (error) => {
                        reject(error);
                    }
                );
            });
        }

        /**
         * Create placeholder for failed/unverified models
         * @param {object} product - Product data
         */
        createPlaceholder(product) {
            // Create elegant placeholder geometry
            const geometry = new THREE.CylinderGeometry(0.5, 0.5, 1.5, 32);
            const material = new THREE.MeshStandardMaterial({
                color: SKYYROSE_BRAND_COLOR,
                roughness: 0.3,
                metalness: 0.8,
                transparent: true,
                opacity: 0.7
            });

            const mesh = new THREE.Mesh(geometry, material);

            if (product.position) {
                const pos = Array.isArray(product.position)
                    ? product.position
                    : [product.position.x, product.position.y, product.position.z];
                mesh.position.set(pos[0], pos[1] + 0.75, pos[2]);
            } else {
                mesh.position.set(0, 0.75, 0);
            }

            mesh.castShadow = true;
            mesh.userData = {
                productId: product.id,
                name: product.name,
                isPlaceholder: true
            };

            this.models.set(product.id, mesh);
            this.scene.add(mesh);
        }

        /**
         * Show placeholder content when API fails
         */
        showPlaceholderContent() {
            const collection = COLLECTIONS[this.config.collection];
            if (!collection) return;

            // Create demo products based on collection
            const demoProducts = [
                { id: 'demo-1', name: 'Item 1', position: [-3, 0, 0] },
                { id: 'demo-2', name: 'Item 2', position: [0, 0, 0] },
                { id: 'demo-3', name: 'Item 3', position: [3, 0, 0] }
            ];

            demoProducts.forEach(product => this.createPlaceholder(product));
        }

        /**
         * Handle window resize
         */
        handleResize() {
            const width = this.container.clientWidth;
            const height = this.container.clientHeight;

            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        }

        /**
         * Start animation loop
         */
        start() {
            if (this.isRunning) return;
            this.isRunning = true;

            const animate = () => {
                if (!this.isRunning) return;
                this.animationId = requestAnimationFrame(animate);

                // Update controls
                if (this.controls) {
                    this.controls.update();
                }

                // Animate particles
                if (this.particles) {
                    this.particles.rotation.y += 0.0002;
                }

                // Render
                this.renderer.render(this.scene, this.camera);
            };

            animate();
        }

        /**
         * Stop animation loop
         */
        stop() {
            this.isRunning = false;
            if (this.animationId) {
                cancelAnimationFrame(this.animationId);
                this.animationId = null;
            }
        }

        /**
         * Hide loading indicator
         */
        hideLoader() {
            const loader = this.container.querySelector('.skyyrose-3d-loader');
            if (loader) {
                loader.classList.add('hidden');
                setTimeout(() => loader.remove(), 500);
            }
        }

        /**
         * Show error message
         * @param {string} message - Error message
         */
        showError(message) {
            const loader = this.container.querySelector('.skyyrose-3d-loader');
            if (loader) {
                loader.innerHTML = `
                    <div class="skyyrose-3d-error">
                        <h3>Unable to load 3D experience</h3>
                        <p>${message}</p>
                        <button onclick="location.reload()">Retry</button>
                    </div>
                `;
            }
        }

        /**
         * Dispose of all resources
         */
        dispose() {
            this.stop();

            // Dispose models
            this.models.forEach((model) => {
                model.traverse((child) => {
                    if (child.isMesh) {
                        child.geometry?.dispose();
                        if (Array.isArray(child.material)) {
                            child.material.forEach(m => m.dispose());
                        } else {
                            child.material?.dispose();
                        }
                    }
                });
                this.scene.remove(model);
            });
            this.models.clear();

            // Dispose particles
            if (this.particles) {
                this.particles.geometry.dispose();
                this.particles.material.dispose();
            }

            // Dispose controls and renderer
            if (this.controls) this.controls.dispose();
            this.renderer.dispose();
            this.renderer.forceContextLoss();

            // Remove canvas
            if (this.renderer.domElement.parentNode) {
                this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
            }
        }
    }

    // ============================================================================
    // Public API
    // ============================================================================

    /**
     * Initialize a 3D experience in a container
     * @param {string|HTMLElement} selector - CSS selector or element
     * @returns {Experience3DManager|null}
     */
    SkyyRose3D.init = function(selector) {
        const container = typeof selector === 'string'
            ? document.querySelector(selector)
            : selector;

        if (!container) {
            console.error('[SkyyRose3D] Container not found:', selector);
            return null;
        }

        // Parse config from data attribute
        const configStr = container.getAttribute('data-skyyrose-3d');
        let config = {};

        try {
            config = configStr ? JSON.parse(configStr) : {};
        } catch (e) {
            console.error('[SkyyRose3D] Invalid config:', e);
        }

        // Create and return experience
        return new Experience3DManager(container, config);
    };

    /**
     * Initialize all 3D containers on the page
     */
    SkyyRose3D.initAll = function() {
        const containers = document.querySelectorAll('[data-skyyrose-3d]');
        const experiences = [];

        containers.forEach((container) => {
            const experience = SkyyRose3D.init(container);
            if (experience) {
                experiences.push(experience);
            }
        });

        return experiences;
    };

    /**
     * Get minimum fidelity score required
     */
    SkyyRose3D.getMinimumFidelity = function() {
        return MINIMUM_FIDELITY_SCORE;
    };

    /**
     * Get available collections
     */
    SkyyRose3D.getCollections = function() {
        return { ...COLLECTIONS };
    };

    // ============================================================================
    // Auto-initialize on DOM ready
    // ============================================================================

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', SkyyRose3D.initAll);
    } else {
        SkyyRose3D.initAll();
    }

})();
