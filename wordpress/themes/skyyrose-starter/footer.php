<?php
/**
 * Footer Template
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;
?>
</main>

<!-- Newsletter Section -->
<section class="newsletter">
    <div class="newsletter-content">
        <span class="section-label">Stay Connected</span>
        <h2>Join the SkyyRose Family</h2>
        <p>Be the first to know about new drops, exclusive offers, and behind-the-scenes content.</p>
        <form class="newsletter-form" id="newsletterForm">
            <input type="email" name="email" placeholder="Enter your email" required>
            <button type="submit" class="btn btn-primary">Subscribe</button>
        </form>
        <p class="newsletter-note">By subscribing, you agree to receive marketing emails. Unsubscribe anytime.</p>
    </div>
</section>

<!-- Footer -->
<footer class="footer">
    <div class="footer-grid">
        <div class="footer-brand">
            <?php skyyrose_logo(); ?>
            <p>Where love meets luxury. Oakland-born streetwear for those who wear their heart on their sleeve.</p>
            <?php skyyrose_social_links(); ?>
        </div>

        <div class="footer-column">
            <h4 class="footer-title">Shop</h4>
            <ul class="footer-links">
                <li><a href="<?php echo esc_url(home_url('/collection-black-rose')); ?>">Black Rose</a></li>
                <li><a href="<?php echo esc_url(home_url('/collection-love-hurts')); ?>">Love Hurts</a></li>
                <li><a href="<?php echo esc_url(home_url('/collection-signature')); ?>">Signature</a></li>
                <li><a href="<?php echo esc_url(home_url('/shop')); ?>">All Products</a></li>
            </ul>
        </div>

        <div class="footer-column">
            <h4 class="footer-title">Company</h4>
            <ul class="footer-links">
                <li><a href="<?php echo esc_url(home_url('/about')); ?>">About Us</a></li>
                <li><a href="<?php echo esc_url(home_url('/blog')); ?>">Journal</a></li>
                <li><a href="<?php echo esc_url(home_url('/contact')); ?>">Contact</a></li>
                <li><a href="<?php echo esc_url(home_url('/careers')); ?>">Careers</a></li>
            </ul>
        </div>

        <div class="footer-column">
            <h4 class="footer-title">Support</h4>
            <ul class="footer-links">
                <li><a href="<?php echo esc_url(home_url('/shipping')); ?>">Shipping & Returns</a></li>
                <li><a href="<?php echo esc_url(home_url('/size-guide')); ?>">Size Guide</a></li>
                <li><a href="<?php echo esc_url(home_url('/faq')); ?>">FAQ</a></li>
                <li><a href="<?php echo esc_url(home_url('/track-order')); ?>">Track Order</a></li>
            </ul>
        </div>

        <div class="footer-column">
            <h4 class="footer-title">Legal</h4>
            <ul class="footer-links">
                <li><a href="<?php echo esc_url(home_url('/privacy-policy')); ?>">Privacy Policy</a></li>
                <li><a href="<?php echo esc_url(home_url('/terms')); ?>">Terms of Service</a></li>
                <li><a href="<?php echo esc_url(home_url('/cookie-policy')); ?>">Cookie Policy</a></li>
            </ul>
        </div>
    </div>

    <div class="footer-bottom">
        <p>&copy; <?php echo date('Y'); ?> SkyyRose. All rights reserved.</p>
        <?php skyyrose_payment_icons(); ?>
    </div>
</footer>

<!-- Toast Notification -->
<div class="toast" id="toast">
    <span class="toast-message"></span>
</div>

<?php wp_footer(); ?>
</body>
</html>
