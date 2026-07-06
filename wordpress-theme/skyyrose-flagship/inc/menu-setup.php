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
 * Rebuild menu items for all registered locations.
 *
 * Deletes existing items and recreates them from the current definitions.
 * Gated on a version option so it fires exactly once per version bump —
 * mirrors the theme-activation-setup pattern.
 *
 * To re-run: change SKYYROSE_MENU_BUILD_VERSION to a new string value.
 *
 * @since 7.0.0
 * @return void
 */
function skyyrose_rebuild_menu_items() {
	$menus = skyyrose_get_menu_definitions();

	foreach ( $menus as $location => $menu_data ) {
		$menu_obj = wp_get_nav_menu_object( $menu_data['name'] );
		if ( ! $menu_obj ) {
			continue;
		}
		$menu_id = $menu_obj->term_id;

		// Delete all existing items so the current definitions take effect.
		$existing = wp_get_nav_menu_items( $menu_id );
		if ( $existing ) {
			foreach ( $existing as $existing_item ) {
				wp_delete_post( $existing_item->db_id, true );
			}
		}

		// Recreate items without the empty-check guard.
		if ( ! empty( $menu_data['items'] ) ) {
			foreach ( $menu_data['items'] as $item ) {
				$args    = array(
					'menu-item-title'  => $item['title'],
					'menu-item-url'    => home_url( $item['url'] ),
					'menu-item-status' => 'publish',
					'menu-item-type'   => 'custom',
				);
				$item_id = wp_update_nav_menu_item( $menu_id, 0, $args );

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
	}
}

// One-time rebuild trigger on init — bump SKYYROSE_MENU_BUILD_VERSION to re-run.
// Fires after skyyrose_setup_menus() (priority 20 vs 10) so menu objects exist.
define( 'SKYYROSE_MENU_BUILD_VERSION', 'v702' );

add_action(
	'init',
	function () {
		$flag = 'skyyrose_menu_rebuild_' . SKYYROSE_MENU_BUILD_VERSION;
		if ( get_option( $flag ) ) {
			return;
		}
		skyyrose_rebuild_menu_items();
		update_option( $flag, true );
	},
	20
);

/**
 * Menu definitions: location => name + items.
 *
 * @return array
 */
function skyyrose_get_menu_definitions() {
	return array(
		'primary' => array(
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
							'url'   => '/collections/black-rose/',
						),
						array(
							'title' => __( 'Love Hurts', 'skyyrose' ),
							'url'   => '/collections/love-hurts/',
						),
						array(
							'title' => __( 'Signature', 'skyyrose' ),
							'url'   => '/collections/signature/',
						),
						array(
							'title' => __( 'Kids Capsule', 'skyyrose' ),
							'url'   => '/collections/kids-capsule/',
						),
					),
				),
				// Experiences tree removed (structural remediation WS3) — each
				// experience is now the opening layer of its collection page.
				array(
					'title' => __( 'Pre-Order', 'skyyrose' ),
					'url'   => '/pre-order/',
				),
				array(
					'title' => __( 'Our Story', 'skyyrose' ),
					'url'   => '/about/',
				),
				array(
					'title' => __( 'Contact', 'skyyrose' ),
					'url'   => '/contact/',
				),
			),
		),
		'footer'  => array(
			'name'  => __( 'Footer Menu', 'skyyrose' ),
			'items' => array(
				array(
					'title' => __( 'Our Story', 'skyyrose' ),
					'url'   => '/about/',
				),
				array(
					'title' => __( 'Contact', 'skyyrose' ),
					'url'   => '/contact/',
				),
				array(
					'title' => __( 'FAQ', 'skyyrose' ),
					'url'   => '/faq/',
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
		// NOTE: 'footer-legal' location removed — it was never rendered in any template.
		// Footer legal links live in the 'footer' menu (rendered in footer.php:235)
		// and in the hardcoded footer-grid Legal column. No separate location needed.

		// NOTE: 'mobile' location removed — the mobile slide-in panel uses the
		// 'primary' location (header.php:110). A separate mobile menu object was DB
		// waste. If mobile and desktop menus ever need to diverge, register 'mobile'
		// in theme-setup.php and re-add it here.

		// 'collection' and 'experiences' locations removed (audit 2026-06-28).
		// These were never called by any template; removed from register_nav_menus()
		// in theme-setup.php in the same change. No live consumers confirmed.
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
