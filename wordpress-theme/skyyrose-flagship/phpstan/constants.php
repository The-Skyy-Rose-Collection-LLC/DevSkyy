<?php
/**
 * PHPStan symbol-discovery declarations. NEVER loaded by WordPress.
 *
 * The real definitions live in functions.php. PHPStan can constant-fold a
 * define() whose value is a literal (SKYYROSE_VERSION), but not one whose
 * value comes from a function call:
 *
 *     define( 'SKYYROSE_DIR', get_template_directory() );
 *
 * so it reports "Constant SKYYROSE_DIR not found" in every consuming file.
 * Declaring them here (scanFiles) makes the symbols discoverable; pairing
 * that with `dynamicConstantNames` in phpstan.neon stops PHPStan narrowing
 * them to the placeholder literals below — which is also simply true: these
 * are absolute paths/URLs that differ per install.
 *
 * Do not add constants with literal values here — those already resolve from
 * functions.php, and a second copy would drift (SKYYROSE_VERSION especially).
 *
 * @package SkyyRose
 */

define( 'SKYYROSE_DIR', '/path/to/theme' );
define( 'SKYYROSE_URI', 'https://example.com/wp-content/themes/skyyrose' );

// WordPress core runtime constant (wp-includes/default-constants.php); not
// covered by the WordPress stub package because it is defined at boot.
define( 'COOKIEPATH', '/' );
