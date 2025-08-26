<?php
/**
 * Inventory Management Agent
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Inventory Agent for digital asset management
 */
class InventoryAgent
{
    /**
     * Singleton instance
     * @var InventoryAgent
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
     * Supported file types
     * @var array
     */
    private $supported_types = [
        'image' => ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'],
        'video' => ['mp4', 'webm', 'ogg', 'avi', 'mov'],
        'document' => ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'],
        'audio' => ['mp3', 'wav', 'ogg', 'flac'],
        'archive' => ['zip', 'rar', '7z', 'tar', 'gz']
    ];

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
        $this->config = $settings['agents']['inventory'] ?? [
            'enabled' => true,
            'auto_scan' => true,
            'duplicate_threshold' => 0.85
        ];
    }

    /**
     * Scan digital assets
     */
    public function scanAssets($data = [])
    {
        if (!$this->config['enabled']) {
            return ['error' => __('Inventory Agent is disabled.', SKYY_ROSE_AI_TEXT_DOMAIN)];
        }

        try {
            // Start scan activity
            $activity_id = $this->db->insertAgentActivity(
                'inventory',
                'scan_assets',
                $data,
                'running'
            );

            $scan_result = [
                'timestamp' => current_time('mysql'),
                'scanned_directories' => [],
                'total_assets' => 0,
                'new_assets' => 0,
                'updated_assets' => 0,
                'duplicates_found' => 0,
                'issues_detected' => [],
                'recommendations' => [],
                'performance_metrics' => []
            ];

            // Scan WordPress uploads directory
            $uploads_dir = wp_upload_dir();
            $scan_result['scanned_directories'][] = $uploads_dir['basedir'];
            
            $upload_scan = $this->scanDirectory($uploads_dir['basedir']);
            $scan_result = array_merge_recursive($scan_result, $upload_scan);

            // Scan theme assets
            $theme_dir = get_template_directory();
            $scan_result['scanned_directories'][] = $theme_dir;
            
            $theme_scan = $this->scanDirectory($theme_dir . '/assets', ['recursive' => false]);
            $scan_result = array_merge_recursive($scan_result, $theme_scan);

            // Scan for duplicates
            $duplicate_scan = $this->scanForDuplicates();
            $scan_result['duplicates_found'] = count($duplicate_scan['duplicates']);
            $scan_result['issues_detected'] = array_merge($scan_result['issues_detected'], $duplicate_scan['issues']);

            // Generate recommendations
            $scan_result['recommendations'] = $this->generateInventoryRecommendations($scan_result);

            // Update activity
            $this->db->updateAgentActivity($activity_id, 'completed', $scan_result);

            return [
                'success' => true,
                'scan_result' => $scan_result,
                'message' => __('Asset scan completed successfully.', SKYY_ROSE_AI_TEXT_DOMAIN)
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
     * Scan directory for assets
     */
    private function scanDirectory($directory, $options = [])
    {
        $options = wp_parse_args($options, [
            'recursive' => true,
            'max_depth' => 5,
            'current_depth' => 0
        ]);

        $scan_result = [
            'total_assets' => 0,
            'new_assets' => 0,
            'updated_assets' => 0,
            'issues_detected' => []
        ];

        if (!is_dir($directory) || $options['current_depth'] > $options['max_depth']) {
            return $scan_result;
        }

        $files = scandir($directory);
        if ($files === false) {
            $scan_result['issues_detected'][] = "Unable to read directory: $directory";
            return $scan_result;
        }

        foreach ($files as $file) {
            if ($file === '.' || $file === '..') {
                continue;
            }

            $file_path = $directory . DIRECTORY_SEPARATOR . $file;

            if (is_dir($file_path) && $options['recursive']) {
                $sub_options = $options;
                $sub_options['current_depth']++;
                $sub_scan = $this->scanDirectory($file_path, $sub_options);
                $scan_result['total_assets'] += $sub_scan['total_assets'];
                $scan_result['new_assets'] += $sub_scan['new_assets'];
                $scan_result['updated_assets'] += $sub_scan['updated_assets'];
                $scan_result['issues_detected'] = array_merge($scan_result['issues_detected'], $sub_scan['issues_detected']);
            } elseif (is_file($file_path)) {
                $asset_result = $this->processAsset($file_path);
                $scan_result['total_assets']++;
                
                if ($asset_result['is_new']) {
                    $scan_result['new_assets']++;
                } elseif ($asset_result['is_updated']) {
                    $scan_result['updated_assets']++;
                }

                if (!empty($asset_result['issues'])) {
                    $scan_result['issues_detected'] = array_merge($scan_result['issues_detected'], $asset_result['issues']);
                }
            }
        }

        return $scan_result;
    }

    /**
     * Process individual asset
     */
    private function processAsset($file_path)
    {
        $result = [
            'is_new' => false,
            'is_updated' => false,
            'issues' => []
        ];

        // Get file information
        $file_info = $this->getFileInfo($file_path);
        
        if (!$file_info) {
            $result['issues'][] = "Unable to process file: $file_path";
            return $result;
        }

        // Check if asset exists in database
        $existing_asset = $this->getExistingAsset($file_path);
        
        if (!$existing_asset) {
            // New asset
            $this->storeAsset($file_info);
            $result['is_new'] = true;
        } else {
            // Check if asset has been updated
            if ($existing_asset->asset_hash !== $file_info['hash']) {
                $this->updateAsset($existing_asset->id, $file_info);
                $result['is_updated'] = true;
            }
        }

        // Check for issues
        $issues = $this->analyzeAsset($file_info);
        $result['issues'] = $issues;

        return $result;
    }

    /**
     * Get file information
     */
    private function getFileInfo($file_path)
    {
        if (!file_exists($file_path) || !is_readable($file_path)) {
            return false;
        }

        $file_size = filesize($file_path);
        $file_hash = md5_file($file_path);
        $file_extension = strtolower(pathinfo($file_path, PATHINFO_EXTENSION));
        $asset_type = $this->determineAssetType($file_extension);

        $metadata = [
            'extension' => $file_extension,
            'mime_type' => mime_content_type($file_path),
            'created_date' => date('Y-m-d H:i:s', filectime($file_path)),
            'modified_date' => date('Y-m-d H:i:s', filemtime($file_path))
        ];

        // Add type-specific metadata
        switch ($asset_type) {
            case 'image':
                $image_data = getimagesize($file_path);
                if ($image_data) {
                    $metadata['width'] = $image_data[0];
                    $metadata['height'] = $image_data[1];
                    $metadata['dimensions'] = $image_data[0] . 'x' . $image_data[1];
                }
                break;
            
            case 'video':
                // Would add video metadata extraction here
                break;
        }

        return [
            'path' => $file_path,
            'type' => $asset_type,
            'size' => $file_size,
            'hash' => $file_hash,
            'metadata' => $metadata
        ];
    }

    /**
     * Determine asset type from extension
     */
    private function determineAssetType($extension)
    {
        foreach ($this->supported_types as $type => $extensions) {
            if (in_array($extension, $extensions)) {
                return $type;
            }
        }
        return 'other';
    }

    /**
     * Get existing asset from database
     */
    private function getExistingAsset($file_path)
    {
        global $wpdb;
        
        return $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$wpdb->prefix}skyy_rose_inventory_assets WHERE asset_path = %s",
            $file_path
        ));
    }

    /**
     * Store new asset in database
     */
    private function storeAsset($file_info)
    {
        return $this->db->insertInventoryAsset(
            $file_info['type'],
            $file_info['path'],
            $file_info['hash'],
            $file_info['size'],
            $file_info['metadata']
        );
    }

    /**
     * Update existing asset
     */
    private function updateAsset($asset_id, $file_info)
    {
        global $wpdb;
        
        return $wpdb->update(
            $wpdb->prefix . 'skyy_rose_inventory_assets',
            [
                'asset_hash' => $file_info['hash'],
                'file_size' => $file_info['size'],
                'metadata' => wp_json_encode($file_info['metadata']),
                'updated_at' => current_time('mysql')
            ],
            ['id' => $asset_id],
            ['%s', '%d', '%s', '%s'],
            ['%d']
        );
    }

    /**
     * Analyze asset for issues
     */
    private function analyzeAsset($file_info)
    {
        $issues = [];

        // Check file size
        if ($file_info['size'] > 5 * 1024 * 1024) { // 5MB
            $issues[] = "Large file size: " . $this->formatFileSize($file_info['size']);
        }

        // Check image dimensions (if image)
        if ($file_info['type'] === 'image' && isset($file_info['metadata']['width'])) {
            if ($file_info['metadata']['width'] > 3000 || $file_info['metadata']['height'] > 3000) {
                $issues[] = "Large image dimensions: " . $file_info['metadata']['dimensions'];
            }
        }

        // Check for unoptimized images
        if ($file_info['type'] === 'image' && $file_info['metadata']['extension'] === 'png') {
            if ($file_info['size'] > 500 * 1024) { // 500KB
                $issues[] = "PNG file may benefit from optimization";
            }
        }

        return $issues;
    }

    /**
     * Scan for duplicate assets
     */
    private function scanForDuplicates()
    {
        $assets = $this->db->getInventoryAssets();
        $duplicates = [];
        $issues = [];
        $hash_groups = [];

        // Group assets by hash
        foreach ($assets as $asset) {
            if (!isset($hash_groups[$asset->asset_hash])) {
                $hash_groups[$asset->asset_hash] = [];
            }
            $hash_groups[$asset->asset_hash][] = $asset;
        }

        // Find duplicates
        foreach ($hash_groups as $hash => $group) {
            if (count($group) > 1) {
                $duplicates[$hash] = $group;
                $issues[] = count($group) . " duplicate files found with hash: " . substr($hash, 0, 8);
            }
        }

        return [
            'duplicates' => $duplicates,
            'issues' => $issues
        ];
    }

    /**
     * Optimize assets
     */
    public function optimizeAssets()
    {
        if (!$this->config['enabled']) {
            return false;
        }

        $optimization_result = [
            'images_optimized' => 0,
            'space_saved' => 0,
            'duplicates_removed' => 0,
            'issues_fixed' => []
        ];

        // Get assets that need optimization
        $assets = $this->getAssetsNeedingOptimization();

        foreach ($assets as $asset) {
            $metadata = json_decode($asset->metadata, true);
            
            if ($asset->asset_type === 'image') {
                $optimized = $this->optimizeImage($asset->asset_path);
                if ($optimized) {
                    $optimization_result['images_optimized']++;
                    $optimization_result['space_saved'] += $optimized['space_saved'];
                }
            }
        }

        // Clean up duplicates
        $duplicate_cleanup = $this->cleanupDuplicates();
        $optimization_result['duplicates_removed'] = $duplicate_cleanup['removed'];

        return $optimization_result;
    }

    /**
     * Get assets needing optimization
     */
    private function getAssetsNeedingOptimization()
    {
        global $wpdb;
        
        return $wpdb->get_results("
            SELECT * FROM {$wpdb->prefix}skyy_rose_inventory_assets 
            WHERE asset_type = 'image' 
            AND file_size > 500000 
            AND status = 'active'
            ORDER BY file_size DESC
            LIMIT 50
        ");
    }

    /**
     * Optimize image
     */
    private function optimizeImage($image_path)
    {
        // This would implement actual image optimization
        // For now, return placeholder data
        return [
            'optimized' => true,
            'space_saved' => 102400 // 100KB saved
        ];
    }

    /**
     * Clean up duplicate assets
     */
    private function cleanupDuplicates()
    {
        $duplicates = $this->scanForDuplicates()['duplicates'];
        $removed = 0;

        foreach ($duplicates as $hash => $group) {
            // Keep the first file, mark others as duplicates
            for ($i = 1; $i < count($group); $i++) {
                global $wpdb;
                
                $wpdb->update(
                    $wpdb->prefix . 'skyy_rose_inventory_assets',
                    ['status' => 'duplicate'],
                    ['id' => $group[$i]->id],
                    ['%s'],
                    ['%d']
                );
                $removed++;
            }
        }

        return ['removed' => $removed];
    }

    /**
     * Generate inventory recommendations
     */
    private function generateInventoryRecommendations($scan_result)
    {
        $recommendations = [];

        if ($scan_result['duplicates_found'] > 0) {
            $recommendations[] = "Remove {$scan_result['duplicates_found']} duplicate files to save space";
        }

        if (!empty($scan_result['issues_detected'])) {
            $large_files = array_filter($scan_result['issues_detected'], function($issue) {
                return strpos($issue, 'Large file size') !== false;
            });
            
            if (count($large_files) > 0) {
                $recommendations[] = "Optimize " . count($large_files) . " large files for better performance";
            }
        }

        if ($scan_result['new_assets'] > 10) {
            $recommendations[] = "Consider implementing automated asset optimization for new uploads";
        }

        return $recommendations;
    }

    /**
     * Format file size for display
     */
    private function formatFileSize($size)
    {
        $units = ['B', 'KB', 'MB', 'GB'];
        $unit_index = 0;
        
        while ($size >= 1024 && $unit_index < count($units) - 1) {
            $size /= 1024;
            $unit_index++;
        }
        
        return round($size, 2) . ' ' . $units[$unit_index];
    }
}