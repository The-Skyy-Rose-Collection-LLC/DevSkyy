# SkyyRose Design & Imagery Enhancement Guide

## 🎨 New Packages Installed

### JavaScript/TypeScript (24 packages)

#### 3D & Immersive
- `@react-three/fiber` (9.5.0) - React bindings for Three.js
- `@react-three/drei` (10.7.7) - 100+ Three.js helpers
- `postprocessing` (6.38.2) - Post-processing effects
- `@google/model-viewer` (4.1.0) - AR-ready 3D viewer
- `@pixiv/three-vrm` (3.4.5) - VRM avatar support
- `troika-three-text` (0.52.4) - High-quality 3D text
- `maath` (0.10.8) - Math utilities for Three.js

#### Animation
- `framer-motion` (12.30.0) - Production-grade animations
- `react-spring` (10.0.3) - Physics-based animations
- `leva` (0.10.1) - Real-time 3D controls

#### Image Processing
- `sharp` (0.34.5) - High-performance image processing
- `pica` (9.0.1) - High-quality resizing
- `blurhash` (2.0.5) + `react-blurhash` (0.3.0) - Image placeholders
- `canvas` (3.2.1) - Server-side canvas
- `@vercel/og` (0.8.6) - Dynamic OG images

#### Design System
- `@vanilla-extract/css` (1.18.0) - Type-safe CSS

### Python (15 packages)

#### AI Image Generation & Enhancement
- `fal-client` (0.13.0) - Fast inference (FLUX, SD3)
- `stability-sdk` (0.8.6) - Stable Diffusion 3.5
- `together` (0.2.11) - Together AI SDK
- `rembg` (2.0.72) - Background removal
- `clip-interrogator` (0.6.0) - Prompt extraction

#### Video & Animation
- `imageio` (2.37.2) - Video/GIF generation
- `imageio-ffmpeg` (0.6.0) - Video encoding
- `runwayml` (4.4.0) - RunwayML Gen-3

#### Image Processing
- `Pillow` (12.1.0) - Latest PIL
- `scikit-image` (0.26.0) - Advanced processing
- `timm` (1.0.24) - Vision models

---

## 🚀 Quick Start Guide

### 1. Luxury 3D Product Viewer

```tsx
import LuxuryProductViewer from '@/components/3d/LuxuryProductViewer';

export default function ProductPage() {
  return (
    <LuxuryProductViewer
      modelUrl="/models/black-rose-jacket.glb"
      productName="Midnight Rose Jacket"
      environment="studio"
      enableAR={true}
      autoRotate={true}
      showEffects={true}
    />
  );
}
```

**Features:**
- ✨ Advanced lighting with luxury environment
- 🌹 Rose gold tinted shadows
- 💎 Bloom and tone mapping effects
- 🔄 Auto-rotate presentation
- 📱 AR support ready
- 🎭 Framer Motion animations

### 2. AI Image Enhancement API

```typescript
import { luxuryImageProcessor } from '@/api/image-processing/luxury-enhance';

// Enhance product image
const enhanced = await luxuryImageProcessor.enhanceProductImage(
  imageBuffer,
  {
    removeBackground: true,
    upscale: true,
    applyLuxuryFilter: true,
    targetWidth: 2048,
    quality: 95,
    format: 'webp',
  }
);

// Generate responsive image set
const responsiveSet = await luxuryImageProcessor.generateResponsiveSet(
  imageBuffer,
  [320, 640, 960, 1280, 1920]
);

// Generate blurhash placeholder
const blurhash = await luxuryImageProcessor.generateBlurhash(imageBuffer);

// Generate OG image
const ogImage = await luxuryImageProcessor.generateOGImage({
  productName: 'Midnight Rose Jacket',
  collectionName: 'Black Rose Collection',
  price: '$2,499',
  imageBuffer,
});
```

### 3. Luxury Animations

```tsx
import { motion } from 'framer-motion';
import {
  productCard,
  staggerContainer,
  luxuryButton,
} from '@/lib/animations/luxury-transitions';

export default function ProductGrid({ products }) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="grid grid-cols-3 gap-8"
    >
      {products.map((product) => (
        <motion.div
          key={product.id}
          variants={productCard}
          whileHover="hover"
          whileTap="tap"
        >
          <img src={product.image} alt={product.name} />
          <motion.button variants={luxuryButton}>
            View Details
          </motion.button>
        </motion.div>
      ))}
    </motion.div>
  );
}
```

### 4. Python AI Image Enhancement

```python
from services.ai_image_enhancement import LuxuryImageEnhancer

enhancer = LuxuryImageEnhancer(
    replicate_api_key="your-key",
    fal_api_key="your-key",
    together_api_key="your-key",
)

# Remove background
img = await enhancer.remove_background("product.jpg", "output.png")

# Upscale 4x
url = await enhancer.upscale_image("product.jpg", scale=4)

# Generate new product image
generated = await enhancer.generate_product_image(
    "black rose leather jacket with metallic details",
    model="flux",
)

# Extract prompt from image
analysis = await enhancer.interrogate_image("product.jpg")
print(analysis["best_prompt"])

# Apply luxury filter
await enhancer.apply_luxury_filter("input.jpg", "output.jpg")

# Batch process
results = await enhancer.batch_process_products(
    input_dir="./raw_photos",
    output_dir="./processed",
    remove_bg=True,
    upscale=True,
    apply_filter=True,
)
```

---

## 📚 Full Example: Luxury Product Showcase

See `examples/luxury-product-showcase.tsx` for a complete implementation featuring:
- Hero section with animated gradients
- Product grid with stagger animations
- Blurhash placeholders
- 3D viewer modal
- Framer Motion throughout
- Responsive design
- Production-ready patterns

---

## 🎨 Available Animations

### Page Transitions
- `pageTransition` - Smooth page enter/exit
- `fadeInDirection` - Fade from any direction
- `scrollFadeIn` - Scroll-triggered fade in

### Product Animations
- `productReveal` - 3D reveal with rotation
- `productCard` - Card with hover effects
- `staggerContainer` - Staggered children

### Interactive Elements
- `luxuryButton` - Button with hover/tap states
- `magneticHover` - Magnetic hover effect
- `cardTilt` - 3D card tilt on mouse move

### Text Animations
- `textReveal` - Word-by-word reveal
- `heroTitle` - Large title entrance
- `heroSubtitle` - Subtitle with delay

### Modals & Overlays
- `modalOverlay` - Backdrop with blur
- `modalContent` - Modal content animation
- `navMenu` - Navigation menu with stagger

---

## 🌹 SkyyRose Color Grading

The luxury filter applies:
- **Rose gold tint**: #B76E79 (RGB: 183, 110, 121)
- **Warmth boost**: +10% red, +5% green
- **Saturation increase**: +20%
- **Contrast enhancement**: Gamma 1.2
- **Slight sharpening**: Sigma 1

---

## 🎭 Environment Presets

Available 3D environments:
- `studio` - Clean studio lighting (default)
- `sunset` - Warm golden hour
- `dawn` - Soft morning light
- `night` - Dramatic low light
- `warehouse` - Industrial aesthetic
- `forest` - Natural outdoor
- `apartment` - Interior lighting
- `city` - Urban environment
- `park` - Outdoor daylight
- `lobby` - Luxury hotel lobby

---

## 🚀 Performance Tips

### 3D Optimization
1. **Preload models**: Use `preloadModel(url)` before rendering
2. **Lazy load**: Wrap viewer in `Suspense`
3. **Reduce shadows**: Set `frames={60}` for faster accumulation
4. **Disable effects**: Set `showEffects={false}` on mobile

### Image Processing
1. **Use WebP**: Best quality/size ratio
2. **Generate responsive sets**: Better UX across devices
3. **Implement blurhash**: Instant placeholders
4. **Batch process**: More efficient than one-by-one

### Animations
1. **Use `layoutId`**: For shared element transitions
2. **Prefer `whileInView`**: Better than scroll listeners
3. **Set `once: true`**: Animations trigger once
4. **Use spring physics**: More natural than easing

---

## 📦 API Keys Required

Set these environment variables:

```bash
# Image Generation
REPLICATE_API_TOKEN=r8_...
FAL_KEY=...
STABILITY_API_KEY=sk-...
TOGETHER_API_KEY=...

# Video Generation
RUNWAY_API_KEY=...

# Optional
TRIPO_API_KEY=...
FASHN_API_KEY=...
```

---

## 🔗 Resources

- [React Three Fiber Docs](https://docs.pmnd.rs/react-three-fiber)
- [Drei Components](https://github.com/pmndrs/drei)
- [Framer Motion Docs](https://www.framer.com/motion/)
- [Sharp Documentation](https://sharp.pixelplumbing.com/)
- [FAL AI Platform](https://fal.ai/)
- [Replicate Models](https://replicate.com/)
- [Stability AI](https://stability.ai/)

---

## 💎 Next Steps

1. **Create Product Models**: Export GLB files from Blender/Cinema4D
2. **Process Images**: Batch process with Python enhancement
3. **Build Pages**: Use components and animations
4. **Deploy**: Vercel handles everything
5. **Test AR**: Use model-viewer for AR experiences

---

**Built with love for SkyyRose 🌹**
