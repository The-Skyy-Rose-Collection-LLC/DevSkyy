# WordPress Copilot

> **Comprehensive WordPress development copilot with professor-grade web development, immersive 3D expertise, and open-source intelligence.**

Hardcoded for **skyyrose.co** but intelligently leverages the open-source ecosystem.

---

## 🎯 What It Does

WordPress Copilot is a **world-class development assistant** that combines:

### 🎓 Professor-Grade Web Development
- **Interactive:** React, Vue, Svelte, state management, SSR/CSR
- **Static:** Jamstack, SSG, edge functions, ISR
- **Architecture:** Component patterns, design systems, CSS methodologies
- **Performance:** Core Web Vitals, lazy loading, code splitting
- **Accessibility:** WCAG 2.1 AA/AAA, ARIA patterns, keyboard navigation

### 🌐 Immersive 3D Web Development
- **Libraries:** Three.js, React Three Fiber, Babylon.js, WebGL/WebGPU
- **Graphics:** Shaders (GLSL), post-processing, custom effects
- **Physics:** Cannon.js, Ammo.js, Rapier, collision detection
- **XR:** WebXR API, VR/AR experiences, spatial audio
- **Optimization:** LOD, occlusion culling, instancing, GPU optimization

### 🔧 WordPress/Elementor/WooCommerce Mastery
- **Themes:** Custom theme development with modern JS/CSS
- **Elementor:** Custom widget development, 3D product viewers
- **WooCommerce:** Hooks, filters, custom functionality
- **WordPress.com:** Platform-specific deployment and optimization

### 🎯 Open-Source Intelligence (Web Sniper)
- **Discovery:** Find themes, components, libraries on GitHub, npm, WordPress.org
- **Evaluation:** Quality scoring (stars, downloads, maintenance, license)
- **Integration:** Adapt open-source resources to SkyyRose branding

---

## 🚀 Features

### Auto-Triggering
Automatically activates on WordPress-related keywords:
```
wordpress, elementor, woocommerce, theme, widget, deploy,
3d, threejs, babylonjs, react, vue, performance, accessibility
```

### Smart Integration - Context7 First

**🔒 MANDATORY CODE GENERATION POLICY:**

This plugin will **NEVER** generate WordPress/Elementor/WooCommerce code without first verifying current documentation via Context7 MCP.

**Workflow for ALL code generation:**
```
1. User requests WordPress/Elementor/WooCommerce code
2. Plugin STOPS and calls Context7:
   - resolve-library-id → get library ID
   - query-docs → get current documentation
3. Plugin reviews verified docs (WordPress 6.4+, Elementor 3.18+, WooCommerce 8.5+)
4. Plugin generates code based on VERIFIED current patterns
5. Plugin never uses memory/cached examples without verification
```

**Pre-Write Hook:**
- Blocks Write/Edit tools until Context7 verification completed
- Forces explicit confirmation of Context7 check
- Prevents outdated code generation

**Integration:**
- **Context7 (MANDATORY):** Verified docs before ANY code generation
- **Serena:** Stores patterns (but re-verifies with Context7 before using)
- **Playwright:** Browser automation for deployment verification

### Deployment Automation
- Creates optimized theme ZIP
- Verifies deployment (CSP headers, CSS loading, console errors)
- Automatic rollback on failure
- Post-deployment validation

### Code Generation
- React/Vue/Svelte components
- Three.js/R3F 3D scenes
- Elementor widgets
- WordPress templates
- Custom shaders (GLSL)

### Continuous Learning
- Extracts patterns from each session
- Saves to Serena memory
- Improves recommendations over time

---

## 📦 Installation

### Option 1: Local Development
```bash
# Clone or copy to your project
cp -r wordpress-copilot /path/to/your/project/

# Test with Claude Code
cc --plugin-dir /path/to/your/project/wordpress-copilot
```

### Option 2: Global Installation
```bash
# Copy to Claude plugins directory
cp -r wordpress-copilot ~/.claude/plugins/

# Restart Claude Code
```

---

## 💻 Usage

### Commands

#### `/wordpress-copilot:deploy`
Deploy theme to skyyrose.co with verification
```bash
/wordpress-copilot:deploy
# Creates ZIP, opens browser, verifies deployment
```

#### `/wordpress-copilot:scaffold [type]`
Generate components, widgets, templates
```bash
/wordpress-copilot:scaffold widget product-configurator --3d
/wordpress-copilot:scaffold template collection-page
/wordpress-copilot:scaffold component ProductCard --react --typescript
```

#### `/wordpress-copilot:optimize [--type]`
Run performance or security optimization
```bash
/wordpress-copilot:optimize --type=performance
/wordpress-copilot:optimize --type=security
```

#### `/wordpress-copilot:verify`
Check deployment status and health
```bash
/wordpress-copilot:verify
# Checks: CSP headers, CSS loading, console errors, performance
```

#### `/wordpress-copilot:rollback [backup-id]`
Restore previous theme version
```bash
/wordpress-copilot:rollback
# Guides rollback process
```

#### `/wordpress-copilot:search [query]`
Find open-source resources
```bash
/wordpress-copilot:search "luxury product slider react"
/wordpress-copilot:search "three.js clothing configurator"
```

#### `/wordpress-copilot:learn`
Extract patterns from current session
```bash
/wordpress-copilot:learn
# Saves patterns to Serena memory
```

### Auto-Activation

The copilot **automatically activates** when you:
- Mention WordPress, Elementor, or WooCommerce
- Ask about 3D web development (Three.js, Babylon.js)
- Work on React/Vue/Svelte components
- Discuss performance or accessibility

No need to invoke explicitly - it's always listening!

---

## 🏗️ Architecture

```
wordpress-copilot/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
│
├── skills/                   # 15 auto-activating skills
│   ├── Foundation (Web Development)
│   │   ├── interactive-web-development/
│   │   ├── static-web-development/
│   │   ├── frontend-architecture/
│   │   ├── web-performance/
│   │   ├── web-accessibility/
│   │   ├── immersive-3d-web-development/
│   │   └── open-source-intelligence/
│   │
│   └── WordPress Specialization
│       ├── theme-development/
│       ├── elementor-widgets/
│       ├── woocommerce-integration/
│       ├── performance-optimization/
│       ├── deployment-workflow/
│       ├── security-hardening/
│       ├── infrastructure/
│       └── continuous-learning/
│
├── commands/                 # 7 user-invoked commands
│   ├── deploy.md
│   ├── scaffold.md
│   ├── optimize.md
│   ├── verify.md
│   ├── rollback.md
│   ├── search.md
│   └── learn.md
│
├── agents/                   # 9 autonomous specialists
│   ├── immersive-3d-specialist.md
│   ├── web-dev-consultant.md
│   ├── wordpress-architect.md
│   ├── theme-builder.md
│   ├── deployment-manager.md
│   ├── performance-auditor.md
│   ├── context7-consultant.md
│   ├── pattern-learner.md
│   └── resource-hunter.md
│
├── hooks/                    # Auto-triggering
│   ├── hooks.json
│   └── scripts/
│
├── scripts/                  # 25+ utilities
│   ├── OSS Intelligence
│   ├── 3D Development
│   ├── Web Development
│   └── WordPress
│
├── references/               # Detailed documentation
└── examples/                 # Working code samples
```

---

## ⚙️ Configuration

### SkyyRose Hardcoded Settings

The plugin is pre-configured for skyyrose.co:

```json
{
  "site": {
    "url": "https://skyyrose.co",
    "theme": "skyyrose-2025",
    "themeDir": "/Users/coreyfoster/DevSkyy/wordpress-theme/skyyrose-2025",
    "branding": {
      "primaryColor": "#B76E79",
      "tagline": "Where Love Meets Luxury"
    }
  },
  "verification": {
    "cspRequirements": [
      "unsafe-inline",
      "stats.wp.com",
      "cdn.babylonjs.com"
    ],
    "consoleErrorThreshold": 10,
    "performanceTargets": {
      "LCP": 2.5,
      "FID": 100,
      "CLS": 0.1
    }
  },
  "ossStrategy": {
    "preferredLicenses": ["MIT", "Apache-2.0", "GPL-2.0", "GPL-3.0"],
    "minimumStars": 100,
    "maximumAge": "6 months"
  }
}
```

### Custom Settings (Optional)

Create `.claude/wordpress-copilot.local.md` to override defaults:

```markdown
# WordPress Copilot - Local Settings

## Site Configuration
- URL: https://skyyrose.co
- Theme Directory: /path/to/custom/theme

## Branding
- Primary Color: #B76E79
- Apply branding automatically: yes

## OSS Strategy
- Minimum stars: 200
- Maximum age: 3 months
```

---

## 🎓 Skills Overview

### Web Development Foundation

| Skill | Expertise |
|-------|-----------|
| **Interactive Web Development** | React, Vue, Svelte, SSR, state management |
| **Static Web Development** | Jamstack, SSG, edge functions, ISR |
| **Frontend Architecture** | Component patterns, design systems, CSS |
| **Web Performance** | Core Web Vitals, optimization, bundle analysis |
| **Web Accessibility** | WCAG 2.1 AA/AAA, ARIA, keyboard navigation |
| **Immersive 3D Web** | Three.js, R3F, Babylon.js, WebXR, shaders |
| **Open-Source Intelligence** | GitHub, npm, WordPress.org resource discovery |

### WordPress Specialization

| Skill | Expertise |
|-------|-----------|
| **Theme Development** | Custom themes, file structure, best practices |
| **Elementor Widgets** | Custom widget development, 3D integration |
| **WooCommerce Integration** | Hooks, filters, custom functionality |
| **Performance Optimization** | WordPress-specific performance patterns |
| **Deployment Workflow** | WordPress.com deployment and verification |
| **Security Hardening** | OWASP compliance, CSP, XSS prevention |
| **Infrastructure** | WordPress.com platform specifics |
| **Continuous Learning** | Pattern extraction and memory storage |

---

## 🤖 Agents

### Autonomous Specialists

| Agent | Role |
|-------|------|
| **Immersive 3D Specialist** | Three.js, R3F, Babylon.js, WebXR expert |
| **Web Dev Consultant** | React, Vue, TypeScript, performance guru |
| **WordPress Architect** | System design for WordPress projects |
| **Theme Builder** | Code generation (web + 3D + WordPress) |
| **Deployment Manager** | Automated deployment to skyyrose.co |
| **Performance Auditor** | Web + 3D performance analysis |
| **Context7 Consultant** | Documentation verification |
| **Pattern Learner** | Extract and save patterns to Serena |
| **Resource Hunter** | Find and evaluate open-source resources |

---

## 📊 Example Workflows

### 1. Deploy Theme Update

```
User: "Deploy the CSP fix to skyyrose.co"

Copilot:
1. Creates optimized theme ZIP
2. Opens WordPress.com admin
3. User uploads theme
4. Verifies CSP headers updated
5. Checks console errors reduced
6. Confirms CSS loading properly
7. Reports deployment success
```

### 2. Create 3D Product Configurator

```
User: "Create a 3D product configurator for jewelry"

Copilot:
1. Auto-triggers (3D + product keywords)
2. Queries Context7 for R3F best practices
3. Searches GitHub for similar configurators
4. Presents top 3 open-source options
5. Adapts chosen template to SkyyRose branding
6. Generates React Three Fiber component
7. Optimizes for 60fps performance
8. Creates Elementor widget wrapper
9. Saves pattern to Serena
```

### 3. Optimize Performance

```
User: "The site is slow, optimize it"

Copilot:
1. Runs Lighthouse audit
2. Identifies issues (large images, render-blocking CSS)
3. Generates optimization plan
4. Implements lazy loading
5. Optimizes images (WebP, AVIF)
6. Defers non-critical CSS
7. Re-tests performance
8. Reports improvements (LCP: 4.5s → 2.1s)
```

---

## 🔧 Development

### Running Tests

```bash
# Validate plugin structure
bash scripts/validate-plugin.sh

# Test hook configuration
bash scripts/test-hooks.sh

# Test deployment workflow
bash scripts/test-deployment.sh
```

### Adding New Skills

1. Create skill directory: `skills/my-skill/`
2. Add `SKILL.md` with frontmatter
3. Add references in `references/`
4. Add examples in `examples/`
5. Test with trigger phrases

### Adding New Agents

1. Create agent file: `agents/my-agent.md`
2. Add frontmatter with description
3. Define triggering conditions
4. Specify tools and capabilities
5. Test with relevant scenarios

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

Built with:
- [Claude Code](https://claude.ai/code) - AI-powered development assistant
- [Context7](https://context7.com) - Verified documentation
- [Serena](https://github.com/serena-ai/serena) - Memory and pattern storage

---

## 📞 Support

**Issues:** https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues
**Email:** dev@skyyrose.co
**Website:** https://skyyrose.co

---

**Status:** ✅ **Production Ready** ✅

Version 1.0.0 - Complete implementation with all 34 components
