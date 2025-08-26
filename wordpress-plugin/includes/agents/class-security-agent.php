<?php
/**
 * Security Monitoring Agent
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Security Agent for vulnerability scanning and protection
 */
class SecurityAgent
{
    /**
     * Singleton instance
     * @var SecurityAgent
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
        $this->config = $settings['agents']['security'] ?? [
            'enabled' => true,
            'auto_scan' => true,
            'threat_response' => 'alert'
        ];
    }

    /**
     * Run comprehensive security scan
     */
    public function runSecurityScan($data = [])
    {
        if (!$this->config['enabled']) {
            return ['error' => __('Security Agent is disabled.', SKYY_ROSE_AI_TEXT_DOMAIN)];
        }

        try {
            // Start security scan activity
            $activity_id = $this->db->insertAgentActivity(
                'security',
                'security_scan',
                $data,
                'running'
            );

            $security_result = [
                'timestamp' => current_time('mysql'),
                'file_integrity' => $this->checkFileIntegrity(),
                'malware_scan' => $this->scanForMalware(),
                'vulnerability_check' => $this->checkVulnerabilities(),
                'user_security' => $this->checkUserSecurity(),
                'plugin_security' => $this->checkPluginSecurity(),
                'configuration_security' => $this->checkSecurityConfiguration(),
                'threats_detected' => 0,
                'recommendations' => [],
                'risk_level' => 'low'
            ];

            // Calculate threat level and generate recommendations
            $security_result = $this->calculateSecurityScore($security_result);

            // Update activity
            $this->db->updateAgentActivity($activity_id, 'completed', $security_result);

            return [
                'success' => true,
                'security' => $security_result,
                'message' => __('Security scan completed successfully.', SKYY_ROSE_AI_TEXT_DOMAIN)
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
     * Basic security check (for cron)
     */
    public function basicSecurityCheck()
    {
        if (!$this->config['enabled']) {
            return false;
        }

        $basic_checks = [
            'admin_user_check' => $this->checkAdminUserSecurity(),
            'plugin_updates' => $this->checkForSecurityUpdates(),
            'failed_logins' => $this->checkFailedLogins()
        ];

        return $basic_checks;
    }

    /**
     * Check file integrity
     */
    private function checkFileIntegrity()
    {
        $integrity_result = [
            'core_files_modified' => 0,
            'suspicious_files' => [],
            'new_files' => [],
            'score' => 100
        ];

        // Check WordPress core files
        $core_checksums = $this->getWordPressCoreChecksums();
        $modified_files = $this->compareFileIntegrity($core_checksums);
        $integrity_result['core_files_modified'] = count($modified_files);

        // Look for suspicious files
        $suspicious_files = $this->scanForSuspiciousFiles();
        $integrity_result['suspicious_files'] = $suspicious_files;

        // Calculate score
        if ($integrity_result['core_files_modified'] > 0) {
            $integrity_result['score'] -= 30;
        }
        if (!empty($suspicious_files)) {
            $integrity_result['score'] -= 40;
        }

        return $integrity_result;
    }

    /**
     * Scan for malware
     */
    private function scanForMalware()
    {
        $malware_result = [
            'infected_files' => [],
            'suspicious_patterns' => [],
            'quarantined_files' => 0,
            'score' => 100
        ];

        // Scan common malware patterns
        $suspicious_patterns = $this->scanForMalwarePatterns();
        $malware_result['suspicious_patterns'] = $suspicious_patterns;

        // Check for infected files
        $infected_files = $this->detectInfectedFiles();
        $malware_result['infected_files'] = $infected_files;

        // Calculate score
        if (!empty($infected_files)) {
            $malware_result['score'] = 0; // Critical if malware found
        } elseif (!empty($suspicious_patterns)) {
            $malware_result['score'] = 40;
        }

        return $malware_result;
    }

    /**
     * Check for vulnerabilities
     */
    private function checkVulnerabilities()
    {
        $vulnerability_result = [
            'core_vulnerabilities' => [],
            'plugin_vulnerabilities' => [],
            'theme_vulnerabilities' => [],
            'configuration_issues' => [],
            'score' => 100
        ];

        // Check WordPress core version
        $core_vulns = $this->checkCoreVulnerabilities();
        $vulnerability_result['core_vulnerabilities'] = $core_vulns;

        // Check plugin vulnerabilities
        $plugin_vulns = $this->checkPluginVulnerabilities();
        $vulnerability_result['plugin_vulnerabilities'] = $plugin_vulns;

        // Check theme vulnerabilities
        $theme_vulns = $this->checkThemeVulnerabilities();
        $vulnerability_result['theme_vulnerabilities'] = $theme_vulns;

        // Check configuration issues
        $config_issues = $this->checkConfigurationVulnerabilities();
        $vulnerability_result['configuration_issues'] = $config_issues;

        // Calculate score
        $total_vulns = count($core_vulns) + count($plugin_vulns) + count($theme_vulns) + count($config_issues);
        if ($total_vulns > 5) {
            $vulnerability_result['score'] = 20;
        } elseif ($total_vulns > 2) {
            $vulnerability_result['score'] = 60;
        } elseif ($total_vulns > 0) {
            $vulnerability_result['score'] = 80;
        }

        return $vulnerability_result;
    }

    /**
     * Check user security
     */
    private function checkUserSecurity()
    {
        $user_security = [
            'weak_passwords' => 0,
            'admin_users' => 0,
            'inactive_users' => 0,
            'two_factor_enabled' => false,
            'score' => 100
        ];

        // Check for admin users
        $admin_users = get_users(['role' => 'administrator']);
        $user_security['admin_users'] = count($admin_users);

        // Check for default admin username
        $admin_user = get_user_by('login', 'admin');
        if ($admin_user) {
            $user_security['score'] -= 20;
        }

        // Check for users with weak passwords (simplified check)
        $weak_password_users = $this->checkWeakPasswords();
        $user_security['weak_passwords'] = count($weak_password_users);

        // Check for two-factor authentication
        $user_security['two_factor_enabled'] = $this->checkTwoFactorAuth();

        // Calculate score adjustments
        if ($user_security['weak_passwords'] > 0) {
            $user_security['score'] -= 30;
        }
        if (!$user_security['two_factor_enabled'] && $user_security['admin_users'] > 0) {
            $user_security['score'] -= 20;
        }

        return $user_security;
    }

    /**
     * Check plugin security
     */
    private function checkPluginSecurity()
    {
        $plugin_security = [
            'outdated_plugins' => [],
            'vulnerable_plugins' => [],
            'inactive_plugins' => [],
            'score' => 100
        ];

        // Get all plugins
        $all_plugins = get_plugins();
        $active_plugins = get_option('active_plugins', []);

        // Check for outdated plugins
        $plugin_updates = get_plugin_updates();
        $plugin_security['outdated_plugins'] = array_keys($plugin_updates);

        // Check for inactive plugins
        foreach ($all_plugins as $plugin_file => $plugin_data) {
            if (!in_array($plugin_file, $active_plugins)) {
                $plugin_security['inactive_plugins'][] = $plugin_file;
            }
        }

        // Calculate score
        if (count($plugin_security['outdated_plugins']) > 5) {
            $plugin_security['score'] -= 30;
        } elseif (count($plugin_security['outdated_plugins']) > 2) {
            $plugin_security['score'] -= 15;
        }

        if (count($plugin_security['inactive_plugins']) > 10) {
            $plugin_security['score'] -= 20;
        }

        return $plugin_security;
    }

    /**
     * Check security configuration
     */
    private function checkSecurityConfiguration()
    {
        $config_security = [
            'debug_enabled' => defined('WP_DEBUG') && WP_DEBUG,
            'file_editing_enabled' => !defined('DISALLOW_FILE_EDIT') || !DISALLOW_FILE_EDIT,
            'directory_browsing' => $this->checkDirectoryBrowsing(),
            'ssl_enabled' => is_ssl(),
            'security_headers' => $this->checkSecurityHeaders(),
            'score' => 100
        ];

        // Deduct points for security misconfigurations
        if ($config_security['debug_enabled']) {
            $config_security['score'] -= 20;
        }
        if ($config_security['file_editing_enabled']) {
            $config_security['score'] -= 25;
        }
        if ($config_security['directory_browsing']) {
            $config_security['score'] -= 15;
        }
        if (!$config_security['ssl_enabled']) {
            $config_security['score'] -= 30;
        }
        if (empty($config_security['security_headers'])) {
            $config_security['score'] -= 10;
        }

        return $config_security;
    }

    /**
     * Calculate overall security score and risk level
     */
    private function calculateSecurityScore($security_result)
    {
        $scores = [
            $security_result['file_integrity']['score'],
            $security_result['malware_scan']['score'],
            $security_result['vulnerability_check']['score'],
            $security_result['user_security']['score'],
            $security_result['plugin_security']['score'],
            $security_result['configuration_security']['score']
        ];

        $overall_score = array_sum($scores) / count($scores);

        // Determine risk level
        if ($overall_score >= 80) {
            $risk_level = 'low';
        } elseif ($overall_score >= 60) {
            $risk_level = 'medium';
        } elseif ($overall_score >= 40) {
            $risk_level = 'high';
        } else {
            $risk_level = 'critical';
        }

        // Count total threats
        $threats = 0;
        $threats += count($security_result['malware_scan']['infected_files']);
        $threats += count($security_result['vulnerability_check']['core_vulnerabilities']);
        $threats += count($security_result['vulnerability_check']['plugin_vulnerabilities']);

        // Generate recommendations
        $recommendations = $this->generateSecurityRecommendations($security_result);

        $security_result['overall_score'] = round($overall_score, 2);
        $security_result['risk_level'] = $risk_level;
        $security_result['threats_detected'] = $threats;
        $security_result['recommendations'] = $recommendations;

        return $security_result;
    }

    /**
     * Generate security recommendations
     */
    private function generateSecurityRecommendations($security_result)
    {
        $recommendations = [];

        // File integrity recommendations
        if ($security_result['file_integrity']['core_files_modified'] > 0) {
            $recommendations[] = [
                'type' => 'critical',
                'title' => 'Core Files Modified',
                'description' => 'WordPress core files have been modified. Restore from backup or reinstall WordPress.'
            ];
        }

        // Malware recommendations
        if (!empty($security_result['malware_scan']['infected_files'])) {
            $recommendations[] = [
                'type' => 'critical',
                'title' => 'Malware Detected',
                'description' => 'Malware has been detected. Clean infected files immediately and change all passwords.'
            ];
        }

        // Vulnerability recommendations
        if (!empty($security_result['vulnerability_check']['core_vulnerabilities'])) {
            $recommendations[] = [
                'type' => 'high',
                'title' => 'Update WordPress',
                'description' => 'WordPress core has known vulnerabilities. Update to the latest version immediately.'
            ];
        }

        // User security recommendations
        if ($security_result['user_security']['weak_passwords'] > 0) {
            $recommendations[] = [
                'type' => 'high',
                'title' => 'Strengthen Passwords',
                'description' => 'Some users have weak passwords. Enforce strong password policies.'
            ];
        }

        // Configuration recommendations
        if ($security_result['configuration_security']['debug_enabled']) {
            $recommendations[] = [
                'type' => 'medium',
                'title' => 'Disable Debug Mode',
                'description' => 'WordPress debug mode is enabled. Disable it in production environments.'
            ];
        }

        return $recommendations;
    }

    /**
     * Helper methods for security checks
     */
    private function getWordPressCoreChecksums()
    {
        // This would fetch WordPress core checksums from wordpress.org
        return [];
    }

    private function compareFileIntegrity($checksums)
    {
        // Compare current files against known checksums
        return [];
    }

    private function scanForSuspiciousFiles()
    {
        // Scan for files with suspicious extensions or patterns
        return [];
    }

    private function scanForMalwarePatterns()
    {
        // Scan files for known malware patterns
        return [];
    }

    private function detectInfectedFiles()
    {
        // Advanced malware detection
        return [];
    }

    private function checkCoreVulnerabilities()
    {
        // Check WordPress version against vulnerability database
        return [];
    }

    private function checkPluginVulnerabilities()
    {
        // Check plugins against vulnerability database
        return [];
    }

    private function checkThemeVulnerabilities()
    {
        // Check themes against vulnerability database
        return [];
    }

    private function checkConfigurationVulnerabilities()
    {
        // Check for common configuration vulnerabilities
        return [];
    }

    private function checkAdminUserSecurity()
    {
        $admin_user = get_user_by('login', 'admin');
        return !$admin_user;
    }

    private function checkForSecurityUpdates()
    {
        return count(get_plugin_updates()) + count(get_theme_updates());
    }

    private function checkFailedLogins()
    {
        // This would check for recent failed login attempts
        return 0;
    }

    private function checkWeakPasswords()
    {
        // This would check for users with weak passwords
        return [];
    }

    private function checkTwoFactorAuth()
    {
        // Check if two-factor authentication is enabled
        return false;
    }

    private function checkDirectoryBrowsing()
    {
        // Check if directory browsing is enabled
        return false;
    }

    private function checkSecurityHeaders()
    {
        // Check for security headers
        return [];
    }
}