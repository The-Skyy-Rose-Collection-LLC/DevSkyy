<?php
/**
 * Elementor Lookbook Widget
 *
 * Masonry-style image gallery for social proof / lifestyle photos.
 * Uses Elementor's built-in gallery control with hover overlay.
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SkyyRose_Lookbook_Widget extends \Elementor\Widget_Base {

	public function get_name() {
		return 'skyyrose-lookbook';
	}

	public function get_title() {
		return esc_html__( 'Lookbook Gallery', 'skyyrose-flagship' );
	}

	public function get_icon() {
		return 'eicon-gallery-masonry';
	}

	public function get_categories() {
		return array( 'skyyrose' );
	}

	public function get_keywords() {
		return array( 'lookbook', 'gallery', 'masonry', 'photos', 'skyyrose' );
	}

	protected function register_controls() {

		$this->start_controls_section( 'section_gallery', array(
			'label' => esc_html__( 'Gallery', 'skyyrose-flagship' ),
			'tab'   => \Elementor\Controls_Manager::TAB_CONTENT,
		) );

		$this->add_control( 'gallery', array(
			'label'   => esc_html__( 'Images', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::GALLERY,
			'default' => array(),
		) );

		$this->add_control( 'columns', array(
			'label'   => esc_html__( 'Columns', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::SELECT,
			'options' => array(
				'2' => '2',
				'3' => '3',
				'4' => '4',
			),
			'default' => '3',
		) );

		$this->add_control( 'aspect_ratio', array(
			'label'   => esc_html__( 'Aspect Ratio', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::SELECT,
			'options' => array(
				'1/1'   => esc_html__( 'Square', 'skyyrose-flagship' ),
				'3/4'   => esc_html__( '3:4 Portrait', 'skyyrose-flagship' ),
				'4/3'   => esc_html__( '4:3 Landscape', 'skyyrose-flagship' ),
				'auto'  => esc_html__( 'Auto', 'skyyrose-flagship' ),
			),
			'default' => '3/4',
		) );

		$this->add_control( 'overlay_text', array(
			'label'       => esc_html__( 'Overlay Text', 'skyyrose-flagship' ),
			'type'        => \Elementor\Controls_Manager::TEXT,
			'placeholder' => esc_html__( 'e.g. @skyyrose', 'skyyrose-flagship' ),
		) );

		$this->end_controls_section();
	}

	protected function render() {
		$settings = $this->get_settings_for_display();
		$gallery  = $settings['gallery'];
		$columns  = intval( $settings['columns'] );
		$ratio    = $settings['aspect_ratio'];
		$overlay  = $settings['overlay_text'];

		if ( empty( $gallery ) ) {
			echo '<p class="elementor-alert">' . esc_html__( 'Add images to the gallery.', 'skyyrose-flagship' ) . '</p>';
			return;
		}

		$aspect_style = 'auto' !== $ratio ? "aspect-ratio:{$ratio};" : '';
		?>
		<div class="col-rv" style="display:grid;grid-template-columns:repeat(<?php echo esc_attr( $columns ); ?>,1fr);
			gap:8px;padding:40px 0;">
			<?php foreach ( $gallery as $image ) :
				$url  = ! empty( $image['url'] ) ? $image['url'] : '';
				$id   = ! empty( $image['id'] ) ? $image['id'] : 0;
				$alt  = $id ? get_post_meta( $id, '_wp_attachment_image_alt', true ) : '';
				$srcs = $id ? wp_get_attachment_image_srcset( $id, 'large' ) : '';
			?>
				<div style="position:relative;overflow:hidden;border-radius:4px;<?php echo esc_attr( $aspect_style ); ?>">
					<img src="<?php echo esc_url( $url ); ?>"
						alt="<?php echo esc_attr( $alt ); ?>"
						<?php if ( $srcs ) : ?>srcset="<?php echo esc_attr( $srcs ); ?>"<?php endif; ?>
						sizes="(max-width:768px) 50vw, <?php echo esc_attr( round( 100 / $columns ) ); ?>vw"
						loading="lazy"
						style="width:100%;height:100%;object-fit:cover;transition:transform .6s cubic-bezier(.16,1,.3,1);">

					<?php if ( $overlay ) : ?>
						<div style="position:absolute;inset:0;background:rgba(0,0,0,.5);opacity:0;
							transition:opacity .4s;display:flex;align-items:center;justify-content:center;
							font-family:'Bebas Neue',sans-serif;font-size:14px;letter-spacing:4px;
							color:#fff;text-transform:uppercase;"
							onmouseenter="this.style.opacity='1';this.previousElementSibling.style.transform='scale(1.06)'"
							onmouseleave="this.style.opacity='0';this.previousElementSibling.style.transform='scale(1)'">
							<?php echo esc_html( $overlay ); ?>
						</div>
					<?php endif; ?>
				</div>
			<?php endforeach; ?>
		</div>
		<?php
	}
}
