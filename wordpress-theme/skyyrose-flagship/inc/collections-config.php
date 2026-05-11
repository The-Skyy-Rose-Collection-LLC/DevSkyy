<?php
/**
 * Collections Configuration — Single Source of Truth
 *
 * All collection metadata (slug, label, colors, tagline, description, palette)
 * lives here. PHP templates should reference this config instead of hardcoding
 * collection data in multiple places (404.php, front-page.php, template-functions.php).
 *
 * Depends on inc/brand-colors.php for color constants.
 *
 * @package SkyyRose
 * @since   6.4.0
 */

defined( 'ABSPATH' ) || exit;

/**
 * Get the full configuration for all collections.
 *
 * Returns an immutable associative array keyed by collection slug. Each entry
 * contains label, slug, accent color, glow color, tagline, description,
 * and full color palette (primary/secondary/accent).
 *
 * @since  6.4.0
 * @return array<string, array<string, mixed>>
 */
function skyyrose_get_collections_config(): array {
	static $cache = null;
	if ( null !== $cache ) {
		return $cache;
	}

	$uri = defined( 'SKYYROSE_ASSETS_URI' ) ? SKYYROSE_ASSETS_URI : '';

	$cache = array(
		'black-rose'   => array(
			'slug'        => 'black-rose',
			'class_abbr'  => 'br',
			'label'       => __( 'Black Rose', 'skyyrose' ),
			'short_desc'  => __( 'Dark Elegance', 'skyyrose' ),
			'accent'      => SKYYROSE_COLOR_SILVER,
			'glow'        => skyyrose_hex_to_rgba( SKYYROSE_COLOR_SILVER, 0.3 ),
			'tagline'     => __( 'Gothic elegance, dark romance', 'skyyrose' ),
			'description' => __( 'Monochromatic pieces that channel mystery and silver-toned refinement.', 'skyyrose' ),
			'page_url'    => home_url( '/collection-black-rose/' ),
			'palette'     => array(
				'primary'   => SKYYROSE_COLOR_DEEP_BLACK,
				'secondary' => SKYYROSE_COLOR_NAVY,
				'accent'    => SKYYROSE_COLOR_DEEP_BLUE,
			),
			'front_page'  => array(
				'title'          => 'Black<br>Rose',
				'poetic_tagline' => __( 'For those who found power in the dark.', 'skyyrose' ),
				'label'          => __( 'Limited', 'skyyrose' ),
				'num'            => __( 'Collection 01', 'skyyrose' ),
				'image'          => $uri . '/images/homepage-col-black-rose.webp',
				'show_on_front'  => true,
			),
		),
		'love-hurts'   => array(
			'slug'        => 'love-hurts',
			'class_abbr'  => 'lh',
			'label'       => __( 'Love Hurts', 'skyyrose' ),
			'short_desc'  => __( 'Crimson Rebellion', 'skyyrose' ),
			'accent'      => SKYYROSE_COLOR_CRIMSON,
			'glow'        => skyyrose_hex_to_rgba( SKYYROSE_COLOR_CRIMSON, 0.3 ),
			'tagline'     => __( 'Dramatic, passionate, fearless', 'skyyrose' ),
			'description' => __( 'Bold crimson statements for those who wear their heart on their sleeve.', 'skyyrose' ),
			'page_url'    => home_url( '/collection-love-hurts/' ),
			'palette'     => array(
				'primary'   => SKYYROSE_COLOR_DEEP_RED,
				'secondary' => SKYYROSE_COLOR_PURPLE,
				'accent'    => SKYYROSE_COLOR_GOLD,
			),
			'front_page'  => array(
				'title'          => 'Love<br>Hurts',
				'poetic_tagline' => __( 'Wear your heart. Own your scars.', 'skyyrose' ),
				'label'          => __( 'Family Legacy', 'skyyrose' ),
				'num'            => __( 'Collection 02', 'skyyrose' ),
				'image'          => $uri . '/images/homepage-col-love-hurts.webp',
				'show_on_front'  => true,
			),
		),
		'signature'    => array(
			'slug'        => 'signature',
			'class_abbr'  => 'sg',
			'label'       => __( 'Signature', 'skyyrose' ),
			'short_desc'  => __( 'The Foundation', 'skyyrose' ),
			'accent'      => SKYYROSE_COLOR_GOLD,
			'glow'        => skyyrose_hex_to_rgba( SKYYROSE_COLOR_GOLD, 0.3 ),
			'tagline'     => __( 'Elevated, confident, refined', 'skyyrose' ),
			'description' => __( 'Gold luxe essentials for building the foundation wardrobe.', 'skyyrose' ),
			'page_url'    => home_url( '/collection-signature/' ),
			'palette'     => array(
				'primary'   => SKYYROSE_COLOR_GOLD,
				'secondary' => SKYYROSE_COLOR_DARK,
				'accent'    => SKYYROSE_COLOR_ROSE_GOLD,
			),
			'front_page'  => array(
				'title'          => 'Signature',
				'poetic_tagline' => __( 'The foundation of any wardrobe worth building.', 'skyyrose' ),
				'label'          => __( 'Everyday Luxury', 'skyyrose' ),
				'num'            => __( 'Collection 03', 'skyyrose' ),
				'image'          => $uri . '/images/homepage-col-signature.webp',
				'show_on_front'  => true,
			),
		),
		'kids-capsule' => array(
			'slug'        => 'kids-capsule',
			'class_abbr'  => 'kc',
			'label'       => __( 'Kids Capsule', 'skyyrose' ),
			'short_desc'  => __( 'Next Generation', 'skyyrose' ),
			'accent'      => SKYYROSE_COLOR_SOFT_PINK,
			'glow'        => skyyrose_hex_to_rgba( SKYYROSE_COLOR_SOFT_PINK, 0.3 ),
			'tagline'     => __( 'Joyful luxury, playful sophistication', 'skyyrose' ),
			'description' => __( 'Mini versions of our signature pieces for the youngest trendsetters.', 'skyyrose' ),
			'page_url'    => home_url( '/collection-kids-capsule/' ),
			'palette'     => array(
				'primary'   => SKYYROSE_COLOR_SOFT_PINK,
				'secondary' => SKYYROSE_COLOR_LAVENDER,
				'accent'    => SKYYROSE_COLOR_GOLD,
			),
			'front_page'  => array(
				'title'          => 'Kids<br>Capsule',
				'poetic_tagline' => __( 'For the next generation of legacy.', 'skyyrose' ),
				'label'          => __( 'Kids', 'skyyrose' ),
				'num'            => __( 'Collection 04', 'skyyrose' ),
				'image'          => $uri . '/images/homepage-col-kids-capsule.webp',
				'show_on_front'  => true,
			),
		),
	);

	return $cache;
}

/**
 * Get cross-navigation entries (all collections EXCEPT the current one).
 *
 * Used by template-collection-*.php files to build cross-nav links.
 *
 * @since  6.4.0
 * @param  string $exclude_slug Slug of the current collection to exclude.
 * @return array<int, array<string, string>> List of cross-nav entries.
 */
function skyyrose_get_cross_nav( string $exclude_slug ): array {
	$configs = skyyrose_get_collections_config();
	$out     = array();
	foreach ( $configs as $slug => $config ) {
		if ( $slug === $exclude_slug ) {
			continue;
		}
		$out[] = array(
			'slug'  => 'collection-' . $slug,
			'name'  => $config['label'],
			'desc'  => $config['short_desc'],
			'class' => 'col-crossnav__link--' . $slug,
		);
	}
	return $out;
}

/**
 * Get front-page display data (only collections with show_on_front=true).
 *
 * @since  6.4.0
 * @return array<int, array<string, mixed>> Front-page collection entries.
 */
function skyyrose_get_front_page_collections(): array {
	$configs = skyyrose_get_collections_config();
	$out     = array();
	foreach ( $configs as $slug => $config ) {
		if ( empty( $config['front_page']['show_on_front'] ) ) {
			continue;
		}
		$fp    = $config['front_page'];
		$out[] = array(
			'slug'    => $slug,
			'class'   => $config['class_abbr'],
			'name'    => $config['label'],
			'title'   => $fp['title'],
			'tagline' => $fp['poetic_tagline'],
			'label'   => $fp['label'],
			'num'     => $fp['num'],
			'link'    => $config['page_url'],
			'image'   => $fp['image'],
		);
	}
	return $out;
}

/**
 * Get configuration for a single collection by slug.
 *
 * @since  6.4.0
 * @param  string $slug Collection slug.
 * @return array<string, mixed>|null Config array, or null if slug not found.
 */
function skyyrose_get_collection( string $slug ): ?array {
	$configs   = skyyrose_get_collections_config();
	$sanitized = sanitize_key( $slug );
	return $configs[ $sanitized ] ?? null;
}

/**
 * Get a specific field from a collection config.
 *
 * @since  6.4.0
 * @param  string $slug    Collection slug.
 * @param  string $field   Field name (label, accent, tagline, etc.).
 * @param  mixed  $default Default value if collection or field not found.
 * @return mixed Field value or default.
 */
function skyyrose_get_collection_field( string $slug, string $field, $default = null ) {
	$config = skyyrose_get_collection( $slug );
	return $config[ $field ] ?? $default;
}
