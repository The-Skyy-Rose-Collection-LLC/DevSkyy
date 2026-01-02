<?php
/**
 * Elementor Widget Extensions
 *
 * Additional widget customizations and integration helpers
 *
 * @package SkyyRose_Immersive
 */

defined('ABSPATH') || exit;

/**
 * Enqueue Elementor editor styles
 */
add_action('elementor/editor/after_enqueue_styles', 'skyyrose_elementor_editor_styles');
function skyyrose_elementor_editor_styles() {
    wp_enqueue_style(
        'skyyrose-elementor-editor',
        SKYYROSE_IMMERSIVE_URI . '/assets/css/elementor-editor.css',
        array(),
        SKYYROSE_IMMERSIVE_VERSION
    );
}

/**
 * Add custom controls to Elementor
 */
add_action('elementor/controls/register', 'skyyrose_register_elementor_controls');
function skyyrose_register_elementor_controls($controls_manager) {
    // Add custom control types if needed
}

/**
 * Extend Elementor with custom capabilities
 */
add_action('elementor/init', 'skyyrose_elementor_init');
function skyyrose_elementor_init() {
    // Register locations for theme builder
    if (class_exists('\ElementorPro\Modules\ThemeBuilder\Module')) {
        add_action('elementor/theme/register_locations', function($theme_manager) {
            $theme_manager->register_location('skyyrose-collection-header');
            $theme_manager->register_location('skyyrose-collection-footer');
            $theme_manager->register_location('skyyrose-3d-section');
        });
    }
}

/**
 * Add preview capabilities for 3D widgets
 */
add_action('elementor/preview/enqueue_scripts', 'skyyrose_elementor_preview_scripts');
function skyyrose_elementor_preview_scripts() {
    // Enqueue scripts for preview mode
    wp_enqueue_script('threejs');
    wp_enqueue_script('threejs-orbit-controls');
    wp_enqueue_script('skyyrose-experience-base');
}

/**
 * Custom widget icons
 */
add_action('elementor/editor/after_enqueue_scripts', 'skyyrose_add_widget_icons');
function skyyrose_add_widget_icons() {
    ?>
    <style>
        .elementor-element .icon .eicon-3d-cube {
            background: linear-gradient(135deg, #B76E79, #C9A962);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .elementor-panel .elementor-element-wrapper[data-element_type="widget"] [data-widget_type^="skyyrose_"] .icon {
            background: linear-gradient(135deg, #1a1a1a, #2a2a2a);
            border-radius: 4px;
        }

        /* Category styling */
        .elementor-panel-category[data-category="skyyrose"] .elementor-panel-category-title {
            background: linear-gradient(135deg, #1a1a1a, #2a2520);
            color: #C9A962;
        }
    </style>
    <?php
}

/**
 * Dynamic tags for collection data
 */
add_action('elementor/dynamic_tags/register', 'skyyrose_register_dynamic_tags');
function skyyrose_register_dynamic_tags($dynamic_tags) {
    // Register group
    \Elementor\Plugin::$instance->dynamic_tags->register_group(
        'skyyrose',
        [
            'title' => __('SkyyRose', 'skyyrose-immersive'),
        ]
    );

    // Register tags
    // Note: Create actual tag classes in separate files if needed
}

/**
 * Responsive controls for 3D experiences
 */
add_action('elementor/element/skyyrose_threejs_viewer/performance_section/after_section_end', 'skyyrose_add_responsive_controls', 10, 2);
function skyyrose_add_responsive_controls($element, $args) {
    $element->start_controls_section(
        'mobile_section',
        [
            'label' => __('Mobile Settings', 'skyyrose-immersive'),
            'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
        ]
    );

    $element->add_control(
        'mobile_fallback',
        [
            'label' => __('Mobile Fallback', 'skyyrose-immersive'),
            'type' => \Elementor\Controls_Manager::SELECT,
            'default' => 'simplified',
            'options' => [
                'full' => __('Full 3D Experience', 'skyyrose-immersive'),
                'simplified' => __('Simplified (Better Performance)', 'skyyrose-immersive'),
                'static' => __('Static Image', 'skyyrose-immersive'),
            ],
            'description' => __('Choose how the experience renders on mobile devices.', 'skyyrose-immersive'),
        ]
    );

    $element->add_control(
        'mobile_image',
        [
            'label' => __('Mobile Fallback Image', 'skyyrose-immersive'),
            'type' => \Elementor\Controls_Manager::MEDIA,
            'condition' => [
                'mobile_fallback' => 'static',
            ],
        ]
    );

    $element->end_controls_section();
}

/**
 * Add CSS variables based on Elementor Global Colors
 */
add_action('wp_head', 'skyyrose_elementor_css_variables', 100);
function skyyrose_elementor_css_variables() {
    if (!class_exists('\Elementor\Plugin')) {
        return;
    }

    // Get Elementor kit settings
    $kit_id = \Elementor\Plugin::$instance->kits_manager->get_active_id();

    if (!$kit_id) {
        return;
    }

    $kit = \Elementor\Plugin::$instance->documents->get($kit_id);

    if (!$kit) {
        return;
    }

    // You can extend this to map Elementor colors to CSS variables
    ?>
    <style id="skyyrose-elementor-variables">
        :root {
            --skyyrose-elementor-primary: var(--e-global-color-primary, #B76E79);
            --skyyrose-elementor-secondary: var(--e-global-color-secondary, #C9A962);
            --skyyrose-elementor-text: var(--e-global-color-text, #1A1A1A);
            --skyyrose-elementor-accent: var(--e-global-color-accent, #DC143C);
        }
    </style>
    <?php
}
