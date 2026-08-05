<?php
/**
 * Shared Collections index world.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;
?>
<section class="sr2-page-hero sr2-page-hero--collections" aria-labelledby="sr2-page-title">
	<div class="sr2-page-hero__media"><img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'branding/hero/signature-golden-gate-yacht-1280w.webp' ) ); ?>" alt="" width="1280" height="553" fetchpriority="high"></div>
	<div class="sr2-page-hero__copy"><p class="sr2-eyebrow"><?php esc_html_e( 'The House', 'skyyrose-flagship-2' ); ?></p><h1 id="sr2-page-title"><?php esc_html_e( 'Every collection opens another world.', 'skyyrose-flagship-2' ); ?></h1><p><?php esc_html_e( 'Signature begins the story. Black Rose protects it. Love Hurts tells the truth. Kids Capsule carries it forward.', 'skyyrose-flagship-2' ); ?></p></div>
</section>
<?php skyyrose2_render_collection_rail(); ?>
<section class="sr2-section sr2-section--products"><header class="sr2-section-head"><p><?php esc_html_e( 'Across the House', 'skyyrose-flagship-2' ); ?></p><h2><?php esc_html_e( 'Find your chapter.', 'skyyrose-flagship-2' ); ?></h2></header><?php skyyrose2_product_cards( 9 ); ?></section>
