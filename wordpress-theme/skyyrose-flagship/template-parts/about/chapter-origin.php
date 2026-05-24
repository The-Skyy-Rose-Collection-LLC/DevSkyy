<?php
/**
 * About page — Chapter I: The Rebrand (Origin Story).
 *
 * Editorial single-column layout with drop cap on first paragraph and a
 * full-bleed pull quote breakout between paragraphs.
 *
 * Called via get_template_part( 'template-parts/about/chapter-origin', null, $args ).
 *
 * @param array $args {
 *     @type array  $allowed_inline    wp_kses whitelist for em/strong/br.
 *     @type string $origin_quote      Pull-quote string (Cinzel italic breakout).
 *     @type string $origin_cite       Attribution for the pull quote.
 *     @type array  $origin_paragraphs Array of paragraph strings (HTML allowed via $allowed_inline).
 * }
 *
 * @package SkyyRose
 * @since   1.3.0
 */

defined( 'ABSPATH' ) || exit;

$allowed_inline    = $args['allowed_inline'] ?? array();
$origin_quote      = $args['origin_quote'] ?? '';
$origin_cite       = $args['origin_cite'] ?? '';
$origin_paragraphs = $args['origin_paragraphs'] ?? array();

// Split paragraphs in half for pull-quote breakout positioning.
$total     = count( $origin_paragraphs );
$break_at  = (int) ceil( $total / 2 );
$paras_top = array_slice( $origin_paragraphs, 0, $break_at );
$paras_btm = array_slice( $origin_paragraphs, $break_at );
?>

<!-- Chapter I — The Rebrand -->
<section class="abt-chapter abt-chapter--origin" id="origin" aria-label="<?php esc_attr_e( 'The Rebrand Story', 'skyyrose' ); ?>">
	<div class="abt-chapter__container">
		<div class="abt-chapter__head rv rv-clip-up">
			<span class="abt-chapter__num" aria-hidden="true"><?php esc_html_e( 'CH. 01', 'skyyrose' ); ?></span>
			<span class="abt-chapter__rule" aria-hidden="true"></span>
			<span class="abt-chapter__label"><?php esc_html_e( 'The Origin', 'skyyrose' ); ?></span>
		</div>
		<h2 class="abt-chapter__title rv rv-clip-up rv-d1">
			<?php echo wp_kses( __( 'The Birth<br>of the Rebrand', 'skyyrose' ), $allowed_inline ); ?>
		</h2>

		<?php if ( ! empty( $paras_top ) ) : ?>
			<div class="abt-prose abt-prose--dropcap rv rv-blur rv-d2">
				<?php foreach ( $paras_top as $para ) : ?>
					<p><?php echo wp_kses( $para, $allowed_inline ); ?></p>
				<?php endforeach; ?>
			</div>
		<?php endif; ?>
	</div>

	<?php if ( ! empty( $origin_quote ) ) : ?>
		<aside class="abt-pull rv rv-clip-left" aria-label="<?php esc_attr_e( 'Pull quote', 'skyyrose' ); ?>">
			<div class="abt-pull__rule" aria-hidden="true"></div>
			<blockquote class="abt-pull__text">
				<?php echo wp_kses( $origin_quote, $allowed_inline ); ?>
			</blockquote>
			<?php if ( ! empty( $origin_cite ) ) : ?>
				<cite class="abt-pull__cite"><?php echo wp_kses( $origin_cite, $allowed_inline ); ?></cite>
			<?php endif; ?>
			<div class="abt-pull__rule" aria-hidden="true"></div>
		</aside>
	<?php endif; ?>

	<?php if ( ! empty( $paras_btm ) ) : ?>
		<div class="abt-chapter__container">
			<div class="abt-prose rv rv-blur rv-d2">
				<?php foreach ( $paras_btm as $para ) : ?>
					<p><?php echo wp_kses( $para, $allowed_inline ); ?></p>
				<?php endforeach; ?>
			</div>
		</div>
	<?php endif; ?>
</section>

<!-- Editorial Photo Divider -->
<?php
$story1_img = get_theme_file_path( 'assets/images/about-story-1.jpg' );
if ( file_exists( $story1_img ) ) :
	?>
	<div class="abt-divider rv" aria-hidden="true">
		<img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/about-story-1.jpg' ) ); ?>"
			alt="" loading="lazy" width="1920" height="700">
	</div>
<?php endif; ?>
