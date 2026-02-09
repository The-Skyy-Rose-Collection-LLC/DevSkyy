# SkyyRose Flagship Theme - Installation & Setup Guide

## Quick Start

### Installation Steps

1. **Upload Theme**
   ```
   Navigate to: WordPress Admin → Appearance → Themes → Add New → Upload Theme
   Select: skyyrose-flagship-theme.zip
   Click: Install Now → Activate
   ```

2. **Initial Setup**
   - Go to Appearance → Customize
   - Set site logo
   - Configure colors
   - Set up menus
   - Configure widget areas

3. **Menu Setup**
   - Navigate to Appearance → Menus
   - Create menus for:
     - Primary Menu (main navigation)
     - Footer Menu (footer links)
     - Mobile Menu (mobile navigation)
     - Top Bar Menu (top bar links)

4. **Widget Setup**
   - Navigate to Appearance → Widgets
   - Drag widgets to:
     - Primary Sidebar
     - Footer Area 1-4
     - Shop Sidebar (if using WooCommerce)

## Feature Activation

### WooCommerce Integration

**Install WooCommerce:**
```
WordPress Admin → Plugins → Add New
Search: "WooCommerce"
Install and Activate
```

**After Activation:**
- WooCommerce templates will automatically load
- Shop sidebar will be available
- Cart and checkout customizations active
- 3D model viewer available for products

**Add 3D Model to Product:**
1. Edit any product
2. Find "3D Model" meta box in sidebar
3. Enter URL to your GLB/GLTF model file
4. Save product
5. "View in 3D" button appears on frontend

### Elementor Pro Integration

**Install Elementor:**
```
WordPress Admin → Plugins → Add New
Search: "Elementor" and "Elementor Pro"
Install and Activate both
```

**After Activation:**
- Custom widget categories available
- 3D Model Viewer widget ready
- Theme locations supported
- Custom templates enabled

**Use 3D Viewer Widget:**
1. Edit page with Elementor
2. Search for "3D Model Viewer"
3. Drag to canvas
4. Configure:
   - Model URL
   - Viewer height
   - Auto-rotate option
   - Background color

### Wishlist System

**Automatically Active:**
- Wishlist custom post type registered
- Wishlist widget available
- AJAX functionality enabled
- Guest and logged-in user support

**Create Wishlist Page:**
1. Pages → Add New
2. Title: "My Wishlist"
3. Template: Wishlist Page Template
4. Publish
5. Add link in menu

## Configuration

### Theme Customizer Options

**Access:** Appearance → Customize

#### Header Settings
```
Path: Customize → Theme Options → Header Settings

Options:
- Header Layout: Default | Centered | Minimal
- Enable Sticky Header: Yes/No
```

#### Footer Settings
```
Path: Customize → Theme Options → Footer Settings

Options:
- Copyright Text: Custom HTML allowed
```

#### Layout Settings
```
Path: Customize → Theme Options → Layout Settings

Options:
- Container Width: 960-1920px (default: 1200px)
- Sidebar Position: Left | Right | None
```

#### Typography
```
Path: Customize → Theme Options → Typography

Options:
- Body Font: System | Roboto | Open Sans | Lato | Montserrat
- Body Font Size: 12-24px (default: 16px)
```

#### Colors
```
Path: Customize → Theme Options → Color Settings

Options:
- Primary Color: Hex color picker
- Secondary Color: Hex color picker
```

### Performance Settings

**Recommended Plugins:**
1. **WP Super Cache** or **W3 Total Cache**
   - Enable page caching
   - Enable browser caching
   - Enable GZIP compression

2. **Autoptimize**
   - Optimize JavaScript
   - Optimize CSS
   - Optimize HTML

3. **EWWW Image Optimizer**
   - Automatically optimize images
   - Enable lazy loading

### Security Settings

**Recommended Plugins:**
1. **Wordfence Security**
   - Enable firewall
   - Enable malware scanner
   - Set up 2FA

2. **iThemes Security**
   - Enable file change detection
   - Enable brute force protection
   - Set strong passwords

## Advanced Configuration

### Child Theme Setup

**Create Child Theme:**

1. Create directory:
   ```
   /wp-content/themes/skyyrose-flagship-child/
   ```

2. Create `style.css`:
   ```css
   /*
   Theme Name: SkyyRose Flagship Child
   Template: skyyrose-flagship-theme
   */
   ```

3. Create `functions.php`:
   ```php
   <?php
   function skyyrose_child_enqueue_styles() {
       wp_enqueue_style( 'parent-style', get_template_directory_uri() . '/style.css' );
   }
   add_action( 'wp_enqueue_scripts', 'skyyrose_child_enqueue_styles' );
   ```

4. Activate child theme

### Custom Code Snippets

**Add Custom Functions:**

Create file: `/wp-content/themes/skyyrose-flagship-child/functions.php`

```php
<?php
// Enqueue parent theme styles
function skyyrose_child_enqueue_styles() {
    wp_enqueue_style( 'parent-style', get_template_directory_uri() . '/style.css' );
}
add_action( 'wp_enqueue_scripts', 'skyyrose_child_enqueue_styles' );

// Add custom functionality below
```

**Override Templates:**

Copy template from parent to child theme:
```
Parent: /skyyrose-flagship-theme/single.php
Child:  /skyyrose-flagship-child/single.php
```

### Database Optimization

**Recommended Settings:**

1. Set up database backups
2. Install WP-Optimize plugin
3. Clean up:
   - Post revisions
   - Auto-drafts
   - Spam comments
   - Transients

## Three.js 3D Models

### Preparing 3D Models

**Recommended Formats:**
- GLB (preferred, binary)
- GLTF (with textures)

**Optimization Tips:**
1. Keep polygon count under 50,000
2. Compress textures (1024x1024 max)
3. Use Draco compression
4. Test in Three.js editor first

**Tools:**
- Blender (free 3D software)
- gltf-transform (compression)
- Three.js Editor (testing)

### Uploading Models

**Method 1: Media Library**
1. Allow GLB/GLTF uploads (add to functions.php):
   ```php
   add_filter('upload_mimes', function($mimes) {
       $mimes['glb'] = 'model/gltf-binary';
       $mimes['gltf'] = 'model/gltf+json';
       return $mimes;
   });
   ```

2. Upload via Media Library
3. Copy file URL
4. Paste in product meta box or Elementor widget

**Method 2: External CDN**
1. Upload to CDN (AWS S3, Cloudflare R2)
2. Get public URL
3. Use URL in theme

## Troubleshooting

### Common Issues

**Issue: Menu not appearing**
- Solution: Go to Appearance → Menus → assign menu to location

**Issue: Widgets not showing**
- Solution: Go to Appearance → Widgets → add widgets to areas

**Issue: 3D model not loading**
- Solution: Check model URL, file format, and CORS headers

**Issue: Wishlist not working**
- Solution: Clear cache, check JavaScript errors in console

**Issue: WooCommerce templates not loading**
- Solution: Go to WooCommerce → Status → Templates → check for updates

**Issue: Elementor widgets missing**
- Solution: Ensure Elementor is activated, clear Elementor cache

### Debug Mode

**Enable WordPress Debug:**

Edit `wp-config.php`:
```php
define( 'WP_DEBUG', true );
define( 'WP_DEBUG_LOG', true );
define( 'WP_DEBUG_DISPLAY', false );
```

**Check Logs:**
```
Location: /wp-content/debug.log
```

### Browser Console

**Check for JavaScript Errors:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Check for errors
4. Report errors with details

## Testing Checklist

### Before Going Live

- [ ] Test on multiple browsers
- [ ] Test on mobile devices
- [ ] Test all page templates
- [ ] Test WooCommerce checkout flow
- [ ] Test wishlist functionality
- [ ] Test 3D model viewer
- [ ] Test Elementor widgets
- [ ] Test contact forms
- [ ] Test navigation menus
- [ ] Check accessibility (WAVE)
- [ ] Check performance (GTmetrix)
- [ ] Check security (Sucuri)
- [ ] Set up backups
- [ ] Set up monitoring
- [ ] Configure analytics

### Performance Targets

- [ ] Page load time < 3 seconds
- [ ] Time to Interactive < 5 seconds
- [ ] First Contentful Paint < 1.8 seconds
- [ ] Largest Contentful Paint < 2.5 seconds
- [ ] Cumulative Layout Shift < 0.1
- [ ] Google PageSpeed Score > 90

### Accessibility Targets

- [ ] WCAG 2.1 Level AA compliant
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Color contrast passes
- [ ] Form labels present
- [ ] Skip links functional
- [ ] ARIA attributes correct

## Support Resources

### Documentation
- Theme Docs: https://skyyrose.com/docs
- WordPress Codex: https://codex.wordpress.org
- WooCommerce Docs: https://woocommerce.com/documentation
- Elementor Docs: https://elementor.com/help
- Three.js Docs: https://threejs.org/docs

### Community
- Theme Support: https://skyyrose.com/support
- WordPress Forums: https://wordpress.org/support
- Stack Overflow: https://stackoverflow.com/questions/tagged/wordpress

### Development Tools
- Local Development: Local by Flywheel
- Version Control: Git
- Code Editor: VS Code with WordPress extensions
- Browser Testing: BrowserStack
- Performance: GTmetrix, Google PageSpeed

## Maintenance

### Regular Tasks

**Weekly:**
- Check for WordPress updates
- Check for plugin updates
- Check for theme updates
- Review security logs
- Check backup status

**Monthly:**
- Optimize database
- Review analytics
- Check broken links
- Update content
- Review comments

**Quarterly:**
- Security audit
- Performance review
- Accessibility audit
- SEO review
- User experience review

## Getting Help

### Before Requesting Support

1. Check documentation
2. Search support forums
3. Clear cache
4. Disable plugins (test conflict)
5. Switch to default theme (test theme)
6. Check error logs
7. Gather system info

### Support Request Template

```
Subject: [Issue Description]

WordPress Version:
Theme Version: 1.0.0
PHP Version:
Server:
Active Plugins: [List]

Issue Description:
[Detailed description]

Steps to Reproduce:
1.
2.
3.

Expected Result:
[What should happen]

Actual Result:
[What actually happens]

Error Messages:
[Any error messages]

Screenshots:
[Attach if relevant]
```

---

**Need Help?**
- Email: support@skyyrose.com
- Documentation: https://skyyrose.com/docs
- Live Chat: https://skyyrose.com/chat

**Happy Building! 🚀**
