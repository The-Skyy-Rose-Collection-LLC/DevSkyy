/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { SuccessCelebration } from '../SuccessCelebration';

// Mock canvas context for confetti animation
beforeAll(() => {
  HTMLCanvasElement.prototype.getContext = jest.fn(() => ({
    clearRect: jest.fn(),
    save: jest.fn(),
    restore: jest.fn(),
    translate: jest.fn(),
    rotate: jest.fn(),
    fillRect: jest.fn(),
    fillStyle: '',
    globalAlpha: 1,
  })) as any;
});

describe('SuccessCelebration', () => {
  const defaultProps = {
    orderId: 'ORD-12345',
    orderTotal: 149.99,
    currency: 'USD',
    customerEmail: 'test@example.com',
    onContinueShopping: jest.fn(),
    onViewOrder: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders order confirmation message', () => {
    render(<SuccessCelebration {...defaultProps} />);
    jest.advanceTimersByTime(100);
    expect(screen.getByText('Order Confirmed!')).toBeInTheDocument();
  });

  it('displays correct order ID', () => {
    render(<SuccessCelebration {...defaultProps} />);
    expect(screen.getByText('ORD-12345')).toBeInTheDocument();
  });

  it('displays formatted order total', () => {
    render(<SuccessCelebration {...defaultProps} />);
    expect(screen.getByText('$149.99')).toBeInTheDocument();
  });

  it('displays customer email', () => {
    render(<SuccessCelebration {...defaultProps} />);
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  it('calls onContinueShopping when button clicked', () => {
    render(<SuccessCelebration {...defaultProps} />);
    const button = screen.getByLabelText('Continue shopping');
    fireEvent.click(button);
    expect(defaultProps.onContinueShopping).toHaveBeenCalledTimes(1);
  });

  it('calls onViewOrder with orderId when View Order button clicked', () => {
    render(<SuccessCelebration {...defaultProps} />);
    const button = screen.getByLabelText('View order details');
    fireEvent.click(button);
    expect(defaultProps.onViewOrder).toHaveBeenCalledWith('ORD-12345');
  });

  it('renders with correct aria attributes for accessibility', () => {
    render(<SuccessCelebration {...defaultProps} />);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'success-title');
  });
});
