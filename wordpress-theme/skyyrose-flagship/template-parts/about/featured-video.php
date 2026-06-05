<?php
/**
 * About page — Featured Video module (The Blox interview).
 *
 * Relocated directly beneath the hero (from Chapter IV — Press Room) so the
 * founder interview leads the page. Reuses the `.abt-press__video*` visual
 * module already defined in about.css; only the section wrapper is new.
 *
 * Called via get_template_part( 'template-parts/about/featured-video', null, $args ).
 *
 * @param array $args {
 *     @type string $youtube_embed_id YouTube video ID string. Renders nothing if empty.
 * }
 *
 * @package SkyyRose
 * @since   1.5.27
 */

defined( 'ABSPATH' ) || exit;

$youtube_embed_id = $args['youtube_embed_id'] ?? '';

if ( empty( $youtube_embed_id ) ) {
	return;
}
?>

<!-- Featured Video — The Blox interview -->
<section class="abt-featured-video" aria-label="<?php esc_attr_e( 'Featured video', 'skyyrose' ); ?>">
	<div class="abt-press__video rv rv-clip-up">
		<div class="abt-press__video-meta">
			<span class="abt-press__video-label"><?php esc_html_e( 'Featured Video', 'skyyrose' ); ?></span>
			<span class="abt-press__video-rule" aria-hidden="true"></span>
			<span class="abt-press__video-source"><?php esc_html_e( 'The Blox', 'skyyrose' ); ?></span>
		</div>
		<div class="abt-press__video-frame">
			<iframe
				src="<?php echo esc_url( 'https://www.youtube.com/embed/' . $youtube_embed_id . '?rel=0&modestbranding=1' ); ?>"
				title="<?php esc_attr_e( 'SkyyRose Collection — The Blox Interview', 'skyyrose' ); ?>"
				frameborder="0"
				allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
				allowfullscreen
				loading="lazy">
			</iframe>
		</div>
	</div>
</section>
