---
name: search
description: Search for open-source WordPress themes, plugins, components, or examples
argument-hint: "[query] [--type=theme|plugin|component|example] [--evaluate]"
allowed-tools: [Bash, WebSearch, WebFetch, Read]
---

# Search Open-Source Resources

Find battle-tested WordPress themes, plugins, React components, 3D examples, and code snippets to accelerate SkyyRose development.

## Usage

```bash
/wordpress-copilot:search "luxury fashion WordPress theme"
/wordpress-copilot:search "Elementor 3D product widget" --type=plugin
/wordpress-copilot:search "React Three Fiber jewelry viewer" --evaluate
/wordpress-copilot:search "WooCommerce pre-order form" --type=component
```

## Search Targets

### 1. GitHub Repositories

```bash
# Use GitHub API for targeted searches
curl "https://api.github.com/search/repositories?q=wordpress+luxury+theme+language:php+stars:>100&sort=stars&per_page=10"

# Search with multiple filters
curl "https://api.github.com/search/repositories?q=elementor+widget+3d+language:php+stars:>50&sort=updated"

# Search for React components
curl "https://api.github.com/search/repositories?q=react+three+fiber+product+viewer+language:typescript+stars:>100"
```

**Query optimization:**
- Include tech stack: `wordpress`, `elementor`, `react`, `three.js`
- Filter by language: `language:php`, `language:typescript`
- Require quality: `stars:>100`, `forks:>20`
- Recent updates: `pushed:>2024-01-01`

### 2. npm Registry

```bash
# Search packages
npm search "three.js product viewer" --searchlimit=10

# Get package details
npm view @react-three/fiber

# Check bundle size
npm view @react-three/fiber dist.unpackedSize

# Alternative: use npms.io API
curl "https://api.npms.io/v2/search?q=react+three+fiber+product"
```

### 3. WordPress.org

```bash
# Search themes
curl "https://api.wordpress.org/themes/info/1.2/?action=query-themes&request[search]=luxury+fashion&request[per_page]=10"

# Search plugins
curl "https://api.wordpress.org/plugins/info/1.2/?action=query_plugins&request[search]=elementor+widget&request[per_page]=10"

# Get specific theme details
curl "https://api.wordpress.org/themes/info/1.2/?action=theme_information&request[slug]=astra"
```

### 4. CodeSandbox / CodePen

```bash
# Search CodeSandbox (via web)
open "https://codesandbox.io/search?query=three.js%20product%20viewer"

# Search CodePen
open "https://codepen.io/search/pens?q=luxury%20product%20animation"
```

### 5. Three.js Examples

```bash
# Official Three.js examples
curl -s "https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/README.md" | grep -i "jewelry\|product\|pbr\|material"

# React Three Fiber examples
curl -s "https://api.github.com/repos/pmndrs/drei/contents/examples" | jq '.[].name'
```

## Search Strategies

### For WordPress Themes

```javascript
const searchThemes = async (query) => {
  // 1. WordPress.org themes
  const wpThemes = await searchWordPressOrg(query, 'theme');

  // 2. GitHub premium themes
  const githubThemes = await searchGitHub({
    query: `${query} wordpress theme`,
    language: 'php',
    stars: '>200',
    license: 'MIT,Apache-2.0,GPL-2.0'
  });

  // 3. ThemeForest (manual search)
  console.log('Check ThemeForest:', `https://themeforest.net/search/${query}`);

  return {
    wpOrg: wpThemes,
    github: githubThemes,
    premium: 'Manual search required'
  };
};
```

### For React Components

```javascript
const searchComponents = async (query) => {
  // 1. npm packages
  const npmPackages = await searchNpm(query);

  // 2. GitHub repositories
  const githubRepos = await searchGitHub({
    query: `${query} react component`,
    language: 'typescript',
    stars: '>100',
    topics: ['react', 'component', 'ui']
  });

  // 3. Component libraries
  const libraries = [
    'shadcn/ui',
    'radix-ui',
    'chakra-ui',
    'mantine'
  ];

  return { npm: npmPackages, github: githubRepos, libraries };
};
```

### For 3D Examples

```javascript
const search3DExamples = async (query) => {
  // 1. Three.js official examples
  const threeExamples = await fetch('https://threejs.org/examples/');

  // 2. React Three Fiber showcase
  const r3fExamples = await searchGitHub({
    query: `${query} react-three-fiber`,
    language: 'javascript',
    stars: '>50'
  });

  // 3. Babylon.js playground
  console.log('Check Babylon Playground:', 'https://playground.babylonjs.com/');

  // 4. CodeSandbox
  const sandboxes = await searchCodeSandbox(query);

  return { three: threeExamples, r3f: r3fExamples, sandboxes };
};
```

## Quality Evaluation (--evaluate flag)

Automatically score and rank results:

```javascript
function calculateQualityScore(repo) {
  const scores = {
    // Stars (max 10 points)
    stars: Math.min(repo.stargazers_count / 1000, 10),

    // Recent maintenance (10 points if < 6 months)
    maintenance: getDaysSinceUpdate(repo.pushed_at) < 180 ? 10 : 5,

    // Documentation (10 points)
    documentation: hasGoodDocs(repo) ? 10 : 0,

    // TypeScript (5 points)
    typescript: repo.language === 'TypeScript' ? 5 : 0,

    // Tests (5 points)
    tests: hasTestDirectory(repo) ? 5 : 0,

    // License compatibility (5 points)
    license: ['MIT', 'Apache-2.0', 'BSD-3-Clause'].includes(repo.license?.spdx_id) ? 5 : 0,

    // Community (5 points)
    community: (repo.forks_count > 50 && repo.open_issues_count < 100) ? 5 : 0,

    // Bundle size (5 points for < 100KB)
    bundleSize: repo.size < 100000 ? 5 : 0
  };

  const total = Object.values(scores).reduce((a, b) => a + b, 0);

  return {
    score: total,
    maxScore: 55,
    percentage: Math.round((total / 55) * 100),
    breakdown: scores
  };
}
```

**Quality thresholds:**
- **Excellent** (40-55): Production-ready, actively maintained
- **Good** (30-39): Solid choice with minor concerns
- **Fair** (20-29): Usable but needs evaluation
- **Poor** (< 20): Avoid or use with caution

## Red Flags Detection

Automatically flag concerning patterns:

```javascript
const RED_FLAGS = [
  {
    flag: 'Abandoned',
    check: (repo) => getDaysSinceUpdate(repo.pushed_at) > 365,
    severity: 'HIGH'
  },
  {
    flag: 'Security Issues',
    check: (repo) => hasOpenSecurityIssues(repo),
    severity: 'CRITICAL'
  },
  {
    flag: 'No License',
    check: (repo) => !repo.license,
    severity: 'HIGH'
  },
  {
    flag: 'Large Bundle',
    check: (repo) => repo.size > 500000,
    severity: 'MEDIUM'
  },
  {
    flag: 'Many Dependencies',
    check: async (repo) => (await getDepCount(repo)) > 50,
    severity: 'MEDIUM'
  },
  {
    flag: 'No Tests',
    check: (repo) => !hasTestDirectory(repo),
    severity: 'LOW'
  }
];
```

## Search Report Format

```
🔍 Search Results: "luxury WordPress theme"
Query: luxury wordpress theme language:php stars:>100
Date: 2026-02-06
Results: 15 repositories, 8 npm packages, 12 WordPress.org themes

═══════════════════════════════════════════════════════════

TOP RESULTS (Quality Score > 35)

1. Astra Theme ⭐️ 92/100
   - URL: https://github.com/brainstormforce/astra
   - Stars: 5,234 | Forks: 892 | Updated: 3 days ago
   - License: GPL-2.0
   - Description: Fast, customizable WordPress theme
   - Bundle: 487KB | Tests: ✅ | Docs: ✅
   - Red Flags: None
   - SkyyRose Fit: Excellent - Elementor compatible, customizable

2. GeneratePress ⭐️ 85/100
   - URL: https://github.com/generatepress/generatepress
   - Stars: 3,876 | Forks: 654 | Updated: 1 week ago
   - License: GPL-2.0
   - Description: Lightweight, performance-focused
   - Bundle: 298KB | Tests: ✅ | Docs: ✅
   - Red Flags: None
   - SkyyRose Fit: Good - Fast, but less luxury styling

═══════════════════════════════════════════════════════════

GOOD MATCHES (Quality Score 25-34)
[List of 5 more results...]

FAIR MATCHES (Quality Score 15-24)
[List of 3 results...]

EXCLUDED (Red Flags)
- OldTheme: Abandoned (last update 2 years ago)
- NoLicenseTheme: No license specified
- HugeTheme: Bundle size 2.3MB

═══════════════════════════════════════════════════════════

RECOMMENDATIONS

For SkyyRose luxury fashion site:
1. **Astra** - Best overall fit, Elementor compatible
2. **GeneratePress** - Best performance, but needs luxury styling
3. Consider hybrid: Use GeneratePress base + custom luxury styling

Next Steps:
- Review top 3 themes in detail
- Test with SkyyRose branding (#B76E79)
- Evaluate Elementor widget compatibility
- Check WooCommerce integration
```

## SkyyRose Adaptation

After finding resources, adapt to SkyyRose brand:

```javascript
const adaptToSkyyRose = (component) => {
  return {
    ...component,
    branding: {
      primaryColor: '#B76E79',      // Rose gold
      fontFamily: 'Playfair Display',
      spacing: 'luxury',             // More whitespace
      animations: 'smooth',          // 0.3s ease-in-out
    },
    features: {
      ...component.features,
      threeD: true,                  // Add 3D support
      accessibility: 'WCAG 2.1 AA',
      performance: 'Core Web Vitals optimized'
    }
  };
};
```

## Integration Workflow

```bash
# 1. Search
/wordpress-copilot:search "React product viewer" --evaluate

# 2. Review top results
# Read quality scores, check red flags

# 3. Clone winner
git clone <top-result-url> temp-evaluation

# 4. Evaluate locally
cd temp-evaluation
npm install
npm run dev

# 5. Adapt to SkyyRose
# Apply branding, integrate with theme

# 6. Test
# Verify functionality, performance

# 7. Document attribution
# Add to README, package.json
```

## Search Examples

### Find Elementor Widget

```bash
/wordpress-copilot:search "Elementor custom widget" --type=plugin --evaluate
```

### Find 3D Product Viewer

```bash
/wordpress-copilot:search "Three.js jewelry viewer" --type=component
```

### Find WooCommerce Extension

```bash
/wordpress-copilot:search "WooCommerce pre-order" --type=plugin
```

### Find Performance Plugin

```bash
/wordpress-copilot:search "WordPress cache performance" --type=plugin --evaluate
```

### Find React Animation Library

```bash
/wordpress-copilot:search "React scroll animations" --type=component
```

## License Compatibility

**Compatible with SkyyRose (commercial use allowed):**
- MIT
- Apache-2.0
- BSD-2-Clause / BSD-3-Clause
- GPL-2.0 / GPL-3.0 (for WordPress themes/plugins)

**Review carefully:**
- LGPL (derivative works)
- CC-BY (attribution required)
- Custom licenses

**Avoid:**
- CC-BY-NC (non-commercial)
- Proprietary licenses without purchase
- No license (all rights reserved)

## See Also

- `/wordpress-copilot:scaffold` - Generate components from scratch
- `skills/open-source-intelligence/` - Detailed OSS search strategies
- `skills/immersive-3d-web-development/` - 3D component patterns
