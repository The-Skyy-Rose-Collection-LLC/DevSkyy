<?php
/**
 * Homepage Act VI — the origin.
 *
 * Full-bleed testimony: the founder speaks first and the page is his voice.
 * The film is a LAYER, not an object — edge to edge, unframed, scrimmed, with
 * the quote sitting on top of it. Every prose paragraph is dropped; the quote
 * IS the section, and the affordance is a transport control over the film.
 *
 * Copy is verbatim from the founder-locked quote already on this site. The
 * film never autoplays on load: homepage-v3.js starts it only while this
 * section is on screen (and stops it when it leaves), so it can never contend
 * with the hero clip or the LCP paint.
 *
 * @package SkyyRose
 * @since   1.13.0
 */

defined( 'ABSPATH' ) || exit;

$hp_assets = SKYYROSE_ASSETS_URI;
?>
<section class="hp-origin" id="story" aria-labelledby="hp-origin-q">

	<div class="hp-origin__layer" aria-hidden="true">
		<video poster="<?php echo esc_url( $hp_assets . '/images/hero/home-hero-poster-480w.webp' ); ?>"
			muted
			playsinline
			loop
			preload="none"
			width="720"
			height="1280">
			<source src="<?php echo esc_url( $hp_assets . '/video/home-hero.webm' ); ?>" type="video/webm">
			<source src="<?php echo esc_url( $hp_assets . '/video/home-hero.mp4' ); ?>" type="video/mp4">
		</video>
	</div>
	<div class="hp-origin__scrim" aria-hidden="true"></div>

	<div class="hp-origin__inner">
		<p class="hp-origin__mark" data-reveal><?php esc_html_e( 'Oakland · Est. 2020', 'skyyrose' ); ?></p>

		<blockquote class="hp-origin__quote" id="hp-origin-q">
			<span class="hp-origin__phrase" data-reveal style="--rv-delay:0ms">
				<?php esc_html_e( '“If you asked me four years ago, I never would have thought I’d be here.', 'skyyrose' ); ?>
			</span>
			<span class="hp-origin__phrase" data-reveal style="--rv-delay:200ms">
				<?php esc_html_e( 'I had no drive, lost it all, a baby on the way, and was broke.', 'skyyrose' ); ?>
			</span>
			<span class="hp-origin__phrase" data-reveal style="--rv-delay:400ms">
				<?php
				echo wp_kses(
					__( 'But we knew we had to get it <em>by any means necessary</em>.”', 'skyyrose' ),
					array( 'em' => array() )
				);
				?>
			</span>
		</blockquote>

		<p class="hp-origin__attr" data-reveal style="--rv-delay:640ms">
			<?php echo esc_html( '— ' . __( 'Corey Foster, Founder & CEO', 'skyyrose' ) ); ?>
		</p>
		<p class="hp-origin__line" data-reveal style="--rv-delay:720ms">
			<?php esc_html_e( 'Built by a father, named after a daughter.', 'skyyrose' ); ?>
		</p>

		<button type="button"
			class="hp-origin__ctrl"
			data-origin-play
			data-reveal
			style="--rv-delay:800ms"
			aria-pressed="false"
			data-label-play="<?php esc_attr_e( 'Play the film', 'skyyrose' ); ?>"
			data-label-pause="<?php esc_attr_e( 'Pause the film', 'skyyrose' ); ?>">
			<svg data-origin-icon="play" width="13" height="15" viewBox="0 0 13 15" fill="currentColor" aria-hidden="true"><path d="M0 0l13 7.5L0 15z"/></svg>
			<svg data-origin-icon="pause" width="13" height="15" viewBox="0 0 13 15" fill="currentColor" aria-hidden="true" hidden><path d="M0 0h4.5v15H0zM8.5 0H13v15H8.5z"/></svg>
			<span data-origin-label><?php esc_html_e( 'Play the film', 'skyyrose' ); ?></span>
		</button>

		<p class="hp-origin__line" data-reveal style="--rv-delay:860ms">
			<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>"><?php esc_html_e( 'Read the full story →', 'skyyrose' ); ?></a>
		</p>
	</div>
</section>
