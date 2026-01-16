<?php
/**
 * Elementor Three.js Viewer Widget
 *
 * Displays immersive 3D collection experiences
 *
 * @package SkyyRose_Immersive
 */

if (!defined('ABSPATH')) {
    exit; // Exit if accessed directly
}

class SkyyRose_ThreeJS_Viewer_Widget extends \Elementor\Widget_Base {

    /**
     * Get widget name
     */
    public function get_name() {
        return 'skyyrose_threejs_viewer';
    }

    /**
     * Get widget title
     */
    public function get_title() {
        return __('3D Collection Experience', 'skyyrose-immersive');
    }

    /**
     * Get widget icon
     */
    public function get_icon() {
        return 'eicon-3d-cube';
    }

    /**
     * Get widget categories
     */
    public function get_categories() {
        return ['skyyrose'];
    }

    /**
     * Get widget keywords
     */
    public function get_keywords() {
        return ['3d', 'threejs', 'immersive', 'collection', 'experience', 'skyyrose'];
    }

    /**
     * Get script dependencies
     *
     * IMPORTANT: Never call get_settings() here - this runs before register_controls()
     * These handle names must match the registered scripts in skyyrose-3d-experience plugin
     */
    public function get_script_depends() {
        return [
            'three-js',           // Three.js core from skyyrose-3d-experience plugin
            'three-js-addons',    // OrbitControls, GLTFLoader, etc.
            'skyyrose-3d',        // Main experience bundle
        ];
    }

    /**
     * Get style dependencies
     */
    public function get_style_depends() {
        return ['skyyrose-immersive'];
    }

    /**
     * Register widget controls
     */
    protected function register_controls() {
        // Content Section
        $this->start_controls_section(
            'content_section',
            [
                'label' => __('Collection Experience', 'skyyrose-immersive'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        $this->add_control(
            'collection',
            [
                'label' => __('Collection', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::SELECT,
                'default' => 'signature',
                'options' => [
                    'signature' => __('Signature - Rose Garden', 'skyyrose-immersive'),
                    'lovehurts' => __('Love Hurts - Enchanted Castle', 'skyyrose-immersive'),
                    'blackrose' => __('Black Rose - Gothic Garden', 'skyyrose-immersive'),
                ],
                'description' => __('Select which immersive 3D experience to display.', 'skyyrose-immersive'),
            ]
        );

        $this->add_control(
            'height',
            [
                'label' => __('Height', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'size_units' => ['px', 'vh'],
                'range' => [
                    'px' => [
                        'min' => 300,
                        'max' => 1200,
                        'step' => 10,
                    ],
                    'vh' => [
                        'min' => 30,
                        'max' => 100,
                        'step' => 5,
                    ],
                ],
                'default' => [
                    'unit' => 'vh',
                    'size' => 100,
                ],
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-3d-container' => 'height: {{SIZE}}{{UNIT}};',
                ],
            ]
        );

        $this->add_control(
            'enable_fullscreen',
            [
                'label' => __('Enable Fullscreen Button', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => __('Yes', 'skyyrose-immersive'),
                'label_off' => __('No', 'skyyrose-immersive'),
                'return_value' => 'yes',
                'default' => 'yes',
            ]
        );

        $this->add_control(
            'show_instructions',
            [
                'label' => __('Show Navigation Instructions', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => __('Yes', 'skyyrose-immersive'),
                'label_off' => __('No', 'skyyrose-immersive'),
                'return_value' => 'yes',
                'default' => 'yes',
            ]
        );

        $this->end_controls_section();

        // Loading Section
        $this->start_controls_section(
            'loading_section',
            [
                'label' => __('Loading Screen', 'skyyrose-immersive'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        $this->add_control(
            'loading_text',
            [
                'label' => __('Loading Text', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::TEXT,
                'default' => __('Entering Experience...', 'skyyrose-immersive'),
                'placeholder' => __('Loading text', 'skyyrose-immersive'),
            ]
        );

        $this->add_control(
            'loading_logo',
            [
                'label' => __('Loading Logo', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::MEDIA,
                'default' => [
                    'url' => '',
                ],
            ]
        );

        $this->end_controls_section();

        // Style Section
        $this->start_controls_section(
            'style_section',
            [
                'label' => __('Style', 'skyyrose-immersive'),
                'tab' => \Elementor\Controls_Manager::TAB_STYLE,
            ]
        );

        $this->add_control(
            'loading_bg_color',
            [
                'label' => __('Loading Background', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => '#0a0a0a',
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-3d-loading' => 'background-color: {{VALUE}};',
                ],
            ]
        );

        $this->add_control(
            'loading_text_color',
            [
                'label' => __('Loading Text Color', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => '#ffffff',
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-3d-loading' => 'color: {{VALUE}};',
                ],
            ]
        );

        $this->add_control(
            'progress_bar_color',
            [
                'label' => __('Progress Bar Color', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => '#B76E79',
                'selectors' => [
                    '{{WRAPPER}} .loading-progress' => 'background-color: {{VALUE}};',
                ],
            ]
        );

        $this->end_controls_section();

        // Performance Section
        $this->start_controls_section(
            'performance_section',
            [
                'label' => __('Performance', 'skyyrose-immersive'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        $this->add_control(
            'enable_shadows',
            [
                'label' => __('Enable Shadows', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => __('Yes', 'skyyrose-immersive'),
                'label_off' => __('No', 'skyyrose-immersive'),
                'return_value' => 'yes',
                'default' => 'yes',
                'description' => __('Disable on mobile for better performance.', 'skyyrose-immersive'),
            ]
        );

        $this->add_control(
            'enable_postprocessing',
            [
                'label' => __('Enable Post-Processing', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::SWITCHER,
                'label_on' => __('Yes', 'skyyrose-immersive'),
                'label_off' => __('No', 'skyyrose-immersive'),
                'return_value' => 'yes',
                'default' => 'yes',
                'description' => __('Bloom, depth of field, and other effects.', 'skyyrose-immersive'),
            ]
        );

        $this->add_control(
            'particle_density',
            [
                'label' => __('Particle Density', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::SELECT,
                'default' => 'normal',
                'options' => [
                    'low' => __('Low (Mobile)', 'skyyrose-immersive'),
                    'normal' => __('Normal', 'skyyrose-immersive'),
                    'high' => __('High', 'skyyrose-immersive'),
                ],
            ]
        );

        $this->end_controls_section();
    }

    /**
     * Render widget output on the frontend
     */
    protected function render() {
        $settings = $this->get_settings_for_display();
        $collection = $settings['collection'];
        $widget_id = $this->get_id();
        $container_id = $collection . '-experience-' . $widget_id;

        // Build data attributes for JS configuration
        $config = [
            'collection' => $collection,
            'enableShadows' => $settings['enable_shadows'] === 'yes',
            'enablePostProcessing' => $settings['enable_postprocessing'] === 'yes',
            'particleDensity' => $settings['particle_density'],
        ];
        ?>
        <div class="skyyrose-3d-container skyyrose-3d-<?php echo esc_attr($collection); ?>"
             id="<?php echo esc_attr($container_id); ?>"
             data-config='<?php echo wp_json_encode($config); ?>'>

            <!-- Loading Screen -->
            <div class="skyyrose-3d-loading">
                <?php if (!empty($settings['loading_logo']['url'])): ?>
                    <img src="<?php echo esc_url($settings['loading_logo']['url']); ?>"
                         alt="Loading" class="loading-logo">
                <?php endif; ?>

                <div class="loading-text">
                    <?php echo esc_html($settings['loading_text']); ?>
                </div>

                <div class="loading-bar">
                    <div class="loading-progress"></div>
                </div>
            </div>

            <?php if ($settings['show_instructions'] === 'yes'): ?>
            <!-- Navigation Instructions -->
            <div class="skyyrose-3d-instructions">
                <span class="instruction-item">
                    <span class="instruction-icon">🖱️</span>
                    Drag to rotate
                </span>
                <span class="instruction-item">
                    <span class="instruction-icon">🔍</span>
                    Scroll to zoom
                </span>
                <span class="instruction-item">
                    <span class="instruction-icon">👆</span>
                    Click products to view
                </span>
            </div>
            <?php endif; ?>

            <?php if ($settings['enable_fullscreen'] === 'yes'): ?>
            <!-- Fullscreen Button -->
            <button class="skyyrose-fullscreen-btn" title="Toggle Fullscreen">
                <svg viewBox="0 0 24 24" width="24" height="24">
                    <path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
                </svg>
            </button>
            <?php endif; ?>
        </div>

        <script>
        (function() {
            // Wait for Three.js and experience class to load
            function initExperience() {
                var containerId = '<?php echo esc_js($container_id); ?>';
                var collection = '<?php echo esc_js($collection); ?>';
                var config = <?php echo wp_json_encode($config); ?>;

                var ExperienceClass;
                switch(collection) {
                    case 'signature':
                        ExperienceClass = window.SignatureExperience;
                        break;
                    case 'lovehurts':
                        ExperienceClass = window.LoveHurtsExperience;
                        break;
                    case 'blackrose':
                        ExperienceClass = window.BlackRoseExperience;
                        break;
                }

                if (ExperienceClass && typeof THREE !== 'undefined') {
                    new ExperienceClass(containerId, config);
                } else {
                    // Retry after a short delay
                    setTimeout(initExperience, 100);
                }
            }

            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initExperience);
            } else {
                initExperience();
            }

            // Fullscreen handler
            var container = document.getElementById('<?php echo esc_js($container_id); ?>');
            var fsBtn = container.querySelector('.skyyrose-fullscreen-btn');
            if (fsBtn) {
                fsBtn.addEventListener('click', function() {
                    if (!document.fullscreenElement) {
                        container.requestFullscreen().catch(function(err) {
                            console.log('Fullscreen error:', err);
                        });
                    } else {
                        document.exitFullscreen();
                    }
                });
            }
        })();
        </script>
        <?php
    }

    /**
     * Render widget output in the editor
     */
    protected function content_template() {
        ?>
        <#
        var collection = settings.collection;
        var containerId = collection + '-experience-preview';
        #>
        <div class="skyyrose-3d-container skyyrose-3d-{{ collection }}" id="{{ containerId }}">
            <div class="skyyrose-3d-loading" style="display: flex;">
                <# if (settings.loading_logo.url) { #>
                    <img src="{{ settings.loading_logo.url }}" alt="Loading" class="loading-logo">
                <# } #>
                <div class="loading-text">{{ settings.loading_text }}</div>
                <div class="loading-bar">
                    <div class="loading-progress" style="width: 45%;"></div>
                </div>
            </div>

            <div class="elementor-preview-message" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #fff; z-index: 5;">
                <h3>{{ collection.toUpperCase() }} Experience</h3>
                <p>3D experience will render on frontend</p>
            </div>
        </div>
        <?php
    }
}
