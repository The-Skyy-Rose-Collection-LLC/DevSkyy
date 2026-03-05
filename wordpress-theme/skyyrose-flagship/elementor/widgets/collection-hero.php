<?php
/**
 * Elementor Collection Hero Widget
 *
 * Full-bleed hero section with parallax image, collection number,
 * name, tagline, and CTA buttons. Reuses .col-hero CSS from collection-v4.css.
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SkyyRose_Collection_Hero_Widget extends \Elementor\Widget_Base {

	public function get_name() {
		return 'skyyrose-collection-hero';
	}

	public function get_title() {
		return esc_html__( 'Collection Hero', 'skyyrose-flagship' );
	}

	public function get_icon() {
		return 'eicon-header';
	}

	public function get_categories() {
		return array( 'skyyrose' );
	}

	public function get_keywords() {
		return array( 'hero', 'collection', 'banner', 'skyyrose' );
	}

	/**
	 * Collection metadata used for auto-population.
	 */
	private function get_collection_data() {
		return array(
			'black-rose' => array(
				'name'    => 'Black Rose',
				'tagline' => 'Gothic luxury blooms in twilight',
				'number'  => 'Collection 01',
				'accent'  => '#C0C0C0',
				'image'   => 'assets/scenes/black-rose/scene-cathedral.webp',
			),
			'love-hurts' => array(
				'name'    => 'Love Hurts',
				'tagline' => 'Oakland grit meets passionate fire',
				'number'  => 'Collection 02',
				'accent'  => '#DC143C',
				'image'   => 'assets/scenes/love-hurts/scene-castle.webp',
			),
			'signature' => array(
				'name'    => 'Signature',
				'tagline' => 'Bay Area luxury in every stitch',
				'number'  => 'Collection 03',
				'accent'  => '#D4AF37',
				'image'   => 'assets/scenes/signature/scene-city.webp',
			),
		);
	}

	protected function register_controls() {

		/* ── Content ────────────────────────────── */

		$this->start_controls_section( 'section_hero', array(
			'label' => esc_html__( 'Hero', 'skyyrose-flagship' ),
			'tab'   => \Elementor\Controls_Manager::TAB_CONTENT,
		) );

		$this->add_control( 'collection', array(
			'label'   => esc_html__( 'Collection', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::SELECT,
			'options' => array(
				'black-rose' => esc_html__( 'Black Rose', 'skyyrose-flagship' ),
				'love-hurts' => esc_html__( 'Love Hurts', 'skyyrose-flagship' ),
				'signature'  => esc_html__( 'Signature', 'skyyrose-flagship' ),
			),
			'default' => 'black-rose',
		) );

		$this->add_control( 'heading_override', array(
			'label'       => esc_html__( 'Heading Override', 'skyyrose-flagship' ),
			'type'        => \Elementor\Controls_Manager::TEXT,
			'placeholder' => esc_html__( 'Auto-loaded from collection', 'skyyrose-flagship' ),
			'description' => esc_html__( 'Leave empty to use collection name.', 'skyyrose-flagship' ),
		) );

		$this->add_control( 'tagline_override', array(
			'label'       => esc_html__( 'Tagline Override', 'skyyrose-flagship' ),
			'type'        => \Elementor\Controls_Manager::TEXTAREA,
			'placeholder' => esc_html__( 'Auto-loaded from collection', 'skyyrose-flagship' ),
		) );

		$this->add_control( 'hero_image', array(
			'label'       => esc_html__( 'Hero Image', 'skyyrose-flagship' ),
			'type'        => \Elementor\Controls_Manager::MEDIA,
			'description' => esc_html__( 'Leave empty to use default collection scene.', 'skyyrose-flagship' ),
		) );

		$this->add_control( 'cta_primary_text', array(
			'label'   => esc_html__( 'Primary CTA Text', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::TEXT,
			'default' => esc_html__( 'Explore Collection', 'skyyrose-flagship' ),
		) );

		$this->add_control( 'cta_primary_url', array(
			'label' => esc_html__( 'Primary CTA URL', 'skyyrose-flagship' ),
			'type'  => \Elementor\Controls_Manager::URL,
		) );

		$this->add_control( 'cta_secondary_text', array(
			'label'   => esc_html__( 'Secondary CTA Text', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::TEXT,
			'default' => esc_html__( 'Pre-Order', 'skyyrose-flagship' ),
		) );

		$this->add_control( 'cta_secondary_url', array(
			'label' => esc_html__( 'Secondary CTA URL', 'skyyrose-flagship' ),
			'type'  => \Elementor\Controls_Manager::URL,
		) );

		$this->end_controls_section();
	}

	protected function render() {
		$settings    = $this->get_settings_for_display();
		$collections = $this->get_collection_data();
		$slug        = sanitize_key( $settings['collection'] );
		$col         = isset( $collections[ $slug ] ) ? $collections[ $slug ] : $collections['black-rose'];

		$accent  = $col['accent'];
		$r = hexdec( substr( $accent, 1, 2 ) );
		$g = hexdec( substr( $accent, 3, 2 ) );
		$b = hexdec( substr( $accent, 5, 2 ) );

		$heading = ! empty( $settings['heading_override'] ) ? $settings['heading_override'] : $col['name'];
		$tagline = ! empty( $settings['tagline_override'] ) ? $settings['tagline_override'] : $col['tagline'];

		$image_url = '';
		if ( ! empty( $settings['hero_image']['url'] ) ) {
			$image_url = $settings['hero_image']['url'];
		} else {
			$image_url = get_theme_file_uri( $col['image'] );
		}

		$primary_url = ! empty( $settings['cta_primary_url']['url'] ) ? $settings['cta_primary_url']['url'] : '#';
		$secondary_url = ! empty( $settings['cta_secondary_url']['url'] ) ? $settings['cta_secondary_url']['url'] : '';
		?>
		<section class="col-hero"
			style="--col-accent:<?php echo esc_attr( $accent ); ?>;--col-accent-rgb:<?php echo esc_attr( "$r,$g,$b" ); ?>">

			<div class="col-hero__img">
				<img src="<?php echo esc_url( $image_url ); ?>"
					alt="<?php echo esc_attr( $heading ); ?>"
					loading="eager" width="1920" height="1080">
			</div>

			<div class="col-hero__overlay"></div>

			<div class="col-hero__content col-rv">
				<div class="col-hero__num"><?php echo esc_html( $col['number'] ); ?></div>
				<h1 class="col-hero__name"><?php echo esc_html( $heading ); ?></h1>
				<p class="col-hero__tag"><?php echo esc_html( $tagline ); ?></p>

				<div class="col-hero__ctas">
					<a href="<?php echo esc_url( $primary_url ); ?>" class="col-btn col-btn--fill">
						<?php echo esc_html( $settings['cta_primary_text'] ); ?>
					</a>
					<?php if ( ! empty( $secondary_url ) ) : ?>
						<a href="<?php echo esc_url( $secondary_url ); ?>" class="col-btn">
							<?php echo esc_html( $settings['cta_secondary_text'] ); ?>
						</a>
					<?php endif; ?>
				</div>
			</div>
		</section>
		<?php
	}
}
