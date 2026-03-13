<?php
/**
 * Klaviyo Email Capture — Reusable Partial
 *
 * Renders an email capture form in either popup or inline mode.
 * All submissions route through the skyyrose_klaviyo_subscribe AJAX endpoint.
 *
 * Usage (from any template):
 *   // Inline form:
 *   get_template_part( 'template-parts/klaviyo-capture', null, array(
 *       'mode'        => 'inline',
 *       'list_slug'   => 'black_rose',
 *       'headline'    => 'Join the Black Rose Drop List',
 *       'subheadline' => 'Be first when we drop. No spam, ever.',
 *       'cta'         => 'Get Early Access',
 *   ) );
 *
 *   // Popup (injects a hidden modal — JS controls visibility):
 *   get_template_part( 'template-parts/klaviyo-capture', null, array(
 *       'mode'      => 'popup',
 *       'list_slug' => 'general',
 *       'popup_id'  => 'sr-collection-popup',
 *   ) );
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

// --- Extract template vars (wp_parse_args for safe defaults) ---
$args = wp_parse_args(
	$args ?? array(),
	array(
		'mode'        => 'inline',          // 'inline' | 'popup'
		'list_slug'   => 'general',         // Klaviyo list target
		'popup_id'    => 'sr-klav-popup',   // Unique ID for popup mode
		'headline'    => 'Get Early Access to Drops',
		'subheadline' => 'Join the SkyyRose inner circle — exclusive drops, founder updates, and pre-order discounts.',
		'cta'         => 'Join the List',
		'show_phone'  => false,
		'collection'  => '',                // Optional: collection context class
	)
);

$mode       = in_array( $args['mode'], array( 'inline', 'popup' ), true ) ? $args['mode'] : 'inline';
$list_slug  = sanitize_key( $args['list_slug'] );
$popup_id   = sanitize_html_class( $args['popup_id'] );
$headline   = esc_html( $args['headline'] );
$subhead    = esc_html( $args['subheadline'] );
$cta        = esc_html( $args['cta'] );
$show_phone = (bool) $args['show_phone'];
$collection = sanitize_html_class( $args['collection'] );

// Map list slug to collection color accent.
$accent_map = array(
	'black_rose' => '#C0C0C0',
	'love_hurts' => '#DC143C',
	'signature'  => '#D4AF37',
	'jersey_vip' => '#B76E79',
	'general'    => '#B76E79',
);
$accent = isset( $accent_map[ $list_slug ] ) ? $accent_map[ $list_slug ] : '#B76E79';

$form_id    = 'sr-klav-form-' . $list_slug . '-' . wp_rand( 1000, 9999 );
$nonce_val  = wp_create_nonce( 'skyyrose-nonce' );

if ( 'popup' === $mode ) : ?>
<div id="<?php echo esc_attr( $popup_id ); ?>" class="sr-klav-popup<?php echo $collection ? ' ' . $collection : ''; ?>" role="dialog" aria-modal="true" aria-label="<?php echo $headline; ?>" hidden>
	<div class="sr-klav-popup__backdrop" data-klav-close></div>
	<div class="sr-klav-popup__card" style="--sr-klav-accent: <?php echo esc_attr( $accent ); ?>;">
		<button class="sr-klav-popup__close" type="button" data-klav-close aria-label="<?php esc_attr_e( 'Close', 'skyyrose-flagship' ); ?>">&times;</button>
		<p class="sr-klav-popup__eyebrow"><?php esc_html_e( 'Exclusive Access', 'skyyrose-flagship' ); ?></p>
		<h2 class="sr-klav-popup__headline"><?php echo $headline; ?></h2>
		<p class="sr-klav-popup__sub"><?php echo $subhead; ?></p>
		<?php include __FILE__; // Re-render as inline inside popup — handled below. ?>
	</div>
</div>

<?php else : ?>

<div class="sr-klav-capture<?php echo $collection ? ' sr-klav-capture--' . $collection : ''; ?>"
	style="--sr-klav-accent: <?php echo esc_attr( $accent ); ?>;">

	<form id="<?php echo esc_attr( $form_id ); ?>"
		class="sr-klav-form"
		data-list-slug="<?php echo esc_attr( $list_slug ); ?>"
		novalidate>

		<input type="hidden" name="action" value="skyyrose_klaviyo_subscribe" />
		<input type="hidden" name="nonce" value="<?php echo esc_attr( $nonce_val ); ?>" />
		<input type="hidden" name="list_slug" value="<?php echo esc_attr( $list_slug ); ?>" />

		<div class="sr-klav-form__fields">
			<label for="<?php echo esc_attr( $form_id ); ?>-email" class="sr-sr-only">
				<?php esc_html_e( 'Email address', 'skyyrose-flagship' ); ?>
			</label>
			<input
				type="email"
				id="<?php echo esc_attr( $form_id ); ?>-email"
				name="email"
				class="sr-klav-form__input"
				placeholder="<?php esc_attr_e( 'Your email address', 'skyyrose-flagship' ); ?>"
				required
				autocomplete="email"
			/>

			<?php if ( $show_phone ) : ?>
			<label for="<?php echo esc_attr( $form_id ); ?>-phone" class="sr-sr-only">
				<?php esc_html_e( 'Phone number (optional)', 'skyyrose-flagship' ); ?>
			</label>
			<input
				type="tel"
				id="<?php echo esc_attr( $form_id ); ?>-phone"
				name="phone"
				class="sr-klav-form__input"
				placeholder="<?php esc_attr_e( 'Phone (optional — for SMS drops)', 'skyyrose-flagship' ); ?>"
				autocomplete="tel"
			/>
			<?php endif; ?>

			<button type="submit" class="sr-klav-form__submit">
				<?php echo $cta; ?>
			</button>
		</div>

		<p class="sr-klav-form__legal">
			<?php esc_html_e( 'No spam · Unsubscribe anytime · Privacy protected', 'skyyrose-flagship' ); ?>
		</p>

		<div class="sr-klav-form__status" aria-live="polite" hidden></div>
	</form>
</div>

<?php endif; ?>
<script>
(function () {
	'use strict';
	var form = document.getElementById('<?php echo esc_js( $form_id ); ?>');
	if (!form) return;

	var ajaxUrl = (typeof skyyRoseData !== 'undefined' && skyyRoseData.ajaxUrl)
		? skyyRoseData.ajaxUrl
		: '/wp-admin/admin-ajax.php';

	form.addEventListener('submit', function (e) {
		e.preventDefault();

		var emailInput  = form.querySelector('[name="email"]');
		var submitBtn   = form.querySelector('[type="submit"]');
		var statusEl    = form.querySelector('.sr-klav-form__status');
		var email       = (emailInput ? emailInput.value : '').trim();

		if (!email || email.indexOf('@') < 1) {
			if (emailInput) emailInput.style.borderColor = '#DC143C';
			return;
		}
		if (emailInput) emailInput.style.borderColor = '';

		var origText = submitBtn ? submitBtn.textContent : '';
		if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Joining\u2026'; }

		var data = new FormData(form);

		fetch(ajaxUrl, { method: 'POST', body: data })
			.then(function (r) { return r.json(); })
			.then(function (resp) {
				if (resp && resp.success) {
					if (statusEl) {
						statusEl.textContent = resp.data && resp.data.message
							? resp.data.message
							: 'You\u2019re in!';
						statusEl.removeAttribute('hidden');
						statusEl.className = 'sr-klav-form__status sr-klav-form__status--ok';
					}
					if (submitBtn) submitBtn.textContent = 'Welcome \u2713';
					form.querySelectorAll('input').forEach(function (i) { i.value = ''; });

					// Close parent popup if applicable.
					var popup = form.closest('.sr-klav-popup');
					if (popup) {
						setTimeout(function () {
							popup.setAttribute('hidden', '');
							popup.classList.remove('sr-klav-popup--visible');
						}, 2500);
					}
				} else {
					if (submitBtn) { submitBtn.textContent = origText; submitBtn.disabled = false; }
					if (statusEl) {
						statusEl.textContent = resp.data && resp.data.message
							? resp.data.message
							: 'Please try again.';
						statusEl.removeAttribute('hidden');
						statusEl.className = 'sr-klav-form__status sr-klav-form__status--err';
					}
				}
			})
			.catch(function () {
				if (submitBtn) { submitBtn.textContent = origText; submitBtn.disabled = false; }
			});
	});

	<?php if ( 'popup' === $mode ) : ?>
	// Popup open/close logic.
	var popup = document.getElementById('<?php echo esc_js( $popup_id ); ?>');
	if (popup) {
		popup.querySelectorAll('[data-klav-close]').forEach(function (el) {
			el.addEventListener('click', function () {
				popup.setAttribute('hidden', '');
				popup.classList.remove('sr-klav-popup--visible');
				sessionStorage.setItem('sr_klav_popup_<?php echo esc_js( $list_slug ); ?>', '1');
			});
		});
		document.addEventListener('keydown', function (e) {
			if (e.key === 'Escape' && !popup.hasAttribute('hidden')) {
				popup.setAttribute('hidden', '');
				popup.classList.remove('sr-klav-popup--visible');
			}
		});
	}

	/**
	 * Call window.SkyyRoseKlaviyoCapture.open('<?php echo esc_js( $popup_id ); ?>')
	 * from any JS engine to open this popup programmatically.
	 */
	window.SkyyRoseKlaviyoCapture = window.SkyyRoseKlaviyoCapture || {};
	window.SkyyRoseKlaviyoCapture.open = function (id) {
		var p = document.getElementById(id);
		if (!p) return;
		if (sessionStorage.getItem('sr_klav_popup_<?php echo esc_js( $list_slug ); ?>')) return;
		p.removeAttribute('hidden');
		requestAnimationFrame(function () { p.classList.add('sr-klav-popup--visible'); });
		var firstInput = p.querySelector('input[type="email"]');
		if (firstInput) setTimeout(function () { firstInput.focus(); }, 100);
	};
	<?php endif; ?>
}());
</script>
