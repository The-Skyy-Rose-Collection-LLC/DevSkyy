# WordPress Development

This skill provides comprehensive knowledge of WordPress theme development fundamentals. It activates when users mention "WordPress", "theme development", "functions.php", "hooks", "filters", "custom post types", or need core WordPress functionality.

---

## Theme Structure

### Complete Theme Directory
```
theme-name/
├── style.css                 # Theme metadata & main styles
├── functions.php             # Theme setup & functionality
├── index.php                 # Fallback template
├── front-page.php           # Homepage template
├── page.php                  # Default page template
├── single.php               # Single post template
├── archive.php              # Archive template
├── search.php               # Search results
├── 404.php                  # 404 page
├── header.php               # Header template
├── footer.php               # Footer template
├── sidebar.php              # Sidebar template
├── inc/                     # PHP includes
│   ├── theme-setup.php      # Theme support features
│   ├── enqueue.php          # Scripts & styles
│   ├── customizer.php       # Customizer settings
│   ├── widgets.php          # Custom widgets
│   ├── shortcodes.php       # Custom shortcodes
│   ├── ajax.php             # AJAX handlers
│   └── cpt.php              # Custom post types
├── template-parts/          # Reusable templates
│   ├── header/
│   ├── footer/
│   └── content/
├── assets/
│   ├── css/
│   ├── js/
│   ├── images/
│   └── fonts/
├── languages/               # Translation files
└── page-templates/          # Custom page templates
```

## Theme Setup

### style.css Header
```css
/*
Theme Name: Theme Name
Theme URI: https://example.com/theme
Author: Author Name
Author URI: https://example.com
Description: A stunning immersive e-commerce theme
Version: 1.0.0
Requires at least: 6.0
Tested up to: 6.4
Requires PHP: 8.0
License: GPL-2.0-or-later
License URI: https://www.gnu.org/licenses/gpl-2.0.html
Text Domain: theme-textdomain
Tags: e-commerce, woocommerce, custom-colors, custom-menu
*/
```

### functions.php Setup
```php
<?php
/**
 * Theme functions and definitions
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Theme constants
define('THEME_VERSION', '1.0.0');
define('THEME_DIR', get_template_directory());
define('THEME_URI', get_template_directory_uri());

// Include theme files
$theme_includes = [
    '/inc/theme-setup.php',
    '/inc/enqueue.php',
    '/inc/customizer.php',
    '/inc/widgets.php',
    '/inc/shortcodes.php',
    '/inc/ajax.php',
];

foreach ($theme_includes as $file) {
    require_once THEME_DIR . $file;
}

// WooCommerce integration (if exists)
if (class_exists('WooCommerce')) {
    require_once THEME_DIR . '/inc/woocommerce.php';
}
```

### Theme Support
```php
// inc/theme-setup.php
function theme_setup() {
    // Translation support
    load_theme_textdomain('theme-textdomain', THEME_DIR . '/languages');

    // Theme supports
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('automatic-feed-links');
    add_theme_support('html5', [
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
        'style',
        'script'
    ]);

    // Custom logo
    add_theme_support('custom-logo', [
        'height'      => 100,
        'width'       => 300,
        'flex-height' => true,
        'flex-width'  => true,
    ]);

    // Editor styles
    add_theme_support('editor-styles');
    add_editor_style('assets/css/editor-style.css');

    // Block editor
    add_theme_support('wp-block-styles');
    add_theme_support('responsive-embeds');
    add_theme_support('align-wide');

    // Custom image sizes
    add_image_size('hero', 1920, 1080, true);
    add_image_size('product-large', 800, 800, true);
    add_image_size('product-thumb', 400, 400, true);

    // Navigation menus
    register_nav_menus([
        'primary'   => __('Primary Navigation', 'theme-textdomain'),
        'footer'    => __('Footer Navigation', 'theme-textdomain'),
        'mobile'    => __('Mobile Navigation', 'theme-textdomain'),
    ]);
}
add_action('after_setup_theme', 'theme_setup');
```

## Enqueuing Assets

### Scripts and Styles
```php
// inc/enqueue.php
function theme_enqueue_assets() {
    // Main stylesheet
    wp_enqueue_style(
        'theme-style',
        THEME_URI . '/assets/css/main.css',
        [],
        THEME_VERSION
    );

    // Google Fonts
    wp_enqueue_style(
        'theme-fonts',
        'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
        [],
        null
    );

    // Main JavaScript
    wp_enqueue_script(
        'theme-script',
        THEME_URI . '/assets/js/main.js',
        ['jquery'],
        THEME_VERSION,
        true
    );

    // GSAP (if needed)
    wp_enqueue_script(
        'gsap',
        'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js',
        [],
        '3.12.2',
        true
    );

    wp_enqueue_script(
        'gsap-scrolltrigger',
        'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js',
        ['gsap'],
        '3.12.2',
        true
    );

    // Localize script
    wp_localize_script('theme-script', 'themeData', [
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'nonce'   => wp_create_nonce('theme_nonce'),
        'siteUrl' => home_url(),
    ]);
}
add_action('wp_enqueue_scripts', 'theme_enqueue_assets');

// Conditional loading
function theme_conditional_assets() {
    if (is_singular() && comments_open()) {
        wp_enqueue_script('comment-reply');
    }

    if (is_page_template('page-templates/contact.php')) {
        wp_enqueue_script('contact-form', THEME_URI . '/assets/js/contact.js', [], THEME_VERSION, true);
    }
}
add_action('wp_enqueue_scripts', 'theme_conditional_assets');
```

### Deferred/Async Loading
```php
function theme_async_scripts($tag, $handle, $src) {
    $async_scripts = ['theme-script', 'gsap'];
    $defer_scripts = ['gsap-scrolltrigger'];

    if (in_array($handle, $async_scripts)) {
        return str_replace(' src', ' async src', $tag);
    }

    if (in_array($handle, $defer_scripts)) {
        return str_replace(' src', ' defer src', $tag);
    }

    return $tag;
}
add_filter('script_loader_tag', 'theme_async_scripts', 10, 3);
```

## Hooks and Filters

### Common Actions
```php
// Before header
add_action('theme_before_header', 'theme_announcement_bar');
function theme_announcement_bar() {
    if (get_theme_mod('show_announcement', true)) {
        get_template_part('template-parts/header/announcement');
    }
}

// After content
add_action('theme_after_content', 'theme_related_posts');
function theme_related_posts() {
    if (is_singular('post')) {
        get_template_part('template-parts/content/related-posts');
    }
}
```

### Common Filters
```php
// Excerpt length
add_filter('excerpt_length', function($length) {
    return 20;
});

// Excerpt more
add_filter('excerpt_more', function($more) {
    return '...';
});

// Body classes
add_filter('body_class', function($classes) {
    if (is_front_page()) {
        $classes[] = 'home-page';
    }
    if (is_singular()) {
        global $post;
        $classes[] = 'page-' . $post->post_name;
    }
    return $classes;
});

// Archive title
add_filter('get_the_archive_title', function($title) {
    if (is_category()) {
        return single_cat_title('', false);
    } elseif (is_tag()) {
        return single_tag_title('', false);
    } elseif (is_author()) {
        return get_the_author();
    }
    return $title;
});
```

## Custom Post Types

```php
// inc/cpt.php
function register_custom_post_types() {
    // Portfolio
    register_post_type('portfolio', [
        'labels' => [
            'name'               => __('Portfolio', 'theme-textdomain'),
            'singular_name'      => __('Project', 'theme-textdomain'),
            'add_new'            => __('Add Project', 'theme-textdomain'),
            'add_new_item'       => __('Add New Project', 'theme-textdomain'),
            'edit_item'          => __('Edit Project', 'theme-textdomain'),
            'new_item'           => __('New Project', 'theme-textdomain'),
            'view_item'          => __('View Project', 'theme-textdomain'),
            'search_items'       => __('Search Projects', 'theme-textdomain'),
            'not_found'          => __('No projects found', 'theme-textdomain'),
        ],
        'public'             => true,
        'has_archive'        => true,
        'menu_icon'          => 'dashicons-portfolio',
        'supports'           => ['title', 'editor', 'thumbnail', 'excerpt', 'custom-fields'],
        'rewrite'            => ['slug' => 'portfolio'],
        'show_in_rest'       => true,
    ]);

    // Portfolio Category
    register_taxonomy('portfolio_category', 'portfolio', [
        'labels' => [
            'name'              => __('Categories', 'theme-textdomain'),
            'singular_name'     => __('Category', 'theme-textdomain'),
            'search_items'      => __('Search Categories', 'theme-textdomain'),
            'all_items'         => __('All Categories', 'theme-textdomain'),
            'parent_item'       => __('Parent Category', 'theme-textdomain'),
            'edit_item'         => __('Edit Category', 'theme-textdomain'),
            'add_new_item'      => __('Add New Category', 'theme-textdomain'),
        ],
        'hierarchical'      => true,
        'public'            => true,
        'rewrite'           => ['slug' => 'portfolio-category'],
        'show_in_rest'      => true,
    ]);
}
add_action('init', 'register_custom_post_types');
```

## Customizer

```php
// inc/customizer.php
function theme_customize_register($wp_customize) {
    // Theme Options Panel
    $wp_customize->add_panel('theme_options', [
        'title'    => __('Theme Options', 'theme-textdomain'),
        'priority' => 30,
    ]);

    // Header Section
    $wp_customize->add_section('header_options', [
        'title' => __('Header', 'theme-textdomain'),
        'panel' => 'theme_options',
    ]);

    // Sticky Header
    $wp_customize->add_setting('sticky_header', [
        'default'           => true,
        'sanitize_callback' => 'wp_validate_boolean',
    ]);

    $wp_customize->add_control('sticky_header', [
        'label'   => __('Enable Sticky Header', 'theme-textdomain'),
        'section' => 'header_options',
        'type'    => 'checkbox',
    ]);

    // Primary Color
    $wp_customize->add_setting('primary_color', [
        'default'           => '#000000',
        'sanitize_callback' => 'sanitize_hex_color',
    ]);

    $wp_customize->add_control(new WP_Customize_Color_Control($wp_customize, 'primary_color', [
        'label'   => __('Primary Color', 'theme-textdomain'),
        'section' => 'colors',
    ]));
}
add_action('customize_register', 'theme_customize_register');

// Output custom CSS
function theme_customizer_css() {
    $primary_color = get_theme_mod('primary_color', '#000000');
    ?>
    <style type="text/css">
        :root {
            --color-primary: <?php echo esc_attr($primary_color); ?>;
        }
    </style>
    <?php
}
add_action('wp_head', 'theme_customizer_css');
```

## AJAX Handlers

```php
// inc/ajax.php
function theme_load_more_posts() {
    check_ajax_referer('theme_nonce', 'nonce');

    $page = isset($_POST['page']) ? intval($_POST['page']) : 1;
    $posts_per_page = isset($_POST['posts_per_page']) ? intval($_POST['posts_per_page']) : 6;

    $args = [
        'post_type'      => 'post',
        'posts_per_page' => $posts_per_page,
        'paged'          => $page,
        'post_status'    => 'publish',
    ];

    $query = new WP_Query($args);

    if ($query->have_posts()) {
        while ($query->have_posts()) {
            $query->the_post();
            get_template_part('template-parts/content/card', 'post');
        }
        wp_reset_postdata();
    }

    wp_die();
}
add_action('wp_ajax_load_more_posts', 'theme_load_more_posts');
add_action('wp_ajax_nopriv_load_more_posts', 'theme_load_more_posts');
```

## Security Best Practices

```php
// Escape output
echo esc_html($text);
echo esc_attr($attribute);
echo esc_url($url);
echo wp_kses_post($html);

// Sanitize input
sanitize_text_field($_POST['field']);
sanitize_email($_POST['email']);
absint($_POST['number']);

// Nonce verification
wp_nonce_field('action_name', 'nonce_name');
check_ajax_referer('action_name', 'nonce_name');

// Capability checks
if (current_user_can('edit_posts')) {
    // Perform action
}
```

## Performance Optimization

```php
// Remove unnecessary features
remove_action('wp_head', 'wp_generator');
remove_action('wp_head', 'wlwmanifest_link');
remove_action('wp_head', 'rsd_link');
remove_action('wp_head', 'wp_shortlink_wp_head');
remove_action('wp_head', 'adjacent_posts_rel_link_wp_head');
remove_action('wp_head', 'print_emoji_detection_script', 7);
remove_action('wp_print_styles', 'print_emoji_styles');

// Disable XML-RPC
add_filter('xmlrpc_enabled', '__return_false');

// Limit post revisions
if (!defined('WP_POST_REVISIONS')) {
    define('WP_POST_REVISIONS', 5);
}

// Optimize heartbeat
add_filter('heartbeat_settings', function($settings) {
    $settings['interval'] = 60;
    return $settings;
});
```

## Template Tags

```php
// Custom template tag for social links
function theme_social_links() {
    $social = [
        'facebook'  => get_theme_mod('social_facebook'),
        'instagram' => get_theme_mod('social_instagram'),
        'twitter'   => get_theme_mod('social_twitter'),
    ];

    foreach ($social as $platform => $url) {
        if ($url) {
            printf(
                '<a href="%s" target="_blank" rel="noopener noreferrer" class="social-link social-link--%s">%s</a>',
                esc_url($url),
                esc_attr($platform),
                esc_html(ucfirst($platform))
            );
        }
    }
}

// Pagination
function theme_pagination() {
    global $wp_query;

    $total_pages = $wp_query->max_num_pages;

    if ($total_pages > 1) {
        echo '<nav class="pagination">';
        echo paginate_links([
            'total'     => $total_pages,
            'current'   => max(1, get_query_var('paged')),
            'prev_text' => '&larr;',
            'next_text' => '&rarr;',
        ]);
        echo '</nav>';
    }
}
```

## Debugging

```php
// Debug mode (wp-config.php)
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);

// Log to debug.log
if (WP_DEBUG) {
    error_log('Debug message: ' . print_r($variable, true));
}

// Query debugging
add_action('wp_footer', function() {
    if (current_user_can('administrator')) {
        global $wpdb;
        echo '<!-- Queries: ' . $wpdb->num_queries . ' -->';
    }
});
```
