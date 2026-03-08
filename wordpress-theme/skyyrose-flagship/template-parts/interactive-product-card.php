<?php
/**
 * Template Part: Interactive Product Card
 *
 * 3D rotating product card with drag-to-rotate cube, conversion layer
 * (size pills, scarcity counter, quick-buy), and wishlist/share actions.
 * Progressively enhanced by interactive-cards.js.
 *
 * Usage:
 *   get_template_part( 'template-parts/interactive-product-card', null, $args );
 *
 * @param array $args {
 *     @type array $product    Product data (sku, name, price, price_display, desc, image, url, sizes, is_preorder, badge).
 *     @type array $images     Render images keyed by view: front, back, branding (URLs).
 *     @type array $collection Collection config: slug, name, accent, accent_rgb.
 * }
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

// Parse top-level args.
$args = wp_parse_args( $args ?? array(), array(
	'product'    => array(),
	'images'     => array(),
	'collection' => array(),
) );

// Normalise product.
$product = wp_parse_args( is_array( $args['product'] ) ? $args['product'] : array(), array(
	'sku'           => '',
	'name'          => '',
	'price'         => 0,
	'price_display' => '',
	'desc'          => '',
	'image'         => '',
	'url'           => '#',
	'sizes'         => array(),
	'is_preorder'   => false,
	'badge'         => '',
) );

// Normalise images.
$images = wp_parse_args( is_array( $args['images'] ) ? $args['images'] : array(), array(
	'front'    => '',
	'back'     => '',
	'branding' => '',
) );

// Normalise collection.
$collection = wp_parse_args( is_array( $args['collection'] ) ? $args['collection'] : array(), array(
	'slug'       => '',
	'name'       => '',
	'accent'     => '#C0C0C0',
	'accent_rgb' => '192, 192, 192',
) );

// Resolve front face image: prefer render, fall back to product image.
$front_image = ! empty( $images['front'] ) ? $images['front'] : '';
if ( empty( $front_image ) && ! empty( $product['image'] ) ) {
	if ( 0 === strpos( $product['image'], 'http' ) ) {
		$front_image = $product['image'];
	} elseif ( function_exists( 'skyyrose_product_image_uri' ) ) {
		$front_image = skyyrose_product_image_uri( $product['image'] );
	} else {
		$front_image = get_theme_file_uri( $product['image'] );
	}
}
if ( empty( $front_image ) ) {
	$front_image = SKYYROSE_ASSETS_URI . '/images/placeholder-product.jpg';
}

// Count gallery faces.
$gallery_count = 1;
if ( ! empty( $images['back'] ) ) $gallery_count++;
if ( ! empty( $images['branding'] ) ) $gallery_count++;

// Check for GLB model.
$sku      = $product['sku'];
$glb_path = '/assets/models/' . $sku . '.glb';
$glb_src  = file_exists( SKYYROSE_DIR . $glb_path ) ? SKYYROSE_ASSETS_URI . $glb_path : '';

// Sizes.
$sizes_raw = $product['sizes'];
if ( is_string( $sizes_raw ) ) {
	$sizes_raw = array_filter( array_map( 'trim', explode( '|', $sizes_raw ) ) );
}
$sizes_array = is_array( $sizes_raw ) ? array_values( array_filter( $sizes_raw ) ) : array();

// Price display.
$price_display = '';
if ( ! empty( $product['price_display'] ) ) {
	$price_display = $product['price_display'];
} elseif ( ! empty( $product['price'] ) ) {
	$price_display = '$' . number_format( (float) $product['price'], 0 );
}

// Collection name.
$col_name = ! empty( $collection['name'] ) ? $collection['name'] : ucwords( str_replace( '-', ' ', $collection['slug'] ) );

// Stock / edition size.
$stock = 0;
if ( ! empty( $product['edition_size'] ) ) {
	$stock = (int) $product['edition_size'];
}

// Buy button label.
$buy_label = $product['is_preorder']
	? sprintf( __( 'Pre-Order — %s', 'skyyrose-flagship' ), wp_strip_all_tags( $price_display ) )
	: sprintf( __( 'Add to Cart — %s', 'skyyrose-flagship' ), wp_strip_all_tags( $price_display ) );
?>

<article class="ipc"
	data-product-sku="<?php echo esc_attr( $sku ); ?>"
	data-image-front="<?php echo esc_url( $front_image ); ?>"
	data-image-back="<?php echo esc_url( $images['back'] ); ?>"
	data-image-branding="<?php echo esc_url( $images['branding'] ); ?>"
	data-glb-src="<?php echo esc_url( $glb_src ); ?>"
	data-stock="<?php echo esc_attr( $stock ); ?>"
	data-price="<?php echo esc_attr( $product['price'] ); ?>"
	data-price-display="<?php echo esc_attr( wp_strip_all_tags( $price_display ) ); ?>"
	data-product-url="<?php echo esc_url( $product['url'] ); ?>"
	data-gallery-count="<?php echo esc_attr( $gallery_count ); ?>"
	tabindex="0"
	role="group"
	aria-label="<?php echo esc_attr( sprintf(
		/* translators: %s: product name */
		__( 'Product: %s', 'skyyrose-flagship' ),
		$product['name']
	) ); ?>"
	style="--collection-accent: <?php echo esc_attr( $collection['accent'] ); ?>; --collection-accent-rgb: <?php echo esc_attr( $collection['accent_rgb'] ); ?>;">

	<!-- 3D Rotating Container -->
	<div class="ipc__cube" style="--cube-z: 0px;">

		<!-- Front face (always present) -->
		<div class="ipc__face ipc__face--front">
			<img src="<?php echo esc_url( $front_image ); ?>"
				alt="<?php echo esc_attr( sprintf(
					/* translators: %s: product name */
					__( '%s front view', 'skyyrose-flagship' ),
					$product['name']
				) ); ?>"
				width="400" height="533" loading="lazy" decoding="async">
		</div>

		<?php if ( ! empty( $images['back'] ) ) : ?>
		<div class="ipc__face ipc__face--back">
			<img src="<?php echo esc_url( $images['back'] ); ?>"
				alt="<?php echo esc_attr( sprintf(
					/* translators: %s: product name */
					__( '%s back view', 'skyyrose-flagship' ),
					$product['name']
				) ); ?>"
				width="400" height="533" loading="lazy" decoding="async">
		</div>
		<?php endif; ?>

		<?php if ( ! empty( $images['branding'] ) ) : ?>
		<div class="ipc__face ipc__face--branding">
			<img src="<?php echo esc_url( $images['branding'] ); ?>"
				alt="<?php echo esc_attr( sprintf(
					/* translators: %s: product name */
					__( '%s branding detail', 'skyyrose-flagship' ),
					$product['name']
				) ); ?>"
				width="400" height="533" loading="lazy" decoding="async">
		</div>
		<?php endif; ?>

	</div>

	<!-- model-viewer (hidden, activated by JS when .glb exists) -->
	<model-viewer class="ipc__3d"
		src=""
		poster="<?php echo esc_url( $front_image ); ?>"
		camera-controls auto-rotate shadow-intensity="0.4"
		ar ar-modes="webxr scene-viewer quick-look"
		alt="<?php echo esc_attr( sprintf(
			/* translators: %s: product name */
			__( '%s 3D model', 'skyyrose-flagship' ),
			$product['name']
		) ); ?>"
		style="display:none;">
	</model-viewer>

	<?php if ( $gallery_count > 1 ) : ?>
	<!-- Dot indicators -->
	<div class="ipc__dots" aria-hidden="true">
		<span class="ipc__dot ipc__dot--active"></span>
		<?php for ( $i = 1; $i < $gallery_count; $i++ ) : ?>
			<span class="ipc__dot"></span>
		<?php endfor; ?>
	</div>
	<?php endif; ?>

	<!-- Badges -->
	<?php if ( ! empty( $product['badge'] ) || ! empty( $col_name ) ) : ?>
		<span class="ipc__badge"><?php echo esc_html( strtoupper( $col_name ) ); ?></span>
	<?php endif; ?>

	<?php if ( $product['is_preorder'] ) : ?>
		<span class="ipc__pre-badge"><?php esc_html_e( 'Pre-Order', 'skyyrose-flagship' ); ?></span>
	<?php endif; ?>

	<!-- Quick Actions -->
	<div class="ipc__actions">
		<button class="ipc__wishlist"
			data-wishlist-id="<?php echo esc_attr( $sku ); ?>"
			aria-label="<?php echo esc_attr( sprintf(
				/* translators: %s: product name */
				__( 'Add %s to wishlist', 'skyyrose-flagship' ),
				$product['name']
			) ); ?>"
			aria-pressed="false"
			type="button">
			<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
				<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
			</svg>
		</button>
		<button class="ipc__share"
			aria-label="<?php echo esc_attr( sprintf(
				/* translators: %s: product name */
				__( 'Share %s', 'skyyrose-flagship' ),
				$product['name']
			) ); ?>"
			type="button">
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
				<circle cx="18" cy="5" r="3"/>
				<circle cx="6" cy="12" r="3"/>
				<circle cx="18" cy="19" r="3"/>
				<line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
				<line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
			</svg>
		</button>
	</div>

	<!-- Conversion Layer -->
	<div class="ipc__conversion">

		<?php if ( $stock > 0 && $stock <= 20 ) : ?>
		<div class="ipc__scarcity" aria-live="polite">
			<?php
			printf(
				/* translators: %s: stock count */
				esc_html__( 'Only %s left', 'skyyrose-flagship' ),
				'<span class="ipc__stock-count">' . esc_html( $stock ) . '</span>'
			);
			?>
		</div>
		<?php endif; ?>

		<?php if ( ! empty( $sizes_array ) ) : ?>
		<div class="ipc__sizes" role="radiogroup" aria-label="<?php esc_attr_e( 'Select size', 'skyyrose-flagship' ); ?>">
			<?php foreach ( $sizes_array as $size ) : ?>
				<button class="ipc__size-pill"
					data-size="<?php echo esc_attr( $size ); ?>"
					role="radio"
					aria-checked="false"
					type="button">
					<?php echo esc_html( $size ); ?>
				</button>
			<?php endforeach; ?>
		</div>
		<?php endif; ?>

		<button class="ipc__buy-btn"
			<?php echo ! empty( $sizes_array ) ? 'disabled' : ''; ?>
			type="button"
			aria-label="<?php echo esc_attr( $buy_label ); ?>">
			<?php echo esc_html( $buy_label ); ?>
		</button>

	</div>

	<!-- Info -->
	<div class="ipc__info">
		<h3 class="ipc__title">
			<a href="<?php echo esc_url( $product['url'] ); ?>">
				<?php echo esc_html( $product['name'] ); ?>
			</a>
		</h3>
		<?php if ( ! empty( $col_name ) ) : ?>
			<span class="ipc__collection-tag">
				<?php echo esc_html( strtoupper( $col_name ) . ' COLLECTION' ); ?>
			</span>
		<?php endif; ?>
	</div>

</article>
