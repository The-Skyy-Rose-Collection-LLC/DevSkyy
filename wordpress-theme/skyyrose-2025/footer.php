<style>
:root {
    --skyyrose-gold: #B76E79;
    --skyyrose-dark: #1a1a1a;
}

.site-footer {
    background: linear-gradient(180deg, #0a0a0a 0%, #000 100%);
    color: rgba(255, 255, 255, 0.8);
    padding: 5rem 0 2rem;
    border-top: 1px solid rgba(183, 110, 121, 0.2);
    margin-top: 8rem;
    position: relative;
}

.site-footer::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, #B76E79 50%, transparent 100%);
}

.footer-container {
    max-width: 1600px;
    margin: 0 auto;
    padding: 0 2rem;
}

.footer-grid {
    display: grid;
    grid-template-columns: 1.5fr 1fr 1fr 1.5fr;
    gap: 4rem;
    margin-bottom: 4rem;
}

/* Brand Section */
.footer-brand {
    animation: fadeInUp 0.6s ease;
}

.footer-brand .brand-logo {
    max-width: 180px;
    margin-bottom: 1.5rem;
}

.footer-brand h3 {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    color: var(--skyyrose-gold);
    margin-bottom: 0.5rem;
    letter-spacing: 2px;
}

.footer-tagline {
    font-style: italic;
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.95rem;
    margin-bottom: 1rem;
}

.footer-brand p {
    line-height: 1.8;
    margin-bottom: 1.5rem;
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.9rem;
}

.footer-location {
    color: var(--skyyrose-gold);
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.footer-social {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
}

.social-link {
    width: 42px;
    height: 42px;
    background: rgba(183, 110, 121, 0.1);
    border: 1px solid rgba(183, 110, 121, 0.3);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    font-size: 1.1rem;
    transition: all 0.4s cubic-bezier(0.6, -0.05, 0.01, 0.99);
}

.social-link:hover {
    background: var(--skyyrose-gold);
    border-color: var(--skyyrose-gold);
    transform: translateY(-4px) scale(1.05);
    box-shadow: 0 8px 20px rgba(183, 110, 121, 0.3);
}

/* Footer Sections */
.footer-section {
    animation: fadeInUp 0.6s ease;
    animation-delay: 0.2s;
    opacity: 0;
    animation-fill-mode: forwards;
}

.footer-section h4 {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--skyyrose-gold);
    margin-bottom: 1.5rem;
    font-weight: 600;
}

.footer-menu {
    list-style: none;
    padding: 0;
    margin: 0;
}

.footer-menu li {
    margin-bottom: 0.8rem;
}

.footer-menu a {
    color: rgba(255, 255, 255, 0.65);
    text-decoration: none;
    transition: all 0.3s ease;
    font-size: 0.9rem;
    display: inline-block;
}

.footer-menu a:hover {
    color: var(--skyyrose-gold);
    transform: translateX(5px);
}

/* Newsletter Section */
.footer-newsletter {
    animation: fadeInUp 0.6s ease;
    animation-delay: 0.4s;
    opacity: 0;
    animation-fill-mode: forwards;
}

.newsletter-subtitle {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.9rem;
    margin-bottom: 1rem;
    line-height: 1.6;
}

.newsletter-incentive {
    background: rgba(183, 110, 121, 0.1);
    border: 1px solid rgba(183, 110, 121, 0.3);
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 1.5rem;
    font-size: 0.85rem;
    color: var(--skyyrose-gold);
    text-align: center;
}

.newsletter-form {
    display: flex;
    gap: 0;
    margin-bottom: 1rem;
}

.newsletter-form input[type="email"] {
    flex: 1;
    padding: 0.875rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(183, 110, 121, 0.3);
    border-right: none;
    border-radius: 8px 0 0 8px;
    color: #fff;
    font-size: 0.9rem;
    transition: all 0.3s ease;
}

.newsletter-form input[type="email"]:focus {
    outline: none;
    border-color: var(--skyyrose-gold);
    background: rgba(255, 255, 255, 0.08);
}

.newsletter-form button {
    padding: 0.875rem 1.5rem;
    background: var(--skyyrose-gold);
    border: 1px solid var(--skyyrose-gold);
    border-radius: 0 8px 8px 0;
    color: #fff;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.6, -0.05, 0.01, 0.99);
}

.newsletter-form button:hover {
    background: #8B5A62;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(183, 110, 121, 0.4);
}

.newsletter-privacy {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.4);
    line-height: 1.5;
}

.newsletter-privacy a {
    color: var(--skyyrose-gold);
    text-decoration: none;
}

/* Footer Bottom */
.footer-bottom {
    padding-top: 2.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 2rem;
}

.footer-bottom-left {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.footer-copyright {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.5);
}

.footer-made-with {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.4);
}

.footer-made-with span {
    color: var(--skyyrose-gold);
}

.footer-bottom-center {
    display: flex;
    gap: 2rem;
    align-items: center;
}

.footer-bottom-center a {
    color: rgba(255, 255, 255, 0.5);
    text-decoration: none;
    font-size: 0.85rem;
    transition: color 0.3s ease;
}

.footer-bottom-center a:hover {
    color: var(--skyyrose-gold);
}

.footer-bottom-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.75rem;
}

.payment-methods {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.payment-icon {
    width: 40px;
    height: 26px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    color: rgba(255, 255, 255, 0.6);
}

.security-badges {
    display: flex;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.4);
}

.security-badge {
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

/* Animations */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Responsive */
@media (max-width: 1200px) {
    .footer-grid {
        grid-template-columns: 1fr 1fr;
        gap: 3rem;
    }
}

@media (max-width: 768px) {
    .site-footer {
        padding: 3rem 0 1.5rem;
        margin-top: 4rem;
    }

    .footer-grid {
        grid-template-columns: 1fr;
        gap: 2.5rem;
        margin-bottom: 2.5rem;
    }

    .footer-bottom {
        flex-direction: column;
        text-align: center;
        gap: 1.5rem;
    }

    .footer-bottom-left,
    .footer-bottom-right {
        align-items: center;
    }

    .footer-bottom-center {
        flex-direction: column;
        gap: 0.75rem;
    }

    .newsletter-form {
        flex-direction: column;
    }

    .newsletter-form input[type="email"],
    .newsletter-form button {
        border-radius: 8px;
        border: 1px solid rgba(183, 110, 121, 0.3);
    }
}
</style>

<footer class="site-footer">
    <div class="footer-container">
        <div class="footer-grid">
            <!-- Brand Section -->
            <div class="footer-brand">
                <?php if (has_custom_logo()) : ?>
                    <div class="brand-logo">
                        <?php the_custom_logo(); ?>
                    </div>
                <?php else : ?>
                    <h3><?php bloginfo('name'); ?></h3>
                <?php endif; ?>
                
                <p class="footer-tagline">Where Love Meets Luxury</p>
                <p>Oakland-born luxury fashion celebrating emotional depth, cultural richness, and uncompromising craftsmanship.</p>
                
                <div class="footer-location">
                    <span>📍</span>
                    <span>Oakland, California</span>
                </div>

                <div class="footer-social">
                    <a href="https://instagram.com/skyyrose" class="social-link" aria-label="Instagram" target="_blank" rel="noopener">📷</a>
                    <a href="https://facebook.com/skyyrose" class="social-link" aria-label="Facebook" target="_blank" rel="noopener">📘</a>
                    <a href="https://twitter.com/skyyrose" class="social-link" aria-label="Twitter" target="_blank" rel="noopener">🐦</a>
                    <a href="https://tiktok.com/@skyyrose" class="social-link" aria-label="TikTok" target="_blank" rel="noopener">🎵</a>
                    <a href="https://pinterest.com/skyyrose" class="social-link" aria-label="Pinterest" target="_blank" rel="noopener">📌</a>
                </div>
            </div>

            <!-- Quick Links -->
            <div class="footer-section">
                <h4>Quick Links</h4>
                <ul class="footer-menu">
                    <li><a href="<?php echo esc_url(home_url('/')); ?>">Home</a></li>
                    <li><a href="<?php echo esc_url(home_url('/collection/black-rose')); ?>">BLACK ROSE</a></li>
                    <li><a href="<?php echo esc_url(home_url('/collection/love-hurts')); ?>">LOVE HURTS</a></li>
                    <li><a href="<?php echo esc_url(home_url('/collection/signature')); ?>">SIGNATURE</a></li>
                    <li><a href="<?php echo esc_url(home_url('/vault')); ?>">Vault (Pre-Order)</a></li>
                    <li><a href="<?php echo esc_url(home_url('/about')); ?>">About Us</a></li>
                    <li><a href="<?php echo esc_url(home_url('/contact')); ?>">Contact</a></li>
                    <?php if (class_exists('WooCommerce')) : ?>
                    <li><a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>">Shop</a></li>
                    <?php endif; ?>
                </ul>
            </div>

            <!-- Customer Service -->
            <div class="footer-section">
                <h4>Customer Service</h4>
                <ul class="footer-menu">
                    <li><a href="<?php echo esc_url(home_url('/shipping-returns')); ?>">Shipping & Returns</a></li>
                    <li><a href="<?php echo esc_url(home_url('/size-guide')); ?>">Size Guide</a></li>
                    <li><a href="<?php echo esc_url(home_url('/care-instructions')); ?>">Care Instructions</a></li>
                    <li><a href="<?php echo esc_url(home_url('/faq')); ?>">FAQ</a></li>
                    <li><a href="<?php echo esc_url(home_url('/privacy-policy')); ?>">Privacy Policy</a></li>
                    <li><a href="<?php echo esc_url(home_url('/terms-conditions')); ?>">Terms & Conditions</a></li>
                    <li><a href="<?php echo esc_url(home_url('/accessibility')); ?>">Accessibility</a></li>
                    <?php if (class_exists('WooCommerce')) : ?>
                    <li><a href="<?php echo esc_url(wc_get_page_permalink('myaccount')); ?>">My Account</a></li>
                    <?php endif; ?>
                </ul>
            </div>

            <!-- Newsletter -->
            <div class="footer-newsletter">
                <h4>Stay Updated</h4>
                <p class="newsletter-subtitle">Subscribe to get exclusive offers, new collection launches, and styling tips.</p>
                
                <div class="newsletter-incentive">
                    ✨ Get 10% off your first order
                </div>

                <form class="newsletter-form" method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                    <input type="hidden" name="action" value="skyyrose_newsletter_signup">
                    <?php wp_nonce_field('skyyrose_newsletter', 'newsletter_nonce'); ?>
                    <input type="email" 
                           name="newsletter_email" 
                           placeholder="Enter your email" 
                           required 
                           aria-label="Email address">
                    <button type="submit">Subscribe</button>
                </form>

                <p class="newsletter-privacy">
                    By subscribing, you agree to our <a href="<?php echo esc_url(home_url('/privacy-policy')); ?>">Privacy Policy</a>. Unsubscribe anytime.
                </p>
            </div>
        </div>

        <!-- Footer Bottom -->
        <div class="footer-bottom">
            <div class="footer-bottom-left">
                <p class="footer-copyright">
                    &copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?> LLC. All Rights Reserved.
                </p>
                <p class="footer-made-with">
                    Built with <span>♥</span> in Oakland, CA
                </p>
            </div>

            <div class="footer-bottom-center">
                <a href="mailto:hello@skyyrose.co">hello@skyyrose.co</a>
                <a href="<?php echo esc_url(home_url('/wholesale')); ?>">Wholesale Inquiry</a>
                <a href="<?php echo esc_url(home_url('/press')); ?>">Press</a>
            </div>

            <div class="footer-bottom-right">
                <div class="payment-methods" aria-label="Accepted payment methods">
                    <span class="payment-icon" title="Visa">VISA</span>
                    <span class="payment-icon" title="Mastercard">MC</span>
                    <span class="payment-icon" title="American Express">AMEX</span>
                    <span class="payment-icon" title="PayPal">PP</span>
                    <span class="payment-icon" title="Apple Pay">🍎</span>
                </div>
                <div class="security-badges">
                    <span class="security-badge">🔒 SSL Secure</span>
                    <span class="security-badge">✓ GDPR Compliant</span>
                </div>
            </div>
        </div>
    </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
