<?php
/**
 * About page — Chapter IV: Press Room.
 *
 * Called via get_template_part( 'template-parts/about/press-section', null, $args ).
 *
 * @param array $args {
 *     @type array  $allowed_inline   wp_kses whitelist for em/strong/br.
 *     @type string $youtube_embed_id YouTube video ID string.
 *     @type array  $press_features   Array of press feature data (src, year, headline, excerpt, url).
 *     @type string $arrow_svg        Arrow SVG markup string.
 * }
 *
 * @package SkyyRose_Flagship
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$allowed_inline   = $args['allowed_inline'] ?? array();
$youtube_embed_id = $args['youtube_embed_id'] ?? '';
$press_features   = $args['press_features'] ?? array();
$arrow_svg        = $args['arrow_svg'] ?? '';
$svg_kses         = skyyrose_svg_kses();
?>

<!-- Press Room -->
<section class="abt-chapter abt-press" id="press" aria-label="<?php esc_attr_e( 'Press & Media', 'skyyrose' ); ?>">
	<span class="abt-chapter__num rv-split-char" aria-hidden="true">04</span>
	<div class="abt-chapter__container">
		<p class="abt-chapter__label rv-blur-down"><?php esc_html_e( 'Chapter IV', 'skyyrose' ); ?></p>
		<h2 class="abt-chapter__title rv-clip-up"><?php esc_html_e( 'As Seen In', 'skyyrose' ); ?></h2>
		<p class="abt-press__intro rv rv-d2">
			<?php esc_html_e( 'The SkyyRose story has been recognized by national and regional publications for its authenticity, innovation, and the power of its origin.', 'skyyrose' ); ?>
		</p>

		<?php
		$press_img = get_theme_file_path( 'assets/images/press-the-blox-interview.jpg' );
		if ( file_exists( $press_img ) ) :
			?>
			<figure class="abt-press__photo rv rv-d2">
				<img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/press-the-blox-interview.jpg' ) ); ?>"
					alt="<?php esc_attr_e( 'Corey Foster interviewed on The Blox', 'skyyrose' ); ?>"
					loading="lazy" width="1200" height="675">
				<figcaption><?php esc_html_e( 'Corey Foster on The Blox — discussing the SkyyRose story', 'skyyrose' ); ?></figcaption>
			</figure>
		<?php endif; ?>

		<?php if ( ! empty( $youtube_embed_id ) ) : ?>
			<div class="abt-press__video-wrap rv rv-d3">
				<div class="abt-press__video-header">
					<span><?php esc_html_e( 'Featured Video', 'skyyrose' ); ?></span>
					<div class="abt-press__video-line" aria-hidden="true"></div>
				</div>
				<div class="abt-press__video-embed">
					<iframe
						src="<?php echo esc_url( 'https://www.youtube.com/embed/' . $youtube_embed_id . '?rel=0&modestbranding=1&color=white' ); ?>"
						title="<?php esc_attr_e( 'SkyyRose Collection — Featured Video', 'skyyrose' ); ?>"
						frameborder="0"
						allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
						allowfullscreen
						loading="lazy">
					</iframe>
				</div>
			</div>
		<?php endif; ?>
	</div>

	<div class="abt-press__scroll" id="pressScroll">
		<?php
		foreach ( $press_features as $pi => $pf ) :
			$delay = 'rv-d' . min( $pi + 1, 4 );
			?>
			<article class="abt-press-card rv <?php echo esc_attr( $delay ); ?>">
				<div class="abt-press-card__inner">
					<p class="abt-press-card__src"><?php echo esc_html( $pf['src'] ); ?></p>
					<p class="abt-press-card__year"><?php echo esc_html( $pf['year'] ); ?></p>
					<h3 class="abt-press-card__headline">
						<?php echo wp_kses( $pf['headline'], $allowed_inline ); ?>
					</h3>
					<p class="abt-press-card__excerpt">
						<?php echo wp_kses( $pf['excerpt'], $allowed_inline ); ?>
					</p>
					<?php if ( ! empty( $pf['url'] ) ) : ?>
						<a href="<?php echo esc_url( $pf['url'] ); ?>"
							class="abt-press-card__link"
							target="_blank"
							rel="noopener noreferrer">
							<?php esc_html_e( 'Read Article', 'skyyrose' ); ?>
							<?php echo wp_kses( $arrow_svg, $svg_kses ); ?>
						</a>
					<?php endif; ?>
				</div>
			</article>
		<?php endforeach; ?>
		<div class="abt-press__scroll-spacer" aria-hidden="true"></div>
	</div>

	<div class="abt-chapter__container">
		<div class="abt-press__hint rv" aria-hidden="true">
			<div class="abt-press__hint-line"></div>
			<span><?php esc_html_e( 'Scroll to explore', 'skyyrose' ); ?></span>
		</div>
	</div>
</section>
