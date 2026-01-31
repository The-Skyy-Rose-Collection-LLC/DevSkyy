# SkyyRose Immersive Components - Integration Guide

## Components Created

1. **3D Product Viewer** - Three.js GLTF loader with orbit controls
2. **Scroll Animations** - GSAP ScrollTrigger animations  
3. **Component Styles** - Complete CSS for all components

## Quick Start

Add to functions.php:

```php
function skyyrose_enqueue_immersive_components() {
    wp_enqueue_style('skyyrose-components', get_template_directory_uri() . '/assets/css/components.css', array(), '1.0.0');
    wp_enqueue_script('skyyrose-3d-viewer', get_template_directory_uri() . '/assets/js/components/3d-product-viewer.js', array(), '1.0.0', true);
    wp_enqueue_script('skyyrose-scroll-animations', get_template_directory_uri() . '/assets/js/components/scroll-animations.js', array(), '1.0.0', true);
}
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_immersive_components');
```

## Usage Examples

3D Viewer:
```html
<div data-component="3d-viewer" data-model="model.glb" data-fallback="image.jpg"></div>
```

Scroll Animations:
```html
<div data-animate="fade-in">Content</div>
<div data-animate="stagger"><div>Item 1</div><div>Item 2</div></div>
<div data-animate="parallax" data-speed="0.5">Background</div>
<div data-animate="pin">Pinned section</div>
<div data-animate="scale">Scaled content</div>
```

All components are production-ready, security-hardened, and mobile-optimized!
