import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

/* ═══ PRODUCT DATA ═══ */
const PRODUCTS = [
  { id:'br-001', name:'Thorn Hoodie', price:185, sku:'SR-BR-THORN-H', sizes:['S','M','L','XL','XXL'],
    desc:'Heavyweight 380gsm cotton fleece with gothic thorn embroidery along sleeves. Oversized silhouette with hidden rose-motif zipper pulls. Double-stitched seams. Oakland-made mentality.',
    pos: new THREE.Vector3(-4, 2.2, 3) },
  { id:'br-002', name:'Midnight Bomber', price:295, sku:'SR-BR-MID-J', sizes:['S','M','L','XL'],
    desc:'Premium satin bomber with hand-painted black rose motifs on rear panel. Quilted satin interior in crimson. Contrast stitching, ribbed cuffs, rose-gold hardware.',
    pos: new THREE.Vector3(4, 2, 2.5) },
  { id:'br-003', name:'Gothic Tee', price:75, sku:'SR-BR-GOTH-T', sizes:['S','M','L','XL','XXL'],
    desc:'300gsm heavyweight Supima cotton. Screen-printed thorn crown graphic with reflective ink detail. Raw hem, dropped shoulder, boxy fit. This is armor.',
    pos: new THREE.Vector3(-2.5, 1.8, -3) },
  { id:'br-004', name:'Chain Cargo', price:145, sku:'SR-BR-CHAIN-C', sizes:['28','30','32','34','36'],
    desc:'Relaxed cargo silhouette with detachable silver chain hardware. Waxed cotton blend in obsidian. Six utility pockets, adjustable ankle cuffs.',
    pos: new THREE.Vector3(3, 1.6, -2.5) }
];

const VIEWS = [
  { p: new THREE.Vector3(0, 5, 14), t: new THREE.Vector3(0, 1.5, 0) },
  { p: new THREE.Vector3(-8, 3, 6), t: new THREE.Vector3(0, 2, -2) },
  { p: new THREE.Vector3(0, 4, 1), t: new THREE.Vector3(0, 3, 0) },
  { p: new THREE.Vector3(0, 16, 0.1), t: new THREE.Vector3(0, 0, 0) }
];

let scene, camera, renderer, composer, controls, clock, particles;
let currentView = 0, animating = false;
const cart = [];
const hotspotEls = [];
let currentProduct = null;
let selectedSize = null;

/* ═══ INIT ═══ */
function init() {
  clock = new THREE.Clock();
  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x050005, 0.016);
  scene.background = new THREE.Color(0x030003);

  camera = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.1, 100);
  camera.position.copy(VIEWS[0].p);

  renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('scene'), antialias: true, powerPreference: 'high-performance' });
  renderer.setSize(innerWidth, innerHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.85;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.04;
  controls.enablePan = false;
  controls.maxPolarAngle = Math.PI * 0.52;
  controls.minDistance = 3;
  controls.maxDistance = 22;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.12;
  controls.target.copy(VIEWS[0].t);

  buildScene();
  buildPostProcessing();
  buildHotspots();
  initGrain();

  window.addEventListener('resize', onResize);
  renderer.setAnimationLoop(loop);
  simulateLoading();
}

/* ═══ BUILD 3D SCENE ═══ */
function buildScene() {
  const darkMat = new THREE.MeshStandardMaterial({ color: 0x1a0a15, metalness: 0.7, roughness: 0.3 });
  const crimsonMat = new THREE.MeshStandardMaterial({ color: 0xDC143C, emissive: 0x8B0000, emissiveIntensity: 0.4, metalness: 0.8, roughness: 0.2 });
  const thornMat = new THREE.MeshStandardMaterial({ color: 0x2a0a15, roughness: 0.6 });

  // Ground — dark ritual circle
  const ground = new THREE.Mesh(
    new THREE.CircleGeometry(30, 64),
    new THREE.MeshStandardMaterial({ color: 0x0a0008, metalness: 0.95, roughness: 0.12 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  // Cathedral pillars — 10 gothic columns
  for (let i = 0; i < 10; i++) {
    const angle = (i / 10) * Math.PI * 2;
    const radius = 8;
    const x = Math.cos(angle) * radius;
    const z = Math.sin(angle) * radius;

    // Column
    const pillar = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.22, 8, 8), darkMat);
    pillar.position.set(x, 4, z);
    pillar.castShadow = true;
    scene.add(pillar);

    // Capital
    const capital = new THREE.Mesh(new THREE.SphereGeometry(0.35, 8, 6, 0, Math.PI * 2, 0, Math.PI / 2), darkMat);
    capital.position.set(x, 8, z);
    scene.add(capital);

    // Base ornament
    const base = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.4, 0.15, 8), darkMat);
    base.position.set(x, 0.075, z);
    scene.add(base);
  }

  // Gothic arches between pillars
  for (let i = 0; i < 10; i++) {
    const a1 = (i / 10) * Math.PI * 2;
    const a2 = ((i + 1) / 10) * Math.PI * 2;
    const r = 8;
    const mid = (a1 + a2) / 2;

    const archCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(Math.cos(a1) * r, 7, Math.sin(a1) * r),
      new THREE.Vector3(Math.cos(mid) * (r - 0.8), 7.8, Math.sin(mid) * (r - 0.8)),
      new THREE.Vector3(Math.cos(a2) * r, 7, Math.sin(a2) * r)
    ]);
    scene.add(new THREE.Mesh(new THREE.TubeGeometry(archCurve, 16, 0.04, 6, false), thornMat));

    // Thorns along arches
    for (let t = 0; t < 6; t++) {
      const pt = archCurve.getPoint(t / 6 + 0.08);
      const thorn = new THREE.Mesh(new THREE.ConeGeometry(0.025, 0.12, 4), new THREE.MeshStandardMaterial({ color: 0x4a0a20 }));
      thorn.position.copy(pt);
      thorn.rotation.z = Math.random() * Math.PI;
      scene.add(thorn);
    }
  }

  // Blood Altar — center pedestal
  const altarBase = new THREE.Mesh(
    new THREE.CylinderGeometry(1.2, 1.5, 0.6, 8),
    new THREE.MeshStandardMaterial({ color: 0x0d0008, metalness: 0.9, roughness: 0.1 })
  );
  altarBase.position.y = 0.3;
  altarBase.castShadow = true;
  scene.add(altarBase);

  const altarTop = new THREE.Mesh(
    new THREE.CylinderGeometry(1, 1.2, 0.15, 8),
    new THREE.MeshStandardMaterial({ color: 0x1a0010, metalness: 0.95, roughness: 0.05 })
  );
  altarTop.position.y = 0.68;
  scene.add(altarTop);

  // Floating Black Rose — centerpiece
  const roseGroup = new THREE.Group();
  roseGroup.position.set(0, 3.5, 0);
  roseGroup.userData.core = true;

  const petalShape = new THREE.Shape();
  petalShape.moveTo(0, 0);
  petalShape.bezierCurveTo(0.3, 0.3, 0.3, 0.7, 0, 1);
  petalShape.bezierCurveTo(-0.3, 0.7, -0.3, 0.3, 0, 0);

  const extrudeSettings = { depth: 0.02, bevelEnabled: true, bevelThickness: 0.01, bevelSize: 0.01, bevelSegments: 2 };

  for (let layer = 0; layer < 4; layer++) {
    const petalCount = 5 + layer * 2;
    const radius = 0.15 + layer * 0.12;
    const height = 0.3 - layer * 0.06;

    for (let i = 0; i < petalCount; i++) {
      const angle = (i / petalCount) * Math.PI * 2;
      const petalGeo = new THREE.ExtrudeGeometry(petalShape, extrudeSettings);
      const petalMat = new THREE.MeshStandardMaterial({
        color: new THREE.Color().lerpColors(new THREE.Color(0x2a0010), new THREE.Color(0x0a0005), layer / 4),
        metalness: 0.4, roughness: 0.5, side: THREE.DoubleSide
      });
      const petal = new THREE.Mesh(petalGeo, petalMat);
      const scale = 0.2 + layer * 0.05;
      petal.scale.set(scale, scale, scale);
      petal.position.set(Math.cos(angle) * radius, height, Math.sin(angle) * radius);
      petal.rotation.y = -angle;
      petal.rotation.x = -0.3 - layer * 0.15;
      roseGroup.add(petal);
    }
  }

  // Rose center gem
  const centerGem = new THREE.Mesh(
    new THREE.SphereGeometry(0.08, 12, 12),
    crimsonMat
  );
  centerGem.position.y = 0.35;
  roseGroup.add(centerGem);

  // Stem
  const stemCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0.05, -0.5, 0.02),
    new THREE.Vector3(-0.02, -1.2, 0.01),
    new THREE.Vector3(0, -2, 0)
  ]);
  roseGroup.add(new THREE.Mesh(new THREE.TubeGeometry(stemCurve, 16, 0.015, 6, false), new THREE.MeshStandardMaterial({ color: 0x0a2a0a, roughness: 0.6 })));
  scene.add(roseGroup);

  // Scattered dark roses
  for (let i = 0; i < 20; i++) {
    const angle = Math.random() * Math.PI * 2;
    const r = 2 + Math.random() * 5;
    const miniRose = new THREE.Group();
    miniRose.position.set(Math.cos(angle) * r, 0.2 + Math.random() * 0.5, Math.sin(angle) * r);
    miniRose.scale.setScalar(0.25 + Math.random() * 0.35);

    for (let j = 0; j < 8; j++) {
      const ja = (j / 8) * Math.PI * 2;
      const petal = new THREE.Mesh(
        new THREE.SphereGeometry(0.12, 6, 6, 0, Math.PI),
        new THREE.MeshStandardMaterial({
          color: new THREE.Color().setHSL(0, Math.random() * 0.3 + 0.5, 0.04 + Math.random() * 0.06),
          metalness: 0.3, roughness: 0.5, side: THREE.DoubleSide
        })
      );
      petal.position.set(Math.cos(ja) * 0.1, 0.1 + j * 0.01, Math.sin(ja) * 0.1);
      petal.rotation.y = -ja;
      petal.rotation.x = -0.4;
      miniRose.add(petal);
    }
    scene.add(miniRose);
  }

  // Crimson light beam
  const beam = new THREE.Mesh(
    new THREE.CylinderGeometry(0.02, 0.15, 12, 8, 1, true),
    new THREE.MeshBasicMaterial({ color: 0xDC143C, transparent: true, opacity: 0.1, side: THREE.DoubleSide })
  );
  beam.position.y = 6.5;
  scene.add(beam);

  // Ritual rings
  for (let i = 0; i < 3; i++) {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(1.8 + i * 0.6, 0.012, 8, 48),
      new THREE.MeshBasicMaterial({ color: 0xDC143C, transparent: true, opacity: 0.12 - 0.025 * i })
    );
    ring.position.y = 3 + i * 0.8;
    ring.rotation.x = Math.PI / 2 + i * 0.15;
    ring.userData.ringSpeed = 0.15 + i * 0.05;
    ring.userData.ringIdx = i;
    scene.add(ring);
  }

  // Particle system — 6000 crimson dust motes
  const particleCount = 6000;
  const pGeo = new THREE.BufferGeometry();
  const pPositions = new Float32Array(particleCount * 3);
  const pColors = new Float32Array(particleCount * 3);

  for (let i = 0; i < particleCount; i++) {
    pPositions[i * 3] = (Math.random() - 0.5) * 30;
    pPositions[i * 3 + 1] = Math.random() * 15;
    pPositions[i * 3 + 2] = (Math.random() - 0.5) * 30;

    const color = Math.random() > 0.7 ? new THREE.Color(0xDC143C) : new THREE.Color(0x2a0a15);
    pColors[i * 3] = color.r;
    pColors[i * 3 + 1] = color.g;
    pColors[i * 3 + 2] = color.b;
  }

  pGeo.setAttribute('position', new THREE.BufferAttribute(pPositions, 3));
  pGeo.setAttribute('color', new THREE.BufferAttribute(pColors, 3));

  particles = new THREE.Points(pGeo, new THREE.PointsMaterial({
    size: 0.05, vertexColors: true, transparent: true, opacity: 0.55,
    blending: THREE.AdditiveBlending, depthWrite: false
  }));
  scene.add(particles);

  // Lighting
  scene.add(new THREE.AmbientLight(0x1a0010, 0.35));

  const centerLight = new THREE.PointLight(0xDC143C, 2.5, 20);
  centerLight.position.set(0, 1, 0);
  centerLight.castShadow = true;
  centerLight.shadow.mapSize.set(1024, 1024);
  scene.add(centerLight);

  scene.add(Object.assign(new THREE.DirectionalLight(0x6060a0, 0.25), { position: new THREE.Vector3(-5, 12, 5) }));
  scene.add(Object.assign(new THREE.PointLight(0x8B0000, 1.5, 12), { position: new THREE.Vector3(-6, 4, -3) }));
  scene.add(Object.assign(new THREE.PointLight(0x4a0020, 1, 12), { position: new THREE.Vector3(6, 5, 3) }));

  const spotLight = new THREE.SpotLight(0xDC143C, 0.7, 15, Math.PI / 8, 0.6);
  spotLight.position.set(0, 10, 0);
  spotLight.target.position.set(0, 0, 0);
  scene.add(spotLight);
  scene.add(spotLight.target);
}

/* ═══ POST-PROCESSING ═══ */
function buildPostProcessing() {
  const renderTarget = new THREE.WebGLRenderTarget(innerWidth, innerHeight, { type: THREE.HalfFloatType });
  composer = new EffectComposer(renderer, renderTarget);
  composer.addPass(new RenderPass(scene, camera));
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 1.4, 0.5, 0.82));

  // Chromatic aberration
  composer.addPass(new ShaderPass({
    uniforms: { tDiffuse: { value: null }, amount: { value: 0.0012 } },
    vertexShader: 'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
    fragmentShader: 'uniform sampler2D tDiffuse;uniform float amount;varying vec2 vUv;void main(){vec2 d=amount*(vUv-.5);gl_FragColor=vec4(texture2D(tDiffuse,vUv+d).r,texture2D(tDiffuse,vUv).g,texture2D(tDiffuse,vUv-d).b,1.);}'
  }));

  // Vignette
  composer.addPass(new ShaderPass({
    uniforms: { tDiffuse: { value: null }, darkness: { value: 1.2 }, offset: { value: 1.0 } },
    vertexShader: 'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
    fragmentShader: 'uniform sampler2D tDiffuse;uniform float darkness;uniform float offset;varying vec2 vUv;void main(){vec4 c=texture2D(tDiffuse,vUv);vec2 u=(vUv-.5)*2.;gl_FragColor=vec4(c.rgb*clamp(1.-dot(u,u)*darkness+offset,0.,1.),c.a);}'
  }));

  composer.addPass(new OutputPass());
}

/* ═══ HOTSPOTS ═══ */
function buildHotspots() {
  const container = document.getElementById('hotspots');
  PRODUCTS.forEach((product, idx) => {
    const el = document.createElement('div');
    el.className = 'hotspot';
    el.innerHTML = `<div class="hs-ring"><div class="hs-core"></div></div><div class="hs-label">${product.name}<span>$${product.price}</span></div>`;
    el.addEventListener('click', () => openModal(idx));
    container.appendChild(el);
    hotspotEls.push(el);
  });
}

function updateHotspots() {
  PRODUCTS.forEach((product, idx) => {
    const el = hotspotEls[idx];
    const projected = product.pos.clone().project(camera);
    const x = (projected.x * 0.5 + 0.5) * innerWidth;
    const y = (-(projected.y * 0.5) + 0.5) * innerHeight;

    if (projected.z < 1 && x > -50 && x < innerWidth + 50 && y > -50 && y < innerHeight + 50) {
      el.style.display = 'block';
      el.style.left = (x - 26) + 'px';
      el.style.top = (y - 26) + 'px';
    } else {
      el.style.display = 'none';
    }
  });
}

/* ═══ MODAL ═══ */
function openModal(idx) {
  currentProduct = PRODUCTS[idx];
  selectedSize = null;
  document.getElementById('modalName').textContent = currentProduct.name;
  document.getElementById('modalPrice').textContent = '$' + currentProduct.price;
  document.getElementById('modalDesc').textContent = currentProduct.desc;

  const sizesEl = document.getElementById('modalSizes');
  sizesEl.innerHTML = currentProduct.sizes.map((s, i) =>
    `<button class="size-btn" onclick="selectSize(this,'${s}')">${s}</button>`
  ).join('');

  document.getElementById('modal').classList.add('open');
}
window.openModal = openModal;

function closeModal() {
  document.getElementById('modal').classList.remove('open');
  currentProduct = null;
}
window.closeModal = closeModal;

function selectSize(el, size) {
  selectedSize = size;
  document.querySelectorAll('.size-btn').forEach(b => b.classList.remove('sel'));
  el.classList.add('sel');
}
window.selectSize = selectSize;

function addFromModal() {
  if (!currentProduct) return;
  addToCart(currentProduct);
  closeModal();
}
window.addFromModal = addFromModal;

/* ═══ CART ═══ */
function addToCart(product) {
  const existing = cart.find(c => c.id === product.id);
  if (existing) existing.qty++;
  else cart.push({ ...product, qty: 1, size: selectedSize || product.sizes[1] });
  updateCartUI();
}

function removeFromCart(id) {
  const idx = cart.findIndex(c => c.id === id);
  if (idx > -1) cart.splice(idx, 1);
  updateCartUI();
}
window.removeFromCart = removeFromCart;

function updateCartUI() {
  const countEl = document.getElementById('cartCount');
  const total = cart.reduce((sum, item) => sum + item.qty, 0);
  countEl.textContent = total;
  countEl.classList.toggle('show', total > 0);

  const itemsEl = document.getElementById('cartItems');
  if (!cart.length) {
    itemsEl.innerHTML = '<div class="cart-empty">Your garden awaits its first bloom</div>';
  } else {
    itemsEl.innerHTML = cart.map(item =>
      `<div class="cart-item">
        <div class="cart-thumb"></div>
        <div class="cart-info">
          <div class="cart-name">${item.name}${item.qty > 1 ? ' × ' + item.qty : ''}</div>
          <div class="cart-price">$${item.price * item.qty}</div>
        </div>
        <button class="cart-remove" onclick="removeFromCart('${item.id}')">✕</button>
      </div>`
    ).join('');
  }
  document.getElementById('cartTotal').textContent = '$' + cart.reduce((s, c) => s + c.price * c.qty, 0);
}

function toggleCart() {
  document.getElementById('cart').classList.toggle('open');
}
window.toggleCart = toggleCart;

function checkout() {
  if (!cart.length) return;
  // WooCommerce integration
  if (typeof wp !== 'undefined' || document.querySelector('body.woocommerce')) {
    const items = cart.map(c => ({ id: c.sku, quantity: c.qty }));
    Promise.all(items.map(item =>
      fetch('/wp-json/wc/store/v1/cart/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Nonce': window.wcStoreApiNonce || '' },
        body: JSON.stringify({ id: item.id, quantity: item.quantity })
      })
    )).then(() => window.location.href = '/checkout')
      .catch(() => window.location.href = '/checkout');
  } else {
    alert('BLACK ROSE Order:\n' + cart.map(c => c.name + ' × ' + c.qty + ' = $' + (c.price * c.qty)).join('\n') + '\n\nTotal: $' + cart.reduce((s, c) => s + c.price * c.qty, 0));
  }
}
window.checkout = checkout;

function launchAR() {
  alert('AR Experience launching...\nRequires mobile device with ARCore/ARKit.\nFull AR preview coming in the Pre-Order Gateway.');
}
window.launchAR = launchAR;

/* ═══ VIEW TRANSITIONS ═══ */
function showView(idx) {
  if (animating || idx === currentView) return;
  animating = true;
  currentView = idx;

  document.querySelectorAll('.room-btn').forEach((btn, i) => btn.classList.toggle('active', i === idx));

  const target = VIEWS[idx];
  const startPos = camera.position.clone();
  const startTarget = controls.target.clone();
  const duration = 2400;
  const startTime = performance.now();

  function animate(now) {
    const elapsed = now - startTime;
    const t = Math.min(elapsed / duration, 1);
    // Cubic ease in-out
    const ease = t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;

    camera.position.lerpVectors(startPos, target.p, ease);
    controls.target.lerpVectors(startTarget, target.t, ease);
    controls.update();

    if (t < 1) requestAnimationFrame(animate);
    else animating = false;
  }
  requestAnimationFrame(animate);
}
window.showView = showView;

/* ═══ GRAIN OVERLAY ═══ */
function initGrain() {
  const canvas = document.getElementById('grain');
  const ctx = canvas.getContext('2d');
  canvas.width = 256;
  canvas.height = 256;
  (function draw() {
    const imageData = ctx.createImageData(256, 256);
    for (let i = 0; i < imageData.data.length; i += 4) {
      const v = Math.random() * 255;
      imageData.data[i] = imageData.data[i + 1] = imageData.data[i + 2] = v;
      imageData.data[i + 3] = 255;
    }
    ctx.putImageData(imageData, 0, 0);
    requestAnimationFrame(draw);
  })();
}

/* ═══ LOADING ═══ */
function simulateLoading() {
  let progress = 0;
  const fill = document.getElementById('loadFill');
  const interval = setInterval(() => {
    progress += Math.random() * 12 + 4;
    if (progress >= 100) {
      progress = 100;
      clearInterval(interval);
      setTimeout(() => {
        document.getElementById('loader').classList.add('done');
        ['nav', 'rooms', 'info', 'cta'].forEach(id => document.getElementById(id).classList.add('show'));
      }, 500);
    }
    fill.style.width = progress + '%';
  }, 180);
}

/* ═══ RESIZE ═══ */
function onResize() {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  composer.setSize(innerWidth, innerHeight);
}

/* ═══ RENDER LOOP ═══ */
function loop() {
  const t = clock.getElapsedTime();

  // Particle animation
  if (particles) {
    particles.rotation.y = t * 0.008;
    const pos = particles.geometry.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      pos.array[i * 3 + 1] += Math.sin(t + i) * 0.0008;
      if (pos.array[i * 3 + 1] > 15) pos.array[i * 3 + 1] = 0;
    }
    pos.needsUpdate = true;
  }

  // Scene traversal animations
  scene.traverse(obj => {
    if (obj.userData.ringSpeed) {
      obj.rotation.z = t * obj.userData.ringSpeed;
      if (obj.userData.ringIdx === 1) obj.rotation.x = Math.PI / 2 + Math.sin(t * 0.3) * 0.1;
    }
    if (obj.userData.core) {
      obj.rotation.y = t * 0.2;
      obj.position.y = 3.5 + Math.sin(t * 0.8) * 0.15;
    }
  });

  controls.update();
  updateHotspots();
  composer.render();
}

init();
