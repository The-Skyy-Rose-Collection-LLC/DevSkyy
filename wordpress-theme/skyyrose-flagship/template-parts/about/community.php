<?php
/**
 * About page — Oakland manifesto.
 *
 * Replaces the prior 3-pillar card grid with an editorial manifesto stack:
 * an all-caps Bebas list of Oakland places (no explanation) followed by a
 * short Cormorant frame paragraph. Customer-photo gallery preserved with
 * defensive file-existence skip.
 *
 * Called via get_template_part( 'template-parts/about/community', null, $args ).
 *
 * @param array $args {
 *     @type array  $allowed_inline   wp_kses whitelist for em/strong/br.
 *     @type array  $manifesto_places Array of place-name strings (rendered all-caps, dot-separated).
 *     @type string $frame_text       Short framing paragraph beneath the manifesto.
 *     @type array  $customer_photos  Array of customer photo data (file, alt) — optional gallery.
 * }
 *
 * @package SkyyRose
 * @since   1.3.0
 */

defined( 'ABSPATH' ) || exit;

$allowed_inline   = $args['allowed_inline'] ?? array();
$manifesto_places = $args['manifesto_places'] ?? array();
$frame_text       = $args['frame_text'] ?? '';
$customer_photos  = $args['customer_photos'] ?? array();
?>

<!-- Oakland Manifesto -->
<section class="abt-community" id="oakland" aria-label="<?php esc_attr_e( 'Oakland', 'skyyrose' ); ?>">
	<div class="abt-community__inner">
		<div class="abt-community__head rv">
			<span class="abt-community__label"><?php esc_html_e( 'The Town', 'skyyrose' ); ?></span>
			<span class="abt-community__rule" aria-hidden="true"></span>
		</div>
		<h2 class="abt-community__heading rv rv-clip-up rv-d1">
			<?php esc_html_e( 'Oakland', 'skyyrose' ); ?>
		</h2>

		<?php if ( ! empty( $manifesto_places ) ) : ?>
			<p class="abt-community__manifesto rv rv-split-line rv-d2" aria-label="<?php esc_attr_e( 'Oakland places', 'skyyrose' ); ?>">
				<?php
				$last = count( $manifesto_places ) - 1;
				foreach ( $manifesto_places as $i => $place ) {
					echo '<span class="abt-community__place">' . esc_html( $place ) . '</span>';
					if ( $i < $last ) {
						echo '<span class="abt-community__dot" aria-hidden="true">&middot;</span>';
					}
				}
				?>
			</p>
		<?php endif; ?>

		<?php if ( ! empty( $frame_text ) ) : ?>
			<p class="abt-community__frame rv rv-blur rv-d3">
				<?php echo wp_kses( $frame_text, $allowed_inline ); ?>
			</p>
		<?php endif; ?>
	</div>

	<?php
	$has_photos = false;
	foreach ( $customer_photos as $photo ) {
		if ( file_exists( get_theme_file_path( 'assets/images/customers/' . $photo['file'] ) ) ) {
			$has_photos = true;
			break;
		}
	}

	if ( $has_photos ) :
		?>
		<div class="abt-community__gallery rv">
			<p class="abt-community__gallery-label"><?php esc_html_e( 'The SkyyRose Family', 'skyyrose' ); ?></p>
			<div class="abt-community__photos">
				<?php
				foreach ( $customer_photos as $photo ) :
					$photo_path = get_theme_file_path( 'assets/images/customers/' . $photo['file'] );
					if ( file_exists( $photo_path ) ) :
						?>
					<figure class="abt-community__photo">
						<img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/customers/' . $photo['file'] ) ); ?>"
							alt="<?php echo esc_attr( $photo['alt'] ); ?>"
							loading="lazy" width="400" height="500">
					</figure>
						<?php
					endif;
				endforeach;
				?>
			</div>
		</div>
	<?php endif; ?>
</section>
