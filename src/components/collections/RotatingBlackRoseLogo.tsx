/**
 * Rotating BLACK ROSE Logo - Header Component
 *
 * 3D rotating logo animation using CSS 3D transforms for performance.
 * Displayed persistently in the collection page header.
 *
 * @component
 */

import React from 'react';

export interface RotatingBlackRoseLogoProps {
  /** Logo size in pixels (default: 120) */
  size?: number;

  /** Rotation speed (default: 20s) */
  rotationSpeed?: string;

  /** Custom styles */
  style?: React.CSSProperties;
}

export const RotatingBlackRoseLogo: React.FC<RotatingBlackRoseLogoProps> = ({
  size = 120,
  rotationSpeed = '20s',
  style,
}) => {
  const keyframesId = `rotate-black-rose-${rotationSpeed.replace(/[^0-9]/g, '')}`;

  const styles = {
    container: {
      width: `${size}px`,
      height: `${size}px`,
      perspective: '1000px',
      display: 'inline-block',
      ...style,
    },
    logoWrapper: {
      width: '100%',
      height: '100%',
      position: 'relative' as const,
      transformStyle: 'preserve-3d' as const,
      animation: `${keyframesId} ${rotationSpeed} linear infinite`,
    },
    logo: {
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column' as const,
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 50%, #1a1a1a 100%)',
      border: '2px solid rgba(192, 192, 192, 0.3)',
      borderRadius: '50%',
      boxShadow: `
        0 0 20px rgba(192, 192, 192, 0.2),
        0 0 40px rgba(192, 192, 192, 0.1),
        inset 0 0 20px rgba(0, 0, 0, 0.5)
      `,
      position: 'relative' as const,
      overflow: 'hidden',
    },
    text: {
      fontFamily: "'Cinzel', 'Georgia', serif",
      fontSize: `${size * 0.15}px`,
      fontWeight: 700,
      letterSpacing: '0.1em',
      textTransform: 'uppercase' as const,
      color: '#c0c0c0',
      textShadow: `
        0 0 10px rgba(192, 192, 192, 0.5),
        0 0 20px rgba(192, 192, 192, 0.3)
      `,
      zIndex: 2,
    },
    rose: {
      position: 'absolute' as const,
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      fontSize: `${size * 0.4}px`,
      opacity: 0.15,
      zIndex: 1,
    },
    shine: {
      position: 'absolute' as const,
      top: '-50%',
      left: '-50%',
      width: '200%',
      height: '200%',
      background: 'linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%)',
      animation: `${keyframesId}-shine 3s ease-in-out infinite`,
      pointerEvents: 'none' as const,
    },
  };

  return (
    <>
      <style>
        {`
          @keyframes ${keyframesId} {
            from {
              transform: rotateY(0deg);
            }
            to {
              transform: rotateY(360deg);
            }
          }

          @keyframes ${keyframesId}-shine {
            0%, 100% {
              transform: translateX(-100%);
            }
            50% {
              transform: translateX(100%);
            }
          }
        `}
      </style>

      <div style={styles.container}>
        <div style={styles.logoWrapper}>
          <div style={styles.logo}>
            <div style={styles.rose}>🥀</div>
            <div style={styles.shine} />
            <div style={styles.text}>
              BLACK
              <br />
              ROSE
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default RotatingBlackRoseLogo;
