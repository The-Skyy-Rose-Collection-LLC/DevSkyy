# WordPress Site Builder Guide

Complete guide to building WordPress/Elementor sites with DevSkyy's automated theme builder.

## 🚀 Quick Start

### Option 1: Command Line (Easiest)
```bash
# Interactive builder
./scripts/wordpress/build_site.sh interactive

# Quick build
./scripts/wordpress/build_site.sh quick luxury_fashion "My Brand"

# Deploy to WordPress
./scripts/wordpress/build_site.sh deploy staging/themes/deployed/my-theme
```

### Option 2: Python Script
```bash
# Run the example
python3 examples/build_wordpress_site.py
```

### Option 3: Programmatic (Full Control)
```python
from agent.wordpress.theme_builder import ElementorThemeBuilder

builder = ElementorThemeBuilder(api_key="your-api-key")

theme = await builder.generate_theme(
    brand_info={
        "name": "Your Brand",
        "primary_color": "#1a1a1a",
    },
    theme_type="luxury_fashion",
    pages=["home", "shop", "about", "contact"]
)
```

## 📋 Prerequisites

### 1. Environment Setup
```bash
# Required
export ANTHROPIC_API_KEY="sk-ant-..."

# For deployment
export WP_SITE_URL="https://your-site.com"
export WP_USERNAME="admin"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"
```

### 2. WordPress Application Password
Generate in WordPress admin:
1. Go to **Users** > **Profile**
2. Scroll to **Application Passwords**
3. Enter name: "DevSkyy Builder"
4. Click **Add New Application Password**
5. Copy the generated password
6. Set as `WP_APP_PASSWORD`

### 3. Install Dependencies
```bash
# Fashion-specific dependencies
./scripts/install_fashion_dependencies.sh

# Or manually
pip install anthropic requests paramiko
```

## 🎨 Theme Types

### 1. Luxury Fashion
```python
theme_type = "luxury_fashion"
```
- **Style**: Elegant, sophisticated
- **Layout**: Full-width, spacious
- **Colors**: Black, gold, white
- **Fonts**: Playfair Display, Montserrat
- **Best for**: High-end fashion, jewelry, designer brands

### 2. Streetwear
```python
theme_type = "streetwear"
```
- **Style**: Bold, dynamic
- **Layout**: Grid-based, urban
- **Colors**: Vibrant, contrasting
- **Fonts**: Bebas Neue, Roboto
- **Best for**: Urban fashion, sneakers, street culture

### 3. Minimalist
```python
theme_type = "minimalist"
```
- **Style**: Clean, simple
- **Layout**: Centered, whitespace-focused
- **Colors**: Neutral, monochrome
- **Fonts**: Helvetica, Arial
- **Best for**: Scandinavian fashion, basics, contemporary

### 4. Vintage
```python
theme_type = "vintage"
```
- **Style**: Classic, nostalgic
- **Layout**: Magazine-style
- **Colors**: Warm, muted
- **Fonts**: Garamond, Georgia
- **Best for**: Vintage clothing, retro fashion, thrift

### 5. Sustainable
```python
theme_type = "sustainable"
```
- **Style**: Organic, earthy
- **Layout**: Storytelling-focused
- **Colors**: Natural, earth tones
- **Fonts**: Open Sans, Lora
- **Best for**: Eco-fashion, organic materials, ethical brands

## 🛠️ Advanced Features

### AI-Powered Customization
```python
# Optimize color palette
optimized_colors = await builder.optimize_color_palette(
    theme=theme,
    target_audience="luxury fashion consumers",
    conversion_goal="increase add-to-cart rate"
)

# Optimize typography
optimized_fonts = await builder.optimize_typography(
    theme=theme,
    readability_score_target=85,
    brand_personality="elegant and sophisticated"
)

# Generate SEO metadata
seo_data = await builder.generate_seo_metadata(
    theme=theme,
    target_keywords=["luxury fashion", "designer clothing"]
)
```

### WooCommerce Integration
```python
theme = await builder.generate_theme(
    brand_info=brand_info,
    theme_type="luxury_fashion",
    include_woocommerce=True,  # ← Enable WooCommerce
    woocommerce_features=[
        "product_grid",
        "single_product",
        "cart",
        "checkout",
        "my_account"
    ]
)
```

### Responsive Design
All themes are automatically responsive:
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Elementor Pro Features
Includes premium Elementor Pro widgets:
- Posts Widget (blog, portfolio)
- Form Builder (contact, newsletter)
- Slides (carousel, galleries)
- Price Tables (pricing, comparisons)
- Countdown Timers (sales, launches)
- WooCommerce Builder (custom product pages)
- Popup Builder (promotions, email capture)

## 🚢 Deployment Methods

### Method 1: WordPress REST API (Recommended)
```python
from agent.wordpress.automated_theme_uploader import (
    AutomatedThemeUploader,
    WordPressCredentials,
    UploadMethod
)

credentials = WordPressCredentials(
    site_url="https://your-site.com",
    username="admin",
    application_password="xxxx xxxx xxxx xxxx"
)

uploader = AutomatedThemeUploader()
result = await uploader.deploy_theme(
    theme_path="path/to/theme.zip",
    credentials=credentials,
    upload_method=UploadMethod.WORDPRESS_REST_API,
    activate_after_upload=False,  # Manual activation recommended
    backup_existing=True  # Backup current theme
)
```

### Method 2: FTP Upload
```python
credentials = WordPressCredentials(
    site_url="https://your-site.com",
    ftp_host="ftp.your-site.com",
    ftp_username="username",
    ftp_password="password"
)

result = await uploader.deploy_theme(
    theme_path="path/to/theme.zip",
    credentials=credentials,
    upload_method=UploadMethod.FTP
)
```

### Method 3: SFTP Upload (Most Secure)
```python
credentials = WordPressCredentials(
    site_url="https://your-site.com",
    sftp_host="sftp.your-site.com",
    sftp_username="username",
    sftp_private_key="/path/to/private_key"
)

result = await uploader.deploy_theme(
    theme_path="path/to/theme.zip",
    credentials=credentials,
    upload_method=UploadMethod.SFTP
)
```

### Method 4: Manual Upload
1. Generate theme: `./scripts/wordpress/build_site.sh quick`
2. Find theme: `staging/themes/deployed/your-theme.zip`
3. WordPress admin: **Appearance** > **Themes** > **Add New** > **Upload Theme**
4. Choose file and upload
5. Activate theme

## 📦 Theme Export Formats

### Elementor JSON (Recommended)
```python
export_result = await builder.export_theme(
    theme=theme,
    format="elementor_json",
    output_dir="staging/themes/deployed"
)
```
- Full Elementor compatibility
- Easy import/export
- Version controlled

### WordPress Theme ZIP
```python
export_result = await builder.export_theme(
    theme=theme,
    format="wordpress_theme",
    output_dir="staging/themes/deployed"
)
```
- Standard WordPress theme structure
- Ready for WordPress.org submission
- Includes `style.css`, `functions.php`, etc.

### Template Kit
```python
export_result = await builder.export_theme(
    theme=theme,
    format="template_kit",
    output_dir="staging/themes/deployed"
)
```
- Elementor Template Kit format
- Shareable with team
- Reusable across projects

## 🧪 Testing Workflow

### 1. Local Development
```bash
# Build theme locally
./scripts/wordpress/build_site.sh quick luxury_fashion

# Test with Local WP or XAMPP
# Import theme manually to test
```

### 2. Staging Environment
```bash
# Deploy to staging first
export WP_SITE_URL="https://staging.your-site.com"
export WP_APP_PASSWORD="staging-password"

./scripts/wordpress/build_site.sh deploy staging/themes/deployed/my-theme.zip
```

### 3. Production Deployment
```bash
# After testing on staging
export WP_SITE_URL="https://your-site.com"
export WP_APP_PASSWORD="production-password"

./scripts/wordpress/build_site.sh deploy staging/themes/deployed/my-theme.zip
```

## 🔧 Troubleshooting

### Issue: "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Add to ~/.bashrc or ~/.zshrc for persistence
```

### Issue: "WordPress REST API disabled"
Enable in WordPress:
1. **Settings** > **Permalinks**
2. Choose any option except "Plain"
3. Save changes

### Issue: "Upload failed - File too large"
Increase PHP limits in `php.ini`:
```ini
upload_max_filesize = 128M
post_max_size = 128M
max_execution_time = 300
```

### Issue: "Theme not activating"
Check WordPress error log:
```bash
tail -f /var/log/wordpress/debug.log
```

Common causes:
- Missing required plugins (Elementor, WooCommerce)
- PHP version < 7.4
- Insufficient file permissions

## 📚 Examples

### Example 1: Complete E-commerce Site
```python
builder = ElementorThemeBuilder(api_key=api_key)

theme = await builder.generate_theme(
    brand_info={
        "name": "Fashion Boutique",
        "primary_color": "#000000",
        "secondary_color": "#ffffff",
    },
    theme_type="luxury_fashion",
    pages=["home", "shop", "product", "cart", "checkout", "about", "contact"],
    include_woocommerce=True,
    include_seo=True,
    responsive=True
)
```

### Example 2: Blog + Shop
```python
theme = await builder.generate_theme(
    brand_info=brand_info,
    theme_type="minimalist",
    pages=["home", "blog", "shop", "about"],
    include_woocommerce=True,
    blog_layout="magazine"
)
```

### Example 3: Landing Page
```python
theme = await builder.generate_theme(
    brand_info=brand_info,
    theme_type="streetwear",
    pages=["landing"],
    include_woocommerce=False,
    conversion_optimized=True
)
```

## 🎯 Best Practices

1. **Always test on staging first** - Never deploy directly to production
2. **Backup before deploying** - Enable `backup_existing=True`
3. **Use application passwords** - More secure than regular passwords
4. **Version control themes** - Keep theme exports in git
5. **Optimize images** - Compress before uploading
6. **Test mobile responsiveness** - Check on real devices
7. **SEO optimization** - Generate metadata for all pages
8. **Performance testing** - Use Google PageSpeed Insights

## 📞 Support

- **Documentation**: [README.md](README.md)
- **Examples**: [examples/build_wordpress_site.py](examples/build_wordpress_site.py)
- **Issues**: GitHub Issues
- **CLAUDE.md**: Enterprise guidelines and Truth Protocol

## 🔗 Related Resources

- [Elementor Documentation](https://elementor.com/help/)
- [WooCommerce Docs](https://woocommerce.com/documentation/)
- [WordPress REST API](https://developer.wordpress.org/rest-api/)
- [WordPress Theme Development](https://developer.wordpress.org/themes/)

---

**Built with DevSkyy Platform** | Enterprise AI-Powered Fashion E-commerce
