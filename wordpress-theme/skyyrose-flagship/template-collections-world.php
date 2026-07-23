<?php
/**
 * Template Name: Collections World (Scroll Fly-Through)
 * Template Post Type: page
 *
 * Full-bleed, scroll-scrubbed continuous camera fly-through through the four
 * SkyyRose collection worlds + a finale CTA. Bare canvas (no theme header/footer)
 * so the vanilla scroll-world engine (assets/js/scroll-world.js) owns the full
 * viewport — it builds its own fixed chrome (topbar, section rail, copy layer).
 *
 * Assets + copy come from skyyrose_get_collections_world_config()
 * (inc/collections-world.php), localized as SKYY_SCROLL_WORLD_CONFIG by
 * inc/enqueue.php on the 'collections-world' slug. The gothic-noir skin is
 * assets/css/scroll-world.css (loaded via the same slug).
 *
 * IMPORTANT: do NOT assign this template to the page with slug 'collections' —
 * that page is force-routed to page-collections.php by inc/redirects.php. Assign
 * it to a dedicated page (e.g. /world/ or /collections-world/).
 *
 * @package SkyyRose
 * @since   1.12.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?><!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<?php wp_head(); ?>
</head>
<body <?php body_class( 'skyyrose-collections-world' ); ?>>
<?php wp_body_open(); ?>

<a class="skip-link" href="#skyyrose-collections-world"><?php esc_html_e( 'Skip to the collections', 'skyyrose' ); ?></a>

<?php // The scroll-world engine mounts its full experience into this container. ?>
<div id="skyyrose-collections-world" tabindex="-1"></div>

<noscript>
	<div style="min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0A0A0A;color:#F4EFE9;font-family:sans-serif;padding:2rem;text-align:center;">
		<p>
			<?php esc_html_e( 'This scroll experience needs JavaScript.', 'skyyrose' ); ?><br>
			<a style="color:#B76E79;font-weight:600;" href="<?php echo esc_url( home_url( '/collections/' ) ); ?>"><?php esc_html_e( 'Shop the Collections', 'skyyrose' ); ?></a>
		</p>
	</div>
</noscript>

<?php
// Bare canvas never calls get_footer(), so the sitewide mascot mount in
// footer.php never reaches it. Mount independently here, same kill-switch gate
// (Customizer toggle, checkout excluded) as footer.php/front-page.php — keeps the
// site host present on this template like it is on the immersive rooms.
if ( function_exists( 'skyyrose_mascot_is_enabled' ) && skyyrose_mascot_is_enabled()
	&& ! ( function_exists( 'is_checkout' ) && is_checkout() ) ) {
	get_template_part( 'template-parts/skyy-mascot' );
}
?>

<?php wp_footer(); ?>
</body>
</html>
