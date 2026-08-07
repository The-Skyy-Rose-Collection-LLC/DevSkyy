<?php
/**
 * Collection-aware single product experience.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

get_header();

while ( have_posts() ) :
	the_post();
	$product     = wc_get_product( get_the_ID() );
	$collections = skyyrose2_collections();
	$active_slug = '';
	foreach ( array_keys( $collections ) as $collection_slug ) {
		$term_slugs = array( $collection_slug, str_replace( '-', '_', $collection_slug ), str_replace( '-', '', $collection_slug ) );
		if ( has_term( $term_slugs, 'product_cat', get_the_ID() ) ) {
			$active_slug = $collection_slug;
			break;
		}
	}
	$active_collection = $active_slug ? $collections[ $active_slug ] : null;
	?>
	<main id="primary" class="sr2-product-page"<?php echo $active_slug ? ' data-collection="' . esc_attr( $active_slug ) . '"' : ''; ?>>
		<nav class="sr2-product-crumb" aria-label="<?php esc_attr_e( 'Breadcrumb', 'skyyrose-flagship-2' ); ?>"><a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>"><?php esc_html_e( 'Shop', 'skyyrose-flagship-2' ); ?></a><span>/</span><?php if ( $active_collection ) : ?><a href="<?php echo esc_url( skyyrose2_collection_url( $active_slug ) ); ?>"><?php echo esc_html( $active_collection['name'] ); ?></a><span>/</span><?php endif; ?><span aria-current="page"><?php echo esc_html( $product ? $product->get_name() : get_the_title() ); ?></span></nav>
		<?php if ( $product && has_term( array( 'pre-order', 'preorder', 'pre_order' ), 'product_cat', get_the_ID() ) ) : ?><div class="sr2-product-release" role="note"><span><?php esc_html_e( 'Pre-order edition', 'skyyrose-flagship-2' ); ?></span><p><?php esc_html_e( 'Made for your order. Estimated fulfillment timing appears before checkout.', 'skyyrose-flagship-2' ); ?></p></div><?php endif; ?>
		<section class="sr2-product-shell">
			<?php wc_get_template_part( 'content', 'single-product' ); ?>
		</section>
		<?php if ( $active_collection ) : ?>
			<aside class="sr2-product-world" aria-label="<?php echo esc_attr( sprintf( __( 'About %s', 'skyyrose-flagship-2' ), $active_collection['name'] ) ); ?>">
				<div><p class="sr2-eyebrow"><?php echo esc_html( $active_collection['kicker'] ); ?></p><h2><?php echo esc_html( $active_collection['headline'] ); ?></h2><p><?php echo esc_html( $active_collection['manifesto'] ); ?></p><a class="sr2-text-link" href="<?php echo esc_url( skyyrose2_collection_url( $active_slug ) ); ?>"><?php esc_html_e( 'Enter full collection', 'skyyrose-flagship-2' ); ?> ↗</a></div>
				<img src="<?php echo esc_url( skyyrose2_sot_asset_uri( $active_collection['hero'] ) ); ?>" alt="" width="1280" height="720" loading="lazy" decoding="async">
			</aside>
		<?php endif; ?>
	</main>
	<?php
endwhile;

get_footer();
