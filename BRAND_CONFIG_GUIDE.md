# Brand Configuration System

Automated WordPress site builder using pre-defined brand configurations. Just provide your brand assets (colors, logos, images) and let the AI agents build your site automatically!

## 🚀 Quick Start

### 1. Setup Asset Directory
```bash
# Create directory structure
./scripts/wordpress/quick_build.sh setup-assets

# Add your brand assets
cp your-logo.png assets/brand/logo.png
cp your-hero.jpg assets/brand/hero-1.jpg
# ... add more assets
```

### 2. Create Brand Configuration
```bash
# Option A: Interactive creation
./scripts/wordpress/quick_build.sh create

# Option B: Use example template
cp config/brand-config.example.json config/brands/my-brand.json
# Edit config/brands/my-brand.json with your details
```

### 3. Build WordPress Site
```bash
# Build only
./scripts/wordpress/quick_build.sh build config/brands/my-brand.json

# Build and deploy
./scripts/wordpress/quick_build.sh build-deploy config/brands/my-brand.json
```

That's it! Your WordPress site is built and ready to deploy.

## 📋 Brand Configuration Format

### Complete Example
```json
{
  "brand": {
    "name": "Your Brand Name",
    "tagline": "Your Brand Tagline",
    "description": "Description of your brand",
    "industry": "luxury_fashion",
    "target_audience": "affluent consumers aged 25-45"
  },
  "colors": {
    "primary": "#1a1a1a",
    "secondary": "#d4af37",
    "accent": "#ffffff",
    "background": "#f8f8f8",
    "text_primary": "#2c2c2c",
    "text_secondary": "#6c6c6c"
  },
  "typography": {
    "heading_font": "Playfair Display",
    "body_font": "Montserrat",
    "font_weights": {
      "light": 300,
      "regular": 400,
      "medium": 500,
      "bold": 700
    }
  },
  "assets": {
    "logo": "assets/brand/logo.png",
    "logo_white": "assets/brand/logo-white.png",
    "favicon": "assets/brand/favicon.ico",
    "hero_images": [
      "assets/brand/hero-1.jpg",
      "assets/brand/hero-2.jpg"
    ],
    "about_image": "assets/brand/about.jpg",
    "product_placeholder": "assets/brand/product.jpg"
  },
  "theme": {
    "type": "luxury_fashion",
    "layout_style": "full-width",
    "animation_style": "subtle",
    "header_style": "transparent",
    "footer_style": "dark"
  },
  "pages": [
    "home",
    "shop",
    "product",
    "about",
    "contact",
    "blog"
  ],
  "features": {
    "woocommerce": true,
    "blog": true,
    "newsletter": true,
    "instagram_feed": true,
    "live_chat": false
  },
  "seo": {
    "site_title": "Your Brand | Tagline",
    "meta_description": "Your brand description for search engines",
    "keywords": [
      "keyword1",
      "keyword2"
    ],
    "social_media": {
      "facebook": "https://facebook.com/yourbrand",
      "instagram": "https://instagram.com/yourbrand"
    }
  },
  "contact": {
    "email": "info@yourbrand.com",
    "phone": "+1 (555) 123-4567",
    "address": "123 Street, City, State 12345"
  },
  "deployment": {
    "wordpress_url": "https://your-site.com",
    "deploy_method": "wordpress_rest_api",
    "auto_activate": false,
    "backup_before_deploy": true
  }
}
```

## 🎨 Theme Types

| Type | Description | Best For |
|------|-------------|----------|
| `luxury_fashion` | Elegant, sophisticated | High-end fashion, jewelry |
| `streetwear` | Bold, dynamic, urban | Street fashion, sneakers |
| `minimalist` | Clean, simple | Contemporary, basics |
| `vintage` | Classic, nostalgic | Retro fashion, thrift |
| `sustainable` | Organic, earthy | Eco-fashion, ethical brands |

## 📁 Asset Management

### Directory Structure
```
assets/brand/
├── logo.png              # Main logo (transparent PNG, 500x500px)
├── logo-white.png        # White version for dark backgrounds
├── favicon.ico           # Site favicon (32x32px)
├── hero-1.jpg           # Hero/banner image (1920x1080px)
├── hero-2.jpg           # Alternative hero image
├── hero-3.jpg           # Third hero image
├── about.jpg            # About page image (1200x800px)
└── product-placeholder.jpg  # Default product image
```

### Image Specifications

**Logo:**
- Format: PNG with transparency
- Size: 500x500px (or proportional)
- Max file size: 200KB

**Hero Images:**
- Format: JPG or WebP
- Size: 1920x1080px (16:9 ratio)
- Max file size: 500KB each
- Optimized for web

**Other Images:**
- About page: 1200x800px
- Product images: 800x800px minimum
- Always optimize for web (compress)

### Asset Optimization

```bash
# Install ImageMagick for optimization
sudo apt-get install imagemagick

# Optimize images
mogrify -strip -quality 85 -resize 1920x1080 assets/brand/hero-*.jpg
mogrify -strip -quality 90 -resize 500x500 assets/brand/logo.png
```

## 🎯 Configuration Fields

### Required Fields
- `brand.name` - Your brand name
- `colors.primary` - Primary brand color (hex)
- `theme.type` - Theme type (see above)

### Optional but Recommended
- `colors.secondary` - Secondary color
- `typography.heading_font` - Heading font
- `typography.body_font` - Body text font
- `assets.logo` - Logo path
- `assets.hero_images` - Hero image paths
- `pages` - List of pages to create
- `seo.site_title` - SEO title
- `seo.meta_description` - SEO description

### Color Palette Guidelines

**Luxury Fashion:**
- Primary: Dark/Black (#1a1a1a, #000000)
- Secondary: Gold/Metallic (#d4af37, #c0a080)
- Accent: White/Cream (#ffffff, #f8f8f8)

**Streetwear:**
- Primary: Bold colors (#ff0000, #0000ff)
- Secondary: Black/White (#000000, #ffffff)
- Accent: Neon/Bright (#ffff00, #00ff00)

**Minimalist:**
- Primary: Neutral (#2c2c2c, #666666)
- Secondary: Light gray (#e0e0e0, #f5f5f5)
- Accent: Single accent color

## 🛠️ Advanced Usage

### Command Line Options

```bash
# List all available configurations
./scripts/wordpress/quick_build.sh list

# Create new configuration interactively
./scripts/wordpress/quick_build.sh create

# Build from specific config
./scripts/wordpress/quick_build.sh build config/brands/my-brand.json

# Build and deploy to WordPress
./scripts/wordpress/quick_build.sh build-deploy config/brands/my-brand.json

# Setup asset directory structure
./scripts/wordpress/quick_build.sh setup-assets
```

### Python API

```python
from scripts.auto_build_wp import BrandConfigBuilder

# Build theme
builder = BrandConfigBuilder("config/brands/my-brand.json")
result = await builder.build_theme()

# Deploy
await builder.deploy_theme(result['export_path'])

# Get summary
print(builder.generate_summary(result))
```

### Programmatic Configuration

```python
config = {
    "brand": {
        "name": "My Brand",
        "tagline": "My Tagline"
    },
    "colors": {
        "primary": "#000000",
        "secondary": "#ffffff"
    },
    "theme": {
        "type": "luxury_fashion"
    }
}

# Save config
import json
with open("config/brands/my-brand.json", "w") as f:
    json.dump(config, f, indent=2)

# Build
builder = BrandConfigBuilder("config/brands/my-brand.json")
await builder.build_theme()
```

## 🚢 Deployment

### Method 1: Automatic Deployment (Recommended)
```bash
# Set environment variables
export WP_SITE_URL="https://your-site.com"
export WP_USERNAME="admin"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"

# Build and deploy
./scripts/wordpress/quick_build.sh build-deploy config/brands/my-brand.json
```

### Method 2: Manual Upload
```bash
# Build theme
./scripts/wordpress/quick_build.sh build config/brands/my-brand.json

# Find theme ZIP
ls staging/themes/deployed/

# Upload manually via WordPress admin
# Appearance → Themes → Add New → Upload Theme
```

### Method 3: Staging → Production Workflow
```bash
# Deploy to staging
export WP_SITE_URL="https://staging.your-site.com"
./scripts/wordpress/quick_build.sh build-deploy config/brands/my-brand.json

# Test on staging
# ...

# Deploy to production
export WP_SITE_URL="https://your-site.com"
./scripts/wordpress/quick_build.sh build-deploy config/brands/my-brand.json
```

## 📝 Example Configurations

### Example 1: Luxury Fashion Brand
```bash
cp config/brand-config.example.json config/brands/luxury-brand.json
# Edit: Set luxury_fashion theme, elegant colors, premium fonts
./scripts/wordpress/quick_build.sh build config/brands/luxury-brand.json
```

### Example 2: Streetwear Brand
```bash
cp config/brands/streetwear-example.json config/brands/my-streetwear.json
# Edit: Update brand name, colors, assets
./scripts/wordpress/quick_build.sh build config/brands/my-streetwear.json
```

### Example 3: Minimal Portfolio
```json
{
  "brand": {"name": "Portfolio", "industry": "minimalist"},
  "colors": {"primary": "#2c2c2c", "secondary": "#f5f5f5"},
  "theme": {"type": "minimalist"},
  "pages": ["home", "portfolio", "about", "contact"],
  "features": {"woocommerce": false, "blog": true}
}
```

## 🔧 Troubleshooting

### Issue: "Config file not found"
```bash
# Check file exists
ls -la config/brands/

# Create from template
cp config/brand-config.example.json config/brands/my-brand.json
```

### Issue: "Assets not found"
```bash
# Setup asset directories
./scripts/wordpress/quick_build.sh setup-assets

# Check asset paths in config match actual files
ls -la assets/brand/
```

### Issue: "AI features limited"
```bash
# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Verify
echo $ANTHROPIC_API_KEY
```

### Issue: "Deployment failed"
```bash
# Check WordPress URL
echo $WP_SITE_URL

# Check application password
echo $WP_APP_PASSWORD

# Test WordPress REST API
curl -u "admin:$WP_APP_PASSWORD" "$WP_SITE_URL/wp-json/wp/v2/users/me"
```

## 🎓 Best Practices

1. **Version Control:** Keep brand configs in git
2. **Asset Organization:** Use consistent naming for assets
3. **Color Testing:** Test colors for accessibility (WCAG AA)
4. **Image Optimization:** Always optimize images before use
5. **Staging First:** Test on staging before production
6. **Backup:** Enable `backup_before_deploy: true`
7. **Incremental Updates:** Update configs gradually, test often

## 📚 Related Documentation

- [WORDPRESS_GUIDE.md](WORDPRESS_GUIDE.md) - Complete WordPress building guide
- [README.md](README.md) - Platform overview
- [CLAUDE.md](CLAUDE.md) - Enterprise guidelines

---

**Built with DevSkyy Platform** | Enterprise AI-Powered Fashion E-commerce
