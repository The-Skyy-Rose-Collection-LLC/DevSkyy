/**
 * PRE-ORDER Page - Server Component
 * ==================================
 * Manually curated pre-order selection.
 * Update CURATED_PRODUCT_IDS below to feature specific products.
 */

import { Suspense } from 'react';
import { COLLECTIONS, type Product } from '@/types/collections';
import { ProductGridSkeleton } from '@/components/skeletons';
import PreOrderClientPage from './PreOrderClientPage';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WORDPRESS_URL = process.env.WORDPRESS_URL || 'https://shop.skyyrose.com';

// ⚠️ CURATED SELECTION - Update these IDs to feature specific products
const CURATED_PRODUCT_IDS: number[] = [
  // Add WooCommerce product IDs here
  // Example: 123, 456, 789
];

async function getCuratedProducts(): Promise<Product[]> {
  if (CURATED_PRODUCT_IDS.length === 0) {
    // No products curated yet - return empty
    return [];
  }

  try {
    const res = await fetch(
      `${WORDPRESS_URL}/wp-json/wc/v3/products?include=${CURATED_PRODUCT_IDS.join(',')}&per_page=50&consumer_key=${process.env.WOOCOMMERCE_KEY}&consumer_secret=${process.env.WOOCOMMERCE_SECRET}`,
      {
        next: { revalidate: 300 }, // Cache for 5 minutes
      }
    );

    if (!res.ok) {
      console.error('Failed to fetch curated products:', res.statusText);
      return [];
    }

    return res.json();
  } catch (error) {
    console.error('Error fetching curated products:', error);
    return [];
  }
}

export const metadata = {
  title: 'Pre-Order - Curated Selection - SkyyRose',
  description: 'Pre-order exclusive pieces from our curated collection',
};

export default async function PreOrderPage() {
  const products = await getCuratedProducts();

  return (
    <Suspense fallback={<ProductGridSkeleton />}>
      <PreOrderClientPage curatedProducts={products} />
    </Suspense>
  );
}
