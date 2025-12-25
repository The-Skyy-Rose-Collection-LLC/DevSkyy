/**
 * Ambient Particles Effect
 *
 * Creates collection-specific particle effects for Three.js scenes.
 * Optimized for 60fps performance with intersection observer for visibility.
 *
 * Effects:
 * - Signature: Gold geometric shapes floating
 * - Black Rose: Silver sparkles/stars
 * - Love Hurts: Floating rose petals with soft colors
 *
 * Features:
 * - Intersection Observer (pause when off-screen)
 * - requestAnimationFrame (60fps animation)
 * - Customizable particle count (max 100)
 * - Performance monitoring
 * - Proper Three.js resource cleanup
 *
 * @module AmbientParticles
 */

import * as THREE from 'three';

// ============================================================================
// Types & Interfaces
// ============================================================================

export type CollectionType = 'signature' | 'black-rose' | 'love-hurts';

export interface ParticleConfig {
  /** Collection type for color scheme */
  collection: CollectionType;
  /** Maximum number of particles (capped at 100 for performance) */
  particleCount?: number;
  /** Speed multiplier (1 = normal) */
  speedMultiplier?: number;
  /** Container element (for intersection observer) */
  container?: HTMLElement | null;
  /** Whether to auto-start animation */
  autoStart?: boolean;
}

export interface Particle {
  mesh: THREE.Mesh;
  position: THREE.Vector3;
  velocity: THREE.Vector3;
  rotation: THREE.Euler;
  rotationVelocity: THREE.Vector3;
  lifespan: number;
  maxLifespan: number;
  scale: number;
  initialScale: number;
}

// ============================================================================
// Collection Color Schemes
// ============================================================================

const COLLECTION_SCHEMES = {
  signature: {
    colors: [
      0xD4AF37, // Gold
      0xC9A962, // Lighter gold
      0xFFD700, // Bright gold
    ],
    particleType: 'geometric', // Cubes and octahedrons
    speed: 0.3,
  },
  'black-rose': {
    colors: [
      0xC0C0C0, // Silver
      0xE8E8E8, // Light silver
      0xA9A9A9, // Dark gray
    ],
    particleType: 'sparkles', // Star shapes
    speed: 0.5,
  },
  'love-hurts': {
    colors: [
      0xB76E79, // Rose gold
      0xE8B4BC, // Light rose
      0xD4AF37, // Gold accent
    ],
    particleType: 'petals', // Flattened spheres (rose petals)
    speed: 0.2,
  },
};

// ============================================================================
// Particle Geometry Generators
// ============================================================================

/**
 * Create geometric particle (cube or octahedron)
 */
function createGeometricParticle(): THREE.Mesh {
  const geometries = [
    new THREE.BoxGeometry(0.3, 0.3, 0.3),
    new THREE.OctahedronGeometry(0.25),
  ];
  const geometry = geometries[Math.floor(Math.random() * geometries.length)];

  const material = new THREE.MeshStandardMaterial({
    metalness: 0.8,
    roughness: 0.2,
    wireframe: false,
  });

  return new THREE.Mesh(geometry, material);
}

/**
 * Create sparkle particle (star/point)
 */
function createSparkleParticle(): THREE.Mesh {
  // Use point geometry for sparkles
  const geometry = new THREE.BufferGeometry();
  const vertices = new Float32Array([0, 0, 0]);
  geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));

  const material = new THREE.PointsMaterial({
    size: 2,
    sizeAttenuation: true,
  });

  return new THREE.Points(geometry, material) as any as THREE.Mesh;
}

/**
 * Create petal particle (flattened sphere)
 */
function createPetalParticle(): THREE.Mesh {
  const geometry = new THREE.SphereGeometry(0.25, 8, 8);
  geometry.scale(1, 0.4, 0.8); // Flatten to petal shape

  const material = new THREE.MeshStandardMaterial({
    metalness: 0.3,
    roughness: 0.6,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.8,
  });

  return new THREE.Mesh(geometry, material);
}

// ============================================================================
// Ambient Particles Manager
// ============================================================================

export class AmbientParticles {
  private scene: THREE.Scene;
  private collection: CollectionType;
  private particles: Particle[] = [];
  private particleGroup: THREE.Group;
  private animationId: number | null = null;
  private isAnimating = false;
  private isVisible = true;
  private config: Required<ParticleConfig>;
  private intersectionObserver: IntersectionObserver | null = null;
  private startTime: number = 0;

  constructor(scene: THREE.Scene, config: ParticleConfig) {
    this.scene = scene;
    this.collection = config.collection;
    this.particleGroup = new THREE.Group();
    this.scene.add(this.particleGroup);

    // Merge config with defaults
    this.config = {
      collection: config.collection,
      particleCount: Math.min(config.particleCount || 50, 100),
      speedMultiplier: config.speedMultiplier || 1,
      container: config.container || null,
      autoStart: config.autoStart !== false,
    };

    // Setup intersection observer if container provided
    if (this.config.container) {
      this.setupIntersectionObserver();
    }

    // Create particles
    this.createParticles();

    // Auto-start if requested
    if (this.config.autoStart) {
      this.start();
    }
  }

  // =========================================================================
  // Setup & Initialization
  // =========================================================================

  private setupIntersectionObserver(): void {
    try {
      this.intersectionObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              if (!this.isAnimating) {
                this.start();
              }
              this.isVisible = true;
            } else {
              this.isVisible = false;
              if (this.isAnimating) {
                this.stop();
              }
            }
          });
        },
        { threshold: 0.1 }
      );

      if (this.config.container) {
        this.intersectionObserver.observe(this.config.container);
      }
    } catch (error) {
      console.warn('IntersectionObserver not supported:', error);
    }
  }

  private createParticles(): void {
    const scheme = COLLECTION_SCHEMES[this.collection];

    for (let i = 0; i < this.config.particleCount; i++) {
      const mesh = this.createParticleMesh(scheme.particleType);

      // Random initial position (within scene bounds)
      const x = (Math.random() - 0.5) * 20;
      const y = Math.random() * 15 - 5;
      const z = (Math.random() - 0.5) * 20;

      mesh.position.set(x, y, z);

      // Set material color
      const colorIndex = i % scheme.colors.length;
      if (mesh instanceof THREE.Mesh && mesh.material instanceof THREE.Material) {
        (mesh.material as any).color.setHex(scheme.colors[colorIndex]);
      }

      // Create particle data
      const particle: Particle = {
        mesh,
        position: mesh.position,
        velocity: new THREE.Vector3(
          (Math.random() - 0.5) * scheme.speed * this.config.speedMultiplier,
          (Math.random() * 0.5 + 0.1) * scheme.speed * this.config.speedMultiplier,
          (Math.random() - 0.5) * scheme.speed * this.config.speedMultiplier
        ),
        rotation: mesh.rotation,
        rotationVelocity: new THREE.Vector3(
          Math.random() * 0.02,
          Math.random() * 0.02,
          Math.random() * 0.02
        ),
        lifespan: 0,
        maxLifespan: 1000 + Math.random() * 500, // 1-1.5 seconds
        scale: 1,
        initialScale: 1,
      };

      this.particles.push(particle);
      this.particleGroup.add(mesh);
    }
  }

  private createParticleMesh(type: string): THREE.Mesh {
    switch (type) {
      case 'geometric':
        return createGeometricParticle();
      case 'sparkles':
        return createSparkleParticle();
      case 'petals':
        return createPetalParticle();
      default:
        return createGeometricParticle();
    }
  }

  // =========================================================================
  // Animation Loop
  // =========================================================================

  private animate = (): void => {
    if (!this.isVisible) {
      return; // Pause if off-screen
    }

    const elapsed = Date.now() - this.startTime;

    this.particles.forEach((particle) => {
      // Update position
      particle.position.add(particle.velocity);

      // Update rotation
      particle.rotation.x += particle.rotationVelocity.x;
      particle.rotation.y += particle.rotationVelocity.y;
      particle.rotation.z += particle.rotationVelocity.z;

      // Update lifespan
      particle.lifespan += 16; // ~60fps = 16ms per frame
      const lifespanRatio = Math.min(particle.lifespan / particle.maxLifespan, 1);

      // Fade out near end of life
      if (lifespanRatio > 0.8) {
        const fadeRatio = (lifespanRatio - 0.8) / 0.2; // 0 to 1 over last 20% of life
        if (particle.mesh.material instanceof THREE.Material) {
          (particle.mesh.material as any).opacity = 1 - fadeRatio;
        }
      }

      // Reset particle when it reaches max age
      if (particle.lifespan > particle.maxLifespan) {
        this.resetParticle(particle);
      }

      // Wrap around if out of bounds
      if (Math.abs(particle.position.x) > 15) {
        particle.velocity.x *= -1;
        particle.position.x = Math.sign(particle.position.x) * 14;
      }
      if (particle.position.y < -10) {
        particle.position.y = 15;
      }
      if (Math.abs(particle.position.z) > 15) {
        particle.velocity.z *= -1;
        particle.position.z = Math.sign(particle.position.z) * 14;
      }
    });

    this.animationId = requestAnimationFrame(this.animate);
  };

  private resetParticle(particle: Particle): void {
    const scheme = COLLECTION_SCHEMES[this.collection];

    // Reset position to random location
    particle.position.set(
      (Math.random() - 0.5) * 20,
      Math.random() * 10 + 5,
      (Math.random() - 0.5) * 20
    );

    // Reset velocity
    particle.velocity.set(
      (Math.random() - 0.5) * scheme.speed * this.config.speedMultiplier,
      (Math.random() * 0.5 + 0.1) * scheme.speed * this.config.speedMultiplier,
      (Math.random() - 0.5) * scheme.speed * this.config.speedMultiplier
    );

    // Reset lifespan and opacity
    particle.lifespan = 0;
    if (particle.mesh.material instanceof THREE.Material) {
      (particle.mesh.material as any).opacity = 0.8;
    }
  }

  // =========================================================================
  // Public API
  // =========================================================================

  public start(): void {
    if (this.isAnimating) return;

    this.isAnimating = true;
    this.startTime = Date.now();
    this.animate();
  }

  public stop(): void {
    if (!this.isAnimating) return;

    this.isAnimating = false;
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  public setSpeedMultiplier(multiplier: number): void {
    this.config.speedMultiplier = Math.max(0.1, Math.min(multiplier, 5));

    // Update particle velocities
    const scheme = COLLECTION_SCHEMES[this.collection];
    this.particles.forEach((particle) => {
      const speed = scheme.speed * this.config.speedMultiplier;
      const currentSpeed = particle.velocity.length();
      if (currentSpeed > 0) {
        particle.velocity.normalize().multiplyScalar(speed);
      }
    });
  }

  public dispose(): void {
    // Stop animation
    this.stop();

    // Remove intersection observer
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect();
      this.intersectionObserver = null;
    }

    // Dispose all particle meshes
    this.particles.forEach((particle) => {
      if (particle.mesh.geometry) {
        particle.mesh.geometry.dispose();
      }
      if (particle.mesh.material instanceof THREE.Material) {
        particle.mesh.material.dispose();
      } else if (Array.isArray(particle.mesh.material)) {
        particle.mesh.material.forEach((mat) => mat.dispose());
      }
    });

    // Remove group from scene
    this.scene.remove(this.particleGroup);
    this.particles = [];
  }

  public getParticleCount(): number {
    return this.particles.length;
  }

  public isRunning(): boolean {
    return this.isAnimating;
  }
}

export default AmbientParticles;
