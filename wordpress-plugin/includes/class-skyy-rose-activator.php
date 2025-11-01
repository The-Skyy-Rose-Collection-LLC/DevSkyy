<?php
/**
 * Plugin activation handler
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Handles plugin activation
 */
class SkyyRoseActivator
{
    /**
     * Plugin activation callback
     */
    public static function activate()
    {
        // Check requirements
        self::checkRequirements();

        // Create database tables
        self::createDatabaseTables();

        // Set default options
        self::setDefaultOptions();

        // Schedule cron events
        self::scheduleCronEvents();

        // Set activation flag
        update_option('skyy_rose_ai_activated', time());

        // Flush rewrite rules
        flush_rewrite_rules();
    }

    /**
     * Check system requirements
     */
    private static function checkRequirements()
    {
        // PHP version check
        if (version_compare(PHP_VERSION, '8.0', '<')) {
            deactivate_plugins(plugin_basename(__FILE__));
            wp_die(__('Skyy Rose AI Agents requires PHP 8.0 or higher.', SKYY_ROSE_AI_TEXT_DOMAIN));
        }

        // WordPress version check
        global $wp_version;
        if (version_compare($wp_version, '6.0', '<')) {
            deactivate_plugins(plugin_basename(__FILE__));
            wp_die(__('Skyy Rose AI Agents requires WordPress 6.0 or higher.', SKYY_ROSE_AI_TEXT_DOMAIN));
        }

        // Check if required extensions are loaded
        $required_extensions = ['curl', 'json', 'mbstring'];
        foreach ($required_extensions as $extension) {
            if (!extension_loaded($extension)) {
                deactivate_plugins(plugin_basename(__FILE__));
                wp_die(sprintf(
                    __('Skyy Rose AI Agents requires PHP extension: %s', SKYY_ROSE_AI_TEXT_DOMAIN),
                    $extension
                ));
            }
        }
    }

    /**
     * Create database tables
     */
    private static function createDatabaseTables()
    {
        global $wpdb;

        $charset_collate = $wpdb->get_charset_collate();

        // Agent activities table
        $agent_activities_table = $wpdb->prefix . 'skyy_rose_agent_activities';
        $sql1 = "CREATE TABLE $agent_activities_table (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            agent_type varchar(50) NOT NULL,
            action varchar(100) NOT NULL,
            status varchar(20) NOT NULL DEFAULT 'pending',
            data longtext,
            result longtext,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            updated_at datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY agent_type (agent_type),
            KEY status (status),
            KEY created_at (created_at)
        ) $charset_collate;";

        // Agent settings table
        $agent_settings_table = $wpdb->prefix . 'skyy_rose_agent_settings';
        $sql2 = "CREATE TABLE $agent_settings_table (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            agent_type varchar(50) NOT NULL,
            setting_key varchar(100) NOT NULL,
            setting_value longtext,
            is_encrypted tinyint(1) DEFAULT 0,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            updated_at datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY agent_setting (agent_type, setting_key)
        ) $charset_collate;";

        // Brand intelligence data table
        $brand_data_table = $wpdb->prefix . 'skyy_rose_brand_data';
        $sql3 = "CREATE TABLE $brand_data_table (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            data_type varchar(50) NOT NULL,
            data_key varchar(100) NOT NULL,
            data_value longtext,
            confidence_score decimal(5,2) DEFAULT 0.00,
            source varchar(100),
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            updated_at datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY data_type (data_type),
            KEY data_key (data_key),
            KEY confidence_score (confidence_score)
        ) $charset_collate;";

        // Performance metrics table
        $performance_table = $wpdb->prefix . 'skyy_rose_performance_metrics';
        $sql4 = "CREATE TABLE $performance_table (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            metric_type varchar(50) NOT NULL,
            metric_value decimal(10,4) NOT NULL,
            metric_unit varchar(20),
            context longtext,
            recorded_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY metric_type (metric_type),
            KEY recorded_at (recorded_at)
        ) $charset_collate;";

        // Inventory assets table
        $inventory_table = $wpdb->prefix . 'skyy_rose_inventory_assets';
        $sql5 = "CREATE TABLE $inventory_table (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            asset_type varchar(50) NOT NULL,
            asset_path varchar(500) NOT NULL,
            asset_hash varchar(64),
            file_size bigint(20),
            metadata longtext,
            status varchar(20) DEFAULT 'active',
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            updated_at datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY asset_type (asset_type),
            KEY asset_hash (asset_hash),
            KEY status (status)
        ) $charset_collate;";

        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql1);
        dbDelta($sql2);
        dbDelta($sql3);
        dbDelta($sql4);
        dbDelta($sql5);
    }

    /**
     * Set default plugin options
     */
    private static function setDefaultOptions()
    {
        $default_options = [
            'skyy_rose_ai_version' => SKYY_ROSE_AI_VERSION,
            'skyy_rose_ai_settings' => [
                'general' => [
                    'enable_logging' => true,
                    'log_level' => 'info',
                    'enable_cron' => true,
                    'scan_interval' => 'hourly'
                ],
                'agents' => [
                    'brand_intelligence' => [
                        'enabled' => true,
                        'auto_analysis' => true,
                        'confidence_threshold' => 0.75
                    ],
                    'inventory' => [
                        'enabled' => true,
                        'auto_scan' => true,
                        'duplicate_threshold' => 0.85
                    ],
                    'wordpress' => [
                        'enabled' => true,
                        'auto_optimize' => false,
                        'performance_target' => 90
                    ],
                    'performance' => [
                        'enabled' => true,
                        'monitoring_interval' => 300,
                        'alert_threshold' => 80
                    ],
                    'security' => [
                        'enabled' => true,
                        'auto_scan' => true,
                        'threat_response' => 'alert'
                    ]
                ],
                'integrations' => [
                    'openai' => [
                        'enabled' => false,
                        'api_key' => '',
                        'model' => 'gpt-4'
                    ],
                    'woocommerce' => [
                        'enabled' => is_plugin_active('woocommerce/woocommerce.php'),
                        'sync_products' => true,
                        'optimize_images' => true
                    ]
                ]
            ]
        ];

        foreach ($default_options as $option_name => $option_value) {
            if (!get_option($option_name)) {
                add_option($option_name, $option_value);
            }
        }
    }

    /**
     * Schedule cron events
     */
    private static function scheduleCronEvents()
    {
        // Clear existing schedules
        wp_clear_scheduled_hook('skyy_rose_hourly_scan');
        wp_clear_scheduled_hook('skyy_rose_daily_optimization');

        // Schedule new events
        if (!wp_next_scheduled('skyy_rose_hourly_scan')) {
            wp_schedule_event(time(), 'hourly', 'skyy_rose_hourly_scan');
        }

        if (!wp_next_scheduled('skyy_rose_daily_optimization')) {
            wp_schedule_event(time(), 'daily', 'skyy_rose_daily_optimization');
        }
    }
}