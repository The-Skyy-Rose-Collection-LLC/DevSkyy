/**
 * SHOWROOM Collection - React Canvas Component
 *
 * Lazy-loads and manages the Three.js ShowroomExperience.
 * Includes fullscreen toggle, product click handling, and responsive resizing.
 *
 * @component
 */

import React, { useEffect, useRef, useState } from 'react';
import type { ShowroomExperience, ShowroomConfig } from '../../collections/ShowroomExperience';
import type { ShowroomProduct } from '../../types/product';

export interface ShowroomCanvasProps {
  /** Products to display in gallery */
  products: ShowroomProduct[];

  /** Callback when product is clicked */
  onProductClick?: (product: ShowroomProduct) => void;

  /** Showroom configuration */
  config?: ShowroomConfig;

  /** Show performance overlay (default: false) */
  showPerformance?: boolean;
}

export const ShowroomCanvas: React.FC<ShowroomCanvasProps> = ({
  products,
  onProductClick,
  config = {},
  showPerformance = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const experienceRef = useRef<ShowroomExperience | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let experience: ShowroomExperience | null = null;
    let isMounted = true;

    const initExperience = async () => {
      if (!containerRef.current) return;

      try {
        // Lazy-load ShowroomExperience (code-splitting)
        const { ShowroomExperience } = await import('../../collections/ShowroomExperience');

        if (!isMounted) return;

        // Initialize experience
        experience = new ShowroomExperience(containerRef.current, {
          backgroundColor: 0x0d0d0d,
          ambientLightIntensity: 0.3,
          floorColor: 0x1a1a1a,
          wallColor: 0x0d0d0d,
          roomWidth: 20,
          roomDepth: 30,
          roomHeight: 8,
          ...config,
        });

        experienceRef.current = experience;

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
  }, [products, config, showPerformance, onProductClick]);

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
      backgroundColor: '#0d0d0d',
    },
    loading: {
      position: 'absolute' as const,
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      color: '#d4af37',
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
      backgroundColor: 'rgba(13, 13, 13, 0.95)',
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
      color: '#0d0d0d',
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
    <div
      style={styles.container}
      ref={containerRef}
      role="application"
      tabIndex={0}
      aria-label="SHOWROOM Collection 3D Experience - Use Tab to navigate products, Enter to select"
    >
      {isLoading && (
        <div style={styles.loading}>
          <div>Loading SHOWROOM Gallery...</div>
          <div style={{ fontSize: '0.8rem', marginTop: '1rem', opacity: 0.6 }}>
            Preparing luxury exhibition
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

export default ShowroomCanvas;
