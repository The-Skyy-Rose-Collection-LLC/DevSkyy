# SkyyRose Flagship Theme

## Description

SkyyRose Flagship is a premium WordPress theme featuring Three.js 3D integration, WooCommerce support, and Elementor Pro compatibility. Built with modern web standards and optimized for performance.

## Features

- **Three.js 3D Integration**: Built-in support for 3D models and interactive experiences
- **WooCommerce Compatible**: Full e-commerce functionality with custom templates
- **Elementor Pro Ready**: Custom widgets and seamless integration
- **Responsive Design**: Mobile-first approach with optimized layouts
- **Performance Optimized**: Lazy loading, deferred scripts, and efficient code
- **Accessibility Ready**: WCAG compliant with keyboard navigation support
- **Translation Ready**: Fully translatable with .pot file included
- **Custom Widgets**: Multiple widget areas for flexible layouts
- **SEO Optimized**: Clean, semantic HTML5 markup
- **Security Enhanced**: Following WordPress security best practices

## Installation

1. Upload the theme folder to `/wp-content/themes/`
2. Activate the theme through the 'Themes' menu in WordPress
3. Navigate to Appearance > Customize to configure theme settings

## Requirements

- WordPress 6.0 or higher
- PHP 7.4 or higher
- WooCommerce 7.0+ (optional)
- Elementor Pro 3.0+ (optional)

## Theme Structure

```
skyyrose-flagship-theme/
├── assets/
│   ├── css/          # Stylesheets
│   ├── js/           # JavaScript files
│   ├── images/       # Theme images
│   ├── fonts/        # Web fonts
│   ├── three/        # Three.js library
│   └── models/       # 3D model files
├── elementor/
│   ├── widgets/      # Custom Elementor widgets
│   └── templates/    # Elementor templates
├── inc/
│   ├── customizer.php        # Theme Customizer settings
│   ├── template-functions.php # Template helper functions
│   ├── woocommerce.php       # WooCommerce integration
│   └── elementor.php         # Elementor integration
├── template-parts/
│   ├── header/       # Header components
│   ├── footer/       # Footer components
│   └── content/      # Content templates
├── woocommerce/
│   ├── cart/         # Cart templates
│   ├── checkout/     # Checkout templates
│   └── single-product/ # Product templates
├── languages/        # Translation files
├── functions.php     # Theme functions
├── style.css         # Main stylesheet
├── header.php        # Header template
├── footer.php        # Footer template
├── index.php         # Main template
├── front-page.php    # Front page template
└── README.md         # This file
```

## Navigation Menus

The theme supports 4 navigation menu locations:

1. **Primary Menu**: Main site navigation
2. **Footer Menu**: Footer navigation
3. **Mobile Menu**: Mobile-specific menu
4. **Top Bar Menu**: Top bar menu

Configure menus via Appearance > Menus

## Widget Areas

The theme includes 6 widget areas:

1. **Primary Sidebar**: Main sidebar
2. **Footer Area 1-4**: Four footer widget columns
3. **Shop Sidebar**: WooCommerce shop pages (if WooCommerce is active)

## Customizer Options

Access via Appearance > Customize:

- **Header Settings**: Layout, sticky header
- **Footer Settings**: Copyright text
- **Layout Settings**: Container width, sidebar position
- **Typography**: Font family and sizes
- **Color Settings**: Primary and secondary colors

## WooCommerce Integration

The theme includes:

- Custom product templates
- 3D model viewer for products
- Cart fragments for AJAX updates
- Custom product gallery
- Shop sidebar

### Adding 3D Models to Products

1. Edit a product
2. Find the "3D Model" meta box in the sidebar
3. Enter the URL to your GLB or GLTF model file
4. The "View in 3D" button will appear on the product page

## Elementor Integration

The theme is fully compatible with Elementor and Elementor Pro:

- Custom widget categories
- Theme locations support
- Custom breakpoints
- Editor styles

## Development

### Building Assets

The theme uses standard WordPress development practices. No build process required.

### Coding Standards

- WordPress Coding Standards
- PHP_CodeSniffer configured
- ESLint for JavaScript
- PHPCS for PHP

## Support

For support, please visit:
- Website: https://skyyrose.com
- Documentation: https://skyyrose.com/docs
- Support Forum: https://skyyrose.com/support

## Changelog

### Version 1.0.0
- Initial release
- Three.js integration
- WooCommerce compatibility
- Elementor Pro support
- Responsive design
- Accessibility features

## Credits

- Three.js: https://threejs.org/
- Elementor: https://elementor.com/
- WooCommerce: https://woocommerce.com/

## License

SkyyRose Flagship Theme, Copyright 2026 SkyyRose Team
SkyyRose Flagship is distributed under the terms of the GNU GPL v2 or later.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
