---
name: Open-Source Intelligence
description: Use when searching for open-source resources, themes, components, libraries, or examples. Triggers on keywords like "find", "search for", "look for", "discover", "open source", "github", "npm", "template", "example", "boilerplate".
version: 1.0.0
---

# Open-Source Intelligence (Web Sniper)

Expert at discovering, evaluating, and integrating open-source resources from GitHub, npm, WordPress.org, and other platforms.

## Search Strategy

### 1. GitHub Search
```bash
# Use GitHub API for targeted searches
curl "https://api.github.com/search/repositories?q=wordpress+theme+luxury+language:php+stars:>100&sort=stars"

# Search for specific tech stack
curl "https://api.github.com/search/repositories?q=react+three+fiber+product+configurator+stars:>50"
```

### 2. npm Registry Search
```bash
# Search packages by keywords
npm search "3d viewer threejs gltf" --searchlimit=10

# Get package details
npm view @react-three/fiber
```

### 3. WordPress.org Search
```bash
# Search themes
curl "https://api.wordpress.org/themes/info/1.2/?action=query-themes&request[search]=luxury+fashion"

# Search plugins
curl "https://api.wordpress.org/plugins/info/1.2/?action=query_plugins&request[search]=elementor+widget"
```

## Evaluation Criteria

### Quality Score Algorithm
```javascript
function calculateQualityScore(repo) {
  const scores = {
    stars: Math.min(repo.stargazers_count / 1000, 10),
    maintenance: repo.pushed_at_days_ago < 180 ? 10 : 5,
    documentation: repo.has_readme ? 10 : 0,
    typescript: repo.has_typescript ? 5 : 0,
    tests: repo.has_tests ? 5 : 0,
    license: ['MIT', 'Apache-2.0'].includes(repo.license) ? 5 : 0
  };

  return Object.values(scores).reduce((a, b) => a + b, 0);
}
```

### Red Flags
- Last commit > 1 year ago
- Many open issues, few closed
- No documentation
- No license or restrictive license
- Large bundle size (> 500KB)
- Many dependencies
- Security vulnerabilities

## Integration Workflow

### 1. Find Resources
```javascript
// Search GitHub for React components
const results = await searchGitHub({
  query: 'react product viewer',
  language: 'typescript',
  stars: '>100',
  sort: 'updated'
});

// Filter by quality score
const filtered = results.filter(r => calculateQualityScore(r) > 30);
```

### 2. Evaluate Top Results
```javascript
const evaluation = {
  name: repo.name,
  url: repo.html_url,
  stars: repo.stargazers_count,
  lastUpdate: repo.pushed_at,
  license: repo.license?.spdx_id,
  bundleSize: await getBundleSize(repo),
  typescript: hasTypeScript(repo),
  qualityScore: calculateQualityScore(repo)
};
```

### 3. Adapt to SkyyRose
```javascript
// Apply SkyyRose branding
const branded = adaptComponent(component, {
  primaryColor: '#B76E79', // Rose gold
  fontFamily: 'Playfair Display',
  spacing: 'luxury', // More whitespace
  animations: 'smooth' // Elegant transitions
});
```

### 4. Document Attribution
```javascript
// Add to package.json or README
{
  "dependencies": {
    "original-package": "^1.0.0"
  },
  "attributions": [
    {
      "name": "original-package",
      "license": "MIT",
      "url": "https://github.com/author/original-package"
    }
  ]
}
```

## Resource Types

### WordPress Themes
**Sources:**
- WordPress.org theme directory
- ThemeForest (premium)
- GitHub (open-source)

**Search for:**
- Luxury fashion themes
- E-commerce themes with 3D support
- Elementor-compatible themes

### React/Vue Components
**Sources:**
- GitHub
- npm registry
- Component libraries (shadcn/ui, Radix UI)

**Search for:**
- Product configurators
- 3D viewers
- Gallery components
- Interactive carousels

### Three.js Examples
**Sources:**
- threejs.org/examples
- CodeSandbox
- GitHub showcases

**Search for:**
- Product visualization
- Material effects
- Lighting setups
- Performance optimization examples

### Elementor Widgets
**Sources:**
- GitHub
- WordPress.org plugins
- Elementor addon packs

**Search for:**
- Custom widgets
- 3D integration
- Product display widgets

## Best Practices

### License Compliance
```javascript
const COMPATIBLE_LICENSES = [
  'MIT',
  'Apache-2.0',
  'BSD-2-Clause',
  'BSD-3-Clause',
  'GPL-2.0',
  'GPL-3.0'
];

function isLicenseCompatible(license) {
  return COMPATIBLE_LICENSES.includes(license);
}
```

### Security Check
```bash
# Check for vulnerabilities
npm audit

# Scan with Snyk
npx snyk test
```

### Bundle Size Impact
```bash
# Check package size
npm view <package-name> dist.unpackedSize

# Analyze bundle impact
npx bundle-phobia <package-name>
```

## SkyyRose Adaptation

### Branding Rules
1. Replace colors with #B76E79 (rose gold)
2. Use Playfair Display for headings
3. Add elegant animations (0.3s ease-in-out)
4. Increase whitespace for luxury feel
5. Add SkyyRose attribution

### Code Modifications
```javascript
// Before (generic)
<Component color="blue" />

// After (SkyyRose branded)
<Component
  color="#B76E79"
  className="skyyrose-luxury-component"
  animationDuration={300}
/>
```

## References

See `references/` for:
- `github-search-guide.md`
- `npm-discovery.md`
- `wordpress-org-search.md`
- `evaluation-criteria.md`
- `license-compatibility.md`

## Scripts

See `scripts/` for:
- `github-search.sh`
- `npm-search.sh`
- `evaluate-quality.js`
- `check-license.sh`
- `bundle-size-check.js`
