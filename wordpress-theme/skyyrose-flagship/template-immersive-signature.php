<?php
/**
 * Template Name: Signature — 3D Runway Experience
 * Template Post Type: page
 *
 * Immersive Three.js virtual runway with spotlights,
 * mannequins, paparazzi flashes, and product interaction.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<div id="signature-experience" class="three-scene-wrapper">

	<!-- Loading Curtain -->
	<div id="sig-curtain" style="position:fixed;inset:0;background:#000;z-index:999;display:flex;justify-content:center;align-items:center;transition:transform 1s cubic-bezier(.7,0,.3,1)">
		<div style="font-family:'Playfair Display',Georgia,serif;font-size:2rem;color:#D4AF37;letter-spacing:5px">SKYYROSE</div>
	</div>

	<!-- 3D Canvas Container -->
	<div id="sig-canvas-container" class="scene-container"></div>

	<!-- UI Overlay -->
	<div class="scene-ui-overlay">

		<!-- Header -->
		<div style="position:absolute;top:2rem;left:4rem;text-align:left;pointer-events:none">
			<div style="font-size:.8rem;letter-spacing:.4em;text-transform:uppercase;color:#fff;margin-bottom:.5rem">Fall/Winter 2025</div>
			<h1 style="font-family:'Playfair Display',Georgia,serif;font-size:4rem;margin:0;color:#D4AF37;letter-spacing:-2px;line-height:.9">SIGNATURE<br>RUNWAY</h1>
		</div>

		<!-- Camera Dock -->
		<div style="position:absolute;bottom:3rem;right:4rem;display:flex;flex-direction:column;gap:1rem;pointer-events:auto">
			<button class="sig-cam-btn" onclick="window.sigSetCam(1)" style="background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:#fff;width:50px;height:50px;border-radius:50%;cursor:pointer;transition:all .3s;display:flex;align-items:center;justify-content:center;font-size:1rem">1</button>
			<button class="sig-cam-btn" onclick="window.sigSetCam(2)" style="background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:#fff;width:50px;height:50px;border-radius:50%;cursor:pointer;transition:all .3s;display:flex;align-items:center;justify-content:center;font-size:1rem">2</button>
			<button class="sig-cam-btn" onclick="window.sigSetCam(3)" style="background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:#fff;width:50px;height:50px;border-radius:50%;cursor:pointer;transition:all .3s;display:flex;align-items:center;justify-content:center;font-size:1rem">3</button>
		</div>

		<!-- Exit Link -->
		<a href="<?php echo esc_url( home_url( '/signature-collection/' ) ); ?>" style="position:fixed;top:2rem;right:4rem;color:#D4AF37;text-decoration:none;text-transform:uppercase;font-size:.8rem;letter-spacing:.2em;pointer-events:auto;border-bottom:1px solid #D4AF37;z-index:100">Exit Show</a>

		<!-- Product Panel (slides up from bottom) -->
		<div id="sig-product-panel" style="position:fixed;bottom:-300px;left:50%;transform:translateX(-50%);width:500px;max-width:90%;background:rgba(0,0,0,.8);border-top:2px solid #D4AF37;padding:2rem;z-index:200;transition:bottom .5s ease;backdrop-filter:blur(10px);text-align:center;pointer-events:auto">
			<button onclick="document.getElementById('sig-product-panel').style.bottom='-300px'" style="position:absolute;top:10px;right:15px;background:none;border:none;color:#555;cursor:pointer;font-size:1.2rem">&times;</button>
			<h2 id="sig-pp-title" style="font-family:'Playfair Display',Georgia,serif;font-size:2rem;color:#fff;margin:0">Foundation Blazer</h2>
			<div id="sig-pp-price" style="color:#D4AF37;font-size:1.2rem;margin:.5rem 0">$425</div>
			<p id="sig-pp-desc" style="color:#888;margin-bottom:1.5rem">Italian wool blend with gold button detailing. The piece that started it all.</p>
			<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" style="display:inline-block;padding:1rem 3rem;background:#fff;color:#000;border:none;text-transform:uppercase;font-weight:600;letter-spacing:2px;text-decoration:none;transition:background .3s">Pre-Order</a>
		</div>

		<!-- Brand Logo -->
		<a href="<?php echo esc_url( home_url( '/' ) ); ?>" style="position:fixed;bottom:2rem;left:4rem;font-family:'Playfair Display',Georgia,serif;font-size:1rem;letter-spacing:.3em;color:#D4AF37;opacity:.6;z-index:100;text-decoration:none;pointer-events:auto">SKYYROSE</a>

	</div>
</div>

<style>
.sig-cam-btn:hover{background:#D4AF37!important;border-color:#D4AF37!important;color:#000!important}
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
let spotlights = [];
const hotspots = [];

const models = [
	{ id:1, name:'Foundation Blazer', price:'$425', desc:'Italian wool blend with gold button detailing.', pos:new THREE.Vector3(0,1.5,-5) },
	{ id:2, name:'Silhouette Dress', price:'$350', desc:'Form-fitting architectural knitwear.', pos:new THREE.Vector3(0,1.5,0) },
	{ id:3, name:'Icon Trench', price:'$595', desc:'Water-resistant bonded cotton with signature gold lining.', pos:new THREE.Vector3(0,1.5,5) }
];

init();
animate();

function init() {
	scene = new THREE.Scene();
	scene.background = new THREE.Color(0x000000);
	scene.fog = new THREE.Fog(0x000000, 10, 50);

	camera = new THREE.PerspectiveCamera(50, window.innerWidth/window.innerHeight, 0.1, 100);
	camera.position.set(8,5,12);
	camera.lookAt(0,0,0);

	renderer = new THREE.WebGLRenderer({ antialias:true, alpha:false });
	renderer.setSize(window.innerWidth, window.innerHeight);
	renderer.shadowMap.enabled = true;
	renderer.shadowMap.type = THREE.PCFSoftShadowMap;
	document.getElementById('sig-canvas-container').appendChild(renderer.domElement);

	// Runway Floor
	const floor = new THREE.Mesh(
		new THREE.PlaneGeometry(8,40),
		new THREE.MeshStandardMaterial({ color:0x111111, roughness:0.1, metalness:0.5 })
	);
	floor.rotation.x = -Math.PI/2;
	floor.receiveShadow = true;
	scene.add(floor);

	// Side floors
	const sideMat = new THREE.MeshBasicMaterial({ color:0x050505 });
	const left = new THREE.Mesh(new THREE.PlaneGeometry(40,40), sideMat);
	left.rotation.x = -Math.PI/2; left.position.set(-24,-0.1,0);
	scene.add(left);
	const right = new THREE.Mesh(new THREE.PlaneGeometry(40,40), sideMat);
	right.rotation.x = -Math.PI/2; right.position.set(24,-0.1,0);
	scene.add(right);

	// Lighting
	scene.add(new THREE.AmbientLight(0x222222));
	for (let i=0; i<5; i++) {
		const spot = new THREE.SpotLight(0xffffff, 2);
		spot.position.set(i%2===0?-5:5, 10, -10+i*5);
		spot.angle = 0.5; spot.penumbra = 0.5; spot.decay = 2; spot.distance = 50;
		spot.castShadow = true;
		spot.target.position.set(0, 0, -10+i*5);
		scene.add(spot); scene.add(spot.target);
		spotlights.push(spot);
		const cone = new THREE.Mesh(
			new THREE.ConeGeometry(2,10,32,1,true),
			new THREE.MeshBasicMaterial({ color:0xffffff, transparent:true, opacity:0.03, side:THREE.DoubleSide })
		);
		cone.position.set(spot.position.x, spot.position.y-5, spot.position.z);
		cone.lookAt(spot.target.position);
		cone.rotation.x += Math.PI/2;
		scene.add(cone);
	}

	// Mannequins / Products
	const manGeo = new THREE.CylinderGeometry(0.5,0.5,3,16);
	manGeo.translate(0,1.5,0);
	const manMat = new THREE.MeshStandardMaterial({ color:0x333333, metalness:0.8, roughness:0.2 });
	models.forEach(m => {
		const mesh = new THREE.Mesh(manGeo, manMat);
		mesh.position.copy(m.pos);
		mesh.castShadow = true;
		mesh.userData = { data:m };
		scene.add(mesh);
		hotspots.push(mesh);
		const ring = new THREE.Mesh(
			new THREE.RingGeometry(0.8,0.85,32),
			new THREE.MeshBasicMaterial({ color:0xD4AF37, side:THREE.DoubleSide })
		);
		ring.position.set(m.pos.x, 0.1, m.pos.z);
		ring.rotation.x = -Math.PI/2;
		scene.add(ring);
	});

	// Paparazzi Flashes
	setInterval(() => {
		const fl = new THREE.PointLight(0xffffff, 5, 10);
		fl.position.set((Math.random()>.5?8:-8), Math.random()*3+1, Math.random()*20-10);
		scene.add(fl);
		setTimeout(() => scene.remove(fl), 100);
	}, 500);

	controls = new OrbitControls(camera, renderer.domElement);
	controls.enableDamping = true;
	controls.autoRotate = true;
	controls.autoRotateSpeed = 0.5;
	controls.maxPolarAngle = Math.PI/2 - 0.1;

	window.addEventListener('resize', onResize);
	window.addEventListener('click', onClick);

	// Open curtain
	setTimeout(() => {
		document.getElementById('sig-curtain').style.transform = 'translateY(-100%)';
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
	if (e.target.closest('button') || e.target.closest('a')) return;
	mouse.x = (e.clientX/window.innerWidth)*2-1;
	mouse.y = -(e.clientY/window.innerHeight)*2+1;
	raycaster.setFromCamera(mouse, camera);
	const intersects = raycaster.intersectObjects(hotspots);
	if (intersects.length > 0) {
		const d = intersects[0].object.userData.data;
		document.getElementById('sig-pp-title').textContent = d.name;
		document.getElementById('sig-pp-price').textContent = d.price;
		document.getElementById('sig-pp-desc').textContent = d.desc;
		document.getElementById('sig-product-panel').style.bottom = '0';
	} else {
		document.getElementById('sig-product-panel').style.bottom = '-300px';
	}
}

window.sigSetCam = function(view) {
	controls.autoRotate = false;
	if (view === 1) { camera.position.set(0,2,12); controls.target.set(0,1.5,0); }
	else if (view === 2) { camera.position.set(10,8,0); controls.target.set(0,0,0); }
	else { camera.position.set(0,5,-12); controls.target.set(0,1.5,0); }
};

function animate() {
	controls.update();
	renderer.render(scene, camera);
	requestAnimationFrame(animate);
}
</script>

<?php get_footer(); ?>
