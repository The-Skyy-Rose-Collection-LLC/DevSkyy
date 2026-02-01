<?php
/**
 * Pre-Order Form Widget
 * Email capture with Mailchimp/Klaviyo integration
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

namespace SkyyRose\Elementor;

if (!defined('ABSPATH')) exit;

class PreOrder_Form_Widget extends \Elementor\Widget_Base {

    public function get_name() {
        return 'skyyrose_preorder_form';
    }

    public function get_title() {
        return esc_html__('Pre-Order Form', 'skyyrose');
    }

    public function get_icon() {
        return 'eicon-form-horizontal';
    }

    public function get_categories() {
        return ['skyyrose'];
    }

    protected function register_controls() {

        // ===== CONTENT TAB =====
        $this->start_controls_section(
            'content_section',
            [
                'label' => esc_html__('Form Settings', 'skyyrose'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        // Form Title
        $this->add_control(
            'form_title',
            [
                'label' => esc_html__('Form Title', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::TEXT,
                'default' => esc_html__('Get Early Access', 'skyyrose'),
                'label_block' => true,
            ]
        );

        // Form Description
        $this->add_control(
            'form_description',
            [
                'label' => esc_html__('Description', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::TEXTAREA,
                'default' => esc_html__('Be the first to shop our exclusive collections. Reserve your spot now.', 'skyyrose'),
                'rows' => 3,
            ]
        );

        // Collection Filter
        $this->add_control(
            'collection_filter',
            [
                'label' => esc_html__('Collection Filter', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SELECT,
                'default' => 'all',
                'options' => [
                    'all' => esc_html__('All Collections', 'skyyrose'),
                    'black_rose' => esc_html__('Black Rose Only', 'skyyrose'),
                    'love_hurts' => esc_html__('Love Hurts Only', 'skyyrose'),
                    'signature' => esc_html__('Signature Only', 'skyyrose'),
                ],
            ]
        );

        // Email Service
        $this->add_control(
            'email_service',
            [
                'label' => esc_html__('Email Service', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SELECT,
                'default' => get_theme_mod('skyyrose_email_service', 'mailchimp'),
                'options' => [
                    'mailchimp' => esc_html__('Mailchimp', 'skyyrose'),
                    'klaviyo' => esc_html__('Klaviyo', 'skyyrose'),
                    'convertkit' => esc_html__('ConvertKit', 'skyyrose'),
                    'database' => esc_html__('WordPress Database', 'skyyrose'),
                ],
            ]
        );

        // Success Message
        $this->add_control(
            'success_message',
            [
                'label' => esc_html__('Success Message', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::TEXT,
                'default' => esc_html__('Welcome to the exclusive list! Check your email for confirmation.', 'skyyrose'),
                'label_block' => true,
            ]
        );

        $this->end_controls_section();

        // ===== PERKS SECTION =====
        $this->start_controls_section(
            'perks_section',
            [
                'label' => esc_html__('Member Perks', 'skyyrose'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        // Perks Repeater
        $repeater = new \Elementor\Repeater();

        $repeater->add_control(
            'perk_icon',
            [
                'label' => esc_html__('Icon', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::ICONS,
                'default' => [
                    'value' => 'fas fa-star',
                    'library' => 'solid',
                ],
            ]
        );

        $repeater->add_control(
            'perk_text',
            [
                'label' => esc_html__('Perk Text', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::TEXT,
                'default' => esc_html__('Exclusive early access', 'skyyrose'),
                'label_block' => true,
            ]
        );

        $this->add_control(
            'perks',
            [
                'label' => esc_html__('Member Perks', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::REPEATER,
                'fields' => $repeater->get_controls(),
                'default' => [
                    [
                        'perk_text' => esc_html__('Exclusive early access', 'skyyrose'),
                    ],
                    [
                        'perk_text' => esc_html__('Limited edition pieces', 'skyyrose'),
                    ],
                    [
                        'perk_text' => esc_html__('VIP pricing', 'skyyrose'),
                    ],
                ],
                'title_field' => '{{{ perk_text }}}',
            ]
        );

        $this->end_controls_section();

        // ===== STYLE TAB =====
        $this->start_controls_section(
            'style_section',
            [
                'label' => esc_html__('Form Style', 'skyyrose'),
                'tab' => \Elementor\Controls_Manager::TAB_STYLE,
            ]
        );

        // Background
        $this->add_control(
            'form_background',
            [
                'label' => esc_html__('Background', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => 'rgba(255, 255, 255, 0.05)',
                'selectors' => [
                    '{{WRAPPER}} .preorder-form-container' => 'background-color: {{VALUE}};',
                ],
            ]
        );

        // Button Color
        $this->add_control(
            'button_color',
            [
                'label' => esc_html__('Button Color', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => '#D4AF37',
                'selectors' => [
                    '{{WRAPPER}} .submit-btn' => 'background-color: {{VALUE}};',
                ],
            ]
        );

        $this->end_controls_section();
    }

    protected function render() {
        $settings = $this->get_settings_for_display();
        ?>
        <div class="preorder-form-container">
            <div class="form-header">
                <h3 class="form-title"><?php echo esc_html($settings['form_title']); ?></h3>
                <p class="form-description"><?php echo esc_html($settings['form_description']); ?></p>
            </div>

            <?php if (!empty($settings['perks'])): ?>
                <div class="member-perks">
                    <?php foreach ($settings['perks'] as $perk): ?>
                        <div class="perk-item">
                            <?php \Elementor\Icons_Manager::render_icon($perk['perk_icon'], ['aria-hidden' => 'true']); ?>
                            <span><?php echo esc_html($perk['perk_text']); ?></span>
                        </div>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>

            <form class="skyyrose-preorder-form" data-service="<?php echo esc_attr($settings['email_service']); ?>"
                  data-collection="<?php echo esc_attr($settings['collection_filter']); ?>">

                <div class="form-row">
                    <input type="text" name="first_name" placeholder="<?php echo esc_attr__('First Name', 'skyyrose'); ?>" required>
                    <input type="text" name="last_name" placeholder="<?php echo esc_attr__('Last Name', 'skyyrose'); ?>" required>
                </div>

                <div class="form-row">
                    <input type="email" name="email" placeholder="<?php echo esc_attr__('Email Address', 'skyyrose'); ?>" required>
                </div>

                <div class="form-row">
                    <label class="checkbox-label">
                        <input type="checkbox" name="sms_consent">
                        <span><?php echo esc_html__('Send me SMS updates (optional)', 'skyyrose'); ?></span>
                    </label>
                </div>

                <div class="form-row sms-input" style="display: none;">
                    <input type="tel" name="phone" placeholder="<?php echo esc_attr__('Phone Number', 'skyyrose'); ?>">
                </div>

                <button type="submit" class="submit-btn">
                    <span class="btn-text"><?php echo esc_html__('Reserve My Spot', 'skyyrose'); ?></span>
                    <span class="btn-loading" style="display: none;">
                        <svg class="spinner" width="20" height="20" viewBox="0 0 50 50">
                            <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="5"></circle>
                        </svg>
                    </span>
                </button>

                <div class="form-message" style="display: none;"></div>
            </form>

            <p class="form-disclaimer">
                <?php echo esc_html__('By signing up, you agree to receive marketing emails. Unsubscribe anytime.', 'skyyrose'); ?>
            </p>
        </div>

        <style>
            .preorder-form-container {
                max-width: 600px;
                margin: 0 auto;
                padding: 3rem;
                border-radius: 8px;
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }

            .form-header {
                text-align: center;
                margin-bottom: 2rem;
            }

            .form-title {
                font-family: var(--font-heading);
                font-size: 2rem;
                color: #fff;
                margin-bottom: 0.5rem;
            }

            .form-description {
                color: rgba(255, 255, 255, 0.7);
                font-size: 1rem;
            }

            .member-perks {
                display: grid;
                gap: 1rem;
                margin-bottom: 2rem;
                padding: 1.5rem;
                background: rgba(255, 255, 255, 0.03);
                border-radius: 4px;
            }

            .perk-item {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                color: var(--signature-gold);
                font-size: 0.9rem;
            }

            .perk-item i {
                font-size: 1.2rem;
            }

            .form-row {
                margin-bottom: 1rem;
            }

            .form-row input[type="text"],
            .form-row input[type="email"],
            .form-row input[type="tel"] {
                width: 100%;
                padding: 1rem;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                color: #fff;
                font-size: 1rem;
                transition: all 0.3s ease;
            }

            .form-row input:focus {
                outline: none;
                border-color: var(--signature-gold);
                background: rgba(255, 255, 255, 0.15);
            }

            .form-row input::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }

            .checkbox-label {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: rgba(255, 255, 255, 0.8);
                cursor: pointer;
            }

            .checkbox-label input[type="checkbox"] {
                width: 18px;
                height: 18px;
                cursor: pointer;
            }

            .submit-btn {
                width: 100%;
                padding: 1.2rem;
                background-color: var(--signature-gold);
                color: #000;
                border: none;
                border-radius: 4px;
                font-size: 1rem;
                font-weight: 600;
                letter-spacing: 1px;
                text-transform: uppercase;
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .submit-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 30px rgba(212, 175, 55, 0.3);
            }

            .submit-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }

            .spinner {
                animation: spin 1s linear infinite;
            }

            @keyframes spin {
                100% { transform: rotate(360deg); }
            }

            .form-message {
                margin-top: 1rem;
                padding: 1rem;
                border-radius: 4px;
                text-align: center;
            }

            .form-message.success {
                background: rgba(76, 175, 80, 0.2);
                color: #4CAF50;
                border: 1px solid #4CAF50;
            }

            .form-message.error {
                background: rgba(244, 67, 54, 0.2);
                color: #f44336;
                border: 1px solid #f44336;
            }

            .form-disclaimer {
                margin-top: 1rem;
                text-align: center;
                color: rgba(255, 255, 255, 0.5);
                font-size: 0.75rem;
            }
        </style>

        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.querySelector('.skyyrose-preorder-form');
            const smsCheckbox = form.querySelector('input[name="sms_consent"]');
            const smsInput = form.querySelector('.sms-input');

            smsCheckbox.addEventListener('change', function() {
                smsInput.style.display = this.checked ? 'block' : 'none';
            });

            form.addEventListener('submit', async function(e) {
                e.preventDefault();

                const submitBtn = form.querySelector('.submit-btn');
                const btnText = submitBtn.querySelector('.btn-text');
                const btnLoading = submitBtn.querySelector('.btn-loading');
                const messageDiv = form.querySelector('.form-message');

                submitBtn.disabled = true;
                btnText.style.display = 'none';
                btnLoading.style.display = 'inline-block';

                const formData = new FormData(form);
                formData.append('action', 'skyyrose_preorder_submit');
                formData.append('nonce', '<?php echo wp_create_nonce("skyyrose_preorder"); ?>');

                try {
                    const response = await fetch('<?php echo admin_url("admin-ajax.php"); ?>', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();

                    messageDiv.style.display = 'block';
                    if (data.success) {
                        messageDiv.className = 'form-message success';
                        messageDiv.textContent = '<?php echo esc_js($settings["success_message"]); ?>';
                        form.reset();
                    } else {
                        messageDiv.className = 'form-message error';
                        messageDiv.textContent = data.data || '<?php echo esc_js__("Something went wrong. Please try again.", "skyyrose"); ?>';
                    }
                } catch (error) {
                    messageDiv.style.display = 'block';
                    messageDiv.className = 'form-message error';
                    messageDiv.textContent = '<?php echo esc_js__("Network error. Please try again.", "skyyrose"); ?>';
                } finally {
                    submitBtn.disabled = false;
                    btnText.style.display = 'inline-block';
                    btnLoading.style.display = 'none';
                }
            });
        });
        </script>
        <?php
    }
}
