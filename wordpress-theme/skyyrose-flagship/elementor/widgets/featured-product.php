<?php
/**
 * Elementor Featured Product Widget
 *
 * Full-width product spotlight with large image + info panel.
 * Reuses .col-feat CSS from collection-v4.css.
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SkyyRose_Featured_Product_Widget extends \Elementor\Widget_Base {

	public function get_name() {
		return 'skyyrose-featured-product';
	}

	public function get_title() {
		return esc_html__( 'Featured Product', 'skyyrose-flagship' );
	}

	public function get_icon() {
		return 'eicon-featured-image';
	}

	public function get_categories() {
		return array( 'skyyrose' );
	}

	public function get_keywords() {
		return array( 'featured', 'product', 'spotlight', 'skyyrose' );
	}

	protected function register_controls() {

		/* ── Content ────────────────────────────── */

		$this->start_controls_section( 'section_product', array(
			'label' => esc_html__( 'Product', 'skyyrose-flagship' ),
			'tab'   => \Elementor\Controls_Manager::TAB_CONTENT,
		) );

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

		$this->add_control( 'layout', array(
			'label'   => esc_html__( 'Layout', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::SELECT,
			'options' => array(
				'image-left'  => esc_html__( 'Image Left', 'skyyrose-flagship' ),
				'image-right' => esc_html__( 'Image Right', 'skyyrose-flagship' ),
			),
			'default' => 'image-left',
		) );

		$this->add_control( 'show_sizes', array(
			'label'        => esc_html__( 'Show Sizes', 'skyyrose-flagship' ),
			'type'         => \Elementor\Controls_Manager::SWITCHER,
			'default'      => 'yes',
			'return_value' => 'yes',
		) );

		$this->add_control( 'cta_text', array(
			'label'   => esc_html__( 'CTA Text', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::TEXT,
			'default' => esc_html__( 'Pre-Order Now', 'skyyrose-flagship' ),
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

		$collection_accents = array(
			'black-rose' => '#C0C0C0',
			'love-hurts' => '#DC143C',
			'signature'  => '#D4AF37',
		);
		$accent = isset( $collection_accents[ $product['collection'] ] )
			? $collection_accents[ $product['collection'] ]
			: '#B76E79';

		$r = hexdec( substr( $accent, 1, 2 ) );
		$g = hexdec( substr( $accent, 3, 2 ) );
		$b = hexdec( substr( $accent, 5, 2 ) );

		$image   = skyyrose_product_image_uri( $product['image'] );
		$url     = skyyrose_product_url( $sku );
		$price   = skyyrose_format_price( $product );
		$cta     = $settings['cta_text'];
		$sizes   = explode( '|', $product['sizes'] );
		$is_right = 'image-right' === $settings['layout'];

		$collection_labels = array(
			'black-rose' => 'Black Rose Collection',
			'love-hurts' => 'Love Hurts Collection',
			'signature'  => 'Signature Collection',
		);
		$col_label = isset( $collection_labels[ $product['collection'] ] )
			? $collection_labels[ $product['collection'] ]
			: ucfirst( $product['collection'] );
		?>
		<section class="col-featured col-rv"
			style="--col-accent:<?php echo esc_attr( $accent ); ?>;--col-accent-rgb:<?php echo esc_attr( "$r,$g,$b" ); ?>">
			<div class="col-feat__inner" style="<?php echo $is_right ? 'direction:rtl;' : ''; ?>">

				<div class="col-feat__vis" style="direction:ltr;">
					<?php if ( $product['badge'] ) : ?>
						<span class="col-feat__badge"><?php echo esc_html( $product['badge'] ); ?></span>
					<?php endif; ?>
					<img src="<?php echo esc_url( $image ); ?>"
						alt="<?php echo esc_attr( $product['name'] ); ?>"
						loading="lazy" width="600" height="750">
				</div>

				<div style="direction:ltr;">
					<span class="col-feat__tag"><?php echo esc_html__( 'Featured', 'skyyrose-flagship' ); ?></span>
					<span class="col-feat__col"><?php echo esc_html( $col_label ); ?></span>
					<h2 class="col-feat__name"><?php echo esc_html( $product['name'] ); ?></h2>
					<span class="col-feat__price"><?php echo esc_html( $price ); ?></span>
					<p class="col-feat__desc"><?php echo esc_html( $product['description'] ); ?></p>

					<?php if ( 'yes' === $settings['show_sizes'] && count( $sizes ) > 1 ) : ?>
						<div class="col-feat__sizes">
							<?php foreach ( $sizes as $size ) : ?>
								<button type="button"><?php echo esc_html( trim( $size ) ); ?></button>
							<?php endforeach; ?>
						</div>
					<?php endif; ?>

					<a href="<?php echo esc_url( $url ); ?>" class="col-feat__add col-btn">
						<?php echo esc_html( $cta ); ?>
					</a>
				</div>

			</div>
		</section>
		<?php
	}
}
