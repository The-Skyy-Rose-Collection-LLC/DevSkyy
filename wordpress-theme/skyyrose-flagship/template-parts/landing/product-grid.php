<?php
/**
 * Landing Page — Product Grid
 *
 * Displays product cards with price, cost-per-wear, scarcity indicator.
 * Pulls product data from product-catalog.php by SKU list.
 *
 * Expected $args:
 *   'heading'     => string  Section heading ("The Collection")
 *   'subheading'  => string  Subtext below heading
 *   'skus'        => array   List of SKU strings to display
 *   'wear_count'  => int     Estimated wears for cost-per-wear calc (default 200)
 *   'remaining'   => array   SKU => remaining count map (optional scarcity data)
 *
 * @package SkyyRose_Flagship
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$heading    = $args['heading'] ?? 'The Collection';
$subheading = $args['subheading'] ?? '';
$skus       = $args['skus'] ?? array();
$wear_count = $args['wear_count'] ?? 200;
$remaining  = $args['remaining'] ?? array();

if ( empty( $skus ) ) {
	return;
}

$catalog = function_exists( 'skyyrose_get_product_catalog' ) ? skyyrose_get_product_catalog() : array();
$assets_uri = defined( 'SKYYROSE_ASSETS_URI' ) ? SKYYROSE_ASSETS_URI : '';
?>

<section class="lp-products" id="products">
	<div class="lp__container">
		<div class="lp-products__header lp-rv">
			<h2><?php echo esc_html( $heading ); ?></h2>
			<?php if ( $subheading ) : ?>
				<p><?php echo esc_html( $subheading ); ?></p>
			<?php endif; ?>
		</div>

		<div class="lp-products__grid">
			<?php
			$delay = 1;
			foreach ( $skus as $sku ) :
				$product = $catalog[ $sku ] ?? null;
				if ( ! $product ) {
					continue;
				}

				$name         = $product['name'];
				$price        = $product['price'];
				$image        = $product['image'] ?? '';
				$edition_size = $product['edition_size'] ?? 250;
				$left         = $remaining[ $sku ] ?? intval( $edition_size * 0.6 );
				$pct_sold     = round( ( ( $edition_size - $left ) / $edition_size ) * 100 );
				$cpw          = $wear_count > 0 ? round( $price / $wear_count, 2 ) : 0;

				// Build image URL
				$image_url = '';
				if ( $image ) {
					$image_url = strpos( $image, 'http' ) === 0 ? $image : get_template_directory_uri() . '/' . ltrim( $image, '/' );
				}
			?>
				<div class="lp-product-card lp-rv" data-delay="<?php echo esc_attr( min( $delay, 5 ) ); ?>">
					<?php if ( $image_url ) : ?>
						<div class="lp-product-card__image-wrap">
							<img src="<?php echo esc_url( $image_url ); ?>"
							     alt="<?php echo esc_attr( $name ); ?>"
							     loading="lazy"
							     width="400"
							     height="400"
							     decoding="async">
						</div>
					<?php endif; ?>

					<h3 class="lp-product-card__name"><?php echo esc_html( $name ); ?></h3>

					<div class="lp-product-card__price-row">
						<span class="lp-product-card__price">$<?php echo esc_html( number_format( $price, 0 ) ); ?></span>
						<?php if ( $cpw > 0 ) : ?>
							<span class="lp-product-card__cpw">$<?php echo esc_html( number_format( $cpw, 2 ) ); ?>/wear</span>
						<?php endif; ?>
					</div>

					<div class="lp-product-card__scarcity">
						<p class="lp-product-card__scarcity-text">
							<?php
							echo esc_html(
								sprintf( '%d of %d remaining', $left, $edition_size )
							);
							?>
						</p>
						<div class="lp-product-card__scarcity-bar">
							<div class="lp-product-card__scarcity-fill"
							     data-pct="<?php echo esc_attr( $pct_sold ); ?>"
							     style="width: 0%;"
							     aria-label="<?php echo esc_attr( $pct_sold . '% sold' ); ?>"></div>
						</div>
					</div>

					<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"
					   class="lp-btn lp-btn--primary lp-product-card__btn">
						Add to Bag
					</a>
				</div>
			<?php
				$delay++;
			endforeach;
			?>
		</div>
	</div>
</section>
