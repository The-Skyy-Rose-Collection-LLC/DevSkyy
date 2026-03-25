<?php
/**
 * Elementor Testimonials Widget
 *
 * Carousel of customer testimonials with star rating, avatar,
 * and auto-play fade transitions.
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SkyyRose_Testimonials_Widget extends \Elementor\Widget_Base {

	public function get_name() {
		return 'skyyrose-testimonials';
	}

	public function get_title() {
		return esc_html__( 'Testimonials', 'skyyrose-flagship' );
	}

	public function get_icon() {
		return 'eicon-testimonial-carousel';
	}

	public function get_categories() {
		return array( 'skyyrose' );
	}

	public function get_keywords() {
		return array( 'testimonials', 'reviews', 'social proof', 'skyyrose' );
	}

	protected function register_controls() {

		$this->start_controls_section( 'section_testimonials', array(
			'label' => esc_html__( 'Testimonials', 'skyyrose-flagship' ),
			'tab'   => \Elementor\Controls_Manager::TAB_CONTENT,
		) );

		$repeater = new \Elementor\Repeater();

		$repeater->add_control( 'name', array(
			'label'   => esc_html__( 'Name', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::TEXT,
			'default' => esc_html__( 'Customer Name', 'skyyrose-flagship' ),
		) );

		$repeater->add_control( 'quote', array(
			'label'   => esc_html__( 'Quote', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::TEXTAREA,
			'default' => esc_html__( 'This is the most beautiful piece I own.', 'skyyrose-flagship' ),
		) );

		$repeater->add_control( 'rating', array(
			'label'   => esc_html__( 'Rating (1-5)', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::NUMBER,
			'min'     => 1,
			'max'     => 5,
			'default' => 5,
		) );

		$repeater->add_control( 'avatar', array(
			'label' => esc_html__( 'Avatar', 'skyyrose-flagship' ),
			'type'  => \Elementor\Controls_Manager::MEDIA,
		) );

		$this->add_control( 'testimonials', array(
			'label'       => esc_html__( 'Testimonials', 'skyyrose-flagship' ),
			'type'        => \Elementor\Controls_Manager::REPEATER,
			'fields'      => $repeater->get_controls(),
			'default'     => array(
				array(
					'name'   => 'Jordan M.',
					'quote'  => 'The quality is insane. This is real luxury streetwear.',
					'rating' => 5,
				),
				array(
					'name'   => 'Aisha K.',
					'quote'  => 'I get compliments every time I wear my Black Rose hoodie.',
					'rating' => 5,
				),
			),
			'title_field' => '{{{ name }}}',
		) );

		$this->add_control( 'autoplay', array(
			'label'        => esc_html__( 'Auto-Play', 'skyyrose-flagship' ),
			'type'         => \Elementor\Controls_Manager::SWITCHER,
			'default'      => 'yes',
			'return_value' => 'yes',
		) );

		$this->add_control( 'speed', array(
			'label'   => esc_html__( 'Transition Speed (ms)', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::NUMBER,
			'min'     => 2000,
			'max'     => 10000,
			'step'    => 500,
			'default' => 5000,
		) );

		$this->end_controls_section();
	}

	protected function render() {
		$settings     = $this->get_settings_for_display();
		$testimonials = $settings['testimonials'];
		$autoplay     = 'yes' === $settings['autoplay'];
		$speed        = intval( $settings['speed'] );
		$carousel_id  = 'tm-' . $this->get_id();

		if ( empty( $testimonials ) ) {
			echo '<p class="elementor-alert">' . esc_html__( 'Add testimonials.', 'skyyrose-flagship' ) . '</p>';
			return;
		}
		?>
		<div id="<?php echo esc_attr( $carousel_id ); ?>" class="col-rv"
			style="padding:80px 40px;text-align:center;position:relative;overflow:hidden;">

			<?php foreach ( $testimonials as $i => $t ) :
				$display = 0 === $i ? 'block' : 'none';
				$rating  = min( 5, max( 1, intval( $t['rating'] ) ) );
			?>
				<div class="skyyrose-tm-slide" style="display:<?php echo esc_attr( $display ); ?>;
					transition:opacity .6s ease;">

					<?php if ( ! empty( $t['avatar']['url'] ) ) : ?>
						<img src="<?php echo esc_url( $t['avatar']['url'] ); ?>"
							alt="<?php echo esc_attr( $t['name'] ); ?>"
							style="width:64px;height:64px;border-radius:50%;object-fit:cover;
								margin:0 auto 20px;display:block;border:2px solid #B76E79;"
							loading="lazy">
					<?php endif; ?>

					<div style="color:#D4AF37;font-size:18px;letter-spacing:4px;margin-bottom:16px;">
						<?php echo esc_html( str_repeat( "\u{2605}", $rating ) . str_repeat( "\u{2606}", 5 - $rating ) ); ?>
					</div>

					<blockquote style="font-family:'Cormorant Garamond',serif;font-style:italic;
						font-size:clamp(18px,2.5vw,28px);color:rgba(255,255,255,.7);
						max-width:700px;margin:0 auto 24px;line-height:1.7;">
						&ldquo;<?php echo esc_html( $t['quote'] ); ?>&rdquo;
					</blockquote>

					<cite style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:4px;
						text-transform:uppercase;color:#8A8A8A;font-style:normal;">
						<?php echo esc_html( $t['name'] ); ?>
					</cite>
				</div>
			<?php endforeach; ?>
		</div>

		<?php if ( $autoplay && count( $testimonials ) > 1 ) : ?>
			<script>
			(function(){
				var wrap = document.getElementById('<?php echo esc_js( $carousel_id ); ?>');
				if (!wrap) return;
				var slides = wrap.querySelectorAll('.skyyrose-tm-slide');
				var idx = 0;
				setInterval(function() {
					slides[idx].style.opacity = '0';
					setTimeout(function() {
						slides[idx].style.display = 'none';
						idx = (idx + 1) % slides.length;
						slides[idx].style.display = 'block';
						slides[idx].style.opacity = '0';
						requestAnimationFrame(function() {
							slides[idx].style.opacity = '1';
						});
					}, 600);
				}, <?php echo esc_js( $speed ); ?>);
			})();
			</script>
		<?php endif; ?>
		<?php
	}
}
