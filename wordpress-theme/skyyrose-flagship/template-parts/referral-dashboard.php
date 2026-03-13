<?php
/**
 * Referral Dashboard — Post-Purchase Panel
 *
 * Shown on the WooCommerce order-received page. Generates a unique
 * referral link for the customer and displays their referral stats.
 * Referrer earns $10 store credit; referred friend gets 10% off.
 *
 * Hooked into: woocommerce_thankyou (priority 20) via inc/woocommerce.php
 * or include directly: get_template_part( 'template-parts/referral-dashboard' )
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

if ( ! defined( 'ABSPATH' ) ) { exit; }

// Only show for logged-in users or when order email is available.
$user_id    = get_current_user_id();
$order_id   = absint( $args['order_id'] ?? 0 );
$order      = $order_id ? wc_get_order( $order_id ) : null;
$user_email = '';

if ( $order ) {
	$user_email = $order->get_billing_email();
}
if ( ! $user_email && $user_id ) {
	$user_email = get_userdata( $user_id )->user_email ?? '';
}
if ( ! $user_email ) { return; }

// Retrieve or generate referral code for this customer.
$referral_code = $user_id ? get_user_meta( $user_id, '_skyyrose_referral_code', true ) : '';

// For guest orders, use a session-safe hash of the email.
if ( ! $referral_code ) {
	if ( $user_id ) {
		$referral_code = 'SKYY' . strtoupper( substr( base_convert( md5( $user_email . $user_id ), 16, 36 ), 0, 6 ) );
		update_user_meta( $user_id, '_skyyrose_referral_code', $referral_code );
	} else {
		$referral_code = 'SKYY' . strtoupper( substr( base_convert( md5( $user_email . wp_salt() ), 16, 36 ), 0, 6 ) );
	}
}

// Ensure the WooCommerce coupon exists for this code.
if ( class_exists( 'WC_Coupon' ) ) {
	$coupon = new WC_Coupon( $referral_code );
	if ( ! $coupon->get_id() ) {
		$coupon_post = array(
			'post_title'  => $referral_code,
			'post_name'   => strtolower( $referral_code ),
			'post_status' => 'publish',
			'post_type'   => 'shop_coupon',
			'post_author' => 1,
		);
		$coupon_id = wp_insert_post( $coupon_post );
		if ( $coupon_id && ! is_wp_error( $coupon_id ) ) {
			update_post_meta( $coupon_id, 'discount_type', 'percent' );
			update_post_meta( $coupon_id, 'coupon_amount', '10' );
			update_post_meta( $coupon_id, 'individual_use', 'yes' );
			update_post_meta( $coupon_id, 'usage_limit', '' );  // unlimited new-customer uses
			update_post_meta( $coupon_id, 'usage_limit_per_user', '1' );
			update_post_meta( $coupon_id, '_skyyrose_referral_owner_email', sanitize_email( $user_email ) );
		}
	}
}

// Referral stats.
$referral_count = $user_id ? (int) get_user_meta( $user_id, '_skyyrose_referral_count', true ) : 0;
$total_earned   = $user_id ? (float) get_user_meta( $user_id, '_skyyrose_referral_earned', true ) : 0;
$is_founding    = $referral_count >= 0 && $user_id && (int) get_user_meta( $user_id, '_skyyrose_founding_ambassador', true ) === 1;

$shareable_url  = add_query_arg( 'ref', $referral_code, home_url( '/' ) );
$share_text     = rawurlencode( 'I just pre-ordered from @SkyyRose — use my link for 10% off: ' );
$twitter_share  = 'https://twitter.com/intent/tweet?text=' . $share_text . '&url=' . rawurlencode( $shareable_url );
$ig_caption     = 'Luxury Grows from Concrete. Get 10% off SkyyRose with code ' . $referral_code;
?>
<section class="sr-referral-dashboard" aria-label="<?php esc_attr_e( 'Referral Program', 'skyyrose-flagship' ); ?>">
	<div class="sr-referral-dashboard__inner">
		<div class="sr-referral-dashboard__header">
			<h2 class="sr-referral-dashboard__title">
				<?php esc_html_e( 'Share & Earn', 'skyyrose-flagship' ); ?>
				<?php if ( $is_founding ) : ?>
				<span class="sr-referral-dashboard__badge sr-referral-dashboard__badge--founding">
					<?php esc_html_e( 'Founding Ambassador', 'skyyrose-flagship' ); ?>
				</span>
				<?php endif; ?>
			</h2>
			<p class="sr-referral-dashboard__sub">
				<?php esc_html_e( 'Give friends 10% off their first order. Earn $10 store credit for every successful referral.', 'skyyrose-flagship' ); ?>
			</p>
		</div>

		<div class="sr-referral-dashboard__link-wrap">
			<span class="sr-referral-dashboard__label"><?php esc_html_e( 'Your referral link', 'skyyrose-flagship' ); ?></span>
			<div class="sr-referral-dashboard__link-row">
				<input
					type="text"
					class="sr-referral-dashboard__link-input"
					id="sr-referral-link"
					value="<?php echo esc_attr( $shareable_url ); ?>"
					readonly
					aria-label="<?php esc_attr_e( 'Your unique referral link', 'skyyrose-flagship' ); ?>"
				/>
				<button type="button" class="sr-referral-dashboard__copy" data-copy-target="sr-referral-link">
					<?php esc_html_e( 'Copy', 'skyyrose-flagship' ); ?>
				</button>
			</div>
			<p class="sr-referral-dashboard__code-hint">
				<?php esc_html_e( 'Or share code:', 'skyyrose-flagship' ); ?>
				<strong class="sr-referral-dashboard__code"><?php echo esc_html( $referral_code ); ?></strong>
			</p>
		</div>

		<div class="sr-referral-dashboard__share">
			<a href="<?php echo esc_url( $twitter_share ); ?>" target="_blank" rel="noopener noreferrer"
				class="sr-referral-dashboard__share-btn sr-referral-dashboard__share-btn--twitter">
				<?php esc_html_e( 'Share on X', 'skyyrose-flagship' ); ?>
			</a>
			<button type="button" class="sr-referral-dashboard__share-btn sr-referral-dashboard__share-btn--copy-caption"
				data-caption="<?php echo esc_attr( $ig_caption ); ?>">
				<?php esc_html_e( 'Copy Caption', 'skyyrose-flagship' ); ?>
			</button>
		</div>

		<?php if ( $referral_count > 0 || $total_earned > 0 ) : ?>
		<div class="sr-referral-dashboard__stats">
			<div class="sr-referral-stat">
				<span class="sr-referral-stat__num"><?php echo esc_html( $referral_count ); ?></span>
				<span class="sr-referral-stat__label"><?php esc_html_e( 'Referrals', 'skyyrose-flagship' ); ?></span>
			</div>
			<div class="sr-referral-stat">
				<span class="sr-referral-stat__num">$<?php echo esc_html( number_format( $total_earned, 0 ) ); ?></span>
				<span class="sr-referral-stat__label"><?php esc_html_e( 'Earned', 'skyyrose-flagship' ); ?></span>
			</div>
		</div>
		<?php endif; ?>

		<p class="sr-referral-dashboard__terms">
			<?php esc_html_e( 'Earn $10 store credit when your referral places their first order. First 100 referrers earn the Founding Ambassador badge.', 'skyyrose-flagship' ); ?>
		</p>
	</div>
</section>

<script>
(function () {
	'use strict';
	var section = document.querySelector('.sr-referral-dashboard');
	if (!section) return;

	// Copy referral link.
	var copyBtn = section.querySelector('.sr-referral-dashboard__copy');
	if (copyBtn) {
		copyBtn.addEventListener('click', function () {
			var input = document.getElementById(copyBtn.dataset.copyTarget);
			if (!input) return;
			input.select();
			if (navigator.clipboard) {
				navigator.clipboard.writeText(input.value)
					.then(function () { copyBtn.textContent = 'Copied!'; setTimeout(function () { copyBtn.textContent = 'Copy'; }, 2000); })
					.catch(function () { document.execCommand('copy'); copyBtn.textContent = 'Copied!'; setTimeout(function () { copyBtn.textContent = 'Copy'; }, 2000); });
			} else {
				document.execCommand('copy');
				copyBtn.textContent = 'Copied!';
				setTimeout(function () { copyBtn.textContent = 'Copy'; }, 2000);
			}
		});
	}

	// Copy Instagram caption.
	var captionBtn = section.querySelector('.sr-referral-dashboard__share-btn--copy-caption');
	if (captionBtn) {
		captionBtn.addEventListener('click', function () {
			var text = captionBtn.dataset.caption || '';
			if (navigator.clipboard) {
				navigator.clipboard.writeText(text)
					.then(function () { captionBtn.textContent = 'Caption Copied!'; setTimeout(function () { captionBtn.textContent = 'Copy Caption'; }, 2000); })
					.catch(function () {});
			}
		});
	}
}());
</script>
