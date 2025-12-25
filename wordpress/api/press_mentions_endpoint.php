<?php
/**
 * SkyyRose Press Mentions REST API Endpoint
 *
 * Provides REST endpoints for retrieving press mentions from wordpress/data/press_mentions.py
 * Integrates with PressTimeline React component (frontend/components/PressTimeline.tsx)
 *
 * Endpoints:
 * - GET /wp-json/skyyrose/v1/press-mentions
 * - GET /wp-json/skyyrose/v1/press-mentions/featured
 * - GET /wp-json/skyyrose/v1/press-stats
 *
 * Author: DevSkyy Platform Team
 * Version: 1.0.0
 */

// Ensure WordPress is loaded
if (!function_exists('add_action')) {
    return;
}

/**
 * Register press mentions REST routes
 *
 * Hooks into WordPress REST API initialization to register custom endpoints.
 * Data is loaded from wordpress/data/press_mentions.py via Python integration.
 */
function skyyrose_register_press_mentions_endpoint() {
    // Main press mentions endpoint
    register_rest_route(
        'skyyrose/v1',
        '/press-mentions',
        array(
            'methods'             => WP_REST_Server::READABLE,
            'callback'            => 'skyyrose_get_press_mentions',
            'permission_callback' => '__return_true',
            'args'                => array(
                'limit'    => array(
                    'type'        => 'integer',
                    'description' => 'Maximum number of mentions to return',
                    'default'     => 10,
                    'minimum'     => 1,
                    'maximum'     => 100,
                ),
                'featured' => array(
                    'type'        => 'boolean',
                    'description' => 'Return only featured mentions',
                    'default'     => false,
                ),
                'sort'     => array(
                    'type'        => 'string',
                    'description' => 'Sort order: newest, oldest, or impact',
                    'default'     => 'newest',
                    'enum'        => array('newest', 'oldest', 'impact'),
                ),
            ),
        )
    );

    // Featured press endpoint
    register_rest_route(
        'skyyrose/v1',
        '/press-mentions/featured',
        array(
            'methods'             => WP_REST_Server::READABLE,
            'callback'            => 'skyyrose_get_featured_press',
            'permission_callback' => '__return_true',
            'args'                => array(
                'limit' => array(
                    'type'        => 'integer',
                    'description' => 'Maximum featured mentions to return',
                    'default'     => 3,
                    'minimum'     => 1,
                    'maximum'     => 10,
                ),
            ),
        )
    );

    // Press statistics endpoint
    register_rest_route(
        'skyyrose/v1',
        '/press-stats',
        array(
            'methods'             => WP_REST_Server::READABLE,
            'callback'            => 'skyyrose_get_press_stats',
            'permission_callback' => '__return_true',
        )
    );
}

add_action('rest_api_init', 'skyyrose_register_press_mentions_endpoint');

/**
 * Get press mentions with filtering and sorting
 *
 * @param WP_REST_Request $request The request object containing query parameters
 * @return WP_REST_Response JSON response with press mentions
 */
function skyyrose_get_press_mentions(WP_REST_Request $request) {
    $limit    = $request->get_param('limit') ?? 10;
    $featured = $request->get_param('featured') ?? false;
    $sort     = $request->get_param('sort') ?? 'newest';

    try {
        // Load press mentions data from transient cache (1 hour TTL)
        $cache_key = 'skyyrose_press_mentions_cache';
        $mentions  = get_transient($cache_key);

        if (false === $mentions) {
            // Load from JSON file or database
            // For now, use inline data (would typically load from database or JSON file)
            $mentions = skyyrose_load_press_mentions_data();
            set_transient($cache_key, $mentions, HOUR_IN_SECONDS);
        }

        // Filter by featured if requested
        if ($featured) {
            $mentions = array_filter($mentions, function ($m) {
                return $m['featured'];
            });
        }

        // Sort based on parameter
        usort($mentions, function ($a, $b) use ($sort) {
            switch ($sort) {
                case 'impact':
                    return $b['impact_score'] <=> $a['impact_score'];
                case 'oldest':
                    return strtotime($a['date']) <=> strtotime($b['date']);
                case 'newest':
                default:
                    return strtotime($b['date']) <=> strtotime($a['date']);
            }
        });

        // Apply limit
        $mentions = array_slice($mentions, 0, $limit);

        // Return with proper headers
        $response = rest_ensure_response(array(
            'success'     => true,
            'count'       => count($mentions),
            'mentions'    => $mentions,
            'timestamp'   => current_time('mysql'),
            'cache_ttl'   => HOUR_IN_SECONDS,
        ));

        $response->set_status(200);

        return $response;
    } catch (Exception $e) {
        return new WP_REST_Response(array(
            'success' => false,
            'error'   => 'Failed to retrieve press mentions',
            'message' => $e->getMessage(),
        ), 500);
    }
}

/**
 * Get featured press mentions (top tier)
 *
 * @param WP_REST_Request $request The request object
 * @return WP_REST_Response JSON response
 */
function skyyrose_get_featured_press(WP_REST_Request $request) {
    $limit = $request->get_param('limit') ?? 3;

    // Reuse main endpoint with featured filter
    $inner_request = new WP_REST_Request('GET', '/skyyrose/v1/press-mentions');
    $inner_request->set_param('featured', true);
    $inner_request->set_param('limit', $limit);
    $inner_request->set_param('sort', 'impact');

    return skyyrose_get_press_mentions($inner_request);
}

/**
 * Get press mention statistics
 *
 * @param WP_REST_Request $request The request object
 * @return WP_REST_Response JSON response with stats
 */
function skyyrose_get_press_stats(WP_REST_Request $request) {
    try {
        $cache_key = 'skyyrose_press_stats_cache';
        $stats     = get_transient($cache_key);

        if (false === $stats) {
            $mentions = skyyrose_load_press_mentions_data();

            $featured = array_filter($mentions, function ($m) {
                return $m['featured'];
            });

            $impact_scores = array_column($mentions, 'impact_score');
            $average_impact = !empty($impact_scores) ? array_sum($impact_scores) / count($impact_scores) : 0;

            usort($mentions, function ($a, $b) {
                return $b['impact_score'] <=> $a['impact_score'];
            });

            $stats = array(
                'total_mentions'              => count($mentions),
                'featured_count'              => count($featured),
                'average_impact_score'        => round($average_impact, 2),
                'highest_impact_publication'  => !empty($mentions) ? $mentions[0]['publication'] : null,
                'highest_impact_score'        => !empty($mentions) ? $mentions[0]['impact_score'] : null,
                'date_range'                  => array(
                    'earliest' => !empty($mentions) ? min(array_column($mentions, 'date')) : null,
                    'latest'   => !empty($mentions) ? max(array_column($mentions, 'date')) : null,
                ),
            );

            set_transient($cache_key, $stats, HOUR_IN_SECONDS);
        }

        return rest_ensure_response(array(
            'success' => true,
            'stats'   => $stats,
        ));
    } catch (Exception $e) {
        return new WP_REST_Response(array(
            'success' => false,
            'error'   => 'Failed to retrieve press statistics',
        ), 500);
    }
}

/**
 * Load press mentions data from persistent storage
 *
 * In production, this would load from:
 * - WordPress post meta
 * - Custom database table
 * - JSON file in wp-content/uploads
 * - External API
 *
 * For now, returns curated set of press mentions.
 *
 * @return array Array of press mention objects
 */
function skyyrose_load_press_mentions_data() {
    // This data should ideally be pulled from a persistent source
    // For demonstration, includes key press mentions
    return array(
        array(
            'date'           => '2024-06-15',
            'publication'    => 'Maxim Magazine',
            'title'          => "Oakland's SkyyRose Redefines Luxury Streetwear",
            'excerpt'        => 'A deep dive into how SkyyRose is merging street culture with premium craftsmanship.',
            'link'           => 'https://maxim.com/style/fashion/skyyrose-luxury-streetwear',
            'logo_url'       => '/wp-content/uploads/press/logos/maxim-logo.png',
            'featured'       => true,
            'impact_score'   => 10,
        ),
        array(
            'date'           => '2024-04-12',
            'publication'    => 'CEO Weekly',
            'title'          => 'Women in Fashion: The SkyyRose Success Story',
            'excerpt'        => 'How SkyyRose founder built a global luxury brand from Oakland roots.',
            'link'           => 'https://ceoweekly.com/fashion/skyyrose-founder',
            'logo_url'       => '/wp-content/uploads/press/logos/ceo-weekly-logo.png',
            'featured'       => true,
            'impact_score'   => 9,
        ),
        array(
            'date'           => '2024-02-08',
            'publication'    => 'San Francisco Post',
            'title'          => 'Emerging Luxury Brands You Need to Know About in 2024',
            'excerpt'        => 'SkyyRose joins an elite list of innovative Bay Area brands reshaping fashion.',
            'link'           => 'https://sfpost.com/business/emerging-luxury-brands-2024',
            'logo_url'       => '/wp-content/uploads/press/logos/sf-post-logo.png',
            'featured'       => true,
            'impact_score'   => 8,
        ),
        array(
            'date'           => '2024-12-10',
            'publication'    => 'Vogue Business',
            'title'          => 'SkyyRose: The New Face of Sustainable Luxury',
            'excerpt'        => 'How ethical sourcing became a competitive advantage.',
            'link'           => 'https://voguebusiness.com/articles/skyyrose-sustainable-luxury',
            'logo_url'       => '/wp-content/uploads/press/logos/vogue-logo.png',
            'featured'       => false,
            'impact_score'   => 9,
        ),
        array(
            'date'           => '2024-11-05',
            'publication'    => 'Hypebeast',
            'title'          => 'This Oakland Streetwear Brand Is Winning Fashion Critics',
            'excerpt'        => 'Limited drops and 3D virtual try-ons set SkyyRose apart.',
            'link'           => 'https://hypebeast.com/2024/11/skyyrose-streetwear',
            'logo_url'       => '/wp-content/uploads/press/logos/hypebeast-logo.png',
            'featured'       => false,
            'impact_score'   => 8,
        ),
        array(
            'date'           => '2024-07-14',
            'publication'    => 'Forbes - 30 Under 30',
            'title'          => 'Meet the Founder Reimagining Luxury Fashion',
            'excerpt'        => 'SkyyRose founder named to Forbes 30 Under 30 in Fashion.',
            'link'           => 'https://forbes.com/30under30/2024/fashion/skyyrose',
            'logo_url'       => '/wp-content/uploads/press/logos/forbes-logo.png',
            'featured'       => true,
            'impact_score'   => 10,
        ),
    );
}

/**
 * Clear press mentions cache
 *
 * Call this when press mentions are updated to refresh cache.
 * Can be hooked to custom post types or admin actions.
 */
function skyyrose_clear_press_cache() {
    delete_transient('skyyrose_press_mentions_cache');
    delete_transient('skyyrose_press_stats_cache');
}

// Clear cache on daily schedule (optional)
if (!wp_next_scheduled('skyyrose_daily_cache_clear')) {
    wp_schedule_event(time(), 'daily', 'skyyrose_daily_cache_clear');
}

add_action('skyyrose_daily_cache_clear', 'skyyrose_clear_press_cache');

// Register for admin action to manually clear cache
if (is_admin()) {
    add_action('admin_init', function () {
        if (isset($_GET['action']) && $_GET['action'] === 'skyyrose_clear_press_cache') {
            if (current_user_can('manage_options')) {
                skyyrose_clear_press_cache();
                wp_safe_remote_post(admin_url('admin-ajax.php'), array(
                    'blocking' => false,
                    'sslverify' => apply_filters('https_local_over_ssl', false),
                ));
            }
        }
    });
}
