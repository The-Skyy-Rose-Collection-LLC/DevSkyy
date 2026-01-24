<?php
/**
 * Klaviyo Integration for SkyyRose
 *
 * Syncs email subscribers to Klaviyo for automated welcome sequences,
 * abandoned cart recovery, and personalized campaigns.
 *
 * @package SkyyRose
 * @version 1.0.0
 *
 * Required environment:
 * - KLAVIYO_API_KEY (Private API Key from Klaviyo)
 * - KLAVIYO_LIST_ID (Newsletter list ID)
 */

defined('ABSPATH') || exit;

/**
 * Get Klaviyo API credentials
 */
function skyyrose_get_klaviyo_credentials(): array {
    return [
        'api_key' => defined('KLAVIYO_API_KEY') ? KLAVIYO_API_KEY : get_option('skyyrose_klaviyo_api_key', ''),
        'list_id' => defined('KLAVIYO_LIST_ID') ? KLAVIYO_LIST_ID : get_option('skyyrose_klaviyo_list_id', ''),
    ];
}

/**
 * Check if Klaviyo is configured
 */
function skyyrose_klaviyo_is_configured(): bool {
    $creds = skyyrose_get_klaviyo_credentials();
    return !empty($creds['api_key']) && !empty($creds['list_id']);
}

/**
 * Add subscriber to Klaviyo list
 *
 * @param string $email Subscriber email
 * @param string $source Signup source (popup, footer, checkout)
 * @param string $discount_code Generated discount code
 */
function skyyrose_add_to_klaviyo(string $email, string $source, string $discount_code): bool {
    if (!skyyrose_klaviyo_is_configured()) {
        return false;
    }

    $creds = skyyrose_get_klaviyo_credentials();

    // Klaviyo API v3 endpoint
    $url = 'https://a.klaviyo.com/api/profile-subscription-bulk-create-jobs/';

    $body = [
        'data' => [
            'type' => 'profile-subscription-bulk-create-job',
            'attributes' => [
                'profiles' => [
                    'data' => [
                        [
                            'type' => 'profile',
                            'attributes' => [
                                'email' => $email,
                                'properties' => [
                                    'source' => $source,
                                    'discount_code' => $discount_code,
                                    'signup_date' => current_time('c'),
                                    'brand' => 'SkyyRose',
                                ],
                            ],
                        ],
                    ],
                ],
                'historical_import' => false,
            ],
            'relationships' => [
                'list' => [
                    'data' => [
                        'type' => 'list',
                        'id' => $creds['list_id'],
                    ],
                ],
            ],
        ],
    ];

    $response = wp_remote_post($url, [
        'timeout' => 30,
        'headers' => [
            'Authorization' => 'Klaviyo-API-Key ' . $creds['api_key'],
            'Content-Type' => 'application/json',
            'Accept' => 'application/json',
            'revision' => '2024-02-15',
        ],
        'body' => wp_json_encode($body),
    ]);

    if (is_wp_error($response)) {
        error_log('Klaviyo API error: ' . $response->get_error_message());
        return false;
    }

    $code = wp_remote_retrieve_response_code($response);

    if ($code >= 200 && $code < 300) {
        // Also track the signup event
        skyyrose_track_klaviyo_event($email, 'Newsletter Signup', [
            'source' => $source,
            'discount_code' => $discount_code,
            'value' => 0,
        ]);
        return true;
    }

    error_log('Klaviyo API error: ' . wp_remote_retrieve_body($response));
    return false;
}

/**
 * Track custom event in Klaviyo
 *
 * @param string $email Customer email
 * @param string $event Event name
 * @param array $properties Event properties
 */
function skyyrose_track_klaviyo_event(string $email, string $event, array $properties = []): bool {
    if (!skyyrose_klaviyo_is_configured()) {
        return false;
    }

    $creds = skyyrose_get_klaviyo_credentials();

    $url = 'https://a.klaviyo.com/api/events/';

    $body = [
        'data' => [
            'type' => 'event',
            'attributes' => [
                'profile' => [
                    'data' => [
                        'type' => 'profile',
                        'attributes' => [
                            'email' => $email,
                        ],
                    ],
                ],
                'metric' => [
                    'data' => [
                        'type' => 'metric',
                        'attributes' => [
                            'name' => $event,
                        ],
                    ],
                ],
                'properties' => $properties,
                'time' => current_time('c'),
                'unique_id' => uniqid('sr_', true),
            ],
        ],
    ];

    $response = wp_remote_post($url, [
        'timeout' => 30,
        'headers' => [
            'Authorization' => 'Klaviyo-API-Key ' . $creds['api_key'],
            'Content-Type' => 'application/json',
            'Accept' => 'application/json',
            'revision' => '2024-02-15',
        ],
        'body' => wp_json_encode($body),
    ]);

    return !is_wp_error($response) && wp_remote_retrieve_response_code($response) >= 200 && wp_remote_retrieve_response_code($response) < 300;
}

/**
 * Hook into new subscriber action
 */
function skyyrose_klaviyo_on_new_subscriber(string $email, string $source, string $discount_code): void {
    skyyrose_add_to_klaviyo($email, $source, $discount_code);
}
add_action('skyyrose_new_subscriber', 'skyyrose_klaviyo_on_new_subscriber', 10, 3);

/**
 * Track WooCommerce events in Klaviyo
 */
function skyyrose_klaviyo_track_order(int $order_id): void {
    if (!skyyrose_klaviyo_is_configured()) {
        return;
    }

    $order = wc_get_order($order_id);
    if (!$order) {
        return;
    }

    $email = $order->get_billing_email();
    if (!$email) {
        return;
    }

    $items = [];
    foreach ($order->get_items() as $item) {
        $product = $item->get_product();
        if ($product) {
            $items[] = [
                'name' => $product->get_name(),
                'sku' => $product->get_sku(),
                'price' => $product->get_price(),
                'quantity' => $item->get_quantity(),
                'url' => $product->get_permalink(),
                'image_url' => wp_get_attachment_image_url($product->get_image_id(), 'medium'),
            ];
        }
    }

    skyyrose_track_klaviyo_event($email, 'Placed Order', [
        'order_id' => $order_id,
        'value' => (float) $order->get_total(),
        'items' => $items,
        'item_count' => $order->get_item_count(),
        'currency' => $order->get_currency(),
        'discount_code' => implode(', ', $order->get_coupon_codes()),
    ]);
}
add_action('woocommerce_order_status_completed', 'skyyrose_klaviyo_track_order');
add_action('woocommerce_order_status_processing', 'skyyrose_klaviyo_track_order');

/**
 * Add Klaviyo settings to admin
 */
function skyyrose_klaviyo_admin_settings(): void {
    add_settings_section(
        'skyyrose_klaviyo_section',
        'Klaviyo Integration',
        function () {
            echo '<p>Connect your Klaviyo account for automated email sequences.</p>';
        },
        'skyyrose_settings'
    );

    register_setting('skyyrose_settings', 'skyyrose_klaviyo_api_key');
    register_setting('skyyrose_settings', 'skyyrose_klaviyo_list_id');

    add_settings_field(
        'skyyrose_klaviyo_api_key',
        'Klaviyo API Key',
        function () {
            $value = get_option('skyyrose_klaviyo_api_key', '');
            echo '<input type="password" name="skyyrose_klaviyo_api_key" value="' . esc_attr($value) . '" class="regular-text" />';
            echo '<p class="description">Your private API key from Klaviyo Settings > API Keys</p>';
        },
        'skyyrose_settings',
        'skyyrose_klaviyo_section'
    );

    add_settings_field(
        'skyyrose_klaviyo_list_id',
        'Newsletter List ID',
        function () {
            $value = get_option('skyyrose_klaviyo_list_id', '');
            echo '<input type="text" name="skyyrose_klaviyo_list_id" value="' . esc_attr($value) . '" class="regular-text" />';
            echo '<p class="description">The List ID for your newsletter subscribers</p>';
        },
        'skyyrose_settings',
        'skyyrose_klaviyo_section'
    );
}
add_action('admin_init', 'skyyrose_klaviyo_admin_settings');

/**
 * Add settings page
 */
function skyyrose_add_settings_page(): void {
    add_submenu_page(
        'woocommerce',
        'SkyyRose Settings',
        'SkyyRose Settings',
        'manage_woocommerce',
        'skyyrose-settings',
        'skyyrose_settings_page'
    );
}
add_action('admin_menu', 'skyyrose_add_settings_page');

/**
 * Render settings page
 */
function skyyrose_settings_page(): void {
    ?>
    <div class="wrap">
        <h1>SkyyRose Settings</h1>

        <?php if (skyyrose_klaviyo_is_configured()) : ?>
            <div class="notice notice-success">
                <p><strong>Klaviyo Connected!</strong> New subscribers will sync automatically.</p>
            </div>
        <?php else : ?>
            <div class="notice notice-warning">
                <p><strong>Klaviyo Not Configured.</strong> Add your API key and List ID below, or define KLAVIYO_API_KEY and KLAVIYO_LIST_ID in wp-config.php</p>
            </div>
        <?php endif; ?>

        <form method="post" action="options.php">
            <?php
            settings_fields('skyyrose_settings');
            do_settings_sections('skyyrose_settings');
            submit_button();
            ?>
        </form>

        <hr>

        <h2>Setup Instructions</h2>
        <ol>
            <li>Log in to <a href="https://www.klaviyo.com/account#api-keys-tab" target="_blank">Klaviyo API Keys</a></li>
            <li>Create a new Private API Key with <code>profiles:write</code>, <code>events:write</code>, and <code>lists:write</code> scopes</li>
            <li>Copy the key and paste it above</li>
            <li>Go to <a href="https://www.klaviyo.com/lists" target="_blank">Klaviyo Lists</a></li>
            <li>Find your newsletter list and copy the List ID from the URL (e.g., <code>ABC123</code>)</li>
            <li>Paste the List ID above</li>
        </ol>

        <h3>Alternatively, add to wp-config.php:</h3>
        <pre style="background: #f1f1f1; padding: 15px; border-radius: 4px;">
define('KLAVIYO_API_KEY', 'pk_xxxxxxxxxxxxxxxxxxxx');
define('KLAVIYO_LIST_ID', 'ABC123');
        </pre>
    </div>
    <?php
}

/**
 * Add Klaviyo tracking script to frontend
 */
function skyyrose_klaviyo_tracking_script(): void {
    $creds = skyyrose_get_klaviyo_credentials();

    // Only add if we have a public key (different from private API key)
    $public_key = defined('KLAVIYO_PUBLIC_KEY') ? KLAVIYO_PUBLIC_KEY : get_option('skyyrose_klaviyo_public_key', '');

    if (empty($public_key)) {
        return;
    }
    ?>
    <script async type="text/javascript" src="https://static.klaviyo.com/onsite/js/klaviyo.js?company_id=<?php echo esc_attr($public_key); ?>"></script>
    <?php
}
add_action('wp_head', 'skyyrose_klaviyo_tracking_script', 5);
