<?php
/**
 * Template Name: Experiences Hub
 *
 * Hub page that links to all four immersive 3D collection experiences.
 * Imagery and copy sourced entirely from per-collection sot.json — no
 * hardcoded paths. Uses the unified rv-* IntersectionObserver reveal system.
 *
 * Linked experience slugs (confirmed from Template Name headers):
 *   /experience-black-rose/     → template-immersive-black-rose.php
 *   /experience-love-hurts/     → template-immersive-love-hurts.php
 *   /experience-signature/      → template-immersive-signature.php
 *   /experience-kids-capsule/   → template-immersive-kids-capsule.php
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
 * Returns the decoded array on success, or an empty array on failure.
 * All downstream code must handle missing keys gracefully.
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
 * Resolve the best available card image path from a SOT array.
 *
 * Priority: imagery.scene_portrait → imagery.lookbook[0] → null.
 * Returns a theme-relative path (without leading slash) suitable for
 * passing to get_template_directory_uri() + '/' . $path.
 *
 * @param array $sot Decoded SOT data.
 * @return string|null Theme-relative asset path, or null if none found.
 */
function skyyrose_experiences_card_image( $sot ) {
	$imagery = isset( $sot['imagery'] ) ? $sot['imagery'] : array();

	// Prefer scene_portrait (collection card / portal art).
	if ( ! empty( $imagery['scene_portrait']['resolved'] ) ) {
		return 'assets/' . ltrim( $imagery['scene_portrait']['resolved'], '/' );
	}

	// Fallback: first lookbook image.
	if ( ! empty( $imagery['lookbook'][0]['resolved'] ) ) {
		return 'assets/' . ltrim( $imagery['lookbook'][0]['resolved'], '/' );
	}

	return null;
}

/**
 * Resolve the canonical lockup image path from a SOT array.
 *
 * Returns a theme-relative path or null.
 *
 * @param array $sot Decoded SOT data.
 * @return string|null Theme-relative asset path, or null if none found.
 */
function skyyrose_experiences_lockup_image( $sot ) {
	$lockup = isset( $sot['lockup'] ) ? $sot['lockup'] : array();

	// display_webp is the canonical first choice.
	if ( ! empty( $lockup['display_webp']['resolved'] ) ) {
		return 'assets/' . ltrim( $lockup['display_webp']['resolved'], '/' );
	}

	// Fallback: source_art resolved path.
	if ( ! empty( $lockup['source_art']['resolved'] ) ) {
		return 'assets/' . ltrim( $lockup['source_art']['resolved'], '/' );
	}

	return null;
}

// ─── Collection Definitions ───────────────────────────────────────────────────
// Each entry maps a URL slug to static metadata + dynamically loaded SOT data.
// The URL slugs are confirmed from _wp_page_template assignments in
// theme-activation-setup.php and the Template Name headers in each template file.

$experiences_collections = array(
	array(
		'slug'            => 'black-rose',
		'name'            => __( 'Black Rose', 'skyyrose' ),
		'experience_slug' => 'experience-black-rose',
		'collection_slug' => 'collection-black-rose',
		'accent'          => '#C0C0C0',
		'bg'              => '#0A0A0A',
	),
	array(
		'slug'            => 'love-hurts',
		'name'            => __( 'Love Hurts', 'skyyrose' ),
		'experience_slug' => 'experience-love-hurts',
		'collection_slug' => 'collection-love-hurts',
		'accent'          => '#DC143C',
		'bg'              => '#0A0A0A',
	),
	array(
		'slug'            => 'signature',
		'name'            => __( 'Signature', 'skyyrose' ),
		'experience_slug' => 'experience-signature',
		'collection_slug' => 'collection-signature',
		'accent'          => '#D4AF37',
		'bg'              => '#0A0A0A',
	),
	array(
		'slug'            => 'kids-capsule',
		'name'            => __( 'Kids Capsule', 'skyyrose' ),
		'experience_slug' => 'experience-kids-capsule',
		'collection_slug' => 'collection-kids-capsule',
		'accent'          => '#B76E79',
		'bg'              => '#0A0A0A',
	),
);

// Enrich each collection entry with SOT-driven imagery and copy.
foreach ( $experiences_collections as &$col ) {
	$sot              = skyyrose_experiences_load_sot( $col['slug'] );
	$col['sot']       = $sot;
	$col['card_img']  = skyyrose_experiences_card_image( $sot );
	$col['lockup']    = skyyrose_experiences_lockup_image( $sot );
	$col['story']     = isset( $sot['story']['seed'] ) ? $sot['story']['seed'] : '';
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

	<?php // ─── Hero ──────────────────────────────────────────────────────────── ?>
	<section class="exp-hero rv-clip-up" aria-labelledby="exp-hub-title">
		<div class="exp-hero__inner sr-container">

			<p class="exp-hero__eyebrow rv-blur">
				<?php esc_html_e( 'Luxury Grows from Concrete.', 'skyyrose' ); ?>
			</p>

			<h1 id="exp-hub-title" class="exp-hero__title">
				<?php esc_html_e( 'Immersive Worlds', 'skyyrose' ); ?>
			</h1>

			<p class="exp-hero__body rv-clip-up">
				<?php esc_html_e( 'Step inside each collection. Four worlds, four stories — built for the garment to be the protagonist.', 'skyyrose' ); ?>
			</p>

		</div>
	</section>

	<?php // ─── Experience Cards Grid ────────────────────────────────────────── ?>
	<section
		class="exp-grid stagger-grid"
		aria-label="<?php esc_attr_e( 'Collection experiences', 'skyyrose' ); ?>"
	>
		<div class="exp-grid__inner sr-container">

			<?php foreach ( $experiences_collections as $col ) : ?>

				<?php
				$card_img_url  = $col['card_img'] ? get_template_directory_uri() . '/' . esc_attr( $col['card_img'] ) : '';
				$lockup_url    = $col['lockup'] ? get_template_directory_uri() . '/' . esc_attr( $col['lockup'] ) : '';
				$exp_url       = home_url( '/' . $col['experience_slug'] . '/' );
				$col_url       = home_url( '/' . $col['collection_slug'] . '/' );
				$accent_hex    = esc_attr( $col['accent'] );
				$story_text    = esc_html( $col['story'] );
				$col_name      = esc_html( $col['name'] );
				$col_data_attr = esc_attr( $col['slug'] );
				?>

				<article
					class="exp-card rv-clip-up magnetic"
					data-collection="<?php echo $col_data_attr; ?>"
					style="--exp-accent: <?php echo $accent_hex; ?>;"
				>
					<?php // Card image (scene portrait or lookbook fallback from SOT). ?>
					<a
						href="<?php echo esc_url( $exp_url ); ?>"
						class="exp-card__media-link"
						tabindex="-1"
						aria-hidden="true"
					>
						<div class="exp-card__media">

							<?php if ( $card_img_url ) : ?>
								<img
									src="<?php echo esc_url( $card_img_url ); ?>"
									alt="<?php
									/* translators: %s: collection name */
									echo esc_attr( sprintf( __( '%s collection world', 'skyyrose' ), $col['name'] ) );
									?>"
									class="exp-card__bg-img"
									loading="lazy"
									decoding="async"
									width="600"
									height="750"
								>
							<?php else : ?>
								<div
									class="exp-card__bg-placeholder"
									style="background: <?php echo esc_attr( $col['bg'] ); ?>;"
									aria-hidden="true"
								></div>
							<?php endif; ?>

							<div class="exp-card__overlay" aria-hidden="true"></div>

						</div>
					</a>

					<div class="exp-card__content">

						<?php // Lockup image (canonical from SOT lockup.display_webp). ?>
						<?php if ( $lockup_url ) : ?>
							<div class="exp-card__lockup" aria-hidden="true">
								<img
									src="<?php echo esc_url( $lockup_url ); ?>"
									alt=""
									class="exp-card__lockup-img"
									loading="lazy"
									decoding="async"
									width="280"
									height="120"
								>
							</div>
						<?php else : ?>
							<h2 class="exp-card__title">
								<?php echo $col_name; ?>
							</h2>
						<?php endif; ?>

						<?php if ( $story_text ) : ?>
							<p class="exp-card__story">
								<?php echo $story_text; ?>
							</p>
						<?php endif; ?>

						<div class="exp-card__actions">

							<a
								href="<?php echo esc_url( $exp_url ); ?>"
								class="exp-card__cta btn-sweep"
								style="--btn-accent: <?php echo $accent_hex; ?>;"
							>
								<?php esc_html_e( 'Enter World', 'skyyrose' ); ?>
								<span class="exp-card__cta-arrow" aria-hidden="true">&rarr;</span>
							</a>

							<a
								href="<?php echo esc_url( $col_url ); ?>"
								class="exp-card__link"
							>
								<?php esc_html_e( 'Shop Collection', 'skyyrose' ); ?>
							</a>

						</div>

					</div>

				</article>

			<?php endforeach; ?>

		</div>
	</section>

	<?php // ─── Brand Sign-Off ───────────────────────────────────────────────── ?>
	<section class="exp-signoff rv-clip-up" aria-label="<?php esc_attr_e( 'Brand statement', 'skyyrose' ); ?>">
		<div class="exp-signoff__inner sr-container">
			<p class="exp-signoff__quote">
				<?php esc_html_e( 'Luxury Grows from Concrete.', 'skyyrose' ); ?>
			</p>
			<a
				href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"
				class="exp-signoff__cta btn-border-draw"
			>
				<?php esc_html_e( 'Pre-Order Now', 'skyyrose' ); ?>
			</a>
		</div>
	</section>

</main>

<?php
get_footer();
