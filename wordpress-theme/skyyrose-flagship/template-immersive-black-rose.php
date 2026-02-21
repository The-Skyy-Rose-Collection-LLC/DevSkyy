<?php
/**
 * Template Name: Black Rose — 3D Garden Experience
 * Template Post Type: page
 *
 * Immersive Three.js garden with pillars, floating particles,
 * product hotspots, UnrealBloom post-processing.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<div id="black-rose-experience" class="three-scene-wrapper">

	<!-- Loading Screen -->
	<div id="loading-screen" class="loading-overlay" style="background:linear-gradient(135deg,#0a0505 0%,#1a0a0a 100%)">
		<div style="text-align:center">
			<div style="font-family:'Playfair Display',Georgia,serif;font-size:3rem;font-weight:600;letter-spacing:.3em;margin-bottom:2rem;background:linear-gradient(135deg,#DC143C,#B76E79);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;animation:brPulse 2s ease-in-out infinite">SKYYROSE</div>
			<div style="font-size:.9rem;letter-spacing:.5em;text-transform:uppercase;color:#C0C0C0;margin-bottom:3rem">Black Rose Collection</div>
			<div style="width:200px;height:2px;background:rgba(255,255,255,.1);border-radius:2px;overflow:hidden;margin:0 auto">
				<div id="br-loading-bar" style="height:100%;width:0%;background:linear-gradient(90deg,#8B0000,#DC143C);transition:width .3s ease"></div>
			</div>
		</div>
	</div>

	<!-- 3D Canvas Container -->
	<div id="br-canvas-container" class="scene-container"></div>

	<!-- UI Overlay -->
	<div class="scene-ui-overlay">

		<!-- Collection Header -->
		<div style="position:absolute;top:2rem;left:50%;transform:translateX(-50%);text-align:center;pointer-events:none">
			<h1 style="font-family:'Playfair Display',Georgia,serif;font-size:2.5rem;font-weight:600;letter-spacing:.2em;text-transform:uppercase;background:linear-gradient(180deg,#fff 0%,#C0C0C0 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0">Black Rose</h1>
			<p style="font-size:.85rem;letter-spacing:.4em;text-transform:uppercase;color:#DC143C;margin-top:.5rem">Dark Elegance &bull; Limited Edition</p>
		</div>

		<!-- Product Hotspots (positioned by JS) -->
		<div id="br-hotspots-container"></div>

		<!-- Product Card (slides in from right) -->
		<div id="br-product-card" style="position:fixed;right:-400px;top:50%;transform:translateY(-50%);width:350px;background:linear-gradient(135deg,rgba(10,5,5,.95),rgba(26,10,10,.95));border-left:1px solid #DC143C;padding:2rem;z-index:200;transition:right .5s cubic-bezier(.4,0,.2,1);backdrop-filter:blur(20px)">
			<button onclick="document.getElementById('br-product-card').style.right='-400px'" style="position:absolute;top:1rem;right:1rem;width:32px;height:32px;border:1px solid #C0C0C0;background:transparent;color:#C0C0C0;font-size:1.2rem;cursor:pointer;border-radius:50%">&times;</button>
			<span id="br-p-badge" style="display:inline-block;padding:.3rem .8rem;background:#8B0000;color:#fff;font-size:.7rem;letter-spacing:.15em;text-transform:uppercase;margin-bottom:1rem">Limited Edition</span>
			<div id="br-p-image" style="width:100%;height:200px;background:linear-gradient(45deg,#0a0505,#1a0a0a);border:1px solid rgba(220,20,60,.3);display:flex;align-items:center;justify-content:center;margin-bottom:1.5rem;font-size:4rem">&#x1F940;</div>
			<h2 id="br-p-title" style="font-family:'Playfair Display',Georgia,serif;font-size:1.5rem;font-weight:500;margin:0 0 .5rem;color:#fff">Thorn Hoodie</h2>
			<p id="br-p-price" style="font-size:1.25rem;color:#DC143C;margin-bottom:1rem">$185</p>
			<p id="br-p-desc" style="font-size:.9rem;color:#C0C0C0;line-height:1.6;margin-bottom:1.5rem">Premium heavyweight cotton hoodie with embroidered thorn details. Part of our limited BLACK ROSE collection.</p>
			<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" style="display:block;width:100%;padding:1rem;background:linear-gradient(135deg,#DC143C,#8B0000);border:none;color:#fff;font-size:.85rem;letter-spacing:.2em;text-transform:uppercase;text-align:center;text-decoration:none;cursor:pointer;transition:all .3s ease">Pre-Order Now</a>
		</div>

		<!-- Navigation Controls -->
		<div style="position:absolute;bottom:2rem;left:50%;transform:translateX(-50%);display:flex;gap:1rem;pointer-events:auto">
			<button class="br-nav-btn" data-view="garden" style="padding:.8rem 1.5rem;background:rgba(10,5,5,.8);border:1px solid #C0C0C0;color:#C0C0C0;font-size:.75rem;letter-spacing:.15em;text-transform:uppercase;cursor:pointer;backdrop-filter:blur(10px);transition:all .3s ease">Garden View</button>
			<button class="br-nav-btn" data-view="throne" style="padding:.8rem 1.5rem;background:rgba(10,5,5,.8);border:1px solid #C0C0C0;color:#C0C0C0;font-size:.75rem;letter-spacing:.15em;text-transform:uppercase;cursor:pointer;backdrop-filter:blur(10px);transition:all .3s ease">Throne View</button>
			<button class="br-nav-btn" data-view="altar" style="padding:.8rem 1.5rem;background:rgba(10,5,5,.8);border:1px solid #C0C0C0;color:#C0C0C0;font-size:.75rem;letter-spacing:.15em;text-transform:uppercase;cursor:pointer;backdrop-filter:blur(10px);transition:all .3s ease">Altar View</button>
		</div>

		<!-- Shop Collection Link -->
		<a href="<?php echo esc_url( home_url( '/black-rose-collection/' ) ); ?>" style="position:fixed;top:2rem;right:2rem;padding:.8rem 1.5rem;background:rgba(10,5,5,.9);border:1px solid #DC143C;color:#DC143C;font-size:.75rem;letter-spacing:.15em;text-transform:uppercase;text-decoration:none;z-index:100;backdrop-filter:blur(10px);transition:all .3s ease;pointer-events:auto">Shop Collection &rarr;</a>

		<!-- Brand Logo -->
		<a href="<?php echo esc_url( home_url( '/' ) ); ?>" style="position:fixed;bottom:2rem;right:2rem;font-family:'Playfair Display',Georgia,serif;font-size:1rem;letter-spacing:.3em;color:#C0C0C0;opacity:.6;z-index:100;text-decoration:none;pointer-events:auto">SKYYROSE</a>

	</div>
</div>

<style>
@keyframes brPulse{0%,100%{opacity:.8;transform:scale(1)}50%{opacity:1;transform:scale(1.02)}}
@keyframes brHotspotPulse{0%,100%{transform:scale(1);box-shadow:0 0 0 0 rgba(220,20,60,.4)}50%{transform:scale(1.1);box-shadow:0 0 20px 10px rgba(220,20,60,.2)}}
.br-hotspot{position:absolute;width:40px;height:40px;cursor:pointer;pointer-events:auto;transform:translate(-50%,-50%);z-index:50}
.br-hotspot-inner{width:100%;height:100%;border-radius:50%;background:radial-gradient(circle,#DC143C 0%,transparent 70%);border:2px solid #DC143C;animation:brHotspotPulse 2s ease-in-out infinite;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(4px)}
.br-hotspot-inner::before{content:'+';font-size:1.5rem;color:#fff;font-weight:300}
.br-nav-btn:hover,.br-nav-btn.active{background:#DC143C!important;border-color:#DC143C!important;color:#fff!important}
</style>

<?php /* Three.js importmap must be in head; we add via wp_head hook in the inline script below */ ?>
<script>
(function(){
	// Dynamically add import map before module loads
	var im = document.createElement('script');
	im.type = 'importmap';
	im.textContent = JSON.stringify({imports:{"three":"https://unpkg.com/three@0.160.0/build/three.module.js","three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"}});
	document.currentScript.parentElement.insertBefore(im, document.currentScript);
})();
</script>

<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

let scene, camera, renderer, controls, composer;
let particles, pillars = [], orbs = [];
let clock = new THREE.Clock();
let hotspots3D = [];

const products = {
	'thorn-hoodie': {
		title: 'Thorn Hoodie', price: '$185',
		description: 'Premium heavyweight cotton hoodie with embroidered thorn details. Part of our limited BLACK ROSE collection.',
		badge: 'Limited Edition', emoji: '\u{1F940}',
		position: new THREE.Vector3(-3, 1.5, 2)
	},
	'midnight-jacket': {
		title: 'Midnight Leather Jacket', price: '$295',
		description: 'Full-grain leather jacket with crimson satin lining. Hand-finished brass hardware.',
		badge: 'Exclusive', emoji: '\u{1F339}',
		position: new THREE.Vector3(3, 2, -2)
	},
	'gothic-tee': {
		title: 'Gothic Rose Tee', price: '$75',
		description: 'Oversized cotton tee with front and back rose graphic. Enzyme-washed for vintage feel.',
		badge: 'New Arrival', emoji: '\u{1F5A4}',
		position: new THREE.Vector3(0, 1, 4)
	}
};

const cameraViews = {
	garden: { position: new THREE.Vector3(0, 3, 8), target: new THREE.Vector3(0, 1, 0) },
	throne: { position: new THREE.Vector3(-6, 4, 0), target: new THREE.Vector3(0, 1, 0) },
	altar:  { position: new THREE.Vector3(0, 2, -6), target: new THREE.Vector3(0, 1, 2) }
};

init();
animate();

function init() {
	scene = new THREE.Scene();
	scene.background = new THREE.Color(0x0a0505);
	scene.fog = new THREE.FogExp2(0x0a0505, 0.06);

	camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
	camera.position.copy(cameraViews.garden.position);

	renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
	renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
	renderer.setSize(window.innerWidth, window.innerHeight);
	renderer.toneMapping = THREE.ACESFilmicToneMapping;
	renderer.toneMappingExposure = 0.8;
	document.getElementById('br-canvas-container').appendChild(renderer.domElement);

	controls = new OrbitControls(camera, renderer.domElement);
	controls.enableDamping = true;
	controls.dampingFactor = 0.05;
	controls.target.copy(cameraViews.garden.target);
	controls.minDistance = 3;
	controls.maxDistance = 15;
	controls.maxPolarAngle = Math.PI / 2;
	controls.autoRotate = true;
	controls.autoRotateSpeed = 0.3;

	setupLighting();
	createGround();
	createPillars();
	createCentralRose();
	createParticles();
	createHotspots();
	setupPostProcessing();

	window.addEventListener('resize', onWindowResize);
	setupNavigation();
	simulateLoading();
}

function setupLighting() {
	scene.add(new THREE.AmbientLight(0x1a0a0a, 0.5));
	const mainLight = new THREE.PointLight(0xDC143C, 2, 20);
	mainLight.position.set(0, 5, 0);
	scene.add(mainLight);
	const a1 = new THREE.PointLight(0x8B0000, 1.5, 15);
	a1.position.set(-5, 3, -5);
	scene.add(a1);
	const a2 = new THREE.PointLight(0x8B0000, 1.5, 15);
	a2.position.set(5, 3, 5);
	scene.add(a2);
	const rim = new THREE.PointLight(0xC0C0C0, 1, 12);
	rim.position.set(0, 8, -8);
	scene.add(rim);
	scene.add(new THREE.HemisphereLight(0x1a0505, 0x050202, 0.3));
}

function createGround() {
	const g = new THREE.Mesh(
		new THREE.PlaneGeometry(50, 50),
		new THREE.MeshStandardMaterial({ color: 0x0a0505, roughness: 0.2, metalness: 0.8 })
	);
	g.rotation.x = -Math.PI / 2;
	g.position.y = -0.5;
	g.receiveShadow = true;
	scene.add(g);
}

function createPillars() {
	const positions = [
		{x:-4,z:-4},{x:4,z:-4},{x:-4,z:4},{x:4,z:4},
		{x:-6,z:0},{x:6,z:0},{x:0,z:-6},{x:0,z:6}
	];
	positions.forEach((pos, i) => {
		const p = new THREE.Mesh(
			new THREE.CylinderGeometry(0.3, 0.4, 6, 16),
			new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.4, metalness: 0.6 })
		);
		p.position.set(pos.x, 2.5, pos.z);
		scene.add(p);
		pillars.push(p);
		const orb = new THREE.Mesh(
			new THREE.SphereGeometry(0.2, 32, 32),
			new THREE.MeshBasicMaterial({ color: 0xDC143C, transparent: true, opacity: 0.8 })
		);
		orb.position.set(pos.x, 5.8, pos.z);
		orb.userData.baseY = 5.8;
		orb.userData.phase = i * 0.5;
		scene.add(orb);
		orbs.push(orb);
		const ol = new THREE.PointLight(0xDC143C, 0.5, 4);
		ol.position.copy(orb.position);
		scene.add(ol);
	});
}

function createCentralRose() {
	const rg = new THREE.Group();
	const cols = [0xDC143C, 0x8B0000, 0x722F37, 0xB76E79];
	for (let l = 0; l < 5; l++) {
		const n = 5 + l, r = 0.3 + l * 0.15, h = 0.5 + l * 0.3;
		for (let p = 0; p < n; p++) {
			const a = (p / n) * Math.PI * 2;
			const petal = new THREE.Mesh(
				new THREE.TorusGeometry(r, 0.08, 8, 16, Math.PI),
				new THREE.MeshStandardMaterial({ color: cols[l % cols.length], roughness: 0.4, metalness: 0.3, side: THREE.DoubleSide })
			);
			petal.position.set(Math.cos(a) * r * 0.3, h, Math.sin(a) * r * 0.3);
			petal.rotation.set(Math.PI / 2 - l * 0.2, a, Math.random() * 0.3);
			rg.add(petal);
		}
	}
	const stem = new THREE.Mesh(
		new THREE.CylinderGeometry(0.05, 0.08, 2, 8),
		new THREE.MeshStandardMaterial({ color: 0x1a3a1a, roughness: 0.8 })
	);
	stem.position.y = -0.5;
	rg.add(stem);
	rg.position.set(0, 1.5, 0);
	scene.add(rg);
	const glow = new THREE.Mesh(
		new THREE.SphereGeometry(1.5, 32, 32),
		new THREE.MeshBasicMaterial({ color: 0xDC143C, transparent: true, opacity: 0.1 })
	);
	glow.position.copy(rg.position);
	scene.add(glow);
}

function createParticles() {
	const count = 3000;
	const pos = new Float32Array(count * 3);
	const cols = new Float32Array(count * 3);
	const velocities = [];
	const palette = [
		new THREE.Color(0xDC143C), new THREE.Color(0x8B0000),
		new THREE.Color(0xC0C0C0), new THREE.Color(0xB76E79), new THREE.Color(0x722F37)
	];
	for (let i = 0; i < count; i++) {
		const r = Math.random() * 15 + 2, a = Math.random() * Math.PI * 2, h = Math.random() * 10;
		pos[i*3] = Math.cos(a)*r; pos[i*3+1] = h; pos[i*3+2] = Math.sin(a)*r;
		const c = palette[Math.floor(Math.random() * palette.length)];
		cols[i*3] = c.r; cols[i*3+1] = c.g; cols[i*3+2] = c.b;
		velocities.push({ x:(Math.random()-.5)*.01, y:-Math.random()*.02-.005, z:(Math.random()-.5)*.01 });
	}
	const geo = new THREE.BufferGeometry();
	geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
	geo.setAttribute('color', new THREE.BufferAttribute(cols, 3));
	const mat = new THREE.PointsMaterial({ size: 0.1, vertexColors: true, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, sizeAttenuation: true });
	particles = new THREE.Points(geo, mat);
	particles.userData.velocities = velocities;
	scene.add(particles);
}

function createHotspots() {
	Object.entries(products).forEach(([id, product]) => {
		const marker = new THREE.Mesh(
			new THREE.SphereGeometry(0.15, 16, 16),
			new THREE.MeshBasicMaterial({ color: 0xDC143C, transparent: true, opacity: 0.8 })
		);
		marker.position.copy(product.position);
		marker.userData.productId = id;
		scene.add(marker);
		hotspots3D.push(marker);
		const ring = new THREE.Mesh(
			new THREE.RingGeometry(0.2, 0.25, 32),
			new THREE.MeshBasicMaterial({ color: 0xC0C0C0, transparent: true, opacity: 0.5, side: THREE.DoubleSide })
		);
		ring.position.copy(product.position);
		ring.rotation.x = -Math.PI / 2;
		scene.add(ring);
	});
}

function setupPostProcessing() {
	composer = new EffectComposer(renderer);
	composer.addPass(new RenderPass(scene, camera));
	composer.addPass(new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 0.8, 0.4, 0.2));
	composer.addPass(new OutputPass());
}

function animate() {
	requestAnimationFrame(animate);
	const time = clock.getElapsedTime();
	controls.update();
	orbs.forEach(o => {
		o.position.y = o.userData.baseY + Math.sin(time * 2 + o.userData.phase) * 0.1;
		o.material.opacity = 0.6 + Math.sin(time * 3 + o.userData.phase) * 0.2;
	});
	if (particles) {
		const pa = particles.geometry.attributes.position.array;
		const v = particles.userData.velocities;
		for (let i = 0; i < v.length; i++) {
			pa[i*3] += v[i].x; pa[i*3+1] += v[i].y; pa[i*3+2] += v[i].z;
			if (pa[i*3+1] < -0.5) {
				const r = Math.random()*15+2, a = Math.random()*Math.PI*2;
				pa[i*3] = Math.cos(a)*r; pa[i*3+1] = 10; pa[i*3+2] = Math.sin(a)*r;
			}
		}
		particles.geometry.attributes.position.needsUpdate = true;
		particles.rotation.y += 0.0002;
	}
	hotspots3D.forEach((m,i) => m.scale.setScalar(1 + Math.sin(time*3+i)*.1));
	composer.render();
	updateHotspotPositions();
}

function updateHotspotPositions() {
	const container = document.getElementById('br-hotspots-container');
	container.innerHTML = '';
	hotspots3D.forEach(marker => {
		const sp = marker.position.clone().project(camera);
		if (sp.z < 1) {
			const x = (sp.x*.5+.5)*window.innerWidth;
			const y = (-sp.y*.5+.5)*window.innerHeight;
			const el = document.createElement('div');
			el.className = 'br-hotspot';
			el.style.left = x+'px';
			el.style.top = y+'px';
			el.innerHTML = '<div class="br-hotspot-inner"></div>';
			el.onclick = () => showProduct(marker.userData.productId);
			container.appendChild(el);
		}
	});
}

function showProduct(id) {
	const p = products[id];
	if (!p) return;
	document.getElementById('br-p-badge').textContent = p.badge;
	document.getElementById('br-p-image').textContent = p.emoji;
	document.getElementById('br-p-title').textContent = p.title;
	document.getElementById('br-p-price').textContent = p.price;
	document.getElementById('br-p-desc').textContent = p.description;
	document.getElementById('br-product-card').style.right = '0';
	animateCameraTo(p.position.clone().add(new THREE.Vector3(2,1,2)), p.position);
}

function animateCameraTo(pos, target) {
	const sp = camera.position.clone(), st = controls.target.clone();
	const start = Date.now();
	controls.autoRotate = false;
	(function update() {
		const t = Math.min((Date.now()-start)/1000, 1);
		const e = 1 - Math.pow(1-t, 3);
		camera.position.lerpVectors(sp, pos, e);
		controls.target.lerpVectors(st, target, e);
		if (t < 1) requestAnimationFrame(update);
	})();
}

function setupNavigation() {
	document.querySelectorAll('.br-nav-btn').forEach(btn => {
		btn.addEventListener('click', () => {
			const v = cameraViews[btn.dataset.view];
			if (v) {
				animateCameraTo(v.position, v.target);
				document.querySelectorAll('.br-nav-btn').forEach(b => b.classList.remove('active'));
				btn.classList.add('active');
			}
		});
	});
}

function onWindowResize() {
	camera.aspect = window.innerWidth / window.innerHeight;
	camera.updateProjectionMatrix();
	renderer.setSize(window.innerWidth, window.innerHeight);
	composer.setSize(window.innerWidth, window.innerHeight);
}

function simulateLoading() {
	const bar = document.getElementById('br-loading-bar');
	let progress = 0;
	const interval = setInterval(() => {
		progress += Math.random() * 15;
		if (progress >= 100) {
			progress = 100;
			clearInterval(interval);
			setTimeout(() => {
				document.getElementById('loading-screen').classList.add('hidden');
			}, 500);
		}
		bar.style.width = progress + '%';
	}, 100);
}
</script>

<?php get_footer(); ?>
