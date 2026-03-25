/**
 * Products API Route
 *
 * Serves the SkyyRose product catalog.
 * All products are pre-order status — browsable and reservable but not yet purchasable.
 *
 * GET  /api/products                        — All products
 * GET  /api/products?collection=black-rose  — Filter by collection
 * GET  /api/products?sku=br-001             — Single product by SKU
 */

import { NextRequest, NextResponse } from 'next/server';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface RawProduct {
  name: string;
  collection: string;
  description: string;
  short_description: string;
  seo_meta: string;
  instagram: string;
  tiktok: string;
}

interface Product {
  sku: string;
  name: string;
  collection: string;
  description: string;
  shortDescription: string;
  seoMeta: string;
  status: 'pre-order';
  badge: string;
  preOrderPrice: number;
  originalPrice: number;
  remaining: number;
  social: {
    instagram: string;
    tiktok: string;
  };
}

// ---------------------------------------------------------------------------
// Pricing & edition sizes (source: data/product-catalog.csv)
// ---------------------------------------------------------------------------

const PRICES: Record<string, { price: number; editionSize: number }> = {
  // Black Rose
  'br-001': { price: 35, editionSize: 250 },
  'br-002': { price: 50, editionSize: 250 },
  'br-003': { price: 45, editionSize: 250 },
  'br-004': { price: 40, editionSize: 250 },
  'br-005': { price: 65, editionSize: 250 },
  'br-006': { price: 95, editionSize: 250 },
  'br-007': { price: 65, editionSize: 250 },
  'br-008': { price: 115, editionSize: 80 },
  'br-009': { price: 115, editionSize: 80 },
  'br-010': { price: 115, editionSize: 80 },
  'br-011': { price: 115, editionSize: 80 },
  // Love Hurts
  'lh-002': { price: 95, editionSize: 250 },
  'lh-003': { price: 75, editionSize: 250 },
  'lh-004': { price: 265, editionSize: 250 },
  'lh-006': { price: 45, editionSize: 250 },
  // Signature
  'sg-001': { price: 195, editionSize: 250 },
  'sg-002': { price: 65, editionSize: 250 },
  'sg-003': { price: 65, editionSize: 250 },
  'sg-004': { price: 55, editionSize: 250 },
  'sg-005': { price: 25, editionSize: 250 },
  'sg-006': { price: 45, editionSize: 250 },
  'sg-007': { price: 25, editionSize: 250 },
  'sg-009': { price: 80, editionSize: 250 },
  'sg-011': { price: 30, editionSize: 250 },
  'sg-012': { price: 30, editionSize: 250 },
  'sg-013': { price: 40, editionSize: 250 },
  'sg-014': { price: 45, editionSize: 250 },
  // Kids Capsule
  'kids-001': { price: 40, editionSize: 250 },
  'kids-002': { price: 40, editionSize: 250 },
};

// ---------------------------------------------------------------------------
// Product Catalog
// ---------------------------------------------------------------------------

const PRODUCT_CATALOG: Record<string, RawProduct> = {
  // ── Black Rose ─────────────────────────────────────────────────────────────
  'br-001': {
    name: 'BLACK Rose Crewneck',
    collection: 'black-rose',
    description: 'Gothic luxury crewneck with embroidered black rose. Premium black fabric with white ribbed cuffs and hem.',
    short_description: 'Gothic luxury blooms in twilight. Embroidered with defiant elegance.',
    seo_meta: 'SkyyRose BLACK Rose Crewneck — gothic luxury streetwear.',
    instagram: '',
    tiktok: '',
  },
  'br-002': {
    name: 'BLACK Rose Joggers',
    collection: 'black-rose',
    description: 'Premium soft-touch joggers with embroidered black rose emblem. Twilight comfort in dark romantic streetwear.',
    short_description: 'Twilight comfort meets gothic romance.',
    seo_meta: 'SkyyRose BLACK Rose Joggers — gothic luxury streetwear.',
    instagram: '',
    tiktok: '',
  },
  'br-003': {
    name: 'BLACK is Beautiful Jersey',
    collection: 'black-rose',
    description: 'Statement mesh jersey with bold BLACK is Beautiful declaration. Oakland-rooted gothic luxury athletic wear.',
    short_description: 'A bold statement in luxury athletic wear. Black is beautiful.',
    seo_meta: 'SkyyRose BLACK is Beautiful Jersey — Black Rose Collection.',
    instagram: '',
    tiktok: '',
  },
  'br-004': {
    name: 'BLACK Rose Hoodie',
    collection: 'black-rose',
    description: 'Premium hoodie with intricately embroidered black rose. Generous hood, kangaroo pocket, twilight colorway.',
    short_description: 'Gothic luxury in twilight shadows.',
    seo_meta: 'SkyyRose BLACK Rose Hoodie — embroidered gothic luxury.',
    instagram: '',
    tiktok: '',
  },
  'br-005': {
    name: 'BLACK Rose Hoodie — Signature Edition',
    collection: 'black-rose',
    description: 'The definitive Black Rose hoodie. Signature edition with premium detailing, cascade of roses on sleeve, and numbered tag.',
    short_description: 'The definitive Black Rose hoodie. Numbered and premium.',
    seo_meta: 'SkyyRose BLACK Rose Hoodie Signature Edition — limited luxury.',
    instagram: '',
    tiktok: '',
  },
  'br-006': {
    name: 'BLACK Rose Sherpa Jacket',
    collection: 'black-rose',
    description: 'Lustrous black satin with plush Sherpa lining, crowned by an exquisite embroidered rose. Dark opulence in wearable form.',
    short_description: 'Satin and Sherpa unite in dark allure.',
    seo_meta: 'SkyyRose BLACK Rose Sherpa Jacket — luxury gothic outerwear.',
    instagram: '',
    tiktok: '',
  },
  'br-007': {
    name: 'BLACK Rose \u00d7 Love Hurts Basketball Shorts',
    collection: 'black-rose',
    description: 'Two worlds collide. Premium black mesh shorts merging Black Rose darkness with Love Hurts fire. A cross-collection collaboration.',
    short_description: 'Two collections, one collaboration.',
    seo_meta: 'SkyyRose BLACK Rose \u00d7 Love Hurts Basketball Shorts.',
    instagram: '',
    tiktok: '',
  },
  'br-008': {
    name: 'BLACK is Beautiful Jersey Series: 1. SF inspired',
    collection: 'black-rose',
    description: 'Red #80 football jersey. SF 49ers inspired with alternating rose fill on numbers — left digit rose-filled, right plain on front; reversed on back. Exclusive 80-piece edition.',
    short_description: 'Red #80. SF 49ers inspired. 80-piece exclusive.',
    seo_meta: 'SkyyRose BLACK is Beautiful Jersey Series — SF inspired edition.',
    instagram: '',
    tiktok: '',
  },
  'br-009': {
    name: 'BLACK is Beautiful Jersey Series: 2. LAST OAKLAND',
    collection: 'black-rose',
    description: "White #32 football jersey with black border and alternating rose fill. A tribute to Oakland's Raiders legacy. LAST OAKLAND — exclusive 80-piece edition.",
    short_description: 'White #32. A tribute to Oakland. 80-piece exclusive.',
    seo_meta: 'SkyyRose BLACK is Beautiful Jersey Series — LAST OAKLAND edition.',
    instagram: '',
    tiktok: '',
  },
  'br-010': {
    name: 'BLACK is Beautiful Jersey Series: 3. THE BAY',
    collection: 'black-rose',
    description: 'Basketball tank with THE BAY gold text. Rose circle graphic with grey/silver rose fade. Bay Area pride in motion — exclusive 80-piece edition.',
    short_description: 'THE BAY in gold. Bay Area basketball tank. 80-piece exclusive.',
    seo_meta: 'SkyyRose BLACK is Beautiful Jersey Series — THE BAY edition.',
    instagram: '',
    tiktok: '',
  },
  'br-011': {
    name: 'BLACK is Beautiful Jersey Series: 4. THE ROSE (SHARKS EDITION)',
    collection: 'black-rose',
    description: 'Hooded hockey jersey in black and teal. San Jose Sharks inspired with rose crest on front. THE ROSE — exclusive 80-piece edition.',
    short_description: 'Black and teal hooded hockey jersey. Sharks inspired. 80-piece exclusive.',
    seo_meta: 'SkyyRose BLACK is Beautiful Jersey Series — Sharks Edition.',
    instagram: '',
    tiktok: '',
  },
  // ── Love Hurts ─────────────────────────────────────────────────────────────
  'lh-002': {
    name: 'Love Hurts Joggers',
    collection: 'love-hurts',
    description: 'Deep black joggers with embroidered rose. Oakland grit meets luxury — feel the fire with every step.',
    short_description: 'Oakland grit meets luxury comfort.',
    seo_meta: 'SkyyRose Love Hurts Joggers — luxury streetwear.',
    instagram: '',
    tiktok: '',
  },
  'lh-003': {
    name: 'Love Hurts Basketball Shorts',
    collection: 'love-hurts',
    description: 'Oakland-inspired luxury streetwear. Defiant rose design on breathable mesh. Street passion meets the court.',
    short_description: 'Defiant rose on breathable mesh.',
    seo_meta: 'SkyyRose Love Hurts Basketball Shorts.',
    instagram: '',
    tiktok: '',
  },
  'lh-004': {
    name: 'Love Hurts Varsity Jacket',
    collection: 'love-hurts',
    description: 'Oakland street couture. Satin shell with bold fire-red Love Hurts script and hidden rose garden in hood. The statement piece.',
    short_description: 'Oakland street couture. Fire-red script, hidden rose garden.',
    seo_meta: 'SkyyRose Love Hurts Varsity Jacket — Oakland street couture.',
    instagram: '',
    tiktok: '',
  },
  'lh-006': {
    name: 'The Fannie',
    collection: 'love-hurts',
    description: 'Oakland luxury meets everyday utility. The essential Love Hurts fanny pack with premium embroidery. Carry the grit.',
    short_description: 'Oakland luxury meets everyday utility.',
    seo_meta: 'SkyyRose The Fannie — Love Hurts luxury fanny pack.',
    instagram: '',
    tiktok: '',
  },
  // ── Signature ──────────────────────────────────────────────────────────────
  'sg-001': {
    name: "The Bridge Series 'The Bay Bridge' Shorts",
    collection: 'signature',
    description: 'Embody West Coast luxury. Exclusive shorts with iconic blue rose and vibrant Bay Area skyline. The Bay Bridge in fabric form.',
    short_description: 'West Coast luxury. Bay Bridge in fabric.',
    seo_meta: "SkyyRose The Bridge Series 'The Bay Bridge' Shorts.",
    instagram: '',
    tiktok: '',
  },
  'sg-002': {
    name: "The Bridge Series 'Stay Golden' Shirt",
    collection: 'signature',
    description: 'Embrace West Coast prestige. Luxurious statement of Bay Area style featuring the signature rose in gold.',
    short_description: 'Bay Area prestige in gold.',
    seo_meta: "SkyyRose The Bridge Series 'Stay Golden' Shirt.",
    instagram: '',
    tiktok: '',
  },
  'sg-003': {
    name: "The Bridge Series 'Stay Golden' Shorts",
    collection: 'signature',
    description: 'Athletic shorts in Stay Golden colorway celebrating Bay Area luxury. From the Bridge Series — West Coast style in motion.',
    short_description: 'Stay Golden. West Coast style in motion.',
    seo_meta: "SkyyRose The Bridge Series 'Stay Golden' Shorts.",
    instagram: '',
    tiktok: '',
  },
  'sg-004': {
    name: 'The Signature Hoodie',
    collection: 'signature',
    description: 'The quintessential SkyyRose hoodie. Rose gold colorway with premium fleece and embroidered rose detail. The one.',
    short_description: 'The quintessential SkyyRose hoodie.',
    seo_meta: 'SkyyRose The Signature Hoodie — rose gold luxury.',
    instagram: '',
    tiktok: '',
  },
  'sg-005': {
    name: "The Bridge Series 'The Bay Bridge' Shirt",
    collection: 'signature',
    description: 'Athletic shirt celebrating the iconic Bay Area bridges. From the Bridge Series — navy and clean.',
    short_description: 'Bay Area bridges. Navy athletic shirt.',
    seo_meta: "SkyyRose The Bridge Series 'The Bay Bridge' Shirt.",
    instagram: '',
    tiktok: '',
  },
  'sg-006': {
    name: 'Mint & Lavender Hoodie',
    collection: 'signature',
    description: 'Sweet pastel vibes meet streetwear luxury. Mint and lavender colorblock with signature rose detail and ultra-soft fleece.',
    short_description: 'Fresh pastel tones meet luxury streetwear.',
    seo_meta: 'SkyyRose Mint & Lavender Hoodie — Signature Collection.',
    instagram: '',
    tiktok: '',
  },
  'sg-007': {
    name: 'The Signature Beanie',
    collection: 'signature',
    description: 'Classic fitted beanie with embroidered signature rose. West Coast luxury meets everyday warmth. One size fits all.',
    short_description: 'Crown yourself in rose gold.',
    seo_meta: 'SkyyRose The Signature Beanie — luxury knitwear.',
    instagram: '',
    tiktok: '',
  },
  'sg-009': {
    name: 'The Sherpa Jacket',
    collection: 'signature',
    description: 'Plush sherpa warmth in the SkyyRose signature cream colorway. Luxury outerwear for the West Coast.',
    short_description: 'Plush sherpa. Signature warmth.',
    seo_meta: 'SkyyRose The Sherpa Jacket — Signature Collection luxury outerwear.',
    instagram: '',
    tiktok: '',
  },
  'sg-011': {
    name: 'Original Label Tee (White)',
    collection: 'signature',
    description: 'The original SkyyRose label tee in clean white. Minimal design with signature branding — the foundation.',
    short_description: 'The original. Clean white label tee.',
    seo_meta: 'SkyyRose Original Label Tee White — Signature Collection.',
    instagram: '',
    tiktok: '',
  },
  'sg-012': {
    name: 'Original Label Tee (Orchid)',
    collection: 'signature',
    description: 'The original SkyyRose label tee in rich orchid. Minimal design with signature branding — elevated.',
    short_description: 'The original. Rich orchid label tee.',
    seo_meta: 'SkyyRose Original Label Tee Orchid — Signature Collection.',
    instagram: '',
    tiktok: '',
  },
  'sg-013': {
    name: 'Mint & Lavender Crewneck',
    collection: 'signature',
    description: 'Pastel luxury in crewneck form. Mint and lavender colorblock with signature rose embroidery.',
    short_description: 'Pastel luxury. Mint and lavender crewneck.',
    seo_meta: 'SkyyRose Mint & Lavender Crewneck — Signature Collection.',
    instagram: '',
    tiktok: '',
  },
  'sg-014': {
    name: 'Mint & Lavender Sweatpants',
    collection: 'signature',
    description: 'Pastel luxury meets streetwear comfort. Mint and lavender sweatpants with signature rose detail.',
    short_description: 'Pastel luxury streetwear comfort.',
    seo_meta: 'SkyyRose Mint & Lavender Sweatpants — Signature Collection.',
    instagram: '',
    tiktok: '',
  },
  // ── Kids Capsule ───────────────────────────────────────────────────────────
  'kids-001': {
    name: 'Kids Red Set',
    collection: 'kids-capsule',
    description: 'Bold red and black V-chevron colorblock hoodie and jogger set. Designed for young ones who wear luxury from the start.',
    short_description: 'Luxury from the start. Bold red set for kids.',
    seo_meta: 'SkyyRose Kids Red Set — Kids Capsule Collection.',
    instagram: '',
    tiktok: '',
  },
  'kids-002': {
    name: 'Kids Purple Set',
    collection: 'kids-capsule',
    description: 'Rich purple and black V-chevron colorblock hoodie and jogger set. Little ones deserve luxury too.',
    short_description: 'Luxury from the start. Rich purple set for kids.',
    seo_meta: 'SkyyRose Kids Purple Set — Kids Capsule Collection.',
    instagram: '',
    tiktok: '',
  },
};

const BADGES = ['Pre-Order Now', 'Reserve Yours', 'Coming Soon', 'Limited Edition'];

function buildProduct(sku: string, raw: RawProduct): Product {
  const pricing = PRICES[sku] ?? { price: 50, editionSize: 250 };
  const price = pricing.price;
  const badgeIndex = sku.charCodeAt(sku.length - 1) % BADGES.length;

  return {
    sku,
    name: raw.name,
    collection: raw.collection,
    description: raw.description,
    shortDescription: raw.short_description,
    seoMeta: raw.seo_meta,
    status: 'pre-order',
    badge: BADGES[badgeIndex],
    preOrderPrice: price,
    originalPrice: Math.round(price * 1.25),
    remaining: Math.min(50 + (sku.charCodeAt(sku.length - 1) % 50), pricing.editionSize),
    social: {
      instagram: raw.instagram,
      tiktok: raw.tiktok,
    },
  };
}

// ---------------------------------------------------------------------------
// GET Handler
// ---------------------------------------------------------------------------

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const collection = searchParams.get('collection');
  const sku = searchParams.get('sku');

  // Single product lookup
  if (sku) {
    const raw = PRODUCT_CATALOG[sku];
    if (!raw) {
      return NextResponse.json({ success: false, error: 'Product not found' }, { status: 404 });
    }
    return NextResponse.json({ success: true, data: buildProduct(sku, raw) });
  }

  // Build full list, optionally filtered by collection
  let entries = Object.entries(PRODUCT_CATALOG);
  if (collection) {
    entries = entries.filter(([, raw]) => raw.collection === collection);
  }

  const products = entries.map(([id, raw]) => buildProduct(id, raw));

  return NextResponse.json({
    success: true,
    data: {
      products,
      total: products.length,
      collections: ['black-rose', 'love-hurts', 'signature', 'kids-capsule'],
    },
  });
}
