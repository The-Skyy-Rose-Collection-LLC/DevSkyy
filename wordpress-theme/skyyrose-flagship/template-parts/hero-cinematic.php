<?php
/**
 * Template Part: Cinematic Hero
 *
 * Full-bleed image/video hero with a collection lockup, supporting copy, and CTA.
 * Brand-adapted port of the 21st.dev "prisma-hero" pattern.
 *
 * Image-first: the still is the LCP element ( <img fetchpriority="high"> ); the
 * video is progressive enhancement layered above it with the still as poster, so
 * blocked autoplay, slow networks, and reduced-motion all fall back to the still.
 *
 * Brand rule: the hero title is the collection LOCKUP IMAGE, never type-rendered.
 * Only Black Rose / Love Hurts / Signature have real name lockups; Kids/unknown
 * fall back to the SR monogram — never another collection's wordmark.
 *
 * Accepts $args:
 *   collection (string) 'black-rose'|'love-hurts'|'signature'|'kids-capsule' — palette + default lockup.
 *   image      (string) URL of the still background (LCP). Required unless video or video_webm is supplied.
 *   image_webp (string) Optional webp source for the still.
 *   video      (string) Optional self-hosted mp4 URL (progressive enhancement, universal fallback).
 *   video_webm (string) Optional self-hosted webm/VP9 URL (served first; smaller than mp4 on Chrome/Firefox).
 *   lockup     (string) Optional full URL override for the title lockup image.
 *   lockup_alt (string) Accessible name for the lockup (the collection name).
 *   eyebrow    (string) Optional small uppercase label above the body copy.
 *   body       (string) Supporting paragraph (allows inline markup via wp_kses_post).
 *   cta_label  (string) CTA button text.
 *   cta_url    (string) CTA destination URL.
 *
 * @package SkyyRose
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$skyyrose_hero = wp_parse_args(
	isset( $args ) && is_array( $args ) ? $args : array(),
	array(
		'collection' => 'signature',
		'image'      => '',
		'image_webp' => '',
		'video'      => '',
		'video_webm' => '',
		'lockup'     => '',
		'lockup_alt' => '',
		'eyebrow'    => '',
		'body'       => '',
		'cta_label'  => '',
		'cta_url'    => '',
	)
);

$skyyrose_hero_collection = sanitize_title( $skyyrose_hero['collection'] );

// Per-collection default lockups. Base path is relative to the theme images dir.
$skyyrose_hero_lockups = array(
	'black-rose'   => array(
		'base' => 'hero-overlays/br-brand-script-logotype',
		'alt'  => __( 'Black Rose', 'skyyrose' ),
	),
	'love-hurts'   => array(
		'base' => 'hero-overlays/lh-logo-combined',
		'alt'  => __( 'Love Hurts', 'skyyrose' ),
	),
	'signature'    => array(
		'base' => 'hero-overlays/sig-brand-skyy-rose-gold',
		'alt'  => __( 'Signature', 'skyyrose' ),
	),
	'kids-capsule' => array(
		'base' => 'logos/sr-monogram-rose-gold',
		'alt'  => __( 'SkyyRose Kids', 'skyyrose' ),
	),
);

$skyyrose_hero_default = isset( $skyyrose_hero_lockups[ $skyyrose_hero_collection ] )
	? $skyyrose_hero_lockups[ $skyyrose_hero_collection ]
	: $skyyrose_hero_lockups['signature'];

// Resolve lockup sources (raw URLs; escaped at output). Explicit override wins.
if ( '' !== $skyyrose_hero['lockup'] ) {
	$skyyrose_hero_lockup_webp = $skyyrose_hero['lockup'];
	$skyyrose_hero_lockup_png  = $skyyrose_hero['lockup'];
} else {
	$skyyrose_hero_lockup_uri  = SKYYROSE_ASSETS_URI . '/images/' . $skyyrose_hero_default['base'];
	$skyyrose_hero_lockup_webp = $skyyrose_hero_lockup_uri . '.webp';
	$skyyrose_hero_lockup_png  = $skyyrose_hero_lockup_uri . '.png';
}

$skyyrose_hero_lockup_alt = '' !== $skyyrose_hero['lockup_alt']
	? $skyyrose_hero['lockup_alt']
	: $skyyrose_hero_default['alt'];

// A hero with neither still nor video is non-functional — render nothing.
if ( '' === $skyyrose_hero['image'] && '' === $skyyrose_hero['video'] && '' === $skyyrose_hero['video_webm'] ) {
	if ( defined( 'WP_DEBUG' ) && WP_DEBUG ) {
		echo '<!-- skyyrose hero-cinematic: no image/video supplied; nothing rendered -->';
	}
	return;
}
?>
<section class="cine-hero" data-collection="<?php echo esc_attr( $skyyrose_hero_collection ); ?>" aria-label="<?php echo esc_attr( sprintf( /* translators: %s: collection name */ __( '%s collection hero', 'skyyrose' ), $skyyrose_hero_lockup_alt ) ); ?>">
	<div class="cine-hero__frame">

		<?php if ( '' !== $skyyrose_hero['image'] ) : ?>
			<picture class="cine-hero__media">
				<?php if ( '' !== $skyyrose_hero['image_webp'] ) : ?>
					<source srcset="<?php echo esc_url( $skyyrose_hero['image_webp'] ); ?>" type="image/webp">
				<?php endif; ?>
				<img
					class="cine-hero__img"
					src="<?php echo esc_url( $skyyrose_hero['image'] ); ?>"
					alt=""
					fetchpriority="high"
					decoding="async"
					aria-hidden="true"
				>
			</picture>
		<?php endif; ?>

		<?php if ( '' !== $skyyrose_hero['video'] || '' !== $skyyrose_hero['video_webm'] ) : ?>
			<video
				class="cine-hero__video"
				autoplay
				loop
				muted
				playsinline
				preload="none"
				<?php if ( '' !== $skyyrose_hero['image'] ) : ?>
					poster="<?php echo esc_url( $skyyrose_hero['image'] ); ?>"
				<?php endif; ?>
				aria-hidden="true"
			>
				<?php if ( '' !== $skyyrose_hero['video_webm'] ) : ?>
					<source src="<?php echo esc_url( $skyyrose_hero['video_webm'] ); ?>" type="video/webm">
				<?php endif; ?>
				<?php if ( '' !== $skyyrose_hero['video'] ) : ?>
					<source src="<?php echo esc_url( $skyyrose_hero['video'] ); ?>" type="video/mp4">
				<?php endif; ?>
			</video>
		<?php endif; ?>

		<span class="cine-hero__scrim" aria-hidden="true"></span>

		<div class="cine-hero__content">

			<div class="cine-hero__lockup-wrap rv-blur">
				<picture>
					<source srcset="<?php echo esc_url( $skyyrose_hero_lockup_webp ); ?>" type="image/webp">
					<img
						class="cine-hero__lockup"
						src="<?php echo esc_url( $skyyrose_hero_lockup_png ); ?>"
						alt="<?php echo esc_attr( $skyyrose_hero_lockup_alt ); ?>"
						decoding="async"
						loading="eager"
					>
				</picture>
			</div>

			<div class="cine-hero__aside">
				<?php if ( '' !== $skyyrose_hero['eyebrow'] ) : ?>
					<p class="cine-hero__eyebrow rv-clip-up"><?php echo esc_html( $skyyrose_hero['eyebrow'] ); ?></p>
				<?php endif; ?>

				<?php if ( '' !== $skyyrose_hero['body'] ) : ?>
					<p class="cine-hero__body rv-clip-up"><?php echo wp_kses_post( $skyyrose_hero['body'] ); ?></p>
				<?php endif; ?>

				<?php if ( '' !== $skyyrose_hero['cta_label'] && '' !== $skyyrose_hero['cta_url'] ) : ?>
					<a class="cine-hero__cta magnetic rv-clip-up" href="<?php echo esc_url( $skyyrose_hero['cta_url'] ); ?>">
						<span class="cine-hero__cta-label"><?php echo esc_html( $skyyrose_hero['cta_label'] ); ?></span>
						<span class="cine-hero__cta-icon" aria-hidden="true">
							<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" focusable="false"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
						</span>
					</a>
				<?php endif; ?>
			</div>

		</div>
	</div>
</section>
