/**
 * ProductCard Component
 *
 * Luxury product card with CSS-based parallax hover effects.
 * Uses product images directly from WordPress (no pre-generated assets).
 *
 * @component
 */

import React, { useState } from 'react';
import type { Product } from '../../types/collections';

export interface ProductCardProps {
  /** Product data from WordPress */
  product: Product;

  /** Callback when card is clicked */
  onClick?: (product: Product) => void;

  /** Collection theme color for accents */
  accentColor?: string;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onClick,
  accentColor = '#B76E79',
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5; // -0.5 to 0.5
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setMousePosition({ x, y });
  };

  const handleMouseEnter = () => setIsHovered(true);
  const handleMouseLeave = () => {
    setIsHovered(false);
    setMousePosition({ x: 0, y: 0 });
  };

  const handleClick = () => {
    if (onClick) onClick(product);
  };

  // Calculate parallax transforms
  const parallaxX = mousePosition.x * 20; // Max 10px movement
  const parallaxY = mousePosition.y * 20;
  const scale = isHovered ? 1.05 : 1;
  const shadowDepth = isHovered ? 30 : 10;

  const primaryImage = product.images[0]?.src || '/placeholder-product.jpg';

  const styles = {
    card: {
      position: 'relative' as const,
      cursor: 'pointer',
      borderRadius: '12px',
      overflow: 'hidden',
      backgroundColor: '#ffffff',
      boxShadow: `0 ${shadowDepth}px ${shadowDepth * 2}px rgba(0, 0, 0, ${isHovered ? 0.15 : 0.08})`,
      transition: 'box-shadow 0.3s ease, transform 0.3s ease',
      transform: `scale(${scale})`,
    },
    imageContainer: {
      position: 'relative' as const,
      width: '100%',
      paddingBottom: '133.33%', // 3:4 aspect ratio
      overflow: 'hidden',
      backgroundColor: '#f5f5f5',
    },
    image: {
      position: 'absolute' as const,
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      objectFit: 'cover' as const,
      transition: 'transform 0.3s ease',
      transform: `translate(${parallaxX}px, ${parallaxY}px) scale(${isHovered ? 1.1 : 1})`,
    },
    overlay: {
      position: 'absolute' as const,
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: `linear-gradient(to bottom, transparent 0%, rgba(0, 0, 0, ${isHovered ? 0.3 : 0}) 100%)`,
      transition: 'background 0.3s ease',
      pointerEvents: 'none' as const,
    },
    quickView: {
      position: 'absolute' as const,
      bottom: '1rem',
      left: '50%',
      transform: `translateX(-50%) translateY(${isHovered ? '0' : '20px'})`,
      opacity: isHovered ? 1 : 0,
      transition: 'opacity 0.3s ease, transform 0.3s ease',
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(10px)',
      padding: '0.5rem 1.5rem',
      borderRadius: '24px',
      fontSize: '0.85rem',
      fontWeight: 600,
      letterSpacing: '0.05em',
      color: '#1a1a1a',
      border: `1px solid ${accentColor}`,
      pointerEvents: 'none' as const,
    },
    details: {
      padding: '1.25rem',
    },
    name: {
      fontSize: '1.1rem',
      fontWeight: 600,
      color: '#1a1a1a',
      marginBottom: '0.5rem',
      lineHeight: 1.3,
      minHeight: '2.6em',
      display: '-webkit-box',
      WebkitLineClamp: 2,
      WebkitBoxOrient: 'vertical' as const,
      overflow: 'hidden',
    },
    priceContainer: {
      display: 'flex',
      alignItems: 'baseline',
      gap: '0.5rem',
      marginBottom: '0.25rem',
    },
    price: {
      fontSize: '1.25rem',
      fontWeight: 700,
      color: accentColor,
    },
    regularPrice: {
      fontSize: '0.95rem',
      fontWeight: 400,
      color: '#999',
      textDecoration: 'line-through',
    },
    stock: {
      fontSize: '0.85rem',
      color: product.inStock ? '#22c55e' : '#999',
      fontWeight: 500,
    },
    badge: {
      position: 'absolute' as const,
      top: '1rem',
      right: '1rem',
      background: accentColor,
      color: '#ffffff',
      padding: '0.25rem 0.75rem',
      borderRadius: '24px',
      fontSize: '0.75rem',
      fontWeight: 700,
      letterSpacing: '0.05em',
      textTransform: 'uppercase' as const,
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
    },
  };

  const isOnSale = product.salePrice && parseFloat(product.salePrice) < parseFloat(product.regularPrice);

  return (
    <div
      style={styles.card}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={`View ${product.name}`}
    >
      <div style={styles.imageContainer}>
        <img
          src={primaryImage}
          alt={product.images[0]?.alt || product.name}
          style={styles.image}
          loading="lazy"
        />
        <div style={styles.overlay} />
        <div style={styles.quickView}>Quick View</div>

        {isOnSale && <div style={styles.badge}>Sale</div>}
      </div>

      <div style={styles.details}>
        <h3 style={styles.name}>{product.name}</h3>

        <div style={styles.priceContainer}>
          <span style={styles.price}>
            ${isOnSale ? product.salePrice : product.price}
          </span>
          {isOnSale && (
            <span style={styles.regularPrice}>${product.regularPrice}</span>
          )}
        </div>

        <div style={styles.stock}>
          {product.inStock ? 'In Stock' : 'Out of Stock'}
        </div>
      </div>
    </div>
  );
};

export default ProductCard;
