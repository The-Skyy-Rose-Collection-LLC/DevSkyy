/**
 * Unit Tests for PriceTag3D
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { PriceTag3D, createPriceTag3DObject, setupCSS2DRenderer, updateCSS2DRenderer } from '../PriceTag3D';
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

// Mock CSS2DRenderer
const mockRender = jest.fn();
jest.mock('three/examples/jsm/renderers/CSS2DRenderer.js', () => ({
  CSS2DRenderer: jest.fn().mockImplementation(() => ({
    setSize: jest.fn(),
    render: mockRender,
    domElement: Object.assign(document.createElement('div'), {
      style: { position: '', top: '', left: '', pointerEvents: '' },
    }),
  })),
  CSS2DObject: jest.fn().mockImplementation((element) => ({
    element,
    position: { copy: jest.fn() },
    layers: { set: jest.fn() },
  })),
}));

describe('PriceTag3D Component', () => {
  const defaultProps = {
    position: new THREE.Vector3(0, 1, 0),
    price: 199.99,
    currency: 'USD',
    productId: 'prod-1',
  };

  it('should render regular price', () => {
    render(<PriceTag3D {...defaultProps} />);
    expect(screen.getByText('$199.99')).toBeTruthy();
  });

  it('should render sale price when discounted', () => {
    render(<PriceTag3D {...defaultProps} salePrice={149.99} />);
    expect(screen.getByText('$149.99')).toBeTruthy();
    expect(screen.getByText('$199.99')).toBeTruthy();
  });

  it('should show discount percentage', () => {
    render(<PriceTag3D {...defaultProps} salePrice={100} />);
    expect(screen.getByText('-50%')).toBeTruthy();
  });

  it('should show SALE indicator for discounted items', () => {
    render(<PriceTag3D {...defaultProps} salePrice={100} />);
    expect(screen.getByText('SALE')).toBeTruthy();
  });

  it('should not show SALE for regular priced items', () => {
    render(<PriceTag3D {...defaultProps} />);
    expect(screen.queryByText('SALE')).toBeNull();
  });

  it('should not show discount badge when discount is 0', () => {
    render(<PriceTag3D {...defaultProps} salePrice={199.99} />);
    expect(screen.queryByText(/-\d+%/)).toBeNull();
  });

  it('should default currency to USD', () => {
    render(<PriceTag3D position={new THREE.Vector3()} price={50} />);
    expect(screen.getByText('$50.00')).toBeTruthy();
  });
});

describe('createPriceTag3DObject', () => {
  beforeEach(() => {
    // Clean up animation style
    const el = document.getElementById('price-tag-3d-animations');
    if (el) el.remove();
  });

  it('should create CSS2DObject for regular price', () => {
    const pos = new THREE.Vector3(1, 2, 3);
    const obj = createPriceTag3DObject(pos, 100);

    expect(obj).toBeDefined();
    expect(obj.position.copy).toHaveBeenCalledWith(pos);
    expect(obj.element).toBeInstanceOf(HTMLDivElement);
    expect(obj.element.textContent).toContain('$100.00');
  });

  it('should render sale price and original when discounted', () => {
    const obj = createPriceTag3DObject(new THREE.Vector3(), 200, 150);

    expect(obj.element.textContent).toContain('$150.00');
    expect(obj.element.textContent).toContain('$200.00');
  });

  it('should show SALE indicator for discounted items', () => {
    const obj = createPriceTag3DObject(new THREE.Vector3(), 200, 100);

    expect(obj.element.textContent).toContain('SALE');
  });

  it('should show discount badge', () => {
    const obj = createPriceTag3DObject(new THREE.Vector3(), 200, 100);

    expect(obj.element.textContent).toContain('-50%');
  });

  it('should not show SALE for regular price', () => {
    const obj = createPriceTag3DObject(new THREE.Vector3(), 100);

    expect(obj.element.textContent).not.toContain('SALE');
  });

  it('should inject pulse animation styles into document head', () => {
    createPriceTag3DObject(new THREE.Vector3(), 200, 100);

    const style = document.getElementById('price-tag-3d-animations');
    expect(style).not.toBeNull();
    expect(style.textContent).toContain('@keyframes pulse');
  });

  it('should not duplicate animation styles', () => {
    createPriceTag3DObject(new THREE.Vector3(), 200, 100);
    createPriceTag3DObject(new THREE.Vector3(), 300, 150);

    const styles = document.querySelectorAll('#price-tag-3d-animations');
    expect(styles.length).toBe(1);
  });

  it('should add hover effects to container', () => {
    const obj = createPriceTag3DObject(new THREE.Vector3(), 100);
    const container = obj.element;

    // Simulate mouseenter
    container.dispatchEvent(new Event('mouseenter'));
    expect(container.style.transform).toBe('scale(1.05)');

    // Simulate mouseleave
    container.dispatchEvent(new Event('mouseleave'));
    expect(container.style.transform).toBe('scale(1)');
  });

  it('should accept custom currency', () => {
    const obj = createPriceTag3DObject(new THREE.Vector3(), 50, undefined, 'EUR');
    expect(obj.element.textContent).toContain('50.00');
  });
});

describe('setupCSS2DRenderer', () => {
  it('should create and configure CSS2DRenderer', () => {
    const container = document.createElement('div');
    Object.defineProperty(container, 'clientWidth', { value: 800 });
    Object.defineProperty(container, 'clientHeight', { value: 600 });

    const renderer = setupCSS2DRenderer(container);

    expect(renderer).toBeDefined();
    expect(renderer.setSize).toHaveBeenCalledWith(800, 600);
    expect(container.children.length).toBe(1);
  });
});

describe('updateCSS2DRenderer', () => {
  it('should call renderer.render with scene and camera', () => {
    mockRender.mockClear();
    const container = document.createElement('div');
    Object.defineProperty(container, 'clientWidth', { value: 800 });
    Object.defineProperty(container, 'clientHeight', { value: 600 });
    const renderer = setupCSS2DRenderer(container);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera();

    updateCSS2DRenderer(renderer, scene, camera);

    expect(mockRender).toHaveBeenCalledWith(scene, camera);
  });
});
