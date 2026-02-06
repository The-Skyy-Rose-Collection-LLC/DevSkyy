---
name: learn
description: Extract reusable patterns from current session and save as skills
argument-hint: "[pattern-name] [--auto]"
allowed-tools: [Read, Write, Bash]
---

# Learn from Experience

Extract reusable patterns from WordPress development sessions and save them as skills for future use.

## Usage

```bash
/wordpress-copilot:learn
/wordpress-copilot:learn "elementor-widget-debugging"
/wordpress-copilot:learn --auto
```

## When to Use

Use this command when you:
- Solve a tricky WordPress issue
- Discover a useful Elementor pattern
- Find a reliable debugging technique
- Create a reusable component pattern
- Learn a WooCommerce integration trick
- Master a 3D viewer optimization
- Figure out a CSP configuration
- Develop a deployment workflow improvement

## What Gets Extracted

### 1. Error Resolution Patterns

```markdown
# Pattern: CSP Blocking WordPress.com Resources

**Context:** WordPress.com managed hosting with strict CSP

## Problem
- Console shows 107+ errors
- Resources blocked by CSP
- Elementor not loading
- Stats.wp.com blocked

## Solution
Update `inc/security-hardening.php`:
\`\`\`php
'script-src' => "'self' 'unsafe-inline' 'unsafe-eval' stats.wp.com widgets.wp.com",
'style-src' => "'self' 'unsafe-inline' s0.wp.com fonts.googleapis.com"
\`\`\`

## When to Use
- WordPress.com managed hosting
- Elementor integration
- Console errors related to CSP
- After theme deployment
```

### 2. Component Patterns

```markdown
# Pattern: Elementor 3D Product Widget

**Context:** Integrate Three.js into Elementor widget

## Implementation
\`\`\`php
class Product_3D_Widget extends \\Elementor\\Widget_Base {
    protected function render() {
        // Load Three.js CDN
        wp_enqueue_script('threejs', 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js');

        // Render container
        echo '<div id="product-3d-viewer" data-model="' . esc_url($model_url) . '"></div>';

        // Initialize viewer
        wp_add_inline_script('threejs', $this->get_viewer_script());
    }
}
\`\`\`

## When to Use
- Adding 3D product viewers
- Elementor widget development
- Three.js integration
```

### 3. Debugging Techniques

```markdown
# Pattern: WordPress.com Deployment Debugging

**Context:** Theme deployed but changes not visible

## Diagnostic Steps
1. Check theme actually uploaded (file modification date)
2. Clear Batcache (5-10 min wait)
3. Test with `?nocache=1` parameter
4. Verify in incognito window
5. Check browser console for errors
6. Curl CSP headers directly

## When to Use
- After deployment
- Changes not appearing
- Old content still showing
```

### 4. Framework Workarounds

```markdown
# Pattern: WordPress.com API Limitations

**Context:** WordPress.com uses different REST API path

## Problem
Standard `/wp-json/` doesn't work on WordPress.com

## Solution
Use: `https://site.wordpress.com/index.php?rest_route=/wp/v2/posts`
NOT: `https://site.wordpress.com/wp-json/wp/v2/posts`

## When to Use
- WordPress.com managed hosting
- REST API calls
- Plugin development for WordPress.com
```

### 5. Performance Optimizations

```markdown
# Pattern: 3D Viewer Performance Optimization

**Context:** Three.js viewer causing frame drops

## Optimization Techniques
1. Use LOD (Level of Detail) for distant objects
2. Implement instancing for repeated geometries
3. Enable frustum culling
4. Use GPU instancing for particles
5. Implement lazy loading for 3D assets

\`\`\`javascript
// LOD setup
const lod = new THREE.LOD();
lod.addLevel(highPolyMesh, 0);
lod.addLevel(mediumPolyMesh, 50);
lod.addLevel(lowPolyMesh, 100);
\`\`\`

## When to Use
- 3D viewers with frame rate issues
- Complex 3D scenes
- Mobile optimization
```

## Learning Modes

### Interactive Mode (default)

Prompts you to categorize the learning:

```
🎓 What did you learn?

1. Error Resolution
2. Component Pattern
3. Debugging Technique
4. Framework Workaround
5. Performance Optimization
6. Other

Select category: 1

Pattern name: csp-wordpress-com-fix

Brief description: Fix CSP blocking WordPress.com resources

[Extracts relevant code/steps from session]

Save to: ~/.claude/skills/wordpress-copilot/learned/csp-wordpress-com-fix.md

Preview:
[Shows generated skill file]

Save? (y/n): y
✅ Skill saved! Available as: wordpress-copilot:learned:csp-wordpress-com-fix
```

### Auto Mode (--auto)

Automatically detects patterns from session:

```bash
/wordpress-copilot:learn --auto
```

Scans conversation for:
- Error messages and their resolutions
- Repeated code patterns
- User corrections (indicates discovery)
- Successful debugging sequences
- Performance improvements

## Skill File Format

Generated skills follow this structure:

```markdown
---
name: [pattern-name]
description: [one-line description]
category: [error-resolution|component-pattern|debugging|workaround|optimization]
confidence: [high|medium|low]
date-learned: [YYYY-MM-DD]
session-id: [session-hash]
---

# [Pattern Name]

**Context:** [When this applies]

## Problem / Use Case
[What situation requires this pattern]

## Solution / Implementation
[Code, steps, or technique]

## When to Use
[Specific triggers for using this pattern]

## Related Patterns
[Links to similar skills]

## Example
[Real-world usage example]

## Gotchas
[Common mistakes or edge cases]
```

## Storage Structure

```
~/.claude/skills/wordpress-copilot/
└── learned/
    ├── csp-wordpress-com-fix.md
    ├── elementor-3d-widget-pattern.md
    ├── deployment-debugging.md
    ├── wordpress-com-api-workaround.md
    ├── 3d-viewer-optimization.md
    └── woocommerce-webhook-setup.md
```

## Pattern Confidence Levels

**High Confidence:**
- Used successfully 3+ times
- No exceptions or edge cases found
- Documented in official docs

**Medium Confidence:**
- Used successfully 1-2 times
- Some edge cases known
- Community-validated approach

**Low Confidence:**
- Used once, seemed to work
- Not fully tested
- May have edge cases

## Continuous Learning Flow

```mermaid
graph TD
    A[Session] --> B{Issue Solved?}
    B -->|Yes| C[/wordpress-copilot:learn]
    B -->|No| D[Continue troubleshooting]
    C --> E[Categorize Pattern]
    E --> F[Generate Skill File]
    F --> G[Review & Approve]
    G --> H[Save to learned/]
    H --> I[Available in future sessions]
    I --> J[Pattern gets refined with use]
    J --> K{High Confidence?}
    K -->|Yes| L[Promote to main skills/]
    K -->|No| I
```

## Pattern Promotion

After a learned pattern proves reliable:

```bash
# Review learned patterns
ls -la ~/.claude/skills/wordpress-copilot/learned/

# Promote high-confidence pattern to main skills
mv ~/.claude/skills/wordpress-copilot/learned/csp-wordpress-com-fix.md \
   /Users/coreyfoster/DevSkyy/wordpress-copilot/skills/csp-hardening/references/wordpress-com-csp-patterns.md
```

## Integration with Stop Hook

Auto-learning can run as Stop hook:

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "*",
      "hooks": [{
        "type": "prompt",
        "prompt": "Review this session for learnings. If any WordPress patterns, debugging techniques, or error resolutions were discovered, extract them using /wordpress-copilot:learn --auto"
      }]
    }]
  }
}
```

## Learning Analytics

Track learning over time:

```bash
# Count learned patterns
ls ~/.claude/skills/wordpress-copilot/learned/ | wc -l

# List by category
grep -l "category: error-resolution" ~/.claude/skills/wordpress-copilot/learned/*.md

# Find high-confidence patterns
grep -l "confidence: high" ~/.claude/skills/wordpress-copilot/learned/*.md

# Recent learnings
ls -lt ~/.claude/skills/wordpress-copilot/learned/ | head -5
```

## Pattern Sharing

Share learned patterns with team:

```bash
# Export patterns
tar -czf wordpress-patterns-export.tar.gz \
  ~/.claude/skills/wordpress-copilot/learned/

# Import patterns
tar -xzf wordpress-patterns-export.tar.gz -C ~/
```

## Examples

### Learn from CSP Fix

```bash
# After solving CSP issue
/wordpress-copilot:learn "csp-wordpress-com-fix"

# System extracts:
# - Original problem (107 console errors)
# - Solution (updated CSP in security-hardening.php)
# - Verification steps (curl headers, check console)
# - Related files (inc/security-hardening.php)
```

### Learn from 3D Optimization

```bash
# After optimizing 3D viewer
/wordpress-copilot:learn "3d-lod-optimization"

# System extracts:
# - Performance issue (frame drops)
# - LOD implementation
# - Before/after metrics
# - Code snippet
```

### Auto-Learn from Session

```bash
# At end of productive session
/wordpress-copilot:learn --auto

# System scans for:
# - Errors → solutions
# - Repeated patterns
# - User confirmations ("that worked!")
# - Performance improvements
```

## Pattern Quality Criteria

**Good patterns include:**
- ✅ Clear problem statement
- ✅ Step-by-step solution
- ✅ Code examples
- ✅ When to use
- ✅ Edge cases / gotchas
- ✅ Verification steps

**Avoid:**
- ❌ Vague descriptions
- ❌ No context
- ❌ One-time hacks
- ❌ Unverified solutions
- ❌ No examples

## See Also

- `skills/continuous-learning/` - Detailed learning methodology
- `/wordpress-copilot:verify` - Pattern verification
- `~/.claude/skills/` - All learned skills
