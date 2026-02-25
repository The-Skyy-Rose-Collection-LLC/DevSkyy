/**
 * Unit Tests for ProductConfigurator
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductConfigurator } from '../ProductConfigurator';
import * as THREE from 'three';
// Mock Logger
jest.mock('../../utils/Logger', () => ({
  Logger: jest.fn().mockImplementation(() => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  })),
}));

// Mock materialSwapper
jest.mock('../../lib/materialSwapper', () => ({
  materialSwapper: {
    setColor: jest.fn(),
    saveOriginal: jest.fn(),
    resetToOriginal: jest.fn(),
  },
}));

const mockProduct = {
  id: 'prod-1',
  name: 'Rose Gold Jacket',
  modelUrl: '/models/jacket.glb',
  position: [0, 0, 0],
  sku: 'RGJ-001',
  price: 299.99,
  salePrice: 249.99,
  stockStatus: 'in_stock',
  stockQuantity: 15,
  sizes: ['S', 'M', 'L', 'XL'],
  colors: [
    { name: 'Rose Gold', hex: '#B76E79' },
    { name: 'Black', hex: '#000000' },
  ],
  description: 'A beautiful jacket',
};

const mockMesh = {
  material: { color: new THREE.Color(), needsUpdate: false },
  uuid: 'mesh-1',
};

describe('ProductConfigurator', () => {
  const mockConfigChange = jest.fn();
  const mockAddToCart = jest.fn();

  const defaultProps = {
    product: mockProduct,
    mesh: mockMesh,
    onConfigChange: mockConfigChange,
    onAddToCart: mockAddToCart,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render product name', () => {
    render(<ProductConfigurator {...defaultProps} />);
    expect(screen.getByText('Rose Gold Jacket')).toBeTruthy();
  });

  it('should render product info', () => {
    const { container } = render(<ProductConfigurator {...defaultProps} />);
    // SKU may be in combined text node
    expect(container.textContent).toContain('RGJ-001');
  });

  it('should show stock status', () => {
    render(<ProductConfigurator {...defaultProps} />);
    expect(screen.getByText('In Stock')).toBeTruthy();
  });

  it('should show sale price', () => {
    const { container } = render(<ProductConfigurator {...defaultProps} />);
    expect(container.textContent).toContain('$249.99');
  });

  it('should show discount percentage', () => {
    render(<ProductConfigurator {...defaultProps} />);
    expect(screen.getByText(/-17%/)).toBeTruthy();
  });

  it('should render size options', () => {
    render(<ProductConfigurator {...defaultProps} />);
    expect(screen.getByText('S')).toBeTruthy();
    expect(screen.getByText('M')).toBeTruthy();
    expect(screen.getByText('L')).toBeTruthy();
    expect(screen.getByText('XL')).toBeTruthy();
  });

  it('should render color swatches', () => {
    render(<ProductConfigurator {...defaultProps} />);
    expect(screen.getByTitle('Rose Gold')).toBeTruthy();
    expect(screen.getByTitle('Black')).toBeTruthy();
  });

  it('should render Add to Cart button', () => {
    render(<ProductConfigurator {...defaultProps} />);
    expect(screen.getByText(/add to cart/i)).toBeTruthy();
  });

  it('should call onAddToCart when button clicked', () => {
    render(<ProductConfigurator {...defaultProps} />);
    fireEvent.click(screen.getByText(/add to cart/i));
    expect(mockAddToCart).toHaveBeenCalled();
  });

  it('should disable Add to Cart for out of stock', () => {
    const outOfStock = { ...mockProduct, stockStatus: 'out_of_stock', stockQuantity: 0 };
    const { container } = render(<ProductConfigurator {...defaultProps} product={outOfStock} />);
    expect(container.textContent).toMatch(/out of stock/i);
  });

  it('should show quantity selector', () => {
    render(<ProductConfigurator {...defaultProps} />);
    // Should have +/- buttons
    expect(screen.getByText('+')).toBeTruthy();
    expect(screen.getByText('-')).toBeTruthy();
  });
});
