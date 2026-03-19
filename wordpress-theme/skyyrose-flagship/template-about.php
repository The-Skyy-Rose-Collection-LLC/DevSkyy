<?php
/**
 * Template Name: About
 * Impeccable Luxury Refinement
 */

defined( 'ABSPATH' ) || exit;
get_header();

// Hero Data
$hero_img = get_theme_file_uri('assets/images/homepage-story-founder.webp');
?>

<main id="primary" class="site-main abt-page" role="main">

	<!-- Hero -->
	<section class="abt-hero">
		<div class="abt-hero__img">
			<img src="<?php echo esc_url($hero_img); ?>" alt="SkyyRose Origin" fetchpriority="high">
		</div>
		<div class="abt-hero__overlay"></div>
		<div class="abt-hero__content">
			<p class="abt-hero__eyebrow rv-blur-down">Oakland, California — Est. 2020</p>
			<h1 class="abt-hero__title rv-clip-up">
				<span>The Origin</span>
				Luxury Grows<br>from Concrete.
			</h1>
			<p class="abt-hero__sub rv-blur">
				Oakland-born luxury streetwear. Built by a father. Named after a daughter. Four collections, one bloodline — this is the birth of the rebrand.
			</p>
		</div>
	</section>

	<!-- Origin / Founder Story -->
	<section class="abt-origin">
		<div class="abt-origin__inner">
			<div class="abt-origin__quote rv-clip-up">
				<blockquote>“I didn’t start SkyyRose to be in fashion. I started it because my daughter deserved to see her father build something real — something that proved luxury doesn’t have to come from privilege. It can grow from concrete.”</blockquote>
				<span class="abt-origin__cite">— Corey Foster, Founder & CEO</span>
			</div>
			<div class="abt-origin__prose rv-blur">
				<p>SkyyRose was never just a clothing brand. It was a promise — born in Oakland, forged by a single father who refused to let his circumstances write his daughter's story. <strong>Corey Foster</strong> named the brand after his reason for everything: his daughter, <strong>Skyy Rose</strong>.</p>
				<p>The rebrand is the full realization of that promise. Four collections, each with its own world, its own story, its own identity — unified under one crown. This is Oakland-born luxury streetwear that doesn't apologize for where it came from. It <strong>celebrates</strong> it.</p>
				<p>Fashion was always self-expression for Corey. Growing up in Oakland's toughest neighborhoods, what you wore said everything — who you were, where you were going, what you refused to accept. SkyyRose carries that energy into every thread, every stitch, every rose.</p>
				<p>This isn't a business strategy. It's a <strong>bloodline</strong>. The Hurts family name runs through every collection. A grandmother's legacy. A father's drive. A daughter's future. That's the foundation no competitor can replicate.</p>
			</div>
		</div>
	</section>

	<!-- 3D Collections Portals -->
	<?php get_template_part('template-parts/about/collections-grid'); ?>

	<!-- Timeline -->
	<section class="abt-timeline">
		<div class="abt-timeline__inner">
			<div class="abt-col-header rv-clip-up">
				<h2>The Blueprint</h2>
				<p>From the streets to the runway.</p>
			</div>
			<div class="abt-timeline__grid">
				<div class="abt-milestone rv-clip-up">
					<div class="abt-milestone__year">2020</div>
					<h3 class="abt-milestone__title">The Promise</h3>
					<p class="abt-milestone__desc">With his daughter Skyy Rose on the way, Corey commits to building a brand that would support his family and inspire his community. The Skyy Rose Collection is born.</p>
				</div>
				<div class="abt-milestone rv-clip-up">
					<div class="abt-milestone__year">2022</div>
					<h3 class="abt-milestone__title">Three Worlds Emerge</h3>
					<p class="abt-milestone__desc">The collection launches online. Three distinct collection identities crystallize: SIGNATURE, BLACK ROSE, and LOVE HURTS.</p>
				</div>
				<div class="abt-milestone rv-clip-up">
					<div class="abt-milestone__year">2024</div>
					<h3 class="abt-milestone__title">Award-Winning</h3>
					<p class="abt-milestone__desc">Wins Best Oakland Clothing Line. Featured in San Francisco Post, CEO Weekly. The brand's story resonates nationally as proof that vision and fatherhood can coexist at the highest level.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Press -->
	<section class="abt-press">
		<div class="abt-col-header rv-clip-up">
			<h2>Press</h2>
		</div>
		<div class="abt-press__grid">
			<a href="https://www.maxim.com/" target="_blank" class="abt-press-card rv-clip-up">
				<div class="abt-press-card__meta">
					<span class="abt-press-card__src">Maxim</span>
					<span>Feb 2023</span>
				</div>
				<h3 class="abt-press-card__title">“14 Game-Changing Entrepreneurs to Watch in 2023”</h3>
				<p class="abt-press-card__desc">Maxim spotlighted Corey Foster alongside tech founders and multimillion-dollar CEOs as one of the year’s most compelling entrepreneurs.</p>
				<span class="abt-press-card__link">Read Article →</span>
			</a>
			<a href="https://ceoweekly.com/" target="_blank" class="abt-press-card rv-clip-up">
				<div class="abt-press-card__meta">
					<span class="abt-press-card__src">CEO Weekly</span>
					<span>Oct 2024</span>
				</div>
				<h3 class="abt-press-card__title">“The Unyielding Journey of a Single Father and Entrepreneur”</h3>
				<p class="abt-press-card__desc">CEO Weekly profiled the full arc of Corey’s journey — from growing up in an environment where crime was the norm, to building a brand that embodies hope.</p>
				<span class="abt-press-card__link">Read Article →</span>
			</a>
		</div>
	</section>

	<!-- Mission -->
	<section class="abt-mission rv-clip-up">
		<h2>Luxury Grows<br>from Concrete.</h2>
	</section>

</main>

<?php get_footer(); ?>
