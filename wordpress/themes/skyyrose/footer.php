<?php
/**
 * SkyyRose Theme Footer
 *
 * Newsletter signup, footer navigation, social links, and copyright.
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;
?>

    <!-- Back to Top Button -->
    <button id="back-to-top" class="back-to-top" aria-label="<?php esc_attr_e('Back to top', 'skyyrose'); ?>">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="18 15 12 9 6 15"></polyline>
        </svg>
    </button>

    <footer id="site-footer" class="site-footer" role="contentinfo">

        <!-- Newsletter Section -->
        <section class="footer-newsletter">
            <div class="container">
                <div class="newsletter-glass-card">
                    <div class="newsletter-content">
                        <div class="newsletter-text">
                            <h3 class="newsletter-heading"><?php esc_html_e('Join the Rose Garden', 'skyyrose'); ?></h3>
                            <p class="newsletter-description">
                                <?php esc_html_e('Be the first to know about exclusive drops, early access to collections, and members-only offers. Welcome to the inner circle.', 'skyyrose'); ?>
                            </p>
                        </div>
                        <div class="newsletter-form-wrapper">
                            <?php if (is_active_sidebar('footer-newsletter')) : ?>
                                <?php dynamic_sidebar('footer-newsletter'); ?>
                            <?php else : ?>
                                <!-- Klaviyo-ready fallback form -->
                                <form class="newsletter-form klaviyo-form" action="#" method="post" data-klaviyo-list="<?php echo esc_attr(get_theme_mod('skyyrose_klaviyo_list_id', '')); ?>">
                                    <div class="form-group">
                                        <label for="newsletter-email" class="sr-only"><?php esc_attr_e('Email address', 'skyyrose'); ?></label>
                                        <input
                                            type="email"
                                            id="newsletter-email"
                                            name="email"
                                            class="newsletter-input"
                                            placeholder="<?php esc_attr_e('Enter your email', 'skyyrose'); ?>"
                                            required
                                            autocomplete="email"
                                        >
                                        <button type="submit" class="newsletter-submit btn btn-primary">
                                            <span class="btn-text"><?php esc_html_e('Subscribe', 'skyyrose'); ?></span>
                                            <svg class="btn-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                                <line x1="5" y1="12" x2="19" y2="12"></line>
                                                <polyline points="12 5 19 12 12 19"></polyline>
                                            </svg>
                                        </button>
                                    </div>
                                    <p class="newsletter-disclaimer">
                                        <?php esc_html_e('By subscribing, you agree to our Privacy Policy and consent to receive updates.', 'skyyrose'); ?>
                                    </p>
                                </form>
                            <?php endif; ?>
                        </div>
                    </div>
                    <!-- Decorative rose element -->
                    <div class="newsletter-rose-decoration" aria-hidden="true">
                        <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M60 10C60 10 75 25 75 45C75 65 60 80 60 80C60 80 45 65 45 45C45 25 60 10 60 10Z" fill="currentColor" opacity="0.1"/>
                            <path d="M60 30C60 30 80 40 85 60C90 80 75 95 75 95C75 95 55 85 50 65C45 45 60 30 60 30Z" fill="currentColor" opacity="0.15"/>
                            <path d="M60 30C60 30 40 40 35 60C30 80 45 95 45 95C45 95 65 85 70 65C75 45 60 30 60 30Z" fill="currentColor" opacity="0.15"/>
                            <circle cx="60" cy="60" r="8" fill="currentColor" opacity="0.2"/>
                        </svg>
                    </div>
                </div>
            </div>
        </section>

        <!-- Footer Links Grid -->
        <div class="footer-main">
            <div class="container">
                <div class="footer-grid">

                    <!-- Column 1: Shop -->
                    <div class="footer-column">
                        <h4 class="footer-column-title"><?php esc_html_e('Shop', 'skyyrose'); ?></h4>
                        <?php
                        if (has_nav_menu('footer-shop')) {
                            wp_nav_menu([
                                'theme_location' => 'footer-shop',
                                'menu_class'     => 'footer-menu',
                                'container'      => false,
                                'depth'          => 1,
                                'fallback_cb'    => false,
                            ]);
                        } else {
                            // Default fallback menu
                            ?>
                            <ul class="footer-menu">
                                <li><a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>"><?php esc_html_e('All Products', 'skyyrose'); ?></a></li>
                                <li><a href="<?php echo esc_url(home_url('/collection/black-rose/')); ?>"><?php esc_html_e('Black Rose', 'skyyrose'); ?></a></li>
                                <li><a href="<?php echo esc_url(home_url('/collection/signature/')); ?>"><?php esc_html_e('Signature', 'skyyrose'); ?></a></li>
                                <li><a href="<?php echo esc_url(home_url('/collection/love-hurts/')); ?>"><?php esc_html_e('Love Hurts', 'skyyrose'); ?></a></li>
                            </ul>
                            <?php
                        }
                        ?>
                    </div>

                    <!-- Column 2: Company -->
                    <div class="footer-column">
                        <h4 class="footer-column-title"><?php esc_html_e('Company', 'skyyrose'); ?></h4>
                        <?php
                        if (has_nav_menu('footer-company')) {
                            wp_nav_menu([
                                'theme_location' => 'footer-company',
                                'menu_class'     => 'footer-menu',
                                'container'      => false,
                                'depth'          => 1,
                                'fallback_cb'    => false,
                            ]);
                        } else {
                            ?>
                            <ul class="footer-menu">
                                <li><a href="<?php echo esc_url(home_url('/about/')); ?>"><?php esc_html_e('About Us', 'skyyrose'); ?></a></li>
                                <li><a href="<?php echo esc_url(home_url('/press/')); ?>"><?php esc_html_e('Press', 'skyyrose'); ?></a></li>
                                <li><a href="<?php echo esc_url(home_url('/careers/')); ?>"><?php esc_html_e('Careers', 'skyyrose'); ?></a></li>
                                <li><a href="<?php echo esc_url(home_url('/sustainability/')); ?>"><?php esc_html_e('Sustainability', 'skyyrose'); ?></a></li>
                            </ul>
                            <?php
                        }
                        ?>
                    </div>

                    <!-- Column 3: Support -->
                    <div class="footer-column">
                        <h4 class="footer-column-title"><?php esc_html_e('Support', 'skyyrose'); ?></h4>
                        <?php
                        if (has_nav_menu('footer-support')) {
                            wp_nav_menu([
                                'theme_location' => 'footer-support',
                                'menu_class'     => 'footer-menu',
                                'container'      => false,
                                'depth'          => 1,
                                'fallback_cb'    => false,
                            ]);
                        } else {
                            ?>
                            <ul class="footer-menu">
                                <li><a href="<?php echo esc_url(home_url('/faq/')); ?>"><?php esc_html_e('FAQ', 'skyyrose'); ?></a></li>
                                <li><a href="<?php echo esc_url(home_url('/shipping/')); ?>"><?php esc_html_e('Shipping', 'skyyrose'); ?></a></li>
                                <li><a href="<?php echo esc_url(home_url('/returns/')); ?>"><?php esc_html_e('Returns', 'skyyrose'); ?></a></li>
                                <li><a href="<?php echo esc_url(home_url('/contact/')); ?>"><?php esc_html_e('Contact', 'skyyrose'); ?></a></li>
                                <li><a href="<?php echo esc_url(home_url('/size-guide/')); ?>"><?php esc_html_e('Size Guide', 'skyyrose'); ?></a></li>
                            </ul>
                            <?php
                        }
                        ?>
                    </div>

                    <!-- Column 4: Legal -->
                    <div class="footer-column">
                        <h4 class="footer-column-title"><?php esc_html_e('Legal', 'skyyrose'); ?></h4>
                        <ul class="footer-menu">
                            <li><a href="<?php echo esc_url(get_privacy_policy_url()); ?>"><?php esc_html_e('Privacy Policy', 'skyyrose'); ?></a></li>
                            <li><a href="<?php echo esc_url(home_url('/terms/')); ?>"><?php esc_html_e('Terms of Service', 'skyyrose'); ?></a></li>
                            <li><a href="<?php echo esc_url(home_url('/cookies/')); ?>"><?php esc_html_e('Cookie Policy', 'skyyrose'); ?></a></li>
                        </ul>
                    </div>

                </div>
            </div>
        </div>

        <!-- Social & Payment Icons -->
        <div class="footer-bottom-section">
            <div class="container">

                <!-- Social Icons -->
                <div class="footer-social">
                    <span class="social-label"><?php esc_html_e('Follow Us', 'skyyrose'); ?></span>
                    <div class="social-icons">
                        <?php
                        $social_links = [
                            'instagram' => [
                                'url'   => get_theme_mod('skyyrose_social_instagram', 'https://instagram.com/skyyrose'),
                                'label' => __('Instagram', 'skyyrose'),
                                'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>',
                            ],
                            'tiktok' => [
                                'url'   => get_theme_mod('skyyrose_social_tiktok', 'https://tiktok.com/@skyyrose'),
                                'label' => __('TikTok', 'skyyrose'),
                                'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/></svg>',
                            ],
                            'pinterest' => [
                                'url'   => get_theme_mod('skyyrose_social_pinterest', 'https://pinterest.com/skyyrose'),
                                'label' => __('Pinterest', 'skyyrose'),
                                'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0a12 12 0 0 0-4.37 23.17c-.1-.94-.2-2.4.04-3.43.22-.94 1.4-5.94 1.4-5.94a4.15 4.15 0 0 1-.35-1.7c0-1.59.92-2.78 2.07-2.78.98 0 1.45.73 1.45 1.61 0 .98-.62 2.45-.95 3.81-.27 1.14.57 2.07 1.7 2.07 2.04 0 3.6-2.15 3.6-5.24 0-2.74-1.97-4.66-4.78-4.66a4.95 4.95 0 0 0-5.16 4.97c0 .98.38 2.04.85 2.61.1.12.11.22.08.34-.09.36-.28 1.14-.32 1.3-.05.21-.17.26-.39.16-1.46-.68-2.37-2.81-2.37-4.52 0-3.68 2.67-7.06 7.7-7.06 4.04 0 7.18 2.88 7.18 6.73 0 4.01-2.53 7.25-6.05 7.25-1.18 0-2.29-.61-2.67-1.34 0 0-.58 2.22-.73 2.76-.26 1.02-.98 2.3-1.46 3.08A12 12 0 1 0 12 0z"/></svg>',
                            ],
                        ];

                        foreach ($social_links as $platform => $data) :
                            if (!empty($data['url'])) :
                                ?>
                                <a
                                    href="<?php echo esc_url($data['url']); ?>"
                                    class="social-link social-link--<?php echo esc_attr($platform); ?>"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    aria-label="<?php echo esc_attr($data['label']); ?>"
                                >
                                    <?php echo $data['icon']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
                                </a>
                                <?php
                            endif;
                        endforeach;
                        ?>
                    </div>
                </div>

                <!-- Payment Icons -->
                <div class="footer-payment">
                    <span class="payment-label"><?php esc_html_e('Secure Payment', 'skyyrose'); ?></span>
                    <div class="payment-icons">
                        <span class="payment-icon" aria-label="<?php esc_attr_e('Visa', 'skyyrose'); ?>">
                            <svg width="40" height="24" viewBox="0 0 40 24" fill="none">
                                <rect width="40" height="24" rx="4" fill="#1A1F71"/>
                                <path d="M17.5 15.5H15.5L17 8.5H19L17.5 15.5Z" fill="white"/>
                                <path d="M25 8.5L23.2 13.3L23 12.2L22.3 9.2C22.3 9.2 22.2 8.5 21.3 8.5H18L18 8.7C18 8.7 19 8.9 20.1 9.6L22 15.5H24.2L27.2 8.5H25Z" fill="white"/>
                                <path d="M14.3 8.5L12 13.5L11.7 12L11 9.2C11 9.2 10.9 8.5 10 8.5H6L6 8.7C6 8.7 7.1 8.9 8.3 9.7L10.3 15.5H12.5L16 8.5H14.3Z" fill="white"/>
                                <path d="M29 15.5C29 15.5 28.5 13 28.5 13H26L25.3 15.5H23L26 8.6C26 8.6 26.2 8.5 26.5 8.5H28.5L31 15.5H29ZM27 11.5L28 8.5L28.5 11.5H27Z" fill="white"/>
                            </svg>
                        </span>
                        <span class="payment-icon" aria-label="<?php esc_attr_e('Mastercard', 'skyyrose'); ?>">
                            <svg width="40" height="24" viewBox="0 0 40 24" fill="none">
                                <rect width="40" height="24" rx="4" fill="#1A1A1A"/>
                                <circle cx="16" cy="12" r="7" fill="#EB001B"/>
                                <circle cx="24" cy="12" r="7" fill="#F79E1B"/>
                                <path d="M20 6.5C21.8 7.9 23 10.1 23 12.5C23 14.9 21.8 17.1 20 18.5C18.2 17.1 17 14.9 17 12.5C17 10.1 18.2 7.9 20 6.5Z" fill="#FF5F00"/>
                            </svg>
                        </span>
                        <span class="payment-icon" aria-label="<?php esc_attr_e('American Express', 'skyyrose'); ?>">
                            <svg width="40" height="24" viewBox="0 0 40 24" fill="none">
                                <rect width="40" height="24" rx="4" fill="#006FCF"/>
                                <path d="M8 9H10L11 11L12 9H14L12 12.5L14 16H12L11 14L10 16H8L10 12.5L8 9Z" fill="white"/>
                                <path d="M15 9H20V10.5H17V11.5H19.5V13H17V14.5H20V16H15V9Z" fill="white"/>
                                <path d="M21 9H23.5C25 9 26 10 26 11.5C26 12.7 25.3 13.5 24.2 13.8L26.5 16H24L22 14V16H21V9ZM23.3 12.5C23.8 12.5 24 12.1 24 11.7C24 11.3 23.8 11 23.3 11H23V12.5H23.3Z" fill="white"/>
                                <path d="M27 9H29V16H27V9Z" fill="white"/>
                                <path d="M30 9H32.5C34 9 35 9.8 35 11C35 11.8 34.5 12.3 34 12.5C34.6 12.7 35.2 13.3 35.2 14.2C35.2 15.3 34.2 16 32.7 16H30V9ZM32.3 12C32.7 12 33 11.7 33 11.4C33 11.1 32.7 10.8 32.3 10.8H32V12H32.3ZM32.4 14.5C32.9 14.5 33.2 14.2 33.2 13.8C33.2 13.4 32.9 13.1 32.4 13.1H32V14.5H32.4Z" fill="white"/>
                            </svg>
                        </span>
                        <span class="payment-icon" aria-label="<?php esc_attr_e('Apple Pay', 'skyyrose'); ?>">
                            <svg width="40" height="24" viewBox="0 0 40 24" fill="none">
                                <rect width="40" height="24" rx="4" fill="#1A1A1A"/>
                                <path d="M12.5 7.5C12.1 8 11.5 8.4 10.9 8.4C10.8 7.8 11.1 7.2 11.5 6.7C11.9 6.2 12.6 5.8 13.1 5.8C13.2 6.4 12.9 7 12.5 7.5ZM13.1 8.6C12.3 8.6 11.6 9.1 11.2 9.1C10.8 9.1 10.2 8.6 9.5 8.6C8.4 8.6 7.4 9.5 7.4 11.2C7.4 13.7 9.2 17.2 10.5 17.2C11 17.2 11.4 16.9 12 16.9C12.6 16.9 13 17.2 13.5 17.2C14.2 17.2 15.3 15 15.7 14C14.3 13.4 14.1 11.3 15.5 10.4C14.9 9.3 14 8.6 13.1 8.6Z" fill="white"/>
                                <path d="M18 9.5H20.5C22 9.5 23 10.5 23 12C23 13.5 22 14.5 20.5 14.5H19.5V17H18V9.5ZM20.3 13.3C21.2 13.3 21.7 12.8 21.7 12C21.7 11.2 21.2 10.7 20.3 10.7H19.5V13.3H20.3Z" fill="white"/>
                                <path d="M24 14C24 12.5 25.2 11.5 27 11.5C27.7 11.5 28.3 11.6 28.5 11.8V11.3C28.5 10.5 28 10 27.1 10C26.4 10 25.8 10.3 25.5 10.9L24.5 10.2C25 9.4 25.9 8.8 27.2 8.8C28.9 8.8 30 9.7 30 11.3V17H28.6V16.1C28.2 16.7 27.5 17.2 26.6 17.2C25.1 17.2 24 16.3 24 14.9V14ZM28.5 14.3V13C28.2 12.8 27.7 12.6 27.1 12.6C26.2 12.6 25.5 13.1 25.5 13.9C25.5 14.7 26.1 15.1 26.9 15.1C27.8 15.1 28.5 14.5 28.5 14.3Z" fill="white"/>
                                <path d="M31 16.2L31.7 15.1C32.2 15.5 32.9 15.8 33.5 15.8C34.2 15.8 34.5 15.5 34.5 15.1C34.5 14.1 31.2 14.5 31.2 12.3C31.2 11.2 32.1 10.3 33.8 10.3C34.7 10.3 35.5 10.6 36 11L35.4 12C35 11.7 34.4 11.4 33.8 11.4C33.2 11.4 32.8 11.7 32.8 12.1C32.8 13 36.1 12.5 36.1 14.9C36.1 16.1 35.1 17 33.5 17C32.4 17 31.5 16.6 31 16.2Z" fill="white"/>
                            </svg>
                        </span>
                        <span class="payment-icon" aria-label="<?php esc_attr_e('PayPal', 'skyyrose'); ?>">
                            <svg width="40" height="24" viewBox="0 0 40 24" fill="none">
                                <rect width="40" height="24" rx="4" fill="#1A1A1A"/>
                                <path d="M16.5 6H12L9 18H12L12.5 15H14.5C17.5 15 19.5 13 19.5 10C19.5 7.5 18 6 16.5 6ZM14.8 12.5H13L13.7 8.5H15.5C16.5 8.5 17 9.2 17 10C17 11.5 16 12.5 14.8 12.5Z" fill="#003087"/>
                                <path d="M27.5 6H23L20 18H23L23.5 15H25.5C28.5 15 30.5 13 30.5 10C30.5 7.5 29 6 27.5 6ZM25.8 12.5H24L24.7 8.5H26.5C27.5 8.5 28 9.2 28 10C28 11.5 27 12.5 25.8 12.5Z" fill="#0070BA"/>
                            </svg>
                        </span>
                        <span class="payment-icon" aria-label="<?php esc_attr_e('Shop Pay', 'skyyrose'); ?>">
                            <svg width="40" height="24" viewBox="0 0 40 24" fill="none">
                                <rect width="40" height="24" rx="4" fill="#5A31F4"/>
                                <path d="M9 10C9 9.4 9.4 9 10 9H11.5C12.9 9 14 10.1 14 11.5C14 12.9 12.9 14 11.5 14H10.5V16H9V10ZM11.3 12.5C11.9 12.5 12.3 12.1 12.3 11.5C12.3 10.9 11.9 10.5 11.3 10.5H10.5V12.5H11.3Z" fill="white"/>
                                <path d="M15 13.5C15 12 16.1 11 17.5 11C18.9 11 20 12 20 13.5V16H18.5V15.5C18.2 15.9 17.7 16.2 17 16.2C16 16.2 15 15.5 15 14.3C15 13.3 15.8 12.5 17 12.5C17.6 12.5 18.1 12.7 18.5 13V13.5C18.5 12.8 18.1 12.3 17.5 12.3C16.9 12.3 16.5 12.7 16.5 13.3C16.5 13.9 16.9 14.3 17.5 14.3C18.1 14.3 18.5 13.9 18.5 13.5C18.5 13.1 18.1 12.7 17.5 12.7C16.9 12.7 16.5 13.1 16.5 13.5V13.5ZM17.3 14.8C17.8 14.8 18.2 14.5 18.5 14V13.3C18.3 13.1 17.9 12.9 17.4 12.9C16.8 12.9 16.4 13.2 16.4 13.8C16.4 14.4 16.8 14.8 17.3 14.8Z" fill="white"/>
                                <path d="M21 16.5L21.8 15.5C22.2 15.8 22.7 16 23.2 16C23.7 16 24 15.8 24 15.4C24 14.6 21.2 14.8 21.2 13C21.2 12 22.1 11.2 23.5 11.2C24.3 11.2 25 11.5 25.5 11.9L24.8 12.8C24.4 12.5 24 12.3 23.5 12.3C23 12.3 22.7 12.5 22.7 12.9C22.7 13.6 25.5 13.4 25.5 15.3C25.5 16.4 24.6 17.1 23.2 17.1C22.3 17.1 21.5 16.8 21 16.5Z" fill="white"/>
                                <path d="M26 9H27.5V11.2H28V12.4H27.5V16H26V12.4H25.5V11.2H26V9Z" fill="white"/>
                                <path d="M29 13.5C29 12 30.1 11 31.5 11C32.9 11 34 12 34 13.5C34 15 32.9 16 31.5 16C30.1 16 29 15 29 13.5ZM32.5 13.5C32.5 12.8 32.1 12.3 31.5 12.3C30.9 12.3 30.5 12.8 30.5 13.5C30.5 14.2 30.9 14.7 31.5 14.7C32.1 14.7 32.5 14.2 32.5 13.5Z" fill="white"/>
                            </svg>
                        </span>
                    </div>
                </div>

            </div>
        </div>

        <!-- Copyright Bar -->
        <div class="footer-copyright">
            <div class="container">
                <div class="copyright-content">
                    <p class="copyright-text">
                        &copy; <?php echo esc_html(date('Y')); ?> <?php esc_html_e('SkyyRose. All rights reserved.', 'skyyrose'); ?>
                        <span class="copyright-tagline"><?php echo esc_html(get_theme_mod('skyyrose_footer_tagline', __('Where Love Meets Luxury.', 'skyyrose'))); ?></span>
                    </p>
                    <p class="copyright-location">
                        <?php echo esc_html(get_theme_mod('skyyrose_footer_location', __('Oakland, California', 'skyyrose'))); ?>
                    </p>
                </div>
            </div>
        </div>

    </footer>

    <?php wp_footer(); ?>

    <!-- Back to Top Script -->
    <script>
    (function() {
        const backToTop = document.getElementById('back-to-top');
        if (!backToTop) return;

        // Show/hide based on scroll position
        const toggleVisibility = () => {
            if (window.scrollY > 500) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        };

        window.addEventListener('scroll', toggleVisibility, { passive: true });
        toggleVisibility();

        // Smooth scroll to top
        backToTop.addEventListener('click', () => {
            if (typeof gsap !== 'undefined' && gsap.to) {
                gsap.to(window, {
                    duration: 1,
                    scrollTo: { y: 0 },
                    ease: 'power3.inOut'
                });
            } else {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
    })();
    </script>

</body>
</html>
