# SkyyRose Luxury Animation System

Comprehensive GSAP-powered animation framework with Framer Motion-inspired timing and rose gold aesthetics.

## Overview

The animation system provides:
- **10 animation modules** covering all page interactions
- **Rose gold (#B76E79)** themed effects
- **Luxury timing** with power3.out easing
- **Mobile optimization** with reduced motion support
- **Performance-first** with GPU acceleration and lazy loading

---

## Files

| File | Purpose | Lines |
|------|---------|-------|
| `assets/js/animations.js` | GSAP animation logic | 830 lines |
| `assets/css/animations.css` | Utility classes & keyframes | 580 lines |

---

## Animation Modules

### 1. Page Load Animations
**Auto-activates on page load**

Animates body fade-in, header slide-down, and main content stagger.

```javascript
// Automatically applied, no code needed
```

**CSS Classes:**
- `.fade-in` - Fade in element
- `.fade-in-up` - Fade in from below
- `.fade-in-down` - Fade in from above

---

### 2. Hero Section Animations
**Auto-activates on hero sections**

Targets: `.hero`, `.page-header`, `.entry-header`

Animates:
- Hero title (50px up, fade in)
- Subtitle (30px up, fade in)
- Buttons (stagger, 20px up)
- Hero image (Ken Burns scale effect)

**Example:**
```html
<div class="hero">
    <h1>Your Hero Title</h1>
    <p>Your subtitle</p>
    <a href="#" class="btn">Call to Action</a>
    <img src="hero.jpg" alt="Hero">
</div>
```

---

### 3. Scroll Animations
**Auto-activates on scroll**

Targets:
- `section`, `article`, `.content-section`
- `.post-card`, `.entry`, `.product`
- `.glass`, `.card`, `.box`
- Images for parallax (desktop only)
- Text blocks in `.entry-content`
- Counters with `[data-count]` attribute

**Parallax Example:**
```html
<div class="post-thumbnail">
    <img src="image.jpg" alt="Parallax" class="parallax-image">
</div>
```

**Counter Example:**
```html
<div class="counter" data-count="1250">0</div>
```

**CSS Classes:**
- `.reveal-on-scroll` - Reveal on scroll (add `.visible` via JS)
- `.stagger-item` - Auto-stagger on scroll

---

### 4. Hover Effects
**Auto-activates on hover**

**Buttons:**
- Scale up to 1.05
- Rose gold glow shadow

**Links:**
- Color change to rose gold
- Smooth 0.3s transition

**Cards:**
- Lift up 10px
- Add rose gold shadow

**Images:**
- Zoom to 1.1 scale

**CSS Classes:**
- `.hover-lift` - Lift on hover
- `.hover-zoom` - Zoom image on hover
- `.rose-gold-glow` - Rose gold glow effect
- `.animated-underline` - Underline appears on hover

**Example:**
```html
<div class="card hover-lift">
    <div class="hover-zoom">
        <img src="image.jpg" alt="Zoom on hover">
    </div>
    <a href="#" class="animated-underline">Read more</a>
</div>
```

---

### 5. Navigation Animations
**Auto-activates on navigation**

**Mobile Menu:**
- Slide in from left (300px)
- Stagger menu items (0.05s delay)

**Header Scroll:**
- Adds `.scrolled` class at 100px scroll
- Background blur and darkening

**Example:**
```html
<header class="site-header">
    <button class="menu-toggle">Menu</button>
    <nav class="mobile-menu">
        <ul class="menu">
            <li class="menu-item"><a href="#">Home</a></li>
            <li class="menu-item"><a href="#">Shop</a></li>
        </ul>
    </nav>
</header>
```

---

### 6. Product Animations (WooCommerce)
**Auto-activates on product pages**

Targets:
- `.product`, `.woocommerce-LoopProduct-link`
- `.add_to_cart_button`, `.single_add_to_cart_button`
- `.woocommerce-product-gallery__image`
- `.price`, `.woocommerce-Price-amount`

**Add to Cart Animation:**
- Scale down to 0.9, bounce back
- Automatic on click

**Price Reveal:**
- Scale from 0 with elastic bounce

---

### 7. Text Animations
**Auto-activates on headings**

Targets: `h1`, `h2`, `h3`, `.animate-text`

**Split Text Animation:**
- Characters animate in with 0.03s stagger
- 20px up fade-in per character

**CSS Classes:**
- `.text-reveal` - Wipe reveal left to right
- `.text-shimmer` - Animated shimmer gradient
- `.text-gradient` - Rose gold to gold gradient

**Example:**
```html
<h1 class="animate-text">Luxury Heading</h1>
<p class="text-gradient">Gradient text</p>
<span class="text-shimmer">Shimmering effect</span>
```

---

### 8. Image Animations
**Auto-activates on images**

**Lazy Load:**
- Fade in + scale from 1.1 on load

**Image Overlays:**
- Slide in from left (scaleX animation)

**Galleries:**
- Stagger items with 0.1s delay
- Scale from 0.8

**CSS Classes:**
- `.image-overlay-effect` - Rose gold overlay on hover
- `.float` - Floating animation loop

**Example:**
```html
<div class="image-overlay-effect hover-zoom">
    <img src="image.jpg" alt="Overlay effect" loading="lazy">
</div>
```

---

### 9. Form Animations
**Auto-activates on forms**

**Field Focus:**
- Border changes to rose gold
- Rose gold shadow (3px glow)
- Label moves up 5px

**Form Submit:**
- Button scale down to 0.95, bounce back

**Form Elements Scroll:**
- Stagger reveal with 0.05s delay

**Example:**
```html
<form>
    <label for="email">Email</label>
    <input type="email" id="email" name="email">
    <button type="submit" class="btn-luxury">Submit</button>
</form>
```

---

### 10. Page Transitions
**Auto-activates on navigation**

**Smooth Scroll:**
- Anchor links scroll with easing
- 100px offset for header

**Scroll to Top:**
- Appears after 200px scroll
- Smooth scroll to top on click

**Example:**
```html
<a href="#section" class="scroll-link">Scroll to Section</a>
<button class="scroll-to-top">↑</button>
```

---

## CSS Utility Classes

### Layout & Visibility
```css
.fade-in              /* Fade in */
.fade-in-up          /* Fade in from below */
.fade-in-down        /* Fade in from above */
.fade-in-left        /* Fade in from left */
.fade-in-right       /* Fade in from right */
```

### Scale Effects
```css
.scale-in            /* Scale in with bounce */
.scale-in-center     /* Scale from center */
```

### Slide Effects
```css
.slide-in-left       /* Slide from left */
.slide-in-right      /* Slide from right */
```

### Glow & Shadows
```css
.rose-gold-glow      /* Rose gold shadow */
.pulse-glow          /* Pulsing glow animation */
```

### Hover Effects
```css
.hover-lift          /* Lift 10px on hover */
.hover-zoom          /* Zoom image 1.1x on hover */
.rotate-on-hover     /* Rotate 5deg on hover */
```

### Glassmorphism
```css
.glass               /* Glassmorphism effect */
```

### Buttons
```css
.btn-luxury          /* Luxury button with ripple effect */
```

### Text Effects
```css
.text-reveal         /* Wipe reveal animation */
.text-shimmer        /* Shimmer gradient */
.text-gradient       /* Rose gold gradient */
.animated-underline  /* Animated underline on hover */
```

### Loading States
```css
.skeleton-loading    /* Skeleton loading animation */
.spinner             /* Rose gold spinner */
```

### Special Effects
```css
.float               /* Floating animation */
.scroll-indicator    /* Scroll bounce indicator */
```

### Performance
```css
.will-animate        /* Hint browser to optimize */
.gpu-accelerate      /* Force GPU acceleration */
```

---

## Configuration

### Timing
```javascript
const config = {
    durations: {
        fast: 0.3s,
        normal: 0.6s,
        slow: 1.2s,
        verySlow: 1.8s
    },
    easing: {
        luxury: 'power3.out',      // Main easing
        smooth: 'power2.inOut',    // Smooth transitions
        bounce: 'elastic.out',     // Bouncy effects
        snap: 'back.out(1.7)'      // Snap back effect
    }
}
```

### Colors
```css
:root {
    --rose-gold: #B76E79;
    --rose-gold-glow: rgba(183, 110, 121, 0.3);
    --gold: #D4AF37;
}
```

---

## Usage Examples

### Hero Section
```html
<section class="hero">
    <h1>Luxury Fashion</h1>
    <p>Where Love Meets Luxury</p>
    <a href="#shop" class="btn-luxury hover-lift">Shop Now</a>
    <img src="hero.jpg" alt="Hero">
</section>
```

### Product Grid
```html
<div class="products-grid">
    <div class="product hover-lift">
        <div class="hover-zoom">
            <img src="product.jpg" alt="Product" loading="lazy">
        </div>
        <h3>Product Name</h3>
        <span class="price text-gradient">$199</span>
        <button class="add_to_cart_button btn-luxury">Add to Cart</button>
    </div>
</div>
```

### Testimonial Cards
```html
<div class="testimonials">
    <div class="card glass hover-lift stagger-item">
        <p class="text-shimmer">"Amazing quality!"</p>
        <strong>— Sarah M.</strong>
    </div>
</div>
```

### Counter Section
```html
<section class="stats">
    <div class="stat">
        <div class="counter" data-count="10000">0</div>
        <p>Happy Customers</p>
    </div>
    <div class="stat">
        <div class="counter" data-count="5000">0</div>
        <p>Products Sold</p>
    </div>
</section>
```

### Form with Animations
```html
<form class="contact-form">
    <div class="form-group">
        <label for="name">Name</label>
        <input type="text" id="name" name="name">
    </div>
    <div class="form-group">
        <label for="email">Email</label>
        <input type="email" id="email" name="email">
    </div>
    <button type="submit" class="btn-luxury">Send Message</button>
</form>
```

---

## Mobile Optimization

### Automatic Adjustments
- **Durations reduced** by 50% on mobile
- **Parallax disabled** on mobile for performance
- **Hover effects simplified** (lift reduced to 5px)

### Reduced Motion
Respects `prefers-reduced-motion: reduce`:
- All animations set to 0.01ms duration
- Scroll behavior set to auto
- Animations skip automatically

---

## Performance Tips

1. **Use `will-animate` class** for elements that will animate:
```html
<div class="will-animate fade-in-up">Content</div>
```

2. **GPU acceleration** for transform-heavy animations:
```html
<div class="gpu-accelerate hover-lift">Card</div>
```

3. **Lazy load images** with native loading:
```html
<img src="image.jpg" alt="Lazy" loading="lazy">
```

4. **Limit parallax elements** to 5-10 per page

5. **Avoid animating on mobile** when possible

---

## Browser Support

| Browser | Version | Support |
|---------|---------|---------|
| Chrome | 90+ | Full |
| Firefox | 88+ | Full |
| Safari | 14+ | Full |
| Edge | 90+ | Full |
| Mobile Safari | iOS 14+ | Full |
| Chrome Mobile | Latest | Optimized |

**Requirements:**
- GSAP 3.12.5+
- ScrollTrigger plugin
- Modern browser with CSS Grid support

---

## Troubleshooting

### Animations not working
1. Check GSAP is loaded: `console.log(typeof gsap)`
2. Check ScrollTrigger: `console.log(typeof ScrollTrigger)`
3. Check browser console for errors
4. Verify elements have correct classes

### Performance issues
1. Reduce parallax elements
2. Disable on mobile: `if (!isMobile()) { animate(); }`
3. Use `will-animate` class
4. Check for memory leaks with ScrollTrigger

### Reduced motion not working
1. Test: `window.matchMedia('(prefers-reduced-motion: reduce)').matches`
2. Verify OS-level setting is enabled
3. Check animations.js line 45

---

## SkyyRose Brand Guidelines

### Animation Personality
- **Elegant** - Smooth, refined movements
- **Luxurious** - Long durations (1.2s+), power3.out easing
- **Sophisticated** - Rose gold glows, subtle effects
- **Confident** - Snap-back hovers, bounce effects

### Do's
✅ Use rose gold (#B76E79) for glows and accents
✅ Use power3.out easing for luxury feel
✅ Stagger animations for elegance
✅ Add subtle hover effects
✅ Respect reduced motion preferences

### Don'ts
❌ Don't use fast, jarring animations
❌ Don't overuse bounce effects
❌ Don't animate too many elements at once
❌ Don't use bright, neon colors
❌ Don't ignore mobile performance

---

## Version History

**v3.0.0** (Current)
- Complete rewrite with 10 animation modules
- Rose gold luxury aesthetics
- Mobile optimization
- Reduced motion support
- 830 lines of animation logic
- 580 lines of CSS utilities

**v2.0.0** (Previous)
- Basic GSAP implementation
- 3 simple animations
- 62 lines total

---

**Documentation by**: SkyyRose Development Team
**Last Updated**: 2026-02-02
**WordPress Theme**: SkyyRose 2025 v3.0.0
