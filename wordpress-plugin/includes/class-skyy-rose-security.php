<?php
/**
 * Security management class
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Handles security operations for the plugin
 */
class SkyyRoseSecurity
{
    /**
     * Verify nonce
     */
    public static function verifyNonce($nonce, $action)
    {
        return wp_verify_nonce($nonce, $action);
    }

    /**
     * Create nonce
     */
    public static function createNonce($action)
    {
        return wp_create_nonce($action);
    }

    /**
     * Check user capabilities
     */
    public static function checkCapability($capability = 'manage_options')
    {
        return current_user_can($capability);
    }

    /**
     * Sanitize input data
     */
    public static function sanitizeInput($data, $type = 'text')
    {
        switch ($type) {
            case 'email':
                return sanitize_email($data);
            case 'url':
                return esc_url_raw($data);
            case 'textarea':
                return sanitize_textarea_field($data);
            case 'html':
                return wp_kses_post($data);
            case 'int':
                return intval($data);
            case 'float':
                return floatval($data);
            case 'array':
                return is_array($data) ? array_map(['self', 'sanitizeInput'], $data) : [];
            default:
                return sanitize_text_field($data);
        }
    }

    /**
     * Validate agent action
     */
    public static function validateAgentAction($action)
    {
        $allowed_actions = [
            'scan_inventory',
            'analyze_brand',
            'optimize_wordpress',
            'check_performance',
            'run_security_scan',
            'update_settings',
            'get_dashboard_data'
        ];

        return in_array($action, $allowed_actions);
    }

    /**
     * Log security event
     */
    public static function logSecurityEvent($event_type, $details = [])
    {
        $log_entry = [
            'timestamp' => current_time('mysql'),
            'user_id' => get_current_user_id(),
            'ip_address' => self::getUserIP(),
            'event_type' => $event_type,
            'details' => $details
        ];

        // Store in database or log file
        error_log('Skyy Rose Security: ' . wp_json_encode($log_entry));
    }

    /**
     * Get user IP address
     */
    private static function getUserIP()
    {
        if (!empty($_SERVER['HTTP_CLIENT_IP'])) {
            return $_SERVER['HTTP_CLIENT_IP'];
        } elseif (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
            return $_SERVER['HTTP_X_FORWARDED_FOR'];
        } else {
            return $_SERVER['REMOTE_ADDR'] ?? '';
        }
    }

    /**
     * Rate limiting check
     */
    public static function checkRateLimit($action, $limit = 60, $window = 3600)
    {
        $user_id = get_current_user_id();
        $key = "skyy_rose_rate_limit_{$action}_{$user_id}";
        
        $count = get_transient($key);
        if ($count === false) {
            set_transient($key, 1, $window);
            return true;
        }

        if ($count >= $limit) {
            return false;
        }

        set_transient($key, $count + 1, $window);
        return true;
    }
}