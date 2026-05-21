<?php
/**
 * Elementor Pre-Order CTA Widget
 *
 * Full-width urgency banner with live countdown timer,
 * pulsing CTA button, and "limited pieces" messaging.
 *
 * @package SkyyRose
 * @since   3.3.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SkyyRose_Preorder_CTA_Widget extends \Elementor\Widget_Base {

	public function get_name() {
		return 'skyyrose-preorder-cta';
	}

	public function get_title() {
		return esc_html__( 'Pre-Order CTA', 'skyyrose' );
	}

	public function get_icon() {
		return 'eicon-countdown';
	}

	public function get_categories() {
		return array( 'skyyrose' );
	}

	public function get_keywords() {
		return array( 'preorder', 'countdown', 'urgency', 'cta', 'skyyrose' );
	}

	protected function register_controls() {

		$this->start_controls_section(
			'section_content',
			array(
				'label' => esc_html__( 'Content', 'skyyrose' ),
				'tab'   => \Elementor\Controls_Manager::TAB_CONTENT,
			)
		);

		$this->add_control(
			'headline',
			array(
				'label'   => esc_html__( 'Headline', 'skyyrose' ),
				'type'    => \Elementor\Controls_Manager::TEXT,
				'default' => esc_html__( 'Limited Edition — Pre-Order Now', 'skyyrose' ),
			)
		);

		$this->add_control(
			'subtext',
			array(
				'label'   => esc_html__( 'Subtext', 'skyyrose' ),
				'type'    => \Elementor\Controls_Manager::TEXTAREA,
				'default' => esc_html__( 'Only 250 pieces per style. Once they are gone, they are gone.', 'skyyrose' ),
			)
		);

		$this->add_control(
			'deadline',
			array(
				'label'       => esc_html__( 'Countdown Deadline', 'skyyrose' ),
				'type'        => \Elementor\Controls_Manager::DATE_TIME,
				'description' => esc_html__( 'Leave empty to hide countdown.', 'skyyrose' ),
			)
		);

		$this->add_control(
			'cta_text',
			array(
				'label'   => esc_html__( 'CTA Text', 'skyyrose' ),
				'type'    => \Elementor\Controls_Manager::TEXT,
				'default' => esc_html__( 'Secure Your Piece', 'skyyrose' ),
			)
		);

		$this->add_control(
			'cta_url',
			array(
				'label'   => esc_html__( 'CTA URL', 'skyyrose' ),
				'type'    => \Elementor\Controls_Manager::URL,
				'default' => array( 'url' => '/pre-order/' ),
			)
		);

		$this->add_control(
			'collection_accent',
			array(
				'label'   => esc_html__( 'Accent Color', 'skyyrose' ),
				'type'    => \Elementor\Controls_Manager::COLOR,
				'default' => '#B76E79',
			)
		);

		$this->end_controls_section();
	}

	protected function render() {
		$settings = $this->get_settings_for_display();
		$accent   = $settings['collection_accent'];
		$r        = hexdec( substr( $accent, 1, 2 ) );
		$g        = hexdec( substr( $accent, 3, 2 ) );
		$b        = hexdec( substr( $accent, 5, 2 ) );

		$cta_url = ! empty( $settings['cta_url']['url'] ) ? $settings['cta_url']['url'] : '/pre-order/';
		?>
		<section class="col-rv"
			style="--col-accent:<?php echo esc_attr( $accent ); ?>;--col-accent-rgb:<?php echo esc_attr( "$r,$g,$b" ); ?>;
				background:#0a0a0a;padding:80px 40px;text-align:center;">

			<h2 style="font-family:'Cinzel',serif;font-weight:900;font-size:clamp(24px,4vw,48px);
				letter-spacing:6px;text-transform:uppercase;color:#fff;margin:0 0 16px;">
				<?php echo esc_html( $settings['headline'] ); ?>
			</h2>

			<p style="font-family:'Cormorant Garamond',serif;font-style:italic;font-size:clamp(14px,2vw,20px);
				color:rgba(255,255,255,.5);max-width:600px;margin:0 auto 40px;line-height:1.7;">
				<?php echo esc_html( $settings['subtext'] ); ?>
			</p>

			<?php if ( ! empty( $settings['deadline'] ) ) : ?>
				<div class="skyyrose-countdown" data-deadline="<?php echo esc_attr( $settings['deadline'] ); ?>"
					style="display:flex;justify-content:center;gap:32px;margin-bottom:40px;">
					<?php
					$units = array(
						'days'  => esc_html__( 'Days', 'skyyrose' ),
						'hours' => esc_html__( 'Hours', 'skyyrose' ),
						'mins'  => esc_html__( 'Mins', 'skyyrose' ),
						'secs'  => esc_html__( 'Secs', 'skyyrose' ),
					);
					foreach ( $units as $class => $label ) :
						?>
						<div style="text-align:center;">
							<span class="cd-<?php echo esc_attr( $class ); ?>"
								style="font-family:'Bebas Neue',sans-serif;font-size:clamp(36px,6vw,64px);
									color:<?php echo esc_attr( $accent ); ?>;display:block;line-height:1;">0</span>
							<span style="font-family:ui-monospace,'SF Mono',Menlo,monospace;font-size:8px;letter-spacing:4px;
								text-transform:uppercase;color:#8A8A8A;"><?php echo esc_html( $label ); ?></span>
						</div>
					<?php endforeach; ?>
				</div>
			<?php endif; ?>

			<a href="<?php echo esc_url( $cta_url ); ?>" class="col-btn col-btn--fill"
				style="animation:skyyrosePulse 2s ease-in-out infinite;">
				<?php echo esc_html( $settings['cta_text'] ); ?>
			</a>

			<style>
				@keyframes skyyrosePulse {
					0%, 100% { box-shadow: 0 0 0 0 rgba(<?php echo esc_attr( "$r,$g,$b" ); ?>, .4); }
					50% { box-shadow: 0 0 0 12px rgba(<?php echo esc_attr( "$r,$g,$b" ); ?>, 0); }
				}
			</style>
		</section>
		<?php
	}
}
