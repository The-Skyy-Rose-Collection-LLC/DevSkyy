/**
 * BLACK ROSE Collection Client Component
 * ======================================
 * Interactive 3D experience and product filtering.
 */

'use client';

import React, { useState, useMemo } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { CollectionLayout } from '@/components/collections/CollectionLayout';
import { ProductGrid } from '@/components/collections/ProductGrid';
import { FilterSidebar } from '@/components/collections/FilterSidebar';
import { FilterDrawer } from '@/components/collections/FilterDrawer';
import { useProductFilters } from '@/hooks/useProductFilters';
import type { Product, Collection } from '@/types/collections';
import type { BlackRoseProduct } from '@/collections/BlackRoseExperience';

// Dynamic import for Three.js (code splitting, client-only)
const BlackRoseCanvas = dynamic(
  () =>
    import('@/components/collections/BlackRoseCanvas').then((mod) => ({
      default: mod.BlackRoseCanvas,
    })),
  {
    loading: () => (
      <div
        style={{
          width: '100%',
          height: '600px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#0a0a0a',
          color: '#c0c0c0',
          fontSize: '1.2rem',
        }}
      >
        Loading 3D Experience...
      </div>
    ),
    ssr: false,
  }
);

interface BlackRoseClientPageProps {
  initialProducts: Product[];
  collection: Collection;
}

export default function BlackRoseClientPage({
  initialProducts,
  collection,
}: BlackRoseClientPageProps) {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Product filtering and sorting
  const {
    filters,
    filteredProducts,
    availableFilters,
    updateFilters,
    clearFilters,
    hasActiveFilters,
  } = useProductFilters(initialProducts);

  // Convert WooCommerce products to BlackRoseProduct format for 3D
  const blackRoseProducts = useMemo((): BlackRoseProduct[] => {
    return initialProducts.slice(0, 4).map((product, index) => {
      // Arrange products in a gothic garden layout
      const positions: [number, number, number][] = [
        [-5, 0, -3],  // Left front
        [5, 0, -3],   // Right front
        [-5, 0, 3],   // Left back
        [5, 0, 3],    // Right back
      ];

      return {
        id: product.id.toString(),
        name: product.name,
        price: parseFloat(product.price) || 0,
        modelUrl: product.images[0]?.src || '',
        thumbnailUrl: product.images[0]?.src || '',
        position: positions[index] || [0, 0, 0],
        isEasterEgg: false,
      };
    });
  }, [initialProducts]);

  const handleProductClick = (blackRoseProduct: BlackRoseProduct) => {
    const fullProduct = initialProducts.find(
      (p) => p.id.toString() === blackRoseProduct.id
    );
    if (fullProduct) {
      setSelectedProduct(fullProduct);
    }
  };

  const experienceComponent = (
    <div style={{ position: 'relative' }}>
      {/* Pre-Order CTA */}
      <div
        style={{
          position: 'absolute',
          bottom: '2rem',
          left: '2rem',
          zIndex: 20,
        }}
      >
        <Link href="/collections/pre-order">
          <button
            style={{
              padding: '1rem 2rem',
              backgroundColor: '#1a1a1a',
              color: '#c0c0c0',
              border: '2px solid #c0c0c0',
              borderRadius: '12px',
              fontSize: '1.1rem',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(192, 192, 192, 0.4)',
              transition: 'all 0.3s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'scale(1.05)';
              e.currentTarget.style.backgroundColor = '#c0c0c0';
              e.currentTarget.style.color = '#1a1a1a';
              e.currentTarget.style.boxShadow = '0 6px 20px rgba(192, 192, 192, 0.6)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.backgroundColor = '#1a1a1a';
              e.currentTarget.style.color = '#c0c0c0';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(192, 192, 192, 0.4)';
            }}
          >
            🛍️ Pre-Order Collection
          </button>
        </Link>
      </div>

      {/* 3D Experience */}
      <BlackRoseCanvas
        products={blackRoseProducts}
        onProductClick={handleProductClick}
        onEasterEgg={(url) => console.log('Easter egg:', url)}
        enableBloom={true}
        showPerformance={false}
      />
    </div>
  );

  const filterControls = (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1.5rem 2rem',
        backgroundColor: '#0a0a0a',
        borderBottom: '1px solid #1a1a1a',
      }}
    >
      <div style={{ fontSize: '0.95rem', color: '#c0c0c0' }}>
        {filteredProducts.length}{' '}
        {filteredProducts.length === 1 ? 'Product' : 'Products'}
      </div>

      <button
        onClick={() => setIsFilterOpen(true)}
        style={{
          display: 'none',
          background: collection.theme.primaryColor,
          color: collection.theme.textColor,
          border: 'none',
          padding: '0.75rem 1.5rem',
          borderRadius: '8px',
          fontSize: '0.9rem',
          fontWeight: 600,
          cursor: 'pointer',
        }}
        className="mobile-filter-button"
      >
        🎨 Filters{' '}
        {hasActiveFilters && `(${filters.sizes.length + filters.colors.length})`}
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
      <div style={{ display: 'flex', gap: 0 }}>
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

        <div style={{ flex: 1 }}>
          {filterControls}
          <ProductGrid
            products={filteredProducts}
            loading={false}
            error={null}
            onProductClick={setSelectedProduct}
            accentColor={collection.theme.primaryColor}
          />
        </div>
      </div>

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
      loading={false}
    />
  );
}
