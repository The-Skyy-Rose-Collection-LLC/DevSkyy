<?php
/**
 * WooCommerce Integration — Product page enhancements and data attributes.
 *
 * Hooks into WooCommerce templates to inject data attributes for JS modules,
 * add scroll storytelling markup, and enhance product cards with collection
 * awareness.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Woocommerce {

	private SEE_Plugin $plugin;

	public function __construct( SEE_Plugin $plugin ) {
		$this->plugin = $plugin;
	}

	public function register( SEE_Loader $loader ): void {
		// Product loop items — add data attributes for JS.
		$loader->add_filter( 'woocommerce_post_class', $this, 'add_product_classes', 10, 2 );
		$loader->add_action( 'woocommerce_before_shop_loop_item', $this, 'inject_product_data_attrs', 5 );
		$loader->add_action( 'woocommerce_after_shop_loop_item', $this, 'close_product_wrapper', 50 );

		// Single product page — scroll storytelling injection point.
		$loader->add_action( 'woocommerce_before_single_product_summary', $this, 'inject_scroll_story_start', 5 );
		$loader->add_action( 'woocommerce_after_single_product_summary', $this, 'inject_scroll_story_end', 5 );

		// After shop loop — curated recommendations section.
		$loader->add_action( 'woocommerce_after_shop_loop', $this, 'inject_curated_section', 20 );

		// Product card tracking attribute.
		$loader->add_action( 'woocommerce_before_shop_loop_item_title', $this, 'inject_tracking_attr', 1 );
	}

	/**
	 * Add SEE CSS classes to product loop items.
	 */
	public function add_product_classes( array $classes, $product ): array {
		$classes[] = 'see-product-card';

		$collection = $this->get_product_collection( $product );
		if ( $collection ) {
			$classes[] = 'see-collection-' . sanitize_html_class( $collection );
		}

		return $classes;
	}

	/**
	 * Open a wrapper with data attributes before each product in the loop.
	 */
	public function inject_product_data_attrs(): void {
		global $product;
		if ( ! $product ) {
			return;
		}

		$collection = $this->get_product_collection( $product );
		$sku        = $product->get_sku();
		$price      = $product->get_price();

		printf(
			'<div class="see-product-wrapper" data-see-track="product-%s" data-see-collection="%s" data-see-sku="%s" data-see-price="%s" data-product-id="%d">',
			esc_attr( $product->get_id() ),
			esc_attr( $collection ),
			esc_attr( $sku ),
			esc_attr( $price ),
			intval( $product->get_id() )
		);
	}

	public function close_product_wrapper(): void {
		echo '</div><!-- .see-product-wrapper -->';
	}

	/**
	 * Inject scroll storytelling container before product summary.
	 */
	public function inject_scroll_story_start(): void {
		global $product;
		if ( ! $product ) {
			return;
		}

		$collection = $this->get_product_collection( $product );
		$config     = $this->get_collection_accent( $collection );

		printf(
			'<div class="see-scroll-story" data-see-lazy-module="scroll-storyteller" data-see-collection="%s" style="--see-accent: %s;">',
			esc_attr( $collection ),
			esc_attr( $config['accent'] ?? '#B76E79' )
		);
	}

	public function inject_scroll_story_end(): void {
		echo '</div><!-- .see-scroll-story -->';
	}

	/**
	 * Inject curated recommendations placeholder after shop loop.
	 */
	public function inject_curated_section(): void {
		echo '<section class="see-curated-section" data-see-lazy-module="personalization">';
		echo '<div class="see-skeleton" style="height: 300px;" aria-hidden="true"></div>';
		echo '</section>';
	}

	/**
	 * Add tracking attribute to product thumbnails.
	 */
	public function inject_tracking_attr(): void {
		global $product;
		if ( $product ) {
			printf(
				'<span class="see-track-pixel" data-see-track="thumb-%s" style="display:none;"></span>',
				esc_attr( $product->get_sku() ?: $product->get_id() )
			);
		}
	}

	/*--------------------------------------------------------------
	 * Helpers
	 *--------------------------------------------------------------*/

	private function get_product_collection( $product ): string {
		if ( function_exists( 'skyyrose_get_product_collection' ) ) {
			$id = is_object( $product ) ? $product->get_id() : intval( $product );
			return skyyrose_get_product_collection( $id );
		}

		// Fallback: check product categories for collection slugs.
		$id   = is_object( $product ) ? $product->get_id() : intval( $product );
		$cats = wp_get_post_terms( $id, 'product_cat', array( 'fields' => 'slugs' ) );

		if ( is_wp_error( $cats ) ) {
			return '';
		}

		$known = array( 'black-rose', 'love-hurts', 'signature', 'kids-capsule' );
		foreach ( $cats as $slug ) {
			if ( in_array( $slug, $known, true ) ) {
				return $slug;
			}
		}

		return '';
	}

	private function get_collection_accent( string $collection ): array {
		if ( function_exists( 'skyyrose_collection_config' ) ) {
			return skyyrose_collection_config( $collection );
		}

		$defaults = array(
			'black-rose'   => array( 'accent' => '#C0C0C0' ),
			'love-hurts'   => array( 'accent' => '#DC143C' ),
			'signature'    => array( 'accent' => '#D4AF37' ),
			'kids-capsule' => array( 'accent' => '#FFB6C1' ),
		);

		return $defaults[ $collection ] ?? array( 'accent' => '#B76E79' );
	}
}
