---
name: Immersive 3D Web Development
description: Use when working with 3D graphics, WebGL, Three.js, React Three Fiber, Babylon.js, WebXR, VR/AR experiences, shaders, physics engines, or any immersive web content. Triggers on keywords like "3d", "three.js", "webgl", "babylon", "r3f", "shader", "vr", "ar", "xr", "immersive", "scene", "mesh", "animation".
version: 1.0.0
---

# Immersive 3D Web Development

Expert knowledge for creating immersive 3D experiences on the web using Three.js, React Three Fiber, Babylon.js, and WebXR technologies.

## When to Use This Skill

Apply this skill when:
- Building 3D product configurators or visualizers
- Creating immersive web experiences (galleries, tours, showrooms)
- Developing WebXR applications (VR/AR)
- Implementing custom shaders or visual effects
- Optimizing 3D scene performance
- Working with 3D models (glTF, FBX, OBJ)
- Integrating physics simulations
- Creating interactive 3D environments

## Core Libraries

### Three.js (Foundation)
**Use for:** Low-level 3D control, maximum flexibility

**Key concepts:**
- Scene graph hierarchy (Scene → Camera → Objects)
- Geometries (BoxGeometry, SphereGeometry, BufferGeometry)
- Materials (MeshBasicMaterial, MeshStandardMaterial, ShaderMaterial)
- Lighting (AmbientLight, DirectionalLight, PointLight, SpotLight)
- Cameras (PerspectiveCamera, OrthographicCamera)
- Renderers (WebGLRenderer, WebGPURenderer)

**Example setup:**
```javascript
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

// Scene setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
document.body.appendChild(renderer.domElement);

// Controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
directionalLight.position.set(5, 10, 7.5);
scene.add(directionalLight);

// Animation loop
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
animate();
```

### React Three Fiber (R3F)
**Use for:** React integration, declarative 3D, component-based architecture

**Benefits:**
- Declarative syntax (JSX for 3D)
- React hooks integration
- Built-in resize handling
- Automatic disposal
- Better performance with React 18

**Example component:**
```jsx
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';

function ProductModel({ modelUrl }) {
  const gltf = useGLTF(modelUrl);

  return (
    <primitive
      object={gltf.scene}
      scale={1.5}
      position={[0, 0, 0]}
    />
  );
}

function Scene() {
  return (
    <Canvas shadows dpr={[1, 2]}>
      <PerspectiveCamera makeDefault position={[0, 0, 5]} />
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 10, 7.5]} intensity={0.8} castShadow />

      <ProductModel modelUrl="/models/product.glb" />

      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        minDistance={2}
        maxDistance={10}
      />
    </Canvas>
  );
}
```

### Babylon.js
**Use for:** Game-like experiences, complete engine, built-in physics

**Benefits:**
- Comprehensive game engine
- Built-in physics (Cannon.js, Ammo.js, Havok)
- Advanced animation system
- Scene optimizer
- Inspector for debugging

**Example:**
```javascript
import * as BABYLON from '@babylonjs/core';

const canvas = document.getElementById('renderCanvas');
const engine = new BABYLON.Engine(canvas, true);

const createScene = () => {
  const scene = new BABYLON.Scene(engine);

  const camera = new BABYLON.ArcRotateCamera(
    'camera',
    Math.PI / 2,
    Math.PI / 2,
    5,
    BABYLON.Vector3.Zero(),
    scene
  );
  camera.attachControl(canvas, true);

  const light = new BABYLON.HemisphericLight(
    'light',
    new BABYLON.Vector3(0, 1, 0),
    scene
  );

  // Load glTF model
  BABYLON.SceneLoader.ImportMesh(
    '',
    '/models/',
    'product.glb',
    scene,
    (meshes) => {
      // Model loaded
    }
  );

  return scene;
};

const scene = createScene();
engine.runRenderLoop(() => scene.render());
```

## Performance Optimization

### Level of Detail (LOD)
Swap models based on camera distance:

```javascript
import { LOD } from 'three';

const lod = new LOD();

// High detail (close)
lod.addLevel(highDetailMesh, 0);

// Medium detail
lod.addLevel(mediumDetailMesh, 50);

// Low detail (far)
lod.addLevel(lowDetailMesh, 100);

scene.add(lod);

// Update in animation loop
lod.update(camera);
```

### Instancing
Render many similar objects efficiently:

```javascript
import { InstancedMesh } from 'three';

const geometry = new THREE.BoxGeometry(1, 1, 1);
const material = new THREE.MeshStandardMaterial({ color: 0xB76E79 });

const count = 1000;
const mesh = new InstancedMesh(geometry, material, count);

// Set individual positions/rotations
const matrix = new THREE.Matrix4();
for (let i = 0; i < count; i++) {
  matrix.setPosition(
    Math.random() * 100 - 50,
    Math.random() * 100 - 50,
    Math.random() * 100 - 50
  );
  mesh.setMatrixAt(i, matrix);
}

mesh.instanceMatrix.needsUpdate = true;
scene.add(mesh);
```

### GPU Optimization
```javascript
// Texture compression
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader';

const ktx2Loader = new KTX2Loader();
ktx2Loader.setTranscoderPath('/basis/');
ktx2Loader.detectSupport(renderer);

// Load compressed texture
ktx2Loader.load('/textures/diffuse.ktx2', (texture) => {
  material.map = texture;
});

// Geometry compression
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';

const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('/draco/');

const gltfLoader = new GLTFLoader();
gltfLoader.setDRACOLoader(dracoLoader);
```

## Shaders & Custom Effects

### Custom Shader Material
```glsl
// Vertex Shader (vertex.glsl)
uniform float uTime;
varying vec2 vUv;
varying vec3 vNormal;

void main() {
  vUv = uv;
  vNormal = normalize(normalMatrix * normal);

  vec3 pos = position;
  pos.y += sin(position.x * 2.0 + uTime) * 0.1;

  gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
}

// Fragment Shader (fragment.glsl)
uniform vec3 uColor;
uniform float uTime;
varying vec2 vUv;
varying vec3 vNormal;

void main() {
  // Fresnel effect
  vec3 viewDirection = normalize(cameraPosition - vNormal);
  float fresnel = pow(1.0 - dot(viewDirection, vNormal), 3.0);

  // Animated gradient
  float gradient = sin(vUv.y * 10.0 + uTime) * 0.5 + 0.5;

  vec3 color = mix(uColor, vec3(1.0), fresnel * gradient);

  gl_FragColor = vec4(color, 1.0);
}
```

```javascript
import vertexShader from './vertex.glsl';
import fragmentShader from './fragment.glsl';

const shaderMaterial = new THREE.ShaderMaterial({
  uniforms: {
    uTime: { value: 0 },
    uColor: { value: new THREE.Color(0xB76E79) }
  },
  vertexShader,
  fragmentShader
});

// Update in animation loop
shaderMaterial.uniforms.uTime.value = elapsedTime;
```

## Physics Integration

### Cannon.js with React Three Fiber
```jsx
import { Physics, useBox, usePlane } from '@react-three/cannon';

function Box() {
  const [ref, api] = useBox(() => ({
    mass: 1,
    position: [0, 5, 0]
  }));

  return (
    <mesh ref={ref} castShadow>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color="orange" />
    </mesh>
  );
}

function Plane() {
  const [ref] = usePlane(() => ({
    rotation: [-Math.PI / 2, 0, 0]
  }));

  return (
    <mesh ref={ref} receiveShadow>
      <planeGeometry args={[100, 100]} />
      <meshStandardMaterial color="lightblue" />
    </mesh>
  );
}

function Scene() {
  return (
    <Canvas>
      <Physics gravity={[0, -9.8, 0]}>
        <Box />
        <Plane />
      </Physics>
    </Canvas>
  );
}
```

## WebXR (VR/AR)

### VR Setup with Three.js
```javascript
// Enable VR
renderer.xr.enabled = true;

// Add VR button
document.body.appendChild(VRButton.createButton(renderer));

// Controllers
const controller1 = renderer.xr.getController(0);
const controller2 = renderer.xr.getController(1);
scene.add(controller1, controller2);

// Use setAnimationLoop instead of requestAnimationFrame
renderer.setAnimationLoop(() => {
  renderer.render(scene, camera);
});
```

### AR with React Three Fiber
```jsx
import { ARButton, XR } from '@react-three/xr';

function ARScene() {
  return (
    <>
      <ARButton />
      <Canvas>
        <XR>
          <ambientLight intensity={0.5} />
          <mesh position={[0, 1, -2]}>
            <boxGeometry />
            <meshStandardMaterial color="red" />
          </mesh>
        </XR>
      </Canvas>
    </>
  );
}
```

## SkyyRose-Specific Patterns

### Luxury Product Viewer
```jsx
import { Canvas, useLoader } from '@react-three/fiber';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { Environment, ContactShadows } from '@react-three/drei';

function LuxuryProductViewer({ modelPath }) {
  const gltf = useLoader(GLTFLoader, modelPath);

  return (
    <Canvas camera={{ position: [0, 0, 5], fov: 45 }} shadows>
      {/* Rose gold environment lighting */}
      <Environment preset="sunset" />

      {/* Product model */}
      <primitive
        object={gltf.scene}
        scale={1.5}
        rotation={[0, Math.PI / 4, 0]}
      />

      {/* Soft shadows */}
      <ContactShadows
        position={[0, -1, 0]}
        opacity={0.4}
        scale={10}
        blur={2}
        far={4}
      />

      {/* Rose gold accent light */}
      <pointLight
        position={[5, 5, 5]}
        color="#B76E79"
        intensity={0.3}
      />

      <OrbitControls
        enableDamping
        minPolarAngle={Math.PI / 4}
        maxPolarAngle={Math.PI / 2}
      />
    </Canvas>
  );
}
```

## Best Practices

### Performance Targets
- **Desktop:** 60 FPS minimum
- **Mobile:** 30 FPS minimum
- **Draw calls:** < 100 per frame
- **Triangles:** < 100k visible
- **Textures:** Compressed (KTX2, Basis Universal)

### Model Optimization
1. **Decimate geometry** in Blender (target: < 50k triangles)
2. **Compress with Draco** for glTF files
3. **Use texture atlases** to reduce draw calls
4. **Bake lighting** for static objects
5. **LOD meshes** for far distances

### Memory Management
```javascript
// Dispose geometries and materials
geometry.dispose();
material.dispose();
texture.dispose();

// Dispose entire object tree
object.traverse((child) => {
  if (child.geometry) child.geometry.dispose();
  if (child.material) {
    if (Array.isArray(child.material)) {
      child.material.forEach(m => m.dispose());
    } else {
      child.material.dispose();
    }
  }
});
```

## Troubleshooting

### Black Screen
- Check camera position (not inside geometry)
- Verify lights are added to scene
- Check renderer size matches canvas

### Poor Performance
- Enable stats.js to measure FPS
- Check draw call count (renderer.info.render.calls)
- Use Chrome DevTools Performance profiler
- Reduce geometry complexity
- Use instancing for repeated objects

### Textures Not Loading
- Check file paths (case-sensitive)
- Verify CORS headers for external resources
- Use texture loading manager for progress
- Check texture size (power of 2 for mipmaps)

## References

See `references/` directory for:
- `threejs-fundamentals.md` - Three.js core concepts
- `r3f-patterns.md` - React Three Fiber patterns
- `babylonjs-guide.md` - Babylon.js complete guide
- `webxr-api.md` - WebXR specification and examples
- `shader-cookbook.md` - GLSL shader recipes
- `physics-integration.md` - Physics engine integration
- `performance-optimization.md` - 3D performance tuning

## Examples

See `examples/` directory for working implementations:
- `threejs-scene.js` - Basic Three.js setup
- `r3f-component.jsx` - React Three Fiber component
- `babylonjs-setup.js` - Babylon.js initialization
- `custom-shader.glsl` - Custom shader effects
- `physics-demo.js` - Physics simulation
- `xr-experience.js` - WebXR VR/AR example

## Scripts

See `scripts/` directory for utilities:
- `optimize-model.js` - glTF model optimization
- `compress-textures.sh` - Texture compression pipeline
- `benchmark-scene.js` - Performance benchmarking
