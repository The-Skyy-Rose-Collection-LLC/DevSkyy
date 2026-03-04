<?php
/**
 * Template Name: About
 *
 * Cinematic chapter-based brand story page for SkyyRose.
 * Design: Elite Web Builder v4 — editorial documentary style.
 *
 * Sections: Hero → Chapter I (Origin) → Chapter II (Values) →
 *           Chapter III (Timeline) → Chapter IV (Press Room) →
 *           Mission Banner → Community.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();

/*--------------------------------------------------------------
 * Hero Section Data
 *--------------------------------------------------------------*/
$hero_eyebrow = get_theme_mod( 'about_hero_eyebrow', 'Oakland, California &mdash; Est. 2020' );
$hero_title    = get_theme_mod( 'about_hero_title', 'Named After<br>a Daughter.' );
$hero_title_2  = get_theme_mod( 'about_hero_title_2', 'Built by<br>a Father.' );
$hero_sub      = get_theme_mod(
	'about_hero_sub',
	'The Skyy Rose Collection is what happens when a single father from Oakland decides his daughter deserves a different story.'
);

/*--------------------------------------------------------------
 * Chapter I — The Origin
 *--------------------------------------------------------------*/
$origin_quote  = __( '&ldquo;You ask me this four years ago, I never would&rsquo;ve thought I&rsquo;d be here. I had no drive, lost it all, baby on the way, and was broke. But we knew we had to get it by any means necessary.&rdquo;', 'skyyrose-flagship' );
$origin_cite   = __( '&mdash; Corey Foster, Founder &amp; CEO', 'skyyrose-flagship' );
$origin_paragraphs = array(
	__( 'In the heart of Oakland&rsquo;s toughest neighborhoods, where opportunities are scarce and the wrong path is always the easiest one, <strong>Corey Foster</strong> made a choice. With a daughter on the way, no savings, and a community that had already claimed too many people he loved &mdash; he decided to build something.', 'skyyrose-flagship' ),
	__( 'Not a hustle. Not a side project. A <strong>legacy</strong>.', 'skyyrose-flagship' ),
	__( 'He named it after the reason he couldn&rsquo;t fail: his daughter, <strong>Skyy Rose</strong>. What started as a father&rsquo;s promise became a brand that would redefine what luxury streetwear looks like when it comes from somewhere real.', 'skyyrose-flagship' ),
	__( 'The road was brutal. Failed websites. Manufacturers who took money and delivered nothing. Balancing 3 AM feedings with business plans written on a phone screen. Zero support. Zero guarantees. But Corey had something no setback could take &mdash; <strong>a reason bigger than himself</strong>.', 'skyyrose-flagship' ),
);

/*--------------------------------------------------------------
 * Chapter II — Values (6 pillars)
 *--------------------------------------------------------------*/
$brand_values = array(
	array(
		'icon'  => '&#9830;',
		'title' => __( 'Gender-Neutral Pioneer', 'skyyrose-flagship' ),
		'text'  => __( 'One of the first Bay Area brands to design clothing that transcends gender and age. Fashion without boundaries &mdash; for anyone with taste.', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '&#10022;',
		'title' => __( 'Oakland Authenticity', 'skyyrose-flagship' ),
		'text'  => __( 'Culture created, not imported. Every piece carries the resilience of the Town &mdash; where beauty and grit coexist without apology.', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '&#9829;',
		'title' => __( 'Family at the Core', 'skyyrose-flagship' ),
		'text'  => __( 'Named after a daughter. Built by a father. &ldquo;Hurts&rdquo; is our family name. This brand isn&rsquo;t a business strategy &mdash; it&rsquo;s a bloodline.', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '&#9733;',
		'title' => __( 'Quality Over Quantity', 'skyyrose-flagship' ),
		'text'  => __( 'Every garment is crafted with meticulous attention to detail. This isn&rsquo;t fast fashion. This is armor &mdash; designed to last and built to make a statement.', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '&#9650;',
		'title' => __( 'Black-Owned, Community Built', 'skyyrose-flagship' ),
		'text'  => __( 'A source of pride and inspiration for Oakland. Representing cultural heritage and future potential in every stitch.', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '&#8962;',
		'title' => __( 'Integrity Over Shortcuts', 'skyyrose-flagship' ),
		'text'  => __( 'Where many in the community were led astray, Corey chose the harder path. Every decision reflects the values he&rsquo;s teaching his daughter.', 'skyyrose-flagship' ),
	),
);

/*--------------------------------------------------------------
 * Chapter III — Timeline Milestones
 *--------------------------------------------------------------*/
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
		'event' => __( 'Breaking Through', 'skyyrose-flagship' ),
		'desc'  => __( 'The collection launches online. Word spreads through Oakland, then the Bay Area. Three distinct collections emerge: BLACK ROSE, LOVE HURTS, and SIGNATURE &mdash; each a world of its own.', 'skyyrose-flagship' ),
	),
	array(
		'year'  => '2023',
		'event' => __( 'National Recognition', 'skyyrose-flagship' ),
		'desc'  => __( 'Featured in Maxim&rsquo;s &ldquo;14 Game-Changing Entrepreneurs to Watch.&rdquo; Spotlighted on The Blox. The children&rsquo;s collection launches in March to celebrate Skyy Rose&rsquo;s birthday.', 'skyyrose-flagship' ),
	),
	array(
		'year'  => '2024',
		'event' => __( 'Award-Winning', 'skyyrose-flagship' ),
		'desc'  => __( 'Wins Best Bay Area Clothing Line from Best of Best Review. Featured in San Francisco Post, CEO Weekly. The brand&rsquo;s story resonates nationally as proof that vision and fatherhood can coexist at the highest level.', 'skyyrose-flagship' ),
	),
	array(
		'year'  => '2025&ndash;26',
		'event' => __( 'Full-Stack Luxury', 'skyyrose-flagship' ),
		'desc'  => __( 'Custom marketplace platform. AI-powered operations. Three collection worlds with dedicated product experiences. SkyyRose evolves from a brand into a complete luxury ecosystem.', 'skyyrose-flagship' ),
	),
);

/*--------------------------------------------------------------
 * Chapter IV — Press Features
 *--------------------------------------------------------------*/
$youtube_embed_id = get_theme_mod( 'about_youtube_id', 'Ja11W-g34Zo' );

$press_features = array(
	array(
		'src'      => __( 'Maxim', 'skyyrose-flagship' ),
		'year'     => __( 'February 2023', 'skyyrose-flagship' ),
		'headline' => __( '&ldquo;14 Game-Changing Entrepreneurs to Watch in 2023&rdquo;', 'skyyrose-flagship' ),
		'excerpt'  => __( 'Maxim spotlighted Corey Foster alongside tech founders and multimillion-dollar CEOs as one of the year&rsquo;s most compelling entrepreneurs &mdash; recognizing the SkyyRose Collection as a rising force in streetwear built on resilience and authenticity.', 'skyyrose-flagship' ),
		'url'      => 'https://www.maxim.com/partner/14-game-changing-entrepreneurs-to-watch-in-2023/',
	),
	array(
		'src'      => __( 'CEO Weekly', 'skyyrose-flagship' ),
		'year'     => __( 'October 2024', 'skyyrose-flagship' ),
		'headline' => __( '&ldquo;The Unyielding Journey of a Single Father and Entrepreneur&rdquo;', 'skyyrose-flagship' ),
		'excerpt'  => __( 'CEO Weekly profiled the full arc of Corey&rsquo;s journey &mdash; from growing up in an environment where crime was the norm, to building a brand that embodies hope and hard work while maintaining integrity every step of the way.', 'skyyrose-flagship' ),
		'url'      => 'https://ceoweekly.com/the-unyielding-journey-of-a-single-father-and-entrepreneur/',
	),
	array(
		'src'      => __( 'San Francisco Post', 'skyyrose-flagship' ),
		'year'     => __( 'August 2024', 'skyyrose-flagship' ),
		'headline' => __( '&ldquo;From Oakland&rsquo;s Streets to Fashion Heights&rdquo;', 'skyyrose-flagship' ),
		'excerpt'  => __( 'The San Francisco Post chronicled how the brand pioneered gender-neutral fashion in the Bay Area, creating a line that transcends societal boundaries with versatile, stylish pieces accessible to all &mdash; rooted in Oakland&rsquo;s cultural landscape.', 'skyyrose-flagship' ),
		'url'      => 'https://sanfranciscopost.com/the-skyy-rose-collection-from-oaklands-streets-to-fashion-heights/',
	),
	array(
		'src'      => __( 'Best of Best Review', 'skyyrose-flagship' ),
		'year'     => __( 'August 2024', 'skyyrose-flagship' ),
		'headline' => __( '&ldquo;Best Bay Area Clothing Line Award 2024&rdquo;', 'skyyrose-flagship' ),
		'excerpt'  => __( 'SkyyRose was honored with the Best Bay Area Clothing Line award, recognizing the brand&rsquo;s exceptional contribution to fashion &mdash; citing authenticity, innovation in gender-neutral design, quality craftsmanship, and community impact as deciding factors.', 'skyyrose-flagship' ),
		'url'      => 'https://bestofbestreview.com/awards/the-skyy-rose-collection-best-bay-area-clothing-line-award-2024',
	),
);

/*--------------------------------------------------------------
 * Allowed HTML tags for wp_kses
 *--------------------------------------------------------------*/
$allowed_inline = array(
	'em'     => array(),
	'strong' => array(),
	'br'     => array(),
);

$arrow_svg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true" focusable="false"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
?>

<main id="primary" class="site-main abt-page" role="main" tabindex="-1">

	<!-- ═══ HERO — Cinematic Full-Bleed ═══ -->
	<section class="abt-hero" aria-label="<?php esc_attr_e( 'About SkyyRose', 'skyyrose-flagship' ); ?>">
		<div class="abt-hero__img" aria-hidden="true">
			<?php
			$hero_img = get_theme_file_path( 'assets/images/about-story-0.jpg' );
			if ( file_exists( $hero_img ) ) :
			?>
				<img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/about-story-0.jpg' ) ); ?>"
					 alt="<?php esc_attr_e( 'SkyyRose — luxury streetwear born in Oakland', 'skyyrose-flagship' ); ?>"
					 loading="eager" width="1920" height="1080">
			<?php endif; ?>
		</div>
		<div class="abt-hero__overlay" aria-hidden="true"></div>
		<div class="abt-hero__content">
			<p class="abt-hero__eyebrow rv">
				<?php echo wp_kses( $hero_eyebrow, $allowed_inline ); ?>
			</p>
			<h1 class="abt-hero__title rv rv-d1">
				<span><?php echo wp_kses( $hero_title, $allowed_inline ); ?></span>
				<?php echo wp_kses( $hero_title_2, $allowed_inline ); ?>
			</h1>
			<p class="abt-hero__sub rv rv-d2">
				<?php echo wp_kses( $hero_sub, $allowed_inline ); ?>
			</p>
		</div>
		<div class="abt-hero__scroll rv rv-d3" aria-hidden="true">
			<span><?php esc_html_e( 'Scroll', 'skyyrose-flagship' ); ?></span>
			<div class="abt-hero__scroll-line"></div>
		</div>
	</section>

	<!-- ═══ CHAPTER I — The Origin ═══ -->
	<section class="abt-chapter abt-origin" id="origin" aria-label="<?php esc_attr_e( 'The Origin Story', 'skyyrose-flagship' ); ?>">
		<span class="abt-chapter__num" aria-hidden="true">01</span>
		<div class="abt-chapter__container">
			<p class="abt-chapter__label rv"><?php esc_html_e( 'Chapter I', 'skyyrose-flagship' ); ?></p>
			<h2 class="abt-chapter__title rv rv-d1">
				<?php echo wp_kses( __( 'From Concrete<br>to Collection', 'skyyrose-flagship' ), $allowed_inline ); ?>
			</h2>

			<div class="abt-origin__grid">
				<div class="abt-origin__quote rv rv-d2">
					<blockquote>
						<?php echo wp_kses( $origin_quote, $allowed_inline ); ?>
					</blockquote>
					<cite><?php echo wp_kses( $origin_cite, $allowed_inline ); ?></cite>
				</div>
				<div class="abt-origin__text rv rv-d3">
					<?php foreach ( $origin_paragraphs as $para ) : ?>
						<p><?php echo wp_kses( $para, $allowed_inline ); ?></p>
					<?php endforeach; ?>
				</div>
			</div>
		</div>
	</section>

	<!-- ═══ CHAPTER II — Values ═══ -->
	<section class="abt-chapter abt-values" aria-label="<?php esc_attr_e( 'Our Values', 'skyyrose-flagship' ); ?>">
		<span class="abt-chapter__num" aria-hidden="true">02</span>
		<div class="abt-chapter__container">
			<p class="abt-chapter__label rv"><?php esc_html_e( 'Chapter II', 'skyyrose-flagship' ); ?></p>
			<h2 class="abt-chapter__title rv rv-d1">
				<?php echo wp_kses( __( 'What We<br>Stand On', 'skyyrose-flagship' ), $allowed_inline ); ?>
			</h2>

			<div class="abt-values__grid">
				<?php foreach ( $brand_values as $vi => $val ) :
					$delay = 'rv-d' . ( ( $vi % 3 ) + 1 );
				?>
					<div class="abt-val-card rv <?php echo esc_attr( $delay ); ?>">
						<div class="abt-val-card__icon" aria-hidden="true">
							<?php
							// HTML entity for decorative icon — safe to output unescaped.
							echo $val['icon']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
							?>
						</div>
						<h3 class="abt-val-card__title"><?php echo esc_html( $val['title'] ); ?></h3>
						<p class="abt-val-card__text"><?php echo wp_kses( $val['text'], $allowed_inline ); ?></p>
					</div>
				<?php endforeach; ?>
			</div>
		</div>
	</section>

	<!-- ═══ CHAPTER III — Timeline ═══ -->
	<section class="abt-chapter abt-timeline" aria-label="<?php esc_attr_e( 'Our Journey', 'skyyrose-flagship' ); ?>">
		<span class="abt-chapter__num" aria-hidden="true">03</span>
		<div class="abt-chapter__container">
			<p class="abt-chapter__label rv"><?php esc_html_e( 'Chapter III', 'skyyrose-flagship' ); ?></p>
			<h2 class="abt-chapter__title rv rv-d1"><?php esc_html_e( 'The Journey', 'skyyrose-flagship' ); ?></h2>

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

	<!-- ═══ CHAPTER IV — Press Room ═══ -->
	<section class="abt-chapter abt-press" aria-label="<?php esc_attr_e( 'Press &amp; Media', 'skyyrose-flagship' ); ?>">
		<span class="abt-chapter__num" aria-hidden="true">04</span>
		<div class="abt-chapter__container">
			<p class="abt-chapter__label rv"><?php esc_html_e( 'Chapter IV', 'skyyrose-flagship' ); ?></p>
			<h2 class="abt-chapter__title rv rv-d1"><?php esc_html_e( 'As Seen In', 'skyyrose-flagship' ); ?></h2>
			<p class="abt-press__intro rv rv-d2">
				<?php esc_html_e( 'The SkyyRose story has been recognized by national and regional publications for its authenticity, innovation, and the power of its origin.', 'skyyrose-flagship' ); ?>
			</p>

			<!-- Featured Video -->
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

		<!-- Horizontal Scroll Press Cards -->
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
								<?php echo $arrow_svg; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- static SVG ?>
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

	<!-- ═══ MISSION BANNER ═══ -->
	<section class="abt-mission" aria-label="<?php esc_attr_e( 'Our Mission', 'skyyrose-flagship' ); ?>">
		<div class="rv">
			<p class="abt-chapter__label" style="text-align:center;margin-bottom:24px">
				<?php esc_html_e( 'The Mission', 'skyyrose-flagship' ); ?>
			</p>
			<h2 class="abt-mission__tagline">
				<?php echo wp_kses( __( 'Luxury Grows<br>from Concrete', 'skyyrose-flagship' ), $allowed_inline ); ?>
			</h2>
			<p class="abt-mission__sub">
				<?php esc_html_e( 'Where Bay Area authenticity meets high-fashion aesthetics. Where a father\'s love becomes a brand\'s foundation. Where fashion is a force for change.', 'skyyrose-flagship' ); ?>
			</p>
			<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="abt-mission__cta">
				<?php esc_html_e( 'Shop the Collection', 'skyyrose-flagship' ); ?>
			</a>
		</div>
	</section>

	<!-- ═══ COMMUNITY — Oakland Roots ═══ -->
	<section class="abt-community" aria-label="<?php esc_attr_e( 'Our Community', 'skyyrose-flagship' ); ?>">
		<div class="abt-community__inner">
			<div class="abt-community__content rv">
				<h2 class="abt-community__heading">
					<?php esc_html_e( 'Rooted in Oakland, Connected to the World', 'skyyrose-flagship' ); ?>
				</h2>
				<p class="abt-community__text">
					<?php
					echo wp_kses(
						__( 'Oakland isn\'t just where SkyyRose was born&mdash;it\'s <em>who</em> we are. The creativity, the resilience, the unapologetic swagger of the Bay Area runs through every thread of our brand. Our community is our foundation, and we never forget that.', 'skyyrose-flagship' ),
						$allowed_inline
					);
					?>
				</p>
				<p class="abt-community__text">
					<?php
					echo wp_kses(
						__( 'We give back because it\'s in our DNA. Whether it\'s partnering with local Oakland artists, supporting youth creative programs, or spotlighting the voices that inspire our collections&mdash;SkyyRose exists to lift up the community that lifted us.', 'skyyrose-flagship' ),
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
					<h3><?php esc_html_e( 'Sustainable Future', 'skyyrose-flagship' ); ?></h3>
					<p><?php esc_html_e( 'Committed to responsible production, ethical sourcing, and building a brand that respects both people and planet.', 'skyyrose-flagship' ); ?></p>
				</div>
			</div>
		</div>
	</section>

</main><!-- #primary -->

<?php
get_footer();
