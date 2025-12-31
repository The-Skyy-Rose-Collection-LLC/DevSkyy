<?php
/**
 * SkyyRose 3D Experience Elementor Widget
 *
 * @package SkyyRose_3D_Experience
 * @since 2.0.0
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Elementor widget for SkyyRose 3D experiences
 */
class SkyyRose_3D_Elementor_Widget extends \Elementor\Widget_Base {

    /**
     * Get widget name
     */
    public function get_name(): string {
        return 'skyyrose_3d_experience';
    }

    /**
     * Get widget title
     */
    public function get_title(): string {
        return __('SkyyRose 3D Experience', 'skyyrose-3d');
    }

    /**
     * Get widget icon
     */
    public function get_icon(): string {
        return 'eicon-cube';
    }

    /**
     * Get widget categories
     */
    public function get_categories(): array {
        return ['skyyrose', 'general'];
    }

    /**
     * Get widget keywords
     */
    public function get_keywords(): array {
        return ['3d', 'product', 'experience', 'skyyrose', 'three.js', 'model'];
    }

    /**
     * Get script dependencies
     */
    public function get_script_depends(): array {
        return ['three-js', 'skyyrose-3d'];
    }

    /**
     * Get style dependencies
     */
    public function get_style_depends(): array {
        return ['skyyrose-3d'];
    }

    /**
     * Register widget controls
     */
    protected function register_controls(): void {
        // Content Section
        $this->start_controls_section(
            'content_section',
            [
                'label' => __('Experience Settings', 'skyyrose-3d'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        $this->add_control(
            'collection',
            [
                'label' => __('Collection', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::SELECT,
                'default' => 'black_rose',
                'options' => SkyyRose_3D_Experience::COLLECTIONS,
                'description' => __('Select the 3D collection experience to display.', 'skyyrose-3d'),
            ]
        );

        $this->add_responsive_control(
            'height',
            [
                'label' => __('Height', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'size_units' => ['px', 'vh', '%'],
                'range' => [
                    'px' => [
                        'min' => 300,
                        'max' => 1200,
                        'step' => 50,
                    ],
                    'vh' => [
                        'min' => 30,
                        'max' => 100,
                    ],
                    '%' => [
                        'min' => 30,
                        'max' => 100,
                    ],
                ],
                'default' => [
                    'unit' => 'px',
                    'size' => 600,
                ],
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-3d-container' => 'height: {{SIZE}}{{UNIT}};',
                ],
            ]
        );

        $this->add_control(
            'enable_fullscreen',
            [
                'label' => __('Enable Fullscreen', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => __('Yes', 'skyyrose-3d'),
                'label_off' => __('No', 'skyyrose-3d'),
                'return_value' => 'yes',
                'default' => 'yes',
            ]
        );

        $this->end_controls_section();

        // Visual Effects Section
        $this->start_controls_section(
            'effects_section',
            [
                'label' => __('Visual Effects', 'skyyrose-3d'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        $this->add_control(
            'enable_bloom',
            [
                'label' => __('Bloom Effect', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => __('Yes', 'skyyrose-3d'),
                'label_off' => __('No', 'skyyrose-3d'),
                'return_value' => 'yes',
                'default' => 'yes',
            ]
        );

        $this->add_control(
            'bloom_strength',
            [
                'label' => __('Bloom Strength', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'range' => [
                    'px' => [
                        'min' => 0,
                        'max' => 2,
                        'step' => 0.1,
                    ],
                ],
                'default' => [
                    'size' => 0.5,
                ],
                'condition' => [
                    'enable_bloom' => 'yes',
                ],
            ]
        );

        $this->add_control(
            'background_color',
            [
                'label' => __('Background Color', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => '#1A1A1A',
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-3d-container' => 'background-color: {{VALUE}};',
                ],
            ]
        );

        $this->add_control(
            'particle_count',
            [
                'label' => __('Particle Count', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::NUMBER,
                'min' => 0,
                'max' => 5000,
                'step' => 100,
                'default' => 1000,
            ]
        );

        $this->end_controls_section();

        // Interactivity Section
        $this->start_controls_section(
            'interactivity_section',
            [
                'label' => __('Interactivity', 'skyyrose-3d'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        $this->add_control(
            'enable_product_cards',
            [
                'label' => __('Show Product Cards', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => __('Yes', 'skyyrose-3d'),
                'label_off' => __('No', 'skyyrose-3d'),
                'return_value' => 'yes',
                'default' => 'yes',
            ]
        );

        $this->add_control(
            'enable_ar',
            [
                'label' => __('Enable AR Preview', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => __('Yes', 'skyyrose-3d'),
                'label_off' => __('No', 'skyyrose-3d'),
                'return_value' => 'yes',
                'default' => 'no',
                'description' => __('Allow users to view products in AR on supported devices.', 'skyyrose-3d'),
            ]
        );

        $this->add_control(
            'cursor_spotlight',
            [
                'label' => __('Cursor Spotlight', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => __('Yes', 'skyyrose-3d'),
                'label_off' => __('No', 'skyyrose-3d'),
                'return_value' => 'yes',
                'default' => 'yes',
            ]
        );

        $this->end_controls_section();

        // Products Section
        $this->start_controls_section(
            'products_section',
            [
                'label' => __('Products', 'skyyrose-3d'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        $this->add_control(
            'product_source',
            [
                'label' => __('Product Source', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::SELECT,
                'default' => 'auto',
                'options' => [
                    'auto' => __('Auto (from collection)', 'skyyrose-3d'),
                    'woocommerce' => __('WooCommerce Products', 'skyyrose-3d'),
                    'manual' => __('Manual Selection', 'skyyrose-3d'),
                ],
            ]
        );

        $this->add_control(
            'woo_category',
            [
                'label' => __('WooCommerce Category', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::SELECT2,
                'multiple' => false,
                'options' => $this->get_woo_categories(),
                'condition' => [
                    'product_source' => 'woocommerce',
                ],
            ]
        );

        $this->add_control(
            'manual_products',
            [
                'label' => __('Product IDs', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::TEXT,
                'placeholder' => '123, 456, 789',
                'description' => __('Comma-separated product IDs', 'skyyrose-3d'),
                'condition' => [
                    'product_source' => 'manual',
                ],
            ]
        );

        $this->end_controls_section();

        // Style Section
        $this->start_controls_section(
            'style_section',
            [
                'label' => __('Container Style', 'skyyrose-3d'),
                'tab' => \Elementor\Controls_Manager::TAB_STYLE,
            ]
        );

        $this->add_group_control(
            \Elementor\Group_Control_Border::get_type(),
            [
                'name' => 'container_border',
                'selector' => '{{WRAPPER}} .skyyrose-3d-container',
            ]
        );

        $this->add_responsive_control(
            'container_border_radius',
            [
                'label' => __('Border Radius', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::DIMENSIONS,
                'size_units' => ['px', '%'],
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-3d-container' => 'border-radius: {{TOP}}{{UNIT}} {{RIGHT}}{{UNIT}} {{BOTTOM}}{{UNIT}} {{LEFT}}{{UNIT}};',
                ],
            ]
        );

        $this->add_group_control(
            \Elementor\Group_Control_Box_Shadow::get_type(),
            [
                'name' => 'container_box_shadow',
                'selector' => '{{WRAPPER}} .skyyrose-3d-container',
            ]
        );

        $this->end_controls_section();

        // Loading Style Section
        $this->start_controls_section(
            'loading_style_section',
            [
                'label' => __('Loading Style', 'skyyrose-3d'),
                'tab' => \Elementor\Controls_Manager::TAB_STYLE,
            ]
        );

        $this->add_control(
            'loader_color',
            [
                'label' => __('Loader Color', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => '#B76E79',
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-3d-spinner' => 'border-top-color: {{VALUE}};',
                ],
            ]
        );

        $this->add_control(
            'loader_text_color',
            [
                'label' => __('Loading Text Color', 'skyyrose-3d'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => '#888888',
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-3d-loader p' => 'color: {{VALUE}};',
                ],
            ]
        );

        $this->end_controls_section();
    }

    /**
     * Get WooCommerce categories
     */
    private function get_woo_categories(): array {
        $categories = [];

        if (!function_exists('get_terms')) {
            return $categories;
        }

        $terms = get_terms([
            'taxonomy' => 'product_cat',
            'hide_empty' => false,
        ]);

        if (!is_wp_error($terms)) {
            foreach ($terms as $term) {
                $categories[$term->term_id] = $term->name;
            }
        }

        return $categories;
    }

    /**
     * Render widget output
     */
    protected function render(): void {
        $settings = $this->get_settings_for_display();
        $container_id = 'skyyrose-3d-' . $this->get_id();

        $config = [
            'collection' => $settings['collection'],
            'enableFullscreen' => $settings['enable_fullscreen'] === 'yes',
            'enableBloom' => $settings['enable_bloom'] === 'yes',
            'bloomStrength' => $settings['bloom_strength']['size'] ?? 0.5,
            'backgroundColor' => $settings['background_color'],
            'particleCount' => intval($settings['particle_count']),
            'enableProductCards' => $settings['enable_product_cards'] === 'yes',
            'enableAR' => $settings['enable_ar'] === 'yes',
            'cursorSpotlight' => $settings['cursor_spotlight'] === 'yes',
        ];

        // Get products based on source
        if ($settings['product_source'] === 'woocommerce' && !empty($settings['woo_category'])) {
            $config['products'] = $this->get_woo_products($settings['woo_category']);
        } elseif ($settings['product_source'] === 'manual' && !empty($settings['manual_products'])) {
            $config['products'] = array_map('trim', explode(',', $settings['manual_products']));
        }

        ?>
        <div
            id="<?php echo esc_attr($container_id); ?>"
            class="skyyrose-3d-container"
            data-skyyrose-3d="<?php echo esc_attr(wp_json_encode($config)); ?>"
        >
            <div class="skyyrose-3d-loader">
                <div class="skyyrose-3d-spinner"></div>
                <p><?php esc_html_e('Loading 3D Experience...', 'skyyrose-3d'); ?></p>
            </div>
        </div>
        <?php
    }

    /**
     * Get WooCommerce products for a category
     */
    private function get_woo_products(int $category_id): array {
        if (!function_exists('wc_get_products')) {
            return [];
        }

        $products = wc_get_products([
            'category' => [$category_id],
            'limit' => 12,
            'status' => 'publish',
        ]);

        return array_map(function($product) {
            return [
                'id' => $product->get_id(),
                'name' => $product->get_name(),
                'price' => $product->get_price(),
                'thumbnail' => wp_get_attachment_url($product->get_image_id()),
            ];
        }, $products);
    }

    /**
     * Render in Elementor editor
     */
    protected function content_template(): void {
        ?>
        <#
        var containerId = 'skyyrose-3d-' + view.getID();
        var config = {
            collection: settings.collection,
            enableFullscreen: settings.enable_fullscreen === 'yes',
            enableBloom: settings.enable_bloom === 'yes',
        };
        #>
        <div
            id="{{ containerId }}"
            class="skyyrose-3d-container"
            data-skyyrose-3d="{{ JSON.stringify(config) }}"
            style="background-color: {{ settings.background_color }};"
        >
            <div class="skyyrose-3d-loader">
                <div class="skyyrose-3d-spinner" style="border-top-color: {{ settings.loader_color }};"></div>
                <p style="color: {{ settings.loader_text_color }};"><?php esc_html_e('Loading 3D Experience...', 'skyyrose-3d'); ?></p>
            </div>
            <div class="elementor-editor-preview-notice">
                <p><strong>{{ settings.collection }}</strong> 3D Experience</p>
                <p class="elementor-editor-preview-hint"><?php esc_html_e('Preview in frontend to see 3D experience', 'skyyrose-3d'); ?></p>
            </div>
        </div>
        <style>
            #{{ containerId }} .elementor-editor-preview-notice {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                color: #B76E79;
            }
            #{{ containerId }} .elementor-editor-preview-hint {
                color: #888;
                font-size: 12px;
            }
        </style>
        <?php
    }
}
