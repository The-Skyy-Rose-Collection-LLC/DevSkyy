<?php
/**
 * WordPress.com Custom Headers
 * This file is executed BEFORE platform CSP injection
 *
 * Per WordPress.com docs: https://developer.wordpress.com/docs/guides/add-http-headers
 */

// Content Security Policy for SkyyRose luxury theme
// WordPress.com will merge this with platform nonce-based CSP
header("Content-Security-Policy: " .
    "default-src 'self'; " .
    "script-src 'self' 'unsafe-inline' " .
        "https://cdn.jsdelivr.net " .
        "https://cdnjs.cloudflare.com " .
        "https://cdn.babylonjs.com " .
        "https://stats.wp.com " .
        "https://widgets.wp.com " .
        "https://s0.wp.com " .
        "https://cdn.elementor.com " .
        "https://fonts.googleapis.com " .
        "https://unpkg.com; " .
    "style-src 'self' 'unsafe-inline' " .
        "https://fonts.googleapis.com " .
        "https://fonts-api.wp.com " .
        "https://s0.wp.com " .
        "https://cdn.elementor.com; " .
    "font-src 'self' data: " .
        "https://fonts.gstatic.com " .
        "https://fonts-api.wp.com; " .
    "img-src 'self' data: https: blob:; " .
    "connect-src 'self' " .
        "https://stats.wp.com " .
        "https://public-api.wordpress.com " .
        "https://api.skyyrose.co; " .
    "frame-src 'self' " .
        "https://widgets.wp.com " .
        "https://jetpack.wordpress.com; " .
    "object-src 'none'; " .
    "base-uri 'self';"
);

// Additional security headers
header('X-XSS-Protection: 1; mode=block');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: SAMEORIGIN');
header('Referrer-Policy: strict-origin-when-cross-origin');
header('Strict-Transport-Security: max-age=31536000; includeSubDomains; preload');
header('Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=()');

// Remove server signature
header_remove('X-Powered-By');
header_remove('Server');
?>
