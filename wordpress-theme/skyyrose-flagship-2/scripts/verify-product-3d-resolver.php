<?php
/**
 * Verify the fail-closed product GLB resolver without booting WordPress.
 *
 * @package SkyyRoseFlagship2
 */

class WC_Product {
	/** @var string */
	private $sku;

	/** @param string $sku Product SKU. */
	public function __construct( $sku ) {
		$this->sku = $sku;
	}

	/** @return string */
	public function get_sku() {
		return $this->sku;
	}
}

/** WordPress hook stub. */
function add_action() {}

$test_root = sys_get_temp_dir() . '/skyyrose2-glb-' . bin2hex( random_bytes( 8 ) );
$model_dir = $test_root . '/assets/sot/3d/models';
if ( ! mkdir( $model_dir, 0700, true ) && ! is_dir( $model_dir ) ) {
	throw new RuntimeException( 'Unable to create resolver test directory.' );
}

$model_path    = $model_dir . '/sg-001.glb';
$manifest_path = $test_root . '/assets/sot/3d/approved-models.json';

try {
	$document = json_encode( array( 'asset' => array( 'version' => '2.0' ) ) );
	$document .= str_repeat( ' ', ( 4 - strlen( $document ) % 4 ) % 4 );
	$length    = 20 + strlen( $document );
	$glb       = pack( 'a4VV', 'glTF', 2, $length ) . pack( 'VV', strlen( $document ), 0x4E4F534A ) . $document;
	file_put_contents( $model_path, $glb );
	$model_hash     = hash_file( 'sha256', $model_path );
	$reference_hash = str_repeat( 'a', 64 );
	$manifest       = array(
		'schema' => 'skyyrose.approved-models.v2',
		'models' => array(
			'sg-001' => array(
				'sku'                         => 'sg-001',
				'path'                        => 'models/sg-001.glb',
				'status'                      => 'approved',
				'gate_disposition'            => 'approved',
				'provenance_verified'         => true,
				'policy_attestation_verified' => true,
				'founder_approval_verified'   => true,
				'asset_profile'               => 'self-contained-glb-v1',
				'external_resources'          => false,
				'compression'                 => 'none',
				'ktx2'                        => false,
				'lottie'                      => false,
				'model_sha256'                => $model_hash,
				'reference_sha256'            => array_fill_keys( array( 'front', 'back', 'left', 'right', 'detail-1' ), $reference_hash ),
			),
		),
	);
	file_put_contents( $manifest_path, json_encode( $manifest ) );

	define( 'ABSPATH', '/' );
	define( 'SKYYROSE2_DIR', $test_root );
	define( 'SKYYROSE2_URI', 'https://example.test/wp-content/themes/skyyrose-flagship-2' );

	require dirname( __DIR__ ) . '/inc/product-3d-viewer.php';

	if ( null !== skyyrose2_resolve_approved_product_model( new WC_Product( '../sg-001' ) ) ) {
		throw new RuntimeException( 'Unsafe SKU resolved.' );
	}

	$resolved = skyyrose2_resolve_approved_product_model( new WC_Product( 'sg-001' ) );
	if ( ! is_array( $resolved ) || false === strpos( $resolved['url'], '/assets/sot/3d/models/sg-001.glb' ) ) {
		throw new RuntimeException( 'Valid approved local GLB did not resolve.' );
	}

	file_put_contents( $model_path, "tampered", FILE_APPEND );
	if ( null !== skyyrose2_resolve_approved_product_model( new WC_Product( 'sg-001' ) ) ) {
		throw new RuntimeException( 'Tampered GLB resolved.' );
	}

	$external_document = json_encode(
		array(
			'asset'  => array( 'version' => '2.0' ),
			'images' => array( array( 'uri' => 'https://example.invalid/product.png' ) ),
		)
	);
	$external_document .= str_repeat( ' ', ( 4 - strlen( $external_document ) % 4 ) % 4 );
	$external_length    = 20 + strlen( $external_document );
	$external_glb       = pack( 'a4VV', 'glTF', 2, $external_length ) . pack( 'VV', strlen( $external_document ), 0x4E4F534A ) . $external_document;
	file_put_contents( $model_path, $external_glb );
	if ( skyyrose2_validate_approved_glb_file( $model_path ) ) {
		throw new RuntimeException( 'GLB with an external resource passed validation.' );
	}

	echo "Product 3D resolver: PASS\n";
} finally {
	foreach ( array( $manifest_path, $model_path ) as $path ) {
		if ( is_file( $path ) ) {
			unlink( $path );
		}
	}
	foreach ( array( $model_dir, dirname( $model_dir ), dirname( dirname( $model_dir ) ), dirname( dirname( dirname( $model_dir ) ) ), $test_root ) as $directory ) {
		if ( is_dir( $directory ) ) {
			rmdir( $directory );
		}
	}
}
