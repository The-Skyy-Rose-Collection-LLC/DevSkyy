<?php
/**
 * Template Name: Contact Page
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;

get_header();

// Check if Elementor is active and page is built with Elementor
$is_elementor = false;
if (did_action('elementor/loaded')) {
    $document = \Elementor\Plugin::$instance->documents->get(get_the_ID());
    $is_elementor = $document && $document->is_built_with_elementor();
}

if ($is_elementor) {
    // Let Elementor render the content
    while (have_posts()) : the_post();
        the_content();
    endwhile;
} else {
    // Use theme template as fallback
?>

<section class="contact-section">
    <div class="container">
        <div class="contact-grid">
            <div class="contact-info">
                <span class="section-label">Get in Touch</span>
                <h2>We'd Love to Hear From You</h2>
                <p>Whether you have a question about our products, need styling advice, or just want to say hello, we're here for you.</p>

                <div class="contact-details">
                    <div class="contact-item">
                        <span class="contact-icon">📍</span>
                        <div>
                            <h4>Location</h4>
                            <p>Oakland, California</p>
                        </div>
                    </div>

                    <div class="contact-item">
                        <span class="contact-icon">✉️</span>
                        <div>
                            <h4>Email</h4>
                            <a href="mailto:hello@skyyrose.com">hello@skyyrose.com</a>
                        </div>
                    </div>

                    <div class="contact-item">
                        <span class="contact-icon">📱</span>
                        <div>
                            <h4>Social</h4>
                            <p>@skyyrose on Instagram, TikTok, Twitter</p>
                        </div>
                    </div>

                    <div class="contact-item">
                        <span class="contact-icon">⏰</span>
                        <div>
                            <h4>Response Time</h4>
                            <p>We typically respond within 24 hours</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="contact-form-wrapper">
                <form class="contact-form" id="contactForm">
                    <?php wp_nonce_field('skyyrose_contact', 'contact_nonce'); ?>

                    <div class="form-group">
                        <label for="contact_name"><?php esc_html_e('Name', 'skyyrose'); ?></label>
                        <input type="text" id="contact_name" name="name" required>
                    </div>

                    <div class="form-group">
                        <label for="contact_email"><?php esc_html_e('Email', 'skyyrose'); ?></label>
                        <input type="email" id="contact_email" name="email" required>
                    </div>

                    <div class="form-group">
                        <label for="contact_subject"><?php esc_html_e('Subject', 'skyyrose'); ?></label>
                        <input type="text" id="contact_subject" name="subject" required>
                    </div>

                    <div class="form-group">
                        <label for="contact_message"><?php esc_html_e('Message', 'skyyrose'); ?></label>
                        <textarea id="contact_message" name="message" rows="5" required></textarea>
                    </div>

                    <button type="submit" class="btn btn-primary"><?php esc_html_e('Send Message', 'skyyrose'); ?></button>
                </form>
            </div>
        </div>
    </div>
</section>

<section class="faq-section">
    <div class="container">
        <div class="section-header">
            <span class="section-label">FAQ</span>
            <h2 class="section-title">Frequently Asked Questions</h2>
        </div>

        <div class="faq-grid">
            <div class="accordion">
                <div class="accordion-item">
                    <button class="accordion-header" aria-expanded="false">
                        <h4>What is your return policy?</h4>
                        <span class="accordion-icon">+</span>
                    </button>
                    <div class="accordion-content">
                        <div class="accordion-content-inner">
                            <p>We offer a 30-day return policy on all unworn items with original tags attached. Free returns on domestic orders.</p>
                        </div>
                    </div>
                </div>

                <div class="accordion-item">
                    <button class="accordion-header" aria-expanded="false">
                        <h4>How long does shipping take?</h4>
                        <span class="accordion-icon">+</span>
                    </button>
                    <div class="accordion-content">
                        <div class="accordion-content-inner">
                            <p>Standard shipping takes 5-7 business days. Express shipping (2-3 business days) is available at checkout. Free shipping on orders over $150.</p>
                        </div>
                    </div>
                </div>

                <div class="accordion-item">
                    <button class="accordion-header" aria-expanded="false">
                        <h4>How do I find my size?</h4>
                        <span class="accordion-icon">+</span>
                    </button>
                    <div class="accordion-content">
                        <div class="accordion-content-inner">
                            <p>Check our size guide on each product page. Our items generally run true to size, but each collection has specific fit notes. When in doubt, size up for a relaxed fit.</p>
                        </div>
                    </div>
                </div>

                <div class="accordion-item">
                    <button class="accordion-header" aria-expanded="false">
                        <h4>Do you ship internationally?</h4>
                        <span class="accordion-icon">+</span>
                    </button>
                    <div class="accordion-content">
                        <div class="accordion-content-inner">
                            <p>Yes! We ship worldwide. International shipping rates and delivery times are calculated at checkout based on your location.</p>
                        </div>
                    </div>
                </div>

                <div class="accordion-item">
                    <button class="accordion-header" aria-expanded="false">
                        <h4>Are your products ethically made?</h4>
                        <span class="accordion-icon">+</span>
                    </button>
                    <div class="accordion-content">
                        <div class="accordion-content-inner">
                            <p>Absolutely. We partner with manufacturers who share our commitment to fair wages, safe working conditions, and sustainable practices. Quality over quantity, always.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<script>
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        // Contact form submission
        var form = document.getElementById('contactForm');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();

                var submitBtn = form.querySelector('button[type="submit"]');
                var originalText = submitBtn.textContent;
                submitBtn.disabled = true;
                submitBtn.textContent = 'Sending...';

                var formData = new FormData(form);
                formData.append('action', 'skyyrose_contact');

                fetch(window.skyyrose ? window.skyyrose.ajax_url : '/wp-admin/admin-ajax.php', {
                    method: 'POST',
                    body: formData
                })
                .then(function(response) {
                    return response.json();
                })
                .then(function(data) {
                    if (data.success) {
                        window.SkyyRose.showToast(data.data.message || 'Message sent successfully!');
                        form.reset();
                    } else {
                        window.SkyyRose.showToast(data.data.message || 'Failed to send message.', 'error');
                    }
                })
                .catch(function() {
                    window.SkyyRose.showToast('Something went wrong. Please try again.', 'error');
                })
                .finally(function() {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                });
            });
        }

        // Accordions
        document.querySelectorAll('.accordion-header').forEach(function(header) {
            header.addEventListener('click', function() {
                var item = header.parentElement;
                var isOpen = item.classList.contains('open');

                item.classList.toggle('open');
                header.setAttribute('aria-expanded', !isOpen);
            });
        });
    });
})();
</script>

<?php
} // End else (non-Elementor fallback)

get_footer();
?>
