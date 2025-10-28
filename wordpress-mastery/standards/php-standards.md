# WordPress PHP Development Standards

## 🎯 VERIFIED WORDPRESS CODING STANDARDS

### ✅ FUNDAMENTAL REQUIREMENTS

#### **PHP Version Compatibility**
- **Minimum:** PHP 8.1+
- **Current Environment:** PHP 8.4.12 ✅
- **WordPress.com Compatible:** Yes ✅

#### **WordPress Coding Standards Compliance**
- Based on PSR-12 with WordPress modifications
- WordPress-specific naming conventions
- Proper indentation (tabs, not spaces)
- Consistent brace placement

### 🔒 SECURITY STANDARDS

#### **Data Sanitization (MANDATORY)**
```php
// Input sanitization
$user_input = sanitize_text_field($_POST['user_input']);
$email = sanitize_email($_POST['email']);
$url = esc_url_raw($_POST['url']);

// Output escaping
echo esc_html($user_data);
echo esc_attr($attribute_value);
echo esc_url($link_url);
```

#### **Nonce Verification (MANDATORY)**
```php
// Creating nonces
wp_nonce_field('my_action_nonce', 'my_nonce_field');

// Verifying nonces
if (!wp_verify_nonce($_POST['my_nonce_field'], 'my_action_nonce')) {
    wp_die('Security check failed');
}
```

#### **Capability Checks (MANDATORY)**
```php
// Check user capabilities
if (!current_user_can('manage_options')) {
    wp_die('Insufficient permissions');
}
```

### 🏗️ THEME STRUCTURE STANDARDS

#### **Theme File Organization**
```
theme-name/
├── style.css (REQUIRED)
├── index.php (REQUIRED)
├── functions.php (REQUIRED)
├── header.php
├── footer.php
├── sidebar.php
├── single.php
├── page.php
├── archive.php
├── search.php
├── 404.php
├── comments.php
├── assets/
│   ├── css/
│   ├── js/
│   └── images/
├── template-parts/
├── inc/
└── languages/
```

#### **Functions.php Structure**
```php
<?php
/**
 * Theme Name Functions
 * 
 * @package ThemeName
 * @version 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Theme setup
 */
function theme_name_setup() {
    // Add theme support
    add_theme_support('post-thumbnails');
    add_theme_support('title-tag');
    add_theme_support('html5', array(
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
        'style',
        'script',
    ));
    
    // Register navigation menus
    register_nav_menus(array(
        'primary' => __('Primary Menu', 'theme-textdomain'),
        'footer'  => __('Footer Menu', 'theme-textdomain'),
    ));
}
add_action('after_setup_theme', 'theme_name_setup');

/**
 * Enqueue scripts and styles
 */
function theme_name_scripts() {
    // Enqueue styles
    wp_enqueue_style(
        'theme-name-style',
        get_stylesheet_uri(),
        array(),
        wp_get_theme()->get('Version')
    );
    
    // Enqueue scripts
    wp_enqueue_script(
        'theme-name-script',
        get_template_directory_uri() . '/assets/js/main.js',
        array(),
        wp_get_theme()->get('Version'),
        true
    );
}
add_action('wp_enqueue_scripts', 'theme_name_scripts');
```

### 🎯 WORDPRESS.COM COMPATIBILITY REQUIREMENTS

#### **Prohibited Functions/Features**
- Custom post types (use plugins instead)
- Custom database tables
- File system writes
- External API calls without proper error handling
- PHP sessions
- Custom cron jobs

#### **Required Theme Features**
```php
// REQUIRED theme supports
add_theme_support('post-thumbnails');
add_theme_support('title-tag');
add_theme_support('html5');
add_theme_support('custom-logo');

// RECOMMENDED theme supports
add_theme_support('custom-background');
add_theme_support('custom-header');
add_theme_support('editor-styles');
add_theme_support('responsive-embeds');
```

### 🔍 VALIDATION STANDARDS

#### **PHP Syntax Validation**
```bash
# Validate PHP syntax
php -l filename.php

# WordPress Coding Standards check
phpcs --standard=WordPress filename.php
```

#### **WordPress.com Compatibility Check**
```php
// Check for WordPress.com environment
if (defined('IS_WPCOM') && IS_WPCOM) {
    // WordPress.com specific code
}
```

### 📊 PERFORMANCE STANDARDS

#### **Database Query Optimization**
```php
// Use WP_Query properly
$query = new WP_Query(array(
    'post_type' => 'post',
    'posts_per_page' => 10,
    'meta_query' => array(
        array(
            'key' => 'featured',
            'value' => 'yes',
            'compare' => '='
        )
    )
));

// Always reset post data
wp_reset_postdata();
```

#### **Caching Best Practices**
```php
// Use transients for expensive operations
$cached_data = get_transient('expensive_operation');
if (false === $cached_data) {
    $cached_data = expensive_operation();
    set_transient('expensive_operation', $cached_data, HOUR_IN_SECONDS);
}
```

### 🚨 ERROR HANDLING STANDARDS

#### **Comprehensive Error Handling**
```php
/**
 * Safe function execution with error handling
 */
function theme_safe_function($param) {
    try {
        // Validate input
        if (empty($param)) {
            return new WP_Error('invalid_param', 'Parameter cannot be empty');
        }
        
        // Sanitize input
        $param = sanitize_text_field($param);
        
        // Execute function logic
        $result = some_operation($param);
        
        // Validate result
        if (is_wp_error($result)) {
            error_log('Theme function error: ' . $result->get_error_message());
            return false;
        }
        
        return $result;
        
    } catch (Exception $e) {
        error_log('Theme exception: ' . $e->getMessage());
        return false;
    }
}
```

### 📝 DOCUMENTATION STANDARDS

#### **Function Documentation**
```php
/**
 * Function description
 *
 * @since 1.0.0
 * @param string $param Parameter description
 * @return mixed Return value description
 */
function theme_function($param) {
    // Function implementation
}
```

### ✅ VALIDATION CHECKLIST

- [ ] PHP syntax validation passed
- [ ] WordPress Coding Standards compliant
- [ ] Security measures implemented
- [ ] WordPress.com compatibility verified
- [ ] Performance optimized
- [ ] Error handling comprehensive
- [ ] Documentation complete
- [ ] Automated tests passing

---

**STATUS:** PHP standards established and ready for implementation validation.
