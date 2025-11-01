<?php
/**
 * REST API endpoints
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * REST API class for agent endpoints
 */
class SkyyRoseRestAPI
{
    /**
     * API namespace
     */
    const NAMESPACE = 'skyy-rose-ai/v1';

    /**
     * Initialize REST API routes
     */
    public static function init()
    {
        add_action('rest_api_init', [__CLASS__, 'registerRoutes']);
    }

    /**
     * Register all API routes
     */
    public static function registerRoutes()
    {
        // Agent execution endpoints
        register_rest_route(self::NAMESPACE, '/agents/(?P<agent_type>[a-zA-Z0-9_-]+)/(?P<action>[a-zA-Z0-9_-]+)', [
            'methods' => 'POST',
            'callback' => [__CLASS__, 'executeAgentAction'],
            'permission_callback' => [__CLASS__, 'checkPermissions'],
            'args' => [
                'agent_type' => [
                    'required' => true,
                    'type' => 'string',
                    'validate_callback' => [__CLASS__, 'validateAgentType']
                ],
                'action' => [
                    'required' => true,
                    'type' => 'string',
                    'validate_callback' => [__CLASS__, 'validateAgentAction']
                ]
            ]
        ]);

        // Dashboard data endpoint
        register_rest_route(self::NAMESPACE, '/dashboard', [
            'methods' => 'GET',
            'callback' => [__CLASS__, 'getDashboardData'],
            'permission_callback' => [__CLASS__, 'checkPermissions']
        ]);

        // Activities endpoint
        register_rest_route(self::NAMESPACE, '/activities', [
            'methods' => 'GET',
            'callback' => [__CLASS__, 'getActivities'],
            'permission_callback' => [__CLASS__, 'checkPermissions'],
            'args' => [
                'agent_type' => [
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field'
                ],
                'limit' => [
                    'type' => 'integer',
                    'default' => 20,
                    'minimum' => 1,
                    'maximum' => 100
                ],
                'offset' => [
                    'type' => 'integer',
                    'default' => 0,
                    'minimum' => 0
                ]
            ]
        ]);

        // Performance metrics endpoint
        register_rest_route(self::NAMESPACE, '/metrics/performance', [
            'methods' => 'GET',
            'callback' => [__CLASS__, 'getPerformanceMetrics'],
            'permission_callback' => [__CLASS__, 'checkPermissions'],
            'args' => [
                'hours' => [
                    'type' => 'integer',
                    'default' => 24,
                    'minimum' => 1,
                    'maximum' => 168
                ]
            ]
        ]);

        // Settings endpoints
        register_rest_route(self::NAMESPACE, '/settings', [
            [
                'methods' => 'GET',
                'callback' => [__CLASS__, 'getSettings'],
                'permission_callback' => [__CLASS__, 'checkPermissions']
            ],
            [
                'methods' => 'POST',
                'callback' => [__CLASS__, 'updateSettings'],
                'permission_callback' => [__CLASS__, 'checkPermissions'],
                'args' => [
                    'settings' => [
                        'required' => true,
                        'type' => 'object',
                        'validate_callback' => [__CLASS__, 'validateSettings']
                    ]
                ]
            ]
        ]);

        // Brand data endpoint
        register_rest_route(self::NAMESPACE, '/brand-data', [
            'methods' => 'GET',
            'callback' => [__CLASS__, 'getBrandData'],
            'permission_callback' => [__CLASS__, 'checkPermissions'],
            'args' => [
                'data_type' => [
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field'
                ]
            ]
        ]);

        // Status endpoint
        register_rest_route(self::NAMESPACE, '/status', [
            'methods' => 'GET',
            'callback' => [__CLASS__, 'getStatus'],
            'permission_callback' => '__return_true' // Public endpoint
        ]);
    }

    /**
     * Execute agent action
     */
    public static function executeAgentAction($request)
    {
        $agent_type = $request->get_param('agent_type');
        $action = $request->get_param('action');
        $data = $request->get_json_params() ?? [];

        // Rate limiting
        if (!SkyyRoseSecurity::checkRateLimit("agent_action_{$agent_type}_{$action}", 10, 60)) {
            return new WP_Error(
                'rate_limit_exceeded',
                __('Rate limit exceeded. Please try again later.', SKYY_ROSE_AI_TEXT_DOMAIN),
                ['status' => 429]
            );
        }

        try {
            $result = null;

            switch ($agent_type) {
                case 'brand_intelligence':
                    if ($action === 'analyze_brand') {
                        $result = BrandIntelligenceAgent::getInstance()->analyzeBrand($data);
                    }
                    break;

                case 'inventory':
                    if ($action === 'scan_assets') {
                        $result = InventoryAgent::getInstance()->scanAssets($data);
                    } elseif ($action === 'optimize_assets') {
                        $result = InventoryAgent::getInstance()->optimizeAssets();
                    }
                    break;

                case 'wordpress':
                    if ($action === 'optimize_wordpress') {
                        $result = WordPressAgent::getInstance()->optimizeWordPress($data);
                    }
                    break;

                case 'performance':
                    if ($action === 'check_performance') {
                        $result = PerformanceAgent::getInstance()->checkPerformance($data);
                    }
                    break;

                case 'security':
                    if ($action === 'run_security_scan') {
                        $result = SecurityAgent::getInstance()->runSecurityScan($data);
                    }
                    break;

                default:
                    return new WP_Error(
                        'invalid_agent',
                        __('Invalid agent type.', SKYY_ROSE_AI_TEXT_DOMAIN),
                        ['status' => 400]
                    );
            }

            if ($result === null) {
                return new WP_Error(
                    'invalid_action',
                    __('Invalid action for agent.', SKYY_ROSE_AI_TEXT_DOMAIN),
                    ['status' => 400]
                );
            }

            // Log the action
            SkyyRoseSecurity::logSecurityEvent('agent_action_executed', [
                'agent_type' => $agent_type,
                'action' => $action,
                'user_id' => get_current_user_id()
            ]);

            return rest_ensure_response($result);

        } catch (Exception $e) {
            return new WP_Error(
                'agent_execution_failed',
                $e->getMessage(),
                ['status' => 500]
            );
        }
    }

    /**
     * Get dashboard data
     */
    public static function getDashboardData($request)
    {
        $db = SkyyRoseDatabase::getInstance();
        
        $dashboard_data = [
            'agents_status' => self::getAgentsStatus(),
            'recent_activities' => $db->getAgentActivities(null, 10),
            'performance_overview' => self::getPerformanceOverview(),
            'security_overview' => self::getSecurityOverview(),
            'quick_stats' => self::getQuickStats()
        ];

        return rest_ensure_response($dashboard_data);
    }

    /**
     * Get activities
     */
    public static function getActivities($request)
    {
        $db = SkyyRoseDatabase::getInstance();
        
        $agent_type = $request->get_param('agent_type');
        $limit = $request->get_param('limit');
        $offset = $request->get_param('offset');

        $activities = $db->getAgentActivities($agent_type, $limit, $offset);

        return rest_ensure_response([
            'activities' => $activities,
            'pagination' => [
                'limit' => $limit,
                'offset' => $offset,
                'has_more' => count($activities) === $limit
            ]
        ]);
    }

    /**
     * Get performance metrics
     */
    public static function getPerformanceMetrics($request)
    {
        $db = SkyyRoseDatabase::getInstance();
        $hours = $request->get_param('hours');

        $metrics = $db->getPerformanceMetrics(null, $hours);

        // Group metrics by type
        $grouped_metrics = [];
        foreach ($metrics as $metric) {
            $grouped_metrics[$metric->metric_type][] = [
                'value' => floatval($metric->metric_value),
                'unit' => $metric->metric_unit,
                'timestamp' => $metric->recorded_at
            ];
        }

        return rest_ensure_response([
            'metrics' => $grouped_metrics,
            'timeframe' => $hours . ' hours'
        ]);
    }

    /**
     * Get settings
     */
    public static function getSettings($request)
    {
        $settings = SkyyRoseSettings::getInstance();
        return rest_ensure_response($settings->getAll());
    }

    /**
     * Update settings
     */
    public static function updateSettings($request)
    {
        $new_settings = $request->get_param('settings');
        $settings = SkyyRoseSettings::getInstance();

        // Validate and sanitize settings
        $sanitized_settings = $settings->sanitizeSettings($new_settings);
        
        // Update settings
        update_option('skyy_rose_ai_settings', $sanitized_settings);

        // Log settings change
        SkyyRoseSecurity::logSecurityEvent('settings_updated', [
            'user_id' => get_current_user_id(),
            'timestamp' => current_time('mysql')
        ]);

        return rest_ensure_response([
            'success' => true,
            'message' => __('Settings updated successfully.', SKYY_ROSE_AI_TEXT_DOMAIN),
            'settings' => $sanitized_settings
        ]);
    }

    /**
     * Get brand data
     */
    public static function getBrandData($request)
    {
        $db = SkyyRoseDatabase::getInstance();
        $data_type = $request->get_param('data_type');

        $brand_data = $db->getBrandData($data_type);

        return rest_ensure_response([
            'brand_data' => $brand_data,
            'count' => count($brand_data)
        ]);
    }

    /**
     * Get plugin status
     */
    public static function getStatus($request)
    {
        return rest_ensure_response([
            'plugin' => 'Skyy Rose AI Agents',
            'version' => SKYY_ROSE_AI_VERSION,
            'status' => 'active',
            'wp_version' => get_bloginfo('version'),
            'php_version' => PHP_VERSION,
            'agents_enabled' => self::getEnabledAgentsCount(),
            'last_activity' => self::getLastActivityTime()
        ]);
    }

    /**
     * Permission callback
     */
    public static function checkPermissions($request)
    {
        return current_user_can('manage_options');
    }

    /**
     * Validate agent type
     */
    public static function validateAgentType($param, $request, $key)
    {
        $valid_agents = [
            'brand_intelligence',
            'inventory',
            'wordpress',
            'performance',
            'security'
        ];

        return in_array($param, $valid_agents);
    }

    /**
     * Validate agent action
     */
    public static function validateAgentAction($param, $request, $key)
    {
        $valid_actions = [
            'analyze_brand',
            'scan_assets',
            'optimize_assets',
            'optimize_wordpress',
            'check_performance',
            'run_security_scan'
        ];

        return in_array($param, $valid_actions);
    }

    /**
     * Validate settings
     */
    public static function validateSettings($param, $request, $key)
    {
        return is_array($param);
    }

    /**
     * Helper methods
     */
    private static function getAgentsStatus()
    {
        $settings = SkyyRoseSettings::getInstance();
        
        return [
            'brand_intelligence' => $settings->get('agents.brand_intelligence.enabled', true),
            'inventory' => $settings->get('agents.inventory.enabled', true),
            'wordpress' => $settings->get('agents.wordpress.enabled', true),
            'performance' => $settings->get('agents.performance.enabled', true),
            'security' => $settings->get('agents.security.enabled', true)
        ];
    }

    private static function getPerformanceOverview()
    {
        $db = SkyyRoseDatabase::getInstance();
        $recent_metrics = $db->getPerformanceMetrics('overall_score', 24);
        
        if (empty($recent_metrics)) {
            return ['score' => 0, 'trend' => 'neutral'];
        }

        $latest_score = end($recent_metrics)->metric_value;
        $trend = count($recent_metrics) > 1 ? 
            ($latest_score > $recent_metrics[0]->metric_value ? 'up' : 'down') : 
            'neutral';

        return [
            'score' => round($latest_score, 2),
            'trend' => $trend
        ];
    }

    private static function getSecurityOverview()
    {
        $db = SkyyRoseDatabase::getInstance();
        $recent_activities = $db->getAgentActivities('security', 5);
        
        $last_scan = null;
        $threat_level = 'low';
        
        foreach ($recent_activities as $activity) {
            if ($activity->action === 'security_scan' && $activity->status === 'completed') {
                $last_scan = $activity;
                break;
            }
        }

        if ($last_scan && $last_scan->result) {
            $result = json_decode($last_scan->result, true);
            $threat_level = $result['risk_level'] ?? 'low';
        }

        return [
            'threat_level' => $threat_level,
            'last_scan' => $last_scan ? $last_scan->created_at : null
        ];
    }

    private static function getQuickStats()
    {
        $db = SkyyRoseDatabase::getInstance();
        
        return [
            'total_activities' => count($db->getAgentActivities()),
            'activities_today' => count($db->getAgentActivities(null, 100)), // Simplified
            'enabled_agents' => self::getEnabledAgentsCount(),
            'last_optimization' => self::getLastOptimizationTime()
        ];
    }

    private static function getEnabledAgentsCount()
    {
        $status = self::getAgentsStatus();
        return count(array_filter($status));
    }

    private static function getLastActivityTime()
    {
        $db = SkyyRoseDatabase::getInstance();
        $activities = $db->getAgentActivities(null, 1);
        
        return !empty($activities) ? $activities[0]->created_at : null;
    }

    private static function getLastOptimizationTime()
    {
        $db = SkyyRoseDatabase::getInstance();
        $activities = $db->getAgentActivities('wordpress', 10);
        
        foreach ($activities as $activity) {
            if (strpos($activity->action, 'optimize') !== false) {
                return $activity->created_at;
            }
        }
        
        return null;
    }
}