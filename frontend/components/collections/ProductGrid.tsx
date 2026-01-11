/**
 * ProductGrid Component
 *
 * Responsive grid layout for product cards.
 * 3 columns desktop, 2 tablet, 1 mobile.
 *
 * @component
 */

import React from 'react';
import { ProductCard } from './ProductCard';
import { ScrollAnimatedSection } from './ScrollAnimatedSection';
import type { Product } from '../../types/collections';

export interface ProductGridProps {
  /** Products to display */
  products: Product[];

  /** Loading state */
  loading?: boolean;

  /** Error message */
  error?: string | null;

  /** Retry callback */
  onRetry?: () => void;

  /** Product click handler */
  onProductClick?: (product: Product) => void;

  /** Collection theme color */
  accentColor?: string;
}

export const ProductGrid: React.FC<ProductGridProps> = ({
  products,
  loading = false,
  error = null,
  onRetry,
  onProductClick,
  accentColor = '#B76E79',
}) => {
  const styles = {
    container: {
      width: '100%',
      maxWidth: '1400px',
      margin: '0 auto',
      padding: '0 2rem',
    },
    grid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
      gap: '2rem',
      width: '100%',
    },
    loading: {
      display: 'flex',
      flexDirection: 'column' as const,
      alignItems: 'center',
      justifyContent: 'center',
      padding: '4rem 2rem',
      color: '#666',
      fontFamily: "'Inter', sans-serif",
    },
    loadingSpinner: {
      width: '48px',
      height: '48px',
      border: `3px solid rgba(0, 0, 0, 0.1)`,
      borderTopColor: accentColor,
      borderRadius: '50%',
      animation: 'spin 1s linear infinite',
      marginBottom: '1rem',
    },
    error: {
      display: 'flex',
      flexDirection: 'column' as const,
      alignItems: 'center',
      justifyContent: 'center',
      padding: '4rem 2rem',
      color: '#dc2626',
      fontFamily: "'Inter', sans-serif",
      textAlign: 'center' as const,
    },
    errorTitle: {
      fontSize: '1.25rem',
      fontWeight: 600,
      marginBottom: '0.5rem',
    },
    errorMessage: {
      fontSize: '1rem',
      marginBottom: '1.5rem',
      color: '#666',
    },
    retryButton: {
      background: accentColor,
      color: '#ffffff',
      border: 'none',
      padding: '0.75rem 2rem',
      borderRadius: '8px',
      fontSize: '1rem',
      fontWeight: 600,
      cursor: 'pointer',
      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
    } as React.CSSProperties,
    empty: {
      textAlign: 'center' as const,
      padding: '4rem 2rem',
      color: '#666',
      fontFamily: "'Inter', sans-serif",
    },
    emptyTitle: {
      fontSize: '1.5rem',
      fontWeight: 600,
      marginBottom: '0.5rem',
      color: '#333',
    },
    emptyMessage: {
      fontSize: '1.1rem',
    },
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>
          <div style={styles.loadingSpinner} />
          <div>Loading products...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>
          <div style={styles.errorTitle}>Failed to Load Products</div>
          <div style={styles.errorMessage}>{error}</div>
          {onRetry && (
            <button
              style={styles.retryButton}
              onClick={onRetry}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.empty}>
          <div style={styles.emptyTitle}>No Products Found</div>
          <div style={styles.emptyMessage}>
            This collection doesn't have any products yet.
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <style>
        {`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }

          @media (max-width: 1024px) {
            .product-grid {
              grid-template-columns: repeat(2, 1fr) !important;
              gap: 1.5rem !important;
            }
          }

          @media (max-width: 640px) {
            .product-grid {
              grid-template-columns: 1fr !important;
              gap: 1.5rem !important;
            }
          }
        `}
      </style>

      <div style={styles.container}>
        <div style={styles.grid} className="product-grid">
          {products.map((product, index) => (
            <ScrollAnimatedSection
              key={product.id}
              animation="fade-up"
              delay={index * 100}
              duration={600}
            >
              <ProductCard
                product={product}
                {...(onProductClick && { onClick: onProductClick })}
                accentColor={accentColor}
              />
            </ScrollAnimatedSection>
          ))}
        </div>
      </div>
    </>
  );
};

export default ProductGrid;
