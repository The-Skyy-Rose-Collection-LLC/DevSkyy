/**
 * SkyyRose Collection Experiences
 *
 * Immersive 3D landing pages for each SkyyRose collection.
 *
 * @author DevSkyy Platform Team
 * @version 2.0.0 - Production-grade with model loading and performance monitoring
 */

// Base Class & Production Utilities
export { BaseCollectionExperience } from './BaseCollectionExperience.js';
export type {
  BaseProduct,
  BaseExperienceConfig,
  ExperienceState,
  LifecycleEvent,
  LifecycleHandler,
} from './BaseCollectionExperience.js';

export * from './ProductionHandlers.js';

// Collection Experiences
export { BlackRoseExperience } from './BlackRoseExperience.js';
export type {
  BlackRoseProduct,
  BlackRoseConfig,
  ProductCardData,
  ProductClickHandler,
  EasterEggHandler,
} from './BlackRoseExperience.js';

export { SignatureExperience } from './SignatureExperience.js';
export type {
  SignatureProduct,
  SignatureConfig,
  CategorySelectHandler,
  ProductSelectHandler,
} from './SignatureExperience.js';

export { LoveHurtsExperience } from './LoveHurtsExperience.js';
export type {
  LoveHurtsProduct,
  LoveHurtsConfig,
  HeroInteractionHandler,
  MirrorClickHandler,
  FloorSpotlightHandler,
} from './LoveHurtsExperience.js';

// Existing experiences
export { ShowroomExperience } from './ShowroomExperience.js';
export { default as RunwayExperience } from './RunwayExperience.js';

// AR Try-On & Transitions
export { ARTryOnViewer } from './ARTryOnViewer.js';
export type { ARProduct, ARTryOnConfig } from './ARTryOnViewer.js';

export { WebXRARViewer, createBestARViewer } from './WebXRARViewer.js';
export type { WebXRProduct, WebXRConfig } from './WebXRARViewer.js';

export { EnvironmentTransition } from './EnvironmentTransition.js';
export type { TransitionType, TransitionConfig, CollectionType as TransitionCollectionType } from './EnvironmentTransition.js';

// WooCommerce Integration
export { WooCommerceProductLoader, getProductLoader, initProductLoader } from './WooCommerceProductLoader.js';
export type {
  WooCommerceProduct,
  WooCommerceVariation,
  ProductLoaderConfig,
} from './WooCommerceProductLoader.js';

// ============================================================================
// Collection3DExperienceSpec - Unified schema for all collection experiences
// ============================================================================

export type CollectionType = 'black_rose' | 'signature' | 'love_hurts' | 'showroom' | 'runway';

export interface Collection3DExperienceSpec {
  /** Collection identifier */
  collection: CollectionType;

  /** Experience configuration */
  config?: {
    backgroundColor?: number;
    enableBloom?: boolean;
    bloomStrength?: number;
    enableDepthOfField?: boolean;
    particleCount?: number;
    [key: string]: unknown;
  };

  /** Products to display (optional) */
  products?: Array<{
    id: string;
    name: string;
    price?: number;
    modelUrl?: string;
    thumbnailUrl?: string;
    position?: [number, number, number] | { x: number; y: number; z: number };
    [key: string]: unknown;
  }>;

  /** Interactive features (optional) */
  interactivity?: {
    enableProductCards?: boolean;
    enableCategoryNavigation?: boolean;
    enableSpatialAudio?: boolean;
    enableARPreview?: boolean;
    cursorSpotlight?: boolean;
  };

  /** Responsive fallback (optional) */
  fallback?: {
    enable2DParallax?: boolean;
    lowPerformanceThreshold?: number; // FPS
  };
}

// ============================================================================
// Experience Factory
// ============================================================================

import { BlackRoseExperience as BRE } from './BlackRoseExperience.js';
import { SignatureExperience as SE } from './SignatureExperience.js';
import { LoveHurtsExperience as LHE } from './LoveHurtsExperience.js';
import { ShowroomExperience as SRE } from './ShowroomExperience.js';
import RunwayExperience from './RunwayExperience.js';

export type CollectionExperience = BRE | SE | LHE | SRE | typeof RunwayExperience.prototype;

export function createCollectionExperience(
  container: HTMLElement,
  spec: Collection3DExperienceSpec
): CollectionExperience {
  switch (spec.collection) {
    case 'black_rose':
      return new BRE(container, spec.config);
    case 'signature':
      return new SE(container, spec.config);
    case 'love_hurts':
      return new LHE(container, spec.config);
    case 'showroom':
      return new SRE(container, spec.config);
    case 'runway':
      return new RunwayExperience(container, spec.config);
    default:
      throw new Error(`Unknown collection type: ${spec.collection}`);
  }
}
