<?php
/**
 * Admin Dashboard — Main view.
 *
 * Displays: Module status, analytics overview, Core Web Vitals,
 * Design Narrative pipeline (submit/accept/decline), and directive history.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$settings       = $this->plugin->get_settings();
$active_modules = $this->plugin->get_active_modules();
$directives     = $this->plugin->get_active_directives();
$history        = $settings['narrative_history'] ?? array();
$is_flagship    = $this->plugin->is_flagship();

$fastapi = new SEE_Fastapi_Client( $this->plugin );
$api_available = $fastapi->is_available();
?>

<div class="wrap see-dashboard">
	<h1 class="see-dashboard__title">
		SkyyRose Experience Engine
		<span class="see-version"><?php echo esc_html( SEE_VERSION ); ?></span>
	</h1>

	<!-- ── Status Bar ── -->
	<div class="see-status-bar">
		<div class="see-status-item <?php echo $is_flagship ? 'see-status--active' : 'see-status--standalone'; ?>">
			<span class="see-status-dot"></span>
			<?php echo $is_flagship ? 'Enhanced Mode (skyyrose-flagship)' : 'Standalone Mode'; ?>
		</div>
		<div class="see-status-item <?php echo $api_available ? 'see-status--active' : 'see-status--offline'; ?>">
			<span class="see-status-dot"></span>
			FastAPI Backend: <?php echo $api_available ? 'Connected' : 'Offline (client-side fallback)'; ?>
		</div>
		<div class="see-status-item see-status--active">
			<span class="see-status-dot"></span>
			<?php echo count( $active_modules ); ?> Modules Active
		</div>
	</div>

	<div class="see-grid">
		<!-- ── Active Modules ── -->
		<div class="see-card see-card--modules">
			<h2>Active Modules</h2>
			<div class="see-module-list">
				<?php
				$all_modules = array(
					'experience_analyzer'  => array( 'label' => 'Experience Analyzer', 'icon' => 'chart-bar', 'desc' => 'Behavioral tracking pipeline' ),
					'scroll_storyteller'   => array( 'label' => 'Scroll Storyteller', 'icon' => 'book', 'desc' => 'Scroll-driven product reveals' ),
					'smart_showcase'       => array( 'label' => 'Smart Showcase', 'icon' => 'layout', 'desc' => '3D tilt cards, quick view' ),
					'personalization'      => array( 'label' => 'Personalization', 'icon' => 'admin-users', 'desc' => 'Affinity scoring, Curated For You' ),
					'micro_interactions'   => array( 'label' => 'Micro-Interactions', 'icon' => 'controls-play', 'desc' => 'Cart fly, wishlist burst, toasts' ),
					'performance_guardian' => array( 'label' => 'Performance Guardian', 'icon' => 'performance', 'desc' => 'Animation budget, CLS prevention' ),
					'brand_atmosphere'     => array( 'label' => 'Brand Atmosphere', 'icon' => 'art', 'desc' => 'Particles, cursor, cinematic mode' ),
				);

				foreach ( $all_modules as $slug => $info ) :
					$is_active = in_array( $slug, $active_modules, true );
				?>
				<div class="see-module-item <?php echo $is_active ? 'see-module--active' : 'see-module--inactive'; ?>">
					<span class="dashicons dashicons-<?php echo esc_attr( $info['icon'] ); ?>"></span>
					<div class="see-module-info">
						<strong><?php echo esc_html( $info['label'] ); ?></strong>
						<small><?php echo esc_html( $info['desc'] ); ?></small>
					</div>
					<span class="see-module-badge"><?php echo $is_active ? 'Active' : 'Off'; ?></span>
				</div>
				<?php endforeach; ?>
			</div>
		</div>

		<!-- ── Analytics Overview ── -->
		<div class="see-card see-card--analytics">
			<h2>Engagement Analytics <small>(7 days)</small></h2>
			<div id="see-analytics-loading" class="see-loading">Loading analytics data...</div>
			<div id="see-analytics-content" style="display:none;">
				<div class="see-analytics-grid">
					<div class="see-metric">
						<span class="see-metric-value" id="see-metric-events">--</span>
						<span class="see-metric-label">Total Events</span>
					</div>
					<div class="see-metric">
						<span class="see-metric-value" id="see-metric-collections">--</span>
						<span class="see-metric-label">Collections Engaged</span>
					</div>
					<div class="see-metric">
						<span class="see-metric-value" id="see-metric-top-event">--</span>
						<span class="see-metric-label">Top Event Type</span>
					</div>
				</div>
				<div id="see-collection-chart" class="see-chart"></div>
				<div id="see-daily-trend" class="see-chart"></div>
			</div>
		</div>

		<!-- ── Design Narrative Pipeline ── -->
		<div class="see-card see-card--narrative see-card--full">
			<h2>Design Narratives</h2>
			<p class="see-card-desc">
				Feed design directives to the engine. Describe the experience you want —
				the engine will accept or decline based on active modules and conflicts.
			</p>

			<form id="see-narrative-form" class="see-narrative-form">
				<div class="see-form-row">
					<textarea id="see-narrative-input" rows="3"
						placeholder="e.g., Emphasize Black Rose collection this week. Gothic mood, silver accents, increase scroll storytelling depth on product pages..."
					></textarea>
				</div>
				<div class="see-form-row see-form-row--inline">
					<label>
						Target Module:
						<select id="see-narrative-target">
							<option value="all">All Modules</option>
							<?php foreach ( $all_modules as $slug => $info ) : ?>
							<option value="<?php echo esc_attr( $slug ); ?>"><?php echo esc_html( $info['label'] ); ?></option>
							<?php endforeach; ?>
							<option value="theme_bridge">Theme Bridge (Engines)</option>
						</select>
					</label>
					<label>
						Priority:
						<select id="see-narrative-priority">
							<option value="3">Low (3)</option>
							<option value="5" selected>Normal (5)</option>
							<option value="7">High (7)</option>
							<option value="10">Critical (10)</option>
						</select>
					</label>
					<label>
						Expires:
						<input type="date" id="see-narrative-expires" min="<?php echo esc_attr( gmdate( 'Y-m-d' ) ); ?>" />
					</label>
					<button type="submit" class="button button-primary">Submit Narrative</button>
				</div>
			</form>

			<div id="see-narrative-result" class="see-narrative-result" style="display:none;"></div>

			<!-- Active Directives -->
			<div class="see-directives">
				<h3>Active Directives</h3>
				<div id="see-directives-list">
					<?php if ( empty( $directives ) ) : ?>
						<p class="see-empty">No active directives. Submit a narrative above to guide the engine.</p>
					<?php else : ?>
						<?php foreach ( $directives as $d ) : ?>
						<div class="see-directive see-directive--accepted" data-id="<?php echo esc_attr( $d['id'] ?? '' ); ?>">
							<div class="see-directive-content">
								<span class="see-directive-badge">Accepted</span>
								<p><?php echo esc_html( $d['description'] ?? '' ); ?></p>
								<small>Target: <?php echo esc_html( $d['target'] ?? 'all' ); ?> | Priority: <?php echo intval( $d['priority'] ?? 5 ); ?>
								<?php if ( ! empty( $d['expires'] ) ) : ?> | Expires: <?php echo esc_html( $d['expires'] ); ?><?php endif; ?>
								<?php if ( ! empty( $d['ai_source'] ) ) : ?> | AI-Enhanced<?php endif; ?>
								</small>
							</div>
							<button class="see-directive-remove button-link-delete" data-id="<?php echo esc_attr( $d['id'] ?? '' ); ?>">Remove</button>
						</div>
						<?php endforeach; ?>
					<?php endif; ?>
				</div>
			</div>

			<!-- Narrative History -->
			<details class="see-history">
				<summary>Directive History (<?php echo count( $history ); ?> events)</summary>
				<div class="see-history-list">
					<?php foreach ( array_reverse( $history ) as $event ) : ?>
					<div class="see-history-item see-history--<?php echo esc_attr( $event['action'] ?? '' ); ?>">
						<span class="see-history-badge"><?php echo esc_html( ucfirst( $event['action'] ?? '' ) ); ?></span>
						<span class="see-history-detail"><?php echo esc_html( $event['detail'] ?? '' ); ?></span>
						<small><?php echo esc_html( $event['timestamp'] ?? '' ); ?></small>
					</div>
					<?php endforeach; ?>
				</div>
			</details>
		</div>

		<?php if ( $is_flagship ) : ?>
		<!-- ── Theme Engine Status ── -->
		<div class="see-card see-card--engines">
			<h2>Theme Engine Orchestration</h2>
			<p class="see-card-desc">These are your existing theme engines, now managed by the Experience Engine.</p>
			<div class="see-engine-list">
				<?php
				$engines = array(
					'aurora_engine'             => 'Aurora — Ambient engagement, CTA shimmer, 3D card tilt',
					'magnetic_obsidian'         => 'Magnetic Obsidian — 3D card effects, exit-intent, A/B variants',
					'conversion_engine'         => 'Conversion Engine — Social proof toasts, urgency timers, scarcity',
					'adaptive_personalization'  => 'Adaptive Personalization — Behavioral scoring, Your Picks drawer',
					'journey_gamification'      => 'Journey Gamification — Room tracking, achievements, rewards',
					'momentum_commerce'         => 'Momentum Commerce — Scroll-driven storytelling, velocity',
					'velocity_scroll'           => 'Velocity Scroll — Apple-style progressive reveals',
					'pulse_engine'              => 'Pulse Engine — Unified conversion infrastructure',
					'the_pulse'                 => 'The Pulse — Real-time social proof & urgency',
					'social_proof'              => 'Social Proof — Purchase notifications, live viewers',
				);

				foreach ( $engines as $slug => $desc ) :
				?>
				<div class="see-engine-item">
					<span class="see-engine-label"><?php echo esc_html( $desc ); ?></span>
					<span class="see-engine-badge">Contextual</span>
				</div>
				<?php endforeach; ?>
			</div>
		</div>
		<?php endif; ?>
	</div>
</div>
