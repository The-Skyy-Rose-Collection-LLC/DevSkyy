<?php
/**
 * Template Name: Front Page
 *
 * Three.js portal hero homepage with collection showcase grid,
 * brand story section, and newsletter CTA.
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

defined( 'ABSPATH' ) || exit;

/**
 * Enqueue homepage portal CSS.
 *
 * @since 5.0.0
 * @return void
 */
/* CSS enqueued by inc/enqueue.php via 'front-page' => 'homepage-portal.css' */
/* GSAP enqueued globally by inc/enqueue.php */

/**
 * Output Three.js importmap in <head>.
 *
 * @since 5.0.0
 * @return void
 */
function skyyrose_output_threejs_importmap() {
	if ( ! is_front_page() ) {
		return;
	}
	?>
	<script type="importmap">
	{
		"imports": {
			"three": "https://unpkg.com/three@0.160.0/build/three.module.js",
			"three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
		}
	}
	</script>
	<?php
}
add_action( 'wp_head', 'skyyrose_output_threejs_importmap', 5 );

get_header();

/*--------------------------------------------------------------
 * Collection data
 *--------------------------------------------------------------*/
$skyyrose_collections = array(
	'signature' => array(
		'name'    => __( 'Signature', 'skyyrose-flagship' ),
		'tagline' => __( 'The Origin. The Crown.', 'skyyrose-flagship' ),
		'link'    => home_url( '/collection-signature/' ),
		'slug'    => 'signature',
	),
	'black-rose' => array(
		'name'    => __( 'Black Rose', 'skyyrose-flagship' ),
		'tagline' => __( 'Every Man Would Wear a Black Rose.', 'skyyrose-flagship' ),
		'link'    => home_url( '/collection-black-rose/' ),
		'slug'    => 'black-rose',
	),
	'love-hurts' => array(
		'name'    => __( 'Love Hurts', 'skyyrose-flagship' ),
		'tagline' => __( 'The Hurts Bloodline. Love Through Pain.', 'skyyrose-flagship' ),
		'link'    => home_url( '/collection-love-hurts/' ),
		'slug'    => 'love-hurts',
	),
	'kids-capsule' => array(
		'name'    => __( 'Kids Capsule', 'skyyrose-flagship' ),
		'tagline' => __( 'Luxury Runs In The Family.', 'skyyrose-flagship' ),
		'link'    => home_url( '/collection-kids-capsule/' ),
		'slug'    => 'kids-capsule',
	),
);

$skyyrose_portal_urls = array(
	'signature'  => esc_url( home_url( '/collection-signature/' ) ),
	'black-rose' => esc_url( home_url( '/collection-black-rose/' ) ),
	'love-hurts' => esc_url( home_url( '/collection-love-hurts/' ) ),
);

$skyyrose_cart_url = function_exists( 'wc_get_cart_url' )
	? wc_get_cart_url()
	: home_url( '/cart/' );
?>

<div id="primary" class="site-main front-page-portal">

	<!-- ══════════════════════════════════════════
	     Hero — Three.js Portal Scene
	     ══════════════════════════════════════════ -->
	<section class="portal-hero" id="hero" aria-label="<?php esc_attr_e( 'Interactive 3D collection portals', 'skyyrose-flagship' ); ?>">
		<canvas id="hero-canvas" aria-hidden="true"></canvas>

		<div class="portal-hero-fallback" id="hero-fallback">
			<div class="fallback-title"><?php esc_html_e( 'SKYYROSE', 'skyyrose-flagship' ); ?></div>
		</div>

		<div class="portal-scroll-indicator">
			<span><?php esc_html_e( 'Scroll to Explore', 'skyyrose-flagship' ); ?></span>
		</div>
	</section>

	<!-- Portal label tooltip (positioned by JS) -->
	<div id="portal-label" aria-hidden="true"></div>

	<!-- ══════════════════════════════════════════
	     Collections Showcase
	     ══════════════════════════════════════════ -->
	<section class="collections-showcase" id="collections" aria-label="<?php esc_attr_e( 'Collections', 'skyyrose-flagship' ); ?>">
		<div class="showcase-header reveal">
			<span class="showcase-label"><?php esc_html_e( 'The Collections', 'skyyrose-flagship' ); ?></span>
			<h2 class="showcase-title"><?php esc_html_e( 'Four Stories, One Vision', 'skyyrose-flagship' ); ?></h2>
			<p class="showcase-subtitle">
				<?php esc_html_e( 'Each collection represents a chapter in our story — from dark elegance to emotional depth to timeless luxury to the next generation.', 'skyyrose-flagship' ); ?>
			</p>
		</div>

		<div class="collections-showcase-grid">
			<?php foreach ( $skyyrose_collections as $col_slug => $col ) : ?>
				<div class="showcase-card showcase-card--<?php echo esc_attr( $col_slug ); ?>">
					<div class="showcase-card-bg"></div>
					<div class="showcase-card-content">
						<h3 class="showcase-card-name"><?php echo esc_html( strtoupper( $col['name'] ) ); ?></h3>
						<p class="showcase-card-tagline"><?php echo esc_html( $col['tagline'] ); ?></p>
						<a href="<?php echo esc_url( $col['link'] ); ?>" class="showcase-card-link">
							<?php esc_html_e( 'Explore Collection', 'skyyrose-flagship' ); ?>
							<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true" focusable="false">
								<path d="M5 12h14M12 5l7 7-7 7"/>
							</svg>
						</a>
					</div>
				</div>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ══════════════════════════════════════════
	     Brand Story
	     ══════════════════════════════════════════ -->
	<section class="brand-story-section" aria-label="<?php esc_attr_e( 'Brand story', 'skyyrose-flagship' ); ?>">
		<div class="showcase-header reveal">
			<span class="showcase-label"><?php esc_html_e( 'Our Story', 'skyyrose-flagship' ); ?></span>
			<h2 class="showcase-title"><?php esc_html_e( 'Born in Oakland, Crafted with Love', 'skyyrose-flagship' ); ?></h2>
			<p class="showcase-subtitle">
				<?php
				echo esc_html__(
					'SkyyRose emerged from the vibrant streets of Oakland, where authenticity isn\'t just valued — it\'s essential. The name "Love Hurts" carries deep meaning — it\'s our founder\'s family name, Hurts, woven into the fabric of every piece.',
					'skyyrose-flagship'
				);
				?>
			</p>
		</div>
		<div class="brand-story-cta">
			<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>" class="portal-btn portal-btn--outline">
				<?php esc_html_e( 'Learn Our Story', 'skyyrose-flagship' ); ?>
			</a>
		</div>
	</section>

	<!-- ══════════════════════════════════════════
	     Newsletter
	     ══════════════════════════════════════════ -->
	<section class="portal-newsletter" aria-label="<?php esc_attr_e( 'Newsletter signup', 'skyyrose-flagship' ); ?>">
		<div class="portal-newsletter-content reveal">
			<span class="showcase-label"><?php esc_html_e( 'Stay Connected', 'skyyrose-flagship' ); ?></span>
			<h2 class="showcase-title"><?php esc_html_e( 'Join the SkyyRose Family', 'skyyrose-flagship' ); ?></h2>
			<p class="portal-newsletter-text">
				<?php esc_html_e( 'Be the first to know about new drops, exclusive offers, and behind-the-scenes content.', 'skyyrose-flagship' ); ?>
			</p>
			<form class="portal-newsletter-form" id="portal-newsletter-form" aria-label="<?php esc_attr_e( 'Newsletter', 'skyyrose-flagship' ); ?>">
				<?php wp_nonce_field( 'skyyrose_newsletter', 'skyyrose_newsletter_nonce' ); ?>
				<label for="portal-newsletter-email" class="screen-reader-text">
					<?php esc_html_e( 'Email address', 'skyyrose-flagship' ); ?>
				</label>
				<input
					type="email"
					id="portal-newsletter-email"
					name="email"
					placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose-flagship' ); ?>"
					required
					autocomplete="email"
					class="portal-newsletter-input"
				>
				<button type="submit" class="portal-btn portal-btn--primary">
					<?php esc_html_e( 'Subscribe', 'skyyrose-flagship' ); ?>
				</button>
			</form>
		</div>
	</section>

</div><!-- #primary -->

<!-- ═══════════════════════════════════════════
     Three.js Portal Scene
     ═══════════════════════════════════════════ -->
<script type="module">
import * as THREE from 'three';

const PORTALS = [
	{
		name: 'SIGNATURE',
		color: 0xD4AF37,
		glow: 0xD4AF37,
		url: <?php echo wp_json_encode( $skyyrose_portal_urls['signature'] ); ?>,
		pos: [0, 0.6, 0]
	},
	{
		name: 'BLACK ROSE',
		color: 0xC0C0C0,
		glow: 0xDC143C,
		url: <?php echo wp_json_encode( $skyyrose_portal_urls['black-rose'] ); ?>,
		pos: [-1.8, -0.8, 0]
	},
	{
		name: 'LOVE HURTS',
		color: 0xDC143C,
		glow: 0x2D0A1F,
		url: <?php echo wp_json_encode( $skyyrose_portal_urls['love-hurts'] ); ?>,
		pos: [1.8, -0.8, 0]
	}
];

const canvas = document.getElementById('hero-canvas');
const fallback = document.getElementById('hero-fallback');
const label = document.getElementById('portal-label');

function hasWebGL() {
	try {
		const c = document.createElement('canvas');
		return !!(window.WebGLRenderingContext && (c.getContext('webgl') || c.getContext('experimental-webgl')));
	} catch (e) { return false; }
}

if (!hasWebGL()) {
	canvas.style.display = 'none';
	fallback.classList.add('active');
} else {
	initScene();
}

function initScene() {
	const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
	renderer.setSize(window.innerWidth, window.innerHeight);
	renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
	renderer.setClearColor(0x0A0A0A);

	const scene = new THREE.Scene();
	scene.fog = new THREE.FogExp2(0x0A0A0A, 0.25);

	const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 100);
	camera.position.set(0, 0, 5);

	/* Lighting */
	const ambient = new THREE.AmbientLight(0x111111, 1.0);
	scene.add(ambient);

	PORTALS.forEach(function(p) {
		const pt = new THREE.PointLight(p.color, 0.6, 8);
		pt.position.set(p.pos[0], p.pos[1], 1.5);
		scene.add(pt);
	});

	/* Rose-gold particle field */
	const particleCount = 2000;
	const pGeo = new THREE.BufferGeometry();
	const positions = new Float32Array(particleCount * 3);
	const velocities = new Float32Array(particleCount * 3);
	for (let i = 0; i < particleCount; i++) {
		const i3 = i * 3;
		positions[i3]     = (Math.random() - 0.5) * 10;
		positions[i3 + 1] = (Math.random() - 0.5) * 8;
		positions[i3 + 2] = (Math.random() - 0.5) * 6;
		velocities[i3]     = (Math.random() - 0.5) * 0.002;
		velocities[i3 + 1] = (Math.random() - 0.5) * 0.002;
		velocities[i3 + 2] = (Math.random() - 0.5) * 0.001;
	}
	pGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));

	const pMat = new THREE.PointsMaterial({
		color: 0xB76E79,
		size: 0.025,
		transparent: true,
		opacity: 0.7,
		sizeAttenuation: true,
		blending: THREE.AdditiveBlending,
		depthWrite: false
	});
	const particles = new THREE.Points(pGeo, pMat);
	scene.add(particles);

	/* Brand text plane — SKYYROSE */
	const textCanvas = document.createElement('canvas');
	textCanvas.width = 1024;
	textCanvas.height = 256;
	const ctx = textCanvas.getContext('2d');
	ctx.fillStyle = 'transparent';
	ctx.fillRect(0, 0, 1024, 256);
	ctx.font = '700 120px Cinzel, serif';
	ctx.textAlign = 'center';
	ctx.textBaseline = 'middle';
	const grad = ctx.createLinearGradient(200, 0, 824, 256);
	grad.addColorStop(0, '#FFFFFF');
	grad.addColorStop(0.5, '#B76E79');
	grad.addColorStop(1, '#D4AF37');
	ctx.fillStyle = grad;
	ctx.fillText('SKYYROSE', 512, 128);
	const textTex = new THREE.CanvasTexture(textCanvas);
	const textMat = new THREE.MeshBasicMaterial({
		map: textTex,
		transparent: true,
		depthWrite: false,
		blending: THREE.AdditiveBlending
	});
	const textMesh = new THREE.Mesh(new THREE.PlaneGeometry(4.5, 1.1), textMat);
	textMesh.position.set(0, 2.2, -1);
	scene.add(textMesh);

	/* Portal rings */
	const portalMeshes = [];
	PORTALS.forEach(function(p) {
		const group = new THREE.Group();

		/* Outer ring */
		const ringGeo = new THREE.TorusGeometry(0.55, 0.04, 24, 64);
		const ringMat = new THREE.MeshStandardMaterial({
			color: p.color,
			emissive: p.color,
			emissiveIntensity: 0.6,
			metalness: 0.8,
			roughness: 0.2,
			transparent: true,
			opacity: 0.9
		});
		const ring = new THREE.Mesh(ringGeo, ringMat);
		group.add(ring);

		/* Inner glow disc */
		const discGeo = new THREE.CircleGeometry(0.45, 48);
		const discMat = new THREE.MeshBasicMaterial({
			color: p.glow,
			transparent: true,
			opacity: 0.12,
			blending: THREE.AdditiveBlending,
			side: THREE.DoubleSide,
			depthWrite: false
		});
		const disc = new THREE.Mesh(discGeo, discMat);
		group.add(disc);

		/* Second ring for depth */
		const ring2Geo = new THREE.TorusGeometry(0.48, 0.02, 16, 48);
		const ring2Mat = new THREE.MeshStandardMaterial({
			color: p.glow,
			emissive: p.glow,
			emissiveIntensity: 0.4,
			transparent: true,
			opacity: 0.5
		});
		const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
		ring2.rotation.x = 0.3;
		group.add(ring2);

		group.position.set(p.pos[0], p.pos[1], p.pos[2]);
		group.userData = { name: p.name, url: p.url, baseScale: 1.0 };
		scene.add(group);
		portalMeshes.push(group);
	});

	/* Raycaster */
	const raycaster = new THREE.Raycaster();
	const mouse = new THREE.Vector2();
	let hoveredPortal = null;

	canvas.addEventListener('mousemove', function(e) {
		const rect = canvas.getBoundingClientRect();
		mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
		mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
		label.style.left = (e.clientX + 16) + 'px';
		label.style.top  = (e.clientY - 16) + 'px';
	});

	canvas.addEventListener('click', function() {
		if (hoveredPortal) {
			window.location.href = hoveredPortal.userData.url;
		}
	});

	canvas.style.cursor = 'default';

	/* Resize */
	function onResize() {
		camera.aspect = window.innerWidth / window.innerHeight;
		camera.updateProjectionMatrix();
		renderer.setSize(window.innerWidth, window.innerHeight);
	}
	window.addEventListener('resize', onResize);

	/* Animation loop */
	const clock = new THREE.Clock();
	function animate() {
		requestAnimationFrame(animate);
		const t = clock.getElapsedTime();

		/* Float particles */
		const pos = particles.geometry.attributes.position.array;
		for (let i = 0; i < particleCount; i++) {
			const i3 = i * 3;
			pos[i3]     += velocities[i3];
			pos[i3 + 1] += velocities[i3 + 1];
			pos[i3 + 2] += velocities[i3 + 2];
			if (Math.abs(pos[i3]) > 5) velocities[i3] *= -1;
			if (Math.abs(pos[i3 + 1]) > 4) velocities[i3 + 1] *= -1;
			if (Math.abs(pos[i3 + 2]) > 3) velocities[i3 + 2] *= -1;
		}
		particles.geometry.attributes.position.needsUpdate = true;

		/* Animate portals: gentle bob + pulse */
		portalMeshes.forEach(function(g, i) {
			const offset = i * 2.1;
			g.rotation.z = Math.sin(t * 0.5 + offset) * 0.1;
			g.position.y = PORTALS[i].pos[1] + Math.sin(t * 0.7 + offset) * 0.08;
			const pulse = 1.0 + Math.sin(t * 1.5 + offset) * 0.04;
			const targetScale = (hoveredPortal === g) ? 1.18 : 1.0;
			g.userData.baseScale += (targetScale - g.userData.baseScale) * 0.08;
			const s = g.userData.baseScale * pulse;
			g.scale.set(s, s, s);
			/* Pulse inner disc opacity */
			g.children[1].material.opacity = 0.10 + Math.sin(t * 2 + offset) * 0.06;
		});

		/* Text subtle breathe */
		textMesh.material.opacity = 0.85 + Math.sin(t * 0.8) * 0.15;

		/* Raycast */
		raycaster.setFromCamera(mouse, camera);
		const allChildren = portalMeshes.flatMap(function(g) {
			return g.children.map(function(c) { return { mesh: c, group: g }; });
		});
		const intersects = raycaster.intersectObjects(allChildren.map(function(o) { return o.mesh; }));
		if (intersects.length > 0) {
			const hit = allChildren.find(function(o) { return o.mesh === intersects[0].object; });
			if (hit) {
				hoveredPortal = hit.group;
				canvas.style.cursor = 'pointer';
				label.textContent = hoveredPortal.userData.name;
				label.classList.add('visible');
			} else {
				hoveredPortal = null;
				canvas.style.cursor = 'default';
				label.classList.remove('visible');
			}
		} else {
			hoveredPortal = null;
			canvas.style.cursor = 'default';
			label.classList.remove('visible');
		}

		renderer.render(scene, camera);
	}
	animate();
}
</script>

<!-- Page Logic -->
<script>
(function() {
	/* Navbar scroll effect */
	window.addEventListener('scroll', function() {
		var navbar = document.getElementById('navbar');
		if (navbar) {
			if (window.scrollY > 50) {
				navbar.classList.add('scrolled');
			} else {
				navbar.classList.remove('scrolled');
			}
		}
	});

	/* Smooth scroll for anchor links */
	document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
		anchor.addEventListener('click', function(e) {
			e.preventDefault();
			var target = document.querySelector(this.getAttribute('href'));
			if (target) {
				target.scrollIntoView({ behavior: 'smooth' });
			}
		});
	});

	/* Newsletter form — submit via AJAX */
	var form = document.getElementById('portal-newsletter-form');
	if (form) {
		form.addEventListener('submit', function(e) {
			e.preventDefault();
			var data = new FormData(form);
			data.append('action', 'skyyrose_newsletter_subscribe');
			var btn = form.querySelector('button[type="submit"]');
			if (btn) btn.disabled = true;
			fetch(<?php echo wp_json_encode( admin_url( 'admin-ajax.php' ) ); ?>, { method: 'POST', body: data })
				.then(function(r) { return r.json(); })
				.then(function(res) {
					var toast = document.createElement('div');
					toast.className = 'portal-toast';
					toast.textContent = (res.success && res.data && res.data.message) ? res.data.message : <?php echo wp_json_encode( __( 'Welcome to the SkyyRose family.', 'skyyrose-flagship' ) ); ?>;
					document.body.appendChild(toast);
					setTimeout(function() { toast.remove(); }, 3000);
					form.reset();
				})
				.catch(function() {
					var toast = document.createElement('div');
					toast.className = 'portal-toast';
					toast.textContent = <?php echo wp_json_encode( __( 'Welcome to the SkyyRose family.', 'skyyrose-flagship' ) ); ?>;
					document.body.appendChild(toast);
					setTimeout(function() { toast.remove(); }, 3000);
					form.reset();
				})
				.finally(function() { if (btn) btn.disabled = false; });
		});
	}

	/* GSAP reveal animations */
	if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
		gsap.registerPlugin(ScrollTrigger);
		gsap.utils.toArray('.reveal').forEach(function(el) {
			gsap.from(el, {
				y: 60,
				opacity: 0,
				duration: 1,
				ease: 'power2.out',
				scrollTrigger: {
					trigger: el,
					start: 'top 85%',
					toggleActions: 'play none none none'
				}
			});
		});
	}
})();
</script>

<?php
get_footer();
