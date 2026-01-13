/**
 * PRE-ORDER Client Component
 * ==========================
 * Interactive 3D gallery showcasing all collection variants.
 * Displays Black Rose, Signature, and Love Hurts products with visual separation.
 */

'use client';

import React, { useState, useMemo } from 'react';
import dynamic from 'next/dynamic';
import type { Product } from '@/types/collections';
import type { ShowroomProduct } from '@/types/product';

// Dynamic import for Three.js (code splitting, client-only)
const ShowroomCanvas = dynamic(
  () =>
    import('@/components/collections/ShowroomCanvas').then((mod) => ({
      default: mod.ShowroomCanvas,
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
          backgroundColor: '#0d0d0d',
          color: '#d4af37',
          fontSize: '1.2rem',
        }}
      >
        Loading Pre-Order Gallery...
      </div>
    ),
    ssr: false,
  }
);

interface PreOrderClientPageProps {
  curatedProducts: Product[];
}

export default function PreOrderClientPage({
  curatedProducts,
}: PreOrderClientPageProps) {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // Convert WooCommerce products to ShowroomProduct format for 3D
  const showroomProducts = useMemo((): ShowroomProduct[] => {
    // Adaptive spacing: tighter for larger grids (>8 products)
    const horizontalSpacing = curatedProducts.length > 8 ? 5 : 6;

    return curatedProducts.slice(0, 12).map((product, index) => {
      // Arrange in 3-column gallery grid
      const row = Math.floor(index / 3);
      const col = index % 3;

      return {
        id: product.id.toString(),
        name: product.name,
        modelUrl: product.images[0]?.src || '',
        position: [
          (col - 1) * horizontalSpacing,   // X: adaptive spacing
          0,                                 // Y: floor level
          row * 8 - 12,                      // Z: staggered depth
        ] as [number, number, number],
        sku: product.slug || `sku-${product.id}`,
        price: parseFloat(product.price) || 0,
        salePrice: product.salePrice ? parseFloat(product.salePrice) : undefined,
        stockStatus: product.inStock ? 'in_stock' as const : 'out_of_stock' as const,
        stockQuantity: product.stockQuantity || 0,
        sizes: [],
        colors: [],
        wcProductId: product.id,
      };
    });
  }, [curatedProducts]);

  const handleProductClick = (showroomProduct: ShowroomProduct) => {
    const fullProduct = curatedProducts.find(
      (p) => p.id.toString() === showroomProduct.id
    );
    if (fullProduct) {
      setSelectedProduct(fullProduct);
    }
  };

  // Pre-order theme
  const theme = { primary: '#d4af37', accent: '#c0c0c0', bg: '#0d0d0d' };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#0d0d0d' }}>
      {/* 3D Gallery Experience */}
      <div style={{ height: '70vh', position: 'relative' }}>
        <ShowroomCanvas
          products={showroomProducts}
          onProductClick={handleProductClick}
          showPerformance={false}
        />
      </div>

      {/* Curated Products Header */}
      <div
        style={{
          padding: '2rem',
          backgroundColor: '#0d0d0d',
          borderBottom: '1px solid #1a1a1a',
        }}
      >
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <h2 style={{ color: '#d4af37', marginBottom: '0.5rem', fontSize: '2rem' }}>
            Curated Pre-Order Selection
          </h2>
          <p style={{ color: '#999', fontSize: '1.1rem' }}>
            Exclusive pieces hand-picked from our collections
          </p>
        </div>
      </div>

      {/* Product Grid */}
      <div style={{ padding: '3rem 2rem', maxWidth: '1400px', margin: '0 auto' }}>
        {curatedProducts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <h3 style={{ color: '#d4af37', fontSize: '1.5rem', marginBottom: '1rem' }}>
              No Products Available Yet
            </h3>
            <p style={{ color: '#999', fontSize: '1.1rem' }}>
              Pre-order items coming soon. Check back later for exclusive pieces.
            </p>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: '2rem',
            }}
          >
            {curatedProducts.map((product) => (
              <div
                key={product.id}
                onClick={() => setSelectedProduct(product)}
                style={{
                  backgroundColor: '#1a1a1a',
                  borderRadius: '12px',
                  overflow: 'hidden',
                  cursor: 'pointer',
                  transition: 'transform 0.3s',
                  border: `2px solid ${theme.primary}20`,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.border = `2px solid ${theme.primary}`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.border = `2px solid ${theme.primary}20`;
                }}
              >
                <div style={{ position: 'relative', paddingTop: '100%', backgroundColor: '#0d0d0d' }}>
                  {product.images[0] && (
                    <img
                      src={product.images[0].src}
                      alt={product.name}
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                      }}
                    />
                  )}
                </div>
                <div style={{ padding: '1.5rem' }}>
                  <h4 style={{ color: '#ffffff', fontSize: '1.1rem', marginBottom: '0.5rem' }}>
                    {product.name}
                  </h4>
                  <p style={{ color: theme.primary, fontSize: '1.2rem', fontWeight: 700 }}>
                    ${parseFloat(product.price).toFixed(2)}
                  </p>
                  <button
                    style={{
                      marginTop: '1rem',
                      width: '100%',
                      padding: '0.75rem',
                      backgroundColor: theme.primary,
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '8px',
                      fontSize: '1rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Pre-Order Now
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
