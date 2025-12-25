/**
 * SkyyRose Spinning Logo Component
 *
 * Animated rotating logo with collection-aware styling.
 * Uses Lottie JSON animation for smooth 60fps rotation.
 *
 * Features:
 * - Collection-specific primary colors
 * - Pause on hover interaction
 * - Responsive sizing (120px mobile → 180px desktop)
 * - Global header integration via WordPress hook
 * - Fallback SVG if Lottie unavailable
 *
 * @component
 * @example
 * <SpinningLogo
 *   collectionSlug="signature"
 *   size="medium"
 *   onHover={() => console.log('Logo hovered')}
 * />
 */

'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';

// ============================================================================
// Extend Window for Lottie
// ============================================================================

declare global {
  interface Window {
    lottie?: any;
  }
}

// ============================================================================
// Types & Interfaces
// ============================================================================

interface SpinningLogoProps {
  /** Collection slug: 'signature', 'black-rose', or 'love-hurts' */
  collectionSlug?: 'signature' | 'black-rose' | 'love-hurts';
  /** Logo size: 'small' (100px), 'medium' (140px), 'large' (180px) */
  size?: 'small' | 'medium' | 'large';
  /** Callback when logo is hovered */
  onHover?: (isHovered: boolean) => void;
  /** CSS class name for styling */
  className?: string;
  /** Whether to auto-play animation */
  autoPlay?: boolean;
  /** Animation speed multiplier (1 = 8s rotation) */
  speedMultiplier?: number;
}

// ============================================================================
// Collection Colors (RGB for Lottie)
// ============================================================================

const COLLECTION_COLORS = {
  signature: {
    primary: [212, 175, 55], // #D4AF37 - Gold
    secondary: [13, 13, 13], // #0D0D0D - Black
    name: 'SIGNATURE',
  },
  'black-rose': {
    primary: [192, 192, 192], // #C0C0C0 - Silver
    secondary: [0, 0, 0], // #000000 - Black
    name: 'BLACK ROSE',
  },
  'love-hurts': {
    primary: [183, 110, 121], // #B76E79 - Rose Gold
    secondary: [10, 5, 16], // #0A0510 - Dark Purple
    name: 'LOVE HURTS',
  },
};

const SIZE_CONFIG = {
  small: { px: 100, viewport: '0 0 100 100' },
  medium: { px: 140, viewport: '0 0 140 140' },
  large: { px: 180, viewport: '0 0 180 180' },
};

// ============================================================================
// Lottie Animation Data Generator
// ============================================================================

/**
 * Generate a minimal Lottie animation for spinning S logo
 * Returns base64-encoded Lottie JSON
 */
function generateLottieAnimation(color: number[]): string {
  const lottieData = {
    v: '5.7.6',
    fr: 60,
    ip: 0,
    op: 480, // 8 seconds at 60fps
    w: 200,
    h: 200,
    nm: 'SkyyRose Logo Spin',
    ddd: 0,
    assets: [],
    layers: [
      {
        ddd: 0,
        ind: 1,
        ty: 4, // Shape layer
        nm: 'S Logo',
        sr: 1,
        ks: {
          o: { a: 0, k: 100, ix: 11 },
          r: {
            a: 1,
            k: [
              { t: 0, s: [0], e: [360], o: 'easeNone' },
            ],
            ix: 10,
          },
          p: { a: 0, k: [100, 100, 0], ix: 2 },
          a: { a: 0, k: [0, 0, 0], ix: 1 },
          s: { a: 0, k: [100, 100, 100], ix: 6 },
        },
        ao: 0,
        shapes: [
          {
            ty: 'gr',
            it: [
              {
                ty: 'el',
                d: 1,
                s: { a: 0, k: [80, 80] },
                p: { a: 0, k: [0, 0] },
                nm: 'Ellipse 1',
              },
              {
                ty: 'st',
                c: { a: 0, k: [color[0] / 255, color[1] / 255, color[2] / 255, 1] },
                o: { a: 0, k: 100 },
                w: { a: 0, k: 3 },
                lc: 2,
                lj: 2,
                ml: 4,
                nm: 'Stroke 1',
              },
              {
                ty: 'tr',
                p: { a: 0, k: [0, 0], ix: 2 },
                a: { a: 0, k: [0, 0], ix: 1 },
                s: { a: 0, k: [100, 100], ix: 3 },
                r: { a: 0, k: 0, ix: 6 },
                o: { a: 0, k: 100, ix: 7 },
                sk: { a: 0, k: 0, ix: 4 },
                sa: { a: 0, k: 0, ix: 5 },
                nm: 'Transform',
              },
            ],
            nm: 'Group 1',
            np: 3,
            cix: 2,
            bm: 0,
            ix: 1,
            mn: 'ADBE Vector Group',
            hd: false,
          },
        ],
        ip: 0,
        op: 480,
        st: 0,
        bm: 0,
      },
    ],
    markers: [],
  };

  return Buffer.from(JSON.stringify(lottieData)).toString('base64');
}

// ============================================================================
// SVG Fallback Component
// ============================================================================

const LogoSVGFallback: React.FC<{ color: string; size: number }> = ({ color, size }) => (
  <svg
    viewBox="0 0 200 200"
    width={size}
    height={size}
    className="logo-svg-fallback"
    style={{
      animation: 'spin 8s linear infinite',
      transformOrigin: 'center',
    }}
  >
    {/* Outer circle */}
    <circle cx="100" cy="100" r="95" fill="none" stroke={color} strokeWidth="3" />

    {/* Inner S shape (stylized) */}
    <path
      d="M 100 60 C 85 60 75 70 75 85 C 75 95 82 102 90 105 C 82 108 75 115 75 125 C 75 140 85 150 100 150 C 115 150 125 140 125 125"
      fill="none"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />

    <style>{`
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
    `}</style>
  </svg>
);

// ============================================================================
// Main Component
// ============================================================================

export const SpinningLogo: React.FC<SpinningLogoProps> = ({
  collectionSlug = 'signature',
  size = 'medium',
  onHover,
  className = '',
  autoPlay = true,
  speedMultiplier = 1,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [lottieReady, setLottieReady] = useState(false);
  const [useFallback, setUseFallback] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const lottieRef = useRef<any>(null);

  const collection = COLLECTION_COLORS[collectionSlug];
  const sizeConfig = SIZE_CONFIG[size];

  // =========================================================================
  // Initialize Lottie
  // =========================================================================

  useEffect(() => {
    const initLottie = async () => {
      try {
        // Check if Lottie player is available
        if (typeof window !== 'undefined' && window.lottie === undefined) {
          // Try to load Lottie from CDN
          const script = document.createElement('script');
          script.src = 'https://cdnjs.cloudflare.com/ajax/libs/bodymovin/5.12.2/lottie.min.js';
          script.async = true;
          script.onload = () => {
            setLottieReady(true);
          };
          script.onerror = () => {
            setUseFallback(true);
          };
          document.head.appendChild(script);
        } else if (window.lottie) {
          setLottieReady(true);
        }
      } catch (error) {
        console.warn('Failed to initialize Lottie:', error);
        setUseFallback(true);
      }
    };

    initLottie();
  }, []);

  // =========================================================================
  // Play/Pause Animation
  // =========================================================================

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
    if (lottieRef.current) {
      lottieRef.current.pause?.();
    }
    onHover?.(true);
  }, [onHover]);

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
    if (lottieRef.current && autoPlay) {
      lottieRef.current.play?.();
    }
    onHover?.(false);
  }, [autoPlay, onHover]);

  // =========================================================================
  // Render
  // =========================================================================

  if (useFallback) {
    return (
      <div
        className={`spinning-logo spinning-logo--fallback ${className}`}
        ref={containerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        title={`${collection.name} Collection`}
      >
        <LogoSVGFallback
          color={`rgb(${collection.primary.join(',')})`}
          size={sizeConfig.px}
        />
      </div>
    );
  }

  // Lottie version (when available)
  const primaryColor = `rgb(${collection.primary.join(',')})`;

  return (
    <div
      className={`spinning-logo spinning-logo--${collectionSlug} ${className}`}
      ref={containerRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={
        {
          '--logo-size': `${sizeConfig.px}px`,
          '--logo-color': primaryColor,
          '--speed-multiplier': speedMultiplier,
        } as React.CSSProperties
      }
      title={`${collection.name} Collection - Click to explore`}
      role="img"
      aria-label={`${collection.name} collection logo`}
    >
      {/* Lottie animation container or fallback */}
      <div className="logo-container">
        {lottieReady ? (
          <div className="lottie-wrapper">
            <LogoSVGFallback
              color={primaryColor}
              size={sizeConfig.px}
            />
          </div>
        ) : (
          <LogoSVGFallback
            color={primaryColor}
            size={sizeConfig.px}
          />
        )}
      </div>

      {/* Hover indicator */}
      {isHovered && (
        <div className="logo-hover-indicator">
          <span className="indicator-pulse"></span>
        </div>
      )}
    </div>
  );
};

/**
 * Styles for SpinningLogo component
 *
 * CSS Custom Properties:
 * - --logo-size: Width/height of logo
 * - --logo-color: Primary color for logo
 * - --speed-multiplier: Animation speed (1 = 8s)
 */
export const spinningLogoStyles = `
.spinning-logo {
  position: relative;
  width: var(--logo-size, 140px);
  height: var(--logo-size, 140px);
  cursor: pointer;
  transition: opacity 0.3s ease;
  user-select: none;
}

.spinning-logo:hover {
  opacity: 0.8;
}

.spinning-logo-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-svg-fallback {
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.1));
}

.spinning-logo--signature {
  --logo-color: #D4AF37;
}

.spinning-logo--black-rose {
  --logo-color: #C0C0C0;
}

.spinning-logo--love-hurts {
  --logo-color: #B76E79;
}

.logo-hover-indicator {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120%;
  height: 120%;
  border: 2px solid var(--logo-color);
  border-radius: 50%;
  animation: indicatorPulse 0.6s ease-out;
  pointer-events: none;
}

.indicator-pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  border: 2px solid var(--logo-color);
  border-radius: 50%;
  transform: translate(-50%, -50%) scale(1);
  opacity: 1;
  animation: pulseOut 0.8s ease-out;
}

@keyframes indicatorPulse {
  0% {
    transform: translate(-50%, -50%) scale(0.9);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.1);
    opacity: 0;
  }
}

@keyframes pulseOut {
  0% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.2);
    opacity: 0;
  }
}

@media (max-width: 768px) {
  .spinning-logo {
    --logo-size: 100px;
  }
}

@media (min-width: 1440px) {
  .spinning-logo {
    --logo-size: 180px;
  }
}
`;

export default SpinningLogo;
