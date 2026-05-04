<?php
/**
 * Component: Input
 *
 * Usage:
 *   get_template_part( 'template-parts/components/input', null, [
 *       'id'          => 'email',           // required for label association
 *       'name'        => 'email',
 *       'type'        => 'text',            // text | email | password | tel | url | search | number | textarea
 *       'label'       => 'Email address',
 *       'placeholder' => '',
 *       'value'       => '',
 *       'required'    => false,
 *       'disabled'    => false,
 *       'readonly'    => false,
 *       'autocomplete'=> '',
 *       'error'       => '',               // inline error message (WCAG 2.2 §3.3)
 *       'hint'        => '',               // helper text below field
 *       'rows'        => 4,                // textarea only
 *       'maxlength'   => 0,                // 0 = no limit
 *       'pattern'     => '',
 *       'extra_classes'=> '',
 *       'attrs'       => [],
 *   ] );
 *
 * @package SkyyRose
 */

defined( 'ABSPATH' ) || exit;

$args = wp_parse_args(
	$args ?? array(),
	array(
		'id'            => '',
		'name'          => '',
		'type'          => 'text',
		'label'         => '',
		'placeholder'   => '',
		'value'         => '',
		'required'      => false,
		'disabled'      => false,
		'readonly'      => false,
		'autocomplete'  => '',
		'error'         => '',
		'hint'          => '',
		'rows'          => 4,
		'maxlength'     => 0,
		'pattern'       => '',
		'extra_classes' => '',
		'attrs'         => array(),
	)
);

$allowed_types = array( 'text', 'email', 'password', 'tel', 'url', 'search', 'number', 'textarea' );
$type          = in_array( $args['type'], $allowed_types, true ) ? $args['type'] : 'text';
$is_textarea   = 'textarea' === $type;

$field_id   = sanitize_html_class( $args['id'] );
$field_name = esc_attr( $args['name'] ?? $field_id );
$has_error  = ! empty( $args['error'] );
$has_hint   = ! empty( $args['hint'] );
$error_id   = $field_id ? $field_id . '-error' : '';
$hint_id    = $field_id ? $field_id . '-hint' : '';

$field_classes = implode(
	' ',
	array_filter(
		array(
			'sr-input__field',
			$has_error ? 'sr-input__field--error' : '',
			$args['disabled'] ? 'sr-input__field--disabled' : '',
			sanitize_html_class( $args['extra_classes'] ),
		)
	)
);

$described_by = implode( ' ', array_filter( array( $has_error ? $error_id : '', $has_hint ? $hint_id : '' ) ) );

// Build extra attributes string.
$attr_string = skyyrose_build_attr_string( $args['attrs'] ?? array() );
?>
<div class="sr-input<?php echo $has_error ? ' sr-input--has-error' : ''; ?>" data-component="input">

	<?php if ( $args['label'] ) : ?>
		<label
			class="sr-input__label"
			<?php echo $field_id ? 'for="' . esc_attr( $field_id ) . '"' : ''; ?>
		>
			<?php echo esc_html( $args['label'] ); ?>
			<?php if ( $args['required'] ) : ?>
				<span class="sr-input__required" aria-hidden="true">*</span>
			<?php endif; ?>
		</label>
	<?php endif; ?>

	<?php if ( $is_textarea ) : ?>
		<textarea
			class="<?php echo esc_attr( $field_classes ); ?>"
			<?php echo $field_id ? 'id="' . esc_attr( $field_id ) . '"' : ''; ?>
			name="<?php echo esc_attr( $field_name ); ?>"
			rows="<?php echo absint( $args['rows'] ); ?>"
			<?php echo $args['required'] ? 'required' : ''; ?>
			<?php echo $args['disabled'] ? 'disabled' : ''; ?>
			<?php echo $args['readonly'] ? 'readonly' : ''; ?>
			<?php echo $described_by ? 'aria-describedby="' . esc_attr( $described_by ) . '"' : ''; ?>
			<?php echo $has_error ? 'aria-invalid="true"' : ''; ?>
			<?php echo $args['maxlength'] ? 'maxlength="' . absint( $args['maxlength'] ) . '"' : ''; ?>
			<?php echo $args['autocomplete'] ? 'autocomplete="' . esc_attr( $args['autocomplete'] ) . '"' : ''; ?>
			<?php echo $attr_string; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- pre-escaped above. ?>
		><?php echo esc_textarea( $args['value'] ); ?></textarea>
	<?php else : ?>
		<input
			class="<?php echo esc_attr( $field_classes ); ?>"
			type="<?php echo esc_attr( $type ); ?>"
			<?php echo $field_id ? 'id="' . esc_attr( $field_id ) . '"' : ''; ?>
			name="<?php echo esc_attr( $field_name ); ?>"
			value="<?php echo esc_attr( $args['value'] ); ?>"
			placeholder="<?php echo esc_attr( $args['placeholder'] ); ?>"
			<?php echo $args['required'] ? 'required' : ''; ?>
			<?php echo $args['disabled'] ? 'disabled' : ''; ?>
			<?php echo $args['readonly'] ? 'readonly' : ''; ?>
			<?php echo $described_by ? 'aria-describedby="' . esc_attr( $described_by ) . '"' : ''; ?>
			<?php echo $has_error ? 'aria-invalid="true"' : ''; ?>
			<?php echo $args['maxlength'] ? 'maxlength="' . absint( $args['maxlength'] ) . '"' : ''; ?>
			<?php echo $args['pattern'] ? 'pattern="' . esc_attr( $args['pattern'] ) . '"' : ''; ?>
			<?php echo $args['autocomplete'] ? 'autocomplete="' . esc_attr( $args['autocomplete'] ) . '"' : ''; ?>
			<?php echo $attr_string; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- pre-escaped above. ?>
		/>
	<?php endif; ?>

	<?php if ( $has_error ) : ?>
		<span
			class="sr-input__error"
			id="<?php echo esc_attr( $error_id ); ?>"
			role="alert"
		><?php echo esc_html( $args['error'] ); ?></span>
	<?php endif; ?>

	<?php if ( $has_hint ) : ?>
		<span
			class="sr-input__hint"
			id="<?php echo esc_attr( $hint_id ); ?>"
		><?php echo esc_html( $args['hint'] ); ?></span>
	<?php endif; ?>

</div>
