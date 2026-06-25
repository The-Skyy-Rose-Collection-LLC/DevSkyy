<?php
/**
 * Template part for displaying a message that posts cannot be found
 *
 * Used by archive.php and search.php fallback paths. Renders the brand
 * empty-state copy and a CTA pair built from the shared button primitive
 * (template-parts/components/button.php) — primary leads to /shop/,
 * secondary returns home.
 *
 * @package SkyyRose
 * @since   1.0.0
 */

defined( 'ABSPATH' ) || exit;
?>

<section class="no-results not-found">
	<header class="page-header">
		<h1 class="page-title"><?php esc_html_e( 'The Vault Is Quiet.', 'skyyrose' ); ?></h1>
	</header><!-- .page-header -->

	<div class="page-content">
		<?php
		if ( is_home() && current_user_can( 'publish_posts' ) ) :

			printf(
				'<p>' . wp_kses(
					/* translators: 1: link to WP admin new post page. */
					__( 'Ready to publish your first post? <a href="%1$s">Get started here</a>.', 'skyyrose' ),
					array(
						'a' => array(
							'href' => array(),
						),
					)
				) . '</p>',
				esc_url( admin_url( 'post-new.php' ) )
			);

		elseif ( is_search() ) :
			?>

			<p><?php esc_html_e( 'Those pieces don\'t live here. Try another name, another collection.', 'skyyrose' ); ?></p>
			<?php
			get_search_form();

		else :
			?>

			<p><?php esc_html_e( 'Nothing in this drawer yet. The drop you\'re looking for might be in another collection.', 'skyyrose' ); ?></p>
			<?php
		endif;
		?>

		<div class="no-results__cta-group">
			<?php
			get_template_part(
				'template-parts/components/button',
				null,
				array(
					'label'         => __( 'Browse Collections', 'skyyrose' ),
					'tag'           => 'a',
					'href'          => esc_url( home_url( '/shop/' ) ),
					'variant'       => 'primary',
					'size'          => 'md',
					'extra_classes' => 'no-results__cta no-results__cta--primary',
				)
			);
			get_template_part(
				'template-parts/components/button',
				null,
				array(
					'label'         => __( 'Return Home', 'skyyrose' ),
					'tag'           => 'a',
					'href'          => esc_url( home_url( '/' ) ),
					'variant'       => 'ghost',
					'size'          => 'md',
					'extra_classes' => 'no-results__cta no-results__cta--secondary',
				)
			);
			?>
		</div>
	</div><!-- .page-content -->
</section><!-- .no-results -->
