/**
 * Signature Collection Experience
 * Rose Garden with Fountain - Crimson, Gold & Ivory
 *
 * Scene: Elegant rose garden at golden hour
 * - Central fountain with flowing water
 * - Golden pathways leading to product pedestals
 * - Crimson, gold, and ivory roses throughout
 * - Soft particle effects (rose petals floating)
 */

class SignatureExperience extends SkyyRoseExperience {
    constructor(containerId) {
        super(containerId, {
            backgroundColor: 0x1a1510,
            enablePostProcessing: true,
            enableParticles: true,
            cameraFov: 55
        });

        // Collection colors
        this.colors = {
            crimson: 0xDC143C,
            gold: 0xFFD700,
            ivory: 0xFFFFF0,
            rose: 0xB76E79
        };

        this.petalParticles = null;
        this.fountain = null;
        this.waterParticles = null;

        this.buildScene();
    }

    async buildScene() {
        this.setupLighting();
        this.createGround();
        this.createFountain();
        this.createPathways();
        this.createRoseArches();
        this.createProductPedestals();
        this.createPetalParticles();
        this.createAmbientParticles();
    }

    setupLighting() {
        // Golden hour sunlight
        const sunlight = new THREE.DirectionalLight(0xFFE4B5, 2);
        sunlight.position.set(10, 15, 5);
        sunlight.castShadow = true;
        sunlight.shadow.mapSize.width = 2048;
        sunlight.shadow.mapSize.height = 2048;
        sunlight.shadow.camera.near = 0.5;
        sunlight.shadow.camera.far = 50;
        sunlight.shadow.camera.left = -15;
        sunlight.shadow.camera.right = 15;
        sunlight.shadow.camera.top = 15;
        sunlight.shadow.camera.bottom = -15;
        this.scene.add(sunlight);

        // Warm ambient light
        const ambient = new THREE.AmbientLight(0xFFDAB9, 0.4);
        this.scene.add(ambient);

        // Soft hemisphere light for sky/ground color variation
        const hemisphere = new THREE.HemisphereLight(0x87CEEB, 0x3D2914, 0.3);
        this.scene.add(hemisphere);

        // Accent lights near roses
        const roseLight1 = new THREE.PointLight(this.colors.crimson, 0.5, 8);
        roseLight1.position.set(-4, 2, -4);
        this.scene.add(roseLight1);

        const roseLight2 = new THREE.PointLight(this.colors.gold, 0.5, 8);
        roseLight2.position.set(4, 2, -4);
        this.scene.add(roseLight2);
    }

    createGround() {
        // Main garden ground
        const groundGeometry = new THREE.CircleGeometry(20, 64);
        const groundMaterial = new THREE.MeshStandardMaterial({
            color: 0x2d4a2d,
            roughness: 0.9,
            metalness: 0.1
        });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        this.scene.add(ground);

        // Decorative center circle
        const centerCircleGeometry = new THREE.RingGeometry(2, 3, 64);
        const centerCircleMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.gold,
            metalness: 0.7,
            roughness: 0.3,
            side: THREE.DoubleSide
        });
        const centerCircle = new THREE.Mesh(centerCircleGeometry, centerCircleMaterial);
        centerCircle.rotation.x = -Math.PI / 2;
        centerCircle.position.y = 0.01;
        this.scene.add(centerCircle);
    }

    createFountain() {
        const fountainGroup = new THREE.Group();

        // Base pool
        const poolGeometry = new THREE.CylinderGeometry(2, 2.2, 0.5, 32);
        const stoneMaterial = new THREE.MeshStandardMaterial({
            color: 0xD4C4A8,
            roughness: 0.8,
            metalness: 0.1
        });
        const pool = new THREE.Mesh(poolGeometry, stoneMaterial);
        pool.position.y = 0.25;
        pool.castShadow = true;
        pool.receiveShadow = true;
        fountainGroup.add(pool);

        // Water surface
        const waterGeometry = new THREE.CircleGeometry(1.8, 32);
        const waterMaterial = new THREE.MeshStandardMaterial({
            color: 0x4FA4DE,
            transparent: true,
            opacity: 0.7,
            metalness: 0.3,
            roughness: 0.1
        });
        const water = new THREE.Mesh(waterGeometry, waterMaterial);
        water.rotation.x = -Math.PI / 2;
        water.position.y = 0.45;
        fountainGroup.add(water);

        // Center column
        const columnGeometry = new THREE.CylinderGeometry(0.15, 0.2, 1.5, 16);
        const column = new THREE.Mesh(columnGeometry, stoneMaterial);
        column.position.y = 1;
        column.castShadow = true;
        fountainGroup.add(column);

        // Rose sculpture on top
        const roseGeometry = new THREE.IcosahedronGeometry(0.3, 1);
        const roseMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.crimson,
            metalness: 0.6,
            roughness: 0.3,
            emissive: this.colors.crimson,
            emissiveIntensity: 0.2
        });
        const roseSculpture = new THREE.Mesh(roseGeometry, roseMaterial);
        roseSculpture.position.y = 2;
        roseSculpture.castShadow = true;
        fountainGroup.add(roseSculpture);

        // Water spray particles
        this.waterParticles = this.createWaterSpray();
        fountainGroup.add(this.waterParticles);

        this.fountain = fountainGroup;
        this.scene.add(fountainGroup);
    }

    createWaterSpray() {
        const count = 200;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(count * 3);
        const velocities = new Float32Array(count * 3);

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            const angle = Math.random() * Math.PI * 2;
            const radius = Math.random() * 0.1;

            positions[i3] = Math.cos(angle) * radius;
            positions[i3 + 1] = 1.8 + Math.random();
            positions[i3 + 2] = Math.sin(angle) * radius;

            velocities[i3] = Math.cos(angle) * 0.02;
            velocities[i3 + 1] = 0.05 + Math.random() * 0.03;
            velocities[i3 + 2] = Math.sin(angle) * 0.02;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.userData.velocities = velocities;
        geometry.userData.initialPositions = positions.slice();

        const material = new THREE.PointsMaterial({
            color: 0x88CCFF,
            size: 0.03,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending
        });

        return new THREE.Points(geometry, material);
    }

    createPathways() {
        // Golden pathways radiating from fountain
        const pathwayMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.gold,
            metalness: 0.5,
            roughness: 0.4
        });

        const pathCount = 4;
        for (let i = 0; i < pathCount; i++) {
            const angle = (i / pathCount) * Math.PI * 2 + Math.PI / 4;

            const pathGeometry = new THREE.PlaneGeometry(1, 8);
            const path = new THREE.Mesh(pathGeometry, pathwayMaterial);
            path.rotation.x = -Math.PI / 2;
            path.position.set(
                Math.cos(angle) * 6,
                0.02,
                Math.sin(angle) * 6
            );
            path.rotation.z = -angle + Math.PI / 2;
            path.receiveShadow = true;
            this.scene.add(path);
        }
    }

    createRoseArches() {
        // Rose arches at pathway entrances
        const archPositions = [
            { x: 8, z: 0, rotation: 0 },
            { x: -8, z: 0, rotation: Math.PI },
            { x: 0, z: 8, rotation: Math.PI / 2 },
            { x: 0, z: -8, rotation: -Math.PI / 2 }
        ];

        archPositions.forEach((pos, index) => {
            const arch = this.createArch(index % 3);
            arch.position.set(pos.x, 0, pos.z);
            arch.rotation.y = pos.rotation;
            this.scene.add(arch);
        });
    }

    createArch(colorVariant) {
        const archGroup = new THREE.Group();

        // Arch structure
        const archMaterial = new THREE.MeshStandardMaterial({
            color: 0x8B4513,
            roughness: 0.8,
            metalness: 0.2
        });

        // Left pillar
        const pillarGeometry = new THREE.CylinderGeometry(0.1, 0.1, 3, 8);
        const leftPillar = new THREE.Mesh(pillarGeometry, archMaterial);
        leftPillar.position.set(-1, 1.5, 0);
        leftPillar.castShadow = true;
        archGroup.add(leftPillar);

        // Right pillar
        const rightPillar = new THREE.Mesh(pillarGeometry, archMaterial);
        rightPillar.position.set(1, 1.5, 0);
        rightPillar.castShadow = true;
        archGroup.add(rightPillar);

        // Arch curve
        const curve = new THREE.CatmullRomCurve3([
            new THREE.Vector3(-1, 3, 0),
            new THREE.Vector3(-0.5, 3.5, 0),
            new THREE.Vector3(0, 3.7, 0),
            new THREE.Vector3(0.5, 3.5, 0),
            new THREE.Vector3(1, 3, 0)
        ]);
        const tubeGeometry = new THREE.TubeGeometry(curve, 20, 0.08, 8, false);
        const archCurve = new THREE.Mesh(tubeGeometry, archMaterial);
        archGroup.add(archCurve);

        // Roses on arch
        const roseColors = [this.colors.crimson, this.colors.ivory, this.colors.rose];
        const roseColor = roseColors[colorVariant];

        for (let i = 0; i < 12; i++) {
            const t = i / 11;
            const point = curve.getPoint(t);
            const rose = this.createRose(roseColor);
            rose.position.copy(point);
            rose.position.y += (Math.random() - 0.5) * 0.2;
            rose.rotation.set(
                Math.random() * 0.5,
                Math.random() * Math.PI * 2,
                Math.random() * 0.5
            );
            archGroup.add(rose);
        }

        return archGroup;
    }

    createRose(color) {
        const roseGroup = new THREE.Group();

        // Rose bloom (simplified geometric representation)
        const petalMaterial = new THREE.MeshStandardMaterial({
            color: color,
            roughness: 0.4,
            metalness: 0.1,
            side: THREE.DoubleSide
        });

        // Outer petals
        for (let i = 0; i < 5; i++) {
            const angle = (i / 5) * Math.PI * 2;
            const petalGeometry = new THREE.SphereGeometry(0.08, 8, 8, 0, Math.PI);
            const petal = new THREE.Mesh(petalGeometry, petalMaterial);
            petal.position.set(
                Math.cos(angle) * 0.06,
                0,
                Math.sin(angle) * 0.06
            );
            petal.rotation.set(Math.PI / 4, angle, 0);
            petal.scale.set(1, 0.6, 1);
            roseGroup.add(petal);
        }

        // Center
        const centerGeometry = new THREE.SphereGeometry(0.04, 8, 8);
        const center = new THREE.Mesh(centerGeometry, petalMaterial);
        roseGroup.add(center);

        roseGroup.scale.setScalar(0.8 + Math.random() * 0.4);
        return roseGroup;
    }

    createProductPedestals() {
        // 4 product pedestals around fountain
        const pedestalPositions = [
            { x: 5, z: 5 },
            { x: -5, z: 5 },
            { x: 5, z: -5 },
            { x: -5, z: -5 }
        ];

        pedestalPositions.forEach((pos, index) => {
            const pedestal = this.createPedestal({
                position: new THREE.Vector3(pos.x, 0, pos.z),
                radius: 0.6,
                height: 1.2,
                color: 0xFFFAF0,
                emissive: this.colors.gold
            });

            // Add product placeholder sphere
            const productGeometry = new THREE.BoxGeometry(0.5, 0.5, 0.5);
            const productMaterial = new THREE.MeshStandardMaterial({
                color: this.colors.rose,
                metalness: 0.3,
                roughness: 0.5
            });
            const product = new THREE.Mesh(productGeometry, productMaterial);
            product.position.set(pos.x, 1.5, pos.z);
            product.castShadow = true;
            product.userData.productIndex = index;
            product.userData.onClick = (obj) => {
                console.log(`Product ${obj.userData.productIndex} clicked`);
                // Trigger product modal
                window.dispatchEvent(new CustomEvent('skyyrose:product-click', {
                    detail: { index: obj.userData.productIndex, collection: 'signature' }
                }));
            };
            this.interactiveObjects.push(product);
            this.scene.add(product);
        });
    }

    createPetalParticles() {
        // Floating rose petals
        const count = 100;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(count * 3);
        const rotations = new Float32Array(count * 3);
        const velocities = new Float32Array(count * 3);

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            positions[i3] = (Math.random() - 0.5) * 20;
            positions[i3 + 1] = Math.random() * 8;
            positions[i3 + 2] = (Math.random() - 0.5) * 20;

            rotations[i3] = Math.random() * Math.PI * 2;
            rotations[i3 + 1] = Math.random() * Math.PI * 2;
            rotations[i3 + 2] = Math.random() * Math.PI * 2;

            velocities[i3] = (Math.random() - 0.5) * 0.01;
            velocities[i3 + 1] = -0.01 - Math.random() * 0.02;
            velocities[i3 + 2] = (Math.random() - 0.5) * 0.01;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.userData.rotations = rotations;
        geometry.userData.velocities = velocities;

        // Use point sprites for petals
        const petalTexture = this.createPetalTexture();
        const material = new THREE.PointsMaterial({
            color: this.colors.crimson,
            size: 0.15,
            map: petalTexture,
            transparent: true,
            opacity: 0.9,
            blending: THREE.NormalBlending,
            depthWrite: false
        });

        this.petalParticles = new THREE.Points(geometry, material);
        this.scene.add(this.petalParticles);
    }

    createPetalTexture() {
        const canvas = document.createElement('canvas');
        canvas.width = 32;
        canvas.height = 32;
        const ctx = canvas.getContext('2d');

        // Draw petal shape
        ctx.beginPath();
        ctx.ellipse(16, 16, 14, 8, 0, 0, Math.PI * 2);
        ctx.fillStyle = '#DC143C';
        ctx.fill();

        const texture = new THREE.CanvasTexture(canvas);
        return texture;
    }

    createAmbientParticles() {
        // Golden sparkles in the air
        this.sparkles = this.createParticles({
            count: 50,
            color: this.colors.gold,
            size: 0.03,
            area: { x: 16, y: 6, z: 16 },
            velocity: { x: 0, y: 0.005, z: 0 }
        });
    }

    update(delta) {
        // Animate water spray
        if (this.waterParticles) {
            const positions = this.waterParticles.geometry.attributes.position.array;
            const velocities = this.waterParticles.geometry.userData.velocities;
            const initial = this.waterParticles.geometry.userData.initialPositions;

            for (let i = 0; i < positions.length; i += 3) {
                // Apply gravity
                velocities[i + 1] -= 0.002;

                positions[i] += velocities[i];
                positions[i + 1] += velocities[i + 1];
                positions[i + 2] += velocities[i + 2];

                // Reset when below water
                if (positions[i + 1] < 0.5) {
                    positions[i] = initial[i];
                    positions[i + 1] = initial[i + 1];
                    positions[i + 2] = initial[i + 2];
                    velocities[i + 1] = 0.05 + Math.random() * 0.03;
                }
            }
            this.waterParticles.geometry.attributes.position.needsUpdate = true;
        }

        // Animate floating petals
        if (this.petalParticles) {
            const positions = this.petalParticles.geometry.attributes.position.array;
            const velocities = this.petalParticles.geometry.userData.velocities;
            const rotations = this.petalParticles.geometry.userData.rotations;

            for (let i = 0; i < positions.length; i += 3) {
                // Gentle swaying motion
                positions[i] += velocities[i] + Math.sin(this.clock.elapsedTime + i) * 0.002;
                positions[i + 1] += velocities[i + 1];
                positions[i + 2] += velocities[i + 2] + Math.cos(this.clock.elapsedTime + i) * 0.002;

                // Update rotation
                rotations[i] += 0.01;
                rotations[i + 1] += 0.02;

                // Reset when below ground
                if (positions[i + 1] < 0) {
                    positions[i] = (Math.random() - 0.5) * 20;
                    positions[i + 1] = 8;
                    positions[i + 2] = (Math.random() - 0.5) * 20;
                }
            }
            this.petalParticles.geometry.attributes.position.needsUpdate = true;
        }

        // Animate sparkles upward
        if (this.sparkles) {
            const positions = this.sparkles.geometry.attributes.position.array;
            for (let i = 0; i < positions.length; i += 3) {
                positions[i + 1] += 0.01;
                if (positions[i + 1] > 6) {
                    positions[i + 1] = 0;
                }
            }
            this.sparkles.geometry.attributes.position.needsUpdate = true;
        }

        // Gentle fountain rose sculpture rotation
        if (this.fountain) {
            const roseSculpture = this.fountain.children[3];
            if (roseSculpture) {
                roseSculpture.rotation.y += delta * 0.2;
            }
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('signature-experience');
    if (container) {
        window.signatureExperience = new SignatureExperience('signature-experience');
    }
});

window.SignatureExperience = SignatureExperience;
