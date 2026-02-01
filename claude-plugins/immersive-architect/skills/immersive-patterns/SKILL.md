# Immersive E-commerce Patterns

This skill provides design patterns for creating immersive, interactive e-commerce experiences. It activates when users mention "immersive design", "interactive experience", "e-commerce patterns", "engaging shopping", or want to create standout online stores.

---

## What Makes an Experience Immersive

### The Three Pillars
1. **Visual Depth** - Layers, parallax, 3D, shadows create dimension
2. **Responsive Interaction** - Every action has satisfying feedback
3. **Emotional Journey** - Story and pacing that builds desire

### Beyond Flat Design
Immersive isn't just "pretty." It's:
- Purposeful motion that guides
- Depth that creates hierarchy
- Interactions that reward exploration
- Pacing that builds anticipation

## Hero Section Patterns

### Cinematic Hero
```
┌─────────────────────────────────────────────┐
│  [Full-screen video/image background]       │
│                                             │
│     HEADLINE THAT STOPS SCROLLING           │
│     Supporting text that intrigues          │
│                                             │
│            [ Explore →]                     │
│                                             │
│     ↓ Scroll indicator                      │
└─────────────────────────────────────────────┘
```
- Video or animated background
- Text reveals on load
- Parallax depth on scroll
- Magnetic CTA button

### Product Showcase Hero
```
┌─────────────────────────────────────────────┐
│  Floating                    Brand          │
│  navigation                  Logo           │
├─────────────────────────────────────────────┤
│                                             │
│   Text        │      3D Product             │
│   Content     │      (draggable/rotating)   │
│               │                             │
│   [Shop Now]  │      Price floating         │
│                                             │
└─────────────────────────────────────────────┘
```
- 3D product that users can rotate
- Text animates in from left
- Product casts realistic shadow
- Price tag floats dynamically

### Split-Screen Hero
```
┌──────────────────┬──────────────────────────┐
│                  │                          │
│    Image/Video   │    Headline              │
│    (parallax)    │    Description           │
│                  │    [CTA Button]          │
│                  │                          │
└──────────────────┴──────────────────────────┘
```
- Image moves at different scroll speed
- Text side has subtle gradient
- On mobile, stacks elegantly

## Product Grid Patterns

### Masonry with Hover Depth
- Products at varying heights
- On hover: lift up with shadow
- Quick-view appears from bottom
- Add to cart button reveals

### Infinite Gallery
- Products load as you scroll
- Subtle entrance animations
- Filter/sort without page reload
- Smooth transitions between views

### Category Takeover
- Click category: full-screen transition
- Products animate in as grid
- Category image becomes header
- Smooth filtering animations

## Product Detail Patterns

### Gallery Theater
- Main image takes 60%+ width
- Thumbnails as filmstrip below
- Click thumbnail: smooth crossfade
- Zoom: lens follows cursor
- Full-screen gallery mode

### Sticky Add-to-Cart
```
┌─────────────────────────────────────────────┐
│  [Gallery]              │ Product Title     │
│                         │ Price             │
│                         │ Description       │
│                         │                   │
│                         │ [Variants]        │
│                         │                   │
│                         │ ──────────────────│
│                         │ [Add to Cart]     │ ← Sticks on scroll
└─────────────────────────────────────────────┘
```

### Scroll Story Product
- Each scroll section reveals feature
- Product rotates to show angles
- Text appears at key moments
- Builds desire through pacing

## Navigation Patterns

### Magnetic Navigation
- Links attract cursor slightly
- Hover reveals underline animation
- Active state has subtle glow
- Mobile: swipe-friendly menu

### Full-Screen Menu Takeover
- Menu icon morphs to X
- Background fades to brand color
- Links animate in staggered
- Categories expand on click

### Floating Mini-Cart
- Cart icon shows count
- Hover/click reveals preview
- Items can be removed inline
- Checkout button prominent

## Micro-interaction Patterns

### Buttons
- Hover: lift + shadow
- Click: press down
- Success: checkmark animation
- Loading: subtle pulse

### Form Fields
- Focus: label floats up
- Typing: subtle border animation
- Valid: green checkmark
- Error: shake + red highlight

### Cards
- Hover: slight lift
- Image zooms subtly
- Quick-action buttons appear
- Add-to-cart: item flies to cart

## Scroll-Driven Patterns

### Parallax Layers
```
Layer 1 (back): moves 0.3x scroll speed
Layer 2 (mid): moves 0.6x scroll speed
Layer 3 (front): moves 1x scroll speed
```

### Reveal Sections
- Content fades up as enters viewport
- Stagger children for flow
- Use intersection observer
- Don't animate too much at once

### Scroll Progress
- Progress bar at top
- Section indicators
- "Back to top" appears
- Reading time indicator

## Loading Patterns

### Skeleton Screens
- Show content structure immediately
- Pulse animation on placeholders
- Content fades in when ready
- Never show empty states

### Progressive Loading
- Critical content first
- Images lazy load
- Below-fold deferred
- Animations load last

## 2D/2.5D Techniques

Even without full 3D, create depth:
- **Layered shadows** - Multiple shadows at different distances
- **Perspective transforms** - Subtle tilt on hover
- **Gradient depth** - Gradients that suggest light source
- **Overlapping elements** - Cards that peek behind others
- **Parallax scrolling** - Elements at different speeds
- **Floating elements** - Subtle up/down animation

## Implementation Considerations

### Performance
- 60fps animations
- Hardware-accelerated properties
- Lazy load heavy elements
- Reduced motion support

### Mobile
- Touch-friendly targets (44px+)
- Swipe gestures where appropriate
- Simplified animations
- Bottom-reachable actions

### Accessibility
- Animations respect prefers-reduced-motion
- Focus states visible
- Screen reader friendly
- Keyboard navigable
