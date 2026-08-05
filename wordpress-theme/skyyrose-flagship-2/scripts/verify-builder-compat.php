<?php
/**
 * Verify builder ownership and location contracts without booting WordPress.
 *
 * @package SkyyRoseFlagship2
 */

$GLOBALS['skyyrose2_test_actions']   = array();
$GLOBALS['skyyrose2_test_filters']   = array();
$GLOBALS['skyyrose2_test_support']   = array();
$GLOBALS['skyyrose2_test_meta']      = array();
$GLOBALS['skyyrose2_test_locations'] = array();
$GLOBALS['skyyrose2_test_renders']   = array();
$GLOBALS['skyyrose2_test_loop']      = 0;

/** @param string $hook Hook. @param mixed $callback Callback. */
function add_action( $hook, $callback ) {
	$GLOBALS['skyyrose2_test_actions'][ $hook ][] = $callback;
}

/** @param string $hook Hook. @param mixed $callback Callback. */
function add_filter( $hook, $callback ) {
	$GLOBALS['skyyrose2_test_filters'][ $hook ][] = $callback;
}

/** @param string $feature Feature. */
function add_theme_support( $feature ) {
	$GLOBALS['skyyrose2_test_support'][] = $feature;
}

/** @param mixed $value Value. @return int */
function absint( $value ) {
	return abs( (int) $value );
}

/** @param string $value Value. @return string */
function sanitize_key( $value ) {
	return preg_replace( '/[^a-z0-9_\-]/', '', strtolower( $value ) );
}

/** @param string $value Value. @return string */
function sanitize_html_class( $value ) {
	return preg_replace( '/[^A-Za-z0-9_\-]/', '', $value );
}

/** @param string $value Value. @return string */
function esc_attr( $value ) {
	return htmlspecialchars( $value, ENT_QUOTES, 'UTF-8' );
}

/** @return bool */
function have_posts() {
	return $GLOBALS['skyyrose2_test_loop'] > 0;
}

/** @return void */
function the_post() {
	--$GLOBALS['skyyrose2_test_loop'];
}

/** @return void */
function the_content() {
	echo 'Builder content';
}

/** @return int */
function get_queried_object_id() {
	return 42;
}

/** @param int $post_id ID. @param string $key Key. @return mixed */
function get_post_meta( $post_id, $key ) {
	return $GLOBALS['skyyrose2_test_meta'][ $post_id ][ $key ] ?? '';
}

/** @param string $location Location. @return bool */
function elementor_theme_do_location( $location ) {
	$GLOBALS['skyyrose2_test_renders'][ $location ] = ( $GLOBALS['skyyrose2_test_renders'][ $location ] ?? 0 ) + 1;
	return ! empty( $GLOBALS['skyyrose2_test_locations'][ $location ] );
}

/** Minimal Elementor location manager test double. */
class SkyyRose2_Test_Locations_Manager {
	/** @var int */
	public $calls = 0;

	/** @return void */
	public function register_all_core_location() {
		++$this->calls;
	}
}

define( 'ABSPATH', '/' );
define( 'ELEMENTOR_VERSION', 'test' );
define( 'ET_BUILDER_VERSION', 'test' );
define( 'FL_BUILDER_VERSION', 'test' );

require dirname( __DIR__ ) . '/inc/builder-compat.php';

skyyrose2_builder_support();
foreach ( array( 'elementor', 'elementor-pro', 'et-builder' ) as $feature ) {
	if ( ! in_array( $feature, $GLOBALS['skyyrose2_test_support'], true ) ) {
		throw new RuntimeException( 'Missing builder theme support: ' . $feature );
	}
}

$manager = new SkyyRose2_Test_Locations_Manager();
skyyrose2_register_elementor_locations( $manager );
if ( 1 !== $manager->calls ) {
	throw new RuntimeException( 'Elementor core locations were not registered.' );
}

$GLOBALS['skyyrose2_test_locations']['header'] = true;
if ( ! skyyrose2_render_builder_location( 'header' ) || ! skyyrose2_render_builder_location( 'header' ) ) {
	throw new RuntimeException( 'Assigned Elementor header did not render.' );
}
if ( 1 !== $GLOBALS['skyyrose2_test_renders']['header'] || ! skyyrose2_builder_location_rendered( 'header' ) ) {
	throw new RuntimeException( 'Elementor header location rendered more than once.' );
}
if ( false !== strpos( skyyrose2_builder_content_class(), '--theme-header' ) ) {
	throw new RuntimeException( 'Builder content retained fallback-header spacing.' );
}
$GLOBALS['skyyrose2_builder_locations']['header'] = false;
if ( false === strpos( skyyrose2_builder_content_class(), '--theme-header' ) ) {
	throw new RuntimeException( 'Theme header spacing was not restored for the fallback.' );
}

$builder_meta = array(
	'elementor'      => array( '_elementor_edit_mode' => 'builder' ),
	'divi'           => array( '_et_pb_use_builder' => 'on' ),
	'beaver-builder' => array( '_fl_builder_enabled' => '1' ),
);
foreach ( $builder_meta as $expected => $meta ) {
	$GLOBALS['skyyrose2_test_meta'][42] = $meta;
	if ( $expected !== skyyrose2_page_builder( 42 ) || ! skyyrose2_builder_owns_page( 42 ) ) {
		throw new RuntimeException( 'Builder ownership failed for ' . $expected );
	}
}
$GLOBALS['skyyrose2_test_meta'][42] = array();
if ( '' !== skyyrose2_page_builder( 42 ) || skyyrose2_builder_owns_page( 42 ) ) {
	throw new RuntimeException( 'A page without builder metadata was claimed.' );
}
ob_start();
if ( skyyrose2_render_builder_owned_content( 42 ) || '' !== ob_get_clean() ) {
	throw new RuntimeException( 'Unowned content was rendered through the builder path.' );
}

$GLOBALS['skyyrose2_test_meta'][42] = $builder_meta['elementor'];
$GLOBALS['skyyrose2_test_loop']     = 1;
ob_start();
$content_rendered = skyyrose2_render_builder_owned_content( 42 );
$builder_output   = ob_get_clean();
if ( ! $content_rendered || false === strpos( $builder_output, 'sr2-builder-content' ) || false === strpos( $builder_output, 'Builder content' ) ) {
	throw new RuntimeException( 'Builder-owned content did not render through the shared path.' );
}

$GLOBALS['skyyrose2_test_meta'][42] = $builder_meta['beaver-builder'];
$classes = skyyrose2_builder_body_classes( array( 'page' ) );
if ( ! in_array( 'sr2-builder-beaver-builder', $classes, true ) ) {
	throw new RuntimeException( 'Builder body class was not scoped.' );
}

echo "Builder compatibility: PASS\n";
