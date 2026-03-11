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
		 * BLACK ROSE COLLECTION (11 products)
		 *--------------------------------------------------------------*/

		'br-001' => array(
			'sku'               => 'br-001',
			'name'              => 'BLACK Rose Crewneck',
			'price'             => 35.00,
			'collection'        => 'black-rose',
			'description'       => 'Gothic luxury blooms in twilight. Embroidered with defiant elegance, a dark romance woven in every thread.',
			'badge'             => 'Draft',
			'image'             => $img . '/black-rose-crewneck-techflat-v4.jpg',
			'front_model_image' => $img . '/black-rose-crewneck-front-model.webp',
			'back_image'        => '',
			'back_model_image'  => $img . '/black-rose-crewneck-back-model.webp',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => false,
		),
		'br-002' => array(
			'sku'               => 'br-002',
			'name'              => 'BLACK Rose Joggers',
			'price'             => 50.00,
			'collection'        => 'black-rose',
			'description'       => 'Twilight comfort meets gothic romance. Embroidered black roses bloom on soft fabric.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/black-rose-joggers-source.jpg',
			'front_model_image' => $img . '/black-rose-joggers-front-model.webp',
			'back_image'        => $img . '/black-rose-joggers-back-model.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'br-003' => array(
			'sku'               => 'br-003',
			'name'              => 'BLACK is Beautiful Jersey',
			'price'             => 45.00,
			'collection'        => 'black-rose',
			'description'       => 'A bold statement in luxury athletic wear. Black is beautiful, and this jersey proves it.',
			'badge'             => 'Draft',
			'image'             => $img . '/black-is-beautiful-jersey-techflat-black.jpeg',
			'front_model_image' => $img . '/black-is-beautiful-jersey-front-model.webp',
			'back_image'        => $img . '/black-is-beautiful-jersey-back-model.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => false,
		),
		'br-004' => array(
			'sku'               => 'br-004',
			'name'              => 'BLACK Rose Hoodie',
			'price'             => 40.00,
			'collection'        => 'black-rose',
			'description'       => 'Gothic luxury in twilight shadows. Intricate embroidery captures the bloom of darkness.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/black-rose-hoodie-source.jpg',
			'front_model_image' => $img . '/black-rose-hoodie-front-model.webp',
			'back_image'        => $img . '/black-rose-hoodie-back-model.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'br-005' => array(
			'sku'               => 'br-005',
			'name'              => 'BLACK Rose Hoodie — Signature Edition',
			'price'             => 65.00,
			'collection'        => 'black-rose',
			'description'       => 'The definitive Black Rose hoodie. Signature edition with premium detailing and numbered tag.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/black-rose-hoodie-signature-edition-hoodie-ltd-source.jpg',
			'front_model_image' => $img . '/black-rose-hoodie-signature-edition-front-model.webp',
			'back_image'        => $img . '/black-rose-hoodie-signature-edition-back-model.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'br-006' => array(
			'sku'               => 'br-006',
			'name'              => 'BLACK Rose Sherpa Jacket',
			'price'             => 95.00,
			'collection'        => 'black-rose',
			'description'       => 'Lustrous black satin with plush Sherpa lining, crowned by an exquisite embroidered rose.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/black-rose-sherpa-jacket-sherpa-product.jpg',
			'front_model_image' => $img . '/black-rose-sherpa-jacket-front-model.webp',
			'back_image'        => $img . '/black-rose-sherpa-jacket-back-model.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'br-007' => array(
			'sku'               => 'br-007',
			'name'              => 'BLACK Rose x Love Hurts Basketball Shorts',
			'price'             => 65.00,
			'collection'        => 'black-rose',
			'description'       => 'Two worlds collide. A cross-collection collaboration merging Black Rose darkness with Love Hurts fire.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/black-rose-love-hurts-basketball-shorts-shorts.jpg',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => $img . '/black-rose-love-hurts-basketball-shorts-back-model.webp',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),

		// BLACK is Beautiful Jersey Series — Exclusive editions ($115 each, 80 pieces).
		'br-008' => array(
			'sku'               => 'br-008',
			'name'              => 'BLACK is Beautiful Jersey Series: 1. SF inspired',
			'price'             => 115.00,
			'collection'        => 'black-rose',
			'description'       => 'A bold statement in luxury athletic wear. Black is beautiful, and this jersey proves it.',
			'badge'             => 'Pre-Order',
			'image'             => '',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 80,
			'published'         => false,
			'is_preorder'       => true,
		),
		'br-009' => array(
			'sku'               => 'br-009',
			'name'              => 'BLACK is Beautiful Jersey Series: 2. LAST OAKLAND',
			'price'             => 115.00,
			'collection'        => 'black-rose',
			'description'       => 'A bold statement in luxury athletic wear. Black is beautiful.',
			'badge'             => 'Pre-Order',
			'image'             => '',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 80,
			'published'         => false,
			'is_preorder'       => true,
		),
		'br-010' => array(
			'sku'               => 'br-010',
			'name'              => 'BLACK is Beautiful Jersey Series: 3. THE BAY',
			'price'             => 115.00,
			'collection'        => 'black-rose',
			'description'       => 'A bold statement in luxury athletic wear. Black is beautiful.',
			'badge'             => 'Pre-Order',
			'image'             => '',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 80,
			'published'         => false,
			'is_preorder'       => true,
		),
		'br-011' => array(
			'sku'               => 'br-011',
			'name'              => 'BLACK is Beautiful Jersey Series: 4. THE ROSE (SHARKS EDITION)',
			'price'             => 115.00,
			'collection'        => 'black-rose',
			'description'       => 'A bold statement in luxury athletic wear. Black is beautiful.',
			'badge'             => 'Pre-Order',
			'image'             => '',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 80,
			'published'         => false,
			'is_preorder'       => true,
		),

		/*--------------------------------------------------------------
		 * LOVE HURTS COLLECTION (5 products)
		 *--------------------------------------------------------------*/

		'lh-002' => array(
			'sku'               => 'lh-002',
			'name'              => 'Love Hurts Joggers',
			'price'             => 95.00,
			'collection'        => 'love-hurts',
			'description'       => 'Oakland grit meets luxury. Feel the fire with the embroidered rose, a symbol of passion.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/love-hurts-joggers-techflat.jpeg',
			'front_model_image' => $img . '/love-hurts-joggers-front-model.webp',
			'back_image'        => $img . '/love-hurts-joggers-back-model.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'lh-003' => array(
			'sku'               => 'lh-003',
			'name'              => 'Love Hurts Basketball Shorts',
			'price'             => 75.00,
			'collection'        => 'love-hurts',
			'description'       => 'Oakland-inspired luxury streetwear. Defiant rose design on breathable mesh.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/love-hurts-basketball-shorts-source.jpg',
			'front_model_image' => $img . '/love-hurts-basketball-shorts-front-model.webp',
			'back_image'        => '',
			'back_model_image'  => $img . '/love-hurts-basketball-shorts-back-model.webp',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'lh-004' => array(
			'sku'               => 'lh-004',
			'name'              => 'Love Hurts Varsity Jacket',
			'price'             => 265.00,
			'collection'        => 'love-hurts',
			'description'       => 'Oakland street couture. Satin, bold fire-red script, hidden rose garden in hood.',
			'badge'             => 'Draft',
			'image'             => $img . '/love-hurts-varsity-jacket-varsity-source.jpg',
			'front_model_image' => $img . '/love-hurts-varsity-jacket-front-model.webp',
			'back_image'        => $img . '/love-hurts-varsity-jacket-back-model.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => false,
		),
		'lh-005' => array(
			'sku'               => 'lh-005',
			'name'              => 'Love Hurts Windbreaker',
			'price'             => 145.00,
			'collection'        => 'love-hurts',
			'description'       => 'Oakland fire meets the elements. Blush pink windbreaker with Love Hurts text and rose detailing.',
			'badge'             => 'Draft',
			'image'             => '',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Blush',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => false,
		),
		'lh-006' => array(
			'sku'               => 'lh-006',
			'name'              => 'The Fannie',
			'price'             => 45.00,
			'collection'        => 'love-hurts',
			'description'       => 'Oakland luxury meets everyday utility. The essential Love Hurts fanny pack with premium embroidery.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/the-fannie-pack-photo.jpg',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'One Size',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),

		/*--------------------------------------------------------------
		 * SIGNATURE COLLECTION (13 products)
		 *--------------------------------------------------------------*/

		'sg-001' => array(
			'sku'               => 'sg-001',
			'name'              => "The Bridge Series 'The Bay Bridge' Shorts",
			'price'             => 195.00,
			'collection'        => 'signature',
			'description'       => 'Embody West Coast luxury with this exclusive ensemble. Iconic blue rose and vibrant Bay Area skyline.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/the-bay-set-source.jpeg',
			'front_model_image' => $img . '/the-bay-set-front-model.webp',
			'back_image'        => $img . '/the-bay-set-back-model.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Blue',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'sg-002' => array(
			'sku'               => 'sg-002',
			'name'              => "The Bridge Series 'Stay Golden' Shirt",
			'price'             => 65.00,
			'collection'        => 'signature',
			'description'       => 'Embrace West Coast prestige. Luxurious statement of Bay Area style featuring signature rose.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/stay-golden-tee-techflat-v4.jpg',
			'front_model_image' => $img . '/stay-golden-tee-front-model.webp',
			'back_image'        => '',
			'back_model_image'  => $img . '/stay-golden-tee-back-model.webp',
			'sizes'             => 'XS|S|M|L|XL|2XL',
			'color'             => 'Gold',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'sg-003' => array(
			'sku'               => 'sg-003',
			'name'              => "The Bridge Series 'Stay Golden' Shorts",
			'price'             => 65.00,
			'collection'        => 'signature',
			'description'       => 'From the Bridge Series. Athletic shorts in Stay Golden colorway celebrating Bay Area luxury.',
			'badge'             => 'Pre-Order',
			'image'             => '',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Gold',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'sg-004' => array(
			'sku'               => 'sg-004',
			'name'              => 'The Signature Hoodie',
			'price'             => 55.00,
			'collection'        => 'signature',
			'description'       => 'The quintessential SkyyRose hoodie in signature colorway. Premium fleece with embroidered rose detail.',
			'badge'             => 'Draft',
			'image'             => $img . '/the-signature-hoodie-techflat.jpeg',
			'front_model_image' => $img . '/the-signature-hoodie-front-model.webp',
			'back_image'        => '',
			'back_model_image'  => $img . '/the-signature-hoodie-back-model.webp',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Rose Gold',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => false,
		),
		'sg-005' => array(
			'sku'               => 'sg-005',
			'name'              => "The Bridge Series 'The Bay Bridge' Shirt",
			'price'             => 25.00,
			'collection'        => 'signature',
			'description'       => 'From the Bridge Series. Athletic shirt celebrating the iconic Bay Area bridges.',
			'badge'             => 'Pre-Order',
			'image'             => '',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL',
			'color'             => 'Navy',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'sg-006' => array(
			'sku'               => 'sg-006',
			'name'              => 'Mint & Lavender Hoodie',
			'price'             => 45.00,
			'collection'        => 'signature',
			'description'       => 'Sweet pastel vibes meet streetwear luxury. Mint and lavender colorblock with signature rose detail.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/mint-lavender-hoodie-source.jpg',
			'front_model_image' => $img . '/mint-lavender-hoodie-front-model.webp',
			'back_image'        => $img . '/mint-lavender-hoodie-back-model.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Mint/Lavender',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'sg-007' => array(
			'sku'               => 'sg-007',
			'name'              => 'The Signature Beanie',
			'price'             => 25.00,
			'collection'        => 'signature',
			'description'       => 'Classic fitted beanie with embroidered signature rose. West Coast luxury meets everyday warmth.',
			'badge'             => 'Pre-Order',
			'image'             => '',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'One Size',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'sg-009' => array(
			'sku'               => 'sg-009',
			'name'              => 'The Sherpa Jacket',
			'price'             => 80.00,
			'collection'        => 'signature',
			'description'       => 'Plush sherpa warmth in the SkyyRose signature colorway. Luxury outerwear for the West Coast.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/the-sherpa-jacket-front-model.webp',
			'front_model_image' => $img . '/the-sherpa-jacket-front-model.webp',
			'back_image'        => $img . '/the-sherpa-jacket-back-model.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Cream',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'sg-010' => array(
			'sku'               => 'sg-010',
			'name'              => 'The Bridge Series Shorts',
			'price'             => 60.00,
			'collection'        => 'signature',
			'description'       => 'From the Bridge Series. Athletic shorts celebrating the iconic Bay Area bridges.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/bridge-series-shorts-front-model.webp',
			'front_model_image' => $img . '/bridge-series-shorts-front-model.webp',
			'back_image'        => $img . '/bridge-series-shorts-back-model.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL',
			'color'             => 'Navy',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'sg-011' => array(
			'sku'               => 'sg-011',
			'name'              => 'Original Label Tee (White)',
			'price'             => 30.00,
			'collection'        => 'signature',
			'description'       => 'The original SkyyRose label tee in clean white. Minimal design with signature branding.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/original-label-tee-white-front-model.webp',
			'front_model_image' => $img . '/original-label-tee-white-front-model.webp',
			'back_image'        => $img . '/original-label-tee-white-back-model.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'White',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'sg-012' => array(
			'sku'               => 'sg-012',
			'name'              => 'Original Label Tee (Orchid)',
			'price'             => 30.00,
			'collection'        => 'signature',
			'description'       => 'The original SkyyRose label tee in rich orchid. Minimal design with signature branding.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/original-label-tee-orchid-front-model.webp',
			'front_model_image' => $img . '/original-label-tee-orchid-front-model.webp',
			'back_image'        => $img . '/original-label-tee-orchid-back-model.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Orchid',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'sg-013' => array(
			'sku'               => 'sg-013',
			'name'              => 'Mint & Lavender Crewneck',
			'price'             => 40.00,
			'collection'        => 'signature',
			'description'       => 'Pastel luxury in crewneck form. Mint and lavender colorblock with signature rose embroidery.',
			'badge'             => 'Pre-Order',
			'image'             => '',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Mint/Lavender',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		'sg-014' => array(
			'sku'               => 'sg-014',
			'name'              => 'Mint & Lavender Sweatpants',
			'price'             => 45.00,
			'collection'        => 'signature',
			'description'       => 'Pastel luxury meets streetwear comfort. Mint and lavender sweatpants with signature rose detail.',
			'badge'             => 'Pre-Order',
			'image'             => '',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Mint/Lavender',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => true,
		),
		/*--------------------------------------------------------------
		 * KIDS CAPSULE (2 products)
		 *--------------------------------------------------------------*/

		'kids-001' => array(
			'sku'               => 'kids-001',
			'name'              => 'Kids Red Set',
			'price'             => 40.00,
			'collection'        => 'kids-capsule',
			'description'       => 'Bold red and black V-chevron colorblock hoodie and jogger set. Designed for young ones who wear luxury from the start.',
			'badge'             => '',
			'image'             => $img . '/colorblock-red-set-real.jpg',
			'front_model_image' => $img . '/kids-red-set-front-model.webp',
			'back_image'        => '',
			'back_model_image'  => $img . '/kids-red-set-back-model.webp',
			'sizes'             => '2T|3T|4T|5|6|7',
			'color'             => 'Red/Black',
			'edition_size'      => 150,
			'published'         => true,
			'is_preorder'       => false,
		),
		'kids-002' => array(
			'sku'               => 'kids-002',
			'name'              => 'Kids Purple Set',
			'price'             => 40.00,
			'collection'        => 'kids-capsule',
			'description'       => 'Rich purple and black V-chevron colorblock hoodie and jogger set. Little ones deserve luxury too.',
			'badge'             => '',
			'image'             => $img . '/colorblock-purple-set-real.jpg',
			'front_model_image' => $img . '/kids-purple-set-front-model.webp',
			'back_image'        => '',
			'back_model_image'  => $img . '/kids-purple-set-back-model.webp',
			'sizes'             => '2T|3T|4T|5|6|7',
			'color'             => 'Purple/Black',
			'edition_size'      => 150,
			'published'         => true,
			'is_preorder'       => false,
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
	$sku     = sanitize_key( $sku );
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
	$collection = sanitize_key( $collection );
	$catalog    = skyyrose_get_product_catalog();
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
		'black-rose'   => array(),
		'love-hurts'   => array(),
		'signature'    => array(),
		'kids-capsule' => array(),
	);

	foreach ( $catalog as $product ) {
		if ( $product['is_preorder'] && $product['published'] ) {
			if ( ! isset( $collections[ $product['collection'] ] ) ) {
				$collections[ $product['collection'] ] = array();
			}
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

	$price = (float) $product['price'];

	// Pre-order products with zero price show "Pre-Order" instead of "$0".
	if ( ! empty( $product['is_preorder'] ) && $price <= 0 ) {
		return esc_html__( 'Pre-Order', 'skyyrose-flagship' );
	}

	// Use zero decimal places — all prices are whole-dollar and $95 reads
	// cleaner than $95.00 for a luxury fashion brand.
	return '$' . number_format( $price, 0 );
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
		return get_theme_file_uri( 'assets/images/placeholder-product.jpg' );
	}
	return get_theme_file_uri( $image_path );
}

/**
 * Get the best available URL for a product.
 *
 * Uses WooCommerce permalink if product exists, falls back to pre-order page.
 *
 * @since  3.2.3
 * @param  string $sku Product SKU.
 * @return string Product URL.
 */
function skyyrose_product_url( $sku ) {
	if ( function_exists( 'wc_get_product_id_by_sku' ) ) {
		// Strip variant suffixes for WC lookup.
		$lookup_sku = preg_replace( '/-(tee|shorts)$/', '', $sku );
		$lookup_sku = preg_replace( '/([a-z]{2}-\d{3})[a-z]$/', '$1', $lookup_sku );
		$product_id = wc_get_product_id_by_sku( $lookup_sku );
		if ( $product_id ) {
			return get_permalink( $product_id );
		}
	}

	// Fallback: route pre-order products to the pre-order gateway,
	// non-preorder products to their collection page.
	$product = skyyrose_get_product( $sku );
	if ( $product && ! empty( $product['is_preorder'] ) ) {
		return home_url( '/pre-order/#' . sanitize_title( $sku ) );
	}
	if ( $product && ! empty( $product['collection'] ) ) {
		return home_url( '/collection-' . sanitize_title( $product['collection'] ) . '/#' . sanitize_title( $sku ) );
	}

	return home_url( '/pre-order/#' . sanitize_title( $sku ) );
}

/**
 * Build an immersive hotspot product entry from the centralized catalog.
 *
 * Merges catalog data (name, price, image, sizes, collection) with
 * scene-specific placement data (left, top, prop, prop_label).
 * Supports virtual split SKUs (e.g., 'sg-001-tee') by looking up
 * the parent SKU and allowing name/price/image overrides.
 *
 * @since 3.2.2
 * @param string $sku       Product SKU (e.g., 'br-006') or virtual split (e.g., 'sg-001-tee').
 * @param array  $scene     Scene-specific data: left, top, prop, prop_label, and optional overrides.
 * @return array Merged product entry ready for hotspot rendering.
 */
function skyyrose_immersive_product( $sku, $scene ) {

	// Validate required scene keys.
	$required_keys = array( 'left', 'top', 'prop', 'prop_label' );
	foreach ( $required_keys as $key ) {
		if ( ! isset( $scene[ $key ] ) ) {
			return array();
		}
	}

	// For split/variant SKUs like 'sg-001-tee' or 'lh-002b', look up the parent.
	$parent_sku = preg_replace( '/-(tee|shorts)$/', '', $sku );
	$parent_sku = preg_replace( '/([a-z]{2}-\d{3})[a-z]$/', '$1', $parent_sku );
	$product    = skyyrose_get_product( $parent_sku );

	// Skip unpublished products.
	if ( $product && isset( $product['published'] ) && ! $product['published'] ) {
		return array();
	}

	// Determine the best display image: front-model VTON > flat product.
	$display_image = '';
	if ( $product ) {
		$display_image = ! empty( $product['front_model_image'] )
			? $product['front_model_image']
			: $product['image'];
	}

	// Collection display name.
	$collection_label = '';
	if ( $product ) {
		$slugs = array(
			'black-rose' => 'Black Rose Collection',
			'love-hurts' => 'Love Hurts Collection',
			'signature'  => 'Signature Collection',
		);
		$collection_label = isset( $slugs[ $product['collection'] ] )
			? $slugs[ $product['collection'] ]
			: ucfirst( $product['collection'] ) . ' Collection';
	}

	// Build the entry — scene overrides win for name/price/image/sizes.
	// Return raw strings — templates apply esc_html()/esc_attr() at output time.
	// Do NOT pre-escape here or templates will double-encode via esc_attr().
	return array(
		'id'         => $sku,
		'name'       => isset( $scene['name'] )
			? $scene['name']
			: ( $product ? $product['name'] : $sku ),
		'price'      => isset( $scene['price'] )
			? $scene['price']
			: ( $product ? skyyrose_format_price( $product ) : '' ),
		'collection' => isset( $scene['collection'] )
			? $scene['collection']
			: $collection_label,
		'sizes'      => isset( $scene['sizes'] )
			? $scene['sizes']
			: ( $product ? str_replace( '|', ',', $product['sizes'] ) : '' ),
		'image'      => isset( $scene['image'] )
			? $scene['image']
			: ( $display_image ? get_theme_file_uri( $display_image ) : '' ),
		'url'        => skyyrose_product_url( $sku ),
		'left'       => $scene['left'],
		'top'        => $scene['top'],
		'prop'       => $scene['prop'],
		'prop_label' => $scene['prop_label'],
	);
}
