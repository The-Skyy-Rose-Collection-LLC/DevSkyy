/**
 * Product Quick-View Modal
 *
 * Accessible modal for product preview with:
 * - Image gallery with thumbnails and arrow navigation
 * - Product details (name, description, price)
 * - Add to cart functionality
 * - Keyboard navigation (ESC to close, arrows for images)
 * - Focus trap and ARIA labels
 * - Smooth animations
 *
 * @component
 */

import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import type { Product } from '../../types/collections';

export interface ProductModalProps {
  product: Product | null;
  onClose: () => void;
  onAddToCart?: (product: Product) => void;
  accentColor?: string;
}

export const ProductModal: React.FC<ProductModalProps> = ({
  product,
  onClose,
  onAddToCart,
  accentColor = '#B76E79',
}) => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Reset image index when product changes
  useEffect(() => {
    setCurrentImageIndex(0);
  }, [product]);

  // Focus trap and keyboard navigation
  useEffect(() => {
    if (!product) return;

    // Focus close button when modal opens
    closeButtonRef.current?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        navigateImage('prev');
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        navigateImage('next');
      } else if (e.key === 'Tab') {
        // Focus trap: keep focus within modal
        const modal = modalRef.current;
        if (!modal) return;

        const focusableElements = modal.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [product, onClose]);

  const navigateImage = (direction: 'prev' | 'next') => {
    if (!product?.images.length) return;

    setIsAnimating(true);
    setTimeout(() => setIsAnimating(false), 300);

    setCurrentImageIndex((prev) => {
      if (direction === 'prev') {
        return prev > 0 ? prev - 1 : product.images.length - 1;
      } else {
        return prev < product.images.length - 1 ? prev + 1 : 0;
      }
    });
  };

  const handleAddToCart = () => {
    if (product && onAddToCart) {
      onAddToCart(product);
    }
  };

  if (!product) return null;

  const currentImage = product.images[currentImageIndex];
  const hasMultipleImages = product.images.length > 1;

  const styles = {
    overlay: {
      position: 'fixed' as const,
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '2rem',
      animation: 'fadeIn 0.2s ease-out',
      backdropFilter: 'blur(8px)',
    },
    modal: {
      backgroundColor: '#ffffff',
      borderRadius: '12px',
      maxWidth: '900px',
      width: '100%',
      maxHeight: '90vh',
      overflow: 'auto',
      position: 'relative' as const,
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: '2rem',
      padding: '2rem',
      animation: 'slideUp 0.3s ease-out',
      boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
    },
    closeButton: {
      position: 'absolute' as const,
      top: '1rem',
      right: '1rem',
      background: 'none',
      border: 'none',
      fontSize: '2rem',
      cursor: 'pointer',
      color: '#666',
      width: '40px',
      height: '40px',
      borderRadius: '50%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'all 0.2s ease',
      zIndex: 10,
    },
    imageSection: {
      position: 'relative' as const,
    },
    mainImage: {
      width: '100%',
      height: '500px',
      objectFit: 'cover' as const,
      borderRadius: '8px',
      transition: 'opacity 0.3s ease',
      opacity: isAnimating ? 0.5 : 1,
    },
    imageNavButton: {
      position: 'absolute' as const,
      top: '50%',
      transform: 'translateY(-50%)',
      background: 'rgba(255, 255, 255, 0.9)',
      border: 'none',
      borderRadius: '50%',
      width: '40px',
      height: '40px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer',
      fontSize: '1.5rem',
      color: '#333',
      transition: 'all 0.2s ease',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
    },
    prevButton: {
      left: '10px',
    },
    nextButton: {
      right: '10px',
    },
    thumbnails: {
      display: 'flex',
      gap: '0.5rem',
      marginTop: '1rem',
      overflowX: 'auto' as const,
      padding: '0.5rem 0',
    },
    thumbnail: {
      width: '80px',
      height: '80px',
      objectFit: 'cover' as const,
      borderRadius: '4px',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      flexShrink: 0,
    },
    thumbnailActive: {
      border: `3px solid ${accentColor}`,
      opacity: 1,
    },
    thumbnailInactive: {
      border: '3px solid transparent',
      opacity: 0.6,
    },
    detailsSection: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: '1.5rem',
    },
    title: {
      fontSize: '2rem',
      fontWeight: 600,
      color: '#1a1a1a',
      margin: 0,
      paddingRight: '3rem', // Space for close button
    },
    price: {
      fontSize: '1.75rem',
      fontWeight: 700,
      color: accentColor,
    },
    description: {
      fontSize: '1rem',
      lineHeight: 1.6,
      color: '#666',
      flex: 1,
    },
    addToCartButton: {
      background: accentColor,
      color: '#ffffff',
      border: 'none',
      borderRadius: '8px',
      padding: '1rem 2rem',
      fontSize: '1.1rem',
      fontWeight: 600,
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      textTransform: 'uppercase' as const,
      letterSpacing: '0.05em',
      marginTop: 'auto',
    },
    imageCounter: {
      position: 'absolute' as const,
      bottom: '10px',
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'rgba(0, 0, 0, 0.7)',
      color: '#ffffff',
      padding: '0.5rem 1rem',
      borderRadius: '20px',
      fontSize: '0.9rem',
      fontWeight: 500,
    },
  };

  const modalContent = (
    <div
      style={styles.overlay}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        ref={modalRef}
        style={styles.modal}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          ref={closeButtonRef}
          style={styles.closeButton}
          onClick={onClose}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#f0f0f0';
            e.currentTarget.style.color = '#333';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.color = '#666';
          }}
          aria-label="Close modal"
        >
          ×
        </button>

        {/* Image Section */}
        <div style={styles.imageSection}>
          <img
            src={currentImage?.src}
            alt={`${product.name} - Image ${currentImageIndex + 1}`}
            style={styles.mainImage}
          />

          {hasMultipleImages && (
            <>
              <button
                style={{ ...styles.imageNavButton, ...styles.prevButton }}
                onClick={() => navigateImage('prev')}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#ffffff';
                  e.currentTarget.style.transform = 'translateY(-50%) scale(1.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
                  e.currentTarget.style.transform = 'translateY(-50%) scale(1)';
                }}
                aria-label="Previous image"
              >
                ‹
              </button>

              <button
                style={{ ...styles.imageNavButton, ...styles.nextButton }}
                onClick={() => navigateImage('next')}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#ffffff';
                  e.currentTarget.style.transform = 'translateY(-50%) scale(1.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
                  e.currentTarget.style.transform = 'translateY(-50%) scale(1)';
                }}
                aria-label="Next image"
              >
                ›
              </button>

              <div style={styles.imageCounter}>
                {currentImageIndex + 1} / {product.images.length}
              </div>
            </>
          )}

          {/* Thumbnails */}
          {hasMultipleImages && (
            <div style={styles.thumbnails}>
              {product.images.map((image, index) => (
                <img
                  key={image.id}
                  src={image.src}
                  alt={`${product.name} thumbnail ${index + 1}`}
                  style={{
                    ...styles.thumbnail,
                    ...(index === currentImageIndex
                      ? styles.thumbnailActive
                      : styles.thumbnailInactive),
                  }}
                  onClick={() => {
                    setIsAnimating(true);
                    setTimeout(() => setIsAnimating(false), 300);
                    setCurrentImageIndex(index);
                  }}
                  onMouseEnter={(e) => {
                    if (index !== currentImageIndex) {
                      (e.currentTarget as HTMLImageElement).style.opacity = '1';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (index !== currentImageIndex) {
                      (e.currentTarget as HTMLImageElement).style.opacity = '0.6';
                    }
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Details Section */}
        <div style={styles.detailsSection}>
          <h2 id="modal-title" style={styles.title}>
            {product.name}
          </h2>

          <div style={styles.price}>
            ${parseFloat(product.price).toFixed(2)}
          </div>

          <div
            style={styles.description}
            dangerouslySetInnerHTML={{
              __html: product.shortDescription || product.description,
            }}
          />

          <button
            style={styles.addToCartButton}
            onClick={handleAddToCart}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = `0 6px 20px ${accentColor}66`;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
            }}
            aria-label={`Add ${product.name} to cart`}
          >
            Add to Cart
          </button>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @media (max-width: 768px) {
          ${JSON.stringify(styles.modal).replace(/"gridTemplateColumns":"1fr 1fr"/, '"gridTemplateColumns":"1fr"')}
        }
      `}</style>
    </div>
  );

  // Render modal in a portal at document.body
  return createPortal(modalContent, document.body);
};

export default ProductModal;
