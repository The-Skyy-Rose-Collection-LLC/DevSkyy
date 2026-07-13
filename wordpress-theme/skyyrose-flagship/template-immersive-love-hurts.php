<?php
/**
 * Template Name: Immersive - Love Hurts
 *
 * "The Cathedral" — candlelit chamber, enchanted rose dome, stained glass.
 *
 * Structural remediation WS3: the experience now lives as the opening layer
 * of /collections/love-hurts/ and this route 301s there (inc/redirects.php).
 * Room data moved to skyyrose_get_experience_config() in
 * inc/experience-rooms.php — this template renders the same config standalone
 * and remains only as the assigned template of the legacy page (rollback path).
 *
 * @package SkyyRose
 * @since   3.0.0
 * @updated 1.8.0 — Room data centralized in inc/experience-rooms.php.
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$experience = skyyrose_get_experience_config( 'love-hurts' );

get_header();
?>

<main id="primary" class="site-main immersive-page" role="main" tabindex="-1">
	<?php
	if ( $experience ) {
		get_template_part(
			'template-parts/immersive/scene',
			null,
			array(
				'collection_slug' => 'love-hurts',
				'collection_name' => $experience['collection_name'],
				'world_name'      => $experience['world_name'],
				'tagline'         => $experience['tagline'],
				'accent_color'    => $experience['accent_color'],
				'collection_url'  => home_url( '/collections/love-hurts/' ),
				'rooms'           => $experience['rooms'],
			)
		);
	}
	?>
</main>

<?php
get_footer();
