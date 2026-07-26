<?php
/**
 * About page — Chapter IV: Press Room.
 *
 * Newspaper-style 2-column grid: each feature is a column-of-type with a
 * masthead, date stamp, italic headline, short Hanken Grotesk excerpt, and a
 * monospace "READ →" link. No card chrome — rules between columns/rows.
 * The Blox YouTube embed renders above the grid as a letterboxed module.
 *
 * Called via get_template_part( 'template-parts/about/press-section', null, $args ).
 *
 * @param array $args {
 *     @type array  $allowed_inline   wp_kses whitelist for em/strong/br.
 *     @type string $youtube_embed_id YouTube video ID string.
 *     @type array  $press_features   Array of press feature data (src, year, headline, excerpt, url).
 *     @type string $arrow_svg        Arrow SVG markup string (passed for "READ →" affordance).
 * }
 *
 * @package SkyyRose
 * @since   1.3.0
 */

defined( 'ABSPATH' ) || exit;

$allowed_inline   = $args['allowed_inline'] ?? array();
$youtube_embed_id = $args['youtube_embed_id'] ?? '';
$press_features   = $args['press_features'] ?? array();
$arrow_svg        = $args['arrow_svg'] ?? '';
$svg_kses         = function_exists( 'skyyrose_svg_kses' ) ? skyyrose_svg_kses() : array();
?>

<!-- Chapter IV — Press Room -->
<section class="abt-chapter abt-chapter--press" id="press" aria-label="<?php esc_attr_e( 'Press & Media', 'skyyrose' ); ?>">
	<div class="abt-chapter__container">
		<div class="abt-chapter__head rv">
			<span class="abt-chapter__num" aria-hidden="true"><?php esc_html_e( 'CH. 04', 'skyyrose' ); ?></span>
			<span class="abt-chapter__rule" aria-hidden="true"></span>
			<span class="abt-chapter__label"><?php esc_html_e( 'Press', 'skyyrose' ); ?></span>
		</div>
		<h2 class="abt-chapter__title rv rv-clip-up rv-d1">
			<?php esc_html_e( 'As Seen In', 'skyyrose' ); ?>
		</h2>

		<?php
		$press_img = get_theme_file_path( 'assets/images/press-the-blox-interview.jpg' );
		if ( file_exists( $press_img ) ) :
			?>
			<figure class="abt-press__poster rv rv-d2">
				<picture>
					<source srcset="<?php echo esc_url( get_theme_file_uri( 'assets/images/press-the-blox-interview.avif' ) ); ?>" type="image/avif">
					<source srcset="<?php echo esc_url( get_theme_file_uri( 'assets/images/press-the-blox-interview.webp' ) ); ?>" type="image/webp">
					<img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/press-the-blox-interview.jpg' ) ); ?>"
						alt="<?php esc_attr_e( 'Corey Foster interviewed on The Blox', 'skyyrose' ); ?>"
						loading="lazy" width="1200" height="675">
				</picture>
				<figcaption class="abt-press__poster-cap"><?php esc_html_e( 'Corey Foster on The Blox', 'skyyrose' ); ?></figcaption>
			</figure>
		<?php endif; ?>

		<?php if ( ! empty( $youtube_embed_id ) ) : ?>
			<div class="abt-press__video rv rv-d3">
				<div class="abt-press__video-meta">
					<span class="abt-press__video-label"><?php esc_html_e( 'Featured Video', 'skyyrose' ); ?></span>
					<span class="abt-press__video-rule" aria-hidden="true"></span>
					<span class="abt-press__video-source"><?php esc_html_e( 'The Blox', 'skyyrose' ); ?></span>
				</div>
				<div class="abt-press__video-frame">
					<iframe
						src="<?php echo esc_url( 'https://www.youtube-nocookie.com/embed/' . $youtube_embed_id . '?rel=0&modestbranding=1' ); ?>"
						title="<?php esc_attr_e( 'SkyyRose Collection — The Blox Interview', 'skyyrose' ); ?>"
						frameborder="0"
						allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
						allowfullscreen
						loading="lazy">
					</iframe>
				</div>
			</div>
		<?php endif; ?>
	</div>

	<div class="abt-press__paper stagger-grid">
		<?php foreach ( $press_features as $pi => $pf ) : ?>
			<article class="abt-press__col">
				<header class="abt-press__col-head">
					<p class="abt-press__col-src"><?php echo esc_html( $pf['src'] ); ?></p>
					<p class="abt-press__col-date">
						<?php echo esc_html( $pf['year'] ); ?>
					</p>
				</header>
				<h3 class="abt-press__col-headline">
					<?php echo wp_kses( $pf['headline'], $allowed_inline ); ?>
				</h3>
				<p class="abt-press__col-excerpt">
					<?php echo wp_kses( $pf['excerpt'], $allowed_inline ); ?>
				</p>
				<?php if ( ! empty( $pf['url'] ) ) : ?>
					<a href="<?php echo esc_url( $pf['url'] ); ?>"
						class="abt-press__col-link"
						target="_blank"
						rel="noopener noreferrer">
						<?php esc_html_e( 'Read', 'skyyrose' ); ?>
						<?php echo wp_kses( $arrow_svg, $svg_kses ); ?>
					</a>
				<?php endif; ?>
			</article>
		<?php endforeach; ?>
	</div>
</section>
