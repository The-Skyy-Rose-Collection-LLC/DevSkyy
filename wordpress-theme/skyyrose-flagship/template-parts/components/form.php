<?php
/**
 * Component: Form
 *
 * Renders a <form> wrapper with optional nonce, ARIA live region, and a
 * named slot for caller-provided fields and actions.
 *
 * Usage:
 *   ob_start();
 *   get_template_part( 'template-parts/components/input', null, [ 'id' => 'email', ... ] );
 *   get_template_part( 'template-parts/components/button', null, [ 'label' => 'Subscribe', 'type' => 'submit' ] );
 *   $slot = ob_get_clean();
 *
 *   get_template_part( 'template-parts/components/form', null, [
 *       'id'           => 'newsletter-form',
 *       'action'       => admin_url( 'admin-ajax.php' ),
 *       'method'       => 'post',
 *       'nonce_action' => 'skyyrose_newsletter',   // omit to skip nonce
 *       'ajax'         => true,                    // adds data-ajax="true"
 *       'legend'       => 'Join the list',         // <fieldset> legend; omit = no fieldset wrap
 *       'success_msg'  => "You're on the list.",
 *       'error_msg'    => 'Something went wrong. Try again.',
 *       'extra_classes'=> '',
 *       'attrs'        => [],
 *       'slot'         => $slot,
 *   ] );
 *
 * @package SkyyRose
 */

defined( 'ABSPATH' ) || exit;

$args = wp_parse_args(
	$args ?? array(),
	array(
		'id'            => '',
		'action'        => '',
		'method'        => 'post',
		'nonce_action'  => '',
		'ajax'          => false,
		'legend'        => '',
		'success_msg'   => '',
		'error_msg'     => '',
		'extra_classes' => '',
		'attrs'         => array(),
		'slot'          => '',
	)
);

$form_id      = sanitize_html_class( $args['id'] );
$method       = 'get' === strtolower( $args['method'] ) ? 'get' : 'post';
$use_fieldset = ! empty( $args['legend'] );
$status_id    = $form_id ? $form_id . '-status' : 'sr-form-status';

$form_classes = implode(
	' ',
	array_filter(
		array(
			'sr-form',
			skyyrose_sanitize_class_list( $args['extra_classes'] ?? '' ),
		)
	)
);

// Build extra attributes string.
$attr_string = skyyrose_build_attr_string( $args['attrs'] ?? array() );
?>
<form
	class="<?php echo esc_attr( $form_classes ); ?>"
	<?php echo $form_id ? 'id="' . esc_attr( $form_id ) . '"' : ''; ?>
	method="<?php echo esc_attr( $method ); ?>"
	<?php echo $args['action'] ? 'action="' . esc_url( $args['action'] ) . '"' : ''; ?>
	<?php echo $args['ajax'] ? 'data-ajax="true"' : ''; ?>
	<?php echo $args['ajax'] ? 'aria-live="polite"' : ''; ?>
	novalidate
	data-component="form"
	<?php echo $attr_string; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- pre-escaped above. ?>
>

	<?php if ( $args['nonce_action'] ) : ?>
		<?php wp_nonce_field( sanitize_key( $args['nonce_action'] ), '_skyyrose_nonce' ); ?>
	<?php endif; ?>

	<?php if ( $args['success_msg'] || $args['error_msg'] ) : ?>
		<div
			class="sr-form__status"
			id="<?php echo esc_attr( $status_id ); ?>"
			role="status"
			aria-live="polite"
			aria-atomic="true"
			hidden
		>
			<?php if ( $args['success_msg'] ) : ?>
				<p class="sr-form__status-success" hidden><?php echo esc_html( $args['success_msg'] ); ?></p>
			<?php endif; ?>
			<?php if ( $args['error_msg'] ) : ?>
				<p class="sr-form__status-error" hidden><?php echo esc_html( $args['error_msg'] ); ?></p>
			<?php endif; ?>
		</div>
	<?php endif; ?>

	<?php if ( $use_fieldset ) : ?>
		<fieldset class="sr-form__fieldset">
			<legend class="sr-form__legend"><?php echo esc_html( $args['legend'] ); ?></legend>
			<?php
			/*
			 * CALLER CONTRACT: $args['slot'] must be pre-escaped at the call site.
			 * The slot of a <form> component IS form fields (<input>, <select>,
			 * <textarea>, <button>) — these are explicitly NOT in WordPress's
			 * wp_kses_post allowlist, so wrapping here would silently empty the
			 * form at render time. Callers passing user-derived content into the
			 * slot MUST sanitize at the call site with a form-aware allowlist
			 * (wp_kses with a custom $allowed_html). Phase 4 first-composition
			 * exercises this.
			 */
			echo $args['slot']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- caller contract above
			?>
		</fieldset>
	<?php else : ?>
		<?php
			/*
			 * CALLER CONTRACT: $args['slot'] must be pre-escaped at the call site.
			 * The slot of a <form> component IS form fields (<input>, <select>,
			 * <textarea>, <button>) — these are explicitly NOT in WordPress's
			 * wp_kses_post allowlist, so wrapping here would silently empty the
			 * form at render time. Callers passing user-derived content into the
			 * slot MUST sanitize at the call site with a form-aware allowlist
			 * (wp_kses with a custom $allowed_html). Phase 4 first-composition
			 * exercises this.
			 */
			echo $args['slot']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- caller contract above
		?>
	<?php endif; ?>

</form>
