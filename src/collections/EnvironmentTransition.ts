/**
 * EnvironmentTransition - Smooth Scene Transitions for SkyyRose Collections
 *
 * Handles animated transitions between:
 * - Collection 3D environments (BlackRose, LoveHurts, Signature)
 * - 3D environment to AR try-on mode
 * - Cross-collection navigation
 */

import * as THREE from 'three';
import gsap from 'gsap';

export type TransitionType =
  | 'fade'
  | 'dissolve'
  | 'zoom'
  | 'slide'
  | 'portal'
  | 'particles';

export type CollectionType = 'black_rose' | 'love_hurts' | 'signature';

export interface TransitionConfig {
  type: TransitionType;
  duration: number;
  easing?: string;
  color?: THREE.Color;
  onStart?: () => void;
  onComplete?: () => void;
  onProgress?: (progress: number) => void;
}

interface TransitionUniforms {
  uProgress: THREE.IUniform<number>;
  uColor: THREE.IUniform<THREE.Color>;
  uOpacity: THREE.IUniform<number>;
  uPattern: THREE.IUniform<number>;
  uTime: THREE.IUniform<number>;
  uResolution: THREE.IUniform<THREE.Vector2>;
}

interface TransitionOverlay {
  mesh: THREE.Mesh;
  material: THREE.ShaderMaterial & { uniforms: TransitionUniforms };
}

const COLLECTION_TRANSITION_COLORS: Record<CollectionType, THREE.Color> = {
  black_rose: new THREE.Color(0x0a0a0f),
  love_hurts: new THREE.Color(0x2d1f2d),
  signature: new THREE.Color(0x1a1a1a),
};

const DEFAULT_CONFIG: Partial<TransitionConfig> = {
  duration: 1.2,
  easing: 'power2.inOut',
};

export class EnvironmentTransition {
  private scene: THREE.Scene;
  private camera: THREE.Camera;
  private renderer: THREE.WebGLRenderer;

  private overlay: TransitionOverlay | null = null;
  private particleSystem: THREE.Points | null = null;
  private isTransitioning = false;
  private currentTimeline: gsap.core.Timeline | null = null;

  constructor(
    scene: THREE.Scene,
    camera: THREE.Camera,
    renderer: THREE.WebGLRenderer
  ) {
    this.scene = scene;
    this.camera = camera;
    this.renderer = renderer;
    this.createOverlay();
  }

  private createOverlay(): void {
    const geometry = new THREE.PlaneGeometry(2, 2);

    const material = new THREE.ShaderMaterial({
      uniforms: {
        uProgress: { value: 0 },
        uColor: { value: new THREE.Color(0x000000) },
        uOpacity: { value: 0 },
        uPattern: { value: 0 }, // 0=solid, 1=dissolve, 2=radial
        uTime: { value: 0 },
        uResolution: {
          value: new THREE.Vector2(
            this.renderer.domElement.width,
            this.renderer.domElement.height
          ),
        },
      },
      vertexShader: `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float uProgress;
        uniform vec3 uColor;
        uniform float uOpacity;
        uniform float uPattern;
        uniform float uTime;
        uniform vec2 uResolution;
        varying vec2 vUv;

        // Noise function for dissolve effect
        float random(vec2 st) {
          return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
        }

        float noise(vec2 st) {
          vec2 i = floor(st);
          vec2 f = fract(st);
          float a = random(i);
          float b = random(i + vec2(1.0, 0.0));
          float c = random(i + vec2(0.0, 1.0));
          float d = random(i + vec2(1.0, 1.0));
          vec2 u = f * f * (3.0 - 2.0 * f);
          return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
        }

        void main() {
          float alpha = 0.0;

          if (uPattern < 0.5) {
            // Solid fade
            alpha = uOpacity;
          } else if (uPattern < 1.5) {
            // Dissolve pattern
            float n = noise(vUv * 20.0 + uTime * 0.5);
            alpha = smoothstep(uProgress - 0.1, uProgress + 0.1, n) * uOpacity;
          } else {
            // Radial wipe
            vec2 center = vec2(0.5);
            float dist = distance(vUv, center) * 1.414;
            alpha = smoothstep(uProgress - 0.1, uProgress + 0.1, 1.0 - dist) * uOpacity;
          }

          gl_FragColor = vec4(uColor, alpha);
        }
      `,
      transparent: true,
      depthTest: false,
      depthWrite: false,
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.renderOrder = 9999;
    mesh.frustumCulled = false;
    mesh.visible = false;

    this.overlay = { mesh, material: material as THREE.ShaderMaterial & { uniforms: TransitionUniforms } };
  }

  async transition(
    config: Partial<TransitionConfig>,
    targetScene?: () => Promise<void>
  ): Promise<void> {
    if (this.isTransitioning) {
      console.warn('[EnvironmentTransition] Transition already in progress');
      return;
    }

    const finalConfig = { ...DEFAULT_CONFIG, ...config } as TransitionConfig;
    this.isTransitioning = true;

    finalConfig.onStart?.();

    try {
      switch (finalConfig.type) {
        case 'fade':
          await this.fadeTransition(finalConfig, targetScene);
          break;
        case 'dissolve':
          await this.dissolveTransition(finalConfig, targetScene);
          break;
        case 'zoom':
          await this.zoomTransition(finalConfig, targetScene);
          break;
        case 'slide':
          await this.slideTransition(finalConfig, targetScene);
          break;
        case 'portal':
          await this.portalTransition(finalConfig, targetScene);
          break;
        case 'particles':
          await this.particleTransition(finalConfig, targetScene);
          break;
        default:
          await this.fadeTransition(finalConfig, targetScene);
      }

      finalConfig.onComplete?.();
    } catch (error) {
      console.error('[EnvironmentTransition] Transition error:', error);
    } finally {
      this.isTransitioning = false;
    }
  }

  private async fadeTransition(
    config: TransitionConfig,
    targetScene?: () => Promise<void>
  ): Promise<void> {
    if (!this.overlay) return;

    const { material, mesh } = this.overlay;
    material.uniforms.uPattern.value = 0;
    material.uniforms.uColor.value = config.color || new THREE.Color(0x000000);
    mesh.visible = true;
    this.scene.add(mesh);

    return new Promise(resolve => {
      this.currentTimeline = gsap.timeline({
        onComplete: () => {
          mesh.visible = false;
          this.scene.remove(mesh);
          resolve();
        },
      });

      // Fade in
      this.currentTimeline.to(material.uniforms.uOpacity, {
        value: 1,
        duration: config.duration / 2,
        ease: config.easing ?? 'power2.inOut',
        onUpdate: () => {
          config.onProgress?.(material.uniforms.uOpacity.value * 0.5);
        },
      });

      // Execute scene change at midpoint
      if (targetScene) {
        this.currentTimeline.call(() => {
          void targetScene();
        });
      }

      // Fade out
      this.currentTimeline.to(material.uniforms.uOpacity, {
        value: 0,
        duration: config.duration / 2,
        ease: config.easing ?? 'power2.inOut',
        onUpdate: () => {
          config.onProgress?.(0.5 + (1 - material.uniforms.uOpacity.value) * 0.5);
        },
      });
    });
  }

  private async dissolveTransition(
    config: TransitionConfig,
    targetScene?: () => Promise<void>
  ): Promise<void> {
    if (!this.overlay) return;

    const { material, mesh } = this.overlay;
    material.uniforms.uPattern.value = 1;
    material.uniforms.uColor.value = config.color || new THREE.Color(0x000000);
    material.uniforms.uProgress.value = 0;
    material.uniforms.uOpacity.value = 1;
    mesh.visible = true;
    this.scene.add(mesh);

    const startTime = performance.now();
    const animate = () => {
      const elapsed = (performance.now() - startTime) / 1000;
      material.uniforms.uTime.value = elapsed;
    };

    const animationId = requestAnimationFrame(function loop() {
      animate();
      requestAnimationFrame(loop);
    });

    return new Promise(resolve => {
      this.currentTimeline = gsap.timeline({
        onComplete: () => {
          cancelAnimationFrame(animationId);
          mesh.visible = false;
          this.scene.remove(mesh);
          resolve();
        },
      });

      // Dissolve in
      this.currentTimeline.to(material.uniforms.uProgress, {
        value: 1,
        duration: config.duration / 2,
        ease: config.easing ?? 'power2.inOut',
        onUpdate: () => {
          config.onProgress?.(material.uniforms.uProgress.value * 0.5);
        },
      });

      // Execute scene change
      if (targetScene) {
        this.currentTimeline.call(() => {
          void targetScene();
        });
      }

      // Dissolve out
      this.currentTimeline.to(material.uniforms.uProgress, {
        value: 0,
        duration: config.duration / 2,
        ease: config.easing ?? 'power2.inOut',
        onUpdate: () => {
          config.onProgress?.(0.5 + (1 - material.uniforms.uProgress.value) * 0.5);
        },
      });
    });
  }

  private async zoomTransition(
    config: TransitionConfig,
    targetScene?: () => Promise<void>
  ): Promise<void> {
    const originalFov = (this.camera as THREE.PerspectiveCamera).fov;
    const targetFov = 10;

    return new Promise(resolve => {
      this.currentTimeline = gsap.timeline({ onComplete: resolve });

      // Zoom in (narrow FOV)
      this.currentTimeline.to(this.camera as THREE.PerspectiveCamera, {
        fov: targetFov,
        duration: config.duration / 2,
        ease: config.easing ?? 'power2.inOut',
        onUpdate: () => {
          (this.camera as THREE.PerspectiveCamera).updateProjectionMatrix();
          const progress = (originalFov - (this.camera as THREE.PerspectiveCamera).fov) /
                          (originalFov - targetFov);
          config.onProgress?.(progress * 0.5);
        },
      });

      // Execute scene change
      if (targetScene) {
        this.currentTimeline.call(() => {
          void targetScene();
        });
      }

      // Zoom out (restore FOV)
      this.currentTimeline.to(this.camera as THREE.PerspectiveCamera, {
        fov: originalFov,
        duration: config.duration / 2,
        ease: config.easing ?? 'power2.inOut',
        onUpdate: () => {
          (this.camera as THREE.PerspectiveCamera).updateProjectionMatrix();
          const progress = ((this.camera as THREE.PerspectiveCamera).fov - targetFov) /
                          (originalFov - targetFov);
          config.onProgress?.(0.5 + progress * 0.5);
        },
      });
    });
  }

  private async slideTransition(
    config: TransitionConfig,
    targetScene?: () => Promise<void>
  ): Promise<void> {
    const originalPosition = this.camera.position.clone();
    const slideOffset = new THREE.Vector3(50, 0, 0);

    return new Promise(resolve => {
      this.currentTimeline = gsap.timeline({ onComplete: resolve });

      // Slide out
      this.currentTimeline.to(this.camera.position, {
        x: originalPosition.x + slideOffset.x,
        duration: config.duration / 2,
        ease: config.easing ?? 'power2.inOut',
        onUpdate: () => {
          const progress = (this.camera.position.x - originalPosition.x) / slideOffset.x;
          config.onProgress?.(progress * 0.5);
        },
      });

      // Execute scene change and reset position to opposite side
      if (targetScene) {
        this.currentTimeline.call(() => {
          void targetScene().then(() => {
            this.camera.position.x = originalPosition.x - slideOffset.x;
          });
        });
      }

      // Slide in
      this.currentTimeline.to(this.camera.position, {
        x: originalPosition.x,
        duration: config.duration / 2,
        ease: config.easing ?? 'power2.inOut',
        onUpdate: () => {
          const progress = 1 - Math.abs(this.camera.position.x - originalPosition.x) / slideOffset.x;
          config.onProgress?.(0.5 + progress * 0.5);
        },
      });
    });
  }

  private async portalTransition(
    config: TransitionConfig,
    targetScene?: () => Promise<void>
  ): Promise<void> {
    if (!this.overlay) return;

    const { material, mesh } = this.overlay;
    material.uniforms.uPattern.value = 2; // Radial wipe
    material.uniforms.uColor.value = config.color || new THREE.Color(0x000000);
    material.uniforms.uProgress.value = 0;
    material.uniforms.uOpacity.value = 1;
    mesh.visible = true;
    this.scene.add(mesh);

    return new Promise(resolve => {
      this.currentTimeline = gsap.timeline({
        onComplete: () => {
          mesh.visible = false;
          this.scene.remove(mesh);
          resolve();
        },
      });

      // Portal close (radial wipe in)
      this.currentTimeline.to(material.uniforms.uProgress, {
        value: 1,
        duration: config.duration / 2,
        ease: 'power3.in',
        onUpdate: () => {
          config.onProgress?.(material.uniforms.uProgress.value * 0.5);
        },
      });

      // Execute scene change
      if (targetScene) {
        this.currentTimeline.call(() => {
          void targetScene();
        });
      }

      // Portal open (radial wipe out)
      this.currentTimeline.to(material.uniforms.uProgress, {
        value: 0,
        duration: config.duration / 2,
        ease: 'power3.out',
        onUpdate: () => {
          config.onProgress?.(0.5 + (1 - material.uniforms.uProgress.value) * 0.5);
        },
      });
    });
  }

  private async particleTransition(
    config: TransitionConfig,
    targetScene?: () => Promise<void>
  ): Promise<void> {
    const particleCount = 2000;
    const positions = new Float32Array(particleCount * 3);
    const velocities = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 20;

      velocities[i * 3] = (Math.random() - 0.5) * 2;
      velocities[i * 3 + 1] = (Math.random() - 0.5) * 2;
      velocities[i * 3 + 2] = (Math.random() - 0.5) * 2;

      sizes[i] = Math.random() * 0.1 + 0.02;
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    const material = new THREE.PointsMaterial({
      color: config.color || new THREE.Color(0xffffff),
      size: 0.05,
      transparent: true,
      opacity: 0,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    this.particleSystem = new THREE.Points(geometry, material);
    this.scene.add(this.particleSystem);

    return new Promise(resolve => {
      this.currentTimeline = gsap.timeline({
        onComplete: () => {
          if (this.particleSystem) {
            this.scene.remove(this.particleSystem);
            this.particleSystem.geometry.dispose();
            (this.particleSystem.material as THREE.Material).dispose();
            this.particleSystem = null;
          }
          resolve();
        },
      });

      // Particles fade in and disperse
      this.currentTimeline.to(material, {
        opacity: 1,
        duration: config.duration / 3,
        ease: 'power2.in',
      });

      // Execute scene change at midpoint
      if (targetScene) {
        this.currentTimeline.call(() => {
          void targetScene();
        }, [], config.duration / 2);
      }

      // Particles converge and fade out
      this.currentTimeline.to(material, {
        opacity: 0,
        duration: config.duration / 3,
        ease: 'power2.out',
        delay: config.duration / 6,
      });
    });
  }

  async transitionToAR(containerElement: HTMLElement): Promise<void> {
    await this.transition(
      {
        type: 'portal',
        duration: 0.8,
        color: new THREE.Color(0x000000),
      },
      async () => {
        // Hide 3D canvas, show AR container
        this.renderer.domElement.style.opacity = '0';
        containerElement.style.opacity = '1';
      }
    );
  }

  async transitionFromAR(containerElement: HTMLElement): Promise<void> {
    await this.transition(
      {
        type: 'portal',
        duration: 0.8,
        color: new THREE.Color(0x000000),
      },
      async () => {
        // Hide AR container, show 3D canvas
        containerElement.style.opacity = '0';
        this.renderer.domElement.style.opacity = '1';
      }
    );
  }

  async transitionToCollection(
    _fromCollection: CollectionType,
    toCollection: CollectionType,
    loadNewScene: () => Promise<void>
  ): Promise<void> {
    const transitionColor = COLLECTION_TRANSITION_COLORS[toCollection];

    await this.transition(
      {
        type: 'dissolve',
        duration: 1.5,
        color: transitionColor,
      },
      loadNewScene
    );
  }

  cancel(): void {
    if (this.currentTimeline) {
      this.currentTimeline.kill();
      this.currentTimeline = null;
    }

    if (this.overlay) {
      this.overlay.mesh.visible = false;
      this.scene.remove(this.overlay.mesh);
    }

    if (this.particleSystem) {
      this.scene.remove(this.particleSystem);
      this.particleSystem.geometry.dispose();
      (this.particleSystem.material as THREE.Material).dispose();
      this.particleSystem = null;
    }

    this.isTransitioning = false;
  }

  dispose(): void {
    this.cancel();

    if (this.overlay) {
      this.overlay.mesh.geometry.dispose();
      this.overlay.material.dispose();
      this.overlay = null;
    }
  }

  get transitioning(): boolean {
    return this.isTransitioning;
  }
}

export default EnvironmentTransition;
