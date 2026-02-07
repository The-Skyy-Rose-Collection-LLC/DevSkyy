<?php
/**
 * AI Image Enhancement Pipeline
 * Integrates luxury image processing with WordPress media library
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

if (!defined('ABSPATH')) exit;

/**
 * AI Image Enhancement Manager
 */
class SkyyRose_AI_Image_Enhancement {

    /**
     * FastAPI backend URL
     */
    private $api_base_url;

    /**
     * Enhancement settings
     */
    private $settings;

    /**
     * Constructor
     */
    public function __construct() {
        $this->api_base_url = defined('SKYYROSE_API_URL') ? SKYYROSE_API_URL : 'http://localhost:8000';
        $this->settings = get_option('skyyrose_ai_enhancement_settings', $this->default_settings());

        // Hooks
        add_filter('wp_handle_upload', array($this, 'process_uploaded_image'), 10, 2);
        add_action('add_attachment', array($this, 'generate_enhanced_metadata'), 10, 1);
        add_filter('wp_generate_attachment_metadata', array($this, 'add_custom_metadata'), 10, 2);

        // AJAX handlers
        add_action('wp_ajax_skyyrose_enhance_image', array($this, 'ajax_enhance_image'));
        add_action('wp_ajax_skyyrose_bulk_enhance', array($this, 'ajax_bulk_enhance'));
        add_action('wp_ajax_skyyrose_test_api', array($this, 'ajax_test_api'));

        // Admin menu
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_assets'));

        // Media library column
        add_filter('manage_media_columns', array($this, 'add_enhancement_column'));
        add_action('manage_media_custom_column', array($this, 'render_enhancement_column'), 10, 2);
    }

    /**
     * Default settings
     */
    private function default_settings() {
        return array(
            'enabled' => false,
            'auto_enhance' => false,
            'apply_luxury_filter' => true,
            'generate_blurhash' => true,
            'responsive_sizes' => true,
            'remove_background' => false,
            'upscale_images' => false,
            'api_key_replicate' => '',
            'api_key_fal' => '',
            'api_key_stability' => '',
            'api_key_together' => '',
            'api_key_runway' => '',
        );
    }

    /**
     * Process uploaded image
     */
    public function process_uploaded_image($upload, $context) {
        // Only process images
        if (strpos($upload['type'], 'image/') !== 0) {
            return $upload;
        }

        // Check if enhancement is enabled and auto-enhance is on
        if (!$this->settings['enabled'] || !$this->settings['auto_enhance']) {
            return $upload;
        }

        // Queue for enhancement
        $this->queue_enhancement($upload['file']);

        return $upload;
    }

    /**
     * Generate enhanced metadata on attachment creation
     */
    public function generate_enhanced_metadata($attachment_id) {
        // Only process images
        if (!wp_attachment_is_image($attachment_id)) {
            return;
        }

        // Check if enhancement is enabled
        if (!$this->settings['enabled'] || !$this->settings['auto_enhance']) {
            return;
        }

        // Process enhancement
        $this->enhance_attachment($attachment_id);
    }

    /**
     * Add custom metadata to attachment
     */
    public function add_custom_metadata($metadata, $attachment_id) {
        // Only process images
        if (!wp_attachment_is_image($attachment_id)) {
            return $metadata;
        }

        // Check if enhancement is enabled
        if (!$this->settings['enabled']) {
            return $metadata;
        }

        // Generate blurhash if enabled
        if ($this->settings['generate_blurhash']) {
            $blurhash = $this->generate_blurhash($attachment_id);
            if ($blurhash) {
                $metadata['blurhash'] = $blurhash;
                update_post_meta($attachment_id, '_skyyrose_blurhash', $blurhash);
            }
        }

        // Add enhancement status
        $metadata['enhancement_status'] = 'pending';
        update_post_meta($attachment_id, '_skyyrose_enhancement_status', 'pending');

        return $metadata;
    }

    /**
     * Enhance attachment
     */
    private function enhance_attachment($attachment_id) {
        $file_path = get_attached_file($attachment_id);

        if (!file_exists($file_path)) {
            return false;
        }

        // Prepare enhancement options
        $options = array(
            'apply_luxury_filter' => $this->settings['apply_luxury_filter'],
            'remove_background' => $this->settings['remove_background'],
            'upscale' => $this->settings['upscale_images'],
        );

        // Call FastAPI backend
        $result = $this->call_enhancement_api($file_path, $options);

        if (is_wp_error($result)) {
            update_post_meta($attachment_id, '_skyyrose_enhancement_status', 'failed');
            update_post_meta($attachment_id, '_skyyrose_enhancement_error', $result->get_error_message());
            return false;
        }

        // Save enhanced image
        if (isset($result['enhanced_path'])) {
            $this->replace_attachment_file($attachment_id, $result['enhanced_path']);
        }

        // Update metadata
        update_post_meta($attachment_id, '_skyyrose_enhancement_status', 'completed');
        update_post_meta($attachment_id, '_skyyrose_enhanced_at', current_time('mysql'));

        // Regenerate thumbnails
        if ($this->settings['responsive_sizes']) {
            require_once(ABSPATH . 'wp-admin/includes/image.php');
            $metadata = wp_generate_attachment_metadata($attachment_id, $file_path);
            wp_update_attachment_metadata($attachment_id, $metadata);
        }

        return true;
    }

    /**
     * Call FastAPI enhancement endpoint
     */
    private function call_enhancement_api($file_path, $options) {
        // Prepare multipart form data
        $boundary = wp_generate_password(24, false);

        $body = '';

        // Add file
        $body .= "--{$boundary}\r\n";
        $body .= 'Content-Disposition: form-data; name="file"; filename="' . basename($file_path) . "\"\r\n";
        $body .= 'Content-Type: ' . mime_content_type($file_path) . "\r\n\r\n";
        $body .= file_get_contents($file_path) . "\r\n";

        // Add options
        foreach ($options as $key => $value) {
            $body .= "--{$boundary}\r\n";
            $body .= "Content-Disposition: form-data; name=\"{$key}\"\r\n\r\n";
            $body .= $value ? 'true' : 'false';
            $body .= "\r\n";
        }

        $body .= "--{$boundary}--\r\n";

        // Make request
        $response = wp_remote_post($this->api_base_url . '/api/v1/ai/enhance-image', array(
            'headers' => array(
                'Content-Type' => 'multipart/form-data; boundary=' . $boundary,
            ),
            'body' => $body,
            'timeout' => 60, // 60 seconds for image processing
        ));

        if (is_wp_error($response)) {
            return $response;
        }

        $response_code = wp_remote_retrieve_response_code($response);

        if ($response_code !== 200) {
            return new WP_Error(
                'api_error',
                'Enhancement API returned error: ' . wp_remote_retrieve_response_message($response)
            );
        }

        $body = json_decode(wp_remote_retrieve_body($response), true);

        return $body;
    }

    /**
     * Generate blurhash placeholder
     */
    private function generate_blurhash($attachment_id) {
        $file_path = get_attached_file($attachment_id);

        if (!file_exists($file_path)) {
            return false;
        }

        // Call FastAPI blurhash endpoint
        $response = wp_remote_post($this->api_base_url . '/api/v1/ai/generate-blurhash', array(
            'headers' => array(
                'Content-Type' => 'application/json',
            ),
            'body' => json_encode(array(
                'image_url' => wp_get_attachment_url($attachment_id),
            )),
            'timeout' => 30,
        ));

        if (is_wp_error($response)) {
            return false;
        }

        $body = json_decode(wp_remote_retrieve_body($response), true);

        return isset($body['blurhash']) ? $body['blurhash'] : false;
    }

    /**
     * Replace attachment file
     */
    private function replace_attachment_file($attachment_id, $new_file_path) {
        if (!file_exists($new_file_path)) {
            return false;
        }

        $old_file_path = get_attached_file($attachment_id);

        // Backup old file
        $backup_path = $old_file_path . '.backup';
        copy($old_file_path, $backup_path);

        // Replace file
        copy($new_file_path, $old_file_path);

        return true;
    }

    /**
     * Queue enhancement for background processing
     */
    private function queue_enhancement($file_path) {
        // Add to queue (could use WP Cron or custom queue)
        $queue = get_option('skyyrose_enhancement_queue', array());
        $queue[] = array(
            'file_path' => $file_path,
            'queued_at' => current_time('mysql'),
        );
        update_option('skyyrose_enhancement_queue', $queue);
    }

    /**
     * AJAX: Enhance single image
     */
    public function ajax_enhance_image() {
        check_ajax_referer('skyyrose_enhance_nonce', 'nonce');

        if (!current_user_can('upload_files')) {
            wp_send_json_error('Insufficient permissions');
        }

        $attachment_id = absint($_POST['attachment_id'] ?? 0);

        if (!$attachment_id) {
            wp_send_json_error('Invalid attachment ID');
        }

        $result = $this->enhance_attachment($attachment_id);

        if ($result) {
            wp_send_json_success('Image enhanced successfully');
        } else {
            wp_send_json_error('Enhancement failed');
        }
    }

    /**
     * AJAX: Bulk enhance images
     */
    public function ajax_bulk_enhance() {
        check_ajax_referer('skyyrose_enhance_nonce', 'nonce');

        if (!current_user_can('upload_files')) {
            wp_send_json_error('Insufficient permissions');
        }

        $attachment_ids = isset($_POST['attachment_ids']) ? array_map('absint', $_POST['attachment_ids']) : array();

        if (empty($attachment_ids)) {
            wp_send_json_error('No attachments selected');
        }

        $results = array(
            'success' => 0,
            'failed' => 0,
        );

        foreach ($attachment_ids as $attachment_id) {
            if ($this->enhance_attachment($attachment_id)) {
                $results['success']++;
            } else {
                $results['failed']++;
            }
        }

        wp_send_json_success($results);
    }

    /**
     * AJAX: Test API connection
     */
    public function ajax_test_api() {
        check_ajax_referer('skyyrose_enhance_nonce', 'nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error('Insufficient permissions');
        }

        $response = wp_remote_get($this->api_base_url . '/health');

        if (is_wp_error($response)) {
            wp_send_json_error('API connection failed: ' . $response->get_error_message());
        }

        $response_code = wp_remote_retrieve_response_code($response);

        if ($response_code === 200) {
            wp_send_json_success('API connection successful');
        } else {
            wp_send_json_error('API returned error code: ' . $response_code);
        }
    }

    /**
     * Add admin menu
     */
    public function add_admin_menu() {
        add_media_page(
            __('AI Enhancement', 'skyyrose-2025'),
            __('AI Enhancement', 'skyyrose-2025'),
            'manage_options',
            'skyyrose-ai-enhancement',
            array($this, 'render_admin_page')
        );
    }

    /**
     * Render admin settings page
     */
    public function render_admin_page() {
        // Save settings
        if (isset($_POST['skyyrose_save_settings'])) {
            check_admin_referer('skyyrose_ai_settings');

            $this->settings = array(
                'enabled' => isset($_POST['enabled']),
                'auto_enhance' => isset($_POST['auto_enhance']),
                'apply_luxury_filter' => isset($_POST['apply_luxury_filter']),
                'generate_blurhash' => isset($_POST['generate_blurhash']),
                'responsive_sizes' => isset($_POST['responsive_sizes']),
                'remove_background' => isset($_POST['remove_background']),
                'upscale_images' => isset($_POST['upscale_images']),
                'api_key_replicate' => sanitize_text_field($_POST['api_key_replicate'] ?? ''),
                'api_key_fal' => sanitize_text_field($_POST['api_key_fal'] ?? ''),
                'api_key_stability' => sanitize_text_field($_POST['api_key_stability'] ?? ''),
                'api_key_together' => sanitize_text_field($_POST['api_key_together'] ?? ''),
                'api_key_runway' => sanitize_text_field($_POST['api_key_runway'] ?? ''),
            );

            update_option('skyyrose_ai_enhancement_settings', $this->settings);

            echo '<div class="notice notice-success"><p>Settings saved successfully!</p></div>';
        }

        require_once SKYYROSE_THEME_DIR . '/admin/ai-enhancement-settings.php';
    }

    /**
     * Enqueue admin assets
     */
    public function enqueue_admin_assets($hook) {
        if ($hook !== 'media_page_skyyrose-ai-enhancement' && $hook !== 'upload.php') {
            return;
        }

        wp_enqueue_style(
            'skyyrose-ai-enhancement-admin',
            SKYYROSE_THEME_URL . '/assets/css/admin-ai-enhancement.css',
            array(),
            SKYYROSE_VERSION
        );

        wp_enqueue_script(
            'skyyrose-ai-enhancement-admin',
            SKYYROSE_THEME_URL . '/assets/js/admin-ai-enhancement.js',
            array('jquery'),
            SKYYROSE_VERSION,
            true
        );

        wp_localize_script('skyyrose-ai-enhancement-admin', 'skyyrose_ai', array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('skyyrose_enhance_nonce'),
        ));
    }

    /**
     * Add enhancement status column to media library
     */
    public function add_enhancement_column($columns) {
        $columns['ai_enhancement'] = __('AI Enhancement', 'skyyrose-2025');
        return $columns;
    }

    /**
     * Render enhancement status column
     */
    public function render_enhancement_column($column_name, $attachment_id) {
        if ($column_name !== 'ai_enhancement') {
            return;
        }

        if (!wp_attachment_is_image($attachment_id)) {
            echo '—';
            return;
        }

        $status = get_post_meta($attachment_id, '_skyyrose_enhancement_status', true);

        switch ($status) {
            case 'completed':
                echo '<span style="color: green;">✓ Enhanced</span>';
                break;
            case 'pending':
                echo '<span style="color: orange;">⏳ Pending</span>';
                break;
            case 'failed':
                echo '<span style="color: red;">✗ Failed</span>';
                break;
            default:
                echo '<button class="button button-small skyyrose-enhance-btn" data-attachment-id="' . $attachment_id . '">Enhance</button>';
                break;
        }
    }
}

// Initialize
new SkyyRose_AI_Image_Enhancement();
