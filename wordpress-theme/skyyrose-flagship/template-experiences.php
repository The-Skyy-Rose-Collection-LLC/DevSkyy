<?php
/**
 * Template Name: Experiences Hub
 *
 * The "Immersive Worlds" hub (/experiences/). A type-led Concrete Index: each
 * collection is a numbered row whose oversized name is the primary affordance,
 * with its SOT scene art shown as an always-visible panel + canonical lockup.
 * All imagery + copy sourced from per-collection sot.json — no hardcoded paths.
 *
 * Linked experience slugs (confirmed from Template Name headers):
 *   /experience-signature/      → template-immersive-signature.php
 *   /experience-black-rose/     → template-immersive-black-rose.php
 *   /experience-love-hurts/     → template-immersive-love-hurts.php
 *   /experience-kids-capsule/   → template-immersive-kids-capsule.php
 *
 * Styling: assets/css/experiences.css (enqueued for slug 'experiences').
 *
 * @package SkyyRose
 * @since   1.2.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Load and parse a collection sot.json file.
 *
 * @param string $slug Collection directory slug (e.g. 'black-rose').
 * @return array Decoded SOT data or empty array.
 */
function skyyrose_experiences_load_sot( $slug ) {
	$sot_path = SKYYROSE_DIR . '/data/collections/' . sanitize_file_name( $slug ) . '/sot.json';
	if ( ! file_exists( $sot_path ) ) {
		return array();
	}
	$raw = file_get_contents( $sot_path ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents
	if ( false === $raw ) {
		return array();
	}
	$decoded = json_decode( $raw, true );
	return is_array( $decoded ) ? $decoded : array();
}

/**
 * Resolve the cinematic scene image for the hub row panel.
 *
 * Priority: imagery.hero_backdrop → imagery.scene_portrait → imagery.lookbook[0].
 * Returns a theme-relative path (no leading slash) or null.
 *
 * @param array $sot Decoded SOT data.
 * @return string|null Theme-relative asset path, or null if none found.
 */
function skyyrose_experiences_card_image( $sot ) {
	$imagery = isset( $sot['imagery'] ) ? $sot['imagery'] : array();

	// Prefer the cinematic hero backdrop for the at-a-glance scene panel.
	if ( ! empty( $imagery['hero_backdrop']['resolved'] ) ) {
		return 'assets/' . ltrim( $imagery['hero_backdrop']['resolved'], '/' );
	}

	// Then the collection portal / scene portrait.
	if ( ! empty( $imagery['scene_portrait']['resolved'] ) ) {
		return 'assets/' . ltrim( $imagery['scene_portrait']['resolved'], '/' );
	}

	// Last: first lookbook image (e.g. Kids Capsule, which has no scene yet).
	if ( ! empty( $imagery['lookbook'][0]['resolved'] ) ) {
		return 'assets/' . ltrim( $imagery['lookbook'][0]['resolved'], '/' );
	}

	return null;
}

/**
 * Resolve the canonical lockup image path from a SOT array.
 *
 * @param array $sot Decoded SOT data.
 * @return string|null Theme-relative asset path, or null if none found.
 */
function skyyrose_experiences_lockup_image( $sot ) {
	$lockup = isset( $sot['lockup'] ) ? $sot['lockup'] : array();

	if ( ! empty( $lockup['display_webp']['resolved'] ) ) {
		return 'assets/' . ltrim( $lockup['display_webp']['resolved'], '/' );
	}

	if ( ! empty( $lockup['source_art']['resolved'] ) ) {
		return 'assets/' . ltrim( $lockup['source_art']['resolved'], '/' );
	}

	return null;
}

// ─── Collection definitions (canonical 01–04 order) ───────────────────────────
$experiences_collections = array(
	array(
		'slug'            => 'signature',
		'name'            => __( 'Signature', 'skyyrose' ),
		'experience_slug' => 'experience-signature',
		'fallback_hook'   => __( 'The beginning of it all — where it started from.', 'skyyrose' ),
	),
	array(
		'slug'            => 'black-rose',
		'name'            => __( 'Black Rose', 'skyyrose' ),
		'experience_slug' => 'experience-black-rose',
		'fallback_hook'   => __( 'Defining beauty through the color black.', 'skyyrose' ),
	),
	array(
		'slug'            => 'love-hurts',
		'name'            => __( 'Love Hurts', 'skyyrose' ),
		'experience_slug' => 'experience-love-hurts',
		'fallback_hook'   => __( 'Beauty and the Beast — told from the Beast\'s side.', 'skyyrose' ),
	),
	array(
		'slug'            => 'kids-capsule',
		'name'            => __( 'Kids Capsule', 'skyyrose' ),
		'experience_slug' => 'experience-kids-capsule',
		'fallback_hook'   => __( 'The heir to the throne.', 'skyyrose' ),
	),
);

// Enrich each entry with SOT-driven imagery + copy.
foreach ( $experiences_collections as &$col ) {
	$sot             = skyyrose_experiences_load_sot( $col['slug'] );
	$col['card_img'] = skyyrose_experiences_card_image( $sot );
	$col['lockup']   = skyyrose_experiences_lockup_image( $sot );
	$seed            = isset( $sot['story']['seed'] ) ? trim( (string) $sot['story']['seed'] ) : '';
	$col['hook']     = '' !== $seed ? $seed : $col['fallback_hook'];
}
unset( $col );

get_header();
?>

<main
	id="primary"
	class="site-main experiences-hub"
	data-collection="signature"
	role="main"
	tabindex="-1"
>

	<?php // ─── Kicker ──────────────────────────────────────────────────────── ?>
	<section class="exp-kicker">
		<p class="exp-kicker__eyebrow"><?php esc_html_e( 'Immersive Worlds', 'skyyrose' ); ?></p>
		<h1 class="exp-kicker__title"><?php esc_html_e( 'Enter the Collection', 'skyyrose' ); ?></h1>
	</section>

	<?php // ─── Index ───────────────────────────────────────────────────────── ?>
	<ol class="exp-index" role="list">

		<?php
		$exp_i = 0;
		foreach ( $experiences_collections as $col ) :
			++$exp_i;
			$scene_url  = $col['card_img'] ? get_template_directory_uri() . '/' . $col['card_img'] : '';
			$lockup_url = $col['lockup'] ? get_template_directory_uri() . '/' . $col['lockup'] : '';
			$exp_url    = home_url( '/' . $col['experience_slug'] . '/' );
			?>

			<li class="exp-index__row" data-collection="<?php echo esc_attr( $col['slug'] ); ?>">
				<a
					class="exp-index__link"
					href="<?php echo esc_url( $exp_url ); ?>"
					aria-label="<?php
					/* translators: %s: collection name */
					echo esc_attr( sprintf( __( 'Enter the %s world', 'skyyrose' ), $col['name'] ) );
					?>"
				>
					<span class="exp-index__num" aria-hidden="true"><?php echo esc_html( sprintf( '%02d', $exp_i ) ); ?></span>

					<span class="exp-index__name">
						<span class="exp-index__name-text"><?php echo esc_html( $col['name'] ); ?></span>
						<?php if ( $col['hook'] ) : ?>
							<span class="exp-index__hook"><?php echo esc_html( $col['hook'] ); ?></span>
						<?php endif; ?>
					</span>

					<span class="exp-index__scene">
						<?php if ( $scene_url ) : ?>
							<img
								class="exp-index__scene-img"
								src="<?php echo esc_url( $scene_url ); ?>"
								alt=""
								aria-hidden="true"
								loading="lazy"
								decoding="async"
								width="1280"
								height="720"
							>
						<?php endif; ?>
						<?php if ( $lockup_url ) : ?>
							<img
								class="exp-index__lockup"
								src="<?php echo esc_url( $lockup_url ); ?>"
								alt=""
								aria-hidden="true"
								loading="lazy"
								decoding="async"
								width="128"
								height="64"
							>
						<?php endif; ?>
					</span>

					<span class="exp-index__caret" aria-hidden="true">&rarr;</span>
				</a>
			</li>

		<?php endforeach; ?>

	</ol>

	<?php // ─── Sign-off ────────────────────────────────────────────────────── ?>
	<section class="exp-signoff" aria-label="<?php esc_attr_e( 'Brand statement', 'skyyrose' ); ?>">
		<p class="exp-signoff__quote"><?php esc_html_e( 'Luxury Grows from Concrete.', 'skyyrose' ); ?></p>
		<a
			href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"
			class="exp-signoff__cta btn-border-draw"
		>
			<?php esc_html_e( 'Pre-Order Now', 'skyyrose' ); ?>
		</a>
	</section>

</main>

<?php
get_footer();
