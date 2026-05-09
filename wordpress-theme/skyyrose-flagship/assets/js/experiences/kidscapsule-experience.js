/**
 * Kids Capsule Experience
 * Enchanted Cloud Garden — Rose Gold, Soft Pink & Pearl
 *
 * Scene: Dreamy floating garden with cloud platforms
 * - Soft pastel ground with rose-gold pathways
 * - Floating cloud platforms at varying heights
 * - Rose-gold star sparkle particle system
 * - Gentle bubble ascent animation
 * - Product pedestals with rose-gold rim glow
 */

class KidsCapsuleExperience extends SkyyRoseExperience {
    constructor(containerId, options) {
        super(containerId, {
            backgroundColor: 0x1a0f14,
            enablePostProcessing: true,
            enableParticles: true,
            cameraFov: 58,
            ...(options || {})
        });

        this.colors = {
            roseGold:  0xB76E79,
            softPink:  0xFFB6C1,
            pearl:     0xFFF5EE,
            lavender:  0xE6D5F0,
            deepRose:  0x8B3A47
        };

        this.starParticles  = null;
        this.bubbleParticles = null;
        this.clouds         = [];

        this.buildScene();
    }

    async buildScene() {
        this.setupLighting();
        this.createGround();
        this.createCloudPlatforms();
        this.createRoseGoldPathways();
        this.createProductPedestals();
        this.createStarParticles();
        this.createBubbleParticles();
    }

    setupLighting() {
        // Soft daylight — low intensity to keep dreamy mood
        const sunlight = new THREE.DirectionalLight(0xFFE8F0, 1.6);
        sunlight.position.set(8, 14, 6);
        sunlight.castShadow = true;
        sunlight.shadow.mapSize.width  = 2048;
        sunlight.shadow.mapSize.height = 2048;
        sunlight.shadow.camera.near   = 0.5;
        sunlight.shadow.camera.far    = 50;
        sunlight.shadow.camera.left   = -15;
        sunlight.shadow.camera.right  = 15;
        sunlight.shadow.camera.top    = 15;
        sunlight.shadow.camera.bottom = -15;
        this.scene.add(sunlight);

        // Warm rose-gold ambient
        const ambient = new THREE.AmbientLight(0xF9E0E8, 0.5);
        this.scene.add(ambient);

        // Hemisphere — sky pink / ground mauve
        const hemisphere = new THREE.HemisphereLight(0xFFB6C1, 0x3D1F28, 0.35);
        this.scene.add(hemisphere);

        // Rose-gold accent fills near centre
        const fill1 = new THREE.PointLight(this.colors.roseGold, 0.6, 10);
        fill1.position.set(-3, 3, -3);
        this.scene.add(fill1);

        const fill2 = new THREE.PointLight(this.colors.softPink, 0.5, 10);
        fill2.position.set(3, 3, -3);
        this.scene.add(fill2);
    }

    createGround() {
        const groundGeometry = new THREE.CircleGeometry(20, 64);
        const groundMaterial = new THREE.MeshStandardMaterial({
            color: 0x2a1520,
            roughness: 0.85,
            metalness: 0.05
        });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        this.scene.add(ground);

        // Pearl centre disc
        const centreGeometry = new THREE.CircleGeometry(2.5, 64);
        const centreMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.pearl,
            metalness: 0.4,
            roughness: 0.4
        });
        const centre = new THREE.Mesh(centreGeometry, centreMaterial);
        centre.rotation.x = -Math.PI / 2;
        centre.position.y = 0.01;
        this.scene.add(centre);

        // Rose-gold ring around centre
        const ringGeometry = new THREE.RingGeometry(2.5, 3, 64);
        const ringMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.roseGold,
            metalness: 0.75,
            roughness: 0.25,
            emissive: this.colors.roseGold,
            emissiveIntensity: 0.15,
            side: THREE.DoubleSide
        });
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.rotation.x = -Math.PI / 2;
        ring.position.y = 0.02;
        this.scene.add(ring);
    }

    createCloudPlatforms() {
        const cloudPositions = [
            { x:  5, y: 2.5, z: -4 },
            { x: -5, y: 1.8, z: -5 },
            { x:  6, y: 3.2, z:  3 },
            { x: -6, y: 2.0, z:  4 },
            { x:  0, y: 4.0, z: -8 }
        ];

        cloudPositions.forEach((pos) => {
            const cloud = this.createCloud();
            cloud.position.set(pos.x, pos.y, pos.z);
            this.clouds.push(cloud);
            this.scene.add(cloud);
        });
    }

    createCloud() {
        const cloudGroup = new THREE.Group();
        const cloudMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.pearl,
            transparent: true,
            opacity: 0.88,
            roughness: 1.0,
            metalness: 0.0
        });

        // Build cloud from overlapping spheres
        const blobData = [
            { r: 0.8, x:  0.0, y: 0,     z: 0 },
            { r: 0.6, x:  0.9, y: -0.15, z: 0 },
            { r: 0.6, x: -0.9, y: -0.15, z: 0 },
            { r: 0.5, x:  0.4, y:  0.3,  z: 0 },
            { r: 0.5, x: -0.4, y:  0.3,  z: 0 }
        ];

        blobData.forEach((b) => {
            const geo  = new THREE.SphereGeometry(b.r, 12, 12);
            const blob = new THREE.Mesh(geo, cloudMaterial);
            blob.position.set(b.x, b.y, b.z);
            blob.castShadow = false;
            blob.receiveShadow = true;
            cloudGroup.add(blob);
        });

        // Random scale variation so clouds feel organic
        const s = 0.7 + Math.random() * 0.5;
        cloudGroup.scale.setScalar(s);
        cloudGroup.userData.baseY    = cloudGroup.position.y;
        cloudGroup.userData.phaseOff = Math.random() * Math.PI * 2;

        return cloudGroup;
    }

    createRoseGoldPathways() {
        const pathMaterial = new THREE.MeshStandardMaterial({
            color: this.colors.roseGold,
            metalness: 0.6,
            roughness: 0.35,
            emissive: this.colors.roseGold,
            emissiveIntensity: 0.08
        });

        const pathCount = 4;
        for (let i = 0; i < pathCount; i++) {
            const angle = (i / pathCount) * Math.PI * 2;
            const geo  = new THREE.PlaneGeometry(0.7, 7);
            const path = new THREE.Mesh(geo, pathMaterial);
            path.rotation.x = -Math.PI / 2;
            path.position.set(Math.cos(angle) * 5, 0.03, Math.sin(angle) * 5);
            path.rotation.z = -angle + Math.PI / 2;
            path.receiveShadow = true;
            this.scene.add(path);
        }
    }

    createProductPedestals() {
        const pedestalPositions = [
            { x:  5, z:  5 },
            { x: -5, z:  5 },
            { x:  5, z: -5 },
            { x: -5, z: -5 }
        ];

        pedestalPositions.forEach((pos, index) => {
            this.createPedestal({
                position: new THREE.Vector3(pos.x, 0, pos.z),
                radius: 0.55,
                height: 1.1,
                color: this.colors.pearl,
                emissive: this.colors.roseGold
            });

            // Placeholder product shape — star-shaped using icosahedron
            const productGeometry = new THREE.IcosahedronGeometry(0.28, 1);
            const productMaterial = new THREE.MeshStandardMaterial({
                color: this.colors.roseGold,
                metalness: 0.55,
                roughness: 0.3,
                emissive: this.colors.roseGold,
                emissiveIntensity: 0.25
            });
            const product = new THREE.Mesh(productGeometry, productMaterial);
            product.position.set(pos.x, 1.45, pos.z);
            product.castShadow = true;
            product.userData.productIndex = index;
            product.userData.onClick = (obj) => {
                window.dispatchEvent(new CustomEvent('skyyrose:product-click', {
                    detail: { index: obj.userData.productIndex, collection: 'kids-capsule' }
                }));
            };
            this.interactiveObjects.push(product);
            this.scene.add(product);
        });
    }

    createStarParticles() {
        const count = 150;
        const geometry = new THREE.BufferGeometry();
        const positions  = new Float32Array(count * 3);
        const velocities = new Float32Array(count * 3);

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            positions[i3]     = (Math.random() - 0.5) * 22;
            positions[i3 + 1] = Math.random() * 9;
            positions[i3 + 2] = (Math.random() - 0.5) * 22;

            velocities[i3]     = (Math.random() - 0.5) * 0.008;
            velocities[i3 + 1] = 0.008 + Math.random() * 0.012;
            velocities[i3 + 2] = (Math.random() - 0.5) * 0.008;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.userData.velocities = velocities;

        const material = new THREE.PointsMaterial({
            color:       this.colors.roseGold,
            size:        0.06,
            transparent: true,
            opacity:     0.85,
            blending:    THREE.AdditiveBlending,
            depthWrite:  false
        });

        this.starParticles = new THREE.Points(geometry, material);
        this.scene.add(this.starParticles);
    }

    createBubbleParticles() {
        const count = 60;
        const geometry = new THREE.BufferGeometry();
        const positions  = new Float32Array(count * 3);
        const velocities = new Float32Array(count * 3);

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            positions[i3]     = (Math.random() - 0.5) * 16;
            positions[i3 + 1] = Math.random() * 5;
            positions[i3 + 2] = (Math.random() - 0.5) * 16;

            velocities[i3]     = (Math.random() - 0.5) * 0.005;
            velocities[i3 + 1] = 0.015 + Math.random() * 0.01;
            velocities[i3 + 2] = (Math.random() - 0.5) * 0.005;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.userData.velocities = velocities;

        const material = new THREE.PointsMaterial({
            color:       this.colors.softPink,
            size:        0.12,
            transparent: true,
            opacity:     0.5,
            blending:    THREE.AdditiveBlending,
            depthWrite:  false
        });

        this.bubbleParticles = new THREE.Points(geometry, material);
        this.scene.add(this.bubbleParticles);
    }

    update(delta) {
        const t = this.clock.elapsedTime;

        // Star drift upward, wrap at top
        if (this.starParticles) {
            const pos = this.starParticles.geometry.attributes.position.array;
            const vel = this.starParticles.geometry.userData.velocities;
            for (let i = 0; i < pos.length; i += 3) {
                pos[i]     += vel[i]     + Math.sin(t + i) * 0.001;
                pos[i + 1] += vel[i + 1];
                pos[i + 2] += vel[i + 2] + Math.cos(t + i) * 0.001;
                if (pos[i + 1] > 9) {
                    pos[i]     = (Math.random() - 0.5) * 22;
                    pos[i + 1] = 0;
                    pos[i + 2] = (Math.random() - 0.5) * 22;
                }
            }
            this.starParticles.geometry.attributes.position.needsUpdate = true;
        }

        // Bubble ascent, wrap at top
        if (this.bubbleParticles) {
            const pos = this.bubbleParticles.geometry.attributes.position.array;
            const vel = this.bubbleParticles.geometry.userData.velocities;
            for (let i = 0; i < pos.length; i += 3) {
                pos[i]     += vel[i];
                pos[i + 1] += vel[i + 1];
                pos[i + 2] += vel[i + 2];
                if (pos[i + 1] > 8) {
                    pos[i]     = (Math.random() - 0.5) * 16;
                    pos[i + 1] = 0;
                    pos[i + 2] = (Math.random() - 0.5) * 16;
                }
            }
            this.bubbleParticles.geometry.attributes.position.needsUpdate = true;
        }

        // Gentle cloud bob
        this.clouds.forEach((cloud) => {
            cloud.position.y = cloud.userData.baseY +
                Math.sin(t * 0.4 + cloud.userData.phaseOff) * 0.18;
        });

        // Slow product rotation on pedestals
        this.interactiveObjects.forEach((obj, idx) => {
            obj.rotation.y += delta * (0.2 + idx * 0.05);
        });
    }
}

// Export class — initialization owned by init-3d.js to prevent dual-init.
window.KidsCapsuleExperience = KidsCapsuleExperience;
