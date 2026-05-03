<?php
/**
 * Template Name: Immersive - Kids Capsule
 *
 * "The Playroom" — warm rose-gold atmosphere, playful sophistication.
 * Luxury grows young. Mini-me collection for the next generation.
 *
 * Per-collection room data lives in inc/immersive-data.php; rendering happens
 * in template-parts/immersive-scene.php (shared across all 4 immersive worlds).
 *
 * @package SkyyRose
 * @since   7.1.0
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>
<main id="primary" class="site-main immersive-page" role="main" tabindex="-1">
	<?php
	get_template_part(
		'template-parts/immersive-scene',
		null,
		skyyrose_get_immersive_args( 'kids-capsule' )
	);
	?>
</main>
<?php
get_footer();
