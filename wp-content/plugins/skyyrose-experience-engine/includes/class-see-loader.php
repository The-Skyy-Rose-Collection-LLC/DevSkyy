<?php
/**
 * Hook/filter registration dispatcher.
 *
 * Collects all add_action/add_filter calls and executes them in run().
 * Follows the WordPress Plugin Boilerplate pattern.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Loader {

	/** @var array */
	private array $actions = array();

	/** @var array */
	private array $filters = array();

	public function add_action( string $hook, object $component, string $callback, int $priority = 10, int $args = 1 ): void {
		$this->actions[] = compact( 'hook', 'component', 'callback', 'priority', 'args' );
	}

	public function add_filter( string $hook, object $component, string $callback, int $priority = 10, int $args = 1 ): void {
		$this->filters[] = compact( 'hook', 'component', 'callback', 'priority', 'args' );
	}

	public function run(): void {
		foreach ( $this->actions as $hook ) {
			add_action(
				$hook['hook'],
				array( $hook['component'], $hook['callback'] ),
				$hook['priority'],
				$hook['args']
			);
		}

		foreach ( $this->filters as $hook ) {
			add_filter(
				$hook['hook'],
				array( $hook['component'], $hook['callback'] ),
				$hook['priority'],
				$hook['args']
			);
		}
	}
}
