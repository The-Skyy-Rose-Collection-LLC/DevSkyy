<?php
/**
 * Product Hotspot Widget
 * Interactive product markers with hover previews
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

namespace SkyyRose\Elementor;

if (!defined('ABSPATH')) exit;

class Product_Hotspot_Widget extends \Elementor\Widget_Base {

    public function get_name() {
        return 'skyyrose_product_hotspot';
    }

    public function get_title() {
        return esc_html__('Product Hotspot', 'skyyrose');
    }

    public function get_icon() {
        return 'eicon-pin';
    }

    public function get_categories() {
        return ['skyyrose'];
    }

    public function get_keywords() {
        return ['product', 'hotspot', 'marker', 'pin'];
    }

    protected function register_controls() {

        // ===== CONTENT TAB =====
        $this->start_controls_section(
            'content_section',
            [
                'label' => esc_html__('Hotspot Settings', 'skyyrose'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        // Product Selection
        $this->add_control(
            'product_id',
            [
                'label' => esc_html__('Select Product', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SELECT2,
                'options' => $this->get_woocommerce_products(),
                'label_block' => true,
            ]
        );

        // Hotspot Position X
        $this->add_responsive_control(
            'hotspot_position_x',
            [
                'label' => esc_html__('Position X (%)', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'size_units' => ['%'],
                'range' => [
                    '%' => [
                        'min' => 0,
                        'max' => 100,
                    ],
                ],
                'default' => [
                    'size' => 50,
                    'unit' => '%',
                ],
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-hotspot' => 'left: {{SIZE}}{{UNIT}};',
                ],
            ]
        );

        // Hotspot Position Y
        $this->add_responsive_control(
            'hotspot_position_y',
            [
                'label' => esc_html__('Position Y (%)', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'size_units' => ['%'],
                'range' => [
                    '%' => [
                        'min' => 0,
                        'max' => 100,
                    ],
                ],
                'default' => [
                    'size' => 50,
                    'unit' => '%',
                ],
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-hotspot' => 'top: {{SIZE}}{{UNIT}};',
                ],
            ]
        );

        // Pulse Animation
        $this->add_control(
            'enable_pulse',
            [
                'label' => esc_html__('Pulse Animation', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => esc_html__('Yes', 'skyyrose'),
                'label_off' => esc_html__('No', 'skyyrose'),
                'return_value' => 'yes',
                'default' => 'yes',
            ]
        );

        // Show Product Preview on Hover
        $this->add_control(
            'show_preview',
            [
                'label' => esc_html__('Show Preview on Hover', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => esc_html__('Yes', 'skyyrose'),
                'label_off' => esc_html__('No', 'skyyrose'),
                'return_value' => 'yes',
                'default' => 'yes',
            ]
        );

        $this->end_controls_section();

        // ===== STYLE TAB =====
        $this->start_controls_section(
            'style_section',
            [
                'label' => esc_html__('Hotspot Style', 'skyyrose'),
                'tab' => \Elementor\Controls_Manager::TAB_STYLE,
            ]
        );

        // Hotspot Size
        $this->add_responsive_control(
            'hotspot_size',
            [
                'label' => esc_html__('Size', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'size_units' => ['px'],
                'range' => [
                    'px' => [
                        'min' => 20,
                        'max' => 100,
                    ],
                ],
                'default' => [
                    'size' => 40,
                    'unit' => 'px',
                ],
                'selectors' => [
                    '{{WRAPPER}} .hotspot-marker' => 'width: {{SIZE}}{{UNIT}}; height: {{SIZE}}{{UNIT}};',
                ],
            ]
        );

        // Hotspot Color
        $this->add_control(
            'hotspot_color',
            [
                'label' => esc_html__('Color', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => '#D4AF37',
                'selectors' => [
                    '{{WRAPPER}} .hotspot-marker' => 'background-color: {{VALUE}}; border-color: {{VALUE}};',
                ],
            ]
        );

        // Preview Card Background
        $this->add_control(
            'preview_bg',
            [
                'label' => esc_html__('Preview Background', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => 'rgba(0, 0, 0, 0.9)',
                'selectors' => [
                    '{{WRAPPER}} .hotspot-preview' => 'background-color: {{VALUE}};',
                ],
                'condition' => [
                    'show_preview' => 'yes',
                ],
            ]
        );

        $this->end_controls_section();
    }

    protected function render() {
        $settings = $this->get_settings_for_display();
        $product_id = $settings['product_id'];

        if (!$product_id || !class_exists('WooCommerce')) {
            return;
        }

        $product = wc_get_product($product_id);
        if (!$product) {
            return;
        }

        $pulse_class = $settings['enable_pulse'] === 'yes' ? 'pulse' : '';
        ?>
        <div class="skyyrose-hotspot">
            <div class="hotspot-marker <?php echo esc_attr($pulse_class); ?>" data-product-id="<?php echo esc_attr($product_id); ?>">
                <span class="hotspot-icon">+</span>
            </div>

            <?php if ($settings['show_preview'] === 'yes'): ?>
                <div class="hotspot-preview">
                    <?php if ($product->get_image_id()): ?>
                        <div class="preview-image">
                            <?php echo wp_get_attachment_image($product->get_image_id(), 'skyyrose-thumbnail'); ?>
                        </div>
                    <?php endif; ?>

                    <div class="preview-content">
                        <h4 class="preview-title"><?php echo esc_html($product->get_name()); ?></h4>
                        <p class="preview-price"><?php echo $product->get_price_html(); ?></p>

                        <a href="<?php echo esc_url($product->get_permalink()); ?>" class="preview-link">
                            <?php echo esc_html__('View Product', 'skyyrose'); ?>
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                <path d="M6 12L10 8L6 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                        </a>
                    </div>
                </div>
            <?php endif; ?>
        </div>

        <style>
            .skyyrose-hotspot {
                position: absolute;
                z-index: 10;
            }

            .hotspot-marker {
                position: relative;
                border-radius: 50%;
                border: 2px solid;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }

            .hotspot-marker.pulse {
                animation: hotspot-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
            }

            .hotspot-marker:hover {
                transform: scale(1.2);
            }

            .hotspot-icon {
                color: #fff;
                font-size: 1.5em;
                font-weight: 300;
            }

            .hotspot-preview {
                position: absolute;
                left: 50%;
                top: 100%;
                transform: translateX(-50%) translateY(10px);
                min-width: 300px;
                padding: 1.5rem;
                border-radius: 8px;
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                opacity: 0;
                pointer-events: none;
                transition: all 0.3s ease;
            }

            .skyyrose-hotspot:hover .hotspot-preview {
                opacity: 1;
                pointer-events: auto;
                transform: translateX(-50%) translateY(0);
            }

            .preview-image img {
                width: 100%;
                height: auto;
                border-radius: 4px;
                margin-bottom: 1rem;
            }

            .preview-title {
                color: #fff;
                font-size: 1.1rem;
                margin-bottom: 0.5rem;
            }

            .preview-price {
                color: var(--signature-gold);
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 1rem;
            }

            .preview-link {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                color: #fff;
                text-decoration: none;
                font-size: 0.9rem;
                transition: color 0.3s ease;
            }

            .preview-link:hover {
                color: var(--signature-gold);
            }

            @keyframes hotspot-pulse {
                0%, 100% {
                    box-shadow: 0 0 0 0 currentColor;
                }
                50% {
                    box-shadow: 0 0 0 10px transparent;
                }
            }
        </style>
        <?php
    }

    private function get_woocommerce_products() {
        if (!class_exists('WooCommerce')) {
            return [];
        }

        $products = wc_get_products([
            'limit' => -1,
            'status' => 'publish',
            'orderby' => 'title',
            'order' => 'ASC',
        ]);

        $options = [];
        foreach ($products as $product) {
            $options[$product->get_id()] = $product->get_name();
        }

        return $options;
    }
}
