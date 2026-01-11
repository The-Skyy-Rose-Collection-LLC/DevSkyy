/**
 * LOVE HURTS Collection Page
 *
 * Enchanted castle with Beauty and the Beast aesthetic.
 * Dramatic candlelight, stained glass, magical particles.
 *
 * URL: /collections/love-hurts
 */

'use client';

import React, { useState, useMemo } from 'react';
import { CollectionLayout } from '../../../components/collections/CollectionLayout';
import { LoveHurtsCanvas } from '../../../components/collections/LoveHurtsCanvas';
import { ProductGrid } from '../../../components/collections/ProductGrid';
import { useCollectionProducts } from '../../../hooks/useCollectionProducts';
import { COLLECTIONS } from '../../../types/collections';
import type { Product } from '../../../types/collections';
import type { LoveHurtsProduct } from '../../../collections/LoveHurtsExperience';

export default function LoveHurtsPage() {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const collection = COLLECTIONS.LOVE_HURTS;

  const { products, loading, error } = useCollectionProducts({
    categorySlug: collection.categorySlug,
    perPage: 20,
  });

  // Convert WooCommerce products to LoveHurtsProduct format
  const loveHurtsProducts = useMemo((): LoveHurtsProduct[] => {
    return products.slice(0, 10).map((product, index) => {
      // First product is the hero (enchanted rose)
      if (index === 0) {
        return {
          id: product.id.toString(),
          name: product.name,
          price: parseFloat(product.price) || 0,
          modelUrl: product.images[0]?.src || '',
          thumbnailUrl: product.images[0]?.src || '',
          displayType: 'hero' as const,
          position: [0, 2, 0], // Center, elevated
          lookbookImages: product.images.slice(0, 3).map((img) => img.src),
        };
      }

      // Next 4 products displayed in mirrors
      if (index >= 1 && index <= 4) {
        const mirrorAngle = ((index - 1) / 4) * Math.PI * 2;
        const radius = 8;

        return {
          id: product.id.toString(),
          name: product.name,
          price: parseFloat(product.price) || 0,
          modelUrl: product.images[0]?.src || '',
          thumbnailUrl: product.images[0]?.src || '',
          displayType: 'mirror' as const,
          position: [
            Math.cos(mirrorAngle) * radius,
            3,
            Math.sin(mirrorAngle) * radius,
          ],
          lookbookImages: product.images.slice(0, 3).map((img) => img.src),
        };
      }

      // Remaining products on ballroom floor
      const floorIndex = index - 5;
      const floorAngle = (floorIndex / 5) * Math.PI * 2;
      const floorRadius = 6;

      return {
        id: product.id.toString(),
        name: product.name,
        price: parseFloat(product.price) || 0,
        modelUrl: product.images[0]?.src || '',
        thumbnailUrl: product.images[0]?.src || '',
        displayType: 'floor' as const,
        position: [
          Math.cos(floorAngle) * floorRadius,
          0.5,
          Math.sin(floorAngle) * floorRadius,
        ],
      };
    });
  }, [products]);

  const handleProductClick = (loveHurtsProduct: LoveHurtsProduct) => {
    const fullProduct = products.find((p) => p.id.toString() === loveHurtsProduct.id);
    if (fullProduct) {
      setSelectedProduct(fullProduct);
    }
  };

  const experienceComponent = (
    <LoveHurtsCanvas
      products={loveHurtsProducts}
      onProductClick={handleProductClick}
      enableBloom={true}
      bloomStrength={1.5}
      showPerformance={false}
    />
  );

  const productGridComponent = (
    <ProductGrid
      products={products}
      loading={loading}
      error={error}
      onProductClick={setSelectedProduct}
      accentColor={collection.theme.primaryColor}
    />
  );

  return (
    <CollectionLayout
      collection={collection}
      experienceComponent={experienceComponent}
      productGridComponent={productGridComponent}
      loading={loading}
    />
  );
}
