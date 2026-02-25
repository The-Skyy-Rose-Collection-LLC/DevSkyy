/**
 * Products API Route
 *
 * Serves the SkyyRose product catalog from product-content.json.
 * All products are pre-order status — browsable and reservable but not yet purchasable.
 *
 * GET  /api/products                       — All products
 * GET  /api/products?collection=black-rose — Filter by collection
 * GET  /api/products?sku=br-001            — Single product by SKU
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
// Product Catalog (canonical source of truth)
// ---------------------------------------------------------------------------

const PRODUCT_CATALOG: Record<string, RawProduct> = {
  'br-001': { name: 'BLACK Rose Crewneck', collection: 'black-rose', description: 'Gothic luxury crewneck with embroidered black rose. Premium black fabric with white ribbed cuffs.', short_description: 'Gothic luxury blooms in twilight. Embroidered with defiant elegance.', seo_meta: 'SkyyRose BLACK Rose Crewneck: gothic luxury meets street style.', instagram: '', tiktok: '' },
  'br-002': { name: 'BLACK Rose Joggers', collection: 'black-rose', description: 'Premium soft-touch joggers with embroidered black rose emblem. Dark romantic streetwear.', short_description: 'Twilight comfort meets gothic romance.', seo_meta: 'SkyyRose BLACK Rose Joggers: Gothic luxury meets streetwear comfort.', instagram: '', tiktok: '' },
  'br-003': { name: 'BLACK is Beautiful Jersey', collection: 'black-rose', description: 'Statement mesh jersey with bold declaration. Oakland-rooted gothic luxury.', short_description: 'A woven manifesto of defiant beauty.', seo_meta: 'SkyyRose BLACK IS BEAUTIFUL Jersey: Oakland-rooted gothic luxury.', instagram: '', tiktok: '' },
  'br-004': { name: 'BLACK Rose Hoodie', collection: 'black-rose', description: 'Premium hoodie with intricately embroidered rose. Generous hood and kangaroo pocket.', short_description: 'Gothic luxury in twilight shadows.', seo_meta: 'SkyyRose BLACK Rose Hoodie: Embroidered gothic luxury.', instagram: '', tiktok: '' },
  'br-005': { name: 'BLACK Rose Hoodie — Signature Edition', collection: 'black-rose', description: 'Deep charcoal hoodie with signature rose embroidery. Cascade of roses on sleeve, secret garden print inside hood.', short_description: 'Embrace twilight with exquisite rose embroidery.', seo_meta: 'SkyyRose BLACK Rose Hoodie Signature Edition.', instagram: '', tiktok: '' },
  'br-006': { name: 'BLACK Rose Sherpa Jacket', collection: 'black-rose', description: 'Lustrous satin-like shell with lavish Sherpa lining. Embroidered black rose on chest.', short_description: 'Satin and Sherpa unite in dark allure.', seo_meta: 'SkyyRose BLACK Rose Sherpa Jacket.', instagram: '', tiktok: '' },
  'br-007': { name: 'BLACK Rose × Love Hurts Basketball Shorts', collection: 'black-rose', description: 'Premium black mesh shorts with shadowed roses. White side panels with embroidered roses.', short_description: 'Gothic poetry etched in mesh.', seo_meta: 'SkyyRose BLACK Rose Basketball Shorts.', instagram: '', tiktok: '' },
  'br-008': { name: "Women's BLACK Rose Hooded Dress", collection: 'black-rose', description: 'Hooded dress in softest midnight fabric. Intricate black rose embroidery.', short_description: 'Gothic mystery meets feminine elegance.', seo_meta: "SkyyRose Women's BLACK Rose Hooded Dress.", instagram: '', tiktok: '' },
  'lh-001': { name: 'The Fannie', collection: 'love-hurts', description: 'Luxury fanny pack embodying Oakland grit. Sleek black with embroidered rose.', short_description: 'Oakland grit meets luxury streetwear.', seo_meta: 'SkyyRose The Fannie: luxury fanny pack from LOVE HURTS.', instagram: '', tiktok: '' },
  'lh-002': { name: 'Love Hurts Joggers', collection: 'love-hurts', description: 'Deep black joggers with white stripes and embroidered rose. Zippered ankles.', short_description: 'Where Oakland grit meets luxury.', seo_meta: 'SkyyRose Love Hurts Joggers.', instagram: '', tiktok: '' },
  'lh-003': { name: 'Love Hurts Basketball Shorts', collection: 'love-hurts', description: 'Breathable white mesh with orange roses and thorny stems. Black panel with crimson roses.', short_description: 'Street passion meets luxury mesh.', seo_meta: 'SkyyRose Love Hurts Basketball Shorts.', instagram: '', tiktok: '' },
  'lh-004': { name: 'Love Hurts Varsity Jacket', collection: 'love-hurts', description: 'Classic varsity silhouette with Oakland soul. Embroidered roses and leather sleeves.', short_description: 'Varsity rebellion meets Oakland soul.', seo_meta: 'SkyyRose Love Hurts Varsity Jacket.', instagram: '', tiktok: '' },
  'sg-001': { name: 'The Bay Set', collection: 'signature', description: 'Complete set celebrating Bay Area roots. Rose gold accents on premium fabric.', short_description: 'Bay Area pride in rose gold.', seo_meta: 'SkyyRose The Bay Set: Signature Collection.', instagram: '', tiktok: '' },
  'sg-002': { name: 'Stay Golden Set', collection: 'signature', description: 'Matching set in golden hour tones. Premium comfort with signature rose gold branding.', short_description: 'Golden hour captured in fabric.', seo_meta: 'SkyyRose Stay Golden Set.', instagram: '', tiktok: '' },
  'sg-003': { name: 'The Signature Tee', collection: 'signature', description: 'Essential tee with signature rose gold branding. Premium cotton construction.', short_description: 'The foundation of SkyyRose style.', seo_meta: 'SkyyRose Signature Tee.', instagram: '', tiktok: '' },
  'sg-005': { name: 'Stay Golden Tee', collection: 'signature', description: 'Golden hour-inspired tee with rose gold details. Relaxed fit premium cotton.', short_description: 'Stay golden, stay SkyyRose.', seo_meta: 'SkyyRose Stay Golden Tee.', instagram: '', tiktok: '' },
  'sg-006': { name: 'Mint & Lavender Hoodie', collection: 'signature', description: 'Fresh mint and lavender colorway with rose gold accents. Ultra-soft fleece interior.', short_description: 'Fresh tones meet luxury comfort.', seo_meta: 'SkyyRose Mint & Lavender Hoodie.', instagram: '', tiktok: '' },
  'sg-007': { name: 'The Signature Beanie', collection: 'signature', description: 'Ribbed beanie with embroidered rose gold logo. One size fits all.', short_description: 'Crown yourself in rose gold.', seo_meta: 'SkyyRose Signature Beanie.', instagram: '', tiktok: '' },
  'sg-009': { name: 'The Sherpa Jacket', collection: 'signature', description: 'Signature Sherpa jacket with rose gold hardware. Plush lining, water-resistant shell.', short_description: 'Signature warmth, signature style.', seo_meta: 'SkyyRose Signature Sherpa Jacket.', instagram: '', tiktok: '' },
  'sg-010': { name: 'The Bridge Series Shorts', collection: 'signature', description: 'Athletic shorts celebrating Bay Area bridges. Rose gold details on premium mesh.', short_description: 'Bridge the gap between luxury and sport.', seo_meta: 'SkyyRose Bridge Series Shorts.', instagram: '', tiktok: '' },
};

// Pricing tiers by collection
const PRICING: Record<string, { original: number; preOrder: number }> = {
  'black-rose': { original: 85, preOrder: 65 },
  'love-hurts': { original: 75, preOrder: 58 },
  'signature': { original: 70, preOrder: 55 },
};

// Override pricing for specific product types
const PRICE_OVERRIDES: Record<string, { original: number; preOrder: number }> = {
  'br-005': { original: 120, preOrder: 95 },  // Signature Edition
  'br-006': { original: 145, preOrder: 115 }, // Sherpa Jacket
  'br-008': { original: 95, preOrder: 75 },   // Hooded Dress
  'lh-004': { original: 135, preOrder: 105 }, // Varsity Jacket
  'sg-001': { original: 130, preOrder: 100 }, // The Bay Set
  'sg-002': { original: 120, preOrder: 95 },  // Stay Golden Set
  'sg-009': { original: 140, preOrder: 110 }, // Sherpa Jacket
};

const BADGES = ['Pre-Order Now', 'Reserve Yours', 'Coming Soon', 'Limited Edition'];

function buildProduct(sku: string, raw: RawProduct): Product {
  const pricing = PRICE_OVERRIDES[sku] ?? PRICING[raw.collection] ?? { original: 75, preOrder: 58 };
  // Deterministic badge based on SKU hash
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
    preOrderPrice: pricing.preOrder,
    originalPrice: pricing.original,
    remaining: 50 + (sku.charCodeAt(sku.length - 1) % 150),
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
      return NextResponse.json(
        { success: false, error: 'Product not found' },
        { status: 404 }
      );
    }
    return NextResponse.json({
      success: true,
      data: buildProduct(sku, raw),
    });
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
      collections: ['black-rose', 'love-hurts', 'signature'],
    },
  });
}
