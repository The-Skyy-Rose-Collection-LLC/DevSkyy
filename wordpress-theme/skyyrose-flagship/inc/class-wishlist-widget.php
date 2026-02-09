<?php
/**
 * Wishlist Widget
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Wishlist Widget Class
 */
class SkyyRose_Wishlist_Widget extends WP_Widget {

	/**
	 * Constructor.
	 */
	public function __construct() {
		parent::__construct(
			'skyyrose_wishlist',
			esc_html__( 'SkyyRose Wishlist', 'skyyrose-flagship' ),
			array(
				'description' => esc_html__( 'Display wishlist items in the sidebar.', 'skyyrose-flagship' ),
			)
		);
	}

	/**
	 * Outputs the content of the widget.
	 *
	 * @param array $args Widget arguments.
	 * @param array $instance Saved values from database.
	 */
	public function widget( $args, $instance ) {
		$title       = ! empty( $instance['title'] ) ? $instance['title'] : esc_html__( 'My Wishlist', 'skyyrose-flagship' );
		$limit       = ! empty( $instance['limit'] ) ? absint( $instance['limit'] ) : 5;
		$show_button = ! empty( $instance['show_button'] ) ? $instance['show_button'] : 'yes';

		echo $args['before_widget'];

		if ( ! empty( $title ) ) {
			echo $args['before_title'] . esc_html( $title ) . $args['after_title'];
		}

		$wishlist = skyyrose_get_wishlist_items();
		$wishlist = array_slice( $wishlist, 0, $limit );

		if ( ! empty( $wishlist ) ) {
			?>
			<ul class="wishlist-widget-items">
				<?php foreach ( $wishlist as $product_id ) : ?>
					<?php
					$product = wc_get_product( $product_id );
					if ( ! $product ) {
						continue;
					}
					?>
					<li class="wishlist-widget-item">
						<div class="wishlist-widget-item-image">
							<a href="<?php echo esc_url( $product->get_permalink() ); ?>">
								<?php echo $product->get_image( 'thumbnail' ); ?>
							</a>
						</div>
						<div class="wishlist-widget-item-info">
							<h4 class="wishlist-widget-item-title">
								<a href="<?php echo esc_url( $product->get_permalink() ); ?>">
									<?php echo esc_html( $product->get_name() ); ?>
								</a>
							</h4>
							<div class="wishlist-widget-item-price">
								<?php echo $product->get_price_html(); ?>
							</div>
						</div>
					</li>
				<?php endforeach; ?>
			</ul>

			<?php if ( 'yes' === $show_button ) : ?>
				<div class="wishlist-widget-actions">
					<a href="<?php echo esc_url( get_permalink( get_page_by_path( 'wishlist' ) ) ); ?>" class="button">
						<?php esc_html_e( 'View All', 'skyyrose-flagship' ); ?>
					</a>
				</div>
			<?php endif; ?>
			<?php
		} else {
			?>
			<div class="wishlist-widget-empty">
				<p><?php esc_html_e( 'Your wishlist is empty.', 'skyyrose-flagship' ); ?></p>
			</div>
			<?php
		}

		echo $args['after_widget'];
	}

	/**
	 * Outputs the options form on admin.
	 *
	 * @param array $instance The widget options.
	 */
	public function form( $instance ) {
		$title       = ! empty( $instance['title'] ) ? $instance['title'] : esc_html__( 'My Wishlist', 'skyyrose-flagship' );
		$limit       = ! empty( $instance['limit'] ) ? absint( $instance['limit'] ) : 5;
		$show_button = ! empty( $instance['show_button'] ) ? $instance['show_button'] : 'yes';
		?>
		<p>
			<label for="<?php echo esc_attr( $this->get_field_id( 'title' ) ); ?>">
				<?php esc_html_e( 'Title:', 'skyyrose-flagship' ); ?>
			</label>
			<input
				class="widefat"
				id="<?php echo esc_attr( $this->get_field_id( 'title' ) ); ?>"
				name="<?php echo esc_attr( $this->get_field_name( 'title' ) ); ?>"
				type="text"
				value="<?php echo esc_attr( $title ); ?>"
			>
		</p>

		<p>
			<label for="<?php echo esc_attr( $this->get_field_id( 'limit' ) ); ?>">
				<?php esc_html_e( 'Number of items to show:', 'skyyrose-flagship' ); ?>
			</label>
			<input
				class="tiny-text"
				id="<?php echo esc_attr( $this->get_field_id( 'limit' ) ); ?>"
				name="<?php echo esc_attr( $this->get_field_name( 'limit' ) ); ?>"
				type="number"
				step="1"
				min="1"
				value="<?php echo esc_attr( $limit ); ?>"
				size="3"
			>
		</p>

		<p>
			<input
				class="checkbox"
				type="checkbox"
				<?php checked( $show_button, 'yes' ); ?>
				id="<?php echo esc_attr( $this->get_field_id( 'show_button' ) ); ?>"
				name="<?php echo esc_attr( $this->get_field_name( 'show_button' ) ); ?>"
				value="yes"
			>
			<label for="<?php echo esc_attr( $this->get_field_id( 'show_button' ) ); ?>">
				<?php esc_html_e( 'Show "View All" button', 'skyyrose-flagship' ); ?>
			</label>
		</p>
		<?php
	}

	/**
	 * Processing widget options on save.
	 *
	 * @param array $new_instance The new options.
	 * @param array $old_instance The previous options.
	 * @return array Updated instance.
	 */
	public function update( $new_instance, $old_instance ) {
		$instance = array();

		$instance['title']       = ! empty( $new_instance['title'] ) ? sanitize_text_field( $new_instance['title'] ) : '';
		$instance['limit']       = ! empty( $new_instance['limit'] ) ? absint( $new_instance['limit'] ) : 5;
		$instance['show_button'] = ! empty( $new_instance['show_button'] ) ? 'yes' : 'no';

		return $instance;
	}
}

/**
 * Register Wishlist Widget.
 */
function skyyrose_register_wishlist_widget() {
	register_widget( 'SkyyRose_Wishlist_Widget' );
}
add_action( 'widgets_init', 'skyyrose_register_wishlist_widget' );
