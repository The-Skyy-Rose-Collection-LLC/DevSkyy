<?php
/**
 * Customer Enhancements — Batch C (2026-07-01)
 *
 * Delivers three founder-approved enhancements:
 *   1. PDP Fit Notes + Model Specs — per-product admin metabox + front-end block.
 *   2. Homepage Drop Block — Customizer section + full-bleed editorial renderer.
 *   3. Sticky ATC Bar (editorial PDPs) — HTML emitted from product-detail-editorial.php;
 *      see skyyrose_render_ed_sticky_atc() helper at the bottom of this file.
 *
 * Enhancement #2 (Complete the Look / "Wears With") is intentionally absent.
 * It was explicitly retired 2026-05-27 per founder canon: "no related products on PDP."
 * The retirement is recorded in inc/enqueue.php:855 and
 * template-parts/product-detail-editorial.php:211. Awaiting team-lead confirmation
 * of founder canon override before building.
 *
 * @package SkyyRose
 * @since   1.6.8
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*
--------------------------------------------------------------
 * 1. Fit Notes + Model Specs — Admin Metabox
 *--------------------------------------------------------------*/

/**
 * Register the "Fit & Experience" metabox on WooCommerce product posts.
 *
 * Uses add_meta_boxes_product (not add_meta_boxes) so the box only
 * appears on product edit screens — pages, posts, and other CPTs are
 * unaffected. Appears below the WC Product Data panel in the normal
 * meta-box zone.
 *
 * @since 1.6.8
 * @return void
 */
function skyyrose_ce_register_metabox() {
	add_meta_box(
		'skyyrose-ce-fit',
		esc_html__( 'Fit & Experience', 'skyyrose' ),
		'skyyrose_ce_render_fit_metabox',
		'product',
		'normal',
		'default'
	);
}
add_action( 'add_meta_boxes_product', 'skyyrose_ce_register_metabox' );

/**
 * Render the Fit & Experience metabox fields.
 *
 * Nonce is scoped to 'skyyrose_ce_fit_save' — kept separate from the
 * existing SkyyRose catalog nonce ('skyyrose_product_meta_nonce') to
 * avoid cross-contamination if either file is modified independently.
 *
 * @since 1.6.8
 *
 * @param WP_Post $post Current product post object.
 * @return void
 */
function skyyrose_ce_render_fit_metabox( $post ) {
	wp_nonce_field( 'skyyrose_ce_fit_save', 'skyyrose_ce_fit_nonce' );

	$fit_note     = get_post_meta( $post->ID, '_skyyrose_fit_note', true );
	$model_height = get_post_meta( $post->ID, '_skyyrose_model_height', true );
	$model_size   = get_post_meta( $post->ID, '_skyyrose_model_size', true );
	?>
	<p class="description" style="margin-bottom:12px;">
		<?php esc_html_e( 'Fit guidance and model reference shown on the product page. All fields optional — leave blank to hide the block entirely.', 'skyyrose' ); ?>
	</p>
	<table class="form-table" style="max-width:640px;">
		<tbody>
			<tr>
				<th scope="row">
					<label for="skyyrose_ce_fit_note"><?php esc_html_e( 'Fit Note', 'skyyrose' ); ?></label>
				</th>
				<td>
					<input
						type="text"
						id="skyyrose_ce_fit_note"
						name="_skyyrose_fit_note"
						value="<?php echo esc_attr( $fit_note ); ?>"
						class="widefat"
						placeholder="<?php esc_attr_e( 'e.g. Runs oversized — size down for a tailored fit', 'skyyrose' ); ?>"
					/>
					<p class="description"><?php esc_html_e( 'Fit guidance text displayed under the ATC button.', 'skyyrose' ); ?></p>
				</td>
			</tr>
			<tr>
				<th scope="row">
					<label for="skyyrose_ce_model_height"><?php esc_html_e( 'Model Height', 'skyyrose' ); ?></label>
				</th>
				<td>
					<input
						type="text"
						id="skyyrose_ce_model_height"
						name="_skyyrose_model_height"
						value="<?php echo esc_attr( $model_height ); ?>"
						class="widefat"
						placeholder="<?php esc_attr_e( 'e.g. 6\'2"', 'skyyrose' ); ?>"
					/>
					<p class="description"><?php esc_html_e( 'Height of the model in the product imagery.', 'skyyrose' ); ?></p>
				</td>
			</tr>
			<tr>
				<th scope="row">
					<label for="skyyrose_ce_model_size"><?php esc_html_e( 'Model Size', 'skyyrose' ); ?></label>
				</th>
				<td>
					<input
						type="text"
						id="skyyrose_ce_model_size"
						name="_skyyrose_model_size"
						value="<?php echo esc_attr( $model_size ); ?>"
						class="widefat"
						placeholder="<?php esc_attr_e( 'e.g. Large', 'skyyrose' ); ?>"
					/>
					<p class="description"><?php esc_html_e( 'Size the model is wearing. Appears beside height in the Model Reference spec.', 'skyyrose' ); ?></p>
				</td>
			</tr>
		</tbody>
	</table>
	<?php
}

/**
 * Persist fit notes on product save.
 *
 * Hooked on save_post_product rather than woocommerce_process_product_meta
 * so the fields also save when the product is updated via the block editor
 * or the REST API — not only through the classic WC product panel.
 *
 * @since 1.6.8
 *
 * @param int $post_id Product post ID.
 * @return void
 */
function skyyrose_ce_save_fit_metabox( $post_id ) {
	// Skip autosave and bulk-edit — no metabox form data present.
	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}

	// Our nonce must be present; absence means the save did not come from
	// a form that included this metabox (e.g. quick-edit, WP REST, cron).
	if ( ! isset( $_POST['skyyrose_ce_fit_nonce'] ) ) {
		return;
	}

	$nonce = sanitize_text_field( wp_unslash( $_POST['skyyrose_ce_fit_nonce'] ) );
	if ( ! wp_verify_nonce( $nonce, 'skyyrose_ce_fit_save' ) ) {
		return;
	}

	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	// Each key is saved only when it is present in the POST payload.
	$keys = array(
		'_skyyrose_fit_note',
		'_skyyrose_model_height',
		'_skyyrose_model_size',
	);

	foreach ( $keys as $key ) {
		if ( array_key_exists( $key, $_POST ) ) {
			update_post_meta(
				$post_id,
				$key,
				sanitize_text_field( wp_unslash( $_POST[ $key ] ) )
			);
		}
	}
}
add_action( 'save_post_product', 'skyyrose_ce_save_fit_metabox' );

/**
 * Render the Fit Notes block for a product.
 *
 * Outputs nothing — no element, no whitespace — when all three meta fields
 * are empty. This keeps the DOM clean on products that have not been
 * configured, and prevents an empty "Fit" heading from appearing.
 *
 * @since 1.6.8
 *
 * @param int $product_id WooCommerce product post ID.
 * @return void Outputs HTML directly; intended for use inside a template.
 */
function skyyrose_render_fit_block( $product_id ) {
	$product_id   = (int) $product_id;
	$fit_note     = get_post_meta( $product_id, '_skyyrose_fit_note', true );
	$model_height = get_post_meta( $product_id, '_skyyrose_model_height', true );
	$model_size   = get_post_meta( $product_id, '_skyyrose_model_size', true );

	// Return early when there is nothing to display. The block must be
	// completely absent from the DOM when unconfigured — prevents an
	// empty labelled region from confusing screen readers or layout.
	if ( empty( $fit_note ) && empty( $model_height ) && empty( $model_size ) ) {
		return;
	}
	?>
	<div class="sr-fit-block" role="complementary" aria-label="<?php esc_attr_e( 'Fit Information', 'skyyrose' ); ?>">
		<p class="sr-fit-block__label"><?php esc_html_e( 'Fit', 'skyyrose' ); ?></p>

		<?php if ( $fit_note ) : ?>
			<p class="sr-fit-block__note"><?php echo esc_html( $fit_note ); ?></p>
		<?php endif; ?>

		<?php if ( $model_height || $model_size ) : ?>
			<dl class="sr-fit-block__model-specs">
				<dt><?php esc_html_e( 'Model Reference', 'skyyrose' ); ?></dt>
				<dd>
					<?php
					// Build natural-language spec from whichever fields are set.
					// Each segment is escaped at the point it is used above; the
					// sprintf wrappers are safe, translateable strings. The
					// implode of already-escaped strings is intentional.
					$parts = array();
					if ( $model_height ) {
						/* translators: %s: model height, e.g. 6'2" */
						$parts[] = sprintf( esc_html__( '%s tall', 'skyyrose' ), esc_html( $model_height ) );
					}
					if ( $model_size ) {
						/* translators: %s: size worn by the model, e.g. Large */
						$parts[] = sprintf( esc_html__( 'wearing a %s', 'skyyrose' ), esc_html( $model_size ) );
					}
					// phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- parts are individually escaped above.
					echo implode( ', ', $parts );
					?>
				</dd>
			</dl>
		<?php endif; ?>
	</div>
	<?php
}

/*
--------------------------------------------------------------
 * 2. Homepage Drop Block — Customizer Section + Render Helper
 *--------------------------------------------------------------*/

/**
 * Register the Drop Block Customizer section and its 6 settings.
 *
 * Registered as a separate function hooked at priority 20 so it appends to
 * the Customizer after the main skyyrose_customize_register() runs at
 * default priority 10 — avoids editing inc/customizer.php.
 *
 * @since 1.6.8
 *
 * @param WP_Customize_Manager $wp_customize Customizer manager instance.
 * @return void
 */
function skyyrose_ce_drop_block_customize_register( $wp_customize ) {

	// ── Section ──────────────────────────────────────────────────────────────
	$wp_customize->add_section(
		'skyyrose_drop_block',
		array(
			'title'       => esc_html__( 'Drop Block', 'skyyrose' ),
			'description' => esc_html__( 'Full-bleed editorial section between the hero and press strip on the homepage. Disabled by default — enable to show.', 'skyyrose' ),
			'priority'    => 55,
		)
	);

	// ── Enabled toggle ────────────────────────────────────────────────────────
	$wp_customize->add_setting(
		'skyyrose_drop_block_enabled',
		array(
			'default'           => false,
			'transport'         => 'refresh',
			'sanitize_callback' => 'skyyrose_ce_sanitize_checkbox',
		)
	);
	$wp_customize->add_control(
		'skyyrose_drop_block_enabled',
		array(
			'type'    => 'checkbox',
			'label'   => esc_html__( 'Enable Drop Block', 'skyyrose' ),
			'section' => 'skyyrose_drop_block',
		)
	);

	// ── Title ─────────────────────────────────────────────────────────────────
	$wp_customize->add_setting(
		'skyyrose_drop_block_title',
		array(
			'default'           => '',
			'transport'         => 'refresh',
			'sanitize_callback' => 'sanitize_text_field',
		)
	);
	$wp_customize->add_control(
		'skyyrose_drop_block_title',
		array(
			'type'    => 'text',
			'label'   => esc_html__( 'Drop Title', 'skyyrose' ),
			'section' => 'skyyrose_drop_block',
		)
	);

	// ── Collection slug ───────────────────────────────────────────────────────
	// Use a select when skyyrose_brand_collections() is available (loaded from
	// inc/brand.generated.php, which is first in $skyyrose_core_includes).
	// Fall back to a text field so the block works without the generated file.
	$wp_customize->add_setting(
		'skyyrose_drop_block_collection',
		array(
			'default'           => '',
			'transport'         => 'refresh',
			'sanitize_callback' => 'sanitize_title',
		)
	);

	if ( function_exists( 'skyyrose_brand_collections' ) ) {
		$choices = array( '' => esc_html__( '— none —', 'skyyrose' ) );
		foreach ( skyyrose_brand_collections() as $slug => $label ) {
			$choices[ sanitize_title( $slug ) ] = esc_html( $label );
		}
		$wp_customize->add_control(
			'skyyrose_drop_block_collection',
			array(
				'type'    => 'select',
				'label'   => esc_html__( 'Collection', 'skyyrose' ),
				'section' => 'skyyrose_drop_block',
				'choices' => $choices,
			)
		);
	} else {
		// brand.generated.php not available — accept a raw slug string.
		$wp_customize->add_control(
			'skyyrose_drop_block_collection',
			array(
				'type'        => 'text',
				'label'       => esc_html__( 'Collection Slug', 'skyyrose' ),
				'description' => esc_html__( 'e.g. signature, black-rose, love-hurts, kids-capsule', 'skyyrose' ),
				'section'     => 'skyyrose_drop_block',
			)
		);
	}

	// ── Image ─────────────────────────────────────────────────────────────────
	$wp_customize->add_setting(
		'skyyrose_drop_block_image',
		array(
			'default'           => '',
			'transport'         => 'refresh',
			'sanitize_callback' => 'esc_url_raw',
		)
	);
	$wp_customize->add_control(
		new WP_Customize_Image_Control(
			$wp_customize,
			'skyyrose_drop_block_image',
			array(
				'label'   => esc_html__( 'Drop Image', 'skyyrose' ),
				'section' => 'skyyrose_drop_block',
			)
		)
	);

	// ── CTA text ──────────────────────────────────────────────────────────────
	$wp_customize->add_setting(
		'skyyrose_drop_block_cta_text',
		array(
			'default'           => '',
			'transport'         => 'refresh',
			'sanitize_callback' => 'sanitize_text_field',
		)
	);
	$wp_customize->add_control(
		'skyyrose_drop_block_cta_text',
		array(
			'type'    => 'text',
			'label'   => esc_html__( 'CTA Text', 'skyyrose' ),
			'section' => 'skyyrose_drop_block',
		)
	);

	// ── CTA URL ───────────────────────────────────────────────────────────────
	$wp_customize->add_setting(
		'skyyrose_drop_block_cta_url',
		array(
			'default'           => '',
			'transport'         => 'refresh',
			'sanitize_callback' => 'esc_url_raw',
		)
	);
	$wp_customize->add_control(
		'skyyrose_drop_block_cta_url',
		array(
			'type'    => 'url',
			'label'   => esc_html__( 'CTA URL', 'skyyrose' ),
			'section' => 'skyyrose_drop_block',
		)
	);
}
add_action( 'customize_register', 'skyyrose_ce_drop_block_customize_register', 20 );

/**
 * Sanitize a Customizer checkbox to a boolean.
 *
 * @since 1.6.8
 *
 * @param mixed $value Raw Customizer input.
 * @return bool True when the checkbox is checked.
 */
function skyyrose_ce_sanitize_checkbox( $value ) {
	return (bool) $value;
}

/**
 * Render the Drop Block section on the homepage.
 *
 * Outputs nothing when disabled or when no title and no image are set —
 * prevents an empty <section> from appearing in the DOM.
 *
 * Called directly from front-page.php between the hero and press strip.
 * No countdown timers — campaign urgency is not SkyyRose canon.
 *
 * @since 1.6.8
 * @return void
 */
function skyyrose_render_drop_block() {
	// Gate 1: admin must enable the block before it appears.
	if ( ! get_theme_mod( 'skyyrose_drop_block_enabled', false ) ) {
		return;
	}

	$title      = get_theme_mod( 'skyyrose_drop_block_title', '' );
	$collection = get_theme_mod( 'skyyrose_drop_block_collection', '' );
	$image_url  = get_theme_mod( 'skyyrose_drop_block_image', '' );
	$cta_text   = get_theme_mod( 'skyyrose_drop_block_cta_text', '' );
	$cta_url    = get_theme_mod( 'skyyrose_drop_block_cta_url', '' );

	// Gate 2: need at least one content element to render.
	if ( empty( $title ) && empty( $image_url ) ) {
		return;
	}

	// Build aria-label from title so the landmark is self-describing.
	$aria_label = $title ? $title : __( 'Drop', 'skyyrose' );
	?>
	<section
		class="sr-drop-block rv"
		<?php if ( $collection ) : ?>data-collection="<?php echo esc_attr( $collection ); ?>"<?php endif; ?>
		aria-label="<?php echo esc_attr( $aria_label ); ?>"
	>
		<?php if ( $image_url ) : ?>
			<div class="sr-drop-block__media" aria-hidden="true">
				<img
					src="<?php echo esc_url( $image_url ); ?>"
					alt=""
					loading="lazy"
					decoding="async"
				/>
				<div class="sr-drop-block__overlay" aria-hidden="true"></div>
			</div>
		<?php endif; ?>

		<div class="sr-drop-block__content">
			<?php if ( $collection ) : ?>
				<p class="sr-drop-block__collection-label">
					<?php
					// Display slug as readable label — replace hyphens with spaces and uppercase.
					echo esc_html( strtoupper( str_replace( '-', ' ', $collection ) ) );
					?>
				</p>
			<?php endif; ?>

			<?php if ( $title ) : ?>
				<h2 class="sr-drop-block__title"><?php echo esc_html( $title ); ?></h2>
			<?php endif; ?>

			<?php if ( $cta_url ) : ?>
				<a href="<?php echo esc_url( $cta_url ); ?>" class="sr-drop-block__cta btn-sweep btn-press">
					<?php
					// Use explicit CTA text when set; fall back to generic "Shop Now".
					echo $cta_text ? esc_html( $cta_text ) : esc_html__( 'Shop Now', 'skyyrose' );
					?>
				</a>
			<?php endif; ?>
		</div>
	</section>
	<?php
}

/*
--------------------------------------------------------------
 * 3. Sticky ATC Bar — Editorial PDP HTML Emitter
 *--------------------------------------------------------------*/

/**
 * Emit the sticky ATC bar HTML for editorial product pages.
 *
 * This outputs the fixed-position bar and its inline controller script.
 * The JS uses IntersectionObserver to show the bar after .sr-ed__encounter
 * (Chapter 1) scrolls out of the viewport — no main-thread scroll listeners.
 *
 * Called from template-parts/product-detail-editorial.php just before </article>.
 * Requires: $product (WC_Product), $price_html (string) from the calling template.
 *
 * @since 1.6.8
 *
 * @param WC_Product $product    WooCommerce product object.
 * @param string     $price_html Already-escaped price HTML from $product->get_price_html().
 * @return void
 */
function skyyrose_render_ed_sticky_atc( $product, $price_html ) {
	if ( ! $product || ! is_a( $product, 'WC_Product' ) ) {
		return;
	}
	?>
	<?php // ── Sticky ATC Bar ─────────────────────────────────────────────────── ?>
	<?php // Fixed bottom bar (mobile) / bottom-right pill (desktop). ?>
	<?php // z-index 900: site header overlay is 1000. ?>
	<?php // aria-hidden toggled by JS — starts hidden so screen readers skip it until visible. ?>
	<aside
		id="sr-ed-sticky-atc"
		class="sr-sticky-atc"
		aria-hidden="true"
		aria-label="<?php esc_attr_e( 'Quick add to bag', 'skyyrose' ); ?>"
	>
		<span class="sr-sticky-atc__name"><?php echo esc_html( $product->get_name() ); ?></span>
		<span class="sr-sticky-atc__price"><?php echo wp_kses_post( $price_html ); ?></span>
		<?php
		// Size select is populated from the WC variations form by JS.
		// Starts hidden; JS reveals it once options are populated.
		?>
		<select
			class="sr-sticky-atc__size"
			aria-label="<?php esc_attr_e( 'Select size', 'skyyrose' ); ?>"
			style="display:none;"
		>
			<option value=""><?php esc_html_e( 'Size', 'skyyrose' ); ?></option>
		</select>
		<button type="button" class="sr-sticky-atc__btn">
			<?php esc_html_e( 'Add to Bag', 'skyyrose' ); ?>
		</button>
	</aside>
	<script>
	/* Editorial sticky ATC — IntersectionObserver visibility + size select mirror.
	   Inline because this controller is tightly coupled to the editorial template's
	   DOM structure and is not shared with any other template. No innerHTML used. */
	(function () {
		'use strict';

		var bar     = document.getElementById('sr-ed-sticky-atc');
		var trigger = document.querySelector('.sr-ed__encounter');
		if (!bar || !trigger) { return; }

		/* Show bar once Chapter 1 (.sr-ed__encounter) is no longer in view.
		   IntersectionObserver is threshold:0 so any pixel leaving viewport fires. */
		var obs = new IntersectionObserver(function (entries) {
			var gone = !entries[0].isIntersecting;
			bar.classList.toggle('is-visible', gone);
			/* Flip aria-hidden so the bar is reachable by keyboard/screen reader
			   only when it is visually present. */
			bar.setAttribute('aria-hidden', gone ? 'false' : 'true');
		}, { threshold: 0 });
		obs.observe(trigger);

		/* Size select wiring ─────────────────────────────────────────────── */
		var stickySel = bar.querySelector('.sr-sticky-atc__size');

		function getMainSel() {
			/* WooCommerce renders the attribute select with attribute_pa_size for
			   taxonomy attributes and attribute_size for custom attributes. */
			return document.querySelector('.variations_form select[name="attribute_pa_size"]')
				|| document.querySelector('.variations_form select[name="attribute_size"]');
		}

		function populateStickySelect() {
			var mainSel = getMainSel();
			if (!mainSel || !stickySel) { return; }

			/* Only populate once — the WC form's options are static HTML
			   rendered server-side and present in the DOM when this script runs. */
			if (stickySel.options.length > 1) { return; }

			/* Build using createElement + textContent — no innerHTML. */
			Array.prototype.slice.call(mainSel.options).forEach(function (opt) {
				var o = document.createElement('option');
				o.value = opt.value;
				o.textContent = opt.textContent;
				stickySel.appendChild(o);
			});

			/* Mirror current selection and reveal the select. */
			stickySel.value = mainSel.value;
			if (stickySel.options.length > 1) {
				stickySel.style.display = '';
			}
		}

		/* Run immediately — WC variation form is in the DOM at this point
		   because woocommerce_template_single_add_to_cart() was called above. */
		populateStickySelect();

		/* Push sticky select choice back to WC form and trigger variation
		   resolution so WC updates stock, price, and button state. */
		if (stickySel) {
			stickySel.addEventListener('change', function () {
				var mainSel = getMainSel();
				if (mainSel) {
					mainSel.value = stickySel.value;
					/* Native event for vanilla JS listeners. */
					mainSel.dispatchEvent(new Event('change', { bubbles: true }));
					/* jQuery event for the WooCommerce variation engine. */
					if (window.jQuery) { window.jQuery(mainSel).trigger('change'); }
				}
			});
		}

		/* Keep sticky select in sync when WC resolves or resets a variation. */
		if (window.jQuery) {
			window.jQuery(document).on('found_variation reset_data', '.variations_form', function () {
				var mainSel = getMainSel();
				if (mainSel && stickySel) { stickySel.value = mainSel.value; }
			});
		}

		/* "Add to Bag" — scroll to real ATC then submit the cart form.
		   Slight delay (350ms) lets smooth-scroll animation settle before
		   WC form focus shift, avoiding a jarring layout jump. */
		var addBtn = bar.querySelector('.sr-sticky-atc__btn');
		if (addBtn) {
			addBtn.addEventListener('click', function (e) {
				e.preventDefault();
				var atcWrap  = document.querySelector('.sr-ed__atc-wrap');
				var cartForm = document.querySelector('form.cart');
				if (atcWrap) {
					atcWrap.scrollIntoView({ behavior: 'smooth', block: 'center' });
				}
				setTimeout(function () {
					if (cartForm) {
						/* requestSubmit() triggers native form validation;
						   .submit() bypasses it — prefer requestSubmit when available. */
						if (typeof cartForm.requestSubmit === 'function') {
							cartForm.requestSubmit();
						} else {
							cartForm.submit();
						}
					}
				}, 350);
			});
		}
	}());
	</script>
	<?php
}
