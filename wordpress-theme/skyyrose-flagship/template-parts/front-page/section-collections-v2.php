<?php
/**
 * Template Part: Collection Cards (Homepage V2)
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 *
 * @param array $args {
 *     @type array  $collections  Collection data array.
 *     @type string $assets_uri   Theme assets URI.
 * }
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$collections = $args['collections'] ?? array();
$assets_uri  = $args['assets_uri'] ?? '';
?>
<!-- ═══ COLLECTIONS ═══ -->
<section class="collections" id="collections" aria-label="<?php esc_attr_e( 'Our Collections', 'skyyrose-flagship' ); ?>">
	<div class="col-header rv">
		<p class="col-header-eyebrow"><?php esc_html_e( 'The Collections', 'skyyrose-flagship' ); ?></p>
		<h2 class="col-header-title"><?php echo esc_html( 'Three Worlds. One Vision.' ); ?></h2>
	</div>
	<div class="col-grid">
		<?php
		$delay = 1;
		foreach ( $collections as $slug => $col ) :
			$key         = $col['key'];
			$delay_class = 'rv-d' . min( $delay, 3 );
			?>
			<a href="<?php echo esc_url( $col['link'] ); ?>" class="col-card <?php echo esc_attr( $key ); ?> rv <?php echo esc_attr( $delay_class ); ?>">
				<div class="col-card-img">
					<img
						src="<?php echo esc_url( $assets_uri . '/images/' . $col['img'] ); ?>"
						alt="<?php echo esc_attr( $col['name'] . ' Collection' ); ?>"
						loading="lazy"
						decoding="async"
						width="480"
						height="640"
					/>
				</div>
				<div class="col-card-ov"></div>
				<div class="col-card-content">
					<p class="col-card-num"><?php echo esc_html( 'Collection ' . $col['number'] ); ?></p>
					<h3 class="col-card-name">
						<?php
						$name_parts = explode( ' ', $col['name'] );
						echo esc_html( $name_parts[0] );
						if ( isset( $name_parts[1] ) ) {
							echo '<br>' . esc_html( $name_parts[1] );
						}
						?>
					</h3>
					<p class="col-card-tag"><?php echo esc_html( $col['tagline'] ); ?></p>
					<div class="col-card-meta">
						<span><?php echo esc_html( $col['product_count'] . ' Pieces' ); ?></span>
						<?php if ( ! empty( $col['price_range'] ) ) : ?>
							<span><?php echo wp_kses_post( $col['price_range'] ); ?></span>
						<?php endif; ?>
						<span><?php echo esc_html( $col['meta_tag'] ); ?></span>
					</div>
					<span class="col-card-cta"><?php esc_html_e( 'Explore Collection', 'skyyrose-flagship' ); ?></span>
				</div>
			</a>
			<?php
			$delay++;
		endforeach;
		?>
	</div>
</section>
