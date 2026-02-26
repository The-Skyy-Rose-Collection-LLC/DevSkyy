<?php
/**
 * Centralized Product Catalog
 *
 * Single source of truth for all product data across the SkyyRose theme.
 * All templates reference this file instead of maintaining duplicate arrays.
 *
 * Data sourced from products.csv (prices, descriptions, attributes)
 * and WordPress media library (image paths).
 *
 * @package SkyyRose_Flagship
 * @since   3.2.1
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Get the full product catalog.
 *
 * Returns an associative array keyed by SKU. Each product includes:
 *   - sku, name, price, collection, description, badge
 *   - image (primary image filename), back_image (optional)
 *   - sizes (pipe-delimited string), color, edition_size
 *   - published (bool), is_preorder (bool)
 *
 * @since  3.2.1
 * @return array Associative array of all products keyed by SKU.
 */
function skyyrose_get_product_catalog() {

	static $catalog = null;

	if ( null !== $catalog ) {
		return $catalog;
	}

	$img = 'assets/images/products';

	$catalog = array(

		/*--------------------------------------------------------------
		 * BLACK ROSE COLLECTION
		 *--------------------------------------------------------------*/

		'br-001' => array(
			'sku'          => 'br-001',
			'name'         => 'BLACK Rose Crewneck',
			'price'        => 35.00,
			'collection'   => 'black-rose',
			'description'  => 'Gothic luxury blooms in twilight. Embroidered with defiant elegance, a dark romance woven in every thread.',
			'badge'        => 'Draft',
			'image'        => $img . '/br-001-crewneck.webp',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Black',
			'edition_size' => 250,
			'published'    => false,
			'is_preorder'  => false,
		),
		'br-002' => array(
			'sku'          => 'br-002',
			'name'         => 'BLACK Rose Joggers',
			'price'        => 50.00,
			'collection'   => 'black-rose',
			'description'  => 'Twilight comfort meets gothic romance. Embroidered black roses bloom on soft fabric.',
			'badge'        => 'Pre-Order',
			'image'        => $img . '/br-002-joggers.jpg',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Black',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'br-003' => array(
			'sku'          => 'br-003',
			'name'         => 'BLACK is Beautiful Jersey',
			'price'        => 45.00,
			'collection'   => 'black-rose',
			'description'  => 'A bold statement in luxury athletic wear. Black is beautiful, and this jersey proves it.',
			'badge'        => 'Draft',
			'image'        => $img . '/br-003-jersey.webp',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Black',
			'edition_size' => 250,
			'published'    => false,
			'is_preorder'  => false,
		),
		'br-004' => array(
			'sku'          => 'br-004',
			'name'         => 'BLACK Rose Hoodie',
			'price'        => 40.00,
			'collection'   => 'black-rose',
			'description'  => 'Gothic luxury in twilight shadows. Intricate embroidery captures the bloom of darkness.',
			'badge'        => 'Pre-Order',
			'image'        => $img . '/br-004-hoodie.jpg',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Black',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'br-005' => array(
			'sku'          => 'br-005',
			'name'         => 'BLACK Rose Hoodie — Signature Edition',
			'price'        => 65.00,
			'collection'   => 'black-rose',
			'description'  => 'The definitive Black Rose hoodie. Signature edition with premium detailing and numbered tag.',
			'badge'        => 'Pre-Order',
			'image'        => $img . '/br-005-hoodie-sig.jpg',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Black',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'br-006' => array(
			'sku'          => 'br-006',
			'name'         => 'BLACK Rose Sherpa Jacket',
			'price'        => 95.00,
			'collection'   => 'black-rose',
			'description'  => 'Lustrous black satin with plush Sherpa lining, crowned by an exquisite embroidered rose.',
			'badge'        => 'Pre-Order',
			'image'        => $img . '/br-006-sherpa.webp',
			'back_image'   => $img . '/br-006-sherpa-back.webp',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Black',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'br-007' => array(
			'sku'          => 'br-007',
			'name'         => 'BLACK Rose x Love Hurts Basketball Shorts',
			'price'        => 65.00,
			'collection'   => 'black-rose',
			'description'  => 'Two worlds collide. A cross-collection collaboration merging Black Rose darkness with Love Hurts fire.',
			'badge'        => 'Pre-Order',
			'image'        => $img . '/br-007-shorts.jpg',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Black',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'br-008' => array(
			'sku'          => 'br-008',
			'name'         => "Women's BLACK Rose Hooded Dress",
			'price'        => 120.00,
			'collection'   => 'black-rose',
			'description'  => 'Intricate black rose embroidery and a silhouette of gothic mystery. Designed for the fearless.',
			'badge'        => 'Draft',
			'image'        => $img . '/br-008-hooded-dress.webp',
			'back_image'   => '',
			'sizes'        => 'XS|S|M|L|XL|2XL',
			'color'        => 'Black',
			'edition_size' => 250,
			'published'    => false,
			'is_preorder'  => false,
		),

		/*--------------------------------------------------------------
		 * LOVE HURTS COLLECTION
		 *--------------------------------------------------------------*/

		'lh-001' => array(
			'sku'          => 'lh-001',
			'name'         => 'The Fannie Pack',
			'price'        => 65.00,
			'collection'   => 'love-hurts',
			'description'  => 'Luxury fanny pack embodying Oakland grit, passion, and the defiant bloom of a street rose.',
			'badge'        => 'Pre-Order',
			'image'        => $img . '/lh-001-fannie.webp',
			'back_image'   => '',
			'sizes'        => 'One Size',
			'color'        => 'Black',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'lh-002' => array(
			'sku'          => 'lh-002',
			'name'         => 'Love Hurts Joggers',
			'price'        => 95.00,
			'collection'   => 'love-hurts',
			'description'  => 'Oakland grit meets luxury. Feel the fire with the embroidered rose, a symbol of passion.',
			'badge'        => 'Pre-Order',
			'image'        => $img . '/lh-002-joggers.webp',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Black',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'lh-003' => array(
			'sku'          => 'lh-003',
			'name'         => 'Love Hurts Basketball Shorts',
			'price'        => 75.00,
			'collection'   => 'love-hurts',
			'description'  => 'Oakland-inspired luxury streetwear. Defiant rose design on breathable mesh.',
			'badge'        => 'Pre-Order',
			'image'        => $img . '/lh-003-shorts.jpg',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Black',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'lh-004' => array(
			'sku'          => 'lh-004',
			'name'         => 'Love Hurts Varsity Jacket',
			'price'        => 265.00,
			'collection'   => 'love-hurts',
			'description'  => 'Oakland street couture. Satin, bold fire-red script, hidden rose garden in hood.',
			'badge'        => 'Draft',
			'image'        => $img . '/lh-004-varsity.jpg',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Black',
			'edition_size' => 250,
			'published'    => false,
			'is_preorder'  => false,
		),
		'lh-005' => array(
			'sku'          => 'lh-005',
			'name'         => 'Love Hurts Windbreaker',
			'price'        => 145.00,
			'collection'   => 'love-hurts',
			'description'  => 'Oakland fire meets the elements. Blush pink windbreaker with Love Hurts text and rose detailing.',
			'badge'        => 'Draft',
			'image'        => $img . '/lh-005-bomber.webp',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Blush',
			'edition_size' => 250,
			'published'    => false,
			'is_preorder'  => false,
		),

		/*--------------------------------------------------------------
		 * SIGNATURE COLLECTION
		 *--------------------------------------------------------------*/

		'sg-001' => array(
			'sku'          => 'sg-001',
			'name'         => 'The Bay Set',
			'price'        => 195.00,
			'collection'   => 'signature',
			'description'  => 'Embody West Coast luxury with this exclusive ensemble. Iconic blue rose and vibrant Bay Area skyline.',
			'badge'        => 'Pre-Order',
			'image'        => $img . '/sg-001-bay-set.webp',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Blue',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'sg-002' => array(
			'sku'          => 'sg-002',
			'name'         => 'Stay Golden Tee',
			'price'        => 65.00,
			'collection'   => 'signature',
			'description'  => 'Embrace West Coast prestige. Luxurious statement of Bay Area style featuring signature rose.',
			'badge'        => 'Pre-Order',
			'image'        => $img . '/sg-002-stay-golden-tee.jpg',
			'back_image'   => '',
			'sizes'        => 'XS|S|M|L|XL|2XL',
			'color'        => 'Gold',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'sg-003' => array(
			'sku'          => 'sg-003',
			'name'         => 'The Signature Tee (Orchid)',
			'price'        => 15.00,
			'collection'   => 'signature',
			'description'  => 'The essential SkyyRose tee in a rich orchid colorway. Soft cotton with embroidered rose.',
			'badge'        => '',
			'image'        => $img . '/sg-003-pink-smoke-crewneck.jpg',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Orchid',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'sg-004' => array(
			'sku'          => 'sg-004',
			'name'         => 'The Signature Hoodie',
			'price'        => 55.00,
			'collection'   => 'signature',
			'description'  => 'The quintessential SkyyRose hoodie in signature colorway. Premium fleece with embroidered rose detail.',
			'badge'        => 'Draft',
			'image'        => $img . '/sg-004-signature-hoodie.webp',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Rose Gold',
			'edition_size' => 250,
			'published'    => false,
			'is_preorder'  => false,
		),
		'sg-005' => array(
			'sku'          => 'sg-005',
			'name'         => 'Stay Golden Tee (Classic)',
			'price'        => 40.00,
			'collection'   => 'signature',
			'description'  => 'The classic Stay Golden silhouette. Timeless Bay Area luxury in every stitch.',
			'badge'        => '',
			'image'        => $img . '/sg-005-stay-golden-tee.webp',
			'back_image'   => '',
			'sizes'        => 'XS|S|M|L|XL|2XL',
			'color'        => 'Gold',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'sg-006' => array(
			'sku'          => 'sg-006',
			'name'         => 'Mint & Lavender Hoodie',
			'price'        => 45.00,
			'collection'   => 'signature',
			'description'  => 'Sweet pastel vibes meet streetwear luxury. Mint and lavender colorblock with signature rose detail.',
			'badge'        => 'New',
			'image'        => $img . '/sg-006-mint-lavender-hoodie.jpg',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Mint/Lavender',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'sg-007' => array(
			'sku'          => 'sg-007',
			'name'         => 'The Signature Beanie',
			'price'        => 25.00,
			'collection'   => 'signature',
			'description'  => 'Classic fitted beanie with embroidered signature rose. West Coast luxury meets everyday warmth.',
			'badge'        => '',
			'image'        => $img . '/sg-007-signature-beanie.webp',
			'back_image'   => '',
			'sizes'        => 'One Size',
			'color'        => 'Black',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'sg-008' => array(
			'sku'          => 'sg-008',
			'name'         => 'Signature Crop Hoodie',
			'price'        => 50.00,
			'collection'   => 'signature',
			'description'  => 'Cropped silhouette meets luxury streetwear. Peach rose-gold front with black rose design on the back.',
			'badge'        => 'Pre-Order',
			'image'        => $img . '/sg-008-crop-hoodie.webp',
			'back_image'   => $img . '/sg-008-crop-hoodie-back.webp',
			'sizes'        => 'XS|S|M|L|XL|2XL',
			'color'        => 'Peach/Black',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'sg-009' => array(
			'sku'          => 'sg-009',
			'name'         => 'The Sherpa Jacket',
			'price'        => 80.00,
			'collection'   => 'signature',
			'description'  => 'Plush sherpa warmth in the SkyyRose signature colorway. Luxury outerwear for the West Coast.',
			'badge'        => 'Pre-Order',
			'image'        => $img . '/sg-009-sherpa-jacket.webp',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Cream',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'sg-010' => array(
			'sku'          => 'sg-010',
			'name'         => 'The Bridge Series Shorts',
			'price'        => 25.00,
			'collection'   => 'signature',
			'description'  => 'From the Bridge Series. Athletic shorts celebrating the iconic Bay Area bridges.',
			'badge'        => 'Pre-Order',
			'image'        => $img . '/sg-010-bridge-shorts.webp',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL',
			'color'        => 'Navy',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'sg-011' => array(
			'sku'          => 'sg-011',
			'name'         => 'Original Label Tee (White)',
			'price'        => 30.00,
			'collection'   => 'signature',
			'description'  => 'The original SkyyRose label tee in clean white. Minimal design with signature branding.',
			'badge'        => 'Draft',
			'image'        => $img . '/sg-011-label-tee-white.webp',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'White',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
		'sg-012' => array(
			'sku'          => 'sg-012',
			'name'         => 'Original Label Tee (Orchid)',
			'price'        => 30.00,
			'collection'   => 'signature',
			'description'  => 'The original SkyyRose label tee in rich orchid. Minimal design with signature branding.',
			'badge'        => 'Draft',
			'image'        => $img . '/sg-012-label-tee-orchid.webp',
			'back_image'   => '',
			'sizes'        => 'S|M|L|XL|2XL|3XL',
			'color'        => 'Orchid',
			'edition_size' => 250,
			'published'    => true,
			'is_preorder'  => true,
		),
	);

	return $catalog;
}

/**
 * Get a single product by SKU.
 *
 * @since  3.2.1
 * @param  string $sku Product SKU (e.g., 'br-006').
 * @return array|null  Product data array or null if not found.
 */
function skyyrose_get_product( $sku ) {
	$catalog = skyyrose_get_product_catalog();
	return isset( $catalog[ $sku ] ) ? $catalog[ $sku ] : null;
}

/**
 * Get all products for a specific collection.
 *
 * @since  3.2.1
 * @param  string $collection Collection slug: 'black-rose', 'love-hurts', or 'signature'.
 * @return array  Array of product data arrays for the collection.
 */
function skyyrose_get_collection_products( $collection ) {
	$catalog  = skyyrose_get_product_catalog();
	$products = array();

	foreach ( $catalog as $product ) {
		if ( $product['collection'] === $collection ) {
			$products[] = $product;
		}
	}

	return $products;
}

/**
 * Get products filtered for the pre-order gateway.
 *
 * Returns only published products with active pre-orders,
 * grouped by collection in display order.
 *
 * @since  3.2.1
 * @return array Associative array keyed by collection slug.
 */
function skyyrose_get_preorder_products() {
	$catalog     = skyyrose_get_product_catalog();
	$collections = array(
		'black-rose' => array(),
		'love-hurts' => array(),
		'signature'  => array(),
	);

	foreach ( $catalog as $product ) {
		if ( $product['is_preorder'] ) {
			$collections[ $product['collection'] ][] = $product;
		}
	}

	return $collections;
}

/**
 * Format a product price for display.
 *
 * Returns 'Coming Soon' for unpublished products without pre-order,
 * or the formatted dollar amount.
 *
 * @since  3.2.1
 * @param  array $product Product data array.
 * @return string Formatted price string.
 */
function skyyrose_format_price( $product ) {
	if ( ! $product['published'] && ! $product['is_preorder'] ) {
		return esc_html__( 'Coming Soon', 'skyyrose-flagship' );
	}

	// Use zero decimal places — all prices are whole-dollar and $95 reads
	// cleaner than $95.00 for a luxury fashion brand.
	return '$' . number_format( $product['price'], 0 );
}

/**
 * Get the theme-relative URI for a product image.
 *
 * @since  3.2.1
 * @param  string $image_path Relative image path from catalog (e.g., 'assets/images/products/br-001.webp').
 * @return string Full URI to the image.
 */
function skyyrose_product_image_uri( $image_path ) {
	if ( empty( $image_path ) ) {
		return get_theme_file_uri( 'assets/images/products/placeholder.jpg' );
	}
	return get_theme_file_uri( $image_path );
}
