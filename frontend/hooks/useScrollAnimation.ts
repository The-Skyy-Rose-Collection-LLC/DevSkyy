/**
 * useScrollAnimation Hook
 *
 * Triggers animations when elements enter viewport using IntersectionObserver.
 * Respects user's prefers-reduced-motion setting for accessibility.
 *
 * @hook
 */

import { useEffect, useRef, useState } from 'react';

export interface UseScrollAnimationOptions {
  /** Trigger animation when element is X% visible (default: 0.2 = 20%) */
  threshold?: number;

  /** Root margin for early/late triggering (default: '0px') */
  rootMargin?: string;

  /** Only animate once (default: true) */
  once?: boolean;

  /** Delay before animation starts in ms (default: 0) */
  delay?: number;
}

export interface UseScrollAnimationResult {
  /** Ref to attach to the element */
  ref: React.RefObject<HTMLElement | null>;

  /** Whether element is visible and should animate */
  isVisible: boolean;

  /** Whether animation has been triggered (for once mode) */
  hasAnimated: boolean;
}

/**
 * Hook to animate elements when they scroll into view
 */
export function useScrollAnimation(
  options: UseScrollAnimationOptions = {}
): UseScrollAnimationResult {
  const {
    threshold = 0.2,
    rootMargin = '0px',
    once = true,
    delay = 0,
  } = options;

  const ref = useRef<HTMLElement>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [hasAnimated, setHasAnimated] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    // Check for prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      // Skip animations if user prefers reduced motion
      setIsVisible(true);
      setHasAnimated(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            if (delay > 0) {
              setTimeout(() => {
                setIsVisible(true);
                setHasAnimated(true);
              }, delay);
            } else {
              setIsVisible(true);
              setHasAnimated(true);
            }

            // Unobserve after first trigger if once=true
            if (once) {
              observer.unobserve(element);
            }
          } else if (!once && hasAnimated) {
            // Allow re-triggering if once=false
            setIsVisible(false);
          }
        });
      },
      {
        threshold,
        rootMargin,
      }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [threshold, rootMargin, once, delay, hasAnimated]);

  return {
    ref,
    isVisible,
    hasAnimated,
  };
}

export default useScrollAnimation;
