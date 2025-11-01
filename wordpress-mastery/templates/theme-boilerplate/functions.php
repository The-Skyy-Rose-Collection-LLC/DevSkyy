<?php
/**
 * WordPress Mastery Boilerplate Functions
 *
 * Production-ready WordPress theme functions following WordPress.com compatibility standards
 *
 * @package WP_Mastery_Boilerplate
 * @version 1.0.0
 * @author DevSkyy WordPress Development Specialist
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
	exit;
}

/**
 * Theme version constant
 */
define('WP_MASTERY_BOILERPLATE_VERSION', '1.0.0');

/**
 * Theme setup
 *
 * Sets up theme defaults and registers support for various WordPress features.
 *
 * @since 1.0.0
 */
function wp_mastery_boilerplate_setup() {
	// Make theme available for translation
	load_theme_textdomain('wp-mastery-boilerplate', get_template_directory() . '/languages');

	// Add default posts and comments RSS feed links to head
	add_theme_support('automatic-feed-links');

	// Let WordPress manage the document title
	add_theme_support('title-tag');

	// Enable support for Post Thumbnails on posts and pages
	add_theme_support('post-thumbnails');

	// Set default thumbnail size
	set_post_thumbnail_size(1200, 9999);

	// Register navigation menus
	register_nav_menus(array(
		'primary' => esc_html__('Primary Menu', 'wp-mastery-boilerplate'),
		'footer'  => esc_html__('Footer Menu', 'wp-mastery-boilerplate'),
	));

	// Switch default core markup to output valid HTML5
	add_theme_support('html5', array(
		'search-form',
		'comment-form',
		'comment-list',
		'gallery',
		'caption',
		'style',
		'script',
	));

	// Add theme support for selective refresh for widgets
	add_theme_support('customize-selective-refresh-widgets');

	// Add support for custom logo
	add_theme_support('custom-logo', array(
		'height'      => 100,
		'width'       => 400,
		'flex-height' => true,
		'flex-width'  => true,
	));

	// Add support for custom background
	add_theme_support('custom-background', array(
		'default-color' => 'ffffff',
	));

	// Add support for custom header
	add_theme_support('custom-header', array(
		'default-image'      => '',
		'default-text-color' => '222222',
		'width'              => 1200,
		'height'             => 300,
		'flex-height'        => true,
		'flex-width'         => true,
	));

	// Add support for editor styles
	add_theme_support('editor-styles');
	add_editor_style('style.css');

	// Add support for responsive embeds
	add_theme_support('responsive-embeds');

	// Add support for wide alignment
	add_theme_support('align-wide');

	// Add support for editor color palette
	add_theme_support('editor-color-palette', array(
		array(
			'name'  => esc_html__('Primary Blue', 'wp-mastery-boilerplate'),
			'slug'  => 'primary-blue',
			'color' => '#0073aa',
		),
		array(
			'name'  => esc_html__('Dark Blue', 'wp-mastery-boilerplate'),
			'slug'  => 'dark-blue',
			'color' => '#005177',
		),
		array(
			'name'  => esc_html__('Dark Gray', 'wp-mastery-boilerplate'),
			'slug'  => 'dark-gray',
			'color' => '#222222',
		),
		array(
			'name'  => esc_html__('Medium Gray', 'wp-mastery-boilerplate'),
			'slug'  => 'medium-gray',
			'color' => '#666666',
		),
	));

	// Add support for editor font sizes
	add_theme_support('editor-font-sizes', array(
		array(
			'name' => esc_html__('Small', 'wp-mastery-boilerplate'),
			'size' => 14,
			'slug' => 'small'
		),
		array(
			'name' => esc_html__('Regular', 'wp-mastery-boilerplate'),
			'size' => 16,
			'slug' => 'regular'
		),
		array(
			'name' => esc_html__('Large', 'wp-mastery-boilerplate'),
			'size' => 20,
			'slug' => 'large'
		),
		array(
			'name' => esc_html__('Extra Large', 'wp-mastery-boilerplate'),
			'size' => 24,
			'slug' => 'extra-large'
		)
	));
}
add_action('after_setup_theme', 'wp_mastery_boilerplate_setup');

/**
 * Set the content width in pixels, based on the theme's design and stylesheet
 *
 * Priority 0 to make it available to lower priority callbacks
 *
 * @since 1.0.0
 * @global int $content_width
 */
function wp_mastery_boilerplate_content_width() {
	$GLOBALS['content_width'] = apply_filters('wp_mastery_boilerplate_content_width', 800);
}
add_action('after_setup_theme', 'wp_mastery_boilerplate_content_width', 0);

/**
 * Enqueue scripts and styles
 *
 * @since 1.0.0
 */
function wp_mastery_boilerplate_scripts() {
	// Enqueue main stylesheet
	wp_enqueue_style(
		'wp-mastery-boilerplate-style',
		get_stylesheet_uri(),
		array(),
		WP_MASTERY_BOILERPLATE_VERSION
	);

	// Enqueue main JavaScript file
	wp_enqueue_script(
		'wp-mastery-boilerplate-script',
		get_template_directory_uri() . '/assets/js/main.js',
		array(),
		WP_MASTERY_BOILERPLATE_VERSION,
		true
	);

	// Enqueue comment reply script on single posts with comments open and threaded comments
	if (is_singular() && comments_open() && get_option('thread_comments')) {
		wp_enqueue_script('comment-reply');
	}
}
add_action('wp_enqueue_scripts', 'wp_mastery_boilerplate_scripts');

/**
 * Custom excerpt length
 *
 * @since 1.0.0
 * @param int $length Excerpt length.
 * @return int Modified excerpt length.
 */
function wp_mastery_boilerplate_excerpt_length($length) {
	return 25;
}
add_filter('excerpt_length', 'wp_mastery_boilerplate_excerpt_length', 999);

/**
 * Custom excerpt more string
 *
 * @since 1.0.0
 * @param string $more "Read More" excerpt string.
 * @return string Modified "Read More" excerpt string.
 */
function wp_mastery_boilerplate_excerpt_more($more) {
	if (is_admin()) {
		return $more;
	}

	return sprintf(
		'&hellip; <a href="%1$s" class="read-more">%2$s</a>',
		esc_url(get_permalink()),
		esc_html__('Continue reading', 'wp-mastery-boilerplate')
	);
}
add_filter('excerpt_more', 'wp_mastery_boilerplate_excerpt_more');

/**
 * Add body classes
 *
 * @since 1.0.0
 * @param array $classes Classes for the body element.
 * @return array Modified body classes.
 */
function wp_mastery_boilerplate_body_classes($classes) {
	// Add class for when there is a custom header image
	if (get_header_image()) {
		$classes[] = 'has-header-image';
	}

	// Add class for when there is a custom logo
	if (has_custom_logo()) {
		$classes[] = 'has-custom-logo';
	}

	// Add class for when there are no widgets in the sidebar
	if (!is_active_sidebar('sidebar-1')) {
		$classes[] = 'no-sidebar';
	}

	return $classes;
}
add_filter('body_class', 'wp_mastery_boilerplate_body_classes');

/**
 * Fallback menu for primary navigation
 *
 * @since 1.0.0
 */
function wp_mastery_boilerplate_fallback_menu() {
	echo '<ul class="fallback-menu">';
	echo '<li><a href="' . esc_url(home_url('/')) . '">' . esc_html__('Home', 'wp-mastery-boilerplate') . '</a></li>';
	
	// Show pages in menu if no custom menu is set
	$pages = get_pages(array(
		'sort_column' => 'menu_order',
		'number' => 5,
	));
	
	foreach ($pages as $page) {
		echo '<li><a href="' . esc_url(get_permalink($page->ID)) . '">' . esc_html($page->post_title) . '</a></li>';
	}
	
	echo '</ul>';
}

/**
 * Safe function to get theme option with fallback
 *
 * @since 1.0.0
 * @param string $option_name Option name.
 * @param mixed  $default Default value.
 * @return mixed Option value or default.
 */
function wp_mastery_boilerplate_get_option($option_name, $default = '') {
	$option_value = get_theme_mod($option_name, $default);
	
	// Sanitize based on option type
	if (is_string($option_value)) {
		return sanitize_text_field($option_value);
	}
	
	return $option_value;
}

/**
 * Display posted on date
 *
 * @since 1.0.0
 */
function wp_mastery_boilerplate_posted_on() {
	$time_string = '<time class="entry-date published updated" datetime="%1$s">%2$s</time>';
	
	if (get_the_time('U') !== get_the_modified_time('U')) {
		$time_string = '<time class="entry-date published" datetime="%1$s">%2$s</time><time class="updated" datetime="%3$s">%4$s</time>';
	}

	$time_string = sprintf(
		$time_string,
		esc_attr(get_the_date(DATE_W3C)),
		esc_html(get_the_date()),
		esc_attr(get_the_modified_date(DATE_W3C)),
		esc_html(get_the_modified_date())
	);

	printf(
		'<span class="posted-on">%1$s <a href="%2$s" rel="bookmark">%3$s</a></span>',
		esc_html__('Posted on', 'wp-mastery-boilerplate'),
		esc_url(get_permalink()),
		$time_string
	);
}

/**
 * Display post author
 *
 * @since 1.0.0
 */
function wp_mastery_boilerplate_posted_by() {
	printf(
		'<span class="byline">%1$s <span class="author vcard"><a class="url fn n" href="%2$s">%3$s</a></span></span>',
		esc_html__('by', 'wp-mastery-boilerplate'),
		esc_url(get_author_posts_url(get_the_author_meta('ID'))),
		esc_html(get_the_author())
	);
}

/**
 * Add custom classes to navigation menu items
 *
 * @since 1.0.0
 * @param array  $classes The CSS classes that are applied to the menu item's <li> element.
 * @param object $item The current menu item.
 * @return array Modified menu item classes.
 */
function wp_mastery_boilerplate_nav_menu_css_class($classes, $item) {
	// Add custom class for external links
	if (strpos($item->url, home_url()) === false && strpos($item->url, 'http') === 0) {
		$classes[] = 'external-link';
	}
	
	return $classes;
}
add_filter('nav_menu_css_class', 'wp_mastery_boilerplate_nav_menu_css_class', 10, 2);

/**
 * WordPress.com compatibility check
 *
 * @since 1.0.0
 * @return bool True if running on WordPress.com.
 */
function wp_mastery_boilerplate_is_wpcom() {
	return defined('IS_WPCOM') && IS_WPCOM;
}

/**
 * Theme activation hook
 *
 * @since 1.0.0
 */
function wp_mastery_boilerplate_activation() {
	// Flush rewrite rules
	flush_rewrite_rules();
	
	// Set default theme options
	if (!get_theme_mod('custom_logo')) {
		// Set default customizer values if needed
	}
}
add_action('after_switch_theme', 'wp_mastery_boilerplate_activation');

/**
 * Theme deactivation hook
 *
 * @since 1.0.0
 */
function wp_mastery_boilerplate_deactivation() {
	// Clean up theme-specific options if needed
	flush_rewrite_rules();
}
add_action('switch_theme', 'wp_mastery_boilerplate_deactivation');
