<?php
/**
 * About page — Community section (Oakland Roots).
 *
 * Called via get_template_part( 'template-parts/about/community', null, $args ).
 *
 * @param array $args {
 *     @type array $allowed_inline  wp_kses whitelist for em/strong/br.
 *     @type array $customer_photos Array of customer photo data (file, alt).
 * }
 *
 * @package SkyyRose_Flagship
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$allowed_inline  = $args['allowed_inline'] ?? array();
$customer_photos = $args['customer_photos'] ?? array();
?>

<!-- Community — Oakland Roots -->
<section class="abt-community" aria-label="<?php esc_attr_e( 'Our Community', 'skyyrose' ); ?>">
	<div class="abt-community__inner">
		<div class="abt-community__content rv">
			<h2 class="abt-community__heading">
				<?php esc_html_e( 'Rooted in Oakland, Built for the World', 'skyyrose' ); ?>
			</h2>
			<p class="abt-community__text">
				<?php
				echo wp_kses(
					__( 'Oakland isn\'t just where SkyyRose was born&mdash;it\'s <em>who</em> we are. The creativity, the resilience, the unapologetic swagger of the Bay Area runs through every thread of our brand. Fashion was always self-expression here. What you wear says who you are, where you\'re going, what you refuse to accept.', 'skyyrose' ),
					$allowed_inline
				);
				?>
			</p>
			<p class="abt-community__text">
				<?php
				echo wp_kses(
					__( 'SkyyRose is family-driven at its core. The Hurts bloodline, a grandmother\'s legacy, a father\'s promise to his daughter&mdash;that\'s the foundation. We give back because it\'s in our DNA. Whether partnering with local Oakland artists, supporting youth programs, or spotlighting the voices that inspire our collections&mdash;SkyyRose exists to lift up the community that lifted us.', 'skyyrose' ),
					$allowed_inline
				);
				?>
			</p>
		</div>
		<div class="abt-community__pillars rv rv-d2">
			<div class="abt-community__pillar">
				<h3><?php esc_html_e( 'Local Artists', 'skyyrose' ); ?></h3>
				<p><?php esc_html_e( 'Collaborating with Oakland creatives to bring fresh perspectives to every collection and campaign.', 'skyyrose' ); ?></p>
			</div>
			<div class="abt-community__pillar">
				<h3><?php esc_html_e( 'Youth Programs', 'skyyrose' ); ?></h3>
				<p><?php esc_html_e( 'Supporting the next generation of designers and entrepreneurs through mentorship and creative workshops.', 'skyyrose' ); ?></p>
			</div>
			<div class="abt-community__pillar">
				<h3><?php esc_html_e( 'Luxury Runs in the Family', 'skyyrose' ); ?></h3>
				<p><?php esc_html_e( 'From the Kids Capsule to every mainline collection, SkyyRose proves that quality, vision, and ambition are inherited. The next generation wears the crown too.', 'skyyrose' ); ?></p>
			</div>
		</div>
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
		<div class="abt-community__gallery rv rv-d3">
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
