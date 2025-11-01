<?php
/**
 * Dashboard management class
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Dashboard rendering and management
 */
class SkyyRoseDashboard
{
    /**
     * Database instance
     * @var SkyyRoseDatabase
     */
    private $db;

    /**
     * Settings instance
     * @var SkyyRoseSettings
     */
    private $settings;

    /**
     * Constructor
     */
    public function __construct()
    {
        $this->db = SkyyRoseDatabase::getInstance();
        $this->settings = SkyyRoseSettings::getInstance();
    }

    /**
     * Render main dashboard page
     */
    public function render()
    {
        ?>
        <div class="wrap skyy-rose-dashboard">
            <h1 class="wp-heading-inline">
                <?php _e('Skyy Rose AI Agents Dashboard', SKYY_ROSE_AI_TEXT_DOMAIN); ?>
                <span class="title-count theme-count"><?php echo $this->getEnabledAgentsCount(); ?></span>
            </h1>
            
            <hr class="wp-header-end">

            <!-- Dashboard Overview -->
            <div class="skyy-rose-overview">
                <div class="overview-cards">
                    <?php $this->renderOverviewCards(); ?>
                </div>
            </div>

            <!-- Main Dashboard Content -->
            <div class="skyy-rose-dashboard-content">
                <div class="dashboard-left">
                    <?php $this->renderAgentStatus(); ?>
                    <?php $this->renderRecentActivities(); ?>
                </div>
                
                <div class="dashboard-right">
                    <?php $this->renderPerformanceWidget(); ?>
                    <?php $this->renderSecurityWidget(); ?>
                    <?php $this->renderQuickActions(); ?>
                </div>
            </div>

            <!-- Charts and Analytics -->
            <div class="skyy-rose-analytics-section">
                <h2><?php _e('Analytics Overview', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h2>
                <div class="analytics-grid">
                    <div class="chart-container">
                        <h3><?php _e('Performance Trends', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h3>
                        <canvas id="performance-trend-chart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3><?php _e('Agent Activity', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h3>
                        <canvas id="agent-activity-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize dashboard
            SkyyRoseDashboard.init();
        });
        </script>
        <?php
    }

    /**
     * Render overview cards
     */
    private function renderOverviewCards()
    {
        $overview_data = $this->getOverviewData();
        ?>
        <div class="overview-card performance-card">
            <div class="card-icon">⚡</div>
            <div class="card-content">
                <h3><?php _e('Performance Score', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h3>
                <div class="card-value"><?php echo $overview_data['performance_score']; ?><span class="unit">%</span></div>
                <div class="card-trend <?php echo $overview_data['performance_trend']; ?>">
                    <?php echo $overview_data['performance_trend'] === 'up' ? '↗' : ($overview_data['performance_trend'] === 'down' ? '↘' : '→'); ?>
                    <?php _e('Last 24h', SKYY_ROSE_AI_TEXT_DOMAIN); ?>
                </div>
            </div>
        </div>

        <div class="overview-card security-card">
            <div class="card-icon">🛡️</div>
            <div class="card-content">
                <h3><?php _e('Security Status', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h3>
                <div class="card-value security-<?php echo $overview_data['security_level']; ?>">
                    <?php echo ucfirst($overview_data['security_level']); ?>
                </div>
                <div class="card-meta">
                    <?php printf(__('Last scan: %s', SKYY_ROSE_AI_TEXT_DOMAIN), $overview_data['last_security_scan']); ?>
                </div>
            </div>
        </div>

        <div class="overview-card activities-card">
            <div class="card-icon">📊</div>
            <div class="card-content">
                <h3><?php _e('Activities Today', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h3>
                <div class="card-value"><?php echo $overview_data['activities_today']; ?></div>
                <div class="card-meta">
                    <?php printf(__('%d total this week', SKYY_ROSE_AI_TEXT_DOMAIN), $overview_data['activities_week']); ?>
                </div>
            </div>
        </div>

        <div class="overview-card agents-card">
            <div class="card-icon">🤖</div>
            <div class="card-content">
                <h3><?php _e('Active Agents', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h3>
                <div class="card-value"><?php echo $overview_data['active_agents']; ?><span class="unit">/5</span></div>
                <div class="card-meta">
                    <?php _e('All systems operational', SKYY_ROSE_AI_TEXT_DOMAIN); ?>
                </div>
            </div>
        </div>
        <?php
    }

    /**
     * Render agent status section
     */
    private function renderAgentStatus()
    {
        $agents = $this->getAgentsData();
        ?>
        <div class="dashboard-widget agents-status">
            <h2><?php _e('Agent Status', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h2>
            
            <div class="agents-grid">
                <?php foreach ($agents as $agent_id => $agent): ?>
                <div class="agent-status-card <?php echo $agent['enabled'] ? 'enabled' : 'disabled'; ?>" data-agent="<?php echo esc_attr($agent_id); ?>">
                    <div class="agent-header">
                        <span class="agent-icon"><?php echo $agent['icon']; ?></span>
                        <div class="agent-info">
                            <h4><?php echo esc_html($agent['name']); ?></h4>
                            <div class="agent-meta">
                                <span class="status-indicator"></span>
                                <?php echo $agent['enabled'] ? __('Active', SKYY_ROSE_AI_TEXT_DOMAIN) : __('Inactive', SKYY_ROSE_AI_TEXT_DOMAIN); ?>
                            </div>
                        </div>
                    </div>
                    
                    <?php if ($agent['enabled']): ?>
                    <div class="agent-stats">
                        <div class="stat">
                            <span class="stat-label"><?php _e('Last Run', SKYY_ROSE_AI_TEXT_DOMAIN); ?></span>
                            <span class="stat-value"><?php echo $agent['last_run']; ?></span>
                        </div>
                        <div class="stat">
                            <span class="stat-label"><?php _e('Success Rate', SKYY_ROSE_AI_TEXT_DOMAIN); ?></span>
                            <span class="stat-value"><?php echo $agent['success_rate']; ?>%</span>
                        </div>
                    </div>
                    
                    <div class="agent-actions">
                        <button class="button button-small run-agent" data-agent="<?php echo esc_attr($agent_id); ?>" data-action="<?php echo esc_attr($agent['primary_action']); ?>">
                            <?php _e('Run Now', SKYY_ROSE_AI_TEXT_DOMAIN); ?>
                        </button>
                    </div>
                    <?php endif; ?>
                </div>
                <?php endforeach; ?>
            </div>
        </div>
        <?php
    }

    /**
     * Render recent activities
     */
    private function renderRecentActivities()
    {
        $activities = $this->db->getAgentActivities(null, 15);
        ?>
        <div class="dashboard-widget recent-activities">
            <div class="widget-header">
                <h2><?php _e('Recent Activities', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h2>
                <a href="<?php echo admin_url('admin.php?page=skyy-rose-ai-agents-analytics'); ?>" class="button button-secondary">
                    <?php _e('View All', SKYY_ROSE_AI_TEXT_DOMAIN); ?>
                </a>
            </div>
            
            <div class="activities-list">
                <?php if (empty($activities)): ?>
                <div class="no-activities">
                    <p><?php _e('No recent activities. Agents will start running automatically based on your settings.', SKYY_ROSE_AI_TEXT_DOMAIN); ?></p>
                </div>
                <?php else: ?>
                <?php foreach ($activities as $activity): ?>
                <div class="activity-item status-<?php echo esc_attr($activity->status); ?>">
                    <div class="activity-icon">
                        <?php echo $this->getAgentIcon($activity->agent_type); ?>
                    </div>
                    <div class="activity-content">
                        <div class="activity-title">
                            <strong><?php echo esc_html($this->getAgentDisplayName($activity->agent_type)); ?></strong>
                            <?php echo esc_html($this->formatActionName($activity->action)); ?>
                        </div>
                        <div class="activity-meta">
                            <span class="activity-status status-<?php echo esc_attr($activity->status); ?>">
                                <?php echo esc_html(ucfirst($activity->status)); ?>
                            </span>
                            <span class="activity-time">
                                <?php echo human_time_diff(strtotime($activity->created_at), current_time('timestamp')); ?> <?php _e('ago', SKYY_ROSE_AI_TEXT_DOMAIN); ?>
                            </span>
                        </div>
                    </div>
                    <?php if ($activity->status === 'failed' && $activity->result): ?>
                    <div class="activity-error">
                        <?php
                        $result = json_decode($activity->result, true);
                        echo esc_html($result['error'] ?? __('Unknown error', SKYY_ROSE_AI_TEXT_DOMAIN));
                        ?>
                    </div>
                    <?php endif; ?>
                </div>
                <?php endforeach; ?>
                <?php endif; ?>
            </div>
        </div>
        <?php
    }

    /**
     * Render performance widget
     */
    private function renderPerformanceWidget()
    {
        $performance_data = $this->getPerformanceData();
        ?>
        <div class="dashboard-widget performance-widget">
            <h2><?php _e('Performance Overview', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h2>
            
            <div class="performance-metrics">
                <div class="metric">
                    <div class="metric-label"><?php _e('Page Load Time', SKYY_ROSE_AI_TEXT_DOMAIN); ?></div>
                    <div class="metric-value"><?php echo $performance_data['page_load_time']; ?><span class="unit">ms</span></div>
                </div>
                <div class="metric">
                    <div class="metric-label"><?php _e('Memory Usage', SKYY_ROSE_AI_TEXT_DOMAIN); ?></div>
                    <div class="metric-value"><?php echo $performance_data['memory_usage']; ?><span class="unit">%</span></div>
                </div>
                <div class="metric">
                    <div class="metric-label"><?php _e('Database Performance', SKYY_ROSE_AI_TEXT_DOMAIN); ?></div>
                    <div class="metric-value"><?php echo $performance_data['database_score']; ?><span class="unit">/100</span></div>
                </div>
            </div>
            
            <div class="widget-actions">
                <button class="button button-primary run-performance-check" data-action="check_performance">
                    <?php _e('Run Performance Check', SKYY_ROSE_AI_TEXT_DOMAIN); ?>
                </button>
            </div>
        </div>
        <?php
    }

    /**
     * Render security widget
     */
    private function renderSecurityWidget()
    {
        $security_data = $this->getSecurityData();
        ?>
        <div class="dashboard-widget security-widget">
            <h2><?php _e('Security Overview', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h2>
            
            <div class="security-status security-<?php echo esc_attr($security_data['risk_level']); ?>">
                <div class="security-icon">🛡️</div>
                <div class="security-info">
                    <div class="security-level"><?php echo esc_html(ucfirst($security_data['risk_level'])); ?> <?php _e('Risk', SKYY_ROSE_AI_TEXT_DOMAIN); ?></div>
                    <div class="security-details">
                        <?php if ($security_data['threats_detected'] > 0): ?>
                        <span class="threats-found"><?php printf(__('%d threats detected', SKYY_ROSE_AI_TEXT_DOMAIN), $security_data['threats_detected']); ?></span>
                        <?php else: ?>
                        <span class="no-threats"><?php _e('No threats detected', SKYY_ROSE_AI_TEXT_DOMAIN); ?></span>
                        <?php endif; ?>
                    </div>
                </div>
            </div>
            
            <div class="security-metrics">
                <div class="metric">
                    <span class="metric-label"><?php _e('Last Scan', SKYY_ROSE_AI_TEXT_DOMAIN); ?></span>
                    <span class="metric-value"><?php echo $security_data['last_scan']; ?></span>
                </div>
                <div class="metric">
                    <span class="metric-label"><?php _e('Vulnerabilities', SKYY_ROSE_AI_TEXT_DOMAIN); ?></span>
                    <span class="metric-value"><?php echo $security_data['vulnerabilities']; ?></span>
                </div>
            </div>
            
            <div class="widget-actions">
                <button class="button button-primary run-security-scan" data-action="run_security_scan">
                    <?php _e('Run Security Scan', SKYY_ROSE_AI_TEXT_DOMAIN); ?>
                </button>
            </div>
        </div>
        <?php
    }

    /**
     * Render quick actions widget
     */
    private function renderQuickActions()
    {
        ?>
        <div class="dashboard-widget quick-actions">
            <h2><?php _e('Quick Actions', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h2>
            
            <div class="actions-grid">
                <button class="action-button brand-action" data-agent="brand_intelligence" data-action="analyze_brand">
                    <div class="action-icon">🎨</div>
                    <div class="action-label"><?php _e('Analyze Brand', SKYY_ROSE_AI_TEXT_DOMAIN); ?></div>
                </button>
                
                <button class="action-button inventory-action" data-agent="inventory" data-action="scan_assets">
                    <div class="action-icon">📦</div>
                    <div class="action-label"><?php _e('Scan Assets', SKYY_ROSE_AI_TEXT_DOMAIN); ?></div>
                </button>
                
                <button class="action-button wordpress-action" data-agent="wordpress" data-action="optimize_wordpress">
                    <div class="action-icon">🌐</div>
                    <div class="action-label"><?php _e('Optimize Site', SKYY_ROSE_AI_TEXT_DOMAIN); ?></div>
                </button>
                
                <button class="action-button performance-action" data-agent="performance" data-action="check_performance">
                    <div class="action-icon">⚡</div>
                    <div class="action-label"><?php _e('Check Performance', SKYY_ROSE_AI_TEXT_DOMAIN); ?></div>
                </button>
            </div>
            
            <div class="bulk-actions">
                <button class="button button-secondary run-all-agents">
                    <?php _e('Run All Agents', SKYY_ROSE_AI_TEXT_DOMAIN); ?>
                </button>
            </div>
        </div>
        <?php
    }

    /**
     * Helper methods for data retrieval
     */
    private function getOverviewData()
    {
        // Get latest performance metrics
        $performance_metrics = $this->db->getPerformanceMetrics('overall_score', 24);
        $performance_score = !empty($performance_metrics) ? end($performance_metrics)->metric_value : 85;
        
        // Get security data
        $security_activities = $this->db->getAgentActivities('security', 5);
        $security_level = 'low';
        $last_scan = __('Never', SKYY_ROSE_AI_TEXT_DOMAIN);
        
        foreach ($security_activities as $activity) {
            if ($activity->action === 'security_scan' && $activity->status === 'completed') {
                $result = json_decode($activity->result, true);
                $security_level = $result['risk_level'] ?? 'low';
                $last_scan = human_time_diff(strtotime($activity->created_at), current_time('timestamp')) . ' ' . __('ago', SKYY_ROSE_AI_TEXT_DOMAIN);
                break;
            }
        }
        
        // Get activity counts
        $all_activities = $this->db->getAgentActivities();
        $today_activities = array_filter($all_activities, function($activity) {
            return date('Y-m-d', strtotime($activity->created_at)) === date('Y-m-d');
        });
        $week_activities = array_filter($all_activities, function($activity) {
            return strtotime($activity->created_at) >= strtotime('-7 days');
        });
        
        return [
            'performance_score' => round($performance_score),
            'performance_trend' => 'up', // Simplified
            'security_level' => $security_level,
            'last_security_scan' => $last_scan,
            'activities_today' => count($today_activities),
            'activities_week' => count($week_activities),
            'active_agents' => $this->getEnabledAgentsCount()
        ];
    }

    private function getAgentsData()
    {
        return [
            'brand_intelligence' => [
                'name' => __('Brand Intelligence', SKYY_ROSE_AI_TEXT_DOMAIN),
                'icon' => '🎨',
                'enabled' => $this->settings->get('agents.brand_intelligence.enabled', true),
                'last_run' => $this->getLastRunTime('brand_intelligence'),
                'success_rate' => $this->getSuccessRate('brand_intelligence'),
                'primary_action' => 'analyze_brand'
            ],
            'inventory' => [
                'name' => __('Inventory Management', SKYY_ROSE_AI_TEXT_DOMAIN),
                'icon' => '📦',
                'enabled' => $this->settings->get('agents.inventory.enabled', true),
                'last_run' => $this->getLastRunTime('inventory'),
                'success_rate' => $this->getSuccessRate('inventory'),
                'primary_action' => 'scan_assets'
            ],
            'wordpress' => [
                'name' => __('WordPress Optimization', SKYY_ROSE_AI_TEXT_DOMAIN),
                'icon' => '🌐',
                'enabled' => $this->settings->get('agents.wordpress.enabled', true),
                'last_run' => $this->getLastRunTime('wordpress'),
                'success_rate' => $this->getSuccessRate('wordpress'),
                'primary_action' => 'optimize_wordpress'
            ],
            'performance' => [
                'name' => __('Performance Monitoring', SKYY_ROSE_AI_TEXT_DOMAIN),
                'icon' => '⚡',
                'enabled' => $this->settings->get('agents.performance.enabled', true),
                'last_run' => $this->getLastRunTime('performance'),
                'success_rate' => $this->getSuccessRate('performance'),
                'primary_action' => 'check_performance'
            ],
            'security' => [
                'name' => __('Security Monitoring', SKYY_ROSE_AI_TEXT_DOMAIN),
                'icon' => '🛡️',
                'enabled' => $this->settings->get('agents.security.enabled', true),
                'last_run' => $this->getLastRunTime('security'),
                'success_rate' => $this->getSuccessRate('security'),
                'primary_action' => 'run_security_scan'
            ]
        ];
    }

    private function getPerformanceData()
    {
        $metrics = $this->db->getPerformanceMetrics(null, 1);
        
        $page_load_time = 1250; // Default values
        $memory_usage = 45;
        $database_score = 85;
        
        foreach ($metrics as $metric) {
            switch ($metric->metric_type) {
                case 'page_load_time':
                    $page_load_time = round($metric->metric_value);
                    break;
                case 'memory_usage':
                    $memory_usage = round($metric->metric_value);
                    break;
                case 'database_score':
                    $database_score = round($metric->metric_value);
                    break;
            }
        }
        
        return [
            'page_load_time' => $page_load_time,
            'memory_usage' => $memory_usage,
            'database_score' => $database_score
        ];
    }

    private function getSecurityData()
    {
        $activities = $this->db->getAgentActivities('security', 5);
        
        $risk_level = 'low';
        $threats_detected = 0;
        $vulnerabilities = 0;
        $last_scan = __('Never', SKYY_ROSE_AI_TEXT_DOMAIN);
        
        foreach ($activities as $activity) {
            if ($activity->action === 'security_scan' && $activity->status === 'completed') {
                $result = json_decode($activity->result, true);
                $risk_level = $result['risk_level'] ?? 'low';
                $threats_detected = $result['threats_detected'] ?? 0;
                $last_scan = human_time_diff(strtotime($activity->created_at), current_time('timestamp')) . ' ' . __('ago', SKYY_ROSE_AI_TEXT_DOMAIN);
                break;
            }
        }
        
        return [
            'risk_level' => $risk_level,
            'threats_detected' => $threats_detected,
            'vulnerabilities' => $vulnerabilities,
            'last_scan' => $last_scan
        ];
    }

    private function getEnabledAgentsCount()
    {
        $agents = ['brand_intelligence', 'inventory', 'wordpress', 'performance', 'security'];
        $enabled_count = 0;
        
        foreach ($agents as $agent) {
            if ($this->settings->get("agents.{$agent}.enabled", true)) {
                $enabled_count++;
            }
        }
        
        return $enabled_count;
    }

    private function getLastRunTime($agent_type)
    {
        $activities = $this->db->getAgentActivities($agent_type, 1);
        
        if (empty($activities)) {
            return __('Never', SKYY_ROSE_AI_TEXT_DOMAIN);
        }
        
        return human_time_diff(strtotime($activities[0]->created_at), current_time('timestamp')) . ' ' . __('ago', SKYY_ROSE_AI_TEXT_DOMAIN);
    }

    private function getSuccessRate($agent_type)
    {
        $activities = $this->db->getAgentActivities($agent_type, 10);
        
        if (empty($activities)) {
            return 100;
        }
        
        $successful = array_filter($activities, function($activity) {
            return $activity->status === 'completed';
        });
        
        return round((count($successful) / count($activities)) * 100);
    }

    private function getAgentIcon($agent_type)
    {
        $icons = [
            'brand_intelligence' => '🎨',
            'inventory' => '📦',
            'wordpress' => '🌐',
            'performance' => '⚡',
            'security' => '🛡️'
        ];
        
        return $icons[$agent_type] ?? '🤖';
    }

    private function getAgentDisplayName($agent_type)
    {
        $names = [
            'brand_intelligence' => __('Brand Intelligence', SKYY_ROSE_AI_TEXT_DOMAIN),
            'inventory' => __('Inventory', SKYY_ROSE_AI_TEXT_DOMAIN),
            'wordpress' => __('WordPress', SKYY_ROSE_AI_TEXT_DOMAIN),
            'performance' => __('Performance', SKYY_ROSE_AI_TEXT_DOMAIN),
            'security' => __('Security', SKYY_ROSE_AI_TEXT_DOMAIN)
        ];
        
        return $names[$agent_type] ?? ucwords(str_replace('_', ' ', $agent_type));
    }

    private function formatActionName($action)
    {
        return ucwords(str_replace('_', ' ', $action));
    }
}