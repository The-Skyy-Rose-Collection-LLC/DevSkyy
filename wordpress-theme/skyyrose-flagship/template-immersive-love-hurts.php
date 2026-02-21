<?php
/**
 * Template Name: Love Hurts — 3D Castle Experience
 * Template Post Type: page
 *
 * Immersive Three.js castle courtyard with rain, lightning,
 * product hotspots, and atmospheric dark romance.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<div id="love-hurts-experience" class="three-scene-wrapper">

	<!-- Loading Screen -->
	<div id="lh-loader" class="loading-overlay" style="background:#050510;z-index:1000">
		<div style="text-align:center">
			<div style="font-family:'Playfair Display',Georgia,serif;font-size:2rem;background:linear-gradient(180deg,#fff,#D4A5AD);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;animation:lhPulse 2s infinite">ENTERING CASTLE...</div>
		</div>
	</div>

	<!-- 3D Canvas Container -->
	<div id="lh-canvas-container" class="scene-container"></div>

	<!-- UI Overlay -->
	<div class="scene-ui-overlay">

		<!-- Collection Header -->
		<div style="position:absolute;top:2rem;left:50%;transform:translateX(-50%);text-align:center;pointer-events:none">
			<h1 style="font-family:'Playfair Display',Georgia,serif;font-size:3rem;background:linear-gradient(180deg,#fff,#D4A5AD);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0">Love Hurts</h1>
			<p style="letter-spacing:.3em;text-transform:uppercase;color:#D4A5AD;font-size:.8rem;margin-top:.5rem">Emotional &bull; Raw &bull; Broken</p>
		</div>

		<!-- Product Card (slides in from right) -->
		<div id="lh-product-card" style="position:fixed;right:-400px;top:50%;transform:translateY(-50%);width:350px;background:rgba(10,10,25,.9);border-left:1px solid #D4A5AD;padding:2rem;z-index:200;transition:right .5s ease;backdrop-filter:blur(15px)">
			<button onclick="document.getElementById('lh-product-card').style.right='-400px'" style="position:absolute;top:1rem;right:1rem;background:none;border:none;color:#fff;font-size:1.5rem;cursor:pointer">&times;</button>
			<h2 id="lh-p-title" style="font-family:'Playfair Display',Georgia,serif;font-size:1.8rem;margin:0 0 .5rem;color:#fff">Product Name</h2>
			<div id="lh-p-price" style="color:#D4A5AD;font-size:1.2rem;margin-bottom:1rem">$0.00</div>
			<p id="lh-p-desc" style="font-size:.9rem;line-height:1.6;color:#ccc;margin-bottom:2rem">Description goes here.</p>
			<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" style="display:block;width:100%;padding:1rem;background:#4B0082;border:none;color:#fff;text-transform:uppercase;letter-spacing:.2em;text-align:center;text-decoration:none;cursor:pointer">Pre-Order Now</a>
		</div>

		<!-- Navigation Controls -->
		<div style="position:absolute;bottom:3rem;left:50%;transform:translateX(-50%);display:flex;gap:1rem;pointer-events:auto">
			<button class="lh-nav-btn active" onclick="window.lhSetView('courtyard')" style="background:rgba(10,10,30,.6);border:1px solid rgba(255,255,255,.2);color:#ccc;padding:.8rem 1.5rem;cursor:pointer;text-transform:uppercase;letter-spacing:.1em;backdrop-filter:blur(5px);transition:all .3s">Courtyard</button>
			<button class="lh-nav-btn" onclick="window.lhSetView('hall')" style="background:rgba(10,10,30,.6);border:1px solid rgba(255,255,255,.2);color:#ccc;padding:.8rem 1.5rem;cursor:pointer;text-transform:uppercase;letter-spacing:.1em;backdrop-filter:blur(5px);transition:all .3s">Great Hall</button>
			<button class="lh-nav-btn" onclick="window.lhSetView('balcony')" style="background:rgba(10,10,30,.6);border:1px solid rgba(255,255,255,.2);color:#ccc;padding:.8rem 1.5rem;cursor:pointer;text-transform:uppercase;letter-spacing:.1em;backdrop-filter:blur(5px);transition:all .3s">Balcony</button>
		</div>

		<!-- Exit to Shop -->
		<a href="<?php echo esc_url( home_url( '/love-hurts-collection/' ) ); ?>" style="position:fixed;top:2rem;right:2rem;color:#fff;text-decoration:none;text-transform:uppercase;font-size:.8rem;letter-spacing:.1em;pointer-events:auto;z-index:100">Exit to Shop</a>

		<!-- Brand Logo -->
		<a href="<?php echo esc_url( home_url( '/' ) ); ?>" style="position:fixed;bottom:2rem;right:2rem;font-family:'Playfair Display',Georgia,serif;font-size:1rem;letter-spacing:.3em;color:#D4A5AD;opacity:.6;z-index:100;text-decoration:none;pointer-events:auto">SKYYROSE</a>

	</div>
</div>

<style>
@keyframes lhPulse{0%,100%{opacity:.6}50%{opacity:1}}
.lh-nav-btn:hover,.lh-nav-btn.active{border-color:#D4A5AD!important;color:#fff!important;box-shadow:0 0 15px rgba(212,165,173,.3)}
</style>

<script>
(function(){
	var im = document.createElement('script');
	im.type = 'importmap';
	im.textContent = JSON.stringify({imports:{"three":"https://unpkg.com/three@0.160.0/build/three.module.js","three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"}});
	document.currentScript.parentElement.insertBefore(im, document.currentScript);
})();
</script>

<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

let scene, camera, renderer, controls;
let rainGeo, rainCount = 15000;
let flash, rain;
const hotspots = [];

const products = [
	{ id:1, name:'Heartbreak Hoodie', price:'$195', desc:'Distressed cotton with hand-stitched broken heart patches.', pos:new THREE.Vector3(-3,2,0) },
	{ id:2, name:'Tears Tee', price:'$85', desc:'Oversized tee featuring puff-print tear graphics.', pos:new THREE.Vector3(3,2,0) },
	{ id:3, name:'Vow Ring', price:'$120', desc:'Sterling silver ring with a crack running through the band.', pos:new THREE.Vector3(0,1.5,4) }
];

init();
animate();

function init() {
	scene = new THREE.Scene();
	scene.fog = new THREE.FogExp2(0x050510, 0.03);

	camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 1, 1000);
	camera.position.set(0,5,15);

	renderer = new THREE.WebGLRenderer({ antialias:true });
	renderer.setSize(window.innerWidth, window.innerHeight);
	renderer.setClearColor(0x050510);
	document.getElementById('lh-canvas-container').appendChild(renderer.domElement);

	// Lighting
	scene.add(new THREE.AmbientLight(0x555555));
	const dir = new THREE.DirectionalLight(0x4B0082, 0.5);
	dir.position.set(0,20,10);
	scene.add(dir);
	flash = new THREE.PointLight(0x062d89, 30, 500, 1.7);
	flash.position.set(200,300,100);
	scene.add(flash);

	// Ground (wet pavement)
	const plane = new THREE.Mesh(
		new THREE.PlaneGeometry(100,100),
		new THREE.MeshStandardMaterial({ color:0x111111, roughness:0.1, metalness:0.8 })
	);
	plane.rotation.x = -Math.PI/2;
	scene.add(plane);

	// Castle Pillars
	const pillarGeo = new THREE.BoxGeometry(2,15,2);
	const pillarMat = new THREE.MeshStandardMaterial({ color:0x222222, roughness:0.9 });
	[[-10,-5],[10,-5],[-10,5],[10,5],[-5,-10],[5,-10]].forEach(p => {
		const pillar = new THREE.Mesh(pillarGeo, pillarMat);
		pillar.position.set(p[0], 7.5, p[1]);
		scene.add(pillar);
	});

	// Rain System
	rainGeo = new THREE.BufferGeometry();
	const rainPos = [];
	for (let i=0; i<rainCount; i++) {
		rainPos.push(Math.random()*400-200, Math.random()*500-250, Math.random()*400-200);
	}
	rainGeo.setAttribute('position', new THREE.Float32BufferAttribute(rainPos, 3));
	rain = new THREE.Points(rainGeo, new THREE.PointsMaterial({ color:0xaaaaaa, size:0.2, transparent:true, opacity:0.6 }));
	scene.add(rain);

	// Product Hotspots
	products.forEach(p => {
		const mesh = new THREE.Mesh(
			new THREE.SphereGeometry(0.3,16,16),
			new THREE.MeshBasicMaterial({ color:0xD4A5AD })
		);
		mesh.position.copy(p.pos);
		mesh.userData = { product:p };
		scene.add(mesh);
		hotspots.push(mesh);
		const ring = new THREE.Mesh(
			new THREE.RingGeometry(0.4,0.45,32),
			new THREE.MeshBasicMaterial({ color:0xD4A5AD, side:THREE.DoubleSide, transparent:true, opacity:0.5 })
		);
		ring.position.copy(p.pos);
		ring.lookAt(camera.position);
		scene.add(ring);
	});

	// Controls
	controls = new OrbitControls(camera, renderer.domElement);
	controls.enableDamping = true;
	controls.maxPolarAngle = Math.PI/2 - 0.1;
	controls.minDistance = 5;
	controls.maxDistance = 30;

	window.addEventListener('resize', onResize);
	window.addEventListener('click', onClick);

	// Remove loader
	setTimeout(() => {
		const loader = document.getElementById('lh-loader');
		loader.style.opacity = '0';
		loader.style.transition = 'opacity 1s';
		setTimeout(() => loader.remove(), 1000);
	}, 1000);
}

function onResize() {
	camera.aspect = window.innerWidth/window.innerHeight;
	camera.updateProjectionMatrix();
	renderer.setSize(window.innerWidth, window.innerHeight);
}

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

function onClick(e) {
	if (e.target.closest('.lh-nav-btn') || e.target.closest('#lh-product-card') || e.target.closest('a')) return;
	mouse.x = (e.clientX/window.innerWidth)*2-1;
	mouse.y = -(e.clientY/window.innerHeight)*2+1;
	raycaster.setFromCamera(mouse, camera);
	const intersects = raycaster.intersectObjects(hotspots);
	if (intersects.length > 0) {
		const p = intersects[0].object.userData.product;
		document.getElementById('lh-p-title').textContent = p.name;
		document.getElementById('lh-p-price').textContent = p.price;
		document.getElementById('lh-p-desc').textContent = p.desc;
		document.getElementById('lh-product-card').style.right = '0';
	} else {
		document.getElementById('lh-product-card').style.right = '-400px';
	}
}

window.lhSetView = function(type) {
	const targets = {
		courtyard: { pos:new THREE.Vector3(0,5,15), look:new THREE.Vector3(0,0,0) },
		hall: { pos:new THREE.Vector3(0,3,-5), look:new THREE.Vector3(0,5,-20) },
		balcony: { pos:new THREE.Vector3(15,10,0), look:new THREE.Vector3(0,0,0) }
	};
	const t = targets[type];
	if (t) { camera.position.copy(t.pos); controls.target.copy(t.look); }
	document.querySelectorAll('.lh-nav-btn').forEach(b => b.classList.remove('active'));
	event.target.classList.add('active');
};

function animate() {
	// Rain
	const positions = rain.geometry.attributes.position.array;
	for (let i=1; i<rainCount*3; i+=3) {
		positions[i] -= 0.5 + Math.random()*0.5;
		if (positions[i] < -100) positions[i] = 100;
	}
	rain.geometry.attributes.position.needsUpdate = true;

	// Lightning
	if (Math.random() > 0.97 || flash.power > 100) {
		if (flash.power < 100) flash.position.set(Math.random()*400, 300+Math.random()*200, 100);
		flash.power = 50 + Math.random()*500;
	} else {
		flash.power = Math.max(0, flash.power*0.95);
	}

	controls.update();
	renderer.render(scene, camera);
	requestAnimationFrame(animate);
}
</script>

<?php get_footer(); ?>
