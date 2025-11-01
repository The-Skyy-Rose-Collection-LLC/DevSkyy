<?php
/**
 * Admin interface management
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Manages WordPress admin interface for the plugin
 */
class SkyyRoseAdmin
{
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
        $this->settings = SkyyRoseSettings::getInstance();
        $this->init();
    }

    /**
     * Initialize admin functionality
     */
    private function init()
    {
        add_action('admin_menu', [$this, 'addAdminMenu']);
        add_action('admin_enqueue_scripts', [$this, 'enqueueAdminAssets']);
        add_action('admin_notices', [$this, 'showAdminNotices']);
        add_action('wp_dashboard_setup', [$this, 'addDashboardWidgets']);
        add_filter('plugin_action_links_' . SKYY_ROSE_AI_PLUGIN_BASENAME, [$this, 'addPluginActionLinks']);
    }

    /**
     * Add admin menu pages
     */
    public function addAdminMenu()
    {
        // Main menu page
        add_menu_page(
            __('Skyy Rose AI Agents', SKYY_ROSE_AI_TEXT_DOMAIN),
            __('AI Agents', SKYY_ROSE_AI_TEXT_DOMAIN),
            'manage_options',
            'skyy-rose-ai-agents',
            [$this, 'renderDashboardPage'],
            'data:image/svg+xml;base64,' . base64_encode('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>'),
            30
        );

        // Dashboard submenu
        add_submenu_page(
            'skyy-rose-ai-agents',
            __('Dashboard', SKYY_ROSE_AI_TEXT_DOMAIN),
            __('Dashboard', SKYY_ROSE_AI_TEXT_DOMAIN),
            'manage_options',
            'skyy-rose-ai-agents',
            [$this, 'renderDashboardPage']
        );

        // Agents submenu
        add_submenu_page(
            'skyy-rose-ai-agents',
            __('Agents', SKYY_ROSE_AI_TEXT_DOMAIN),
            __('Agents', SKYY_ROSE_AI_TEXT_DOMAIN),
            'manage_options',
            'skyy-rose-ai-agents-agents',
            [$this, 'renderAgentsPage']
        );

        // Analytics submenu
        add_submenu_page(
            'skyy-rose-ai-agents',
            __('Analytics', SKYY_ROSE_AI_TEXT_DOMAIN),
            __('Analytics', SKYY_ROSE_AI_TEXT_DOMAIN),
            'manage_options',
            'skyy-rose-ai-agents-analytics',
            [$this, 'renderAnalyticsPage']
        );

        // Settings submenu
        add_submenu_page(
            'skyy-rose-ai-agents',
            __('Settings', SKYY_ROSE_AI_TEXT_DOMAIN),
            __('Settings', SKYY_ROSE_AI_TEXT_DOMAIN),
            'manage_options',
            'skyy-rose-ai-agents-settings',
            [$this, 'renderSettingsPage']
        );
    }

    /**
     * Enqueue admin assets
     */
    public function enqueueAdminAssets($hook_suffix)
    {
        // Only load on our plugin pages
        if (strpos($hook_suffix, 'skyy-rose-ai-agents') === false) {
            return;
        }

        // Admin CSS
        wp_enqueue_style(
            'skyy-rose-ai-admin',
            SKYY_ROSE_AI_PLUGIN_URL . 'admin/css/admin.css',
            [],
            SKYY_ROSE_AI_VERSION
        );

        // Admin JS
        wp_enqueue_script(
            'skyy-rose-ai-admin',
            SKYY_ROSE_AI_PLUGIN_URL . 'admin/js/admin.js',
            ['jquery', 'wp-api'],
            SKYY_ROSE_AI_VERSION,
            true
        );

        // Localize script
        wp_localize_script('skyy-rose-ai-admin', 'skyyRoseAI', [
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => SkyyRoseSecurity::createNonce('skyy_rose_agent_action'),
            'strings' => [
                'confirm_action' => __('Are you sure you want to perform this action?', SKYY_ROSE_AI_TEXT_DOMAIN),
                'loading' => __('Loading...', SKYY_ROSE_AI_TEXT_DOMAIN),
                'error' => __('An error occurred. Please try again.', SKYY_ROSE_AI_TEXT_DOMAIN),
                'success' => __('Action completed successfully.', SKYY_ROSE_AI_TEXT_DOMAIN)
            ]
        ]);

        // Chart.js for analytics
        wp_enqueue_script(
            'chart-js',
            'https://cdn.jsdelivr.net/npm/chart.js',
            [],
            '3.9.1',
            true
        );
    }

    /**
     * Show admin notices
     */
    public function showAdminNotices()
    {
        // Check if OpenAI is configured
        $openai_key = $this->settings->get('integrations.openai.api_key');
        if (empty($openai_key)) {
            echo '<div class="notice notice-warning is-dismissible">';
            echo '<p>' . sprintf(
                __('To unlock AI-powered features, please configure your OpenAI API key in the <a href="%s">settings</a>.', SKYY_ROSE_AI_TEXT_DOMAIN),
                admin_url('admin.php?page=skyy-rose-ai-agents-settings')
            ) . '</p>';
            echo '</div>';
        }

        // Check for recent agent failures
        $db = SkyyRoseDatabase::getInstance();
        $recent_failures = $db->getAgentActivities(null, 5);
        $failed_activities = array_filter($recent_failures, function($activity) {
            return $activity->status === 'failed';
        });

        if (!empty($failed_activities)) {
            echo '<div class="notice notice-error is-dismissible">';
            echo '<p>' . sprintf(
                __('Some agent activities have failed recently. Please check the <a href="%s">dashboard</a> for details.', SKYY_ROSE_AI_TEXT_DOMAIN),
                admin_url('admin.php?page=skyy-rose-ai-agents')
            ) . '</p>';
            echo '</div>';
        }
    }

    /**
     * Add dashboard widgets
     */
    public function addDashboardWidgets()
    {
        wp_add_dashboard_widget(
            'skyy_rose_ai_status',
            __('AI Agents Status', SKYY_ROSE_AI_TEXT_DOMAIN),
            [$this, 'renderDashboardWidget']
        );
    }

    /**
     * Add plugin action links
     */
    public function addPluginActionLinks($links)
    {
        $plugin_links = [
            '<a href="' . admin_url('admin.php?page=skyy-rose-ai-agents') . '">' . __('Dashboard', SKYY_ROSE_AI_TEXT_DOMAIN) . '</a>',
            '<a href="' . admin_url('admin.php?page=skyy-rose-ai-agents-settings') . '">' . __('Settings', SKYY_ROSE_AI_TEXT_DOMAIN) . '</a>'
        ];

        return array_merge($plugin_links, $links);
    }

    /**
     * Render dashboard page
     */
    public function renderDashboardPage()
    {
        require_once SKYY_ROSE_AI_PLUGIN_PATH . 'admin/class-skyy-rose-dashboard.php';
        $dashboard = new SkyyRoseDashboard();
        $dashboard->render();
    }

    /**
     * Render agents page
     */
    public function renderAgentsPage()
    {
        ?>
        <div class="wrap">
            <h1><?php _e('AI Agents Management', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h1>
            
            <div class="skyy-rose-agents-grid">
                <?php $this->renderAgentCard('brand_intelligence', [
                    'title' => __('Brand Intelligence Agent', SKYY_ROSE_AI_TEXT_DOMAIN),
                    'description' => __('Analyzes brand consistency and provides optimization recommendations.', SKYY_ROSE_AI_TEXT_DOMAIN),
                    'icon' => '🎨',
                    'actions' => ['analyze_brand']
                ]); ?>

                <?php $this->renderAgentCard('inventory', [
                    'title' => __('Inventory Agent', SKYY_ROSE_AI_TEXT_DOMAIN),
                    'description' => __('Manages digital assets and optimizes file storage.', SKYY_ROSE_AI_TEXT_DOMAIN),
                    'icon' => '📦',
                    'actions' => ['scan_inventory']
                ]); ?>

                <?php $this->renderAgentCard('wordpress', [
                    'title' => __('WordPress Agent', SKYY_ROSE_AI_TEXT_DOMAIN),
                    'description' => __('Optimizes WordPress performance, security, and SEO.', SKYY_ROSE_AI_TEXT_DOMAIN),
                    'icon' => '🌐',
                    'actions' => ['optimize_wordpress']
                ]); ?>

                <?php $this->renderAgentCard('performance', [
                    'title' => __('Performance Agent', SKYY_ROSE_AI_TEXT_DOMAIN),
                    'description' => __('Monitors site performance and identifies bottlenecks.', SKYY_ROSE_AI_TEXT_DOMAIN),
                    'icon' => '⚡',
                    'actions' => ['check_performance']
                ]); ?>

                <?php $this->renderAgentCard('security', [
                    'title' => __('Security Agent', SKYY_ROSE_AI_TEXT_DOMAIN),
                    'description' => __('Scans for security vulnerabilities and threats.', SKYY_ROSE_AI_TEXT_DOMAIN),
                    'icon' => '🛡️',
                    'actions' => ['run_security_scan']
                ]); ?>
            </div>
        </div>
        <?php
    }

    /**
     * Render analytics page
     */
    public function renderAnalyticsPage()
    {
        $db = SkyyRoseDatabase::getInstance();
        $performance_metrics = $db->getPerformanceMetrics();
        
        ?>
        <div class="wrap">
            <h1><?php _e('Analytics & Reports', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h1>
            
            <div class="skyy-rose-analytics-grid">
                <div class="analytics-card">
                    <h3><?php _e('Performance Metrics', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h3>
                    <canvas id="performance-chart"></canvas>
                </div>
                
                <div class="analytics-card">
                    <h3><?php _e('Agent Activity', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h3>
                    <canvas id="activity-chart"></canvas>
                </div>
                
                <div class="analytics-card">
                    <h3><?php _e('Recent Activities', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h3>
                    <?php $this->renderRecentActivities(); ?>
                </div>
            </div>
        </div>
        
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize charts
            const performanceData = <?php echo wp_json_encode($this->getPerformanceChartData()); ?>;
            const activityData = <?php echo wp_json_encode($this->getActivityChartData()); ?>;
            
            // Render performance chart
            new Chart(document.getElementById('performance-chart'), {
                type: 'line',
                data: performanceData,
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: '<?php _e('Performance Over Time', SKYY_ROSE_AI_TEXT_DOMAIN); ?>'
                        }
                    }
                }
            });
            
            // Render activity chart
            new Chart(document.getElementById('activity-chart'), {
                type: 'doughnut',
                data: activityData,
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: '<?php _e('Agent Activity Distribution', SKYY_ROSE_AI_TEXT_DOMAIN); ?>'
                        }
                    }
                }
            });
        });
        </script>
        <?php
    }

    /**
     * Render settings page
     */
    public function renderSettingsPage()
    {
        if (isset($_POST['submit'])) {
            check_admin_referer('skyy_rose_ai_settings_nonce');
            
            $settings = $_POST['skyy_rose_ai_settings'] ?? [];
            $sanitized_settings = $this->settings->sanitizeSettings($settings);
            update_option('skyy_rose_ai_settings', $sanitized_settings);
            
            echo '<div class="notice notice-success is-dismissible"><p>' . 
                 __('Settings saved successfully.', SKYY_ROSE_AI_TEXT_DOMAIN) . 
                 '</p></div>';
        }

        $current_settings = $this->settings->getAll();
        ?>
        <div class="wrap">
            <h1><?php _e('Skyy Rose AI Agents Settings', SKYY_ROSE_AI_TEXT_DOMAIN); ?></h1>
            
            <form method="post" action="">
                <?php wp_nonce_field('skyy_rose_ai_settings_nonce'); ?>
                
                <nav class="nav-tab-wrapper">
                    <a href="#general" class="nav-tab nav-tab-active"><?php _e('General', SKYY_ROSE_AI_TEXT_DOMAIN); ?></a>
                    <a href="#agents" class="nav-tab"><?php _e('Agents', SKYY_ROSE_AI_TEXT_DOMAIN); ?></a>
                    <a href="#integrations" class="nav-tab"><?php _e('Integrations', SKYY_ROSE_AI_TEXT_DOMAIN); ?></a>
                    <a href="#notifications" class="nav-tab"><?php _e('Notifications', SKYY_ROSE_AI_TEXT_DOMAIN); ?></a>
                </nav>
                
                <div id="general" class="tab-content">
                    <?php $this->renderGeneralSettings($current_settings); ?>
                </div>
                
                <div id="agents" class="tab-content" style="display: none;">
                    <?php $this->renderAgentSettings($current_settings); ?>
                </div>
                
                <div id="integrations" class="tab-content" style="display: none;">
                    <?php $this->renderIntegrationSettings($current_settings); ?>
                </div>
                
                <div id="notifications" class="tab-content" style="display: none;">
                    <?php $this->renderNotificationSettings($current_settings); ?>
                </div>
                
                <?php submit_button(); ?>
            </form>
        </div>
        <?php
    }

    /**
     * Render dashboard widget
     */
    public function renderDashboardWidget()
    {
        $db = SkyyRoseDatabase::getInstance();
        $recent_activities = $db->getAgentActivities(null, 5);
        
        echo '<div class="skyy-rose-widget">';
        echo '<p><strong>' . __('Recent Agent Activities:', SKYY_ROSE_AI_TEXT_DOMAIN) . '</strong></p>';
        
        if (empty($recent_activities)) {
            echo '<p>' . __('No recent activities.', SKYY_ROSE_AI_TEXT_DOMAIN) . '</p>';
        } else {
            echo '<ul>';
            foreach ($recent_activities as $activity) {
                $status_class = $activity->status === 'completed' ? 'success' : ($activity->status === 'failed' ? 'error' : 'info');
                echo '<li class="status-' . $status_class . '">';
                echo '<strong>' . esc_html(ucwords(str_replace('_', ' ', $activity->agent_type))) . '</strong>: ';
                echo esc_html($activity->action) . ' - ';
                echo '<span class="status">' . esc_html($activity->status) . '</span>';
                echo '</li>';
            }
            echo '</ul>';
        }
        
        echo '<p><a href="' . admin_url('admin.php?page=skyy-rose-ai-agents') . '" class="button button-primary">' . 
             __('View Full Dashboard', SKYY_ROSE_AI_TEXT_DOMAIN) . '</a></p>';
        echo '</div>';
    }

    /**
     * Helper methods for rendering
     */
    private function renderAgentCard($agent_type, $config)
    {
        $enabled = $this->settings->get("agents.{$agent_type}.enabled", true);
        $status_class = $enabled ? 'enabled' : 'disabled';
        
        ?>
        <div class="agent-card <?php echo $status_class; ?>" data-agent="<?php echo esc_attr($agent_type); ?>">
            <div class="agent-icon"><?php echo $config['icon']; ?></div>
            <h3><?php echo esc_html($config['title']); ?></h3>
            <p><?php echo esc_html($config['description']); ?></p>
            
            <div class="agent-status">
                <span class="status-indicator"></span>
                <?php echo $enabled ? __('Enabled', SKYY_ROSE_AI_TEXT_DOMAIN) : __('Disabled', SKYY_ROSE_AI_TEXT_DOMAIN); ?>
            </div>
            
            <?php if ($enabled && !empty($config['actions'])): ?>
            <div class="agent-actions">
                <?php foreach ($config['actions'] as $action): ?>
                <button class="button agent-action" data-action="<?php echo esc_attr($action); ?>">
                    <?php echo esc_html(ucwords(str_replace('_', ' ', $action))); ?>
                </button>
                <?php endforeach; ?>
            </div>
            <?php endif; ?>
        </div>
        <?php
    }

    private function renderRecentActivities()
    {
        $db = SkyyRoseDatabase::getInstance();
        $activities = $db->getAgentActivities(null, 10);
        
        if (empty($activities)) {
            echo '<p>' . __('No recent activities.', SKYY_ROSE_AI_TEXT_DOMAIN) . '</p>';
            return;
        }
        
        echo '<table class="wp-list-table widefat">';
        echo '<thead><tr>';
        echo '<th>' . __('Agent', SKYY_ROSE_AI_TEXT_DOMAIN) . '</th>';
        echo '<th>' . __('Action', SKYY_ROSE_AI_TEXT_DOMAIN) . '</th>';
        echo '<th>' . __('Status', SKYY_ROSE_AI_TEXT_DOMAIN) . '</th>';
        echo '<th>' . __('Date', SKYY_ROSE_AI_TEXT_DOMAIN) . '</th>';
        echo '</tr></thead><tbody>';
        
        foreach ($activities as $activity) {
            echo '<tr>';
            echo '<td>' . esc_html(ucwords(str_replace('_', ' ', $activity->agent_type))) . '</td>';
            echo '<td>' . esc_html($activity->action) . '</td>';
            echo '<td><span class="status-' . $activity->status . '">' . esc_html($activity->status) . '</span></td>';
            echo '<td>' . esc_html(mysql2date('F j, Y g:i a', $activity->created_at)) . '</td>';
            echo '</tr>';
        }
        
        echo '</tbody></table>';
    }

    private function getPerformanceChartData()
    {
        // This would return actual performance data
        return [
            'labels' => ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'datasets' => [[
                'label' => 'Performance Score',
                'data' => [65, 70, 75, 80, 85, 90],
                'borderColor' => 'rgb(75, 192, 192)',
                'tension' => 0.1
            ]]
        ];
    }

    private function getActivityChartData()
    {
        // This would return actual activity data
        return [
            'labels' => ['Brand Intelligence', 'Inventory', 'WordPress', 'Performance', 'Security'],
            'datasets' => [[
                'data' => [12, 19, 3, 5, 2],
                'backgroundColor' => [
                    'rgb(255, 99, 132)',
                    'rgb(54, 162, 235)',
                    'rgb(255, 205, 86)',
                    'rgb(75, 192, 192)',
                    'rgb(153, 102, 255)'
                ]
            ]]
        ];
    }

    private function renderGeneralSettings($settings)
    {
        // Render general settings form fields
        echo '<table class="form-table">';
        // Add form fields here
        echo '</table>';
    }

    private function renderAgentSettings($settings)
    {
        // Render agent settings form fields
        echo '<table class="form-table">';
        // Add form fields here
        echo '</table>';
    }

    private function renderIntegrationSettings($settings)
    {
        // Render integration settings form fields
        echo '<table class="form-table">';
        // Add form fields here
        echo '</table>';
    }

    private function renderNotificationSettings($settings)
    {
        // Render notification settings form fields
        echo '<table class="form-table">';
        // Add form fields here
        echo '</table>';
    }
}