<?php
/**
 * SkyyRose 3D Admin Settings
 *
 * WordPress Settings API page for controlling 3D experience parameters
 *
 * @package SkyyRose_Immersive
 */

defined('ABSPATH') || exit;

/**
 * Register admin menu
 */
add_action('admin_menu', 'skyyrose_3d_add_admin_menu');
function skyyrose_3d_add_admin_menu() {
    add_options_page(
        __('SkyyRose 3D Settings', 'skyyrose-immersive'),
        __('SkyyRose 3D', 'skyyrose-immersive'),
        'manage_options',
        'skyyrose-3d',
        'skyyrose_3d_settings_page'
    );
}

/**
 * Register settings
 */
add_action('admin_init', 'skyyrose_3d_register_settings');
function skyyrose_3d_register_settings() {
    register_setting('skyyrose_3d_options', 'skyyrose_3d_settings', 'skyyrose_3d_sanitize_settings');

    // Performance Section
    add_settings_section(
        'skyyrose_3d_performance',
        __('Performance Settings', 'skyyrose-immersive'),
        'skyyrose_3d_performance_section_callback',
        'skyyrose-3d'
    );

    add_settings_field(
        'particle_count',
        __('Particle Count (Desktop)', 'skyyrose-immersive'),
        'skyyrose_3d_particle_count_field',
        'skyyrose-3d',
        'skyyrose_3d_performance'
    );

    add_settings_field(
        'mobile_particle_percent',
        __('Mobile Particle %', 'skyyrose-immersive'),
        'skyyrose_3d_mobile_particle_field',
        'skyyrose-3d',
        'skyyrose_3d_performance'
    );

    add_settings_field(
        'enable_bloom',
        __('Bloom Effect', 'skyyrose-immersive'),
        'skyyrose_3d_bloom_field',
        'skyyrose-3d',
        'skyyrose_3d_performance'
    );

    add_settings_field(
        'bloom_intensity',
        __('Bloom Intensity', 'skyyrose-immersive'),
        'skyyrose_3d_bloom_intensity_field',
        'skyyrose-3d',
        'skyyrose_3d_performance'
    );

    // Page Enable/Disable Section
    add_settings_section(
        'skyyrose_3d_pages',
        __('3D Experience Pages', 'skyyrose-immersive'),
        'skyyrose_3d_pages_section_callback',
        'skyyrose-3d'
    );

    add_settings_field(
        'enable_homepage_3d',
        __('Homepage 3D Hero', 'skyyrose-immersive'),
        'skyyrose_3d_homepage_field',
        'skyyrose-3d',
        'skyyrose_3d_pages'
    );

    add_settings_field(
        'enable_preorder_3d',
        __('Pre-Order Experience', 'skyyrose-immersive'),
        'skyyrose_3d_preorder_field',
        'skyyrose-3d',
        'skyyrose_3d_pages'
    );

    add_settings_field(
        'enable_collections_3d',
        __('Collection Pages', 'skyyrose-immersive'),
        'skyyrose_3d_collections_field',
        'skyyrose-3d',
        'skyyrose_3d_pages'
    );

    // Visual Section
    add_settings_section(
        'skyyrose_3d_visual',
        __('Visual Settings', 'skyyrose-immersive'),
        'skyyrose_3d_visual_section_callback',
        'skyyrose-3d'
    );

    add_settings_field(
        'lighting_intensity',
        __('Lighting Intensity', 'skyyrose-immersive'),
        'skyyrose_3d_lighting_field',
        'skyyrose-3d',
        'skyyrose_3d_visual'
    );

    add_settings_field(
        'enable_chromatic',
        __('Chromatic Aberration', 'skyyrose-immersive'),
        'skyyrose_3d_chromatic_field',
        'skyyrose-3d',
        'skyyrose_3d_visual'
    );
}

/**
 * Sanitize settings
 */
function skyyrose_3d_sanitize_settings($input) {
    $sanitized = array();

    $sanitized['particle_count'] = isset($input['particle_count'])
        ? min(10000, max(100, intval($input['particle_count'])))
        : 3000;

    $sanitized['mobile_particle_percent'] = isset($input['mobile_particle_percent'])
        ? min(100, max(10, intval($input['mobile_particle_percent'])))
        : 30;

    $sanitized['enable_bloom'] = isset($input['enable_bloom']) ? 1 : 0;

    $sanitized['bloom_intensity'] = isset($input['bloom_intensity'])
        ? min(3.0, max(0.1, floatval($input['bloom_intensity'])))
        : 1.5;

    $sanitized['enable_homepage_3d'] = isset($input['enable_homepage_3d']) ? 1 : 0;
    $sanitized['enable_preorder_3d'] = isset($input['enable_preorder_3d']) ? 1 : 0;
    $sanitized['enable_collections_3d'] = isset($input['enable_collections_3d']) ? 1 : 0;

    $sanitized['lighting_intensity'] = isset($input['lighting_intensity'])
        ? min(3.0, max(0.1, floatval($input['lighting_intensity'])))
        : 1.0;

    $sanitized['enable_chromatic'] = isset($input['enable_chromatic']) ? 1 : 0;

    return $sanitized;
}

/**
 * Section callbacks
 */
function skyyrose_3d_performance_section_callback() {
    echo '<p>' . __('Configure performance settings for 3D experiences. Lower values improve performance on slower devices.', 'skyyrose-immersive') . '</p>';
}

function skyyrose_3d_pages_section_callback() {
    echo '<p>' . __('Enable or disable 3D experiences on specific pages.', 'skyyrose-immersive') . '</p>';
}

function skyyrose_3d_visual_section_callback() {
    echo '<p>' . __('Adjust visual quality and effects.', 'skyyrose-immersive') . '</p>';
}

/**
 * Field callbacks
 */
function skyyrose_3d_particle_count_field() {
    $options = get_option('skyyrose_3d_settings', array());
    $value = isset($options['particle_count']) ? $options['particle_count'] : 3000;
    ?>
    <input type="range" name="skyyrose_3d_settings[particle_count]" value="<?php echo esc_attr($value); ?>" min="100" max="10000" step="100" id="particle_count" oninput="document.getElementById('particle_count_value').textContent = this.value">
    <span id="particle_count_value"><?php echo esc_html($value); ?></span>
    <p class="description"><?php _e('Number of particles in 3D scenes (100-10000). Default: 3000', 'skyyrose-immersive'); ?></p>
    <?php
}

function skyyrose_3d_mobile_particle_field() {
    $options = get_option('skyyrose_3d_settings', array());
    $value = isset($options['mobile_particle_percent']) ? $options['mobile_particle_percent'] : 30;
    ?>
    <input type="range" name="skyyrose_3d_settings[mobile_particle_percent]" value="<?php echo esc_attr($value); ?>" min="10" max="100" step="5" id="mobile_percent" oninput="document.getElementById('mobile_percent_value').textContent = this.value + '%'">
    <span id="mobile_percent_value"><?php echo esc_html($value); ?>%</span>
    <p class="description"><?php _e('Percentage of desktop particles on mobile devices (10-100%). Default: 30%', 'skyyrose-immersive'); ?></p>
    <?php
}

function skyyrose_3d_bloom_field() {
    $options = get_option('skyyrose_3d_settings', array());
    $checked = isset($options['enable_bloom']) ? $options['enable_bloom'] : 1;
    ?>
    <label>
        <input type="checkbox" name="skyyrose_3d_settings[enable_bloom]" value="1" <?php checked($checked, 1); ?>>
        <?php _e('Enable bloom post-processing effect', 'skyyrose-immersive'); ?>
    </label>
    <p class="description"><?php _e('Adds a glow effect to bright areas. May impact performance on older devices.', 'skyyrose-immersive'); ?></p>
    <?php
}

function skyyrose_3d_bloom_intensity_field() {
    $options = get_option('skyyrose_3d_settings', array());
    $value = isset($options['bloom_intensity']) ? $options['bloom_intensity'] : 1.5;
    ?>
    <input type="range" name="skyyrose_3d_settings[bloom_intensity]" value="<?php echo esc_attr($value); ?>" min="0.1" max="3.0" step="0.1" id="bloom_intensity" oninput="document.getElementById('bloom_intensity_value').textContent = this.value">
    <span id="bloom_intensity_value"><?php echo esc_html($value); ?></span>
    <p class="description"><?php _e('Bloom effect intensity (0.1-3.0). Default: 1.5', 'skyyrose-immersive'); ?></p>
    <?php
}

function skyyrose_3d_homepage_field() {
    $options = get_option('skyyrose_3d_settings', array());
    $checked = isset($options['enable_homepage_3d']) ? $options['enable_homepage_3d'] : 1;
    ?>
    <label>
        <input type="checkbox" name="skyyrose_3d_settings[enable_homepage_3d]" value="1" <?php checked($checked, 1); ?>>
        <?php _e('Enable 3D hero on homepage', 'skyyrose-immersive'); ?>
    </label>
    <?php
}

function skyyrose_3d_preorder_field() {
    $options = get_option('skyyrose_3d_settings', array());
    $checked = isset($options['enable_preorder_3d']) ? $options['enable_preorder_3d'] : 1;
    ?>
    <label>
        <input type="checkbox" name="skyyrose_3d_settings[enable_preorder_3d]" value="1" <?php checked($checked, 1); ?>>
        <?php _e('Enable 3D pre-order experience', 'skyyrose-immersive'); ?>
    </label>
    <?php
}

function skyyrose_3d_collections_field() {
    $options = get_option('skyyrose_3d_settings', array());
    $checked = isset($options['enable_collections_3d']) ? $options['enable_collections_3d'] : 1;
    ?>
    <label>
        <input type="checkbox" name="skyyrose_3d_settings[enable_collections_3d]" value="1" <?php checked($checked, 1); ?>>
        <?php _e('Enable 3D on collection pages (Signature, Love Hurts, Black Rose)', 'skyyrose-immersive'); ?>
    </label>
    <?php
}

function skyyrose_3d_lighting_field() {
    $options = get_option('skyyrose_3d_settings', array());
    $value = isset($options['lighting_intensity']) ? $options['lighting_intensity'] : 1.0;
    ?>
    <input type="range" name="skyyrose_3d_settings[lighting_intensity]" value="<?php echo esc_attr($value); ?>" min="0.1" max="3.0" step="0.1" id="lighting_intensity" oninput="document.getElementById('lighting_intensity_value').textContent = this.value">
    <span id="lighting_intensity_value"><?php echo esc_html($value); ?></span>
    <p class="description"><?php _e('Scene lighting intensity (0.1-3.0). Default: 1.0', 'skyyrose-immersive'); ?></p>
    <?php
}

function skyyrose_3d_chromatic_field() {
    $options = get_option('skyyrose_3d_settings', array());
    $checked = isset($options['enable_chromatic']) ? $options['enable_chromatic'] : 1;
    ?>
    <label>
        <input type="checkbox" name="skyyrose_3d_settings[enable_chromatic]" value="1" <?php checked($checked, 1); ?>>
        <?php _e('Enable chromatic aberration effect', 'skyyrose-immersive'); ?>
    </label>
    <p class="description"><?php _e('Adds a subtle color fringe effect for a cinematic look.', 'skyyrose-immersive'); ?></p>
    <?php
}

/**
 * Settings page HTML
 */
function skyyrose_3d_settings_page() {
    if (!current_user_can('manage_options')) {
        return;
    }

    // Check if settings saved
    if (isset($_GET['settings-updated'])) {
        add_settings_error('skyyrose_3d_messages', 'skyyrose_3d_message', __('Settings Saved', 'skyyrose-immersive'), 'updated');
    }

    settings_errors('skyyrose_3d_messages');
    ?>
    <div class="wrap">
        <h1><?php echo esc_html(get_admin_page_title()); ?></h1>

        <style>
            .skyyrose-admin-header {
                background: linear-gradient(135deg, #B76E79, #8B4D5C);
                color: #fff;
                padding: 20px 25px;
                margin: 20px 0;
                border-radius: 4px;
            }
            .skyyrose-admin-header h2 {
                margin: 0 0 5px;
                font-size: 24px;
            }
            .skyyrose-admin-header p {
                margin: 0;
                opacity: 0.9;
            }
            .skyyrose-admin-collections {
                display: flex;
                gap: 20px;
                margin: 20px 0;
            }
            .skyyrose-collection-card {
                flex: 1;
                padding: 20px;
                background: #fff;
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
            }
            .skyyrose-collection-card .emoji {
                font-size: 48px;
                display: block;
                margin-bottom: 10px;
            }
            .skyyrose-collection-card h3 {
                margin: 0 0 5px;
            }
            .skyyrose-collection-card p {
                color: #666;
                margin: 0;
                font-size: 13px;
            }
        </style>

        <div class="skyyrose-admin-header">
            <h2>SkyyRose Immersive 3D</h2>
            <p>Configure 3D experiences for your luxury streetwear collections</p>
        </div>

        <div class="skyyrose-admin-collections">
            <div class="skyyrose-collection-card">
                <span class="emoji">🌹</span>
                <h3>Signature</h3>
                <p>Gold, Rose Gold, Black</p>
            </div>
            <div class="skyyrose-collection-card">
                <span class="emoji">🥀</span>
                <h3>Black Rose</h3>
                <p>Crimson, Obsidian, Silver</p>
            </div>
            <div class="skyyrose-collection-card">
                <span class="emoji">💔</span>
                <h3>Love Hurts</h3>
                <p>Rose, Burgundy, Purple</p>
            </div>
        </div>

        <form action="options.php" method="post">
            <?php
            settings_fields('skyyrose_3d_options');
            do_settings_sections('skyyrose-3d');
            submit_button(__('Save Settings', 'skyyrose-immersive'));
            ?>
        </form>

        <hr>

        <h2><?php _e('Quick Links', 'skyyrose-immersive'); ?></h2>
        <ul>
            <li><a href="<?php echo home_url('/'); ?>"><?php _e('View Homepage', 'skyyrose-immersive'); ?></a></li>
            <li><a href="<?php echo home_url('/preorder/'); ?>"><?php _e('View Pre-Order Experience', 'skyyrose-immersive'); ?></a></li>
            <li><a href="<?php echo admin_url('edit.php?post_type=page'); ?>"><?php _e('Manage Pages', 'skyyrose-immersive'); ?></a></li>
        </ul>
    </div>
    <?php
}

/**
 * Get 3D settings (helper function for templates)
 */
function skyyrose_get_3d_settings() {
    $defaults = array(
        'particle_count' => 3000,
        'mobile_particle_percent' => 30,
        'enable_bloom' => 1,
        'bloom_intensity' => 1.5,
        'enable_homepage_3d' => 1,
        'enable_preorder_3d' => 1,
        'enable_collections_3d' => 1,
        'lighting_intensity' => 1.0,
        'enable_chromatic' => 1,
    );

    $options = get_option('skyyrose_3d_settings', array());

    return wp_parse_args($options, $defaults);
}

/**
 * Expose settings to JavaScript
 */
add_action('wp_head', 'skyyrose_3d_settings_js', 5);
function skyyrose_3d_settings_js() {
    $settings = skyyrose_get_3d_settings();
    ?>
    <script>
    window.skyyrose3DSettings = <?php echo wp_json_encode($settings); ?>;
    </script>
    <?php
}
