/**
 * Hotspot System
 * Reusable product hotspot interaction system for Three.js scenes
 */

import * as THREE from 'three';

export class HotspotSystem {
    constructor(scene, camera, renderer) {
        this.scene = scene;
        this.camera = camera;
        this.renderer = renderer;

        this.hotspots = [];
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        this.hoveredHotspot = null;
        this.callbacks = {
            onHover: null,
            onClick: null,
            onHoverEnd: null
        };

        this.bindEvents();
    }

    /**
     * Add a hotspot to the system
     */
    addHotspot(mesh, data = {}) {
        const hotspot = {
            mesh,
            data,
            isHovered: false
        };

        this.hotspots.push(hotspot);
        return hotspot;
    }

    /**
     * Remove a hotspot
     */
    removeHotspot(hotspot) {
        const index = this.hotspots.indexOf(hotspot);
        if (index > -1) {
            this.hotspots.splice(index, 1);
        }
    }

    /**
     * Set callback functions
     */
    on(event, callback) {
        if (Object.prototype.hasOwnProperty.call(this.callbacks, `on${event.charAt(0).toUpperCase() + event.slice(1)}`)) {
            this.callbacks[`on${event.charAt(0).toUpperCase() + event.slice(1)}`] = callback;
        }
    }

    /**
     * Bind mouse events
     */
    bindEvents() {
        this.renderer.domElement.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.renderer.domElement.addEventListener('click', this.onClick.bind(this));
    }

    /**
     * Handle mouse move
     */
    onMouseMove(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);

        const meshes = this.hotspots.map(h => h.mesh);
        const intersects = this.raycaster.intersectObjects(meshes, true);

        // Reset previous hover
        if (this.hoveredHotspot && intersects.length === 0) {
            this.hoveredHotspot.isHovered = false;
            if (this.callbacks.onHoverEnd) {
                this.callbacks.onHoverEnd(this.hoveredHotspot);
            }
            this.hoveredHotspot = null;
            this.renderer.domElement.style.cursor = 'default';
        }

        // Check for new hover
        if (intersects.length > 0) {
            const hotspot = this.hotspots.find(h => {
                return h.mesh === intersects[0].object || h.mesh.children.includes(intersects[0].object);
            });

            if (hotspot && hotspot !== this.hoveredHotspot) {
                if (this.hoveredHotspot) {
                    this.hoveredHotspot.isHovered = false;
                    if (this.callbacks.onHoverEnd) {
                        this.callbacks.onHoverEnd(this.hoveredHotspot);
                    }
                }

                hotspot.isHovered = true;
                this.hoveredHotspot = hotspot;
                this.renderer.domElement.style.cursor = 'pointer';

                if (this.callbacks.onHover) {
                    this.callbacks.onHover(hotspot);
                }
            }
        }
    }

    /**
     * Handle click
     */
    onClick() {
        if (this.hoveredHotspot && this.callbacks.onClick) {
            this.callbacks.onClick(this.hoveredHotspot);
        }
    }

    /**
     * Update hotspot states (call in animation loop)
     */
    update() {
        // Can be used for continuous animations
        this.hotspots.forEach(hotspot => {
            if (hotspot.isHovered) {
                // Apply hover effects
            }
        });
    }

    /**
     * Dispose
     */
    dispose() {
        this.renderer.domElement.removeEventListener('mousemove', this.onMouseMove);
        this.renderer.domElement.removeEventListener('click', this.onClick);
        this.hotspots = [];
    }
}

export default HotspotSystem;
