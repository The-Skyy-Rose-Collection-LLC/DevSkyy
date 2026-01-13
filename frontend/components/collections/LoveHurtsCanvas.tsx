/**
 * LOVE HURTS Collection - React Canvas Component
 *
 * Lazy-loads and manages the Three.js LoveHurtsExperience.
 * Includes fullscreen toggle, product click handling, and responsive resizing.
 *
 * @component
 */

import React, { useEffect, useRef, useState } from 'react';
import type { LoveHurtsExperience, LoveHurtsProduct } from '../../collections/LoveHurtsExperience';

export interface LoveHurtsCanvasProps {
  /** Products to display (hero, mirrors, floor) */
  products: LoveHurtsProduct[];

  /** Callback when product is clicked */
  onProductClick?: (product: LoveHurtsProduct) => void;

  /** Enable bloom post-processing (default: true) */
  enableBloom?: boolean;

  /** Bloom strength (default: 1.5) */
  bloomStrength?: number;

  /** Show performance overlay (default: false) */
  showPerformance?: boolean;
}

export const LoveHurtsCanvas: React.FC<LoveHurtsCanvasProps> = ({
  products,
  onProductClick,
  enableBloom = true,
  bloomStrength = 1.5,
  showPerformance = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const experienceRef = useRef<LoveHurtsExperience | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let experience: LoveHurtsExperience | null = null;
    let isMounted = true;

    const initExperience = async () => {
      if (!containerRef.current) return;

      try {
        // Lazy-load LoveHurtsExperience (code-splitting)
        const { LoveHurtsExperience } = await import('../../collections/LoveHurtsExperience');

        if (!isMounted) return;

        // Initialize experience
        experience = new LoveHurtsExperience(containerRef.current, {
          enableBloom,
          bloomStrength,
          backgroundColor: 0x0a0505, // Dark burgundy
          candlelightColor: 0xff6347, // Warm red-orange
          candlelightIntensity: 1.8,
          particleCount: 100,
          stainedGlassColors: [0xdc143c, 0xb76e79, 0x8b0000], // Crimson, rose, dark red
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
  }, [products, enableBloom, bloomStrength, showPerformance, onProductClick]);

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
      backgroundColor: '#0a0505',
    },
    loading: {
      position: 'absolute' as const,
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      color: '#b76e79',
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
      backgroundColor: 'rgba(10, 5, 5, 0.95)',
      borderRadius: '8px',
      border: '1px solid rgba(220, 20, 60, 0.3)',
      maxWidth: '400px',
    },
    fullscreenButton: {
      position: 'absolute' as const,
      bottom: '2rem',
      right: '2rem',
      background: 'rgba(183, 110, 121, 0.9)',
      border: '1px solid rgba(220, 20, 60, 0.5)',
      borderRadius: '8px',
      color: '#ffffff',
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
      background: 'rgba(220, 20, 60, 1)',
      transform: 'scale(1.05)',
      boxShadow: '0 4px 12px rgba(220, 20, 60, 0.6)',
    },
  };

  return (
    <div
      style={styles.container}
      ref={containerRef}
      role="application"
      tabIndex={0}
      aria-label="LOVE HURTS Collection 3D Experience - Use Tab to navigate products, Enter to select"
    >
      {isLoading && (
        <div style={styles.loading}>
          <div>Loading LOVE HURTS Castle...</div>
          <div style={{ fontSize: '0.8rem', marginTop: '1rem', opacity: 0.6 }}>
            Preparing enchanted experience
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
              background: 'rgba(183, 110, 121, 0.9)',
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

export default LoveHurtsCanvas;
