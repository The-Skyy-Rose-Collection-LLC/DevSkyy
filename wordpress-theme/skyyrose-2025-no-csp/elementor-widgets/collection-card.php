<?php
/**
 * Collection Card Widget
 * Animated collection preview cards with GSAP
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

namespace SkyyRose\Elementor;

if (!defined('ABSPATH')) exit;

class Collection_Card_Widget extends \Elementor\Widget_Base {

    public function get_name() {
        return 'skyyrose_collection_card';
    }

    public function get_title() {
        return esc_html__('Collection Card', 'skyyrose');
    }

    public function get_icon() {
        return 'eicon-gallery-grid';
    }

    public function get_categories() {
        return ['skyyrose'];
    }

    public function get_script_depends() {
        return ['gsap', 'gsap-scrolltrigger'];
    }

    protected function register_controls() {

        // ===== CONTENT TAB =====
        $this->start_controls_section(
            'content_section',
            [
                'label' => esc_html__('Collection Settings', 'skyyrose'),
                'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        // Collection Type
        $this->add_control(
            'collection_type',
            [
                'label' => esc_html__('Collection', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SELECT,
                'default' => 'black_rose',
                'options' => [
                    'black_rose' => esc_html__('Black Rose', 'skyyrose'),
                    'love_hurts' => esc_html__('Love Hurts', 'skyyrose'),
                    'signature' => esc_html__('Signature', 'skyyrose'),
                ],
            ]
        );

        // Collection Title
        $this->add_control(
            'title',
            [
                'label' => esc_html__('Title', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::TEXT,
                'default' => esc_html__('Black Rose', 'skyyrose'),
                'label_block' => true,
            ]
        );

        // Collection Tagline
        $this->add_control(
            'tagline',
            [
                'label' => esc_html__('Tagline', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::TEXT,
                'default' => esc_html__('DARK ELEGANCE', 'skyyrose'),
                'label_block' => true,
            ]
        );

        // Collection Description
        $this->add_control(
            'description',
            [
                'label' => esc_html__('Description', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::TEXTAREA,
                'default' => esc_html__('For the bold and resilient. Sharp lines, deep reds, and uncompromised strength.', 'skyyrose'),
                'rows' => 3,
            ]
        );

        // Background Image
        $this->add_control(
            'background_image',
            [
                'label' => esc_html__('Background Image', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::MEDIA,
                'default' => [
                    'url' => \Elementor\Utils::get_placeholder_image_src(),
                ],
            ]
        );

        // Link to Immersive Page
        $this->add_control(
            'immersive_link',
            [
                'label' => esc_html__('Immersive Experience Link', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::URL,
                'placeholder' => esc_html__('https://your-link.com', 'skyyrose'),
                'default' => [
                    'url' => '#',
                ],
            ]
        );

        // Animation Style
        $this->add_control(
            'animation_style',
            [
                'label' => esc_html__('Animation Style', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SELECT,
                'default' => 'fade-up',
                'options' => [
                    'fade-up' => esc_html__('Fade Up', 'skyyrose'),
                    'scale-in' => esc_html__('Scale In', 'skyyrose'),
                    'slide-in' => esc_html__('Slide In', 'skyyrose'),
                ],
            ]
        );

        $this->end_controls_section();

        // ===== STYLE TAB =====
        $this->start_controls_section(
            'style_section',
            [
                'label' => esc_html__('Card Style', 'skyyrose'),
                'tab' => \Elementor\Controls_Manager::TAB_STYLE,
            ]
        );

        // Card Height
        $this->add_responsive_control(
            'card_height',
            [
                'label' => esc_html__('Card Height', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'size_units' => ['px', 'vh'],
                'range' => [
                    'px' => [
                        'min' => 400,
                        'max' => 800,
                    ],
                    'vh' => [
                        'min' => 50,
                        'max' => 100,
                    ],
                ],
                'default' => [
                    'size' => 650,
                    'unit' => 'px',
                ],
                'selectors' => [
                    '{{WRAPPER}} .collection-card' => 'height: {{SIZE}}{{UNIT}};',
                ],
            ]
        );

        // Overlay Opacity
        $this->add_control(
            'overlay_opacity',
            [
                'label' => esc_html__('Overlay Opacity', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::SLIDER,
                'range' => [
                    'px' => [
                        'min' => 0,
                        'max' => 1,
                        'step' => 0.1,
                    ],
                ],
                'default' => [
                    'size' => 0.7,
                ],
                'selectors' => [
                    '{{WRAPPER}} .card-overlay' => 'background-color: rgba(0, 0, 0, {{SIZE}});',
                ],
            ]
        );

        // Collection Color
        $this->add_control(
            'collection_color',
            [
                'label' => esc_html__('Collection Color', 'skyyrose'),
                'type' => \Elementor\Controls_Manager::COLOR,
                'default' => '#8B0000',
                'selectors' => [
                    '{{WRAPPER}} .collection-title' => 'color: {{VALUE}};',
                    '{{WRAPPER}} .collection-link' => 'color: {{VALUE}};',
                ],
            ]
        );

        $this->end_controls_section();
    }

    protected function render() {
        $settings = $this->get_settings_for_display();
        $link_url = $settings['immersive_link']['url'] ?? '#';
        ?>
        <div class="collection-card reveal <?php echo esc_attr($settings['animation_style']); ?>"
             onclick="window.location.href='<?php echo esc_url($link_url); ?>'">

            <div class="card-bg" style="background-image: url('<?php echo esc_url($settings['background_image']['url']); ?>');"></div>
            <div class="card-overlay"></div>

            <div class="card-content">
                <h3 class="collection-title"><?php echo esc_html($settings['title']); ?></h3>
                <p class="collection-tagline"><?php echo esc_html($settings['tagline']); ?></p>

                <div class="collection-details">
                    <p class="collection-description"><?php echo esc_html($settings['description']); ?></p>
                    <a href="<?php echo esc_url($link_url); ?>" class="collection-link" onclick="event.stopPropagation();">
                        <?php echo esc_html__('Enter Experience', 'skyyrose'); ?> →
                    </a>
                </div>
            </div>
        </div>

        <style>
            .collection-card {
                position: relative;
                overflow: hidden;
                border-radius: 4px;
                cursor: pointer;
                transition: transform 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
            }

            .collection-card:hover {
                transform: translateY(-10px);
            }

            .card-bg {
                position: absolute;
                inset: 0;
                background-size: cover;
                background-position: center;
                transition: transform 1s ease;
            }

            .collection-card:hover .card-bg {
                transform: scale(1.1);
            }

            .card-overlay {
                position: absolute;
                inset: 0;
                transition: background-color 0.6s ease;
            }

            .collection-card:hover .card-overlay {
                background-color: rgba(0, 0, 0, 0.4) !important;
            }

            .card-content {
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                padding: 3rem;
                z-index: 10;
                background: linear-gradient(to top, #000 0%, transparent 100%);
            }

            .collection-title {
                font-family: var(--font-heading);
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
                transform: translateY(20px);
                transition: transform 0.5s ease;
            }

            .collection-card:hover .collection-title {
                transform: translateY(0);
            }

            .collection-tagline {
                color: #ccc;
                letter-spacing: 1px;
                font-size: 0.9rem;
                margin-bottom: 1rem;
            }

            .collection-details {
                height: 0;
                overflow: hidden;
                opacity: 0;
                transition: all 0.5s ease;
            }

            .collection-card:hover .collection-details {
                height: auto;
                opacity: 1;
                margin-top: 1rem;
            }

            .collection-description {
                font-size: 0.9rem;
                color: #888;
                margin-bottom: 1.5rem;
            }

            .collection-link {
                text-decoration: none;
                text-transform: uppercase;
                letter-spacing: 2px;
                font-size: 0.8rem;
                display: inline-block;
                transition: text-shadow 0.3s ease;
            }

            .collection-link:hover {
                text-shadow: 0 0 10px currentColor;
            }

            /* Animation Styles */
            .reveal {
                opacity: 0;
                transform: translateY(30px);
            }

            .reveal.active {
                opacity: 1;
                transform: translateY(0);
                transition: all 0.8s ease;
            }

            .reveal.scale-in {
                transform: scale(0.9);
            }

            .reveal.scale-in.active {
                transform: scale(1);
            }

            .reveal.slide-in {
                transform: translateX(-50px);
            }

            .reveal.slide-in.active {
                transform: translateX(0);
            }
        </style>

        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('active');
                    }
                });
            }, { threshold: 0.1 });

            document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
        });
        </script>
        <?php
    }
}
