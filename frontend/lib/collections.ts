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
            name: 'BLACK Rose Crewneck',
            price: 35,
            image: '/images/scenes/black-rose-product-1.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
          {
            id: 'br-002',
            name: 'BLACK Rose Joggers',
            price: 50,
            image: '/images/scenes/black-rose-product-2.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
          {
            id: 'br-003',
            name: 'BLACK is Beautiful Jersey',
            price: 45,
            image: '/images/scenes/black-rose-product-3.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
          {
            id: 'br-004',
            name: 'BLACK Rose Hoodie',
            price: 40,
            image: '/images/scenes/black-rose-product-4.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
          {
            id: 'br-005',
            name: 'BLACK Rose Hoodie \u2014 Signature Edition',
            price: 65,
            image: '/images/scenes/black-rose-product-5.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
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
            id: 'lh-006',
            name: 'The Fannie',
            price: 45,
            image: '/images/scenes/love-hurts-product-1.jpg',
            sizes: ['One Size'],
          },
          {
            id: 'lh-002',
            name: 'Love Hurts Joggers',
            price: 95,
            image: '/images/scenes/love-hurts-product-2.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
          {
            id: 'lh-003',
            name: 'Love Hurts Basketball Shorts',
            price: 75,
            image: '/images/scenes/love-hurts-product-3.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
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
            name: 'Love Hurts Varsity Jacket',
            price: 265,
            image: '/images/scenes/love-hurts-product-4.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
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
            name: "The Bridge Series 'The Bay Bridge' Shorts",
            price: 195,
            image: '/images/scenes/signature-product-1.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
          {
            id: 'sg-002',
            name: "The Bridge Series 'Stay Golden' Shirt",
            price: 65,
            image: '/images/scenes/signature-product-2.jpg',
            sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'],
          },
          {
            id: 'sg-003',
            name: "The Bridge Series 'Stay Golden' Shorts",
            price: 65,
            image: '/images/scenes/signature-product-3.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
          {
            id: 'sg-004',
            name: 'The Signature Hoodie',
            price: 55,
            image: '/images/scenes/signature-product-4.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
          {
            id: 'sg-005',
            name: "The Bridge Series 'The Bay Bridge' Shirt",
            price: 25,
            image: '/images/scenes/signature-product-5.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL'],
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
            name: 'Mint & Lavender Hoodie',
            price: 45,
            image: '/images/scenes/signature-product-6.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
          {
            id: 'sg-007',
            name: 'The Signature Beanie',
            price: 25,
            image: '/images/scenes/signature-product-7.jpg',
            sizes: ['One Size'],
          },
          {
            id: 'sg-013',
            name: 'Mint & Lavender Crewneck',
            price: 40,
            image: '/images/scenes/signature-product-8.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
          {
            id: 'sg-009',
            name: 'The Sherpa Jacket',
            price: 80,
            image: '/images/scenes/signature-product-9.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
          {
            id: 'sg-014',
            name: 'Mint & Lavender Sweatpants',
            price: 45,
            image: '/images/scenes/signature-product-10.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
        ],
      },
      {
        id: 'the-fitting-room',
        name: 'The Fitting Room',
        description: 'Intimate dressing area with signature racks',
        backgroundImage: '/images/scenes/signature-fitting-room.jpg',
        products: [
          {
            id: 'sg-011',
            name: 'Original Label Tee (White)',
            price: 30,
            image: '/images/scenes/signature-beanie-1.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
          {
            id: 'sg-012',
            name: 'Original Label Tee (Orchid)',
            price: 30,
            image: '/images/scenes/signature-beanie-2.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
          },
          {
            id: 'sg-007',
            name: 'The Signature Beanie',
            price: 25,
            image: '/images/scenes/signature-beanie-3.jpg',
            sizes: ['One Size'],
          },
          {
            id: 'sg-009',
            name: 'The Sherpa Jacket',
            price: 80,
            image: '/images/scenes/signature-beanie-4.jpg',
            sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
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
