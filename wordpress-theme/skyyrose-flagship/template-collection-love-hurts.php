<?php
/**
 * Template Name: Collection - Love Hurts
 *
 * LOVE HURTS collection page — Passionate drama mood with rotating 3D logo,
 * product grid, story section, immersive CTA, and pre-order CTA.
 * Crimson (#DC143C) accents on deep black.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

defined( 'ABSPATH' ) || exit;

get_header();

/**
 * Build the LOVE HURTS product list for template rendering.
 *
 * Uses the centralized catalog (inc/product-catalog.php) as source of truth.
 * Adds the lh-002b (white joggers) variant for the collection display.
 */
if ( ! function_exists( 'skyyrose_get_love_hurts_products' ) ) :
function skyyrose_get_love_hurts_products() {

	// Try WooCommerce first.
	if ( function_exists( 'wc_get_products' ) ) {
		$wc_products = wc_get_products(
			array(
				'limit'    => 6,
				'category' => array( 'love-hurts' ),
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

	// Fallback: centralized product catalog.
	$catalog_products = skyyrose_get_collection_products( 'love-hurts' );
	$display_products = array();

	foreach ( $catalog_products as $p ) {
		// Skip unpublished products.
		if ( empty( $p['published'] ) ) {
			continue;
		}
		// Prefer VTON front-model image over flat product shot.
		$primary_img = ! empty( $p['front_model_image'] ) ? $p['front_model_image'] : $p['image'];
		$display_products[] = array(
			'sku'        => $p['sku'],
			'name'       => $p['name'],
			'price'      => skyyrose_format_price( $p ),
			'desc'       => $p['description'],
			'badge'      => $p['badge'],
			'image'      => skyyrose_product_image_uri( $primary_img ),
			'back_image' => ! empty( $p['back_image'] ) ? skyyrose_product_image_uri( $p['back_image'] ) : '',
			'url'        => skyyrose_product_url( $p['sku'] ),
		);

		// Insert white joggers variant after the black joggers.
		// NOTE: lh-002b has no dedicated white-colorway image yet. Use the flat
		// product image (not front-model VTON) as a neutral stand-in until a
		// white variant WebP is available.
		if ( 'lh-002' === $p['sku'] ) {
			$display_products[] = array(
				'sku'        => 'lh-002b',
				'name'       => __( 'Love Hurts Joggers (WHITE)', 'skyyrose-flagship' ),
				'price'      => skyyrose_format_price( $p ),
				'desc'       => __( 'The same Oakland fire in a fresh white colorway — embroidered rose, tapered fit', 'skyyrose-flagship' ),
				'badge'      => __( 'New', 'skyyrose-flagship' ),
				'image'      => skyyrose_product_image_uri( $p['image'] ),
				'back_image' => '',
				'url'        => skyyrose_product_url( 'lh-002' ),
			);
		}
	}

	return $display_products;
}
endif;

$skyyrose_lh_products    = skyyrose_get_love_hurts_products();
$skyyrose_lh_shop_url    = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : '/shop';
$skyyrose_lh_placeholder = esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder-product.jpg' );
$skyyrose_lh_logo_url    = esc_url( get_template_directory_uri() . '/assets/branding/love-hurts-logo.webp' );
$skyyrose_lh_scene_url   = esc_url( get_template_directory_uri() . '/assets/scenes/love-hurts/love-hurts-giant-rose-staircase.png' );
?>

<main id="primary" class="site-main" role="main" tabindex="-1">
<div class="collection--love-hurts" data-collection="love-hurts">

	<!-- ============================================================
	     HERO SECTION — Rotating 3D Logo
	     ============================================================ -->
	<section class="collection-hero" aria-label="<?php esc_attr_e( 'Collection hero', 'skyyrose-flagship' ); ?>"
		style="background-image: url('<?php echo esc_attr( $skyyrose_lh_scene_url ); ?>'); background-size: cover; background-position: center;">

		<div class="collection-logo-3d collection-logo-3d--love-hurts">
			<img src="<?php echo esc_url( $skyyrose_lh_logo_url ); ?>"
			     alt="<?php echo esc_attr__( 'Love Hurts Collection Logo', 'skyyrose-flagship' ); ?>"
			     width="280"
			     height="280"
			     fetchpriority="high"
			     loading="eager" />
		</div>

		<h1 class="collection-hero__title">
			<?php echo esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ); ?>
		</h1>

		<p class="collection-hero__subtitle">
			<?php echo esc_html__( 'Passion Forged in Fire', 'skyyrose-flagship' ); ?>
		</p>

		<a href="#products" class="collection-hero__cta">
			<?php echo esc_html__( 'Shop the Pain', 'skyyrose-flagship' ); ?>
		</a>
	</section>

	<!-- ============================================================
	     COLLECTION STORY
	     ============================================================ -->
	<section class="collection-story" id="story" aria-labelledby="story-heading">
		<h2 id="story-heading" class="screen-reader-text"><?php esc_html_e( 'Collection Story', 'skyyrose-flagship' ); ?></h2>
		<p class="collection-story__text">
			<?php echo esc_html__( 'The Love Hurts collection is born from the raw, unfiltered intensity of real love. Crimson reds bleed into midnight blacks. Every stitch tells a story of passion, heartbreak, and the courage to love again. This is not for the faint of heart — it is for those who love fiercely, who wear their scars as badges of honor, and who know that the deepest connections always come with a cost.', 'skyyrose-flagship' ); ?>
		</p>
	</section>

	<!-- ============================================================
	     PRODUCT GRID
	     ============================================================ -->
	<section id="products" class="collection-products" aria-labelledby="products-heading">
		<h2 id="products-heading" class="screen-reader-text">
			<?php echo esc_html__( 'Love Hurts Products', 'skyyrose-flagship' ); ?>
		</h2>
		<div class="collection-grid">
			<?php
			foreach ( $skyyrose_lh_products as $skyyrose_product ) :
				$skyyrose_p_url   = isset( $skyyrose_product['url'] ) ? $skyyrose_product['url'] : '#';
				$skyyrose_p_image = ! empty( $skyyrose_product['image'] ) ? $skyyrose_product['image'] : $skyyrose_lh_placeholder;
				?>
				<a href="<?php echo esc_url( $skyyrose_p_url ); ?>"
				   class="collection-product-card">

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
						     data-fallback="<?php echo esc_url( $skyyrose_lh_placeholder ); ?>" />
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
		<a href="<?php echo esc_url( home_url( '/experience-love-hurts/' ) ); ?>"
		   class="collection-immersive-cta__link"
		   aria-label="<?php esc_attr_e( 'Enter the Love Hurts 3D Experience', 'skyyrose-flagship' ); ?>">
			<?php echo esc_html__( 'Enter the 3D Experience', 'skyyrose-flagship' ); ?>
		</a>
	</section>

	<!-- ============================================================
	     PRE-ORDER CTA
	     ============================================================ -->
	<!-- Conversion Intelligence -->
	<div data-cie-viewers="27" style="text-align:center; padding:1rem 0;"></div>
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
					'slug' => 'collection-signature',
					'name' => __( 'Signature', 'skyyrose-flagship' ),
					'desc' => __( 'Elevated Luxury', 'skyyrose-flagship' ),
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

</div><!-- .collection--love-hurts -->
</main><!-- #primary -->

<?php get_footer(); ?>
