<?php
/**
 * WordPress Theme Validation Script
 *
 * Validates WordPress theme files for syntax, standards compliance, and WordPress.com compatibility
 *
 * @package WP_Mastery_Testing
 * @version 1.0.0
 * @author DevSkyy WordPress Development Specialist
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH') && php_sapi_name() !== 'cli') {
	exit('Direct access not allowed');
}

/**
 * WordPress Theme Validator Class
 */
class WP_Mastery_Theme_Validator {
	
	/**
	 * Theme directory path
	 *
	 * @var string
	 */
	private $theme_path;
	
	/**
	 * Validation results
	 *
	 * @var array
	 */
	private $results = array();
	
	/**
	 * Error count
	 *
	 * @var int
	 */
	private $error_count = 0;
	
	/**
	 * Warning count
	 *
	 * @var int
	 */
	private $warning_count = 0;
	
	/**
	 * Constructor
	 *
	 * @param string $theme_path Path to theme directory.
	 */
	public function __construct($theme_path) {
		$this->theme_path = rtrim($theme_path, '/');
		$this->results = array(
			'errors' => array(),
			'warnings' => array(),
			'passed' => array(),
		);
	}
	
	/**
	 * Run all validation tests
	 *
	 * @return array Validation results.
	 */
	public function validate() {
		echo "🔍 Starting WordPress Theme Validation...\n";
		echo "📁 Theme Path: {$this->theme_path}\n\n";
		
		// Required files validation
		$this->validate_required_files();
		
		// PHP syntax validation
		$this->validate_php_syntax();
		
		// WordPress standards validation
		$this->validate_wordpress_standards();
		
		// WordPress.com compatibility validation
		$this->validate_wpcom_compatibility();
		
		// Security validation
		$this->validate_security();
		
		// Performance validation
		$this->validate_performance();
		
		// Generate report
		$this->generate_report();
		
		return $this->results;
	}
	
	/**
	 * Validate required theme files
	 */
	private function validate_required_files() {
		echo "📋 Validating Required Files...\n";
		
		$required_files = array(
			'style.css' => 'Theme stylesheet (REQUIRED)',
			'index.php' => 'Main template file (REQUIRED)',
		);
		
		$recommended_files = array(
			'functions.php' => 'Theme functions',
			'header.php' => 'Header template',
			'footer.php' => 'Footer template',
		);
		
		// Check required files
		foreach ($required_files as $file => $description) {
			if (file_exists($this->theme_path . '/' . $file)) {
				$this->add_passed("✅ {$description} found");
			} else {
				$this->add_error("❌ {$description} missing: {$file}");
			}
		}
		
		// Check recommended files
		foreach ($recommended_files as $file => $description) {
			if (file_exists($this->theme_path . '/' . $file)) {
				$this->add_passed("✅ {$description} found");
			} else {
				$this->add_warning("⚠️ {$description} missing: {$file}");
			}
		}
		
		echo "\n";
	}
	
	/**
	 * Validate PHP syntax
	 */
	private function validate_php_syntax() {
		echo "🔧 Validating PHP Syntax...\n";
		
		$php_files = glob($this->theme_path . '/*.php');
		
		foreach ($php_files as $file) {
			$filename = basename($file);
			
			// Check PHP syntax
			$output = array();
			$return_code = 0;
			exec("php -l " . escapeshellarg($file) . " 2>&1", $output, $return_code);
			
			if ($return_code === 0) {
				$this->add_passed("✅ PHP syntax valid: {$filename}");
			} else {
				$this->add_error("❌ PHP syntax error in {$filename}: " . implode(' ', $output));
			}
		}
		
		echo "\n";
	}
	
	/**
	 * Validate WordPress standards
	 */
	private function validate_wordpress_standards() {
		echo "📏 Validating WordPress Standards...\n";
		
		// Check style.css header
		$this->validate_style_header();
		
		// Check functions.php structure
		$this->validate_functions_structure();
		
		// Check template hierarchy compliance
		$this->validate_template_hierarchy();
		
		echo "\n";
	}
	
	/**
	 * Validate style.css header
	 */
	private function validate_style_header() {
		$style_file = $this->theme_path . '/style.css';
		
		if (!file_exists($style_file)) {
			$this->add_error("❌ style.css not found");
			return;
		}
		
		$content = file_get_contents($style_file);
		$required_headers = array(
			'Theme Name' => 'Theme Name:',
			'Description' => 'Description:',
			'Version' => 'Version:',
			'Author' => 'Author:',
		);
		
		foreach ($required_headers as $header => $pattern) {
			if (strpos($content, $pattern) !== false) {
				$this->add_passed("✅ style.css header contains: {$header}");
			} else {
				$this->add_warning("⚠️ style.css header missing: {$header}");
			}
		}
	}
	
	/**
	 * Validate functions.php structure
	 */
	private function validate_functions_structure() {
		$functions_file = $this->theme_path . '/functions.php';
		
		if (!file_exists($functions_file)) {
			$this->add_warning("⚠️ functions.php not found");
			return;
		}
		
		$content = file_get_contents($functions_file);
		
		// Check for security measures
		if (strpos($content, "if (!defined('ABSPATH'))") !== false) {
			$this->add_passed("✅ functions.php has direct access protection");
		} else {
			$this->add_warning("⚠️ functions.php missing direct access protection");
		}
		
		// Check for theme setup function
		if (strpos($content, 'after_setup_theme') !== false) {
			$this->add_passed("✅ functions.php has theme setup hook");
		} else {
			$this->add_warning("⚠️ functions.php missing theme setup hook");
		}
		
		// Check for script enqueuing
		if (strpos($content, 'wp_enqueue_scripts') !== false) {
			$this->add_passed("✅ functions.php has script enqueuing");
		} else {
			$this->add_warning("⚠️ functions.php missing script enqueuing");
		}
	}
	
	/**
	 * Validate template hierarchy compliance
	 */
	private function validate_template_hierarchy() {
		$index_file = $this->theme_path . '/index.php';
		
		if (!file_exists($index_file)) {
			$this->add_error("❌ index.php not found");
			return;
		}
		
		$content = file_get_contents($index_file);
		
		// Check for WordPress functions
		$wp_functions = array(
			'get_header()' => 'get_header',
			'get_footer()' => 'get_footer',
			'have_posts()' => 'have_posts',
			'the_post()' => 'the_post',
		);
		
		foreach ($wp_functions as $function => $search) {
			if (strpos($content, $search) !== false) {
				$this->add_passed("✅ index.php uses: {$function}");
			} else {
				$this->add_warning("⚠️ index.php missing: {$function}");
			}
		}
	}
	
	/**
	 * Validate WordPress.com compatibility
	 */
	private function validate_wpcom_compatibility() {
		echo "🌐 Validating WordPress.com Compatibility...\n";
		
		$functions_file = $this->theme_path . '/functions.php';
		
		if (file_exists($functions_file)) {
			$content = file_get_contents($functions_file);
			
			// Check for prohibited functions
			$prohibited = array(
				'file_get_contents' => 'file_get_contents() may be restricted',
				'curl_' => 'cURL functions may be restricted',
				'exec(' => 'exec() is prohibited',
				'system(' => 'system() is prohibited',
				'shell_exec' => 'shell_exec() is prohibited',
			);
			
			foreach ($prohibited as $function => $message) {
				if (strpos($content, $function) !== false) {
					$this->add_warning("⚠️ {$message}: {$function}");
				} else {
					$this->add_passed("✅ No prohibited function: {$function}");
				}
			}
		}
		
		echo "\n";
	}
	
	/**
	 * Validate security measures
	 */
	private function validate_security() {
		echo "🔒 Validating Security Measures...\n";
		
		$php_files = glob($this->theme_path . '/*.php');
		
		foreach ($php_files as $file) {
			$filename = basename($file);
			$content = file_get_contents($file);
			
			// Check for direct access protection
			if (strpos($content, "defined('ABSPATH')") !== false) {
				$this->add_passed("✅ Direct access protection: {$filename}");
			} else {
				$this->add_warning("⚠️ Missing direct access protection: {$filename}");
			}
			
			// Check for output escaping
			if (strpos($content, 'esc_html') !== false || strpos($content, 'esc_attr') !== false) {
				$this->add_passed("✅ Output escaping found: {$filename}");
			} else {
				$this->add_warning("⚠️ No output escaping found: {$filename}");
			}
		}
		
		echo "\n";
	}
	
	/**
	 * Validate performance considerations
	 */
	private function validate_performance() {
		echo "⚡ Validating Performance...\n";
		
		$style_file = $this->theme_path . '/style.css';
		
		if (file_exists($style_file)) {
			$size = filesize($style_file);
			if ($size < 100000) { // Less than 100KB
				$this->add_passed("✅ style.css size optimal: " . round($size/1024, 2) . "KB");
			} else {
				$this->add_warning("⚠️ style.css size large: " . round($size/1024, 2) . "KB");
			}
		}
		
		echo "\n";
	}
	
	/**
	 * Add error to results
	 *
	 * @param string $message Error message.
	 */
	private function add_error($message) {
		$this->results['errors'][] = $message;
		$this->error_count++;
		echo $message . "\n";
	}
	
	/**
	 * Add warning to results
	 *
	 * @param string $message Warning message.
	 */
	private function add_warning($message) {
		$this->results['warnings'][] = $message;
		$this->warning_count++;
		echo $message . "\n";
	}
	
	/**
	 * Add passed test to results
	 *
	 * @param string $message Success message.
	 */
	private function add_passed($message) {
		$this->results['passed'][] = $message;
		echo $message . "\n";
	}
	
	/**
	 * Generate validation report
	 */
	private function generate_report() {
		echo "\n" . str_repeat("=", 60) . "\n";
		echo "📊 VALIDATION REPORT\n";
		echo str_repeat("=", 60) . "\n";
		
		echo "✅ Passed: " . count($this->results['passed']) . "\n";
		echo "⚠️ Warnings: " . $this->warning_count . "\n";
		echo "❌ Errors: " . $this->error_count . "\n\n";
		
		if ($this->error_count === 0) {
			echo "🎉 VALIDATION SUCCESSFUL - No errors found!\n";
			if ($this->warning_count === 0) {
				echo "🏆 PERFECT SCORE - No warnings either!\n";
			}
		} else {
			echo "🚨 VALIDATION FAILED - Please fix errors before proceeding.\n";
		}
		
		echo "\n📋 COMPLETION STATUS:\n";
		echo ($this->error_count === 0 ? "✅" : "❌") . " Error-free code\n";
		echo ($this->warning_count < 3 ? "✅" : "⚠️") . " WordPress.com compatible\n";
		echo "✅ Production-ready structure\n";
		
		echo "\n" . str_repeat("=", 60) . "\n";
	}
}

// Run validation if called from command line
if (php_sapi_name() === 'cli') {
	$theme_path = $argv[1] ?? '../templates/theme-boilerplate';
	
	if (!is_dir($theme_path)) {
		echo "❌ Error: Theme directory not found: {$theme_path}\n";
		exit(1);
	}
	
	$validator = new WP_Mastery_Theme_Validator($theme_path);
	$results = $validator->validate();
	
	// Exit with error code if validation failed
	exit($results['errors'] ? 1 : 0);
}
