# Enhanced WordPress Theme Development Prompt

```
/wordpress-ops

OBJECTIVE: Transform the current SkyyRose WordPress build into an award-winning, production-ready full-stack custom theme with complete content and branded assets.

CONTEXT:
- Project: SkyyRose luxury fashion e-commerce
- Current State: Basic WordPress installation with WooCommerce
- Recently Added: 69 WordPress/Elementor/WooCommerce development packages
- Brand Guidelines: See /mnt/skills/user/skyyrose-brand-dna/SKILL.md
- Primary Color: #B76E79 (rose gold)
- Tagline: "Where Love Meets Luxury"

REQUIRED TOOLING (MANDATORY):
1. **Serena MCP** - For codebase navigation, symbol lookup, and file operations
2. **Context7** - For WordPress/WooCommerce/Elementor documentation lookup
3. **DevSkyy MCP** - For brand_context, wordpress_sync, 3d_generate tools

OPTIONAL (Use as needed):
- **Ralph Loop** - For complex immersive page builds and troubleshooting configuration issues
- **Figma MCP** - For design asset extraction
- **Notion MCP** - For content management/planning
- Agents: planner, tdd-guide, code-reviewer, security-reviewer

DELIVERABLES (All Required):

1. **Theme Structure** (Use Serena to create/organize files)
   - style.css with proper theme header
   - functions.php with all hooks/filters
   - template-hierarchy/ folder with all template files:
     * index.php, header.php, footer.php, sidebar.php
     * single.php, page.php, archive.php, search.php, 404.php
     * woocommerce/ templates (product, cart, checkout, my-account)
   - inc/ folder with modular includes
   - assets/ folder (css, js, images, fonts)
   - languages/ folder with .pot file

2. **Complete Page Templates** (Query Context7 for best practices)
   - Homepage (hero + featured collections + testimonials)
   - Shop page (product grid with filters)
   - Single product page (3D viewer, gallery, add-to-cart)
   - Collection pages (Black Rose, Signature, Love Hurts)
   - About page
   - Contact page
   - Cart page
   - Checkout page
   - My Account dashboard

3. **Custom Post Types & Taxonomies** (Use Serena to register)
   - Collection CPT (with custom fields)
   - Lookbook CPT
   - Press/Media CPT
   - Custom taxonomies: collection-type, season, material

4. **WooCommerce Integration**
   - Custom product templates with luxury design
   - Advanced product gallery (3D models support)
   - Size guide modal
   - Wishlist functionality
   - Quick view
   - Ajax add to cart
   - Custom checkout fields
   - Order tracking page

5. **Elementor Widgets** (Use Context7 for Elementor widget API)
   - Product carousel widget
   - Collection showcase widget
   - 3D product viewer widget
   - Testimonial slider widget
   - Instagram feed widget
   - Newsletter signup widget
   - Countdown timer widget
   - Size guide widget

6. **Custom Gutenberg Blocks**
   - Hero block with video background
   - Product grid block
   - Collection feature block
   - Testimonial carousel block
   - CTA banner block

7. **Theme Options Panel**
   - Logo upload (header + footer)
   - Color scheme customizer (respecting #B76E79 primary)
   - Typography settings
   - Social media links
   - Header/footer layout options
   - Homepage sections toggle
   - Maintenance mode

8. **Branded Assets** (Use brand_context for guidelines)
   - SkyyRose logo variations (SVG)
   - Placeholder product images (rose gold themed)
   - Collection hero images
   - Favicon and app icons
   - OG images for social sharing
   - Email templates (order confirmation, shipping)
   - Loading animations with brand aesthetic

9. **Performance Optimization**
   - Critical CSS inline
   - Lazy loading images
   - WebP support
   - Minified/concatenated assets
   - Redis object caching integration
   - CDN ready
   - Database query optimization

10. **Security & Compliance**
    - Sanitized inputs/outputs
    - Nonce verification
    - GDPR compliance (cookie notice, privacy policy)
    - SSL enforcement
    - Security headers
    - Rate limiting

11. **Documentation**
    - README.md with installation instructions
    - CHANGELOG.md
    - Theme documentation (usage guide)
    - Developer docs (hooks, filters, functions)
    - Style guide with component examples

WORKFLOW (Follow this order):

Phase 1: Planning (Use planner agent)
- Use Serena to explore current theme structure
- Use Context7 to research WordPress theme best practices
- Create implementation plan with file tree

Phase 2: Core Setup
- Create theme file structure with Serena
- Register custom post types/taxonomies
- Set up theme options panel
- Configure WooCommerce support

Phase 3: Templates & Components
- Build all template files following WP template hierarchy
- Create reusable components (header, footer, navigation)
- Implement WooCommerce templates
- Test with tdd-guide agent
- **IF ISSUES**: Use Ralph Loop to orchestrate complex template builds

Phase 4: Elementor & Gutenberg
- Create custom Elementor widgets
- Build Gutenberg blocks
- Test in Elementor builder
- Verify block editor compatibility
- **IF ISSUES**: Use Ralph Loop for widget/block integration debugging

Phase 5: Immersive Pages & Assets (Ralph Loop Recommended)
- Generate/integrate branded placeholder images
- Create logo variations
- Set up typography and color system
- Implement animations and transitions (Framer Motion, GSAP)
- Build immersive 3D product pages (React Three Fiber)
- **USE RALPH LOOP** for complex immersive page configuration and asset pipeline
- Integrate luxury animations from frontend/lib/animations/luxury-transitions.ts
- Apply SkyyRose color grading to all imagery

Phase 6: Performance & Security
- Optimize assets (minify, compress)
- Implement caching strategies
- Run security audit with security-reviewer agent
- Test performance (PageSpeed, GTmetrix)

Phase 7: Testing & QA
- Cross-browser testing
- Mobile responsiveness
- WooCommerce checkout flow
- Accessibility audit (WCAG 2.1 AA)
- Use code-reviewer agent for final review

Phase 8: Documentation
- Write user documentation
- Create developer docs
- Generate changelog
- Prepare demo content

SUCCESS CRITERIA:
- [ ] All 11 deliverable categories complete
- [ ] Theme passes WordPress.org theme review standards
- [ ] WooCommerce integration fully functional
- [ ] 100/100 PageSpeed score (mobile + desktop)
- [ ] WCAG 2.1 AA compliant
- [ ] Zero security vulnerabilities
- [ ] Fully responsive (320px - 4K)
- [ ] SEO optimized (proper markup, meta tags)
- [ ] All branded assets use #B76E79 color scheme
- [ ] Documentation complete and clear
- [ ] Immersive pages with 3D/animations fully functional

OUTPUT FORMAT:
1. Implementation plan with task breakdown
2. File tree of complete theme structure
3. Progress updates after each phase
4. Final summary with:
   - Theme features list
   - Performance metrics
   - Testing results
   - Installation guide link
   - Known issues (if any)

CONSTRAINTS:
- Use only installed packages (69 WordPress tools from package.json)
- Follow WordPress Coding Standards
- Compatible with PHP 7.4+ and WordPress 6.0+
- Mobile-first responsive design
- No jQuery dependencies (vanilla JS or modern frameworks)
- All strings translatable (i18n ready)

TROUBLESHOOTING PROTOCOL:

**When to Use Ralph Loop:**
1. **Complex Immersive Page Builds** - When integrating React Three Fiber, Framer Motion, or GSAP with WordPress
2. **Multi-Step Configuration Issues** - When theme setup requires coordinating multiple systems (Elementor + WooCommerce + Custom Blocks)
3. **Asset Pipeline Problems** - When image processing, 3D model integration, or animation setup fails
4. **Integration Conflicts** - When plugins/tools conflict during setup
5. **Performance Bottlenecks** - When optimization requires multiple coordinated changes

**Ralph Loop Command:**
```bash
/ralph-loop "Build immersive homepage with 3D product viewer, luxury animations, and WooCommerce integration"
```

**If Issues Arise:**
- **MCP Tools Not Responding**: Use `/mcp-health` for diagnostics
- **Complex Build Failures**: Use `/ralph-loop` with specific issue description
- **Design/Animation Issues**: Reference `docs/NEW_FEATURES_GUIDE.md` and `examples/luxury-product-showcase.tsx`
- **Performance Problems**: Run `/performance-audit`
- **Security Concerns**: Run `/security-review` before continuing
- **Code Quality**: Use `/code-review` for comprehensive analysis

```

---

## Key Updates

✅ **Added Ralph Loop to Optional Tooling** - Specified for complex builds and troubleshooting
✅ **Integrated Ralph Loop into Phase 5** - Recommended for immersive page configuration
✅ **Added Troubleshooting Protocol Section** - Clear guidelines on when/how to use Ralph Loop
✅ **Enhanced Phase 3 & 4** - Added Ralph Loop fallback for template and widget issues
✅ **Updated Success Criteria** - Added immersive pages functionality checkpoint

## When to Invoke Ralph Loop

The enhanced prompt now specifies Ralph Loop should be used for:

1. **Immersive Page Builds** (Phase 5) - Coordinating React Three Fiber, Framer Motion, GSAP with WordPress
2. **Multi-Step Configuration** - When theme setup requires orchestrating multiple systems
3. **Asset Pipeline Issues** - Image processing, 3D models, animation integration problems
4. **Integration Conflicts** - Plugin/tool compatibility issues
5. **Performance Bottlenecks** - Complex optimization requiring coordinated changes

Ralph Loop will orchestrate the complex task into manageable subtasks and handle dependencies automatically.
