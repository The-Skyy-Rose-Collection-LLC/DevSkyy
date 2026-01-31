<style>
.site-footer {
    background: #000;
    color: rgba(255, 255, 255, 0.8);
    padding: 4rem 0 2rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    margin-top: 6rem;
}

.footer-container {
    max-width: 1600px;
    margin: 0 auto;
    padding: 0 2rem;
}

.footer-grid {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr;
    gap: 4rem;
    margin-bottom: 3rem;
}

.footer-brand h3 {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    color: #D4AF37;
    margin-bottom: 1rem;
}

.footer-brand p {
    line-height: 1.8;
    margin-bottom: 1.5rem;
    color: rgba(255, 255, 255, 0.6);
}

.footer-social {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
}

.social-link {
    width: 40px;
    height: 40px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    font-size: 1.1rem;
    transition: all 0.3s ease;
}

.social-link:hover {
    background: #D4AF37;
    border-color: #D4AF37;
    transform: translateY(-3px);
}

.footer-section h4 {
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #D4AF37;
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
    color: rgba(255, 255, 255, 0.6);
    text-decoration: none;
    transition: color 0.3s ease;
    font-size: 0.95rem;
}

.footer-menu a:hover {
    color: #D4AF37;
}

.footer-bottom {
    padding-top: 2rem;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.5);
}

.footer-credits {
    display: flex;
    gap: 2rem;
}

.footer-credits a {
    color: rgba(255, 255, 255, 0.5);
    text-decoration: none;
    transition: color 0.3s ease;
}

.footer-credits a:hover {
    color: #D4AF37;
}

@media (max-width: 1024px) {
    .footer-grid {
        grid-template-columns: 1fr 1fr;
        gap: 3rem;
    }
}

@media (max-width: 768px) {
    .footer-grid {
        grid-template-columns: 1fr;
        gap: 2rem;
    }

    .footer-bottom {
        flex-direction: column;
        gap: 1rem;
        text-align: center;
    }

    .footer-credits {
        flex-direction: column;
        gap: 0.5rem;
    }
}
</style>

<footer class="site-footer">
    <div class="footer-container">
        <div class="footer-grid">
            <!-- Brand Section -->
            <div class="footer-brand">
                <h3><?php bloginfo('name'); ?></h3>
                <p>Oakland-born luxury streetwear celebrating emotional depth, cultural richness, and uncompromising craftsmanship. Where Love Meets Luxury.</p>
                <div class="footer-social">
                    <a href="#" class="social-link" aria-label="Instagram">📷</a>
                    <a href="#" class="social-link" aria-label="Twitter">🐦</a>
                    <a href="#" class="social-link" aria-label="TikTok">🎵</a>
                    <a href="#" class="social-link" aria-label="Pinterest">📌</a>
                </div>
            </div>

            <!-- Shop Section -->
            <div class="footer-section">
                <h4>Collections</h4>
                <ul class="footer-menu">
                    <li><a href="<?php echo esc_url(home_url('/black-rose')); ?>">Black Rose</a></li>
                    <li><a href="<?php echo esc_url(home_url('/love-hurts')); ?>">Love Hurts</a></li>
                    <li><a href="<?php echo esc_url(home_url('/signature')); ?>">Signature</a></li>
                    <li><a href="<?php echo esc_url(home_url('/vault')); ?>">Pre-Order</a></li>
                </ul>
            </div>

            <!-- About Section -->
            <div class="footer-section">
                <h4>About</h4>
                <ul class="footer-menu">
                    <li><a href="<?php echo esc_url(home_url('/about')); ?>">Our Story</a></li>
                    <li><a href="<?php echo esc_url(home_url('/contact')); ?>">Contact</a></li>
                    <li><a href="#">Careers</a></li>
                    <li><a href="#">Press</a></li>
                </ul>
            </div>

            <!-- Support Section -->
            <div class="footer-section">
                <h4>Support</h4>
                <ul class="footer-menu">
                    <li><a href="#">Shipping & Returns</a></li>
                    <li><a href="#">Size Guide</a></li>
                    <li><a href="#">FAQ</a></li>
                    <li><a href="#">Privacy Policy</a></li>
                </ul>
            </div>
        </div>

        <!-- Footer Bottom -->
        <div class="footer-bottom">
            <p>&copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?>. All rights reserved.</p>
            <div class="footer-credits">
                <a href="mailto:hello@skyyrose.co">hello@skyyrose.co</a>
                <span>Oakland, California</span>
            </div>
        </div>
    </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
