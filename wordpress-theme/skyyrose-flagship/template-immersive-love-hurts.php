<?php
/* Template Name: Immersive - Love Hurts */

defined( 'ABSPATH' ) || exit;

add_action( 'wp_enqueue_scripts', function () {
	wp_enqueue_style( 'skyyrose-love-hurts-experience', get_template_directory_uri() . '/assets/css/love-hurts-experience.css', array(), SKYYROSE_VERSION );
}, 20 );

/* ── WooCommerce Product Data ── */
$lh_products = array();

if ( class_exists( 'WooCommerce' ) ) {
	$product_map = array(
		'enchanted-rose-hoodie' => array(
			'fallback_title' => 'Enchanted Rose Hoodie',
			'fallback_price' => '$195',
			'desc'           => 'Heavyweight French terry hoodie with embroidered enchanted rose on back. Thorned vine detailing on sleeves. A tribute to what endures.',
			'room'           => 0,
			'screen_pos'     => array( 25, 55 ),
		),
		'beast-mode-tee' => array(
			'fallback_title' => 'Beast Mode Tee',
			'fallback_price' => '$85',
			'desc'           => 'Oversized cotton tee with distressed Beast silhouette. Water-based inks, vintage wash. Isolation made beautiful.',
			'room'           => 0,
			'screen_pos'     => array( 68, 48 ),
		),
		'thorned-heart-jacket' => array(
			'fallback_title' => 'Thorned Heart Jacket',
			'fallback_price' => '$345',
			'desc'           => 'Structured bomber with thorn-embossed leather panels. Crimson satin lining. Every boundary is a lesson.',
			'room'           => 1,
			'screen_pos'     => array( 18, 42 ),
		),
		'bloodline-crewneck' => array(
			'fallback_title' => 'Bloodline Crewneck',
			'fallback_price' => '$145',
			'desc'           => 'Midweight crewneck with HURTS gothic-letter chest print. Rose gold thread detailing. Heritage in every stitch.',
			'room'           => 1,
			'screen_pos'     => array( 72, 58 ),
		),
		'glass-dome-varsity' => array(
			'fallback_title' => 'Glass Dome Varsity',
			'fallback_price' => '$295',
			'desc'           => 'Wool-blend varsity jacket with crystal dome emblem. Gold chenille lettering. The crown jewel of the collection.',
			'room'           => 2,
			'screen_pos'     => array( 30, 50 ),
		),
		'last-petal-joggers' => array(
			'fallback_title' => 'Last Petal Joggers',
			'fallback_price' => '$135',
			'desc'           => 'Tapered joggers with falling-petal print down the leg. French terry, brushed interior. Comfort through the storm.',
			'room'           => 2,
			'screen_pos'     => array( 65, 52 ),
		),
	);

	$wc_query = new WP_Query( array(
		'post_type'      => 'product',
		'post_status'    => 'publish',
		'posts_per_page' => 20,
		'tax_query'      => array( array(
			'taxonomy' => 'product_cat',
			'field'    => 'slug',
			'terms'    => 'love-hurts',
		) ),
	) );

	$wc_products_by_slug = array();
	if ( $wc_query->have_posts() ) {
		while ( $wc_query->have_posts() ) {
			$wc_query->the_post();
			$wc_product = wc_get_product( get_the_ID() );
			if ( $wc_product ) {
				$wc_products_by_slug[ $wc_product->get_slug() ] = $wc_product;
			}
		}
		wp_reset_postdata();
	}

	foreach ( $product_map as $slug => $meta ) {
		$wc_product = isset( $wc_products_by_slug[ $slug ] ) ? $wc_products_by_slug[ $slug ] : null;

		$title     = $wc_product ? $wc_product->get_name() : $meta['fallback_title'];
		$price_raw = $wc_product ? $wc_product->get_price() : '';
		$price_fmt = $wc_product ? wp_strip_all_tags( wc_price( $wc_product->get_price() ) ) : $meta['fallback_price'];
		$image_url = $wc_product ? wp_get_attachment_url( $wc_product->get_image_id() ) : '';
		$permalink = $wc_product ? $wc_product->get_permalink() : '';
		$wc_id     = $wc_product ? $wc_product->get_id() : 0;

		$lh_products[] = array(
			'id'        => $slug,
			'wcId'      => $wc_id,
			'title'     => $title,
			'price'     => $price_fmt,
			'desc'      => $meta['desc'],
			'image'     => $image_url ? $image_url : '',
			'permalink' => $permalink,
			'room'      => $meta['room'],
			'screenPos' => $meta['screen_pos'],
		);
	}
} else {
	/* Fallback when WooCommerce is not active — reuse product_map structure */
	$product_map = array(
		'enchanted-rose-hoodie' => array( 'fallback_title' => 'Enchanted Rose Hoodie', 'fallback_price' => '$195', 'desc' => 'Heavyweight French terry hoodie with embroidered enchanted rose on back. Thorned vine detailing on sleeves. A tribute to what endures.', 'room' => 0, 'screen_pos' => array( 25, 55 ) ),
		'beast-mode-tee'        => array( 'fallback_title' => 'Beast Mode Tee', 'fallback_price' => '$85', 'desc' => 'Oversized cotton tee with distressed Beast silhouette. Water-based inks, vintage wash. Isolation made beautiful.', 'room' => 0, 'screen_pos' => array( 68, 48 ) ),
		'thorned-heart-jacket'  => array( 'fallback_title' => 'Thorned Heart Jacket', 'fallback_price' => '$345', 'desc' => 'Structured bomber with thorn-embossed leather panels. Crimson satin lining. Every boundary is a lesson.', 'room' => 1, 'screen_pos' => array( 18, 42 ) ),
		'bloodline-crewneck'    => array( 'fallback_title' => 'Bloodline Crewneck', 'fallback_price' => '$145', 'desc' => 'Midweight crewneck with HURTS gothic-letter chest print. Rose gold thread detailing. Heritage in every stitch.', 'room' => 1, 'screen_pos' => array( 72, 58 ) ),
		'glass-dome-varsity'    => array( 'fallback_title' => 'Glass Dome Varsity', 'fallback_price' => '$295', 'desc' => 'Wool-blend varsity jacket with crystal dome emblem. Gold chenille lettering. The crown jewel of the collection.', 'room' => 2, 'screen_pos' => array( 30, 50 ) ),
		'last-petal-joggers'    => array( 'fallback_title' => 'Last Petal Joggers', 'fallback_price' => '$135', 'desc' => 'Tapered joggers with falling-petal print down the leg. French terry, brushed interior. Comfort through the storm.', 'room' => 2, 'screen_pos' => array( 65, 52 ) ),
	);
	foreach ( $product_map as $slug => $meta ) {
		$lh_products[] = array( 'id' => $slug, 'wcId' => 0, 'title' => $meta['fallback_title'], 'price' => $meta['fallback_price'], 'desc' => $meta['desc'], 'image' => '', 'permalink' => '', 'room' => $meta['room'], 'screenPos' => $meta['screen_pos'] );
	}
}

/* ── Collection URL ── */
$collection_url = '';
if ( class_exists( 'WooCommerce' ) ) {
	$love_hurts_cat = get_term_by( 'slug', 'love-hurts', 'product_cat' );
	$collection_url = $love_hurts_cat ? get_term_link( $love_hurts_cat ) : '';
	if ( is_wp_error( $collection_url ) ) {
		$collection_url = '';
	}
}
if ( empty( $collection_url ) ) {
	$collection_url = home_url( '/collections/love-hurts/' );
}

$experiences_url = home_url( '/experiences/' );
$cart_url        = class_exists( 'WooCommerce' ) ? wc_get_cart_url() : home_url( '/cart/' );

?><!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title><?php echo esc_html( 'LOVE HURTS | ' . get_bloginfo( 'name' ) . ' Immersive Experience' ); ?></title>
<meta name="description" content="<?php echo esc_attr( 'Enter the Beast\'s bedroom. An immersive 3D experience for the SkyyRose LOVE HURTS collection — the enchanted rose, the balcony, the transformation.' ); ?>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<?php wp_head(); ?>
<script type="importmap">
{
	"imports": {
		"three": "https://unpkg.com/three@0.160.0/build/three.module.js",
		"three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
	}
}
</script>
</head>
<body class="love-hurts-immersive">

<!-- Loading Screen -->
<div id="loading-screen">
	<div class="loading-logo"><?php echo esc_html( 'LOVE HURTS' ); ?></div>
	<div class="loading-subtitle"><?php echo esc_html( 'A SkyyRose Immersive Experience' ); ?></div>
	<div class="loading-progress">
		<div class="loading-bar" id="loading-bar"></div>
	</div>
	<div class="loading-status" id="loading-status"><?php echo esc_html( "Entering the Beast's chamber..." ); ?></div>
</div>

<!-- 3D Canvas -->
<div id="canvas-container"></div>

<!-- UI Overlay -->
<div id="ui-overlay">
	<div class="brand-header">
		<div class="brand-name"><?php echo esc_html( 'SKYYROSE' ); ?></div>
		<div class="collection-label"><?php echo esc_html( 'Love Hurts Collection' ); ?></div>
	</div>

	<div class="room-indicator">
		<div class="room-label" id="room-label"><?php echo esc_html( 'Room 1 of 3 — The Bedroom' ); ?></div>
		<div class="room-dots">
			<div class="room-dot active" data-room="0"></div>
			<div class="room-dot" data-room="1"></div>
			<div class="room-dot" data-room="2"></div>
		</div>
	</div>

	<div class="narrative" id="narrative">
		<p class="narrative-text" id="narrative-text"></p>
	</div>

	<div class="nav-arrows" id="nav-arrows"></div>

	<div id="hotspots-layer"></div>

	<div class="shop-cta" id="shop-cta">
		<a href="<?php echo esc_url( $collection_url ); ?>"><?php echo esc_html( 'Shop the Collection' ); ?></a>
	</div>

	<div class="back-link">
		<a href="<?php echo esc_url( $experiences_url ); ?>"><?php echo esc_html( 'Back to Experiences' ); ?></a>
	</div>
</div>

<!-- Product Detail Panel -->
<div class="product-panel" id="product-panel">
	<button class="panel-close" id="panel-close" aria-label="<?php echo esc_attr( 'Close panel' ); ?>">&times;</button>
	<div class="panel-image" id="panel-image"></div>
	<h2 class="panel-title" id="panel-title"></h2>
	<p class="panel-price" id="panel-price"></p>
	<p class="panel-desc" id="panel-desc"></p>
	<a class="panel-cta" id="panel-cta" href="#"><?php echo esc_html( 'Add to Cart' ); ?></a>
</div>

<!-- WooCommerce Product Data -->
<script>
window.skyyroseLoveHurts = <?php echo wp_json_encode( array(
	'products'      => $lh_products,
	'collectionUrl' => $collection_url,
	'cartUrl'       => $cart_url,
	'ajaxUrl'       => admin_url( 'admin-ajax.php' ),
	'nonce'         => wp_create_nonce( 'wc_store_api' ),
) ); ?>;
</script>

<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

/* ── WebGL Check ── */
function hasWebGL() {
	try {
		var c = document.createElement('canvas');
		return !!(window.WebGLRenderingContext && (c.getContext('webgl') || c.getContext('experimental-webgl')));
	} catch (e) { return false; }
}

if (!hasWebGL()) {
	var ls = document.getElementById('loading-screen');
	if (ls) {
		ls.innerHTML = '<div class="webgl-fallback"><h2>Experience Unavailable</h2><p>Your browser does not support WebGL. Please use a modern browser for the full experience.</p><a href="' + window.skyyroseLoveHurts.collectionUrl + '">View the Collection</a></div>';
	}
	throw new Error('WebGL not supported');
}

/* ── Product & Room Data ── */
var wpProducts = window.skyyroseLoveHurts.products || [];

function getProductsByRoom(roomIndex) {
	return wpProducts.filter(function(p) { return p.room === roomIndex; });
}

var ROOMS = [
	{
		name: 'The Bedroom',
		label: 'Room 1 of 3 \u2014 The Bedroom',
		narrative: '\u201CThey gave me this name\u2026 Hurts. My grandmother\u2019s bloodline. Every generation carries it \u2014 the weight, the beauty, the pain.\u201D',
		nav: [{ text: 'Step onto the Balcony \u2192', target: 1 }],
		camera: { pos: [0, 2.5, 6], target: [0, 1.5, 0] },
		fog: 0x0A0510
	},
	{
		name: 'The Balcony',
		label: 'Room 2 of 3 \u2014 The Balcony',
		narrative: '\u201CLove hurts. That\u2019s not just words \u2014 it\u2019s my last name. And this rose\u2026 it\u2019s all I have left of her.\u201D',
		nav: [{ text: '\u2190 Back to Bedroom', target: 0 }, { text: 'Witness the Transformation \u2192', target: 2 }],
		camera: { pos: [0, 2.8, 5], target: [0, 2, -1] },
		fog: 0x050210
	},
	{
		name: 'The Transformation',
		label: 'Room 3 of 3 \u2014 The Transformation',
		narrative: '\u201CFrom grit to grace. Every petal that falls is a lesson. Every thorn, a boundary. This bloodline doesn\u2019t break \u2014 it transforms.\u201D',
		nav: [{ text: '\u2190 Back to Balcony', target: 1 }],
		camera: { pos: [0, 3, 7], target: [0, 2, 0] },
		fog: 0x0A0505
	}
];

var scene, camera, renderer, controls, composer, bloomPass;
var clock = new THREE.Clock();
var currentRoom = 0;
var isTransitioning = false;

var roomGroups = [new THREE.Group(), new THREE.Group(), new THREE.Group()];
var roomLights = [[], [], []];
var enchantedRose, petalParticles, dustParticles;
var transformationParticles;

var $ = function(id) { return document.getElementById(id); };
var loadingBar = $('loading-bar'), loadingStatus = $('loading-status'), loadingScreen = $('loading-screen');
var narrativeEl = $('narrative'), narrativeText = $('narrative-text'), navArrows = $('nav-arrows');
var roomLabel = $('room-label'), hotspotsLayer = $('hotspots-layer'), productPanel = $('product-panel'), shopCta = $('shop-cta');

function setProgress(pct, text) { loadingBar.style.width = pct + '%'; loadingStatus.textContent = text; }

async function init() {
	scene = new THREE.Scene();
	scene.background = new THREE.Color(ROOMS[0].fog);
	scene.fog = new THREE.FogExp2(ROOMS[0].fog, 0.06);
	camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 100);
	camera.position.set(...ROOMS[0].camera.pos);
	renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
	renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
	renderer.setSize(window.innerWidth, window.innerHeight);
	renderer.toneMapping = THREE.ACESFilmicToneMapping;
	renderer.toneMappingExposure = 0.8;
	renderer.shadowMap.enabled = true;
	renderer.shadowMap.type = THREE.PCFSoftShadowMap;
	$('canvas-container').appendChild(renderer.domElement);
	controls = new OrbitControls(camera, renderer.domElement);
	controls.enableDamping = true; controls.dampingFactor = 0.05;
	controls.target.set(...ROOMS[0].camera.target);
	controls.minDistance = 3; controls.maxDistance = 12;
	controls.maxPolarAngle = Math.PI / 1.7; controls.enablePan = false;
	setupPostProcessing();
	setProgress(15, 'Building the chamber...'); buildRoom1();
	setProgress(35, 'Opening the balcony doors...'); buildRoom2();
	setProgress(55, 'Preparing the transformation...'); buildRoom3();
	setProgress(75, 'Lighting the candles...'); createDustParticles();
	setProgress(90, 'Almost there...');
	roomGroups.forEach(function(g, i) { g.visible = i === 0; scene.add(g); });
	setupUI(); showRoom(0, true);
	setProgress(100, 'Welcome.');
	setTimeout(function() { loadingScreen.classList.add('hidden'); }, 800);
	window.addEventListener('resize', onResize); animate();
}

function setupPostProcessing() {
	composer = new EffectComposer(renderer);
	composer.addPass(new RenderPass(scene, camera));
	bloomPass = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 0.9, 0.4, 0.35);
	composer.addPass(bloomPass); composer.addPass(new OutputPass());
}

/* Helpers */
function M(geo, mat) { return new THREE.Mesh(geo, mat); }
function SM(opts) { return new THREE.MeshStandardMaterial(opts); }
function addM(g, geo, mat, pos, opts) {
	var m = M(geo, mat); m.position.set(...pos);
	if (opts) { if (opts.rx) m.rotation.x = opts.rx; if (opts.ry) m.rotation.y = opts.ry; if (opts.cs) m.castShadow = true; if (opts.rs) m.receiveShadow = true; }
	g.add(m); return m;
}
function addL(g, ri, light, pos) { light.position.set(...pos); g.add(light); roomLights[ri].push(light); return light; }

/* ── ROOM 1 — THE BEAST'S BEDROOM ── */
function buildRoom1() {
	var g = roomGroups[0];
	addM(g, new THREE.PlaneGeometry(18,18), SM({color:0x12080C,roughness:0.9,metalness:0.05}), [0,0,0], {rx:-Math.PI/2,rs:true});
	var wallMat = SM({color:0x0E0610,roughness:0.95,metalness:0.02});
	addM(g, new THREE.PlaneGeometry(18,10), wallMat, [0,5,-6]);
	addM(g, new THREE.PlaneGeometry(12,10), wallMat, [-7,5,0], {ry:Math.PI/2});
	addM(g, new THREE.PlaneGeometry(12,10), wallMat, [7,5,0], {ry:-Math.PI/2});
	addM(g, new THREE.BoxGeometry(3.5,0.6,4), SM({color:0x1A0A12,roughness:0.85,metalness:0.05}), [2,0.3,-3], {cs:true});
	addM(g, new THREE.BoxGeometry(3.3,0.25,3.8), SM({color:0x3A1520,roughness:0.95}), [2,0.72,-3]);
	addM(g, new THREE.BoxGeometry(3.5,2.5,0.2), SM({color:0x200E15,roughness:0.7,metalness:0.15}), [2,1.85,-4.95]);
	var chairMat = SM({color:0x2A1018,roughness:0.8});
	addM(g, new THREE.BoxGeometry(1,0.15,1), chairMat, [-3,1,-2]);
	addM(g, new THREE.BoxGeometry(1,1.5,0.12), chairMat, [-3,1.75,-2.5]);
	var legMat = SM({color:0x1A0A10,roughness:0.6,metalness:0.3}), legGeo = new THREE.CylinderGeometry(0.04,0.04,1,8);
	[[-0.4,-0.4],[0.4,-0.4],[-0.4,0.4],[0.4,0.4]].forEach(function(o) { addM(g, legGeo, legMat, [-3+o[0],0.5,-2+o[1]]); });
	addL(g,0, new THREE.AmbientLight(0x150810,0.5), [0,0,0]);
	var ml = addL(g,0, new THREE.PointLight(0x8B2252,2.5,14), [0,6,0]); ml.castShadow = true;
	addL(g,0, new THREE.PointLight(0xDC143C,0.8,6), [2,3,-3]);
	addL(g,0, new THREE.PointLight(0x722F37,0.6,5), [-3,3,-1]);
	addM(g, new THREE.BoxGeometry(0.8,0.8,0.8), SM({color:0x1A0A10,roughness:0.7,metalness:0.2}), [4.2,0.4,-3]);
	addM(g, new THREE.CylinderGeometry(0.06,0.06,0.5,12), SM({color:0xFFF8DC,roughness:0.9}), [4.2,1.05,-3]);
	addL(g,0, new THREE.PointLight(0xFFAA44,0.6,3), [4.2,1.4,-3]);
}

/* ── ROOM 2 — THE BALCONY (Enchanted Rose) ── */
function buildRoom2() {
	var g = roomGroups[1];
	addM(g, new THREE.PlaneGeometry(14,10), SM({color:0x0E0A0C,roughness:0.92,metalness:0.05}), [0,0,0], {rx:-Math.PI/2,rs:true});
	var railMat = SM({color:0x1A1015,roughness:0.5,metalness:0.4});
	addM(g, new THREE.BoxGeometry(0.1,1.2,8), railMat, [-5,0.6,-1]);
	addM(g, new THREE.BoxGeometry(0.1,1.2,8), railMat, [5,0.6,-1]);
	addM(g, new THREE.BoxGeometry(10,1.2,0.1), railMat, [0,0.6,-5]);
	var bGeo = new THREE.CylinderGeometry(0.03,0.03,1.2,8);
	for (var i = -4; i <= 4; i += 0.8) addM(g, bGeo, railMat, [i,0.6,-5]);
	addM(g, new THREE.CylinderGeometry(0.7,0.7,0.08,24), SM({color:0x200E14,roughness:0.5,metalness:0.3}), [0,1.8,-2]);
	addM(g, new THREE.CylinderGeometry(0.08,0.12,1.8,12), SM({color:0x1A0E12,roughness:0.6,metalness:0.3}), [0,0.9,-2]);
	/* Enchanted Rose */
	enchantedRose = new THREE.Group();
	enchantedRose.position.set(0, 2.2, -2);
	var domeMat = new THREE.MeshPhysicalMaterial({color:0xffffff,roughness:0.05,metalness:0,transmission:0.92,thickness:0.3,transparent:true,opacity:0.3});
	enchantedRose.add(M(new THREE.SphereGeometry(0.55,32,32,0,Math.PI*2,0,Math.PI/1.3), domeMat));
	var bloomMat = SM({color:0xDC143C,emissive:0xDC143C,emissiveIntensity:0.8,roughness:0.4,metalness:0.1});
	enchantedRose.add(M(new THREE.SphereGeometry(0.12,16,16), bloomMat));
	for (var i = 0; i < 5; i++) {
		var a = (i/5)*Math.PI*2, p = M(new THREE.SphereGeometry(0.08,12,12), bloomMat);
		p.position.set(Math.cos(a)*0.1, 0.02, Math.sin(a)*0.1); p.scale.set(1.2,0.6,1.2);
		enchantedRose.add(p);
	}
	var stem = M(new THREE.CylinderGeometry(0.015,0.02,0.5,8), SM({color:0x1A3A1A,roughness:0.7}));
	stem.position.y = -0.3; enchantedRose.add(stem);
	var roseLight = new THREE.PointLight(0xDC143C,3,6);
	enchantedRose.add(roseLight); roomLights[1].push(roseLight);
	g.add(enchantedRose);
	/* Falling petal particles */
	var pc = 60, pp = new Float32Array(pc*3), pcol = new Float32Array(pc*3);
	for (var i = 0; i < pc; i++) {
		pp[i*3]=(Math.random()-0.5)*1.2; pp[i*3+1]=Math.random()*2; pp[i*3+2]=(Math.random()-0.5)*1.2-2;
		pcol[i*3]=0.86+Math.random()*0.14; pcol[i*3+1]=0.05+Math.random()*0.1; pcol[i*3+2]=0.15+Math.random()*0.1;
	}
	var pGeo = new THREE.BufferGeometry();
	pGeo.setAttribute('position', new THREE.BufferAttribute(pp,3));
	pGeo.setAttribute('color', new THREE.BufferAttribute(pcol,3));
	petalParticles = new THREE.Points(pGeo, new THREE.PointsMaterial({size:0.04,vertexColors:true,transparent:true,opacity:0.9,blending:THREE.AdditiveBlending}));
	g.add(petalParticles);
	addL(g,1, new THREE.DirectionalLight(0x6677AA,0.6), [2,8,-10]);
	addL(g,1, new THREE.AmbientLight(0x0A0515,0.4), [0,0,0]);
	addL(g,1, new THREE.PointLight(0x2D0A1F,1,8), [-4,2,-3]);
}

/* ── ROOM 3 — THE TRANSFORMATION ── */
function buildRoom3() {
	var g = roomGroups[2];
	addM(g, new THREE.PlaneGeometry(16,16), SM({color:0x100808,roughness:0.3,metalness:0.4}), [0,0,0], {rx:-Math.PI/2,rs:true});
	var sMat = SM({color:0x1A0E10,roughness:0.4,metalness:0.5}), gMat = SM({color:0xD4AF37,roughness:0.2,metalness:0.8});
	[[-2.5,0],[2.5,0]].forEach(function(c) {
		var x=c[0], z=c[1];
		addM(g, new THREE.CylinderGeometry(0.5,0.6,2.5,16), sMat, [x,1.25,z], {cs:true});
		addM(g, new THREE.CylinderGeometry(0.6,0.5,0.1,16), gMat, [x,2.55,z]);
		var spot = new THREE.SpotLight(0xD4AF37,2,8,Math.PI/8,0.5);
		spot.position.set(x,6,z+2); spot.target.position.set(x,2.5,z); spot.castShadow = true;
		g.add(spot); g.add(spot.target); roomLights[2].push(spot);
	});
	var cl = addL(g,2, new THREE.PointLight(0xDC143C,0.5,12), [0,5,0]); cl.name = 'transformCentralLight';
	var u1 = addL(g,2, new THREE.PointLight(0x722F37,1.5,10), [-3,0.5,-3]); u1.name = 'transformUp1';
	var u2 = addL(g,2, new THREE.PointLight(0x722F37,1.5,10), [3,0.5,-3]); u2.name = 'transformUp2';
	addL(g,2, new THREE.AmbientLight(0x0A0505,0.3), [0,0,0]);
	/* Transformation particle burst */
	var tc=300, tp=new Float32Array(tc*3), tcol=new Float32Array(tc*3);
	for (var i=0;i<tc;i++) {
		tp[i*3]=(Math.random()-0.5)*10; tp[i*3+1]=Math.random()*8; tp[i*3+2]=(Math.random()-0.5)*10;
		var cr=Math.random()>0.5; tcol[i*3]=cr?0.86:0.83; tcol[i*3+1]=cr?0.08:0.69; tcol[i*3+2]=cr?0.24:0.22;
	}
	var tGeo=new THREE.BufferGeometry();
	tGeo.setAttribute('position',new THREE.BufferAttribute(tp,3));
	tGeo.setAttribute('color',new THREE.BufferAttribute(tcol,3));
	transformationParticles = new THREE.Points(tGeo, new THREE.PointsMaterial({size:0.06,vertexColors:true,transparent:true,opacity:0.8,blending:THREE.AdditiveBlending}));
	g.add(transformationParticles);
}

/* ── AMBIENT DUST ── */
function createDustParticles() {
	var n=400, pos=new Float32Array(n*3);
	for (var i=0;i<n;i++) { pos[i*3]=(Math.random()-0.5)*16; pos[i*3+1]=Math.random()*8; pos[i*3+2]=(Math.random()-0.5)*16; }
	var geo=new THREE.BufferGeometry(); geo.setAttribute('position',new THREE.BufferAttribute(pos,3));
	dustParticles = new THREE.Points(geo, new THREE.PointsMaterial({size:0.025,color:0xB76E79,transparent:true,opacity:0.4,blending:THREE.AdditiveBlending}));
	scene.add(dustParticles);
}

/* ── UI MANAGEMENT ── */
function setupUI() {
	document.querySelectorAll('.room-dot').forEach(function(dot) {
		dot.addEventListener('click', function() { var t=parseInt(dot.dataset.room); if(t!==currentRoom&&!isTransitioning) showRoom(t); });
	});
	$('panel-close').addEventListener('click', closePanel);
}

function showRoom(index, instant) {
	if (isTransitioning && !instant) return;
	isTransitioning = true;
	var room = ROOMS[index]; currentRoom = index;
	roomLabel.textContent = room.label;
	document.querySelectorAll('.room-dot').forEach(function(d,i) { d.classList.toggle('active',i===index); });
	narrativeEl.classList.remove('visible'); shopCta.classList.remove('visible'); closePanel();
	var dur = instant ? 0 : 1200;
	var sp = {x:camera.position.x,y:camera.position.y,z:camera.position.z};
	var st = {x:controls.target.x,y:controls.target.y,z:controls.target.z};
	var ep = {x:room.camera.pos[0],y:room.camera.pos[1],z:room.camera.pos[2]};
	var et = {x:room.camera.target[0],y:room.camera.target[1],z:room.camera.target[2]};
	var t0 = performance.now();
	function step(now) {
		var t = dur===0 ? 1 : Math.min((now-t0)/dur,1), e = 1-Math.pow(1-t,3);
		camera.position.x=sp.x+(ep.x-sp.x)*e; camera.position.y=sp.y+(ep.y-sp.y)*e; camera.position.z=sp.z+(ep.z-sp.z)*e;
		controls.target.x=st.x+(et.x-st.x)*e; controls.target.y=st.y+(et.y-st.y)*e; controls.target.z=st.z+(et.z-st.z)*e;
		t<1 ? requestAnimationFrame(step) : (isTransitioning=false);
	}
	if (dur>0) requestAnimationFrame(step);
	else { camera.position.set(...room.camera.pos); controls.target.set(...room.camera.target); isTransitioning=false; }
	roomGroups.forEach(function(g,i) { g.visible = i===index; });
	scene.background.set(room.fog); scene.fog.color.set(room.fog);
	if (index===2) triggerTransformation();
	setTimeout(function() { narrativeText.textContent=room.narrative; narrativeEl.classList.add('visible'); if(index===2) shopCta.classList.add('visible'); }, instant?100:800);
	buildNavArrows(room.nav); buildHotspots(getProductsByRoom(index));
}

function buildNavArrows(items) {
	navArrows.innerHTML = '';
	items.forEach(function(item) {
		var b=document.createElement('button'); b.className='nav-arrow'; b.textContent=item.text;
		b.addEventListener('click',function(){showRoom(item.target);}); navArrows.appendChild(b);
	});
}

function buildHotspots(products) {
	hotspotsLayer.innerHTML = '';
	products.forEach(function(p) {
		var s=document.createElement('div'); s.className='hotspot'; s.style.left=p.screenPos[0]+'%'; s.style.top=p.screenPos[1]+'%';
		var r=document.createElement('div'); r.className='hotspot-ring'; s.appendChild(r);
		var l=document.createElement('div'); l.className='hotspot-label'; l.textContent=p.title+' \u2014 '+p.price; s.appendChild(l);
		s.addEventListener('click',function(){openPanel(p);}); hotspotsLayer.appendChild(s);
	});
}

function openPanel(p) {
	$('panel-title').textContent=p.title; $('panel-price').textContent=p.price; $('panel-desc').textContent=p.desc;
	var ic=$('panel-image'); ic.innerHTML='';
	if(p.image){var img=document.createElement('img');img.src=p.image;img.alt=p.title;ic.appendChild(img);}
	var cta=$('panel-cta');
	if(p.wcId&&p.wcId>0){cta.href=window.skyyroseLoveHurts.cartUrl+'?add-to-cart='+p.wcId;cta.textContent='Add to Cart';}
	else if(p.permalink){cta.href=p.permalink;cta.textContent='View Product';}
	else{cta.href='#';cta.textContent='Add to Cart';}
	productPanel.classList.add('visible');
}

function closePanel() { productPanel.classList.remove('visible'); }

/* ── TRANSFORMATION LIGHTING SHIFT ── */
function triggerTransformation() {
	var g=roomGroups[2], c=g.getObjectByName('transformCentralLight'), u1=g.getObjectByName('transformUp1'), u2=g.getObjectByName('transformUp2');
	if(!c) return;
	var sc=new THREE.Color(0xDC143C), ec=new THREE.Color(0xD4AF37), su=new THREE.Color(0x722F37), eu=new THREE.Color(0xB76E79);
	var dur=2500, t0=performance.now();
	function step(now) {
		var t=Math.min((now-t0)/dur,1), e=t*t*(3-2*t);
		c.color.copy(sc).lerp(ec,e); c.intensity=0.5+e*3;
		if(u1) u1.color.copy(su).lerp(eu,e); if(u2) u2.color.copy(su).lerp(eu,e);
		if(t<1) requestAnimationFrame(step);
	}
	requestAnimationFrame(step);
}

/* ── ANIMATION LOOP ── */
function animate() {
	requestAnimationFrame(animate);
	var time=clock.getElapsedTime(); controls.update();
	if(dustParticles) {
		var dp=dustParticles.geometry.attributes.position.array;
		for(var i=0;i<dp.length;i+=3){dp[i+1]+=Math.sin(time*0.4+i*0.3)*0.002;if(dp[i+1]>8)dp[i+1]=0;}
		dustParticles.geometry.attributes.position.needsUpdate=true; dustParticles.rotation.y+=0.0002;
	}
	if(currentRoom===0) animateBedroom(time);
	if(currentRoom===1) animateBalcony(time);
	if(currentRoom===2) animateTransformation(time);
	composer.render();
}

function animateBedroom(time) {
	var fl=roomLights[0][3]; if(fl) fl.intensity=0.5+Math.sin(time*12)*0.15+Math.sin(time*7.3)*0.1;
}

function animateBalcony(time) {
	if(enchantedRose) { enchantedRose.rotation.y=Math.sin(time*0.3)*0.1; var rl=roomLights[1][0]; if(rl) rl.intensity=2.5+Math.sin(time*1.5)*0.8; }
	if(petalParticles) {
		var pp=petalParticles.geometry.attributes.position.array;
		for(var i=0;i<pp.length;i+=3){
			pp[i+1]-=0.004+Math.sin(i+time)*0.001; pp[i]+=Math.sin(time*0.8+i*0.5)*0.002;
			if(pp[i+1]<-0.5){pp[i+1]=2+Math.random();pp[i]=(Math.random()-0.5)*1.2;pp[i+2]=(Math.random()-0.5)*1.2-2;}
		}
		petalParticles.geometry.attributes.position.needsUpdate=true;
	}
}

function animateTransformation(time) {
	if(!transformationParticles) return;
	var tp=transformationParticles.geometry.attributes.position.array;
	for(var i=0;i<tp.length;i+=3){
		tp[i+1]+=Math.sin(time*1.2+i*0.2)*0.006; tp[i]+=Math.cos(time*0.5+i*0.3)*0.003;
		if(tp[i+1]>8)tp[i+1]=0; if(tp[i+1]<0)tp[i+1]=8;
	}
	transformationParticles.geometry.attributes.position.needsUpdate=true; transformationParticles.rotation.y+=0.001;
}

function onResize() {
	camera.aspect=window.innerWidth/window.innerHeight; camera.updateProjectionMatrix();
	renderer.setSize(window.innerWidth,window.innerHeight); composer.setSize(window.innerWidth,window.innerHeight);
}

init();
</script>

<?php wp_footer(); ?>
</body>
</html>
