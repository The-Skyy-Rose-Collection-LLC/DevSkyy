    <footer id="colophon" class="site-footer">
        <div class="container">
            <div class="site-info">
                <p>&copy; <?php echo date('Y'); ?> <a href="<?php echo esc_url(home_url('/')); ?>"><?php bloginfo('name'); ?></a>. <?php esc_html_e('All rights reserved.', 'skyy-rose-luxury-fixed-2024'); ?></p>
                <p class="luxury-accent"><?php esc_html_e('Luxury Fashion Redefined', 'skyy-rose-luxury-fixed-2024'); ?></p>
                <p><small><?php esc_html_e('Powered by', 'skyy-rose-luxury-fixed-2024'); ?> <a href="https://devskyy.com" target="_blank" rel="noopener">DevSkyy Platform</a></small></p>
            </div>

            <?php if (has_nav_menu('footer')) : ?>
                <nav class="footer-navigation" role="navigation" aria-label="<?php esc_attr_e('Footer Menu', 'skyy-rose-luxury-fixed-2024'); ?>">
                    <?php
                    wp_nav_menu(array(
                        'theme_location' => 'footer',
                        'menu_id' => 'footer-menu',
                        'depth' => 1,
                        'container' => false,
                    ));
                    ?>
                </nav>
            <?php endif; ?>
        </div>
    </footer>
</div>

<?php wp_footer(); ?>
</body>
</html>
