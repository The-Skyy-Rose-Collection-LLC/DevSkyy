/**
 * Love Hurts Collection Experience
 * Enchanted Castle - Beauty & the Beast Theme
 *
 * Scene: Gothic castle interior with romantic darkness
 * - Floating candelabras with flickering flames
 * - Gothic mirrors reflecting the space
 * - Enchanted rose under glass dome (centerpiece)
 * - Rich burgundy and midnight blue atmosphere
 * - Dust motes and magical sparkles
 */

class LoveHurtsExperience extends SkyyRoseExperience {
    constructor(containerId) {
        super(containerId, {
            backgroundColor: 0x0a0510,
            enablePostProcessing: true,
            enableParticles: true,
            cameraFov: 50
        });

        // Collection colors
        this.colors = {
            burgundy: 0x722F37,
            midnight: 0x1a1a2e,
            crimson: 0xDC143C,
            gold: 0xFFD700,
            candleLight: 0xFF6B35
        };

        this.candles = [];
        this.enchantedRose = null;
        this.dustParticles = null;
        this.magicSparkles = null;

        this.buildScene();
    }

    async buildScene() {
        this.setupLighting();
        this.createFloor();
        this.createWalls();
        this.createEnchantedRose();
        this.createCandelabras();
        this.createMirrors();
        this.createProductPedestals();
        this.createDustParticles();
        this.createMagicSparkles();
    }

    setupLighting() {
        // Dim ambient light for mysterious atmosphere
        const ambient = new THREE.AmbientLight(0x1a0a1a, 0.15);
        this.scene.add(ambient);

        // Moonlight through windows
        const moonlight = new THREE.DirectionalLight(0x4444aa, 0.3);
        moonlight.position.set(-5, 10, -5);
        moonlight.castShadow = true;
        moonlight.shadow.mapSize.width = 2048;
        moonlight.shadow.mapSize.height = 2048;
        this.scene.add(moonlight);

        // Central spotlight on enchanted rose
        const roseSpotlight = new THREE.SpotLight(this.colors.crimson, 2, 10, Math.PI / 6, 0.5);
        roseSpotlight.position.set(0, 8, 0);
        roseSpotlight.target.position.set(0, 0, 0);
        roseSpotlight.castShadow = true;
        this.scene.add(roseSpotlight);
        this.scene.add(roseSpotlight.target);

        // Warm fill from candles
        const candleFill = new THREE.PointLight(this.colors.candleLight, 0.3, 20);
        candleFill.position.set(0, 3, 0);
        this.scene.add(candleFill);
    }

    createFloor() {
        // Dark marble floor with reflections
        const floorGeometry = new THREE.PlaneGeometry(30, 30);
        const floorMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a1a1a,
            roughness: 0.2,
            metalness: 0.8
        });
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        this.scene.add(floor);

        // Decorative rug
        const rugGeometry = new THREE.CircleGeometry(6, 64);
        const rugMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.burgundy,
            roughness: 0.9,
            metalness: 0.1
        });
        const rug = new THREE.Mesh(rugGeometry, rugMaterial);
        rug.rotation.x = -Math.PI / 2;
        rug.position.y = 0.01;
        this.scene.add(rug);

        // Gold trim on rug
        const trimGeometry = new THREE.RingGeometry(5.8, 6, 64);
        const trimMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.gold,
            metalness: 0.8,
            roughness: 0.2
        });
        const trim = new THREE.Mesh(trimGeometry, trimMaterial);
        trim.rotation.x = -Math.PI / 2;
        trim.position.y = 0.02;
        this.scene.add(trim);
    }

    createWalls() {
        const wallMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a1520,
            roughness: 0.8,
            metalness: 0.1
        });

        // Back wall
        const backWall = new THREE.Mesh(
            new THREE.PlaneGeometry(30, 15),
            wallMaterial
        );
        backWall.position.set(0, 7.5, -10);
        this.scene.add(backWall);

        // Side walls
        const leftWall = new THREE.Mesh(
            new THREE.PlaneGeometry(20, 15),
            wallMaterial
        );
        leftWall.position.set(-10, 7.5, 0);
        leftWall.rotation.y = Math.PI / 2;
        this.scene.add(leftWall);

        const rightWall = new THREE.Mesh(
            new THREE.PlaneGeometry(20, 15),
            wallMaterial
        );
        rightWall.position.set(10, 7.5, 0);
        rightWall.rotation.y = -Math.PI / 2;
        this.scene.add(rightWall);

        // Gothic arched windows (back wall)
        this.createGothicWindow(-5, 5, -9.9);
        this.createGothicWindow(5, 5, -9.9);
    }

    createGothicWindow(x, y, z) {
        const windowGroup = new THREE.Group();

        // Window frame
        const frameMaterial = new THREE.MeshStandardMaterial({
            color: 0x2a2a2a,
            metalness: 0.7,
            roughness: 0.3
        });

        // Arch shape using curve
        const curve = new THREE.CatmullRomCurve3([
            new THREE.Vector3(-1, 0, 0),
            new THREE.Vector3(-1, 2, 0),
            new THREE.Vector3(-0.7, 3, 0),
            new THREE.Vector3(0, 3.5, 0),
            new THREE.Vector3(0.7, 3, 0),
            new THREE.Vector3(1, 2, 0),
            new THREE.Vector3(1, 0, 0)
        ]);

        const tubeGeometry = new THREE.TubeGeometry(curve, 30, 0.1, 8, false);
        const frame = new THREE.Mesh(tubeGeometry, frameMaterial);
        windowGroup.add(frame);

        // Window glass with moonlight glow
        const glassGeometry = new THREE.PlaneGeometry(1.8, 3);
        const glassMaterial = new THREE.MeshStandardMaterial({
            color: 0x2244aa,
            transparent: true,
            opacity: 0.3,
            emissive: 0x112244,
            emissiveIntensity: 0.5,
            side: THREE.DoubleSide
        });
        const glass = new THREE.Mesh(glassGeometry, glassMaterial);
        glass.position.set(0, 1.5, 0.05);
        windowGroup.add(glass);

        // Moonlight beam through window
        const beamGeometry = new THREE.ConeGeometry(2, 8, 16, 1, true);
        const beamMaterial = new THREE.MeshBasicMaterial({
            color: 0x4466cc,
            transparent: true,
            opacity: 0.1,
            side: THREE.DoubleSide
        });
        const beam = new THREE.Mesh(beamGeometry, beamMaterial);
        beam.rotation.x = -Math.PI / 4;
        beam.position.set(0, 1, 4);
        windowGroup.add(beam);

        windowGroup.position.set(x, y, z);
        this.scene.add(windowGroup);
    }

    createEnchantedRose() {
        const roseGroup = new THREE.Group();

        // Ornate pedestal
        const pedestalBase = new THREE.Mesh(
            new THREE.CylinderGeometry(0.8, 1, 0.3, 8),
            new THREE.MeshStandardMaterial({
                color: 0x1a1a1a,
                metalness: 0.8,
                roughness: 0.2
            })
        );
        pedestalBase.position.y = 0.15;
        pedestalBase.castShadow = true;
        roseGroup.add(pedestalBase);

        const pedestalColumn = new THREE.Mesh(
            new THREE.CylinderGeometry(0.3, 0.4, 1.5, 8),
            new THREE.MeshStandardMaterial({
                color: this.colors.gold,
                metalness: 0.9,
                roughness: 0.1
            })
        );
        pedestalColumn.position.y = 1;
        pedestalColumn.castShadow = true;
        roseGroup.add(pedestalColumn);

        // Glass dome
        const domeGeometry = new THREE.SphereGeometry(1.2, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2);
        const domeMaterial = new THREE.MeshPhysicalMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.15,
            roughness: 0,
            metalness: 0.1,
            clearcoat: 1,
            clearcoatRoughness: 0,
            side: THREE.DoubleSide
        });
        const dome = new THREE.Mesh(domeGeometry, domeMaterial);
        dome.position.y = 1.8;
        roseGroup.add(dome);

        // The enchanted rose
        const rose = this.createDetailedRose();
        rose.position.y = 2;
        rose.scale.setScalar(0.5);
        this.enchantedRose = rose;
        roseGroup.add(rose);

        // Fallen petals on base
        for (let i = 0; i < 5; i++) {
            const petal = this.createFallenPetal();
            petal.position.set(
                (Math.random() - 0.5) * 0.6,
                1.85,
                (Math.random() - 0.5) * 0.6
            );
            petal.rotation.set(
                Math.random() * 0.3,
                Math.random() * Math.PI * 2,
                Math.random() * 0.3
            );
            roseGroup.add(petal);
        }

        // Glow effect
        const glowGeometry = new THREE.SphereGeometry(0.4, 16, 16);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: this.colors.crimson,
            transparent: true,
            opacity: 0.3
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        glow.position.y = 2.1;
        roseGroup.add(glow);

        // Point light from rose
        const roseLight = new THREE.PointLight(this.colors.crimson, 1.5, 5);
        roseLight.position.y = 2.1;
        roseGroup.add(roseLight);

        this.scene.add(roseGroup);
    }

    createDetailedRose() {
        const roseGroup = new THREE.Group();

        const petalMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.crimson,
            roughness: 0.3,
            metalness: 0.1,
            emissive: this.colors.crimson,
            emissiveIntensity: 0.2,
            side: THREE.DoubleSide
        });

        // Multiple layers of petals
        for (let layer = 0; layer < 4; layer++) {
            const petalCount = 5 + layer * 2;
            const radius = 0.1 + layer * 0.12;
            const height = 0.3 - layer * 0.05;

            for (let i = 0; i < petalCount; i++) {
                const angle = (i / petalCount) * Math.PI * 2 + layer * 0.2;
                const petalGeometry = new THREE.SphereGeometry(0.15, 8, 8, 0, Math.PI);
                const petal = new THREE.Mesh(petalGeometry, petalMaterial);

                petal.position.set(
                    Math.cos(angle) * radius,
                    height,
                    Math.sin(angle) * radius
                );
                petal.rotation.set(
                    Math.PI / 4 + layer * 0.15,
                    angle,
                    0
                );
                petal.scale.set(1 + layer * 0.2, 0.4, 1 + layer * 0.1);

                roseGroup.add(petal);
            }
        }

        // Stem
        const stemGeometry = new THREE.CylinderGeometry(0.02, 0.03, 0.8, 8);
        const stemMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a3a1a,
            roughness: 0.8
        });
        const stem = new THREE.Mesh(stemGeometry, stemMaterial);
        stem.position.y = -0.4;
        roseGroup.add(stem);

        return roseGroup;
    }

    createFallenPetal() {
        const petalGeometry = new THREE.CircleGeometry(0.08, 8);
        const petalMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.crimson,
            roughness: 0.5,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.8
        });
        return new THREE.Mesh(petalGeometry, petalMaterial);
    }

    createCandelabras() {
        // Floating candelabras around the room
        const positions = [
            { x: -4, y: 4, z: -4 },
            { x: 4, y: 4.5, z: -4 },
            { x: -5, y: 3.5, z: 2 },
            { x: 5, y: 4, z: 2 },
            { x: -3, y: 5, z: -6 },
            { x: 3, y: 4.8, z: -6 }
        ];

        positions.forEach((pos, index) => {
            const candelabra = this.createCandelabra(3 + (index % 2));
            candelabra.position.set(pos.x, pos.y, pos.z);
            candelabra.rotation.y = Math.random() * Math.PI * 2;
            candelabra.userData.floatOffset = Math.random() * Math.PI * 2;
            candelabra.userData.floatSpeed = 0.5 + Math.random() * 0.3;
            candelabra.userData.baseY = pos.y;
            this.candles.push(candelabra);
            this.scene.add(candelabra);
        });
    }

    createCandelabra(candleCount) {
        const group = new THREE.Group();

        const goldMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.gold,
            metalness: 0.9,
            roughness: 0.1
        });

        // Central column
        const column = new THREE.Mesh(
            new THREE.CylinderGeometry(0.04, 0.06, 0.5, 8),
            goldMaterial
        );
        group.add(column);

        // Candle arms
        for (let i = 0; i < candleCount; i++) {
            const angle = (i / candleCount) * Math.PI * 2;
            const armLength = 0.4;

            // Curved arm
            const armCurve = new THREE.CatmullRomCurve3([
                new THREE.Vector3(0, 0.1, 0),
                new THREE.Vector3(Math.cos(angle) * armLength * 0.5, 0.15, Math.sin(angle) * armLength * 0.5),
                new THREE.Vector3(Math.cos(angle) * armLength, 0.1, Math.sin(angle) * armLength)
            ]);
            const armGeometry = new THREE.TubeGeometry(armCurve, 10, 0.015, 6, false);
            const arm = new THREE.Mesh(armGeometry, goldMaterial);
            group.add(arm);

            // Candle holder
            const holder = new THREE.Mesh(
                new THREE.CylinderGeometry(0.04, 0.03, 0.08, 8),
                goldMaterial
            );
            holder.position.set(
                Math.cos(angle) * armLength,
                0.14,
                Math.sin(angle) * armLength
            );
            group.add(holder);

            // Candle
            const candle = new THREE.Mesh(
                new THREE.CylinderGeometry(0.025, 0.025, 0.15, 8),
                new THREE.MeshStandardMaterial({
                    color: 0xFFFAF0,
                    roughness: 0.9
                })
            );
            candle.position.set(
                Math.cos(angle) * armLength,
                0.25,
                Math.sin(angle) * armLength
            );
            group.add(candle);

            // Flame
            const flame = this.createFlame();
            flame.position.set(
                Math.cos(angle) * armLength,
                0.35,
                Math.sin(angle) * armLength
            );
            flame.userData.flameOffset = Math.random() * Math.PI * 2;
            group.add(flame);

            // Flame light
            const flameLight = new THREE.PointLight(this.colors.candleLight, 0.3, 3);
            flameLight.position.copy(flame.position);
            group.add(flameLight);
        }

        return group;
    }

    createFlame() {
        const flameGroup = new THREE.Group();

        // Inner flame (bright)
        const innerGeometry = new THREE.ConeGeometry(0.015, 0.05, 8);
        const innerMaterial = new THREE.MeshBasicMaterial({
            color: 0xFFFFAA,
            transparent: true,
            opacity: 0.9
        });
        const inner = new THREE.Mesh(innerGeometry, innerMaterial);
        flameGroup.add(inner);

        // Outer flame (orange glow)
        const outerGeometry = new THREE.ConeGeometry(0.025, 0.08, 8);
        const outerMaterial = new THREE.MeshBasicMaterial({
            color: this.colors.candleLight,
            transparent: true,
            opacity: 0.6
        });
        const outer = new THREE.Mesh(outerGeometry, outerMaterial);
        outer.position.y = 0.01;
        flameGroup.add(outer);

        return flameGroup;
    }

    createMirrors() {
        // Gothic mirrors on walls
        const mirrorPositions = [
            { x: -9.9, y: 4, z: 0, rotY: Math.PI / 2 },
            { x: 9.9, y: 4, z: 0, rotY: -Math.PI / 2 }
        ];

        mirrorPositions.forEach(pos => {
            const mirror = this.createGothicMirror();
            mirror.position.set(pos.x, pos.y, pos.z);
            mirror.rotation.y = pos.rotY;
            this.scene.add(mirror);
        });
    }

    createGothicMirror() {
        const mirrorGroup = new THREE.Group();

        const frameMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.gold,
            metalness: 0.9,
            roughness: 0.2
        });

        // Ornate frame
        const frameGeometry = new THREE.TorusGeometry(1.5, 0.1, 8, 64);
        const frame = new THREE.Mesh(frameGeometry, frameMaterial);
        mirrorGroup.add(frame);

        // Mirror surface
        const mirrorGeometry = new THREE.CircleGeometry(1.4, 32);
        const mirrorMaterial = new THREE.MeshPhysicalMaterial({
            color: 0x888899,
            metalness: 1,
            roughness: 0,
            clearcoat: 1
        });
        const mirrorSurface = new THREE.Mesh(mirrorGeometry, mirrorMaterial);
        mirrorSurface.position.z = 0.05;
        mirrorGroup.add(mirrorSurface);

        return mirrorGroup;
    }

    createProductPedestals() {
        // 4 product displays arranged around the enchanted rose
        const positions = [
            { x: -3, z: 3 },
            { x: 3, z: 3 },
            { x: -4, z: -2 },
            { x: 4, z: -2 }
        ];

        positions.forEach((pos, index) => {
            const pedestal = this.createPedestal({
                position: new THREE.Vector3(pos.x, 0, pos.z),
                radius: 0.5,
                height: 1,
                color: 0x1a1a1a,
                emissive: this.colors.burgundy
            });

            // Product placeholder
            const productGeometry = new THREE.BoxGeometry(0.4, 0.4, 0.4);
            const productMaterial = new THREE.MeshStandardMaterial({
                color: this.colors.burgundy,
                metalness: 0.3,
                roughness: 0.5
            });
            const product = new THREE.Mesh(productGeometry, productMaterial);
            product.position.set(pos.x, 1.3, pos.z);
            product.castShadow = true;
            product.userData.productIndex = index;
            product.userData.onClick = (obj) => {
                window.dispatchEvent(new CustomEvent('skyyrose:product-click', {
                    detail: { index: obj.userData.productIndex, collection: 'lovehurts' }
                }));
            };
            this.interactiveObjects.push(product);
            this.scene.add(product);
        });
    }

    createDustParticles() {
        // Floating dust motes in candlelight
        const count = 300;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(count * 3);
        const velocities = new Float32Array(count * 3);

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            positions[i3] = (Math.random() - 0.5) * 20;
            positions[i3 + 1] = Math.random() * 10;
            positions[i3 + 2] = (Math.random() - 0.5) * 20;

            velocities[i3] = (Math.random() - 0.5) * 0.005;
            velocities[i3 + 1] = (Math.random() - 0.5) * 0.002;
            velocities[i3 + 2] = (Math.random() - 0.5) * 0.005;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.userData.velocities = velocities;

        const material = new THREE.PointsMaterial({
            color: 0xFFE4B5,
            size: 0.02,
            transparent: true,
            opacity: 0.4,
            blending: THREE.AdditiveBlending
        });

        this.dustParticles = new THREE.Points(geometry, material);
        this.scene.add(this.dustParticles);
    }

    createMagicSparkles() {
        // Magical sparkles around the enchanted rose
        const count = 50;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(count * 3);

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            const angle = Math.random() * Math.PI * 2;
            const radius = 0.5 + Math.random() * 1.5;
            positions[i3] = Math.cos(angle) * radius;
            positions[i3 + 1] = 1.5 + Math.random() * 2;
            positions[i3 + 2] = Math.sin(angle) * radius;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const material = new THREE.PointsMaterial({
            color: 0xFFD700,
            size: 0.05,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending
        });

        this.magicSparkles = new THREE.Points(geometry, material);
        this.scene.add(this.magicSparkles);
    }

    update(delta) {
        const time = this.clock.elapsedTime;

        // Floating candelabras
        this.candles.forEach(candelabra => {
            const offset = candelabra.userData.floatOffset;
            const speed = candelabra.userData.floatSpeed;
            const baseY = candelabra.userData.baseY;

            candelabra.position.y = baseY + Math.sin(time * speed + offset) * 0.15;
            candelabra.rotation.y += delta * 0.1;

            // Flicker flames
            candelabra.children.forEach(child => {
                if (child.userData.flameOffset !== undefined) {
                    const flicker = 0.8 + Math.sin(time * 10 + child.userData.flameOffset) * 0.2;
                    child.scale.setScalar(flicker);
                }
            });
        });

        // Rotate enchanted rose slowly
        if (this.enchantedRose) {
            this.enchantedRose.rotation.y += delta * 0.3;
        }

        // Dust particle drift
        if (this.dustParticles) {
            const positions = this.dustParticles.geometry.attributes.position.array;
            const velocities = this.dustParticles.geometry.userData.velocities;

            for (let i = 0; i < positions.length; i += 3) {
                positions[i] += velocities[i] + Math.sin(time + i) * 0.001;
                positions[i + 1] += velocities[i + 1];
                positions[i + 2] += velocities[i + 2] + Math.cos(time + i) * 0.001;

                // Wrap around bounds
                if (Math.abs(positions[i]) > 10) positions[i] *= -0.9;
                if (positions[i + 1] > 10) positions[i + 1] = 0;
                if (positions[i + 1] < 0) positions[i + 1] = 10;
                if (Math.abs(positions[i + 2]) > 10) positions[i + 2] *= -0.9;
            }
            this.dustParticles.geometry.attributes.position.needsUpdate = true;
        }

        // Magic sparkles orbit
        if (this.magicSparkles) {
            this.magicSparkles.rotation.y += delta * 0.5;
            const positions = this.magicSparkles.geometry.attributes.position.array;

            for (let i = 0; i < positions.length; i += 3) {
                positions[i + 1] += Math.sin(time * 2 + i) * 0.01;
            }
            this.magicSparkles.geometry.attributes.position.needsUpdate = true;
        }

        // Bloom pulse effect
        if (this.bloomPass) {
            this.bloomPass.strength = 0.5 + Math.sin(time * 0.5) * 0.1;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('lovehurts-experience');
    if (container) {
        window.lovehurtsExperience = new LoveHurtsExperience('lovehurts-experience');
    }
});

window.LoveHurtsExperience = LoveHurtsExperience;
