/**
 * SIGNATURE Collection Client Component
 * =====================================
 * Interactive 3D experience with Garden/Runway toggle and product filtering.
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
import type { SignatureProduct } from '@/collections/SignatureExperience';
import type { RunwayProduct } from '@/collections/RunwayExperience';

// Dynamic imports for Three.js (code splitting, client-only)
const SignatureCanvas = dynamic(
  () =>
    import('@/components/collections/SignatureCanvas').then((mod) => ({
      default: mod.SignatureCanvas,
    })),
  { loading: () => <LoadingScreen text="Loading Garden Experience..." />, ssr: false }
);

const RunwayCanvas = dynamic(
  () =>
    import('@/components/collections/RunwayCanvas').then((mod) => ({
      default: mod.RunwayCanvas,
    })),
  { loading: () => <LoadingScreen text="Loading Runway Show..." />, ssr: false }
);

function LoadingScreen({ text }: { text: string }) {
  return (
    <div
      style={{
        width: '100%',
        height: '600px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#fff8e7',
        color: '#d4af37',
        fontSize: '1.2rem',
      }}
    >
      {text}
    </div>
  );
}

interface SignatureClientPageProps {
  initialProducts: Product[];
  collection: Collection;
}

export default function SignatureClientPage({
  initialProducts,
  collection,
}: SignatureClientPageProps) {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [experienceMode, setExperienceMode] = useState<'garden' | 'runway'>('garden');

  // Product filtering and sorting
  const {
    filters,
    filteredProducts,
    availableFilters,
    updateFilters,
    clearFilters,
    hasActiveFilters,
  } = useProductFilters(initialProducts);

  // Convert WooCommerce products to SignatureProduct format for Garden
  const signatureProducts = useMemo((): SignatureProduct[] => {
    return initialProducts.slice(0, 8).map((product, index) => {
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
  }, [initialProducts]);

  // Convert WooCommerce products to RunwayProduct format
  const runwayProducts = useMemo((): RunwayProduct[] => {
    return initialProducts.slice(0, 5).map((product, index) => ({
      id: product.id.toString(),
      name: product.name,
      modelUrl: product.images[0]?.src || '',
      walkOrder: index + 1,
    }));
  }, [initialProducts]);

  const handleSignatureProductClick = (signatureProduct: SignatureProduct) => {
    const fullProduct = initialProducts.find(
      (p) => p.id.toString() === signatureProduct.id
    );
    if (fullProduct) {
      setSelectedProduct(fullProduct);
    }
  };

  const handleRunwayProductClick = (runwayProduct: RunwayProduct) => {
    const fullProduct = initialProducts.find(
      (p) => p.id.toString() === runwayProduct.id
    );
    if (fullProduct) {
      setSelectedProduct(fullProduct);
    }
  };

  const experienceComponent = (
    <div style={{ position: 'relative' }}>
      {/* Experience Toggle */}
      <div
        style={{
          position: 'absolute',
          top: '2rem',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 20,
          display: 'flex',
          gap: '1rem',
          backgroundColor: 'rgba(255, 248, 231, 0.95)',
          padding: '0.5rem',
          borderRadius: '12px',
          border: '2px solid #d4af37',
          backdropFilter: 'blur(10px)',
        }}
      >
        <button
          onClick={() => setExperienceMode('garden')}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: experienceMode === 'garden' ? '#d4af37' : 'transparent',
            color: experienceMode === 'garden' ? '#ffffff' : '#d4af37',
            border: 'none',
            borderRadius: '8px',
            fontSize: '1rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.3s',
          }}
        >
          🌿 Garden View
        </button>
        <button
          onClick={() => setExperienceMode('runway')}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: experienceMode === 'runway' ? '#d4af37' : 'transparent',
            color: experienceMode === 'runway' ? '#ffffff' : '#d4af37',
            border: 'none',
            borderRadius: '8px',
            fontSize: '1rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.3s',
          }}
        >
          ✨ Runway Show
        </button>
      </div>

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
              backgroundColor: '#d4af37',
              color: '#ffffff',
              border: 'none',
              borderRadius: '12px',
              fontSize: '1.1rem',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(212, 175, 55, 0.4)',
              transition: 'all 0.3s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'scale(1.05)';
              e.currentTarget.style.boxShadow = '0 6px 20px rgba(212, 175, 55, 0.6)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(212, 175, 55, 0.4)';
            }}
          >
            🛍️ Pre-Order Collection
          </button>
        </Link>
      </div>

      {/* 3D Experience */}
      {experienceMode === 'garden' ? (
        <SignatureCanvas
          products={signatureProducts}
          onProductClick={handleSignatureProductClick}
          onCategorySelect={(category) => console.log('Category:', category)}
          enableDepthOfField={true}
          showPerformance={false}
        />
      ) : (
        <RunwayCanvas
          products={runwayProducts}
          onProductClick={handleRunwayProductClick}
          showPerformance={false}
        />
      )}
    </div>
  );

  const filterControls = (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1.5rem 2rem',
        backgroundColor: '#ffffff',
        borderBottom: '1px solid #e5e5e5',
      }}
    >
      <div style={{ fontSize: '0.95rem', color: '#666' }}>
        {filteredProducts.length}{' '}
        {filteredProducts.length === 1 ? 'Product' : 'Products'}
      </div>

      <button
        onClick={() => setIsFilterOpen(true)}
        style={{
          display: 'none',
          background: collection.theme.primaryColor,
          color: collection.theme.backgroundColor,
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
