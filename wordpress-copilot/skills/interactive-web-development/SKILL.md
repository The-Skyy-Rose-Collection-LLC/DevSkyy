---
name: Interactive Web Development
description: Expert knowledge in building interactive, dynamic web experiences with React, Vue, Svelte, animations, and user interactions. Triggers on keywords like "interactive", "animation", "dynamic", "react", "vue", "svelte", "gsap", "framer motion", "scroll animations", "parallax", "hover effects", "transitions".
version: 1.0.0
---

# Interactive Web Development

Build engaging, interactive web experiences with modern JavaScript frameworks, animation libraries, and interaction patterns.

## When to Use This Skill

Activate when working on:
- React, Vue, or Svelte components with rich interactions
- Scroll-based animations and parallax effects
- Hover states, transitions, and micro-interactions
- Form animations and validation UX
- Loading states and skeleton screens
- Interactive data visualizations
- Gesture-based interfaces
- State management for complex UIs

## Core Technologies

### React Ecosystem

**React + TypeScript** for type-safe components:
```typescript
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ProductCardProps {
  product: Product;
  onQuickView: (id: string) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product, onQuickView }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.div
      className="product-card"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
    >
      <motion.img
        src={product.image}
        alt={product.name}
        animate={{ scale: isHovered ? 1.1 : 1 }}
        transition={{ duration: 0.3 }}
      />

      <AnimatePresence>
        {isHovered && (
          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            onClick={() => onQuickView(product.id)}
          >
            Quick View
          </motion.button>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
```

**React Hooks** for complex state logic:
```typescript
function useIntersectionObserver(
  ref: RefObject<Element>,
  options: IntersectionObserverInit = {}
) {
  const [isIntersecting, setIsIntersecting] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
    }, options);

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [ref, options]);

  return isIntersecting;
}

// Usage: Lazy load 3D viewer
function ProductViewer({ modelUrl }: { modelUrl: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const isVisible = useIntersectionObserver(ref, { threshold: 0.5 });

  return (
    <div ref={ref}>
      {isVisible && <ThreeJSViewer modelUrl={modelUrl} />}
    </div>
  );
}
```

### Animation Libraries

**Framer Motion** for React animations:
```typescript
import { motion, useScroll, useTransform } from 'framer-motion';

function ParallaxSection() {
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], ['0%', '50%']);
  const opacity = useTransform(scrollYProgress, [0, 0.5, 1], [1, 0.5, 0]);

  return (
    <motion.section style={{ y, opacity }}>
      <h2>SkyyRose Collection</h2>
      <p>Where Love Meets Luxury</p>
    </motion.section>
  );
}
```

**GSAP** for advanced scroll animations:
```typescript
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

useEffect(() => {
  gsap.to('.product-grid', {
    scrollTrigger: {
      trigger: '.product-grid',
      start: 'top center',
      end: 'bottom center',
      scrub: 1,
    },
    scale: 1.1,
    opacity: 1,
  });
}, []);
```

**React Spring** for physics-based animations:
```typescript
import { useSpring, animated } from '@react-spring/web';

function BouncyButton() {
  const [{ scale }, api] = useSpring(() => ({ scale: 1 }));

  return (
    <animated.button
      style={{ scale }}
      onMouseDown={() => api.start({ scale: 0.9 })}
      onMouseUp={() => api.start({ scale: 1 })}
    >
      Add to Cart
    </animated.button>
  );
}
```

### Vue 3 Composition API

```vue
<template>
  <Transition name="fade">
    <div v-if="isVisible" class="modal">
      <div class="modal-content" @click.stop>
        <slot />
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

const props = defineProps<{
  show: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const isVisible = ref(props.show);

const handleEscape = (e: KeyboardEvent) => {
  if (e.key === 'Escape') emit('close');
};

onMounted(() => {
  document.addEventListener('keydown', handleEscape);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape);
});
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
```

### Svelte for Simple Interactions

```svelte
<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';

  export let items: Product[] = [];

  let selectedItem: Product | null = null;
</script>

{#each items as item (item.id)}
  <div
    class="item"
    in:fly={{ y: 50, duration: 300, easing: quintOut }}
    out:fade={{ duration: 200 }}
    on:click={() => selectedItem = item}
  >
    <img src={item.image} alt={item.name} />
    <h3>{item.name}</h3>
  </div>
{/each}

{#if selectedItem}
  <div transition:fade>
    <ProductDetail product={selectedItem} />
  </div>
{/if}
```

## Interaction Patterns

### Scroll-Based Interactions

**Reveal on Scroll:**
```typescript
function RevealOnScroll({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const isVisible = useIntersectionObserver(ref);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isVisible ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
}
```

**Stagger Children:**
```typescript
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

<motion.div variants={container} initial="hidden" animate="show">
  {products.map(product => (
    <motion.div key={product.id} variants={item}>
      <ProductCard product={product} />
    </motion.div>
  ))}
</motion.div>
```

### Gesture-Based Interactions

**Drag and Drop:**
```typescript
import { motion } from 'framer-motion';

<motion.div
  drag
  dragConstraints={{ left: 0, right: 300, top: 0, bottom: 0 }}
  dragElastic={0.2}
  onDragEnd={(event, info) => {
    if (info.offset.x > 100) {
      // Swiped right
      onNextProduct();
    }
  }}
>
  <ProductImage />
</motion.div>
```

**Touch Gestures:**
```typescript
import { useGesture } from '@use-gesture/react';
import { useSpring, animated } from '@react-spring/web';

function SwipeableCard() {
  const [{ x, opacity }, api] = useSpring(() => ({ x: 0, opacity: 1 }));

  const bind = useGesture({
    onDrag: ({ movement: [mx], direction: [xDir], velocity: [vx] }) => {
      const trigger = vx > 0.2;
      const dir = xDir < 0 ? -1 : 1;

      if (!trigger) {
        api.start({ x: 0, opacity: 1 });
      } else {
        api.start({ x: dir * 300, opacity: 0 });
        setTimeout(() => onSwipe(dir), 300);
      }
    }
  });

  return <animated.div {...bind()} style={{ x, opacity }} />;
}
```

### Micro-Interactions

**Button Feedback:**
```typescript
const ButtonWithFeedback: React.FC<{ onClick: () => void }> = ({ onClick }) => {
  const [{ scale, backgroundColor }, api] = useSpring(() => ({
    scale: 1,
    backgroundColor: '#B76E79'
  }));

  const handleClick = () => {
    api.start({
      scale: 0.95,
      config: { tension: 300, friction: 10 }
    });
    setTimeout(() => api.start({ scale: 1 }), 100);
    onClick();
  };

  return (
    <animated.button
      style={{ scale, backgroundColor }}
      onClick={handleClick}
      onHoverStart={() => api.start({ backgroundColor: '#A65E69' })}
      onHoverEnd={() => api.start({ backgroundColor: '#B76E79' })}
    >
      Add to Cart
    </animated.button>
  );
};
```

**Loading States:**
```typescript
function LoadingButton({ isLoading, onClick, children }) {
  return (
    <motion.button
      onClick={onClick}
      disabled={isLoading}
      animate={{ width: isLoading ? 40 : 'auto' }}
    >
      <AnimatePresence mode="wait">
        {isLoading ? (
          <motion.div
            key="spinner"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, rotate: 360 }}
            exit={{ opacity: 0 }}
            transition={{ rotate: { repeat: Infinity, duration: 1 } }}
          >
            ⏳
          </motion.div>
        ) : (
          <motion.span
            key="text"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {children}
          </motion.span>
        )}
      </AnimatePresence>
    </motion.button>
  );
}
```

## Performance Optimization

**Lazy Loading Components:**
```typescript
import { lazy, Suspense } from 'react';

const Heavy3DViewer = lazy(() => import('./Heavy3DViewer'));

function ProductPage() {
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <Heavy3DViewer />
    </Suspense>
  );
}
```

**Memoization:**
```typescript
import { memo, useMemo } from 'react';

const ProductCard = memo(({ product }: { product: Product }) => {
  const discountedPrice = useMemo(
    () => calculateDiscount(product.price, product.discount),
    [product.price, product.discount]
  );

  return <div>{discountedPrice}</div>;
});
```

**Virtual Scrolling:**
```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

function ProductList({ products }: { products: Product[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: products.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 350,
    overscan: 5
  });

  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
        {virtualizer.getVirtualItems().map(item => (
          <div
            key={item.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${item.start}px)`
            }}
          >
            <ProductCard product={products[item.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

## SkyyRose-Specific Patterns

### Luxury Transition Timings

```typescript
export const skyyrose = {
  transitions: {
    fast: { duration: 0.15, ease: 'easeOut' },
    base: { duration: 0.3, ease: 'easeInOut' },
    slow: { duration: 0.6, ease: [0.43, 0.13, 0.23, 0.96] },
    spring: { type: 'spring', stiffness: 300, damping: 30 }
  },
  colors: {
    primary: '#B76E79',
    primaryHover: '#A65E69',
    secondary: '#2C2C2C'
  }
};
```

### Rose Gold Gradient Animations

```typescript
function RoseGoldShimmer() {
  return (
    <motion.div
      className="shimmer"
      animate={{
        backgroundPosition: ['0% 50%', '100% 50%', '0% 50%']
      }}
      transition={{
        duration: 3,
        repeat: Infinity,
        ease: 'linear'
      }}
      style={{
        background: 'linear-gradient(90deg, #B76E79 0%, #E8C5A5 50%, #B76E79 100%)',
        backgroundSize: '200% 100%'
      }}
    />
  );
}
```

## Accessibility

Ensure animations respect user preferences:

```typescript
import { useReducedMotion } from 'framer-motion';

function AccessibleAnimation() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      animate={{ opacity: 1 }}
      transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.6 }}
    >
      Content
    </motion.div>
  );
}
```

## References

See `references/` for detailed guides:
- `react-animation-patterns.md` - Complete React animation patterns
- `vue-interaction-guide.md` - Vue 3 Composition API interactions
- `gsap-scroll-animations.md` - Advanced GSAP techniques
- `performance-optimization.md` - Animation performance best practices
- `accessibility-guidelines.md` - Motion accessibility

## Examples

See `examples/` for working implementations:
- `product-card-hover.tsx` - Interactive product card
- `scroll-reveal.tsx` - Scroll-based reveal animations
- `gesture-swipe.tsx` - Touch gesture handling
- `loading-states.tsx` - Loading and skeleton screens
- `parallax-section.tsx` - Parallax scroll effects
