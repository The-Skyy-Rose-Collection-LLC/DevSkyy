<?php
/**
 * Elementor Newsletter Widget
 *
 * Email capture form with AJAX submission, nonce-protected,
 * reusing the existing skyyrose_newsletter AJAX handler.
 * Reuses .col-nl CSS from collection-v4.css.
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SkyyRose_Newsletter_Widget extends \Elementor\Widget_Base {

	public function get_name() {
		return 'skyyrose-newsletter';
	}

	public function get_title() {
		return esc_html__( 'Newsletter Signup', 'skyyrose-flagship' );
	}

	public function get_icon() {
		return 'eicon-email-field';
	}

	public function get_categories() {
		return array( 'skyyrose' );
	}

	public function get_keywords() {
		return array( 'newsletter', 'email', 'signup', 'subscribe', 'skyyrose' );
	}

	protected function register_controls() {

		$this->start_controls_section( 'section_content', array(
			'label' => esc_html__( 'Content', 'skyyrose-flagship' ),
			'tab'   => \Elementor\Controls_Manager::TAB_CONTENT,
		) );

		$this->add_control( 'heading', array(
			'label'   => esc_html__( 'Heading', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::TEXT,
			'default' => esc_html__( 'Join the Inner Circle', 'skyyrose-flagship' ),
		) );

		$this->add_control( 'description', array(
			'label'   => esc_html__( 'Description', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::TEXTAREA,
			'default' => esc_html__( 'Early access to drops, exclusive offers, and behind-the-scenes from the studio.', 'skyyrose-flagship' ),
		) );

		$this->add_control( 'button_text', array(
			'label'   => esc_html__( 'Button Text', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::TEXT,
			'default' => esc_html__( 'Subscribe', 'skyyrose-flagship' ),
		) );

		$this->add_control( 'success_message', array(
			'label'   => esc_html__( 'Success Message', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::TEXT,
			'default' => esc_html__( 'Welcome to the circle.', 'skyyrose-flagship' ),
		) );

		$this->add_control( 'collection_accent', array(
			'label'   => esc_html__( 'Accent Color', 'skyyrose-flagship' ),
			'type'    => \Elementor\Controls_Manager::COLOR,
			'default' => '#B76E79',
		) );

		$this->end_controls_section();
	}

	protected function render() {
		$settings = $this->get_settings_for_display();
		$accent   = $settings['collection_accent'];
		$r = hexdec( substr( $accent, 1, 2 ) );
		$g = hexdec( substr( $accent, 3, 2 ) );
		$b = hexdec( substr( $accent, 5, 2 ) );

		$widget_id = 'nl-' . $this->get_id();
		$nonce     = wp_create_nonce( 'skyyrose_newsletter' );
		$ajax_url  = admin_url( 'admin-ajax.php' );
		?>
		<section class="col-nl col-rv"
			style="--col-accent:<?php echo esc_attr( $accent ); ?>;--col-accent-rgb:<?php echo esc_attr( "$r,$g,$b" ); ?>">

			<div class="col-nl__eye">&bull;</div>

			<h2 class="col-nl__title"><?php echo esc_html( $settings['heading'] ); ?></h2>
			<p class="col-nl__desc"><?php echo esc_html( $settings['description'] ); ?></p>

			<form class="col-nl__form" id="<?php echo esc_attr( $widget_id ); ?>"
				data-ajax-url="<?php echo esc_url( $ajax_url ); ?>"
				data-nonce="<?php echo esc_attr( $nonce ); ?>"
				data-success="<?php echo esc_attr( $settings['success_message'] ); ?>">
				<input type="email" class="col-nl__input" name="email" required
					placeholder="<?php echo esc_attr__( 'Your email address', 'skyyrose-flagship' ); ?>"
					autocomplete="email">
				<button type="submit" class="col-nl__btn">
					<?php echo esc_html( $settings['button_text'] ); ?>
				</button>
			</form>
			<div class="col-nl__msg" id="<?php echo esc_attr( $widget_id ); ?>-msg"></div>
		</section>

		<script>
		(function(){
			var form = document.getElementById('<?php echo esc_js( $widget_id ); ?>');
			if (!form) return;
			form.addEventListener('submit', function(e) {
				e.preventDefault();
				var msg = document.getElementById('<?php echo esc_js( $widget_id ); ?>-msg');
				var email = form.querySelector('input[name="email"]').value;
				var data = new FormData();
				data.append('action', 'skyyrose_newsletter_subscribe');
				data.append('email', email);
				data.append('skyyrose_newsletter_nonce', form.dataset.nonce);

				fetch(form.dataset.ajaxUrl, { method: 'POST', body: data })
					.then(function(r) { return r.json(); })
					.then(function(res) {
						if (res.success) {
							msg.textContent = form.dataset.success;
							msg.className = 'col-nl__msg col-nl__msg--success';
							form.reset();
						} else {
							msg.textContent = res.data || 'Something went wrong.';
							msg.className = 'col-nl__msg col-nl__msg--error';
						}
					})
					.catch(function() {
						msg.textContent = 'Network error. Please try again.';
						msg.className = 'col-nl__msg col-nl__msg--error';
					});
			});
		})();
		</script>
		<?php
	}
}
