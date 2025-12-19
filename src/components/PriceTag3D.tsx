/**
 * 3D Price Tag Component
 * HTML overlay price display using Three.js CSS2DRenderer
 *
 * Features:
 * - HTML overlays positioned in 3D space
 * - Animated sale indicators (pulsing effect)
 * - Rose gold styling for sale prices
 * - Strikethrough original price when on sale
 * - Automatic positioning relative to 3D objects
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js';
import { formatPrice, hasValidDiscount, calculateDiscount } from '../lib/priceUtils.js';
import { Logger } from '../utils/Logger.js';

const logger = new Logger('PriceTag3D');

export interface PriceTag3DProps {
  position: THREE.Vector3;
  price: number;
  salePrice?: number;
  currency?: string;
  productId?: string;
}

/**
 * 3D Price Tag Component
 */
export function PriceTag3D({
  position: _position, // Available for future CSS2D positioning
  price,
  salePrice,
  currency = 'USD',
  productId,
}: PriceTag3DProps): React.ReactElement {
  const containerRef = useRef<HTMLDivElement>(null);

  const hasDiscount = hasValidDiscount(price, salePrice);
  const discountPercent = hasDiscount && salePrice
    ? calculateDiscount(price, salePrice)
    : 0;

  useEffect(() => {
    if (containerRef.current) {
      logger.debug('Price tag mounted', { productId, hasDiscount });
    }
  }, [productId, hasDiscount]);

  return (
    <div ref={containerRef} style={styles['container']}>
      {/* Price Display */}
      <div style={styles['priceContainer']}>
        {hasDiscount && salePrice ? (
          <>
            {/* Sale Price */}
            <div style={styles['salePriceWrapper']}>
              <span style={styles['salePrice']}>{formatPrice(salePrice, currency)}</span>
              {discountPercent > 0 && (
                <span style={styles['discountBadge']}>-{discountPercent}%</span>
              )}
            </div>
            {/* Original Price (Strikethrough) */}
            <span style={styles['originalPrice']}>{formatPrice(price, currency)}</span>
          </>
        ) : (
          /* Regular Price */
          <span style={styles['regularPrice']}>{formatPrice(price, currency)}</span>
        )}
      </div>

      {/* Sale Indicator (Pulsing) */}
      {hasDiscount && (
        <div style={styles['saleIndicator']}>
          <span style={styles['saleText']}>SALE</span>
        </div>
      )}
    </div>
  );
}

/**
 * Create CSS2DObject for a price tag
 * This function is used to attach the price tag to a Three.js scene
 *
 * @param position - 3D position for the price tag
 * @param price - Original price
 * @param salePrice - Sale price (optional)
 * @param currency - Currency code (default: 'USD')
 * @returns CSS2DObject to be added to the scene
 */
export function createPriceTag3DObject(
  position: THREE.Vector3,
  price: number,
  salePrice?: number,
  currency: string = 'USD'
): CSS2DObject {
  const hasDiscount = hasValidDiscount(price, salePrice);
  const discountPercent = hasDiscount && salePrice
    ? calculateDiscount(price, salePrice)
    : 0;

  // Create container element
  const container = document.createElement('div');
  container.style.cssText = `
    background: rgba(26, 26, 26, 0.95);
    backdrop-filter: blur(10px);
    padding: 12px 16px;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    pointer-events: auto;
    cursor: pointer;
    transition: transform 0.3s, box-shadow 0.3s;
    border: 1px solid rgba(183, 110, 121, 0.3);
  `;

  // Add hover effect
  container.addEventListener('mouseenter', () => {
    container.style.transform = 'scale(1.05)';
    container.style.boxShadow = '0 12px 40px rgba(183, 110, 121, 0.4)';
  });
  container.addEventListener('mouseleave', () => {
    container.style.transform = 'scale(1)';
    container.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.5)';
  });

  // Price container
  const priceContainer = document.createElement('div');
  priceContainer.style.cssText = 'display: flex; flex-direction: column; gap: 4px;';

  if (hasDiscount && salePrice) {
    // Sale price wrapper
    const salePriceWrapper = document.createElement('div');
    salePriceWrapper.style.cssText = 'display: flex; align-items: center; gap: 8px;';

    // Sale price
    const salePriceEl = document.createElement('span');
    salePriceEl.textContent = formatPrice(salePrice, currency);
    salePriceEl.style.cssText = `
      font-size: 24px;
      font-weight: 700;
      color: #B76E79;
      animation: pulse 2s ease-in-out infinite;
    `;

    // Discount badge
    if (discountPercent > 0) {
      const discountBadge = document.createElement('span');
      discountBadge.textContent = `-${discountPercent}%`;
      discountBadge.style.cssText = `
        padding: 4px 8px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        background-color: #B76E79;
        color: #ffffff;
      `;
      salePriceWrapper.appendChild(discountBadge);
    }

    salePriceWrapper.appendChild(salePriceEl);
    priceContainer.appendChild(salePriceWrapper);

    // Original price (strikethrough)
    const originalPriceEl = document.createElement('span');
    originalPriceEl.textContent = formatPrice(price, currency);
    originalPriceEl.style.cssText = `
      font-size: 16px;
      color: #9ca3af;
      text-decoration: line-through;
    `;
    priceContainer.appendChild(originalPriceEl);

    // Sale indicator
    const saleIndicator = document.createElement('div');
    saleIndicator.style.cssText = `
      position: absolute;
      top: -8px;
      right: -8px;
      padding: 4px 8px;
      border-radius: 8px;
      background: linear-gradient(135deg, #B76E79, #d4af37);
      animation: pulse 2s ease-in-out infinite;
    `;

    const saleText = document.createElement('span');
    saleText.textContent = 'SALE';
    saleText.style.cssText = `
      font-size: 10px;
      font-weight: 700;
      color: #ffffff;
      letter-spacing: 1px;
    `;

    saleIndicator.appendChild(saleText);
    container.appendChild(saleIndicator);
  } else {
    // Regular price
    const regularPriceEl = document.createElement('span');
    regularPriceEl.textContent = formatPrice(price, currency);
    regularPriceEl.style.cssText = `
      font-size: 24px;
      font-weight: 700;
      color: #ffffff;
    `;
    priceContainer.appendChild(regularPriceEl);
  }

  container.appendChild(priceContainer);

  // Add pulse animation to document
  if (hasDiscount && !document.getElementById('price-tag-3d-animations')) {
    const style = document.createElement('style');
    style.id = 'price-tag-3d-animations';
    style.textContent = `
      @keyframes pulse {
        0%, 100% {
          opacity: 1;
          transform: scale(1);
        }
        50% {
          opacity: 0.8;
          transform: scale(1.05);
        }
      }
    `;
    document.head.appendChild(style);
  }

  // Create CSS2DObject
  const css2DObject = new CSS2DObject(container);
  css2DObject.position.copy(position);

  logger.debug('Created CSS2D price tag', {
    position: position.toArray(),
    price,
    salePrice,
    hasDiscount,
  });

  return css2DObject;
}

/**
 * Create and setup CSS2DRenderer
 * This function should be called once to create the CSS2D renderer overlay
 *
 * @param container - HTML container element
 * @returns CSS2DRenderer instance
 */
export function setupCSS2DRenderer(container: HTMLElement): CSS2DRenderer {
  const renderer = new CSS2DRenderer();
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.domElement.style.position = 'absolute';
  renderer.domElement.style.top = '0';
  renderer.domElement.style.left = '0';
  renderer.domElement.style.pointerEvents = 'none';

  // Append to container
  container.appendChild(renderer.domElement);

  logger.info('CSS2D renderer setup complete');

  return renderer;
}

/**
 * Update CSS2D renderer
 * Call this in your animation loop
 *
 * @param renderer - CSS2DRenderer instance
 * @param scene - Three.js scene
 * @param camera - Three.js camera
 */
export function updateCSS2DRenderer(
  renderer: CSS2DRenderer,
  scene: THREE.Scene,
  camera: THREE.Camera
): void {
  renderer.render(scene, camera);
}

/**
 * Component Styles
 */
const styles: Record<string, React.CSSProperties> = {
  container: {
    position: 'relative',
    background: 'rgba(26, 26, 26, 0.95)',
    backdropFilter: 'blur(10px)',
    padding: '12px 16px',
    borderRadius: '12px',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    pointerEvents: 'auto',
    cursor: 'pointer',
    transition: 'transform 0.3s, box-shadow 0.3s',
    border: '1px solid rgba(183, 110, 121, 0.3)',
  },
  priceContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  salePriceWrapper: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  salePrice: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#B76E79', // SkyyRose rose gold
    animation: 'pulse 2s ease-in-out infinite',
  },
  regularPrice: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#ffffff',
  },
  originalPrice: {
    fontSize: '16px',
    color: '#9ca3af',
    textDecoration: 'line-through',
  },
  discountBadge: {
    padding: '4px 8px',
    borderRadius: '8px',
    fontSize: '12px',
    fontWeight: '600',
    backgroundColor: '#B76E79',
    color: '#ffffff',
  },
  saleIndicator: {
    position: 'absolute',
    top: '-8px',
    right: '-8px',
    padding: '4px 8px',
    borderRadius: '8px',
    background: 'linear-gradient(135deg, #B76E79, #d4af37)',
    animation: 'pulse 2s ease-in-out infinite',
  },
  saleText: {
    fontSize: '10px',
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: '1px',
  },
};

export default PriceTag3D;
