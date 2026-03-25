/**
 * Unit Tests for useScrollAnimation
 * @jest-environment jsdom
 */

import React from 'react';
import { renderHook, act, render } from '@testing-library/react';
import { useScrollAnimation } from '../useScrollAnimation';

// Capture the IntersectionObserver callback so tests can trigger it
let intersectionCallback;
let mockObserve;
let mockUnobserve;
let mockDisconnect;
let MockIntersectionObserver;

function installIntersectionObserverMock() {
  mockObserve = jest.fn();
  mockUnobserve = jest.fn();
  mockDisconnect = jest.fn();
  MockIntersectionObserver = jest.fn().mockImplementation((cb) => {
    intersectionCallback = cb;
    return {
      observe: mockObserve,
      unobserve: mockUnobserve,
      disconnect: mockDisconnect,
    };
  });
  Object.defineProperty(window, 'IntersectionObserver', {
    writable: true,
    configurable: true,
    value: MockIntersectionObserver,
  });
}

function installMatchMedia(prefersReducedMotion) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: jest.fn().mockImplementation((query) => ({
      matches: prefersReducedMotion
        ? query === '(prefers-reduced-motion: reduce)'
        : false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
}

beforeEach(() => {
  jest.useFakeTimers();
  intersectionCallback = null;
  installMatchMedia(false);
  installIntersectionObserverMock();
});

afterEach(() => {
  jest.useRealTimers();
});

// Helper component that attaches a real DOM element to the hook's ref
function TestComponent({ options, onResult }) {
  const result = useScrollAnimation(options);
  // Report the result back to the test via callback ref pattern
  React.useEffect(() => {
    onResult(result);
  });
  // Attach the hook's ref to a real div element
  return React.createElement('div', { ref: result.ref, 'data-testid': 'observed' });
}

// Helper to render the hook with a real DOM element
function renderWithElement(options) {
  let latestResult = { isVisible: false, hasAnimated: false, ref: { current: null } };
  const onResult = (r) => { latestResult = r; };

  const rendered = render(
    React.createElement(TestComponent, { options: options || {}, onResult })
  );

  return {
    getResult: () => latestResult,
    unmount: rendered.unmount,
    rerender: (newOptions) => {
      rendered.rerender(
        React.createElement(TestComponent, { options: newOptions || options || {}, onResult })
      );
    },
  };
}

describe('useScrollAnimation', () => {
  it('should return ref, isVisible, and hasAnimated', () => {
    const { result } = renderHook(() => useScrollAnimation());
    expect(result.current.ref).toBeDefined();
    expect(result.current.isVisible).toBe(false);
    expect(result.current.hasAnimated).toBe(false);
  });

  it('should accept custom options', () => {
    const { result } = renderHook(() =>
      useScrollAnimation({ threshold: 0.5, rootMargin: '10px', once: false, delay: 200 })
    );
    expect(result.current).toBeDefined();
  });

  it('should default once to true', () => {
    const { result } = renderHook(() => useScrollAnimation());
    expect(result.current.hasAnimated).toBe(false);
  });

  // --- Tests covering lines 59-101 ---

  describe('with element attached (lines 59-101)', () => {
    it('should set isVisible and hasAnimated immediately when prefers-reduced-motion is enabled', () => {
      installMatchMedia(true);
      installIntersectionObserverMock();

      const { getResult } = renderWithElement({});

      expect(getResult().isVisible).toBe(true);
      expect(getResult().hasAnimated).toBe(true);
      // Should NOT have created an IntersectionObserver
      expect(mockObserve).not.toHaveBeenCalled();
    });

    it('should create IntersectionObserver with default options and observe element', () => {
      renderWithElement({});

      expect(MockIntersectionObserver).toHaveBeenCalledWith(
        expect.any(Function),
        { threshold: 0.2, rootMargin: '0px' }
      );
      expect(mockObserve).toHaveBeenCalled();
    });

    it('should pass custom threshold and rootMargin to IntersectionObserver', () => {
      renderWithElement({ threshold: 0.8, rootMargin: '50px' });

      expect(MockIntersectionObserver).toHaveBeenCalledWith(
        expect.any(Function),
        { threshold: 0.8, rootMargin: '50px' }
      );
    });

    it('should set isVisible and hasAnimated when entry is intersecting (no delay)', () => {
      const { getResult } = renderWithElement({});

      act(() => {
        intersectionCallback([
          { isIntersecting: true, target: document.createElement('div') },
        ]);
      });

      expect(getResult().isVisible).toBe(true);
      expect(getResult().hasAnimated).toBe(true);
    });

    it('should delay setting isVisible when delay option is provided', () => {
      const { getResult } = renderWithElement({ delay: 500 });

      act(() => {
        intersectionCallback([
          { isIntersecting: true, target: document.createElement('div') },
        ]);
      });

      // Before timeout fires, still not visible
      expect(getResult().isVisible).toBe(false);
      expect(getResult().hasAnimated).toBe(false);

      // Advance timers past the delay
      act(() => {
        jest.advanceTimersByTime(500);
      });

      expect(getResult().isVisible).toBe(true);
      expect(getResult().hasAnimated).toBe(true);
    });

    it('should unobserve element after first intersection when once is true (default)', () => {
      renderWithElement({});

      act(() => {
        intersectionCallback([
          { isIntersecting: true, target: document.createElement('div') },
        ]);
      });

      expect(mockUnobserve).toHaveBeenCalled();
    });

    it('should NOT unobserve element when once is false', () => {
      renderWithElement({ once: false });

      act(() => {
        intersectionCallback([
          { isIntersecting: true, target: document.createElement('div') },
        ]);
      });

      expect(mockUnobserve).not.toHaveBeenCalled();
    });

    it('should set isVisible to false when element leaves viewport and once is false', () => {
      const { getResult } = renderWithElement({ once: false });

      // First, trigger intersection to set hasAnimated = true
      act(() => {
        intersectionCallback([
          { isIntersecting: true, target: document.createElement('div') },
        ]);
      });

      expect(getResult().isVisible).toBe(true);
      expect(getResult().hasAnimated).toBe(true);

      // hasAnimated changed -> useEffect re-runs -> new observer created
      // intersectionCallback is now the new observer's callback
      // Trigger leaving viewport
      act(() => {
        intersectionCallback([
          { isIntersecting: false, target: document.createElement('div') },
        ]);
      });

      expect(getResult().isVisible).toBe(false);
    });

    it('should NOT set isVisible to false when leaving viewport if once is true', () => {
      const { getResult } = renderWithElement({});

      act(() => {
        intersectionCallback([
          { isIntersecting: true, target: document.createElement('div') },
        ]);
      });

      expect(getResult().isVisible).toBe(true);

      // Send not-intersecting entry; with once=true, the else-if branch is skipped
      act(() => {
        intersectionCallback([
          { isIntersecting: false, target: document.createElement('div') },
        ]);
      });

      // Should remain visible
      expect(getResult().isVisible).toBe(true);
    });

    it('should disconnect observer on unmount', () => {
      const { unmount } = renderWithElement({});

      unmount();

      expect(mockDisconnect).toHaveBeenCalled();
    });

    it('should handle multiple entries in a single callback', () => {
      const { getResult } = renderWithElement({});

      act(() => {
        intersectionCallback([
          { isIntersecting: false, target: document.createElement('div') },
          { isIntersecting: true, target: document.createElement('div') },
        ]);
      });

      expect(getResult().isVisible).toBe(true);
      expect(getResult().hasAnimated).toBe(true);
    });

    it('should not set visible when entry is not intersecting and hasAnimated is false', () => {
      const { getResult } = renderWithElement({ once: false });

      act(() => {
        intersectionCallback([
          { isIntersecting: false, target: document.createElement('div') },
        ]);
      });

      expect(getResult().isVisible).toBe(false);
      expect(getResult().hasAnimated).toBe(false);
    });
  });
});
