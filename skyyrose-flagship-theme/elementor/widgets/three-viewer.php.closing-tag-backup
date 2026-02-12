<?php
/**
 * Elementor Three.js Viewer Widget
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Three.js Viewer Widget Class
 */
class SkyyRose_Three_Viewer_Widget extends \Elementor\Widget_Base {

	/**
	 * Get widget name.
	 *
	 * @since 1.0.0
	 * @return string Widget name.
	 */
	public function get_name() {
		return 'skyyrose-three-viewer';
	}

	/**
	 * Get widget title.
	 *
	 * @since 1.0.0
	 * @return string Widget title.
	 */
	public function get_title() {
		return esc_html__( '3D Model Viewer', 'skyyrose-flagship' );
	}

	/**
	 * Get widget icon.
	 *
	 * @since 1.0.0
	 * @return string Widget icon.
	 */
	public function get_icon() {
		return 'eicon-code';
	}

	/**
	 * Get widget categories.
	 *
	 * @since 1.0.0
	 * @return array Widget categories.
	 */
	public function get_categories() {
		return array( 'skyyrose-3d' );
	}

	/**
	 * Register widget controls.
	 *
	 * @since 1.0.0
	 */
	protected function register_controls() {

		$this->start_controls_section(
			'content_section',
			array(
				'label' => esc_html__( 'Content', 'skyyrose-flagship' ),
				'tab'   => \Elementor\Controls_Manager::TAB_CONTENT,
			)
		);

		$this->add_control(
			'model_url',
			array(
				'label'       => esc_html__( 'Model URL', 'skyyrose-flagship' ),
				'type'        => \Elementor\Controls_Manager::TEXT,
				'input_type'  => 'url',
				'placeholder' => esc_html__( 'https://your-domain.com/model.glb', 'skyyrose-flagship' ),
				'description' => esc_html__( 'Enter the URL of your GLB or GLTF model file.', 'skyyrose-flagship' ),
			)
		);

		$this->add_control(
			'viewer_height',
			array(
				'label'      => esc_html__( 'Viewer Height', 'skyyrose-flagship' ),
				'type'       => \Elementor\Controls_Manager::SLIDER,
				'size_units' => array( 'px', 'vh' ),
				'range'      => array(
					'px' => array(
						'min' => 200,
						'max' => 1000,
					),
					'vh' => array(
						'min' => 20,
						'max' => 100,
					),
				),
				'default'    => array(
					'unit' => 'px',
					'size' => 500,
				),
			)
		);

		$this->add_control(
			'auto_rotate',
			array(
				'label'        => esc_html__( 'Auto Rotate', 'skyyrose-flagship' ),
				'type'         => \Elementor\Controls_Manager::SWITCHER,
				'label_on'     => esc_html__( 'Yes', 'skyyrose-flagship' ),
				'label_off'    => esc_html__( 'No', 'skyyrose-flagship' ),
				'return_value' => 'yes',
				'default'      => 'yes',
			)
		);

		$this->end_controls_section();

		$this->start_controls_section(
			'style_section',
			array(
				'label' => esc_html__( 'Style', 'skyyrose-flagship' ),
				'tab'   => \Elementor\Controls_Manager::TAB_STYLE,
			)
		);

		$this->add_control(
			'background_color',
			array(
				'label'     => esc_html__( 'Background Color', 'skyyrose-flagship' ),
				'type'      => \Elementor\Controls_Manager::COLOR,
				'default'   => '#f5f5f5',
				'selectors' => array(
					'{{WRAPPER}} .skyyrose-three-viewer' => 'background-color: {{VALUE}}',
				),
			)
		);

		$this->end_controls_section();
	}

	/**
	 * Render widget output on the frontend.
	 *
	 * @since 1.0.0
	 */
	protected function render() {
		$settings = $this->get_settings_for_display();

		if ( empty( $settings['model_url'] ) ) {
			echo '<p>' . esc_html__( 'Please add a model URL.', 'skyyrose-flagship' ) . '</p>';
			return;
		}

		$viewer_id = 'three-viewer-' . $this->get_id();
		?>
		<div class="skyyrose-three-viewer" id="<?php echo esc_attr( $viewer_id ); ?>"
			data-model="<?php echo esc_url( $settings['model_url'] ); ?>"
			data-auto-rotate="<?php echo esc_attr( $settings['auto_rotate'] ); ?>"
			style="height: <?php echo esc_attr( $settings['viewer_height']['size'] . $settings['viewer_height']['unit'] ); ?>">
		</div>
		<?php
	}

	/**
	 * Render widget output in the editor.
	 *
	 * @since 1.0.0
	 */
	protected function content_template() {
		?>
		<#
		var viewerId = 'three-viewer-' + view.getID();
		#>
		<div class="skyyrose-three-viewer" id="{{ viewerId }}"
			data-model="{{ settings.model_url }}"
			data-auto-rotate="{{ settings.auto_rotate }}"
			style="height: {{ settings.viewer_height.size }}{{ settings.viewer_height.unit }}">
		</div>
		<?php
	}
}

// Register the widget.
\Elementor\Plugin::instance()->widgets_manager->register_widget_type( new SkyyRose_Three_Viewer_Widget() );
