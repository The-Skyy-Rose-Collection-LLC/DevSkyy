<?php
/**
 * Garment Upload Shortcode — [skyyrose_garment_upload]
 *
 * Registers the upload gate UI as a shortcode and conditionally enqueues the
 * classifier/gate JS + CSS only on pages that use it (zero cost elsewhere).
 *
 * Usage:
 *   [skyyrose_garment_upload]
 *   [skyyrose_garment_upload endpoint="/wp-json/skyyrose/v1/upload" label="Upload your garment"]
 *
 * The classifier runs entirely client-side via Transformers.js. No paid API
 * is hit during classification — only the configured endpoint is called
 * AFTER the verdict accepts the upload.
 *
 * @package SkyyRose
 * @since   1.1.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Register the upload gate scripts and styles.
 *
 * Registered (not enqueued) — the shortcode renderer enqueues on demand so
 * pages without the upload form don't pay the asset cost.
 *
 * @since 1.1.0
 * @return void
 */
function skyyrose_register_garment_upload_assets() {
	wp_register_style(
		'skyyrose-garment-upload',
		SKYYROSE_ASSETS_URI . '/css/components/garment-upload-gate.css',
		array(),
		SKYYROSE_VERSION
	);

	wp_register_script(
		'skyyrose-garment-upload',
		SKYYROSE_ASSETS_URI . '/js/components/garment-upload-gate.js',
		array(),
		SKYYROSE_VERSION,
		array(
			'in_footer' => true,
			'strategy'  => 'defer',
		)
	);

	// ES module — required for the dynamic CDN import inside garment-classifier.js.
	add_filter( 'script_loader_tag', 'skyyrose_garment_upload_module_tag', 10, 3 );
}
add_action( 'init', 'skyyrose_register_garment_upload_assets' );

/**
 * Add type="module" to our upload-gate script tag.
 *
 * @param string $tag    Generated <script> HTML.
 * @param string $handle Script handle.
 * @param string $src    Script URL.
 * @return string Filtered tag.
 */
function skyyrose_garment_upload_module_tag( $tag, $handle, $src ) {
	if ( 'skyyrose-garment-upload' !== $handle ) {
		return $tag;
	}
	// The script is enqueued via wp_enqueue_script() — this filter only
	// rewrites the tag to add type="module". PHPCS sniff misses that context.
	return sprintf(
		'<script type="module" src="%s" defer></script>' . "\n", // phpcs:ignore WordPress.WP.EnqueuedResources.NonEnqueuedScript
		esc_url( $src )
	);
}

/**
 * Render the upload gate shortcode.
 *
 * @since 1.1.0
 * @param array $atts Shortcode attributes.
 * @return string HTML markup.
 */
function skyyrose_garment_upload_shortcode( $atts ) {
	$atts = shortcode_atts(
		array(
			'endpoint' => '',
			'label'    => __( 'Upload a garment reference', 'skyyrose' ),
			'help'     => __( 'JPEG, PNG, or WebP. Max 12 MB. Clear, well-lit shots work best.', 'skyyrose' ),
		),
		$atts,
		'skyyrose_garment_upload'
	);

	wp_enqueue_style( 'skyyrose-garment-upload' );
	wp_enqueue_script( 'skyyrose-garment-upload' );

	wp_localize_script(
		'skyyrose-garment-upload',
		'skyyroseUploadGate',
		array(
			'nonce' => wp_create_nonce( 'skyyrose_garment_upload' ),
		)
	);

	$instance_id = wp_unique_id( 'sr-upload-' );

	ob_start();
	?>
	<form
		class="sr-upload"
		data-skyyrose-upload-gate
		data-phase="idle"
		data-endpoint="<?php echo esc_url( $atts['endpoint'] ); ?>"
		id="<?php echo esc_attr( $instance_id ); ?>"
		aria-busy="false"
	>
		<label class="sr-upload__label" for="<?php echo esc_attr( $instance_id ); ?>-file">
			<?php echo esc_html( $atts['label'] ); ?>
		</label>

		<input
			type="file"
			id="<?php echo esc_attr( $instance_id ); ?>-file"
			class="sr-upload__file"
			data-upload-file
			accept="image/jpeg,image/png,image/webp"
		/>

		<p class="sr-upload__help"><?php echo esc_html( $atts['help'] ); ?></p>

		<figure class="sr-upload__previewWrap" aria-live="polite">
			<img class="sr-upload__preview" data-upload-preview alt="" />
		</figure>

		<progress
			class="sr-upload__progress"
			data-upload-progress
			max="100"
			value="0"
			aria-label="<?php esc_attr_e( 'Vision model loading progress', 'skyyrose' ); ?>"
		></progress>

		<p class="sr-upload__status" data-upload-status role="status"></p>

		<div class="sr-upload__verdict" data-upload-verdict></div>

		<div class="sr-upload__actions">
			<button type="button" class="sr-upload__reset" data-upload-reset>
				<?php esc_html_e( 'Reset', 'skyyrose' ); ?>
			</button>
			<button type="button" class="sr-upload__submit" data-upload-submit disabled>
				<?php esc_html_e( 'Submit', 'skyyrose' ); ?>
			</button>
		</div>
	</form>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'skyyrose_garment_upload', 'skyyrose_garment_upload_shortcode' );
