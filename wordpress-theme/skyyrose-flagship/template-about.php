<?php
/**
 * Template Name: About
 *
 * Cinematic chapter-based brand story for SkyyRose.
 * Sections: Hero -> Ch I (Rebrand) -> Ch II (Collections) ->
 *           Ch III (Timeline) -> Press -> Mission -> Community.
 *
 * @package SkyyRose
 * @since   4.1.0
 */

defined( 'ABSPATH' ) || exit;

get_header();

/* Allowed HTML for wp_kses throughout the template. */
$allowed_inline = array(
	'em'     => array(),
	'strong' => array(),
	'br'     => array(),
);

/* Hero Section Data. */
$hero_eyebrow = get_theme_mod( 'about_hero_eyebrow', 'Oakland, California &mdash; Est. 2020' );
/* Hardcoded — Customizer DB may have stale "Where Love Meets Luxury" value */
$hero_title   = 'Luxury Grows<br>from Concrete.';
$hero_title_2 = 'Luxury Grows<br>from Concrete.';
$hero_sub     = get_theme_mod(
	'about_hero_sub',
	'Oakland-born luxury streetwear. Built by a father. Named after a daughter. Three collections, one bloodline &mdash; this is the birth of the rebrand.'
);

/* Chapter I — The Rebrand. */
$origin_quote = __( '&ldquo;I didn&rsquo;t start SkyyRose to be in fashion. I started it because my daughter deserved to see her father build something real &mdash; something that proved luxury doesn&rsquo;t have to come from privilege. It can grow from concrete.&rdquo;', 'skyyrose' );
$origin_cite  = __( '&mdash; Corey Foster, Founder &amp; CEO', 'skyyrose' );

$origin_paragraphs = array(
	__( 'SkyyRose was never just a clothing brand. It was a promise &mdash; born in Oakland, forged by a single father who refused to let his circumstances write his daughter&rsquo;s story. <strong>Corey Foster</strong> named the brand after his reason for everything: his daughter, <strong>Skyy Rose</strong>.', 'skyyrose' ),
	__( 'The rebrand is the full realization of that promise. Three collections, each with its own world, its own story, its own identity &mdash; unified under one crown. This is Oakland-born luxury streetwear that doesn&rsquo;t apologize for where it came from. It <strong>celebrates</strong> it.', 'skyyrose' ),
	__( 'Fashion was always self-expression for Corey. Growing up in Oakland&rsquo;s toughest neighborhoods, what you wore said everything &mdash; who you were, where you were going, what you refused to accept. SkyyRose carries that energy into every thread, every stitch, every rose.', 'skyyrose' ),
	__( 'This isn&rsquo;t a business strategy. It&rsquo;s a <strong>bloodline</strong>. The Hurts family name runs through every collection. A grandmother&rsquo;s legacy. A father&rsquo;s drive. A daughter&rsquo;s future. That&rsquo;s the foundation no competitor can replicate.', 'skyyrose' ),
);

/* Chapter II — The Collections. */
$collections = array(
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5Z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',
		'title' => __( 'Signature Collection', 'skyyrose' ),
		'text'  => __( 'The origin. The crown. The first rose and script logo that started it all. Signature is the foundation of SkyyRose &mdash; where the brand was born and where every thread carries the weight of a father&rsquo;s promise.', 'skyyrose' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
		'title' => __( 'Black Rose Collection', 'skyyrose' ),
		'text'  => __( 'Born from a single conviction: &ldquo;every man would wear a black rose.&rdquo; Masculine elegance meets the beauty of black. Dark, powerful, unapologetic &mdash; Black Rose redefines what luxury streetwear looks like through a lens of strength and sophistication.', 'skyyrose' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
		'title' => __( 'Love Hurts Collection', 'skyyrose' ),
		'text'  => __( 'The Hurts bloodline. A grandmother&rsquo;s legacy. Told from Beast&rsquo;s perspective with the enchanted rose at its heart. Love Hurts is the most personal collection &mdash; where family history becomes fashion, and every piece carries the weight of love that endures.', 'skyyrose' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
		'title' => __( 'Kids Capsule', 'skyyrose' ),
		'text'  => __( 'Dark, powerful, high-end &mdash; but inviting. The Kids Capsule proves luxury runs in the family. Designed for the next generation with the same uncompromising quality and bold aesthetic that defines SkyyRose. No watered-down versions. Real luxury, young kings and queens.', 'skyyrose' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
		'title' => __( 'Oakland Authenticity', 'skyyrose' ),
		'text'  => __( 'Culture created, not imported. Every piece carries the resilience of the Town &mdash; where beauty and grit coexist without apology. Oakland isn&rsquo;t just our origin. It&rsquo;s our identity.', 'skyyrose' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/><path d="M12 2v1"/></svg>',
		'title' => __( 'Black-Owned, Family-Driven', 'skyyrose' ),
		'text'  => __( 'Named after a daughter. Built by a father. &ldquo;Hurts&rdquo; is our family name. This brand isn&rsquo;t a business strategy &mdash; it&rsquo;s a bloodline. A source of pride and inspiration for Oakland and beyond.', 'skyyrose' ),
	),
);

/* Chapter III — Timeline Milestones. */
$timeline_milestones = array(
	array(
		'year'  => '2020',
		'event' => __( 'The Promise', 'skyyrose' ),
		'desc'  => __( 'With his daughter Skyy Rose on the way, Corey commits to building a brand that would support his family and inspire his community. The Skyy Rose Collection is born from a father&rsquo;s determination.', 'skyyrose' ),
	),
	array(
		'year'  => '2021',
		'event' => __( 'The Grind', 'skyyrose' ),
		'desc'  => __( 'Multiple website failures. Scam manufacturers. Sleepless nights balancing fatherhood and business. Every setback becomes fuel. The brand takes shape through sheer persistence.', 'skyyrose' ),
	),
	array(
		'year'  => '2022',
		'event' => __( 'Three Worlds Emerge', 'skyyrose' ),
		'desc'  => __( 'The collection launches online. Three distinct collection identities crystallize: SIGNATURE &mdash; the origin and the crown. BLACK ROSE &mdash; masculine elegance born from a conviction. LOVE HURTS &mdash; the Hurts bloodline and Beast&rsquo;s enchanted rose.', 'skyyrose' ),
	),
	array(
		'year'  => '2023',
		'event' => __( 'National Recognition', 'skyyrose' ),
		'desc'  => __( 'Featured in Maxim&rsquo;s &ldquo;14 Game-Changing Entrepreneurs to Watch.&rdquo; Spotlighted on The Blox. The Kids Capsule launches in March &mdash; dark, powerful, high-end luxury for the next generation.', 'skyyrose' ),
	),
	array(
		'year'  => '2024',
		'event' => __( 'Award-Winning', 'skyyrose' ),
		'desc'  => __( 'Wins Best Bay Area Clothing Line from Best of Best Review. Featured in San Francisco Post, CEO Weekly. The brand&rsquo;s story resonates nationally as proof that vision and fatherhood can coexist at the highest level.', 'skyyrose' ),
	),
	array(
		'year'  => '2025&ndash;26',
		'event' => __( 'The Rebrand', 'skyyrose' ),
		'desc'  => __( 'The full vision realized. Three collection worlds with dedicated immersive experiences. AI-powered operations. Custom luxury platform. SkyyRose evolves from a promise into a legacy &mdash; Oakland-born luxury streetwear. Luxury grows from concrete.', 'skyyrose' ),
	),
);

/* Press Features. */
$youtube_embed_id = get_theme_mod( 'about_youtube_id', 'Ja11W-g34Zo' );

$press_features = array(
	array(
		'src'      => __( 'Maxim', 'skyyrose' ),
		'year'     => __( 'February 2023', 'skyyrose' ),
		'headline' => __( '&ldquo;14 Game-Changing Entrepreneurs to Watch in 2023&rdquo;', 'skyyrose' ),
		'excerpt'  => __( 'Maxim spotlighted Corey Foster alongside tech founders and multimillion-dollar CEOs as one of the year&rsquo;s most compelling entrepreneurs.', 'skyyrose' ),
		'url'      => 'https://www.maxim.com/partner/14-game-changing-entrepreneurs-to-watch-in-2023/',
	),
	array(
		'src'      => __( 'CEO Weekly', 'skyyrose' ),
		'year'     => __( 'October 2024', 'skyyrose' ),
		'headline' => __( '&ldquo;The Unyielding Journey of a Single Father and Entrepreneur&rdquo;', 'skyyrose' ),
		'excerpt'  => __( 'CEO Weekly profiled the full arc of Corey&rsquo;s journey &mdash; from growing up in an environment where crime was the norm, to building a brand that embodies hope.', 'skyyrose' ),
		'url'      => 'https://ceoweekly.com/the-unyielding-journey-of-a-single-father-and-entrepreneur/',
	),
	array(
		'src'      => __( 'San Francisco Post', 'skyyrose' ),
		'year'     => __( 'August 2024', 'skyyrose' ),
		'headline' => __( '&ldquo;From Oakland&rsquo;s Streets to Fashion Heights&rdquo;', 'skyyrose' ),
		'excerpt'  => __( 'The San Francisco Post chronicled how the brand pioneered gender-neutral fashion in the Bay Area, rooted in Oakland&rsquo;s cultural landscape.', 'skyyrose' ),
		'url'      => 'https://sanfranciscopost.com/the-skyy-rose-collection-from-oaklands-streets-to-fashion-heights/',
	),
	array(
		'src'      => __( 'Best of Best Review', 'skyyrose' ),
		'year'     => __( 'August 2024', 'skyyrose' ),
		'headline' => __( '&ldquo;Best Bay Area Clothing Line Award 2024&rdquo;', 'skyyrose' ),
		'excerpt'  => __( 'SkyyRose was honored with the Best Bay Area Clothing Line award, citing authenticity, innovation, and community impact.', 'skyyrose' ),
		'url'      => 'https://bestofbestreview.com/awards/the-skyy-rose-collection-best-bay-area-clothing-line-award-2024',
	),
);

$arrow_svg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true" focusable="false"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';

/* Customer Photos. */
$customer_photos = array(
	array(
		'file' => 'customer-kid-black-rose-hoodie-enhanced.webp',
		'alt'  => __( 'Young fan wearing Black Rose hoodie', 'skyyrose' ),
	),
	array(
		'file' => 'customer-love-hurts-varsity-enhanced.webp',
		'alt'  => __( 'Customer in Love Hurts varsity jacket', 'skyyrose' ),
	),
	array(
		'file' => 'customer-rose-hoodie-beanie-enhanced.webp',
		'alt'  => __( 'Customer wearing rose hoodie and beanie', 'skyyrose' ),
	),
	array(
		'file' => 'customer-love-hurts-shorts-enhanced.webp',
		'alt'  => __( 'Customer in Love Hurts shorts', 'skyyrose' ),
	),
);
?>

<main id="primary" class="site-main abt-page" role="main" tabindex="-1">

	<!-- Hero -->
	<section class="abt-hero" data-scroll-fade aria-label="<?php esc_attr_e( 'About SkyyRose', 'skyyrose' ); ?>">
		<div class="abt-hero__img parallax-ken-burns" aria-hidden="true">
			<?php
			$hero_img_custom = get_theme_mod( 'about_hero_image', '' );
			$hero_candidates = array(
				'assets/images/about-hero.jpg',
				'assets/images/about-story-0.jpg',
			);

			$hero_src = '';
			if ( ! empty( $hero_img_custom ) ) {
				$hero_src = $hero_img_custom;
			} else {
				foreach ( $hero_candidates as $candidate ) {
					if ( file_exists( get_theme_file_path( $candidate ) ) ) {
						$hero_src = get_theme_file_uri( $candidate );
						break;
					}
				}
			}

			if ( ! empty( $hero_src ) ) :
				?>
				<img src="<?php echo esc_url( $hero_src ); ?>"
					alt="<?php esc_attr_e( 'SkyyRose — Oakland-born luxury streetwear. Luxury grows from concrete.', 'skyyrose' ); ?>"
					loading="eager" fetchpriority="high" decoding="async" width="1920" height="1080">
			<?php endif; ?>
		</div>
		<div class="abt-hero__overlay" aria-hidden="true"></div>
		<div class="abt-hero__content">
			<p class="abt-hero__eyebrow rv-blur-down">
				<?php echo wp_kses( $hero_eyebrow, $allowed_inline ); ?>
			</p>
			<h1 class="abt-hero__title rv-clip-up">
				<span><?php echo wp_kses( $hero_title, $allowed_inline ); ?></span>
				<?php echo wp_kses( $hero_title_2, $allowed_inline ); ?>
			</h1>
			<p class="abt-hero__sub rv-blur">
				<?php echo wp_kses( $hero_sub, $allowed_inline ); ?>
			</p>
		</div>
		<div class="abt-hero__scroll rv rv-d3" aria-hidden="true">
			<span><?php esc_html_e( 'Scroll', 'skyyrose' ); ?></span>
			<div class="abt-hero__scroll-line"></div>
		</div>
	</section>

	<?php
	/* Chapter I — The Rebrand (Origin Story). */
	get_template_part(
		'template-parts/about/chapter-origin',
		null,
		array(
			'allowed_inline'    => $allowed_inline,
			'origin_quote'      => $origin_quote,
			'origin_cite'       => $origin_cite,
			'origin_paragraphs' => $origin_paragraphs,
		)
	);

	/* Chapter II — The Collections Grid. */
	get_template_part(
		'template-parts/about/collections-grid',
		null,
		array(
			'allowed_inline' => $allowed_inline,
			'collections'    => $collections,
		)
	);

	/* Chapter III — Timeline / The Journey. */
	get_template_part(
		'template-parts/about/timeline',
		null,
		array(
			'allowed_inline'      => $allowed_inline,
			'timeline_milestones' => $timeline_milestones,
		)
	);

	/* Chapter IV — Press Room. */
	get_template_part(
		'template-parts/about/press-section',
		null,
		array(
			'allowed_inline'   => $allowed_inline,
			'youtube_embed_id' => $youtube_embed_id,
			'press_features'   => $press_features,
			'arrow_svg'        => $arrow_svg,
		)
	);

	/* Mission Banner. */
	get_template_part(
		'template-parts/about/mission',
		null,
		array(
			'allowed_inline' => $allowed_inline,
		)
	);

	/* Community — Oakland Roots. */
	get_template_part(
		'template-parts/about/community',
		null,
		array(
			'allowed_inline'  => $allowed_inline,
			'customer_photos' => $customer_photos,
		)
	);
	?>

</main>

<?php
get_footer();
