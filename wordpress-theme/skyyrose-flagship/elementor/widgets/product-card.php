<?php
/**
 * Elementor Product Card Widget
 *
 * Displays a single product from the centralized catalog with
 * collection-aware accent colors, hover overlay, and CTA button.
 * Reuses .col-card CSS from collection-v4.css.
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SkyyRose_Product_Card_Widget extends \Elementor\Widget_Base {

	public function get_name() {
		return 'skyyrose-product-card';
	}

	public function get_title() {
		return esc_html__( 'Product Card', 'skyyrose-flagship' );
	}

	public function get_icon() {
		return 'eicon-products';
	}

	public function get_categories() {
		return array( 'skyyrose' );
	}

	public function get_keywords() {
		return array( 'product', 'card', 'shop', 'skyyrose' );
	}

	protected function register_controls() {

		/* ── Content ────────────────────────────── */

		$this->start_controls_section( 'section_product', array(
			'label' => esc_html__( 'Product', 'skyyrose-flagship' ),
			'tab'   => \Elementor\Controls_Manager::TAB_CONTENT,
		) );

		// Build SKU options from catalog.
		$sku_options = array( '' => esc_html__( '— Select Product —', 'skyyrose-flagship' ) );
		if ( function_exists( 'skyyrose_get_product_catalog' ) ) {
			foreach ( skyyrose_get_product_catalog() as $sku => $p ) {
				if ( ! empty( $p['published'] ) ) {
					$sku_options[ $sku ] = $p['name'] . ' (' . $sku . ')';
				}
			}
		}

		$this->add_control( 'product_sku', array(
			'label'   => esc_html__( 'Product SKU', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::SELECT,
			'options' => $sku_options,
			'default' => '',
		) );

		$this->add_control( 'show_price', array(
			'label'        => esc_html__( 'Show Price', 'skyyrose-flagship' ),
			'type'         => \Elementor\Controls_Manager::SWITCHER,
			'default'      => 'yes',
			'return_value' => 'yes',
		) );

		$this->add_control( 'show_sizes', array(
			'label'        => esc_html__( 'Show Sizes', 'skyyrose-flagship' ),
			'type'         => \Elementor\Controls_Manager::SWITCHER,
			'default'      => '',
			'return_value' => 'yes',
		) );

		$this->add_control( 'badge_text', array(
			'label'       => esc_html__( 'Badge Override', 'skyyrose-flagship' ),
			'type'        => \Elementor\Controls_Manager::TEXT,
			'placeholder' => esc_html__( 'e.g. NEW, SOLD OUT', 'skyyrose-flagship' ),
			'description' => esc_html__( 'Leave empty to use catalog badge.', 'skyyrose-flagship' ),
		) );

		$this->add_control( 'cta_text', array(
			'label'   => esc_html__( 'CTA Text', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::TEXT,
			'default' => esc_html__( 'View Piece', 'skyyrose-flagship' ),
		) );

		$this->end_controls_section();

		/* ── Style ──────────────────────────────── */

		$this->start_controls_section( 'section_style', array(
			'label' => esc_html__( 'Card Style', 'skyyrose-flagship' ),
			'tab'   => \Elementor\Controls_Manager::TAB_STYLE,
		) );

		$this->add_control( 'accent_color', array(
			'label'   => esc_html__( 'Accent Color', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::COLOR,
			'default' => '',
			'description' => esc_html__( 'Leave empty to auto-detect from collection.', 'skyyrose-flagship' ),
		) );

		$this->end_controls_section();
	}

	protected function render() {
		$settings = $this->get_settings_for_display();
		$sku      = sanitize_key( $settings['product_sku'] );

		if ( empty( $sku ) || ! function_exists( 'skyyrose_get_product' ) ) {
			echo '<p class="elementor-alert">' . esc_html__( 'Select a product SKU.', 'skyyrose-flagship' ) . '</p>';
			return;
		}

		$product = skyyrose_get_product( $sku );
		if ( ! $product ) {
			echo '<p class="elementor-alert">' . esc_html__( 'Product not found.', 'skyyrose-flagship' ) . '</p>';
			return;
		}

		// Resolve accent color.
		$accent = $settings['accent_color'];
		if ( empty( $accent ) ) {
			$collection_accents = array(
				'black-rose' => '#C0C0C0',
				'love-hurts' => '#DC143C',
				'signature'  => '#D4AF37',
			);
			$accent = isset( $collection_accents[ $product['collection'] ] )
				? $collection_accents[ $product['collection'] ]
				: '#B76E79';
		}

		// Convert hex to RGB.
		$r = hexdec( substr( $accent, 1, 2 ) );
		$g = hexdec( substr( $accent, 3, 2 ) );
		$b = hexdec( substr( $accent, 5, 2 ) );

		$badge = ! empty( $settings['badge_text'] ) ? $settings['badge_text'] : $product['badge'];
		$image = skyyrose_product_image_uri( $product['image'] );
		$url   = skyyrose_product_url( $sku );
		$price = skyyrose_format_price( $product );
		$cta   = $settings['cta_text'];
		?>
		<div class="col-card col-rv"
			style="--col-accent:<?php echo esc_attr( $accent ); ?>;--col-accent-rgb:<?php echo esc_attr( "$r,$g,$b" ); ?>">

			<div class="col-card__img">
				<img src="<?php echo esc_url( $image ); ?>"
					alt="<?php echo esc_attr( $product['name'] ); ?>"
					loading="lazy" width="400" height="500">
			</div>

			<?php if ( $badge ) : ?>
				<span class="col-card__badge"><?php echo esc_html( $badge ); ?></span>
			<?php endif; ?>

			<div class="col-card__hover">
				<span><?php echo esc_html( $cta ); ?></span>
			</div>

			<div class="col-card__body">
				<h3 class="col-card__name"><?php echo esc_html( $product['name'] ); ?></h3>
				<p class="col-card__desc"><?php echo esc_html( $product['description'] ); ?></p>

				<?php if ( 'yes' === $settings['show_sizes'] && ! empty( $product['sizes'] ) ) : ?>
					<p style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:2px;color:#8A8A8A;margin-top:8px;">
						<?php echo esc_html( str_replace( '|', ' / ', $product['sizes'] ) ); ?>
					</p>
				<?php endif; ?>

				<div class="col-card__foot">
					<?php if ( 'yes' === $settings['show_price'] ) : ?>
						<span class="col-card__price"><?php echo esc_html( $price ); ?></span>
					<?php endif; ?>
					<a href="<?php echo esc_url( $url ); ?>" class="col-card__view-btn">
						<?php echo esc_html( $cta ); ?>
					</a>
				</div>
			</div>
		</div>
		<?php
	}
}
