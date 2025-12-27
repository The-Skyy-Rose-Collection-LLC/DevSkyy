/**
 * Brand API Route Handler
 * Returns SkyyRose brand configuration for the Brand Kit page
 */

import { NextResponse } from 'next/server';

const SKYYROSE_BRAND = {
  name: 'The Skyy Rose Collection',
  tagline: 'Luxury Streetwear with Soul',
  philosophy: 'Where Love Meets Luxury',
  location: 'Oakland, California',
  tone: {
    primary: 'Elegant, empowering, romantic, bold',
    descriptors: [
      'sophisticated yet accessible',
      'poetic but not pretentious',
      'confident without arrogance',
      'romantic with edge',
    ],
    avoid: [
      'generic fashion buzzwords',
      'overly casual language',
      'aggressive or harsh tones',
      'clichéd luxury language',
    ],
  },
  colors: {
    primary: { name: 'Black Rose', hex: '#1A1A1A', rgb: '26, 26, 26' },
    accent: { name: 'Rose Gold', hex: '#D4AF37', rgb: '212, 175, 55' },
    highlight: { name: 'Deep Rose', hex: '#8B0000', rgb: '139, 0, 0' },
    ivory: { name: 'Ivory', hex: '#F5F5F0', rgb: '245, 245, 240' },
    obsidian: { name: 'Obsidian', hex: '#0D0D0D', rgb: '13, 13, 13' },
  },
  typography: {
    heading: 'Playfair Display',
    body: 'Inter',
    accent: 'Cormorant Garamond',
  },
  target_audience: {
    age_range: '18-35',
    description: 'Fashion-forward individuals who value self-expression',
    interests: ['streetwear', 'luxury fashion', 'self-expression', 'art', 'music'],
    values: ['authenticity', 'quality', 'individuality', 'emotional connection'],
  },
  product_types: ['hoodies', 'tees', 'bombers', 'track pants', 'accessories', 'caps', 'beanies'],
  quality_descriptors: [
    'premium heavyweight cotton',
    'meticulous construction',
    'attention to detail',
    'limited edition exclusivity',
    'elevated street poetry',
  ],
};

const COLLECTION_CONTEXT = {
  BLACK_ROSE: {
    name: 'Black Rose',
    tagline: 'Limited Edition Exclusivity',
    mood: 'mysterious, sophisticated, rare, coveted',
    colors: 'deep black, subtle rose gold accents, matte finish',
    style: 'dark elegance, limited edition, exclusive drops',
    description: 'The pinnacle of SkyyRose luxury. Each Black Rose piece is a limited release, crafted for those who understand that true style is rare.',
  },
  SIGNATURE: {
    name: 'Signature',
    tagline: 'Timeless Essentials',
    mood: 'classic, versatile, foundational, elevated basics',
    colors: 'clean neutrals, rose gold details, ivory accents',
    style: 'essential wardrobe, everyday luxury, refined simplicity',
    description: 'The foundation of SkyyRose style. Signature pieces are the building blocks of a discerning wardrobe—timeless, versatile, unmistakably premium.',
  },
  MIDNIGHT_BLOOM: {
    name: 'Midnight Bloom',
    tagline: 'Beauty in Darkness',
    mood: 'romantic, mysterious, nocturnal, blooming',
    colors: 'deep purples, midnight blue, silver accents',
    style: 'romantic darkness, floral motifs, night-inspired',
    description: 'For those who find beauty in the shadows. Midnight Bloom celebrates the romance of darkness, where flowers bloom under moonlight.',
  },
  LOVE_HURTS: {
    name: 'Love Hurts',
    tagline: 'Feel Everything',
    mood: 'passionate, vulnerable, powerful, emotional',
    colors: 'deep reds, black, heart motifs, distressed textures',
    style: 'emotional expression, storytelling through design',
    description: 'Raw emotion worn proudly. Love Hurts transforms the beautiful pain of human experience into wearable art.',
  },
};

export async function GET() {
  return NextResponse.json({
    brand: SKYYROSE_BRAND,
    collections: COLLECTION_CONTEXT,
  });
}
