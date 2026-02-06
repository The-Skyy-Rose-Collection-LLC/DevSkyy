# WordPress Copilot - Testing Guide

## Context7 Enforcement Test

The plugin enforces Context7 verification for ALL WordPress/Elementor/WooCommerce code generation.

### Test 1: Code Generation WITHOUT Context7 (Should Block)

**User request:**
```
Create an Elementor widget for a 3D product viewer
```

**Expected behavior:**
```
PreToolUse hook activates BEFORE Write/Edit:

CRITICAL: Before using Write or Edit tool for WordPress/Elementor/WooCommerce code:

1. Have you called Context7 MCP to verify current documentation?
   - Call: resolve-library-id (library name)
   - Call: query-docs (with specific query)

2. Are you implementing based on VERIFIED current docs (not memory)?

3. Which WordPress/Elementor/WooCommerce version are you targeting?

IF YOU HAVE NOT VERIFIED WITH CONTEXT7, STOP AND DO THAT FIRST.
```

**Result:** ❌ Write/Edit BLOCKED until Context7 verification

---

### Test 2: Code Generation WITH Context7 (Should Succeed)

**User request:**
```
Create an Elementor widget for a 3D product viewer
```

**Correct workflow:**
```
Step 1: I'll verify current Elementor widget API with Context7 first.

[Calls Context7 MCP]
1. resolve-library-id:
   {
     "libraryName": "elementor",
     "query": "custom widget development 3d product viewer"
   }

2. query-docs:
   {
     "libraryId": "/elementor/elementor",
     "query": "Widget_Base register_controls render responsive controls"
   }

Step 2: Context7 Verification Complete
✅ Verified: Elementor v3.18.2 documentation
- Widget class: Elementor\Widget_Base
- Control registration: register_controls()
- Render: render() and content_template()
- Responsive: add_responsive_control()

Step 3: Generate code following Elementor 3.18+ verified patterns

[NOW PreToolUse hook allows Write/Edit]

[Generates widget code]
```

**Result:** ✅ Code generated with current Elementor 3.18+ API

---

## Testing Commands

### 1. Deploy Command

```bash
/wordpress-copilot:deploy
```

**Expected:**
- Creates ZIP from theme directory
- Opens WordPress.com admin
- Guides user through upload
- Verifies deployment (CSP, console errors, CSS)
- Reports success/failure

### 2. Scaffold Command

```bash
/wordpress-copilot:scaffold widget product-3d-viewer --3d
```

**Expected:**
1. Calls Context7 to verify Elementor widget API
2. Generates widget file with current API
3. Includes 3D viewer integration
4. Applies SkyyRose branding (#B76E79)

### 3. Verify Command

```bash
/wordpress-copilot:verify --deep
```

**Expected:**
- Checks site availability
- Verifies CSP headers
- Counts console errors
- Runs Lighthouse audit
- Tests 3D CDN accessibility
- Reports overall health score

### 4. Search Command

```bash
/wordpress-copilot:search "luxury product slider react"
```

**Expected:**
- Searches GitHub repositories
- Searches npm packages
- Evaluates quality scores
- Ranks by relevance
- Shows top 3-5 results with pros/cons

---

## Testing Skills (Auto-Activation)

### Skill: immersive-3d-web-development

**Trigger:** User mentions "three.js", "3d", "webgl", "babylon", "r3f"

**Test:**
```
User: "How do I create a 3D jewelry viewer with Three.js?"
```

**Expected:**
- Skill auto-activates
- Provides Three.js guidance
- Suggests React Three Fiber for React integration
- References SkyyRose luxury lighting (#B76E79 rose gold)

### Skill: luxury-fashion-ecommerce

**Trigger:** User mentions "luxury", "fashion", "jewelry", "skyyrose", "high-end"

**Test:**
```
User: "Design a luxury checkout experience"
```

**Expected:**
- Skill auto-activates
- Applies SkyyRose brand DNA
- Suggests premium features (gift wrapping, concierge delivery)
- Implements luxury UX patterns

### Skill: deployment-workflow

**Trigger:** User mentions "deploy", "upload", "production", "rollback"

**Test:**
```
User: "Deploy the theme"
```

**Expected:**
- Skill auto-activates
- Follows deployment checklist
- WordPress.com specific workflow
- Post-deployment verification

---

## Testing Agents

### Agent: context7-enforcer

**Invocation:** Automatic before any WordPress/Elementor/WooCommerce code

**Test:**
```
User: "Create WooCommerce checkout field"
```

**Expected:**
1. Agent activates BEFORE code generation
2. Calls Context7 MCP:
   - resolve-library-id: "woocommerce"
   - query-docs: "checkout custom fields hooks"
3. Reviews WooCommerce 8.5+ documentation
4. Generates code with verified patterns
5. States version targeted: "WooCommerce 8.5+"

### Agent: deployment-manager

**Invocation:** `/wordpress-copilot:deploy` or "deploy theme"

**Test:**
```
User: "Deploy the CSP fix to skyyrose.co"
```

**Expected:**
1. Agent activates
2. Pre-deployment validation (PHP syntax, files, CSP)
3. Creates ZIP package
4. Opens WordPress.com admin
5. User uploads (guided)
6. Post-deployment verification
7. Reports: Console errors reduced from 107 to 8

### Agent: wordpress-architect

**Invocation:** Complex WordPress planning requests

**Test:**
```
User: "Plan a custom product type for pre-orders"
```

**Expected:**
1. Agent activates
2. Queries Context7 for WooCommerce product types API
3. Designs architecture:
   - Custom product class extending WC_Product
   - Meta fields for ship date
   - Admin UI integration
   - Frontend display
4. Provides implementation plan with phases

---

## Context7 Integration Verification

### Check 1: resolve-library-id Works

```bash
# Should find library ID
resolve-library-id --library-name="wordpress" --query="theme development"

# Expected output:
# Library ID: /wordpress/wordpress
# Version: 6.4.2
# Description: WordPress core documentation
```

### Check 2: query-docs Works

```bash
# Should return current documentation
query-docs --library-id="/wordpress/wordpress" --query="add_action hooks"

# Expected output:
# [Current WordPress 6.4+ documentation about hooks]
```

### Check 3: Blocking Works

**Without Context7 verification:**
```
[Attempt to Write WordPress code]
→ PreToolUse hook BLOCKS
→ Error: "Context7 verification required"
```

**With Context7 verification:**
```
[Call Context7 MCP]
✅ Verification complete
[Attempt to Write WordPress code]
→ PreToolUse hook ALLOWS
→ Code generated
```

---

## SkyyRose-Specific Tests

### Test: Brand Application

**Request:** "Create a product card"

**Expected:**
- Primary color: #B76E79 (rose gold)
- Font: Playfair Display (headings)
- Tagline: "Where Love Meets Luxury"
- Luxury animations (0.3s ease-in-out)
- Elegant hover effects

### Test: Collection Integration

**Request:** "Display products from Black Rose collection"

**Expected:**
- Query WooCommerce products with meta: _skyyrose_collection = 'black_rose'
- Apply gothic aesthetic
- Dark/moody styling
- Link to immersive 3D cathedral experience

### Test: 3D CDN Verification

**Request:** "Add Three.js to theme"

**Expected:**
- Verify CDN URL accessible: https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js
- Add to CSP whitelist
- Test loading before deployment

---

## Success Criteria

✅ **Context7 Enforcement:**
- 100% of WordPress/Elementor/WooCommerce code has Context7 verification
- 0 code generated from memory/outdated examples
- All generated code targets current versions (WP 6.4+, Elementor 3.18+, WC 8.5+)

✅ **Commands Work:**
- All 7 commands execute without errors
- Deploy command successfully creates ZIP and verifies deployment
- Scaffold command generates valid code with Context7 verification

✅ **Skills Auto-Activate:**
- WordPress keywords trigger appropriate skills
- Skills provide guidance (not outdated code)
- Skills reference Context7 for implementation

✅ **Agents Function:**
- context7-enforcer blocks code without verification
- deployment-manager handles WordPress.com deployment
- wordpress-architect plans with Context7-verified patterns

✅ **SkyyRose Branding:**
- All generated code uses #B76E79 rose gold
- Luxury aesthetics applied consistently
- Collections (Signature, Black Rose, Love Hurts) properly handled

---

## Troubleshooting

**Issue:** Context7 MCP not available

**Fix:**
1. Verify Context7 plugin installed
2. Check MCP server running
3. Test: `resolve-library-id --library-name="wordpress"`

**Issue:** PreToolUse hook not blocking

**Fix:**
1. Check hooks/hooks.json syntax
2. Verify hook type: "prompt" with "blocking": true
3. Restart Claude Code

**Issue:** Skills not auto-activating

**Fix:**
1. Verify SKILL.md frontmatter has `description` with trigger keywords
2. Check skill directory has `SKILL.md` (not `README.md`)
3. Test with exact trigger phrases

---

## Next Steps

After testing:
1. Run validation: `bash scripts/validate-plugin.sh` (if created)
2. Test with real skyyrose.co deployment
3. Measure Context7 verification rate (should be 100%)
4. Collect feedback on enforcement mechanism
5. Refine skills based on usage patterns

---

**Target:** Zero outdated WordPress/Elementor/WooCommerce code ever generated. Context7 verification enforced for everything.
