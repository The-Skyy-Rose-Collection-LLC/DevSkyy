<?php
/**
 * Elementor Collection Hero Widget
 *
 * Displays collection hero sections with branding and CTAs
 *
 * @package SkyyRose_Immersive
 */

if (!defined('ABSPATH')) {
    exit;
}

class SkyyRose_Collection_Hero_Widget extends \Elementor\Widget_Base {

    public function get_name() {
        return 'skyyrose_collection_hero';
    }

    public function get_title() {
        return __('Collection Hero', 'skyyrose-immersive');
    }

    public function get_icon() {
        return 'eicon-banner';
    }

    public function get_categories() {
        return ['skyyrose'];
    }

    public function get_keywords() {
        return ['hero', 'collection', 'banner', 'header', 'skyyrose'];
    }

    public function get_style_depends() {
        return ['skyyrose-immersive'];
    }

    protected function register_controls() {
        // Content Section
        $this->start_controls_section(
            'content_section',
            [
                'label' => __('Hero Content', 'skyyrose-immersive'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        $this->add_control(
            'collection',
            [
                'label' => __('Collection Theme', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::SELECT,
                'default' => 'signature',
                'options' => [
                    'signature' => __('Signature - Gold & Rose', 'skyyrose-immersive'),
                    'lovehurts' => __('Love Hurts - Crimson', 'skyyrose-immersive'),
                    'blackrose' => __('Black Rose - Dark Red', 'skyyrose-immersive'),
                ],
            ]
        );

        $this->add_control(
            'logo',
            [
                'label' => __('Collection Logo', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::MEDIA,
                'default' => [
                    'url' => '',
                ],
            ]
        );

        $this->add_control(
            'title',
            [
                'label' => __('Title', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::TEXT,
                'default' => __('SIGNATURE', 'skyyrose-immersive'),
                'placeholder' => __('Collection name', 'skyyrose-immersive'),
            ]
        );

        $this->add_control(
            'tagline',
            [
                'label' => __('Tagline', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::TEXT,
                'default' => __('The Foundation. Built to Last.', 'skyyrose-immersive'),
                'placeholder' => __('Collection tagline', 'skyyrose-immersive'),
            ]
        );

        $this->add_control(
            'description',
            [
                'label' => __('Description', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::TEXTAREA,
                'default' => __('Premium essentials for everyday luxury.', 'skyyrose-immersive'),
                'rows' => 3,
            ]
        );

        $this->add_control(
            'cta_text',
            [
                'label' => __('CTA Button Text', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::TEXT,
                'default' => __('Shop Collection', 'skyyrose-immersive'),
            ]
        );

        $this->add_control(
            'cta_link',
            [
                'label' => __('CTA Link', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::URL,
                'placeholder' => __('https://your-link.com', 'skyyrose-immersive'),
                'default' => [
                    'url' => '#',
                ],
            ]
        );

        $this->add_control(
            'secondary_cta_text',
            [
                'label' => __('Secondary CTA Text', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::TEXT,
                'default' => __('Enter 3D Experience', 'skyyrose-immersive'),
            ]
        );

        $this->add_control(
            'secondary_cta_link',
            [
                'label' => __('Secondary CTA Link', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::URL,
                'placeholder' => __('https://your-link.com', 'skyyrose-immersive'),
                'default' => [
                    'url' => '#experience',
                ],
            ]
        );

        $this->end_controls_section();

        // Layout Section
        $this->start_controls_section(
            'layout_section',
            [
                'label' => __('Layout', 'skyyrose-immersive'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
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
                        'max' => 1000,
                    ],
                    'vh' => [
                        'min' => 30,
                        'max' => 100,
                    ],
                ],
                'default' => [
                    'unit' => 'vh',
                    'size' => 60,
                ],
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-hero' => 'min-height: {{SIZE}}{{UNIT}};',
                ],
            ]
        );

        $this->add_control(
            'content_alignment',
            [
                'label' => __('Content Alignment', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::CHOOSE,
                'options' => [
                    'left' => [
                        'title' => __('Left', 'skyyrose-immersive'),
                        'icon' => 'eicon-text-align-left',
                    ],
                    'center' => [
                        'title' => __('Center', 'skyyrose-immersive'),
                        'icon' => 'eicon-text-align-center',
                    ],
                    'right' => [
                        'title' => __('Right', 'skyyrose-immersive'),
                        'icon' => 'eicon-text-align-right',
                    ],
                ],
                'default' => 'center',
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-hero' => 'text-align: {{VALUE}};',
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
            'title_color',
            [
                'label' => __('Title Color', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-hero-title' => 'color: {{VALUE}};',
                ],
            ]
        );

        $this->add_group_control(
            \Elementor\Group_Control_Typography::get_type(),
            [
                'name' => 'title_typography',
                'label' => __('Title Typography', 'skyyrose-immersive'),
                'selector' => '{{WRAPPER}} .skyyrose-hero-title',
            ]
        );

        $this->add_control(
            'tagline_color',
            [
                'label' => __('Tagline Color', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => 'rgba(255,255,255,0.8)',
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-hero-tagline' => 'color: {{VALUE}};',
                ],
            ]
        );

        $this->add_control(
            'button_bg_color',
            [
                'label' => __('Button Background', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => '#ffffff',
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-hero-cta' => 'background-color: {{VALUE}};',
                ],
            ]
        );

        $this->add_control(
            'button_text_color',
            [
                'label' => __('Button Text Color', 'skyyrose-immersive'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => '#0a0a0a',
                'selectors' => [
                    '{{WRAPPER}} .skyyrose-hero-cta' => 'color: {{VALUE}};',
                ],
            ]
        );

        $this->end_controls_section();
    }

    protected function render() {
        $settings = $this->get_settings_for_display();
        $collection = $settings['collection'];

        // Collection-specific colors
        $collection_colors = [
            'signature' => [
                'title' => '#C9A962',
                'bg' => 'linear-gradient(135deg, #1a1a18 0%, #2a2820 50%, #1a1a18 100%)',
            ],
            'lovehurts' => [
                'title' => '#FF4444',
                'bg' => 'linear-gradient(135deg, #1a0505 0%, #2a0a0a 50%, #1a0505 100%)',
            ],
            'blackrose' => [
                'title' => '#DC143C',
                'bg' => 'linear-gradient(135deg, #0a0a0a 0%, #1a0808 50%, #0a0a0a 100%)',
            ],
        ];

        $colors = $collection_colors[$collection];
        $title_color = $settings['title_color'] ?: $colors['title'];
        ?>
        <div class="skyyrose-hero skyyrose-hero-<?php echo esc_attr($collection); ?>"
             style="background: <?php echo esc_attr($colors['bg']); ?>;">
            <div class="skyyrose-hero-content">
                <?php if (!empty($settings['logo']['url'])): ?>
                    <img src="<?php echo esc_url($settings['logo']['url']); ?>"
                         alt="<?php echo esc_attr($settings['title']); ?>"
                         class="skyyrose-hero-logo">
                <?php endif; ?>

                <h1 class="skyyrose-hero-title" style="color: <?php echo esc_attr($title_color); ?>;">
                    <?php echo esc_html($settings['title']); ?>
                </h1>

                <?php if (!empty($settings['tagline'])): ?>
                    <p class="skyyrose-hero-tagline">
                        <?php echo esc_html($settings['tagline']); ?>
                    </p>
                <?php endif; ?>

                <?php if (!empty($settings['description'])): ?>
                    <p class="skyyrose-hero-description">
                        <?php echo esc_html($settings['description']); ?>
                    </p>
                <?php endif; ?>

                <div class="skyyrose-hero-buttons">
                    <?php if (!empty($settings['cta_text'])): ?>
                        <a href="<?php echo esc_url($settings['cta_link']['url']); ?>"
                           class="skyyrose-hero-cta"
                           <?php echo $settings['cta_link']['is_external'] ? 'target="_blank"' : ''; ?>
                           <?php echo $settings['cta_link']['nofollow'] ? 'rel="nofollow"' : ''; ?>>
                            <?php echo esc_html($settings['cta_text']); ?>
                        </a>
                    <?php endif; ?>

                    <?php if (!empty($settings['secondary_cta_text'])): ?>
                        <a href="<?php echo esc_url($settings['secondary_cta_link']['url']); ?>"
                           class="skyyrose-hero-cta-secondary"
                           <?php echo $settings['secondary_cta_link']['is_external'] ? 'target="_blank"' : ''; ?>>
                            <?php echo esc_html($settings['secondary_cta_text']); ?> →
                        </a>
                    <?php endif; ?>
                </div>
            </div>

            <div class="skyyrose-hero-scroll-indicator">
                <span>↓ Scroll to Explore</span>
            </div>
        </div>
        <?php
    }

    protected function content_template() {
        ?>
        <#
        var collection = settings.collection;
        var collectionColors = {
            'signature': { title: '#C9A962', bg: 'linear-gradient(135deg, #1a1a18 0%, #2a2820 50%, #1a1a18 100%)' },
            'lovehurts': { title: '#FF4444', bg: 'linear-gradient(135deg, #1a0505 0%, #2a0a0a 50%, #1a0505 100%)' },
            'blackrose': { title: '#DC143C', bg: 'linear-gradient(135deg, #0a0a0a 0%, #1a0808 50%, #0a0a0a 100%)' }
        };
        var colors = collectionColors[collection];
        var titleColor = settings.title_color || colors.title;
        #>
        <div class="skyyrose-hero skyyrose-hero-{{ collection }}" style="background: {{ colors.bg }};">
            <div class="skyyrose-hero-content">
                <# if (settings.logo.url) { #>
                    <img src="{{ settings.logo.url }}" alt="{{ settings.title }}" class="skyyrose-hero-logo">
                <# } #>

                <h1 class="skyyrose-hero-title" style="color: {{ titleColor }};">
                    {{{ settings.title }}}
                </h1>

                <# if (settings.tagline) { #>
                    <p class="skyyrose-hero-tagline">{{{ settings.tagline }}}</p>
                <# } #>

                <# if (settings.description) { #>
                    <p class="skyyrose-hero-description">{{{ settings.description }}}</p>
                <# } #>

                <div class="skyyrose-hero-buttons">
                    <# if (settings.cta_text) { #>
                        <a href="{{ settings.cta_link.url }}" class="skyyrose-hero-cta">
                            {{{ settings.cta_text }}}
                        </a>
                    <# } #>

                    <# if (settings.secondary_cta_text) { #>
                        <a href="{{ settings.secondary_cta_link.url }}" class="skyyrose-hero-cta-secondary">
                            {{{ settings.secondary_cta_text }}} →
                        </a>
                    <# } #>
                </div>
            </div>
        </div>
        <?php
    }
}
