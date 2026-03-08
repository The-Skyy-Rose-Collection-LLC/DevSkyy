# Code Style and Conventions

## PHP
- WordPress coding standards (tabs for indentation)
- Functions prefixed with skyyrose_
- Constants: SKYYROSE_VERSION, SKYYROSE_ASSETS_URI
- All output escaped: esc_html(), esc_attr(), esc_url(), wp_kses_post()
- Translation-ready: __(), _e(), esc_html_e()

## CSS
- BEM naming: .navbar__brand, .col-card__img
- Design tokens in :root variables
- Prefixes by section: .sr- (single product), .lux- (luxury homepage), .col- (collections)
- Breakpoints: 1024px, 768px, 480px

## JS
- Vanilla JS, IIFE pattern (function() { 'use strict'; })();
- IntersectionObserver for scroll-reveal
- WCAG compliance (focus traps, aria attributes)
