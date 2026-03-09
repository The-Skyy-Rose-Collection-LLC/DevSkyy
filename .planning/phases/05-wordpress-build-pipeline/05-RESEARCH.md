# Phase 5: WordPress Build Pipeline - Research

**Researched:** 2026-03-09
**Domain:** WordPress theme asset minification (JS + CSS) via npm build tooling
**Confidence:** HIGH

## Summary

The WordPress theme `skyyrose-flagship` already has partial build infrastructure: webpack 5.105 with TerserPlugin for JS and clean-css-cli 5.6.3 for CSS. However, the existing configuration is severely incomplete. Webpack only has 6 JS entry points (3 of which reference files that no longer exist -- `main.js`, `three-init.js`, `accessibility.js`), while there are 43 actual JS source files. The CSS build script only handles 3 files out of 55. No source maps are generated. The existing `.min.js` and `.min.css` files (41 JS, 54 CSS) appear to have been generated previously by some process and are already checked in.

The fix is straightforward: expand the webpack config to auto-discover all JS source files (eliminating the need to manually maintain entry points), replace the hardcoded CSS build with a script that processes all CSS files (including `system/animations.css` in a subdirectory and `style.css` at the theme root), enable source map generation in both tools, and ensure a single `npm run build` produces everything.

**Primary recommendation:** Use webpack with dynamic entry discovery via `glob.sync` for JS minification, and a Node.js build script using `clean-css` (programmatic API) for CSS minification -- both with source map generation enabled.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BUILD-01 | All 24 JS files in WordPress theme pass through webpack minification | Actual count is 43 JS source files. Webpack config needs dynamic entry discovery via `glob.sync()` to catch all files without manual maintenance. Current config only has 6 entries (3 broken). |
| BUILD-02 | All 31 CSS files in WordPress theme pass through clean-css minification | Actual count is 55 CSS source files (54 top-level + 1 in `system/` subdir) plus root `style.css`. Current build script only handles 3 files. Needs a Node.js script using clean-css programmatic API to process all files. |
| BUILD-03 | Source maps generated for development debugging | Webpack: add `devtool: 'source-map'`. Clean-css: add `--source-map` flag or `sourceMap: true` option. `.gitignore` already excludes `*.map` files -- source maps will exist locally but not in git (correct behavior). |
| BUILD-04 | Single `npm run build` command produces all .min files from source | Existing `build` script already chains `build:js && build:css`. Just need both sub-scripts to actually work correctly. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| webpack | 5.105.4 | JS minification/bundling | Already installed, industry standard for WordPress theme builds |
| webpack-cli | 6.0.1 | CLI for webpack | Already installed, required for `npx webpack` |
| terser-webpack-plugin | 5.3.17 | JS minification within webpack | Already installed, best-in-class JS minifier |
| clean-css-cli | 5.6.3 | CSS minification | Already installed, fast and reliable CSS minifier |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| glob (Node built-in) | N/A | Dynamic file discovery for webpack entries | Used in webpack.config.js to find all `*.js` files |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| webpack for JS | terser-cli directly | Simpler but no dynamic entry discovery, no future bundling capability |
| clean-css-cli | PostCSS + cssnano | More powerful but overkill -- these are standalone CSS files, not a PostCSS pipeline |
| Separate JS/CSS tools | Vite or esbuild | Would require ripping out existing working setup for minimal gain |

**Installation:**
```bash
# No new packages needed -- all tools already installed
cd wordpress-theme/skyyrose-flagship
npm install  # ensures existing deps are in node_modules
```

## Architecture Patterns

### Current File Layout
```
wordpress-theme/skyyrose-flagship/
  style.css                          # WordPress theme header (1235 lines)
  assets/
    js/
      *.js          (43 source files)
      *.min.js      (41 minified -- missing elementor-frontend, immersive-world)
    css/
      *.css         (54 top-level source files)
      *.min.css     (54 top-level minified -- missing immersive-world)
      system/
        animations.css      (1 source)
        animations.min.css  (1 minified)
  webpack.config.js                  # JS build config (NEEDS REWRITE)
  package.json                       # Build scripts (NEEDS UPDATE)
```

### Pattern 1: Dynamic Webpack Entry Discovery
**What:** Use `glob.sync()` to auto-discover all JS source files instead of manually listing entries
**When to use:** When you have many standalone script files that each need individual minification (not bundled together)
**Example:**
```javascript
// webpack.config.js
const path = require('path');
const glob = require('glob');
const TerserPlugin = require('terser-webpack-plugin');

// Auto-discover all source JS files (exclude .min.js)
const entries = {};
glob.sync('./assets/js/*.js', { ignore: './assets/js/*.min.js' }).forEach(file => {
  const name = path.basename(file, '.js');
  entries[name] = file;
});

module.exports = {
  mode: 'production',
  entry: entries,
  output: {
    path: path.resolve(__dirname, 'assets/js'),
    filename: '[name].min.js',
    clean: false,  // Don't delete source files
    iife: true,    // Wrap in IIFE (these are browser scripts, not modules)
  },
  devtool: 'source-map',  // BUILD-03: generate .map files
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: false,
            drop_debugger: true,
            pure_funcs: ['console.debug'],
          },
          format: { comments: false },
        },
        extractComments: false,
      }),
    ],
  },
};
```

### Pattern 2: Programmatic CSS Minification Script
**What:** A Node.js script that uses clean-css programmatically to process all CSS files with source maps
**When to use:** When clean-css-cli can't handle dynamic file lists or you need source map generation
**Example:**
```javascript
// scripts/build-css.js
const CleanCSS = require('clean-css');
const fs = require('fs');
const path = require('path');
const glob = require('glob');

const cssDir = path.resolve(__dirname, '../assets/css');
const rootDir = path.resolve(__dirname, '..');

// All CSS files: assets/css/**/*.css + style.css (exclude *.min.css)
const cssFiles = [
  ...glob.sync('assets/css/**/*.css', { cwd: rootDir, ignore: 'assets/css/**/*.min.css' }),
  'style.css',
];

cssFiles.forEach(relPath => {
  const srcPath = path.resolve(rootDir, relPath);
  const minPath = srcPath.replace(/\.css$/, '.min.css');
  const source = fs.readFileSync(srcPath, 'utf8');
  const output = new CleanCSS({ sourceMap: true }).minify(source);
  fs.writeFileSync(minPath, output.styles);
  fs.writeFileSync(minPath + '.map', output.sourceMap.toString());
});
```

### Anti-Patterns to Avoid
- **Manually listing every file in webpack entry:** Breaks whenever a new JS file is added; use `glob.sync` instead
- **Using webpack for CSS:** Webpack's CSS handling requires loaders, extract plugins, etc. -- overkill for standalone CSS files that just need minification
- **Outputting minified files to a separate `dist/` directory:** The WordPress `enqueue.php` system expects `.min.js` and `.min.css` files alongside source files in the same directory
- **Using `output.clean: true` in webpack:** This would delete all source JS files in the output directory
- **Bundling all JS files into one:** Each file is independently enqueued by WordPress based on the current template -- they must remain separate

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JS minification | Custom regex-based minifier | TerserPlugin via webpack | Handles ES2021+, preserves semantics, source maps |
| CSS minification | Custom CSS stripping | clean-css (programmatic) | Handles edge cases (calc, custom properties, @supports) |
| File discovery | Hardcoded file list | `glob.sync()` pattern | Self-maintaining, never misses new files |
| Source maps | Manual position mapping | Built into both tools | Source maps are complex (VLQ encoding, source content) |

**Key insight:** The existing tools already installed in the project are the right ones. The problem is not tool selection but incomplete configuration. Don't add new tools -- fix the config.

## Common Pitfalls

### Pitfall 1: Webpack Treats JS Files as Modules by Default
**What goes wrong:** Webpack wraps output in module boilerplate, breaking scripts that expect to run in global scope (e.g., `window.SkyyRose = ...`)
**Why it happens:** Webpack 5 defaults to `output.library.type: 'module'` behavior
**How to avoid:** Set `output.iife: true` to wrap in IIFE. Do NOT set `output.library` (not needed for standalone scripts). These files are vanilla browser scripts, not modules.
**Warning signs:** Minified JS throws "X is not defined" errors in browser, or global variables become undefined

### Pitfall 2: Webpack output.clean Deletes Source Files
**What goes wrong:** Setting `output.clean: true` deletes ALL files in the output directory -- including source `.js` files
**Why it happens:** Output directory (`assets/js`) IS the source directory
**How to avoid:** Keep `clean: false` (already set in current config)
**Warning signs:** After build, source files disappear

### Pitfall 3: CSS Files in Subdirectories (system/animations.css)
**What goes wrong:** A flat glob like `assets/css/*.css` misses `assets/css/system/animations.css`
**Why it happens:** Single-star glob doesn't recurse into subdirectories
**How to avoid:** Use `assets/css/**/*.css` (double-star glob) to recurse
**Warning signs:** animations.min.css is never generated

### Pitfall 4: .gitignore Subdirectory Rule Gap
**What goes wrong:** `.gitignore` has `!assets/css/*.min.css` to un-ignore minified CSS, but this only covers the top-level `assets/css/` directory. `assets/css/system/animations.min.css` remains ignored.
**Why it happens:** Git `!` negation with single-star doesn't cover subdirectories
**How to avoid:** Add `!assets/css/**/*.min.css` to `.gitignore` (same for source maps if they should be committed)
**Warning signs:** `git status` doesn't show newly generated minified files in subdirectories

### Pitfall 5: Root style.css Has WordPress Theme Header
**What goes wrong:** Minifying `style.css` strips the `/* Theme Name: ... */` comment header that WordPress requires
**Why it happens:** clean-css removes comments by default
**How to avoid:** Use the `level: { 1: { specialComments: 1 } }` option to preserve the first `/*!` comment, OR skip root style.css minification entirely (it's already included as-is by `get_stylesheet_uri()`)
**Warning signs:** After deploy, WordPress doesn't recognize the theme

### Pitfall 6: Three Missing Files in Webpack Config (main.js, three-init.js, accessibility.js)
**What goes wrong:** Current webpack build fails with 3 errors because entry files don't exist
**Why it happens:** Files were deleted/renamed but webpack config wasn't updated
**How to avoid:** Dynamic entry discovery eliminates this class of bug entirely
**Warning signs:** `npm run build:js` exits with errors

### Pitfall 7: Large Diff When First Built
**What goes wrong:** The first proper build will regenerate all 43 .min.js and 55 .min.css files, creating a massive diff
**Why it happens:** Existing minified files were generated by unknown tools (possibly different minifier versions/settings)
**How to avoid:** This is expected and acceptable. One big commit to establish the pipeline. Already noted in STATE.md as a known concern.
**Warning signs:** 96+ files changed in the commit

## Code Examples

### webpack.config.js (Complete Replacement)
```javascript
// Source: pattern verified against webpack 5 docs + existing project setup
const path = require('path');
const glob = require('glob');
const TerserPlugin = require('terser-webpack-plugin');

// Auto-discover all .js files, exclude .min.js
const entries = {};
glob.sync('./assets/js/*.js', { ignore: './assets/js/*.min.js' }).forEach(file => {
  const name = path.basename(file, '.js');
  entries[name] = file;
});

module.exports = {
  mode: 'production',
  entry: entries,
  output: {
    path: path.resolve(__dirname, 'assets/js'),
    filename: '[name].min.js',
    clean: false,
    iife: true,
  },
  devtool: 'source-map',
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: false,
            drop_debugger: true,
            pure_funcs: ['console.debug'],
          },
          format: { comments: false },
        },
        extractComments: false,
      }),
    ],
  },
  performance: {
    maxAssetSize: 500000,
    maxEntrypointSize: 500000,
    hints: 'warning',
  },
};
```

### package.json build scripts (Updated)
```json
{
  "scripts": {
    "build": "npm run build:js && npm run build:css",
    "build:js": "webpack --mode production",
    "build:css": "node scripts/build-css.js"
  }
}
```

### enqueue.php Pattern (Already Correct -- No Changes Needed)
```php
// The existing pattern in enqueue.php is correct:
$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
$file = $use_min && file_exists( $dir . '/foo.min.js' ) ? 'foo.min.js' : 'foo.js';
// This gracefully falls back to source when SCRIPT_DEBUG is true or .min doesn't exist
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual webpack entry listing | `glob.sync()` auto-discovery | webpack 4+ (2018) | No stale entries, zero maintenance |
| clean-css CLI with hardcoded files | Programmatic API with glob | clean-css 4+ (2017) | Handles any number of files, source maps |
| No source maps | Source maps alongside minified | Always supported | `SCRIPT_DEBUG` enables debugging |

**Deprecated/outdated:**
- `UglifyJS`: Replaced by Terser (ES2015+ support)
- `CSSNano` for simple minification: Overkill when clean-css handles it fine
- Manually listed webpack entries: Replaced by dynamic discovery pattern

## Current State Analysis

### File Counts (ACTUAL vs REQUIREMENTS)
| Asset Type | Requirement Says | Actual Count | Notes |
|------------|------------------|--------------|-------|
| JS source files | 24 | 43 | Requirements were written before full file audit |
| CSS source files | 31 | 55 (54 top-level + 1 subdir) | Requirements were written before full file audit |
| Root style.css | Not mentioned | 1 (1235 lines) | May or may not need minification |

**Recommendation:** Build ALL files. The requirement intent is "every file gets minified." The specific counts (24, 31) appear to be from an earlier snapshot of the codebase.

### Current Build Status
| Component | Status | Issues |
|-----------|--------|--------|
| webpack.config.js | Broken | 3 of 6 entries reference non-existent files; only 6 of 43 files listed |
| build:css script | Incomplete | Only processes 3 of 55 CSS files; no source maps |
| Source maps | Not generated | webpack `devtool` not set; clean-css `--source-map` not used |
| `npm run build` | Fails | JS build fails due to missing entry files |

### Existing Minified Files
- 41 of 43 JS files already have `.min.js` (missing: `elementor-frontend`, `immersive-world`)
- 54 of 55 CSS files already have `.min.css` (missing: `immersive-world`)
- 0 source map files exist for theme assets
- Existing `.min` files are real minified output (verified by size comparison)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Shell script + file existence checks |
| Config file | N/A (no test framework needed for build verification) |
| Quick run command | `cd wordpress-theme/skyyrose-flagship && npm run build` |
| Full suite command | `cd wordpress-theme/skyyrose-flagship && npm run build && node -e "..."` (verification script) |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BUILD-01 | All JS files minified | smoke | `cd wordpress-theme/skyyrose-flagship && npm run build:js && test $(find assets/js -maxdepth 1 -name "*.js" -not -name "*.min.js" \| wc -l) -eq $(find assets/js -maxdepth 1 -name "*.min.js" \| wc -l)` | N/A (inline) |
| BUILD-02 | All CSS files minified | smoke | `cd wordpress-theme/skyyrose-flagship && npm run build:css && test $(find assets/css -name "*.css" -not -name "*.min.css" \| wc -l) -eq $(find assets/css -name "*.min.css" \| wc -l)` | N/A (inline) |
| BUILD-03 | Source maps generated | smoke | `find wordpress-theme/skyyrose-flagship/assets -name "*.map" \| wc -l` (should be > 0) | N/A (inline) |
| BUILD-04 | Single build command | smoke | `cd wordpress-theme/skyyrose-flagship && npm run build` (exit code 0) | N/A (inline) |

### Sampling Rate
- **Per task commit:** `cd wordpress-theme/skyyrose-flagship && npm run build`
- **Per wave merge:** Full build + file count verification
- **Phase gate:** Build succeeds + all source files have matching .min files + .map files exist

### Wave 0 Gaps
- [ ] `wordpress-theme/skyyrose-flagship/scripts/build-css.js` -- new CSS build script
- [ ] `wordpress-theme/skyyrose-flagship/scripts/verify-build.sh` -- post-build verification (optional but recommended for CI integration in Phase 6)

## Open Questions

1. **Root style.css minification**
   - What we know: `style.css` is 1235 lines with a WordPress theme header comment. The existing build script creates `style.min.css` via clean-css.
   - What's unclear: Whether the planner should preserve the WordPress header comment in the minified version, or whether `style.min.css` even gets loaded (the `enqueue.php` uses `get_stylesheet_uri()` which always loads `style.css`, not `style.min.css`)
   - Recommendation: Continue minifying `style.css` to `style.min.css` (preserving the first comment block) since the existing build already does this and the enqueue system checks for `.min` variants. Low risk.

2. **Requirement file counts (24 JS / 31 CSS) vs actual (43 JS / 55 CSS)**
   - What we know: The requirements document says 24 and 31. The actual codebase has 43 and 55.
   - What's unclear: Whether requirements should be updated, or if some files should be excluded.
   - Recommendation: Build ALL files. The requirement intent is clear -- "every source file gets minified." Update the requirement counts in REQUIREMENTS.md after implementation.

3. **elementor-frontend.js special handling**
   - What we know: This file exists but has no `.min.js` counterpart. Elementor is a WordPress page builder.
   - What's unclear: Whether this file should be minified (it might interact with Elementor's own build system).
   - Recommendation: Minify it like all others. If Elementor has issues, the `file_exists()` check in enqueue.php will gracefully fall back to the source file.

## Sources

### Primary (HIGH confidence)
- **Local filesystem analysis** -- direct examination of all 43 JS and 55 CSS source files, webpack.config.js, package.json, enqueue.php, .gitignore
- **webpack 5.105.4 installed** -- verified config options against installed version
- **clean-css-cli 5.6.3 installed** -- verified CLI behavior via `npm run build:css`
- **Existing build tested** -- `npm run build:js` confirmed broken (3 missing entry files), `npm run build:css` confirmed working but incomplete (3 files only)

### Secondary (MEDIUM confidence)
- **glob.sync() pattern for webpack** -- widely used pattern in WordPress theme build tooling, verified compatible with Node.js built-in `glob` (Node 22+) and npm `glob` package

### Tertiary (LOW confidence)
- None -- all findings verified directly against the local codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all tools already installed and verified
- Architecture: HIGH - existing enqueue.php pattern is correct and needs no changes
- Pitfalls: HIGH - all pitfalls discovered through direct testing of existing build

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (stable tooling, no version-sensitive findings)
