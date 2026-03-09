<?php
/**
 * Template Name: Collections
 *
 * All collections overview page — displays each collection as a card
 * linking to its individual template page.
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

defined( 'ABSPATH' ) || exit;

get_header();

$collections = array(
	array(
		'slug'    => 'collection-black-rose',
		'name'    => __( 'Black Rose', 'skyyrose-flagship' ),
		'tagline' => __( 'Where darkness blooms, beauty follows.', 'skyyrose-flagship' ),
		'accent'  => '#C0C0C0',
		'image'   => SKYYROSE_ASSETS_URI . '/scenes/black-rose/black-rose-rooftop-garden-v2.webp',
		'class'   => 'collection--black-rose',
		'skus'    => array( 'br-001', 'br-002', 'br-003', 'br-004', 'br-005', 'br-006', 'br-007', 'br-008' ),
	),
	array(
		'slug'    => 'collection-love-hurts',
		'name'    => __( 'Love Hurts', 'skyyrose-flagship' ),
		'tagline' => __( 'Love is a beautiful wound.', 'skyyrose-flagship' ),
		'accent'  => '#DC143C',
		'image'   => SKYYROSE_ASSETS_URI . '/scenes/love-hurts/love-hurts-cathedral-rose-chamber-v2.webp',
		'class'   => 'collection--love-hurts',
		'skus'    => array( 'lh-001', 'lh-002', 'lh-003', 'lh-004', 'lh-005' ),
	),
	array(
		'slug'    => 'collection-signature',
		'name'    => __( 'Signature', 'skyyrose-flagship' ),
		'tagline' => __( 'The original. The standard.', 'skyyrose-flagship' ),
		'accent'  => '#B76E79',
		'image'   => SKYYROSE_ASSETS_URI . '/scenes/signature/signature-golden-gate-showroom-v2.webp',
		'class'   => 'collection--signature',
		'skus'    => array( 'sg-001', 'sg-002', 'sg-003', 'sg-004', 'sg-005', 'sg-006', 'sg-007', 'sg-008', 'sg-009', 'sg-010', 'sg-011', 'sg-012' ),
	),
	array(
		'slug'    => 'collection-kids-capsule',
		'name'    => __( 'Kids Capsule', 'skyyrose-flagship' ),
		'tagline' => __( 'Little legends. Big style.', 'skyyrose-flagship' ),
		'accent'  => '#FFB6C1',
		'image'   => get_template_directory_uri() . '/assets/branding/kids-capsule-preview.webp',
		'class'   => 'collection--kids-capsule',
		'skus'    => array(),
	),
);
?>

<main id="primary" class="site-main collections-page">

	<!-- Hero -->
	<section class="collection-hero">
		<p class="collection-hero__subtitle"><?php esc_html_e( 'SkyyRose Collections', 'skyyrose-flagship' ); ?></p>
		<h1 class="collection-hero__title"><?php esc_html_e( 'Explore the Universe', 'skyyrose-flagship' ); ?></h1>
		<p class="collection-hero__desc"><?php esc_html_e( 'Four worlds. One brand. Luxury grows from concrete.', 'skyyrose-flagship' ); ?></p>
	</section>

	<!-- Collections Grid -->
	<section class="collections-grid-wrap">
		<div class="collections-grid">
			<?php foreach ( $collections as $i => $col ) :
				$page = get_page_by_path( $col['slug'] );
				$url  = $page ? get_permalink( $page ) : '#';
				$count = count( $col['skus'] );
			?>
			<a href="<?php echo esc_url( $url ); ?>"
			   class="collections-card card-reveal-target <?php echo esc_attr( $col['class'] ); ?>"
			   style="--collection-accent: <?php echo esc_attr( $col['accent'] ); ?>; transition-delay: <?php echo esc_attr( $i * 0.1 ); ?>s;">

				<div class="collections-card__image-wrap">
					<img src="<?php echo esc_url( $col['image'] ); ?>"
					     alt="<?php echo esc_attr( $col['name'] ); ?>"
					     loading="<?php echo esc_attr( $i < 2 ? 'eager' : 'lazy' ); ?>"
					     decoding="async"
					     width="600" height="800">
				</div>

				<div class="collections-card__info">
					<h2 class="collections-card__name"><?php echo esc_html( $col['name'] ); ?></h2>
					<p class="collections-card__tagline"><?php echo esc_html( $col['tagline'] ); ?></p>
					<?php if ( $count > 0 ) : ?>
						<span class="collections-card__count">
							<?php printf( esc_html( _n( '%d piece', '%d pieces', $count, 'skyyrose-flagship' ) ), $count ); ?>
						</span>
					<?php endif; ?>
					<span class="collections-card__cta"><?php esc_html_e( 'Explore Collection', 'skyyrose-flagship' ); ?> &rarr;</span>
				</div>

			</a>
			<?php endforeach; ?>
		</div>
	</section>

</main>

<?php get_footer(); ?>
