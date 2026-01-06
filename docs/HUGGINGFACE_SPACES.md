# HuggingFace Spaces Integration Guide

## Overview

DevSkyy integrates 5 custom HuggingFace Spaces to provide AI-powered tools for 3D conversion, image enhancement, training monitoring, and product analysis. These spaces are embedded in the frontend dashboard at `/ai-tools`.

---

## Architecture

```
Frontend (/ai-tools)
    ↓
HFSpaceCard Component (iframe embed)
    ↓
HuggingFace Spaces (Public)
    ├── 3D Model Converter
    ├── Flux Upscaler
    ├── LoRA Training Monitor
    ├── Product Analyzer
    └── Product Photography
```

---

## Configured Spaces

### 1. 3D Model Converter

**Purpose**: Convert between 3D model formats with optimization

- **Space ID**: `3d-converter`
- **URL**: https://huggingface.co/spaces/skyyrose/3d-converter
- **Category**: Conversion
- **Icon**: 🎲
- **Tags**: 3D, conversion, GLB, FBX, OBJ

**Features**:
- GLB ↔ FBX ↔ OBJ conversion
- Automatic mesh optimization
- Texture preservation
- File size reduction

**Use Cases**:
- Prepare 3D models for WooCommerce
- Convert customer uploads
- Optimize for web display

**Location**: `/Users/coreyfoster/DevSkyy/hf-spaces/3d-converter/`

---

### 2. Flux Upscaler

**Purpose**: AI-powered image upscaling and enhancement

- **Space ID**: `flux-upscaler`
- **URL**: https://huggingface.co/spaces/skyyrose/flux-upscaler
- **Category**: Generation
- **Icon**: 🔍
- **Tags**: image, upscaling, enhancement, AI

**Features**:
- 2x/4x/8x upscaling
- Detail enhancement
- Noise reduction
- Super-resolution AI

**Use Cases**:
- Enhance product images
- Upscale low-resolution uploads
- Improve image quality for marketing

**Location**: `/Users/coreyfoster/DevSkyy/hf-spaces/flux-upscaler/`

---

### 3. LoRA Training Monitor

**Purpose**: Real-time monitoring of LoRA model training

- **Space ID**: `lora-training-monitor`
- **URL**: https://huggingface.co/spaces/skyyrose/lora-training-monitor
- **Category**: Training
- **Icon**: 📊
- **Tags**: LoRA, training, monitoring, ML

**Features**:
- Training progress tracking
- Loss curve visualization
- Checkpoint management
- Resource utilization metrics

**Use Cases**:
- Monitor custom model training
- Track LoRA fine-tuning
- Debug training issues

**Location**: `/Users/coreyfoster/DevSkyy/hf-spaces/lora-training-monitor/`

---

### 4. Product Analyzer

**Purpose**: AI-powered product analysis and insights

- **Space ID**: `product-analyzer`
- **URL**: https://huggingface.co/spaces/skyyrose/product-analyzer
- **Category**: Analysis
- **Icon**: 🔬
- **Tags**: product, analysis, e-commerce, AI

**Features**:
- Product image analysis
- Quality assessment
- Attribute extraction
- Competitive insights

**Use Cases**:
- Analyze product listings
- Extract product attributes
- Quality control checks
- SEO optimization insights

**Location**: `/Users/coreyfoster/DevSkyy/hf-spaces/product-analyzer/`

---

### 5. Product Photography

**Purpose**: Generate professional product photos with AI

- **Space ID**: `product-photography`
- **URL**: https://huggingface.co/spaces/skyyrose/product-photography
- **Category**: Generation
- **Icon**: 📸
- **Tags**: product, photography, AI, generation

**Features**:
- Background removal
- Background generation
- Lighting enhancement
- Professional styling

**Use Cases**:
- Create product photos
- Generate lifestyle images
- Remove/replace backgrounds
- Enhance product presentation

**Location**: `/Users/coreyfoster/DevSkyy/hf-spaces/product-photography/`

---

## Frontend Integration

### Configuration File

**Location**: `/Users/coreyfoster/DevSkyy/frontend/lib/hf-spaces.ts`

```typescript
export interface HFSpace {
  id: string;                    // Unique identifier
  name: string;                  // Display name
  description: string;           // Short description
  url: string;                   // HuggingFace Space URL
  icon: string;                  // Emoji icon
  category: SpaceCategory;       // Category for filtering
  tags: string[];                // Search tags
}

export type SpaceCategory =
  | 'generation'
  | 'analysis'
  | 'training'
  | 'conversion';

export const HF_SPACES: HFSpace[] = [
  // ... 5 spaces configured
];
```

### UI Component

**Location**: `/Users/coreyfoster/DevSkyy/frontend/components/HFSpaceCard.tsx`

```typescript
interface HFSpaceCardProps {
  space: HFSpace;              // Space configuration
  fullscreen?: boolean;        // Fullscreen mode
  onToggleFullscreen?: () => void;
  className?: string;
}
```

**Features**:
- iframe embedding with sandbox
- Fullscreen toggle
- Refresh button
- Open in new tab
- Loading states
- Error handling

### Page Component

**Location**: `/Users/coreyfoster/DevSkyy/frontend/app/ai-tools/page.tsx`

**Features**:
- Tab navigation between spaces
- Category filtering
- Search functionality
- Grid view of all spaces
- Responsive layout (mobile/desktop)
- Dark mode support

**Routes**:
- `/ai-tools` - Main page
- `/ai-tools?space=3d-converter` - Direct link to specific space

---

## Security Configuration

### iframe Sandbox Attributes

```html
<iframe
  src="https://huggingface.co/spaces/skyyrose/..."
  sandbox="allow-scripts allow-same-origin allow-forms allow-downloads allow-popups allow-modals"
  allow="accelerometer; camera; microphone; clipboard-write"
/>
```

**Permissions**:
- ✅ `allow-scripts` - JavaScript execution
- ✅ `allow-same-origin` - Same-origin requests
- ✅ `allow-forms` - Form submission
- ✅ `allow-downloads` - File downloads
- ✅ `allow-popups` - Modal dialogs
- ✅ `allow-modals` - Alert/confirm dialogs
- ❌ `allow-top-navigation` - Prevent navigation hijacking

### CORS Configuration

HuggingFace Spaces must be configured to allow iframe embedding:

1. **X-Frame-Options**: Not set (or `ALLOWALL`)
2. **Content-Security-Policy**: Should allow embedding
3. **CORS Headers**: Should allow cross-origin requests

**Verification**:
```bash
# Check if space allows embedding
curl -I https://huggingface.co/spaces/skyyrose/3d-converter | grep -i "x-frame-options"

# Should NOT return "DENY" or "SAMEORIGIN"
```

---

## Adding New Spaces

### Step 1: Create HuggingFace Space

1. Go to https://huggingface.co/new-space
2. Configure space:
   - Owner: `skyyrose`
   - Name: `new-tool-name`
   - SDK: Gradio or Streamlit
   - Visibility: Public

3. Implement space functionality
4. Test space at `https://huggingface.co/spaces/skyyrose/new-tool-name`

### Step 2: Add to Frontend Configuration

Edit `/frontend/lib/hf-spaces.ts`:

```typescript
export const HF_SPACES: HFSpace[] = [
  // ... existing spaces ...
  {
    id: 'new-tool-name',
    name: 'New AI Tool',
    description: 'Description of what the tool does',
    url: 'https://huggingface.co/spaces/skyyrose/new-tool-name',
    icon: '🚀', // Choose appropriate emoji
    category: 'generation', // or 'analysis', 'training', 'conversion'
    tags: ['AI', 'relevant', 'keywords'],
  },
];
```

### Step 3: Update Category (if new)

If adding a new category, update:

```typescript
export const SPACE_CATEGORIES = [
  // ... existing categories ...
  { id: 'new-category', label: 'New Category', icon: '🆕' },
];
```

### Step 4: Test Integration

```bash
cd /Users/coreyfoster/DevSkyy/frontend

# Start development server
npm run dev

# Visit http://localhost:3000/ai-tools
# Verify new space appears in list
# Test iframe loading
# Test fullscreen mode
```

### Step 5: Deploy

```bash
# Build and deploy
npm run build
vercel --prod
```

---

## Troubleshooting

### Space Not Loading

**Symptoms**: Blank iframe or "refused to connect" error

**Possible Causes**:
1. Space is private (not public)
2. Space has X-Frame-Options: DENY
3. CORS restrictions
4. Space is down or building

**Solutions**:
```bash
# 1. Check space visibility
# Go to HuggingFace Space → Settings
# Ensure visibility is "Public"

# 2. Test space URL directly
curl -I https://huggingface.co/spaces/skyyrose/space-name

# 3. Check X-Frame-Options header
curl -I https://huggingface.co/spaces/skyyrose/space-name | grep -i "x-frame"

# 4. Check space status
# Visit space URL in browser
# Look for build logs or errors
```

### iframe Security Errors

**Symptoms**: Console errors about sandbox violations

**Solution**: Update sandbox attributes in `HFSpaceCard.tsx`:

```typescript
<iframe
  sandbox="allow-scripts allow-same-origin allow-forms allow-downloads"
  // Add more permissions if needed
/>
```

### Slow Loading

**Symptoms**: Spaces take long to load

**Solutions**:
1. **Lazy loading** (already implemented):
   ```html
   <iframe loading="lazy" />
   ```

2. **Optimize space**:
   - Reduce dependencies
   - Use smaller models
   - Enable caching

3. **CDN/Edge hosting**:
   - HuggingFace Spaces run on shared infrastructure
   - Consider upgrading to Spaces Pro for dedicated resources

### Space Not Found in List

**Symptoms**: Space doesn't appear in `/ai-tools`

**Check**:
1. Space is defined in `HF_SPACES` array
2. Space category matches filter
3. No TypeScript errors
4. Frontend rebuilt after changes

**Solution**:
```bash
# Rebuild frontend
cd /Users/coreyfoster/DevSkyy/frontend
npm run build

# Check for TypeScript errors
npm run type-check
```

---

## Performance Optimization

### 1. iframe Loading Strategy

```typescript
// Lazy load iframes for better performance
<iframe loading="lazy" />

// Only load selected space initially
{selectedSpace && <HFSpaceCard space={selectedSpace} />}
```

### 2. Caching

```typescript
// Cache space list with SWR
const { data: spaces } = useSWR('/api/spaces', fetcher, {
  revalidateOnFocus: false,
  dedupingInterval: 60000, // 1 minute
});
```

### 3. Preloading

```typescript
// Preload common spaces
<link rel="preconnect" href="https://huggingface.co" />
<link rel="dns-prefetch" href="https://huggingface.co" />
```

---

## Monitoring

### Usage Analytics

Track space usage via Vercel Analytics:

```typescript
// Track space selection
analytics.track('space_selected', {
  space_id: space.id,
  category: space.category,
  timestamp: new Date(),
});
```

### Error Tracking

```typescript
// Track iframe loading errors
useEffect(() => {
  const handleError = (e: ErrorEvent) => {
    if (e.target?.tagName === 'IFRAME') {
      errorTracking.capture('iframe_load_error', {
        space_id: space.id,
        error: e.message,
      });
    }
  };

  window.addEventListener('error', handleError);
  return () => window.removeEventListener('error', handleError);
}, [space.id]);
```

---

## Best Practices

### 1. Space Development

- ✅ Keep spaces simple and focused
- ✅ Use latest Gradio/Streamlit versions
- ✅ Test in different browsers
- ✅ Optimize model loading
- ✅ Provide clear error messages
- ❌ Don't use blocking operations
- ❌ Avoid large file uploads without progress

### 2. Frontend Integration

- ✅ Use lazy loading for iframes
- ✅ Provide loading states
- ✅ Handle errors gracefully
- ✅ Test on mobile devices
- ✅ Ensure accessibility
- ❌ Don't load all spaces at once
- ❌ Don't skip security attributes

### 3. User Experience

- ✅ Clear descriptions
- ✅ Relevant icons
- ✅ Intuitive categories
- ✅ Search functionality
- ✅ Fullscreen option
- ❌ Don't hide navigation
- ❌ Don't auto-play media

---

## API Reference

### `getSpaceById(id: string): HFSpace | undefined`

Get space configuration by ID.

```typescript
const space = getSpaceById('3d-converter');
```

### `getSpacesByCategory(category: string): HFSpace[]`

Filter spaces by category.

```typescript
const generationSpaces = getSpacesByCategory('generation');
```

### `searchSpaces(query: string): HFSpace[]`

Search spaces by name, description, or tags.

```typescript
const results = searchSpaces('image upscaling');
```

---

## Deployment Checklist

Before deploying new spaces:

- [ ] Space is public on HuggingFace
- [ ] Space URL works in browser
- [ ] Space allows iframe embedding
- [ ] Configuration added to `hf-spaces.ts`
- [ ] Icon and category are appropriate
- [ ] Tags are relevant
- [ ] TypeScript types are correct
- [ ] Local testing completed
- [ ] Build succeeds without errors
- [ ] Mobile responsive verified
- [ ] Accessibility checked
- [ ] Documentation updated

---

## Related Files

### Frontend
- `/frontend/lib/hf-spaces.ts` - Space configuration
- `/frontend/app/ai-tools/page.tsx` - Main page
- `/frontend/components/HFSpaceCard.tsx` - Embed component
- `/frontend/components/Navigation.tsx` - Navigation menu

### HuggingFace Spaces
- `/hf-spaces/3d-converter/` - 3D converter space
- `/hf-spaces/flux-upscaler/` - Upscaler space
- `/hf-spaces/lora-training-monitor/` - Training monitor
- `/hf-spaces/product-analyzer/` - Analyzer space
- `/hf-spaces/product-photography/` - Photography space

### Documentation
- `/docs/deployment/VERCEL_DEPLOYMENT_GUIDE.md` - Deployment guide
- `/docs/deployment/VERCEL_QUICK_START.md` - Quick start
- `/docs/HUGGINGFACE_SPACES.md` - This file

---

## Support

- **HuggingFace Docs**: https://huggingface.co/docs/hub/spaces
- **Gradio Docs**: https://gradio.app/docs/
- **Streamlit Docs**: https://docs.streamlit.io/
- **DevSkyy Issues**: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues

---

**Last Updated**: 2026-01-06
**Version**: 1.0.0
**Status**: Production Ready
