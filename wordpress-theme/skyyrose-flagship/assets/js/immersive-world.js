/**
 * Immersive World Engine — Three.js powered collection experiences
 *
 * Replaces flat image-map hotspots with scroll-driven 3D worlds.
 * Progressive enhancement: falls back to immersive.js if WebGL unavailable.
 *
 * @package SkyyRose_Flagship
 * @since   4.2.0
 */

(function () {
  'use strict';

  /* ──────────────────────────────────────────────
     Feature Detection
     ────────────────────────────────────────────── */

  function supportsWebGL() {
    try {
      var c = document.createElement('canvas');
      return !!(window.WebGLRenderingContext &&
        (c.getContext('webgl') || c.getContext('experimental-webgl')));
    } catch (e) {
      return false;
    }
  }

  if (!supportsWebGL()) {
    console.log('[SkyyRose World] WebGL not supported — using 2D fallback');
    return; // Let immersive.js handle it
  }

  /* ──────────────────────────────────────────────
     Config
     ────────────────────────────────────────────── */

  var configEl = document.getElementById('world-config');
  if (!configEl) return;

  var config;
  try {
    config = JSON.parse(configEl.textContent);
  } catch (e) {
    console.error('[SkyyRose World] Invalid config JSON');
    return;
  }

  /* ──────────────────────────────────────────────
     Three.js Loader
     ────────────────────────────────────────────── */

  var THREE_CDN = 'https://cdn.jsdelivr.net/npm/three@0.172.0/build/three.module.min.js';
  var THREE;
  var scene, camera, renderer, clock;
  var container = document.getElementById('world-canvas');
  var scrollProgress = 0;
  var particleSystems = [];
  var productHotspots = [];
  var sceneLayers = [];
  var narrativePanels = [];
  var isInitialized = false;
  var rafId = null;

  // Hide the 2D fallback when 3D takes over
  var fallbackScene = document.querySelector('.immersive-scene');

  function loadThreeJS(callback) {
    // Check if Three.js already loaded globally
    if (window.THREE) {
      THREE = window.THREE;
      callback();
      return;
    }

    var script = document.createElement('script');
    script.type = 'module';
    script.textContent = 'import * as THREE from "' + THREE_CDN + '"; window.THREE = THREE; window.dispatchEvent(new Event("three-ready"));';
    document.head.appendChild(script);

    window.addEventListener('three-ready', function () {
      THREE = window.THREE;
      callback();
    }, { once: true });
  }

  /* ──────────────────────────────────────────────
     Initialization
     ────────────────────────────────────────────── */

  function init() {
    if (!container || !THREE) return;

    clock = new THREE.Clock();

    // Scene
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(config.bgColor || 0x0a0a0a, 0.015);

    // Camera
    camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 2, 8);

    // Renderer
    renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(renderer.domElement);

    // Lighting
    setupLighting();

    // Build the world
    buildSceneLayers();
    buildParticles();
    buildProductHotspots();
    buildNarrativePanels();

    // Events
    window.addEventListener('resize', onResize);
    window.addEventListener('scroll', onScroll, { passive: true });
    container.addEventListener('click', onClickRaycast);
    container.addEventListener('mousemove', onHoverRaycast);

    // Mobile gyroscope
    if (window.DeviceOrientationEvent && 'ontouchstart' in window) {
      window.addEventListener('deviceorientation', onGyroscope, { passive: true });
    }

    // Hide 2D fallback, show 3D
    if (fallbackScene) fallbackScene.style.display = 'none';
    container.classList.add('active');

    isInitialized = true;
    animate();

    // Dismiss loading screen
    var loading = document.querySelector('.scene-loading');
    if (loading) loading.classList.add('hidden');
  }

  /* ──────────────────────────────────────────────
     Lighting
     ────────────────────────────────────────────── */

  function setupLighting() {
    var ambient = new THREE.AmbientLight(0xffffff, 0.3);
    scene.add(ambient);

    // Main accent light
    var accentColor = new THREE.Color(config.accentColor || '#DC143C');
    var spot = new THREE.SpotLight(accentColor, 1.5, 50, Math.PI / 4, 0.8);
    spot.position.set(5, 10, 5);
    spot.castShadow = false;
    scene.add(spot);

    // Fill light
    var fill = new THREE.DirectionalLight(0xffffff, 0.4);
    fill.position.set(-3, 5, -2);
    scene.add(fill);

    // Rim/back light for drama
    var rim = new THREE.PointLight(accentColor, 0.6, 30);
    rim.position.set(0, 3, -10);
    scene.add(rim);
  }

  /* ──────────────────────────────────────────────
     Scene Layers (Parallax Depth)
     ────────────────────────────────────────────── */

  function buildSceneLayers() {
    if (!config.layers || !config.layers.length) return;

    var loader = new THREE.TextureLoader();

    config.layers.forEach(function (layer, i) {
      loader.load(layer.image, function (texture) {
        texture.colorSpace = THREE.SRGBColorSpace;

        // Calculate plane size to cover viewport at this depth
        var depth = layer.depth * -20; // Map 0-1 to 0 to -20 in Z
        var aspect = texture.image.width / texture.image.height;
        var height = 14 + (layer.depth * 6); // Farther = larger
        var width = height * aspect;

        var geo = new THREE.PlaneGeometry(width, height);
        var mat = new THREE.MeshBasicMaterial({
          map: texture,
          transparent: true,
          opacity: layer.opacity || 1,
          depthWrite: false,
          side: THREE.FrontSide,
        });

        var mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(0, height / 3, depth);
        mesh.userData.parallax = layer.parallax || 1;
        mesh.userData.baseY = mesh.position.y;
        mesh.userData.baseX = mesh.position.x;
        scene.add(mesh);
        sceneLayers.push(mesh);
      });
    });
  }

  /* ──────────────────────────────────────────────
     Particle Systems
     ────────────────────────────────────────────── */

  function buildParticles() {
    if (!config.particles || !config.particles.length) return;

    config.particles.forEach(function (p) {
      var count = p.count || 100;
      var positions = new Float32Array(count * 3);
      var velocities = new Float32Array(count * 3);
      var bounds = p.bounds || [10, 10, 10];

      for (var i = 0; i < count; i++) {
        positions[i * 3] = (Math.random() - 0.5) * bounds[0];
        positions[i * 3 + 1] = Math.random() * bounds[1];
        positions[i * 3 + 2] = (Math.random() - 0.5) * bounds[2];

        velocities[i * 3] = (Math.random() - 0.5) * p.speed * 0.5;
        velocities[i * 3 + 1] = -Math.random() * p.speed; // Fall
        velocities[i * 3 + 2] = (Math.random() - 0.5) * p.speed * 0.3;
      }

      var geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));

      var color = new THREE.Color(p.color || '#DC143C');
      var mat = new THREE.PointsMaterial({
        color: color,
        size: p.size || 0.05,
        transparent: true,
        opacity: p.opacity || 0.6,
        sizeAttenuation: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });

      var points = new THREE.Points(geo, mat);
      scene.add(points);
      particleSystems.push({
        mesh: points,
        velocities: velocities,
        bounds: bounds,
        speed: p.speed || 0.5,
        type: p.type,
      });
    });
  }

  function updateParticles(delta) {
    particleSystems.forEach(function (sys) {
      var pos = sys.mesh.geometry.attributes.position;
      var count = pos.count;
      var b = sys.bounds;

      for (var i = 0; i < count; i++) {
        var x = pos.getX(i) + sys.velocities[i * 3] * delta;
        var y = pos.getY(i) + sys.velocities[i * 3 + 1] * delta;
        var z = pos.getZ(i) + sys.velocities[i * 3 + 2] * delta;

        // Add gentle sine sway
        x += Math.sin(clock.elapsedTime * 0.5 + i) * 0.002;

        // Reset particles that fall below
        if (y < -1) {
          y = b[1];
          x = (Math.random() - 0.5) * b[0];
          z = (Math.random() - 0.5) * b[2];
        }

        // Wrap horizontally
        if (x > b[0] / 2) x = -b[0] / 2;
        if (x < -b[0] / 2) x = b[0] / 2;

        pos.setXYZ(i, x, y, z);
      }
      pos.needsUpdate = true;
    });
  }

  /* ──────────────────────────────────────────────
     Product Hotspots
     ────────────────────────────────────────────── */

  function buildProductHotspots() {
    if (!config.productPlacements || !config.products) return;

    var loader = new THREE.TextureLoader();

    config.productPlacements.forEach(function (placement) {
      var product = config.products.find(function (p) { return p.sku === placement.sku; });
      if (!product) return;

      // Create a glowing hotspot sphere
      var geo = new THREE.SphereGeometry(0.15, 16, 16);
      var accentColor = new THREE.Color(config.accentColor || '#DC143C');
      var mat = new THREE.MeshBasicMaterial({
        color: accentColor,
        transparent: true,
        opacity: 0.8,
      });

      var hotspot = new THREE.Mesh(geo, mat);
      hotspot.position.set(placement.position[0], placement.position[1], placement.position[2]);
      hotspot.userData.product = product;
      hotspot.userData.isHotspot = true;

      // Pulsing ring around hotspot
      var ringGeo = new THREE.RingGeometry(0.2, 0.25, 32);
      var ringMat = new THREE.MeshBasicMaterial({
        color: accentColor,
        transparent: true,
        opacity: 0.4,
        side: THREE.DoubleSide,
      });
      var ring = new THREE.Mesh(ringGeo, ringMat);
      ring.userData.pulseRing = true;
      hotspot.add(ring);

      scene.add(hotspot);
      productHotspots.push(hotspot);
    });
  }

  function updateHotspots(delta) {
    var pulse = Math.sin(clock.elapsedTime * 2) * 0.3 + 0.7;

    productHotspots.forEach(function (h) {
      // Gentle float
      h.position.y += Math.sin(clock.elapsedTime * 1.5 + h.position.x) * 0.001;

      // Pulse ring
      h.children.forEach(function (child) {
        if (child.userData.pulseRing) {
          child.scale.setScalar(pulse);
          child.material.opacity = 0.2 + pulse * 0.3;
        }
      });

      // Always face camera
      h.lookAt(camera.position);
    });
  }

  /* ──────────────────────────────────────────────
     Narrative Panels (HTML overlay)
     ────────────────────────────────────────────── */

  function buildNarrativePanels() {
    if (!config.narrativePanels) return;

    var overlay = document.getElementById('world-narrative');
    if (!overlay) return;

    config.narrativePanels.forEach(function (panel) {
      var el = document.createElement('div');
      el.className = 'narrative-panel narrative-' + panel.position + ' narrative-' + panel.style;
      el.dataset.trigger = panel.trigger;
      el.innerHTML = '<p class="narrative-text">' + panel.text + '</p>' +
        (panel.subtext ? '<p class="narrative-subtext">' + panel.subtext + '</p>' : '');
      overlay.appendChild(el);
      narrativePanels.push(el);
    });
  }

  function updateNarrativePanels() {
    narrativePanels.forEach(function (el) {
      var trigger = parseFloat(el.dataset.trigger);
      var distance = Math.abs(scrollProgress - trigger);
      var visible = distance < 0.08;
      var opacity = visible ? Math.max(0, 1 - distance / 0.08) : 0;

      el.style.opacity = opacity;
      el.style.transform = 'translateY(' + (visible ? 0 : 20) + 'px)';
    });
  }

  /* ──────────────────────────────────────────────
     Scroll-Driven Camera
     ────────────────────────────────────────────── */

  function onScroll() {
    var docHeight = document.documentElement.scrollHeight - window.innerHeight;
    scrollProgress = docHeight > 0 ? window.scrollY / docHeight : 0;
    scrollProgress = Math.max(0, Math.min(1, scrollProgress));
  }

  function updateCamera() {
    if (!config.cameraPath || config.cameraPath.length < 2) {
      // Default: gentle drift based on scroll
      camera.position.y = 2 + scrollProgress * -3;
      camera.position.z = 8 - scrollProgress * 6;
      camera.lookAt(0, 1 - scrollProgress * 2, -5);
      return;
    }

    // Interpolate between waypoints
    var path = config.cameraPath;
    var totalSegments = path.length - 1;
    var progressMapped = scrollProgress * totalSegments;
    var segIndex = Math.min(Math.floor(progressMapped), totalSegments - 1);
    var segT = progressMapped - segIndex;

    var from = path[segIndex];
    var to = path[segIndex + 1];

    // Smooth interpolation
    var t = smoothstep(segT);

    camera.position.x = lerp(from.position[0], to.position[0], t);
    camera.position.y = lerp(from.position[1], to.position[1], t);
    camera.position.z = lerp(from.position[2], to.position[2], t);

    var targetX = lerp(from.target[0], to.target[0], t);
    var targetY = lerp(from.target[1], to.target[1], t);
    var targetZ = lerp(from.target[2], to.target[2], t);
    camera.lookAt(targetX, targetY, targetZ);

    camera.fov = lerp(from.fov || 60, to.fov || 60, t);
    camera.updateProjectionMatrix();
  }

  function updateParallax() {
    sceneLayers.forEach(function (mesh) {
      var p = mesh.userData.parallax;
      mesh.position.y = mesh.userData.baseY + scrollProgress * p * -2;
      mesh.position.x = mesh.userData.baseX + Math.sin(scrollProgress * Math.PI) * p * 0.3;
    });
  }

  /* ──────────────────────────────────────────────
     Interaction (Raycasting)
     ────────────────────────────────────────────── */

  var raycaster = null;
  var mouse = new (function () { this.x = 0; this.y = 0; })();

  function initRaycaster() {
    if (!THREE) return;
    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();
  }

  function onClickRaycast(e) {
    if (!raycaster) initRaycaster();
    setMouse(e);
    raycaster.setFromCamera(mouse, camera);
    var hits = raycaster.intersectObjects(productHotspots, true);
    if (hits.length > 0) {
      var obj = hits[0].object;
      var product = obj.userData.product || (obj.parent && obj.parent.userData.product);
      if (product) openProductPanel(product);
    }
  }

  function onHoverRaycast(e) {
    if (!raycaster) initRaycaster();
    setMouse(e);
    raycaster.setFromCamera(mouse, camera);
    var hits = raycaster.intersectObjects(productHotspots, true);
    container.style.cursor = hits.length > 0 ? 'pointer' : 'default';
  }

  function setMouse(e) {
    var rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  }

  /* ──────────────────────────────────────────────
     Product Panel (reuse existing immersive panel)
     ────────────────────────────────────────────── */

  function openProductPanel(product) {
    var panel = document.querySelector('.product-panel');
    var overlay = document.querySelector('.product-panel-overlay');
    if (!panel || !overlay) return;

    var thumb = panel.querySelector('.product-panel-thumb img');
    var name = panel.querySelector('.product-panel-name');
    var price = panel.querySelector('.product-panel-price');
    var sizes = panel.querySelector('.product-panel-sizes');
    var btn = panel.querySelector('.btn-view-details');

    if (thumb) thumb.src = product.image || '';
    if (name) name.textContent = product.name || '';
    if (price) price.textContent = product.price ? '$' + product.price : '';
    if (sizes && product.sizes) {
      sizes.innerHTML = product.sizes.map(function (s) {
        return '<span class="size-chip">' + s + '</span>';
      }).join('');
    }
    if (btn && product.sku) {
      btn.href = '/?post_type=product&p=0&sku=' + product.sku;
    }

    panel.dataset.currentProductSku = product.sku || '';
    overlay.classList.add('visible');
    panel.classList.add('visible');
  }

  /* ──────────────────────────────────────────────
     Gyroscope (mobile tilt-to-explore)
     ────────────────────────────────────────────── */

  var gyroOffset = { x: 0, y: 0 };

  function onGyroscope(e) {
    if (!e.gamma || !e.beta) return;
    gyroOffset.x = (e.gamma / 90) * 0.5; // Left/right tilt
    gyroOffset.y = ((e.beta - 45) / 90) * 0.3; // Forward/back tilt
  }

  function applyGyroscope() {
    if (!gyroOffset.x && !gyroOffset.y) return;
    camera.position.x += (gyroOffset.x - camera.position.x * 0.1) * 0.02;
    camera.rotation.x += (gyroOffset.y * 0.1 - camera.rotation.x) * 0.02;
  }

  /* ──────────────────────────────────────────────
     Animation Loop
     ────────────────────────────────────────────── */

  function animate() {
    rafId = requestAnimationFrame(animate);
    var delta = clock.getDelta();

    updateCamera();
    updateParallax();
    updateParticles(delta);
    updateHotspots(delta);
    updateNarrativePanels();
    applyGyroscope();

    renderer.render(scene, camera);
  }

  /* ──────────────────────────────────────────────
     Window Events
     ────────────────────────────────────────────── */

  function onResize() {
    if (!camera || !renderer) return;
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }

  /* ──────────────────────────────────────────────
     Math Helpers
     ────────────────────────────────────────────── */

  function lerp(a, b, t) { return a + (b - a) * t; }
  function smoothstep(t) { return t * t * (3 - 2 * t); }

  /* ──────────────────────────────────────────────
     Cleanup
     ────────────────────────────────────────────── */

  function destroy() {
    if (rafId) cancelAnimationFrame(rafId);
    window.removeEventListener('resize', onResize);
    window.removeEventListener('scroll', onScroll);
    if (renderer) {
      renderer.dispose();
      if (renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
    }
  }

  // Expose for debugging
  window.skyyRoseWorld = {
    destroy: destroy,
    getScrollProgress: function () { return scrollProgress; },
    getConfig: function () { return config; },
  };

  /* ──────────────────────────────────────────────
     Boot
     ────────────────────────────────────────────── */

  loadThreeJS(init);

})();
