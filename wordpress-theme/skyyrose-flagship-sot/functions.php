<?php
/**
 * SkyyRose Flagship SOT staging theme.
 *
 * @package SkyyRoseFlagshipSOT
 */

defined( 'ABSPATH' ) || exit;

define( 'SKYYROSESOT_VERSION', '0.1.0' );
define( 'SKYYROSESOT_URI', get_template_directory_uri() );

function skyyrosesot_source_dir() {
	return apply_filters( 'skyyrosesot_source_directory', WP_CONTENT_DIR . '/themes/skyyrose-flagship' );
}

function skyyrosesot_asset_uri( $resolved_path ) {
	$base = apply_filters( 'skyyrosesot_asset_base_uri', content_url( '/themes/skyyrose-flagship/assets' ) );
	return trailingslashit( $base ) . ltrim( $resolved_path, '/' );
}

function skyyrosesot_collection( $slug ) {
	$slug = sanitize_key( $slug );
	if ( '' === $slug ) {
		return array();
	}
	$cache_key = 'skyyrosesot_' . $slug;
	$cached    = wp_cache_get( $cache_key, 'skyyrosesot' );
	if ( false !== $cached ) {
		return $cached;
	}
	$file = trailingslashit( skyyrosesot_source_dir() ) . 'data/collections/' . $slug . '/sot.json';
	if ( ! is_readable( $file ) ) {
		wp_cache_set( $cache_key, array(), 'skyyrosesot' );
		return array();
	}
	// phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents
	$data = json_decode( file_get_contents( $file ), true );
	$data = is_array( $data ) ? $data : array();
	wp_cache_set( $cache_key, $data, 'skyyrosesot' );
	return $data;
}

function skyyrosesot_collections() {
	$slugs = array( 'signature', 'black-rose', 'love-hurts', 'kids-capsule' );
	return array_filter(
		array_combine(
			$slugs,
			array_map( 'skyyrosesot_collection', $slugs )
		)
	);
}

function skyyrosesot_resolved( $value ) {
	if ( ! is_array( $value ) ) {
		return '';
	}
	$resolved = $value['resolved'] ?? '';
	return is_string( $resolved ) ? ltrim( $resolved, '/' ) : '';
}

function skyyrosesot_first_image( $collection ) {
	$imagery = $collection['imagery'] ?? array();
	foreach ( array( 'scene_portrait', 'hero_backdrop', 'hero' ) as $key ) {
		$resolved = skyyrosesot_resolved( $imagery[ $key ] ?? array() );
		if ( '' !== $resolved ) {
			return $resolved;
		}
	}
	foreach ( array( 'atmospherics', 'lookbook' ) as $key ) {
		foreach ( $imagery[ $key ] ?? array() as $item ) {
			$resolved = skyyrosesot_resolved( $item );
			if ( '' !== $resolved ) {
				return $resolved;
			}
		}
	}
	return '';
}

function skyyrosesot_lockup( $collection ) {
	foreach ( array( 'display_webp', 'source_art' ) as $key ) {
		$resolved = skyyrosesot_resolved( $collection['lockup'][ $key ] ?? array() );
		if ( '' !== $resolved ) {
			return $resolved;
		}
	}
	$canonical = $collection['lockup']['canonical'] ?? '';
	return is_string( $canonical ) ? ltrim( $canonical, '/' ) : '';
}

function skyyrosesot_collection_style( $collection ) {
	$accent = $collection['palette']['accent'] ?? '#B76E79';
	$script = $collection['fonts']['script']['family'] ?? 'Hanken Grotesk';
	return '--srs-accent:' . sanitize_hex_color( $accent ) . ";--srs-script:'" . esc_attr( $script ) . "';";
}

function skyyrosesot_product_image( $product_data ) {
	$images = $product_data['images'] ?? array();
	foreach ( array( 'front_model_image', 'image' ) as $role ) {
		$resolved = skyyrosesot_resolved( $images[ $role ] ?? array() );
		if ( '' !== $resolved ) {
			return $resolved;
		}
	}
	return '';
}

function skyyrosesot_product_by_sku( $sku ) {
	foreach ( skyyrosesot_collections() as $collection ) {
		foreach ( $collection['products'] ?? array() as $product_data ) {
			if ( ( $product_data['sku'] ?? '' ) === $sku ) {
				return $product_data;
			}
		}
	}
	return array();
}

function skyyrosesot_setup() {
	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'woocommerce' );
	add_theme_support( 'wc-product-gallery-zoom' );
	add_theme_support( 'wc-product-gallery-lightbox' );
	add_theme_support( 'wc-product-gallery-slider' );
	register_nav_menus( array( 'primary' => __( 'Primary Menu', 'skyyrose-flagship-sot' ) ) );
}
add_action( 'after_setup_theme', 'skyyrosesot_setup' );

function skyyrosesot_assets() {
	wp_enqueue_style( 'skyyrosesot-fonts', skyyrosesot_asset_uri( 'css/fonts.css' ), array(), SKYYROSESOT_VERSION );
	wp_enqueue_style( 'skyyrosesot-theme', SKYYROSESOT_URI . '/assets/css/theme.css', array( 'skyyrosesot-fonts' ), SKYYROSESOT_VERSION );
	wp_enqueue_style( 'skyyrosesot-commerce', SKYYROSESOT_URI . '/assets/css/commerce.css', array( 'skyyrosesot-theme' ), SKYYROSESOT_VERSION );
	if ( is_page_template( 'template-collections-world.php' ) ) {
		wp_enqueue_style( 'skyyrosesot-world', SKYYROSESOT_URI . '/assets/css/scroll-world.css', array( 'skyyrosesot-theme' ), SKYYROSESOT_VERSION );
		wp_enqueue_script( 'skyyrosesot-world', SKYYROSESOT_URI . '/assets/js/scroll-world.js', array(), SKYYROSESOT_VERSION, true );
		wp_add_inline_script( 'skyyrosesot-world', 'window.SKYY_SCROLL_WORLD_CONFIG = ' . wp_json_encode( skyyrosesot_world_config(), JSON_HEX_TAG | JSON_UNESCAPED_SLASHES ) . ';', 'before' );
	}
	wp_enqueue_script( 'skyyrosesot-theme', SKYYROSESOT_URI . '/assets/js/theme.js', array(), SKYYROSESOT_VERSION, true );
}
add_action( 'wp_enqueue_scripts', 'skyyrosesot_assets' );

function skyyrosesot_world_config() {
	$sections = array();
	foreach ( skyyrosesot_collections() as $slug => $collection ) {
		$still = skyyrosesot_first_image( $collection );
		if ( '' === $still ) {
			continue;
		}
		$sections[] = array(
			'id'      => $slug,
			'label'   => $collection['name'],
			'accent'  => $collection['palette']['accent'],
			'font'    => $collection['fonts']['script']['family'],
			'still'   => skyyrosesot_asset_uri( $still ),
			'eyebrow' => $collection['name'],
			'title'   => $collection['story']['seed'],
			'body'    => __( 'Explore verified pieces from this collection.', 'skyyrose-flagship-sot' ),
			'cta'     => array(
				'primary' => array(
					/* translators: %s: collection name. */
					'label' => sprintf( __( 'Shop %s', 'skyyrose-flagship-sot' ), $collection['name'] ),
					'href'  => home_url( '/collections/' . $slug . '/' ),
				),
			),
		);
	}
	return array(
		'brand'      => array(
			'name' => 'SkyyRose',
			'href' => home_url( '/' ),
		),
		'cta'        => array(
			'label' => __( 'Shop all', 'skyyrose-flagship-sot' ),
			'href'  => home_url( '/shop/' ),
		),
		'hint'       => __( 'Scroll to enter', 'skyyrose-flagship-sot' ),
		'nav'        => true,
		'atmosphere' => false,
		'diveScroll' => 1.35,
		'crossfade'  => 0.12,
		'sections'   => $sections,
	);
}

function skyyrosesot_render_products( $collection_slug = '', $limit = 12 ) {
	$collections = skyyrosesot_collections();
	if ( $collection_slug ) {
		$collections = isset( $collections[ $collection_slug ] ) ? array( $collection_slug => $collections[ $collection_slug ] ) : array();
	}
	$shown = 0;
	echo '<div class="srs-products">';
	foreach ( $collections as $slug => $collection ) {
		foreach ( $collection['products'] ?? array() as $product_data ) {
			if ( $shown >= $limit ) {
				break 2;
			}
			$sku       = $product_data['sku'] ?? '';
			$image_uri = skyyrosesot_product_image( $product_data );
			$product   = function_exists( 'wc_get_product' ) ? wc_get_product( wc_get_product_id_by_sku( $sku ) ) : false;
			if ( ! $product || '' === $image_uri ) {
				continue;
			}
			++$shown;
			?>
			<article class="srs-product" data-collection="<?php echo esc_attr( $slug ); ?>"><a href="<?php echo esc_url( get_permalink( $product->get_id() ) ); ?>"><img src="<?php echo esc_url( skyyrosesot_asset_uri( $image_uri ) ); ?>" alt="<?php echo esc_attr( $product->get_name() ); ?>" loading="lazy" width="720" height="960"></a><p><?php echo esc_html( $collection['name'] ); ?></p><h3><a href="<?php echo esc_url( get_permalink( $product->get_id() ) ); ?>"><?php echo esc_html( $product->get_name() ); ?></a></h3><div><span><?php echo wp_kses_post( $product->get_price_html() ); ?></span><a href="<?php echo esc_url( get_permalink( $product->get_id() ) ); ?>"><?php esc_html_e( 'View piece', 'skyyrose-flagship-sot' ); ?></a></div></article>
			<?php
		}
	}
	echo '</div>';
	if ( 0 === $shown ) {
		echo '<p class="srs-empty">' . esc_html__( 'Pieces arriving soon.', 'skyyrose-flagship-sot' ) . '</p>';
	}
}
