'use client';

import { motion, type Variants, type HTMLMotionProps } from 'framer-motion';
import { forwardRef } from 'react';

/**
 * Reusable Framer Motion variants for consistent animations across the app
 */

// Fade in from bottom (for cards, sections)
export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: 'easeOut' }
  },
};

// Fade in from left (for sidebars, panels)
export const fadeInLeft: Variants = {
  hidden: { opacity: 0, x: -20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.3, ease: 'easeOut' }
  },
};

// Fade in from right
export const fadeInRight: Variants = {
  hidden: { opacity: 0, x: 20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.3, ease: 'easeOut' }
  },
};

// Simple fade
export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.3 }
  },
};

// Scale up (for modals, tooltips)
export const scaleUp: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.2, ease: 'easeOut' }
  },
};

// Stagger children container
export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

// Stagger item (use with staggerContainer)
export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3 }
  },
};

// Pulse animation (for loading states)
export const pulse: Variants = {
  idle: { scale: 1 },
  pulse: {
    scale: [1, 1.05, 1],
    transition: { duration: 1.5, repeat: Infinity }
  },
};

// Slide in overlay (for drawers, modals)
export const slideInOverlay: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.2 } },
  exit: { opacity: 0, transition: { duration: 0.2 } },
};

// Slide in from bottom (for drawers)
export const slideInBottom: Variants = {
  hidden: { y: '100%' },
  visible: {
    y: 0,
    transition: { type: 'spring', damping: 25, stiffness: 300 }
  },
  exit: {
    y: '100%',
    transition: { duration: 0.2, ease: 'easeIn' }
  },
};

// Slide in from right (for sidebars)
export const slideInFromRight: Variants = {
  hidden: { x: '100%' },
  visible: {
    x: 0,
    transition: { type: 'spring', damping: 25, stiffness: 300 }
  },
  exit: {
    x: '100%',
    transition: { duration: 0.2, ease: 'easeIn' }
  },
};

/**
 * Pre-built animated components
 */

// Animated div with fade-in-up effect
export const MotionDiv = motion.div;

// Animated card container
interface MotionCardProps extends HTMLMotionProps<'div'> {
  delay?: number;
}

export const MotionCard = forwardRef<HTMLDivElement, MotionCardProps>(
  ({ delay = 0, ...props }, ref) => (
    <motion.div
      ref={ref}
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: {
          opacity: 1,
          y: 0,
          transition: { duration: 0.4, delay, ease: 'easeOut' }
        },
      }}
      {...props}
    />
  )
);
MotionCard.displayName = 'MotionCard';

// Animated list container with stagger
interface MotionListProps extends HTMLMotionProps<'div'> {
  staggerDelay?: number;
}

export const MotionList = forwardRef<HTMLDivElement, MotionListProps>(
  ({ staggerDelay = 0.1, children, ...props }, ref) => (
    <motion.div
      ref={ref}
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            staggerChildren: staggerDelay,
            delayChildren: 0.1,
          },
        },
      }}
      {...props}
    >
      {children}
    </motion.div>
  )
);
MotionList.displayName = 'MotionList';

// Animated list item
export const MotionListItem = forwardRef<HTMLDivElement, HTMLMotionProps<'div'>>(
  (props, ref) => (
    <motion.div
      ref={ref}
      variants={staggerItem}
      {...props}
    />
  )
);
MotionListItem.displayName = 'MotionListItem';

// Page transition wrapper
interface PageTransitionProps extends HTMLMotionProps<'div'> {
  children: React.ReactNode;
}

export const PageTransition = forwardRef<HTMLDivElement, PageTransitionProps>(
  ({ children, ...props }, ref) => (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      {...props}
    >
      {children}
    </motion.div>
  )
);
PageTransition.displayName = 'PageTransition';

// Re-export AnimatePresence for convenience
export { AnimatePresence } from 'framer-motion';
