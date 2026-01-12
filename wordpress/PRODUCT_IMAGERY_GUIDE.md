# Product Imagery Guide for WordPress Media Library

> **Complete guide for processing, optimizing, and uploading product images to WordPress**
>
> **Created**: 2026-01-11
> **Target**: SkyyRose WooCommerce store with Shoptimizer theme
> **Image Source**: `/assets/3d-models/` collections

---

## 📸 Image Inventory

### Love Hurts Collection

**Location**: `/Users/coreyfoster/DevSkyy/assets/3d-models/love-hurts/_Love Hurts Collection_/`

**Product Images** (48 files):
- Windbreaker Jackets (Men's & Women's): 5 images
- Windbreaker Shorts (Men's): 3 images
- Fannie Packs: 4 images
- Hoodies (Mint & Lavender): 6 images
- Joggers (Sincerely Hearted - Black & White): 2 images
- Collection Lifestyle/Editorial: 28 images (PhotoRoom series)

### Black Rose Collection

**Location**: `/Users/coreyfoster/DevSkyy/assets/3d-models/black-rose/_BLACK Rose Collection_/`

**Product Images** (17 files):
- Sherpa Jackets: 3 images
- Hooded Dresses (Women's): 3 images
- Editorial/Artistic: 11 images (AI-generated black rose artwork)

### SIGNATURE Collection

**Location**: To be confirmed (not yet found in assets)

---

## 🎨 WordPress/WooCommerce Image Requirements

### Standard Sizes (Shoptimizer Theme)

| Image Type | Dimensions | Purpose | File Size Target |
|-----------|-----------|---------|------------------|
| **Main Product Image** | 1200×1200px | Product page hero | < 150 KB |
| **Gallery Images** | 1200×1200px | Lightbox/zoom | < 150 KB each |
| **Thumbnails** | 300×300px | Product grid, cart | < 30 KB |
| **Medium** | 600×600px | Mobile product page | < 80 KB |
| **Zoom (Optional)** | 2000×2000px | High-res zoom | < 400 KB |

### Aspect Ratio
- **Primary**: 1:1 (Square) - Best for consistency
- **Alternative**: 4:5 (Portrait) - Fashion products
- **Avoid**: Landscape orientations for products

### File Formats
- **WebP** (First choice): Modern, 30% smaller than JPEG, lossless quality
- **JPEG** (Fallback): Universal compatibility, quality 85-90%
- **PNG** (Transparent backgrounds only): Logos, graphics with transparency

---

## 🛠️ Image Processing Workflow

### Step 1: Organize by Product

Create product folders matching WooCommerce structure:

```
wordpress/product-images/
├── love-hurts/
│   ├── windbreaker-jacket-mens-black/
│   │   ├── main.webp (1200×1200)
│   │   ├── front.webp
│   │   ├── back.webp
│   │   ├── detail.webp
│   │   └── lifestyle.webp
│   ├── windbreaker-jacket-womens-pink/
│   ├── fannie-pack-love-hurts/
│   └── ... (continue for each product)
├── black-rose/
│   ├── sherpa-jacket-black-rose/
│   ├── hooded-dress-black-rose/
│   └── ... (continue for each product)
└── signature/
    └── ... (to be added)
```

### Step 2: Crop to Square (1:1 Aspect Ratio)

**Method A: macOS Preview (Quick)**
```bash
# Open image
open -a Preview "IMG_0114.jpeg"

# 1. Tools → Adjust Size
# 2. Check "Scale proportionally"
# 3. Set width: 1200px
# 4. File → Export → Format: JPEG, Quality: 85%
```

**Method B: ImageMagick (Batch Processing)**
```bash
# Install (if not already)
brew install imagemagick

# Crop to center square
for img in *.{jpg,jpeg,png}; do
  convert "$img" -resize "1200x1200^" -gravity center -extent 1200x1200 "processed_${img}"
done
```

**Method C: Photoshop/GIMP (Professional)**
```
1. Image → Canvas Size → Width: 1200px, Height: 1200px (Center anchor)
2. Image → Image Size → Constrain proportions: ON, Width: 1200px
3. File → Export As → WebP (Quality: 90%)
```

### Step 3: Convert to WebP

**Using cwebp (Google's official tool)**:
```bash
# Install
brew install webp

# Convert single image (lossless quality 90)
cwebp -q 90 input.jpg -o output.webp

# Batch convert all JPEGs in directory
for file in *.jpg; do
  cwebp -q 90 "$file" -o "${file%.jpg}.webp"
done
```

**Using Squoosh (Web-based, visual)**:
1. Go to [https://squoosh.app/](https://squoosh.app/)
2. Upload image
3. Select WebP format (right panel)
4. Adjust quality slider (90 for products)
5. Download

### Step 4: Generate Thumbnails

**WordPress Auto-Generates** (on upload), but to preview locally:

```bash
# 300×300 thumbnails
for img in *.webp; do
  convert "$img" -resize 300x300 "thumb_${img}"
done

# 600×600 mobile
for img in *.webp; do
  convert "$img" -resize 600x600 "mobile_${img}"
done
```

---

## 📦 WordPress Media Library Upload

### Option 1: WordPress Admin Dashboard (Manual)

**For Small Batches (< 20 images)**:

1. **Navigate**: WordPress Admin → Media → Add New
2. **Drag & Drop**: Select all processed .webp files for one product
3. **Edit Details** (for each image):
   - Title: "Love Hurts Windbreaker Jacket - Front View"
   - Alt Text: "Black windbreaker jacket with Love Hurts logo embroidered on chest"
   - Caption: "Front view of Love Hurts Collection windbreaker"
   - Description: "Premium lightweight windbreaker with custom Love Hurts branding, water-resistant fabric, and adjustable hood."

4. **Assign to Product**:
   - Go to Products → Edit Product
   - Product Gallery → Add Images
   - Select uploaded images
   - Drag to reorder (main image first)

### Option 2: WP-CLI (Command Line - Fast)

**For Large Batches (50+ images)**:

```bash
# Install WP-CLI (if not already)
brew install wp-cli

# Navigate to WordPress root
cd /Users/coreyfoster/DevSkyy/wordpress

# Upload images to Media Library
wp media import /path/to/images/*.webp --post_id=123 --title="Love Hurts Windbreaker" --alt="Windbreaker jacket front view" --porcelain

# Example: Upload all Love Hurts images
wp media import /Users/coreyfoster/DevSkyy/wordpress/product-images/love-hurts/**/*.webp
```

### Option 3: FTP + Media Library Sync

**For Very Large Batches (100+ images)**:

1. **Upload via FTP** to `/wp-content/uploads/product-images/`
2. **Install Plugin**: [Add From Server](https://wordpress.org/plugins/add-from-server/)
3. **Scan & Import**: Plugin will detect uploaded files and add to Media Library
4. **Assign Metadata**: Bulk edit using [Media Library Assistant](https://wordpress.org/plugins/media-library-assistant/)

---

## 🎯 Product Image Strategy (Per Product)

### Minimum Required (3-5 images):
1. **Main Hero** - Product on white/neutral background, center-aligned
2. **Front View** - Clean, well-lit, shows logo/branding
3. **Back View** - Shows rear design details
4. **Detail Shot** - Close-up of unique feature (embroidery, texture, hardware)
5. **Lifestyle/Model** - Product worn by model or styled in context

### Premium Experience (7-10 images):
6. **Side View** - Lateral angle
7. **Flat Lay** - Product laid flat showing proportions
8. **Texture Close-Up** - Fabric weave, zipper quality
9. **Packaging** - Unboxing experience (optional)
10. **Comparison** - Size comparison or color variants side-by-side

---

## 📝 Image Naming Convention

**Format**: `{collection}-{product-name}-{view-type}.webp`

**Examples**:
```
love-hurts-windbreaker-jacket-mens-black-main.webp
love-hurts-windbreaker-jacket-mens-black-front.webp
love-hurts-windbreaker-jacket-mens-black-back.webp
love-hurts-windbreaker-jacket-mens-black-detail-logo.webp
love-hurts-windbreaker-jacket-mens-black-lifestyle-model.webp

black-rose-sherpa-jacket-main.webp
black-rose-sherpa-jacket-front.webp
black-rose-sherpa-jacket-texture.webp
```

**Benefits**:
- SEO-friendly URLs
- Easy to find in Media Library search
- Logical sorting (alphabetical by product)

---

## 🔍 SEO & Accessibility Best Practices

### Alt Text (For Screen Readers & SEO)

**Formula**: `[Product Name] - [Color/Variant] - [View Type]`

**Good Examples**:
```html
<img alt="Love Hurts windbreaker jacket in black with embroidered logo - front view">
<img alt="Black Rose sherpa jacket with full-zip closure and hood - lifestyle photo">
<img alt="Fannie pack from Love Hurts collection showing main compartment and strap">
```

**Bad Examples** (Avoid):
```html
<img alt="IMG_0114"> <!-- No context -->
<img alt="Jacket"> <!-- Too generic -->
<img alt="Buy now Love Hurts jacket sale discount cheap best price"> <!-- Keyword stuffing -->
```

### File Names (For SEO)

**Google ranks images based on filename**, so use descriptive names:

✅ **Good**: `love-hurts-windbreaker-jacket-mens-black-front-view.webp`
❌ **Bad**: `IMG_0114.jpeg`, `photo1.jpg`, `image-final-v2.png`

### Image Captions

**Optional but recommended** for editorial context:

```
"The Love Hurts windbreaker features water-resistant fabric and custom embroidery,
perfect for layering on chilly evenings. Available in black, pink, and navy."
```

---

## 🚀 Automation Script (Python)

**For bulk processing 100+ images**:

```python
#!/usr/bin/env python3
"""
Product Image Processor for SkyyRose WordPress
Resizes, converts to WebP, and organizes images
"""

import os
from PIL import Image
from pathlib import Path

# Configuration
SOURCE_DIR = "/Users/coreyfoster/DevSkyy/assets/3d-models"
OUTPUT_DIR = "/Users/coreyfoster/DevSkyy/wordpress/product-images"
SIZES = {
    'main': (1200, 1200),
    'thumb': (300, 300),
    'mobile': (600, 600),
}

def process_image(input_path, product_name, view_type='main'):
    """Resize, crop to square, convert to WebP"""
    img = Image.open(input_path)

    # Convert to RGB (remove alpha channel if present)
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background

    # Crop to center square
    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim) / 2
    top = (height - min_dim) / 2
    right = (width + min_dim) / 2
    bottom = (height + min_dim) / 2
    img = img.crop((left, top, right, bottom))

    # Resize to target dimensions
    for size_name, dimensions in SIZES.items():
        resized = img.resize(dimensions, Image.Resampling.LANCZOS)

        # Save as WebP
        output_path = Path(OUTPUT_DIR) / product_name / f"{product_name}-{view_type}-{size_name}.webp"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        resized.save(output_path, 'WEBP', quality=90, method=6)

        print(f"✓ Created: {output_path}")

def main():
    """Process all product images"""
    collections = {
        'love-hurts': '_Love Hurts Collection_',
        'black-rose': '_BLACK Rose Collection_',
    }

    for collection, folder_name in collections.items():
        source_path = Path(SOURCE_DIR) / folder_name

        if not source_path.exists():
            print(f"⚠ Skipping {collection}: Folder not found")
            continue

        print(f"\nProcessing {collection.upper()} collection...")

        for image_file in source_path.glob('*.{jpg,jpeg,png,JPG,JPEG,PNG}'):
            # Infer product name from filename
            product_name = image_file.stem.lower().replace(' ', '-')
            product_name = f"{collection}-{product_name}"

            # Determine view type
            if 'front' in product_name.lower():
                view_type = 'front'
            elif 'back' in product_name.lower():
                view_type = 'back'
            elif 'lifestyle' in product_name.lower() or 'photoroom' in product_name.lower():
                view_type = 'lifestyle'
            else:
                view_type = 'main'

            process_image(image_file, product_name, view_type)

    print("\n✅ All images processed successfully!")

if __name__ == '__main__':
    main()
```

**Run Script**:
```bash
cd /Users/coreyfoster/DevSkyy/wordpress
python3 PRODUCT_IMAGERY_PROCESSOR.py
```

---

## ✅ Quality Checklist

Before uploading to WordPress, verify:

- [ ] All images are 1200×1200px (main) and square aspect ratio
- [ ] WebP format with quality ≥ 85%
- [ ] File size < 150 KB per image
- [ ] Filenames follow naming convention (lowercase, hyphens, descriptive)
- [ ] White/neutral backgrounds for main product shots
- [ ] Consistent lighting across product images
- [ ] No watermarks or copyright notices from PhotoRoom
- [ ] Images show product clearly (not blurry, good focus)
- [ ] Alt text prepared for each image (descriptive, under 125 characters)

---

## 📊 WordPress Product Setup

### Assigning Images to Products

1. **Create Product** (if not exists):
   - Products → Add New
   - Title: "Love Hurts Windbreaker Jacket - Men's Black"
   - Regular Price: $79.99
   - SKU: LH-WJ-MB-001
   - Categories: Love Hurts, Jackets, Men's

2. **Product Image** (Hero):
   - Set as "Product image" (first image in gallery)
   - This appears on product grid and as main image

3. **Product Gallery**:
   - Add remaining 4-9 images
   - Drag to reorder (WordPress uses order for lightbox slideshow)

4. **Short Description** (Excerpt):
   ```
   Premium lightweight windbreaker with custom Love Hurts embroidery.
   Water-resistant fabric, adjustable hood, and zippered pockets.
   Perfect for layering on cool days.
   ```

5. **Product Tags**:
   - love-hurts, windbreaker, outerwear, water-resistant, embroidered

---

## 🎨 Current Image Status

### Love Hurts Collection (48 Images)

**Products Identified**:
1. **Windbreaker Jacket - Men's** (5 images)
2. **Windbreaker Jacket - Women's** (3 images)
3. **Windbreaker Shorts - Men's** (2 images)
4. **Fannie Pack** (4 images)
5. **Hoodie - Mint & Lavender** (6 images)
6. **Joggers - Sincerely Hearted Black** (2 images)
7. **Joggers - Sincerely Hearted White** (2 images)
8. **Editorial/Lifestyle** (24 images from PhotoRoom series)

**Action Required**:
- Remove PhotoRoom watermarks (if present)
- Crop lifestyle images to square
- Create white-background versions for main product shots

### Black Rose Collection (17 Images)

**Products Identified**:
1. **Sherpa Jacket** (3 images)
2. **Hooded Dress - Women's** (2 images)
3. **AI-Generated Artwork** (12 images - for hero banners, not product gallery)

**Action Required**:
- Separate product photos from editorial artwork
- Need more product angles (currently only front views)
- Consider professional photoshoot for missing angles

---

## 📅 Implementation Timeline

### Phase 1: Preparation (1-2 hours)
- [x] Inventory all product images
- [ ] Create organized folder structure
- [ ] Install ImageMagick or Photoshop

### Phase 2: Processing (3-4 hours)
- [ ] Crop all images to square (1200×1200)
- [ ] Convert to WebP format
- [ ] Generate thumbnails
- [ ] Rename files following naming convention

### Phase 3: WordPress Upload (2-3 hours)
- [ ] Upload images via WordPress Media Library
- [ ] Assign alt text and captions
- [ ] Create WooCommerce products (if not exists)
- [ ] Assign images to products

### Phase 4: Quality Control (1 hour)
- [ ] Verify image display on product pages
- [ ] Test lightbox/zoom functionality
- [ ] Check mobile responsiveness
- [ ] Run Lighthouse audit (image optimization score)

**Total Estimated Time**: 7-10 hours

---

## 🔗 Tools & Resources

### Image Editing
- **Photoshop/GIMP**: Professional editing
- **ImageMagick**: Batch command-line processing
- **Squoosh**: Web-based WebP conversion
- **ImageOptim**: macOS lossless compression

### WordPress Plugins
- **EWWW Image Optimizer**: Auto-convert to WebP, lazy loading
- **Smush**: Image compression and resizing
- **Media Library Assistant**: Bulk metadata editing
- **WooCommerce Product Gallery Slider**: Enhanced product galleries

### Testing
- **Google PageSpeed Insights**: LCP optimization
- **WebPageTest**: Image load time analysis
- **WooCommerce Image Size Guide**: https://woocommerce.com/document/fixing-blurry-product-images/

---

## 💡 Pro Tips

1. **Shoot on White Background**: Easiest to edit, professional look, consistency
2. **Use Natural Light**: Soft, diffused lighting (golden hour or overcast day)
3. **Maintain Consistency**: Same angle, lighting, distance across product line
4. **Include Lifestyle Shots**: 50% product-only, 50% styled/modeled
5. **Show Scale**: Include everyday object for size reference
6. **Video as Cover**: Upload MP4 as first gallery item (Shoptimizer supports video)
7. **360° Rotation**: Use Lazy Susan + tripod for seamless spin videos
8. **Color Accuracy**: Calibrate monitor, shoot RAW format, use color checker

---

**Version**: 1.0.0
**Last Updated**: 2026-01-11
**Next Steps**: Run Python automation script to batch-process all 65+ images
**Contact**: For questions, see main WORDPRESS_ENHANCEMENTS.md documentation
