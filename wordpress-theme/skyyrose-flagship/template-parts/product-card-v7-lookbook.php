<?php
/**
 * V7 lookbook product card.
 *
 * Verified asset-hub imagery (verdict:verified), auto-advance carousel
 * (hover-pauses in place), collection-logo backdrop, [data-collection] palette.
 * Falls back to the holo card when no verified V7 data exists for the SKU.
 *
 * Expected $args: product (WC_Product|null), collection, sku, permalink, index.
 *
 * @package SkyyRose
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$v7_product = isset( $args['product'] ) ? $args['product'] : null;
$v7_sku     = '';
if ( $v7_product instanceof WC_Product ) {
	$v7_sku = $v7_product->get_sku();
}
if ( ! $v7_sku && ! empty( $args['sku'] ) ) {
	$v7_sku = $args['sku'];
}

$v7 = skyyrose_v7_card( $v7_sku );

// No verified V7 data for this SKU → fall back to the existing card (never invent imagery).
if ( ! $v7 || empty( $v7['shots'] ) ) {
	get_template_part( 'template-parts/product-card-holo', null, $args );
	return;
}

$v7_collection = ! empty( $v7['collection'] ) ? $v7['collection'] : ( isset( $args['collection'] ) ? $args['collection'] : '' );
$v7_name       = ! empty( $v7['name'] ) ? (string) $v7['name'] : $v7_sku;
$v7_shots      = $v7['shots'];
$v7_badge      = ! empty( $v7['badge'] ) ? $v7['badge'] : '';
$v7_edition    = ! empty( $v7['edition'] ) ? $v7['edition'] : 0;
$v7_preorder   = ! empty( $v7['preorder'] );
$v7_lockup_set = skyyrose_v7_lockup_sources( $v7_collection );
$v7_lockup     = $v7_lockup_set['webp'];

if ( $v7_product instanceof WC_Product ) {
	$v7_permalink  = get_permalink( $v7_product->get_id() );
	$v7_price_html = $v7_product->get_price_html();
} else {
	$v7_permalink  = ! empty( $args['permalink'] ) ? $args['permalink'] : '#';
	$v7_price_html = function_exists( 'wc_price' )
		? wc_price( (float) $v7['price'] )
		: esc_html( '$' . number_format( (float) $v7['price'], 2 ) );
}
?>
<article class="v7card" data-collection="<?php echo esc_attr( $v7_collection ); ?>" data-sku="<?php echo esc_attr( $v7_sku ); ?>">
	<a class="v7card__frame" href="<?php echo esc_url( $v7_permalink ); ?>" aria-label="<?php echo esc_attr( $v7_name ); ?>">
		<?php if ( $v7_lockup ) : ?>
			<?php
			// Double background-image declaration = cascade fallback: browsers
			// without image-set() keep the WebP url(); AVIF-capable ones take
			// the smaller tier. Decorative layer — stays aria-hidden.
			$v7_lockup_style = "background-image:url('" . esc_url( $v7_lockup ) . "')";
			if ( ! empty( $v7_lockup_set['avif'] ) ) {
				$v7_lockup_style .= ";background-image:image-set(url('" . esc_url( $v7_lockup_set['avif'] ) . "') type('image/avif'),url('" . esc_url( $v7_lockup ) . "') type('image/webp'))";
			}
			?>
			<span class="v7card__logo" aria-hidden="true" style="<?php echo esc_attr( $v7_lockup_style ); ?>"></span>
		<?php endif; ?>
		<div class="v7card__carousel">
			<?php
			foreach ( $v7_shots as $i => $shot ) :
				$shot_uri = ! empty( $shot['uri'] ) ? (string) $shot['uri'] : '';
				if ( '' === $shot_uri ) {
					continue;
				}
				$shot_face = ! empty( $shot['face'] ) ? (string) $shot['face'] : 'view';
				$shot_src  = get_theme_file_uri( $shot_uri );
				// AVIF tier via the shared next-gen sibling prober (Photon-safe): serves the
				// .avif sibling through <picture> when present; <img> is the universal fallback.
				$shot_pic = skyyrose_picture_sources( $shot_src );
				?>
				<picture>
					<?php if ( ! empty( $shot_pic['avif'] ) ) : ?>
						<source type="image/avif" srcset="<?php echo esc_url( $shot_pic['avif'] ); ?>">
					<?php endif; ?>
					<img class="v7card__shot"<?php echo 0 === $i ? ' data-active="true"' : ' aria-hidden="true"'; ?>
						src="<?php echo esc_url( $shot_src ); ?>"
						alt="<?php echo esc_attr( $v7_name . ' — ' . $shot_face ); ?>"
						width="600" height="750"
						loading="<?php echo 0 === $i ? 'eager' : 'lazy'; ?>" decoding="async">
				</picture>
			<?php endforeach; ?>
		</div>
		<span class="v7card__scrim" aria-hidden="true"></span>
		<?php if ( $v7_badge ) : ?>
			<span class="v7card__badge"><?php echo esc_html( $v7_badge ); ?></span>
		<?php endif; ?>
		<?php if ( count( $v7_shots ) > 1 ) : ?>
			<span class="v7card__dots" aria-hidden="true">
				<?php foreach ( $v7_shots as $i => $shot ) : ?>
					<span class="v7card__dot<?php echo 0 === $i ? ' is-on' : ''; ?>"></span>
				<?php endforeach; ?>
			</span>
		<?php endif; ?>
	</a>
	<div class="v7card__meta">
		<span class="v7card__eyebrow"><?php echo esc_html( skyyrose_v7_coll_label( $v7_collection ) ); ?></span>
		<h3 class="v7card__name"><a href="<?php echo esc_url( $v7_permalink ); ?>"><?php echo esc_html( $v7_name ); ?></a></h3>
		<div class="v7card__pricerow">
			<span class="v7card__price"><?php echo wp_kses_post( $v7_price_html ); ?></span>
			<?php if ( $v7_edition ) : ?>
				<span class="v7card__edition"><?php echo esc_html( 'ED. ' . $v7_edition ); ?></span>
			<?php endif; ?>
		</div>
		<?php
		if ( $v7_product instanceof WC_Product && $v7_product->is_purchasable() && $v7_product->is_in_stock() && ! $v7_preorder && $v7_product->is_type( 'simple' ) ) {
			// Editorial posture (WS5): primary action views the piece; AJAX
			// quick-add is secondary. The quick-add href is the PDP no-JS
			// fallback — never a GET ?add-to-cart= URL (crawler cart-adds,
			// cache poisoning). WooCommerce's add-to-cart.js reads
			// data-product_id, not the href.
			printf(
				'<a class="v7card__add" data-magnetic href="%s">%s</a>',
				esc_url( $v7_permalink ),
				esc_html__( 'View Piece', 'skyyrose' )
			);
			printf(
				'<a href="%s" data-quantity="1" data-product_id="%d" data-magnetic class="v7card__quickadd button add_to_cart_button ajax_add_to_cart" rel="nofollow">%s</a>',
				esc_url( $v7_permalink ),
				absint( $v7_product->get_id() ),
				esc_html__( 'Quick Add', 'skyyrose' )
			);
		} else {
			printf(
				'<a class="v7card__add" data-magnetic href="%s">%s</a>',
				esc_url( $v7_permalink ),
				$v7_preorder ? esc_html__( 'Pre-Order', 'skyyrose' ) : esc_html__( 'View', 'skyyrose' )
			);
		}
		?>
	</div>
</article>
