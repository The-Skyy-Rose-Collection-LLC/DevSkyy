<?php
/**
 * Plugin Name: Skyy Rose AI Agents
 * Plugin URI: https://skyyrose.co/plugins/ai-agents
 * Description: Enterprise-level AI agent management platform for luxury e-commerce with WordPress/WooCommerce integration, brand intelligence, and automated optimization.
 * Version: 1.0.0
 * Author: Skyy Rose Co
 * Author URI: https://skyyrose.co
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: skyy-rose-ai-agents
 * Domain Path: /languages
 * Requires at least: 6.0
 * Tested up to: 6.6
 * Requires PHP: 8.0
 * Network: false
 * 
 * @package SkyyRoseAIAgents
 * @author Skyy Rose Co
 * @copyright 2024 Skyy Rose Co
 * @license GPL-2.0-or-later
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('SKYY_ROSE_AI_VERSION', '1.0.0');
define('SKYY_ROSE_AI_PLUGIN_URL', plugin_dir_url(__FILE__));
define('SKYY_ROSE_AI_PLUGIN_PATH', plugin_dir_path(__FILE__));
define('SKYY_ROSE_AI_PLUGIN_BASENAME', plugin_basename(__FILE__));
define('SKYY_ROSE_AI_TEXT_DOMAIN', 'skyy-rose-ai-agents');

// Minimum requirements check
if (!class_exists('SkyyRoseAIAgents')) {

    /**
     * Main plugin class
     */
    class SkyyRoseAIAgents
    {
        /**
         * Plugin instance
         * @var SkyyRoseAIAgents
         */
        private static $instance = null;

        /**
         * Get plugin instance
         */
        public static function getInstance()
        {
            if (self::$instance === null) {
                self::$instance = new self();
            }
            return self::$instance;
        }

        /**
         * Constructor
         */
        private function __construct()
        {
            $this->init();
        }

        /**
         * Initialize plugin
         */
        private function init()
        {
            // Check requirements
            if (!$this->checkRequirements()) {
                return;
            }

            // Load dependencies
            $this->loadDependencies();

            // Initialize hooks
            $this->initHooks();
        }

        /**
         * Check minimum requirements
         */
        private function checkRequirements()
        {
            // Check PHP version
            if (version_compare(PHP_VERSION, '8.0', '<')) {
                add_action('admin_notices', function() {
                    echo '<div class="notice notice-error"><p>';
                    echo sprintf(
                        /* translators: %1$s: Current PHP version, %2$s: Required PHP version */
                        __('Skyy Rose AI Agents requires PHP %2$s or higher. Your current version is %1$s.', SKYY_ROSE_AI_TEXT_DOMAIN),
                        PHP_VERSION,
                        '8.0'
                    );
                    echo '</p></div>';
                });
                return false;
            }

            // Check WordPress version
            global $wp_version;
            if (version_compare($wp_version, '6.0', '<')) {
                add_action('admin_notices', function() {
                    echo '<div class="notice notice-error"><p>';
                    echo sprintf(
                        /* translators: %1$s: Current WP version, %2$s: Required WP version */
                        __('Skyy Rose AI Agents requires WordPress %2$s or higher. Your current version is %1$s.', SKYY_ROSE_AI_TEXT_DOMAIN),
                        $wp_version,
                        '6.0'
                    );
                    echo '</p></div>';
                });
                return false;
            }

            return true;
        }

        /**
         * Load plugin dependencies
         */
        private function loadDependencies()
        {
            // Load core classes
            require_once SKYY_ROSE_AI_PLUGIN_PATH . 'includes/class-skyy-rose-activator.php';
            require_once SKYY_ROSE_AI_PLUGIN_PATH . 'includes/class-skyy-rose-deactivator.php';
            require_once SKYY_ROSE_AI_PLUGIN_PATH . 'includes/class-skyy-rose-database.php';
            require_once SKYY_ROSE_AI_PLUGIN_PATH . 'includes/class-skyy-rose-settings.php';
            require_once SKYY_ROSE_AI_PLUGIN_PATH . 'includes/class-skyy-rose-security.php';

            // Load agent classes
            require_once SKYY_ROSE_AI_PLUGIN_PATH . 'includes/agents/class-brand-intelligence-agent.php';
            require_once SKYY_ROSE_AI_PLUGIN_PATH . 'includes/agents/class-inventory-agent.php';
            require_once SKYY_ROSE_AI_PLUGIN_PATH . 'includes/agents/class-wordpress-agent.php';
            require_once SKYY_ROSE_AI_PLUGIN_PATH . 'includes/agents/class-performance-agent.php';
            require_once SKYY_ROSE_AI_PLUGIN_PATH . 'includes/agents/class-security-agent.php';

            // Load admin classes
            require_once SKYY_ROSE_AI_PLUGIN_PATH . 'admin/class-skyy-rose-admin.php';
            require_once SKYY_ROSE_AI_PLUGIN_PATH . 'admin/class-skyy-rose-dashboard.php';

            // Load API classes
            require_once SKYY_ROSE_AI_PLUGIN_PATH . 'includes/api/class-skyy-rose-rest-api.php';
        }

        /**
         * Initialize WordPress hooks
         */
        private function initHooks()
        {
            // Activation/Deactivation hooks
            register_activation_hook(__FILE__, ['SkyyRoseActivator', 'activate']);
            register_deactivation_hook(__FILE__, ['SkyyRoseDeactivator', 'deactivate']);

            // Plugin loaded hook
            add_action('plugins_loaded', [$this, 'pluginsLoaded']);

            // Admin hooks
            if (is_admin()) {
                new SkyyRoseAdmin();
            }

            // REST API hooks
            add_action('rest_api_init', ['SkyyRoseRestAPI', 'init']);

            // AJAX hooks
            add_action('wp_ajax_skyy_rose_agent_action', [$this, 'handleAjaxAction']);
            add_action('wp_ajax_nopriv_skyy_rose_agent_action', [$this, 'handleAjaxAction']);

            // Cron hooks for scheduled tasks
            add_action('skyy_rose_hourly_scan', [$this, 'runHourlyScan']);
            add_action('skyy_rose_daily_optimization', [$this, 'runDailyOptimization']);
        }

        /**
         * Plugin loaded callback
         */
        public function pluginsLoaded()
        {
            // Load text domain for internationalization
            load_plugin_textdomain(
                SKYY_ROSE_AI_TEXT_DOMAIN,
                false,
                dirname(SKYY_ROSE_AI_PLUGIN_BASENAME) . '/languages'
            );

            // Initialize database
            SkyyRoseDatabase::getInstance()->init();

            // Initialize settings
            SkyyRoseSettings::getInstance()->init();

            // Schedule cron events if not already scheduled
            if (!wp_next_scheduled('skyy_rose_hourly_scan')) {
                wp_schedule_event(time(), 'hourly', 'skyy_rose_hourly_scan');
            }

            if (!wp_next_scheduled('skyy_rose_daily_optimization')) {
                wp_schedule_event(time(), 'daily', 'skyy_rose_daily_optimization');
            }
        }

        /**
         * Handle AJAX actions
         */
        public function handleAjaxAction()
        {
            // Verify nonce
            if (!SkyyRoseSecurity::verifyNonce($_POST['nonce'] ?? '', 'skyy_rose_agent_action')) {
                wp_die(__('Security check failed.', SKYY_ROSE_AI_TEXT_DOMAIN));
            }

            $action = sanitize_text_field($_POST['agent_action'] ?? '');
            $data = $_POST['data'] ?? [];

            try {
                $result = $this->processAgentAction($action, $data);
                wp_send_json_success($result);
            } catch (Exception $e) {
                wp_send_json_error([
                    'message' => $e->getMessage(),
                    'code' => $e->getCode()
                ]);
            }
        }

        /**
         * Process agent actions
         */
        private function processAgentAction($action, $data)
        {
            switch ($action) {
                case 'scan_inventory':
                    return InventoryAgent::getInstance()->scanAssets();
                
                case 'analyze_brand':
                    return BrandIntelligenceAgent::getInstance()->analyzeBrand($data);
                
                case 'optimize_wordpress':
                    return WordPressAgent::getInstance()->optimizeWordPress($data);
                
                case 'check_performance':
                    return PerformanceAgent::getInstance()->checkPerformance();
                
                case 'run_security_scan':
                    return SecurityAgent::getInstance()->runSecurityScan();
                
                default:
                    throw new Exception(__('Unknown agent action.', SKYY_ROSE_AI_TEXT_DOMAIN), 400);
            }
        }

        /**
         * Run hourly scan (cron job)
         */
        public function runHourlyScan()
        {
            try {
                // Run light monitoring tasks
                PerformanceAgent::getInstance()->quickHealthCheck();
                SecurityAgent::getInstance()->basicSecurityCheck();
                
                // Log activity
                error_log('Skyy Rose AI Agents: Hourly scan completed');
            } catch (Exception $e) {
                error_log('Skyy Rose AI Agents: Hourly scan failed - ' . $e->getMessage());
            }
        }

        /**
         * Run daily optimization (cron job)
         */
        public function runDailyOptimization()
        {
            try {
                // Run comprehensive optimization
                InventoryAgent::getInstance()->optimizeAssets();
                WordPressAgent::getInstance()->dailyOptimization();
                BrandIntelligenceAgent::getInstance()->updateBrandInsights();
                
                // Log activity
                error_log('Skyy Rose AI Agents: Daily optimization completed');
            } catch (Exception $e) {
                error_log('Skyy Rose AI Agents: Daily optimization failed - ' . $e->getMessage());
            }
        }
    }

    // Initialize the plugin
    SkyyRoseAIAgents::getInstance();
}