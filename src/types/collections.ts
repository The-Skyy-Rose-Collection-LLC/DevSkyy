/**
 * Type definitions for SkyyRose collections
 */

/**
 * Collection theme configuration
 */
export interface CollectionTheme {
  /** Primary brand color */
  primaryColor: string;

  /** Background color */
  backgroundColor: string;

  /** Text color */
  textColor: string;

  /** Optional accent color for gradients */
  accentColor?: string;
}

/**
 * Collection data structure
 */
export interface Collection {
  /** Collection identifier (BLACK_ROSE, SIGNATURE, LOVE_HURTS) */
  id: string;

  /** Display name */
  name: string;

  /** Short tagline */
  tagline: string;

  /** Full description */
  description: string;

  /** Collection story/narrative */
  story: string;

  /** Visual theme */
  theme: CollectionTheme;

  /** WordPress category slug */
  categorySlug: string;

  /** Three.js experience type */
  experienceType: 'black-rose' | 'signature' | 'love-hurts' | 'showroom' | 'runway';
}

/**
 * Predefined collection configurations
 */
export const COLLECTIONS: Record<string, Collection> = {
  BLACK_ROSE: {
    id: 'BLACK_ROSE',
    name: 'BLACK ROSE',
    tagline: 'Gothic Luxury Reimagined',
    description: 'Where darkness meets elegance in a symphony of rebellious sophistication',
    story: 'The BLACK ROSE collection embodies the beauty found in darkness. Each piece tells a story of mystery and power, crafted for those who find strength in shadows and elegance in the unconventional.',
    theme: {
      primaryColor: '#1a1a1a',
      backgroundColor: '#0a0a0a',
      textColor: '#ffffff',
      accentColor: '#8b0000',
    },
    categorySlug: 'black-rose',
    experienceType: 'black-rose',
  },

  SIGNATURE: {
    id: 'SIGNATURE',
    name: 'SIGNATURE',
    tagline: 'Timeless Luxury',
    description: 'Classic elegance with a contemporary edge - the foundation of refined streetwear',
    story: 'Our SIGNATURE collection represents the perfect balance of timeless sophistication and modern sensibility. Each design is a testament to craftsmanship, created for those who appreciate understated luxury.',
    theme: {
      primaryColor: '#d4af37',
      backgroundColor: '#f5f5f0',
      textColor: '#2a2a2a',
      accentColor: '#8b7355',
    },
    categorySlug: 'signature',
    experienceType: 'signature',
  },

  LOVE_HURTS: {
    id: 'LOVE_HURTS',
    name: 'LOVE HURTS',
    tagline: 'Passion Meets Pain',
    description: 'Raw emotion transformed into wearable art - for hearts that bleed rebellion',
    story: 'LOVE HURTS captures the duality of passion - the ecstasy and the agony. This collection is for those who wear their heart on their sleeve, literally. Bold, unapologetic, and deeply personal.',
    theme: {
      primaryColor: '#b76e79',
      backgroundColor: '#1a0a0a',
      textColor: '#ffffff',
      accentColor: '#dc143c',
    },
    categorySlug: 'love-hurts',
    experienceType: 'love-hurts',
  },
};

/**
 * Product data from WordPress/WooCommerce
 */
export interface Product {
  id: number;
  name: string;
  slug: string;
  price: string;
  regularPrice: string;
  salePrice?: string;
  description: string;
  shortDescription: string;
  images: ProductImage[];
  categories: ProductCategory[];
  tags: ProductTag[];
  attributes: ProductAttribute[];
  inStock: boolean;
  stockQuantity?: number;
}

export interface ProductImage {
  id: number;
  src: string;
  alt: string;
  name: string;
}

export interface ProductCategory {
  id: number;
  name: string;
  slug: string;
}

export interface ProductTag {
  id: number;
  name: string;
  slug: string;
}

export interface ProductAttribute {
  id: number;
  name: string;
  options: string[];
}
