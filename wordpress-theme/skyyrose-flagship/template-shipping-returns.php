<?php
/**
 * Template Name: Shipping & Returns
 *
 * Shipping rates, processing times, return policy, exchanges.
 * Dark luxury layout with glass cards per section.
 *
 * @package SkyyRose
 * @since   6.4.0
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="primary" class="info-page info-page--shipping" role="main">
	<div class="info-page__container">

		<!-- Hero -->
		<header class="info-page__hero rv-clip-up">
			<span class="info-page__badge"><?php esc_html_e( 'Policies', 'skyyrose' ); ?></span>
			<h1 class="info-page__title"><?php esc_html_e( 'Shipping & Returns', 'skyyrose' ); ?></h1>
			<p class="info-page__subtitle"><?php esc_html_e( 'We want you to love what you wear. Here\'s how we make that happen.', 'skyyrose' ); ?></p>
		</header>

		<!-- Shipping Section -->
		<section class="ship-section rv-clip-up" aria-labelledby="shipping-heading">
			<h2 class="ship-section__title" id="shipping-heading">
				<span class="ship-section__icon" aria-hidden="true">&#x2726;</span>
				<?php esc_html_e( 'Shipping', 'skyyrose' ); ?>
			</h2>

			<div class="ship-cards">
				<div class="ship-card">
					<h3><?php esc_html_e( 'Processing Time', 'skyyrose' ); ?></h3>
					<p><?php esc_html_e( 'Orders are processed within 1–3 business days. During new collection drops or holiday periods, processing may take up to 5 business days. You\'ll receive a confirmation email with tracking once your order ships.', 'skyyrose' ); ?></p>
				</div>

				<div class="ship-card">
					<h3><?php esc_html_e( 'Domestic Shipping (US)', 'skyyrose' ); ?></h3>
					<table class="ship-table" aria-label="<?php esc_attr_e( 'US shipping rates', 'skyyrose' ); ?>">
						<thead>
							<tr>
								<th scope="col"><?php esc_html_e( 'Method', 'skyyrose' ); ?></th>
								<th scope="col"><?php esc_html_e( 'Time', 'skyyrose' ); ?></th>
								<th scope="col"><?php esc_html_e( 'Cost', 'skyyrose' ); ?></th>
							</tr>
						</thead>
						<tbody>
							<tr>
								<td><?php esc_html_e( 'Standard', 'skyyrose' ); ?></td>
								<td><?php esc_html_e( '5–7 business days', 'skyyrose' ); ?></td>
								<td><?php esc_html_e( '$7.95', 'skyyrose' ); ?></td>
							</tr>
							<tr>
								<td><?php esc_html_e( 'Express', 'skyyrose' ); ?></td>
								<td><?php esc_html_e( '2–3 business days', 'skyyrose' ); ?></td>
								<td><?php esc_html_e( '$14.95', 'skyyrose' ); ?></td>
							</tr>
							<tr>
								<td><?php esc_html_e( 'Free Shipping', 'skyyrose' ); ?></td>
								<td><?php esc_html_e( '5–7 business days', 'skyyrose' ); ?></td>
								<td><?php
									/* translators: %d: free shipping order minimum in dollars */
									printf( esc_html__( 'Orders $%d+', 'skyyrose' ), intval( SKYYROSE_FREE_SHIPPING_THRESHOLD ) );
									?></td>
							</tr>
						</tbody>
					</table>
				</div>

				<div class="ship-card">
					<h3><?php esc_html_e( 'International Shipping', 'skyyrose' ); ?></h3>
					<p><?php esc_html_e( 'We ship to 40+ countries. International rates are calculated at checkout based on destination and package weight. Delivery typically takes 10–14 business days. Customs duties and import taxes are the responsibility of the recipient and are not included in the shipping cost.', 'skyyrose' ); ?></p>
				</div>
			</div>
		</section>

		<!-- Returns Section -->
		<section class="ship-section rv-clip-up" aria-labelledby="returns-heading">
			<h2 class="ship-section__title" id="returns-heading">
				<span class="ship-section__icon" aria-hidden="true">&#x2726;</span>
				<?php esc_html_e( 'Returns', 'skyyrose' ); ?>
			</h2>

			<div class="ship-cards">
				<div class="ship-card ship-card--highlight">
					<h3><?php esc_html_e( '30-Day Return Window', 'skyyrose' ); ?></h3>
					<p><?php esc_html_e( 'Not feeling it? Return any unworn item within 30 days of delivery for a full refund. Items must be in original condition with tags attached and in original packaging.', 'skyyrose' ); ?></p>
				</div>

				<div class="ship-card">
					<h3><?php esc_html_e( 'How to Return', 'skyyrose' ); ?></h3>
					<ol class="ship-steps">
						<li><?php esc_html_e( 'Email support@skyyrose.co with your order number', 'skyyrose' ); ?></li>
						<li><?php esc_html_e( 'Receive your prepaid return label within 24 hours', 'skyyrose' ); ?></li>
						<li><?php esc_html_e( 'Pack the item in its original packaging', 'skyyrose' ); ?></li>
						<li><?php esc_html_e( 'Drop off at any USPS location', 'skyyrose' ); ?></li>
						<li><?php esc_html_e( 'Refund processed within 5–7 business days of receipt', 'skyyrose' ); ?></li>
					</ol>
				</div>

				<div class="ship-card">
					<h3><?php esc_html_e( 'Non-Returnable Items', 'skyyrose' ); ?></h3>
					<ul class="ship-list">
						<li><?php esc_html_e( 'Items marked "Final Sale"', 'skyyrose' ); ?></li>
						<li><?php esc_html_e( 'Worn, washed, or altered items', 'skyyrose' ); ?></li>
						<li><?php esc_html_e( 'Items without original tags', 'skyyrose' ); ?></li>
						<li><?php esc_html_e( 'Gift cards', 'skyyrose' ); ?></li>
					</ul>
				</div>
			</div>
		</section>

		<!-- Exchanges Section -->
		<section class="ship-section rv-clip-up" aria-labelledby="exchanges-heading">
			<h2 class="ship-section__title" id="exchanges-heading">
				<span class="ship-section__icon" aria-hidden="true">&#x2726;</span>
				<?php esc_html_e( 'Exchanges', 'skyyrose' ); ?>
			</h2>

			<div class="ship-cards">
				<div class="ship-card">
					<h3><?php esc_html_e( 'Free Exchanges (US)', 'skyyrose' ); ?></h3>
					<p><?php esc_html_e( 'Need a different size? Exchanges are free for US orders. Email support@skyyrose.co and we\'ll ship your new size immediately — just return the original within 14 days using our prepaid label.', 'skyyrose' ); ?></p>
				</div>

				<div class="ship-card">
					<h3><?php esc_html_e( 'International Exchanges', 'skyyrose' ); ?></h3>
					<p><?php esc_html_e( 'International customers are responsible for return shipping costs on exchanges. Once we receive and verify the returned item, we\'ll ship the new size at no additional charge.', 'skyyrose' ); ?></p>
				</div>
			</div>
		</section>

		<!-- Pre-Orders Section -->
		<section class="ship-section rv-clip-up" aria-labelledby="preorders-heading">
			<h2 class="ship-section__title" id="preorders-heading">
				<span class="ship-section__icon" aria-hidden="true">&#x2726;</span>
				<?php esc_html_e( 'Pre-Orders', 'skyyrose' ); ?>
			</h2>

			<div class="ship-cards">
				<div class="ship-card">
					<h3><?php esc_html_e( 'How Pre-Orders Work', 'skyyrose' ); ?></h3>
					<p><?php esc_html_e( 'Pre-orders secure your piece before the official drop. Your card is charged at the time of pre-order. Estimated ship dates are displayed on each product page. Pre-order items ship separately from in-stock items.', 'skyyrose' ); ?></p>
				</div>
				<div class="ship-card">
					<h3><?php esc_html_e( 'Pre-Order Cancellations', 'skyyrose' ); ?></h3>
					<p><?php esc_html_e( 'Pre-orders can be cancelled for a full refund up to 48 hours before the estimated ship date. After that, standard return policy applies once delivered.', 'skyyrose' ); ?></p>
				</div>
			</div>
		</section>

		<!-- Contact CTA -->
		<section class="info-page__cta rv-blur">
			<h2><?php esc_html_e( 'Need Help?', 'skyyrose' ); ?></h2>
			<p><?php esc_html_e( 'Our support team responds within 24 hours. Reach out anytime.', 'skyyrose' ); ?></p>
			<a href="mailto:support@skyyrose.co" class="info-page__cta-btn btn-sweep btn-press"><?php esc_html_e( 'Email Support', 'skyyrose' ); ?></a>
		</section>

	</div>
</main>

<?php get_footer(); ?>
