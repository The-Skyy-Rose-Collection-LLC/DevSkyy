<?php
/**
 * Product Taxonomy Setup
 *
 * Registers product categories, tags, and a fallback custom taxonomy
 * when WooCommerce is not active. Ensures the SkyyRose collection
 * hierarchy and product tags exist in the database.
 *
 * @package SkyyRose_Flagship
 * @since   3.1.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*
--------------------------------------------------------------
 * Fallback Taxonomy (when WooCommerce is NOT active)
 *--------------------------------------------------------------*/

/**
 * Register a fallback product tag taxonomy when WooCommerce is not available.
 *
 * This allows the theme to categorize products even without WooCommerce,
 * enabling graceful degradation for development and staging environments.
 *
 * @since 3.1.0
 * @return void
 */
function skyyrose_register_fallback_product_tag() {

	if ( class_exists( 'WooCommerce' ) ) {
		return;
	}

	if ( taxonomy_exists( 'skyyrose_product_tag' ) ) {
		return;
	}

	$labels = array(
		'name'                       => esc_html_x( 'Product Tags', 'taxonomy general name', 'skyyrose' ),
		'singular_name'              => esc_html_x( 'Product Tag', 'taxonomy singular name', 'skyyrose' ),
		'search_items'               => esc_html__( 'Search Product Tags', 'skyyrose' ),
		'popular_items'              => esc_html__( 'Popular Product Tags', 'skyyrose' ),
		'all_items'                  => esc_html__( 'All Product Tags', 'skyyrose' ),
		'edit_item'                  => esc_html__( 'Edit Product Tag', 'skyyrose' ),
		'update_item'                => esc_html__( 'Update Product Tag', 'skyyrose' ),
		'add_new_item'               => esc_html__( 'Add New Product Tag', 'skyyrose' ),
		'new_item_name'              => esc_html__( 'New Product Tag Name', 'skyyrose' ),
		'separate_items_with_commas' => esc_html__( 'Separate product tags with commas', 'skyyrose' ),
		'add_or_remove_items'        => esc_html__( 'Add or remove product tags', 'skyyrose' ),
		'choose_from_most_used'      => esc_html__( 'Choose from the most used product tags', 'skyyrose' ),
		'not_found'                  => esc_html__( 'No product tags found.', 'skyyrose' ),
		'menu_name'                  => esc_html__( 'Product Tags', 'skyyrose' ),
	);

	$args = array(
		'hierarchical'      => false,
		'labels'            => $labels,
		'show_ui'           => true,
		'show_admin_column' => true,
		'show_in_rest'      => true,
		'query_var'         => true,
		'rewrite'           => array( 'slug' => 'product-tag' ),
	);

	register_taxonomy( 'skyyrose_product_tag', array( 'product', 'post' ), $args );
}
add_action( 'init', 'skyyrose_register_fallback_product_tag', 20 );

/*
--------------------------------------------------------------
 * WooCommerce Product Categories
 *--------------------------------------------------------------*/

/**
 * Programmatically create the SkyyRose collection categories.
 *
 * Creates the parent "Shop" category and child collection categories
 * (Black Rose, Love Hurts, Signature, Kids Capsule). Uses existence
 * checks to prevent duplicate creation.
 *
 * @since 3.1.0
 * @return void
 */
function skyyrose_create_product_categories() {

	if ( ! class_exists( 'WooCommerce' ) ) {
		return;
	}

	if ( ! taxonomy_exists( 'product_cat' ) ) {
		return;
	}

	// Define the parent category.
	$parent_slug = 'shop';
	$parent_term = term_exists( $parent_slug, 'product_cat' );

	if ( ! $parent_term ) {
		$parent_term = wp_insert_term(
			__( 'Shop', 'skyyrose' ),
			'product_cat',
			array(
				'slug'        => $parent_slug,
				'description' => __( 'All SkyyRose products.', 'skyyrose' ),
			)
		);
	}

	if ( is_wp_error( $parent_term ) ) {
		return;
	}

	$parent_id = is_array( $parent_term ) ? $parent_term['term_id'] : $parent_term;

	// Define child collection categories.
	$collections = array(
		'black-rose'   => array(
			'name'        => __( 'Black Rose', 'skyyrose' ),
			'description' => __( 'Dark elegance meets luxury streetwear. Cathedral-inspired pieces for the bold.', 'skyyrose' ),
		),
		'love-hurts'   => array(
			'name'        => __( 'Love Hurts', 'skyyrose' ),
			'description' => __( 'Where passion meets pain. Castle-themed pieces that tell a story of love and resilience.', 'skyyrose' ),
		),
		'signature'    => array(
			'name'        => __( 'Signature', 'skyyrose' ),
			'description' => __( 'The quintessential SkyyRose experience. City-inspired luxury for every day.', 'skyyrose' ),
		),
		'kids-capsule' => array(
			'name'        => __( 'Kids Capsule', 'skyyrose' ),
			'description' => __( 'Luxury fashion for the next generation. Where love meets comfort.', 'skyyrose' ),
		),
	);

	foreach ( $collections as $slug => $data ) {
		if ( ! term_exists( $slug, 'product_cat' ) ) {
			wp_insert_term(
				$data['name'],
				'product_cat',
				array(
					'slug'        => $slug,
					'description' => $data['description'],
					'parent'      => absint( $parent_id ),
				)
			);
		}
	}
}
add_action( 'init', 'skyyrose_create_product_categories', 20 );

/*
--------------------------------------------------------------
 * WooCommerce Product Tags
 *--------------------------------------------------------------*/

/**
 * Programmatically create the SkyyRose product tags.
 *
 * Creates product tags for filtering, merchandising, and discovery.
 * Uses existence checks to prevent duplicate creation.
 *
 * @since 3.1.0
 * @return void
 */
function skyyrose_create_product_tags() {

	if ( ! class_exists( 'WooCommerce' ) ) {
		return;
	}

	if ( ! taxonomy_exists( 'product_tag' ) ) {
		return;
	}

	$tags = array(
		'limited-edition' => __( 'Limited Edition', 'skyyrose' ),
		'bestseller'      => __( 'Bestseller', 'skyyrose' ),
		'new-arrival'     => __( 'New Arrival', 'skyyrose' ),
		'pre-order'       => __( 'Pre-Order', 'skyyrose' ),
		'collaboration'   => __( 'Collaboration', 'skyyrose' ),
		'collab'          => __( 'Collab', 'skyyrose' ),
		'hoodie'          => __( 'Hoodie', 'skyyrose' ),
		'jogger'          => __( 'Jogger', 'skyyrose' ),
		'crewneck'        => __( 'Crewneck', 'skyyrose' ),
		'jacket'          => __( 'Jacket', 'skyyrose' ),
		'dress'           => __( 'Dress', 'skyyrose' ),
		'shorts'          => __( 'Shorts', 'skyyrose' ),
		'beanie'          => __( 'Beanie', 'skyyrose' ),
		'jersey'          => __( 'Jersey', 'skyyrose' ),
		'set'             => __( 'Set', 'skyyrose' ),
		'tee'             => __( 'Tee', 'skyyrose' ),
		'sherpa'          => __( 'Sherpa', 'skyyrose' ),
	);

	foreach ( $tags as $slug => $name ) {
		if ( ! term_exists( $slug, 'product_tag' ) ) {
			wp_insert_term(
				$name,
				'product_tag',
				array(
					'slug' => $slug,
				)
			);
		}
	}
}
add_action( 'init', 'skyyrose_create_product_tags', 20 );
