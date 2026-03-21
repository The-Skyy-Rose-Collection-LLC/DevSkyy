<?php
/**
 * Plugin Name:       SkyyRose Experience Engine
 * Plugin URI:        https://skyyrose.com/experience-engine
 * Description:       AI-powered UX orchestration that analyzes, personalizes, and enhances the virtual shopping experience. Zero config — lives, breathes, and elevates the SkyyRose brand automatically.
 * Version:           1.0.0
 * Requires at least: 6.0
 * Requires PHP:      8.0
 * Author:            SkyyRose Engineering
 * Author URI:        https://skyyrose.com
 * License:           GPL-2.0-or-later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       skyyrose-experience-engine
 * Domain Path:       /languages
 * WC requires at least: 8.0
 * WC tested up to:   9.0
 *
 * @package SkyyRose_Experience_Engine
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*--------------------------------------------------------------
 * Constants
 *--------------------------------------------------------------*/

define( 'SEE_VERSION', '1.0.0' );
define( 'SEE_DIR', plugin_dir_path( __FILE__ ) );
define( 'SEE_URI', plugin_dir_url( __FILE__ ) );
define( 'SEE_BASENAME', plugin_basename( __FILE__ ) );
define( 'SEE_SLUG', 'skyyrose-experience-engine' );

/*--------------------------------------------------------------
 * Autoloader
 *--------------------------------------------------------------*/

spl_autoload_register( function ( string $class ) {
	$prefix = 'SEE_';
	if ( strpos( $class, $prefix ) !== 0 ) {
		return;
	}

	$relative = substr( $class, strlen( $prefix ) );
	$filename = 'class-see-' . strtolower( str_replace( '_', '-', $relative ) ) . '.php';

	$directories = array(
		SEE_DIR . 'includes/',
		SEE_DIR . 'includes/modules/',
		SEE_DIR . 'includes/integrations/',
		SEE_DIR . 'includes/rest-api/',
		SEE_DIR . 'admin/',
	);

	foreach ( $directories as $dir ) {
		$file = $dir . $filename;
		if ( file_exists( $file ) ) {
			require_once $file;
			return;
		}
	}
} );

/*--------------------------------------------------------------
 * Activation / Deactivation
 *--------------------------------------------------------------*/

register_activation_hook( __FILE__, array( 'SEE_Activator', 'activate' ) );
register_deactivation_hook( __FILE__, array( 'SEE_Deactivator', 'deactivate' ) );

/*--------------------------------------------------------------
 * Bootstrap
 *--------------------------------------------------------------*/

add_action( 'plugins_loaded', function () {
	SEE_Plugin::instance()->run();
}, 10 );
