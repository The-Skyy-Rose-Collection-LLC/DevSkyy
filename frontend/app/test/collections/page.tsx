/**
 * Test Page for Collection Components
 *
 * Demonstrates ProductGrid with real WordPress data.
 * Tests COLL-003 (API) and COLL-004 (Grid) integration.
 *
 * Navigate to: http://localhost:3001/test/collections
 */

'use client';

import React, { useState } from 'react';
import { ProductGrid } from '../../../components/collections/ProductGrid';
import { useCollectionProducts } from '../../../hooks/useCollectionProducts';
import { COLLECTIONS } from '../../../types/collections';
import type { Product } from '../../../types/collections';

export default function CollectionsTestPage() {
  const [selectedCollection, setSelectedCollection] = useState<'BLACK_ROSE' | 'SIGNATURE' | 'LOVE_HURTS'>('BLACK_ROSE');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  const collection = COLLECTIONS[selectedCollection];

  if (!collection) {
    return <div>Collection not found</div>;
  }

  const { products, loading, error, retry } = useCollectionProducts({
    categorySlug: collection.categorySlug,
    perPage: 20,
  });

  const handleProductClick = (product: Product) => {
    setSelectedProduct(product);
    console.log('Product clicked:', product);
  };

  const closeModal = () => setSelectedProduct(null);

  const styles = {
    page: {
      minHeight: '100vh',
      background: collection.theme.backgroundColor,
      color: collection.theme.textColor,
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    },
    header: {
      padding: '2rem',
      textAlign: 'center' as const,
      borderBottom: `1px solid ${collection.theme.primaryColor}30`,
    },
    title: {
      fontSize: '2.5rem',
      fontWeight: 800,
      color: collection.theme.primaryColor,
      marginBottom: '0.5rem',
    },
    subtitle: {
      fontSize: '1.1rem',
      color: collection.theme.textColor,
      opacity: 0.8,
      marginBottom: '2rem',
    },
    collectionButtons: {
      display: 'flex',
      gap: '1rem',
      justifyContent: 'center',
      flexWrap: 'wrap' as const,
    },
    collectionButton: (isActive: boolean) => ({
      padding: '0.75rem 1.5rem',
      borderRadius: '8px',
      border: `2px solid ${isActive ? collection.theme.primaryColor : 'transparent'}`,
      background: isActive ? collection.theme.primaryColor + '20' : 'transparent',
      color: collection.theme.textColor,
      fontSize: '0.95rem',
      fontWeight: 600,
      cursor: 'pointer',
      transition: 'all 0.3s ease',
    } as React.CSSProperties),
    stats: {
      display: 'flex',
      gap: '2rem',
      justifyContent: 'center',
      padding: '2rem',
      fontSize: '0.9rem',
      color: collection.theme.textColor,
      opacity: 0.7,
    },
    gridSection: {
      padding: '2rem 0 4rem 0',
    },
    modal: {
      position: 'fixed' as const,
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '2rem',
    },
    modalContent: {
      background: '#ffffff',
      borderRadius: '16px',
      padding: '2rem',
      maxWidth: '600px',
      width: '100%',
      maxHeight: '80vh',
      overflow: 'auto',
    },
    modalHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: '1.5rem',
    },
    modalTitle: {
      fontSize: '1.5rem',
      fontWeight: 700,
      color: '#1a1a1a',
    },
    closeButton: {
      background: 'none',
      border: 'none',
      fontSize: '1.5rem',
      cursor: 'pointer',
      color: '#999',
      padding: '0',
      width: '32px',
      height: '32px',
    } as React.CSSProperties,
    modalImage: {
      width: '100%',
      borderRadius: '12px',
      marginBottom: '1.5rem',
    },
    modalPrice: {
      fontSize: '1.75rem',
      fontWeight: 700,
      color: collection.theme.primaryColor,
      marginBottom: '1rem',
    },
    modalDescription: {
      fontSize: '1rem',
      lineHeight: 1.6,
      color: '#666',
      marginBottom: '1.5rem',
    },
    addToCartButton: {
      width: '100%',
      padding: '1rem',
      background: collection.theme.primaryColor,
      color: '#ffffff',
      border: 'none',
      borderRadius: '8px',
      fontSize: '1.1rem',
      fontWeight: 600,
      cursor: 'pointer',
      transition: 'transform 0.2s ease',
    } as React.CSSProperties,
  };

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={styles.title}>Collection Test Page</h1>
        <p style={styles.subtitle}>Testing ProductGrid + WordPress API Integration</p>

        <div style={styles.collectionButtons}>
          {(['BLACK_ROSE', 'SIGNATURE', 'LOVE_HURTS'] as const).map((collectionKey) => (
            <button
              key={collectionKey}
              style={styles.collectionButton(selectedCollection === collectionKey)}
              onClick={() => setSelectedCollection(collectionKey)}
              onMouseEnter={(e) => {
                if (selectedCollection !== collectionKey) {
                  e.currentTarget.style.background = collection.theme.primaryColor + '10';
                }
              }}
              onMouseLeave={(e) => {
                if (selectedCollection !== collectionKey) {
                  e.currentTarget.style.background = 'transparent';
                }
              }}
            >
              {COLLECTIONS[collectionKey]?.name || collectionKey}
            </button>
          ))}
        </div>

        <div style={styles.stats}>
          <div>Collection: {collection.name}</div>
          <div>•</div>
          <div>Products: {loading ? '...' : products.length}</div>
          <div>•</div>
          <div>Status: {loading ? 'Loading' : error ? 'Error' : 'Ready'}</div>
        </div>
      </header>

      <section style={styles.gridSection}>
        <ProductGrid
          products={products}
          loading={loading}
          error={error}
          onRetry={retry}
          onProductClick={handleProductClick}
          accentColor={collection.theme.primaryColor}
        />
      </section>

      {selectedProduct && (
        <div style={styles.modal} onClick={closeModal}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>{selectedProduct.name}</h2>
              <button style={styles.closeButton} onClick={closeModal}>×</button>
            </div>

            <img
              src={selectedProduct.images[0]?.src}
              alt={selectedProduct.name}
              style={styles.modalImage}
            />

            <div style={styles.modalPrice}>${selectedProduct.price}</div>

            <div
              style={styles.modalDescription}
              dangerouslySetInnerHTML={{ __html: selectedProduct.shortDescription || selectedProduct.description }}
            />

            <button
              style={styles.addToCartButton}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              Add to Cart
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
