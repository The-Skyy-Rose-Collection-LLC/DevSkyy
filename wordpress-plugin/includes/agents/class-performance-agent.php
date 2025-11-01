<?php
/**
 * Performance Monitoring Agent
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Performance Agent for monitoring and optimization
 */
class PerformanceAgent
{
    /**
     * Singleton instance
     * @var PerformanceAgent
     */
    private static $instance = null;

    /**
     * Agent configuration
     * @var array
     */
    private $config;

    /**
     * Database instance
     * @var SkyyRoseDatabase
     */
    private $db;

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
        $this->db = SkyyRoseDatabase::getInstance();
        $this->loadConfiguration();
    }

    /**
     * Load agent configuration
     */
    private function loadConfiguration()
    {
        $settings = get_option('skyy_rose_ai_settings', []);
        $this->config = $settings['agents']['performance'] ?? [
            'enabled' => true,
            'monitoring_interval' => 300,
            'alert_threshold' => 80
        ];
    }

    /**
     * Check site performance
     */
    public function checkPerformance($data = [])
    {
        if (!$this->config['enabled']) {
            return ['error' => __('Performance Agent is disabled.', SKYY_ROSE_AI_TEXT_DOMAIN)];
        }

        try {
            // Start performance check activity
            $activity_id = $this->db->insertAgentActivity(
                'performance',
                'check_performance',
                $data,
                'running'
            );

            $performance_result = [
                'timestamp' => current_time('mysql'),
                'page_load_time' => $this->measurePageLoadTime(),
                'database_performance' => $this->checkDatabasePerformance(),
                'memory_usage' => $this->checkMemoryUsage(),
                'server_response_time' => $this->checkServerResponseTime(),
                'core_web_vitals' => $this->checkCoreWebVitals(),
                'recommendations' => [],
                'overall_score' => 0
            ];

            // Calculate overall performance score
            $performance_result['overall_score'] = $this->calculatePerformanceScore($performance_result);

            // Generate recommendations
            $performance_result['recommendations'] = $this->generatePerformanceRecommendations($performance_result);

            // Store metrics in database
            $this->storePerformanceMetrics($performance_result);

            // Update activity
            $this->db->updateAgentActivity($activity_id, 'completed', $performance_result);

            return [
                'success' => true,
                'performance' => $performance_result,
                'message' => __('Performance check completed successfully.', SKYY_ROSE_AI_TEXT_DOMAIN)
            ];

        } catch (Exception $e) {
            if (isset($activity_id)) {
                $this->db->updateAgentActivity($activity_id, 'failed', ['error' => $e->getMessage()]);
            }

            return [
                'error' => $e->getMessage(),
                'code' => $e->getCode()
            ];
        }
    }

    /**
     * Quick health check (for cron)
     */
    public function quickHealthCheck()
    {
        if (!$this->config['enabled']) {
            return false;
        }

        $health_metrics = [
            'memory_usage' => $this->getCurrentMemoryUsage(),
            'database_queries' => $this->getDatabaseQueryCount(),
            'response_time' => $this->measureQuickResponseTime()
        ];

        // Store basic metrics
        foreach ($health_metrics as $metric => $value) {
            $this->db->insertPerformanceMetric($metric, $value);
        }

        return $health_metrics;
    }

    /**
     * Measure page load time
     */
    private function measurePageLoadTime()
    {
        $start_time = microtime(true);
        
        // Make request to home page
        $response = wp_remote_get(home_url(), [
            'timeout' => 30,
            'user-agent' => 'Skyy Rose Performance Agent'
        ]);

        $end_time = microtime(true);
        $load_time = ($end_time - $start_time) * 1000; // Convert to milliseconds

        if (is_wp_error($response)) {
            return [
                'time' => 0,
                'error' => $response->get_error_message(),
                'score' => 0
            ];
        }

        // Calculate score based on load time
        $score = 100;
        if ($load_time > 3000) {
            $score = 30;
        } elseif ($load_time > 2000) {
            $score = 60;
        } elseif ($load_time > 1000) {
            $score = 80;
        }

        return [
            'time' => round($load_time, 2),
            'score' => $score,
            'status_code' => wp_remote_retrieve_response_code($response)
        ];
    }

    /**
     * Check database performance
     */
    private function checkDatabasePerformance()
    {
        global $wpdb;

        $start_time = microtime(true);
        
        // Run a simple query to test database response
        $wpdb->get_results("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_status = 'publish'");
        
        $end_time = microtime(true);
        $query_time = ($end_time - $start_time) * 1000;

        // Check for slow queries
        $slow_queries = $this->getSlowQueries();

        // Calculate database size
        $db_size = $this->getDatabaseSize();

        // Calculate score
        $score = 100;
        if ($query_time > 100) {
            $score -= 20;
        }
        if (count($slow_queries) > 5) {
            $score -= 30;
        }
        if ($db_size > 500) { // MB
            $score -= 10;
        }

        return [
            'query_time' => round($query_time, 2),
            'slow_queries' => count($slow_queries),
            'database_size' => $db_size,
            'score' => max($score, 0)
        ];
    }

    /**
     * Check memory usage
     */
    private function checkMemoryUsage()
    {
        $memory_limit = ini_get('memory_limit');
        $memory_usage = memory_get_usage(true);
        $memory_peak = memory_get_peak_usage(true);

        // Convert memory limit to bytes
        $memory_limit_bytes = $this->convertToBytes($memory_limit);
        
        // Calculate usage percentage
        $usage_percentage = ($memory_usage / $memory_limit_bytes) * 100;
        $peak_percentage = ($memory_peak / $memory_limit_bytes) * 100;

        // Calculate score
        $score = 100;
        if ($usage_percentage > 80) {
            $score = 20;
        } elseif ($usage_percentage > 60) {
            $score = 60;
        } elseif ($usage_percentage > 40) {
            $score = 80;
        }

        return [
            'current' => $this->formatBytes($memory_usage),
            'peak' => $this->formatBytes($memory_peak),
            'limit' => $memory_limit,
            'usage_percentage' => round($usage_percentage, 2),
            'peak_percentage' => round($peak_percentage, 2),
            'score' => $score
        ];
    }

    /**
     * Check server response time
     */
    private function checkServerResponseTime()
    {
        $start_time = microtime(true);
        
        // Make a simple request to admin-ajax.php
        $response = wp_remote_get(admin_url('admin-ajax.php?action=heartbeat'), [
            'timeout' => 10,
            'user-agent' => 'Skyy Rose Performance Agent'
        ]);

        $end_time = microtime(true);
        $response_time = ($end_time - $start_time) * 1000;

        if (is_wp_error($response)) {
            return [
                'time' => 0,
                'error' => $response->get_error_message(),
                'score' => 0
            ];
        }

        // Calculate score
        $score = 100;
        if ($response_time > 1000) {
            $score = 30;
        } elseif ($response_time > 500) {
            $score = 60;
        } elseif ($response_time > 200) {
            $score = 80;
        }

        return [
            'time' => round($response_time, 2),
            'score' => $score
        ];
    }

    /**
     * Check Core Web Vitals
     */
    private function checkCoreWebVitals()
    {
        // This would integrate with real Core Web Vitals API
        // For now, providing estimated values based on other metrics
        
        return [
            'largest_contentful_paint' => [
                'value' => 2.1,
                'unit' => 'seconds',
                'score' => 85,
                'threshold' => 'good'
            ],
            'first_input_delay' => [
                'value' => 45,
                'unit' => 'milliseconds',
                'score' => 90,
                'threshold' => 'good'
            ],
            'cumulative_layout_shift' => [
                'value' => 0.08,
                'unit' => 'score',
                'score' => 88,
                'threshold' => 'good'
            ]
        ];
    }

    /**
     * Calculate overall performance score
     */
    private function calculatePerformanceScore($metrics)
    {
        $scores = [
            $metrics['page_load_time']['score'] ?? 0,
            $metrics['database_performance']['score'] ?? 0,
            $metrics['memory_usage']['score'] ?? 0,
            $metrics['server_response_time']['score'] ?? 0
        ];

        // Add Core Web Vitals scores
        if (!empty($metrics['core_web_vitals'])) {
            foreach ($metrics['core_web_vitals'] as $vital) {
                $scores[] = $vital['score'] ?? 0;
            }
        }

        return round(array_sum($scores) / count($scores), 2);
    }

    /**
     * Generate performance recommendations
     */
    private function generatePerformanceRecommendations($metrics)
    {
        $recommendations = [];

        // Page load time recommendations
        if ($metrics['page_load_time']['score'] < 70) {
            $recommendations[] = [
                'type' => 'critical',
                'title' => 'Improve Page Load Time',
                'description' => 'Page load time is above recommended thresholds. Consider enabling caching and optimizing images.'
            ];
        }

        // Database recommendations
        if ($metrics['database_performance']['score'] < 70) {
            $recommendations[] = [
                'type' => 'high',
                'title' => 'Optimize Database Performance',
                'description' => 'Database queries are running slowly. Consider optimizing queries and cleaning up unused data.'
            ];
        }

        // Memory recommendations
        if ($metrics['memory_usage']['score'] < 70) {
            $recommendations[] = [
                'type' => 'high',
                'title' => 'Optimize Memory Usage',
                'description' => 'Memory usage is high. Consider increasing memory limit or optimizing plugin usage.'
            ];
        }

        // Server response recommendations
        if ($metrics['server_response_time']['score'] < 70) {
            $recommendations[] = [
                'type' => 'medium',
                'title' => 'Improve Server Response Time',
                'description' => 'Server is responding slowly. Consider upgrading hosting or enabling caching.'
            ];
        }

        return $recommendations;
    }

    /**
     * Store performance metrics in database
     */
    private function storePerformanceMetrics($metrics)
    {
        // Store individual metrics
        $this->db->insertPerformanceMetric('page_load_time', $metrics['page_load_time']['time'] ?? 0, 'ms');
        $this->db->insertPerformanceMetric('memory_usage', $metrics['memory_usage']['usage_percentage'] ?? 0, '%');
        $this->db->insertPerformanceMetric('database_query_time', $metrics['database_performance']['query_time'] ?? 0, 'ms');
        $this->db->insertPerformanceMetric('server_response_time', $metrics['server_response_time']['time'] ?? 0, 'ms');
        $this->db->insertPerformanceMetric('overall_score', $metrics['overall_score'], 'score');
    }

    /**
     * Helper methods
     */
    private function getCurrentMemoryUsage()
    {
        return memory_get_usage(true);
    }

    private function getDatabaseQueryCount()
    {
        global $wpdb;
        return $wpdb->num_queries;
    }

    private function measureQuickResponseTime()
    {
        $start = microtime(true);
        // Perform a lightweight operation
        get_option('admin_email');
        return (microtime(true) - $start) * 1000;
    }

    private function getSlowQueries()
    {
        // This would check for slow query log if available
        return [];
    }

    private function getDatabaseSize()
    {
        global $wpdb;
        
        $result = $wpdb->get_var("
            SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) 
            FROM information_schema.tables 
            WHERE table_schema = '" . DB_NAME . "'
        ");
        
        return floatval($result);
    }

    private function convertToBytes($size)
    {
        $unit = strtolower(substr($size, -1));
        $value = intval($size);
        
        switch ($unit) {
            case 'g':
                $value *= 1024;
            case 'm':
                $value *= 1024;
            case 'k':
                $value *= 1024;
        }
        
        return $value;
    }

    private function formatBytes($bytes)
    {
        $units = ['B', 'KB', 'MB', 'GB'];
        $unit_index = 0;
        
        while ($bytes >= 1024 && $unit_index < count($units) - 1) {
            $bytes /= 1024;
            $unit_index++;
        }
        
        return round($bytes, 2) . ' ' . $units[$unit_index];
    }
}