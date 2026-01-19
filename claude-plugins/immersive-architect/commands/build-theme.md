---
name: build-theme
description: Build a complete immersive e-commerce WordPress theme
user-invocable: true
---

# Build Theme

You are building a complete immersive e-commerce WordPress theme with the creative studio team.

## Build Philosophy

**EXCELLENCE THROUGH ITERATION.**

We don't ship "good enough." We Ralph Loop every feature until it's flawless. This is how we build award-winning themes.

## Prerequisites

Before building, ensure you have:
1. A comprehensive theme plan (`/immersive-plan`)
2. Research insights (`/research-theme`)
3. A design system (`/design-system`)

If these don't exist, guide the user to create them first.

## Build Process

### Phase 1: Foundation

Use the **theme-developer** agent to set up:

1. **Theme Structure**
   ```
   theme-name/
   ├── style.css
   ├── functions.php
   ├── inc/
   ├── template-parts/
   ├── assets/
   └── woocommerce/
   ```

2. **Core Setup**
   - Theme supports
   - WooCommerce integration
   - Enqueue scripts/styles
   - Custom post types (if needed)

3. **Design System Implementation**
   - CSS custom properties
   - Global styles
   - Typography setup
   - Color system

4. **Page Builder Configuration**
   - Elementor: Global settings, custom widgets
   - Divi: Theme options, custom modules

### Phase 2: Global Elements

Build with the team:

1. **Header**
   - Logo/branding
   - Navigation
   - Search
   - Cart icon
   - Mobile menu
   - Sticky behavior

2. **Footer**
   - Navigation links
   - Newsletter signup
   - Social links
   - Payment icons
   - Copyright

3. **WooCommerce Global**
   - Mini cart
   - Product quick view
   - Wishlist (if needed)

### Phase 3: Core Pages

**Homepage**
- Hero section (use motion-designer for animations)
- Featured products
- Categories showcase
- Brand story section
- Testimonials
- Newsletter signup

**Shop/Archive**
- Product grid
- Filtering/sorting
- Pagination
- Category headers

**Single Product**
- Product gallery (use 3d-specialist if 3D needed)
- Product info
- Variants/options
- Add to cart
- Related products
- Reviews

**Cart**
- Cart items
- Quantity controls
- Cart totals
- Cross-sells

**Checkout**
- Checkout form
- Order summary
- Payment integration

### Phase 4: Enhancement

**Animations** (motion-designer)
- Page transitions
- Scroll reveals
- Micro-interactions
- Loading states

**3D Elements** (3d-specialist)
- Product viewers
- Virtual showroom
- WebGL backgrounds

**Advanced Features**
- Product configurators
- Size guides
- Comparison tools
- Recently viewed

### Phase 5: Polish

**Performance**
- Image optimization
- Critical CSS
- Script optimization
- Caching configuration

**Accessibility**
- Keyboard navigation
- Screen reader support
- Color contrast
- Focus states

**Cross-Browser**
- Chrome, Firefox, Safari, Edge
- iOS Safari, Chrome Mobile

**Mobile Optimization**
- Touch interactions
- Reduced motion option
- Performance on 3G

## Quality Checklist

Ralph Loop until ALL pass:

### Code Quality
- [ ] No PHP errors or warnings
- [ ] No JavaScript errors
- [ ] WordPress coding standards
- [ ] Clean, documented code
- [ ] No hardcoded strings

### Design Quality
- [ ] Matches design system
- [ ] Consistent spacing
- [ ] Typography hierarchy correct
- [ ] Colors accessible
- [ ] Responsive at all breakpoints

### Performance
- [ ] Page load < 3 seconds
- [ ] Lighthouse score > 90
- [ ] Images optimized
- [ ] Critical CSS inlined
- [ ] JS deferred/async

### WooCommerce
- [ ] All product types work
- [ ] Cart functions correctly
- [ ] Checkout completes
- [ ] Emails styled
- [ ] Account pages work

### Accessibility
- [ ] WCAG AA compliant
- [ ] Keyboard navigable
- [ ] Screen reader tested
- [ ] Reduced motion supported

## Team Coordination

- **Lead Architect**: Orchestrates overall build
- **Visual Designer**: Ensures design consistency
- **Motion Designer**: Handles all animations
- **3D Specialist**: Creates spatial experiences
- **Theme Developer**: Implements everything
- **Experience Researcher**: Validates against research

## Tools

- **Context7**: Fetch official WordPress/WooCommerce docs
- **Serena**: Track build progress
- **Ralph Loop**: Iterate until perfect

## Output

Track progress and document:

```
# Theme Build: [Name]

## Build Status

### Foundation
- [x] Theme structure
- [x] Core setup
- [ ] Design system implementation

### Global Elements
- [ ] Header
- [ ] Footer
- [ ] WooCommerce global

### Core Pages
- [ ] Homepage
- [ ] Shop
- [ ] Product
- [ ] Cart
- [ ] Checkout

### Enhancement
- [ ] Animations
- [ ] 3D elements
- [ ] Advanced features

### Polish
- [ ] Performance
- [ ] Accessibility
- [ ] Cross-browser
- [ ] Mobile

## Quality Status
[Checklist results]

## Files Created
[List of all files]
```

## Important

- Follow the plan - don't skip steps
- Use the right specialist for each task
- Test constantly as you build
- Document everything
- Ralph Loop every component until flawless
