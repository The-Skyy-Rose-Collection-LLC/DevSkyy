<?php
/**
 * Storefront Data
 *
 * Shared social, sizing, and default-navigation data used across templates.
 *
 * @package SkyyRose
 * @since   7.1.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Get the centralized social media links array.
 *
 * @since 3.2.2
 * @return array Associative array of social links keyed by platform.
 */
function skyyrose_get_social_links() {
	$defaults = array(
		'instagram' => array(
			'url'   => 'https://instagram.com/skyyrose.co',
			'label' => __( 'Instagram', 'skyyrose' ),
		),
		'tiktok'    => array(
			'url'   => 'https://tiktok.com/@skyyroseco',
			'label' => __( 'TikTok', 'skyyrose' ),
		),
		'twitter'   => array(
			'url'   => 'https://x.com/skyyroseco',
			'label' => __( 'X (Twitter)', 'skyyrose' ),
		),
		'facebook'  => array(
			'url'   => 'https://facebook.com/TheSkyyRoseCollection',
			'label' => __( 'Facebook', 'skyyrose' ),
		),
	);

	$links = array();
	foreach ( $defaults as $network => $data ) {
		$override = get_theme_mod( 'skyyrose_social_' . $network, '' );
		if ( ! empty( $override ) ) {
			$data['url'] = esc_url_raw( $override );
		}
		$links[ $network ] = $data;
	}

	return $links;
}

/**
 * Get the size-guide measurement tables.
 *
 * @since 1.8.0
 * @return array Tables keyed by category: label, headers, rows.
 */
function skyyrose_get_size_guide_tables() {
	return array(
		'tops'    => array(
			'label'   => __( 'Tops', 'skyyrose' ),
			'headers' => array( 'Size', 'Chest', 'Waist', 'Length', 'Sleeve' ),
			'rows'    => array(
				array( 'XS', '34', '28', '27', '32' ),
				array( 'S', '36', '30', '28', '33' ),
				array( 'M', '38', '32', '29', '34' ),
				array( 'L', '40', '34', '30', '35' ),
				array( 'XL', '42', '36', '31', '35.5' ),
				array( '2XL', '44', '38', '32', '36' ),
			),
		),
		'bottoms' => array(
			'label'   => __( 'Bottoms', 'skyyrose' ),
			'headers' => array( 'Size', 'Waist', 'Hip', 'Inseam', 'Length' ),
			'rows'    => array(
				array( 'XS', '28', '34', '30', '38' ),
				array( 'S', '30', '36', '31', '39' ),
				array( 'M', '32', '38', '32', '40' ),
				array( 'L', '34', '40', '32', '41' ),
				array( 'XL', '36', '42', '33', '42' ),
				array( '2XL', '38', '44', '33', '43' ),
			),
		),
		'kids'    => array(
			'label'   => __( 'Kids', 'skyyrose' ),
			'headers' => array( 'Size', 'Age', 'Chest', 'Waist', 'Height' ),
			'rows'    => array(
				array( '2T', '2', '21', '20', '33-36' ),
				array( '3T', '3', '22', '20.5', '36-39' ),
				array( '4T', '4', '23', '21', '39-42' ),
				array( '5', '5-6', '24', '21.5', '42-45' ),
				array( '6', '6-7', '25', '22', '45-48' ),
			),
		),
	);
}

/**
 * Canonical primary navigation shared by setup, fallbacks, and custom canvases.
 *
 * @since 7.1.0
 * @return array<int,array<string,mixed>>
 */
function skyyrose_get_primary_navigation_items() {
	return array(
		array(
			'title' => __( 'Shop', 'skyyrose' ),
			'url'   => '/shop/',
		),
		array(
			'title'    => __( 'Collections', 'skyyrose' ),
			'url'      => '/collections/',
			'children' => array(
				array(
					'title' => __( 'Collections World', 'skyyrose' ),
					'url'   => '/collections-world/',
				),
				array(
					'title' => __( 'Signature', 'skyyrose' ),
					'url'   => '/collections/signature/',
				),
				array(
					'title' => __( 'Black Rose', 'skyyrose' ),
					'url'   => '/collections/black-rose/',
				),
				array(
					'title' => __( 'Love Hurts', 'skyyrose' ),
					'url'   => '/collections/love-hurts/',
				),
				array(
					'title' => __( 'Kids Capsule', 'skyyrose' ),
					'url'   => '/collections/kids-capsule/',
				),
			),
		),
		array(
			'title' => __( 'Pre-Order', 'skyyrose' ),
			'url'   => '/pre-order/',
		),
		array(
			'title' => __( 'Size Guide', 'skyyrose' ),
			'url'   => '/size-guide/',
		),
		array(
			'title' => __( 'Our Story', 'skyyrose' ),
			'url'   => '/about/',
		),
		array(
			'title' => __( 'Contact', 'skyyrose' ),
			'url'   => '/contact/',
		),
		array(
			'title' => __( 'Wishlist', 'skyyrose' ),
			'url'   => '/wishlist/',
		),
	);
}

/**
 * Quick marketplace navigation used in site-wide footer and page upgrades.
 *
 * Keeps high-value routes visible on every page, independent of assigned
 * WordPress menu state.
 *
 * @since 7.2.0
 * @return array<int,array<string,string>>
 */
function skyyrose_get_marketplace_navigation_items() {
	return array(
		array(
			'title' => __( 'Shop All', 'skyyrose' ),
			'url'   => '/shop/',
		),
		array(
			'title' => __( 'Collections World', 'skyyrose' ),
			'url'   => '/collections-world/',
		),
		array(
			'title' => __( 'Wishlist', 'skyyrose' ),
			'url'   => '/wishlist/',
		),
		array(
			'title' => __( 'Size Guide', 'skyyrose' ),
			'url'   => '/size-guide/',
		),
		array(
			'title' => __( 'Shipping & Returns', 'skyyrose' ),
			'url'   => '/shipping-returns/',
		),
		array(
			'title' => __( 'Contact', 'skyyrose' ),
			'url'   => '/contact/',
		),
	);
}

/**
 * Render fallback navigation when no custom menu is assigned.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_nav_fallback() {
	$items = skyyrose_get_primary_navigation_items();

	echo '<ul class="navbar__menu">';

	foreach ( $items as $item ) {
		$has_children = ! empty( $item['children'] );
		$li_class     = $has_children ? ' class="menu-item menu-item-has-children"' : ' class="menu-item"';

		echo '<li' . $li_class . '>'; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- Hardcoded class string.
		echo '<a href="' . esc_url( home_url( $item['url'] ) ) . '">' . esc_html( $item['title'] ) . '</a>';

		if ( $has_children ) {
			echo '<ul class="sub-menu">';
			foreach ( $item['children'] as $child ) {
				echo '<li class="menu-item"><a href="' . esc_url( home_url( $child['url'] ) ) . '">' . esc_html( $child['title'] ) . '</a></li>';
			}
			echo '</ul>';
		}

		echo '</li>';
	}

	echo '</ul>';
}
