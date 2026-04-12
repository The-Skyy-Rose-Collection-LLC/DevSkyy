<?php
/**
 * Immersive Tab Bar — Cross-Collection Navigation
 *
 * Fixed bottom tab bar for navigating between immersive experiences.
 * Shows all 4 collection worlds with active state detection.
 *
 * @package SkyyRose_Flagship
 * @since   6.0.0
 *
 * @param array $args {
 *     @type string $active_slug Current collection slug for active state.
 * }
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$active = isset( $args['active_slug'] ) ? $args['active_slug'] : '';

$tabs = array(
	array(
		'slug'  => 'signature',
		'label' => __( 'Signature', 'skyyrose' ),
		'url'   => home_url( '/experience-signature/' ),
		'icon'  => 'M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z',
	),
	array(
		'slug'  => 'black-rose',
		'label' => __( 'Black Rose', 'skyyrose' ),
		'url'   => home_url( '/experience-black-rose/' ),
		'icon'  => 'M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z',
	),
	array(
		'slug'  => 'love-hurts',
		'label' => __( 'Love Hurts', 'skyyrose' ),
		'url'   => home_url( '/experience-love-hurts/' ),
		'icon'  => 'M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z',
	),
	array(
		'slug'  => 'kids-capsule',
		'label' => __( 'Kids Capsule', 'skyyrose' ),
		'url'   => home_url( '/experience-kids-capsule/' ),
		'icon'  => 'M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8zm-2-9h4v4h-4zm0-6h4v4h-4z',
	),
);
?>

<nav class="immersive-tab-bar" aria-label="<?php esc_attr_e( 'Explore other collections', 'skyyrose' ); ?>">
	<?php
	foreach ( $tabs as $tab ) :
		$is_active = ( $tab['slug'] === $active );
		?>
		<a href="<?php echo esc_url( $tab['url'] ); ?>"
			class="immersive-tab<?php echo $is_active ? ' immersive-tab--active' : ''; ?>"
			<?php echo $is_active ? 'aria-current="page"' : ''; ?>>
			<svg class="immersive-tab__icon" width="18" height="18" viewBox="0 0 24 24" fill="<?php echo $is_active ? 'currentColor' : 'none'; ?>" stroke="currentColor" stroke-width="1.5" aria-hidden="true" focusable="false">
				<path d="<?php echo esc_attr( $tab['icon'] ); ?>"/>
			</svg>
			<span class="immersive-tab__label"><?php echo esc_html( $tab['label'] ); ?></span>
		</a>
	<?php endforeach; ?>
</nav>
