'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

// =============================================================================
// TYPES
// =============================================================================

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
}

// =============================================================================
// ERROR REPORTING
// =============================================================================

function generateErrorId(): string {
  return `err_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

function sanitizeErrorMessage(message: string): string {
  // Remove potentially sensitive information from error messages
  return message
    .replace(/\/Users\/[^/]+/g, '/Users/***')
    .replace(/Bearer [A-Za-z0-9._-]+/gi, 'Bearer [REDACTED]')
    .replace(/token=[A-Za-z0-9._-]+/gi, 'token=[REDACTED]')
    .replace(/api[_-]?key[=:][A-Za-z0-9._-]+/gi, 'api_key=[REDACTED]')
    .replace(/password[=:][^\s&]+/gi, 'password=[REDACTED]');
}

function sanitizeStackTrace(stack: string | undefined): string {
  if (!stack) return '';
  return sanitizeErrorMessage(stack)
    .split('\n')
    .slice(0, 10) // Limit stack trace depth
    .join('\n');
}

// =============================================================================
// ERROR BOUNDARY CLASS
// =============================================================================

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: generateErrorId(),
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught error:', error);
      console.error('Component stack:', errorInfo.componentStack);
    }

    // In production, you would send this to an error tracking service
    // e.g., Sentry, LogRocket, etc.
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    });
  };

  handleReload = (): void => {
    window.location.reload();
  };

  handleGoHome = (): void => {
    window.location.href = '/admin';
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { error, errorInfo, errorId } = this.state;
      const { showDetails = process.env.NODE_ENV === 'development' } = this.props;

      return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
          <Card className="max-w-lg w-full bg-gray-900 border-gray-800">
            <CardHeader className="text-center">
              <div className="mx-auto w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center mb-4">
                <AlertTriangle className="h-6 w-6 text-red-500" />
              </div>
              <CardTitle className="text-white text-xl">Something went wrong</CardTitle>
              <CardDescription className="text-gray-400">
                An unexpected error occurred. Our team has been notified.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {errorId && (
                <div className="text-center">
                  <span className="text-xs text-gray-500">Error ID: </span>
                  <code className="text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded">
                    {errorId}
                  </code>
                </div>
              )}

              {showDetails && error && (
                <div className="rounded-lg bg-gray-800 p-4 space-y-2">
                  <div className="flex items-center gap-2 text-red-400 text-sm font-medium">
                    <Bug className="h-4 w-4" />
                    Error Details
                  </div>
                  <p className="text-sm text-gray-300 font-mono break-all">
                    {sanitizeErrorMessage(error.message)}
                  </p>
                  {error.stack && (
                    <details className="text-xs text-gray-500">
                      <summary className="cursor-pointer hover:text-gray-400">
                        Stack trace
                      </summary>
                      <pre className="mt-2 overflow-x-auto whitespace-pre-wrap">
                        {sanitizeStackTrace(error.stack)}
                      </pre>
                    </details>
                  )}
                  {errorInfo?.componentStack && (
                    <details className="text-xs text-gray-500">
                      <summary className="cursor-pointer hover:text-gray-400">
                        Component stack
                      </summary>
                      <pre className="mt-2 overflow-x-auto whitespace-pre-wrap">
                        {sanitizeStackTrace(errorInfo.componentStack)}
                      </pre>
                    </details>
                  )}
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-3">
                <Button
                  onClick={this.handleReset}
                  className="flex-1 bg-rose-600 hover:bg-rose-700"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try Again
                </Button>
                <Button
                  onClick={this.handleGoHome}
                  variant="outline"
                  className="flex-1 border-gray-700 text-gray-300 hover:bg-gray-800"
                >
                  <Home className="h-4 w-4 mr-2" />
                  Go to Dashboard
                </Button>
              </div>

              <p className="text-xs text-center text-gray-500">
                If this problem persists, please contact support with the error ID above.
              </p>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// =============================================================================
// HOOK FOR FUNCTIONAL COMPONENTS
// =============================================================================

interface UseErrorHandlerOptions {
  onError?: (error: Error) => void;
  fallbackMessage?: string;
}

export function useErrorHandler(options: UseErrorHandlerOptions = {}) {
  const { onError, fallbackMessage = 'An error occurred' } = options;

  const handleError = React.useCallback(
    (error: unknown) => {
      const normalizedError = error instanceof Error
        ? error
        : new Error(typeof error === 'string' ? error : fallbackMessage);

      if (onError) {
        onError(normalizedError);
      }

      // Re-throw to be caught by ErrorBoundary
      throw normalizedError;
    },
    [onError, fallbackMessage]
  );

  return { handleError };
}

// =============================================================================
// ASYNC ERROR BOUNDARY WRAPPER
// =============================================================================

interface AsyncBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error) => void;
}

export function AsyncBoundary({ children, fallback, onError }: AsyncBoundaryProps) {
  return (
    <ErrorBoundary
      fallback={fallback}
      onError={(error, errorInfo) => {
        onError?.(error);
        // Log component stack for debugging
        if (process.env.NODE_ENV === 'development') {
          console.error('AsyncBoundary caught:', error, errorInfo);
        }
      }}
    >
      {children}
    </ErrorBoundary>
  );
}

// =============================================================================
// ROUTE ERROR BOUNDARY
// =============================================================================

export function RouteErrorBoundary({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary
      onError={(error) => {
        // Track navigation errors
        if (process.env.NODE_ENV === 'production') {
          // Send to error tracking service
          console.error('[Route Error]', sanitizeErrorMessage(error.message));
        }
      }}
    >
      {children}
    </ErrorBoundary>
  );
}
