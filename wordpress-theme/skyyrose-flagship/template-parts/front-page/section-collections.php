<?php
/**
 * Front Page: Collections Showcase
 *
 * 3 collection cards with descriptions and CTAs.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$collections = array(
	array(
		'slug'        => 'black-rose',
		'name'        => __( 'BLACK ROSE', 'skyyrose-flagship' ),
		'tagline'     => __( 'Dark elegance for the bold', 'skyyrose-flagship' ),
		'description' => __( 'Gothic romance meets modern streetwear. Metallic silver accents on midnight black — for those who find beauty in the shadows.', 'skyyrose-flagship' ),
		'class'       => 'collections__card--black-rose',
	),
	array(
		'slug'        => 'love-hurts',
		'name'        => __( 'LOVE HURTS', 'skyyrose-flagship' ),
		'tagline'     => __( 'Where emotion meets fashion', 'skyyrose-flagship' ),
		'description' => __( 'Every scar tells a story. Crimson reds and deep blacks — raw, passionate designs that wear your heart on your sleeve.', 'skyyrose-flagship' ),
		'class'       => 'collections__card--love-hurts',
	),
	array(
		'slug'        => 'signature',
		'name'        => __( 'SIGNATURE', 'skyyrose-flagship' ),
		'tagline'     => __( 'Timeless luxury essentials', 'skyyrose-flagship' ),
		'description' => __( 'Rose gold meets gold in elevated everyday luxury. Premium materials, expert construction — the art of everyday excellence.', 'skyyrose-flagship' ),
		'class'       => 'collections__card--signature',
	),
);
?>

<section class="collections" id="collections" aria-labelledby="collections-heading">
	<div class="collections__header section-header">
		<span class="section-header__label">
			<?php esc_html_e( 'The Collections', 'skyyrose-flagship' ); ?>
		</span>
		<h2 class="section-header__title" id="collections-heading">
			<?php esc_html_e( 'Three Stories, One Vision', 'skyyrose-flagship' ); ?>
		</h2>
		<p class="section-header__subtitle">
			<?php esc_html_e( 'Each collection represents a chapter in our story — from dark elegance to emotional depth to timeless luxury.', 'skyyrose-flagship' ); ?>
		</p>
	</div>

	<div class="collections__grid">
		<?php
		foreach ( $collections as $collection ) :
			// Try to get the WooCommerce product category link.
			$collection_url = home_url( '/collection-' . $collection['slug'] . '/' );

			if ( class_exists( 'WooCommerce' ) ) {
				$term = get_term_by( 'slug', $collection['slug'], 'product_cat' );
				if ( $term && ! is_wp_error( $term ) ) {
					$term_link = get_term_link( $term );
					if ( ! is_wp_error( $term_link ) ) {
						$collection_url = $term_link;
					}
				}
			}
			?>
			<div class="collections__card <?php echo esc_attr( $collection['class'] ); ?> js-scroll-reveal">
				<div class="collections__card-bg" aria-hidden="true"></div>
				<div class="collections__card-content">
					<h3 class="collections__card-name">
						<?php echo esc_html( $collection['name'] ); ?>
					</h3>
					<p class="collections__card-tagline">
						<?php echo esc_html( $collection['tagline'] ); ?>
					</p>
					<p class="collections__card-description">
						<?php echo esc_html( $collection['description'] ); ?>
					</p>
					<div class="collections__card-actions">
						<a href="<?php echo esc_url( $collection_url ); ?>" class="btn btn--collection">
							<?php esc_html_e( 'Shop Collection', 'skyyrose-flagship' ); ?>
							<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
								<path d="M5 12h14M12 5l7 7-7 7"/>
							</svg>
						</a>
						<a href="<?php echo esc_url( home_url( '/immersive/' . $collection['slug'] . '/' ) ); ?>" class="btn btn--immersive">
							<?php esc_html_e( 'Immersive Experience', 'skyyrose-flagship' ); ?>
						</a>
					</div>
				</div>
			</div>
		<?php endforeach; ?>
	</div>
</section>
