/**
 * Product Configurator Component
 * Interactive product configuration with live 3D material updates
 *
 * Features:
 * - Color swatches with live material updates
 * - Size selector with availability indicators
 * - Quantity selector
 * - Price display with sale pricing
 * - Add to Cart functionality
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import * as THREE from 'three';
import type { ShowroomProduct, ProductColor, StockStatus } from '../types/product.js';
import { materialSwapper } from '../lib/materialSwapper.js';
import { formatPrice, hasValidDiscount, getEffectivePrice, calculateDiscount } from '../lib/priceUtils.js';
import { Logger } from '../utils/Logger.js';

const logger = new Logger('ProductConfigurator');

export interface ProductConfig {
  selectedSize: string;
  selectedColor: ProductColor;
  quantity: number;
}

export interface ProductConfiguratorProps {
  product: ShowroomProduct;
  mesh: THREE.Mesh;
  onConfigChange: (config: ProductConfig) => void;
  onAddToCart: () => void;
}

/**
 * Get stock status badge color
 */
function getStockStatusColor(status: StockStatus): string {
  switch (status) {
    case 'in_stock':
      return '#4ade80'; // Green
    case 'low_stock':
      return '#fbbf24'; // Amber
    case 'out_of_stock':
      return '#ef4444'; // Red
    default:
      return '#6b7280'; // Gray
  }
}

/**
 * Get stock status label
 */
function getStockStatusLabel(status: StockStatus): string {
  switch (status) {
    case 'in_stock':
      return 'In Stock';
    case 'low_stock':
      return 'Low Stock';
    case 'out_of_stock':
      return 'Out of Stock';
    default:
      return 'Unknown';
  }
}

/**
 * Product Configurator Component
 */
export function ProductConfigurator({
  product,
  mesh,
  onConfigChange,
  onAddToCart,
}: ProductConfiguratorProps): React.ReactElement {
  const [selectedSize, setSelectedSize] = useState<string>(product.sizes[0] || '');
  const [selectedColor, setSelectedColor] = useState<ProductColor>(product.colors[0] || { name: 'Default', hex: '#000000' });
  const [quantity, setQuantity] = useState<number>(1);

  // Update parent when config changes
  useEffect(() => {
    onConfigChange({
      selectedSize,
      selectedColor,
      quantity,
    });
  }, [selectedSize, selectedColor, quantity, onConfigChange]);

  /**
   * Handle color selection
   */
  const handleColorChange = (color: ProductColor): void => {
    setSelectedColor(color);

    // Apply color to 3D mesh
    try {
      materialSwapper.setColor(mesh, color.hex);
      logger.info('Applied color to mesh', { productId: product.id, color: color.name });
    } catch (error) {
      logger.error('Failed to apply color to mesh', error, { productId: product.id });
    }
  };

  /**
   * Handle size selection
   */
  const handleSizeChange = (size: string): void => {
    setSelectedSize(size);
    logger.info('Size selected', { productId: product.id, size });
  };

  /**
   * Handle quantity change
   */
  const handleQuantityChange = (delta: number): void => {
    const newQuantity = Math.max(1, Math.min(product.stockQuantity, quantity + delta));
    setQuantity(newQuantity);
  };

  /**
   * Handle add to cart
   */
  const handleAddToCart = (): void => {
    if (product.stockStatus === 'out_of_stock') {
      logger.warn('Cannot add out of stock product to cart', { productId: product.id });
      return;
    }

    logger.info('Adding product to cart', {
      productId: product.id,
      size: selectedSize,
      color: selectedColor.name,
      quantity,
    });

    onAddToCart();
  };

  const hasDiscount = hasValidDiscount(product.price, product.salePrice);
  const effectivePrice = getEffectivePrice(product.price, product.salePrice);
  const discountPercent = hasDiscount && product.salePrice
    ? calculateDiscount(product.price, product.salePrice)
    : 0;

  return (
    <div className="product-configurator" style={styles['container']}>
      {/* Product Name */}
      <h2 style={styles['productName']}>{product.name}</h2>

      {/* SKU */}
      <p style={styles['sku']}>SKU: {product.sku}</p>

      {/* Stock Status */}
      <div style={styles['stockStatus']}>
        <span
          style={{
            ...styles['stockBadge'],
            backgroundColor: getStockStatusColor(product.stockStatus),
          }}
        >
          {getStockStatusLabel(product.stockStatus)}
        </span>
        {product.stockStatus !== 'out_of_stock' && (
          <span style={styles['stockQuantity']}>
            {product.stockQuantity} available
          </span>
        )}
      </div>

      {/* Price Display */}
      <div style={styles['priceContainer']}>
        {hasDiscount && product.salePrice && (
          <>
            <span style={styles['salePrice']}>{formatPrice(product.salePrice)}</span>
            <span style={styles['originalPrice']}>{formatPrice(product.price)}</span>
            <span style={styles['discountBadge']}>-{discountPercent}%</span>
          </>
        )}
        {!hasDiscount && (
          <span style={styles['regularPrice']}>{formatPrice(product.price)}</span>
        )}
      </div>

      {/* Color Selector */}
      {product.colors.length > 0 && (
        <div style={styles['section']}>
          <label style={styles['label']}>Color: {selectedColor.name}</label>
          <div style={styles['colorSwatches']}>
            {product.colors.map((color) => (
              <button
                key={color.name}
                onClick={() => handleColorChange(color)}
                style={{
                  ...styles['colorSwatch'],
                  backgroundColor: color.hex,
                  border: selectedColor.name === color.name
                    ? '3px solid #B76E79'
                    : '2px solid #333',
                }}
                title={color.name}
                aria-label={`Select ${color.name} color`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Size Selector */}
      {product.sizes.length > 0 && (
        <div style={styles['section']}>
          <label style={styles['label']}>Size</label>
          <div style={styles['sizeButtons']}>
            {product.sizes.map((size) => (
              <button
                key={size}
                onClick={() => handleSizeChange(size)}
                style={{
                  ...styles['sizeButton'],
                  ...(selectedSize === size ? styles['sizeButtonActive'] : {}),
                }}
              >
                {size}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Quantity Selector */}
      <div style={styles['section']}>
        <label style={styles['label']}>Quantity</label>
        <div style={styles['quantitySelector']}>
          <button
            onClick={() => handleQuantityChange(-1)}
            disabled={quantity <= 1}
            style={{
              ...styles['quantityButton'],
              ...(quantity <= 1 ? styles['quantityButtonDisabled'] : {}),
            }}
          >
            -
          </button>
          <span style={styles['quantityValue']}>{quantity}</span>
          <button
            onClick={() => handleQuantityChange(1)}
            disabled={quantity >= product.stockQuantity}
            style={{
              ...styles['quantityButton'],
              ...(quantity >= product.stockQuantity ? styles['quantityButtonDisabled'] : {}),
            }}
          >
            +
          </button>
        </div>
      </div>

      {/* Total Price */}
      <div style={styles['totalPrice']}>
        <span style={styles['totalLabel']}>Total:</span>
        <span style={styles['totalValue']}>
          {formatPrice(effectivePrice * quantity)}
        </span>
      </div>

      {/* Add to Cart Button */}
      <button
        onClick={handleAddToCart}
        disabled={product.stockStatus === 'out_of_stock'}
        style={{
          ...styles['addToCartButton'],
          ...(product.stockStatus === 'out_of_stock' ? styles['addToCartButtonDisabled'] : {}),
        }}
      >
        {product.stockStatus === 'out_of_stock' ? 'Out of Stock' : 'Add to Cart'}
      </button>

      {/* Description */}
      {product.description && (
        <div style={styles['description']}>
          <p>{product.description}</p>
        </div>
      )}
    </div>
  );
}

/**
 * Component Styles
 */
const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: '#1a1a1a',
    color: '#ffffff',
    padding: '24px',
    borderRadius: '12px',
    maxWidth: '400px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  productName: {
    fontSize: '24px',
    fontWeight: '600',
    marginBottom: '8px',
    color: '#ffffff',
  },
  sku: {
    fontSize: '14px',
    color: '#9ca3af',
    marginBottom: '16px',
  },
  stockStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '16px',
  },
  stockBadge: {
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '600',
    color: '#ffffff',
  },
  stockQuantity: {
    fontSize: '14px',
    color: '#9ca3af',
  },
  priceContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '24px',
  },
  regularPrice: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#ffffff',
  },
  salePrice: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#B76E79', // SkyyRose rose gold
  },
  originalPrice: {
    fontSize: '20px',
    color: '#9ca3af',
    textDecoration: 'line-through',
  },
  discountBadge: {
    padding: '4px 8px',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '600',
    backgroundColor: '#B76E79',
    color: '#ffffff',
  },
  section: {
    marginBottom: '20px',
  },
  label: {
    display: 'block',
    fontSize: '14px',
    fontWeight: '600',
    marginBottom: '8px',
    color: '#e5e7eb',
  },
  colorSwatches: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  },
  colorSwatch: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
  },
  sizeButtons: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  },
  sizeButton: {
    padding: '10px 20px',
    borderRadius: '8px',
    border: '2px solid #333',
    backgroundColor: '#2a2a2a',
    color: '#ffffff',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600',
    transition: 'all 0.2s',
  },
  sizeButtonActive: {
    backgroundColor: '#B76E79',
    borderColor: '#B76E79',
    color: '#ffffff',
  },
  quantitySelector: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  quantityButton: {
    width: '40px',
    height: '40px',
    borderRadius: '8px',
    border: '2px solid #B76E79',
    backgroundColor: '#2a2a2a',
    color: '#B76E79',
    fontSize: '20px',
    fontWeight: '700',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  quantityButtonDisabled: {
    opacity: 0.3,
    cursor: 'not-allowed',
  },
  quantityValue: {
    fontSize: '20px',
    fontWeight: '600',
    minWidth: '40px',
    textAlign: 'center',
  },
  totalPrice: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px',
    backgroundColor: '#2a2a2a',
    borderRadius: '8px',
    marginBottom: '16px',
  },
  totalLabel: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#e5e7eb',
  },
  totalValue: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#B76E79',
  },
  addToCartButton: {
    width: '100%',
    padding: '16px',
    borderRadius: '8px',
    border: 'none',
    backgroundColor: '#B76E79',
    color: '#ffffff',
    fontSize: '16px',
    fontWeight: '700',
    cursor: 'pointer',
    transition: 'all 0.2s',
    marginBottom: '16px',
  },
  addToCartButtonDisabled: {
    backgroundColor: '#4b5563',
    cursor: 'not-allowed',
    opacity: 0.6,
  },
  description: {
    fontSize: '14px',
    color: '#9ca3af',
    lineHeight: '1.6',
    paddingTop: '16px',
    borderTop: '1px solid #333',
  },
};

export default ProductConfigurator;
