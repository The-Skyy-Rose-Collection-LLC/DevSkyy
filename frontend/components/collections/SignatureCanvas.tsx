/**
 * SIGNATURE Collection - React Canvas Component
 *
 * Lazy-loads and manages the Three.js SignatureExperience.
 * Includes fullscreen toggle, product click handling, and responsive resizing.
 *
 * @component
 */

import React, { useEffect, useRef, useState } from 'react';
import type { SignatureExperience, SignatureProduct } from '../../collections/SignatureExperience';

export interface SignatureCanvasProps {
  /** Products to display on pedestals */
  products: SignatureProduct[];

  /** Callback when product is clicked */
  onProductClick?: (product: SignatureProduct) => void;

  /** Callback when category pathway is clicked */
  onCategorySelect?: (category: string) => void;

  /** Enable depth of field post-processing (default: true) */
  enableDepthOfField?: boolean;

  /** Show performance overlay (default: false) */
  showPerformance?: boolean;
}

export const SignatureCanvas: React.FC<SignatureCanvasProps> = ({
  products,
  onProductClick,
  onCategorySelect,
  enableDepthOfField = true,
  showPerformance = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const experienceRef = useRef<SignatureExperience | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let experience: SignatureExperience | null = null;
    let isMounted = true;

    const initExperience = async () => {
      if (!containerRef.current) return;

      try {
        // Lazy-load SignatureExperience (code-splitting)
        const { SignatureExperience } = await import('../../collections/SignatureExperience');

        if (!isMounted) return;

        // Initialize experience
        experience = new SignatureExperience(containerRef.current, {
          enableDepthOfField,
          backgroundColor: 0xfff8e7, // Warm white
          sunlightColor: 0xffd700, // Gold
          sunlightIntensity: 1.2,
          ambientColor: 0xffe4c4, // Bisque
          focusDistance: 10,
        });

        experienceRef.current = experience;

        // Set callbacks
        if (onProductClick) {
          experience.setOnProductSelect(onProductClick);
        }

        if (onCategorySelect) {
          experience.setOnCategorySelect(onCategorySelect);
        }

        // Load products
        await experience.loadProducts(products);

        // Start animation
        experience.start();

        if (showPerformance) {
          experience.showPerformanceOverlay(true);
        }

        setIsLoading(false);
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load 3D experience');
          setIsLoading(false);
        }
      }
    };

    initExperience();

    return () => {
      isMounted = false;
      if (experience) {
        experience.stop();
        experience.dispose();
      }
    };
  }, [products, enableDepthOfField, showPerformance, onProductClick, onCategorySelect]);

  const toggleFullscreen = async () => {
    if (!containerRef.current) return;

    try {
      if (!document.fullscreenElement) {
        await containerRef.current.requestFullscreen();
        setIsFullscreen(true);
      } else {
        await document.exitFullscreen();
        setIsFullscreen(false);
      }
    } catch (err) {
      console.error('Fullscreen error:', err);
    }
  };

  const styles = {
    container: {
      position: 'relative' as const,
      width: '100%',
      height: '100vh',
      overflow: 'hidden',
      backgroundColor: '#fff8e7',
    },
    loading: {
      position: 'absolute' as const,
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      color: '#2a2a2a',
      fontFamily: "'Inter', sans-serif",
      fontSize: '1.2rem',
      fontWeight: 300,
      letterSpacing: '0.1em',
      textAlign: 'center' as const,
    },
    error: {
      position: 'absolute' as const,
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      color: '#8b0000',
      fontFamily: "'Inter', sans-serif",
      fontSize: '1rem',
      textAlign: 'center' as const,
      padding: '2rem',
      backgroundColor: 'rgba(255, 248, 231, 0.95)',
      borderRadius: '8px',
      border: '1px solid rgba(212, 175, 55, 0.3)',
      maxWidth: '400px',
    },
    fullscreenButton: {
      position: 'absolute' as const,
      bottom: '2rem',
      right: '2rem',
      background: 'rgba(212, 175, 55, 0.9)',
      border: '1px solid rgba(212, 175, 55, 1)',
      borderRadius: '8px',
      color: '#2a2a2a',
      padding: '0.75rem 1.5rem',
      fontSize: '0.9rem',
      fontFamily: "'Inter', sans-serif",
      letterSpacing: '0.05em',
      fontWeight: 600,
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      backdropFilter: 'blur(10px)',
      zIndex: 10,
    } as React.CSSProperties,
    fullscreenButtonHover: {
      background: 'rgba(255, 215, 0, 1)',
      transform: 'scale(1.05)',
      boxShadow: '0 4px 12px rgba(212, 175, 55, 0.4)',
    },
  };

  return (
    <div style={styles.container} ref={containerRef}>
      {isLoading && (
        <div style={styles.loading}>
          <div>Loading SIGNATURE Garden...</div>
          <div style={{ fontSize: '0.8rem', marginTop: '1rem', opacity: 0.6 }}>
            Preparing luxury experience
          </div>
        </div>
      )}

      {error && (
        <div style={styles.error}>
          <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Failed to Load</div>
          <div>{error}</div>
          <div style={{ marginTop: '1rem', fontSize: '0.85rem', opacity: 0.7 }}>
            Try refreshing the page
          </div>
        </div>
      )}

      {!isLoading && !error && (
        <button
          style={styles.fullscreenButton}
          onClick={toggleFullscreen}
          onMouseEnter={(e) => {
            Object.assign(e.currentTarget.style, styles.fullscreenButtonHover);
          }}
          onMouseLeave={(e) => {
            Object.assign(e.currentTarget.style, {
              background: 'rgba(212, 175, 55, 0.9)',
              transform: 'scale(1)',
              boxShadow: 'none',
            });
          }}
          aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
        >
          {isFullscreen ? '✕ Exit Fullscreen' : '⛶ Fullscreen'}
        </button>
      )}
    </div>
  );
};

export default SignatureCanvas;
