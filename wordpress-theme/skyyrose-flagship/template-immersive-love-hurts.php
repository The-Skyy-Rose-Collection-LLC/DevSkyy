<?php
/**
 * Template Name: Immersive - Love Hurts
 *
 * "The Cathedral" — candlelit chamber, enchanted rose dome, stained glass.
 * Beauty and the Beast narrative reimagined. "Every petal tells a story."
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
		skyyrose_get_immersive_args( 'love-hurts' )
	);
	?>
</main>
<?php
get_footer();
