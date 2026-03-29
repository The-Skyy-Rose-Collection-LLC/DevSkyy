---
name: deploy-and-verify
description: Deploy WordPress theme and verify every page on production
model: sonnet
---

# Deploy & Verify Agent

Deploy the SkyyRose WordPress theme and verify all pages render correctly.

## Steps

1. **PHP Syntax Check** — Run `php -l` on all theme PHP files. STOP if any fail.

2. **Dead Reference Check** — Grep all PHP/CSS/JS for references to deleted files. STOP if found.

3. **Deploy** — Run `eval "$(/opt/homebrew/bin/brew shellenv)" && bash scripts/deploy-theme.sh`

4. **Cache Flush** — SSH to server and run `wp cache flush && wp transient delete --all`

5. **Verify Every Page** — Use Chrome DevTools MCP to navigate and screenshot:
   - https://skyyrose.co/?nocache=1 (Homepage)
   - https://skyyrose.co/collection-signature/?nocache=1
   - https://skyyrose.co/collection-black-rose/?nocache=1
   - https://skyyrose.co/collection-love-hurts/?nocache=1
   - https://skyyrose.co/collection-kids-capsule/?nocache=1
   - https://skyyrose.co/pre-order/?nocache=1
   - https://skyyrose.co/about/?nocache=1

6. **Report** — For each page, confirm:
   - Page loads (not blank/error)
   - Hero section visible
   - Product grid renders (if applicable)
   - No ticker/social-proof overlays
   - Correct collection colors

Return a pass/fail table for all 7 pages.
