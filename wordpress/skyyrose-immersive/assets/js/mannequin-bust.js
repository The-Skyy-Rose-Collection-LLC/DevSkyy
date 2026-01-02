/**
 * SkyyRose Mannequin Bust Generator
 * Creates a stylized mannequin bust for product display using Three.js geometry
 * Designed for elegant jewelry and clothing presentation
 */

class MannequinBust {
    constructor(options = {}) {
        this.color = options.color || 0xf5e6d3; // Elegant cream/ivory
        this.metalness = options.metalness || 0.1;
        this.roughness = options.roughness || 0.6;
        this.scale = options.scale || 1;
        this.style = options.style || 'elegant'; // 'elegant', 'modern', 'abstract'
    }

    /**
     * Creates a complete mannequin bust group
     * @returns {THREE.Group} The mannequin bust mesh group
     */
    create() {
        const group = new THREE.Group();
        group.name = 'mannequin-bust';

        // Material for the bust
        const bustMaterial = new THREE.MeshStandardMaterial({
            color: this.color,
            metalness: this.metalness,
            roughness: this.roughness,
            side: THREE.DoubleSide
        });

        // Create components based on style
        switch (this.style) {
            case 'modern':
                this._createModernBust(group, bustMaterial);
                break;
            case 'abstract':
                this._createAbstractBust(group, bustMaterial);
                break;
            default:
                this._createElegantBust(group, bustMaterial);
        }

        // Apply scale
        group.scale.set(this.scale, this.scale, this.scale);

        return group;
    }

    /**
     * Creates an elegant classical bust style
     */
    _createElegantBust(group, material) {
        // Neck - elongated cylinder with taper
        const neckGeometry = new THREE.CylinderGeometry(0.12, 0.15, 0.4, 32);
        const neck = new THREE.Mesh(neckGeometry, material);
        neck.position.y = 0.5;
        group.add(neck);

        // Head - stylized oval
        const headGeometry = new THREE.SphereGeometry(0.18, 32, 24);
        headGeometry.scale(0.85, 1.1, 0.9);
        const head = new THREE.Mesh(headGeometry, material);
        head.position.y = 0.85;
        group.add(head);

        // Shoulders - curved shape using lathe
        const shoulderPoints = [];
        for (let i = 0; i <= 10; i++) {
            const t = i / 10;
            const x = 0.5 * Math.sin(t * Math.PI * 0.5) + 0.15;
            const y = -t * 0.3;
            shoulderPoints.push(new THREE.Vector2(x, y));
        }
        const shoulderGeometry = new THREE.LatheGeometry(shoulderPoints, 32, 0, Math.PI * 2);
        const shoulders = new THREE.Mesh(shoulderGeometry, material);
        shoulders.position.y = 0.3;
        group.add(shoulders);

        // Chest/Torso base
        const torsoGeometry = new THREE.CylinderGeometry(0.35, 0.25, 0.5, 32);
        const torso = new THREE.Mesh(torsoGeometry, material);
        torso.position.y = -0.1;
        group.add(torso);

        // Base/Stand
        const baseGeometry = new THREE.CylinderGeometry(0.3, 0.35, 0.1, 32);
        const base = new THREE.Mesh(baseGeometry, material);
        base.position.y = -0.4;
        group.add(base);
    }

    /**
     * Creates a modern minimalist bust style
     */
    _createModernBust(group, material) {
        // Geometric modern style
        const neckGeometry = new THREE.CylinderGeometry(0.1, 0.12, 0.35, 6);
        const neck = new THREE.Mesh(neckGeometry, material);
        neck.position.y = 0.45;
        group.add(neck);

        // Head - faceted sphere
        const headGeometry = new THREE.IcosahedronGeometry(0.16, 1);
        headGeometry.scale(0.9, 1.1, 0.85);
        const head = new THREE.Mesh(headGeometry, material);
        head.position.y = 0.75;
        group.add(head);

        // Angular shoulders
        const shoulderGeometry = new THREE.BoxGeometry(0.9, 0.15, 0.35);
        const shoulders = new THREE.Mesh(shoulderGeometry, material);
        shoulders.position.y = 0.2;
        group.add(shoulders);

        // Torso - tapered box
        const torsoGeometry = new THREE.BoxGeometry(0.5, 0.4, 0.25);
        const torso = new THREE.Mesh(torsoGeometry, material);
        torso.position.y = -0.1;
        group.add(torso);

        // Base
        const baseGeometry = new THREE.BoxGeometry(0.4, 0.08, 0.3);
        const base = new THREE.Mesh(baseGeometry, material);
        base.position.y = -0.35;
        group.add(base);
    }

    /**
     * Creates an abstract artistic bust style
     */
    _createAbstractBust(group, material) {
        // Flowing abstract curves
        const curve = new THREE.CatmullRomCurve3([
            new THREE.Vector3(0, -0.4, 0),
            new THREE.Vector3(0.1, 0, 0.05),
            new THREE.Vector3(0.05, 0.3, 0),
            new THREE.Vector3(0, 0.5, -0.02),
            new THREE.Vector3(-0.02, 0.7, 0),
            new THREE.Vector3(0, 0.85, 0)
        ]);

        const tubeGeometry = new THREE.TubeGeometry(curve, 32, 0.12, 16, false);
        const tube = new THREE.Mesh(tubeGeometry, material);
        group.add(tube);

        // Abstract head
        const headGeometry = new THREE.TorusKnotGeometry(0.1, 0.04, 64, 8, 2, 3);
        const head = new THREE.Mesh(headGeometry, material);
        head.position.y = 0.95;
        head.rotation.x = Math.PI * 0.5;
        group.add(head);

        // Floating shoulder pieces
        const shoulderGeometry = new THREE.TorusGeometry(0.25, 0.05, 16, 32, Math.PI);
        const leftShoulder = new THREE.Mesh(shoulderGeometry, material);
        leftShoulder.position.set(-0.15, 0.25, 0);
        leftShoulder.rotation.z = Math.PI * 0.3;
        group.add(leftShoulder);

        const rightShoulder = new THREE.Mesh(shoulderGeometry, material);
        rightShoulder.position.set(0.15, 0.25, 0);
        rightShoulder.rotation.z = -Math.PI * 0.3;
        rightShoulder.rotation.y = Math.PI;
        group.add(rightShoulder);
    }

    /**
     * Creates a jewelry display necklace stand
     * Specialized for displaying necklaces and pendants
     */
    static createNecklaceStand(options = {}) {
        const group = new THREE.Group();
        group.name = 'necklace-stand';

        const color = options.color || 0x1a1a1a; // Dark elegant
        const material = new THREE.MeshStandardMaterial({
            color: color,
            metalness: 0.3,
            roughness: 0.4
        });

        // Curved neck form
        const neckPoints = [];
        for (let i = 0; i <= 20; i++) {
            const t = i / 20;
            const angle = t * Math.PI;
            const x = 0.15 * Math.sin(angle) * (1 - t * 0.3);
            const y = t * 0.6;
            neckPoints.push(new THREE.Vector2(x, y));
        }
        const neckGeometry = new THREE.LatheGeometry(neckPoints, 32);
        const neck = new THREE.Mesh(neckGeometry, material);
        neck.position.y = 0.2;
        group.add(neck);

        // Collar bone area - curved for necklace draping
        const collarCurve = new THREE.EllipseCurve(0, 0, 0.3, 0.15, 0, Math.PI, false);
        const collarPoints = collarCurve.getPoints(32);
        const collarShape = new THREE.Shape();
        collarShape.moveTo(collarPoints[0].x, collarPoints[0].y);
        for (const point of collarPoints) {
            collarShape.lineTo(point.x, point.y);
        }
        const collarGeometry = new THREE.ExtrudeGeometry(collarShape, {
            depth: 0.08,
            bevelEnabled: true,
            bevelThickness: 0.02,
            bevelSize: 0.02
        });
        const collar = new THREE.Mesh(collarGeometry, material);
        collar.rotation.x = -Math.PI * 0.3;
        collar.position.set(0, 0.15, 0.1);
        group.add(collar);

        // Base
        const baseGeometry = new THREE.CylinderGeometry(0.2, 0.25, 0.15, 32);
        const base = new THREE.Mesh(baseGeometry, material);
        base.position.y = -0.05;
        group.add(base);

        return group;
    }

    /**
     * Adds product attachment points to the bust
     * @param {THREE.Group} bust - The bust group to add attachment points to
     * @returns {Object} Object containing attachment point positions
     */
    static addAttachmentPoints(bust) {
        const attachments = {
            necklace: new THREE.Vector3(0, 0.35, 0.15),
            earringLeft: new THREE.Vector3(-0.15, 0.85, 0.05),
            earringRight: new THREE.Vector3(0.15, 0.85, 0.05),
            brooch: new THREE.Vector3(0, 0.1, 0.2),
            shoulderLeft: new THREE.Vector3(-0.4, 0.2, 0),
            shoulderRight: new THREE.Vector3(0.4, 0.2, 0)
        };

        // Add invisible markers for debugging/positioning
        const markerMaterial = new THREE.MeshBasicMaterial({
            color: 0xff0000,
            transparent: true,
            opacity: 0
        });
        const markerGeometry = new THREE.SphereGeometry(0.02, 8, 8);

        for (const [name, position] of Object.entries(attachments)) {
            const marker = new THREE.Mesh(markerGeometry, markerMaterial);
            marker.position.copy(position);
            marker.name = `attachment-${name}`;
            bust.add(marker);
        }

        return attachments;
    }
}

// Export for use in experience scripts
if (typeof window !== 'undefined') {
    window.MannequinBust = MannequinBust;
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MannequinBust;
}
