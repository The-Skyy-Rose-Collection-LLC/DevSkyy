/**
 * Love Hurts Collection - Beauty and the Beast Enchanted Ballroom Experience
 *
 * Inspired by Disney's Beauty and the Beast
 * Features: Enchanted Rose, Grand Ballroom, Floating Candles, Stained Glass, Magical Particles
 *
 * @requires three.js r150+
 * @requires OrbitControls
 * @requires EffectComposer (post-processing)
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';

/**
 * Main Scene Manager for Love Hurts Collection
 */
export class LoveHurtsScene {
    constructor(container) {
        this.container = container;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.composer = null;

        // Scene objects
        this.enchantedRose = null;
        this.glassCloche = null;
        this.candles = [];
        this.particleSystems = [];
        this.stainedGlassWindows = [];
        this.enchantedObjects = [];

        // Animation state
        this.clock = new THREE.Clock();
        this.animationId = null;
        this.rosePetalTime = 0;
        this.candleFlickerTime = 0;

        // Product hotspots
        this.hotspots = [];
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        // Color palette from creative brief
        this.colors = {
            deepCrimson: 0x8B0000,
            royalGold: 0xFFD700,
            richPurple: 0x4B0082,
            midnightBlue: 0x191970,
            candleAmber: 0xFFBF00,
            rosePink: 0xFF69B4,
            antiqueGold: 0xC5B358,
            shadowBlack: 0x0A0A0A
        };

        this.init();
    }

    /**
     * Initialize the Three.js scene
     */
    init() {
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(this.colors.shadowBlack);
        this.scene.fog = new THREE.FogExp2(0x0A0A0A, 0.015);

        // Setup camera
        this.camera = new THREE.PerspectiveCamera(
            60,
            this.container.clientWidth / this.container.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 3, 15);

        // Setup renderer
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;
        this.container.appendChild(this.renderer.domElement);

        // Setup controls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 5;
        this.controls.maxDistance = 30;
        this.controls.maxPolarAngle = Math.PI / 2.2;
        this.controls.target.set(0, 2, 0);

        // Setup post-processing
        this.setupPostProcessing();

        // Build the scene
        this.createBallroom();
        this.createEnchantedRose();
        this.createFloatingCandles();
        this.createStainedGlassWindows();
        this.createChandelier();
        this.createEnchantedObjects();
        this.createParticleSystems();
        this.setupLighting();
        this.createProductHotspots();

        // Event listeners
        this.addEventListeners();

        // Start animation
        this.animate();
    }

    /**
     * Setup post-processing effects (Bloom, God Rays)
     */
    setupPostProcessing() {
        this.composer = new EffectComposer(this.renderer);

        const renderPass = new RenderPass(this.scene, this.camera);
        this.composer.addPass(renderPass);

        // Bloom pass for magical glow
        const bloomPass = new UnrealBloomPass(
            new THREE.Vector2(window.innerWidth, window.innerHeight),
            1.5,  // strength
            0.4,  // radius
            0.85  // threshold
        );
        this.composer.addPass(bloomPass);
    }

    /**
     * Create the grand ballroom architecture
     */
    createBallroom() {
        const ballroomGroup = new THREE.Group();

        // Floor - Marble with reflection
        const floorGeometry = new THREE.PlaneGeometry(50, 50);
        const floorMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a1a1a,
            roughness: 0.2,
            metalness: 0.8,
            envMapIntensity: 0.5
        });
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        ballroomGroup.add(floor);

        // Checkerboard pattern overlay
        const checkerTexture = this.createCheckerboardTexture();
        const checkerMaterial = new THREE.MeshStandardMaterial({
            map: checkerTexture,
            transparent: true,
            opacity: 0.3,
            roughness: 0.3,
            metalness: 0.5
        });
        const checker = new THREE.Mesh(floorGeometry, checkerMaterial);
        checker.rotation.x = -Math.PI / 2;
        checker.position.y = 0.01;
        checker.receiveShadow = true;
        ballroomGroup.add(checker);

        // Baroque columns (ornate pillars)
        this.createColumns(ballroomGroup);

        // Vaulted ceiling
        this.createCeiling(ballroomGroup);

        // Walls with alcoves
        this.createWalls(ballroomGroup);

        this.scene.add(ballroomGroup);
    }

    /**
     * Create ornate baroque columns with gold leaf accents
     */
    createColumns(parent) {
        const columnPositions = [
            [-12, 0, -8], [12, 0, -8],
            [-12, 0, 0], [12, 0, 0],
            [-12, 0, 8], [12, 0, 8]
        ];

        columnPositions.forEach(pos => {
            const column = this.createSingleColumn();
            column.position.set(...pos);
            parent.add(column);
        });
    }

    /**
     * Create a single ornate column
     */
    createSingleColumn() {
        const columnGroup = new THREE.Group();

        // Base
        const baseGeometry = new THREE.CylinderGeometry(0.8, 1, 0.5, 8);
        const baseMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.antiqueGold,
            roughness: 0.3,
            metalness: 0.7
        });
        const base = new THREE.Mesh(baseGeometry, baseMaterial);
        base.castShadow = true;
        columnGroup.add(base);

        // Shaft
        const shaftGeometry = new THREE.CylinderGeometry(0.6, 0.6, 8, 12);
        const shaftMaterial = new THREE.MeshStandardMaterial({
            color: 0xf5f5dc,
            roughness: 0.6,
            metalness: 0.1
        });
        const shaft = new THREE.Mesh(shaftGeometry, shaftMaterial);
        shaft.position.y = 4.5;
        shaft.castShadow = true;
        columnGroup.add(shaft);

        // Capital (top)
        const capitalGeometry = new THREE.CylinderGeometry(1, 0.6, 0.8, 8);
        const capitalMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.royalGold,
            roughness: 0.2,
            metalness: 0.9,
            emissive: this.colors.royalGold,
            emissiveIntensity: 0.2
        });
        const capital = new THREE.Mesh(capitalGeometry, capitalMaterial);
        capital.position.y = 8.9;
        capital.castShadow = true;
        columnGroup.add(capital);

        // Decorative gold bands
        for (let i = 2; i < 8; i += 2) {
            const bandGeometry = new THREE.TorusGeometry(0.65, 0.05, 8, 16);
            const band = new THREE.Mesh(bandGeometry, capitalMaterial);
            band.rotation.x = Math.PI / 2;
            band.position.y = i;
            columnGroup.add(band);
        }

        return columnGroup;
    }

    /**
     * Create vaulted ceiling with frescoes
     */
    createCeiling(parent) {
        const ceilingGeometry = new THREE.PlaneGeometry(50, 50, 10, 10);

        // Curve the ceiling for vault effect
        const positions = ceilingGeometry.attributes.position;
        for (let i = 0; i < positions.count; i++) {
            const x = positions.getX(i);
            const z = positions.getZ(i);
            const dist = Math.sqrt(x * x + z * z);
            const height = Math.max(0, 12 - dist * 0.1);
            positions.setY(i, height);
        }
        positions.needsUpdate = true;
        ceilingGeometry.computeVertexNormals();

        const ceilingMaterial = new THREE.MeshStandardMaterial({
            color: 0x2a2a2a,
            roughness: 0.8,
            metalness: 0.1,
            side: THREE.DoubleSide
        });

        const ceiling = new THREE.Mesh(ceilingGeometry, ceilingMaterial);
        ceiling.position.y = 12;
        parent.add(ceiling);
    }

    /**
     * Create walls with alcoves for product displays
     */
    createWalls(parent) {
        const wallHeight = 10;
        const wallThickness = 0.5;
        const wallMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a1a1a,
            roughness: 0.7,
            metalness: 0.1
        });

        // Back wall
        const backWallGeometry = new THREE.BoxGeometry(50, wallHeight, wallThickness);
        const backWall = new THREE.Mesh(backWallGeometry, wallMaterial);
        backWall.position.set(0, wallHeight / 2, -15);
        backWall.receiveShadow = true;
        parent.add(backWall);

        // Side walls (with openings for windows)
        const sideWallGeometry = new THREE.BoxGeometry(wallThickness, wallHeight, 30);

        const leftWall = new THREE.Mesh(sideWallGeometry, wallMaterial);
        leftWall.position.set(-25, wallHeight / 2, 0);
        leftWall.receiveShadow = true;
        parent.add(leftWall);

        const rightWall = new THREE.Mesh(sideWallGeometry, wallMaterial);
        rightWall.position.set(25, wallHeight / 2, 0);
        rightWall.receiveShadow = true;
        parent.add(rightWall);

        // Create alcoves for product displays
        this.createAlcoves(parent);
    }

    /**
     * Create decorative alcoves for product displays
     */
    createAlcoves(parent) {
        const alcovePositions = [
            [-20, 2, -10], [-20, 2, 0], [-20, 2, 10],
            [20, 2, -10], [20, 2, 0], [20, 2, 10]
        ];

        alcovePositions.forEach(pos => {
            const alcoveGroup = new THREE.Group();

            // Alcove frame (golden arch)
            const archGeometry = new THREE.TorusGeometry(1.5, 0.1, 8, 16, Math.PI);
            const archMaterial = new THREE.MeshStandardMaterial({
                color: this.colors.royalGold,
                roughness: 0.2,
                metalness: 0.9,
                emissive: this.colors.royalGold,
                emissiveIntensity: 0.3
            });
            const arch = new THREE.Mesh(archGeometry, archMaterial);
            arch.rotation.z = Math.PI;
            arch.position.y = 1.5;
            alcoveGroup.add(arch);

            // Pedestal
            const pedestalGeometry = new THREE.CylinderGeometry(0.5, 0.6, 1, 8);
            const pedestal = new THREE.Mesh(pedestalGeometry, archMaterial);
            pedestal.castShadow = true;
            alcoveGroup.add(pedestal);

            alcoveGroup.position.set(...pos);
            parent.add(alcoveGroup);
        });
    }

    /**
     * Create the enchanted rose under glass cloche (centerpiece!)
     */
    createEnchantedRose() {
        const roseGroup = new THREE.Group();
        roseGroup.position.set(0, 2, 0);

        // Ornate base/pedestal
        const baseGeometry = new THREE.CylinderGeometry(1.2, 1.5, 0.3, 8);
        const baseMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.royalGold,
            roughness: 0.2,
            metalness: 0.9,
            emissive: this.colors.royalGold,
            emissiveIntensity: 0.3
        });
        const base = new THREE.Mesh(baseGeometry, baseMaterial);
        base.castShadow = true;
        roseGroup.add(base);

        // Glass cloche/dome
        const clocheGeometry = new THREE.SphereGeometry(1, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2);
        const clocheMaterial = new THREE.MeshPhysicalMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.2,
            roughness: 0.1,
            metalness: 0,
            transmission: 0.9,
            thickness: 0.5,
            envMapIntensity: 1,
            clearcoat: 1,
            clearcoatRoughness: 0.1
        });
        this.glassCloche = new THREE.Mesh(clocheGeometry, clocheMaterial);
        this.glassCloche.position.y = 1;
        this.glassCloche.castShadow = true;
        roseGroup.add(this.glassCloche);

        // The enchanted rose itself
        this.enchantedRose = this.createRose();
        this.enchantedRose.position.y = 0.5;
        roseGroup.add(this.enchantedRose);

        // Magical glow around rose
        const glowGeometry = new THREE.SphereGeometry(0.8, 16, 16);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: this.colors.deepCrimson,
            transparent: true,
            opacity: 0.3,
            side: THREE.BackSide
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        glow.position.y = 0.5;
        roseGroup.add(glow);

        // Point light inside rose (pulsing)
        const roseLight = new THREE.PointLight(this.colors.deepCrimson, 2, 10);
        roseLight.position.y = 0.5;
        roseLight.castShadow = true;
        roseLight.shadow.mapSize.width = 1024;
        roseLight.shadow.mapSize.height = 1024;
        roseGroup.add(roseLight);
        this.roseLight = roseLight; // Store for animation

        this.scene.add(roseGroup);
        this.roseGroup = roseGroup;
    }

    /**
     * Create the rose flower itself
     */
    createRose() {
        const roseGroup = new THREE.Group();

        // Rose petals (layered spheres forming bloom)
        const petalMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.deepCrimson,
            roughness: 0.4,
            metalness: 0.2,
            emissive: this.colors.deepCrimson,
            emissiveIntensity: 0.5
        });

        // Create multiple petal layers
        const petalLayers = [
            { count: 5, radius: 0.15, height: 0.3, yOffset: 0 },
            { count: 6, radius: 0.18, height: 0.25, yOffset: -0.05 },
            { count: 7, radius: 0.2, height: 0.2, yOffset: -0.1 }
        ];

        petalLayers.forEach(layer => {
            for (let i = 0; i < layer.count; i++) {
                const angle = (i / layer.count) * Math.PI * 2;
                const petalGeometry = new THREE.SphereGeometry(layer.radius, 8, 8, 0, Math.PI);
                const petal = new THREE.Mesh(petalGeometry, petalMaterial);

                petal.position.x = Math.cos(angle) * layer.radius;
                petal.position.z = Math.sin(angle) * layer.radius;
                petal.position.y = layer.yOffset;

                petal.rotation.y = angle;
                petal.rotation.x = Math.PI / 4;

                petal.castShadow = true;
                roseGroup.add(petal);
            }
        });

        // Center of rose (golden stamens)
        const centerGeometry = new THREE.SphereGeometry(0.1, 8, 8);
        const centerMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.royalGold,
            roughness: 0.3,
            metalness: 0.8,
            emissive: this.colors.royalGold,
            emissiveIntensity: 0.8
        });
        const center = new THREE.Mesh(centerGeometry, centerMaterial);
        center.position.y = 0.1;
        roseGroup.add(center);

        // Stem
        const stemGeometry = new THREE.CylinderGeometry(0.02, 0.03, 0.6, 8);
        const stemMaterial = new THREE.MeshStandardMaterial({
            color: 0x0a4d0a,
            roughness: 0.6
        });
        const stem = new THREE.Mesh(stemGeometry, stemMaterial);
        stem.position.y = -0.3;
        roseGroup.add(stem);

        // Leaves
        const leafGeometry = new THREE.SphereGeometry(0.08, 8, 8, 0, Math.PI);
        const leafMaterial = new THREE.MeshStandardMaterial({
            color: 0x0a5d0a,
            roughness: 0.5
        });

        [-0.1, -0.15, -0.2].forEach((yPos, i) => {
            const leaf = new THREE.Mesh(leafGeometry, leafMaterial);
            const angle = (i * Math.PI * 2) / 3;
            leaf.position.x = Math.cos(angle) * 0.05;
            leaf.position.z = Math.sin(angle) * 0.05;
            leaf.position.y = yPos;
            leaf.rotation.y = angle;
            leaf.rotation.x = Math.PI / 3;
            roseGroup.add(leaf);
        });

        return roseGroup;
    }

    /**
     * Create hundreds of floating candles (like Hogwarts!)
     */
    createFloatingCandles() {
        const candleCount = 100;
        const distribution = {
            height: { min: 5, max: 10 },
            radius: { min: 5, max: 20 }
        };

        for (let i = 0; i < candleCount; i++) {
            const candle = this.createSingleCandle();

            // Random position in cylinder distribution
            const angle = Math.random() * Math.PI * 2;
            const radius = distribution.radius.min +
                          Math.random() * (distribution.radius.max - distribution.radius.min);

            candle.position.x = Math.cos(angle) * radius;
            candle.position.z = Math.sin(angle) * radius;
            candle.position.y = distribution.height.min +
                               Math.random() * (distribution.height.max - distribution.height.min);

            // Slight random rotation
            candle.rotation.x = (Math.random() - 0.5) * 0.1;
            candle.rotation.z = (Math.random() - 0.5) * 0.1;

            this.candles.push(candle);
            this.scene.add(candle);
        }
    }

    /**
     * Create a single floating candle
     */
    createSingleCandle() {
        const candleGroup = new THREE.Group();

        // Candle body (wax)
        const bodyGeometry = new THREE.CylinderGeometry(0.05, 0.06, 0.3, 8);
        const bodyMaterial = new THREE.MeshStandardMaterial({
            color: 0xf5e6d3,
            roughness: 0.7
        });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        body.castShadow = true;
        candleGroup.add(body);

        // Flame (emissive cone)
        const flameGeometry = new THREE.ConeGeometry(0.03, 0.08, 8);
        const flameMaterial = new THREE.MeshBasicMaterial({
            color: this.colors.candleAmber,
            transparent: true,
            opacity: 0.9
        });
        const flame = new THREE.Mesh(flameGeometry, flameMaterial);
        flame.position.y = 0.19;
        candleGroup.add(flame);

        // Flame inner core (white)
        const coreGeometry = new THREE.SphereGeometry(0.02, 8, 8);
        const coreMaterial = new THREE.MeshBasicMaterial({
            color: 0xffff99
        });
        const core = new THREE.Mesh(coreGeometry, coreMaterial);
        core.position.y = 0.17;
        candleGroup.add(core);

        // Point light (flickering)
        const candleLight = new THREE.PointLight(this.colors.candleAmber, 0.5, 5);
        candleLight.position.y = 0.2;
        candleLight.castShadow = true;
        candleLight.shadow.mapSize.width = 256;
        candleLight.shadow.mapSize.height = 256;
        candleGroup.add(candleLight);

        // Store light reference for animation
        candleGroup.userData.light = candleLight;
        candleGroup.userData.flame = flame;
        candleGroup.userData.flickerPhase = Math.random() * Math.PI * 2;

        return candleGroup;
    }

    /**
     * Create grand crystal chandelier
     */
    createChandelier() {
        const chandelierGroup = new THREE.Group();
        chandelierGroup.position.set(0, 10, 0);

        // Central sphere
        const centerGeometry = new THREE.SphereGeometry(0.5, 16, 16);
        const centerMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.royalGold,
            roughness: 0.2,
            metalness: 0.9,
            emissive: this.colors.royalGold,
            emissiveIntensity: 0.3
        });
        const center = new THREE.Mesh(centerGeometry, centerMaterial);
        chandelierGroup.add(center);

        // Crystal arms with candles
        const armCount = 8;
        for (let i = 0; i < armCount; i++) {
            const angle = (i / armCount) * Math.PI * 2;

            // Arm
            const armGeometry = new THREE.CylinderGeometry(0.05, 0.03, 2, 8);
            const arm = new THREE.Mesh(armGeometry, centerMaterial);
            arm.position.x = Math.cos(angle) * 1;
            arm.position.z = Math.sin(angle) * 1;
            arm.position.y = -0.5;
            arm.rotation.z = Math.PI / 4;
            arm.rotation.y = angle;
            chandelierGroup.add(arm);

            // Candle on arm
            const candle = this.createSingleCandle();
            candle.position.x = Math.cos(angle) * 1.7;
            candle.position.z = Math.sin(angle) * 1.7;
            candle.position.y = -1.2;
            chandelierGroup.add(candle);
            this.candles.push(candle);
        }

        // Hanging crystals (diamonds)
        for (let i = 0; i < 20; i++) {
            const crystalGeometry = new THREE.OctahedronGeometry(0.1, 0);
            const crystalMaterial = new THREE.MeshPhysicalMaterial({
                color: 0xffffff,
                roughness: 0,
                metalness: 0.1,
                transmission: 0.95,
                thickness: 0.5,
                envMapIntensity: 1,
                clearcoat: 1
            });
            const crystal = new THREE.Mesh(crystalGeometry, crystalMaterial);

            const angle = Math.random() * Math.PI * 2;
            const radius = Math.random() * 1.5;
            crystal.position.x = Math.cos(angle) * radius;
            crystal.position.z = Math.sin(angle) * radius;
            crystal.position.y = -1.5 - Math.random() * 1;

            crystal.rotation.set(
                Math.random() * Math.PI,
                Math.random() * Math.PI,
                Math.random() * Math.PI
            );

            chandelierGroup.add(crystal);
        }

        // Main chandelier light
        const chandelierLight = new THREE.PointLight(this.colors.candleAmber, 3, 30);
        chandelierLight.castShadow = true;
        chandelierLight.shadow.mapSize.width = 2048;
        chandelierLight.shadow.mapSize.height = 2048;
        chandelierGroup.add(chandelierLight);

        this.scene.add(chandelierGroup);
        this.chandelier = chandelierGroup;
    }

    /**
     * Create stained glass windows with colored lighting
     */
    createStainedGlassWindows() {
        const windowPositions = [
            { pos: [-24, 5, -5], rot: [0, Math.PI / 2, 0], color: this.colors.richPurple },
            { pos: [-24, 5, 5], rot: [0, Math.PI / 2, 0], color: this.colors.deepCrimson },
            { pos: [24, 5, -5], rot: [0, -Math.PI / 2, 0], color: this.colors.royalGold },
            { pos: [24, 5, 5], rot: [0, -Math.PI / 2, 0], color: this.colors.rosePink }
        ];

        windowPositions.forEach(windowData => {
            const windowGroup = this.createStainedGlassWindow(windowData.color);
            windowGroup.position.set(...windowData.pos);
            windowGroup.rotation.set(...windowData.rot);
            this.scene.add(windowGroup);
            this.stainedGlassWindows.push(windowGroup);
        });
    }

    /**
     * Create a single stained glass window
     */
    createStainedGlassWindow(color) {
        const windowGroup = new THREE.Group();

        // Window frame (gothic arch)
        const frameMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a1a1a,
            roughness: 0.8
        });

        // Create gothic arch frame
        const leftFrame = new THREE.Mesh(new THREE.BoxGeometry(0.2, 4, 0.2), frameMaterial);
        leftFrame.position.x = -1.4;
        windowGroup.add(leftFrame);

        const rightFrame = new THREE.Mesh(new THREE.BoxGeometry(0.2, 4, 0.2), frameMaterial);
        rightFrame.position.x = 1.4;
        windowGroup.add(rightFrame);

        const bottomFrame = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.2, 3), frameMaterial);
        bottomFrame.position.y = -2;
        windowGroup.add(bottomFrame);

        // Stained glass (rose pattern)
        const glassGeometry = new THREE.PlaneGeometry(2.8, 3.8);
        const glassMaterial = new THREE.MeshPhysicalMaterial({
            color: color,
            transparent: true,
            opacity: 0.6,
            roughness: 0.1,
            metalness: 0,
            transmission: 0.7,
            thickness: 0.5,
            emissive: color,
            emissiveIntensity: 0.5
        });
        const glass = new THREE.Mesh(glassGeometry, glassMaterial);
        windowGroup.add(glass);

        // Rose pattern on glass (simplified)
        const patternGeometry = new THREE.CircleGeometry(0.5, 16);
        const patternMaterial = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0.8
        });
        const pattern = new THREE.Mesh(patternGeometry, patternMaterial);
        pattern.position.z = 0.01;
        windowGroup.add(pattern);

        // Colored spotlight through window
        const windowLight = new THREE.SpotLight(color, 2, 30, Math.PI / 6, 0.5);
        windowLight.position.set(0, 0, 1);
        windowLight.target.position.set(0, -2, -10);
        windowLight.castShadow = true;
        windowGroup.add(windowLight);
        windowGroup.add(windowLight.target);

        // Moonlight (cool blue from behind)
        const moonLight = new THREE.SpotLight(0x9db4ff, 1, 20, Math.PI / 8, 0.3);
        moonLight.position.set(0, 2, 3);
        windowGroup.add(moonLight);

        // Store light for animation
        windowGroup.userData.light = windowLight;

        return windowGroup;
    }

    /**
     * Create enchanted objects (Beauty & Beast Easter eggs)
     */
    createEnchantedObjects() {
        // Lumière (candelabra)
        const candelabra = this.createCandelabra();
        candelabra.position.set(3, 1, 5);
        this.scene.add(candelabra);
        this.enchantedObjects.push(candelabra);

        // Cogsworth (clock)
        const clock = this.createClock();
        clock.position.set(-3, 1.5, 5);
        this.scene.add(clock);
        this.enchantedObjects.push(clock);

        // Mrs. Potts (teapot) and Chip (teacup)
        const teaSet = this.createTeaSet();
        teaSet.position.set(4, 1, -4);
        this.scene.add(teaSet);
        this.enchantedObjects.push(teaSet);

        // Magic mirror
        const mirror = this.createMagicMirror();
        mirror.position.set(0, 3, -14);
        this.scene.add(mirror);
        this.enchantedObjects.push(mirror);

        // Enchanted wardrobe
        const wardrobe = this.createWardrobe();
        wardrobe.position.set(-8, 0, -10);
        this.scene.add(wardrobe);
        this.enchantedObjects.push(wardrobe);

        // Enchanted book (Belle's favorite)
        const book = this.createEnchantedBook();
        book.position.set(5, 1.2, 3);
        this.scene.add(book);
        this.enchantedObjects.push(book);
    }

    /**
     * Create Lumière (floating candelabra)
     */
    createCandelabra() {
        const candelabraGroup = new THREE.Group();

        // Base/body
        const bodyGeometry = new THREE.CylinderGeometry(0.15, 0.2, 0.4, 8);
        const bodyMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.royalGold,
            roughness: 0.2,
            metalness: 0.9
        });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        candelabraGroup.add(body);

        // Three arms
        [-0.3, 0, 0.3].forEach((xOffset) => {
            const armGeometry = new THREE.CylinderGeometry(0.02, 0.02, 0.3, 8);
            const arm = new THREE.Mesh(armGeometry, bodyMaterial);
            arm.position.set(xOffset, 0.3, 0);
            arm.rotation.z = xOffset === 0 ? 0 : (xOffset < 0 ? -Math.PI / 6 : Math.PI / 6);
            candelabraGroup.add(arm);

            const candle = this.createSingleCandle();
            candle.scale.set(0.7, 0.7, 0.7);
            candle.position.set(xOffset, 0.5, 0);
            candelabraGroup.add(candle);
            this.candles.push(candle);
        });

        // Hover animation
        candelabraGroup.userData.floatPhase = Math.random() * Math.PI * 2;

        return candelabraGroup;
    }

    /**
     * Create Cogsworth (enchanted clock)
     */
    createClock() {
        const clockGroup = new THREE.Group();

        // Clock body
        const bodyGeometry = new THREE.BoxGeometry(0.4, 0.6, 0.2);
        const bodyMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.antiqueGold,
            roughness: 0.3,
            metalness: 0.8
        });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        clockGroup.add(body);

        // Clock face
        const faceGeometry = new THREE.CircleGeometry(0.15, 16);
        const faceMaterial = new THREE.MeshBasicMaterial({
            color: 0xffffff
        });
        const face = new THREE.Mesh(faceGeometry, faceMaterial);
        face.position.z = 0.11;
        clockGroup.add(face);

        // Hour hand
        const hourHandGeometry = new THREE.BoxGeometry(0.02, 0.08, 0.01);
        const handMaterial = new THREE.MeshBasicMaterial({ color: 0x000000 });
        const hourHand = new THREE.Mesh(hourHandGeometry, handMaterial);
        hourHand.position.set(0, 0.04, 0.12);
        clockGroup.add(hourHand);

        // Minute hand
        const minuteHand = new THREE.Mesh(
            new THREE.BoxGeometry(0.01, 0.12, 0.01),
            handMaterial
        );
        minuteHand.position.set(0, 0.06, 0.12);
        clockGroup.add(minuteHand);

        // Store hands for animation
        clockGroup.userData.hourHand = hourHand;
        clockGroup.userData.minuteHand = minuteHand;

        return clockGroup;
    }

    /**
     * Create Mrs. Potts and Chip (teapot and cup)
     */
    createTeaSet() {
        const teaSetGroup = new THREE.Group();

        const porcelainMaterial = new THREE.MeshStandardMaterial({
            color: 0xf0f0f0,
            roughness: 0.2,
            metalness: 0.1
        });

        // Teapot (Mrs. Potts)
        const potBody = new THREE.Mesh(
            new THREE.SphereGeometry(0.15, 16, 16),
            porcelainMaterial
        );
        teaSetGroup.add(potBody);

        // Teapot spout
        const spout = new THREE.Mesh(
            new THREE.CylinderGeometry(0.02, 0.03, 0.1, 8),
            porcelainMaterial
        );
        spout.position.set(0.15, 0, 0);
        spout.rotation.z = Math.PI / 2;
        teaSetGroup.add(spout);

        // Teapot handle
        const handleGeometry = new THREE.TorusGeometry(0.08, 0.02, 8, 16, Math.PI);
        const handle = new THREE.Mesh(handleGeometry, porcelainMaterial);
        handle.position.set(-0.1, 0, 0);
        handle.rotation.y = Math.PI / 2;
        teaSetGroup.add(handle);

        // Teacup (Chip)
        const cup = new THREE.Mesh(
            new THREE.CylinderGeometry(0.06, 0.05, 0.08, 16),
            porcelainMaterial
        );
        cup.position.set(0.3, -0.05, 0);
        teaSetGroup.add(cup);

        return teaSetGroup;
    }

    /**
     * Create magic mirror
     */
    createMagicMirror() {
        const mirrorGroup = new THREE.Group();

        // Frame
        const frameGeometry = new THREE.BoxGeometry(3, 4, 0.2);
        const frameMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.royalGold,
            roughness: 0.2,
            metalness: 0.9,
            emissive: this.colors.royalGold,
            emissiveIntensity: 0.2
        });
        const frame = new THREE.Mesh(frameGeometry, frameMaterial);
        mirrorGroup.add(frame);

        // Mirror surface (reflective)
        const mirrorGeometry = new THREE.PlaneGeometry(2.6, 3.6);
        const mirrorMaterial = new THREE.MeshStandardMaterial({
            color: 0x8888aa,
            roughness: 0.1,
            metalness: 0.9,
            envMapIntensity: 1
        });
        const mirror = new THREE.Mesh(mirrorGeometry, mirrorMaterial);
        mirror.position.z = 0.11;
        mirrorGroup.add(mirror);

        // Magical glow
        const glowLight = new THREE.PointLight(0x8888ff, 1, 5);
        glowLight.position.z = 0.5;
        mirrorGroup.add(glowLight);

        // Store for interaction
        mirrorGroup.userData.isMirror = true;
        mirrorGroup.userData.light = glowLight;

        return mirrorGroup;
    }

    /**
     * Create enchanted wardrobe
     */
    createWardrobe() {
        const wardrobeGroup = new THREE.Group();

        const woodMaterial = new THREE.MeshStandardMaterial({
            color: 0x4a2511,
            roughness: 0.8,
            metalness: 0.1
        });

        // Body
        const body = new THREE.Mesh(
            new THREE.BoxGeometry(2, 4, 1),
            woodMaterial
        );
        body.position.y = 2;
        wardrobeGroup.add(body);

        // Doors (slightly open)
        const doorGeometry = new THREE.BoxGeometry(0.95, 3.8, 0.1);
        const leftDoor = new THREE.Mesh(doorGeometry, woodMaterial);
        leftDoor.position.set(-0.5, 2, 0.5);
        leftDoor.rotation.y = -Math.PI / 12; // Slightly ajar
        wardrobeGroup.add(leftDoor);

        const rightDoor = new THREE.Mesh(doorGeometry, woodMaterial);
        rightDoor.position.set(0.5, 2, 0.5);
        rightDoor.rotation.y = Math.PI / 12; // Slightly ajar
        wardrobeGroup.add(rightDoor);

        // Golden handles
        const handleMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.royalGold,
            roughness: 0.2,
            metalness: 0.9
        });
        const handleGeometry = new THREE.SphereGeometry(0.05, 8, 8);

        const leftHandle = new THREE.Mesh(handleGeometry, handleMaterial);
        leftHandle.position.set(-0.3, 2, 0.6);
        wardrobeGroup.add(leftHandle);

        const rightHandle = new THREE.Mesh(handleGeometry, handleMaterial);
        rightHandle.position.set(0.3, 2, 0.6);
        wardrobeGroup.add(rightHandle);

        return wardrobeGroup;
    }

    /**
     * Create enchanted book (Belle's favorite)
     */
    createEnchantedBook() {
        const bookGroup = new THREE.Group();

        // Book cover
        const coverGeometry = new THREE.BoxGeometry(0.3, 0.4, 0.05);
        const coverMaterial = new THREE.MeshStandardMaterial({
            color: 0x8b0000,
            roughness: 0.7,
            metalness: 0.1
        });
        const cover = new THREE.Mesh(coverGeometry, coverMaterial);
        cover.rotation.x = Math.PI / 6; // Slightly open
        bookGroup.add(cover);

        // Pages
        const pagesGeometry = new THREE.BoxGeometry(0.28, 0.38, 0.08);
        const pagesMaterial = new THREE.MeshStandardMaterial({
            color: 0xf5e6d3,
            roughness: 0.9
        });
        const pages = new THREE.Mesh(pagesGeometry, pagesMaterial);
        pages.position.z = 0.01;
        pages.rotation.x = Math.PI / 6;
        bookGroup.add(pages);

        // Magical glow
        const bookLight = new THREE.PointLight(this.colors.royalGold, 0.5, 2);
        bookLight.position.y = 0.3;
        bookGroup.add(bookLight);

        // Floating animation
        bookGroup.userData.floatPhase = Math.random() * Math.PI * 2;
        bookGroup.userData.light = bookLight;

        return bookGroup;
    }

    /**
     * Create magical particle systems
     */
    createParticleSystems() {
        // Rose petal particles
        this.rosePetalSystem = this.createRosePetalParticles();
        this.scene.add(this.rosePetalSystem);
        this.particleSystems.push(this.rosePetalSystem);

        // Golden sparkles
        this.sparkleSystem = this.createSparkleParticles();
        this.scene.add(this.sparkleSystem);
        this.particleSystems.push(this.sparkleSystem);

        // Purple magical mist
        this.mistSystem = this.createMistParticles();
        this.scene.add(this.mistSystem);
        this.particleSystems.push(this.mistSystem);
    }

    /**
     * Create falling rose petal particle system
     */
    createRosePetalParticles() {
        const particleCount = 200;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);
        const sizes = new Float32Array(particleCount);
        const velocities = new Float32Array(particleCount * 3);

        for (let i = 0; i < particleCount; i++) {
            const i3 = i * 3;

            // Random position around rose
            positions[i3] = (Math.random() - 0.5) * 10;
            positions[i3 + 1] = Math.random() * 12;
            positions[i3 + 2] = (Math.random() - 0.5) * 10;

            // Rose petal color (red to pink)
            const color = new THREE.Color(this.colors.deepCrimson);
            color.lerp(new THREE.Color(this.colors.rosePink), Math.random() * 0.5);
            colors[i3] = color.r;
            colors[i3 + 1] = color.g;
            colors[i3 + 2] = color.b;

            sizes[i] = 0.1 + Math.random() * 0.1;

            // Falling velocity
            velocities[i3] = (Math.random() - 0.5) * 0.02;
            velocities[i3 + 1] = -0.05 - Math.random() * 0.05;
            velocities[i3 + 2] = (Math.random() - 0.5) * 0.02;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        const material = new THREE.PointsMaterial({
            size: 0.15,
            vertexColors: true,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        const particles = new THREE.Points(geometry, material);
        particles.userData.velocities = velocities;

        return particles;
    }

    /**
     * Create golden sparkle particles
     */
    createSparkleParticles() {
        const particleCount = 500;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const sizes = new Float32Array(particleCount);

        for (let i = 0; i < particleCount; i++) {
            const i3 = i * 3;

            // Random position throughout ballroom
            positions[i3] = (Math.random() - 0.5) * 40;
            positions[i3 + 1] = Math.random() * 10;
            positions[i3 + 2] = (Math.random() - 0.5) * 30;

            sizes[i] = Math.random() * 0.05;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        const material = new THREE.PointsMaterial({
            color: this.colors.royalGold,
            size: 0.05,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        return new THREE.Points(geometry, material);
    }

    /**
     * Create purple magical mist particles
     */
    createMistParticles() {
        const particleCount = 100;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const sizes = new Float32Array(particleCount);

        for (let i = 0; i < particleCount; i++) {
            const i3 = i * 3;

            positions[i3] = (Math.random() - 0.5) * 30;
            positions[i3 + 1] = Math.random() * 3;
            positions[i3 + 2] = (Math.random() - 0.5) * 20;

            sizes[i] = 0.5 + Math.random() * 1;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        const material = new THREE.PointsMaterial({
            color: this.colors.richPurple,
            size: 1,
            transparent: true,
            opacity: 0.3,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        return new THREE.Points(geometry, material);
    }

    /**
     * Setup dramatic lighting
     */
    setupLighting() {
        // Ambient light (very dim)
        const ambient = new THREE.AmbientLight(0x1a1a2e, 0.3);
        this.scene.add(ambient);

        // Hemisphere light (moonlight from above)
        const hemiLight = new THREE.HemisphereLight(0x9db4ff, 0x080820, 0.4);
        this.scene.add(hemiLight);

        // Main moonlight (directional)
        const moonLight = new THREE.DirectionalLight(0x9db4ff, 0.8);
        moonLight.position.set(10, 15, 10);
        moonLight.castShadow = true;
        moonLight.shadow.mapSize.width = 2048;
        moonLight.shadow.mapSize.height = 2048;
        moonLight.shadow.camera.left = -30;
        moonLight.shadow.camera.right = 30;
        moonLight.shadow.camera.top = 30;
        moonLight.shadow.camera.bottom = -30;
        this.scene.add(moonLight);

        // Additional accent lights around room perimeter
        const accentPositions = [
            [-15, 3, -10], [15, 3, -10],
            [-15, 3, 10], [15, 3, 10]
        ];

        accentPositions.forEach(pos => {
            const accent = new THREE.PointLight(this.colors.candleAmber, 0.5, 15);
            accent.position.set(...pos);
            this.scene.add(accent);
        });
    }

    /**
     * Create product display hotspots
     */
    createProductHotspots() {
        // Product positions (in alcoves and pedestals)
        const productData = [
            { name: 'Product 1', pos: [-20, 2, -10], id: 'prod-1' },
            { name: 'Product 2', pos: [-20, 2, 0], id: 'prod-2' },
            { name: 'Product 3', pos: [-20, 2, 10], id: 'prod-3' },
            { name: 'Product 4', pos: [20, 2, -10], id: 'prod-4' },
            { name: 'Product 5', pos: [20, 2, 0], id: 'prod-5' },
            { name: 'Product 6', pos: [20, 2, 10], id: 'prod-6' }
        ];

        productData.forEach(product => {
            const hotspot = this.createProductHotspot(product);
            hotspot.position.set(...product.pos);
            this.scene.add(hotspot);
            this.hotspots.push(hotspot);
        });
    }

    /**
     * Create a single product hotspot
     */
    createProductHotspot(productData) {
        const hotspotGroup = new THREE.Group();
        hotspotGroup.userData = {
            isHotspot: true,
            productId: productData.id,
            productName: productData.name
        };

        // Glowing rose-shaped marker
        const markerGeometry = new THREE.SphereGeometry(0.3, 16, 16);
        const markerMaterial = new THREE.MeshBasicMaterial({
            color: this.colors.rosePink,
            transparent: true,
            opacity: 0.6
        });
        const marker = new THREE.Mesh(markerGeometry, markerMaterial);
        hotspotGroup.add(marker);

        // Pulsing ring
        const ringGeometry = new THREE.TorusGeometry(0.4, 0.05, 8, 32);
        const ringMaterial = new THREE.MeshBasicMaterial({
            color: this.colors.royalGold,
            transparent: true,
            opacity: 0.8
        });
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.rotation.x = Math.PI / 2;
        hotspotGroup.add(ring);

        // Point light
        const hotspotLight = new THREE.PointLight(this.colors.rosePink, 1, 5);
        hotspotGroup.add(hotspotLight);

        // Store for animation
        hotspotGroup.userData.marker = marker;
        hotspotGroup.userData.ring = ring;
        hotspotGroup.userData.light = hotspotLight;
        hotspotGroup.userData.pulsePhase = Math.random() * Math.PI * 2;

        return hotspotGroup;
    }

    /**
     * Create a checkerboard texture for floor
     */
    createCheckerboardTexture() {
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 512;
        const ctx = canvas.getContext('2d');

        const tileSize = 64;
        for (let y = 0; y < 8; y++) {
            for (let x = 0; x < 8; x++) {
                ctx.fillStyle = (x + y) % 2 === 0 ? '#2a2a2a' : '#1a1a1a';
                ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
            }
        }

        const texture = new THREE.CanvasTexture(canvas);
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.repeat.set(4, 4);

        return texture;
    }

    /**
     * Add event listeners
     */
    addEventListeners() {
        // Window resize
        window.addEventListener('resize', () => this.onWindowResize(), false);

        // Mouse move for hotspot detection
        this.renderer.domElement.addEventListener('mousemove', (e) => this.onMouseMove(e), false);

        // Click for hotspot interaction
        this.renderer.domElement.addEventListener('click', (e) => this.onMouseClick(e), false);
    }

    /**
     * Handle window resize
     */
    onWindowResize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.composer.setSize(this.container.clientWidth, this.container.clientHeight);
    }

    /**
     * Handle mouse move (hotspot hover)
     */
    onMouseMove(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        // Raycast to check for hotspot hover
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.hotspots, true);

        // Reset all hotspots
        this.hotspots.forEach(hotspot => {
            if (hotspot.userData.marker) {
                hotspot.userData.marker.material.opacity = 0.6;
            }
        });

        // Highlight hovered hotspot
        if (intersects.length > 0) {
            let hotspot = intersects[0].object;
            while (hotspot.parent && !hotspot.userData.isHotspot) {
                hotspot = hotspot.parent;
            }
            if (hotspot.userData.isHotspot && hotspot.userData.marker) {
                hotspot.userData.marker.material.opacity = 1;
                this.renderer.domElement.style.cursor = 'pointer';
            }
        } else {
            this.renderer.domElement.style.cursor = 'default';
        }
    }

    /**
     * Handle mouse click (hotspot interaction)
     */
    onMouseClick(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.hotspots, true);

        if (intersects.length > 0) {
            let hotspot = intersects[0].object;
            while (hotspot.parent && !hotspot.userData.isHotspot) {
                hotspot = hotspot.parent;
            }
            if (hotspot.userData.isHotspot) {
                this.onHotspotClick(hotspot.userData);
            }
        }
    }

    /**
     * Handle hotspot click
     */
    onHotspotClick(hotspotData) {
        console.log('Product clicked:', hotspotData.productName, hotspotData.productId);

        // Trigger custom event for product modal
        const event = new CustomEvent('productHotspotClick', {
            detail: {
                productId: hotspotData.productId,
                productName: hotspotData.productName
            }
        });
        window.dispatchEvent(event);

        // Add magical effect on click
        this.createMagicalClickEffect(hotspotData);
    }

    /**
     * Create magical effect when hotspot is clicked
     */
    createMagicalClickEffect() {
        // Create burst of rose petals
        const burstCount = 20;
        const burstGeometry = new THREE.BufferGeometry();
        const positions = new Float32Array(burstCount * 3);

        for (let i = 0; i < burstCount; i++) {
            const i3 = i * 3;
            positions[i3] = 0;
            positions[i3 + 1] = 0;
            positions[i3 + 2] = 0;
        }

        burstGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const burstMaterial = new THREE.PointsMaterial({
            color: this.colors.rosePink,
            size: 0.2,
            transparent: true,
            opacity: 1,
            blending: THREE.AdditiveBlending
        });

        const burst = new THREE.Points(burstGeometry, burstMaterial);
        burst.userData.lifetime = 0;
        burst.userData.maxLifetime = 2;

        this.scene.add(burst);
        this.particleSystems.push(burst);
    }

    /**
     * Animation loop
     */
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());

        const deltaTime = this.clock.getDelta();
        const elapsedTime = this.clock.getElapsedTime();

        // Update controls
        this.controls.update();

        // Animate enchanted rose (pulsing glow)
        if (this.roseLight) {
            this.roseLight.intensity = 2 + Math.sin(elapsedTime * 2) * 0.5;
        }

        // Rotate rose slowly
        if (this.enchantedRose) {
            this.enchantedRose.rotation.y = elapsedTime * 0.2;
        }

        // Animate glass cloche shimmer
        if (this.glassCloche) {
            this.glassCloche.material.opacity = 0.15 + Math.sin(elapsedTime * 3) * 0.05;
        }

        // Animate candles (flickering)
        this.candles.forEach(candle => {
            if (candle.userData.light && candle.userData.flame) {
                const flicker = Math.sin(elapsedTime * 10 + candle.userData.flickerPhase) * 0.2;
                candle.userData.light.intensity = 0.5 + flicker;
                candle.userData.flame.scale.y = 1 + flicker * 0.3;
            }
        });

        // Animate floating objects (candelabra, book)
        this.enchantedObjects.forEach(obj => {
            if (obj.userData.floatPhase !== undefined) {
                obj.position.y += Math.sin(elapsedTime * 2 + obj.userData.floatPhase) * 0.001;
            }
        });

        // Animate clock hands
        this.enchantedObjects.forEach(obj => {
            if (obj.userData.minuteHand) {
                obj.userData.minuteHand.rotation.z = elapsedTime * 0.1;
                obj.userData.hourHand.rotation.z = elapsedTime * 0.01;
            }
        });

        // Animate rose petals falling
        if (this.rosePetalSystem) {
            const positions = this.rosePetalSystem.geometry.attributes.position.array;
            const velocities = this.rosePetalSystem.userData.velocities;

            for (let i = 0; i < positions.length; i += 3) {
                positions[i] += velocities[i];
                positions[i + 1] += velocities[i + 1];
                positions[i + 2] += velocities[i + 2];

                // Reset if fallen below floor
                if (positions[i + 1] < 0) {
                    positions[i] = (Math.random() - 0.5) * 10;
                    positions[i + 1] = 12;
                    positions[i + 2] = (Math.random() - 0.5) * 10;
                }
            }
            this.rosePetalSystem.geometry.attributes.position.needsUpdate = true;
        }

        // Animate sparkles (twinkling)
        if (this.sparkleSystem) {
            const sizes = this.sparkleSystem.geometry.attributes.size.array;
            for (let i = 0; i < sizes.length; i++) {
                sizes[i] = Math.abs(Math.sin(elapsedTime * 5 + i)) * 0.08;
            }
            this.sparkleSystem.geometry.attributes.size.needsUpdate = true;
        }

        // Animate mist (slow drift)
        if (this.mistSystem) {
            this.mistSystem.rotation.y = elapsedTime * 0.05;
        }

        // Animate product hotspots (pulsing)
        this.hotspots.forEach(hotspot => {
            if (hotspot.userData.ring && hotspot.userData.light) {
                const pulse = Math.sin(elapsedTime * 2 + hotspot.userData.pulsePhase);
                hotspot.userData.ring.scale.setScalar(1 + pulse * 0.1);
                hotspot.userData.light.intensity = 1 + pulse * 0.5;
            }
        });

        // Animate stained glass light intensity
        this.stainedGlassWindows.forEach(window => {
            if (window.userData.light) {
                window.userData.light.intensity = 2 + Math.sin(elapsedTime * 1.5) * 0.5;
            }
        });

        // Update particle burst effects
        this.particleSystems.forEach((system, index) => {
            if (system.userData.lifetime !== undefined) {
                system.userData.lifetime += deltaTime;

                if (system.userData.lifetime > system.userData.maxLifetime) {
                    this.scene.remove(system);
                    this.particleSystems.splice(index, 1);
                } else {
                    // Expand and fade
                    const progress = system.userData.lifetime / system.userData.maxLifetime;
                    system.scale.setScalar(1 + progress * 3);
                    system.material.opacity = 1 - progress;
                }
            }
        });

        // Render with post-processing
        this.composer.render();
    }

    /**
     * Dispose of scene resources
     */
    dispose() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }

        // Dispose geometries and materials
        this.scene.traverse((object) => {
            if (object.geometry) {
                object.geometry.dispose();
            }
            if (object.material) {
                if (Array.isArray(object.material)) {
                    object.material.forEach(material => material.dispose());
                } else {
                    object.material.dispose();
                }
            }
        });

        this.renderer.dispose();
        this.composer.dispose();
    }

    /**
     * Camera animation helpers
     */
    animateCameraTo(position, target, duration = 2000) {
        const startPos = this.camera.position.clone();
        const startTarget = this.controls.target.clone();
        const endPos = new THREE.Vector3(...position);
        const endTarget = new THREE.Vector3(...target);

        const startTime = Date.now();

        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Smooth easing
            const eased = progress < 0.5
                ? 2 * progress * progress
                : 1 - Math.pow(-2 * progress + 2, 2) / 2;

            this.camera.position.lerpVectors(startPos, endPos, eased);
            this.controls.target.lerpVectors(startTarget, endTarget, eased);

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        animate();
    }

    /**
     * Navigate to specific room sections
     */
    navigateToSection(section) {
        switch (section) {
            case 'rose':
                this.animateCameraTo([0, 3, 8], [0, 2, 0]);
                break;
            case 'ballroom':
                this.animateCameraTo([0, 5, 20], [0, 2, 0]);
                break;
            case 'mirror':
                this.animateCameraTo([0, 3, -10], [0, 3, -14]);
                break;
            case 'windows':
                this.animateCameraTo([20, 4, 0], [0, 3, 0]);
                break;
            default:
                this.animateCameraTo([0, 3, 15], [0, 2, 0]);
        }
    }
}

// Export for use in other modules
export default LoveHurtsScene;
