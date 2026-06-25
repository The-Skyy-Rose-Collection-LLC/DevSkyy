<?php
/**
 * Component: Product Card
 *
 * Renders a single product card from the SkyyRose catalog.
 * Pulls data via skyyrose_get_product( $sku ) — returns early if SKU not found.
 * Does NOT wrap product-card-holo.php; this is a separate, clean component.
 *
 * Usage:
 *   get_template_part( 'template-parts/components/card-product', null, [
 *       'sku'           => 'br-001',
 *       'show_badge'    => true,
 *       'show_price'    => true,
 *       'show_cta'      => true,
 *       'cta_label'     => '',         // defaults to 'Shop Now' or 'Pre-Order'
 *       'lazy'          => true,
 *       'extra_classes' => '',
 *       'attrs'         => [],
 *   ] );
 *
 * @package SkyyRose
 */

defined( 'ABSPATH' ) || exit;

$args = wp_parse_args(
	$args ?? array(),
	array(
		'sku'           => '',
		'show_badge'    => true,
		'show_price'    => true,
		'show_cta'      => true,
		'cta_label'     => '',
		'lazy'          => true,
		'extra_classes' => '',
		'attrs'         => array(),
	)
);

$sku = sanitize_key( $args['sku'] );
if ( ! $sku ) {
	return;
}

$product = skyyrose_get_product( $sku );
if ( empty( $product ) ) {
	return;
}

$name        = $product['name'] ?? '';
$collection  = $product['collection'] ?? '';
$price_str   = skyyrose_format_price( $product );
$is_preorder = ! empty( $product['is_preorder'] );
$badge       = $product['badge'] ?? ( $is_preorder ? 'Pre-Order' : '' );
$image_path  = $product['image'] ?? '';
$product_url = skyyrose_product_url( $sku );
$cta_label   = $args['cta_label'] ?: ( $is_preorder ? __( 'Pre-Order', 'skyyrose' ) : __( 'Shop Now', 'skyyrose' ) );

$collection_class = $collection ? 'sr-card-product--' . sanitize_html_class( $collection ) : '';

$card_classes = implode(
	' ',
	array_filter(
		array(
			'sr-card-product',
			$collection_class,
			$is_preorder ? 'sr-card-product--preorder' : '',
			skyyrose_sanitize_class_list( $args['extra_classes'] ?? '' ),
		)
	)
);

// Build extra attributes string.
$attr_string = skyyrose_build_attr_string( $args['attrs'] ?? array() );
?>
<article
	class="<?php echo esc_attr( $card_classes ); ?>"
	data-component="card-product"
	data-sku="<?php echo esc_attr( $sku ); ?>"
	data-collection="<?php echo esc_attr( $collection ); ?>"
	<?php echo $attr_string; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- pre-escaped above. ?>
>
	<a class="sr-card-product__link" href="<?php echo esc_url( $product_url ); ?>" tabindex="-1" aria-hidden="true" focusable="false">

		<div class="sr-card-product__media">
			<?php if ( $image_path ) : ?>
				<img
					class="sr-card-product__img"
					src="<?php echo esc_url( skyyrose_product_image_uri( $image_path ) ); ?>"
					alt="<?php echo esc_attr( $name ); ?>"
					loading="<?php echo $args['lazy'] ? 'lazy' : 'eager'; ?>"
					decoding="async"
				/>
			<?php else : ?>
				<!-- sr-card-product: no image found for sku <?php echo esc_html( $sku ); ?> -->
				<div class="sr-card-product__img-placeholder" aria-hidden="true"></div>
			<?php endif; ?>

			<?php if ( $args['show_badge'] && $badge ) : ?>
				<span class="sr-card-product__badge"><?php echo esc_html( $badge ); ?></span>
			<?php endif; ?>
		</div>

	</a>

	<div class="sr-card-product__body">

		<h3 class="sr-card-product__name">
			<a class="sr-card-product__name-link" href="<?php echo esc_url( $product_url ); ?>">
				<?php echo esc_html( $name ); ?>
			</a>
		</h3>

		<?php if ( $args['show_price'] ) : ?>
			<p class="sr-card-product__price"><?php echo esc_html( $price_str ); ?></p>
		<?php endif; ?>

		<?php if ( $args['show_cta'] ) : ?>
			<div class="sr-card-product__cta">
				<?php
				get_template_part(
					'template-parts/components/button',
					null,
					array(
						'label'   => $cta_label,
						'tag'     => 'a',
						'href'    => $product_url,
						'variant' => 'outline',
						'size'    => 'sm',
						'attrs'   => array(
							'data-sku'        => $sku,
							'data-collection' => $collection,
						),
					)
				);
				?>
			</div>
		<?php endif; ?>

	</div>
</article>
