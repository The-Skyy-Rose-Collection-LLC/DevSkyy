<?php
/**
 * Luxury Product Card Widget for SkyyRose.
 *
 * Displays WooCommerce products with luxury styling following NET-A-PORTER/SSENSE standards:
 * - 3:4 aspect ratio portrait images
 * - Collection-specific hover glow effects
 * - Playfair Display typography for titles
 * - Generous 24px internal padding
 *
 * @package SkyyRose_Immersive
 * @since 2.0.0
 */

namespace SkyyRose\Elementor\Widgets;

use Elementor\Widget_Base;
use Elementor\Controls_Manager;

if (!defined('ABSPATH')) {
    exit; // Exit if accessed directly
}

/**
 * Luxury Product Card Widget Class.
 */
class Luxury_Product_Card extends Widget_Base {

    /**
     * Get widget name.
     *
     * @return string Widget name.
     */
    public function get_name() {
        return 'luxury-product-card';
    }

    /**
     * Get widget title.
     *
     * @return string Widget title.
     */
    public function get_title() {
        return __('Luxury Product Card', 'skyyrose-immersive');
    }

    /**
     * Get widget icon.
     *
     * @return string Widget icon.
     */
    public function get_icon() {
        return 'eicon-product-images';
    }

    /**
     * Get widget categories.
     *
     * @return array Widget categories.
     */
    public function get_categories() {
        return ['skyyrose'];
    }

    /**
     * Register widget controls.
     */
    protected function register_controls() {
        // Content Section
        $this->start_controls_section(
            'content_section',
            [
                'label' => __('Product Settings', 'skyyrose-immersive'),
                'tab' => Controls_Manager::TAB_CONTENT,
            ]
        );

        $this->add_control(
            'product_id',
            [
                'label' => __('Product ID', 'skyyrose-immersive'),
                'type' => Controls_Manager::NUMBER,
                'default' => 0,
                'description' => __('Enter WooCommerce product ID', 'skyyrose-immersive'),
            ]
        );

        $this->add_control(
            'collection',
            [
                'label' => __('Collection', 'skyyrose-immersive'),
                'type' => Controls_Manager::SELECT,
                'options' => [
                    'signature' => __('Signature Collection', 'skyyrose-immersive'),
                    'love-hurts' => __('Love Hurts Collection', 'skyyrose-immersive'),
                    'black-rose' => __('Black Rose Collection', 'skyyrose-immersive'),
                ],
                'default' => 'signature',
                'description' => __('Collection for color theme and hover effects', 'skyyrose-immersive'),
            ]
        );

        $this->end_controls_section();
    }

    /**
     * Render widget output on the frontend.
     */
    protected function render() {
        $settings = $this->get_settings_for_display();
        $product = wc_get_product($settings['product_id']);

        if (!$product) {
            if (\Elementor\Plugin::$instance->editor->is_edit_mode()) {
                echo '<p>' . __('Product not found. Please enter a valid product ID.', 'skyyrose-immersive') . '</p>';
            }
            return;
        }

        // Collection color mapping (matches Python BrandKit colors)
        $collection_colors = [
            'signature' => [
                'primary' => '#C9A962',
                'glow' => 'rgba(201, 169, 98, 0.3)',
            ],
            'love-hurts' => [
                'primary' => '#B76E79',
                'glow' => 'rgba(220, 20, 60, 0.3)',
            ],
            'black-rose' => [
                'primary' => '#C0C0C0',
                'glow' => 'rgba(192, 192, 192, 0.3)',
            ],
        ];

        $colors = $collection_colors[$settings['collection']];
        $product_link = $product->get_permalink();
        $product_image = $product->get_image('woocommerce_thumbnail'); // 600px from Phase 1
        $product_name = $product->get_name();
        $product_price = $product->get_price_html();

        ?>
        <div class="luxury-product-card" data-collection="<?php echo esc_attr($settings['collection']); ?>">
            <a href="<?php echo esc_url($product_link); ?>" class="card-link">
                <div class="card-image">
                    <?php echo $product_image; ?>
                    <div class="card-overlay"></div>
                </div>

                <div class="card-content">
                    <h3 class="card-title text-heading-2"><?php echo esc_html($product_name); ?></h3>
                    <p class="card-price text-body"><?php echo $product_price; ?></p>
                </div>
            </a>

            <style>
                .luxury-product-card {
                    position: relative;
                    overflow: hidden;
                    transition: transform var(--transition-base, 300ms ease);
                }

                .luxury-product-card:hover {
                    transform: translateY(-8px);
                }

                .card-image {
                    position: relative;
                    aspect-ratio: 3 / 4;  /* Portrait luxury ratio */
                    overflow: hidden;
                }

                .card-image img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    transition: transform var(--transition-slow, 500ms ease);
                }

                .card-overlay {
                    position: absolute;
                    inset: 0;
                    background: linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.5) 100%);
                    opacity: 0;
                    transition: opacity var(--transition-base, 300ms ease);
                }

                .luxury-product-card:hover .card-image img {
                    transform: scale(1.05);
                }

                .luxury-product-card:hover .card-overlay {
                    opacity: 1;
                }

                /* Collection-specific glow (from Phase 1 BrandKit) */
                .luxury-product-card:hover {
                    box-shadow: 0 8px 24px <?php echo $colors['glow']; ?>;
                }

                .card-content {
                    padding: var(--space-3, 1.5rem);
                }

                .card-title {
                    color: var(--black, #0D0D0D);
                    margin-bottom: var(--space-2, 1rem);
                    font-family: var(--font-display, 'Playfair Display', serif);
                    font-size: var(--text-2xl, 1.563rem);
                    font-weight: 600;
                    line-height: var(--leading-normal, 1.5);
                }

                .card-price {
                    color: <?php echo $colors['primary']; ?>;
                    font-weight: 600;
                    font-family: var(--font-body, 'Inter', sans-serif);
                    font-size: var(--text-lg, 1.125rem);
                }

                .card-link {
                    text-decoration: none;
                    display: block;
                }

                .card-link:hover .card-title {
                    color: <?php echo $colors['primary']; ?>;
                }
            </style>
        </div>
        <?php
    }
}
