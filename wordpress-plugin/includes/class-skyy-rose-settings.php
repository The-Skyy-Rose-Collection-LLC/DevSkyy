<?php
/**
 * Settings management class
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Manages plugin settings and configuration
 */
class SkyyRoseSettings
{
    /**
     * Singleton instance
     * @var SkyyRoseSettings
     */
    private static $instance = null;

    /**
     * Settings option name
     * @var string
     */
    private $option_name = 'skyy_rose_ai_settings';

    /**
     * Default settings
     * @var array
     */
    private $default_settings;

    /**
     * Get singleton instance
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
        $this->initDefaultSettings();
    }

    /**
     * Initialize settings
     */
    public function init()
    {
        add_action('admin_init', [$this, 'registerSettings']);
    }

    /**
     * Initialize default settings
     */
    private function initDefaultSettings()
    {
        $this->default_settings = [
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
            ],
            'notifications' => [
                'email_alerts' => true,
                'admin_email' => get_option('admin_email'),
                'alert_frequency' => 'immediate',
                'dashboard_notifications' => true
            ]
        ];
    }

    /**
     * Register settings with WordPress
     */
    public function registerSettings()
    {
        register_setting(
            'skyy_rose_ai_settings_group',
            $this->option_name,
            [
                'sanitize_callback' => [$this, 'sanitizeSettings']
            ]
        );

        // General settings section
        add_settings_section(
            'skyy_rose_general',
            __('General Settings', SKYY_ROSE_AI_TEXT_DOMAIN),
            [$this, 'renderGeneralSection'],
            'skyy_rose_ai_general'
        );

        // Agent settings section
        add_settings_section(
            'skyy_rose_agents',
            __('Agent Configuration', SKYY_ROSE_AI_TEXT_DOMAIN),
            [$this, 'renderAgentsSection'],
            'skyy_rose_ai_agents'
        );

        // Integration settings section
        add_settings_section(
            'skyy_rose_integrations',
            __('Integrations', SKYY_ROSE_AI_TEXT_DOMAIN),
            [$this, 'renderIntegrationsSection'],
            'skyy_rose_ai_integrations'
        );

        // Add individual fields
        $this->addSettingsFields();
    }

    /**
     * Add settings fields
     */
    private function addSettingsFields()
    {
        // General settings fields
        add_settings_field(
            'enable_logging',
            __('Enable Logging', SKYY_ROSE_AI_TEXT_DOMAIN),
            [$this, 'renderCheckboxField'],
            'skyy_rose_ai_general',
            'skyy_rose_general',
            ['field' => 'general.enable_logging', 'description' => 'Enable detailed logging for debugging']
        );

        add_settings_field(
            'log_level',
            __('Log Level', SKYY_ROSE_AI_TEXT_DOMAIN),
            [$this, 'renderSelectField'],
            'skyy_rose_ai_general',
            'skyy_rose_general',
            [
                'field' => 'general.log_level',
                'options' => [
                    'error' => 'Error',
                    'warning' => 'Warning',
                    'info' => 'Info',
                    'debug' => 'Debug'
                ]
            ]
        );

        // Agent settings fields
        $agents = ['brand_intelligence', 'inventory', 'wordpress', 'performance', 'security'];
        foreach ($agents as $agent) {
            add_settings_field(
                $agent . '_enabled',
                sprintf(__('Enable %s Agent', SKYY_ROSE_AI_TEXT_DOMAIN), ucwords(str_replace('_', ' ', $agent))),
                [$this, 'renderCheckboxField'],
                'skyy_rose_ai_agents',
                'skyy_rose_agents',
                ['field' => "agents.{$agent}.enabled"]
            );
        }

        // Integration fields
        add_settings_field(
            'openai_api_key',
            __('OpenAI API Key', SKYY_ROSE_AI_TEXT_DOMAIN),
            [$this, 'renderPasswordField'],
            'skyy_rose_ai_integrations',
            'skyy_rose_integrations',
            ['field' => 'integrations.openai.api_key', 'description' => 'Required for AI-powered features']
        );
    }

    /**
     * Get setting value
     */
    public function get($key, $default = null)
    {
        $settings = get_option($this->option_name, $this->default_settings);
        return $this->getNestedValue($settings, $key, $default);
    }

    /**
     * Set setting value
     */
    public function set($key, $value)
    {
        $settings = get_option($this->option_name, $this->default_settings);
        $this->setNestedValue($settings, $key, $value);
        return update_option($this->option_name, $settings);
    }

    /**
     * Get all settings
     */
    public function getAll()
    {
        return get_option($this->option_name, $this->default_settings);
    }

    /**
     * Reset settings to defaults
     */
    public function reset()
    {
        return update_option($this->option_name, $this->default_settings);
    }

    /**
     * Sanitize settings before saving
     */
    public function sanitizeSettings($input)
    {
        $sanitized = [];

        // Sanitize general settings
        if (isset($input['general'])) {
            $sanitized['general'] = [
                'enable_logging' => !empty($input['general']['enable_logging']),
                'log_level' => sanitize_text_field($input['general']['log_level'] ?? 'info'),
                'enable_cron' => !empty($input['general']['enable_cron']),
                'scan_interval' => sanitize_text_field($input['general']['scan_interval'] ?? 'hourly')
            ];
        }

        // Sanitize agent settings
        if (isset($input['agents'])) {
            foreach ($input['agents'] as $agent => $settings) {
                $sanitized['agents'][$agent] = [
                    'enabled' => !empty($settings['enabled']),
                    'auto_analysis' => !empty($settings['auto_analysis']),
                    'auto_scan' => !empty($settings['auto_scan']),
                    'auto_optimize' => !empty($settings['auto_optimize']),
                    'confidence_threshold' => floatval($settings['confidence_threshold'] ?? 0.75),
                    'duplicate_threshold' => floatval($settings['duplicate_threshold'] ?? 0.85),
                    'performance_target' => intval($settings['performance_target'] ?? 90),
                    'monitoring_interval' => intval($settings['monitoring_interval'] ?? 300),
                    'alert_threshold' => intval($settings['alert_threshold'] ?? 80),
                    'threat_response' => sanitize_text_field($settings['threat_response'] ?? 'alert')
                ];
            }
        }

        // Sanitize integration settings
        if (isset($input['integrations'])) {
            $sanitized['integrations'] = [
                'openai' => [
                    'enabled' => !empty($input['integrations']['openai']['enabled']),
                    'api_key' => sanitize_text_field($input['integrations']['openai']['api_key'] ?? ''),
                    'model' => sanitize_text_field($input['integrations']['openai']['model'] ?? 'gpt-4')
                ],
                'woocommerce' => [
                    'enabled' => !empty($input['integrations']['woocommerce']['enabled']),
                    'sync_products' => !empty($input['integrations']['woocommerce']['sync_products']),
                    'optimize_images' => !empty($input['integrations']['woocommerce']['optimize_images'])
                ]
            ];
        }

        // Sanitize notification settings
        if (isset($input['notifications'])) {
            $sanitized['notifications'] = [
                'email_alerts' => !empty($input['notifications']['email_alerts']),
                'admin_email' => sanitize_email($input['notifications']['admin_email'] ?? get_option('admin_email')),
                'alert_frequency' => sanitize_text_field($input['notifications']['alert_frequency'] ?? 'immediate'),
                'dashboard_notifications' => !empty($input['notifications']['dashboard_notifications'])
            ];
        }

        return $sanitized;
    }

    /**
     * Render sections
     */
    public function renderGeneralSection()
    {
        echo '<p>' . __('Configure general plugin behavior and performance settings.', SKYY_ROSE_AI_TEXT_DOMAIN) . '</p>';
    }

    public function renderAgentsSection()
    {
        echo '<p>' . __('Enable and configure individual AI agents for your site.', SKYY_ROSE_AI_TEXT_DOMAIN) . '</p>';
    }

    public function renderIntegrationsSection()
    {
        echo '<p>' . __('Configure integrations with third-party services and plugins.', SKYY_ROSE_AI_TEXT_DOMAIN) . '</p>';
    }

    /**
     * Render field types
     */
    public function renderCheckboxField($args)
    {
        $value = $this->get($args['field'], false);
        $field_name = $this->getFieldName($args['field']);
        
        echo "<input type='checkbox' name='{$field_name}' value='1' " . checked(1, $value, false) . " />";
        
        if (!empty($args['description'])) {
            echo "<p class='description'>{$args['description']}</p>";
        }
    }

    public function renderSelectField($args)
    {
        $value = $this->get($args['field'], '');
        $field_name = $this->getFieldName($args['field']);
        
        echo "<select name='{$field_name}'>";
        foreach ($args['options'] as $option_value => $option_label) {
            echo "<option value='{$option_value}' " . selected($option_value, $value, false) . ">{$option_label}</option>";
        }
        echo "</select>";
        
        if (!empty($args['description'])) {
            echo "<p class='description'>{$args['description']}</p>";
        }
    }

    public function renderPasswordField($args)
    {
        $value = $this->get($args['field'], '');
        $field_name = $this->getFieldName($args['field']);
        
        echo "<input type='password' name='{$field_name}' value='{$value}' class='regular-text' />";
        
        if (!empty($args['description'])) {
            echo "<p class='description'>{$args['description']}</p>";
        }
    }

    public function renderTextField($args)
    {
        $value = $this->get($args['field'], '');
        $field_name = $this->getFieldName($args['field']);
        
        echo "<input type='text' name='{$field_name}' value='{$value}' class='regular-text' />";
        
        if (!empty($args['description'])) {
            echo "<p class='description'>{$args['description']}</p>";
        }
    }

    /**
     * Helper methods
     */
    private function getNestedValue($array, $key, $default = null)
    {
        $keys = explode('.', $key);
        $value = $array;
        
        foreach ($keys as $k) {
            if (!isset($value[$k])) {
                return $default;
            }
            $value = $value[$k];
        }
        
        return $value;
    }

    private function setNestedValue(&$array, $key, $value)
    {
        $keys = explode('.', $key);
        $current = &$array;
        
        foreach ($keys as $k) {
            if (!isset($current[$k])) {
                $current[$k] = [];
            }
            $current = &$current[$k];
        }
        
        $current = $value;
    }

    private function getFieldName($field)
    {
        $keys = explode('.', $field);
        $name = $this->option_name;
        
        foreach ($keys as $key) {
            $name .= "[{$key}]";
        }
        
        return $name;
    }
}