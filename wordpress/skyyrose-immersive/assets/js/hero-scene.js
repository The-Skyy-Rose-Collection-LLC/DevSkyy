/**
 * SkyyRose Hero Scene
 *
 * Creates an immersive 3D hero experience with morphing geometry,
 * particle fields, and collection-themed color transitions.
 *
 * @package SkyyRose_Immersive
 * @since 1.0.0
 */

import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

/**
 * Color themes for each collection
 */
const THEMES = {
    hero: {
        primary: new THREE.Color(0xD4AF37),
        secondary: new THREE.Color(0xE91E63),
        tertiary: new THREE.Color(0xDC143C),
        bg: new THREE.Color(0x000000)
    },
    blackRose: {
        primary: new THREE.Color(0xDC143C),
        secondary: new THREE.Color(0xC0C0C0),
        tertiary: new THREE.Color(0x8B0000),
        bg: new THREE.Color(0x0A0505)
    },
    loveHurts: {
        primary: new THREE.Color(0xE91E63),
        secondary: new THREE.Color(0xF8BBD9),
        tertiary: new THREE.Color(0x880E4F),
        bg: new THREE.Color(0x0D0408)
    },
    signature: {
        primary: new THREE.Color(0xD4AF37),
        secondary: new THREE.Color(0xB76E79),
        tertiary: new THREE.Color(0xE5E4E2),
        bg: new THREE.Color(0x0A0A0A)
    }
};

/**
 * Simplex noise vertex shader code
 */
const NOISE_SHADER = `
    vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
    vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

    float snoise(vec3 v) {
        const vec2 C = vec2(1.0/6.0, 1.0/3.0);
        const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
        vec3 i = floor(v + dot(v, C.yyy));
        vec3 x0 = v - i + dot(i, C.xxx);
        vec3 g = step(x0.yzx, x0.xyz);
        vec3 l = 1.0 - g;
        vec3 i1 = min(g.xyz, l.zxy);
        vec3 i2 = max(g.xyz, l.zxy);
        vec3 x1 = x0 - i1 + C.xxx;
        vec3 x2 = x0 - i2 + C.yyy;
        vec3 x3 = x0 - D.yyy;
        i = mod289(i);
        vec4 p = permute(permute(permute(
            i.z + vec4(0.0, i1.z, i2.z, 1.0))
            + i.y + vec4(0.0, i1.y, i2.y, 1.0))
            + i.x + vec4(0.0, i1.x, i2.x, 1.0));
        float n_ = 0.142857142857;
        vec3 ns = n_ * D.wyz - D.xzx;
        vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
        vec4 x_ = floor(j * ns.z);
        vec4 y_ = floor(j - 7.0 * x_);
        vec4 x = x_ * ns.x + ns.yyyy;
        vec4 y = y_ * ns.x + ns.yyyy;
        vec4 h = 1.0 - abs(x) - abs(y);
        vec4 b0 = vec4(x.xy, y.xy);
        vec4 b1 = vec4(x.zw, y.zw);
        vec4 s0 = floor(b0) * 2.0 + 1.0;
        vec4 s1 = floor(b1) * 2.0 + 1.0;
        vec4 sh = -step(h, vec4(0.0));
        vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
        vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
        vec3 p0 = vec3(a0.xy, h.x);
        vec3 p1 = vec3(a0.zw, h.y);
        vec3 p2 = vec3(a1.xy, h.z);
        vec3 p3 = vec3(a1.zw, h.w);
        vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
        p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
        vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
        m = m * m;
        return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
    }
`;

/**
 * Hero Scene Class
 */
export class HeroScene {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.options = {
            particleCount: options.particleCount || 5000,
            enableBloom: options.enableBloom !== false,
            bloomStrength: options.bloomStrength || 1.5,
            bloomRadius: options.bloomRadius || 0.4,
            bloomThreshold: options.bloomThreshold || 0.85,
            isMobile: options.isMobile || false,
            ...options
        };

        // Reduce particles on mobile
        if (this.options.isMobile) {
            this.options.particleCount = Math.floor(this.options.particleCount * 0.3);
        }

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.composer = null;
        this.morphingGeometry = null;
        this.particles = null;
        this.rings = [];
        this.floatingShapes = [];
        this.clock = new THREE.Clock();
        this.scrollY = 0;
        this.targetScrollY = 0;
        this.isAnimating = false;

        this.init();
    }

    init() {
        this.createScene();
        this.createCamera();
        this.createRenderer();
        this.createMorphingCore();
        this.createParticleField();
        this.createOrbitingRings();
        this.createFloatingLogos();

        if (this.options.enableBloom) {
            this.setupPostProcessing();
        }

        this.bindEvents();
    }

    createScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000000);
    }

    createCamera() {
        this.camera = new THREE.PerspectiveCamera(
            60,
            this.canvas.clientWidth / this.canvas.clientHeight,
            0.1,
            1000
        );
        this.camera.position.z = 30;
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
        const geometry = new THREE.IcosahedronGeometry(5, 4);

        const material = new THREE.ShaderMaterial({
            uniforms: {
                uTime: { value: 0 },
                uColor1: { value: THEMES.hero.primary.clone() },
                uColor2: { value: THEMES.hero.secondary.clone() },
                uColor3: { value: THEMES.hero.tertiary.clone() },
                uMorphProgress: { value: 0 }
            },
            vertexShader: `
                uniform float uTime;
                uniform float uMorphProgress;
                varying vec3 vNormal;
                varying vec3 vPosition;
                varying float vDisplacement;

                ${NOISE_SHADER}

                void main() {
                    vNormal = normalize(normalMatrix * normal);

                    float noise1 = snoise(position * 0.3 + uTime * 0.2);
                    float noise2 = snoise(position * 0.6 + uTime * 0.3) * 0.5;
                    float noise3 = snoise(position * 1.2 + uTime * 0.1) * 0.25;

                    float displacement = (noise1 + noise2 + noise3) * (1.0 + uMorphProgress * 0.5);
                    vDisplacement = displacement;

                    vec3 newPosition = position + normal * displacement * 0.8;
                    vPosition = newPosition;

                    gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
                }
            `,
            fragmentShader: `
                uniform float uTime;
                uniform vec3 uColor1;
                uniform vec3 uColor2;
                uniform vec3 uColor3;
                varying vec3 vNormal;
                varying vec3 vPosition;
                varying float vDisplacement;

                void main() {
                    vec3 viewDirection = normalize(cameraPosition - vPosition);
                    float fresnel = pow(1.0 - dot(viewDirection, vNormal), 3.0);

                    float colorMix1 = sin(vDisplacement * 3.0 + uTime) * 0.5 + 0.5;
                    float colorMix2 = cos(vPosition.y * 0.5 + uTime * 0.5) * 0.5 + 0.5;

                    vec3 color = mix(uColor1, uColor2, colorMix1);
                    color = mix(color, uColor3, colorMix2 * 0.5);
                    color += fresnel * uColor1 * 0.5;

                    float emissive = smoothstep(0.3, 0.8, fresnel);

                    gl_FragColor = vec4(color, 0.9 + emissive * 0.1);
                }
            `,
            transparent: true,
            side: THREE.DoubleSide
        });

        this.morphingGeometry = new THREE.Mesh(geometry, material);
        this.scene.add(this.morphingGeometry);
    }

    createParticleField() {
        const positions = new Float32Array(this.options.particleCount * 3);
        const colors = new Float32Array(this.options.particleCount * 3);
        const sizes = new Float32Array(this.options.particleCount);
        const velocities = new Float32Array(this.options.particleCount * 3);

        const colorOptions = [
            new THREE.Color(0xD4AF37),
            new THREE.Color(0xE91E63),
            new THREE.Color(0xDC143C),
            new THREE.Color(0xC0C0C0),
            new THREE.Color(0xF8BBD9)
        ];

        for (let i = 0; i < this.options.particleCount; i++) {
            const radius = 15 + Math.random() * 35;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);

            positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i * 3 + 2] = radius * Math.cos(phi);

            velocities[i * 3] = (Math.random() - 0.5) * 0.02;
            velocities[i * 3 + 1] = (Math.random() - 0.5) * 0.02;
            velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.02;

            const color = colorOptions[Math.floor(Math.random() * colorOptions.length)];
            colors[i * 3] = color.r;
            colors[i * 3 + 1] = color.g;
            colors[i * 3 + 2] = color.b;

            sizes[i] = Math.random() * 0.15 + 0.05;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
        geometry.userData.velocities = velocities;

        const material = new THREE.PointsMaterial({
            size: 0.1,
            vertexColors: true,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending,
            sizeAttenuation: true
        });

        this.particles = new THREE.Points(geometry, material);
        this.scene.add(this.particles);
    }

    createOrbitingRings() {
        const ringCount = 5;
        const colors = [0xD4AF37, 0xE91E63, 0xDC143C, 0xB76E79, 0xC0C0C0];

        for (let i = 0; i < ringCount; i++) {
            const radius = 8 + i * 3;
            const geometry = new THREE.TorusGeometry(radius, 0.02 + i * 0.01, 16, 100);

            const material = new THREE.MeshBasicMaterial({
                color: colors[i],
                transparent: true,
                opacity: 0.4 - i * 0.05
            });

            const ring = new THREE.Mesh(geometry, material);
            ring.rotation.x = Math.random() * Math.PI;
            ring.rotation.y = Math.random() * Math.PI;
            ring.userData.rotationSpeed = {
                x: (Math.random() - 0.5) * 0.01,
                y: (Math.random() - 0.5) * 0.01,
                z: (Math.random() - 0.5) * 0.005
            };

            this.rings.push(ring);
            this.scene.add(ring);
        }
    }

    createFloatingLogos() {
        // Hearts for LOVE HURTS
        for (let i = 0; i < 8; i++) {
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
                opacity: 0.3,
                side: THREE.DoubleSide
            });

            const heart = new THREE.Mesh(geometry, material);
            heart.position.set(
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 20 - 10
            );
            heart.rotation.z = Math.PI;
            heart.scale.setScalar(Math.random() * 1 + 0.5);
            heart.userData.floatSpeed = Math.random() * 0.5 + 0.5;
            heart.userData.floatOffset = Math.random() * Math.PI * 2;
            heart.userData.baseY = heart.position.y;

            this.floatingShapes.push(heart);
            this.scene.add(heart);
        }

        // Roses for BLACK ROSE
        for (let i = 0; i < 6; i++) {
            const roseGroup = new THREE.Group();

            for (let j = 0; j < 5; j++) {
                const petalGeo = new THREE.TorusGeometry(0.3 + j * 0.1, 0.05, 8, 16, Math.PI * 1.5);
                const petalMat = new THREE.MeshBasicMaterial({
                    color: 0xDC143C,
                    transparent: true,
                    opacity: 0.3 - j * 0.04
                });
                const petal = new THREE.Mesh(petalGeo, petalMat);
                petal.rotation.x = j * 0.2;
                petal.rotation.z = j * Math.PI / 5;
                roseGroup.add(petal);
            }

            roseGroup.position.set(
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 20 - 10
            );
            roseGroup.scale.setScalar(Math.random() * 1.5 + 0.5);
            roseGroup.userData.floatSpeed = Math.random() * 0.3 + 0.3;
            roseGroup.userData.floatOffset = Math.random() * Math.PI * 2;
            roseGroup.userData.baseY = roseGroup.position.y;
            roseGroup.userData.rotSpeed = (Math.random() - 0.5) * 0.01;

            this.floatingShapes.push(roseGroup);
            this.scene.add(roseGroup);
        }

        // Diamonds for SIGNATURE
        for (let i = 0; i < 6; i++) {
            const geometry = new THREE.OctahedronGeometry(0.5 + Math.random() * 0.5);
            const material = new THREE.MeshBasicMaterial({
                color: 0xD4AF37,
                transparent: true,
                opacity: 0.25,
                wireframe: true
            });

            const diamond = new THREE.Mesh(geometry, material);
            diamond.position.set(
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 20 - 10
            );
            diamond.userData.floatSpeed = Math.random() * 0.4 + 0.2;
            diamond.userData.floatOffset = Math.random() * Math.PI * 2;
            diamond.userData.baseY = diamond.position.y;
            diamond.userData.rotSpeed = (Math.random() - 0.5) * 0.02;

            this.floatingShapes.push(diamond);
            this.scene.add(diamond);
        }
    }

    setupPostProcessing() {
        this.composer = new EffectComposer(this.renderer);

        const renderPass = new RenderPass(this.scene, this.camera);
        this.composer.addPass(renderPass);

        const bloomPass = new UnrealBloomPass(
            new THREE.Vector2(this.canvas.clientWidth, this.canvas.clientHeight),
            this.options.bloomStrength,
            this.options.bloomRadius,
            this.options.bloomThreshold
        );
        this.composer.addPass(bloomPass);

        // Chromatic aberration
        const chromaticAberrationShader = {
            uniforms: {
                tDiffuse: { value: null },
                uIntensity: { value: 0.002 },
                uTime: { value: 0 }
            },
            vertexShader: `
                varying vec2 vUv;
                void main() {
                    vUv = uv;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform sampler2D tDiffuse;
                uniform float uIntensity;
                uniform float uTime;
                varying vec2 vUv;

                void main() {
                    vec2 center = vec2(0.5);
                    vec2 dir = vUv - center;
                    float dist = length(dir);

                    float intensity = uIntensity * (1.0 + sin(uTime * 0.5) * 0.2);

                    vec2 redOffset = dir * dist * intensity;
                    vec2 blueOffset = -dir * dist * intensity;

                    float r = texture2D(tDiffuse, vUv + redOffset).r;
                    float g = texture2D(tDiffuse, vUv).g;
                    float b = texture2D(tDiffuse, vUv + blueOffset).b;

                    gl_FragColor = vec4(r, g, b, 1.0);
                }
            `
        };

        this.chromaticPass = new ShaderPass(chromaticAberrationShader);
        this.composer.addPass(this.chromaticPass);

        const outputPass = new OutputPass();
        this.composer.addPass(outputPass);
    }

    bindEvents() {
        window.addEventListener('resize', this.onResize.bind(this));
        window.addEventListener('scroll', this.onScroll.bind(this));
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
        this.targetScrollY = window.scrollY;
    }

    updateThemeColors(progress) {
        let theme;

        if (progress < 0.25) {
            theme = this.lerpTheme(THEMES.hero, THEMES.blackRose, progress * 4);
        } else if (progress < 0.5) {
            theme = this.lerpTheme(THEMES.blackRose, THEMES.loveHurts, (progress - 0.25) * 4);
        } else if (progress < 0.75) {
            theme = this.lerpTheme(THEMES.loveHurts, THEMES.signature, (progress - 0.5) * 4);
        } else {
            theme = THEMES.signature;
        }

        if (this.morphingGeometry) {
            this.morphingGeometry.material.uniforms.uColor1.value.copy(theme.primary);
            this.morphingGeometry.material.uniforms.uColor2.value.copy(theme.secondary);
            this.morphingGeometry.material.uniforms.uColor3.value.copy(theme.tertiary);
        }
    }

    lerpTheme(theme1, theme2, t) {
        return {
            primary: theme1.primary.clone().lerp(theme2.primary, t),
            secondary: theme1.secondary.clone().lerp(theme2.secondary, t),
            tertiary: theme1.tertiary.clone().lerp(theme2.tertiary, t),
            bg: theme1.bg.clone().lerp(theme2.bg, t)
        };
    }

    animate() {
        if (!this.isAnimating) return;

        requestAnimationFrame(this.animate.bind(this));

        const time = this.clock.getElapsedTime();

        // Smooth scroll interpolation
        this.scrollY += (this.targetScrollY - this.scrollY) * 0.1;

        // Update morphing geometry
        if (this.morphingGeometry) {
            this.morphingGeometry.material.uniforms.uTime.value = time;
            this.morphingGeometry.rotation.y = time * 0.1;
            this.morphingGeometry.rotation.x = Math.sin(time * 0.2) * 0.2;

            const scrollProgress = this.scrollY / (document.body.scrollHeight - window.innerHeight);
            this.updateThemeColors(scrollProgress);
        }

        // Animate particles
        if (this.particles) {
            this.particles.rotation.y += 0.0005;
            this.particles.rotation.x += 0.0002;

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
                if (dist > 50) {
                    const scale = 15 / dist;
                    positions[i] *= scale;
                    positions[i + 1] *= scale;
                    positions[i + 2] *= scale;
                }
            }
            this.particles.geometry.attributes.position.needsUpdate = true;
        }

        // Animate rings
        this.rings.forEach(ring => {
            ring.rotation.x += ring.userData.rotationSpeed.x;
            ring.rotation.y += ring.userData.rotationSpeed.y;
            ring.rotation.z += ring.userData.rotationSpeed.z;
        });

        // Animate floating shapes
        this.floatingShapes.forEach(shape => {
            if (shape.userData.baseY !== undefined) {
                shape.position.y = shape.userData.baseY +
                    Math.sin(time * shape.userData.floatSpeed + shape.userData.floatOffset) * 2;
            }
            if (shape.userData.rotSpeed) {
                shape.rotation.y += shape.userData.rotSpeed;
                shape.rotation.z += shape.userData.rotSpeed * 0.5;
            }
        });

        // Update chromatic aberration
        if (this.chromaticPass) {
            this.chromaticPass.uniforms.uTime.value = time;
        }

        // Camera movement based on scroll
        this.camera.position.z = 30 - this.scrollY * 0.01;
        this.camera.position.y = this.scrollY * 0.005;

        // Render
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

        // Dispose geometries and materials
        this.scene.traverse(object => {
            if (object.geometry) {
                object.geometry.dispose();
            }
            if (object.material) {
                if (Array.isArray(object.material)) {
                    object.material.forEach(m => m.dispose());
                } else {
                    object.material.dispose();
                }
            }
        });

        this.renderer.dispose();
        if (this.composer) {
            this.composer.dispose();
        }

        window.removeEventListener('resize', this.onResize.bind(this));
        window.removeEventListener('scroll', this.onScroll.bind(this));
    }
}

/**
 * Initialize hero scene on a canvas element
 *
 * @param {HTMLCanvasElement} canvas - The canvas to render to
 * @param {Object} options - Configuration options
 * @returns {HeroScene} The scene instance
 */
export function initHeroScene(canvas, options = {}) {
    const scene = new HeroScene(canvas, options);
    scene.start();
    return scene;
}

// Export for WordPress global access
if (typeof window !== 'undefined') {
    window.SkyyRoseHeroScene = HeroScene;
    window.initHeroScene = initHeroScene;
}
