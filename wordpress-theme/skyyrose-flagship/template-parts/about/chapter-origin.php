<?php
/**
 * About page — Chapter I: The Rebrand (Origin Story).
 *
 * Called via get_template_part( 'template-parts/about/chapter-origin', null, $args ).
 *
 * @param array $args {
 *     @type array  $allowed_inline    wp_kses whitelist for em/strong/br.
 *     @type string $origin_quote      Founder quote string.
 *     @type string $origin_cite       Attribution string.
 *     @type array  $origin_paragraphs Array of paragraph strings.
 * }
 *
 * @package SkyyRose
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$allowed_inline    = $args['allowed_inline'] ?? array();
$origin_quote      = $args['origin_quote'] ?? '';
$origin_cite       = $args['origin_cite'] ?? '';
$origin_paragraphs = $args['origin_paragraphs'] ?? array();
?>

<!-- Chapter I — The Rebrand -->
<section class="abt-chapter abt-origin" id="origin" aria-label="<?php esc_attr_e( 'The Rebrand Story', 'skyyrose' ); ?>">
	<span class="abt-chapter__num rv-split-char" aria-hidden="true">01</span>
	<div class="abt-chapter__container">
		<p class="abt-chapter__label rv-blur-down"><?php esc_html_e( 'Chapter I', 'skyyrose' ); ?></p>
		<h2 class="abt-chapter__title rv-clip-up">
			<?php echo wp_kses( __( 'The Birth of<br>the Rebrand', 'skyyrose' ), $allowed_inline ); ?>
		</h2>

		<div class="abt-origin__grid">
			<div class="abt-origin__quote rv rv-d2">
				<blockquote>
					<?php echo wp_kses( $origin_quote, $allowed_inline ); ?>
				</blockquote>
				<cite><?php echo wp_kses( $origin_cite, $allowed_inline ); ?></cite>

				<?php
				$founder_img = get_theme_file_path( 'assets/images/founder-portrait.jpg' );
				if ( file_exists( $founder_img ) ) :
					?>
					<figure class="abt-origin__portrait rv rv-d3">
						<img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/founder-portrait.jpg' ) ); ?>"
							alt="<?php esc_attr_e( 'Corey Foster — Founder & CEO of SkyyRose', 'skyyrose' ); ?>"
							loading="lazy" width="600" height="750">
						<figcaption><?php esc_html_e( 'Corey Foster, Founder & CEO', 'skyyrose' ); ?></figcaption>
					</figure>
				<?php endif; ?>
			</div>
			<div class="abt-origin__text rv rv-d3">
				<?php foreach ( $origin_paragraphs as $para ) : ?>
					<p><?php echo wp_kses( $para, $allowed_inline ); ?></p>
				<?php endforeach; ?>
			</div>
		</div>
	</div>
</section>

<!-- Photo Divider 1 -->
<?php
$story1_img = get_theme_file_path( 'assets/images/about-story-1.jpg' );
if ( file_exists( $story1_img ) ) :
	?>
	<div class="abt-divider rv" aria-hidden="true">
		<img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/about-story-1.jpg' ) ); ?>"
			alt="" loading="lazy" width="1920" height="600">
		<div class="abt-divider__overlay"></div>
	</div>
<?php endif; ?>
