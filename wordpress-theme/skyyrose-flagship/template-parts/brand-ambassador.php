<?php
/**
 * Template Part: Brand Ambassador — Skyy Rose Chatbot Widget
 *
 * Floating chat widget featuring the Skyy Rose avatar. She answers
 * questions about the brand, collections, sizing, and pre-orders
 * via a guided conversational tree with keyword fallback.
 *
 * Loaded automatically via functions.php wp_footer hook.
 *
 * @package SkyyRose_Flagship
 * @since   3.10.0
 */

defined( 'ABSPATH' ) || exit;

$skyyrose_ambassador_avatar = esc_url( SKYYROSE_ASSETS_URI . '/images/avatar/skyy-rose-reference.jpeg' );
?>

<!-- Brand Ambassador Widget -->
<div class="sr-ambassador" id="sr-ambassador" aria-label="<?php esc_attr_e( 'Chat with Skyy Rose', 'skyyrose-flagship' ); ?>">

	<!-- Floating Avatar Button -->
	<button type="button" class="sr-ambassador__fab" id="sr-ambassador-fab"
	        aria-expanded="false"
	        aria-controls="sr-ambassador-panel"
	        aria-label="<?php esc_attr_e( 'Open chat with Skyy Rose, our brand ambassador', 'skyyrose-flagship' ); ?>">
		<img src="<?php echo esc_url( $skyyrose_ambassador_avatar ); ?>"
		     alt="<?php esc_attr_e( 'Skyy Rose', 'skyyrose-flagship' ); ?>"
		     class="sr-ambassador__fab-avatar"
		     width="56" height="56" loading="lazy" />
		<span class="sr-ambassador__fab-pulse" aria-hidden="true"></span>
	</button>

	<!-- Greeting Bubble (auto-shows after delay) -->
	<div class="sr-ambassador__greeting" id="sr-ambassador-greeting" role="status" aria-live="polite">
		<?php esc_html_e( 'Hey! Need help finding your style?', 'skyyrose-flagship' ); ?>
		<button type="button" class="sr-ambassador__greeting-close" aria-label="<?php esc_attr_e( 'Dismiss', 'skyyrose-flagship' ); ?>">&times;</button>
	</div>

	<!-- Chat Panel -->
	<div class="sr-ambassador__panel" id="sr-ambassador-panel"
	     role="dialog" aria-modal="false"
	     aria-label="<?php esc_attr_e( 'Chat with Skyy Rose', 'skyyrose-flagship' ); ?>"
	     aria-hidden="true" hidden>

		<!-- Header -->
		<div class="sr-ambassador__header">
			<img src="<?php echo esc_url( $skyyrose_ambassador_avatar ); ?>"
			     alt="" class="sr-ambassador__header-avatar"
			     width="32" height="32" loading="lazy" />
			<div class="sr-ambassador__header-info">
				<strong><?php esc_html_e( 'Skyy Rose', 'skyyrose-flagship' ); ?></strong>
				<span class="sr-ambassador__header-status"><?php esc_html_e( 'Brand Ambassador', 'skyyrose-flagship' ); ?></span>
			</div>
			<button type="button" class="sr-ambassador__close" id="sr-ambassador-close"
			        aria-label="<?php esc_attr_e( 'Close chat', 'skyyrose-flagship' ); ?>">&times;</button>
		</div>

		<!-- Messages Area -->
		<div class="sr-ambassador__messages" id="sr-ambassador-messages"
		     role="log" aria-live="polite" aria-relevant="additions">
		</div>

		<!-- Quick Replies -->
		<div class="sr-ambassador__quick-replies" id="sr-ambassador-replies">
		</div>

		<!-- Text Input -->
		<form class="sr-ambassador__input-form" id="sr-ambassador-form" autocomplete="off">
			<input class="sr-ambassador__input" id="sr-ambassador-input"
			       type="text"
			       placeholder="<?php esc_attr_e( 'Ask Skyy Rose anything...', 'skyyrose-flagship' ); ?>"
			       aria-label="<?php esc_attr_e( 'Type your message', 'skyyrose-flagship' ); ?>" />
			<button class="sr-ambassador__send" type="submit"
			        aria-label="<?php esc_attr_e( 'Send message', 'skyyrose-flagship' ); ?>">
				<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
					<line x1="22" y1="2" x2="11" y2="13"></line>
					<polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
				</svg>
			</button>
		</form>

	</div><!-- .sr-ambassador__panel -->
</div><!-- .sr-ambassador -->
