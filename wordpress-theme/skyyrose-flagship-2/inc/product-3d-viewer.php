<?php
/**
 * Fail-closed product GLB resolution and progressive 3D viewer markup.
 *
 * The manifest is intentionally separate from WooCommerce product metadata:
 * product metadata is editable store state, while this file is the committed
 * release boundary for founder-approved visual assets.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

/**
 * Read the committed approved-model manifest.
 *
 * @return array<string,mixed>
 */
function skyyrose2_approved_model_manifest() {
	static $manifest = null;

	if ( null !== $manifest ) {
		return $manifest;
	}

	$path = SKYYROSE2_DIR . '/assets/sot/3d/approved-models.json';
	if ( ! is_readable( $path ) ) {
		$manifest = array();
		return $manifest;
	}

	$decoded = json_decode( (string) file_get_contents( $path ), true );
	$manifest = is_array( $decoded ) && 'skyyrose.approved-models.v2' === ( $decoded['schema'] ?? '' ) ? $decoded : array();
	return $manifest;
}

/**
 * Detect network-capable resource references anywhere in a GLB JSON document.
 *
 * @param mixed $value JSON value.
 * @return bool
 */
function skyyrose2_glb_document_has_external_reference( $value ) {
	if ( ! is_array( $value ) ) {
		return is_string( $value ) && false !== stripos( $value, 'lottie' );
	}

	foreach ( $value as $key => $item ) {
		if ( is_string( $key ) && in_array( strtolower( $key ), array( 'uri', 'url' ), true ) ) {
			return true;
		}
		if ( skyyrose2_glb_document_has_external_reference( $item ) ) {
			return true;
		}
	}

	return false;
}

/**
 * Detect prohibited decoder-dependent extension keys anywhere in GLB JSON.
 *
 * Valid glTF declares extensions at the document root, but the actual payload
 * lives on nested objects. Checking both locations prevents an undeclared
 * extension payload from bypassing the self-contained asset profile.
 *
 * @param mixed $value JSON value.
 * @return bool
 */
function skyyrose2_glb_document_has_blocked_extension( $value ) {
	if ( ! is_array( $value ) ) {
		return false;
	}

	$blocked_extensions = array(
		'EXT_meshopt_compression',
		'KHR_draco_mesh_compression',
		'KHR_texture_basisu',
	);
	foreach ( $value as $key => $item ) {
		if ( is_string( $key ) && in_array( $key, $blocked_extensions, true ) ) {
			return true;
		}
		if ( skyyrose2_glb_document_has_blocked_extension( $item ) ) {
			return true;
		}
	}

	return false;
}

/**
 * Validate a self-contained GLB before exposing it to the browser.
 *
 * @param string $path Absolute model path.
 * @return bool
 */
function skyyrose2_validate_approved_glb_file( $path ) {
	$size = is_file( $path ) ? filesize( $path ) : false;
	if ( false === $size || $size < 20 || $size > 50 * 1024 * 1024 ) {
		return false;
	}

	$handle = fopen( $path, 'rb' );
	if ( false === $handle ) {
		return false;
	}

	$header       = fread( $handle, 12 );
	$chunk_header = fread( $handle, 8 );
	if ( 12 !== strlen( (string) $header ) || 8 !== strlen( (string) $chunk_header ) ) {
		fclose( $handle );
		return false;
	}

	$header_data = unpack( 'a4magic/Vversion/Vlength', $header );
	$chunk_data  = unpack( 'Vlength/Vtype', $chunk_header );
	if (
		! is_array( $header_data )
		|| ! is_array( $chunk_data )
		|| 'glTF' !== $header_data['magic']
		|| 2 !== $header_data['version']
		|| $size !== $header_data['length']
		|| 0x4E4F534A !== $chunk_data['type']
		|| $chunk_data['length'] < 2
		|| $chunk_data['length'] > $size - 20
	) {
		fclose( $handle );
		return false;
	}

	$json = fread( $handle, $chunk_data['length'] );
	fclose( $handle );
	$document = json_decode( rtrim( (string) $json, " \t\n\r\0\x0B" ), true );
	if ( ! is_array( $document ) || 2 !== (int) ( $document['asset']['version'] ?? 0 ) ) {
		return false;
	}

	$blocked_extensions = array(
		'EXT_meshopt_compression',
		'KHR_draco_mesh_compression',
		'KHR_texture_basisu',
	);
	$extensions         = array_merge(
		is_array( $document['extensionsUsed'] ?? null ) ? $document['extensionsUsed'] : array(),
		is_array( $document['extensionsRequired'] ?? null ) ? $document['extensionsRequired'] : array()
	);
	if (
		array_intersect( $blocked_extensions, $extensions )
		|| skyyrose2_glb_document_has_blocked_extension( $document )
	) {
		return false;
	}

	if ( skyyrose2_glb_document_has_external_reference( $document ) ) {
		return false;
	}

	return true;
}

/**
 * Resolve an approved GLB for an exact WooCommerce product.
 *
 * A resolver miss is the safe state. No filename glob, product meta field, or
 * provider output may make a model visible without all release attestations.
 *
 * @param WC_Product $product WooCommerce product.
 * @return array<string,mixed>|null
 */
function skyyrose2_resolve_approved_product_model( $product ) {
	if ( ! $product instanceof WC_Product ) {
		return null;
	}

	$sku = strtolower( trim( (string) $product->get_sku() ) );
	if ( ! preg_match( '/^[a-z]{2,4}-[0-9]{3}$/', $sku ) ) {
		return null;
	}

	$manifest = skyyrose2_approved_model_manifest();
	$entry    = $manifest['models'][ $sku ] ?? null;
	if ( ! is_array( $entry ) || strtolower( (string) ( $entry['sku'] ?? '' ) ) !== $sku ) {
		return null;
	}

	$relative_path = 'models/' . $sku . '.glb';
	if ( $relative_path !== (string) ( $entry['path'] ?? '' ) || array_key_exists( 'url', $entry ) ) {
		return null;
	}

	$model_root = realpath( SKYYROSE2_DIR . '/assets/sot/3d/models' );
	$model_path = realpath( SKYYROSE2_DIR . '/assets/sot/3d/' . $relative_path );
	if (
		false === $model_root
		|| false === $model_path
		|| 0 !== strpos( $model_path, $model_root . DIRECTORY_SEPARATOR )
		|| ! is_readable( $model_path )
	) {
		return null;
	}

	$sha256 = strtolower( (string) ( $entry['model_sha256'] ?? '' ) );
	$reference_sha256 = $entry['reference_sha256'] ?? null;
	$required_angles  = array( 'front', 'back', 'left', 'right', 'detail-1' );
	if (
		'approved' !== strtolower( (string) ( $entry['status'] ?? '' ) )
		|| 'approved' !== strtolower( (string) ( $entry['gate_disposition'] ?? '' ) )
		|| true !== ( $entry['provenance_verified'] ?? false )
		|| true !== ( $entry['policy_attestation_verified'] ?? false )
		|| true !== ( $entry['founder_approval_verified'] ?? false )
		|| 'self-contained-glb-v1' !== ( $entry['asset_profile'] ?? '' )
		|| false !== ( $entry['external_resources'] ?? null )
		|| 'none' !== ( $entry['compression'] ?? '' )
		|| false !== ( $entry['ktx2'] ?? null )
		|| false !== ( $entry['lottie'] ?? null )
		|| ! preg_match( '/^[a-f0-9]{64}$/', $sha256 )
		|| ! is_array( $reference_sha256 )
		|| count( $required_angles ) !== count( $reference_sha256 )
		|| array_diff( $required_angles, array_keys( $reference_sha256 ) )
	) {
		return null;
	}
	foreach ( $required_angles as $angle ) {
		if ( ! is_string( $reference_sha256[ $angle ] ) || ! preg_match( '/^[a-f0-9]{64}$/i', $reference_sha256[ $angle ] ) ) {
			return null;
		}
	}
	$actual_sha256 = hash_file( 'sha256', $model_path );
	if (
		! is_string( $actual_sha256 )
		|| ! hash_equals( $sha256, strtolower( $actual_sha256 ) )
		|| ! skyyrose2_validate_approved_glb_file( $model_path )
	) {
		return null;
	}

	$entry['sku']              = $sku;
	$entry['url']              = SKYYROSE2_URI . '/assets/sot/3d/' . $relative_path;
	$entry['model_sha256']     = $sha256;
	$entry['reference_sha256'] = $reference_sha256;
	return $entry;
}

/**
 * Enqueue the viewer only where an approved model will actually render.
 *
 * @return void
 */
function skyyrose2_enqueue_product_3d_viewer() {
	if ( ! function_exists( 'is_product' ) || ! is_product() ) {
		return;
	}

	$product = wc_get_product( get_queried_object_id() );
	if ( ! skyyrose2_resolve_approved_product_model( $product ) ) {
		return;
	}
	$suffix = defined( 'SCRIPT_DEBUG' ) && SCRIPT_DEBUG ? '' : '.min';

	wp_enqueue_style(
		'skyyrose2-product-3d-viewer',
		SKYYROSE2_URI . '/assets/css/product-3d-viewer' . $suffix . '.css',
		array( 'skyyrose2-theme' ),
		SKYYROSE2_VERSION
	);
	wp_enqueue_script(
		'skyyrose2-model-viewer',
		SKYYROSE2_URI . '/assets/js/lib/model-viewer.min.js',
		array(),
		'4.1.0',
		true
	);
	wp_script_add_data( 'skyyrose2-model-viewer', 'strategy', 'defer' );
	wp_add_inline_script(
		'skyyrose2-model-viewer',
		'window.ModelViewerElement=window.ModelViewerElement||{};window.ModelViewerElement.dracoDecoderLocation=' . wp_json_encode( SKYYROSE2_URI . '/assets/js/lib/disabled/draco/' ) . ';window.ModelViewerElement.ktx2TranscoderLocation=' . wp_json_encode( SKYYROSE2_URI . '/assets/js/lib/disabled/ktx2/' ) . ';window.ModelViewerElement.lottieLoaderLocation=' . wp_json_encode( SKYYROSE2_URI . '/assets/js/lib/disabled/LottieLoader.js' ) . ';',
		'before'
	);
	wp_enqueue_script(
		'skyyrose2-product-3d-viewer',
		SKYYROSE2_URI . '/assets/js/product-3d-viewer' . $suffix . '.js',
		array( 'skyyrose2-model-viewer' ),
		SKYYROSE2_VERSION,
		true
	);
	wp_script_add_data( 'skyyrose2-product-3d-viewer', 'strategy', 'defer' );
}
add_action( 'wp_enqueue_scripts', 'skyyrose2_enqueue_product_3d_viewer', 25 );

/**
 * Render the poster-first product viewer for an approved model.
 *
 * @param WC_Product $product WooCommerce product.
 * @return void
 */
function skyyrose2_render_product_3d_viewer( $product ) {
	$model = skyyrose2_resolve_approved_product_model( $product );
	if ( ! $model ) {
		return;
	}

	$poster = $product->get_image_id() ? wp_get_attachment_image_url( $product->get_image_id(), 'large' ) : '';
	$alt    = sprintf( __( 'Interactive 3D view of %s', 'skyyrose-flagship-2' ), $product->get_name() );
	?>
	<section
		class="sr2-product-3d"
		data-sr2-product-viewer
		data-model-url="<?php echo esc_url( $model['url'] ); ?>"
		data-poster="<?php echo esc_url( $poster ? $poster : '' ); ?>"
		data-alt="<?php echo esc_attr( $alt ); ?>"
		data-sku="<?php echo esc_attr( $model['sku'] ); ?>"
		aria-labelledby="sr2-product-3d-title-<?php echo esc_attr( $product->get_id() ); ?>"
	>
		<div class="sr2-product-3d__heading">
			<p class="sr2-eyebrow"><?php esc_html_e( 'The piece, in space', 'skyyrose-flagship-2' ); ?></p>
			<h2 id="sr2-product-3d-title-<?php echo esc_attr( $product->get_id() ); ?>"><?php esc_html_e( 'Turn the work around.', 'skyyrose-flagship-2' ); ?></h2>
			<p><?php esc_html_e( 'Drag to inspect the approved model. The original product imagery remains the source of truth.', 'skyyrose-flagship-2' ); ?></p>
		</div>
		<div class="sr2-product-3d__stage">
			<div class="sr2-product-3d__fallback" data-sr2-viewer-fallback>
				<?php if ( $poster ) : ?>
					<img src="<?php echo esc_url( $poster ); ?>" alt="<?php echo esc_attr( $product->get_name() ); ?>" width="900" height="1200" loading="lazy" decoding="async">
				<?php endif; ?>
				<p><?php esc_html_e( 'Interactive view loading when available.', 'skyyrose-flagship-2' ); ?></p>
			</div>
			<model-viewer
				class="sr2-product-3d__model"
				data-sr2-model
				alt="<?php echo esc_attr( $alt ); ?>"
				camera-controls
				loading="lazy"
				environment-image="neutral"
				shadow-intensity="1"
				interaction-prompt="none"
				hidden
			></model-viewer>
			<div class="sr2-product-3d__status" data-sr2-viewer-status role="status" aria-live="polite"></div>
			<div class="sr2-product-3d__controls" data-sr2-viewer-controls hidden>
				<button type="button" class="sr2-button" data-sr2-viewer-rotate aria-pressed="false"><?php esc_html_e( 'Auto-rotate', 'skyyrose-flagship-2' ); ?></button>
				<button type="button" class="sr2-button" data-sr2-viewer-reset><?php esc_html_e( 'Reset view', 'skyyrose-flagship-2' ); ?></button>
			</div>
		</div>
	</section>
	<?php
}
