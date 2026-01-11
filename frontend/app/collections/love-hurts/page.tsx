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
import { FilterSidebar } from '../../../components/collections/FilterSidebar';
import { FilterDrawer } from '../../../components/collections/FilterDrawer';
import { useCollectionProducts } from '../../../hooks/useCollectionProducts';
import { useProductFilters } from '../../../hooks/useProductFilters';
import { COLLECTIONS } from '../../../types/collections';
import type { Product } from '../../../types/collections';
import type { LoveHurtsProduct } from '../../../collections/LoveHurtsExperience';

export default function LoveHurtsPage() {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const collection = COLLECTIONS.LOVE_HURTS;

  const { products, loading, error } = useCollectionProducts({
    categorySlug: collection.categorySlug,
    perPage: 20,
  });

  // Product filtering and sorting
  const {
    filters,
    filteredProducts,
    availableFilters,
    updateFilters,
    clearFilters,
    hasActiveFilters,
  } = useProductFilters(products);

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

  // Filter/Sort Controls Component
  const filterControls = (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '1.5rem 2rem',
      backgroundColor: '#ffffff',
      borderBottom: '1px solid #e5e5e5',
    }}>
      <div style={{
        fontSize: '0.95rem',
        color: '#666',
      }}>
        {filteredProducts.length} {filteredProducts.length === 1 ? 'Product' : 'Products'}
      </div>

      {/* Mobile Filter Button */}
      <button
        onClick={() => setIsFilterOpen(true)}
        style={{
          display: 'none',
          background: collection.theme.primaryColor,
          color: '#ffffff',
          border: 'none',
          padding: '0.75rem 1.5rem',
          borderRadius: '8px',
          fontSize: '0.9rem',
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'transform 0.2s ease',
        }}
        className="mobile-filter-button"
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-2px)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
        }}
      >
        🎨 Filters {hasActiveFilters && `(${filters.sizes.length + filters.colors.length})`}
      </button>

      <style jsx>{`
        @media (max-width: 1024px) {
          .mobile-filter-button {
            display: block !important;
          }
        }
      `}</style>
    </div>
  );

  const productGridComponent = (
    <>
      <div style={{
        display: 'flex',
        gap: 0,
      }}>
        {/* Desktop Filter Sidebar */}
        <div style={{ display: 'block' }} className="desktop-filter">
          <FilterSidebar
            filters={filters}
            availableFilters={availableFilters}
            onUpdateFilters={updateFilters}
            onClearFilters={clearFilters}
            hasActiveFilters={hasActiveFilters}
            accentColor={collection.theme.primaryColor}
          />
        </div>

        {/* Product Grid */}
        <div style={{ flex: 1 }}>
          {filterControls}
          <ProductGrid
            products={filteredProducts}
            loading={loading}
            error={error}
            onProductClick={setSelectedProduct}
            accentColor={collection.theme.primaryColor}
          />
        </div>
      </div>

      {/* Mobile Filter Drawer */}
      <FilterDrawer
        isOpen={isFilterOpen}
        onClose={() => setIsFilterOpen(false)}
        filters={filters}
        availableFilters={availableFilters}
        onUpdateFilters={updateFilters}
        onClearFilters={clearFilters}
        hasActiveFilters={hasActiveFilters}
        accentColor={collection.theme.primaryColor}
      />

      <style jsx>{`
        @media (max-width: 1024px) {
          .desktop-filter {
            display: none !important;
          }
        }
      `}</style>
    </>
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
