/**
 * Products API Route
 *
 * Reads the canonical product catalog
 * (`wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`) and serves
 * shaped product records to admin panels and public pages.
 *
 * GET  /api/products                        — All products
 * GET  /api/products?collection=black-rose  — Filter by collection
 * GET  /api/products?sku=br-001             — Single product by SKU
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  getCatalog,
  getCollectionSlugs,
  getProduct as getCatalogProduct,
  type CatalogProduct,
} from '@/lib/catalog';

interface Product {
  sku: string;
  name: string;
  collection: string;
  description: string;
  shortDescription: string;
  seoMeta: string;
  status: 'active' | 'pre-order' | 'draft';
  badge: string;
  preOrderPrice: number;
  originalPrice: number;
  remaining: number;
  social: {
    instagram: string;
    tiktok: string;
  };
}

const BADGES = ['Pre-Order Now', 'Reserve Yours', 'Coming Soon', 'Limited Edition'];

function deriveStatus(p: CatalogProduct): 'active' | 'pre-order' | 'draft' {
  const badge = p.badge.toLowerCase().trim();
  if (p.isPreorder) return 'pre-order';
  if (badge === 'draft') return 'draft';
  if (p.published) return 'active';
  return 'draft';
}

function deriveShortDescription(p: CatalogProduct): string {
  const first = p.description.split(/[.!?]\s/)[0];
  return first && first.length <= 140 ? `${first}.` : p.description.slice(0, 140);
}

function deriveSeoMeta(p: CatalogProduct): string {
  return `SkyyRose ${p.name} — ${p.collection.replace(/-/g, ' ')} collection.`;
}

function shape(p: CatalogProduct): Product {
  const editionSize = p.editionSize > 0 ? p.editionSize : 250;
  const badgeIndex = p.sku.charCodeAt(p.sku.length - 1) % BADGES.length;

  return {
    sku: p.sku,
    name: p.name,
    collection: p.collection,
    description: p.description,
    shortDescription: deriveShortDescription(p),
    seoMeta: deriveSeoMeta(p),
    status: deriveStatus(p),
    badge: p.badge || BADGES[badgeIndex],
    preOrderPrice: p.price,
    originalPrice: Math.round(p.price * 1.25),
    remaining: Math.min(50 + (p.sku.charCodeAt(p.sku.length - 1) % 50), editionSize),
    social: { instagram: '', tiktok: '' },
  };
}

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const collection = searchParams.get('collection');
  const sku = searchParams.get('sku');

  try {
    if (sku) {
      const product = getCatalogProduct(sku);
      if (!product) {
        return NextResponse.json(
          { success: false, error: 'Product not found' },
          { status: 404 }
        );
      }
      return NextResponse.json({ success: true, data: shape(product) });
    }

    const all = getCatalog();
    const filtered = collection ? all.filter((p) => p.collection === collection) : all;
    const products = filtered.map(shape);

    return NextResponse.json({
      success: true,
      data: {
        products,
        total: products.length,
        collections: getCollectionSlugs(),
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Catalog read failed';
    return NextResponse.json(
      { success: false, error: message },
      { status: 500 }
    );
  }
}
