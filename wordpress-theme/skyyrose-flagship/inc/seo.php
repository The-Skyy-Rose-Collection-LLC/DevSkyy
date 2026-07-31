<?php
/**
 * SEO Optimization Features
 *
 * Loads focused SEO modules in hook-registration order.
 *
 * @package SkyyRose
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

require_once __DIR__ . '/seo-structured-data.php';
require_once __DIR__ . '/seo-social-meta.php';
require_once __DIR__ . '/seo-discovery.php';
