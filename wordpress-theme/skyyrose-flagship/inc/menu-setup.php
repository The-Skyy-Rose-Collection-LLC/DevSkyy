<?php
/**
 * Programmatic Navigation Menu Setup
 *
 * Creates and assigns menus to registered locations on theme activation.
 * Runs once via `after_switch_theme` and can be re-triggered via
 * `skyyrose_setup_menus()` manually.
 *
 * @package SkyyRose
 * @since   3.2.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Create navigation menus and assign to theme locations.
 *
 * Safe to call multiple times — skips menus that already exist.
 */
function skyyrose_setup_menus() {
	$menus = skyyrose_get_menu_definitions();

	foreach ( $menus as $location => $menu_data ) {
		$menu_name = $menu_data['name'];
		$menu_obj  = wp_get_nav_menu_object( $menu_name );

		if ( ! $menu_obj ) {
			$menu_id = wp_create_nav_menu( $menu_name );
			if ( is_wp_error( $menu_id ) ) {
				continue;
			}
		} else {
			$menu_id = $menu_obj->term_id;
		}

		// Only add items if the menu is empty (don't duplicate).
		$existing_items = wp_get_nav_menu_items( $menu_id );
		if ( empty( $existing_items ) && ! empty( $menu_data['items'] ) ) {
			foreach ( $menu_data['items'] as $item ) {
				$args = array(
					'menu-item-title'  => $item['title'],
					'menu-item-url'    => home_url( $item['url'] ),
					'menu-item-status' => 'publish',
					'menu-item-type'   => 'custom',
				);

				if ( ! empty( $item['parent_id'] ) ) {
					$args['menu-item-parent-id'] = $item['parent_id'];
				}

				$item_id = wp_update_nav_menu_item( $menu_id, 0, $args );

				// Store item ID for children to reference.
				if ( ! is_wp_error( $item_id ) && ! empty( $item['children'] ) ) {
					foreach ( $item['children'] as $child ) {
						wp_update_nav_menu_item(
							$menu_id,
							0,
							array(
								'menu-item-title'     => $child['title'],
								'menu-item-url'       => home_url( $child['url'] ),
								'menu-item-status'    => 'publish',
								'menu-item-type'      => 'custom',
								'menu-item-parent-id' => $item_id,
							)
						);
					}
				}
			}
		}

		// Assign menu to theme location.
		$locations              = get_theme_mod( 'nav_menu_locations', array() );
		$locations[ $location ] = $menu_id;
		set_theme_mod( 'nav_menu_locations', $locations );
	}
}

/**
 * Menu definitions: location => name + items.
 *
 * @return array
 */
function skyyrose_get_menu_definitions() {
	return array(
		'primary'      => array(
			'name'  => __( 'Primary Menu', 'skyyrose' ),
			'items' => array(
				array(
					'title' => __( 'Home', 'skyyrose' ),
					'url'   => '/',
				),
				array(
					'title'    => __( 'Collections', 'skyyrose' ),
					'url'      => '/collections/',
					'children' => array(
						array(
							'title' => __( 'Black Rose', 'skyyrose' ),
							'url'   => '/collection-black-rose/',
						),
						array(
							'title' => __( 'Love Hurts', 'skyyrose' ),
							'url'   => '/collection-love-hurts/',
						),
						array(
							'title' => __( 'Signature', 'skyyrose' ),
							'url'   => '/collection-signature/',
						),
						array(
							'title' => __( 'Kids Capsule', 'skyyrose' ),
							'url'   => '/collection-kids-capsule/',
						),
					),
				),
				array(
					'title'    => __( 'Experiences', 'skyyrose' ),
					'url'      => '/experiences/',
					'children' => array(
						array(
							'title' => __( 'The Garden', 'skyyrose' ),
							'url'   => '/experience-black-rose/',
						),
						array(
							'title' => __( 'The Ballroom', 'skyyrose' ),
							'url'   => '/experience-love-hurts/',
						),
						array(
							'title' => __( 'The Runway', 'skyyrose' ),
							'url'   => '/experience-signature/',
						),
						array(
							'title' => __( 'Heir Apparent', 'skyyrose' ),
							'url'   => '/experience-kids-capsule/',
						),
					),
				),
				array(
					'title' => __( 'Pre-Order', 'skyyrose' ),
					'url'   => '/pre-order/',
				),
				array(
					'title' => __( 'About', 'skyyrose' ),
					'url'   => '/about/',
				),
				array(
					'title' => __( 'Contact', 'skyyrose' ),
					'url'   => '/contact/',
				),
			),
		),
		'footer'       => array(
			'name'  => __( 'Footer Menu', 'skyyrose' ),
			'items' => array(
				array(
					'title' => __( 'About', 'skyyrose' ),
					'url'   => '/about/',
				),
				array(
					'title' => __( 'Contact', 'skyyrose' ),
					'url'   => '/contact/',
				),
				array(
					'title' => __( 'FAQ', 'skyyrose' ),
					'url'   => '/contact/#faq',
				),
				array(
					'title' => __( 'Privacy Policy', 'skyyrose' ),
					'url'   => '/privacy-policy/',
				),
				array(
					'title' => __( 'Terms of Service', 'skyyrose' ),
					'url'   => '/terms-of-service/',
				),
			),
		),
		'footer-legal' => array(
			'name'  => __( 'Footer - Legal', 'skyyrose' ),
			'items' => array(
				array(
					'title' => __( 'Privacy Policy', 'skyyrose' ),
					'url'   => '/privacy-policy/',
				),
				array(
					'title' => __( 'Terms of Service', 'skyyrose' ),
					'url'   => '/terms-of-service/',
				),
			),
		),
		'mobile'       => array(
			'name'  => __( 'Mobile Menu', 'skyyrose' ),
			'items' => array(
				array(
					'title' => __( 'Home', 'skyyrose' ),
					'url'   => '/',
				),
				array(
					'title'    => __( 'Collections', 'skyyrose' ),
					'url'      => '/collections/',
					'children' => array(
						array(
							'title' => __( 'Black Rose', 'skyyrose' ),
							'url'   => '/collection-black-rose/',
						),
						array(
							'title' => __( 'Love Hurts', 'skyyrose' ),
							'url'   => '/collection-love-hurts/',
						),
						array(
							'title' => __( 'Signature', 'skyyrose' ),
							'url'   => '/collection-signature/',
						),
						array(
							'title' => __( 'Kids Capsule', 'skyyrose' ),
							'url'   => '/collection-kids-capsule/',
						),
					),
				),
				array(
					'title'    => __( 'Experiences', 'skyyrose' ),
					'url'      => '/experiences/',
					'children' => array(
						array(
							'title' => __( 'The Garden', 'skyyrose' ),
							'url'   => '/experience-black-rose/',
						),
						array(
							'title' => __( 'The Ballroom', 'skyyrose' ),
							'url'   => '/experience-love-hurts/',
						),
						array(
							'title' => __( 'The Runway', 'skyyrose' ),
							'url'   => '/experience-signature/',
						),
						array(
							'title' => __( 'Heir Apparent', 'skyyrose' ),
							'url'   => '/experience-kids-capsule/',
						),
					),
				),
				array(
					'title' => __( 'Pre-Order', 'skyyrose' ),
					'url'   => '/pre-order/',
				),
				array(
					'title' => __( 'About', 'skyyrose' ),
					'url'   => '/about/',
				),
				array(
					'title' => __( 'Contact', 'skyyrose' ),
					'url'   => '/contact/',
				),
			),
		),
		'collection'   => array(
			'name'  => __( 'Collection Navigation', 'skyyrose' ),
			'items' => array(
				array(
					'title' => __( 'Black Rose', 'skyyrose' ),
					'url'   => '/collection-black-rose/',
				),
				array(
					'title' => __( 'Love Hurts', 'skyyrose' ),
					'url'   => '/collection-love-hurts/',
				),
				array(
					'title' => __( 'Signature', 'skyyrose' ),
					'url'   => '/collection-signature/',
				),
				array(
					'title' => __( 'Kids Capsule', 'skyyrose' ),
					'url'   => '/collection-kids-capsule/',
				),
			),
		),
		'experiences'  => array(
			'name'  => __( 'Experiences Navigation', 'skyyrose' ),
			'items' => array(
				array(
					'title' => __( 'The Garden', 'skyyrose' ),
					'url'   => '/experience-black-rose/',
				),
				array(
					'title' => __( 'The Ballroom', 'skyyrose' ),
					'url'   => '/experience-love-hurts/',
				),
				array(
					'title' => __( 'The Runway', 'skyyrose' ),
					'url'   => '/experience-signature/',
				),
				array(
					'title' => __( 'Heir Apparent', 'skyyrose' ),
					'url'   => '/experience-kids-capsule/',
				),
			),
		),
	);
}

// Run on theme activation.
add_action( 'after_switch_theme', 'skyyrose_setup_menus' );

// Also run on `init` with a one-time flag so menus are created
// even if theme was already active before this file was deployed.
// Bump version to v400 to re-run with corrected URLs.
add_action(
	'init',
	function () {
		if ( get_option( 'skyyrose_menus_setup_v620' ) ) {
			return;
		}
		skyyrose_setup_menus();
		update_option( 'skyyrose_menus_setup_v620', true );
	}
);
