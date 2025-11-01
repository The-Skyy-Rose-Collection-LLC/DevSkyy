<?php
/**
 * Uninstall script
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('WP_UNINSTALL_PLUGIN')) {
    exit;
}

// Security check
if (!current_user_can('activate_plugins')) {
    exit;
}

// Load dependencies
require_once plugin_dir_path(__FILE__) . 'includes/class-skyy-rose-deactivator.php';

// Run uninstall
SkyyRoseDeactivator::uninstall();