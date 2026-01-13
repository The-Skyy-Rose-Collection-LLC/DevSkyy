/**
 * Black Rose Collection Experience
 * Gothic Moonlit Garden - Dark Elegance
 *
 * Scene: Mysterious midnight garden under a full moon
 * - Black and silver roses throughout
 * - Iron arbors and gothic architecture
 * - Falling petals in moonlight
 * - Mist and fog effects
 * - Moonbeams illuminating product displays
 */

class BlackRoseExperience extends SkyyRoseExperience {
    constructor(containerId) {
        super(containerId, {
            backgroundColor: 0x050508,
            enablePostProcessing: true,
            enableParticles: true,
            cameraFov: 55
        });

        // Collection colors
        this.colors = {
            obsidian: 0x0a0a0a,
            moonlight: 0xc8c8dc,
            silver: 0xC0C0C0,
            darkRed: 0x8B0000,
            midnight: 0x191970
        };

        this.moon = null;
        this.fallingPetals = null;
        this.mistParticles = null;
        this.moonbeams = [];

        this.buildScene();
    }

    async buildScene() {
        this.setupLighting();
        this.createGround();
        this.createMoon();
        this.createIronArbors();
        this.createBlackRoses();
        this.createGothicElements();
        this.createProductPedestals();
        this.createFallingPetals();
        this.createMist();
        this.createMoonbeams();
    }

    setupLighting() {
        // Deep ambient for mystery
        const ambient = new THREE.AmbientLight(0x0a0a15, 0.1);
        this.scene.add(ambient);

        // Moonlight - main illumination
        const moonlight = new THREE.DirectionalLight(this.colors.moonlight, 0.6);
        moonlight.position.set(5, 20, -10);
        moonlight.castShadow = true;
        moonlight.shadow.mapSize.width = 2048;
        moonlight.shadow.mapSize.height = 2048;
        moonlight.shadow.camera.near = 5;
        moonlight.shadow.camera.far = 50;
        moonlight.shadow.camera.left = -15;
        moonlight.shadow.camera.right = 15;
        moonlight.shadow.camera.top = 15;
        moonlight.shadow.camera.bottom = -15;
        this.scene.add(moonlight);

        // Subtle colored rim lights
        const rimLight1 = new THREE.PointLight(this.colors.darkRed, 0.3, 15);
        rimLight1.position.set(-8, 3, -5);
        this.scene.add(rimLight1);

        const rimLight2 = new THREE.PointLight(this.colors.midnight, 0.3, 15);
        rimLight2.position.set(8, 3, -5);
        this.scene.add(rimLight2);
    }

    createGround() {
        // Dark grass/earth
        const groundGeometry = new THREE.PlaneGeometry(40, 40, 32, 32);

        // Add subtle height variation
        const positions = groundGeometry.attributes.position.array;
        for (let i = 0; i < positions.length; i += 3) {
            positions[i + 2] += Math.random() * 0.1;
        }
        groundGeometry.computeVertexNormals();

        const groundMaterial = new THREE.MeshStandardMaterial({
            color: 0x0a0f0a,
            roughness: 0.95,
            metalness: 0.05
        });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        this.scene.add(ground);

        // Stone pathway
        const pathMaterial = new THREE.MeshStandardMaterial({
            color: 0x2a2a2a,
            roughness: 0.8,
            metalness: 0.2
        });

        for (let i = -5; i <= 5; i++) {
            const stone = new THREE.Mesh(
                new THREE.BoxGeometry(0.8 + Math.random() * 0.3, 0.1, 0.6 + Math.random() * 0.2),
                pathMaterial
            );
            stone.position.set(
                (Math.random() - 0.5) * 0.3,
                0.05,
                i * 1.2 + (Math.random() - 0.5) * 0.2
            );
            stone.rotation.y = (Math.random() - 0.5) * 0.2;
            stone.receiveShadow = true;
            this.scene.add(stone);
        }
    }

    createMoon() {
        const moonGroup = new THREE.Group();

        // Moon sphere
        const moonGeometry = new THREE.SphereGeometry(3, 32, 32);
        const moonMaterial = new THREE.MeshBasicMaterial({
            color: this.colors.moonlight
        });
        const moon = new THREE.Mesh(moonGeometry, moonMaterial);
        moonGroup.add(moon);

        // Moon glow
        const glowGeometry = new THREE.SphereGeometry(4, 32, 32);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: this.colors.moonlight,
            transparent: true,
            opacity: 0.2,
            side: THREE.BackSide
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        moonGroup.add(glow);

        // Outer glow halo
        const haloGeometry = new THREE.RingGeometry(3.5, 6, 64);
        const haloMaterial = new THREE.MeshBasicMaterial({
            color: this.colors.moonlight,
            transparent: true,
            opacity: 0.1,
            side: THREE.DoubleSide
        });
        const halo = new THREE.Mesh(haloGeometry, haloMaterial);
        moonGroup.add(halo);

        moonGroup.position.set(5, 25, -30);
        this.moon = moonGroup;
        this.scene.add(moonGroup);
    }

    createIronArbors() {
        // Gothic iron arbors framing the path
        const arborPositions = [
            { x: 0, z: -4, rotation: 0 },
            { x: 0, z: 4, rotation: 0 }
        ];

        arborPositions.forEach(pos => {
            const arbor = this.createIronArbor();
            arbor.position.set(pos.x, 0, pos.z);
            arbor.rotation.y = pos.rotation;
            this.scene.add(arbor);
        });
    }

    createIronArbor() {
        const arborGroup = new THREE.Group();

        const ironMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a1a1a,
            metalness: 0.9,
            roughness: 0.4
        });

        // Left pillar
        const leftPillar = new THREE.Mesh(
            new THREE.CylinderGeometry(0.08, 0.1, 4, 8),
            ironMaterial
        );
        leftPillar.position.set(-2, 2, 0);
        leftPillar.castShadow = true;
        arborGroup.add(leftPillar);

        // Right pillar
        const rightPillar = new THREE.Mesh(
            new THREE.CylinderGeometry(0.08, 0.1, 4, 8),
            ironMaterial
        );
        rightPillar.position.set(2, 2, 0);
        rightPillar.castShadow = true;
        arborGroup.add(rightPillar);

        // Gothic arch
        const archCurve = new THREE.CatmullRomCurve3([
            new THREE.Vector3(-2, 4, 0),
            new THREE.Vector3(-1.5, 4.8, 0),
            new THREE.Vector3(-0.8, 5.3, 0),
            new THREE.Vector3(0, 5.5, 0),
            new THREE.Vector3(0.8, 5.3, 0),
            new THREE.Vector3(1.5, 4.8, 0),
            new THREE.Vector3(2, 4, 0)
        ]);
        const archGeometry = new THREE.TubeGeometry(archCurve, 30, 0.06, 8, false);
        const arch = new THREE.Mesh(archGeometry, ironMaterial);
        arborGroup.add(arch);

        // Decorative iron vines
        for (let i = 0; i < 8; i++) {
            const vine = this.createIronVine();
            const side = i % 2 === 0 ? -2 : 2;
            vine.position.set(side, 0.5 + i * 0.4, 0);
            vine.rotation.y = side > 0 ? Math.PI : 0;
            arborGroup.add(vine);
        }

        // Black roses on arbor
        for (let i = 0; i < 6; i++) {
            const t = i / 5;
            const point = archCurve.getPoint(t);
            const rose = this.createBlackRose();
            rose.position.copy(point);
            rose.position.z += (Math.random() - 0.5) * 0.2;
            rose.scale.setScalar(0.6 + Math.random() * 0.3);
            arborGroup.add(rose);
        }

        return arborGroup;
    }

    createIronVine() {
        const vineGroup = new THREE.Group();

        const ironMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a1a1a,
            metalness: 0.9,
            roughness: 0.4
        });

        // Curling vine
        const vineCurve = new THREE.CatmullRomCurve3([
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(0.3, 0.1, 0.1),
            new THREE.Vector3(0.5, 0.15, -0.1),
            new THREE.Vector3(0.8, 0.1, 0.05)
        ]);
        const vineGeometry = new THREE.TubeGeometry(vineCurve, 15, 0.02, 6, false);
        const vine = new THREE.Mesh(vineGeometry, ironMaterial);
        vineGroup.add(vine);

        // Leaves
        for (let i = 0; i < 3; i++) {
            const t = 0.3 + i * 0.25;
            const point = vineCurve.getPoint(t);
            const leaf = new THREE.Mesh(
                new THREE.SphereGeometry(0.04, 6, 6, 0, Math.PI),
                ironMaterial
            );
            leaf.position.copy(point);
            leaf.rotation.set(Math.random(), Math.random(), Math.random());
            leaf.scale.set(1, 0.3, 0.8);
            vineGroup.add(leaf);
        }

        return vineGroup;
    }

    createBlackRoses() {
        // Scattered black roses throughout the garden
        const rosePositions = [];

        // Generate random positions avoiding the center path
        for (let i = 0; i < 30; i++) {
            let x, z;
            do {
                x = (Math.random() - 0.5) * 18;
                z = (Math.random() - 0.5) * 18;
            } while (Math.abs(x) < 2 && Math.abs(z) < 6); // Avoid path

            rosePositions.push({ x, z });
        }

        rosePositions.forEach(pos => {
            const roseBush = this.createRoseBush();
            roseBush.position.set(pos.x, 0, pos.z);
            roseBush.rotation.y = Math.random() * Math.PI * 2;
            this.scene.add(roseBush);
        });
    }

    createRoseBush() {
        const bushGroup = new THREE.Group();

        // Create 2-4 roses per bush
        const roseCount = 2 + Math.floor(Math.random() * 3);

        for (let i = 0; i < roseCount; i++) {
            const rose = this.createBlackRose();
            rose.position.set(
                (Math.random() - 0.5) * 0.4,
                0.3 + Math.random() * 0.3,
                (Math.random() - 0.5) * 0.4
            );
            rose.scale.setScalar(0.4 + Math.random() * 0.3);
            bushGroup.add(rose);

            // Stem
            const stemGeometry = new THREE.CylinderGeometry(0.01, 0.015, rose.position.y, 6);
            const stemMaterial = new THREE.MeshStandardMaterial({
                color: 0x0a1a0a,
                roughness: 0.8
            });
            const stem = new THREE.Mesh(stemGeometry, stemMaterial);
            stem.position.set(rose.position.x, rose.position.y / 2, rose.position.z);
            bushGroup.add(stem);
        }

        // Leaves at base
        const leafMaterial = new THREE.MeshStandardMaterial({
            color: 0x0a150a,
            roughness: 0.8,
            side: THREE.DoubleSide
        });

        for (let i = 0; i < 5; i++) {
            const angle = (i / 5) * Math.PI * 2;
            const leaf = new THREE.Mesh(
                new THREE.CircleGeometry(0.15, 6),
                leafMaterial
            );
            leaf.position.set(
                Math.cos(angle) * 0.2,
                0.05,
                Math.sin(angle) * 0.2
            );
            leaf.rotation.set(-Math.PI / 3, angle, 0);
            bushGroup.add(leaf);
        }

        return bushGroup;
    }

    createBlackRose() {
        const roseGroup = new THREE.Group();

        // Decide color variation - mostly black, some silver, rare dark red
        const colorRoll = Math.random();
        let petalColor;
        if (colorRoll < 0.7) {
            petalColor = 0x0a0a0a; // Black
        } else if (colorRoll < 0.9) {
            petalColor = this.colors.silver; // Silver
        } else {
            petalColor = this.colors.darkRed; // Dark red
        }

        const petalMaterial = new THREE.MeshStandardMaterial({
            color: petalColor,
            metalness: 0.4,
            roughness: 0.3,
            side: THREE.DoubleSide
        });

        // Multiple layers of petals
        for (let layer = 0; layer < 4; layer++) {
            const petalCount = 5 + layer;
            const radius = 0.05 + layer * 0.06;

            for (let i = 0; i < petalCount; i++) {
                const angle = (i / petalCount) * Math.PI * 2 + layer * 0.3;
                const petalGeometry = new THREE.SphereGeometry(0.08, 6, 6, 0, Math.PI);
                const petal = new THREE.Mesh(petalGeometry, petalMaterial);

                petal.position.set(
                    Math.cos(angle) * radius,
                    0.15 - layer * 0.02,
                    Math.sin(angle) * radius
                );
                petal.rotation.set(
                    Math.PI / 4 + layer * 0.1,
                    angle,
                    0
                );
                petal.scale.set(1 + layer * 0.15, 0.3, 0.8);

                roseGroup.add(petal);
            }
        }

        return roseGroup;
    }

    createGothicElements() {
        // Gothic fence sections
        const fenceMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a1a1a,
            metalness: 0.9,
            roughness: 0.3
        });

        // Back fence
        for (let i = -4; i <= 4; i++) {
            const fencePost = new THREE.Mesh(
                new THREE.CylinderGeometry(0.05, 0.06, 2, 6),
                fenceMaterial
            );
            fencePost.position.set(i * 2, 1, -8);
            fencePost.castShadow = true;
            this.scene.add(fencePost);

            // Spear top
            const spear = new THREE.Mesh(
                new THREE.ConeGeometry(0.08, 0.3, 6),
                fenceMaterial
            );
            spear.position.set(i * 2, 2.15, -8);
            this.scene.add(spear);
        }

        // Horizontal bars
        for (let h = 0; h < 2; h++) {
            const bar = new THREE.Mesh(
                new THREE.BoxGeometry(16, 0.04, 0.04),
                fenceMaterial
            );
            bar.position.set(0, 0.5 + h * 0.8, -8);
            this.scene.add(bar);
        }

        // Gravestone-like monuments (corner pieces)
        const monumentPositions = [
            { x: -8, z: -6 },
            { x: 8, z: -6 }
        ];

        monumentPositions.forEach(pos => {
            const monument = this.createMonument();
            monument.position.set(pos.x, 0, pos.z);
            monument.rotation.y = pos.x > 0 ? -0.2 : 0.2;
            this.scene.add(monument);
        });
    }

    createMonument() {
        const monumentGroup = new THREE.Group();

        const stoneMaterial = new THREE.MeshStandardMaterial({
            color: 0x2a2a2a,
            roughness: 0.9,
            metalness: 0.1
        });

        // Base
        const base = new THREE.Mesh(
            new THREE.BoxGeometry(1.2, 0.3, 0.6),
            stoneMaterial
        );
        base.position.y = 0.15;
        base.castShadow = true;
        monumentGroup.add(base);

        // Main stone with rounded top
        const stoneGeometry = new THREE.CylinderGeometry(0.4, 0.5, 1.5, 16, 1, false, 0, Math.PI);
        const stone = new THREE.Mesh(stoneGeometry, stoneMaterial);
        stone.rotation.x = Math.PI / 2;
        stone.rotation.z = Math.PI / 2;
        stone.position.set(0, 1, 0);
        stone.castShadow = true;
        monumentGroup.add(stone);

        // Carved rose emblem
        const emblemGeometry = new THREE.TorusGeometry(0.15, 0.03, 8, 16);
        const emblemMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.darkRed,
            metalness: 0.5,
            roughness: 0.5
        });
        const emblem = new THREE.Mesh(emblemGeometry, emblemMaterial);
        emblem.position.set(0, 1.2, 0.25);
        monumentGroup.add(emblem);

        return monumentGroup;
    }

    createProductPedestals() {
        // 4 product displays with moonbeam spotlights
        const positions = [
            { x: -4, z: 0 },
            { x: 4, z: 0 },
            { x: -3, z: -5 },
            { x: 3, z: -5 }
        ];

        positions.forEach((pos, index) => {
            // Stone pedestal
            const pedestal = new THREE.Group();

            const stoneMaterial = new THREE.MeshStandardMaterial({
                color: 0x1a1a1a,
                roughness: 0.7,
                metalness: 0.3
            });

            const base = new THREE.Mesh(
                new THREE.CylinderGeometry(0.6, 0.7, 0.2, 8),
                stoneMaterial
            );
            base.position.y = 0.1;
            base.castShadow = true;
            pedestal.add(base);

            const column = new THREE.Mesh(
                new THREE.CylinderGeometry(0.35, 0.4, 1, 8),
                stoneMaterial
            );
            column.position.y = 0.7;
            column.castShadow = true;
            pedestal.add(column);

            const top = new THREE.Mesh(
                new THREE.CylinderGeometry(0.5, 0.35, 0.15, 8),
                stoneMaterial
            );
            top.position.y = 1.27;
            top.castShadow = true;
            pedestal.add(top);

            pedestal.position.set(pos.x, 0, pos.z);
            this.scene.add(pedestal);

            // Product placeholder
            const productGeometry = new THREE.BoxGeometry(0.4, 0.4, 0.4);
            const productMaterial = new THREE.MeshStandardMaterial({
                color: 0x0a0a0a,
                metalness: 0.5,
                roughness: 0.3
            });
            const product = new THREE.Mesh(productGeometry, productMaterial);
            product.position.set(pos.x, 1.55, pos.z);
            product.castShadow = true;
            product.userData.productIndex = index;
            product.userData.onClick = (obj) => {
                window.dispatchEvent(new CustomEvent('skyyrose:product-click', {
                    detail: { index: obj.userData.productIndex, collection: 'blackrose' }
                }));
            };
            this.interactiveObjects.push(product);
            this.scene.add(product);

            // Spotlight from moon direction
            const spotlight = new THREE.SpotLight(this.colors.moonlight, 0.8, 8, Math.PI / 8, 0.5);
            spotlight.position.set(pos.x + 2, 6, pos.z - 3);
            spotlight.target.position.set(pos.x, 1.5, pos.z);
            spotlight.castShadow = true;
            this.scene.add(spotlight);
            this.scene.add(spotlight.target);
        });
    }

    createFallingPetals() {
        // Black rose petals falling through moonlight
        const count = 80;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(count * 3);
        const rotations = new Float32Array(count * 3);
        const velocities = new Float32Array(count * 3);

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            positions[i3] = (Math.random() - 0.5) * 20;
            positions[i3 + 1] = Math.random() * 12;
            positions[i3 + 2] = (Math.random() - 0.5) * 20;

            rotations[i3] = Math.random() * Math.PI * 2;
            rotations[i3 + 1] = Math.random() * Math.PI * 2;
            rotations[i3 + 2] = Math.random() * Math.PI * 2;

            velocities[i3] = (Math.random() - 0.5) * 0.01;
            velocities[i3 + 1] = -0.02 - Math.random() * 0.02;
            velocities[i3 + 2] = (Math.random() - 0.5) * 0.01;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.userData.rotations = rotations;
        geometry.userData.velocities = velocities;

        // Black petal texture
        const petalTexture = this.createBlackPetalTexture();
        const material = new THREE.PointsMaterial({
            color: 0x1a1a1a,
            size: 0.12,
            map: petalTexture,
            transparent: true,
            opacity: 0.8,
            depthWrite: false
        });

        this.fallingPetals = new THREE.Points(geometry, material);
        this.scene.add(this.fallingPetals);
    }

    createBlackPetalTexture() {
        const canvas = document.createElement('canvas');
        canvas.width = 32;
        canvas.height = 32;
        const ctx = canvas.getContext('2d');

        // Draw petal shape
        ctx.beginPath();
        ctx.ellipse(16, 16, 14, 8, 0, 0, Math.PI * 2);
        ctx.fillStyle = '#1a1a1a';
        ctx.fill();

        // Subtle highlight
        ctx.beginPath();
        ctx.ellipse(14, 14, 8, 4, 0.3, 0, Math.PI * 2);
        ctx.fillStyle = '#2a2a2a';
        ctx.fill();

        return new THREE.CanvasTexture(canvas);
    }

    createMist() {
        // Low-lying mist/fog
        const count = 500;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(count * 3);

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            positions[i3] = (Math.random() - 0.5) * 30;
            positions[i3 + 1] = Math.random() * 1.5; // Stay low
            positions[i3 + 2] = (Math.random() - 0.5) * 30;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const material = new THREE.PointsMaterial({
            color: 0x4a4a5a,
            size: 0.3,
            transparent: true,
            opacity: 0.15,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        this.mistParticles = new THREE.Points(geometry, material);
        this.scene.add(this.mistParticles);
    }

    createMoonbeams() {
        // Volumetric moonbeam rays
        const beamCount = 3;

        for (let i = 0; i < beamCount; i++) {
            const beamGeometry = new THREE.ConeGeometry(2, 15, 16, 1, true);
            const beamMaterial = new THREE.MeshBasicMaterial({
                color: this.colors.moonlight,
                transparent: true,
                opacity: 0.03,
                side: THREE.DoubleSide,
                depthWrite: false
            });

            const beam = new THREE.Mesh(beamGeometry, beamMaterial);
            beam.position.set(
                -5 + i * 5,
                7.5,
                -3
            );
            beam.rotation.x = Math.PI + 0.3;
            beam.rotation.z = (Math.random() - 0.5) * 0.2;

            this.moonbeams.push(beam);
            this.scene.add(beam);
        }
    }

    update(delta) {
        const time = this.clock.elapsedTime;

        // Subtle moon glow pulse
        if (this.moon) {
            const glow = this.moon.children[1];
            if (glow) {
                glow.material.opacity = 0.15 + Math.sin(time * 0.3) * 0.05;
            }
        }

        // Falling petals
        if (this.fallingPetals) {
            const positions = this.fallingPetals.geometry.attributes.position.array;
            const velocities = this.fallingPetals.geometry.userData.velocities;
            const rotations = this.fallingPetals.geometry.userData.rotations;

            for (let i = 0; i < positions.length; i += 3) {
                // Swaying descent
                positions[i] += velocities[i] + Math.sin(time + i) * 0.005;
                positions[i + 1] += velocities[i + 1];
                positions[i + 2] += velocities[i + 2] + Math.cos(time + i) * 0.005;

                // Update rotation
                rotations[i] += 0.02;
                rotations[i + 1] += 0.01;

                // Reset when below ground
                if (positions[i + 1] < 0) {
                    positions[i] = (Math.random() - 0.5) * 20;
                    positions[i + 1] = 12;
                    positions[i + 2] = (Math.random() - 0.5) * 20;
                }
            }
            this.fallingPetals.geometry.attributes.position.needsUpdate = true;
        }

        // Drifting mist
        if (this.mistParticles) {
            const positions = this.mistParticles.geometry.attributes.position.array;

            for (let i = 0; i < positions.length; i += 3) {
                positions[i] += Math.sin(time * 0.2 + i) * 0.003;
                positions[i + 2] += Math.cos(time * 0.15 + i) * 0.003;

                // Keep in bounds
                if (Math.abs(positions[i]) > 15) positions[i] *= -0.9;
                if (Math.abs(positions[i + 2]) > 15) positions[i + 2] *= -0.9;
            }
            this.mistParticles.geometry.attributes.position.needsUpdate = true;
        }

        // Moonbeam shimmer
        this.moonbeams.forEach((beam, index) => {
            beam.material.opacity = 0.02 + Math.sin(time * 0.5 + index) * 0.01;
            beam.rotation.z += Math.sin(time * 0.1 + index) * 0.0005;
        });

        // Bloom intensity variation
        if (this.bloomPass) {
            this.bloomPass.strength = 0.4 + Math.sin(time * 0.3) * 0.1;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('blackrose-experience');
    if (container) {
        window.blackroseExperience = new BlackRoseExperience('blackrose-experience');
    }
});

window.BlackRoseExperience = BlackRoseExperience;
