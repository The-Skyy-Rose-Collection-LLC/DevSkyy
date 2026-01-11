/**
 * ScrollAnimatedSection Component
 *
 * Wrapper component that fades in content when scrolled into view.
 * Uses IntersectionObserver for performance (60fps).
 *
 * @component
 */

import React from 'react';
import { useScrollAnimation } from '../../hooks/useScrollAnimation';

export interface ScrollAnimatedSectionProps {
  /** Child elements to animate */
  children: React.ReactNode;

  /** Animation type (default: 'fade-up') */
  animation?: 'fade-up' | 'fade-down' | 'fade-left' | 'fade-right' | 'fade' | 'scale';

  /** Animation duration in ms (default: 600) */
  duration?: number;

  /** Delay before animation starts in ms (default: 0) */
  delay?: number;

  /** Threshold for triggering (0-1, default: 0.2) */
  threshold?: number;

  /** Custom className */
  className?: string;

  /** Custom styles */
  style?: React.CSSProperties;
}

const animationTransforms = {
  'fade-up': 'translateY(40px)',
  'fade-down': 'translateY(-40px)',
  'fade-left': 'translateX(40px)',
  'fade-right': 'translateX(-40px)',
  'fade': 'translateY(0)',
  'scale': 'scale(0.95)',
};

export const ScrollAnimatedSection: React.FC<ScrollAnimatedSectionProps> = ({
  children,
  animation = 'fade-up',
  duration = 600,
  delay = 0,
  threshold = 0.2,
  className,
  style,
}) => {
  const { ref, isVisible } = useScrollAnimation({
    threshold,
    delay,
    once: true,
  });

  const initialTransform = animationTransforms[animation];

  const styles: React.CSSProperties = {
    opacity: isVisible ? 1 : 0,
    transform: isVisible ? 'translateY(0) translateX(0) scale(1)' : initialTransform,
    transition: `opacity ${duration}ms ease-out, transform ${duration}ms ease-out`,
    willChange: 'opacity, transform',
    ...style,
  };

  return (
    <div ref={ref as React.RefObject<HTMLDivElement>} style={styles} className={className}>
      {children}
    </div>
  );
};

export default ScrollAnimatedSection;
