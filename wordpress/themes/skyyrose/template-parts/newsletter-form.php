<?php
/**
 * Template Part: Newsletter Signup Form
 *
 * Inline newsletter form for footer and other locations.
 *
 * @package SkyyRose
 * @version 1.0.0
 */

defined('ABSPATH') || exit;

$form_id = 'newsletter-' . wp_unique_id();
?>

<div class="newsletter-signup" id="<?php echo esc_attr($form_id); ?>">
    <div class="newsletter-content">
        <h3 class="newsletter-title">Stay in Bloom</h3>
        <p class="newsletter-text">Join the SkyyRose community for exclusive drops, style tips, and member-only offers.</p>
    </div>

    <form class="newsletter-form" action="<?php echo esc_url(admin_url('admin-ajax.php')); ?>" method="POST">
        <?php wp_nonce_field('skyyrose_email_capture', 'email_nonce'); ?>
        <input type="hidden" name="action" value="skyyrose_capture_email">
        <input type="hidden" name="source" value="footer">

        <div class="newsletter-input-group">
            <input
                type="email"
                name="email"
                placeholder="your@email.com"
                required
                autocomplete="email"
            >
            <button type="submit" class="btn btn--primary">
                <span class="btn-text">Subscribe</span>
                <span class="btn-loading" style="display: none;">
                    <svg class="spinner" width="18" height="18" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="32" stroke-linecap="round">
                            <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
                        </circle>
                    </svg>
                </span>
            </button>
        </div>

        <p class="newsletter-success" style="display: none;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            Welcome to the garden! Check your email.
        </p>
    </form>
</div>

<style>
.newsletter-signup {
    padding: 40px 0;
}

.newsletter-content {
    text-align: center;
    margin-bottom: 24px;
}

.newsletter-title {
    font-family: 'Playfair Display', serif;
    font-size: 24px;
    color: white;
    margin: 0 0 8px;
}

.newsletter-text {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    margin: 0;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
}

.newsletter-form {
    max-width: 500px;
    margin: 0 auto;
}

.newsletter-input-group {
    display: flex;
    gap: 10px;
}

.newsletter-input-group input[type="email"] {
    flex: 1;
    padding: 14px 18px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    color: white;
    font-size: 15px;
    transition: all 0.2s ease;
}

.newsletter-input-group input[type="email"]:focus {
    outline: none;
    border-color: var(--love-hurts, #B76E79);
    background: rgba(255, 255, 255, 0.08);
}

.newsletter-input-group input[type="email"]::placeholder {
    color: rgba(255, 255, 255, 0.4);
}

.newsletter-input-group .btn {
    padding: 14px 24px;
    background: var(--love-hurts, #B76E79);
    border: none;
    border-radius: 8px;
    color: white;
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
    display: flex;
    align-items: center;
    gap: 8px;
}

.newsletter-input-group .btn:hover {
    background: var(--love-hurts-light, #c98a93);
    transform: translateY(-1px);
}

.newsletter-input-group .btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
    transform: none;
}

.newsletter-success {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-top: 16px;
    padding: 12px;
    background: rgba(34, 197, 94, 0.1);
    border-radius: 8px;
    color: #22C55E;
    font-size: 14px;
}

@media (max-width: 480px) {
    .newsletter-input-group {
        flex-direction: column;
    }

    .newsletter-input-group .btn {
        width: 100%;
        justify-content: center;
    }
}
</style>

<script>
(function() {
    const form = document.querySelector('#<?php echo esc_js($form_id); ?> form');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const btn = form.querySelector('button[type="submit"]');
        const btnText = btn.querySelector('.btn-text');
        const btnLoading = btn.querySelector('.btn-loading');
        const inputGroup = form.querySelector('.newsletter-input-group');
        const success = form.querySelector('.newsletter-success');

        btn.disabled = true;
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline-flex';

        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (data.success) {
                inputGroup.style.display = 'none';
                success.style.display = 'flex';
                localStorage.setItem('skyyrose_email_subscribed', formData.get('email'));
            } else {
                alert(data.data || 'Something went wrong. Please try again.');
                btn.disabled = false;
                btnText.style.display = 'inline';
                btnLoading.style.display = 'none';
            }
        } catch (error) {
            console.error('Newsletter error:', error);
            alert('Something went wrong. Please try again.');
            btn.disabled = false;
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
        }
    });
})();
</script>
