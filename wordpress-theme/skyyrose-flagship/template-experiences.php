<?php
/**
 * Template Name: Experiences Hub
 *
 * "Immersive Worlds" hub (/experiences/) — "Stacked Cinema": four full-viewport
 * scroll-snap worlds. Each collection's SOT hero fills the block edge-to-edge
 * (Ken-Burns), its name centered in that collection's own script face, framed by
 * faded hairline rules + an accent glow.
 *
 * Imagery resolves through SOT imagery.hero via the `experience-hero` placement
 * contract (inc/image-placements.php) — never stretches, auto-upgrades to the
 * full srcset when the dedicated Midjourney masters land (one identity.json swap).
 *
 * Experience slugs: /experience-{signature,black-rose,love-hurts,kids-capsule}/.
 * Styling: assets/css/experiences.css · Behaviour: assets/js/experiences.js
 * (both slug-gated in inc/enqueue.php).
 *
 * @package SkyyRose
 * @since   1.2.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Load and parse a collection sot.json file.
 *
 * @param string $slug Collection directory slug.
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
 * Resolve the full-bleed hero image (theme-relative) from a SOT array.
 *
 * Priority: imagery.hero → imagery.hero_backdrop → imagery.scene_portrait →
 * imagery.lookbook[0]. Returns a theme-relative path (no leading slash) or null.
 *
 * @param array $sot Decoded SOT data.
 * @return string|null
 */
function skyyrose_experiences_hero( $sot ) {
	$imagery = isset( $sot['imagery'] ) ? $sot['imagery'] : array();
	foreach ( array( 'hero', 'hero_backdrop', 'scene_portrait' ) as $key ) {
		if ( ! empty( $imagery[ $key ]['resolved'] ) ) {
			return 'assets/' . ltrim( $imagery[ $key ]['resolved'], '/' );
		}
	}
	if ( ! empty( $imagery['lookbook'][0]['resolved'] ) ) {
		return 'assets/' . ltrim( $imagery['lookbook'][0]['resolved'], '/' );
	}
	return null;
}

/**
 * Resolve the canonical collection lockup (the brand-script name image).
 *
 * Per brand canon the lockup IS the collection's hero name. Returns
 * [ 'url', 'w', 'h' ] for the transparent display lockup, or null when the
 * collection has none (e.g. Kids Capsule → falls back to type-rendered name).
 *
 * @param array $sot Decoded SOT data.
 * @return array|null
 */
function skyyrose_experiences_lockup( $sot ) {
	$lockup = isset( $sot['lockup'] ) ? $sot['lockup'] : array();
	if ( empty( $lockup['display_webp']['resolved'] ) ) {
		return null;
	}
	$rel = 'assets/' . ltrim( $lockup['display_webp']['resolved'], '/' );
	$abs = SKYYROSE_DIR . '/' . $rel;
	$w   = 0;
	$h   = 0;
	if ( file_exists( $abs ) ) {
		$size = @getimagesize( $abs ); // phpcs:ignore WordPress.PHP.NoSilencedErrors.Discouraged -- size probe is best-effort for CLS.
		if ( $size ) {
			$w = (int) $size[0];
			$h = (int) $size[1];
		}
	}
	return array(
		'url' => get_template_directory_uri() . '/' . $rel,
		'w'   => $w,
		'h'   => $h,
	);
}

// ─── Collections (canonical 01–04 order) ──────────────────────────────────────
$exp_collections = array(
	array(
		'slug'            => 'signature',
		'name'            => __( 'Signature', 'skyyrose' ),
		'experience_slug' => 'experience-signature',
	),
	array(
		'slug'            => 'black-rose',
		'name'            => __( 'Black Rose', 'skyyrose' ),
		'experience_slug' => 'experience-black-rose',
	),
	array(
		'slug'            => 'love-hurts',
		'name'            => __( 'Love Hurts', 'skyyrose' ),
		'experience_slug' => 'experience-love-hurts',
	),
	array(
		'slug'            => 'kids-capsule',
		'name'            => __( 'Kids Capsule', 'skyyrose' ),
		'experience_slug' => 'experience-kids-capsule',
	),
);

foreach ( $exp_collections as &$exp_col ) {
	$exp_sot           = skyyrose_experiences_load_sot( $exp_col['slug'] );
	$exp_col['hero']   = skyyrose_experiences_hero( $exp_sot );
	$exp_col['lockup'] = skyyrose_experiences_lockup( $exp_sot );
}
unset( $exp_col );

get_header();
?>

<main id="primary" class="site-main experiences-hub" data-collection="signature" role="main" tabindex="-1">

	<?php // Right-edge progress rail. ?>
	<nav class="exp-rail" aria-label="<?php esc_attr_e( 'Collection navigation', 'skyyrose' ); ?>">
		<?php foreach ( $exp_collections as $i => $exp_col ) : ?>
			<a
				class="exp-rail__tick<?php echo 0 === $i ? ' is-active' : ''; ?>"
				href="#exp-<?php echo esc_attr( $exp_col['slug'] ); ?>"
				data-index="<?php echo esc_attr( (string) $i ); ?>"
				aria-label="<?php echo esc_attr( $exp_col['name'] ); ?>"
			></a>
		<?php endforeach; ?>
	</nav>

	<p class="exp-tagline" aria-hidden="true"><?php esc_html_e( 'Luxury Grows from Concrete.', 'skyyrose' ); ?></p>

	<?php
	$exp_i = 0;
	foreach ( $exp_collections as $exp_col ) :
		$exp_url  = home_url( '/' . $exp_col['experience_slug'] . '/' );
		$hero_url = $exp_col['hero'] ? get_template_directory_uri() . '/' . $exp_col['hero'] : '';
		$is_first = 0 === $exp_i;
		?>

		<section
			class="exp-block"
			id="exp-<?php echo esc_attr( $exp_col['slug'] ); ?>"
			data-collection="<?php echo esc_attr( $exp_col['slug'] ); ?>"
			data-block="<?php echo esc_attr( (string) $exp_i ); ?>"
			aria-label="<?php
			/* translators: %s: collection name */
			echo esc_attr( sprintf( __( '%s — enter the world', 'skyyrose' ), $exp_col['name'] ) );
			?>"
		>
			<div class="exp-block__scene">
				<?php
				if ( $hero_url ) {
					echo skyyrose_render_picture( // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- helper escapes internally.
						$hero_url,
						'',
						array(
							'placement' => 'experience-hero',
							'loading'   => $is_first ? 'eager' : 'lazy',
							'decoding'  => 'async',
							'aria-hidden' => 'true',
						) + ( $is_first ? array( 'fetchpriority' => 'high' ) : array() )
					);
				}
				?>
			</div>

			<div class="exp-block__overlay" aria-hidden="true"></div>
			<div class="exp-block__tint" aria-hidden="true"></div>

			<div class="exp-block__content">
				<a class="exp-name-frame" href="<?php echo esc_url( $exp_url ); ?>" aria-label="<?php
				/* translators: %s: collection name */
				echo esc_attr( sprintf( __( 'Enter the %s world', 'skyyrose' ), $exp_col['name'] ) );
				?>" style="text-decoration:none;">
					<?php if ( $exp_col['lockup'] ) : ?>
						<img
							class="exp-lockup-img"
							src="<?php echo esc_url( $exp_col['lockup']['url'] ); ?>"
							alt=""
							aria-hidden="true"
							<?php
							if ( $exp_col['lockup']['w'] && $exp_col['lockup']['h'] ) {
								printf( 'width="%d" height="%d" ', (int) $exp_col['lockup']['w'], (int) $exp_col['lockup']['h'] );
							}
							?>
							loading="<?php echo $is_first ? 'eager' : 'lazy'; ?>"
							decoding="async"
						>
					<?php else : ?>
						<span class="exp-name"><?php echo esc_html( $exp_col['name'] ); ?></span>
					<?php endif; ?>
				</a>
				<a class="exp-cue" href="<?php echo esc_url( $exp_url ); ?>">
					<?php esc_html_e( 'Enter', 'skyyrose' ); ?>
					<span class="exp-cue__arrow" aria-hidden="true">&rarr;</span>
				</a>
			</div>

			<?php if ( $is_first ) : ?>
				<div class="exp-hint" aria-hidden="true">
					<span><?php esc_html_e( 'Scroll', 'skyyrose' ); ?></span>
					<span class="exp-hint__chevron"></span>
				</div>
			<?php endif; ?>
		</section>

		<?php
		++$exp_i;
	endforeach;
	?>

</main>

<?php
get_footer();
