<?php
/**
 * Template Name: Contact
 * Description: Contact form and information
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

get_header();
?>

<style>
:root {
    --bg-dark: #000000;
    --signature-gold: #D4AF37;
    --love-hurts: #B76E79;
    --black-rose: #8B0000;
}

.contact-page {
    background: var(--bg-dark);
    color: #fff;
    min-height: 100vh;
    padding: 140px 0 80px;
}

.contact-page::before {
    content: '';
    position: fixed;
    inset: 0;
    background: radial-gradient(circle at 50% 30%, rgba(212, 175, 55, 0.08) 0%, transparent 60%);
    z-index: -1;
    pointer-events: none;
}

.contact-page::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%' height='100%' filter='url(%23noise)'/%3E%3C/svg%3E");
    opacity: 0.04;
    pointer-events: none;
    z-index: -1;
    mix-blend-mode: overlay;
}

.contact-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 2rem;
}

.contact-header {
    text-align: center;
    margin-bottom: 6rem;
}

.page-badge {
    display: inline-block;
    padding: 0.6rem 1.5rem;
    border: 1px solid rgba(212, 175, 55, 0.3);
    border-radius: 50px;
    font-size: 0.7rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--signature-gold);
    margin-bottom: 2rem;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(10px);
}

.page-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(3.5rem, 8vw, 5rem);
    margin-bottom: 1.5rem;
    background: linear-gradient(135deg, #fff 0%, var(--signature-gold) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.page-subtitle {
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.7);
    max-width: 700px;
    margin: 0 auto;
    line-height: 1.8;
}

.contact-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6rem;
    margin-bottom: 6rem;
}

/* Contact Form */
.contact-form {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 3rem;
}

.form-title {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    margin-bottom: 2rem;
    color: var(--signature-gold);
}

.form-group {
    margin-bottom: 2rem;
}

.form-label {
    display: block;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 0.8rem;
}

.form-input,
.form-textarea,
.form-select {
    width: 100%;
    padding: 1rem 1.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    color: #fff;
    font-size: 1rem;
    font-family: inherit;
    transition: all 0.3s ease;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
    outline: none;
    border-color: var(--signature-gold);
    box-shadow: 0 0 20px rgba(212, 175, 55, 0.1);
    background: rgba(255, 255, 255, 0.08);
}

.form-textarea {
    min-height: 150px;
    resize: vertical;
}

.form-select {
    cursor: pointer;
}

.submit-btn {
    width: 100%;
    padding: 1.5rem;
    background: var(--signature-gold);
    color: #000;
    border: none;
    border-radius: 4px;
    font-size: 0.9rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.4s ease;
    position: relative;
    overflow: hidden;
}

.submit-btn::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transform: translateX(-100%);
    transition: transform 0.6s ease;
}

.submit-btn:hover::before {
    transform: translateX(100%);
}

.submit-btn:hover {
    box-shadow: 0 0 30px var(--signature-gold);
    transform: translateY(-2px);
}

.submit-btn:disabled {
    background: #333;
    color: #666;
    cursor: not-allowed;
}

.form-message {
    margin-top: 1.5rem;
    padding: 1rem;
    border-radius: 4px;
    text-align: center;
    display: none;
}

.form-message.success {
    background: rgba(0, 255, 0, 0.1);
    border: 1px solid rgba(0, 255, 0, 0.3);
    color: #0f0;
    display: block;
}

.form-message.error {
    background: rgba(255, 0, 0, 0.1);
    border: 1px solid rgba(255, 0, 0, 0.3);
    color: #f00;
    display: block;
}

/* Contact Info */
.contact-info {
    display: flex;
    flex-direction: column;
    gap: 3rem;
}

.info-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 2.5rem;
    transition: all 0.4s ease;
}

.info-card:hover {
    border-color: var(--signature-gold);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    transform: translateY(-5px);
}

.info-icon {
    font-size: 2.5rem;
    margin-bottom: 1.5rem;
    display: block;
}

.info-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: var(--signature-gold);
}

.info-details {
    font-size: 1rem;
    line-height: 1.8;
    color: rgba(255, 255, 255, 0.8);
}

.info-details a {
    color: rgba(255, 255, 255, 0.8);
    text-decoration: none;
    transition: color 0.3s ease;
}

.info-details a:hover {
    color: var(--signature-gold);
}

.social-links {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
}

.social-link {
    width: 45px;
    height: 45px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    font-size: 1.2rem;
    transition: all 0.3s ease;
}

.social-link:hover {
    background: var(--signature-gold);
    border-color: var(--signature-gold);
    transform: translateY(-3px);
}

/* FAQ Section */
.faq-section {
    max-width: 900px;
    margin: 0 auto;
}

.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    text-align: center;
    margin-bottom: 1rem;
    color: var(--signature-gold);
}

.section-subtitle {
    text-align: center;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 4rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-size: 0.9rem;
}

.faq-item {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    margin-bottom: 1.5rem;
    overflow: hidden;
    transition: all 0.3s ease;
}

.faq-item:hover {
    border-color: rgba(212, 175, 55, 0.3);
}

.faq-question {
    padding: 1.5rem 2rem;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.3s ease;
}

.faq-question:hover {
    background: rgba(255, 255, 255, 0.05);
}

.faq-icon {
    transition: transform 0.3s ease;
    color: var(--signature-gold);
}

.faq-item.active .faq-icon {
    transform: rotate(45deg);
}

.faq-answer {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.4s ease, padding 0.4s ease;
}

.faq-item.active .faq-answer {
    max-height: 500px;
    padding: 0 2rem 2rem;
}

.faq-answer p {
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.8;
}

/* Responsive */
@media (max-width: 1024px) {
    .contact-grid {
        grid-template-columns: 1fr;
        gap: 3rem;
    }
}

@media (max-width: 768px) {
    .page-title {
        font-size: 3rem;
    }

    .contact-form,
    .info-card {
        padding: 2rem;
    }

    .section-title {
        font-size: 2.5rem;
    }
}
</style>

<div class="contact-page">
    <div class="contact-container">
        <!-- Header -->
        <div class="contact-header">
            <div class="page-badge">We're Here to Help</div>
            <h1 class="page-title">Get in Touch</h1>
            <p class="page-subtitle">
                Have questions about our collections, need styling advice, or want to collaborate?
                We'd love to hear from you.
            </p>
        </div>

        <!-- Contact Grid -->
        <div class="contact-grid">
            <!-- Contact Form -->
            <div class="contact-form">
                <h2 class="form-title">Send Us a Message</h2>
                <form id="contactForm" method="post" action="<?php echo esc_url(admin_url('admin-ajax.php')); ?>">
                    <input type="hidden" name="action" value="skyyrose_contact_form">
                    <?php wp_nonce_field('skyyrose_contact', 'contact_nonce'); ?>

                    <div class="form-group">
                        <label class="form-label" for="name">Your Name *</label>
                        <input type="text" id="name" name="name" class="form-input" required>
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="email">Email Address *</label>
                        <input type="email" id="email" name="email" class="form-input" required>
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="subject">Subject *</label>
                        <select id="subject" name="subject" class="form-select" required>
                            <option value="">Select a subject</option>
                            <option value="general">General Inquiry</option>
                            <option value="order">Order Status</option>
                            <option value="product">Product Question</option>
                            <option value="collaboration">Collaboration</option>
                            <option value="press">Press & Media</option>
                            <option value="other">Other</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="message">Message *</label>
                        <textarea id="message" name="message" class="form-textarea" required></textarea>
                    </div>

                    <button type="submit" class="submit-btn">Send Message</button>

                    <div class="form-message" id="formMessage"></div>
                </form>
            </div>

            <!-- Contact Info -->
            <div class="contact-info">
                <div class="info-card">
                    <span class="info-icon">✉️</span>
                    <h3 class="info-title">Email Us</h3>
                    <div class="info-details">
                        <p>For general inquiries:</p>
                        <p><a href="mailto:hello@skyyrose.co">hello@skyyrose.co</a></p>
                        <p style="margin-top: 1rem;">For customer support:</p>
                        <p><a href="mailto:support@skyyrose.co">support@skyyrose.co</a></p>
                    </div>
                </div>

                <div class="info-card">
                    <span class="info-icon">📍</span>
                    <h3 class="info-title">Location</h3>
                    <div class="info-details">
                        <p>Oakland, California</p>
                        <p>Where creativity meets the coast</p>
                    </div>
                </div>

                <div class="info-card">
                    <span class="info-icon">💬</span>
                    <h3 class="info-title">Follow Us</h3>
                    <div class="info-details">
                        <p>Stay connected and join our community</p>
                        <div class="social-links">
                            <a href="#" class="social-link" title="Instagram">📷</a>
                            <a href="#" class="social-link" title="Twitter">🐦</a>
                            <a href="#" class="social-link" title="TikTok">🎵</a>
                            <a href="#" class="social-link" title="Pinterest">📌</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- FAQ Section -->
        <div class="faq-section">
            <h2 class="section-title">Frequently Asked Questions</h2>
            <p class="section-subtitle">Quick Answers</p>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFaq(this)">
                    <span>What are your shipping times?</span>
                    <span class="faq-icon">+</span>
                </div>
                <div class="faq-answer">
                    <p>
                        Standard shipping typically takes 3-5 business days within the US. Express shipping
                        (1-2 business days) is available at checkout. International shipping times vary by
                        destination (7-14 business days).
                    </p>
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFaq(this)">
                    <span>What is your return policy?</span>
                    <span class="faq-icon">+</span>
                </div>
                <div class="faq-answer">
                    <p>
                        We offer a 30-day return window for unworn, unwashed items with original tags.
                        Items must be in original packaging. Free returns for US customers. International
                        customers pay return shipping.
                    </p>
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFaq(this)">
                    <span>How do I find my size?</span>
                    <span class="faq-icon">+</span>
                </div>
                <div class="faq-answer">
                    <p>
                        Each product page includes a detailed size chart. Our pieces run true to size,
                        but we recommend checking measurements for the best fit. Contact us at
                        hello@skyyrose.co if you need personalized sizing assistance.
                    </p>
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFaq(this)">
                    <span>Do you offer international shipping?</span>
                    <span class="faq-icon">+</span>
                </div>
                <div class="faq-answer">
                    <p>
                        Yes! We ship worldwide. Duties and taxes are calculated at checkout. International
                        orders may be subject to customs fees determined by your country.
                    </p>
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFaq(this)">
                    <span>Can I track my order?</span>
                    <span class="faq-icon">+</span>
                </div>
                <div class="faq-answer">
                    <p>
                        Absolutely. You'll receive a tracking number via email once your order ships.
                        You can also track orders by logging into your account or contacting
                        support@skyyrose.co.
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// FAQ Toggle
function toggleFaq(element) {
    const faqItem = element.parentElement;
    const allItems = document.querySelectorAll('.faq-item');

    // Close all other items
    allItems.forEach(item => {
        if (item !== faqItem && item.classList.contains('active')) {
            item.classList.remove('active');
        }
    });

    // Toggle current item
    faqItem.classList.toggle('active');
}

// Contact Form Submission
document.getElementById('contactForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const submitBtn = this.querySelector('.submit-btn');
    const formMessage = document.getElementById('formMessage');
    const formData = new FormData(this);

    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending...';
    formMessage.style.display = 'none';

    fetch(this.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            formMessage.className = 'form-message success';
            formMessage.textContent = 'Thank you! Your message has been sent. We\'ll get back to you within 24 hours.';
            this.reset();
        } else {
            formMessage.className = 'form-message error';
            formMessage.textContent = data.data || 'Oops! Something went wrong. Please try again or email us directly.';
        }
        formMessage.style.display = 'block';
    })
    .catch(error => {
        formMessage.className = 'form-message error';
        formMessage.textContent = 'Network error. Please try again or email us at hello@skyyrose.co';
        formMessage.style.display = 'block';
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send Message';
    });
});
</script>

<?php get_footer(); ?>
