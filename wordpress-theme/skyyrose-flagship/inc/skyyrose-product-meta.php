<?php
/**
 * SkyyRose Product Meta — catalog post-meta schema for WooCommerce products.
 *
 * Maps every non-WC-native column in data/skyyrose-catalog.csv to a registered
 * post-meta key on the `product` post type. Provides:
 *
 *   - Schema as single source of truth (skyyrose_product_meta_schema()).
 *   - register_meta() registration for REST + sanitize callbacks.
 *   - WooCommerce Product Data tab "SkyyRose" with grouped inputs.
 *   - Save handler on woocommerce_process_product_meta.
 *   - Public getter skyyrose_get_product_meta_field( $id, $key ).
 *   - WP-CLI importer `wp skyyrose import-catalog-meta` (idempotent upsert).
 *
 * WC-native fields skipped (sku, name, price, description, featured image,
 * sizes/color attributes, status from `published`). Preorder fields owned by
 * inc/woocommerce-preorder.php — do NOT duplicate `_is_preorder` here.
 *
 * @package SkyyRose
 * @since   1.0.1
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*
--------------------------------------------------------------
 * Schema (single source of truth)
 *--------------------------------------------------------------*/

/**
 * Catalog post-meta schema for SkyyRose products.
 *
 * Each entry keyed by the meta key (must start with `_skyyrose_` per theme
 * convention; leading underscore hides it from the default WP custom-fields UI).
 *
 * Fields per entry:
 *   type        — WP register_meta type (string|integer|boolean).
 *   label       — translatable admin label.
 *   description — translatable admin help text.
 *   sanitize    — callable sanitizer applied on save.
 *   input       — admin renderer key (text|textarea|select|checkbox|number).
 *   options     — enum values for `select` (slug => label).
 *   group       — admin panel section header.
 *   csv_column  — matching column in data/skyyrose-catalog.csv (for importer).
 *
 * @since 1.0.1
 *
 * @return array<string,array<string,mixed>>
 */
function skyyrose_product_meta_schema() {

	$collections = array(
		'signature'    => __( 'Signature', 'skyyrose' ),
		'black-rose'   => __( 'Black Rose', 'skyyrose' ),
		'love-hurts'   => __( 'Love Hurts', 'skyyrose' ),
		'kids-capsule' => __( 'Kids Capsule', 'skyyrose' ),
	);

	$engines = array(
		''            => __( '— default —', 'skyyrose' ),
		'gemini-pro'  => __( 'Gemini Pro', 'skyyrose' ),
		'fashn'       => __( 'FASHN', 'skyyrose' ),
		'tripo'       => __( 'Tripo', 'skyyrose' ),
		'meshy'       => __( 'Meshy', 'skyyrose' ),
		'trellis'     => __( 'TRELLIS', 'skyyrose' ),
		'nano-banana' => __( 'Nano Banana', 'skyyrose' ),
	);

	return array(

		// Identity & merchandising.
		'_skyyrose_collection'                  => array(
			'type'        => 'string',
			'label'       => __( 'Collection', 'skyyrose' ),
			'description' => __( 'Brand collection slug.', 'skyyrose' ),
			'sanitize'    => 'sanitize_title',
			'input'       => 'select',
			'options'     => $collections,
			'group'       => __( 'Identity', 'skyyrose' ),
			'csv_column'  => 'collection',
		),
		'_skyyrose_badge'                       => array(
			'type'        => 'string',
			'label'       => __( 'Badge', 'skyyrose' ),
			'description' => __( 'Optional merchandising badge (e.g. NEW, LIMITED).', 'skyyrose' ),
			'sanitize'    => 'sanitize_text_field',
			'input'       => 'text',
			'group'       => __( 'Identity', 'skyyrose' ),
			'csv_column'  => 'badge',
		),
		'_skyyrose_edition_size'                => array(
			'type'        => 'integer',
			'label'       => __( 'Edition Size', 'skyyrose' ),
			'description' => __( 'Total units in the edition. 0 = open edition.', 'skyyrose' ),
			'sanitize'    => 'absint',
			'input'       => 'number',
			'group'       => __( 'Identity', 'skyyrose' ),
			'csv_column'  => 'edition_size',
		),

		// Imagery (non-featured).
		'_skyyrose_front_model_image'           => array(
			'type'        => 'string',
			'label'       => __( 'Front Model Image', 'skyyrose' ),
			'description' => __( 'Path relative to theme (e.g. assets/images/products/x-front-model.webp).', 'skyyrose' ),
			'sanitize'    => 'sanitize_text_field',
			'input'       => 'text',
			'group'       => __( 'Imagery', 'skyyrose' ),
			'csv_column'  => 'front_model_image',
		),
		'_skyyrose_back_image'                  => array(
			'type'        => 'string',
			'label'       => __( 'Back Image', 'skyyrose' ),
			'description' => __( 'Path to back-side product image.', 'skyyrose' ),
			'sanitize'    => 'sanitize_text_field',
			'input'       => 'text',
			'group'       => __( 'Imagery', 'skyyrose' ),
			'csv_column'  => 'back_image',
		),
		'_skyyrose_back_model_image'            => array(
			'type'        => 'string',
			'label'       => __( 'Back Model Image', 'skyyrose' ),
			'description' => __( 'Path to back-side model image.', 'skyyrose' ),
			'sanitize'    => 'sanitize_text_field',
			'input'       => 'text',
			'group'       => __( 'Imagery', 'skyyrose' ),
			'csv_column'  => 'back_model_image',
		),

		// Render pipeline overrides.
		'_skyyrose_dossier_slug'                => array(
			'type'        => 'string',
			'label'       => __( 'Dossier Slug', 'skyyrose' ),
			'description' => __( 'Filename slug in data/dossiers/ (without .md extension).', 'skyyrose' ),
			'sanitize'    => 'sanitize_title',
			'input'       => 'text',
			'group'       => __( 'Render Pipeline', 'skyyrose' ),
			'csv_column'  => 'dossier_slug',
		),
		'_skyyrose_engine_override'             => array(
			'type'        => 'string',
			'label'       => __( 'Engine Override', 'skyyrose' ),
			'description' => __( 'Force a specific render engine. Empty = pipeline default.', 'skyyrose' ),
			'sanitize'    => 'skyyrose_sanitize_engine_override',
			'input'       => 'select',
			'options'     => $engines,
			'group'       => __( 'Render Pipeline', 'skyyrose' ),
			'csv_column'  => 'engine_override',
		),
		'_skyyrose_branding_spec'               => array(
			'type'        => 'string',
			'label'       => __( 'Branding Spec', 'skyyrose' ),
			'description' => __( 'Free-text branding placement instructions for the render pipeline.', 'skyyrose' ),
			'sanitize'    => 'sanitize_textarea_field',
			'input'       => 'textarea',
			'group'       => __( 'Render Pipeline', 'skyyrose' ),
			'csv_column'  => 'branding_spec',
		),
		'_skyyrose_render_output_slug'          => array(
			'type'        => 'string',
			'label'       => __( 'Render Output Slug', 'skyyrose' ),
			'description' => __( 'Filename slug for rendered output (matches renders/output/<slug>).', 'skyyrose' ),
			'sanitize'    => 'sanitize_title',
			'input'       => 'text',
			'group'       => __( 'Render Pipeline', 'skyyrose' ),
			'csv_column'  => 'render_output_slug',
		),
		'_skyyrose_render_source_override'      => array(
			'type'        => 'string',
			'label'       => __( 'Render Source Override (front)', 'skyyrose' ),
			'description' => __( 'Override the front source image used by the render pipeline.', 'skyyrose' ),
			'sanitize'    => 'sanitize_text_field',
			'input'       => 'text',
			'group'       => __( 'Render Pipeline', 'skyyrose' ),
			'csv_column'  => 'render_source_override',
		),
		'_skyyrose_render_back_source_override' => array(
			'type'        => 'string',
			'label'       => __( 'Render Source Override (back)', 'skyyrose' ),
			'description' => __( 'Override the back source image used by the render pipeline.', 'skyyrose' ),
			'sanitize'    => 'sanitize_text_field',
			'input'       => 'text',
			'group'       => __( 'Render Pipeline', 'skyyrose' ),
			'csv_column'  => 'render_back_source_override',
		),
		'_skyyrose_render_is_tech_flat'         => array(
			'type'        => 'boolean',
			'label'       => __( 'Is Tech Flat', 'skyyrose' ),
			'description' => __( 'Source asset is a technical flat (not a 3/4 photo).', 'skyyrose' ),
			'sanitize'    => 'skyyrose_sanitize_bool',
			'input'       => 'checkbox',
			'group'       => __( 'Render Pipeline', 'skyyrose' ),
			'csv_column'  => 'render_is_tech_flat',
		),
		'_skyyrose_render_is_accessory'         => array(
			'type'        => 'boolean',
			'label'       => __( 'Is Accessory', 'skyyrose' ),
			'description' => __( 'Product is an accessory (cap, beanie, bag) not garment.', 'skyyrose' ),
			'sanitize'    => 'skyyrose_sanitize_bool',
			'input'       => 'checkbox',
			'group'       => __( 'Render Pipeline', 'skyyrose' ),
			'csv_column'  => 'render_is_accessory',
		),
		'_skyyrose_garment_type_lock'           => array(
			'type'        => 'string',
			'label'       => __( 'Garment Type Lock', 'skyyrose' ),
			'description' => __( 'Force garment type classification (e.g. crewneck, hoodie, joggers).', 'skyyrose' ),
			'sanitize'    => 'sanitize_title',
			'input'       => 'text',
			'group'       => __( 'Render Pipeline', 'skyyrose' ),
			'csv_column'  => 'garment_type_lock',
		),
	);
}

/**
 * Sanitize a checkbox/boolean post value into a '0'|'1' string for storage.
 *
 * Stored as string to match WP/WC convention (existing _is_preorder uses '1').
 *
 * @since 1.0.1
 *
 * @param mixed $value Raw POST value.
 * @return string '1' if truthy, '0' otherwise.
 */
function skyyrose_sanitize_bool( $value ) {
	if ( is_string( $value ) ) {
		$value = strtolower( trim( $value ) );
	}
	$truthy = array( '1', 'true', 'yes', 'on', 1, true );
	return in_array( $value, $truthy, true ) ? '1' : '0';
}

/**
 * Sanitize the engine_override value against the schema enum.
 *
 * @since 1.0.1
 *
 * @param mixed $value Raw value.
 * @return string Slug from the engine enum, or '' if invalid.
 */
function skyyrose_sanitize_engine_override( $value ) {
	$schema = skyyrose_product_meta_schema();
	$valid  = array_keys( $schema['_skyyrose_engine_override']['options'] );
	$value  = is_scalar( $value ) ? sanitize_title( (string) $value ) : '';
	return in_array( $value, $valid, true ) ? $value : '';
}

/*
--------------------------------------------------------------
 * register_meta() — REST exposure + auth + sanitize
 *--------------------------------------------------------------*/

/**
 * Register every schema entry as `product` post-meta with WP core.
 *
 * Exposes meta to the REST API for authenticated editors, applies sanitize
 * callbacks centrally, and enables `show_in_rest` so the WC REST API can
 * accept these via `meta_data[]` on product create/update.
 *
 * @since 1.0.1
 * @return void
 */
function skyyrose_register_product_meta() {

	foreach ( skyyrose_product_meta_schema() as $key => $def ) {
		register_post_meta(
			'product',
			$key,
			array(
				'type'              => $def['type'],
				'description'       => $def['description'],
				'single'            => true,
				'show_in_rest'      => true,
				'sanitize_callback' => $def['sanitize'],
				'auth_callback'     => static function () {
					return current_user_can( 'manage_woocommerce' );
				},
			)
		);
	}
}
add_action( 'init', 'skyyrose_register_product_meta' );

/*
--------------------------------------------------------------
 * WC Product Data — "SkyyRose" tab + panel
 *--------------------------------------------------------------*/

/**
 * Add a "SkyyRose" tab to the WC Product Data box.
 *
 * @since 1.0.1
 *
 * @param array<string,array<string,mixed>> $tabs Existing WC product data tabs.
 * @return array<string,array<string,mixed>> Tabs with SkyyRose appended.
 */
function skyyrose_add_product_data_tab( $tabs ) {

	$tabs['skyyrose'] = array(
		'label'    => esc_html__( 'SkyyRose', 'skyyrose' ),
		'target'   => 'skyyrose_product_data',
		'class'    => array( 'show_if_simple', 'show_if_variable' ),
		'priority' => 75,
	);

	return $tabs;
}
add_filter( 'woocommerce_product_data_tabs', 'skyyrose_add_product_data_tab' );

/**
 * Render the SkyyRose product data panel.
 *
 * Iterates the schema, grouping fields by `group`, and emits the matching WC
 * helper (woocommerce_wp_text_input etc.) for each.
 *
 * @since 1.0.1
 * @return void
 */
function skyyrose_product_data_panel() {

	$schema = skyyrose_product_meta_schema();
	$post   = get_post();
	$id     = $post ? (int) $post->ID : 0;

	echo '<div id="skyyrose_product_data" class="panel woocommerce_options_panel">';
	wp_nonce_field( 'skyyrose_product_meta_nonce', 'skyyrose_product_meta_nonce' );

	$last_group = '';
	foreach ( $schema as $key => $def ) {

		if ( $def['group'] !== $last_group ) {
			if ( '' !== $last_group ) {
				echo '</div>';
			}
			echo '<div class="options_group">';
			printf(
				'<p style="margin:8px 12px 0;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#666;">%s</p>',
				esc_html( $def['group'] )
			);
			$last_group = $def['group'];
		}

		$value = $id ? get_post_meta( $id, $key, true ) : '';

		switch ( $def['input'] ) {

			case 'select':
				woocommerce_wp_select(
					array(
						'id'          => $key,
						'label'       => $def['label'],
						'description' => $def['description'],
						'desc_tip'    => true,
						'value'       => $value,
						'options'     => $def['options'],
					)
				);
				break;

			case 'textarea':
				woocommerce_wp_textarea_input(
					array(
						'id'          => $key,
						'label'       => $def['label'],
						'description' => $def['description'],
						'desc_tip'    => true,
						'value'       => $value,
						'rows'        => 3,
					)
				);
				break;

			case 'checkbox':
				woocommerce_wp_checkbox(
					array(
						'id'          => $key,
						'label'       => $def['label'],
						'description' => $def['description'],
						'desc_tip'    => true,
						'value'       => '1' === (string) $value ? 'yes' : 'no',
						'cbvalue'     => 'yes',
					)
				);
				break;

			case 'number':
				woocommerce_wp_text_input(
					array(
						'id'                => $key,
						'label'             => $def['label'],
						'description'       => $def['description'],
						'desc_tip'          => true,
						'value'             => $value,
						'type'              => 'number',
						'custom_attributes' => array(
							'min'  => '0',
							'step' => '1',
						),
					)
				);
				break;

			case 'text':
			default:
				woocommerce_wp_text_input(
					array(
						'id'          => $key,
						'label'       => $def['label'],
						'description' => $def['description'],
						'desc_tip'    => true,
						'value'       => $value,
					)
				);
				break;
		}
	}

	if ( '' !== $last_group ) {
		echo '</div>';
	}
	echo '</div>';
}
add_action( 'woocommerce_product_data_panels', 'skyyrose_product_data_panel' );

/*
--------------------------------------------------------------
 * Save handler
 *--------------------------------------------------------------*/

/**
 * Persist SkyyRose product-meta fields on product save.
 *
 * Hooked on woocommerce_process_product_meta — WC verifies the user can edit
 * the post and is_admin() before firing. Nonce check is an additional belt.
 *
 * @since 1.0.1
 *
 * @param int $post_id Product post ID.
 * @return void
 */
function skyyrose_save_product_meta_panel( $post_id ) {

	if ( ! isset( $_POST['skyyrose_product_meta_nonce'] ) ) {
		return;
	}

	$nonce = sanitize_text_field( wp_unslash( $_POST['skyyrose_product_meta_nonce'] ) );
	if ( ! wp_verify_nonce( $nonce, 'skyyrose_product_meta_nonce' ) ) {
		return;
	}

	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	foreach ( skyyrose_product_meta_schema() as $key => $def ) {

		if ( 'checkbox' === $def['input'] ) {
			// Unchecked checkboxes are absent from POST — explicit '0'.
			// phpcs:ignore WordPress.Security.ValidatedSanitizedInput.InputNotSanitized -- sanitized below via $def['sanitize'] callback.
			$raw = isset( $_POST[ $key ] ) ? wp_unslash( $_POST[ $key ] ) : '0';
		} else {
			if ( ! isset( $_POST[ $key ] ) ) {
				continue;
			}
			// phpcs:ignore WordPress.Security.ValidatedSanitizedInput.InputNotSanitized -- sanitized below via $def['sanitize'] callback.
			$raw = wp_unslash( $_POST[ $key ] );
		}

		$sanitized = is_callable( $def['sanitize'] ) ? call_user_func( $def['sanitize'], $raw ) : $raw;
		update_post_meta( $post_id, $key, $sanitized );
	}
}
add_action( 'woocommerce_process_product_meta', 'skyyrose_save_product_meta_panel' );

/*
--------------------------------------------------------------
 * Public getter
 *--------------------------------------------------------------*/

/**
 * Read a SkyyRose meta field with default-aware coercion.
 *
 * Returns a typed value matching the schema entry's `type`:
 *   integer → int, boolean → bool, string → string.
 * Falls back to '' / 0 / false if the key is unset or not in schema.
 *
 * @since 1.0.1
 *
 * @param int    $product_id Product post ID.
 * @param string $key        Schema meta key (with leading underscore).
 * @return mixed Typed value.
 */
function skyyrose_get_product_meta_field( $product_id, $key ) {

	$schema = skyyrose_product_meta_schema();
	if ( ! isset( $schema[ $key ] ) ) {
		return '';
	}

	$raw  = get_post_meta( (int) $product_id, $key, true );
	$type = $schema[ $key ]['type'];

	if ( 'integer' === $type ) {
		return absint( $raw );
	}
	if ( 'boolean' === $type ) {
		return '1' === (string) $raw;
	}
	return is_scalar( $raw ) ? (string) $raw : '';
}

/*
--------------------------------------------------------------
 * WP-CLI importer (idempotent upsert from catalog CSV)
 *--------------------------------------------------------------*/

if ( defined( 'WP_CLI' ) && WP_CLI ) {

	/**
	 * Import SkyyRose catalog meta from data/skyyrose-catalog.csv onto matching
	 * WC products. Matches by SKU. Creates no products.
	 *
	 * ## OPTIONS
	 *
	 * [--dry-run]
	 * : Show what would change without writing.
	 *
	 * [--sku=<sku>]
	 * : Limit to a single SKU.
	 *
	 * ## EXAMPLES
	 *
	 *     wp skyyrose import-catalog-meta --dry-run
	 *     wp skyyrose import-catalog-meta --sku=br-001
	 *
	 * @when after_wp_load
	 *
	 * @param array<int,string>    $args       Positional args (unused).
	 * @param array<string,string> $assoc_args Associative args.
	 * @return void
	 */
	$skyyrose_meta_import_cmd = static function ( $args, $assoc_args ) {

		$dry_run    = isset( $assoc_args['dry-run'] );
		$only_sku   = isset( $assoc_args['sku'] ) ? sanitize_text_field( $assoc_args['sku'] ) : '';
		$csv_path   = trailingslashit( get_stylesheet_directory() ) . 'data/skyyrose-catalog.csv';
		$schema     = skyyrose_product_meta_schema();
		$csv_map    = array();
		$col_to_key = array();
		foreach ( $schema as $key => $def ) {
			if ( ! empty( $def['csv_column'] ) ) {
				$col_to_key[ $def['csv_column'] ] = $key;
			}
		}

		if ( ! file_exists( $csv_path ) || ! is_readable( $csv_path ) ) {
			WP_CLI::error( "Catalog CSV not found at: {$csv_path}" );
		}

		// phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_fopen -- WP_Filesystem lacks streaming readers; CLI-only read of a theme-bundled CSV.
		$handle = fopen( $csv_path, 'r' );
		if ( false === $handle ) {
			WP_CLI::error( 'Failed to open catalog CSV.' );
		}

		$header = fgetcsv( $handle );
		if ( false === $header ) {
			WP_CLI::error( 'Catalog CSV is empty.' );
		}

		$sku_idx = array_search( 'sku', $header, true );
		if ( false === $sku_idx ) {
			WP_CLI::error( "CSV header missing 'sku' column." );
		}

		$rows_seen = 0;
		$rows_hit  = 0;
		$rows_miss = 0;
		$updates   = 0;

		while ( true ) {
			$row = fgetcsv( $handle );
			if ( false === $row ) {
				break;
			}
			++$rows_seen;
			$sku = sanitize_text_field( $row[ $sku_idx ] );
			if ( '' === $sku ) {
				continue;
			}
			if ( '' !== $only_sku && $sku !== $only_sku ) {
				continue;
			}

			$product_id = wc_get_product_id_by_sku( $sku );
			if ( ! $product_id ) {
				++$rows_miss;
				WP_CLI::warning( "No product for SKU {$sku} — skipping." );
				continue;
			}
			++$rows_hit;

			$pairs = array();
			foreach ( $col_to_key as $col => $meta_key ) {
				$col_idx = array_search( $col, $header, true );
				if ( false === $col_idx || ! isset( $row[ $col_idx ] ) ) {
					continue;
				}
				$raw       = $row[ $col_idx ];
				$sanitizer = $schema[ $meta_key ]['sanitize'];
				$value     = is_callable( $sanitizer ) ? call_user_func( $sanitizer, $raw ) : $raw;

				$existing = get_post_meta( $product_id, $meta_key, true );
				if ( (string) $existing === (string) $value ) {
					continue;
				}

				$pairs[ $meta_key ] = $value;
				++$updates;
			}

			if ( empty( $pairs ) ) {
				WP_CLI::log( "[{$sku}] no changes" );
				continue;
			}

			WP_CLI::log( sprintf( '[%s] %s %d fields', $sku, $dry_run ? 'would update' : 'updating', count( $pairs ) ) );

			if ( ! $dry_run ) {
				foreach ( $pairs as $meta_key => $value ) {
					update_post_meta( $product_id, $meta_key, $value );
				}
			}
		}
		// phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_fclose -- matches fopen() above; CLI-only.
		fclose( $handle );

		WP_CLI::success(
			sprintf(
				'Catalog rows: %d | matched: %d | unmatched: %d | %s fields: %d',
				$rows_seen,
				$rows_hit,
				$rows_miss,
				$dry_run ? 'would-update' : 'updated',
				$updates
			)
		);
	};

	WP_CLI::add_command( 'skyyrose import-catalog-meta', $skyyrose_meta_import_cmd );
}
