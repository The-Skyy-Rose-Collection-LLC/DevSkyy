<?php
/**
 * Template Part: Email Capture Popup
 *
 * Luxurious email capture popup with brand styling.
 * Stores in WooCommerce or sends to email provider.
 *
 * @package SkyyRose
 * @version 1.0.0
 */

defined('ABSPATH') || exit;

$collection = get_theme_mod('skyyrose_popup_collection', 'signature');
$discount = get_theme_mod('skyyrose_popup_discount', '15');
$delay = get_theme_mod('skyyrose_popup_delay', 5000);
?>

<!-- Email Capture Popup -->
<div class="skyyrose-popup-overlay" id="emailPopupOverlay" style="display: none;">
    <div class="skyyrose-popup" data-collection="<?php echo esc_attr($collection); ?>">
        <button type="button" class="popup-close" id="popupClose" aria-label="Close popup">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </button>

        <div class="popup-content">
            <div class="popup-visual">
                <div class="popup-rose-icon">
                    <svg width="80" height="80" viewBox="0 0 100 100" fill="none">
                        <path d="M50 10C50 10 60 25 60 40C60 50 55 55 50 60C45 55 40 50 40 40C40 25 50 10 50 10Z" fill="currentColor" opacity="0.8"/>
                        <path d="M30 30C30 30 45 35 50 50C45 55 35 55 25 50C20 40 30 30 30 30Z" fill="currentColor" opacity="0.6"/>
                        <path d="M70 30C70 30 55 35 50 50C55 55 65 55 75 50C80 40 70 30 70 30Z" fill="currentColor" opacity="0.6"/>
                        <path d="M50 55C50 55 50 70 50 85" stroke="currentColor" stroke-width="4" opacity="0.5"/>
                        <path d="M40 70C40 70 45 65 50 70" stroke="currentColor" stroke-width="2" opacity="0.4"/>
                        <path d="M60 75C60 75 55 70 50 75" stroke="currentColor" stroke-width="2" opacity="0.4"/>
                    </svg>
                </div>
                <div class="popup-particles"></div>
            </div>

            <div class="popup-text">
                <span class="popup-eyebrow">Exclusive Access</span>
                <h2 class="popup-title">Join the Rose Garden</h2>
                <p class="popup-description">
                    Get <strong><?php echo esc_html($discount); ?>% off</strong> your first order,
                    early access to new collections, and exclusive member-only offers.
                </p>
            </div>

            <form class="popup-form" id="emailCaptureForm" action="<?php echo esc_url(admin_url('admin-ajax.php')); ?>" method="POST">
                <?php wp_nonce_field('skyyrose_email_capture', 'email_nonce'); ?>
                <input type="hidden" name="action" value="skyyrose_capture_email">
                <input type="hidden" name="source" value="popup">

                <div class="form-group">
                    <input
                        type="email"
                        name="email"
                        id="popupEmail"
                        placeholder="Enter your email"
                        required
                        autocomplete="email"
                    >
                    <button type="submit" class="btn btn--primary">
                        <span class="btn-text">Unlock <?php echo esc_html($discount); ?>% Off</span>
                        <span class="btn-loading" style="display: none;">
                            <svg class="spinner" width="20" height="20" viewBox="0 0 24 24">
                                <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="32" stroke-linecap="round">
                                    <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
                                </circle>
                            </svg>
                        </span>
                    </button>
                </div>

                <p class="form-note">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                    We respect your privacy. Unsubscribe anytime.
                </p>
            </form>

            <div class="popup-success" id="popupSuccess" style="display: none;">
                <div class="success-icon">
                    <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                </div>
                <h3>Welcome to the Garden!</h3>
                <p>Check your email for your <strong><?php echo esc_html($discount); ?>% discount code</strong>.</p>
                <p class="discount-code" id="discountCode"></p>
            </div>
        </div>
    </div>
</div>

<style>
.skyyrose-popup-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(8px);
    z-index: 99999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.4s ease, visibility 0.4s ease;
}

.skyyrose-popup-overlay.is-visible {
    opacity: 1;
    visibility: visible;
}

.skyyrose-popup {
    position: relative;
    width: 100%;
    max-width: 480px;
    background: linear-gradient(145deg, #1A1A1A 0%, #0D0D0D 100%);
    border-radius: 24px;
    padding: 48px 40px;
    text-align: center;
    transform: scale(0.9) translateY(20px);
    transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8);
}

.skyyrose-popup-overlay.is-visible .skyyrose-popup {
    transform: scale(1) translateY(0);
}

/* Collection-specific accent colors */
.skyyrose-popup[data-collection="signature"] {
    --popup-accent: #D4AF37;
}

.skyyrose-popup[data-collection="black-rose"] {
    --popup-accent: #8B0000;
}

.skyyrose-popup[data-collection="love-hurts"] {
    --popup-accent: #B76E79;
}

.popup-close {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 40px;
    height: 40px;
    background: rgba(255, 255, 255, 0.05);
    border: none;
    border-radius: 50%;
    color: rgba(255, 255, 255, 0.5);
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}

.popup-close:hover {
    background: rgba(255, 255, 255, 0.1);
    color: white;
}

.popup-visual {
    position: relative;
    margin-bottom: 24px;
}

.popup-rose-icon {
    color: var(--popup-accent, #B76E79);
    animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.05); opacity: 0.9; }
}

.popup-particles {
    position: absolute;
    inset: 0;
    pointer-events: none;
}

.popup-eyebrow {
    display: inline-block;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--popup-accent, #B76E79);
    margin-bottom: 12px;
}

.popup-title {
    font-family: 'Playfair Display', serif;
    font-size: 32px;
    font-weight: 700;
    color: white;
    margin: 0 0 16px;
    line-height: 1.2;
}

.popup-description {
    font-size: 16px;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.6;
    margin: 0 0 32px;
}

.popup-description strong {
    color: var(--popup-accent, #B76E79);
}

.popup-form .form-group {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
}

.popup-form input[type="email"] {
    flex: 1;
    padding: 16px 20px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    color: white;
    font-size: 16px;
    transition: all 0.2s ease;
}

.popup-form input[type="email"]:focus {
    outline: none;
    border-color: var(--popup-accent, #B76E79);
    background: rgba(255, 255, 255, 0.08);
}

.popup-form input[type="email"]::placeholder {
    color: rgba(255, 255, 255, 0.4);
}

.popup-form .btn {
    padding: 16px 24px;
    background: var(--popup-accent, #B76E79);
    border: none;
    border-radius: 12px;
    color: white;
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
}

.popup-form .btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(183, 110, 121, 0.4);
}

.popup-form .btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
    transform: none;
}

.form-note {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
    margin: 0;
}

.popup-success {
    padding: 20px 0;
}

.success-icon {
    color: #22C55E;
    margin-bottom: 20px;
}

.success-icon svg {
    animation: checkmark 0.6s ease-out;
}

@keyframes checkmark {
    0% { transform: scale(0); opacity: 0; }
    50% { transform: scale(1.2); }
    100% { transform: scale(1); opacity: 1; }
}

.popup-success h3 {
    font-family: 'Playfair Display', serif;
    font-size: 24px;
    color: white;
    margin: 0 0 12px;
}

.popup-success p {
    color: rgba(255, 255, 255, 0.7);
    margin: 0 0 16px;
}

.discount-code {
    display: inline-block;
    padding: 12px 24px;
    background: rgba(255, 255, 255, 0.1);
    border: 2px dashed var(--popup-accent, #B76E79);
    border-radius: 8px;
    font-family: monospace;
    font-size: 20px;
    font-weight: 700;
    color: var(--popup-accent, #B76E79);
    letter-spacing: 2px;
}

@media (max-width: 520px) {
    .skyyrose-popup {
        padding: 32px 24px;
    }

    .popup-title {
        font-size: 26px;
    }

    .popup-form .form-group {
        flex-direction: column;
    }

    .popup-form .btn {
        width: 100%;
    }
}
</style>

<script>
(function() {
    const overlay = document.getElementById('emailPopupOverlay');
    const closeBtn = document.getElementById('popupClose');
    const form = document.getElementById('emailCaptureForm');
    const successEl = document.getElementById('popupSuccess');
    const codeEl = document.getElementById('discountCode');
    const delay = <?php echo intval($delay); ?>;

    // Check if already subscribed or dismissed
    function hasInteracted() {
        return localStorage.getItem('skyyrose_email_subscribed') ||
               sessionStorage.getItem('skyyrose_popup_dismissed');
    }

    // Show popup after delay
    function showPopup() {
        if (hasInteracted()) return;

        overlay.style.display = 'flex';
        requestAnimationFrame(function() {
            overlay.classList.add('is-visible');
        });
        document.body.style.overflow = 'hidden';
    }

    // Hide popup
    function hidePopup() {
        overlay.classList.remove('is-visible');
        setTimeout(function() {
            overlay.style.display = 'none';
        }, 400);
        document.body.style.overflow = '';
        sessionStorage.setItem('skyyrose_popup_dismissed', '1');
    }

    // Close button
    if (closeBtn) {
        closeBtn.addEventListener('click', hidePopup);
    }

    // Click outside to close
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            hidePopup();
        }
    });

    // Escape key to close
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && overlay.classList.contains('is-visible')) {
            hidePopup();
        }
    });

    // Form submission
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            const btn = form.querySelector('button[type="submit"]');
            const btnText = btn.querySelector('.btn-text');
            const btnLoading = btn.querySelector('.btn-loading');
            const email = form.querySelector('input[name="email"]').value;

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
                    // Show success
                    form.style.display = 'none';
                    document.querySelector('.popup-text').style.display = 'none';
                    successEl.style.display = 'block';

                    if (data.data && data.data.code) {
                        codeEl.textContent = data.data.code;
                    }

                    localStorage.setItem('skyyrose_email_subscribed', email);

                    // Auto-close after 5 seconds
                    setTimeout(hidePopup, 5000);
                } else {
                    alert(data.data || 'Something went wrong. Please try again.');
                    btn.disabled = false;
                    btnText.style.display = 'inline';
                    btnLoading.style.display = 'none';
                }
            } catch (error) {
                console.error('Email capture error:', error);
                alert('Something went wrong. Please try again.');
                btn.disabled = false;
                btnText.style.display = 'inline';
                btnLoading.style.display = 'none';
            }
        });
    }

    // Show popup after delay (only on first visit)
    if (delay > 0) {
        setTimeout(showPopup, delay);
    }

    // Also show on exit intent (desktop only)
    if (window.innerWidth > 768) {
        document.addEventListener('mouseout', function(e) {
            if (e.clientY < 10 && !hasInteracted()) {
                showPopup();
            }
        });
    }
})();
</script>
