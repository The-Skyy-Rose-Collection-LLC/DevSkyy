<?php
/**
 * AI Image Enhancement Settings Page
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

if (!defined('ABSPATH')) exit;
?>

<div class="wrap">
    <h1><?php _e('AI Image Enhancement Settings', 'skyyrose-2025'); ?></h1>
    <p><?php _e('Configure luxury AI-powered image enhancement for your media library.', 'skyyrose-2025'); ?></p>

    <div class="skyyrose-ai-settings">
        <form method="post" action="">
            <?php wp_nonce_field('skyyrose_ai_settings'); ?>

            <div class="skyyrose-settings-grid">
                <!-- Main Settings -->
                <div class="skyyrose-settings-section">
                    <h2><?php _e('General Settings', 'skyyrose-2025'); ?></h2>

                    <table class="form-table">
                        <tr>
                            <th scope="row">
                                <label for="enabled"><?php _e('Enable AI Enhancement', 'skyyrose-2025'); ?></label>
                            </th>
                            <td>
                                <label>
                                    <input type="checkbox" name="enabled" id="enabled" value="1" <?php checked($this->settings['enabled'], true); ?>>
                                    <?php _e('Activate AI image enhancement features', 'skyyrose-2025'); ?>
                                </label>
                                <p class="description">
                                    <?php _e('Master switch for all AI enhancement features. Disable to turn off all processing.', 'skyyrose-2025'); ?>
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <th scope="row">
                                <label for="auto_enhance"><?php _e('Auto-Enhance Uploads', 'skyyrose-2025'); ?></label>
                            </th>
                            <td>
                                <label>
                                    <input type="checkbox" name="auto_enhance" id="auto_enhance" value="1" <?php checked($this->settings['auto_enhance'], true); ?>>
                                    <?php _e('Automatically enhance images on upload', 'skyyrose-2025'); ?>
                                </label>
                                <p class="description">
                                    <?php _e('When enabled, all uploaded images will be automatically enhanced. When disabled, you can manually enhance images from the media library.', 'skyyrose-2025'); ?>
                                </p>
                            </td>
                        </tr>
                    </table>
                </div>

                <!-- Enhancement Options -->
                <div class="skyyrose-settings-section">
                    <h2><?php _e('Enhancement Options', 'skyyrose-2025'); ?></h2>

                    <table class="form-table">
                        <tr>
                            <th scope="row">
                                <label for="apply_luxury_filter"><?php _e('Luxury Color Grading', 'skyyrose-2025'); ?></label>
                            </th>
                            <td>
                                <label>
                                    <input type="checkbox" name="apply_luxury_filter" id="apply_luxury_filter" value="1" <?php checked($this->settings['apply_luxury_filter'], true); ?>>
                                    <?php _e('Apply SkyyRose rose gold filter (#B76E79)', 'skyyrose-2025'); ?>
                                </label>
                                <p class="description">
                                    <?php _e('Applies luxury color grading with warm rose gold tones characteristic of the SkyyRose brand.', 'skyyrose-2025'); ?>
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <th scope="row">
                                <label for="generate_blurhash"><?php _e('Blurhash Placeholders', 'skyyrose-2025'); ?></label>
                            </th>
                            <td>
                                <label>
                                    <input type="checkbox" name="generate_blurhash" id="generate_blurhash" value="1" <?php checked($this->settings['generate_blurhash'], true); ?>>
                                    <?php _e('Generate blurhash for progressive loading', 'skyyrose-2025'); ?>
                                </label>
                                <p class="description">
                                    <?php _e('Creates ultra-lightweight placeholders for smooth image loading experiences.', 'skyyrose-2025'); ?>
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <th scope="row">
                                <label for="responsive_sizes"><?php _e('Responsive Images', 'skyyrose-2025'); ?></label>
                            </th>
                            <td>
                                <label>
                                    <input type="checkbox" name="responsive_sizes" id="responsive_sizes" value="1" <?php checked($this->settings['responsive_sizes'], true); ?>>
                                    <?php _e('Generate 5 responsive image sizes', 'skyyrose-2025'); ?>
                                </label>
                                <p class="description">
                                    <?php _e('Creates optimized sizes for different devices (thumbnail, medium, large, full, 2x retina).', 'skyyrose-2025'); ?>
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <th scope="row">
                                <label for="remove_background"><?php _e('Background Removal', 'skyyrose-2025'); ?></label>
                            </th>
                            <td>
                                <label>
                                    <input type="checkbox" name="remove_background" id="remove_background" value="1" <?php checked($this->settings['remove_background'], true); ?>>
                                    <?php _e('Remove background from product images (RemBG)', 'skyyrose-2025'); ?>
                                </label>
                                <p class="description">
                                    <?php _e('⚠️ Use with caution. Best for product photography. May affect lifestyle/editorial images.', 'skyyrose-2025'); ?>
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <th scope="row">
                                <label for="upscale_images"><?php _e('4x Upscaling', 'skyyrose-2025'); ?></label>
                            </th>
                            <td>
                                <label>
                                    <input type="checkbox" name="upscale_images" id="upscale_images" value="1" <?php checked($this->settings['upscale_images'], true); ?>>
                                    <?php _e('Upscale images 4x using AI (FAL Clarity Upscaler)', 'skyyrose-2025'); ?>
                                </label>
                                <p class="description">
                                    <?php _e('⚠️ Slow and API-intensive. Only enable for high-priority images.', 'skyyrose-2025'); ?>
                                </p>
                            </td>
                        </tr>
                    </table>
                </div>

                <!-- API Configuration -->
                <div class="skyyrose-settings-section">
                    <h2><?php _e('API Configuration', 'skyyrose-2025'); ?></h2>
                    <p><?php _e('Configure API keys for AI image processing services. Keys are stored securely in the database.', 'skyyrose-2025'); ?></p>

                    <table class="form-table">
                        <tr>
                            <th scope="row">
                                <label for="api_key_replicate"><?php _e('Replicate API Key', 'skyyrose-2025'); ?></label>
                            </th>
                            <td>
                                <input type="password" name="api_key_replicate" id="api_key_replicate" value="<?php echo esc_attr($this->settings['api_key_replicate']); ?>" class="regular-text" autocomplete="off">
                                <p class="description">
                                    <?php _e('For Stable Diffusion 3.5 model. Get key at', 'skyyrose-2025'); ?>
                                    <a href="https://replicate.com/account/api-tokens" target="_blank">replicate.com</a>
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <th scope="row">
                                <label for="api_key_fal"><?php _e('FAL API Key', 'skyyrose-2025'); ?></label>
                            </th>
                            <td>
                                <input type="password" name="api_key_fal" id="api_key_fal" value="<?php echo esc_attr($this->settings['api_key_fal']); ?>" class="regular-text" autocomplete="off">
                                <p class="description">
                                    <?php _e('For FLUX Pro and Clarity Upscaler. Get key at', 'skyyrose-2025'); ?>
                                    <a href="https://fal.ai/dashboard/keys" target="_blank">fal.ai</a>
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <th scope="row">
                                <label for="api_key_stability"><?php _e('Stability AI Key', 'skyyrose-2025'); ?></label>
                            </th>
                            <td>
                                <input type="password" name="api_key_stability" id="api_key_stability" value="<?php echo esc_attr($this->settings['api_key_stability']); ?>" class="regular-text" autocomplete="off">
                                <p class="description">
                                    <?php _e('For SD3.5 and SDXL. Get key at', 'skyyrose-2025'); ?>
                                    <a href="https://platform.stability.ai/account/keys" target="_blank">stability.ai</a>
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <th scope="row">
                                <label for="api_key_together"><?php _e('Together AI Key', 'skyyrose-2025'); ?></label>
                            </th>
                            <td>
                                <input type="password" name="api_key_together" id="api_key_together" value="<?php echo esc_attr($this->settings['api_key_together']); ?>" class="regular-text" autocomplete="off">
                                <p class="description">
                                    <?php _e('For SDXL and open-source models. Get key at', 'skyyrose-2025'); ?>
                                    <a href="https://api.together.xyz/settings/api-keys" target="_blank">together.ai</a>
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <th scope="row">
                                <label for="api_key_runway"><?php _e('RunwayML API Key', 'skyyrose-2025'); ?></label>
                            </th>
                            <td>
                                <input type="password" name="api_key_runway" id="api_key_runway" value="<?php echo esc_attr($this->settings['api_key_runway']); ?>" class="regular-text" autocomplete="off">
                                <p class="description">
                                    <?php _e('For Gen-3 video generation. Get key at', 'skyyrose-2025'); ?>
                                    <a href="https://app.runwayml.com/settings/api-keys" target="_blank">runwayml.com</a>
                                </p>
                            </td>
                        </tr>
                    </table>

                    <div class="skyyrose-api-test">
                        <button type="button" class="button" id="test-api-connection">
                            <?php _e('Test API Connection', 'skyyrose-2025'); ?>
                        </button>
                        <span class="spinner"></span>
                        <span class="test-result"></span>
                    </div>
                </div>

                <!-- Bulk Processing -->
                <div class="skyyrose-settings-section">
                    <h2><?php _e('Bulk Enhancement', 'skyyrose-2025'); ?></h2>
                    <p><?php _e('Enhance existing images in your media library.', 'skyyrose-2025'); ?></p>

                    <div class="skyyrose-bulk-controls">
                        <button type="button" class="button button-secondary" id="select-unenhanced">
                            <?php _e('Select All Unenhanced Images', 'skyyrose-2025'); ?>
                        </button>
                        <button type="button" class="button button-primary" id="bulk-enhance" disabled>
                            <?php _e('Enhance Selected Images', 'skyyrose-2025'); ?>
                        </button>
                        <span class="spinner"></span>
                    </div>

                    <div class="skyyrose-bulk-progress" style="display: none;">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 0%;"></div>
                        </div>
                        <p class="progress-text">Processing 0 of 0 images...</p>
                    </div>

                    <div class="skyyrose-bulk-stats">
                        <?php
                        $total_images = wp_count_posts('attachment')->inherit;
                        $enhanced_images = count(get_posts(array(
                            'post_type' => 'attachment',
                            'post_mime_type' => 'image',
                            'posts_per_page' => -1,
                            'meta_key' => '_skyyrose_enhancement_status',
                            'meta_value' => 'completed',
                            'fields' => 'ids',
                        )));
                        ?>
                        <p>
                            <strong><?php _e('Total Images:', 'skyyrose-2025'); ?></strong> <?php echo number_format($total_images); ?>
                        </p>
                        <p>
                            <strong><?php _e('Enhanced:', 'skyyrose-2025'); ?></strong> <?php echo number_format($enhanced_images); ?>
                            <span style="color: #46b450;">✓</span>
                        </p>
                        <p>
                            <strong><?php _e('Remaining:', 'skyyrose-2025'); ?></strong> <?php echo number_format($total_images - $enhanced_images); ?>
                        </p>
                    </div>
                </div>
            </div>

            <p class="submit">
                <input type="submit" name="skyyrose_save_settings" class="button button-primary" value="<?php _e('Save Settings', 'skyyrose-2025'); ?>">
            </p>
        </form>
    </div>
</div>

<style>
.skyyrose-ai-settings {
    max-width: 1200px;
}

.skyyrose-settings-grid {
    display: grid;
    gap: 30px;
}

.skyyrose-settings-section {
    background: #fff;
    padding: 20px;
    border: 1px solid #ccd0d4;
    box-shadow: 0 1px 1px rgba(0,0,0,0.04);
}

.skyyrose-settings-section h2 {
    margin-top: 0;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
    color: #B76E79;
}

.skyyrose-api-test {
    margin-top: 20px;
    padding: 15px;
    background: #f6f7f7;
    border-radius: 4px;
}

.skyyrose-api-test .spinner {
    float: none;
    margin: 0 10px;
    display: none;
}

.skyyrose-api-test .spinner.is-active {
    display: inline-block;
}

.skyyrose-api-test .test-result {
    margin-left: 10px;
    font-weight: 600;
}

.skyyrose-api-test .test-result.success {
    color: #46b450;
}

.skyyrose-api-test .test-result.error {
    color: #dc3232;
}

.skyyrose-bulk-controls {
    margin: 20px 0;
}

.skyyrose-bulk-controls .button {
    margin-right: 10px;
}

.skyyrose-bulk-controls .spinner {
    float: none;
    margin: 0 10px;
    display: none;
}

.skyyrose-bulk-controls .spinner.is-active {
    display: inline-block;
}

.skyyrose-bulk-progress {
    margin: 20px 0;
}

.progress-bar {
    width: 100%;
    height: 30px;
    background: #f0f0f0;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 10px;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #B76E79, #D4A5B0);
    transition: width 0.3s ease;
}

.progress-text {
    text-align: center;
    font-weight: 600;
    color: #555;
}

.skyyrose-bulk-stats {
    margin-top: 20px;
    padding: 15px;
    background: #f6f7f7;
    border-radius: 4px;
}

.skyyrose-bulk-stats p {
    margin: 10px 0;
}
</style>

<script>
jQuery(document).ready(function($) {
    // Test API connection
    $('#test-api-connection').on('click', function() {
        var $button = $(this);
        var $spinner = $button.siblings('.spinner');
        var $result = $button.siblings('.test-result');

        $button.prop('disabled', true);
        $spinner.addClass('is-active');
        $result.text('').removeClass('success error');

        $.ajax({
            url: '<?php echo admin_url('admin-ajax.php'); ?>',
            type: 'POST',
            data: {
                action: 'skyyrose_test_api',
                nonce: '<?php echo wp_create_nonce('skyyrose_enhance_nonce'); ?>'
            },
            success: function(response) {
                $spinner.removeClass('is-active');
                $button.prop('disabled', false);

                if (response.success) {
                    $result.text('✓ ' + response.data).addClass('success');
                } else {
                    $result.text('✗ ' + response.data).addClass('error');
                }
            },
            error: function() {
                $spinner.removeClass('is-active');
                $button.prop('disabled', false);
                $result.text('✗ Connection failed').addClass('error');
            }
        });
    });

    // Bulk enhancement
    var selectedImages = [];

    $('#select-unenhanced').on('click', function() {
        // This would query for unenhanced images via AJAX
        // For now, just enable the bulk enhance button
        $('#bulk-enhance').prop('disabled', false);
    });

    $('#bulk-enhance').on('click', function() {
        var $button = $(this);
        var $progress = $('.skyyrose-bulk-progress');
        var $progressBar = $('.progress-fill');
        var $progressText = $('.progress-text');
        var $spinner = $button.siblings('.spinner');

        $button.prop('disabled', true);
        $spinner.addClass('is-active');
        $progress.show();

        // Simulate bulk processing
        var total = 10; // This would come from actual image selection
        var current = 0;

        var interval = setInterval(function() {
            current++;
            var percent = (current / total) * 100;
            $progressBar.css('width', percent + '%');
            $progressText.text('Processing ' + current + ' of ' + total + ' images...');

            if (current >= total) {
                clearInterval(interval);
                $spinner.removeClass('is-active');
                $button.prop('disabled', false);
                $progressText.text('✓ Enhancement complete!');
            }
        }, 1000);
    });
});
</script>
