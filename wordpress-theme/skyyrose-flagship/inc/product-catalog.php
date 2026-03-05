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
			'sku'               => 'br-001',
			'name'              => 'BLACK Rose Crewneck',
			'price'             => 35.00,
			'collection'        => 'black-rose',
			'description'       => 'Gothic luxury blooms in twilight. Embroidered with defiant elegance, a dark romance woven in every thread.',
			'badge'             => 'Draft',
			'image'             => $img . '/br-001-crewneck.webp',
			'front_model_image' => $img . '/br-001-front-model.webp',
			'back_image'        => '',
			'back_model_image'  => $img . '/br-001-back-model.webp',
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
			'badge'             => '',
			'image'             => $img . '/br-002-joggers-source.jpg',
			'front_model_image' => $img . '/br-002-render-front.webp',
			'back_image'        => $img . '/br-002-render-back.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'br-003' => array(
			'sku'               => 'br-003',
			'name'              => 'BLACK is Beautiful Jersey',
			'price'             => 45.00,
			'collection'        => 'black-rose',
			'description'       => 'A bold statement in luxury athletic wear. Black is beautiful, and this jersey proves it.',
			'badge'             => 'Draft',
			'image'             => $img . '/br-003-jersey.webp',
			'front_model_image' => $img . '/br-003-render-front.webp',
			'back_image'        => $img . '/br-003-render-back.webp',
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
			'badge'             => '',
			'image'             => $img . '/br-004-hoodie-source.jpg',
			'front_model_image' => $img . '/br-004-render-front.webp',
			'back_image'        => $img . '/br-004-render-back.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'br-005' => array(
			'sku'               => 'br-005',
			'name'              => 'BLACK Rose Hoodie — Signature Edition',
			'price'             => 65.00,
			'collection'        => 'black-rose',
			'description'       => 'The definitive Black Rose hoodie. Signature edition with premium detailing and numbered tag.',
			'badge'             => '',
			'image'             => $img . '/br-005-hoodie-ltd-source.jpg',
			'front_model_image' => $img . '/br-005-render-front.webp',
			'back_image'        => $img . '/br-005-render-back.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'br-006' => array(
			'sku'               => 'br-006',
			'name'              => 'BLACK Rose Sherpa Jacket',
			'price'             => 95.00,
			'collection'        => 'black-rose',
			'description'       => 'Lustrous black satin with plush Sherpa lining, crowned by an exquisite embroidered rose.',
			'badge'             => '',
			'image'             => $img . '/br-006-sherpa.webp',
			'front_model_image' => $img . '/br-006-render-front.webp',
			'back_image'        => $img . '/br-006-render-back.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		// NOTE: br-007 unpublished — no real product image available (only 37KB placeholder).
		// Re-publish once a real product photo and VTON front-model image are generated.
		'br-007' => array(
			'sku'               => 'br-007',
			'name'              => 'BLACK Rose x Love Hurts Basketball Shorts',
			'price'             => 65.00,
			'collection'        => 'black-rose',
			'description'       => 'Two worlds collide. A cross-collection collaboration merging Black Rose darkness with Love Hurts fire.',
			'badge'             => 'Draft',
			'image'             => $img . '/br-007-shorts.jpg',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => $img . '/br-007-back-model.webp',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => false,
		),
		'br-008' => array(
			'sku'               => 'br-008',
			'name'              => "Women's BLACK Rose Hooded Dress",
			'price'             => 120.00,
			'collection'        => 'black-rose',
			'description'       => 'Intricate black rose embroidery and a silhouette of gothic mystery. Designed for the fearless.',
			'badge'             => 'Draft',
			'image'             => $img . '/br-008-hooded-dress.webp',
			'front_model_image' => $img . '/br-008-render-front.webp',
			'back_image'        => $img . '/br-008-render-back.webp',
			'back_model_image'  => '',
			'sizes'             => 'XS|S|M|L|XL|2XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => false,
		),
		'br-d01' => array(
			'sku'               => 'br-d01',
			'name'              => 'BLACK is Beautiful Hockey Jersey (Teal)',
			'price'             => 55.00,
			'collection'        => 'black-rose',
			'description'       => 'Hooded hockey jersey in bold black and teal. Streetwear meets the rink — luxury athletic design with signature BLACK is Beautiful branding.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/br-design-hockey-jersey.jpg',
			'front_model_image' => $img . '/br-d01-render-front.webp',
			'back_image'        => $img . '/br-d01-render-back.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black/Teal',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => true,
		),
		'br-d02' => array(
			'sku'               => 'br-d02',
			'name'              => 'BLACK is Beautiful Football Jersey (Red #80)',
			'price'             => 55.00,
			'collection'        => 'black-rose',
			'description'       => 'Red football jersey with #80 numbering. Game-day luxury meets street culture — BLACK is Beautiful on the field and off.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/br-design-football-jersey-red.jpg',
			'front_model_image' => $img . '/br-d02-render-front.webp',
			'back_image'        => $img . '/br-d02-render-back.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Red',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => true,
		),
		'br-d03' => array(
			'sku'               => 'br-d03',
			'name'              => 'BLACK is Beautiful Football Jersey (White #32)',
			'price'             => 55.00,
			'collection'        => 'black-rose',
			'description'       => 'White football jersey with #32. Clean luxury on the gridiron — BLACK is Beautiful, game-ready and street-approved.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/br-design-football-jersey-white.jpg',
			'front_model_image' => $img . '/br-d03-render-front.webp',
			'back_image'        => $img . '/br-d03-render-back.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'White',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => true,
		),
		'br-d04' => array(
			'sku'               => 'br-d04',
			'name'              => 'BLACK is Beautiful Basketball Jersey',
			'price'             => 45.00,
			'collection'        => 'black-rose',
			'description'       => 'Basketball jersey with "The Bay" branding. Court-ready luxury streetwear — BLACK is Beautiful, Bay Area edition.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/br-design-basketball-jersey.jpg',
			'front_model_image' => $img . '/br-d04-render-front.webp',
			'back_image'        => $img . '/br-d04-render-back.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black/Red',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => true,
		),

		/*--------------------------------------------------------------
		 * LOVE HURTS COLLECTION
		 *--------------------------------------------------------------*/

		'lh-001' => array(
			'sku'               => 'lh-001',
			'name'              => 'The Fannie Pack',
			'price'             => 65.00,
			'collection'        => 'love-hurts',
			'description'       => 'Luxury fanny pack embodying Oakland grit, passion, and the defiant bloom of a street rose.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/lh-001-fannie.webp',
			'front_model_image' => '',
			'back_image'        => '',
			'sizes'             => 'One Size',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => true,
		),
		'lh-002' => array(
			'sku'               => 'lh-002',
			'name'              => 'Love Hurts Joggers',
			'price'             => 95.00,
			'collection'        => 'love-hurts',
			'description'       => 'Oakland grit meets luxury. Feel the fire with the embroidered rose, a symbol of passion.',
			'badge'             => '',
			'image'             => $img . '/lh-002-joggers.webp',
			'front_model_image' => $img . '/lh-002-render-front.webp',
			'back_image'        => $img . '/lh-002-render-back.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'lh-003' => array(
			'sku'               => 'lh-003',
			'name'              => 'Love Hurts Basketball Shorts',
			'price'             => 75.00,
			'collection'        => 'love-hurts',
			'description'       => 'Oakland-inspired luxury streetwear. Defiant rose design on breathable mesh.',
			'badge'             => '',
			'image'             => $img . '/lh-003.webp',
			'front_model_image' => $img . '/lh-003-front-model.webp',
			'back_image'        => '',
			'back_model_image'  => $img . '/lh-003-back-model.webp',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'lh-004' => array(
			'sku'               => 'lh-004',
			'name'              => 'Love Hurts Varsity Jacket',
			'price'             => 265.00,
			'collection'        => 'love-hurts',
			'description'       => 'Oakland street couture. Satin, bold fire-red script, hidden rose garden in hood.',
			'badge'             => 'Draft',
			'image'             => $img . '/lh-004-varsity.jpg',
			'front_model_image' => $img . '/lh-004-render-front.webp',
			'back_image'        => $img . '/lh-004-render-back.webp',
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
			'image'             => $img . '/lh-005-bomber.webp',
			'front_model_image' => $img . '/lh-005-render-front.webp',
			'back_image'        => $img . '/lh-005-render-back.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Blush',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => false,
		),

		/*--------------------------------------------------------------
		 * SIGNATURE COLLECTION
		 *--------------------------------------------------------------*/

		'sg-001' => array(
			'sku'               => 'sg-001',
			'name'              => 'The Bay Set',
			'price'             => 195.00,
			'collection'        => 'signature',
			'description'       => 'Embody West Coast luxury with this exclusive ensemble. Iconic blue rose and vibrant Bay Area skyline.',
			'badge'             => '',
			'image'             => $img . '/sg-001-bay-set.webp',
			'front_model_image' => $img . '/sg-001-render-front.webp',
			'back_image'        => $img . '/sg-001-render-back.webp',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Blue',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'sg-002' => array(
			'sku'               => 'sg-002',
			'name'              => 'Stay Golden Set',
			'price'             => 65.00,
			'collection'        => 'signature',
			'description'       => 'Embrace West Coast prestige. Luxurious statement of Bay Area style featuring signature rose.',
			'badge'             => '',
			'image'             => $img . '/sg-002.webp',
			'front_model_image' => $img . '/sg-002-front-model.webp',
			'back_image'        => '',
			'back_model_image'  => $img . '/sg-002-back-model.webp',
			'sizes'             => 'XS|S|M|L|XL|2XL',
			'color'             => 'Gold',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'sg-003' => array(
			'sku'               => 'sg-003',
			'name'              => 'The Signature Tee (Orchid)',
			'price'             => 15.00,
			'collection'        => 'signature',
			'description'       => 'The essential SkyyRose tee in a rich orchid colorway. Soft cotton with embroidered rose.',
			'badge'             => '',
			'image'             => $img . '/sg-003.webp',
			'front_model_image' => $img . '/sg-003-front-model.webp',
			'back_image'        => '',
			'back_model_image'  => $img . '/sg-003-back-model.webp',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Orchid',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'sg-004' => array(
			'sku'               => 'sg-004',
			'name'              => 'Signature Tee (White)',
			'price'             => 15.00,
			'collection'        => 'signature',
			'description'       => 'The essential SkyyRose tee in clean white. Minimal design with signature branding.',
			'badge'             => 'Draft',
			'image'             => $img . '/sg-004-signature-hoodie.webp', // Image exists — legacy filename from hoodie variant
			'front_model_image' => $img . '/sg-004-front-model.webp',
			'back_image'        => '',
			'back_model_image'  => $img . '/sg-004-back-model.webp',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'White',
			'edition_size'      => 250,
			'published'         => false,
			'is_preorder'       => false,
		),
		'sg-005' => array(
			'sku'               => 'sg-005',
			'name'              => 'Stay Golden Tee',
			'price'             => 40.00,
			'collection'        => 'signature',
			'description'       => 'The classic Stay Golden silhouette. Timeless Bay Area luxury in every stitch.',
			'badge'             => '',
			'image'             => $img . '/sg-005-stay-golden-tee.webp',
			'front_model_image' => $img . '/sg-005-render-front.webp',
			'back_image'        => $img . '/sg-005-render-back.webp',
			'sizes'             => 'XS|S|M|L|XL|2XL',
			'color'             => 'Gold',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'sg-006' => array(
			'sku'               => 'sg-006',
			'name'              => 'Mint & Lavender Hoodie',
			'price'             => 45.00,
			'collection'        => 'signature',
			'description'       => 'Sweet pastel vibes meet streetwear luxury. Mint and lavender colorblock with signature rose detail.',
			'badge'             => '',
			'image'             => $img . '/sg-006-mint-lavender-hoodie.webp',
			'front_model_image' => $img . '/sg-006-render-front.webp',
			'back_image'        => $img . '/sg-006-render-back.webp',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Mint/Lavender',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'sg-007' => array(
			'sku'               => 'sg-007',
			'name'              => 'The Signature Beanie (Black)',
			'price'             => 25.00,
			'collection'        => 'signature',
			'description'       => 'Classic cuffed beanie in black with woven SkyyRose rose patch. West Coast luxury meets everyday warmth.',
			'badge'             => '',
			'image'             => $img . '/sg-007-beanie-black.jpg',
			'front_model_image' => '',
			'back_image'        => '',
			'sizes'             => 'One Size',
			'color'             => 'Black',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'sg-008' => array(
			'sku'               => 'sg-008',
			'name'              => 'The Signature Beanie (Forest Green)',
			'price'             => 25.00,
			'collection'        => 'signature',
			'description'       => 'Classic cuffed beanie in forest green with woven SkyyRose rose patch in teal accent. West Coast luxury meets everyday warmth.',
			'badge'             => '',
			'image'             => $img . '/sg-008-beanie-green.jpg',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'One Size',
			'color'             => 'Forest Green',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'sg-009' => array(
			'sku'               => 'sg-009',
			'name'              => 'The Sherpa Jacket',
			'price'             => 80.00,
			'collection'        => 'signature',
			'description'       => 'Plush sherpa warmth in the SkyyRose signature colorway. Luxury outerwear for the West Coast.',
			'badge'             => '',
			'image'             => $img . '/sg-009-sherpa-jacket.webp',
			'front_model_image' => $img . '/sg-009-render-front.webp',
			'back_image'        => $img . '/sg-009-render-back.webp',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Cream',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'sg-010' => array(
			'sku'               => 'sg-010',
			'name'              => 'The Bridge Series Shorts',
			'price'             => 25.00,
			'collection'        => 'signature',
			'description'       => 'From the Bridge Series. Athletic shorts celebrating the iconic Bay Area bridges.',
			'badge'             => '',
			'image'             => $img . '/sg-010-bridge-shorts.webp',
			'front_model_image' => $img . '/sg-010-render-front.webp',
			'back_image'        => $img . '/sg-010-render-back.webp',
			'sizes'             => 'S|M|L|XL|2XL',
			'color'             => 'Navy',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'sg-011' => array(
			'sku'               => 'sg-011',
			'name'              => 'Original Label Tee (White)',
			'price'             => 30.00,
			'collection'        => 'signature',
			'description'       => 'The original SkyyRose label tee in clean white. Minimal design with signature branding.',
			'badge'             => '',
			'image'             => $img . '/sg-011-label-tee-white.webp',
			'front_model_image' => $img . '/sg-011-render-front.webp',
			'back_image'        => $img . '/sg-011-render-back.webp',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'White',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'sg-012' => array(
			'sku'               => 'sg-012',
			'name'              => 'Original Label Tee (Orchid)',
			'price'             => 30.00,
			'collection'        => 'signature',
			'description'       => 'The original SkyyRose label tee in rich orchid. Minimal design with signature branding.',
			'badge'             => '',
			'image'             => $img . '/sg-012-label-tee-orchid.webp',
			'front_model_image' => $img . '/sg-012-render-front.webp',
			'back_image'        => $img . '/sg-012-render-back.webp',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Orchid',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'sg-d01' => array(
			'sku'               => 'sg-d01',
			'name'              => 'The Multi-Colored Windbreaker Set',
			'price'             => 75.00,
			'collection'        => 'signature',
			'description'       => 'Pastel V-chevron windbreaker set — hooded zip jacket and matching jogger pants in white with pink, yellow, lavender, and green stripes. Sold separately.',
			'badge'             => 'Pre-Order',
			'image'             => $img . '/sg-d01-windbreaker-set.jpg',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'White/Pastel Multi',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => true,
		),
		'sg-d02' => array(
			'sku'               => 'sg-d02',
			'name'              => 'The SkyyRose Collection Shorts',
			'price'             => 45.00,
			'collection'        => 'signature',
			'description'       => 'Black athletic shorts with gold accents and "The SkyyRose Collection" script branding. Bay Area luxury on the court.',
			'badge'             => '',
			'image'             => $img . '/sg-d02-skyyrose-shorts-2.jpg',
			'front_model_image' => '',
			'back_image'        => $img . '/sg-d02-skyyrose-shorts-1.jpg',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Black/Gold',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'sg-d03' => array(
			'sku'               => 'sg-d03',
			'name'              => 'Mint Rose Crewneck + Jogger Set',
			'price'             => 75.00,
			'collection'        => 'signature',
			'description'       => 'Mint green crewneck sweatshirt and matching joggers with purple rose-growing-from-concrete graphic. Large rose on crewneck front, smaller emblem on jogger thigh.',
			'badge'             => 'NEW',
			'image'             => $img . '/sg-d03-mint-crewneck-set.jpg',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'S|M|L|XL|2XL|3XL',
			'color'             => 'Mint Green/Purple',
			'edition_size'      => 250,
			'published'         => true,
			'is_preorder'       => false,
		),
		'sg-d04' => array(
			'sku'               => 'sg-d04',
			'name'              => 'Mint Rose Hooded Dress',
			'price'             => 65.00,
			'collection'        => 'signature',
			'description'       => 'Mint green hooded dress with large purple rose-growing-from-concrete graphic on front. Kangaroo pocket, purple drawstrings, relaxed fit.',
			'badge'             => 'NEW',
			'image'             => $img . '/sg-d04-mint-hooded-dress.jpg',
			'front_model_image' => '',
			'back_image'        => '',
			'back_model_image'  => '',
			'sizes'             => 'XS|S|M|L|XL|2XL',
			'color'             => 'Mint Green/Purple',
			'edition_size'      => 250,
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
