---
name: scaffold
description: Generate WordPress components, Elementor widgets, React components, or 3D scenes
argument-hint: "[type] [name] [--typescript] [--3d] [--tests]"
allowed-tools: [Read, Write, Bash, Grep, Glob]
---

# Scaffold Component

Generate boilerplate code for various component types.

## Usage

```bash
/wordpress-copilot:scaffold widget product-viewer --3d --typescript
/wordpress-copilot:scaffold template collection-page
/wordpress-copilot:scaffold component ProductCard --react --tests
/wordpress-copilot:scaffold scene jewelry-configurator --r3f
```

## Component Types

### 1. Elementor Widget
```bash
/wordpress-copilot:scaffold widget [name]
```

Generates:
- `elementor-widgets/[name].php`
- Widget class with Elementor integration
- SkyyRose branding (#B76E79)
- Example usage documentation

### 2. WordPress Template
```bash
/wordpress-copilot:scaffold template [name]
```

Generates:
- `template-[name].php`
- Template with header/footer
- WooCommerce integration hooks
- Responsive structure

### 3. React Component
```bash
/wordpress-copilot:scaffold component [Name] --react [--typescript] [--tests]
```

Generates:
- `components/[Name].tsx` (if --typescript)
- PropTypes or TypeScript interface
- Test file (if --tests)
- Storybook story (optional)

### 4. Three.js Scene
```bash
/wordpress-copilot:scaffold scene [name] --threejs
```

Generates:
- Basic Three.js setup
- Scene, camera, renderer
- OrbitControls
- Animation loop
- Lighting setup

### 5. React Three Fiber Component
```bash
/wordpress-copilot:scaffold scene [name] --r3f
```

Generates:
- R3F Canvas setup
- Camera and controls
- Example 3D objects
- Performance optimization

## Flags

**--typescript**: Generate TypeScript code
**--3d**: Include 3D visualization features
**--tests**: Generate test files
**--r3f**: Use React Three Fiber (3D)
**--branded**: Apply SkyyRose branding (default: true)

## Examples

### Elementor 3D Product Widget
```bash
/wordpress-copilot:scaffold widget product-3d-viewer --3d
```

### React Product Card
```bash
/wordpress-copilot:scaffold component ProductCard --react --typescript --tests
```

### Collection Page Template
```bash
/wordpress-copilot:scaffold template love-hurts-collection
```

## Generated Code

All scaffolded code includes:
- Full comments and documentation
- SkyyRose branding (#B76E79 rose gold)
- Accessibility features (ARIA labels, keyboard navigation)
- Responsive design patterns
- Performance optimizations

## Interactive Mode

If no arguments provided, prompts for:
1. Component type
2. Component name
3. Additional features
4. TypeScript or JavaScript
5. Include tests?
