<?php
/**
 * Thankyou — Order Received page
 *
 * Brand-voice override of WooCommerce's default thankyou template.
 * Founder canon: garment is the protagonist, no urgency, no cross-sells.
 *
 * @see     woocommerce/templates/checkout/thankyou.php (WC default)
 * @package SkyyRose
 * @since   1.1.3
 *
 * @var WC_Order|false $order
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

?>
<section class="sr-thankyou" role="region" aria-labelledby="sr-thankyou-h">

	<?php if ( $order ) : ?>

		<?php
		/* Fire WC's standard pre-content hook INSIDE the wrapper (matching WC
		 * core's structural placement) so analytics / conversion-pixel plugins
		 * that emit HTML (e.g. noscript pixels) land inside the section, not
		 * above it. */
		do_action( 'woocommerce_before_thankyou', $order->get_id() );
		?>

		<?php if ( $order->has_status( 'failed' ) ) : ?>

			<p class="sr-thankyou__failed">
				<?php esc_html_e( 'Payment didn\'t go through. Nothing was charged. Try the checkout again, or send us a note and we\'ll sort it.', 'skyyrose' ); ?>
			</p>

			<p class="sr-thankyou__actions">
				<a href="<?php echo esc_url( $order->get_checkout_payment_url() ); ?>" class="button sr-thankyou__retry">
					<?php esc_html_e( 'Try Again', 'skyyrose' ); ?>
				</a>
				<a href="<?php echo esc_url( wc_get_page_permalink( 'myaccount' ) ); ?>" class="button sr-thankyou__account">
					<?php esc_html_e( 'My Account', 'skyyrose' ); ?>
				</a>
			</p>

		<?php else : ?>

			<p class="sr-thankyou__eyebrow"><?php esc_html_e( 'Order Received', 'skyyrose' ); ?></p>
			<h1 id="sr-thankyou-h" class="sr-thankyou__headline">
				<?php
				$first_name = $order->get_billing_first_name();
				if ( $first_name ) {
					/* translators: %s: customer first name */
					printf( esc_html__( 'Thank you, %s.', 'skyyrose' ), esc_html( $first_name ) );
				} else {
					esc_html_e( 'Thank you.', 'skyyrose' );
				}
				?>
			</h1>

			<p class="sr-thankyou__body">
				<?php esc_html_e( 'Your pieces are being prepared. Each one is checked by hand before it leaves us. You\'ll get a shipping confirmation by email once they\'re on their way.', 'skyyrose' ); ?>
			</p>

			<dl class="sr-thankyou__details">
				<div class="sr-thankyou__detail">
					<dt><?php esc_html_e( 'Order', 'skyyrose' ); ?></dt>
					<dd><?php echo esc_html( $order->get_order_number() ); ?></dd>
				</div>
				<div class="sr-thankyou__detail">
					<dt><?php esc_html_e( 'Date', 'skyyrose' ); ?></dt>
					<dd><?php echo esc_html( wc_format_datetime( $order->get_date_created() ) ); ?></dd>
				</div>
				<?php if ( is_user_logged_in() && $order->get_user_id() === get_current_user_id() && $order->get_billing_email() ) : ?>
					<div class="sr-thankyou__detail">
						<dt><?php esc_html_e( 'Email', 'skyyrose' ); ?></dt>
						<dd><?php echo esc_html( $order->get_billing_email() ); ?></dd>
					</div>
				<?php endif; ?>
				<div class="sr-thankyou__detail">
					<dt><?php esc_html_e( 'Total', 'skyyrose' ); ?></dt>
					<dd><?php echo wp_kses_post( $order->get_formatted_order_total() ); ?></dd>
				</div>
				<?php if ( $order->get_payment_method_title() ) : ?>
					<div class="sr-thankyou__detail">
						<dt><?php esc_html_e( 'Payment Method', 'skyyrose' ); ?></dt>
						<dd><?php echo wp_kses_post( $order->get_payment_method_title() ); ?></dd>
					</div>
				<?php endif; ?>
			</dl>

			<?php
			/* Render itemized order line items — the garment IS the proof of
			 * purchase on this page. WC's standard order/order-details.php
			 * template handles permissions (download links, etc.). */
			wc_get_template(
				'order/order-details.php',
				array(
					'order_id'       => $order->get_id(),
					'show_downloads' => $order->has_downloadable_item() && $order->is_download_permitted(),
				)
			);
			?>

			<?php do_action( 'woocommerce_thankyou_' . $order->get_payment_method(), $order->get_id() ); ?>
			<?php do_action( 'woocommerce_thankyou', $order->get_id() ); ?>

		<?php endif; ?>

	<?php else : ?>

		<p class="sr-thankyou__eyebrow"><?php esc_html_e( 'Order Received', 'skyyrose' ); ?></p>
		<h1 id="sr-thankyou-h" class="sr-thankyou__headline"><?php esc_html_e( 'Thank you.', 'skyyrose' ); ?></h1>
		<p class="sr-thankyou__body">
			<?php esc_html_e( 'Your order has been received and is being prepared. A confirmation has been sent to your email.', 'skyyrose' ); ?>
		</p>

	<?php endif; ?>

</section>
