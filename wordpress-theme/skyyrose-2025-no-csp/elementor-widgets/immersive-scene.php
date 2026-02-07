<?php
/**
 * Immersive Scene Widget
 * 3D interactive scenes for Black Rose, Love Hurts, and Signature collections
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

namespace SkyyRose\Elementor;

if (!defined('ABSPATH')) exit;

class Immersive_Scene_Widget extends \Elementor\Widget_Base {

    public function get_name() {
        return 'skyyrose_immersive_scene';
    }

    public function get_title() {
        return esc_html__('Immersive 3D Scene', 'skyyrose');
    }

    public function get_icon() {
        return 'eicon-video-camera';
    }

    public function get_categories() {
        return ['skyyrose'];
    }

    public function get_keywords() {
        return ['3d', 'scene', 'immersive', 'three.js', 'babylon'];
    }

    public function get_script_depends() {
        return ['threejs', 'babylonjs', 'gsap', 'gsap-scrolltrigger', 'skyyrose-three-scenes'];
    }

    protected function register_controls() {

        // ===== CONTENT TAB =====
        $this->start_controls_section(
            'content_section',
            [
                'label' => esc_html__('Scene Settings', 'skyyrose'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        // Scene Type
        $this->add_control(
            'scene_type',
            [
                'label' => esc_html__('Collection Scene', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SELECT,
                'default' => 'black_rose',
                'options' => [
                    'black_rose' => esc_html__('Black Rose - Futuristic Garden', 'skyyrose'),
                    'love_hurts' => esc_html__('Love Hurts - Enchanted Castle', 'skyyrose'),
                    'signature' => esc_html__('Signature - Fashion Runway', 'skyyrose'),
                ],
            ]
        );

        // Scene Height
        $this->add_responsive_control(
            'scene_height',
            [
                'label' => esc_html__('Scene Height', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'size_units' => ['px', 'vh'],
                'range' => [
                    'px' => [
                        'min' => 400,
                        'max' => 1200,
                        'step' => 50,
                    ],
                    'vh' => [
                        'min' => 50,
                        'max' => 100,
                        'step' => 5,
                    ],
                ],
                'default' => [
                    'unit' => 'vh',
                    'size' => 100,
                ],
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-immersive-scene' => 'height: {{SIZE}}{{UNIT}};',
                ],
            ]
        );

        // Enable Physics
        $this->add_control(
            'enable_physics',
            [
                'label' => esc_html__('Enable Physics Interactions', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => esc_html__('Yes', 'skyyrose'),
                'label_off' => esc_html__('No', 'skyyrose'),
                'return_value' => 'yes',
                'default' => 'yes',
            ]
        );

        // Enable Scroll Animations
        $this->add_control(
            'enable_scroll_trigger',
            [
                'label' => esc_html__('Enable Scroll Animations', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => esc_html__('Yes', 'skyyrose'),
                'label_off' => esc_html__('No', 'skyyrose'),
                'return_value' => 'yes',
                'default' => 'yes',
            ]
        );

        // Auto-Rotate Camera
        $this->add_control(
            'auto_rotate',
            [
                'label' => esc_html__('Auto-Rotate Camera', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => esc_html__('Yes', 'skyyrose'),
                'label_off' => esc_html__('No', 'skyyrose'),
                'return_value' => 'yes',
                'default' => 'no',
            ]
        );

        // Camera Speed
        $this->add_control(
            'camera_speed',
            [
                'label' => esc_html__('Camera Speed', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'range' => [
                    'px' => [
                        'min' => 0.1,
                        'max' => 2.0,
                        'step' => 0.1,
                    ],
                ],
                'default' => [
                    'size' => 0.5,
                ],
                'condition' => [
                    'auto_rotate' => 'yes',
                ],
            ]
        );

        $this->end_controls_section();

        // ===== HOTSPOTS SECTION =====
        $this->start_controls_section(
            'hotspots_section',
            [
                'label' => esc_html__('Product Hotspots', 'skyyrose'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        // Hotspots Repeater
        $repeater = new \Elementor\Repeater();

        $repeater->add_control(
            'product_id',
            [
                'label' => esc_html__('WooCommerce Product', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SELECT2,
                'options' => $this->get_woocommerce_products(),
                'label_block' => true,
            ]
        );

        $repeater->add_control(
            'position_x',
            [
                'label' => esc_html__('Position X', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'range' => [
                    'px' => [
                        'min' => -50,
                        'max' => 50,
                        'step' => 0.5,
                    ],
                ],
                'default' => [
                    'size' => 0,
                ],
            ]
        );

        $repeater->add_control(
            'position_y',
            [
                'label' => esc_html__('Position Y', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'range' => [
                    'px' => [
                        'min' => -50,
                        'max' => 50,
                        'step' => 0.5,
                    ],
                ],
                'default' => [
                    'size' => 0,
                ],
            ]
        );

        $repeater->add_control(
            'position_z',
            [
                'label' => esc_html__('Position Z', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'range' => [
                    'px' => [
                        'min' => -50,
                        'max' => 50,
                        'step' => 0.5,
                    ],
                ],
                'default' => [
                    'size' => 0,
                ],
            ]
        );

        $this->add_control(
            'hotspots',
            [
                'label' => esc_html__('Hotspots', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::REPEATER,
                'fields' => $repeater->get_controls(),
                'title_field' => 'Product #{{{ product_id }}}',
            ]
        );

        $this->end_controls_section();

        // ===== STYLE TAB =====
        $this->start_controls_section(
            'style_section',
            [
                'label' => esc_html__('Scene Style', 'skyyrose'),
                'tab' => \Elementor\Controls_Manager::TAB_STYLE,
            ]
        );

        // Background Color
        $this->add_control(
            'background_color',
            [
                'label' => esc_html__('Background Color', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => '#000000',
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-immersive-scene' => 'background-color: {{VALUE}};',
                ],
            ]
        );

        // Ambient Light Intensity
        $this->add_control(
            'ambient_light',
            [
                'label' => esc_html__('Ambient Light Intensity', 'skyyrose'),
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
            ]
        );

        // Fog Density
        $this->add_control(
            'fog_density',
            [
                'label' => esc_html__('Fog Density', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'range' => [
                    'px' => [
                        'min' => 0,
                        'max' => 0.1,
                        'step' => 0.001,
                    ],
                ],
                'default' => [
                    'size' => 0.01,
                ],
            ]
        );

        $this->end_controls_section();
    }

    protected function render() {
        $settings = $this->get_settings_for_display();

        $scene_config = [
            'sceneType' => $settings['scene_type'],
            'enablePhysics' => $settings['enable_physics'] === 'yes',
            'enableScrollTrigger' => $settings['enable_scroll_trigger'] === 'yes',
            'autoRotate' => $settings['auto_rotate'] === 'yes',
            'cameraSpeed' => $settings['camera_speed']['size'] ?? 0.5,
            'ambientLight' => $settings['ambient_light']['size'] ?? 0.5,
            'fogDensity' => $settings['fog_density']['size'] ?? 0.01,
            'hotspots' => $settings['hotspots'] ?? [],
        ];

        ?>
        <div class="skyyrose-immersive-scene"
             data-scene-config='<?php echo esc_attr(wp_json_encode($scene_config)); ?>'>
            <canvas class="scene-canvas"></canvas>
            <div class="scene-loading">
                <div class="loading-spinner"></div>
                <p><?php echo esc_html__('Loading Experience...', 'skyyrose'); ?></p>
            </div>
        </div>
        <?php
    }

    /**
     * Get WooCommerce products for dropdown
     */
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
