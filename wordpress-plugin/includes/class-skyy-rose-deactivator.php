<?php
/**
 * Plugin deactivation handler
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Handles plugin deactivation
 */
class SkyyRoseDeactivator
{
    /**
     * Plugin deactivation callback
     */
    public static function deactivate()
    {
        // Clear scheduled cron events
        self::clearCronEvents();

        // Clean up temporary data
        self::cleanupTempData();

        // Set deactivation flag
        update_option('skyy_rose_ai_deactivated', time());

        // Flush rewrite rules
        flush_rewrite_rules();
    }

    /**
     * Clear scheduled cron events
     */
    private static function clearCronEvents()
    {
        wp_clear_scheduled_hook('skyy_rose_hourly_scan');
        wp_clear_scheduled_hook('skyy_rose_daily_optimization');
    }

    /**
     * Clean up temporary data
     */
    private static function cleanupTempData()
    {
        global $wpdb;

        // Clear expired activities (older than 30 days)
        $wpdb->query($wpdb->prepare(
            "DELETE FROM {$wpdb->prefix}skyy_rose_agent_activities 
             WHERE created_at < %s",
            date('Y-m-d H:i:s', strtotime('-30 days'))
        ));

        // Clear expired performance metrics (older than 7 days)
        $wpdb->query($wpdb->prepare(
            "DELETE FROM {$wpdb->prefix}skyy_rose_performance_metrics 
             WHERE recorded_at < %s",
            date('Y-m-d H:i:s', strtotime('-7 days'))
        ));

        // Clean up transients
        delete_transient('skyy_rose_performance_cache');
        delete_transient('skyy_rose_security_cache');
        delete_transient('skyy_rose_brand_cache');
    }

    /**
     * Complete uninstall (called when plugin is deleted)
     */
    public static function uninstall()
    {
        // Only run if user has capability
        if (!current_user_can('activate_plugins')) {
            return;
        }

        // Check nonce
        check_admin_referer('bulk-plugins');

        // Delete database tables
        self::dropDatabaseTables();

        // Delete options
        self::deleteOptions();

        // Delete user meta
        self::deleteUserMeta();

        // Clear all transients
        self::clearAllTransients();
    }

    /**
     * Drop database tables
     */
    private static function dropDatabaseTables()
    {
        global $wpdb;

        $tables = [
            $wpdb->prefix . 'skyy_rose_agent_activities',
            $wpdb->prefix . 'skyy_rose_agent_settings',
            $wpdb->prefix . 'skyy_rose_brand_data',
            $wpdb->prefix . 'skyy_rose_performance_metrics',
            $wpdb->prefix . 'skyy_rose_inventory_assets'
        ];

        foreach ($tables as $table) {
            $wpdb->query("DROP TABLE IF EXISTS $table");
        }
    }

    /**
     * Delete plugin options
     */
    private static function deleteOptions()
    {
        $options = [
            'skyy_rose_ai_version',
            'skyy_rose_ai_settings',
            'skyy_rose_ai_activated',
            'skyy_rose_ai_deactivated'
        ];

        foreach ($options as $option) {
            delete_option($option);
        }
    }

    /**
     * Delete user meta
     */
    private static function deleteUserMeta()
    {
        global $wpdb;

        $wpdb->query(
            "DELETE FROM {$wpdb->usermeta} 
             WHERE meta_key LIKE 'skyy_rose_%'"
        );
    }

    /**
     * Clear all plugin transients
     */
    private static function clearAllTransients()
    {
        global $wpdb;

        $wpdb->query(
            "DELETE FROM {$wpdb->options} 
             WHERE option_name LIKE '_transient_skyy_rose_%' 
             OR option_name LIKE '_transient_timeout_skyy_rose_%'"
        );
    }
}