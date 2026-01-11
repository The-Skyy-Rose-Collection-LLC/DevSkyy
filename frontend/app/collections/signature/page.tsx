/**
 * SIGNATURE Collection Page
 *
 * Luxury rose garden with golden hour lighting.
 * Oakland & SF tribute collection.
 *
 * URL: /collections/signature
 */

'use client';

import React, { useState, useMemo } from 'react';
import { CollectionLayout } from '../../../components/collections/CollectionLayout';
import { SignatureCanvas } from '../../../components/collections/SignatureCanvas';
import { ProductGrid } from '../../../components/collections/ProductGrid';
import { useCollectionProducts } from '../../../hooks/useCollectionProducts';
import { COLLECTIONS } from '../../../types/collections';
import type { Product } from '../../../types/collections';
import type { SignatureProduct } from '../../../collections/SignatureExperience';

export default function SignaturePage() {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const collection = COLLECTIONS.SIGNATURE;

  const { products, loading, error } = useCollectionProducts({
    categorySlug: collection.categorySlug,
    perPage: 20,
  });

  // Convert WooCommerce products to SignatureProduct format
  const signatureProducts = useMemo((): SignatureProduct[] => {
    return products.slice(0, 8).map((product, index) => {
      // Position products in a circle around the fountain
      const angle = (index / 8) * Math.PI * 2;
      const radius = 6;

      return {
        id: product.id.toString(),
        name: product.name,
        price: parseFloat(product.price) || 0,
        category: 'tops' as const,
        modelUrl: product.images[0]?.src || '',
        thumbnailUrl: product.images[0]?.src || '',
        pedestalPosition: [
          Math.cos(angle) * radius,
          0,
          Math.sin(angle) * radius,
        ],
      };
    });
  }, [products]);

  const handleProductClick = (signatureProduct: SignatureProduct) => {
    const fullProduct = products.find((p) => p.id.toString() === signatureProduct.id);
    if (fullProduct) {
      setSelectedProduct(fullProduct);
    }
  };

  const handleCategorySelect = (category: string) => {
    console.log('Category selected:', category);
  };

  const experienceComponent = (
    <SignatureCanvas
      products={signatureProducts}
      onProductClick={handleProductClick}
      onCategorySelect={handleCategorySelect}
      enableDepthOfField={true}
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
