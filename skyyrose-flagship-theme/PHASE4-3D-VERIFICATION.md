# Ralph Loop Deployment - Phase 4: 3D Asset Verification

## 4.1 Pre-Flight Checks (Local Verification)

### Verify Three.js Version in Templates
**Expected**: All templates loading Three.js 0.182.0 from unpkg CDN

**Check Command**:
```bash
cd /Users/coreyfoster/Documents/GitHub/DevSkyy/skyyrose-flagship-theme
grep -n "three@0.182.0" template-*.php
```

**Expected Output**: 6 matches across 4 templates

### Verify JavaScript Files Exist
```bash
ls -lh assets/js/*.js | grep -E "(signature|love-hurts|black-rose|preorder)"
```

**Expected Files**:
- signature-collection-3d.js
- love-hurts-3d.js
- black-rose-3d.js
- preorder-gateway-3d.js

### Verify Minified Versions Exist
```bash
ls -lh assets/js/*.min.js | grep -E "(signature|love-hurts|black-rose|preorder)"
```

**Expected**: 4 minified files (created in Phase 7)

## 4.2 Live Site Testing (Browser DevTools)

### Test 1: Three.js Library Loading

**Navigate to**: https://skyyrose.co/signature-collection-3d/

**Browser DevTools** (F12):
1. **Console Tab**: Check for errors
2. **Network Tab**: Filter "JS", verify:
   - `three@0.182.0/build/three.module.js` (Status: 200)
   - `three@0.182.0/examples/jsm/controls/OrbitControls.js` (Status: 200)
   - `three@0.182.0/examples/jsm/loaders/GLTFLoader.js` (Status: 200)

**Expected Console Output**:
```
✓ THREE.WebGLRenderer initialized
✓ Scene created
✓ Camera positioned
✓ OrbitControls enabled
```

**Errors to Watch For**:
- ❌ "THREE is not defined" → Three.js failed to load
- ❌ "WebGL not supported" → Browser compatibility issue
- ❌ "OrbitControls is not a constructor" → Addon load failure

### Test 2: 3D Scene Rendering

**Visual Checks** (Each Collection Page):

**Signature Collection** (signature-collection-3d):
- [ ] Glass pavilion renders
- [ ] Rose gold metallic materials visible
- [ ] Bloom/glow effect on metals
- [ ] Product hotspots appear as glowing spheres
- [ ] Camera rotates smoothly (mouse drag)
- [ ] Zoom works (mouse wheel)

**Love Hurts** (love-hurts-3d):
- [ ] Castle environment renders
- [ ] Rose petals falling (physics simulation)
- [ ] Red and black color scheme
- [ ] Enchanted rose glows
- [ ] 60fps animation (check DevTools Performance tab)
- [ ] Hotspots appear in correct positions

**Black Rose** (black-rose-3d):
- [ ] Gothic garden environment
- [ ] Volumetric fog renders
- [ ] Fireflies/particles animate
- [ ] Metallic silver materials
- [ ] Fog moves dynamically
- [ ] Hotspots visible through fog

**Preorder Gateway** (preorder-gateway):
- [ ] Portal shaders compile (no pink/magenta errors)
- [ ] Particle system runs
- [ ] Portal vortex animates
- [ ] Dusty pink/rose gold colors
- [ ] Camera auto-rotates (if enabled)
- [ ] Hotspots in portal rings

### Test 3: WebGL Compatibility

**DevTools Console**:
```javascript
// Check WebGL support
const canvas = document.createElement('canvas');
const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
console.log('WebGL Support:', gl ? 'YES' : 'NO');
console.log('WebGL Version:', gl.getParameter(gl.VERSION));
console.log('Renderer:', gl.getParameter(gl.RENDERER));
```

**Expected**:
- WebGL Support: YES
- WebGL Version: WebGL 1.0 or 2.0
- Renderer: (GPU name)

### Test 4: Performance Metrics

**DevTools Performance Tab**:
1. Start recording
2. Interact with 3D scene (rotate, zoom)
3. Stop after 10 seconds
4. Check metrics:

**Desktop Targets**:
- FPS: 60fps (no drops below 55fps)
- Frame Time: < 16.67ms
- GPU Usage: < 80%
- Memory: Stable (no leaks)

**Mobile Targets**:
- FPS: 30fps minimum
- Frame Time: < 33.33ms
- GPU Usage: < 90%

### Test 5: Product Hotspots

**Navigate to**: Any 3D collection page

**Test Hotspot Interaction**:
1. **Visual**: Hotspots appear as glowing spheres/markers
2. **Hover**: Hotspot highlights (color change or scale)
3. **Click**: Modal opens with product details
4. **Modal Content**:
   - Product name displays
   - Price displays
   - Description displays
   - Size options appear
   - "Add to Cart" button functional

**DevTools Console Check**:
```javascript
// Verify hotspot data loaded
console.log(window.productHotspots);
```

**Expected Output**:
```javascript
[
  {
    id: 1,
    name: "Product Name",
    price: "$XX.XX",
    position: {x: 0, y: 1.5, z: 0}
  },
  // ... more products
]
```

## 4.3 Special Collection Checks

### Signature Collection - Glass Materials
**Test**: Glass pavilion materials
**Check**: DevTools Console for shader compilation
**Expected**: No shader errors, glass appears translucent with reflections

### Love Hurts - Physics Simulation
**Test**: Rose petals falling
**Monitor**: FPS should stay at 60fps with 100+ particles
**Check**: DevTools Performance → Rendering → Paint Flashing
**Expected**: Green boxes around petals (GPU-accelerated)

### Black Rose - Volumetric Fog
**Test**: Fog density and movement
**Check**: Fog should obscure objects at distance
**Expected**: Fog animates smoothly (wind effect)
**Performance**: No FPS drops (fog is expensive)

### Preorder Gateway - Portal Shaders
**Test**: Custom GLSL shaders compile
**Check**: DevTools Console for shader errors
**Expected**: Portal has swirling gradient effect
**Fallback**: If shader fails, should show solid color (not pink/magenta)

## 4.4 Error Troubleshooting

### Error: "THREE is not defined"
**Cause**: Three.js CDN failed to load
**Fix**: Check internet connection, verify CDN URL
**Workaround**: Use local Three.js copy

### Error: "WebGL not supported"
**Cause**: Browser/GPU doesn't support WebGL
**Fix**: Update browser, enable hardware acceleration
**Workaround**: Show 2D fallback images

### Error: "Failed to compile shader"
**Cause**: GPU doesn't support shader complexity
**Fix**: Simplify shader code
**Workaround**: Use simpler materials

### Error: "Uncaught ReferenceError: OrbitControls"
**Cause**: Addon failed to load
**Fix**: Verify importmap includes addons path
**Check**: Network tab shows 404 for addon

### Error: Low FPS (< 30fps desktop)
**Cause**: Too many polygons or complex shaders
**Fix**: Reduce model complexity, disable post-processing
**Check**: DevTools Performance → GPU usage

## 4.5 Validation Checklist

### Three.js Core ✅
- [ ] Three.js 0.182.0 loads from unpkg
- [ ] No console errors on page load
- [ ] WebGLRenderer initializes
- [ ] Canvas element created

### Addons ✅
- [ ] OrbitControls.js loads
- [ ] GLTFLoader.js loads
- [ ] DRACOLoader.js loads (if used)

### Scene Rendering ✅
- [ ] 3D environment visible
- [ ] Camera controls work (rotate, zoom, pan)
- [ ] Lighting appears correct
- [ ] Materials render properly

### Performance ✅
- [ ] Desktop: 60fps sustained
- [ ] Mobile: 30fps minimum
- [ ] No memory leaks (10min test)
- [ ] GPU usage < 80%

### Product Hotspots ✅
- [ ] Hotspots appear in scene
- [ ] Hotspots interactive (click/hover)
- [ ] Modal opens with product data
- [ ] "Add to Cart" functional

### Collection-Specific ✅
- [ ] Signature: Glass materials + bloom
- [ ] Love Hurts: Rose petals physics
- [ ] Black Rose: Volumetric fog
- [ ] Preorder: Portal shaders

## 4.6 Automated Verification Script

**Run on Live Site** (Paste in DevTools Console):

```javascript
(async function verify3D() {
  const checks = {
    three: typeof THREE !== 'undefined',
    webgl: !!document.createElement('canvas').getContext('webgl'),
    scene: !!document.getElementById('scene'),
    renderer: !!window.renderer,
    camera: !!window.camera,
    controls: !!window.controls,
    hotspots: Array.isArray(window.productHotspots)
  };
  
  console.log('=== 3D Asset Verification ===');
  console.log('THREE.js loaded:', checks.three);
  if (checks.three) {
    console.log('THREE.js version:', THREE.REVISION);
  }
  console.log('WebGL supported:', checks.webgl);
  console.log('Scene canvas exists:', checks.scene);
  console.log('Renderer initialized:', checks.renderer);
  console.log('Camera initialized:', checks.camera);
  console.log('Controls initialized:', checks.controls);
  console.log('Hotspots loaded:', checks.hotspots);
  
  const passed = Object.values(checks).filter(v => v).length;
  const total = Object.keys(checks).length;
  
  console.log(`\n✅ Passed: ${passed}/${total} checks`);
  
  if (passed === total) {
    console.log('🎉 All 3D assets verified!');
  } else {
    console.log('⚠️ Some checks failed. Review errors above.');
  }
})();
```

**Expected Output**:
```
=== 3D Asset Verification ===
THREE.js loaded: true
THREE.js version: 182
WebGL supported: true
Scene canvas exists: true
Renderer initialized: true
Camera initialized: true
Controls initialized: true
Hotspots loaded: true

✅ Passed: 8/8 checks
🎉 All 3D assets verified!
```

## Next Steps

Once Phase 4 complete:
- **Phase 5**: Brand Styling Verification (CSS, colors, typography)
- **Phase 6**: WooCommerce Integration (create test products, test cart)
- **Phase 7**: Performance Testing (Lighthouse re-audit)

## Support

If any 3D checks fail, run automated script above and share output for diagnosis.

