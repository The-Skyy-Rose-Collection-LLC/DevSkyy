# 🌹 Skyy Rose Collection - GIF Logo Integration

## Overview
This WordPress theme includes a fully integrated GIF logo system with responsive design and cross-browser compatibility.

## Logo Files Included
- `TSRC-logo-40h.gif` - Extra small mobile (40x40px)
- `TSRC-logo-50h.gif` - Small mobile (50x50px) 
- `TSRC-logo-60h.gif` - Desktop/tablet (60x60px)
- `TSRC-logo-80h.gif` - Large desktop (80x80px)

## Features
✅ **Responsive Design**: Different logo sizes for different screen sizes
✅ **Accessibility**: Proper alt text and ARIA labels
✅ **Performance**: Optimized file sizes and lazy loading
✅ **SEO Friendly**: Proper heading structure (H1 on homepage)
✅ **Cross-Browser**: Works on all modern browsers
✅ **Retina Ready**: Crisp display on high-DPI screens

## Installation
1. Upload the theme to `/wp-content/themes/`
2. Activate the theme in WordPress admin
3. The logo will automatically appear in the header

## Customization
To replace the logo:
1. Replace the GIF files in `/assets/images/`
2. Keep the same naming convention: `TSRC-logo-[size].gif`
3. Recommended sizes:
   - 40x40px for mobile
   - 50x50px for small tablets
   - 60x60px for desktop
   - 80x80px for large screens

## CSS Classes
- `.skyy-rose-logo-container` - Logo wrapper
- `.skyy-rose-logo-link` - Clickable logo link
- `.skyy-rose-logo-gif` - The GIF image
- `.skyy-rose-logo-text` - Site title text
- `.skyy-rose-logo-picture` - Responsive picture element

## WordPress Customizer
The theme supports WordPress custom logo functionality. If a custom logo is uploaded via Appearance > Customize > Site Identity, it will override the default GIF logo.

## Troubleshooting
- **Logo not showing**: Check file permissions and paths
- **Logo too large**: Verify CSS max-width settings
- **Animation not working**: Ensure GIF files are properly optimized
- **Mobile issues**: Check responsive breakpoints in CSS

## Browser Support
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+
- iOS Safari 12+
- Android Chrome 60+

## Performance Notes
- Logo files are optimized for web use
- Uses `loading="eager"` for above-the-fold content
- Implements responsive images with `<picture>` element
- CSS transitions are hardware-accelerated

## Support
For technical support or customization requests, contact the development team.
