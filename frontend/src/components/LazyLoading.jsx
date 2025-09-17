import React, { Suspense, lazy } from 'react';
import { motion } from 'framer-motion';

// Lazy load components for better performance
export const LazyDashboard = lazy(() =>
  import('./Dashboard').then(module => ({ default: module.default }))
);

export const LazyAgentManager = lazy(() =>
  import('./AgentManager').then(module => ({ default: module.default }))
);

export const LazyWordPressConnection = lazy(() =>
  import('./WordPressConnection').then(module => ({ default: module.default }))
);

export const LazyPerformanceMonitor = lazy(() =>
  import('./PerformanceMonitor').then(module => ({ default: module.default }))
);

export const LazyBrandIntelligence = lazy(() =>
  import('./BrandIntelligence').then(module => ({ default: module.default }))
);

export const LazySecurityMonitor = lazy(() =>
  import('./SecurityMonitor').then(module => ({ default: module.default }))
);

// Enhanced loading component with luxury styling
const LuxuryLoadingSpinner = ({ text = 'Loading...' }) => (
  <motion.div
    className="flex flex-col items-center justify-center min-h-[400px] bg-gradient-to-br from-rose-50 to-gold-50"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
  >
    <div className="relative">
      {/* Outer ring */}
      <motion.div
        className="w-16 h-16 border-4 border-rose-gold/20 rounded-full"
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
      />

      {/* Inner ring */}
      <motion.div
        className="absolute top-2 left-2 w-12 h-12 border-4 border-luxury-gold rounded-full border-t-transparent"
        animate={{ rotate: -360 }}
        transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
      />

      {/* Center dot */}
      <motion.div
        className="absolute top-1/2 left-1/2 w-4 h-4 bg-gradient-to-r from-rose-gold to-luxury-gold rounded-full transform -translate-x-1/2 -translate-y-1/2"
        animate={{ scale: [1, 1.2, 1] }}
        transition={{ duration: 1, repeat: Infinity }}
      />
    </div>

    <motion.p
      className="mt-6 text-lg font-elegant text-gray-600"
      animate={{ opacity: [0.5, 1, 0.5] }}
      transition={{ duration: 2, repeat: Infinity }}
    >
      {text}
    </motion.p>

    {/* Luxury brand indicator */}
    <motion.div
      className="mt-2 text-xs text-rose-gold font-medium uppercase tracking-wider"
      initial={{ y: 10, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.5 }}
    >
      Skyy Rose AI
    </motion.div>
  </motion.div>
);

// Error boundary for lazy loaded components
class LazyLoadErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Lazy load error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <motion.div
          className="flex flex-col items-center justify-center min-h-[400px] bg-red-50 border border-red-200 rounded-lg p-8"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <div className="text-red-500 text-xl mb-4">⚠️</div>
          <h3 className="text-lg font-semibold text-red-800 mb-2">
            Failed to load component
          </h3>
          <p className="text-red-600 text-center mb-4">
            There was an error loading this section. Please try refreshing the
            page.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Refresh Page
          </button>
        </motion.div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for lazy loading with luxury styling
export const withLazyLoading = (Component, loadingText = 'Loading...') => {
  return React.forwardRef((props, ref) => (
    <LazyLoadErrorBoundary>
      <Suspense fallback={<LuxuryLoadingSpinner text={loadingText} />}>
        <Component {...props} ref={ref} />
      </Suspense>
    </LazyLoadErrorBoundary>
  ));
};

// Optimized image component with lazy loading
export const OptimizedImage = React.memo(
  ({
    src,
    alt,
    className = '',
    loading = 'lazy',
    onLoad,
    onError,
    ...props
  }) => {
    const [isLoaded, setIsLoaded] = React.useState(false);
    const [hasError, setHasError] = React.useState(false);

    const handleLoad = e => {
      setIsLoaded(true);
      onLoad?.(e);
    };

    const handleError = e => {
      setHasError(true);
      onError?.(e);
    };

    if (hasError) {
      return (
        <div
          className={`bg-gray-200 flex items-center justify-center ${className}`}
        >
          <span className="text-gray-400 text-sm">Image failed to load</span>
        </div>
      );
    }

    return (
      <div className={`relative overflow-hidden ${className}`}>
        {!isLoaded && (
          <div className="absolute inset-0 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 animate-pulse" />
        )}
        <img
          src={src}
          alt={alt}
          loading={loading}
          onLoad={handleLoad}
          onError={handleError}
          className={`transition-opacity duration-300 ${isLoaded ? 'opacity-100' : 'opacity-0'} ${className}`}
          {...props}
        />
      </div>
    );
  }
);

OptimizedImage.displayName = 'OptimizedImage';

// Intersection Observer hook for lazy loading
export const useIntersectionObserver = (options = {}) => {
  const [isIntersecting, setIsIntersecting] = React.useState(false);
  const [hasIntersected, setHasIntersected] = React.useState(false);
  const ref = React.useRef();

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
        if (entry.isIntersecting && !hasIntersected) {
          setHasIntersected(true);
        }
      },
      {
        threshold: 0.1,
        rootMargin: '100px',
        ...options,
      }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, [hasIntersected, options]);

  return [ref, isIntersecting, hasIntersected];
};

// Lazy loading container component
export const LazyContainer = ({ children, className = '', fallback }) => {
  const [ref, isIntersecting, hasIntersected] = useIntersectionObserver();

  return (
    <div ref={ref} className={className}>
      {hasIntersected ? children : fallback || <LuxuryLoadingSpinner />}
    </div>
  );
};

// Performance monitoring for lazy loaded components
export const useLazyLoadPerformance = componentName => {
  React.useEffect(() => {
    const startTime = performance.now();

    return () => {
      const endTime = performance.now();
      const loadTime = endTime - startTime;

      // Report performance metrics
      if (window.gtag) {
        window.gtag('event', 'lazy_load_time', {
          component_name: componentName,
          load_time: Math.round(loadTime),
          event_category: 'Performance',
        });
      }

      // Log for debugging in development
      if (process.env.NODE_ENV === 'development') {
        console.log(
          `[Performance] ${componentName} loaded in ${loadTime.toFixed(2)}ms`
        );
      }
    };
  }, [componentName]);
};

export default {
  LazyDashboard,
  LazyAgentManager,
  LazyWordPressConnection,
  LazyPerformanceMonitor,
  LazyBrandIntelligence,
  LazySecurityMonitor,
  withLazyLoading,
  OptimizedImage,
  LazyContainer,
  useIntersectionObserver,
  useLazyLoadPerformance,
};
