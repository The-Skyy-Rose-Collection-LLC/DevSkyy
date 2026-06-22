<?php
/**
 * Elementor Compatibility — Editorial Helpers
 *
 * Provides shortcodes, scroll-reveal class registration, and a collection
 * palette meta box so Elementor users can build editorial pages that inherit
 * the SkyyRose brand system.
 *
 * Loaded conditionally — only when Elementor is active (see functions.php).
 *
 * @package SkyyRose
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

/*
--------------------------------------------------------------
 * 1. Register custom Elementor widget category for editorial.
 *--------------------------------------------------------------*/
add_action( 'elementor/elements/categories_registered', 'skyyrose_ee_register_categories' );

/**
 * Add an "Editorial" widget category to the Elementor panel.
 *
 * @param \Elementor\Elements_Manager $elements_manager Elements manager.
 */
function skyyrose_ee_register_categories( $elements_manager ) {
	$elements_manager->add_category(
		'skyyrose-editorial',
		array(
			'title' => esc_html__( 'SkyyRose Editorial', 'skyyrose' ),
			'icon'  => 'eicon-document-file',
		)
	);
}

/*
--------------------------------------------------------------
 * 2. Expose scroll-reveal CSS classes to Elementor's class list.
 *--------------------------------------------------------------*/
add_filter( 'elementor/editor/localize_settings', 'skyyrose_ee_expose_classes' );

/**
 * Add SkyyRose utility classes to Elementor's inline help / class suggestions.
 *
 * @param array $settings Elementor editor settings.
 * @return array
 */
function skyyrose_ee_expose_classes( $settings ) {
	$skyyrose_classes = array(
		'lp-rv',
		'lp-rv--left',
		'lp-rv--right',
		'lp-rv--scale',
		'rv',
		'rv-left',
		'rv-right',
		'rv-scale',
		'rv-clip-up',
		'rv-clip-left',
		'rv-blur',
		'stagger-grid',
		'magnetic',
		'btn-sweep',
		'btn-border-draw',
	);

	if ( ! isset( $settings['skyyrose_classes'] ) ) {
		$settings['skyyrose_classes'] = $skyyrose_classes;
	}

	return $settings;
}

/*
--------------------------------------------------------------
 * 3. Collection Palette Meta Box
 *--------------------------------------------------------------*/
add_action( 'add_meta_boxes', 'skyyrose_ee_add_collection_meta_box' );
add_action( 'save_post', 'skyyrose_ee_save_collection_meta', 10, 2 );

/**
 * Register the collection palette meta box on pages using the editorial template.
 */
function skyyrose_ee_add_collection_meta_box() {
	add_meta_box(
		'skyyrose_collection_palette',
		esc_html__( 'SkyyRose Collection Palette', 'skyyrose' ),
		'skyyrose_ee_render_collection_meta_box',
		'page',
		'side',
		'default'
	);
}

/**
 * Render the collection palette selector.
 *
 * @param WP_Post $post Current post object.
 */
function skyyrose_ee_render_collection_meta_box( $post ) {
	$current = get_post_meta( $post->ID, 'skyyrose_collection', true );
	if ( empty( $current ) ) {
		$current = 'signature';
	}

	wp_nonce_field( 'skyyrose_collection_nonce_action', 'skyyrose_collection_nonce' );

	$options = array(
		'signature'  => esc_html__( 'Signature (Gold)', 'skyyrose' ),
		'black-rose' => esc_html__( 'Black Rose (Silver)', 'skyyrose' ),
		'love-hurts' => esc_html__( 'Love Hurts (Crimson)', 'skyyrose' ),
	);
	?>
	<p>
		<label for="skyyrose_collection">
			<?php echo esc_html__( 'Select the collection palette for this page:', 'skyyrose' ); ?>
		</label>
	</p>
	<select id="skyyrose_collection" name="skyyrose_collection" style="width:100%;">
		<?php foreach ( $options as $value => $label ) : ?>
			<option value="<?php echo esc_attr( $value ); ?>" <?php selected( $current, $value ); ?>>
				<?php echo esc_html( $label ); ?>
			</option>
		<?php endforeach; ?>
	</select>
	<p class="description">
		<?php echo esc_html__( 'Controls CSS custom properties (accent colors, glow) on the editorial template.', 'skyyrose' ); ?>
	</p>
	<?php
}

/**
 * Save the collection palette meta value.
 *
 * @param int     $post_id Post ID.
 * @param WP_Post $post    Post object.
 */
function skyyrose_ee_save_collection_meta( $post_id, $post ) {
	// Verify nonce.
	if ( ! isset( $_POST['skyyrose_collection_nonce'] ) ) {
		return;
	}
	if ( ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['skyyrose_collection_nonce'] ) ), 'skyyrose_collection_nonce_action' ) ) {
		return;
	}

	// Check autosave.
	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}

	// Check capability.
	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	if ( isset( $_POST['skyyrose_collection'] ) ) {
		$value   = sanitize_text_field( wp_unslash( $_POST['skyyrose_collection'] ) );
		$allowed = array( 'signature', 'black-rose', 'love-hurts' );

		if ( in_array( $value, $allowed, true ) ) {
			update_post_meta( $post_id, 'skyyrose_collection', $value );
		}
	}
}

/*
--------------------------------------------------------------
 * 4. Shortcodes for Elementor
 *--------------------------------------------------------------*/

/**
 * [skyyrose_countdown hours="72"]
 *
 * Renders a landing-page-style countdown timer.
 * Uses the same markup as template-parts/landing/hero.php countdown.
 *
 * @param array $atts Shortcode attributes.
 * @return string HTML output.
 */
function skyyrose_ee_countdown_shortcode( $atts ) {
	$atts = shortcode_atts(
		array(
			'hours' => '72',
		),
		$atts,
		'skyyrose_countdown'
	);

	$hours = absint( $atts['hours'] );
	if ( $hours <= 0 ) {
		$hours = 72;
	}

	$config = $hours . 'h';

	ob_start();
	?>
	<div class="lp-countdown" data-countdown="<?php echo esc_attr( $config ); ?>">
		<div class="lp-countdown__unit">
			<span class="lp-countdown__num" data-cd="d">00</span>
			<span class="lp-countdown__lbl"><?php echo esc_html__( 'Days', 'skyyrose' ); ?></span>
		</div>
		<span class="lp-countdown__sep" aria-hidden="true">:</span>
		<div class="lp-countdown__unit">
			<span class="lp-countdown__num" data-cd="h">00</span>
			<span class="lp-countdown__lbl"><?php echo esc_html__( 'Hours', 'skyyrose' ); ?></span>
		</div>
		<span class="lp-countdown__sep" aria-hidden="true">:</span>
		<div class="lp-countdown__unit">
			<span class="lp-countdown__num" data-cd="m">00</span>
			<span class="lp-countdown__lbl"><?php echo esc_html__( 'Min', 'skyyrose' ); ?></span>
		</div>
		<span class="lp-countdown__sep" aria-hidden="true">:</span>
		<div class="lp-countdown__unit">
			<span class="lp-countdown__num" data-cd="s">00</span>
			<span class="lp-countdown__lbl"><?php echo esc_html__( 'Sec', 'skyyrose' ); ?></span>
		</div>
	</div>
	<?php
	return ob_get_clean();
}
add_shortcode( 'skyyrose_countdown', 'skyyrose_ee_countdown_shortcode' );

/**
 * [skyyrose_scarcity sku="br-004"]
 *
 * Renders a scarcity / sold-percentage bar for a product.
 * Pulls edition_size and stock data from the product catalog.
 *
 * @param array $atts Shortcode attributes.
 * @return string HTML output.
 */
function skyyrose_ee_scarcity_shortcode( $atts ) {
	$atts = shortcode_atts(
		array(
			'sku' => '',
		),
		$atts,
		'skyyrose_scarcity'
	);

	$sku = sanitize_text_field( $atts['sku'] );
	if ( empty( $sku ) ) {
		return '';
	}

	if ( ! function_exists( 'skyyrose_get_product_catalog' ) ) {
		return '';
	}

	$catalog = skyyrose_get_product_catalog();
	if ( ! isset( $catalog[ $sku ] ) ) {
		return '';
	}

	$product      = $catalog[ $sku ];
	$edition_size = isset( $product['edition_size'] ) ? absint( $product['edition_size'] ) : 200;
	$remaining    = isset( $product['remaining'] ) ? absint( $product['remaining'] ) : $edition_size;
	$sold         = max( 0, $edition_size - $remaining );
	$sold_pct     = $edition_size > 0 ? min( 100, round( ( $sold / $edition_size ) * 100 ) ) : 0;
	$is_low       = ( $remaining <= 10 && $remaining > 0 );
	$product_name = isset( $product['name'] ) ? $product['name'] : $sku;

	ob_start();
	?>
	<div class="lp-scarcity<?php echo $is_low ? ' lp-scarcity--low' : ''; ?>">
		<div class="lp-scarcity__header">
			<span class="lp-scarcity__name"><?php echo esc_html( $product_name ); ?></span>
			<span class="lp-scarcity__stat">
				<?php
				printf(
					/* translators: %d: percentage of stock sold */
					esc_html__( '%d%% sold', 'skyyrose' ),
					intval( $sold_pct )
				);
				?>
			</span>
		</div>
		<div class="lp-scarcity__bar" aria-hidden="true">
			<div class="lp-scarcity__fill" data-percent="<?php echo esc_attr( $sold_pct ); ?>" style="width:0%"></div>
		</div>
		<?php if ( $is_low ) : ?>
			<p class="lp-scarcity__warning">
				<?php
				printf(
					/* translators: %d: number of items remaining */
					esc_html__( 'Only %d left', 'skyyrose' ),
					intval( $remaining )
				);
				?>
			</p>
		<?php endif; ?>
	</div>
	<?php
	return ob_get_clean();
}
add_shortcode( 'skyyrose_scarcity', 'skyyrose_ee_scarcity_shortcode' );

/**
 * [skyyrose_press_bar]
 *
 * Renders the "As Seen In" press mentions bar.
 *
 * @param array $atts Shortcode attributes (currently unused).
 * @return string HTML output.
 */
function skyyrose_ee_press_bar_shortcode( $atts ) {
	$mentions = array( 'Maxim', 'CEO Weekly', 'SF Post', 'Best of Best Review' );

	/**
	 * Filter the press mention names displayed in the press bar shortcode.
	 *
	 * @since 6.5.0
	 * @param array $mentions List of press outlet names.
	 */
	$mentions = apply_filters( 'skyyrose_press_bar_mentions', $mentions );

	ob_start();
	?>
	<div class="lp-press lp-rv" aria-label="<?php echo esc_attr__( 'Featured in', 'skyyrose' ); ?>">
		<div class="lp__container">
			<div class="lp-press__row">
				<?php foreach ( $mentions as $outlet ) : ?>
					<span class="lp-press__name"><?php echo esc_html( $outlet ); ?></span>
				<?php endforeach; ?>
			</div>
		</div>
	</div>
	<?php
	return ob_get_clean();
}
add_shortcode( 'skyyrose_press_bar', 'skyyrose_ee_press_bar_shortcode' );

/**
 * [skyyrose_product_card sku="br-004"]
 *
 * Renders a single holo product card via the existing template part.
 * Falls back to a simple card if the holo template part is not found.
 *
 * @param array $atts Shortcode attributes.
 * @return string HTML output.
 */
function skyyrose_ee_product_card_shortcode( $atts ) {
	$atts = shortcode_atts(
		array(
			'sku' => '',
		),
		$atts,
		'skyyrose_product_card'
	);

	$sku = sanitize_text_field( $atts['sku'] );
	if ( empty( $sku ) ) {
		return '';
	}

	if ( ! function_exists( 'skyyrose_get_product_catalog' ) ) {
		return '';
	}

	$catalog = skyyrose_get_product_catalog();
	if ( ! isset( $catalog[ $sku ] ) ) {
		return '';
	}

	$product    = $catalog[ $sku ];
	$assets_uri = defined( 'SKYYROSE_ASSETS_URI' ) ? SKYYROSE_ASSETS_URI : '';

	// Build args for the holo card template part.
	$card_args = array(
		'sku'        => $sku,
		'title'      => isset( $product['name'] ) ? $product['name'] : '',
		'price'      => isset( $product['price'] ) ? '$' . number_format( (float) $product['price'], 2 ) : '',
		'image_url'  => ! empty( $product['image'] ) ? esc_url( $assets_uri . '/' . $product['image'] ) : '',
		'image_back' => ! empty( $product['back_image'] ) ? esc_url( $assets_uri . '/' . $product['back_image'] ) : '',
		'permalink'  => ! empty( $product['permalink'] ) ? $product['permalink'] : '#',
		'collection' => isset( $product['collection'] ) ? $product['collection'] : '',
		'desc'       => isset( $product['description'] ) ? $product['description'] : '',
		'index'      => 0,
	);

	ob_start();

	// Use the holo card template part if available.
	$template_path = locate_template( 'template-parts/product-card-holo.php' );
	if ( $template_path ) {
		get_template_part( 'template-parts/product-card-holo', null, $card_args );
	} else {
		// Simple fallback card.
		?>
		<div class="lp-product-card" data-collection="<?php echo esc_attr( $card_args['collection'] ); ?>">
			<?php if ( $card_args['image_url'] ) : ?>
				<img src="<?php echo esc_url( $card_args['image_url'] ); ?>"
					alt="<?php echo esc_attr( $card_args['title'] ); ?>"
					loading="lazy"
					width="400" height="400">
			<?php endif; ?>
			<h3><?php echo esc_html( $card_args['title'] ); ?></h3>
			<p class="lp-product-card__price"><?php echo esc_html( $card_args['price'] ); ?></p>
		</div>
		<?php
	}

	return ob_get_clean();
}
add_shortcode( 'skyyrose_product_card', 'skyyrose_ee_product_card_shortcode' );

/*
--------------------------------------------------------------
 * 5. Enqueue landing-pages JS on Elementor editorial pages
 *    so countdown timers and scroll-reveal work.
 *--------------------------------------------------------------*/
add_action( 'wp_enqueue_scripts', 'skyyrose_ee_enqueue_editorial_assets', 25 );

/**
 * Ensure landing-pages.js is loaded on Elementor editorial template pages
 * so shortcode-rendered countdown timers and scroll-reveal animations work.
 */
function skyyrose_ee_enqueue_editorial_assets() {
	$template = get_page_template_slug();
	if ( 'template-elementor-editorial.php' !== $template ) {
		return;
	}

	$js_uri  = SKYYROSE_ASSETS_URI . '/js';
	$js_dir  = SKYYROSE_DIR . '/assets/js';
	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	$lp_js = $use_min && file_exists( $js_dir . '/landing-pages.min.js' )
		? 'landing-pages.min.js' : 'landing-pages.js';

	if ( file_exists( $js_dir . '/' . $lp_js ) && ! wp_script_is( 'skyyrose-landing-pages', 'enqueued' ) ) {
		wp_enqueue_script(
			'skyyrose-landing-pages',
			$js_uri . '/' . $lp_js,
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}
