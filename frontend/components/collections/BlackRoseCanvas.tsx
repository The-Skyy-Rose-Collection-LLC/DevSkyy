/**
 * BLACK ROSE Collection - React Canvas Component
 *
 * Lazy-loads and manages the Three.js BlackRoseExperience.
 * Includes fullscreen toggle, product click handling, and responsive resizing.
 *
 * @component
 */

import React, { useEffect, useRef, useState } from 'react';
import type { BlackRoseExperience, BlackRoseProduct } from '../../collections/BlackRoseExperience';

export interface BlackRoseCanvasProps {
  /** Products to display (3-4 recommended for hotspots) */
  products: BlackRoseProduct[];

  /** Callback when product is clicked */
  onProductClick?: (product: BlackRoseProduct) => void;

  /** Callback when easter egg is clicked */
  onEasterEgg?: (url: string) => void;

  /** Enable bloom post-processing (default: true) */
  enableBloom?: boolean;

  /** Show performance overlay (default: false) */
  showPerformance?: boolean;
}

export const BlackRoseCanvas: React.FC<BlackRoseCanvasProps> = ({
  products,
  onProductClick,
  onEasterEgg,
  enableBloom = true,
  showPerformance = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const experienceRef = useRef<BlackRoseExperience | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let experience: BlackRoseExperience | null = null;
    let isMounted = true;

    const initExperience = async () => {
      if (!containerRef.current) return;

      try {
        // Lazy-load BlackRoseExperience (code-splitting)
        const { BlackRoseExperience } = await import('../../collections/BlackRoseExperience');

        if (!isMounted) return;

        // Initialize experience
        experience = new BlackRoseExperience(containerRef.current, {
          enableBloom,
          backgroundColor: 0x0a0a0a,
          fogColor: 0x0a0a0a,
          fogDensity: 0.03,
          moonlightColor: 0xc0c0c0,
          moonlightIntensity: 0.8,
          petalCount: 50,
        });

        experienceRef.current = experience;

        // Set callbacks
        if (onProductClick) {
          experience.setOnProductClick(onProductClick);
        }

        if (onEasterEgg) {
          experience.setOnEasterEgg(onEasterEgg);
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
  }, [products, enableBloom, showPerformance, onProductClick, onEasterEgg]);

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
      backgroundColor: '#0a0a0a',
    },
    canvas: {
      width: '100%',
      height: '100%',
      display: 'block',
    },
    loading: {
      position: 'absolute' as const,
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      color: '#c0c0c0',
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
      color: '#ff4444',
      fontFamily: "'Inter', sans-serif",
      fontSize: '1rem',
      textAlign: 'center' as const,
      padding: '2rem',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderRadius: '8px',
      maxWidth: '400px',
    },
    fullscreenButton: {
      position: 'absolute' as const,
      bottom: '2rem',
      right: '2rem',
      background: 'rgba(26, 26, 26, 0.9)',
      border: '1px solid rgba(192, 192, 192, 0.3)',
      borderRadius: '8px',
      color: '#c0c0c0',
      padding: '0.75rem 1.5rem',
      fontSize: '0.9rem',
      fontFamily: "'Inter', sans-serif",
      letterSpacing: '0.05em',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      backdropFilter: 'blur(10px)',
      zIndex: 10,
    } as React.CSSProperties,
    fullscreenButtonHover: {
      background: 'rgba(192, 192, 192, 0.2)',
      borderColor: '#c0c0c0',
    },
  };

  return (
    <div
      style={styles.container}
      ref={containerRef}
      role="application"
      tabIndex={0}
      aria-label="BLACK ROSE Collection 3D Experience - Use Tab to navigate products, Enter to select"
    >
      {isLoading && (
        <div style={styles.loading}>
          <div>Loading BLACK ROSE Garden...</div>
          <div style={{ fontSize: '0.8rem', marginTop: '1rem', opacity: 0.6 }}>
            Preparing 3D scene
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
              background: 'rgba(26, 26, 26, 0.9)',
              borderColor: 'rgba(192, 192, 192, 0.3)',
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

export default BlackRoseCanvas;
