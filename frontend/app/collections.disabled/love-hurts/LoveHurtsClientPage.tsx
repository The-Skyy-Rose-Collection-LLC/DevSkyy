/**
 * LOVE HURTS Collection Client Component
 * ======================================
 * Interactive client component for Love Hurts collection.
 */

'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { CollectionLayout } from '@/components/collections/CollectionLayout';
import { ProductGrid } from '@/components/collections/ProductGrid';
import { FilterSidebar } from '@/components/collections/FilterSidebar';
import { FilterDrawer } from '@/components/collections/FilterDrawer';
import { useProductFilters } from '@/hooks/useProductFilters';
import type { Product, Collection } from '@/types/collections';

const LoveHurtsCanvas = dynamic(
  () =>
    import('@/components/collections/LoveHurtsCanvas').then((mod) => ({
      default: mod.LoveHurtsCanvas,
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
          backgroundColor: '#1a1a1a',
          color: '#ff0033',
          fontSize: '1.2rem',
        }}
      >
        Loading 3D Experience...
      </div>
    ),
    ssr: false,
  }
);

interface LoveHurtsClientPageProps {
  initialProducts: Product[];
  collection: Collection;
}

export default function LoveHurtsClientPage({
  initialProducts,
  collection,
}: LoveHurtsClientPageProps) {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const {
    filters,
    filteredProducts,
    availableFilters,
    updateFilters,
    clearFilters,
    hasActiveFilters,
  } = useProductFilters(initialProducts);

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
              backgroundColor: '#b76e79',
              color: '#ffffff',
              border: 'none',
              borderRadius: '12px',
              fontSize: '1.1rem',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(183, 110, 121, 0.4)',
              transition: 'all 0.3s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'scale(1.05)';
              e.currentTarget.style.boxShadow = '0 6px 20px rgba(183, 110, 121, 0.6)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(183, 110, 121, 0.4)';
            }}
          >
            🛍️ Pre-Order Collection
          </button>
        </Link>
      </div>

      {/* 3D Experience */}
      <LoveHurtsCanvas
        products={initialProducts.slice(0, 8).map((p, index) => ({
          id: p.id.toString(),
          name: p.name,
          price: parseFloat(p.price) || 0,
          modelUrl: p.images[0]?.src || '',
          thumbnailUrl: p.images[0]?.src || '',
          displayType: (index === 0 ? 'hero' : index % 2 === 0 ? 'mirror' : 'floor') as 'hero' | 'mirror' | 'floor',
        }))}
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
        backgroundColor: '#1a1a1a',
        borderBottom: '1px solid #333',
        color: '#fff',
      }}
    >
      <div style={{ fontSize: '0.95rem' }}>
        {filteredProducts.length}{' '}
        {filteredProducts.length === 1 ? 'Product' : 'Products'}
      </div>

      <button
        onClick={() => setIsFilterOpen(true)}
        style={{
          display: 'none',
          background: collection.theme.primaryColor,
          color: '#000',
          border: 'none',
          padding: '0.75rem 1.5rem',
          borderRadius: '8px',
          fontSize: '0.9rem',
          fontWeight: 600,
          cursor: 'pointer',
        }}
        className="mobile-filter-button"
      >
        🔥 Filters{' '}
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
