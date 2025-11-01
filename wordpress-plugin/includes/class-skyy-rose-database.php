<?php
/**
 * Database management class
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Manages database operations for the plugin
 */
class SkyyRoseDatabase
{
    /**
     * Singleton instance
     * @var SkyyRoseDatabase
     */
    private static $instance = null;

    /**
     * Database version
     * @var string
     */
    private $db_version = '1.0.0';

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
     * Initialize database operations
     */
    public function init()
    {
        // Check if database needs updating
        $installed_version = get_option('skyy_rose_db_version', '0.0.0');
        if (version_compare($installed_version, $this->db_version, '<')) {
            $this->updateDatabase();
            update_option('skyy_rose_db_version', $this->db_version);
        }
    }

    /**
     * Update database schema
     */
    private function updateDatabase()
    {
        // This would contain migration logic for database updates
        // For now, we'll just ensure tables exist
        require_once SKYY_ROSE_AI_PLUGIN_PATH . 'includes/class-skyy-rose-activator.php';
        // Note: We would call specific migration methods here in a real scenario
    }

    /**
     * Insert agent activity
     */
    public function insertAgentActivity($agent_type, $action, $data = null, $status = 'pending')
    {
        global $wpdb;

        return $wpdb->insert(
            $wpdb->prefix . 'skyy_rose_agent_activities',
            [
                'agent_type' => sanitize_text_field($agent_type),
                'action' => sanitize_text_field($action),
                'status' => sanitize_text_field($status),
                'data' => $data ? wp_json_encode($data) : null,
                'created_at' => current_time('mysql')
            ],
            ['%s', '%s', '%s', '%s', '%s']
        );
    }

    /**
     * Update agent activity
     */
    public function updateAgentActivity($id, $status, $result = null)
    {
        global $wpdb;

        return $wpdb->update(
            $wpdb->prefix . 'skyy_rose_agent_activities',
            [
                'status' => sanitize_text_field($status),
                'result' => $result ? wp_json_encode($result) : null,
                'updated_at' => current_time('mysql')
            ],
            ['id' => intval($id)],
            ['%s', '%s', '%s'],
            ['%d']
        );
    }

    /**
     * Get agent activities
     */
    public function getAgentActivities($agent_type = null, $limit = 50, $offset = 0)
    {
        global $wpdb;

        $where = '';
        $prepare_values = [];

        if ($agent_type) {
            $where = 'WHERE agent_type = %s';
            $prepare_values[] = $agent_type;
        }

        $query = "SELECT * FROM {$wpdb->prefix}skyy_rose_agent_activities 
                  {$where} 
                  ORDER BY created_at DESC 
                  LIMIT %d OFFSET %d";

        $prepare_values[] = $limit;
        $prepare_values[] = $offset;

        return $wpdb->get_results($wpdb->prepare($query, $prepare_values));
    }

    /**
     * Set agent setting
     */
    public function setAgentSetting($agent_type, $setting_key, $setting_value, $is_encrypted = false)
    {
        global $wpdb;

        if ($is_encrypted) {
            $setting_value = $this->encryptValue($setting_value);
        }

        return $wpdb->replace(
            $wpdb->prefix . 'skyy_rose_agent_settings',
            [
                'agent_type' => sanitize_text_field($agent_type),
                'setting_key' => sanitize_text_field($setting_key),
                'setting_value' => $setting_value,
                'is_encrypted' => intval($is_encrypted),
                'updated_at' => current_time('mysql')
            ],
            ['%s', '%s', '%s', '%d', '%s']
        );
    }

    /**
     * Get agent setting
     */
    public function getAgentSetting($agent_type, $setting_key, $default = null)
    {
        global $wpdb;

        $result = $wpdb->get_row($wpdb->prepare(
            "SELECT setting_value, is_encrypted FROM {$wpdb->prefix}skyy_rose_agent_settings 
             WHERE agent_type = %s AND setting_key = %s",
            $agent_type,
            $setting_key
        ));

        if (!$result) {
            return $default;
        }

        $value = $result->setting_value;
        if ($result->is_encrypted) {
            $value = $this->decryptValue($value);
        }

        return $value;
    }

    /**
     * Insert brand data
     */
    public function insertBrandData($data_type, $data_key, $data_value, $confidence_score = 0.0, $source = null)
    {
        global $wpdb;

        return $wpdb->replace(
            $wpdb->prefix . 'skyy_rose_brand_data',
            [
                'data_type' => sanitize_text_field($data_type),
                'data_key' => sanitize_text_field($data_key),
                'data_value' => wp_json_encode($data_value),
                'confidence_score' => floatval($confidence_score),
                'source' => $source ? sanitize_text_field($source) : null,
                'updated_at' => current_time('mysql')
            ],
            ['%s', '%s', '%s', '%f', '%s', '%s']
        );
    }

    /**
     * Get brand data
     */
    public function getBrandData($data_type = null, $data_key = null)
    {
        global $wpdb;

        $where_conditions = [];
        $prepare_values = [];

        if ($data_type) {
            $where_conditions[] = 'data_type = %s';
            $prepare_values[] = $data_type;
        }

        if ($data_key) {
            $where_conditions[] = 'data_key = %s';
            $prepare_values[] = $data_key;
        }

        $where_clause = !empty($where_conditions) ? 'WHERE ' . implode(' AND ', $where_conditions) : '';

        $query = "SELECT * FROM {$wpdb->prefix}skyy_rose_brand_data 
                  {$where_clause} 
                  ORDER BY confidence_score DESC, updated_at DESC";

        if (!empty($prepare_values)) {
            return $wpdb->get_results($wpdb->prepare($query, $prepare_values));
        } else {
            return $wpdb->get_results($query);
        }
    }

    /**
     * Insert performance metric
     */
    public function insertPerformanceMetric($metric_type, $metric_value, $metric_unit = null, $context = null)
    {
        global $wpdb;

        return $wpdb->insert(
            $wpdb->prefix . 'skyy_rose_performance_metrics',
            [
                'metric_type' => sanitize_text_field($metric_type),
                'metric_value' => floatval($metric_value),
                'metric_unit' => $metric_unit ? sanitize_text_field($metric_unit) : null,
                'context' => $context ? wp_json_encode($context) : null,
                'recorded_at' => current_time('mysql')
            ],
            ['%s', '%f', '%s', '%s', '%s']
        );
    }

    /**
     * Get performance metrics
     */
    public function getPerformanceMetrics($metric_type = null, $hours = 24)
    {
        global $wpdb;

        $where = '';
        $prepare_values = [];

        if ($metric_type) {
            $where = 'WHERE metric_type = %s AND';
            $prepare_values[] = $metric_type;
        } else {
            $where = 'WHERE';
        }

        $query = "SELECT * FROM {$wpdb->prefix}skyy_rose_performance_metrics 
                  {$where} recorded_at >= %s 
                  ORDER BY recorded_at DESC";

        $prepare_values[] = date('Y-m-d H:i:s', strtotime("-{$hours} hours"));

        return $wpdb->get_results($wpdb->prepare($query, $prepare_values));
    }

    /**
     * Insert inventory asset
     */
    public function insertInventoryAsset($asset_type, $asset_path, $asset_hash = null, $file_size = null, $metadata = null)
    {
        global $wpdb;

        return $wpdb->replace(
            $wpdb->prefix . 'skyy_rose_inventory_assets',
            [
                'asset_type' => sanitize_text_field($asset_type),
                'asset_path' => sanitize_text_field($asset_path),
                'asset_hash' => $asset_hash ? sanitize_text_field($asset_hash) : null,
                'file_size' => $file_size ? intval($file_size) : null,
                'metadata' => $metadata ? wp_json_encode($metadata) : null,
                'updated_at' => current_time('mysql')
            ],
            ['%s', '%s', '%s', '%d', '%s', '%s']
        );
    }

    /**
     * Get inventory assets
     */
    public function getInventoryAssets($asset_type = null, $status = 'active')
    {
        global $wpdb;

        $where_conditions = ['status = %s'];
        $prepare_values = [$status];

        if ($asset_type) {
            $where_conditions[] = 'asset_type = %s';
            $prepare_values[] = $asset_type;
        }

        $where_clause = 'WHERE ' . implode(' AND ', $where_conditions);

        $query = "SELECT * FROM {$wpdb->prefix}skyy_rose_inventory_assets 
                  {$where_clause} 
                  ORDER BY updated_at DESC";

        return $wpdb->get_results($wpdb->prepare($query, $prepare_values));
    }

    /**
     * Encrypt sensitive value
     */
    private function encryptValue($value)
    {
        if (!function_exists('openssl_encrypt')) {
            return base64_encode($value); // Fallback to base64
        }

        $key = $this->getEncryptionKey();
        $iv = openssl_random_pseudo_bytes(16);
        $encrypted = openssl_encrypt($value, 'AES-256-CBC', $key, 0, $iv);
        
        return base64_encode($iv . $encrypted);
    }

    /**
     * Decrypt sensitive value
     */
    private function decryptValue($encrypted_value)
    {
        if (!function_exists('openssl_decrypt')) {
            return base64_decode($encrypted_value); // Fallback from base64
        }

        $key = $this->getEncryptionKey();
        $data = base64_decode($encrypted_value);
        $iv = substr($data, 0, 16);
        $encrypted = substr($data, 16);
        
        return openssl_decrypt($encrypted, 'AES-256-CBC', $key, 0, $iv);
    }

    /**
     * Get encryption key
     */
    private function getEncryptionKey()
    {
        $key = get_option('skyy_rose_encryption_key');
        if (!$key) {
            $key = wp_generate_password(32, false);
            update_option('skyy_rose_encryption_key', $key);
        }
        return hash('sha256', $key . AUTH_KEY);
    }
}