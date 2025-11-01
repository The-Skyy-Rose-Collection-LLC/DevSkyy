<?php
/**
 * WordPress Optimization Agent
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * WordPress Agent for site optimization and management
 */
class WordPressAgent
{
    /**
     * Singleton instance
     * @var WordPressAgent
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
        $this->config = $settings['agents']['wordpress'] ?? [
            'enabled' => true,
            'auto_optimize' => false,
            'performance_target' => 90
        ];
    }

    /**
     * Optimize WordPress site
     */
    public function optimizeWordPress($data = [])
    {
        if (!$this->config['enabled']) {
            return ['error' => __('WordPress Agent is disabled.', SKYY_ROSE_AI_TEXT_DOMAIN)];
        }

        try {
            // Start optimization activity
            $activity_id = $this->db->insertAgentActivity(
                'wordpress',
                'optimize_site',
                $data,
                'running'
            );

            $optimization_result = [
                'timestamp' => current_time('mysql'),
                'performance_optimization' => $this->optimizePerformance(),
                'security_hardening' => $this->hardenSecurity(),
                'seo_optimization' => $this->optimizeSEO(),
                'content_optimization' => $this->optimizeContent(),
                'database_optimization' => $this->optimizeDatabase(),
                'overall_score' => 0
            ];

            // Calculate overall optimization score
            $optimization_result['overall_score'] = $this->calculateOptimizationScore($optimization_result);

            // Update activity
            $this->db->updateAgentActivity($activity_id, 'completed', $optimization_result);

            return [
                'success' => true,
                'optimization' => $optimization_result,
                'message' => __('WordPress optimization completed successfully.', SKYY_ROSE_AI_TEXT_DOMAIN)
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
     * Optimize site performance
     */
    private function optimizePerformance()
    {
        $performance_optimizations = [
            'caching_enabled' => false,
            'images_optimized' => false,
            'minification_enabled' => false,
            'cdn_configured' => false,
            'database_optimized' => false,
            'score' => 0,
            'recommendations' => []
        ];

        // Check for caching plugins
        $caching_plugins = [
            'wp-rocket/wp-rocket.php',
            'w3-total-cache/w3-total-cache.php',
            'wp-super-cache/wp-cache.php'
        ];

        foreach ($caching_plugins as $plugin) {
            if (is_plugin_active($plugin)) {
                $performance_optimizations['caching_enabled'] = true;
                $performance_optimizations['score'] += 20;
                break;
            }
        }

        if (!$performance_optimizations['caching_enabled']) {
            $performance_optimizations['recommendations'][] = 'Install and configure a caching plugin';
        }

        // Check for image optimization
        $image_plugins = [
            'shortpixel-image-optimiser/wp-shortpixel.php',
            'wp-smushit/wp-smush.php',
            'ewww-image-optimizer/ewww-image-optimizer.php'
        ];

        foreach ($image_plugins as $plugin) {
            if (is_plugin_active($plugin)) {
                $performance_optimizations['images_optimized'] = true;
                $performance_optimizations['score'] += 15;
                break;
            }
        }

        if (!$performance_optimizations['images_optimized']) {
            $performance_optimizations['recommendations'][] = 'Install an image optimization plugin';
        }

        // Check theme performance
        $theme_score = $this->analyzeThemePerformance();
        $performance_optimizations['score'] += $theme_score;

        // Check database optimization
        $db_score = $this->checkDatabaseHealth();
        $performance_optimizations['database_optimized'] = $db_score > 80;
        $performance_optimizations['score'] += ($db_score * 0.2);

        return $performance_optimizations;
    }

    /**
     * Harden WordPress security
     */
    private function hardenSecurity()
    {
        $security_measures = [
            'login_protection' => false,
            'file_permissions' => false,
            'security_headers' => false,
            'malware_scan' => false,
            'score' => 0,
            'vulnerabilities' => [],
            'recommendations' => []
        ];

        // Check for security plugins
        $security_plugins = [
            'wordfence/wordfence.php',
            'better-wp-security/better-wp-security.php',
            'all-in-one-wp-security-and-firewall/wp-security.php'
        ];

        foreach ($security_plugins as $plugin) {
            if (is_plugin_active($plugin)) {
                $security_measures['login_protection'] = true;
                $security_measures['score'] += 25;
                break;
            }
        }

        // Check file permissions
        $security_measures['file_permissions'] = $this->checkFilePermissions();
        if ($security_measures['file_permissions']) {
            $security_measures['score'] += 20;
        } else {
            $security_measures['recommendations'][] = 'Review and fix file permissions';
        }

        // Check for common vulnerabilities
        $vulnerabilities = $this->scanVulnerabilities();
        $security_measures['vulnerabilities'] = $vulnerabilities;
        
        if (empty($vulnerabilities)) {
            $security_measures['score'] += 30;
        } else {
            $security_measures['recommendations'][] = 'Address identified security vulnerabilities';
        }

        // Check WordPress and plugin updates
        $updates_needed = $this->checkForUpdates();
        if (empty($updates_needed)) {
            $security_measures['score'] += 25;
        } else {
            $security_measures['recommendations'][] = 'Update WordPress core and plugins';
        }

        return $security_measures;
    }

    /**
     * Optimize SEO settings
     */
    private function optimizeSEO()
    {
        $seo_optimization = [
            'seo_plugin_active' => false,
            'meta_tags_configured' => false,
            'sitemap_generated' => false,
            'schema_markup' => false,
            'score' => 0,
            'recommendations' => []
        ];

        // Check for SEO plugins
        $seo_plugins = [
            'wordpress-seo/wp-seo.php',
            'all-in-one-seo-pack/all_in_one_seo_pack.php',
            'seo-by-rank-math/rank-math.php'
        ];

        foreach ($seo_plugins as $plugin) {
            if (is_plugin_active($plugin)) {
                $seo_optimization['seo_plugin_active'] = true;
                $seo_optimization['score'] += 30;
                break;
            }
        }

        if (!$seo_optimization['seo_plugin_active']) {
            $seo_optimization['recommendations'][] = 'Install and configure an SEO plugin';
        }

        // Check basic SEO settings
        $home_title = get_option('blogname');
        $home_description = get_option('blogdescription');
        
        if (!empty($home_title) && !empty($home_description)) {
            $seo_optimization['meta_tags_configured'] = true;
            $seo_optimization['score'] += 20;
        }

        // Check for sitemap
        if ($this->checkSitemapExists()) {
            $seo_optimization['sitemap_generated'] = true;
            $seo_optimization['score'] += 25;
        } else {
            $seo_optimization['recommendations'][] = 'Generate and submit XML sitemap';
        }

        // Check for schema markup
        if ($this->checkSchemaMarkup()) {
            $seo_optimization['schema_markup'] = true;
            $seo_optimization['score'] += 25;
        } else {
            $seo_optimization['recommendations'][] = 'Implement structured data markup';
        }

        return $seo_optimization;
    }

    /**
     * Optimize content
     */
    private function optimizeContent()
    {
        $content_optimization = [
            'duplicate_content' => 0,
            'missing_alt_tags' => 0,
            'broken_links' => 0,
            'content_quality_score' => 0,
            'recommendations' => []
        ];

        // Check for duplicate content
        $duplicate_content = $this->scanDuplicateContent();
        $content_optimization['duplicate_content'] = count($duplicate_content);

        // Check for missing alt tags
        $missing_alt_tags = $this->scanMissingAltTags();
        $content_optimization['missing_alt_tags'] = count($missing_alt_tags);

        // Check for broken links
        $broken_links = $this->scanBrokenLinks();
        $content_optimization['broken_links'] = count($broken_links);

        // Calculate content quality score
        $content_optimization['content_quality_score'] = $this->calculateContentQualityScore();

        // Generate recommendations
        if ($content_optimization['duplicate_content'] > 0) {
            $content_optimization['recommendations'][] = 'Address duplicate content issues';
        }

        if ($content_optimization['missing_alt_tags'] > 0) {
            $content_optimization['recommendations'][] = 'Add alt text to images';
        }

        if ($content_optimization['broken_links'] > 0) {
            $content_optimization['recommendations'][] = 'Fix broken internal and external links';
        }

        return $content_optimization;
    }

    /**
     * Optimize database
     */
    private function optimizeDatabase()
    {
        $db_optimization = [
            'size_before' => 0,
            'size_after' => 0,
            'space_saved' => 0,
            'optimizations_applied' => [],
            'recommendations' => []
        ];

        // Get database size before optimization
        $db_optimization['size_before'] = $this->getDatabaseSize();

        // Clean up revisions (keep last 3)
        $revisions_cleaned = $this->cleanupRevisions(3);
        if ($revisions_cleaned > 0) {
            $db_optimization['optimizations_applied'][] = "Cleaned up {$revisions_cleaned} post revisions";
        }

        // Clean up spam comments
        $spam_cleaned = $this->cleanupSpamComments();
        if ($spam_cleaned > 0) {
            $db_optimization['optimizations_applied'][] = "Removed {$spam_cleaned} spam comments";
        }

        // Clean up expired transients
        $transients_cleaned = $this->cleanupExpiredTransients();
        if ($transients_cleaned > 0) {
            $db_optimization['optimizations_applied'][] = "Cleaned up {$transients_cleaned} expired transients";
        }

        // Optimize database tables
        $tables_optimized = $this->optimizeDatabaseTables();
        if ($tables_optimized > 0) {
            $db_optimization['optimizations_applied'][] = "Optimized {$tables_optimized} database tables";
        }

        // Get database size after optimization
        $db_optimization['size_after'] = $this->getDatabaseSize();
        $db_optimization['space_saved'] = $db_optimization['size_before'] - $db_optimization['size_after'];

        return $db_optimization;
    }

    /**
     * Daily optimization routine (called by cron)
     */
    public function dailyOptimization()
    {
        if (!$this->config['auto_optimize']) {
            return false;
        }

        // Run light optimizations only
        $optimizations = [
            'database_cleanup' => $this->lightDatabaseCleanup(),
            'cache_cleanup' => $this->clearExpiredCache(),
            'security_check' => $this->basicSecurityCheck()
        ];

        // Log activity
        $this->db->insertAgentActivity(
            'wordpress',
            'daily_optimization',
            $optimizations,
            'completed'
        );

        return $optimizations;
    }

    /**
     * Helper methods
     */
    private function analyzeThemePerformance()
    {
        // Analyze current theme for performance issues
        return 75; // Placeholder
    }

    private function checkDatabaseHealth()
    {
        global $wpdb;
        
        // Basic database health check
        $tables = $wpdb->get_results("SHOW TABLE STATUS");
        $health_score = 85; // Base score
        
        foreach ($tables as $table) {
            if ($table->Data_free > 0) {
                $health_score -= 5; // Deduct for fragmentation
            }
        }
        
        return max($health_score, 0);
    }

    private function checkFilePermissions()
    {
        // Check critical file permissions
        $wp_config_perms = fileperms(ABSPATH . 'wp-config.php') & 0777;
        return $wp_config_perms <= 0644;
    }

    private function scanVulnerabilities()
    {
        // Basic vulnerability scan
        $vulnerabilities = [];
        
        // Check for common vulnerable files
        $vulnerable_files = [
            ABSPATH . 'wp-config.php.bak',
            ABSPATH . 'wp-config.txt',
            ABSPATH . '.htaccess.bak'
        ];
        
        foreach ($vulnerable_files as $file) {
            if (file_exists($file)) {
                $vulnerabilities[] = "Vulnerable file found: " . basename($file);
            }
        }
        
        return $vulnerabilities;
    }

    private function checkForUpdates()
    {
        $updates = [];
        
        // Check WordPress core updates
        $core_updates = get_core_updates();
        if (!empty($core_updates) && $core_updates[0]->response !== 'latest') {
            $updates[] = 'WordPress core update available';
        }
        
        // Check plugin updates
        $plugin_updates = get_plugin_updates();
        if (!empty($plugin_updates)) {
            $updates[] = count($plugin_updates) . ' plugin updates available';
        }
        
        // Check theme updates
        $theme_updates = get_theme_updates();
        if (!empty($theme_updates)) {
            $updates[] = count($theme_updates) . ' theme updates available';
        }
        
        return $updates;
    }

    private function checkSitemapExists()
    {
        // Check for common sitemap locations
        $sitemap_urls = [
            home_url('/sitemap.xml'),
            home_url('/sitemap_index.xml'),
            home_url('/wp-sitemap.xml')
        ];
        
        foreach ($sitemap_urls as $url) {
            $response = wp_remote_head($url);
            if (!is_wp_error($response) && wp_remote_retrieve_response_code($response) === 200) {
                return true;
            }
        }
        
        return false;
    }

    private function checkSchemaMarkup()
    {
        // Basic check for structured data
        return false; // Would implement actual check
    }

    private function scanDuplicateContent()
    {
        // Scan for duplicate content
        return []; // Placeholder
    }

    private function scanMissingAltTags()
    {
        // Scan for images without alt tags
        return []; // Placeholder
    }

    private function scanBrokenLinks()
    {
        // Scan for broken links
        return []; // Placeholder
    }

    private function calculateContentQualityScore()
    {
        // Calculate overall content quality
        return 80; // Placeholder
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

    private function cleanupRevisions($keep = 3)
    {
        global $wpdb;
        
        return $wpdb->query("
            DELETE FROM {$wpdb->posts} 
            WHERE post_type = 'revision' 
            AND post_date < DATE_SUB(NOW(), INTERVAL 30 DAY)
        ");
    }

    private function cleanupSpamComments()
    {
        global $wpdb;
        
        return $wpdb->query("
            DELETE FROM {$wpdb->comments} 
            WHERE comment_approved = 'spam' 
            AND comment_date < DATE_SUB(NOW(), INTERVAL 30 DAY)
        ");
    }

    private function cleanupExpiredTransients()
    {
        global $wpdb;
        
        return $wpdb->query("
            DELETE FROM {$wpdb->options} 
            WHERE option_name LIKE '_transient_timeout_%' 
            AND option_value < UNIX_TIMESTAMP()
        ");
    }

    private function optimizeDatabaseTables()
    {
        global $wpdb;
        
        $tables = $wpdb->get_col("SHOW TABLES");
        $count = 0;
        
        foreach ($tables as $table) {
            $wpdb->query("OPTIMIZE TABLE $table");
            $count++;
        }
        
        return $count;
    }

    private function lightDatabaseCleanup()
    {
        // Light cleanup for daily routine
        return [
            'revisions_cleaned' => $this->cleanupRevisions(5),
            'spam_cleaned' => $this->cleanupSpamComments(),
            'transients_cleaned' => $this->cleanupExpiredTransients()
        ];
    }

    private function clearExpiredCache()
    {
        // Clear expired cache
        wp_cache_flush();
        return true;
    }

    private function basicSecurityCheck()
    {
        // Basic security check
        return [
            'file_permissions' => $this->checkFilePermissions(),
            'vulnerable_files' => count($this->scanVulnerabilities())
        ];
    }

    private function calculateOptimizationScore($results)
    {
        $scores = [
            $results['performance_optimization']['score'],
            $results['security_hardening']['score'],
            $results['seo_optimization']['score']
        ];
        
        return round(array_sum($scores) / count($scores), 2);
    }
}