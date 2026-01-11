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
import { FilterSidebar } from '../../../components/collections/FilterSidebar';
import { FilterDrawer } from '../../../components/collections/FilterDrawer';
import { useCollectionProducts } from '../../../hooks/useCollectionProducts';
import { useProductFilters } from '../../../hooks/useProductFilters';
import { COLLECTIONS } from '../../../types/collections';
import type { Product } from '../../../types/collections';
import type { SignatureProduct } from '../../../collections/SignatureExperience';

export default function SignaturePage() {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const collection = COLLECTIONS.SIGNATURE;

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
          color: collection.theme.backgroundColor,
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

  // JSON-LD Structured Data for SEO
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'SIGNATURE Collection',
    description: 'Elegant luxury fashion pieces inspired by Oakland & San Francisco. Sophisticated designs that blend urban elegance with timeless style.',
    url: typeof window !== 'undefined' ? window.location.href : 'https://skyyrose.com/collections/signature',
    brand: {
      '@type': 'Brand',
      name: 'SkyyRose',
      url: 'https://skyyrose.com',
    },
    numberOfItems: products.length,
    itemListElement: products.slice(0, 10).map((product, index) => ({
      '@type': 'Product',
      position: index + 1,
      name: product.name,
      description: product.short_description || product.description,
      image: product.images[0]?.src || '',
      offers: {
        '@type': 'Offer',
        price: product.price,
        priceCurrency: 'USD',
        availability: product.stock_status === 'instock' ? 'https://schema.org/InStock' : 'https://schema.org/OutOfStock',
        url: product.permalink,
      },
      brand: {
        '@type': 'Brand',
        name: 'SkyyRose',
      },
    })),
  };

  const breadcrumbJsonLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: 'https://skyyrose.com',
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'Collections',
        item: 'https://skyyrose.com/collections',
      },
      {
        '@type': 'ListItem',
        position: 3,
        name: 'SIGNATURE',
        item: 'https://skyyrose.com/collections/signature',
      },
    ],
  };

  return (
    <>
      {/* JSON-LD Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, '\\u003c'),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(breadcrumbJsonLd).replace(/</g, '\\u003c'),
        }}
      />

      <CollectionLayout
        collection={collection}
        experienceComponent={experienceComponent}
        productGridComponent={productGridComponent}
        loading={loading}
      />
    </>
  );
}
