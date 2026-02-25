/**
 * Unit Tests for ErrorBoundary
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBoundary, ErrorFallback, withErrorBoundary } from '../ErrorBoundary';

// Suppress console.error from error boundaries
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});
afterAll(() => {
  console.error = originalConsoleError;
});

// Component that throws
function ThrowingComponent({ shouldThrow }) {
  if (shouldThrow) throw new Error('Test error');
  return <div>No error</div>;
}

describe('ErrorFallback', () => {
  const mockReset = jest.fn();
  const testError = new Error('Something went wrong');

  it('should render error message', () => {
    render(<ErrorFallback error={testError} resetErrorBoundary={mockReset} />);
    expect(screen.getAllByText(/something went wrong/i).length).toBeGreaterThan(0);
  });

  it('should render custom title', () => {
    render(
      <ErrorFallback error={testError} resetErrorBoundary={mockReset} title="Custom Error" />
    );
    expect(screen.getByText('Custom Error')).toBeTruthy();
  });

  it('should render custom message', () => {
    render(
      <ErrorFallback error={testError} resetErrorBoundary={mockReset} message="Custom msg" />
    );
    expect(screen.getByText('Custom msg')).toBeTruthy();
  });

  it('should call resetErrorBoundary on Try Again button click', () => {
    render(<ErrorFallback error={testError} resetErrorBoundary={mockReset} />);
    // Find the button specifically, not text in paragraphs
    const buttons = screen.getAllByRole('button');
    const tryAgainBtn = buttons.find(b => b.textContent?.includes('Try Again'));
    expect(tryAgainBtn).toBeDefined();
    fireEvent.click(tryAgainBtn);
    expect(mockReset).toHaveBeenCalled();
  });
});

describe('ErrorBoundary', () => {
  it('should render children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Hello</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('Hello')).toBeTruthy();
  });

  it('should render fallback when child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText(/something went wrong/i)).toBeTruthy();
  });

  it('should call onError callback', () => {
    const onError = jest.fn();
    render(
      <ErrorBoundary onError={onError}>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(onError).toHaveBeenCalledWith(expect.any(Error), expect.any(Object));
  });

  it('should render custom FallbackComponent', () => {
    function CustomFallback({ error }) {
      return <div>Custom: {error.message}</div>;
    }
    render(
      <ErrorBoundary FallbackComponent={CustomFallback}>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Custom: Test error')).toBeTruthy();
  });

  it('should render fallbackRender', () => {
    render(
      <ErrorBoundary
        fallbackRender={({ error }) => <div>Render: {error.message}</div>}
      >
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Render: Test error')).toBeTruthy();
  });
});

describe('withErrorBoundary', () => {
  it('should wrap component with error boundary', () => {
    function MyComponent() {
      return <div>Wrapped</div>;
    }
    const Wrapped = withErrorBoundary(MyComponent);
    render(<Wrapped />);
    expect(screen.getByText('Wrapped')).toBeTruthy();
  });
});
