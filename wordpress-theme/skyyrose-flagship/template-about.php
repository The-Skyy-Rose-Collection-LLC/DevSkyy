<?php
/**
 * Template Name: About
 *
 * Cinematic chapter-based brand story for SkyyRose.
 * Sections: Hero -> Ch I (Rebrand) -> Ch II (Collections) ->
 *           Ch III (Timeline) -> Press -> Mission -> Community.
 * @package SkyyRose_Flagship
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
$origin_quote = __( '&ldquo;I didn&rsquo;t start SkyyRose to be in fashion. I started it because my daughter deserved to see her father build something real &mdash; something that proved luxury doesn&rsquo;t have to come from privilege. It can grow from concrete.&rdquo;', 'skyyrose-flagship' );
$origin_cite  = __( '&mdash; Corey Foster, Founder &amp; CEO', 'skyyrose-flagship' );

$origin_paragraphs = array(
	__( 'SkyyRose was never just a clothing brand. It was a promise &mdash; born in Oakland, forged by a single father who refused to let his circumstances write his daughter&rsquo;s story. <strong>Corey Foster</strong> named the brand after his reason for everything: his daughter, <strong>Skyy Rose</strong>.', 'skyyrose-flagship' ),
	__( 'The rebrand is the full realization of that promise. Three collections, each with its own world, its own story, its own identity &mdash; unified under one crown. This is Oakland-born luxury streetwear that doesn&rsquo;t apologize for where it came from. It <strong>celebrates</strong> it.', 'skyyrose-flagship' ),
	__( 'Fashion was always self-expression for Corey. Growing up in Oakland&rsquo;s toughest neighborhoods, what you wore said everything &mdash; who you were, where you were going, what you refused to accept. SkyyRose carries that energy into every thread, every stitch, every rose.', 'skyyrose-flagship' ),
	__( 'This isn&rsquo;t a business strategy. It&rsquo;s a <strong>bloodline</strong>. The Hurts family name runs through every collection. A grandmother&rsquo;s legacy. A father&rsquo;s drive. A daughter&rsquo;s future. That&rsquo;s the foundation no competitor can replicate.', 'skyyrose-flagship' ),
);

/* Chapter II — The Collections. */
$collections = array(
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5Z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',
		'title' => __( 'Signature Collection', 'skyyrose-flagship' ),
		'text'  => __( 'The origin. The crown. The first rose and script logo that started it all. Signature is the foundation of SkyyRose &mdash; where the brand was born and where every thread carries the weight of a father&rsquo;s promise.', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
		'title' => __( 'Black Rose Collection', 'skyyrose-flagship' ),
		'text'  => __( 'Born from a single conviction: &ldquo;every man would wear a black rose.&rdquo; Masculine elegance meets the beauty of black. Dark, powerful, unapologetic &mdash; Black Rose redefines what luxury streetwear looks like through a lens of strength and sophistication.', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
		'title' => __( 'Love Hurts Collection', 'skyyrose-flagship' ),
		'text'  => __( 'The Hurts bloodline. A grandmother&rsquo;s legacy. Told from Beast&rsquo;s perspective with the enchanted rose at its heart. Love Hurts is the most personal collection &mdash; where family history becomes fashion, and every piece carries the weight of love that endures.', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
		'title' => __( 'Kids Capsule', 'skyyrose-flagship' ),
		'text'  => __( 'Dark, powerful, high-end &mdash; but inviting. The Kids Capsule proves luxury runs in the family. Designed for the next generation with the same uncompromising quality and bold aesthetic that defines SkyyRose. No watered-down versions. Real luxury, young kings and queens.', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
		'title' => __( 'Oakland Authenticity', 'skyyrose-flagship' ),
		'text'  => __( 'Culture created, not imported. Every piece carries the resilience of the Town &mdash; where beauty and grit coexist without apology. Oakland isn&rsquo;t just our origin. It&rsquo;s our identity.', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/><path d="M12 2v1"/></svg>',
		'title' => __( 'Black-Owned, Family-Driven', 'skyyrose-flagship' ),
		'text'  => __( 'Named after a daughter. Built by a father. &ldquo;Hurts&rdquo; is our family name. This brand isn&rsquo;t a business strategy &mdash; it&rsquo;s a bloodline. A source of pride and inspiration for Oakland and beyond.', 'skyyrose-flagship' ),
	),
);

/* Chapter III — Timeline Milestones. */
$timeline_milestones = array(
	array(
		'year'  => '2020',
		'event' => __( 'The Promise', 'skyyrose-flagship' ),
		'desc'  => __( 'With his daughter Skyy Rose on the way, Corey commits to building a brand that would support his family and inspire his community. The Skyy Rose Collection is born from a father&rsquo;s determination.', 'skyyrose-flagship' ),
	),
	array(
		'year'  => '2021',
		'event' => __( 'The Grind', 'skyyrose-flagship' ),
		'desc'  => __( 'Multiple website failures. Scam manufacturers. Sleepless nights balancing fatherhood and business. Every setback becomes fuel. The brand takes shape through sheer persistence.', 'skyyrose-flagship' ),
	),
	array(
		'year'  => '2022',
		'event' => __( 'Three Worlds Emerge', 'skyyrose-flagship' ),
		'desc'  => __( 'The collection launches online. Three distinct collection identities crystallize: SIGNATURE &mdash; the origin and the crown. BLACK ROSE &mdash; masculine elegance born from a conviction. LOVE HURTS &mdash; the Hurts bloodline and Beast&rsquo;s enchanted rose.', 'skyyrose-flagship' ),
	),
	array(
		'year'  => '2023',
		'event' => __( 'National Recognition', 'skyyrose-flagship' ),
		'desc'  => __( 'Featured in Maxim&rsquo;s &ldquo;14 Game-Changing Entrepreneurs to Watch.&rdquo; Spotlighted on The Blox. The Kids Capsule launches in March &mdash; dark, powerful, high-end luxury for the next generation.', 'skyyrose-flagship' ),
	),
	array(
		'year'  => '2024',
		'event' => __( 'Award-Winning', 'skyyrose-flagship' ),
		'desc'  => __( 'Wins Best Bay Area Clothing Line from Best of Best Review. Featured in San Francisco Post, CEO Weekly. The brand&rsquo;s story resonates nationally as proof that vision and fatherhood can coexist at the highest level.', 'skyyrose-flagship' ),
	),
	array(
		'year'  => '2025&ndash;26',
		'event' => __( 'The Rebrand', 'skyyrose-flagship' ),
		'desc'  => __( 'The full vision realized. Three collection worlds with dedicated immersive experiences. AI-powered operations. Custom luxury platform. SkyyRose evolves from a promise into a legacy &mdash; Oakland-born luxury streetwear. Luxury grows from concrete.', 'skyyrose-flagship' ),
	),
);

/* Press Features. */
$youtube_embed_id = get_theme_mod( 'about_youtube_id', 'Ja11W-g34Zo' );

$press_features = array(
	array(
		'src'      => __( 'Maxim', 'skyyrose-flagship' ),
		'year'     => __( 'February 2023', 'skyyrose-flagship' ),
		'headline' => __( '&ldquo;14 Game-Changing Entrepreneurs to Watch in 2023&rdquo;', 'skyyrose-flagship' ),
		'excerpt'  => __( 'Maxim spotlighted Corey Foster alongside tech founders and multimillion-dollar CEOs as one of the year&rsquo;s most compelling entrepreneurs.', 'skyyrose-flagship' ),
		'url'      => 'https://www.maxim.com/partner/14-game-changing-entrepreneurs-to-watch-in-2023/',
	),
	array(
		'src'      => __( 'CEO Weekly', 'skyyrose-flagship' ),
		'year'     => __( 'October 2024', 'skyyrose-flagship' ),
		'headline' => __( '&ldquo;The Unyielding Journey of a Single Father and Entrepreneur&rdquo;', 'skyyrose-flagship' ),
		'excerpt'  => __( 'CEO Weekly profiled the full arc of Corey&rsquo;s journey &mdash; from growing up in an environment where crime was the norm, to building a brand that embodies hope.', 'skyyrose-flagship' ),
		'url'      => 'https://ceoweekly.com/the-unyielding-journey-of-a-single-father-and-entrepreneur/',
	),
	array(
		'src'      => __( 'San Francisco Post', 'skyyrose-flagship' ),
		'year'     => __( 'August 2024', 'skyyrose-flagship' ),
		'headline' => __( '&ldquo;From Oakland&rsquo;s Streets to Fashion Heights&rdquo;', 'skyyrose-flagship' ),
		'excerpt'  => __( 'The San Francisco Post chronicled how the brand pioneered gender-neutral fashion in the Bay Area, rooted in Oakland&rsquo;s cultural landscape.', 'skyyrose-flagship' ),
		'url'      => 'https://sanfranciscopost.com/the-skyy-rose-collection-from-oaklands-streets-to-fashion-heights/',
	),
	array(
		'src'      => __( 'Best of Best Review', 'skyyrose-flagship' ),
		'year'     => __( 'August 2024', 'skyyrose-flagship' ),
		'headline' => __( '&ldquo;Best Bay Area Clothing Line Award 2024&rdquo;', 'skyyrose-flagship' ),
		'excerpt'  => __( 'SkyyRose was honored with the Best Bay Area Clothing Line award, citing authenticity, innovation, and community impact.', 'skyyrose-flagship' ),
		'url'      => 'https://bestofbestreview.com/awards/the-skyy-rose-collection-best-bay-area-clothing-line-award-2024',
	),
);

$arrow_svg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true" focusable="false"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';

/* Customer Photos. */
$customer_photos = array(
	array(
		'file' => 'customer-kid-black-rose-hoodie-enhanced.webp',
		'alt'  => __( 'Young fan wearing Black Rose hoodie', 'skyyrose-flagship' ),
	),
	array(
		'file' => 'customer-love-hurts-varsity-enhanced.webp',
		'alt'  => __( 'Customer in Love Hurts varsity jacket', 'skyyrose-flagship' ),
	),
	array(
		'file' => 'customer-rose-hoodie-beanie-enhanced.webp',
		'alt'  => __( 'Customer wearing rose hoodie and beanie', 'skyyrose-flagship' ),
	),
	array(
		'file' => 'customer-love-hurts-shorts-enhanced.webp',
		'alt'  => __( 'Customer in Love Hurts shorts', 'skyyrose-flagship' ),
	),
);
?>

<main id="primary" class="site-main abt-page" role="main" tabindex="-1">

	<!-- Hero -->
	<section class="abt-hero" data-scroll-fade aria-label="<?php esc_attr_e( 'About SkyyRose', 'skyyrose-flagship' ); ?>">
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
					 alt="<?php esc_attr_e( 'SkyyRose — Oakland-born luxury streetwear. Luxury grows from concrete.', 'skyyrose-flagship' ); ?>"
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
			<span><?php esc_html_e( 'Scroll', 'skyyrose-flagship' ); ?></span>
			<div class="abt-hero__scroll-line"></div>
		</div>
	</section>

	<!-- Chapter I — The Rebrand -->
	<section class="abt-chapter abt-origin" id="origin" aria-label="<?php esc_attr_e( 'The Rebrand Story', 'skyyrose-flagship' ); ?>">
		<span class="abt-chapter__num rv-split-char" aria-hidden="true">01</span>
		<div class="abt-chapter__container">
			<p class="abt-chapter__label rv-blur-down"><?php esc_html_e( 'Chapter I', 'skyyrose-flagship' ); ?></p>
			<h2 class="abt-chapter__title rv-clip-up">
				<?php echo wp_kses( __( 'The Birth of<br>the Rebrand', 'skyyrose-flagship' ), $allowed_inline ); ?>
			</h2>

			<div class="abt-origin__grid">
				<div class="abt-origin__quote rv rv-d2">
					<blockquote>
						<?php echo wp_kses( $origin_quote, $allowed_inline ); ?>
					</blockquote>
					<cite><?php echo wp_kses( $origin_cite, $allowed_inline ); ?></cite>

					<?php
					$founder_img = get_theme_file_path( 'assets/images/founder-portrait.jpg' );
					if ( file_exists( $founder_img ) ) :
					?>
						<figure class="abt-origin__portrait rv rv-d3">
							<img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/founder-portrait.jpg' ) ); ?>"
								 alt="<?php esc_attr_e( 'Corey Foster — Founder & CEO of SkyyRose', 'skyyrose-flagship' ); ?>"
								 loading="lazy" width="600" height="750">
							<figcaption><?php esc_html_e( 'Corey Foster, Founder & CEO', 'skyyrose-flagship' ); ?></figcaption>
						</figure>
					<?php endif; ?>
				</div>
				<div class="abt-origin__text rv rv-d3">
					<?php foreach ( $origin_paragraphs as $para ) : ?>
						<p><?php echo wp_kses( $para, $allowed_inline ); ?></p>
					<?php endforeach; ?>
				</div>
			</div>
		</div>
	</section>

	<!-- Photo Divider 1 -->
	<?php
	$story1_img = get_theme_file_path( 'assets/images/about-story-1.jpg' );
	if ( file_exists( $story1_img ) ) :
	?>
		<div class="abt-divider rv" aria-hidden="true">
			<img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/about-story-1.jpg' ) ); ?>"
				 alt="" loading="lazy" width="1920" height="600">
			<div class="abt-divider__overlay"></div>
		</div>
	<?php endif; ?>

	<!-- Chapter II — The Collections -->
	<section class="abt-chapter abt-values" aria-label="<?php esc_attr_e( 'The Collections', 'skyyrose-flagship' ); ?>">
		<span class="abt-chapter__num rv-split-char" aria-hidden="true">02</span>
		<div class="abt-chapter__container">
			<p class="abt-chapter__label rv-blur-down"><?php esc_html_e( 'Chapter II', 'skyyrose-flagship' ); ?></p>
			<h2 class="abt-chapter__title rv-clip-up">
				<?php echo wp_kses( __( 'Three Worlds,<br>One Crown', 'skyyrose-flagship' ), $allowed_inline ); ?>
			</h2>

			<div class="abt-values__grid">
				<?php foreach ( $collections as $ci => $col ) :
					$delay = 'rv-d' . ( ( $ci % 3 ) + 1 );
				?>
					<div class="abt-val-card rv <?php echo esc_attr( $delay ); ?>">
						<div class="abt-val-card__icon" aria-hidden="true">
							<?php echo wp_kses( $col['icon'], array( 'svg' => array( 'viewBox' => true, 'fill' => true, 'stroke' => true, 'class' => true, 'aria-hidden' => true, 'width' => true, 'height' => true, 'xmlns' => true ), 'path' => array( 'd' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true, 'stroke-linecap' => true, 'stroke-linejoin' => true ), 'circle' => array( 'cx' => true, 'cy' => true, 'r' => true, 'fill' => true ), 'line' => array( 'x1' => true, 'y1' => true, 'x2' => true, 'y2' => true, 'stroke' => true, 'stroke-width' => true ), 'polyline' => array( 'points' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true ), 'rect' => array( 'x' => true, 'y' => true, 'width' => true, 'height' => true, 'rx' => true, 'ry' => true, 'fill' => true, 'stroke' => true ) ) ); ?>
						</div>
						<h3 class="abt-val-card__title"><?php echo esc_html( $col['title'] ); ?></h3>
						<p class="abt-val-card__text"><?php echo wp_kses( $col['text'], $allowed_inline ); ?></p>
					</div>
				<?php endforeach; ?>
			</div>
		</div>
	</section>

	<!-- Photo Divider 2 -->
	<?php
	$story2_img = get_theme_file_path( 'assets/images/about-story-2.jpg' );
	if ( file_exists( $story2_img ) ) :
	?>
		<div class="abt-divider rv" aria-hidden="true">
			<img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/about-story-2.jpg' ) ); ?>"
				 alt="" loading="lazy" width="1920" height="600">
			<div class="abt-divider__overlay"></div>
		</div>
	<?php endif; ?>

	<!-- Chapter III — Timeline -->
	<section class="abt-chapter abt-timeline" aria-label="<?php esc_attr_e( 'Our Journey', 'skyyrose-flagship' ); ?>">
		<span class="abt-chapter__num rv-split-char" aria-hidden="true">03</span>
		<div class="abt-chapter__container">
			<p class="abt-chapter__label rv-blur-down"><?php esc_html_e( 'Chapter III', 'skyyrose-flagship' ); ?></p>
			<h2 class="abt-chapter__title rv-clip-up"><?php esc_html_e( 'The Journey', 'skyyrose-flagship' ); ?></h2>

			<div class="abt-tl__track" role="list">
				<?php foreach ( $timeline_milestones as $ms ) : ?>
					<div class="abt-tl__node rv" role="listitem">
						<div class="abt-tl__year"><?php echo wp_kses( $ms['year'], $allowed_inline ); ?></div>
						<h3 class="abt-tl__event"><?php echo esc_html( $ms['event'] ); ?></h3>
						<p class="abt-tl__desc"><?php echo wp_kses( $ms['desc'], $allowed_inline ); ?></p>
					</div>
				<?php endforeach; ?>
			</div>
		</div>
	</section>

	<!-- Press Room -->
	<section class="abt-chapter abt-press" id="press" aria-label="<?php esc_attr_e( 'Press & Media', 'skyyrose-flagship' ); ?>">
		<span class="abt-chapter__num rv-split-char" aria-hidden="true">04</span>
		<div class="abt-chapter__container">
			<p class="abt-chapter__label rv-blur-down"><?php esc_html_e( 'Chapter IV', 'skyyrose-flagship' ); ?></p>
			<h2 class="abt-chapter__title rv-clip-up"><?php esc_html_e( 'As Seen In', 'skyyrose-flagship' ); ?></h2>
			<p class="abt-press__intro rv rv-d2">
				<?php esc_html_e( 'The SkyyRose story has been recognized by national and regional publications for its authenticity, innovation, and the power of its origin.', 'skyyrose-flagship' ); ?>
			</p>

			<?php
			$press_img = get_theme_file_path( 'assets/images/press-the-blox-interview.jpg' );
			if ( file_exists( $press_img ) ) :
			?>
				<figure class="abt-press__photo rv rv-d2">
					<img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/press-the-blox-interview.jpg' ) ); ?>"
						 alt="<?php esc_attr_e( 'Corey Foster interviewed on The Blox', 'skyyrose-flagship' ); ?>"
						 loading="lazy" width="1200" height="675">
					<figcaption><?php esc_html_e( 'Corey Foster on The Blox — discussing the SkyyRose story', 'skyyrose-flagship' ); ?></figcaption>
				</figure>
			<?php endif; ?>

			<?php if ( ! empty( $youtube_embed_id ) ) : ?>
				<div class="abt-press__video-wrap rv rv-d3">
					<div class="abt-press__video-header">
						<span><?php esc_html_e( 'Featured Video', 'skyyrose-flagship' ); ?></span>
						<div class="abt-press__video-line" aria-hidden="true"></div>
					</div>
					<div class="abt-press__video-embed">
						<iframe
							src="<?php echo esc_url( 'https://www.youtube.com/embed/' . $youtube_embed_id . '?rel=0&modestbranding=1&color=white' ); ?>"
							title="<?php esc_attr_e( 'SkyyRose Collection — Featured Video', 'skyyrose-flagship' ); ?>"
							frameborder="0"
							allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
							allowfullscreen
							loading="lazy">
						</iframe>
					</div>
				</div>
			<?php endif; ?>
		</div>

		<div class="abt-press__scroll" id="pressScroll">
			<?php foreach ( $press_features as $pi => $pf ) :
				$delay = 'rv-d' . min( $pi + 1, 4 );
			?>
				<article class="abt-press-card rv <?php echo esc_attr( $delay ); ?>">
					<div class="abt-press-card__inner">
						<p class="abt-press-card__src"><?php echo esc_html( $pf['src'] ); ?></p>
						<p class="abt-press-card__year"><?php echo esc_html( $pf['year'] ); ?></p>
						<h3 class="abt-press-card__headline">
							<?php echo wp_kses( $pf['headline'], $allowed_inline ); ?>
						</h3>
						<p class="abt-press-card__excerpt">
							<?php echo wp_kses( $pf['excerpt'], $allowed_inline ); ?>
						</p>
						<?php if ( ! empty( $pf['url'] ) ) : ?>
							<a href="<?php echo esc_url( $pf['url'] ); ?>"
							   class="abt-press-card__link"
							   target="_blank"
							   rel="noopener noreferrer">
								<?php esc_html_e( 'Read Article', 'skyyrose-flagship' ); ?>
								<?php echo wp_kses( $arrow_svg, array( 'svg' => array( 'viewBox' => true, 'fill' => true, 'stroke' => true, 'class' => true, 'aria-hidden' => true, 'width' => true, 'height' => true, 'xmlns' => true, 'focusable' => true ), 'path' => array( 'd' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true, 'stroke-linecap' => true, 'stroke-linejoin' => true ), 'circle' => array( 'cx' => true, 'cy' => true, 'r' => true, 'fill' => true ), 'line' => array( 'x1' => true, 'y1' => true, 'x2' => true, 'y2' => true, 'stroke' => true, 'stroke-width' => true ), 'polyline' => array( 'points' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true ), 'rect' => array( 'x' => true, 'y' => true, 'width' => true, 'height' => true, 'rx' => true, 'ry' => true, 'fill' => true, 'stroke' => true ) ) ); ?>
							</a>
						<?php endif; ?>
					</div>
				</article>
			<?php endforeach; ?>
			<div class="abt-press__scroll-spacer" aria-hidden="true"></div>
		</div>

		<div class="abt-chapter__container">
			<div class="abt-press__hint rv" aria-hidden="true">
				<div class="abt-press__hint-line"></div>
				<span><?php esc_html_e( 'Scroll to explore', 'skyyrose-flagship' ); ?></span>
			</div>
		</div>
	</section>

	<!-- Mission Banner -->
	<section class="abt-mission" aria-label="<?php esc_attr_e( 'Our Mission', 'skyyrose-flagship' ); ?>">
		<div class="rv">
			<p class="abt-chapter__label" style="text-align:center;margin-bottom:24px">
				<?php esc_html_e( 'The Mission', 'skyyrose-flagship' ); ?>
			</p>
			<h2 class="abt-mission__tagline">
				<?php echo wp_kses( __( 'Luxury Grows<br>from Concrete.', 'skyyrose-flagship' ), $allowed_inline ); ?>
			</h2>
			<p class="abt-mission__sub">
				<?php esc_html_e( 'Luxury grows from concrete. Oakland roots, family-driven, fashion as self-expression. Three collections, one bloodline, one crown. This is SkyyRose.', 'skyyrose-flagship' ); ?>
			</p>
			<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="abt-mission__cta">
				<?php esc_html_e( 'Shop the Collection', 'skyyrose-flagship' ); ?>
			</a>
		</div>
	</section>

	<!-- Community — Oakland Roots -->
	<section class="abt-community" aria-label="<?php esc_attr_e( 'Our Community', 'skyyrose-flagship' ); ?>">
		<div class="abt-community__inner">
			<div class="abt-community__content rv">
				<h2 class="abt-community__heading">
					<?php esc_html_e( 'Rooted in Oakland, Built for the World', 'skyyrose-flagship' ); ?>
				</h2>
				<p class="abt-community__text">
					<?php
					echo wp_kses(
						__( 'Oakland isn\'t just where SkyyRose was born&mdash;it\'s <em>who</em> we are. The creativity, the resilience, the unapologetic swagger of the Bay Area runs through every thread of our brand. Fashion was always self-expression here. What you wear says who you are, where you\'re going, what you refuse to accept.', 'skyyrose-flagship' ),
						$allowed_inline
					);
					?>
				</p>
				<p class="abt-community__text">
					<?php
					echo wp_kses(
						__( 'SkyyRose is family-driven at its core. The Hurts bloodline, a grandmother\'s legacy, a father\'s promise to his daughter&mdash;that\'s the foundation. We give back because it\'s in our DNA. Whether partnering with local Oakland artists, supporting youth programs, or spotlighting the voices that inspire our collections&mdash;SkyyRose exists to lift up the community that lifted us.', 'skyyrose-flagship' ),
						$allowed_inline
					);
					?>
				</p>
			</div>
			<div class="abt-community__pillars rv rv-d2">
				<div class="abt-community__pillar">
					<h3><?php esc_html_e( 'Local Artists', 'skyyrose-flagship' ); ?></h3>
					<p><?php esc_html_e( 'Collaborating with Oakland creatives to bring fresh perspectives to every collection and campaign.', 'skyyrose-flagship' ); ?></p>
				</div>
				<div class="abt-community__pillar">
					<h3><?php esc_html_e( 'Youth Programs', 'skyyrose-flagship' ); ?></h3>
					<p><?php esc_html_e( 'Supporting the next generation of designers and entrepreneurs through mentorship and creative workshops.', 'skyyrose-flagship' ); ?></p>
				</div>
				<div class="abt-community__pillar">
					<h3><?php esc_html_e( 'Luxury Runs in the Family', 'skyyrose-flagship' ); ?></h3>
					<p><?php esc_html_e( 'From the Kids Capsule to every mainline collection, SkyyRose proves that quality, vision, and ambition are inherited. The next generation wears the crown too.', 'skyyrose-flagship' ); ?></p>
				</div>
			</div>
		</div>

		<?php
		$has_photos = false;
		foreach ( $customer_photos as $photo ) {
			if ( file_exists( get_theme_file_path( 'assets/images/customers/' . $photo['file'] ) ) ) {
				$has_photos = true;
				break;
			}
		}

		if ( $has_photos ) :
		?>
			<div class="abt-community__gallery rv rv-d3">
				<p class="abt-community__gallery-label"><?php esc_html_e( 'The SkyyRose Family', 'skyyrose-flagship' ); ?></p>
				<div class="abt-community__photos">
					<?php foreach ( $customer_photos as $photo ) :
						$photo_path = get_theme_file_path( 'assets/images/customers/' . $photo['file'] );
						if ( file_exists( $photo_path ) ) :
					?>
						<figure class="abt-community__photo">
							<img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/customers/' . $photo['file'] ) ); ?>"
								 alt="<?php echo esc_attr( $photo['alt'] ); ?>"
								 loading="lazy" width="400" height="500">
						</figure>
					<?php
						endif;
					endforeach;
					?>
				</div>
			</div>
		<?php endif; ?>
	</section>

</main>

<?php
get_footer();
