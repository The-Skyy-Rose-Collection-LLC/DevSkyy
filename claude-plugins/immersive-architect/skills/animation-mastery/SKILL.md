# Animation Mastery

This skill provides comprehensive knowledge of web animation techniques for e-commerce. It activates when users mention "GSAP", "Framer Motion", "animations", "transitions", "scroll effects", "micro-interactions", or need to add motion to their themes.

---

## Animation Philosophy

**Motion with meaning.** Every animation should:
1. Guide attention
2. Provide feedback
3. Create continuity
4. Express personality
5. Never obstruct

## GSAP (GreenSock Animation Platform)

### Setup
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js"></script>
```

### Basic Animations
```javascript
// Fade in
gsap.from('.element', {
  opacity: 0,
  duration: 0.6,
  ease: 'power2.out'
});

// Slide up
gsap.from('.element', {
  y: 50,
  opacity: 0,
  duration: 0.8,
  ease: 'power3.out'
});

// Scale in
gsap.from('.element', {
  scale: 0.8,
  opacity: 0,
  duration: 0.5,
  ease: 'back.out(1.7)'
});
```

### Staggered Animations
```javascript
// Product cards entrance
gsap.from('.product-card', {
  y: 60,
  opacity: 0,
  duration: 0.8,
  stagger: 0.1,
  ease: 'power3.out'
});

// Text lines
gsap.from('.hero-text span', {
  y: '100%',
  duration: 0.8,
  stagger: 0.05,
  ease: 'power4.out'
});
```

### ScrollTrigger
```javascript
gsap.registerPlugin(ScrollTrigger);

// Reveal on scroll
gsap.from('.section', {
  scrollTrigger: {
    trigger: '.section',
    start: 'top 80%',
    end: 'bottom 20%',
    toggleActions: 'play none none reverse'
  },
  y: 100,
  opacity: 0,
  duration: 1
});

// Pin section
ScrollTrigger.create({
  trigger: '.pinned-section',
  start: 'top top',
  end: '+=500',
  pin: true,
  scrub: 1
});

// Parallax
gsap.to('.parallax-bg', {
  y: '-30%',
  scrollTrigger: {
    trigger: '.hero',
    start: 'top top',
    end: 'bottom top',
    scrub: true
  }
});
```

### Timelines
```javascript
const tl = gsap.timeline({
  defaults: { ease: 'power3.out' }
});

tl.from('.logo', { y: -20, opacity: 0, duration: 0.5 })
  .from('.nav-links a', { y: -20, opacity: 0, stagger: 0.1 }, '-=0.3')
  .from('.hero-title', { y: 40, opacity: 0, duration: 0.8 }, '-=0.2')
  .from('.hero-subtitle', { y: 20, opacity: 0 }, '-=0.4')
  .from('.hero-cta', { scale: 0.9, opacity: 0 }, '-=0.2');
```

## Framer Motion (React)

### Basic Usage
```jsx
import { motion } from 'framer-motion';

// Fade in
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ duration: 0.5 }}
>
  Content
</motion.div>

// Slide up
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.5, ease: [0.25, 0.1, 0.25, 1] }}
>
  Content
</motion.div>
```

### Variants
```jsx
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

<motion.ul variants={containerVariants} initial="hidden" animate="visible">
  {items.map(item => (
    <motion.li key={item.id} variants={itemVariants}>
      {item.name}
    </motion.li>
  ))}
</motion.ul>
```

### Scroll Animations
```jsx
import { motion, useScroll, useTransform } from 'framer-motion';

function ParallaxSection() {
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], ['0%', '-30%']);

  return (
    <motion.div style={{ y }}>
      Parallax content
    </motion.div>
  );
}
```

### Gestures
```jsx
<motion.button
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
  transition={{ type: 'spring', stiffness: 400 }}
>
  Click Me
</motion.button>
```

## CSS Animations

### Transitions
```css
/* Smooth hover */
.button {
  transition: all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* Card lift */
.card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.1);
}
```

### Keyframe Animations
```css
/* Fade up */
@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-up {
  animation: fadeUp 0.6s ease forwards;
}

/* Pulse */
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.pulse {
  animation: pulse 2s infinite;
}

/* Shimmer loading */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

## Timing & Easing

### Duration Guide
| Animation Type | Duration |
|---------------|----------|
| Micro-interaction | 100-200ms |
| Button feedback | 150-250ms |
| Small UI change | 200-300ms |
| Content reveal | 400-600ms |
| Page transition | 300-500ms |
| Complex sequence | 800-1200ms |

### Easing Functions
```css
/* Standard easings */
--ease-out: cubic-bezier(0.25, 0.1, 0.25, 1);
--ease-in-out: cubic-bezier(0.42, 0, 0.58, 1);
--ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);
--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);

/* GSAP equivalents */
ease: 'power2.out'    /* Standard deceleration */
ease: 'power3.out'    /* Snappier deceleration */
ease: 'back.out(1.7)' /* Overshoot */
ease: 'elastic.out'   /* Bouncy */
```

## Common Animation Patterns

### Add to Cart
```javascript
function addToCartAnimation(productElement, cartIcon) {
  const clone = productElement.querySelector('img').cloneNode();
  const cartRect = cartIcon.getBoundingClientRect();

  gsap.to(clone, {
    x: cartRect.x,
    y: cartRect.y,
    scale: 0.1,
    opacity: 0,
    duration: 0.6,
    ease: 'power2.in',
    onComplete: () => clone.remove()
  });

  gsap.from(cartIcon, {
    scale: 1.3,
    duration: 0.3,
    ease: 'back.out'
  });
}
```

### Page Transition
```javascript
function pageTransition() {
  const tl = gsap.timeline();

  tl.to('.page-transition', {
    scaleY: 1,
    transformOrigin: 'bottom',
    duration: 0.5,
    ease: 'power4.inOut'
  })
  .to('.page-transition', {
    scaleY: 0,
    transformOrigin: 'top',
    duration: 0.5,
    ease: 'power4.inOut'
  });

  return tl;
}
```

## Accessibility

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

```javascript
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

if (!prefersReducedMotion) {
  // Run animations
}
```
