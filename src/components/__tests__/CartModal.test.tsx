/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { CartModal } from '../CartModal';

// Mock useCart hook
jest.mock('../../hooks/useCart', () => ({
  useCart: () => ({
    items: [],
    subtotal: 0,
    tax: 0,
    total: 0,
    itemCount: 0,
    currency: 'USD',
    updateQuantity: jest.fn(),
    removeItem: jest.fn(),
    clearCart: jest.fn(),
    error: null,
  }),
}));

describe('CartModal', () => {
  const mockOnClose = jest.fn();
  const mockOnCheckout = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders nothing when isOpen is false', () => {
    const { container } = render(
      <CartModal isOpen={false} onClose={mockOnClose} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders cart title when isOpen is true', () => {
    render(<CartModal isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByText('Shopping Cart')).toBeInTheDocument();
  });

  it('shows empty cart message when no items', () => {
    render(<CartModal isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByText('Your cart is empty')).toBeInTheDocument();
  });

  it('calls onClose when close button clicked', () => {
    render(<CartModal isOpen={true} onClose={mockOnClose} />);
    const closeButton = screen.getByLabelText('Close cart');
    fireEvent.click(closeButton);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when Escape key pressed', () => {
    render(<CartModal isOpen={true} onClose={mockOnClose} />);
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('renders with correct aria attributes for accessibility', () => {
    render(<CartModal isOpen={true} onClose={mockOnClose} />);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'cart-title');
  });
});
