# Known Issues (Audit March 2026)

## CRITICAL: Cursor Disappears
- luxury-cursor.css sets cursor:none on body for desktop
- If luxury-cursor.js fails to load, users see NO cursor
- Fix: Add CSS fallback so cursor:none only applies when JS has initialized

## Navigation Conflicts
- header.php uses .navbar__ BEM classes (z-index: 1000)
- homepage-v2.css has separate .nav system (z-index: 8000) that overlaps
- Two mobile menu implementations: .mobile-menu (header) vs .mob-menu (homepage-v2)

## Content Offset Missing
- Fixed header is 72px tall but no spacer after it
- Pages without full-bleed heroes have content hidden behind navbar
- design-tokens.css has --header-height: 72px but it's not used for offset

## Duplicate Font Loading
- Google Fonts CDN loads Playfair Display
- Self-hosted fonts ALSO load Playfair Display
- 8 font families total from Google CDN (performance concern)

## Duplicate Cursor Elements
- footer.php hardcodes cursor divs (lines 235-237)
- luxury-cursor.js creates them dynamically via ensureElement()
- Results in double DOM elements

## Template-Homepage-Luxury Inline Styles
- 120+ CSS rules inlined in template file
- Duplicates much of homepage-v2.css functionality
- Inline script for scroll-reveal duplicates animations.js
