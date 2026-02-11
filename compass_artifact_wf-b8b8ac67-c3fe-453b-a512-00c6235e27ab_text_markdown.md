# Production-Ready 3D Asset Generation for Luxury Fashion E-commerce

**TripoSR wins for speed at 0.5 seconds per generation with MIT licensing**, while **Hunyuan3D-2.1** offers the best quality-to-deployment balance with production PBR materials. For SkyyRose's WordPress/WooCommerce/Elementor stack, a hybrid architecture using Tripo3D API for low-volume (<3,000/month) and self-hosted Modal inference for scale delivers optimal cost efficiency at **$0.005-0.05 per 3D asset**.

The critical limitation for luxury fashion: **no existing models are trained on fabric-specific textures**. All current image-to-3D models struggle with leather grain, silk sheen, and metallic hardware—requiring post-processing texture enhancement or waiting for specialized fashion models like FabricDiffusion.

---

## Ranked model comparison reveals clear winners by use case

The landscape of image-to-3D models in December 2025 shows three distinct tiers for production deployment. Models were evaluated on inference speed (target <5 seconds), texture/color fidelity to source images, GLB output compatibility, and commercial licensing.

| Model | Speed | Quality | VRAM | GLB Native | License | Production Ready |
|-------|-------|---------|------|------------|---------|------------------|
| **TripoSR** | **0.5s** ⭐ | Good | 8 GB | ✅ Yes | MIT | ✅ Best for real-time |
| **Stable-Fast-3D** | **<1s** | Good+ | 8 GB | ✅ Yes | Community (<$1M) | ✅ With caveats |
| **Hunyuan3D-2.1** | ~10s | **Excellent** ⭐ | 10 GB | ✅ Yes | Custom Tencent | ✅ Best quality |
| **InstantMesh** | ~10s | Excellent | 16 GB | ⚠️ OBJ | Apache 2.0 | ✅ Production-ready |
| **LRM/OpenLRM** | ~5s | High | 16 GB | ⚠️ NeRF | CC-BY-NC | ❌ Non-commercial |
| **One-2-3-45++** | ~60s | High | 12 GB | ⚠️ Mesh | Research | ❌ Too slow |
| **Point-E** | 1-2 min | Low | 4 GB | ❌ Points | MIT | ❌ Quality insufficient |

**For SkyyRose's requirements**, the winning combination is **TripoSR for real-time preview** (sub-second generation while customers browse) and **Hunyuan3D-2.1 for final production assets** (10-second generation with PBR materials for realistic rendering of luxury products).

### Texture fidelity remains the critical challenge

All models exhibit a fundamental limitation: they "hallucinate" textures for occluded regions. Front-facing image quality is preserved, but back and side views degrade significantly. Research paper "FabricDiffusion" (SIGGRAPH Asia 2024) specifically notes that existing methods "struggle to capture and preserve texture details, particularly due to challenging occlusions, distortions, or poses."

For luxury fashion applications requiring **identical** reproduction of leather grain, fabric weave, or metallic finishes, consider:
- Post-generation texture enhancement pipeline
- Multi-view input when available (front + back product photos)
- Future: FabricDiffusion or Garment3DGen when production-ready

---

## HuggingFace ecosystem offers deployment-ready alternatives

The HuggingFace model hub contains **30+ image-to-3D models**, with the top options providing production APIs, consumer GPU compatibility, and commercial licensing. No fashion-specific 3D models exist—all are general-purpose object reconstruction.

**Top 5 HuggingFace models for luxury e-commerce:**

1. **Tencent Hunyuan3D-2.1** (755 likes, 300K downloads) — Best for luxury products with PBR material support (metallic, roughness) enabling realistic rendering of leather and metal hardware. Live demo space available. ~10GB VRAM requirement.

2. **Microsoft TRELLIS-image-large** (17.5M downloads) — Most downloaded model, MIT license for full commercial use, 100+ demo spaces. Structured 3D latents provide versatile output formats.

3. **Stability AI TripoSR** (590K downloads, MIT license) — Fastest option with official demo space. Based on LRM architecture, trained on 22 nodes × 8 A100 GPUs.

4. **TencentARC InstantMesh** (2.6M downloads, Apache 2.0) — Highest geometry quality through multiview diffusion. ~16GB VRAM for full pipeline.

5. **Stability AI Stable-Fast-3D** (86K downloads) — Sub-second generation with delighting step that neutralizes product photography lighting—ideal for consistent catalog appearance.

### Deployment patterns for WooCommerce integration

| Deployment Option | Setup Complexity | Cold Start | Cost Model |
|-------------------|------------------|------------|------------|
| HuggingFace Spaces (demo) | Low | Variable | Free tier limited |
| Self-hosted GPU (Modal/RunPod) | Medium | 2-4 seconds | Per-second billing |
| Tripo3D API | **Low** ⭐ | N/A | Per-credit |
| AWS SageMaker | High | Configurable | Per-hour |

**Recommendation**: Start with **Tripo3D API** for simplest integration, transition to **Modal self-hosted** when exceeding 3,000 generations/month.

---

## Infrastructure architecture balances cost and performance

### Cost per generation comparison

| Platform | Time/Gen | Cost/Gen | 1K/month | 10K/month |
|----------|----------|----------|----------|-----------|
| **Tripo3D Pro** | 10s | **$0.0053** ⭐ | $15.90* | $49.90** |
| Modal A100 | 10s | $0.006 | $6.00 | $60.00 |
| RunPod A100 | 10s | $0.005 | $5.00 | $50.00 |
| Replicate A100 | 10s | $0.015 | $15.00 | $150.00 |
| AWS SageMaker g5 | 10s | $0.006 | $6.00 + setup | $60.00 + setup |

*Pro plan includes 3,000 credits | **Advanced plan includes 8,000 credits

**Break-even analysis**: Tripo3D API wins below 3,000 generations/month. Self-hosted Modal/RunPod wins at 3,000-50,000/month. Enterprise requires negotiated contracts.

### Production architecture for SkyyRose

```
┌─────────────────────────────────────────────────────────────────────┐
│                     WOOCOMMERCE FRONTEND                            │
│  Elementor 3D Widget + model-viewer Web Component                   │
│  WebSocket connection for real-time generation progress             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────────────┐
│                      WORDPRESS API LAYER                            │
│  Custom REST endpoints: /wp-json/fashion/v1/3d-models/{sku}        │
│  WooCommerce product meta_data: _3d_model_url, _3d_model_low       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────┬───────────▼───────────┬──────────────────────────────┐
│   Redis      │    BullMQ Queue       │    PostgreSQL                │
│   Cache      │    + Rate Limiting    │    Asset Tracking            │
│   (hash →    │    (10 concurrent)    │    (generation history)      │
│   model URL) │                       │                              │
└──────┬───────┴───────────┬───────────┴──────────────────────────────┘
       │                   │
       │    ┌──────────────▼──────────────┐
       │    │    INFERENCE BACKEND        │
       │    │                             │
       │    │  Phase 1: Tripo3D API       │
       │    │  Phase 2: Modal self-hosted │
       │    │  (TripoSR + Hunyuan3D)      │
       │    └──────────────┬──────────────┘
       │                   │
┌──────▼───────────────────▼──────────────────────────────────────────┐
│                    CLOUDFLARE CDN + R2 STORAGE                      │
│  Cache-Control: public, max-age=31536000, immutable                 │
│  Content-Type: model/gltf-binary                                    │
│  Versioned URLs: /models/{hash}.glb                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### WebSocket streaming for generation progress

```javascript
// Frontend: Real-time progress during 3D generation
class ModelGenerationClient {
  constructor(wsEndpoint) {
    this.ws = new WebSocket(wsEndpoint);
  }

  async generateModel(productId, options = {}) {
    return new Promise((resolve, reject) => {
      const requestId = `gen_${Date.now()}_${productId}`;
      
      this.ws.send(JSON.stringify({
        type: 'generate_model',
        requestId,
        productId,
        quality: options.quality || 'high'
      }));

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.requestId !== requestId) return;

        switch (data.type) {
          case 'progress':
            options.onProgress?.({
              stage: data.stage,      // 'preprocessing', 'inference', 'postprocessing'
              percent: data.percent,
              message: data.message
            });
            break;
          case 'complete':
            resolve({ modelUrl: data.modelUrl, thumbnailUrl: data.thumbnailUrl });
            break;
          case 'error':
            reject(new Error(data.message));
            break;
        }
      };
    });
  }
}
```

---

## Three.js integration patterns for luxury product visualization

### Production-ready GLB loader with compression support

```javascript
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

class LuxuryProductViewer {
  constructor(container, renderer) {
    this.container = container;
    this.scene = new THREE.Scene();
    this.cache = new Map();
    
    // Configure loaders
    this.dracoLoader = new DRACOLoader();
    this.dracoLoader.setDecoderPath('https://www.gstatic.com/draco/v1/decoders/');
    
    this.ktx2Loader = new KTX2Loader();
    this.ktx2Loader.setTranscoderPath('/libs/basis/');
    this.ktx2Loader.detectSupport(renderer);
    
    this.gltfLoader = new GLTFLoader();
    this.gltfLoader.setDRACOLoader(this.dracoLoader);
    this.gltfLoader.setKTX2Loader(this.ktx2Loader);
    this.gltfLoader.setMeshoptDecoder(MeshoptDecoder);
  }

  async loadFromWooCommerce(productId) {
    // Fetch 3D asset URL from WooCommerce REST API
    const response = await fetch(`/wp-json/fashion/v1/3d-models/${productId}`);
    const data = await response.json();
    
    if (this.cache.has(data.glb_url)) {
      return this.cache.get(data.glb_url).clone();
    }

    const gltf = await this.gltfLoader.loadAsync(data.glb_url);
    this.cache.set(data.glb_url, gltf.scene);
    
    // Apply luxury lighting environment
    await this.setupLuxuryEnvironment();
    
    return gltf.scene;
  }

  async setupLuxuryEnvironment() {
    // Poly Haven studio HDRI for luxury product lighting
    const rgbeLoader = new RGBELoader();
    const texture = await rgbeLoader.loadAsync(
      'https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/studio_small_09_1k.hdr'
    );
    const envMap = this.pmremGenerator.fromEquirectangular(texture).texture;
    this.scene.environment = envMap;
    texture.dispose();
  }
}
```

### Progressive loading for mobile optimization

```javascript
class ProgressiveProductLoader {
  constructor(scene) {
    this.scene = scene;
    this.lodLevels = ['_low.glb', '_medium.glb', '_high.glb'];
    this.currentModel = null;
  }

  async loadProgressive(baseUrl, productId, onProgress) {
    // Show placeholder immediately
    const placeholder = this.createLoadingPlaceholder();
    this.scene.add(placeholder);
    onProgress?.({ stage: 'loading', percent: 0 });

    // Load low-poly first (<100KB, instant display)
    const lowPoly = await this.loadModel(`${baseUrl}/${productId}${this.lodLevels[0]}`);
    this.scene.remove(placeholder);
    this.scene.add(lowPoly);
    this.currentModel = lowPoly;
    onProgress?.({ stage: 'low-quality', percent: 33 });

    // Stream higher quality in background
    for (let i = 1; i < this.lodLevels.length; i++) {
      try {
        const higherLod = await this.loadModel(`${baseUrl}/${productId}${this.lodLevels[i]}`);
        await this.transitionModels(this.currentModel, higherLod);
        this.currentModel = higherLod;
        onProgress?.({ stage: i === 1 ? 'medium-quality' : 'high-quality', percent: 33 + (i * 33) });
      } catch (e) {
        console.log(`LOD ${i} unavailable, using current quality`);
        break;
      }
    }
  }

  async transitionModels(oldModel, newModel) {
    // Smooth crossfade between LOD levels
    return new Promise(resolve => {
      newModel.traverse(child => {
        if (child.material) {
          child.material.transparent = true;
          child.material.opacity = 0;
        }
      });
      
      this.scene.add(newModel);
      
      let opacity = 0;
      const fade = () => {
        opacity += 0.05;
        newModel.traverse(child => {
          if (child.material) child.material.opacity = Math.min(opacity, 1);
        });
        oldModel.traverse(child => {
          if (child.material) child.material.opacity = Math.max(1 - opacity, 0);
        });
        
        if (opacity < 1) {
          requestAnimationFrame(fade);
        } else {
          this.scene.remove(oldModel);
          this.disposeModel(oldModel);
          resolve();
        }
      };
      fade();
    });
  }
}
```

### Mobile optimization targets

| Device Tier | Polygon Budget | Texture Size | Draw Calls | File Size |
|-------------|----------------|--------------|------------|-----------|
| Low-end mobile | 50-100K | 512px | <20 | <2MB |
| Mid-range mobile | 200-300K | 1024px | <50 | <5MB |
| High-end mobile | 500-750K | 2048px | <100 | <10MB |
| Desktop | 1M+ | 4096px | <200 | <20MB |

---

## Custom Elementor widget provides full visual control

### Complete 3D viewer widget with camera/lighting controls

```php
<?php
/**
 * Plugin Name: SkyyRose 3D Viewer
 * Description: Custom Elementor widget for luxury fashion 3D product visualization
 */

class Luxury_3D_Viewer_Widget extends \Elementor\Widget_Base {
    public function get_name() { return 'luxury_3d_viewer'; }
    public function get_title() { return '3D Product Viewer'; }
    public function get_icon() { return 'eicon-image-box'; }
    public function get_categories() { return ['woocommerce-elements']; }

    protected function register_controls(): void {
        // MODEL SECTION
        $this->start_controls_section('model_section', [
            'label' => 'Model Settings',
            'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
        ]);
        
        $this->add_control('model_file', [
            'label' => 'GLB File',
            'type' => \Elementor\Controls_Manager::MEDIA,
            'media_types' => ['application/octet-stream'],
        ]);
        
        $this->add_control('woocommerce_product', [
            'label' => 'Or Select WooCommerce Product',
            'type' => \Elementor\Controls_Manager::SELECT2,
            'options' => $this->get_products_list(),
            'label_block' => true,
        ]);
        $this->end_controls_section();

        // CAMERA CONTROLS
        $this->start_controls_section('camera_section', [
            'label' => 'Camera Settings',
        ]);
        
        $this->add_control('auto_rotate', [
            'label' => 'Auto Rotate',
            'type' => \Elementor\Controls_Manager::SWITCHER,
            'default' => 'yes',
        ]);
        
        $this->add_control('rotation_speed', [
            'label' => 'Rotation Speed (deg/s)',
            'type' => \Elementor\Controls_Manager::SLIDER,
            'range' => ['deg' => ['min' => 5, 'max' => 120]],
            'default' => ['size' => 30],
            'condition' => ['auto_rotate' => 'yes'],
        ]);
        
        $this->add_control('camera_orbit', [
            'label' => 'Initial Camera Position',
            'type' => \Elementor\Controls_Manager::TEXT,
            'default' => '0deg 75deg 105%',
            'description' => 'Format: horizontal vertical distance',
        ]);
        $this->end_controls_section();

        // LIGHTING
        $this->start_controls_section('lighting_section', [
            'label' => 'Luxury Lighting',
        ]);
        
        $this->add_control('exposure', [
            'label' => 'Exposure',
            'type' => \Elementor\Controls_Manager::SLIDER,
            'range' => ['px' => ['min' => 0.1, 'max' => 3, 'step' => 0.1]],
            'default' => ['size' => 1],
        ]);
        
        $this->add_control('shadow_intensity', [
            'label' => 'Shadow Intensity',
            'type' => \Elementor\Controls_Manager::SLIDER,
            'range' => ['px' => ['min' => 0, 'max' => 2, 'step' => 0.1]],
            'default' => ['size' => 1],
        ]);
        
        $this->add_control('environment_preset', [
            'label' => 'Environment',
            'type' => \Elementor\Controls_Manager::SELECT,
            'options' => [
                'neutral' => 'Neutral Studio',
                'legacy' => 'Legacy',
                'apartment' => 'Apartment',
                'studio' => 'Photo Studio',
            ],
            'default' => 'neutral',
        ]);
        $this->end_controls_section();

        // RESPONSIVE STYLE
        $this->start_controls_section('style_section', [
            'label' => 'Viewer Style',
            'tab' => \Elementor\Controls_Manager::TAB_STYLE,
        ]);
        
        $this->add_responsive_control('viewer_height', [
            'label' => 'Height',
            'type' => \Elementor\Controls_Manager::SLIDER,
            'size_units' => ['px', 'vh'],
            'range' => ['px' => ['min' => 200, 'max' => 1000]],
            'default' => ['size' => 500, 'unit' => 'px'],
            'tablet_default' => ['size' => 400, 'unit' => 'px'],
            'mobile_default' => ['size' => 300, 'unit' => 'px'],
            'selectors' => ['{{WRAPPER}} model-viewer' => 'height: {{SIZE}}{{UNIT}};'],
        ]);
        $this->end_controls_section();
    }

    protected function render(): void {
        $s = $this->get_settings_for_display();
        
        // Get model URL from widget or WooCommerce product
        $model_url = $s['model_file']['url'] ?? '';
        if (empty($model_url) && !empty($s['woocommerce_product'])) {
            $model_url = get_post_meta($s['woocommerce_product'], '_3d_model_url', true);
        }
        if (empty($model_url)) return;
        ?>
        <model-viewer
            src="<?php echo esc_url($model_url); ?>"
            <?php if ($s['auto_rotate'] === 'yes'): ?>
                auto-rotate rotation-per-second="<?php echo $s['rotation_speed']['size']; ?>deg"
            <?php endif; ?>
            camera-controls touch-action="pan-y"
            camera-orbit="<?php echo esc_attr($s['camera_orbit']); ?>"
            exposure="<?php echo $s['exposure']['size']; ?>"
            shadow-intensity="<?php echo $s['shadow_intensity']['size']; ?>"
            environment-image="<?php echo $this->get_environment_url($s['environment_preset']); ?>"
            ar ar-modes="webxr scene-viewer quick-look"
            loading="lazy"
            style="width:100%;"
        ></model-viewer>
        <?php
    }
}
```

### WooCommerce product page integration

```php
<?php
// Add 3D model metabox to WooCommerce products
add_action('add_meta_boxes', function() {
    add_meta_box('skyyrose_3d_model', '3D Product Model', 'skyyrose_3d_metabox', 'product', 'side', 'high');
});

function skyyrose_3d_metabox($post) {
    wp_nonce_field('skyyrose_3d_save', 'skyyrose_3d_nonce');
    $model_url = get_post_meta($post->ID, '_3d_model_url', true);
    $replace_gallery = get_post_meta($post->ID, '_3d_replace_gallery', true);
    ?>
    <p>
        <input type="text" name="skyyrose_3d_url" id="skyyrose_3d_url" 
               value="<?php echo esc_attr($model_url); ?>" style="width:100%;">
        <button type="button" class="button" id="upload_3d_btn">Select GLB</button>
    </p>
    <p>
        <label>
            <input type="checkbox" name="skyyrose_3d_replace" value="1" 
                   <?php checked($replace_gallery, '1'); ?>>
            Replace product gallery with 3D viewer
        </label>
    </p>
    <?php
}

// Replace product gallery with 3D viewer when enabled
add_action('woocommerce_before_single_product_summary', function() {
    global $product;
    $model_url = get_post_meta($product->get_id(), '_3d_model_url', true);
    $replace = get_post_meta($product->get_id(), '_3d_replace_gallery', true);
    
    if ($model_url && $replace) {
        remove_action('woocommerce_before_single_product_summary', 'woocommerce_show_product_images', 20);
        echo skyyrose_3d_viewer($model_url, $product->get_id());
    }
}, 15);

function skyyrose_3d_viewer($model_url, $product_id) {
    $poster = get_the_post_thumbnail_url($product_id, 'woocommerce_single');
    return '<div class="skyyrose-3d-viewer">
        <model-viewer 
            src="' . esc_url($model_url) . '" 
            poster="' . esc_url($poster) . '"
            camera-controls auto-rotate loading="lazy" reveal="interaction"
            ar ar-modes="webxr scene-viewer quick-look"
            shadow-intensity="1" exposure="1" 
            style="width:100%;height:500px;">
        </model-viewer>
    </div>';
}

// Custom REST endpoint for 3D assets
add_action('rest_api_init', function() {
    register_rest_route('fashion/v1', '/3d-models/(?P<id>\d+)', [
        'methods' => 'GET',
        'callback' => function($request) {
            $product_id = $request->get_param('id');
            return [
                'glb_url' => get_post_meta($product_id, '_3d_model_url', true),
                'glb_low' => get_post_meta($product_id, '_3d_model_low', true),
                'thumbnail' => get_the_post_thumbnail_url($product_id, 'medium'),
                'color_variants' => get_post_meta($product_id, '_3d_color_variants', true) ?: [],
            ];
        },
        'permission_callback' => '__return_true',
    ]);
});

// Enable GLB/GLTF uploads
add_filter('upload_mimes', function($mimes) {
    $mimes['glb'] = 'model/gltf-binary';
    $mimes['gltf'] = 'model/gltf+json';
    return $mimes;
});
```

---

## Asset pipeline ensures production quality

### Post-processing workflow for ML-generated meshes

```bash
# Complete optimization pipeline using gltf-transform
# Input: ML-generated mesh (potentially large, unoptimized)
# Output: Production-ready GLB (<5MB, <100K triangles)

# Step 1: Validate input
gltf_validator input.glb -r -m

# Step 2: Decimate mesh (reduce polygon count)
gltf-transform simplify input.glb temp1.glb --ratio 0.5 --error 0.001

# Step 3: Optimize geometry (Draco or Meshopt compression)
gltf-transform draco temp1.glb temp2.glb --method edgebreaker

# Step 4: Compress textures to KTX2 for GPU efficiency
gltf-transform uastc temp2.glb temp3.glb --level 4 --zstd 18

# Step 5: Resize textures for web (1024x1024 max for mobile)
gltf-transform resize temp3.glb output.glb --width 1024 --height 1024

# Step 6: Final validation
gltf_validator output.glb -r -m
```

### Automated quality validation script

```javascript
// validate-asset.js - Run before CDN upload
const validator = require('gltf-validator');
const fs = require('fs');

async function validateForProduction(filepath, options = {}) {
  const maxFileSize = options.maxSize || 5 * 1024 * 1024; // 5MB default
  const maxTriangles = options.maxTriangles || 100000;
  
  const asset = fs.readFileSync(filepath);
  const report = await validator.validateBytes(new Uint8Array(asset));
  
  const stats = fs.statSync(filepath);
  const issues = [];
  
  // Check validation errors
  if (report.issues.numErrors > 0) {
    issues.push(`Validation errors: ${report.issues.numErrors}`);
  }
  
  // Check file size
  if (stats.size > maxFileSize) {
    issues.push(`File too large: ${(stats.size / 1024 / 1024).toFixed(2)}MB (max ${maxFileSize / 1024 / 1024}MB)`);
  }
  
  // Check triangle count
  if (report.info.totalTriangleCount > maxTriangles) {
    issues.push(`Too many triangles: ${report.info.totalTriangleCount} (max ${maxTriangles})`);
  }
  
  return {
    valid: issues.length === 0,
    issues,
    metrics: {
      fileSize: stats.size,
      triangles: report.info.totalTriangleCount,
      materials: report.info.materialCount,
      textures: report.info.textureCount,
    }
  };
}
```

### CDN configuration for GLB delivery

**Cloudflare recommended settings:**
```
# Page Rules for 3D assets
Match: *.glb, *.gltf
- Cache Level: Cache Everything
- Edge Cache TTL: 1 month
- Browser Cache TTL: 1 year
- Always Online: On (fallback for origin issues)
```

**Nginx origin headers:**
```nginx
location ~* \.(glb|gltf)$ {
    add_header Cache-Control "public, max-age=31536000, immutable";
    add_header Content-Type "model/gltf-binary";
    add_header Access-Control-Allow-Origin "*";
    
    gzip on;
    gzip_types model/gltf-binary model/gltf+json;
}
```

---

## Working test assets for development

### KhronosGroup glTF sample models

```javascript
// Production-ready test URLs for Three.js development
const TEST_MODELS = {
  // Simple geometry (fast loading)
  box: 'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Box/glTF-Binary/Box.glb',
  boxTextured: 'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/BoxTextured/glTF-Binary/BoxTextured.glb',
  
  // PBR materials (luxury product simulation)
  damagedHelmet: 'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/DamagedHelmet/glTF-Binary/DamagedHelmet.glb',
  metalRoughSpheres: 'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/MetalRoughSpheres/glTF-Binary/MetalRoughSpheres.glb',
  
  // Glass/transparent (luxury accessories)
  glassCandle: 'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/GlassHurricaneCandleHolder/glTF-Binary/GlassHurricaneCandleHolder.glb',
};

// Poly Haven HDRIs for luxury product lighting
const ENVIRONMENT_MAPS = {
  studioSoft: 'https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/studio_small_09_1k.hdr',
  studioNeutral: 'https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/studio_small_03_1k.hdr',
};
```

---

## Final recommendations for SkyyRose implementation

### Phase 1: MVP (Weeks 1-4)
- Integrate **Tripo3D API Pro** ($15.90/month, 3,000 generations)
- Deploy **model-viewer** web component via Elementor widget
- Store GLB URLs in WooCommerce **product meta_data**
- Use **Cloudflare CDN** for asset delivery

### Phase 2: Scale (Months 2-6)
- Migrate to **Modal self-hosted** for inference (when >3,000/month)
- Implement **progressive loading** (low → high quality)
- Add **Redis caching** for duplicate image detection (20-40% cost savings)
- Build **automated pipeline** with gltf-transform

### Phase 3: Premium (Months 6+)
- Evaluate **FabricDiffusion** for luxury fabric texture preservation
- Implement **multi-view input** for higher fidelity (front + back photos)
- Add **AR try-on** via model-viewer AR modes
- Consider fine-tuning on luxury product dataset

### Cost projection

| Volume | Infrastructure | Estimated Monthly Cost |
|--------|----------------|------------------------|
| 100/month | Tripo3D Pro | **$15.90** |
| 1,000/month | Tripo3D Pro | **$15.90** |
| 5,000/month | Tripo3D Advanced | **$49.90** |
| 10,000/month | Modal self-hosted | **$60.00** |
| 50,000/month | Modal + caching | **$200-300** |

The key trade-off remains **speed vs. fidelity**: TripoSR delivers 0.5-second generation but with texture degradation on occluded surfaces, while Hunyuan3D-2.1 provides PBR-quality output in 10 seconds. For luxury fashion where material authenticity matters, the 10-second wait for higher quality is likely worth it—especially when pre-generating assets for catalog products rather than real-time customer uploads.