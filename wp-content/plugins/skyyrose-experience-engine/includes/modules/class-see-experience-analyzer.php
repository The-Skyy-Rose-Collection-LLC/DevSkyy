<?php
/**
 * Experience Analyzer — Privacy-first behavioral tracking pipeline.
 *
 * Tracks scroll depth, hover targets, click paths, time-on-page, and exit
 * intent without PII or cookies. Feeds aggregated data to the admin
 * dashboard and optionally relays to the FastAPI backend for ML.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Experience_Analyzer {

	private SEE_Plugin $plugin;

	public function __construct( SEE_Plugin $plugin ) {
		$this->plugin = $plugin;
	}

	public function register( SEE_Loader $loader ): void {
		$loader->add_action( 'wp_enqueue_scripts', $this, 'enqueue_assets', 52 );

		// Schedule daily rollup cleanup.
		if ( ! wp_next_scheduled( 'see_analytics_rollup' ) ) {
			wp_schedule_event( time(), 'daily', 'see_analytics_rollup' );
		}
		$loader->add_action( 'see_analytics_rollup', $this, 'cleanup_old_data' );
	}

	public function enqueue_assets(): void {
		if ( is_admin() ) {
			return;
		}

		wp_enqueue_script(
			'see-experience-analyzer',
			SEE_URI . 'public/js/see-experience-analyzer.js',
			array( 'see-core' ),
			SEE_VERSION,
			true
		);
	}

	/**
	 * Store a batch of analytics events.
	 *
	 * @param array $events Array of event objects.
	 * @return int Number of events stored.
	 */
	public function store_events( array $events ): int {
		global $wpdb;
		$table   = $wpdb->prefix . 'see_analytics';
		$stored  = 0;

		foreach ( $events as $event ) {
			$event_type   = sanitize_text_field( $event['type'] ?? '' );
			$event_target = sanitize_text_field( $event['target'] ?? '' );
			$page_type    = sanitize_text_field( $event['pageType'] ?? '' );
			$collection   = sanitize_text_field( $event['collection'] ?? '' );
			$value        = floatval( $event['value'] ?? 0 );

			if ( empty( $event_type ) ) {
				continue;
			}

			// Attempt to increment existing rollup row for today.
			$today   = gmdate( 'Y-m-d' );
			$updated = $wpdb->query(
				$wpdb->prepare(
					"UPDATE {$table}
					 SET event_count = event_count + 1, event_value = event_value + %f
					 WHERE event_date = %s AND event_type = %s AND event_target = %s
					   AND page_type = %s AND collection_slug = %s",
					$value,
					$today,
					$event_type,
					$event_target,
					$page_type,
					$collection
				)
			);

			if ( 0 === $updated ) {
				$wpdb->insert(
					$table,
					array(
						'event_date'      => $today,
						'event_type'      => $event_type,
						'event_target'    => $event_target,
						'page_type'       => $page_type,
						'collection_slug' => $collection,
						'event_count'     => 1,
						'event_value'     => $value,
					),
					array( '%s', '%s', '%s', '%s', '%s', '%d', '%f' )
				);
			}

			$stored++;
		}

		return $stored;
	}

	/**
	 * Get analytics summary for dashboard display.
	 *
	 * @param int $days Number of days to look back.
	 * @return array Summary data.
	 */
	public function get_summary( int $days = 7 ): array {
		global $wpdb;
		$table = $wpdb->prefix . 'see_analytics';
		$since = gmdate( 'Y-m-d', strtotime( "-{$days} days" ) );

		$top_events = $wpdb->get_results(
			$wpdb->prepare(
				"SELECT event_type, SUM(event_count) as total_count, SUM(event_value) as total_value
				 FROM {$table} WHERE event_date >= %s
				 GROUP BY event_type ORDER BY total_count DESC LIMIT 10",
				$since
			),
			ARRAY_A
		);

		$collection_engagement = $wpdb->get_results(
			$wpdb->prepare(
				"SELECT collection_slug, SUM(event_count) as total_count
				 FROM {$table} WHERE event_date >= %s AND collection_slug != ''
				 GROUP BY collection_slug ORDER BY total_count DESC",
				$since
			),
			ARRAY_A
		);

		$daily_trend = $wpdb->get_results(
			$wpdb->prepare(
				"SELECT event_date, SUM(event_count) as total_count
				 FROM {$table} WHERE event_date >= %s
				 GROUP BY event_date ORDER BY event_date ASC",
				$since
			),
			ARRAY_A
		);

		return array(
			'top_events'             => $top_events ?: array(),
			'collection_engagement'  => $collection_engagement ?: array(),
			'daily_trend'            => $daily_trend ?: array(),
			'period_days'            => $days,
		);
	}

	/**
	 * Remove analytics data older than 90 days.
	 */
	public function cleanup_old_data(): void {
		global $wpdb;
		$table  = $wpdb->prefix . 'see_analytics';
		$cutoff = gmdate( 'Y-m-d', strtotime( '-90 days' ) );

		$wpdb->query(
			$wpdb->prepare(
				"DELETE FROM {$table} WHERE event_date < %s",
				$cutoff
			)
		);
	}
}
