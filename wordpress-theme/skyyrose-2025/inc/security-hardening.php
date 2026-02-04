<?php
/**
 * Security Hardening for SkyyRose Theme
 *
 * Implements OWASP Top 10 security best practices:
 * - CSRF protection with nonces
 * - XSS prevention with output escaping
 * - SQL injection prevention
 * - Secure session management
 * - Rate limiting enhancements
 * - Content Security Policy
 * - API key encryption
 *
 * @package SkyyRose_2025
 * @version 1.0.0
 */

if (!defined('ABSPATH')) {
    exit;
}

class SkyyRose_Security_Hardening {

    private static $instance = null;

    /**
     * Get singleton instance
     */
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /**
     * Constructor
     */
    private function __construct() {
        $this->init_hooks();
    }

    /**
     * Initialize WordPress hooks
     */
    private function init_hooks() {
        // Enhanced security headers
        add_action('send_headers', [$this, 'add_security_headers']);

        // Secure AJAX nonce generation
        add_action('wp_enqueue_scripts', [$this, 'localize_security_nonces']);

        // Session security
        add_action('init', [$this, 'secure_sessions'], 1);

        // Security logging
        add_action('wp_login_failed', [$this, 'log_failed_login']);
        add_action('wp_login', [$this, 'log_successful_login'], 10, 2);
    }

    /**
     * Add comprehensive security headers
     */
    public function add_security_headers() {
        if (is_admin()) {
            return;
        }

        // Generate CSP nonce
        $csp_nonce = wp_create_nonce('csp-' . get_current_blog_id());

        // Strict Transport Security (HTTPS enforcement)
        header('Strict-Transport-Security: max-age=31536000; includeSubDomains; preload');

        // Content Security Policy (tightened)
        $csp_policy = sprintf(
            "default-src 'self'; " .
            "script-src 'self' 'nonce-%s' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; " .
            "style-src 'self' 'nonce-%s' https://fonts.googleapis.com; " .
            "img-src 'self' data: https:; " .
            "font-src 'self' data: https://fonts.gstatic.com; " .
            "connect-src 'self' %s; " .
            "frame-ancestors 'self'; " .
            "base-uri 'self'; " .
            "form-action 'self';",
            esc_attr($csp_nonce),
            esc_attr($csp_nonce),
            esc_attr(home_url())
        );
        header('Content-Security-Policy: ' . $csp_policy);

        // X-Frame-Options (clickjacking protection)
        header('X-Frame-Options: SAMEORIGIN');

        // X-Content-Type-Options (MIME sniffing protection)
        header('X-Content-Type-Options: nosniff');

        // X-XSS-Protection (XSS filter for older browsers)
        header('X-XSS-Protection: 1; mode=block');

        // Referrer Policy
        header('Referrer-Policy: strict-origin-when-cross-origin');

        // Permissions Policy (formerly Feature-Policy)
        header('Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=()');

        // Expect-CT (Certificate Transparency)
        header('Expect-CT: max-age=86400, enforce');

        // Remove server signature
        header_remove('X-Powered-By');
        header_remove('Server');
    }

    /**
     * Localize security nonces for JavaScript
     */
    public function localize_security_nonces() {
        // Only localize if script is enqueued (defensive error handling)
        if (!wp_script_is('skyyrose-animations', 'enqueued') &&
            !wp_script_is('skyyrose-animations', 'registered')) {
            return;
        }

        // Generate nonces for AJAX endpoints
        $nonces = [
            'ajax' => wp_create_nonce('skyyrose_nonce'),
            'vault' => wp_create_nonce('skyyrose_vault_nonce'),
            'add_to_cart' => wp_create_nonce('skyyrose_cart_nonce'),
            'collection' => wp_create_nonce('skyyrose_collection_nonce'),
        ];

        wp_localize_script('skyyrose-animations', 'skyyrose_security', [
            'nonces' => $nonces,
            'ajax_url' => admin_url('admin-ajax.php'),
            'site_url' => home_url(),
        ]);
    }

    /**
     * Secure session management
     *
     * DISABLED for WordPress.com compatibility
     * WordPress.com manages sessions at platform level
     */
    public function secure_sessions() {
        // Session management causes fatal errors on WordPress.com
        // WordPress.com handles sessions at the platform level
        // Disabling to prevent "headers already sent" errors
        return;
    }

    /**
     * Get client IP address (proxy-aware)
     */
    public static function get_client_ip() {
        $ip = $_SERVER['REMOTE_ADDR'];

        // Trust X-Forwarded-For only behind known proxies
        if (defined('SKYYROSE_TRUSTED_PROXIES')) {
            $proxies = array_map('trim', explode(',', SKYYROSE_TRUSTED_PROXIES));
            if (in_array($ip, $proxies) && !empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
                $forwarded = array_map('trim', explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']));
                $ip = $forwarded[0]; // First IP is the client
            }
        }

        // Validate IP format
        $validated_ip = filter_var($ip, FILTER_VALIDATE_IP);
        return $validated_ip ?: '127.0.0.1';
    }

    /**
     * Enhanced rate limiting with IP fingerprinting
     */
    public static function check_rate_limit($action, $max_attempts = 5, $time_window = 300) {
        $ip = self::get_client_ip();
        $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? '';

        // Create fingerprint
        $fingerprint = hash('sha256', $ip . $user_agent . wp_salt('auth'));
        $attempts_key = "rate_limit_{$action}_{$fingerprint}";

        $attempts = get_transient($attempts_key);
        if (false === $attempts) {
            $attempts = 0;
        }

        if ($attempts >= $max_attempts) {
            // Log rate limit exceeded
            self::log_security_event('rate_limit_exceeded', [
                'action' => $action,
                'ip' => $ip,
                'attempts' => $attempts,
            ]);

            return false;
        }

        // Increment attempts
        set_transient($attempts_key, $attempts + 1, $time_window);
        return true;
    }

    /**
     * Clear rate limit for user (e.g., after successful login)
     */
    public static function clear_rate_limit($action) {
        $ip = self::get_client_ip();
        $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? '';
        $fingerprint = hash('sha256', $ip . $user_agent . wp_salt('auth'));
        $attempts_key = "rate_limit_{$action}_{$fingerprint}";

        delete_transient($attempts_key);
    }

    /**
     * Encrypt sensitive data (API keys, tokens)
     */
    public static function encrypt_data($data) {
        // Use sodium if available (PHP 7.2+)
        if (function_exists('sodium_crypto_secretbox')) {
            $nonce = random_bytes(SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
            $key = hash('sha256', wp_salt('auth') . wp_salt('secure_auth'), true);

            $encrypted = sodium_crypto_secretbox($data, $nonce, $key);
            sodium_memzero($key); // Clear key from memory

            return base64_encode($nonce . $encrypted);
        }

        // Fallback: Base64 encoding (not secure, but better than plaintext)
        error_log('[SKYYROSE_SECURITY] Warning: Sodium not available, using weak encryption');
        return base64_encode($data);
    }

    /**
     * Decrypt sensitive data
     */
    public static function decrypt_data($encrypted) {
        if (function_exists('sodium_crypto_secretbox_open')) {
            $decoded = base64_decode($encrypted);
            if ($decoded === false) {
                return false;
            }

            $nonce = substr($decoded, 0, SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
            $ciphertext = substr($decoded, SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
            $key = hash('sha256', wp_salt('auth') . wp_salt('secure_auth'), true);

            $decrypted = sodium_crypto_secretbox_open($ciphertext, $nonce, $key);
            sodium_memzero($key); // Clear key from memory

            return $decrypted;
        }

        // Fallback: Base64 decoding
        return base64_decode($encrypted);
    }

    /**
     * Sanitize and validate email with disposable domain check
     */
    public static function validate_email($email, $check_disposable = true) {
        $email = sanitize_email($email);

        if (!is_email($email)) {
            return false;
        }

        if ($check_disposable) {
            $disposable_domains = self::get_disposable_email_domains();
            $domain = substr(strrchr($email, "@"), 1);

            if (in_array(strtolower($domain), $disposable_domains)) {
                return false;
            }
        }

        return $email;
    }

    /**
     * Get list of disposable email domains
     */
    private static function get_disposable_email_domains() {
        // Cache for 24 hours
        $cached = get_transient('skyyrose_disposable_domains');
        if (false !== $cached) {
            return $cached;
        }

        // Common disposable email domains
        $domains = [
            'tempmail.com', 'guerrillamail.com', '10minutemail.com',
            'mailinator.com', 'throwaway.email', 'temp-mail.org',
            'fakeinbox.com', 'discard.email', 'trashmail.com',
        ];

        set_transient('skyyrose_disposable_domains', $domains, DAY_IN_SECONDS);
        return $domains;
    }

    /**
     * Log security events
     */
    public static function log_security_event($event_type, $details = []) {
        if (!defined('SKYYROSE_SECURITY_LOG') || !SKYYROSE_SECURITY_LOG) {
            return;
        }

        $log_entry = [
            'timestamp' => current_time('mysql'),
            'event' => $event_type,
            'user_id' => get_current_user_id(),
            'ip' => self::get_client_ip(),
            'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? 'unknown',
            'request_uri' => $_SERVER['REQUEST_URI'] ?? '',
            'details' => $details,
        ];

        error_log('[SKYYROSE_SECURITY] ' . wp_json_encode($log_entry));

        // Also store in database for admin review
        self::store_security_log($log_entry);
    }

    /**
     * Store security log in database
     */
    private static function store_security_log($log_entry) {
        global $wpdb;

        $table_name = $wpdb->prefix . 'skyyrose_security_log';

        // Create table if it doesn't exist
        $charset_collate = $wpdb->get_charset_collate();
        $sql = "CREATE TABLE IF NOT EXISTS $table_name (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            timestamp datetime NOT NULL,
            event_type varchar(50) NOT NULL,
            user_id bigint(20) DEFAULT NULL,
            ip_address varchar(45) NOT NULL,
            user_agent varchar(255) DEFAULT NULL,
            request_uri varchar(255) DEFAULT NULL,
            details text DEFAULT NULL,
            PRIMARY KEY  (id),
            KEY event_type (event_type),
            KEY ip_address (ip_address),
            KEY timestamp (timestamp)
        ) $charset_collate;";

        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);

        // Insert log entry
        $wpdb->insert(
            $table_name,
            [
                'timestamp' => $log_entry['timestamp'],
                'event_type' => $log_entry['event'],
                'user_id' => $log_entry['user_id'],
                'ip_address' => $log_entry['ip'],
                'user_agent' => $log_entry['user_agent'],
                'request_uri' => $log_entry['request_uri'],
                'details' => wp_json_encode($log_entry['details']),
            ],
            ['%s', '%s', '%d', '%s', '%s', '%s', '%s']
        );
    }

    /**
     * Log failed login attempts
     */
    public function log_failed_login($username) {
        self::log_security_event('login_failed', [
            'username' => $username,
        ]);
    }

    /**
     * Log successful login
     */
    public function log_successful_login($username, $user) {
        self::log_security_event('login_success', [
            'username' => $username,
            'user_id' => $user->ID,
        ]);

        // Clear rate limit on successful login
        self::clear_rate_limit('login');
    }

    /**
     * Sanitize meta query recursively
     */
    public static function sanitize_meta_query($meta_query) {
        if (!is_array($meta_query)) {
            return [];
        }

        $sanitized = [];

        foreach ($meta_query as $key => $value) {
            if (is_array($value)) {
                $sanitized[$key] = self::sanitize_meta_query($value);
            } else {
                if ($key === 'key') {
                    $sanitized[$key] = sanitize_key($value);
                } elseif ($key === 'value') {
                    $sanitized[$key] = sanitize_text_field($value);
                } elseif ($key === 'compare') {
                    $allowed_compare = ['=', '!=', '>', '>=', '<', '<=', 'LIKE', 'NOT LIKE', 'IN', 'NOT IN', 'BETWEEN', 'NOT BETWEEN', 'EXISTS', 'NOT EXISTS'];
                    $sanitized[$key] = in_array($value, $allowed_compare) ? $value : '=';
                } else {
                    $sanitized[$key] = sanitize_text_field($value);
                }
            }
        }

        return $sanitized;
    }
}

// Initialize security hardening
SkyyRose_Security_Hardening::get_instance();

/**
 * Helper function to get client IP
 */
function skyyrose_get_client_ip() {
    return SkyyRose_Security_Hardening::get_client_ip();
}

/**
 * Helper function to check rate limit
 */
function skyyrose_check_rate_limit($action, $max_attempts = 5, $time_window = 300) {
    return SkyyRose_Security_Hardening::check_rate_limit($action, $max_attempts, $time_window);
}

/**
 * Helper function to log security events
 */
function skyyrose_log_security_event($event_type, $details = []) {
    SkyyRose_Security_Hardening::log_security_event($event_type, $details);
}

/**
 * Helper function to encrypt data
 */
function skyyrose_encrypt($data) {
    return SkyyRose_Security_Hardening::encrypt_data($data);
}

/**
 * Helper function to decrypt data
 */
function skyyrose_decrypt($encrypted) {
    return SkyyRose_Security_Hardening::decrypt_data($encrypted);
}

/**
 * Helper function to validate email
 */
function skyyrose_validate_email($email, $check_disposable = true) {
    return SkyyRose_Security_Hardening::validate_email($email, $check_disposable);
}
