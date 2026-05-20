<?php
/**
 * Contact Page — Form Section
 *
 * Renders the AJAX contact form with honeypot, validation,
 * subject/referral dropdowns, preferred contact method, and spinner.
 *
 * Expected variables (passed via $args from get_template_part):
 *   $args['subject_options']  — associative array of subject <option> values.
 *   $args['referral_options'] — associative array of referral <option> values.
 *
 * @package SkyyRose
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$subject_options  = isset( $args['subject_options'] ) ? $args['subject_options'] : array();
$referral_options = isset( $args['referral_options'] ) ? $args['referral_options'] : array();
?>

<div class="contact-form-wrapper">
	<h2 class="contact-form__heading">
		<?php esc_html_e( 'Send Us a Message', 'skyyrose' ); ?>
	</h2>

	<form
		id="skyyrose-contact-form"
		class="contact-form"
		method="post"
		action="<?php echo esc_url( admin_url( 'admin-ajax.php' ) ); ?>"
		novalidate
	>
		<?php wp_nonce_field( 'skyyrose_contact_form', 'skyyrose_contact_nonce' ); ?>
		<input type="hidden" name="action" value="skyyrose_contact_submit">

		<!-- Honeypot field for bot detection — display:none removes from both visual and accessibility trees -->
		<div class="contact-form__hp" style="display:none;" aria-hidden="true">
			<label for="contact-website" aria-hidden="true">
				<?php esc_html_e( 'Website', 'skyyrose' ); ?>
			</label>
			<input
				type="text"
				id="contact-website"
				name="website"
				aria-hidden="true"
				tabindex="-1"
				autocomplete="off"
			>
		</div>

		<div class="contact-form__row">
			<div class="contact-form__group">
				<label for="contact-first-name" class="contact-form__label">
					<?php esc_html_e( 'First Name', 'skyyrose' ); ?>
				</label>
				<input
					type="text"
					id="contact-first-name"
					name="first_name"
					class="contact-form__input"
					required
					autocomplete="given-name"
					aria-required="true"
					aria-describedby="contact-first-name-error"
					placeholder="<?php esc_attr_e( 'Your first name', 'skyyrose' ); ?>"
				>
				<span id="contact-first-name-error" class="contact-form__error" role="alert" aria-live="polite"></span>
			</div>
			<div class="contact-form__group">
				<label for="contact-last-name" class="contact-form__label">
					<?php esc_html_e( 'Last Name', 'skyyrose' ); ?>
				</label>
				<input
					type="text"
					id="contact-last-name"
					name="last_name"
					class="contact-form__input"
					required
					autocomplete="family-name"
					aria-required="true"
					aria-describedby="contact-last-name-error"
					placeholder="<?php esc_attr_e( 'Your last name', 'skyyrose' ); ?>"
				>
				<span id="contact-last-name-error" class="contact-form__error" role="alert" aria-live="polite"></span>
			</div>
		</div>

		<div class="contact-form__row">
			<div class="contact-form__group">
				<label for="contact-email" class="contact-form__label">
					<?php esc_html_e( 'Email Address', 'skyyrose' ); ?>
				</label>
				<input
					type="email"
					id="contact-email"
					name="email"
					class="contact-form__input"
					required
					autocomplete="email"
					aria-required="true"
					aria-describedby="contact-email-error"
					placeholder="<?php esc_attr_e( 'you@example.com', 'skyyrose' ); ?>"
				>
				<span id="contact-email-error" class="contact-form__error" role="alert" aria-live="polite"></span>
			</div>
			<div class="contact-form__group">
				<label for="contact-phone" class="contact-form__label">
					<?php esc_html_e( 'Phone (Optional)', 'skyyrose' ); ?>
				</label>
				<input
					type="tel"
					id="contact-phone"
					name="phone"
					class="contact-form__input"
					autocomplete="tel"
					aria-describedby="contact-phone-error"
					placeholder="<?php esc_attr_e( '(555) 123-4567', 'skyyrose' ); ?>"
				>
				<span id="contact-phone-error" class="contact-form__error" role="alert" aria-live="polite"></span>
			</div>
		</div>

		<div class="contact-form__row">
			<div class="contact-form__group">
				<label for="contact-subject" class="contact-form__label">
					<?php esc_html_e( 'Subject', 'skyyrose' ); ?>
				</label>
				<select
					id="contact-subject"
					name="subject"
					class="contact-form__select"
					required
					aria-required="true"
					aria-describedby="contact-subject-error"
				>
					<?php $is_first_opt = true; ?>
					<?php foreach ( $subject_options as $value => $label ) : ?>
						<option value="<?php echo esc_attr( $value ); ?>"
						<?php
						if ( $is_first_opt && '' === $value ) {
							echo ' disabled selected';
							$is_first_opt = false; }
						?>
						>
							<?php echo esc_html( $label ); ?>
						</option>
					<?php endforeach; ?>
				</select>
				<span id="contact-subject-error" class="contact-form__error" role="alert" aria-live="polite"></span>
			</div>
			<div class="contact-form__group contact-form__group--order-number" id="order-number-group">
				<label for="contact-order-number" class="contact-form__label">
					<?php esc_html_e( 'Order Number (Optional)', 'skyyrose' ); ?>
				</label>
				<input
					type="text"
					id="contact-order-number"
					name="order_number"
					class="contact-form__input"
					placeholder="<?php esc_attr_e( 'e.g. SR-2025-123456', 'skyyrose' ); ?>"
					aria-describedby="contact-order-number-error"
				>
				<span id="contact-order-number-error" class="contact-form__error" role="alert" aria-live="polite"></span>
			</div>
		</div>

		<!-- Preferred Contact Method -->
		<div class="contact-form__group">
			<fieldset class="contact-form__fieldset">
				<legend class="contact-form__label">
					<?php esc_html_e( 'Preferred Contact Method', 'skyyrose' ); ?>
				</legend>
				<div class="contact-form__radio-group">
					<label class="contact-form__radio-label">
						<input
							type="radio"
							name="preferred_contact"
							value="email"
							class="contact-form__radio"
							checked
						>
						<span class="contact-form__radio-indicator" aria-hidden="true"></span>
						<span class="contact-form__radio-text">
							<?php esc_html_e( 'Email', 'skyyrose' ); ?>
						</span>
					</label>
					<label class="contact-form__radio-label">
						<input
							type="radio"
							name="preferred_contact"
							value="phone"
							class="contact-form__radio"
						>
						<span class="contact-form__radio-indicator" aria-hidden="true"></span>
						<span class="contact-form__radio-text">
							<?php esc_html_e( 'Phone', 'skyyrose' ); ?>
						</span>
					</label>
					<label class="contact-form__radio-label">
						<input
							type="radio"
							name="preferred_contact"
							value="either"
							class="contact-form__radio"
						>
						<span class="contact-form__radio-indicator" aria-hidden="true"></span>
						<span class="contact-form__radio-text">
							<?php esc_html_e( 'Either', 'skyyrose' ); ?>
						</span>
					</label>
				</div>
			</fieldset>
		</div>

		<div class="contact-form__group">
			<label for="contact-message" class="contact-form__label">
				<?php esc_html_e( 'Your Message', 'skyyrose' ); ?>
			</label>
			<textarea
				id="contact-message"
				name="message"
				class="contact-form__textarea"
				required
				aria-required="true"
				aria-describedby="contact-message-error"
				placeholder="<?php esc_attr_e( "Tell us what's on your mind. We're all ears...", 'skyyrose' ); ?>"
			></textarea>
			<span id="contact-message-error" class="contact-form__error" role="alert" aria-live="polite"></span>
		</div>

		<div class="contact-form__group">
			<label for="contact-referral" class="contact-form__label">
				<?php esc_html_e( 'What brought you to SkyyRose?', 'skyyrose' ); ?>
			</label>
			<select
				id="contact-referral"
				name="referral_source"
				class="contact-form__select"
			>
				<?php $is_first_ref = true; ?>
				<?php foreach ( $referral_options as $value => $label ) : ?>
					<option value="<?php echo esc_attr( $value ); ?>"
					<?php
					if ( $is_first_ref && '' === $value ) {
						echo ' disabled selected';
						$is_first_ref = false; }
					?>
					>
						<?php echo esc_html( $label ); ?>
					</option>
				<?php endforeach; ?>
			</select>
		</div>

		<button type="submit" class="contact-form__submit" id="contact-submit-btn">
			<span class="contact-form__submit-text">
				<?php esc_html_e( 'Send Message', 'skyyrose' ); ?>
			</span>
			<span class="contact-form__submit-loading" aria-hidden="true">
				<svg class="contact-form__spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M21 12a9 9 0 1 1-6.219-8.56"/>
				</svg>
				<?php esc_html_e( 'Sending...', 'skyyrose' ); ?>
			</span>
		</button>
	</form>
</div>
