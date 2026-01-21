/**
 * SkyyRose Pre-Order Experience Scene
 *
 * Full immersive pre-order experience with scroll-based collection transitions,
 * AJAX cart integration, and WooCommerce product display.
 *
 * @package SkyyRose_Immersive
 * @since 1.0.0
 */

import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

/**
 * Pre-Order Scene Class
 *
 * Manages the full-page immersive shopping experience
 */
export class PreOrderScene {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.options = {
            particleCount: options.particleCount || 3000,
            enableBloom: options.enableBloom !== false,
            bloomStrength: options.bloomStrength || 1.2,
            isMobile: options.isMobile || false,
            ajaxUrl: options.ajaxUrl || '/wp-admin/admin-ajax.php',
            nonce: options.nonce || '',
            ...options
        };

        if (this.options.isMobile) {
            this.options.particleCount = Math.floor(this.options.particleCount * 0.3);
        }

        // Three.js components
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.composer = null;
        this.clock = new THREE.Clock();

        // Scene elements
        this.morphingCore = null;
        this.particles = null;
        this.collectionElements = {
            blackRose: [],
            loveHurts: [],
            signature: []
        };

        // State
        this.isAnimating = false;
        this.scrollProgress = 0;
        this.targetScrollProgress = 0;
        this.currentCollection = 'hero';
        this.cart = [];

        // Collection themes
        this.themes = {
            hero: {
                primary: new THREE.Color(0xD4AF37),
                secondary: new THREE.Color(0xE91E63),
                tertiary: new THREE.Color(0xDC143C)
            },
            blackRose: {
                primary: new THREE.Color(0xDC143C),
                secondary: new THREE.Color(0xC0C0C0),
                tertiary: new THREE.Color(0x8B0000)
            },
            loveHurts: {
                primary: new THREE.Color(0xE91E63),
                secondary: new THREE.Color(0xF8BBD9),
                tertiary: new THREE.Color(0x880E4F)
            },
            signature: {
                primary: new THREE.Color(0xD4AF37),
                secondary: new THREE.Color(0xB76E79),
                tertiary: new THREE.Color(0xE5E4E2)
            }
        };

        this.init();
    }

    init() {
        this.createScene();
        this.createCamera();
        this.createRenderer();
        this.createMorphingCore();
        this.createParticleSystem();
        this.createCollectionElements();

        if (this.options.enableBloom) {
            this.setupPostProcessing();
        }

        this.bindEvents();
        this.initCartFromStorage();
    }

    createScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000000);
        this.scene.fog = new THREE.Fog(0x000000, 50, 150);
    }

    createCamera() {
        this.camera = new THREE.PerspectiveCamera(
            60,
            this.canvas.clientWidth / this.canvas.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 0, 30);
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
        this.renderer.toneMappingExposure = 1.2;
    }

    createMorphingCore() {
        const geometry = new THREE.IcosahedronGeometry(4, 3);

        const material = new THREE.MeshBasicMaterial({
            color: this.themes.hero.primary,
            wireframe: true,
            transparent: true,
            opacity: 0.6
        });

        this.morphingCore = new THREE.Mesh(geometry, material);
        this.scene.add(this.morphingCore);

        // Inner glow sphere
        const glowGeometry = new THREE.SphereGeometry(3.5, 32, 32);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: this.themes.hero.secondary,
            transparent: true,
            opacity: 0.2
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        this.morphingCore.add(glow);
    }

    createParticleSystem() {
        const positions = new Float32Array(this.options.particleCount * 3);
        const colors = new Float32Array(this.options.particleCount * 3);
        const velocities = new Float32Array(this.options.particleCount * 3);

        const colorOptions = [
            new THREE.Color(0xD4AF37),
            new THREE.Color(0xE91E63),
            new THREE.Color(0xDC143C),
            new THREE.Color(0xC0C0C0)
        ];

        for (let i = 0; i < this.options.particleCount; i++) {
            const radius = 10 + Math.random() * 40;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);

            positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i * 3 + 2] = radius * Math.cos(phi);

            velocities[i * 3] = (Math.random() - 0.5) * 0.015;
            velocities[i * 3 + 1] = (Math.random() - 0.5) * 0.015;
            velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.015;

            const color = colorOptions[Math.floor(Math.random() * colorOptions.length)];
            colors[i * 3] = color.r;
            colors[i * 3 + 1] = color.g;
            colors[i * 3 + 2] = color.b;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.userData.velocities = velocities;
        geometry.userData.originalColors = colors.slice();

        const material = new THREE.PointsMaterial({
            size: 0.08,
            vertexColors: true,
            transparent: true,
            opacity: 0.7,
            blending: THREE.AdditiveBlending,
            sizeAttenuation: true
        });

        this.particles = new THREE.Points(geometry, material);
        this.scene.add(this.particles);
    }

    createCollectionElements() {
        // BLACK ROSE - Rose petals and thorns
        this.createBlackRoseElements();

        // LOVE HURTS - Hearts and tears
        this.createLoveHurtsElements();

        // SIGNATURE - Diamonds and gold rings
        this.createSignatureElements();
    }

    createBlackRoseElements() {
        // Rose petal shapes
        for (let i = 0; i < 15; i++) {
            const petalGroup = new THREE.Group();

            for (let j = 0; j < 4; j++) {
                const petalGeo = new THREE.TorusGeometry(0.4 + j * 0.1, 0.08, 8, 16, Math.PI * 1.6);
                const petalMat = new THREE.MeshBasicMaterial({
                    color: 0xDC143C,
                    transparent: true,
                    opacity: 0
                });
                const petal = new THREE.Mesh(petalGeo, petalMat);
                petal.rotation.x = j * 0.3;
                petal.rotation.z = j * Math.PI / 4;
                petalGroup.add(petal);
            }

            petalGroup.position.set(
                (Math.random() - 0.5) * 50,
                (Math.random() - 0.5) * 50,
                (Math.random() - 0.5) * 30 - 20
            );
            petalGroup.scale.setScalar(Math.random() * 1.5 + 0.5);
            petalGroup.userData.floatOffset = Math.random() * Math.PI * 2;
            petalGroup.userData.baseY = petalGroup.position.y;

            this.collectionElements.blackRose.push(petalGroup);
            this.scene.add(petalGroup);
        }
    }

    createLoveHurtsElements() {
        // Heart shapes
        for (let i = 0; i < 12; i++) {
            const heartShape = new THREE.Shape();
            const x = 0, y = 0;
            heartShape.moveTo(x + 0.25, y + 0.25);
            heartShape.bezierCurveTo(x + 0.25, y + 0.25, x + 0.2, y, x, y);
            heartShape.bezierCurveTo(x - 0.35, y, x - 0.35, y + 0.35, x - 0.35, y + 0.35);
            heartShape.bezierCurveTo(x - 0.35, y + 0.55, x - 0.2, y + 0.77, x + 0.25, y + 0.95);
            heartShape.bezierCurveTo(x + 0.7, y + 0.77, x + 0.85, y + 0.55, x + 0.85, y + 0.35);
            heartShape.bezierCurveTo(x + 0.85, y + 0.35, x + 0.85, y, x + 0.5, y);
            heartShape.bezierCurveTo(x + 0.35, y, x + 0.25, y + 0.25, x + 0.25, y + 0.25);

            const geometry = new THREE.ShapeGeometry(heartShape);
            const material = new THREE.MeshBasicMaterial({
                color: 0xE91E63,
                transparent: true,
                opacity: 0,
                side: THREE.DoubleSide
            });

            const heart = new THREE.Mesh(geometry, material);
            heart.position.set(
                (Math.random() - 0.5) * 50,
                (Math.random() - 0.5) * 50,
                (Math.random() - 0.5) * 30 - 20
            );
            heart.rotation.z = Math.PI;
            heart.scale.setScalar(Math.random() * 2 + 1);
            heart.userData.floatOffset = Math.random() * Math.PI * 2;
            heart.userData.baseY = heart.position.y;

            this.collectionElements.loveHurts.push(heart);
            this.scene.add(heart);
        }
    }

    createSignatureElements() {
        // Diamond shapes
        for (let i = 0; i < 10; i++) {
            const geometry = new THREE.OctahedronGeometry(0.6 + Math.random() * 0.4);
            const material = new THREE.MeshBasicMaterial({
                color: 0xD4AF37,
                transparent: true,
                opacity: 0,
                wireframe: true
            });

            const diamond = new THREE.Mesh(geometry, material);
            diamond.position.set(
                (Math.random() - 0.5) * 50,
                (Math.random() - 0.5) * 50,
                (Math.random() - 0.5) * 30 - 20
            );
            diamond.userData.rotSpeed = (Math.random() - 0.5) * 0.02;
            diamond.userData.floatOffset = Math.random() * Math.PI * 2;
            diamond.userData.baseY = diamond.position.y;

            this.collectionElements.signature.push(diamond);
            this.scene.add(diamond);
        }

        // Gold rings
        for (let i = 0; i < 5; i++) {
            const geometry = new THREE.TorusGeometry(1 + Math.random(), 0.05, 16, 50);
            const material = new THREE.MeshBasicMaterial({
                color: 0xB76E79,
                transparent: true,
                opacity: 0
            });

            const ring = new THREE.Mesh(geometry, material);
            ring.position.set(
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 20 - 15
            );
            ring.rotation.x = Math.random() * Math.PI;
            ring.rotation.y = Math.random() * Math.PI;
            ring.userData.rotSpeed = {
                x: (Math.random() - 0.5) * 0.01,
                y: (Math.random() - 0.5) * 0.01
            };

            this.collectionElements.signature.push(ring);
            this.scene.add(ring);
        }
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
        window.addEventListener('scroll', this.onScroll.bind(this));

        // Cart button events
        document.addEventListener('click', (e) => {
            if (e.target.matches('.preorder-btn, .preorder-btn *')) {
                const btn = e.target.closest('.preorder-btn');
                if (btn) {
                    const productId = btn.dataset.productId;
                    const productName = btn.dataset.productName;
                    const productPrice = parseFloat(btn.dataset.productPrice);
                    const productEmoji = btn.dataset.productEmoji || '🛍️';
                    const collection = btn.dataset.collection;
                    this.addToCart(productId, productName, productPrice, productEmoji, collection);
                }
            }
        });
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

    onScroll() {
        const scrollHeight = document.body.scrollHeight - window.innerHeight;
        this.targetScrollProgress = scrollHeight > 0 ? window.scrollY / scrollHeight : 0;
    }

    updateCollectionVisibility(progress) {
        // Determine current collection based on scroll
        let newCollection = 'hero';
        if (progress >= 0.75) {
            newCollection = 'signature';
        } else if (progress >= 0.5) {
            newCollection = 'loveHurts';
        } else if (progress >= 0.25) {
            newCollection = 'blackRose';
        }

        // Update collection element visibility with smooth transitions
        const blackRoseOpacity = this.calculateOpacity(progress, 0.15, 0.35, 0.45);
        const loveHurtsOpacity = this.calculateOpacity(progress, 0.4, 0.6, 0.7);
        const signatureOpacity = this.calculateOpacity(progress, 0.65, 0.85, 1.0);

        this.collectionElements.blackRose.forEach(el => {
            el.traverse(child => {
                if (child.material) {
                    child.material.opacity = blackRoseOpacity * 0.4;
                }
            });
        });

        this.collectionElements.loveHurts.forEach(el => {
            if (el.material) {
                el.material.opacity = loveHurtsOpacity * 0.35;
            }
        });

        this.collectionElements.signature.forEach(el => {
            if (el.material) {
                el.material.opacity = signatureOpacity * 0.3;
            }
        });

        // Update core colors
        if (this.morphingCore) {
            const theme = this.getCurrentTheme(progress);
            this.morphingCore.material.color.copy(theme.primary);
            this.morphingCore.children[0].material.color.copy(theme.secondary);
        }

        this.currentCollection = newCollection;
    }

    calculateOpacity(progress, fadeIn, peak, fadeOut) {
        if (progress < fadeIn) return 0;
        if (progress < peak) return (progress - fadeIn) / (peak - fadeIn);
        if (progress < fadeOut) return 1;
        return Math.max(0, 1 - (progress - fadeOut) / 0.15);
    }

    getCurrentTheme(progress) {
        if (progress < 0.25) {
            return this.lerpTheme(this.themes.hero, this.themes.blackRose, progress * 4);
        } else if (progress < 0.5) {
            return this.lerpTheme(this.themes.blackRose, this.themes.loveHurts, (progress - 0.25) * 4);
        } else if (progress < 0.75) {
            return this.lerpTheme(this.themes.loveHurts, this.themes.signature, (progress - 0.5) * 4);
        }
        return this.themes.signature;
    }

    lerpTheme(theme1, theme2, t) {
        return {
            primary: theme1.primary.clone().lerp(theme2.primary, t),
            secondary: theme1.secondary.clone().lerp(theme2.secondary, t),
            tertiary: theme1.tertiary.clone().lerp(theme2.tertiary, t)
        };
    }

    animate() {
        if (!this.isAnimating) return;

        requestAnimationFrame(this.animate.bind(this));

        const time = this.clock.getElapsedTime();

        // Smooth scroll interpolation
        this.scrollProgress += (this.targetScrollProgress - this.scrollProgress) * 0.08;

        // Update morphing core
        if (this.morphingCore) {
            this.morphingCore.rotation.y = time * 0.15;
            this.morphingCore.rotation.x = Math.sin(time * 0.2) * 0.15;

            const scale = 1 + Math.sin(time * 0.5) * 0.1;
            this.morphingCore.scale.setScalar(scale);
        }

        // Update particles
        if (this.particles) {
            this.particles.rotation.y += 0.0003;

            const positions = this.particles.geometry.attributes.position.array;
            const velocities = this.particles.geometry.userData.velocities;

            for (let i = 0; i < positions.length; i += 3) {
                positions[i] += velocities[i];
                positions[i + 1] += velocities[i + 1];
                positions[i + 2] += velocities[i + 2];

                const dist = Math.sqrt(
                    positions[i] ** 2 +
                    positions[i + 1] ** 2 +
                    positions[i + 2] ** 2
                );
                if (dist > 55) {
                    const scale = 10 / dist;
                    positions[i] *= scale;
                    positions[i + 1] *= scale;
                    positions[i + 2] *= scale;
                }
            }
            this.particles.geometry.attributes.position.needsUpdate = true;
        }

        // Animate collection elements
        this.animateCollectionElements(time);

        // Update visibility based on scroll
        this.updateCollectionVisibility(this.scrollProgress);

        // Camera movement
        this.camera.position.z = 30 - this.scrollProgress * 5;
        this.camera.position.y = this.scrollProgress * 3;

        // Render
        if (this.composer) {
            this.composer.render();
        } else {
            this.renderer.render(this.scene, this.camera);
        }
    }

    animateCollectionElements(time) {
        // Black Rose elements
        this.collectionElements.blackRose.forEach(el => {
            if (el.userData.baseY !== undefined) {
                el.position.y = el.userData.baseY + Math.sin(time * 0.4 + el.userData.floatOffset) * 1.5;
            }
            el.rotation.z += 0.003;
        });

        // Love Hurts elements
        this.collectionElements.loveHurts.forEach(el => {
            if (el.userData.baseY !== undefined) {
                el.position.y = el.userData.baseY + Math.sin(time * 0.5 + el.userData.floatOffset) * 2;
            }
        });

        // Signature elements
        this.collectionElements.signature.forEach(el => {
            if (el.userData.baseY !== undefined) {
                el.position.y = el.userData.baseY + Math.sin(time * 0.3 + el.userData.floatOffset) * 1.5;
            }
            if (el.userData.rotSpeed) {
                if (typeof el.userData.rotSpeed === 'object') {
                    el.rotation.x += el.userData.rotSpeed.x;
                    el.rotation.y += el.userData.rotSpeed.y;
                } else {
                    el.rotation.y += el.userData.rotSpeed;
                }
            }
        });
    }

    // =====================
    // Cart Functionality
    // =====================

    initCartFromStorage() {
        try {
            const stored = localStorage.getItem('skyyrose_cart');
            if (stored) {
                this.cart = JSON.parse(stored);
                this.updateCartUI();
            }
        } catch (e) {
            console.warn('Could not load cart from storage:', e);
        }
    }

    saveCartToStorage() {
        try {
            localStorage.setItem('skyyrose_cart', JSON.stringify(this.cart));
        } catch (e) {
            console.warn('Could not save cart to storage:', e);
        }
    }

    addToCart(productId, name, price, emoji, collection) {
        const item = {
            id: productId || `temp-${Date.now()}`,
            name,
            price,
            emoji,
            collection
        };

        this.cart.push(item);
        this.saveCartToStorage();
        this.updateCartUI();

        // Visual feedback
        this.showAddedFeedback(name, collection);

        // If WooCommerce AJAX is available, sync with WC cart
        if (productId && this.options.ajaxUrl) {
            this.syncWithWooCommerce(productId);
        }
    }

    removeFromCart(index) {
        if (index >= 0 && index < this.cart.length) {
            this.cart.splice(index, 1);
            this.saveCartToStorage();
            this.updateCartUI();
        }
    }

    updateCartUI() {
        const countEl = document.getElementById('cart-count');
        const itemsEl = document.getElementById('cart-items');
        const totalEl = document.getElementById('cart-total');

        if (countEl) {
            countEl.textContent = this.cart.length;
        }

        if (itemsEl) {
            if (this.cart.length === 0) {
                itemsEl.innerHTML = '<div class="cart-empty">Your bag is empty</div>';
            } else {
                itemsEl.innerHTML = this.cart.map((item, index) => `
                    <div class="cart-item">
                        <div class="cart-item-image">${item.emoji}</div>
                        <div class="cart-item-details">
                            <div class="cart-item-name">${item.name}</div>
                            <div class="cart-item-price">$${item.price}</div>
                        </div>
                        <button class="cart-item-remove" onclick="window.skyyRosePreorder.removeFromCart(${index})">×</button>
                    </div>
                `).join('');
            }
        }

        if (totalEl) {
            const total = this.cart.reduce((sum, item) => sum + item.price, 0);
            totalEl.textContent = `$${total}`;
        }

        // Dispatch event for external listeners
        document.dispatchEvent(new CustomEvent('skyyrose:cart:updated', {
            detail: { cart: this.cart }
        }));
    }

    showAddedFeedback(name, collection) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'skyyrose-toast';
        toast.innerHTML = `
            <span class="toast-icon">✓</span>
            <span class="toast-text">${name} added to bag</span>
        `;

        // Style based on collection
        const collectionColors = {
            'BLACK ROSE': '#DC143C',
            'LOVE HURTS': '#E91E63',
            'SIGNATURE': '#D4AF37'
        };
        toast.style.borderColor = collectionColors[collection] || '#D4AF37';

        document.body.appendChild(toast);

        // Animate in
        setTimeout(() => toast.classList.add('visible'), 10);

        // Remove after delay
        setTimeout(() => {
            toast.classList.remove('visible');
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    async syncWithWooCommerce(productId) {
        if (!this.options.ajaxUrl || !this.options.nonce) return;

        try {
            const formData = new FormData();
            formData.append('action', 'skyyrose_add_to_cart');
            formData.append('product_id', productId);
            formData.append('nonce', this.options.nonce);

            await fetch(this.options.ajaxUrl, {
                method: 'POST',
                body: formData
            });
        } catch (e) {
            console.warn('Could not sync with WooCommerce:', e);
        }
    }

    getCart() {
        return [...this.cart];
    }

    clearCart() {
        this.cart = [];
        this.saveCartToStorage();
        this.updateCartUI();
    }

    // =====================
    // Lifecycle
    // =====================

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

        window.removeEventListener('resize', this.onResize.bind(this));
        window.removeEventListener('scroll', this.onScroll.bind(this));
    }
}

/**
 * Initialize pre-order scene
 *
 * @param {HTMLCanvasElement} canvas
 * @param {Object} options
 * @returns {PreOrderScene}
 */
export function initPreOrderScene(canvas, options = {}) {
    const scene = new PreOrderScene(canvas, options);
    scene.start();

    // Expose for global access
    window.skyyRosePreorder = scene;

    return scene;
}

// Global exports
if (typeof window !== 'undefined') {
    window.SkyyRosePreOrderScene = PreOrderScene;
    window.initPreOrderScene = initPreOrderScene;
}
