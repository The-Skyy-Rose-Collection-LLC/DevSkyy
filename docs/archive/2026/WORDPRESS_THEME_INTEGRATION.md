# WordPress Theme Integration Guide

**Integration with**: Current SkyyRose.co Theme
**Backend API**: DevSkyy Imagery Pipeline

## Quick Start

### 1. API Endpoints
Base URL: `https://api.skyyrose.co/api/v1`

### 2. Authentication
```javascript
headers: {
  'Authorization': 'Bearer YOUR_JWT_TOKEN'
}
```

### 3. List Assets
```javascript
fetch('/api/v1/assets?collection=signature')
  .then(res => res.json())
  .then(data => console.log(data.assets));
```

### 4. Start 3D Generation
```javascript
fetch('/api/v1/pipeline/batch-generate', {
  method: 'POST',
  body: JSON.stringify({
    asset_ids: ['id1', 'id2'],
    provider: 'tripo',
    quality: 'high'
  })
});
```

### 5. 3D Viewer Integration
```html
<div class="skyyrose-3d-viewer" data-model="model.glb"></div>
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
```

## Full Documentation
See `/Users/coreyfoster/DevSkyy/docs/API_INTEGRATION.md`
