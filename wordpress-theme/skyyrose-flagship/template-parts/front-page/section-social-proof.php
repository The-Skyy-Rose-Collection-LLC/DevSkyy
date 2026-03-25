<?php
/**
 * Front Page: Social Proof Bar
 *
 * Animated stat counters for Instagram followers, customers, products, collections.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$social_stats = array(
	array(
		'value' => 25000,
		'label' => __( 'Instagram Followers', 'skyyrose-flagship' ),
		'suffix' => '+',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>',
	),
	array(
		'value' => 2500,
		'label' => __( 'Satisfied Customers', 'skyyrose-flagship' ),
		'suffix' => '+',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
	),
	array(
		'value' => 150,
		'label' => __( 'Products Crafted', 'skyyrose-flagship' ),
		'suffix' => '+',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>',
	),
	array(
		'value' => 3,
		'label' => __( 'Unique Collections', 'skyyrose-flagship' ),
		'suffix' => '',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
	),
);
?>

<section class="social-proof" aria-label="<?php esc_attr_e( 'Social proof', 'skyyrose-flagship' ); ?>">
	<div class="social-proof__inner">
		<?php foreach ( $social_stats as $stat ) : ?>
			<div class="social-proof__stat js-scroll-reveal">
				<span class="social-proof__icon" aria-hidden="true">
					<?php echo wp_kses_post( $stat['icon'] ); ?>
				</span>
				<span
					class="social-proof__number js-counter"
					data-target="<?php echo esc_attr( $stat['value'] ); ?>"
					data-suffix="<?php echo esc_attr( $stat['suffix'] ); ?>"
					aria-label="<?php echo esc_attr( number_format( $stat['value'] ) . $stat['suffix'] ); ?>"
				>
					<?php echo esc_html( '0' . $stat['suffix'] ); ?>
				</span>
				<span class="social-proof__label">
					<?php echo esc_html( $stat['label'] ); ?>
				</span>
			</div>
		<?php endforeach; ?>
	</div>
</section>
