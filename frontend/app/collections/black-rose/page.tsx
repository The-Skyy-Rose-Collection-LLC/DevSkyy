/**
 * BLACK ROSE Collection Page - Server Component
 * ==============================================
 * Fetches products from WordPress/WooCommerce and renders with ISR caching.
 */

import { Suspense } from 'react';
import { COLLECTIONS, type Product } from '@/types/collections';
import { ProductGridSkeleton } from '@/components/skeletons';
import BlackRoseClientPage from './BlackRoseClientPage';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WORDPRESS_URL = process.env.WORDPRESS_URL || 'https://shop.skyyrose.com';

async function getProducts(): Promise<Product[]> {
  try {
    const res = await fetch(
      `${WORDPRESS_URL}/wp-json/wc/v3/products?category=black-rose&per_page=20&consumer_key=${process.env.WOOCOMMERCE_KEY}&consumer_secret=${process.env.WOOCOMMERCE_SECRET}`,
      {
        next: { revalidate: 300 }, // Cache for 5 minutes
      }
    );

    if (!res.ok) {
      console.error('Failed to fetch products:', res.statusText);
      return [];
    }

    return res.json();
  } catch (error) {
    console.error('Error fetching products:', error);
    return [];
  }
}

export const metadata = {
  title: 'BLACK ROSE Collection - SkyyRose',
  description: 'Gothic Luxury Reimagined - Where darkness meets elegance',
};

export default async function BlackRosePage() {
  const products = await getProducts();
  const collection = COLLECTIONS.BLACK_ROSE;

  return (
    <Suspense fallback={<ProductGridSkeleton />}>
      <BlackRoseClientPage initialProducts={products} collection={collection} />
    </Suspense>
  );
}
