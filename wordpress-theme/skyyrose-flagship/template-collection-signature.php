<?php
/**
 * Template Name: Collection - Signature
 *
 * SIGNATURE collection page — Elevated luxury mood with rotating 3D logo,
 * product grid, story section, immersive CTA, and pre-order CTA.
 * Rose gold (#B76E79) / gold (#D4AF37) accents.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

defined( 'ABSPATH' ) || exit;

get_header();

/**
 * Build the SIGNATURE product list for template rendering.
 *
 * Uses the centralized catalog (inc/product-catalog.php) as source of truth.
 * Splits sg-001 (Bay Set) and sg-002 (Stay Golden) into tee+shorts variants
 * for the collection display.
 */
if ( ! function_exists( 'skyyrose_get_signature_products' ) ) :
function skyyrose_get_signature_products() {

	// Try WooCommerce first.
	if ( function_exists( 'wc_get_products' ) ) {
		$wc_products = wc_get_products(
			array(
				'limit'    => 15,
				'category' => array( 'signature' ),
				'status'   => 'publish',
				'orderby'  => 'menu_order',
				'order'    => 'ASC',
			)
		);

		if ( ! empty( $wc_products ) ) {
			$products = array();
			foreach ( $wc_products as $wc_product ) {
				$products[] = array(
					'sku'   => $wc_product->get_sku(),
					'name'  => $wc_product->get_name(),
					'price' => $wc_product->get_price_html(),
					'desc'  => wp_strip_all_tags( $wc_product->get_short_description() ),
					'badge' => $wc_product->get_meta( '_collection_badge' ),
					'url'   => get_permalink( $wc_product->get_id() ),
					'image' => wp_get_attachment_url( $wc_product->get_image_id() ),
				);
			}
			return $products;
		}
	}

	// Fallback: centralized product catalog with set splits.
	$catalog_products = skyyrose_get_collection_products( 'signature' );
	$display_products = array();

	// SKUs that represent sets — split into tee + shorts for collection display.
	$set_skus = array( 'sg-001', 'sg-002' );

	foreach ( $catalog_products as $p ) {
		$img_uri = skyyrose_product_image_uri( $p['image'] );

		if ( in_array( $p['sku'], $set_skus, true ) ) {
			// Split set into tee and shorts.
			$display_products[] = array(
				'sku'        => $p['sku'] . '-tee',
				'name'       => $p['name'] . ' — Tee',
				'price'      => '$40.00',
				'desc'       => $p['description'],
				'badge'      => $p['badge'],
				'image'      => $img_uri,
				'back_image' => '',
			);
			$shorts_img = 'sg-001' === $p['sku']
				? $img_uri
				: skyyrose_product_image_uri( 'assets/images/products/sg-010-bridge-shorts.webp' );
			$display_products[] = array(
				'sku'        => $p['sku'] . '-shorts',
				'name'       => $p['name'] . ' — Shorts',
				'price'      => '$50.00',
				'desc'       => $p['description'],
				'badge'      => $p['badge'],
				'image'      => $shorts_img,
				'back_image' => '',
			);
		} else {
			$display_products[] = array(
				'sku'        => $p['sku'],
				'name'       => $p['name'],
				'price'      => skyyrose_format_price( $p ),
				'desc'       => $p['description'],
				'badge'      => $p['badge'],
				'image'      => $img_uri,
				'back_image' => ! empty( $p['back_image'] ) ? skyyrose_product_image_uri( $p['back_image'] ) : '',
			);
		}
	}

	return $display_products;
}
endif;

$skyyrose_sg_products    = skyyrose_get_signature_products();
$skyyrose_sg_shop_url    = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : '/shop';
$skyyrose_sg_placeholder = esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder-product.jpg' );
$skyyrose_sg_logo_url    = esc_url( get_template_directory_uri() . '/assets/branding/signature-logo.jpg' );
$skyyrose_sg_scene_url   = esc_url( get_template_directory_uri() . '/assets/scenes/signature/signature-golden-gate-showroom.png' );
?>

<main id="primary" class="site-main" role="main">
<div class="collection--signature" data-collection="signature">

	<!-- ============================================================
	     HERO SECTION — Rotating 3D Logo
	     ============================================================ -->
	<section class="collection-hero" aria-label="<?php esc_attr_e( 'Collection hero', 'skyyrose-flagship' ); ?>"
		style="background-image: url('<?php echo esc_attr( $skyyrose_sg_scene_url ); ?>'); background-size: cover; background-position: center;">

		<div class="collection-logo-3d collection-logo-3d--signature">
			<img src="<?php echo esc_url( $skyyrose_sg_logo_url ); ?>"
			     alt="<?php echo esc_attr__( 'Signature Collection Logo', 'skyyrose-flagship' ); ?>"
			     width="280"
			     height="280"
			     fetchpriority="high"
			     loading="eager" />
		</div>

		<h1 class="collection-hero__title">
			<?php echo esc_html__( 'Signature Collection', 'skyyrose-flagship' ); ?>
		</h1>

		<p class="collection-hero__subtitle">
			<?php echo esc_html__( 'West Coast Prestige', 'skyyrose-flagship' ); ?>
		</p>

		<a href="#products" class="collection-hero__cta">
			<?php echo esc_html__( 'Discover the Line', 'skyyrose-flagship' ); ?>
		</a>
	</section>

	<!-- ============================================================
	     COLLECTION STORY
	     ============================================================ -->
	<section class="collection-story" id="story">
		<p class="collection-story__text">
			<?php echo esc_html__( 'The Signature collection is the heart of SKyyRose. It is where our story began — rose gold warmth meeting modern streetwear sensibility. Every piece carries the DNA of the brand: quality fabrics, intentional design, and a commitment to self-expression. From pastel colorblock sets to essential tees, these are the pieces you build your wardrobe around. Timeless by design, luxurious by nature.', 'skyyrose-flagship' ); ?>
		</p>
	</section>

	<!-- ============================================================
	     PRODUCT GRID
	     ============================================================ -->
	<section id="products" class="collection-products" aria-labelledby="products-heading">
		<h2 id="products-heading" class="screen-reader-text">
			<?php echo esc_html__( 'Signature Products', 'skyyrose-flagship' ); ?>
		</h2>
		<div class="collection-grid">
			<?php
			foreach ( $skyyrose_sg_products as $skyyrose_product ) :
				$skyyrose_p_url   = isset( $skyyrose_product['url'] ) ? $skyyrose_product['url'] : '#';
				$skyyrose_p_image = ! empty( $skyyrose_product['image'] ) ? $skyyrose_product['image'] : $skyyrose_sg_placeholder;
				?>
				<a href="<?php echo esc_url( $skyyrose_p_url ); ?>"
				   class="collection-product-card"
				   aria-label="<?php echo esc_attr( $skyyrose_product['name'] ); ?>">

					<?php if ( ! empty( $skyyrose_product['badge'] ) ) : ?>
						<span class="collection-product-card__badge">
							<?php echo esc_html( $skyyrose_product['badge'] ); ?>
						</span>
					<?php endif; ?>

					<div class="collection-product-card__image-container">
						<img class="collection-product-card__image"
						     src="<?php echo esc_url( $skyyrose_p_image ); ?>"
						     alt="<?php echo esc_attr( $skyyrose_product['name'] ); ?>"
						     loading="lazy"
						     width="400"
						     height="533"
						     data-fallback="<?php echo esc_url( $skyyrose_sg_placeholder ); ?>" />
						<?php if ( ! empty( $skyyrose_product['back_image'] ) ) : ?>
							<img class="collection-product-card__image collection-product-card__image--back"
							     src="<?php echo esc_url( $skyyrose_product['back_image'] ); ?>"
							     alt="<?php /* translators: %s: product name */ echo esc_attr( sprintf( __( '%s — back view', 'skyyrose-flagship' ), $skyyrose_product['name'] ) ); ?>"
							     loading="lazy"
							     width="400"
							     height="533" />
						<?php endif; ?>
					</div>

					<div class="collection-product-card__info">
						<h3 class="collection-product-card__name">
							<?php echo esc_html( $skyyrose_product['name'] ); ?>
						</h3>
						<p class="collection-product-card__price">
							<?php echo wp_kses_post( $skyyrose_product['price'] ); ?>
						</p>
					</div>
				</a>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ============================================================
	     IMMERSIVE CTA
	     ============================================================ -->
	<section class="collection-immersive-cta">
		<a href="<?php echo esc_url( home_url( '/immersive/signature/' ) ); ?>"
		   class="collection-immersive-cta__link">
			<?php echo esc_html__( 'Enter the 3D Experience', 'skyyrose-flagship' ); ?>
		</a>
	</section>

	<!-- ============================================================
	     PRE-ORDER CTA
	     ============================================================ -->
	<!-- Conversion Intelligence -->
	<div data-cie-viewers="35" style="text-align:center; padding:1rem 0;"></div>
	<div data-cie-confidence></div>
	<div data-cie-preorder-progress style="max-width:480px; margin:0 auto; padding:1rem 2rem;"></div>

	<section class="collection-preorder-cta">
		<div data-cie-countdown="auto" data-cie-countdown-label="<?php esc_attr_e( 'Pre-Order Window', 'skyyrose-flagship' ); ?>" style="display:flex; justify-content:center; margin-bottom:1.5rem;"></div>
		<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"
		   class="collection-preorder-cta__btn">
			<?php echo esc_html__( 'Pre-Order Now', 'skyyrose-flagship' ); ?>
		</a>
	</section>

	<!-- ============================================================
	     EXPLORE OTHER COLLECTIONS
	     ============================================================ -->
	<section class="collection-explore fade-in-up">
		<h2 class="collection-explore__heading">
			<?php echo esc_html__( 'Explore Other Collections', 'skyyrose-flagship' ); ?>
		</h2>

		<div class="collection-explore__grid">
			<?php
			$skyyrose_other_collections = array(
				array(
					'slug' => 'collection-black-rose',
					'name' => __( 'BLACK ROSE', 'skyyrose-flagship' ),
					'desc' => __( 'Gothic Garden', 'skyyrose-flagship' ),
				),
				array(
					'slug' => 'collection-love-hurts',
					'name' => __( 'Love Hurts', 'skyyrose-flagship' ),
					'desc' => __( 'Passionate Drama', 'skyyrose-flagship' ),
				),
				array(
					'slug' => 'collection-kids-capsule',
					'name' => __( 'Kids Capsule', 'skyyrose-flagship' ),
					'desc' => __( 'Playful Energy', 'skyyrose-flagship' ),
				),
			);

			foreach ( $skyyrose_other_collections as $skyyrose_col ) :
				$skyyrose_link = home_url( '/' . $skyyrose_col['slug'] . '/' );
				?>
				<a href="<?php echo esc_url( $skyyrose_link ); ?>"
				   class="collection-explore__link">
					<span class="collection-explore__link-name">
						<?php echo esc_html( $skyyrose_col['name'] ); ?>
					</span>
					<span class="collection-explore__link-desc">
						<?php echo esc_html( $skyyrose_col['desc'] ); ?>
					</span>
				</a>
			<?php endforeach; ?>
		</div>
	</section>

</div><!-- .collection--signature -->
</main><!-- #primary -->

<?php get_footer(); ?>
