<?php
/**
 * Collection Feature Scroll — sticky image + scrolling feature items.
 *
 * Desktop: left column holds a sticky media frame whose image cross-fades
 * as the right column's feature items scroll past (GSAP ScrollTrigger,
 * IntersectionObserver fallback). Mobile: stacked — each feature renders
 * its own image above its text, no sticky.
 *
 * Renders the per-collection `features` array from
 * skyyrose_get_collection_content() (features_heading / features_subheading
 * / features[].{icon,title,text,image,image_alt,image_w,image_h}).
 *
 * @package SkyyRose
 * @since   1.10.3
 *
 * @param array $args {
 *     @type string $slug    Collection slug.
 *     @type array  $content Collection content config.
 * }
 */

defined( 'ABSPATH' ) || exit;

$slug = isset( $args['slug'] ) ? sanitize_key( $args['slug'] ) : '';
$c    = isset( $args['content'] ) && is_array( $args['content'] ) ? $args['content'] : array();

$features = isset( $c['features'] ) && is_array( $c['features'] ) ? $c['features'] : array();

// Keep only features whose image asset exists on disk — path built ONCE
// (bug-221: file gate and URL must derive from the same string).
$render_features = array();
foreach ( $features as $feature ) {
	$rel = isset( $feature['image'] ) ? $feature['image'] : '';
	if ( '' === $rel || ! file_exists( get_theme_file_path( 'assets' . $rel ) ) ) {
		continue;
	}
	$feature['image_url'] = SKYYROSE_ASSETS_URI . $rel . '?v=' . SKYYROSE_VERSION;
	$render_features[]    = $feature;
}

if ( count( $render_features ) < 2 ) {
	return;
}

$heading    = isset( $c['features_heading'] ) ? $c['features_heading'] : '';
$subheading = isset( $c['features_subheading'] ) ? $c['features_subheading'] : '';
?>

<section class="col-featscroll" data-featscroll aria-label="<?php echo esc_attr( $heading ); ?>">
	<header class="col-featscroll__header rv-clip-up">
		<?php if ( $heading ) : ?>
			<h2 class="col-featscroll__heading"><?php echo esc_html( $heading ); ?></h2>
		<?php endif; ?>
		<?php if ( $subheading ) : ?>
			<p class="col-featscroll__subheading"><?php echo esc_html( $subheading ); ?></p>
		<?php endif; ?>
	</header>

	<div class="col-featscroll__layout">
		<!-- Sticky media column (desktop only; decorative duplicate of the
			per-item mobile figures, so it stays out of the a11y tree). -->
		<div class="col-featscroll__media" aria-hidden="true">
			<div class="col-featscroll__frame">
				<?php foreach ( $render_features as $i => $feature ) : ?>
					<img
						src="<?php echo esc_url( $feature['image_url'] ); ?>"
						alt=""
						width="<?php echo esc_attr( $feature['image_w'] ); ?>"
						height="<?php echo esc_attr( $feature['image_h'] ); ?>"
						loading="lazy" decoding="async"
						class="col-featscroll__img<?php echo 0 === $i ? ' is-active' : ''; ?>"
						data-feat-img="<?php echo esc_attr( $i ); ?>">
				<?php endforeach; ?>
			</div>
		</div>

		<ol class="col-featscroll__items">
			<?php foreach ( $render_features as $i => $feature ) : ?>
				<li class="col-featscroll__item<?php echo 0 === $i ? ' is-active' : ''; ?>" data-feat-item="<?php echo esc_attr( $i ); ?>">
					<figure class="col-featscroll__item-figure">
						<img
							src="<?php echo esc_url( $feature['image_url'] ); ?>"
							alt="<?php echo esc_attr( isset( $feature['image_alt'] ) ? $feature['image_alt'] : '' ); ?>"
							width="<?php echo esc_attr( $feature['image_w'] ); ?>"
							height="<?php echo esc_attr( $feature['image_h'] ); ?>"
							loading="lazy" decoding="async"
							class="col-featscroll__item-img">
					</figure>
					<?php if ( ! empty( $feature['icon'] ) ) : ?>
						<span class="col-featscroll__icon" aria-hidden="true"><?php echo wp_kses( $feature['icon'], array() ); ?></span>
					<?php endif; ?>
					<h3 class="col-featscroll__title"><?php echo esc_html( $feature['title'] ); ?></h3>
					<p class="col-featscroll__text"><?php echo esc_html( $feature['text'] ); ?></p>
				</li>
			<?php endforeach; ?>
		</ol>
	</div>
</section>
