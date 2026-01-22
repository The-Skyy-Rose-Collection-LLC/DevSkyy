/**
 * DevSkyy Cart Modal Component
 * Slide-in shopping cart UI with SkyyRose branding
 * Three.js E-commerce Integration
 */

import React, { useEffect, useCallback } from 'react';
import { useCart } from '../hooks/useCart.js';
import type { CartItem } from '../lib/cart.js';

// SkyyRose Brand Colors
const COLORS = {
  roseGold: '#B76E79',
  black: '#1A1A1A',
  white: '#FFFFFF',
  lightGray: '#F5F5F5',
  mediumGray: '#CCCCCC',
  darkGray: '#666666',
  error: '#DC2626',
  success: '#10B981',
  overlay: 'rgba(0, 0, 0, 0.5)',
};

// Component Props
export interface CartModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCheckout?: () => void;
}

/**
 * Cart Item Row Component
 * Memoized to prevent unnecessary re-renders when parent state changes
 */
const CartItemRow: React.FC<{
  item: CartItem;
  onUpdateQuantity: (productId: string, quantity: number, size?: string, color?: string) => void;
  onRemove: (productId: string, size?: string, color?: string) => void;
}> = React.memo(({ item, onUpdateQuantity, onRemove }) => {
  const price = item.salePrice ?? item.price;
  const itemTotal = price * item.quantity;

  return (
    <div
      style={{
        display: 'flex',
        gap: '16px',
        padding: '16px',
        borderBottom: `1px solid ${COLORS.lightGray}`,
        alignItems: 'flex-start',
      }}
    >
      {/* Product Image */}
      {item.imageUrl && (
        <div
          style={{
            width: '80px',
            height: '80px',
            flexShrink: 0,
            borderRadius: '8px',
            overflow: 'hidden',
            backgroundColor: COLORS.lightGray,
          }}
        >
          <img
            src={item.imageUrl}
            alt={item.name}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        </div>
      )}

      {/* Product Details */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <h4
          style={{
            margin: '0 0 8px 0',
            fontSize: '16px',
            fontWeight: 600,
            color: COLORS.black,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {item.name}
        </h4>

        {/* Size and Color */}
        {(item.size || item.color) && (
          <div
            style={{
              fontSize: '14px',
              color: COLORS.darkGray,
              marginBottom: '8px',
            }}
          >
            {item.size && <span>Size: {item.size}</span>}
            {item.size && item.color && <span style={{ margin: '0 8px' }}>|</span>}
            {item.color && <span>Color: {item.color}</span>}
          </div>
        )}

        {/* Price */}
        <div style={{ fontSize: '14px', marginBottom: '8px' }}>
          {item.salePrice ? (
            <>
              <span
                style={{
                  color: COLORS.error,
                  fontWeight: 600,
                  marginRight: '8px',
                }}
              >
                ${item.salePrice.toFixed(2)}
              </span>
              <span
                style={{
                  color: COLORS.mediumGray,
                  textDecoration: 'line-through',
                  fontSize: '12px',
                }}
              >
                ${item.price.toFixed(2)}
              </span>
            </>
          ) : (
            <span style={{ color: COLORS.black, fontWeight: 600 }}>
              ${item.price.toFixed(2)}
            </span>
          )}
        </div>

        {/* Quantity Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className="cart-quantity-btn"
            onClick={() => onUpdateQuantity(item.productId, item.quantity - 1, item.size, item.color)}
            aria-label="Decrease quantity"
            style={{
              width: '28px',
              height: '28px',
              border: `1px solid ${COLORS.mediumGray}`,
              borderRadius: '4px',
              backgroundColor: COLORS.white,
              color: COLORS.black,
              fontSize: '16px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s',
            }}
            disabled={item.quantity <= 1}
          >
            -
          </button>

          <span
            style={{
              minWidth: '32px',
              textAlign: 'center',
              fontSize: '14px',
              fontWeight: 600,
              color: COLORS.black,
            }}
          >
            {item.quantity}
          </span>

          <button
            className="cart-quantity-btn"
            onClick={() => onUpdateQuantity(item.productId, item.quantity + 1, item.size, item.color)}
            aria-label="Increase quantity"
            style={{
              width: '28px',
              height: '28px',
              border: `1px solid ${COLORS.mediumGray}`,
              borderRadius: '4px',
              backgroundColor: COLORS.white,
              color: COLORS.black,
              fontSize: '16px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s',
            }}
          >
            +
          </button>

          <button
            className="cart-remove-btn"
            onClick={() => onRemove(item.productId, item.size, item.color)}
            aria-label={`Remove ${item.name} from cart`}
            style={{
              marginLeft: 'auto',
              padding: '4px 8px',
              border: 'none',
              backgroundColor: 'transparent',
              color: COLORS.error,
              fontSize: '12px',
              cursor: 'pointer',
              textDecoration: 'underline',
              transition: 'opacity 0.2s',
            }}
          >
            Remove
          </button>
        </div>
      </div>

      {/* Item Total */}
      <div
        style={{
          fontSize: '16px',
          fontWeight: 600,
          color: COLORS.black,
          flexShrink: 0,
        }}
      >
        ${itemTotal.toFixed(2)}
      </div>
    </div>
  );
});

/**
 * Cart Modal Component
 */
export const CartModal: React.FC<CartModalProps> = ({ isOpen, onClose, onCheckout }) => {
  const {
    items,
    subtotal,
    tax,
    total,
    itemCount,
    currency,
    updateQuantity,
    removeItem,
    clearCart,
    error,
  } = useCart();

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent): void => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // Handle checkout
  const handleCheckout = useCallback(() => {
    if (onCheckout) {
      onCheckout();
    } else {
      // Default behavior: log to console
      console.log('Checkout clicked', { items, total });
    }
  }, [onCheckout, items, total]);

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: COLORS.overlay,
          zIndex: 9998,
          animation: 'fadeIn 0.3s ease-in-out',
        }}
      />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="cart-title"
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: '100%',
          maxWidth: '480px',
          backgroundColor: COLORS.white,
          boxShadow: '-4px 0 24px rgba(0, 0, 0, 0.2)',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          animation: 'slideInRight 0.3s ease-in-out',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '24px',
            borderBottom: `2px solid ${COLORS.roseGold}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <h2
              id="cart-title"
              style={{
                margin: 0,
                fontSize: '24px',
                fontWeight: 700,
                color: COLORS.black,
              }}
            >
              Shopping Cart
            </h2>
            <p
              style={{
                margin: '4px 0 0 0',
                fontSize: '14px',
                color: COLORS.darkGray,
              }}
            >
              {itemCount} {itemCount === 1 ? 'item' : 'items'}
            </p>
          </div>

          <button
            className="cart-close-btn"
            onClick={onClose}
            aria-label="Close cart"
            style={{
              width: '32px',
              height: '32px',
              border: 'none',
              borderRadius: '50%',
              backgroundColor: COLORS.lightGray,
              color: COLORS.black,
              fontSize: '20px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s',
            }}
          >
            ×
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div
            style={{
              padding: '16px 24px',
              backgroundColor: '#FEE2E2',
              borderLeft: `4px solid ${COLORS.error}`,
              color: COLORS.error,
              fontSize: '14px',
            }}
          >
            {error}
          </div>
        )}

        {/* Cart Items */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            backgroundColor: COLORS.white,
          }}
        >
          {items.length === 0 ? (
            <div
              style={{
                padding: '48px 24px',
                textAlign: 'center',
                color: COLORS.darkGray,
              }}
            >
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>🛍️</div>
              <p style={{ margin: 0, fontSize: '16px' }}>Your cart is empty</p>
              <p style={{ margin: '8px 0 0 0', fontSize: '14px' }}>
                Add some items to get started
              </p>
            </div>
          ) : (
            items.map((item) => (
              <CartItemRow
                key={`${item.productId}-${item.size || ''}-${item.color || ''}`}
                item={item}
                onUpdateQuantity={updateQuantity}
                onRemove={removeItem}
              />
            ))
          )}
        </div>

        {/* Footer */}
        {items.length > 0 && (
          <div
            style={{
              padding: '24px',
              borderTop: `1px solid ${COLORS.lightGray}`,
              backgroundColor: COLORS.white,
            }}
          >
            {/* Totals */}
            <div style={{ marginBottom: '20px' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '8px',
                  fontSize: '14px',
                  color: COLORS.darkGray,
                }}
              >
                <span>Subtotal:</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '8px',
                  fontSize: '14px',
                  color: COLORS.darkGray,
                }}
              >
                <span>Tax:</span>
                <span>${tax.toFixed(2)}</span>
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  paddingTop: '12px',
                  borderTop: `1px solid ${COLORS.lightGray}`,
                  fontSize: '18px',
                  fontWeight: 700,
                  color: COLORS.black,
                }}
              >
                <span>Total:</span>
                <span style={{ color: COLORS.roseGold }}>
                  {currency} ${total.toFixed(2)}
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <button
                className="cart-checkout-btn"
                onClick={handleCheckout}
                style={{
                  width: '100%',
                  padding: '16px',
                  border: 'none',
                  borderRadius: '8px',
                  backgroundColor: COLORS.roseGold,
                  color: COLORS.white,
                  fontSize: '16px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                Checkout
              </button>

              <button
                className="cart-continue-btn"
                onClick={onClose}
                style={{
                  width: '100%',
                  padding: '16px',
                  border: `2px solid ${COLORS.roseGold}`,
                  borderRadius: '8px',
                  backgroundColor: COLORS.white,
                  color: COLORS.roseGold,
                  fontSize: '16px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                Continue Shopping
              </button>

              <button
                className="cart-clear-btn"
                onClick={clearCart}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: 'none',
                  borderRadius: '4px',
                  backgroundColor: 'transparent',
                  color: COLORS.darkGray,
                  fontSize: '14px',
                  cursor: 'pointer',
                  textDecoration: 'underline',
                  transition: 'color 0.2s',
                }}
              >
                Clear Cart
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Animations and Hover Styles */}
      <style>
        {`
          @keyframes fadeIn {
            from {
              opacity: 0;
            }
            to {
              opacity: 1;
            }
          }

          @keyframes slideInRight {
            from {
              transform: translateX(100%);
            }
            to {
              transform: translateX(0);
            }
          }

          /* Quantity buttons hover */
          .cart-quantity-btn:hover:not(:disabled) {
            border-color: #B76E79 !important;
            color: #B76E79 !important;
          }

          /* Remove button hover */
          .cart-remove-btn:hover {
            opacity: 0.7;
          }

          /* Close button hover */
          .cart-close-btn:hover {
            background-color: #B76E79 !important;
            color: #FFFFFF !important;
          }

          /* Checkout button hover */
          .cart-checkout-btn:hover {
            background-color: #A05D68 !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(183, 110, 121, 0.3);
          }

          /* Continue Shopping button hover */
          .cart-continue-btn:hover {
            background-color: #F5F5F5 !important;
          }

          /* Clear Cart button hover */
          .cart-clear-btn:hover {
            color: #DC2626 !important;
          }
        `}
      </style>
    </>
  );
};

export default CartModal;
