<footer class="site-footer glass">
    <div class="container">
        <div class="footer-content">
            <p>&copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?>. Where Love Meets Luxury.</p>
            <?php
            wp_nav_menu([
                'theme_location' => 'footer',
                'menu_class' => 'footer-menu',
                'fallback_cb' => false,
            ]);
            ?>
        </div>
    </div>
</footer>
<?php wp_footer(); ?>
</body>
</html>
