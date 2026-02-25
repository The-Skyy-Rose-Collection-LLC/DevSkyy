<?php
/**
 * Programmatic Navigation Menu Setup
 *
 * Creates and assigns menus to registered locations on theme activation.
 * Runs once via `after_switch_theme` and can be re-triggered via
 * `skyyrose_setup_menus()` manually.
 *
 * @package SkyyRose_Flagship
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
			'name'  => 'Primary Menu',
			'items' => array(
				array(
					'title' => 'Home',
					'url'   => '/',
				),
				array(
					'title'    => 'Collections',
					'url'      => '/collections/',
					'children' => array(
						array(
							'title' => 'Black Rose',
							'url'   => '/collection-black-rose/',
						),
						array(
							'title' => 'Love Hurts',
							'url'   => '/collection-love-hurts/',
						),
						array(
							'title' => 'Signature',
							'url'   => '/collection-signature/',
						),
						array(
							'title' => 'Kids Capsule',
							'url'   => '/collection-kids-capsule/',
						),
					),
				),
				array(
					'title'    => 'Experiences',
					'url'      => '#',
					'children' => array(
						array(
							'title' => 'The Garden',
							'url'   => '/experience-black-rose/',
						),
						array(
							'title' => 'The Ballroom',
							'url'   => '/experience-love-hurts/',
						),
						array(
							'title' => 'The Runway',
							'url'   => '/experience-signature/',
						),
					),
				),
				array(
					'title' => 'Pre-Order',
					'url'   => '/preorder/',
				),
				array(
					'title' => 'About',
					'url'   => '/about/',
				),
				array(
					'title' => 'Contact',
					'url'   => '/contact/',
				),
			),
		),
		'footer'       => array(
			'name'  => 'Footer Menu',
			'items' => array(
				array(
					'title' => 'About',
					'url'   => '/about/',
				),
				array(
					'title' => 'Contact',
					'url'   => '/contact/',
				),
				array(
					'title' => 'FAQ',
					'url'   => '/faq/',
				),
				array(
					'title' => 'Shipping & Returns',
					'url'   => '/shipping-returns/',
				),
				array(
					'title' => 'Privacy Policy',
					'url'   => '/privacy-policy/',
				),
				array(
					'title' => 'Terms of Service',
					'url'   => '/terms-of-service/',
				),
			),
		),
		'footer-shop'  => array(
			'name'  => 'Footer - Shop',
			'items' => array(
				array(
					'title' => 'Black Rose',
					'url'   => '/collection-black-rose/',
				),
				array(
					'title' => 'Love Hurts',
					'url'   => '/collection-love-hurts/',
				),
				array(
					'title' => 'Signature',
					'url'   => '/collection-signature/',
				),
				array(
					'title' => 'Pre-Order',
					'url'   => '/preorder/',
				),
			),
		),
		'footer-help'  => array(
			'name'  => 'Footer - Help',
			'items' => array(
				array(
					'title' => 'FAQ',
					'url'   => '/faq/',
				),
				array(
					'title' => 'Shipping & Returns',
					'url'   => '/shipping-returns/',
				),
				array(
					'title' => 'Contact',
					'url'   => '/contact/',
				),
			),
		),
		'footer-legal' => array(
			'name'  => 'Footer - Legal',
			'items' => array(
				array(
					'title' => 'Privacy Policy',
					'url'   => '/privacy-policy/',
				),
				array(
					'title' => 'Terms of Service',
					'url'   => '/terms-of-service/',
				),
			),
		),
		'mobile'       => array(
			'name'  => 'Mobile Menu',
			'items' => array(
				array(
					'title' => 'Home',
					'url'   => '/',
				),
				array(
					'title' => 'Collections',
					'url'   => '/collections/',
				),
				array(
					'title' => 'Black Rose',
					'url'   => '/collection-black-rose/',
				),
				array(
					'title' => 'Love Hurts',
					'url'   => '/collection-love-hurts/',
				),
				array(
					'title' => 'Signature',
					'url'   => '/collection-signature/',
				),
				array(
					'title' => 'Pre-Order',
					'url'   => '/preorder/',
				),
				array(
					'title' => 'About',
					'url'   => '/about/',
				),
				array(
					'title' => 'Contact',
					'url'   => '/contact/',
				),
			),
		),
		'collection'   => array(
			'name'  => 'Collection Navigation',
			'items' => array(
				array(
					'title' => 'Black Rose',
					'url'   => '/collection-black-rose/',
				),
				array(
					'title' => 'Love Hurts',
					'url'   => '/collection-love-hurts/',
				),
				array(
					'title' => 'Signature',
					'url'   => '/collection-signature/',
				),
				array(
					'title' => 'Kids Capsule',
					'url'   => '/collection-kids-capsule/',
				),
			),
		),
		'experiences'  => array(
			'name'  => 'Experiences Navigation',
			'items' => array(
				array(
					'title' => 'The Garden',
					'url'   => '/experience-black-rose/',
				),
				array(
					'title' => 'The Ballroom',
					'url'   => '/experience-love-hurts/',
				),
				array(
					'title' => 'The Runway',
					'url'   => '/experience-signature/',
				),
			),
		),
	);
}

// Run on theme activation.
add_action( 'after_switch_theme', 'skyyrose_setup_menus' );

// Also run on `init` with a one-time flag so menus are created
// even if theme was already active before this file was deployed.
add_action(
	'init',
	function () {
		if ( get_option( 'skyyrose_menus_setup_v320' ) ) {
			return;
		}
		skyyrose_setup_menus();
		update_option( 'skyyrose_menus_setup_v320', true );
	}
);
