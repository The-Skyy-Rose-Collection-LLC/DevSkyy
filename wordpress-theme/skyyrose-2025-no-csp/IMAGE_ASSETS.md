# SkyyRose 2025 Image Assets Guide

## Overview
This document outlines all required images for the SkyyRose WordPress theme and provides sourcing strategies for production deployment.

---

## 🎨 Image Requirements Summary

### Total Images Needed:
- **Collection Hero Banners**: 3 images (1920x1080px each)
- **Product Photography**: 30 products × 4-6 images each = 120-180 images (800x800px)
- **Collection Logos**: 3 logos (transparent PNG, 500x500px)
- **Brand Assets**: 1 site logo (transparent PNG)

---

## 📸 Sourcing Strategies

### Option 1: AI Image Generation (RECOMMENDED)

Use **Midjourney** or **DALL-E 3** for high-quality, royalty-free product photography.

#### Midjourney Prompts:

**Black Rose Collection:**
```
luxury gothic streetwear [ITEM TYPE], dramatic studio lighting, dark crimson and black color palette, professional product photography, high fashion editorial, moody atmosphere, 4k, ultra detailed --ar 1:1 --v 6
```

Examples:
- `luxury gothic streetwear hoodie, dramatic studio lighting, dark crimson and black...`
- `luxury gothic streetwear leather jacket, dramatic studio lighting...`
- `luxury gothic streetwear combat boots on dark background...`

**Love Hurts Collection:**
```
romantic luxury streetwear [ITEM TYPE], soft pink rose gold lighting, dreamy atmosphere, professional product photography, emotional aesthetic, delicate details, 4k, ultra detailed --ar 1:1 --v 6
```

Examples:
- `romantic luxury streetwear dress, soft pink rose gold lighting...`
- `romantic luxury streetwear platform boots, dreamy atmosphere...`

**Signature Collection:**
```
minimalist luxury fashion [ITEM TYPE], clean white background, gold accents, high-end editorial photography, architectural lighting, premium quality, 4k, ultra detailed --ar 1:1 --v 6
```

Examples:
- `minimalist luxury fashion blazer, clean white background, gold accents...`
- `minimalist luxury fashion trench coat, high-end editorial photography...`

#### Collection Hero Banners:
```
luxury streetwear brand [COLLECTION NAME] aesthetic, cinematic lighting, atmospheric, no people, product styling, high fashion editorial, dramatic mood, 4k --ar 16:9 --v 6
```

### Option 2: Stock Photography (FREE)

Use these royalty-free platforms:

#### Unsplash
- **URL**: https://unsplash.com/
- **Search Terms**:
  - "luxury streetwear"
  - "gothic fashion"
  - "minimal fashion"
  - "designer clothing"
  - "high fashion editorial"
- **License**: Free for commercial use

#### Pexels
- **URL**: https://www.pexels.com/
- **Search Terms**:
  - "black clothing studio"
  - "luxury fashion"
  - "streetwear photography"
  - "designer clothes"
- **License**: Free for commercial use

#### Pixabay
- **URL**: https://pixabay.com/
- **Search Terms**: Similar to above
- **License**: Free for commercial use

### Option 3: CSS Gradients (FALLBACK)

The theme already includes CSS gradient backgrounds for collection pages. If images aren't ready, the site will display beautifully with pure CSS:

- **Black Rose**: Dark crimson gradient
- **Love Hurts**: Rose gold gradient
- **Signature**: Gold gradient

---

## 🖼️ Detailed Image Specifications

### 1. Collection Hero Banners (3 images)

| Collection | Dimensions | Aesthetic | Priority |
|------------|-----------|-----------|----------|
| Black Rose | 1920x1080px | Dark, moody, crimson accents | HIGH |
| Love Hurts | 1920x1080px | Soft, pink, romantic | HIGH |
| Signature | 1920x1080px | Clean, minimal, gold accents | HIGH |

**File Format**: JPG or WebP
**Max File Size**: 300KB (optimized)
**Location**: `/wp-content/uploads/2025/01/hero-[collection-name].jpg`

### 2. Product Photography (30 products)

Each product needs **4-6 images**:
1. **Main Image**: Product on white/neutral background (front view)
2. **Detail Shot**: Close-up of fabric/embroidery/hardware
3. **Lifestyle Shot**: Styled or worn (optional but recommended)
4. **Back View**: Full back of product
5. **Additional Angles**: Side views, texture details

**Specifications:**
- **Dimensions**: 800x800px minimum (1200x1200px ideal)
- **Format**: JPG or WebP
- **Background**: White or collection-appropriate gradient
- **Max File Size**: 150KB each (optimized)

**File Naming Convention:**
```
[collection]-[sku]-[number].jpg

Examples:
black-rose-BR-TH-001-1.jpg (main)
black-rose-BR-TH-001-2.jpg (detail)
black-rose-BR-TH-001-3.jpg (lifestyle)
```

### 3. Collection Logos (3 images)

| Logo | Description | Location |
|------|-------------|----------|
| Black Rose | Crimson rose icon on transparent | `/assets/images/BLACK-Rose-LOGO.PNG` |
| Love Hurts | Pink heart icon on transparent | `/assets/images/Love-Hurts-LOGO.PNG` |
| Signature | Gold emblem on transparent | `/assets/images/Signature-LOGO.PNG` |

**Specifications:**
- **Dimensions**: 500x500px
- **Format**: PNG (transparent background)
- **Max File Size**: 50KB

### 4. Site Logo

**SkyyRose Main Logo**
- **Dimensions**: 300x100px (horizontal) or 200x200px (square)
- **Format**: PNG or SVG (transparent)
- **Location**: Upload via WordPress Customizer
- **Colors**: White for dark backgrounds

---

## 📦 Directory Structure

```
wp-content/uploads/2025/01/
├── hero-black-rose.jpg
├── hero-love-hurts.jpg
├── hero-signature.jpg
├── products/
│   ├── black-rose/
│   │   ├── BR-TH-001-1.jpg
│   │   ├── BR-TH-001-2.jpg
│   │   └── ...
│   ├── love-hurts/
│   │   ├── LH-RH-001-1.jpg
│   │   └── ...
│   └── signature/
│       ├── SG-BL-001-1.jpg
│       └── ...
└── logos/
    ├── BLACK-Rose-LOGO.png
    ├── Love-Hurts-LOGO.png
    └── Signature-LOGO.png
```

---

## 🚀 Quick Start: Generating Images with Midjourney

### Step 1: Set Up Midjourney
1. Join Midjourney Discord: https://discord.gg/midjourney
2. Subscribe to a plan (Basic: $10/month)
3. Use `/imagine` command in any bot channel

### Step 2: Generate First Batch (30 minutes)
Run these prompts for each product type:

```
/imagine luxury gothic streetwear hoodie, dramatic studio lighting, dark crimson and black color palette, professional product photography, high fashion editorial, moody atmosphere, 4k, ultra detailed --ar 1:1 --v 6

/imagine romantic luxury streetwear dress, soft pink rose gold lighting, dreamy atmosphere, professional product photography, emotional aesthetic, delicate details, 4k, ultra detailed --ar 1:1 --v 6

/imagine minimalist luxury fashion blazer, clean white background, gold accents, high-end editorial photography, architectural lighting, premium quality, 4k, ultra detailed --ar 1:1 --v 6
```

### Step 3: Download & Organize
1. Upscale best results (`U1`, `U2`, `U3`, `U4` buttons)
2. Download high-resolution images
3. Rename according to file naming convention
4. Optimize with [TinyPNG](https://tinypng.com) or [Squoosh](https://squoosh.app)

### Step 4: Upload to WordPress
1. Go to WordPress Media Library
2. Create folders for organization
3. Upload images
4. Assign to products via Product Gallery

---

## 🎨 Alternative: Use Gradient Backgrounds

If you need to launch TONIGHT without images, the theme supports pure CSS gradients:

**Black Rose Collection:**
```css
background: linear-gradient(45deg, #1a0000, #3d0000);
```

**Love Hurts Collection:**
```css
background: linear-gradient(45deg, #2d1a1d, #5c2e36);
```

**Signature Collection:**
```css
background: linear-gradient(45deg, #1a1810, #2d2820);
```

These are already built into the collection templates and will display beautifully even without images.

---

## 📊 Image Optimization Checklist

Before uploading to WordPress:

- [ ] Resize to exact dimensions (800x800px for products, 1920x1080px for heroes)
- [ ] Compress with TinyPNG (70-80% quality)
- [ ] Convert to WebP for faster loading (optional)
- [ ] Rename with descriptive, SEO-friendly names
- [ ] Add Alt Text in WordPress for accessibility
- [ ] Test on mobile (images should be responsive)

---

## 🔗 Useful Tools

- **AI Generation**: [Midjourney](https://midjourney.com), [DALL-E 3](https://openai.com/dall-e-3)
- **Stock Photos**: [Unsplash](https://unsplash.com), [Pexels](https://pexels.com)
- **Image Compression**: [TinyPNG](https://tinypng.com), [Squoosh](https://squoosh.app)
- **Background Removal**: [Remove.bg](https://remove.bg)
- **Bulk Resize**: [Bulk Resize Photos](https://bulkresizephotos.com)

---

## 📞 Need Help?

If you need assistance with image generation or sourcing:
- Email: hello@skyyrose.co
- Check Midjourney community for inspiration: https://www.midjourney.com/showcase/

---

**Last Updated**: January 30, 2025
**Version**: 2.0.0
