<?php
/**
 * SkyyRose 2025 Theme Deployment Script
 *
 * This script automates the deployment of the SkyyRose 2025 theme:
 * 1. Activates the theme
 * 2. Installs and activates required plugins (WooCommerce, Elementor)
 * 3. Creates sample pages with custom templates
 * 4. Sets up navigation menu
 * 5. Configures WooCommerce basic settings
 * 6. Sets theme customizer defaults
 *
 * USAGE:
 * 1. Upload this file to: /wp-content/themes/skyyrose-2025/
 * 2. Visit in browser: http://localhost:8881/wp-content/themes/skyyrose-2025/skyyrose-2025-deploy.php
 * 3. Follow on-screen instructions
 *
 * IMPORTANT: Delete this file after deployment for security!
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

// Load WordPress
require_once($_SERVER['DOCUMENT_ROOT'] . '/wp-load.php');

// Security check - only admins can run this
if (!current_user_can('activate_plugins')) {
    wp_die('You do not have sufficient permissions to run this deployment script.');
}

// Prevent timeout for long operations
set_time_limit(300);

// Output buffer for clean HTML
ob_start();

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkyyRose 2025 Theme Deployment</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #8B0000;
            border-bottom: 3px solid #D4AF37;
            padding-bottom: 15px;
        }
        .step {
            margin: 20px 0;
            padding: 15px;
            background: #f9f9f9;
            border-left: 4px solid #8B0000;
        }
        .success {
            color: #28a745;
            font-weight: bold;
        }
        .error {
            color: #dc3545;
            font-weight: bold;
        }
        .warning {
            color: #ffc107;
            font-weight: bold;
        }
        .info {
            color: #17a2b8;
        }
        .code {
            background: #272822;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            margin: 10px 0;
        }
        .button {
            display: inline-block;
            padding: 12px 24px;
            background: #8B0000;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 20px;
        }
        .button:hover {
            background: #6B0000;
        }
    </style>
</head>
<body>
<div class="container">
    <h1>🎨 SkyyRose 2025 Theme Deployment</h1>
    <p><strong>Where Love Meets Luxury</strong></p>

    <?php

    $deployment_results = [];
    $errors = [];

    // ============================================
    // STEP 1: Activate Theme
    // ============================================
    echo '<div class="step">';
    echo '<h2>Step 1: Activate Theme</h2>';

    $theme = wp_get_theme('skyyrose-2025');
    if ($theme->exists()) {
        switch_theme('skyyrose-2025');
        echo '<p class="success">✓ SkyyRose 2025 theme activated successfully!</p>';
        $deployment_results[] = 'Theme activated';
    } else {
        echo '<p class="error">✗ Theme not found in wp-content/themes/skyyrose-2025/</p>';
        $errors[] = 'Theme not found';
    }

    echo '</div>';

    // ============================================
    // STEP 2: Check/Install Required Plugins
    // ============================================
    echo '<div class="step">';
    echo '<h2>Step 2: Required Plugins</h2>';

    $required_plugins = [
        'woocommerce' => 'WooCommerce',
        'elementor' => 'Elementor',
    ];

    foreach ($required_plugins as $slug => $name) {
        $plugin_file = $slug . '/' . $slug . '.php';

        if (is_plugin_active($plugin_file)) {
            echo "<p class='success'>✓ $name is already active</p>";
            $deployment_results[] = "$name active";
        } elseif (file_exists(WP_PLUGIN_DIR . '/' . $plugin_file)) {
            activate_plugin($plugin_file);
            echo "<p class='success'>✓ $name activated</p>";
            $deployment_results[] = "$name activated";
        } else {
            echo "<p class='warning'>! $name not installed - please install manually from Plugins > Add New</p>";
            echo "<p class='info'>Search for '$name' and click 'Install Now' then 'Activate'</p>";
            $errors[] = "$name needs manual installation";
        }
    }

    echo '</div>';

    // ============================================
    // STEP 3: Create Sample Pages
    // ============================================
    echo '<div class="step">';
    echo '<h2>Step 3: Create Sample Pages</h2>';

    $pages_to_create = [
        [
            'title' => 'Home',
            'template' => 'template-home.php',
            'content' => 'Welcome to SkyyRose - Where Love Meets Luxury',
            'meta' => [],
        ],
        [
            'title' => 'Black Rose',
            'template' => 'template-immersive.php',
            'content' => 'Enter the futuristic rose garden',
            'meta' => ['_collection_type' => 'black-rose'],
        ],
        [
            'title' => 'Love Hurts',
            'template' => 'template-immersive.php',
            'content' => 'Experience the enchanted castle',
            'meta' => ['_collection_type' => 'love-hurts'],
        ],
        [
            'title' => 'Signature',
            'template' => 'template-immersive.php',
            'content' => 'Walk the golden runway',
            'meta' => ['_collection_type' => 'signature'],
        ],
        [
            'title' => 'Collections',
            'template' => 'template-collection.php',
            'content' => 'Browse our luxury collections',
            'meta' => [],
        ],
        [
            'title' => 'The Vault',
            'template' => 'template-vault.php',
            'content' => 'Pre-order exclusive pieces',
            'meta' => [],
        ],
    ];

    $created_pages = [];

    foreach ($pages_to_create as $page_data) {
        // Check if page already exists
        $existing_page = get_page_by_title($page_data['title'], OBJECT, 'page');

        if ($existing_page) {
            echo "<p class='info'>○ Page '{$page_data['title']}' already exists (ID: {$existing_page->ID})</p>";
            $created_pages[$page_data['title']] = $existing_page->ID;
        } else {
            // Create new page
            $page_id = wp_insert_post([
                'post_title' => $page_data['title'],
                'post_content' => $page_data['content'],
                'post_status' => 'publish',
                'post_type' => 'page',
                'post_author' => get_current_user_id(),
            ]);

            if ($page_id && !is_wp_error($page_id)) {
                // Set template
                update_post_meta($page_id, '_wp_page_template', $page_data['template']);

                // Set custom meta fields
                foreach ($page_data['meta'] as $key => $value) {
                    update_post_meta($page_id, $key, $value);
                }

                echo "<p class='success'>✓ Created '{$page_data['title']}' (ID: $page_id) with template {$page_data['template']}</p>";
                $created_pages[$page_data['title']] = $page_id;
                $deployment_results[] = "Created page: {$page_data['title']}";
            } else {
                echo "<p class='error'>✗ Failed to create '{$page_data['title']}'</p>";
                $errors[] = "Failed to create page: {$page_data['title']}";
            }
        }
    }

    // Set homepage
    if (isset($created_pages['Home'])) {
        update_option('page_on_front', $created_pages['Home']);
        update_option('show_on_front', 'page');
        echo "<p class='success'>✓ Set 'Home' as static front page</p>";
        $deployment_results[] = 'Set homepage';
    }

    echo '</div>';

    // ============================================
    // STEP 4: Create Navigation Menu
    // ============================================
    echo '<div class="step">';
    echo '<h2>Step 4: Navigation Menu</h2>';

    $menu_name = 'Primary Menu';
    $menu_exists = wp_get_nav_menu_object($menu_name);

    if (!$menu_exists) {
        $menu_id = wp_create_nav_menu($menu_name);

        // Add menu items
        $menu_items = [
            'Home' => isset($created_pages['Home']) ? $created_pages['Home'] : null,
            'Black Rose' => isset($created_pages['Black Rose']) ? $created_pages['Black Rose'] : null,
            'Love Hurts' => isset($created_pages['Love Hurts']) ? $created_pages['Love Hurts'] : null,
            'Signature' => isset($created_pages['Signature']) ? $created_pages['Signature'] : null,
            'Collections' => isset($created_pages['Collections']) ? $created_pages['Collections'] : null,
            'The Vault' => isset($created_pages['The Vault']) ? $created_pages['The Vault'] : null,
        ];

        $position = 0;
        foreach ($menu_items as $title => $page_id) {
            if ($page_id) {
                wp_update_nav_menu_item($menu_id, 0, [
                    'menu-item-title' => $title,
                    'menu-item-object' => 'page',
                    'menu-item-object-id' => $page_id,
                    'menu-item-type' => 'post_type',
                    'menu-item-status' => 'publish',
                    'menu-item-position' => ++$position,
                ]);
            }
        }

        // Assign to primary location
        $locations = get_theme_mod('nav_menu_locations');
        $locations['primary'] = $menu_id;
        set_theme_mod('nav_menu_locations', $locations);

        echo "<p class='success'>✓ Created '$menu_name' and assigned to primary location</p>";
        $deployment_results[] = 'Created navigation menu';
    } else {
        echo "<p class='info'>○ Menu '$menu_name' already exists</p>";
    }

    echo '</div>';

    // ============================================
    // STEP 5: Theme Customizer Defaults
    // ============================================
    echo '<div class="step">';
    echo '<h2>Step 5: Theme Customizer Settings</h2>';

    $customizer_defaults = [
        'skyyrose_brand_name' => 'SkyyRose',
        'skyyrose_tagline' => 'Where Love Meets Luxury',
        'skyyrose_collection_black_rose_color' => '#8B0000',
        'skyyrose_collection_love_hurts_color' => '#B76E79',
        'skyyrose_collection_signature_color' => '#D4AF37',
    ];

    foreach ($customizer_defaults as $setting => $value) {
        set_theme_mod($setting, $value);
        echo "<p class='success'>✓ Set $setting: $value</p>";
    }

    $deployment_results[] = 'Configured theme customizer';

    echo '</div>';

    // ============================================
    // STEP 6: WooCommerce Settings
    // ============================================
    if (is_plugin_active('woocommerce/woocommerce.php')) {
        echo '<div class="step">';
        echo '<h2>Step 6: WooCommerce Configuration</h2>';

        // Create WooCommerce pages if needed
        WC_Install::create_pages();

        // Basic WooCommerce settings
        update_option('woocommerce_store_address', 'Oakland');
        update_option('woocommerce_store_city', 'Oakland');
        update_option('woocommerce_default_country', 'US:CA');
        update_option('woocommerce_currency', 'USD');
        update_option('woocommerce_enable_reviews', 'yes');

        // Create product categories for collections
        $collections = [
            'Black Rose' => 'Futuristic gothic streetwear with metallic accents',
            'Love Hurts' => 'Romantic rebellion - where beauty meets pain',
            'Signature' => 'Timeless luxury with golden details',
        ];

        foreach ($collections as $cat_name => $cat_desc) {
            $term = term_exists($cat_name, 'product_cat');
            if (!$term) {
                wp_insert_term($cat_name, 'product_cat', [
                    'description' => $cat_desc,
                    'slug' => sanitize_title($cat_name),
                ]);
                echo "<p class='success'>✓ Created product category: $cat_name</p>";
            } else {
                echo "<p class='info'>○ Product category '$cat_name' already exists</p>";
            }
        }

        echo "<p class='success'>✓ WooCommerce configured with basic settings</p>";
        $deployment_results[] = 'Configured WooCommerce';

        echo '</div>';
    }

    // ============================================
    // FINAL SUMMARY
    // ============================================
    echo '<div class="step" style="border-left-color: #D4AF37;">';
    echo '<h2>🎉 Deployment Summary</h2>';

    if (count($errors) === 0) {
        echo '<p class="success" style="font-size: 18px;">✓ Deployment completed successfully!</p>';
    } else {
        echo '<p class="warning" style="font-size: 18px;">⚠ Deployment completed with warnings</p>';
    }

    echo '<h3>Completed Actions:</h3><ul>';
    foreach ($deployment_results as $result) {
        echo "<li class='success'>$result</li>";
    }
    echo '</ul>';

    if (count($errors) > 0) {
        echo '<h3>Manual Actions Required:</h3><ul>';
        foreach ($errors as $error) {
            echo "<li class='warning'>$error</li>";
        }
        echo '</ul>';
    }

    echo '<h3>Next Steps:</h3>';
    echo '<ol>';
    echo '<li>Visit <a href="' . admin_url('customize.php') . '">Appearance > Customize</a> to customize brand colors and settings</li>';
    echo '<li>Add products via <a href="' . admin_url('edit.php?post_type=product') . '">Products > Add New</a></li>';
    echo '<li>Edit pages with Elementor to add immersive 3D scenes and widgets</li>';
    echo '<li>Configure WooCommerce payment gateways and shipping in <a href="' . admin_url('admin.php?page=wc-settings') . '">WooCommerce Settings</a></li>';
    echo '<li><strong class="error">DELETE THIS FILE (skyyrose-2025-deploy.php) for security!</strong></li>';
    echo '</ol>';

    echo '<a href="' . admin_url() . '" class="button">Go to WordPress Admin</a>';
    echo '<a href="' . home_url() . '" class="button" style="background: #D4AF37; margin-left: 10px;">View Site</a>';

    echo '</div>';

    ?>

    <div style="margin-top: 30px; padding: 20px; background: #272822; color: #f8f8f2; border-radius: 4px;">
        <p><strong>SkyyRose 2025 Theme v2.0.0</strong></p>
        <p>Created with ❤️ by SkyyRose LLC</p>
        <p><em>Where Love Meets Luxury</em></p>
    </div>
</div>
</body>
</html>
<?php

ob_end_flush();
