<?php
/**
 * Kids Capsule — Parent-Child Matching Set Section
 *
 * Displays the matching adult product when a Kids Capsule product
 * has a `_kc_matching_adult_id` meta value. Used on single product
 * pages in live mode.
 *
 * @package SkyyRose
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$kc_adult_id = (int) get_post_meta( get_the_ID(), '_kc_matching_adult_id', true );
if ( ! $kc_adult_id ) {
	return;
}

$kc_adult_product = wc_get_product( $kc_adult_id );
if ( ! $kc_adult_product || 'publish' !== get_post_status( $kc_adult_id ) ) {
	return;
}
?>

<section class="kc-matching-set" aria-label="<?php esc_attr_e( 'Shop the Matching Set', 'skyyrose' ); ?>">
	<h2 class="kc-matching-set__title"><?php esc_html_e( 'Shop the Matching Set', 'skyyrose' ); ?></h2>
	<p class="kc-matching-set__subtitle">
		<?php esc_html_e( 'This piece was designed to pair with its adult counterpart. Twin with your little one.', 'skyyrose' ); ?>
	</p>
	<div class="kc-matching-set__card">
		<?php
		get_template_part(
			'template-parts/product-card-holo',
			null,
			array(
				'product'    => $kc_adult_product,
				'collection' => 'kids-capsule',
			)
		);
		?>
	</div>
</section>
