---
name: build-component
description: Build a single immersive component for a WordPress theme
user-invocable: true
---

# Build Component

You are building a single immersive component for a WordPress theme.

## Component Philosophy

**EVERY COMPONENT IS A MICRO-EXPERIENCE.**

Components aren't just HTML/CSS—they're opportunities to delight users. We build each one with the same care we'd give the entire theme.

## Process

### 1. Understand the Component

Ask clarifying questions:
- What is this component for?
- Where will it be used?
- What interactions does it need?
- Does it need animations?
- Does it need 3D elements?
- What's the design direction?

### 2. Assign the Right Specialist

Based on the component type:

**Visual/Static Components** → visual-designer + theme-developer
- Cards, buttons, layouts
- Typography elements
- Static sections

**Animated Components** → motion-designer + theme-developer
- Hero sections with motion
- Animated cards
- Scroll-triggered elements
- Micro-interactions

**3D Components** → 3d-specialist + theme-developer
- Product viewers
- 3D showcases
- WebGL backgrounds
- Virtual spaces

**Complex Components** → Full team coordination
- Product configurators
- Interactive galleries
- Complete page sections

### 3. Build Process

**Step 1: Design Specification**
- Visual appearance
- All states (default, hover, active, disabled)
- Responsive behavior
- Animation/interaction details

**Step 2: HTML Structure**
- Semantic markup
- BEM naming convention
- Accessibility attributes
- Data attributes for JS

**Step 3: CSS Styling**
- Use design system tokens
- Mobile-first responsive
- State variations
- Transitions

**Step 4: JavaScript (if needed)**
- Interaction logic
- Animation code
- AJAX functionality
- Event handlers

**Step 5: Page Builder Integration**
- Elementor widget OR
- Divi module OR
- Shortcode
- Template part

**Step 6: WordPress Integration**
- PHP functions
- Hooks/filters
- Localization
- Security

### 4. Component Types

**Product Card**
```
Elements:
- Image with hover effect
- Quick view button
- Title
- Price (regular/sale)
- Rating stars
- Add to cart button

States:
- Default
- Hover (image zoom, buttons appear)
- Loading (add to cart)
- Added (success feedback)
```

**Hero Section**
```
Elements:
- Background (image/video/gradient)
- Headline (animated entrance)
- Subheadline
- CTA button(s)
- Scroll indicator

Animations:
- Headline reveal
- Parallax background
- Button pulse
```

**Product Gallery**
```
Elements:
- Main image
- Thumbnails
- Zoom functionality
- 3D viewer option
- Navigation arrows

Interactions:
- Click to zoom
- Drag to pan
- Thumbnail selection
- 3D rotation
```

**Testimonial Slider**
```
Elements:
- Quote text
- Author info
- Avatar
- Navigation dots
- Arrows

Animations:
- Slide transitions
- Fade effects
- Auto-play
```

### 5. Output Format

```
# Component: [Name]

## Purpose
[What this component does and where it's used]

## Design Specification

### Visual
- [Description of appearance]
- [Color usage]
- [Typography]
- [Spacing]

### States
- Default: [description]
- Hover: [description]
- Active: [description]
- [Other states]

### Responsive
- Mobile: [behavior]
- Tablet: [behavior]
- Desktop: [behavior]

### Animation
- [Animation 1]: [trigger, duration, easing]
- [Animation 2]: [trigger, duration, easing]

## Implementation

### HTML
\`\`\`html
[Semantic HTML structure]
\`\`\`

### CSS
\`\`\`css
[Styles using design system tokens]
\`\`\`

### JavaScript
\`\`\`javascript
[Interaction/animation code]
\`\`\`

### PHP
\`\`\`php
[WordPress integration]
\`\`\`

### Elementor Widget (if applicable)
\`\`\`php
[Widget class]
\`\`\`

### Divi Module (if applicable)
\`\`\`php
[Module class]
\`\`\`

## Usage

### Shortcode
[shortcode_name attr="value"]

### Template
get_template_part('template-parts/components/[name]');

### Elementor
Add "[Widget Name]" from the widget panel

### Divi
Add "[Module Name]" from the module panel

## Quality Checklist

- [ ] Matches design system
- [ ] All states work correctly
- [ ] Responsive at all breakpoints
- [ ] Animations smooth (60fps)
- [ ] Accessible (keyboard, screen reader)
- [ ] Cross-browser compatible
- [ ] Performance optimized
- [ ] Code is clean and documented

## Testing

- [ ] Visual matches specification
- [ ] All interactions work
- [ ] Mobile touch works
- [ ] Reduced motion respected
- [ ] No console errors
```

## Important

- Use design system tokens, not hardcoded values
- Test every state and breakpoint
- Ensure accessibility from the start
- Document usage clearly
- Ralph Loop until the component is flawless
