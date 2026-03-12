<?php
/**
 * Template Name: Spatial Home
 *
 * Drake-style "virtual house" front door. Full-viewport dark scene with
 * 3 door cards linking to the immersive collection experiences.
 * No Three.js — CSS-only transitions and particles for fast load.
 *
 * @package SkyyRose_Flagship
 * @since   4.4.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$assets_uri = get_template_directory_uri() . '/assets';

/**
 * World door data.
 *
 * Each door links to an immersive experience page. The image used is
 * the homepage collection card (already sized for cards at 600x800).
 * Lookbook composites are available as alternatives for richer previews.
 */
$worlds = array(
	array(
		'slug'       => 'black-rose',
		'name'       => __( 'The Garden', 'skyyrose-flagship' ),
		'collection' => __( 'Black Rose', 'skyyrose-flagship' ),
		'url'        => home_url( '/experience-black-rose/' ),
		'image'      => $assets_uri . '/images/homepage-col-black-rose.webp',
		'accent'     => '#C0C0C0',
	),
	array(
		'slug'       => 'love-hurts',
		'name'       => __( 'The Cathedral', 'skyyrose-flagship' ),
		'collection' => __( 'Love Hurts', 'skyyrose-flagship' ),
		'url'        => home_url( '/experience-love-hurts/' ),
		'image'      => $assets_uri . '/images/homepage-col-love-hurts.webp',
		'accent'     => '#DC143C',
	),
	array(
		'slug'       => 'signature',
		'name'       => __( 'The Runway', 'skyyrose-flagship' ),
		'collection' => __( 'Signature', 'skyyrose-flagship' ),
		'url'        => home_url( '/experience-signature/' ),
		'image'      => $assets_uri . '/images/homepage-col-signature.webp',
		'accent'     => '#B76E79',
	),
);

get_header();
?>

<main id="primary" class="site-main spatial-home" role="main" tabindex="-1">

	<!-- Particle Canvas (CSS-only, decorative) -->
	<div class="spatial-home__particles" aria-hidden="true"></div>

	<!-- Brand Hero -->
	<div class="spatial-home__hero">
		<div class="spatial-home__monogram"><?php echo esc_html__( 'SR', 'skyyrose-flagship' ); ?></div>
		<p class="spatial-home__tagline"><?php echo esc_html__( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ); ?></p>
	</div>

	<!-- Door Cards -->
	<div class="spatial-home__doors">
		<?php foreach ( $worlds as $world ) : ?>
			<a
				href="<?php echo esc_url( $world['url'] ); ?>"
				class="spatial-home__door"
				style="--door-accent: <?php echo esc_attr( $world['accent'] ); ?>;"
				aria-label="<?php echo esc_attr(
					/* translators: 1: world name, 2: collection name */
					sprintf( __( 'Enter %1$s — %2$s Collection', 'skyyrose-flagship' ), $world['name'], $world['collection'] )
				); ?>"
			>
				<div class="spatial-home__door-image-wrap">
					<img
						src="<?php echo esc_url( $world['image'] ); ?>"
						alt=""
						loading="eager"
						width="600"
						height="800"
					>
				</div>
				<div class="spatial-home__door-content">
					<span class="spatial-home__door-enter"><?php echo esc_html__( 'Enter', 'skyyrose-flagship' ); ?></span>
					<span class="spatial-home__door-name"><?php echo esc_html( $world['name'] ); ?></span>
					<span class="spatial-home__door-collection"><?php echo esc_html( $world['collection'] ); ?></span>
				</div>
			</a>
		<?php endforeach; ?>
	</div>

	<!-- Shop All Fallback -->
	<div class="spatial-home__footer">
		<a href="<?php echo esc_url( home_url( '/collections/' ) ); ?>" class="spatial-home__shop-all">
			<?php echo esc_html__( 'Shop All Collections', 'skyyrose-flagship' ); ?>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
				<path d="M5 12h14"/>
				<path d="m12 5 7 7-7 7"/>
			</svg>
		</a>
	</div>

</main><!-- #primary -->

<?php
get_footer();
