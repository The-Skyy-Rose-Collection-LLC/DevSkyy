<?php
/**
 * Front Page: Press / As Seen In
 *
 * Media mention logo bar.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$press_logos = array(
	__( 'Complex', 'skyyrose-flagship' ),
	__( 'Hypebeast', 'skyyrose-flagship' ),
	__( 'GQ', 'skyyrose-flagship' ),
	__( 'Vogue', 'skyyrose-flagship' ),
	__( 'Highsnobiety', 'skyyrose-flagship' ),
	__( 'SSENSE', 'skyyrose-flagship' ),
);
?>

<section class="press" aria-label="<?php esc_attr_e( 'As seen in', 'skyyrose-flagship' ); ?>">
	<div class="press__inner">
		<p class="press__label">
			<?php esc_html_e( 'As Seen In', 'skyyrose-flagship' ); ?>
		</p>
		<div class="press__logos">
			<?php foreach ( $press_logos as $logo_name ) : ?>
				<span class="press__logo" aria-label="<?php echo esc_attr( $logo_name ); ?>">
					<?php echo esc_html( $logo_name ); ?>
				</span>
			<?php endforeach; ?>
		</div>
	</div>
</section>
