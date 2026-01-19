# Immersive Architect Validation Protocol

This skill provides the 5-gate validation system for all code generation. It activates on ANY code writing, modification, or suggestion to ensure production-grade output.

---

## Validation Pipeline

```
REQUEST → [G1] → [G2] → [G3] → [G4] → [G5] → EXECUTE/BLOCK
          │      │      │      │      │
       Design  Security Quality  Perf  Immersive
```

Every code generation must pass ALL 5 gates before execution.

---

## GATE 1: DESIGN & ARCHITECTURE ALIGNMENT

Validates structural integrity and pattern consistency.

### Checkpoints

| Checkpoint | Criteria |
|------------|----------|
| **Theme Structure** | Follows WordPress theme hierarchy (template-parts/, inc/, assets/) |
| **Plugin Boundaries** | Theme-building logic stays in plugin; generated themes are standalone |
| **Hook Architecture** | Uses appropriate actions/filters; no direct function overwrites |
| **Template System** | Compatible with block themes (theme.json) AND classic themes |
| **Naming Conventions** | Prefixed functions/classes (e.g., `immersive_`, `Immersive_Architect_`) |
| **Dependency Declaration** | Required plugins declared via TGM or similar |

### Valid Example
```php
// CORRECT: Properly namespaced, hookable
add_action('immersive_architect_render_section', function($section_data) {
    do_action('immersive_before_section', $section_data);
    // render logic
    do_action('immersive_after_section', $section_data);
});
```

### Invalid Example
```php
// WRONG: Global function, no hooks
function render_section($data) {
    echo $data['content'];
}
```

---

## GATE 2: SECURITY & WORDPRESS STANDARDS

Non-negotiable security requirements for theme generation.

### Checkpoints

| Checkpoint | Criteria |
|------------|----------|
| **Input Sanitization** | All user inputs through `sanitize_*()` functions |
| **Output Escaping** | Context-appropriate: `esc_html()`, `esc_attr()`, `esc_url()`, `wp_kses_post()` |
| **Nonce Verification** | All form submissions and AJAX calls verified |
| **Capability Checks** | `current_user_can()` before privileged operations |
| **SQL Safety** | `$wpdb->prepare()` for all dynamic queries |
| **File Operations** | `WP_Filesystem` API only; no direct file writing functions |
| **Dynamic Code** | NO code execution functions or dynamic includes from user input |
| **Theme Check** | Generated themes pass Theme Check plugin validation |

### Valid Example
```php
// CORRECT: Full security chain
public function save_theme_settings() {
    // 1. Nonce check
    if (!wp_verify_nonce($_POST['_wpnonce'], 'immersive_save_settings')) {
        wp_die(__('Security check failed', 'immersive-architect'));
    }

    // 2. Capability check
    if (!current_user_can('edit_theme_options')) {
        wp_die(__('Unauthorized', 'immersive-architect'));
    }

    // 3. Sanitize input
    $settings = array_map('sanitize_text_field', $_POST['settings']);

    // 4. Validate against schema
    $validated = $this->validate_settings_schema($settings);

    // 5. Save with escaping handled at output
    update_option('immersive_theme_settings', $validated);
}
```

---

## GATE 3: WOOCOMMERCE & E-COMMERCE INTEGRATION

Ensures seamless commerce functionality in generated themes.

### Checkpoints

| Checkpoint | Criteria |
|------------|----------|
| **WooCommerce Hooks** | Uses official hooks, not template overwrites where avoidable |
| **Cart/Checkout Safety** | No interference with payment flow; AJAX cart updates proper |
| **Product Templates** | Supports all product types (simple, variable, grouped, external) |
| **Shop Loop Integrity** | Preserves `woocommerce_before/after_shop_loop_item` hooks |
| **Mini-Cart Compatibility** | Fragments update correctly with immersive elements |
| **Checkout Blocks** | Compatible with both classic checkout AND checkout blocks |
| **HPOS Compatibility** | High-Performance Order Storage ready (no direct postmeta for orders) |

### Valid Example
```php
// CORRECT: Hook-based product card enhancement
add_action('woocommerce_before_shop_loop_item', function() {
    echo '<div class="immersive-product-wrapper" data-immersive-hover="true">';
}, 5);

add_action('woocommerce_after_shop_loop_item', function() {
    immersive_render_product_enhancements();
    echo '</div>';
}, 99);
```

### Invalid Example
```php
// WRONG: Completely replacing WooCommerce template
remove_action('woocommerce_before_shop_loop_item', 'woocommerce_template_loop_product_link_open');
// This breaks plugin compatibility
```

---

## GATE 4: PERFORMANCE & OPTIMIZATION

Immersive experiences must not sacrifice load times.

### Checkpoints

| Checkpoint | Criteria |
|------------|----------|
| **Asset Loading** | Conditional enqueue; immersive assets only where needed |
| **Critical CSS** | Above-fold styles inlined or preloaded |
| **JavaScript Strategy** | Defer non-critical; no render-blocking in head |
| **Image Optimization** | WebP with fallbacks; srcset for responsive images |
| **3D/AR Assets** | Lazy-loaded; compressed glTF/GLB; LOD support |
| **Database Queries** | No N+1; use WP_Query with proper caching |
| **Object Caching** | Transients for expensive operations; cache invalidation hooks |
| **Core Web Vitals** | LCP < 2.5s, FID < 100ms, CLS < 0.1 target |

### Valid Example
```php
// CORRECT: Conditional, deferred asset loading
public function enqueue_immersive_assets() {
    if (!is_woocommerce()) {
        return;
    }

    wp_enqueue_style(
        'immersive-critical',
        IMMERSIVE_URL . 'assets/css/critical.css',
        [],
        IMMERSIVE_VERSION
    );

    if ($this->page_has_3d_products()) {
        wp_enqueue_script(
            'immersive-3d-viewer',
            IMMERSIVE_URL . 'assets/js/3d-viewer.min.js',
            ['three-js'],
            IMMERSIVE_VERSION,
            ['strategy' => 'defer', 'in_footer' => true]
        );
    }
}
```

---

## GATE 5: IMMERSIVE EXPERIENCE INTEGRITY

Validates the "wow factor" without breaking usability.

### Checkpoints

| Checkpoint | Criteria |
|------------|----------|
| **Progressive Enhancement** | Core functionality works without JS; immersive layers on top |
| **Accessibility (a11y)** | WCAG 2.1 AA minimum; motion respects prefers-reduced-motion |
| **Touch Support** | All interactions work on touch devices; no hover-only states |
| **Fallback Rendering** | Graceful degradation for unsupported browsers/devices |
| **Animation Performance** | GPU-accelerated (transform/opacity); no layout thrashing |
| **3D/AR Standards** | WebXR where supported; model-viewer fallback |
| **Loading States** | Skeleton screens or progressive loading for heavy assets |
| **Interaction Feedback** | Every action has visual/haptic response |

### Valid Example
```html
<div class="immersive-product-hero"
     data-immersive-parallax="true"
     aria-label="Product showcase">

    <!-- Base: Static image (works everywhere) -->
    <img src="fallback.jpg"
         alt="Product name"
         class="immersive-hero__fallback"
         loading="eager">

    <!-- Enhancement: 3D model (loaded conditionally) -->
    <model-viewer
        class="immersive-hero__3d"
        src="model.glb"
        alt="Product 3D view"
        ar
        camera-controls
        loading="lazy"
        reveal="interaction">
    </model-viewer>
</div>
```

---

## Response Protocol

After running all gates, respond with:

### VERIFIED
All 5 gates pass. Code is approved for execution.

```
VERIFIED

Gates Passed: G1 OK | G2 OK | G3 OK | G4 OK | G5 OK

Summary: [Brief description]
Execution: Proceeding with implementation
```

### PARTIAL
Some gates pass, but specific items need attention.

```
PARTIAL

Gates: G1 OK | G2 OK | G3 WARN | G4 OK | G5 OK

Blocker: [Specific issue]
- Issue: [What's wrong]
- Impact: [Why it matters]
- Resolution: [What needs to happen]

Action: Researching solution
```

### BLOCKED
Critical issues prevent safe execution.

```
BLOCKED

Failed Gate: G2 (Security)

Critical Issue: [Specific concern]
- Risk: [What could go wrong]
- Evidence: [Why flagged]

Required Action:
1. [First step]
2. [Second step]

Will Not Proceed Until: [Condition met]
```

---

## Recovery Protocol

When PARTIAL or BLOCKED:

1. **IDENTIFY** - Pinpoint exact gate failure
2. **RESEARCH** - Consult official docs / Context7 MCP
3. **VALIDATE** - Confirm solution against gate criteria
4. **IMPLEMENT** - Apply fix to code
5. **RE-VALIDATE** - Run all gates again
6. **PROCEED** - Only when all gates pass

### Research Sources (Priority Order)

1. WordPress Developer Resources: developer.wordpress.org
2. WooCommerce Docs: woocommerce.com/documentation
3. Theme Handbook: developer.wordpress.org/themes
4. Block Editor Handbook: developer.wordpress.org/block-editor
5. WebXR/Three.js: threejs.org/docs
6. Context7 MCP: Real-time documentation lookup

---

## Quick Reference

```
IMMERSIVE ARCHITECT VALIDATION
─────────────────────────────────────────────────────────────
GATE 1  │ Design & Architecture — Structure, Hooks, Names
GATE 2  │ Security — Sanitize, Escape, Nonce, Caps
GATE 3  │ WooCommerce — Hooks, Templates, HPOS
GATE 4  │ Performance — Assets, Queries, Core Web Vitals
GATE 5  │ Immersive — A11y, Progressive, Fallbacks
─────────────────────────────────────────────────────────────
VERIFIED │ All gates pass - Execute
PARTIAL  │ Some issues - Research & Resolve
BLOCKED  │ Critical block - Halt until fixed
─────────────────────────────────────────────────────────────
```

---

**Protocol Version**: 1.0.0
**Compatible With**: WordPress 6.4+, WooCommerce 8.0+, PHP 8.1+
