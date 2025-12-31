# Draco Decoder Files

This directory should contain the Draco decoder files for loading compressed 3D models.

## Setup Instructions

### Option 1: Copy from three.js node_modules

```bash
# From project root
cp node_modules/three/examples/jsm/libs/draco/draco_decoder.js public/draco/
cp node_modules/three/examples/jsm/libs/draco/draco_decoder.wasm public/draco/
cp node_modules/three/examples/jsm/libs/draco/draco_wasm_wrapper.js public/draco/
```

### Option 2: Use CDN (modify loader path)

In your code, update the Draco decoder path to use a CDN:

```typescript
dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
```

### Option 3: Use three-stdlib (recommended)

The project already has `three-stdlib` installed which includes the decoder:

```typescript
import { DRACOLoader } from 'three-stdlib';
// Decoder is bundled
```

## Files Required (if using Option 1)

- `draco_decoder.js` - JavaScript decoder (fallback)
- `draco_decoder.wasm` - WebAssembly decoder (faster)
- `draco_wasm_wrapper.js` - WASM wrapper

## Usage

```typescript
import { getModelLoader } from '@/lib/ModelAssetLoader';

const loader = getModelLoader({
  dracoDecoderPath: '/draco/',  // Points to this directory
});

const model = await loader.load('/models/compressed-model.glb');
```
