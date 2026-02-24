export type CollectionSlug = 'black-rose' | 'love-hurts' | 'signature';

export interface CollectionProduct {
  id: string;
  name: string;
  price: number;
  image: string;
  sizes: string[];
  category?: string;
  description?: string;
}

export interface CollectionScene {
  id: string;
  name: string;
  description: string;
  backgroundImage: string;
  products: CollectionProduct[];
}

export interface CollectionConfig {
  slug: CollectionSlug;
  name: string;
  tagline: string;
  description: string;
  accentColor: string;
  accentColorRGB: string;
  bgColor: string;
  heroImage: string;
  scenes: CollectionScene[];
  environment: 'night' | 'apartment' | 'studio';
  enableBloom: boolean;
  bloomStrength: number;
}

export const COLLECTIONS: Record<CollectionSlug, CollectionConfig> = {
  'black-rose': {
    slug: 'black-rose',
    name: 'Black Rose',
    tagline: 'Where Darkness Blooms',
    description:
      'A gothic garden of silver and shadow. Wrought-iron racks draped in velvet, stone pedestals crowned with glass bell jars, and roses that never wilt.',
    accentColor: '#C0C0C0',
    accentColorRGB: '192, 192, 192',
    bgColor: '#0D0D0D',
    heroImage: '/images/scenes/black-rose-garden.jpg',
    environment: 'night',
    enableBloom: true,
    bloomStrength: 0.4,
    scenes: [
      {
        id: 'the-garden',
        name: 'The Garden',
        description: 'Wrought-iron racks amid gothic rose arbors',
        backgroundImage: '/images/scenes/black-rose-garden.jpg',
        products: [
          {
            id: 'br-001',
            name: 'Midnight Velvet Blazer',
            price: 385,
            image: '/images/scenes/black-rose-product-1.jpg',
            sizes: ['XS', 'S', 'M', 'L', 'XL'],
          },
          {
            id: 'br-002',
            name: 'Silver Thorn Pendant',
            price: 165,
            image: '/images/scenes/black-rose-product-2.jpg',
            sizes: ['One Size'],
          },
          {
            id: 'br-003',
            name: 'Gothic Lace Corset Top',
            price: 245,
            image: '/images/scenes/black-rose-product-3.jpg',
            sizes: ['XS', 'S', 'M', 'L'],
          },
          {
            id: 'br-004',
            name: 'Rose Embroidered Skirt',
            price: 295,
            image: '/images/scenes/black-rose-product-4.jpg',
            sizes: ['XS', 'S', 'M', 'L', 'XL'],
          },
          {
            id: 'br-005',
            name: 'Obsidian Silk Gloves',
            price: 125,
            image: '/images/scenes/black-rose-product-5.jpg',
            sizes: ['S', 'M', 'L'],
          },
        ],
      },
    ],
  },
  'love-hurts': {
    slug: 'love-hurts',
    name: 'Love Hurts',
    tagline: 'Pain is Beautiful',
    description:
      'A candlelit ballroom of crimson and gold. Crystal chandeliers cast warm light on velvet chaises and ornate frames, where every piece tells a story of passion.',
    accentColor: '#DC143C',
    accentColorRGB: '220, 20, 60',
    bgColor: '#1A0A0F',
    heroImage: '/images/scenes/love-hurts-ballroom.jpg',
    environment: 'apartment',
    enableBloom: true,
    bloomStrength: 0.3,
    scenes: [
      {
        id: 'the-ballroom',
        name: 'The Ballroom',
        description: 'Candlelit manor with crystal chandeliers',
        backgroundImage: '/images/scenes/love-hurts-ballroom.jpg',
        products: [
          {
            id: 'lh-001',
            name: 'Crimson Heart Dress',
            price: 495,
            image: '/images/scenes/love-hurts-product-1.jpg',
            sizes: ['XS', 'S', 'M', 'L'],
          },
          {
            id: 'lh-002',
            name: 'Passion Chain Necklace',
            price: 225,
            image: '/images/scenes/love-hurts-product-2.jpg',
            sizes: ['One Size'],
          },
          {
            id: 'lh-003',
            name: 'Velvet Heartbreak Jacket',
            price: 425,
            image: '/images/scenes/love-hurts-product-3.jpg',
            sizes: ['S', 'M', 'L', 'XL'],
          },
        ],
      },
      {
        id: 'the-manor',
        name: 'The Manor',
        description: 'Golden pedestals with flickering candlelight',
        backgroundImage: '/images/scenes/love-hurts-manor.jpg',
        products: [
          {
            id: 'lh-004',
            name: 'Baroque Lace Blouse',
            price: 275,
            image: '/images/scenes/love-hurts-product-4.jpg',
            sizes: ['XS', 'S', 'M', 'L'],
          },
          {
            id: 'lh-005',
            name: 'Rose Thorn Ring Set',
            price: 185,
            image: '/images/scenes/love-hurts-product-5.jpg',
            sizes: ['One Size'],
          },
        ],
      },
    ],
  },
  signature: {
    slug: 'signature',
    name: 'Signature',
    tagline: 'The Art of Being',
    description:
      'An ultra-modern runway experience. Glass venues overlooking the Bay Bridge, marble showrooms, and intimate fitting rooms where every piece is a statement.',
    accentColor: '#B76E79',
    accentColorRGB: '183, 110, 121',
    bgColor: '#0A0A0A',
    heroImage: '/images/scenes/signature-runway.jpg',
    environment: 'studio',
    enableBloom: true,
    bloomStrength: 0.35,
    scenes: [
      {
        id: 'the-runway',
        name: 'The Runway',
        description: 'Bay Bridge glass venue with industrial racks',
        backgroundImage: '/images/scenes/signature-runway.jpg',
        products: [
          {
            id: 'sg-001',
            name: 'Runway Silk Blazer',
            price: 550,
            image: '/images/scenes/signature-product-1.jpg',
            sizes: ['XS', 'S', 'M', 'L', 'XL'],
          },
          {
            id: 'sg-002',
            name: 'Neon Statement Dress',
            price: 475,
            image: '/images/scenes/signature-product-2.jpg',
            sizes: ['XS', 'S', 'M', 'L'],
          },
          {
            id: 'sg-003',
            name: 'Glass Display Clutch',
            price: 195,
            image: '/images/scenes/signature-product-3.jpg',
            sizes: ['One Size'],
          },
          {
            id: 'sg-004',
            name: 'Concrete Pedestal Heels',
            price: 345,
            image: '/images/scenes/signature-product-4.jpg',
            sizes: ['6', '7', '8', '9', '10'],
          },
          {
            id: 'sg-005',
            name: 'Industrial Chain Belt',
            price: 165,
            image: '/images/scenes/signature-product-5.jpg',
            sizes: ['S', 'M', 'L'],
          },
        ],
      },
      {
        id: 'the-showroom',
        name: 'The Showroom',
        description: 'Grand exhibition hall with marble columns',
        backgroundImage: '/images/scenes/signature-showroom.jpg',
        products: [
          {
            id: 'sg-006',
            name: 'Marble Column Coat',
            price: 685,
            image: '/images/scenes/signature-product-6.jpg',
            sizes: ['S', 'M', 'L'],
          },
          {
            id: 'sg-007',
            name: 'Spotlight Sequin Top',
            price: 315,
            image: '/images/scenes/signature-product-7.jpg',
            sizes: ['XS', 'S', 'M', 'L'],
          },
          {
            id: 'sg-008',
            name: 'Velvet Plinth Trousers',
            price: 395,
            image: '/images/scenes/signature-product-8.jpg',
            sizes: ['XS', 'S', 'M', 'L', 'XL'],
          },
          {
            id: 'sg-009',
            name: 'Glass Vitrine Earrings',
            price: 145,
            image: '/images/scenes/signature-product-9.jpg',
            sizes: ['One Size'],
          },
          {
            id: 'sg-010',
            name: 'Mannequin Drape Gown',
            price: 725,
            image: '/images/scenes/signature-product-10.jpg',
            sizes: ['XS', 'S', 'M', 'L'],
          },
        ],
      },
      {
        id: 'the-fitting-room',
        name: 'The Fitting Room',
        description: 'Intimate dressing area with beanie stands',
        backgroundImage: '/images/scenes/signature-fitting-room.jpg',
        products: [
          {
            id: 'sg-011',
            name: 'Classic Rose Beanie',
            price: 85,
            image: '/images/scenes/signature-beanie-1.jpg',
            sizes: ['One Size'],
          },
          {
            id: 'sg-012',
            name: 'Midnight Knit Beanie',
            price: 85,
            image: '/images/scenes/signature-beanie-2.jpg',
            sizes: ['One Size'],
          },
          {
            id: 'sg-013',
            name: 'Urban Edge Beanie',
            price: 95,
            image: '/images/scenes/signature-beanie-3.jpg',
            sizes: ['One Size'],
          },
          {
            id: 'sg-014',
            name: 'Luxe Cashmere Beanie',
            price: 125,
            image: '/images/scenes/signature-beanie-4.jpg',
            sizes: ['One Size'],
          },
        ],
      },
    ],
  },
};

export function getCollection(slug: string): CollectionConfig | undefined {
  return COLLECTIONS[slug as CollectionSlug];
}

export function getAllCollections(): CollectionConfig[] {
  return Object.values(COLLECTIONS);
}

export function getAllCollectionSlugs(): CollectionSlug[] {
  return Object.keys(COLLECTIONS) as CollectionSlug[];
}
