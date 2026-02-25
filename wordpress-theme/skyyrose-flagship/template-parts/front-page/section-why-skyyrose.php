<?php
/**
 * Front Page: Why SkyyRose
 *
 * 4 value proposition cards.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$value_props = array(
	array(
		'icon'        => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg>',
		'title'       => __( 'Handcrafted Quality', 'skyyrose-flagship' ),
		'description' => __( 'Every piece tells a story of meticulous craftsmanship. From embroidered details to silicone appliques, each garment is a work of art.', 'skyyrose-flagship' ),
	),
	array(
		'icon'        => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
		'title'       => __( 'Oakland Roots', 'skyyrose-flagship' ),
		'description' => __( 'Born in Oakland, designed for the world. Our streetwear carries the authenticity and grit of the Bay Area in every stitch.', 'skyyrose-flagship' ),
	),
	array(
		'icon'        => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>',
		'title'       => __( 'Limited Editions', 'skyyrose-flagship' ),
		'description' => __( 'Exclusive drops that won\'t last forever. When they\'re gone, they\'re gone. Own a piece of something truly rare.', 'skyyrose-flagship' ),
	),
	array(
		'icon'        => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
		'title'       => __( 'Community First', 'skyyrose-flagship' ),
		'description' => __( 'Building more than a brand, building a movement. The SkyyRose family is a community of dreamers, creators, and believers.', 'skyyrose-flagship' ),
	),
);
?>

<section class="why-skyyrose" aria-labelledby="why-heading">
	<div class="why-skyyrose__header section-header">
		<span class="section-header__label">
			<?php esc_html_e( 'The Difference', 'skyyrose-flagship' ); ?>
		</span>
		<h2 class="section-header__title" id="why-heading">
			<?php esc_html_e( 'Why SkyyRose', 'skyyrose-flagship' ); ?>
		</h2>
		<p class="section-header__subtitle">
			<?php esc_html_e( 'More than a brand. A movement built on authenticity, quality, and community.', 'skyyrose-flagship' ); ?>
		</p>
	</div>

	<div class="why-skyyrose__grid">
		<?php foreach ( $value_props as $index => $prop ) : ?>
			<div class="why-skyyrose__card js-scroll-reveal">
				<div class="why-skyyrose__card-glow" aria-hidden="true"></div>
				<span class="why-skyyrose__card-number" aria-hidden="true">
					<?php echo esc_html( str_pad( $index + 1, 2, '0', STR_PAD_LEFT ) ); ?>
				</span>
				<span class="why-skyyrose__card-icon">
					<?php echo wp_kses_post( $prop['icon'] ); ?>
				</span>
				<h3 class="why-skyyrose__card-title">
					<?php echo esc_html( $prop['title'] ); ?>
				</h3>
				<p class="why-skyyrose__card-text">
					<?php echo esc_html( $prop['description'] ); ?>
				</p>
			</div>
		<?php endforeach; ?>
	</div>
</section>
