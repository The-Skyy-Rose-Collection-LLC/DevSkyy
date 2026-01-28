# 3D Web Development

This skill provides comprehensive knowledge of 3D web technologies for e-commerce. It activates when users mention "Three.js", "WebGL", "3D product viewer", "React Three Fiber", "virtual showroom", or need to add 3D elements to their themes.

---

## Three.js Fundamentals

### Basic Setup
```javascript
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

// Scene
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xffffff);

// Camera
const camera = new THREE.PerspectiveCamera(
  45,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);
camera.position.set(0, 0, 5);

// Renderer
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
document.body.appendChild(renderer.domElement);

// Controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
directionalLight.position.set(5, 5, 5);
scene.add(directionalLight);

// Animation loop
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
animate();
```

### Loading 3D Models
```javascript
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader';

const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('/draco/');

const gltfLoader = new GLTFLoader();
gltfLoader.setDRACOLoader(dracoLoader);

gltfLoader.load(
  '/models/product.glb',
  (gltf) => {
    const model = gltf.scene;
    model.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });
    scene.add(model);
  },
  (progress) => {
    console.log((progress.loaded / progress.total) * 100 + '% loaded');
  },
  (error) => {
    console.error('Error loading model:', error);
  }
);
```

## React Three Fiber

### Basic Setup
```jsx
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, useGLTF } from '@react-three/drei';

function App() {
  return (
    <Canvas
      camera={{ position: [0, 0, 5], fov: 45 }}
      gl={{ antialias: true }}
    >
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} />
      <Suspense fallback={<Loader />}>
        <Model />
        <Environment preset="studio" />
      </Suspense>
      <OrbitControls enablePan={false} />
    </Canvas>
  );
}

function Model() {
  const { scene } = useGLTF('/model.glb');
  return <primitive object={scene} />;
}
```

### Product Viewer Component
```jsx
import { Canvas } from '@react-three/fiber';
import {
  OrbitControls,
  Environment,
  ContactShadows,
  useGLTF,
  Html,
  useProgress
} from '@react-three/drei';

function Loader() {
  const { progress } = useProgress();
  return (
    <Html center>
      <div className="loader">{progress.toFixed(0)}%</div>
    </Html>
  );
}

function Product({ url, color }) {
  const { scene, materials } = useGLTF(url);

  useEffect(() => {
    if (materials && color) {
      Object.values(materials).forEach((material) => {
        if (material.color) material.color.set(color);
      });
    }
  }, [materials, color]);

  return <primitive object={scene} />;
}

export function ProductViewer({ modelUrl, selectedColor }) {
  return (
    <div className="product-viewer">
      <Canvas
        camera={{ position: [0, 0, 4], fov: 45 }}
        gl={{
          antialias: true,
          alpha: true,
          preserveDrawingBuffer: true
        }}
      >
        <ambientLight intensity={0.4} />
        <spotLight
          position={[10, 10, 10]}
          angle={0.15}
          penumbra={1}
          intensity={1}
        />

        <Suspense fallback={<Loader />}>
          <Product url={modelUrl} color={selectedColor} />
          <Environment preset="city" />
          <ContactShadows
            position={[0, -1.5, 0]}
            opacity={0.4}
            scale={10}
            blur={2}
          />
        </Suspense>

        <OrbitControls
          enablePan={false}
          minPolarAngle={Math.PI / 4}
          maxPolarAngle={Math.PI / 2}
          minDistance={2}
          maxDistance={6}
        />
      </Canvas>
    </div>
  );
}
```

## Product Configurator

```jsx
import { useState } from 'react';
import { ProductViewer } from './ProductViewer';

const colorOptions = [
  { name: 'Black', hex: '#000000' },
  { name: 'White', hex: '#ffffff' },
  { name: 'Navy', hex: '#1a365d' },
];

export function ProductConfigurator({ modelUrl }) {
  const [selectedColor, setSelectedColor] = useState(colorOptions[0].hex);

  return (
    <div className="configurator">
      <ProductViewer modelUrl={modelUrl} selectedColor={selectedColor} />

      <div className="color-picker">
        {colorOptions.map((color) => (
          <button
            key={color.name}
            className={`color-swatch ${selectedColor === color.hex ? 'active' : ''}`}
            style={{ backgroundColor: color.hex }}
            onClick={() => setSelectedColor(color.hex)}
            aria-label={`Select ${color.name}`}
          />
        ))}
      </div>
    </div>
  );
}
```

## WebGL Backgrounds

### Gradient Mesh
```javascript
const vertexShader = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const fragmentShader = `
  varying vec2 vUv;
  uniform vec3 uColor1;
  uniform vec3 uColor2;
  uniform float uTime;

  void main() {
    vec3 color = mix(uColor1, uColor2, vUv.y + sin(uTime * 0.5) * 0.1);
    gl_FragColor = vec4(color, 1.0);
  }
`;

const material = new THREE.ShaderMaterial({
  vertexShader,
  fragmentShader,
  uniforms: {
    uColor1: { value: new THREE.Color('#1a1a2e') },
    uColor2: { value: new THREE.Color('#16213e') },
    uTime: { value: 0 }
  }
});
```

## Performance Optimization

### Model Optimization
- Use Draco compression (reduces file size 90%+)
- Keep polygon count under 100k for mobile
- Use texture atlasing
- Implement LOD (Level of Detail)

### Rendering Optimization
```javascript
// Adaptive pixel ratio
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

// Frustum culling (enabled by default)
mesh.frustumCulled = true;

// Dispose unused resources
function cleanup() {
  geometry.dispose();
  material.dispose();
  texture.dispose();
}
```

### Mobile Optimization
```javascript
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

if (isMobile) {
  renderer.setPixelRatio(1);
  // Reduce shadow quality
  directionalLight.shadow.mapSize.width = 512;
  directionalLight.shadow.mapSize.height = 512;
}
```

## WordPress Integration

### Shortcode
```php
function product_3d_viewer_shortcode($atts) {
  $atts = shortcode_atts([
    'model' => '',
    'height' => '500px',
  ], $atts);

  wp_enqueue_script('product-3d-viewer');

  return sprintf(
    '<div class="product-3d-viewer" data-model="%s" style="height: %s;"></div>',
    esc_url($atts['model']),
    esc_attr($atts['height'])
  );
}
add_shortcode('product_3d', 'product_3d_viewer_shortcode');
```

## Fallbacks

```jsx
function ProductViewer({ modelUrl }) {
  const [webglSupported, setWebglSupported] = useState(true);

  useEffect(() => {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      setWebglSupported(!!gl);
    } catch (e) {
      setWebglSupported(false);
    }
  }, []);

  if (!webglSupported) {
    return <img src="/product-fallback.jpg" alt="Product" />;
  }

  return <Canvas>...</Canvas>;
}
```
