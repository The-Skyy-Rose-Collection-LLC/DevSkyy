<?php
/**
 * The template for displaying the footer
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

?>

	</div><!-- #content -->

	<footer id="colophon" class="site-footer">
		<?php if ( is_active_sidebar( 'footer-1' ) || is_active_sidebar( 'footer-2' ) || is_active_sidebar( 'footer-3' ) || is_active_sidebar( 'footer-4' ) ) : ?>
			<div class="footer-widgets">
				<div class="footer-widgets-container">
					<?php if ( is_active_sidebar( 'footer-1' ) ) : ?>
						<div class="footer-widget-area footer-widget-1">
							<?php dynamic_sidebar( 'footer-1' ); ?>
						</div>
					<?php endif; ?>

					<?php if ( is_active_sidebar( 'footer-2' ) ) : ?>
						<div class="footer-widget-area footer-widget-2">
							<?php dynamic_sidebar( 'footer-2' ); ?>
						</div>
					<?php endif; ?>

					<?php if ( is_active_sidebar( 'footer-3' ) ) : ?>
						<div class="footer-widget-area footer-widget-3">
							<?php dynamic_sidebar( 'footer-3' ); ?>
						</div>
					<?php endif; ?>

					<?php if ( is_active_sidebar( 'footer-4' ) ) : ?>
						<div class="footer-widget-area footer-widget-4">
							<?php dynamic_sidebar( 'footer-4' ); ?>
						</div>
					<?php endif; ?>
				</div><!-- .footer-widgets-container -->
			</div><!-- .footer-widgets -->
		<?php endif; ?>

		<div class="site-info">
			<div class="site-info-container">
				<?php
				// Footer navigation menu.
				if ( has_nav_menu( 'footer' ) ) :
					wp_nav_menu(
						array(
							'theme_location' => 'footer',
							'menu_id'        => 'footer-menu',
							'container'      => 'nav',
							'container_class' => 'footer-navigation',
							'depth'          => 1,
							'fallback_cb'    => false,
						)
					);
				endif;
				?>

				<div class="copyright">
					<?php
					/* translators: %s: Site name */
					printf( esc_html__( '&copy; %1$s %2$s. All rights reserved.', 'skyyrose-flagship' ), esc_html( gmdate( 'Y' ) ), esc_html( get_bloginfo( 'name' ) ) );
					?>
					<span class="sep"> | </span>
					<?php
					/* translators: %s: Theme name */
					printf( esc_html__( 'Powered by %s', 'skyyrose-flagship' ), '<a href="https://skyyrose.com" rel="nofollow">SkyyRose Flagship</a>' );
					?>
				</div><!-- .copyright -->
			</div><!-- .site-info-container -->
		</div><!-- .site-info -->
	</footer><!-- #colophon -->
</div><!-- #page -->

<?php wp_footer(); ?>

</body>
</html>
