# Immersive Architect Validation Protocol

> Theme building validation for immersive e-commerce. Advisory guidance only.

## 5-Gate System

### Gate 1: Design
- WordPress theme hierarchy
- Namespaced functions (`immersive_*`)
- Hook-based architecture

### Gate 2: Security  
- `sanitize_*()` for inputs
- `esc_*()` for outputs
- Nonce verification
- Capability checks

### Gate 3: WooCommerce
- Official WC hooks
- HPOS compatible
- All product types supported

### Gate 4: Performance
- Conditional asset loading
- Deferred JS
- No N+1 queries

### Gate 5: Immersive
- Progressive enhancement
- Reduced-motion support
- Touch compatible
- Graceful fallbacks

## Status Format

```
✅ VERIFIED — All gates pass
⚠️ PARTIAL — [issue] → fixing
🛑 BLOCKED — [critical] → resolving first
```

## Usage

Reference this during theme development. Not a blocker.
