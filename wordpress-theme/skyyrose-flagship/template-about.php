<?php
/**
 * Template Name: About
 *
 * Brand story page for SkyyRose — born in Oakland, built with love.
 * Sections: Hero, Story, Collections, Timeline, Stats, Values, Founder, Community.
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();

/*--------------------------------------------------------------
 * Customizer / Theme Mod Defaults
 *
 * Allow the site owner to override brand copy via Customizer.
 * Fallbacks match the canonical source HTML.
 *--------------------------------------------------------------*/
$hero_label       = get_theme_mod( 'about_hero_label', 'Our Story' );
$hero_title       = get_theme_mod( 'about_hero_title', 'Born in Oakland,<br>Built with Love' );
$hero_tagline     = get_theme_mod( 'about_hero_tagline', 'Where the sky meets the rose &mdash; luxury streetwear rooted in Oakland, CA' );
$hero_description = get_theme_mod(
	'about_hero_description',
	'SkyyRose isn\'t just a brand&mdash;it\'s a movement. Born from the vibrant streets of Oakland, California, we pour love into every stitch, every silhouette, every story. We blend authentic street culture with luxury craftsmanship to create pieces that make you feel powerful, beautiful, and unapologetically yourself.'
);

/*--------------------------------------------------------------
 * Story Sections Data (immutable array -- never mutated)
 *--------------------------------------------------------------*/
$story_sections = array(
	array(
		'heading'    => 'The Dream That Started It All',
		'paragraphs' => array(
			'SkyyRose was born in 2019 inside a small Oakland apartment, fueled by a dream that luxury fashion had lost its soul. The founder saw an industry obsessed with exclusivity for exclusivity\'s sake&mdash;price tags that locked people out, designs that felt cold and impersonal, brands that forgot that fashion is supposed to make you <em>feel</em> something.',
			'Growing up on the streets of Oakland taught one fundamental truth: real style comes from authenticity. It comes from wearing your story on your sleeve, literally. Every neighborhood, every corner, every late-night conversation about what it means to dress with intention&mdash;that\'s where SkyyRose found its voice.',
			'We set out to create something different&mdash;a brand that honors both the raw energy of street culture and the meticulous craftsmanship of luxury fashion. A brand where every piece is designed to be armor for those bold enough to be themselves.',
		),
		'highlight'  => '&ldquo;We don\'t just make clothes. We craft armor for those bold enough to be themselves.&rdquo;',
		'image_alt'  => 'SkyyRose brand story &mdash; the dream that started it all in Oakland',
		'reverse'    => false,
	),
	array(
		'heading'    => 'The Name Behind the Brand',
		'paragraphs' => array(
			'Every great brand carries meaning in its name, and SkyyRose is no exception. <em>Skyy</em> represents aspiration&mdash;the limitless ceiling above us, the audacity to reach higher than anyone expects. <em>Rose</em> represents beauty rooted in the earth, grounded in reality, growing through the concrete. Together, they embody reaching high while staying grounded.',
			'The name &ldquo;Love Hurts&rdquo; carries even deeper personal meaning. Hurts is the founder\'s family name, woven into every piece we create. It represents the beautiful pain of growth, the strength found in vulnerability, and the courage to wear your heart openly. When you put on a Love Hurts piece, you\'re carrying a legacy.',
			'Our philosophy is simple but radical: luxury should be accessible. Fashion should tell a story. Quality should never be compromised. And every single person who wears SkyyRose should feel like the most powerful version of themselves.',
		),
		'highlight'  => '',
		'image_alt'  => 'SkyyRose brand story &mdash; sky meets rose, reaching high while staying grounded',
		'reverse'    => true,
	),
	array(
		'heading'    => 'Crafted with Purpose',
		'paragraphs' => array(
			'At SkyyRose, we believe in the power of intentional creation. Every fabric is hand-selected for its feel, its durability, its ability to make you look and feel extraordinary. We work with premium materials&mdash;heavyweight cotton, custom-dyed fabrics, embroidered details, silicone appliqu&eacute;s, and laser-engraved leather&mdash;because our community deserves nothing less.',
			'We are committed to ethical production practices. Our pieces are crafted in small batches, ensuring quality control at every stage. We pay fair wages, we source responsibly, and we reject the fast-fashion model that treats both workers and customers as disposable. When you invest in SkyyRose, you\'re investing in something built to last.',
		),
		'highlight'  => '&ldquo;Luxury is not a price tag. Luxury is the care poured into every detail, the love woven into every seam.&rdquo;',
		'image_alt'  => 'SkyyRose brand story &mdash; craftsmanship and quality materials',
		'reverse'    => false,
	),
);

/*--------------------------------------------------------------
 * Collections Story Data (immutable array)
 *--------------------------------------------------------------*/
$collections_story = array(
	array(
		'name'        => 'Black Rose',
		'slug'        => 'black-rose',
		'tagline'     => 'Elegance in Darkness',
		'description' => 'The Black Rose Collection finds beauty in contrast&mdash;silver-toned luxury against midnight black, gothic elegance that commands every room. Inspired by the strength of roses that bloom in darkness, each piece is an exercise in refined rebellion. Metallic silver accents meet heavyweight construction, creating streetwear that feels like couture.',
		'accent'      => 'silver',
	),
	array(
		'name'        => 'Love Hurts',
		'slug'        => 'love-hurts',
		'tagline'     => 'Wear Your Heart Outside',
		'description' => 'The Love Hurts Collection is passion made wearable&mdash;crimson-drenched streetwear that bleeds emotion. Named after the founder\'s family name, every piece carries the weight of vulnerability and the fire of resilience. From varsity jackets to bomber silhouettes, this collection is for those who aren\'t afraid to feel deeply and dress boldly.',
		'accent'      => 'crimson',
	),
	array(
		'name'        => 'Signature',
		'slug'        => 'signature',
		'tagline'     => 'The Crown Jewel',
		'description' => 'The Signature Collection is where rose gold meets gold&mdash;the ultimate luxury statement. This is SkyyRose at its most refined, its most confident, its most unapologetic. From The Bay Set to the Sherpa Jacket, every piece is designed to be the crown jewel of your wardrobe. This is elevated streetwear for those who know exactly who they are.',
		'accent'      => 'gold',
	),
	array(
		'name'        => 'Kids Capsule',
		'slug'        => 'kids-capsule',
		'tagline'     => 'Passing the Torch',
		'description' => 'The Kids Capsule is about legacy&mdash;passing the torch of self-expression to the next generation. Mini luxury for young trendsetters who deserve to feel just as powerful as their parents. Soft pastels, playful details, and the same uncompromising quality that defines every SkyyRose piece. Because style has no age limit.',
		'accent'      => 'pink',
	),
);

/*--------------------------------------------------------------
 * Timeline Milestones (immutable array)
 *--------------------------------------------------------------*/
$timeline_milestones = array(
	array(
		'year'        => '2019',
		'title'       => 'The Dream Begins',
		'description' => 'Late nights in an Oakland apartment, sketching by lamplight. The first SkyyRose designs take shape on paper&mdash;raw, emotional, and unlike anything else in streetwear. A vision crystallizes: luxury fashion that speaks the language of the streets.',
	),
	array(
		'year'        => '2020',
		'title'       => 'Against All Odds',
		'description' => 'While the world paused, SkyyRose pressed forward. Launching during a global pandemic wasn\'t the plan, but it proved something essential&mdash;this brand was built on resilience. The setbacks became fuel. The isolation became focus. SkyyRose emerged stronger than the dream that started it.',
	),
	array(
		'year'        => '2021',
		'title'       => 'Finding Our Voice',
		'description' => 'BLACK ROSE drops to underground acclaim. Limited pieces sell out within hours, proving the demand for authentic luxury streetwear. The Oakland community rallies behind the brand, and word-of-mouth becomes our most powerful marketing tool. SkyyRose isn\'t a brand anymore&mdash;it\'s a movement.',
	),
	array(
		'year'        => '2022',
		'title'       => 'Growing Roots',
		'description' => 'The product line expands, the team grows, and SkyyRose begins to plant deep roots. New silhouettes, new fabrications, new collaborations with local Oakland artists. The brand identity sharpens into focus: dark luxury with a heartbeat. Every piece tells a story, and more people want to be part of it.',
	),
	array(
		'year'        => '2023',
		'title'       => 'Breaking Through',
		'description' => 'LOVE HURTS launches to a global audience, and the emotional resonance is undeniable. Major collaborations bring national recognition. Features in fashion publications. A presence that extends far beyond Oakland while never losing its roots. The Hurts family name reaches hearts worldwide.',
	),
	array(
		'year'        => '2024',
		'title'       => 'The Flagship Era',
		'description' => 'SIGNATURE completes the vision. Three distinct collections, one unified brand. SkyyRose enters its flagship era with a full digital experience, immersive shopping, and a community that spans continents. The brand doesn\'t just make clothes&mdash;it creates a complete luxury lifestyle.',
	),
	array(
		'year'        => '2025',
		'title'       => 'The Future Is Now',
		'description' => 'New collections on the horizon. Expanded Kids Capsule. International reach. SkyyRose stands at the intersection of where it\'s been and where it\'s going&mdash;and the future has never looked more radiant. The dream that started in an Oakland apartment now lights up the world.',
	),
);

/*--------------------------------------------------------------
 * Brand Stats (immutable array)
 *--------------------------------------------------------------*/
$brand_stats = array(
	array(
		'number' => '28+',
		'label'  => 'Products Designed',
		'detail' => 'Across four distinct collections',
	),
	array(
		'number' => '4',
		'label'  => 'Collections Launched',
		'detail' => 'Each with its own soul and story',
	),
	array(
		'number' => '6',
		'label'  => 'Years of Dedication',
		'detail' => 'From first sketch to flagship',
	),
	array(
		'number' => '1000+',
		'label'  => 'Happy Customers',
		'detail' => 'A growing global community',
	),
);

/*--------------------------------------------------------------
 * Brand Values (immutable array)
 *--------------------------------------------------------------*/
$brand_values = array(
	array(
		'icon'        => '&#x1F339;', /* Rose */
		'title'       => 'Authenticity',
		'description' => 'Every piece tells a real story&mdash;one born from Oakland streets, shaped by lived experience, and refined by an uncompromising vision. We never chase trends or water down our identity for mass appeal. When you wear SkyyRose, you\'re wearing something genuine, something that started as a feeling and became fabric.',
	),
	array(
		'icon'        => '&#x2728;', /* Sparkles */
		'title'       => 'Craftsmanship',
		'description' => 'Premium materials meet meticulous construction in every single piece. From heavyweight cotton to custom-dyed fabrics, from embroidered details to laser-engraved leather&mdash;we obsess over quality so you never have to question it. Our pieces are built to outlast seasons, trends, and fast-fashion cycles.',
	),
	array(
		'icon'        => '&#x1F5A4;', /* Black heart */
		'title'       => 'Community',
		'description' => 'SkyyRose was built by Oakland, for the world. Our roots run deep in the culture, the creativity, and the resilience of the Bay Area. We give back to the communities that raised us, we celebrate the artists who inspire us, and we never forget that a brand is only as strong as the people who believe in it.',
	),
	array(
		'icon'        => '&#x1F4AB;', /* Dizzy / star */
		'title'       => 'Evolution',
		'description' => 'We refuse to stand still. Each collection pushes boundaries further than the last&mdash;new silhouettes, new techniques, new stories to tell. Growth isn\'t comfortable, but it\'s necessary. SkyyRose evolves with its community, always reaching for that next level while staying true to the vision that started it all.',
	),
);

/*--------------------------------------------------------------
 * Founder Section
 *--------------------------------------------------------------*/
$founder_intro = 'Behind every stitch, every colorway, every collection name is a person who poured their entire heart into building something meaningful. SkyyRose wasn\'t born in a boardroom&mdash;it was born from sleepless nights, hand-drawn sketches, and an unshakable belief that luxury streetwear could be different.';

$founder_quotes = array(
	'&ldquo;When I started SkyyRose, I had one goal: create clothes I actually wanted to wear. Clothes that felt like armor, that made a statement without saying a word. I wanted people to put on a SkyyRose piece and feel invincible&mdash;like they could walk into any room and own it.&rdquo;',
	'&ldquo;Growing up in Oakland taught me that style is survival. It\'s how you tell the world who you are before you speak. Every fit is a first impression, every outfit is a declaration. That\'s what SkyyRose is about&mdash;giving people the pieces to tell their story without saying a word.&rdquo;',
	'&ldquo;The LOVE HURTS collection is the most personal to me because it carries my family name. Every piece is a piece of me, shared with everyone brave enough to wear their heart openly. When someone puts on that varsity jacket or that bomber, they\'re carrying my family\'s legacy with them.&rdquo;',
);

$founder_vision = '&ldquo;The future of SkyyRose is bigger than clothing. It\'s about building a world where luxury meets authenticity, where street culture gets the respect it deserves, and where every person who wears our pieces feels like the most powerful version of themselves. We\'re just getting started.&rdquo;';

$founder_signature = get_theme_mod( 'about_founder_signature', '&mdash; The Founder, SkyyRose' );
?>

<main id="primary" class="site-main about-page" role="main">

	<!-- ============================================
	     HERO -- Gradient mesh with radial glow
	     ============================================ -->
	<section class="about-hero" aria-label="<?php esc_attr_e( 'About SkyyRose', 'skyyrose-flagship' ); ?>">
		<div class="about-hero__mesh" aria-hidden="true"></div>
		<div class="about-hero__content about-reveal">
			<span class="about-hero__label">
				<?php echo esc_html( $hero_label ); ?>
			</span>
			<h1 class="about-hero__title">
				<?php
				// Title may contain <br> for line breaks -- allow only <br>.
				echo wp_kses( $hero_title, array( 'br' => array() ) );
				?>
			</h1>
			<p class="about-hero__tagline">
				<?php
				echo wp_kses(
					$hero_tagline,
					array(
						'em'     => array(),
						'strong' => array(),
					)
				);
				?>
			</p>
			<p class="about-hero__description">
				<?php
				echo wp_kses(
					$hero_description,
					array(
						'em'     => array(),
						'strong' => array(),
					)
				);
				?>
			</p>
		</div>
	</section>

	<!-- ============================================
	     STORY SECTIONS -- Alternating 2-column grid
	     ============================================ -->
	<section class="about-story" aria-label="<?php esc_attr_e( 'Our Story', 'skyyrose-flagship' ); ?>">
		<?php
		foreach ( $story_sections as $index => $story ) :
			$grid_class  = 'about-story__grid';
			$grid_class .= $story['reverse'] ? ' about-story__grid--reverse' : '';
			$delay_class = 'about-reveal--delay-' . ( $index + 1 );
			?>
			<div class="<?php echo esc_attr( $grid_class ); ?>">

				<figure class="about-story__image about-reveal <?php echo esc_attr( $story['reverse'] ? 'about-reveal--right' : 'about-reveal--left' ); ?> <?php echo esc_attr( $delay_class ); ?>" aria-hidden="true">
					<?php
					/*
					 * Image placeholder. When actual brand photography is uploaded,
					 * replace with:
					 * <img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/about-story-' . $index . '.jpg' ) ); ?>"
					 *      alt="<?php echo esc_attr( $story['image_alt'] ); ?>"
					 *      loading="lazy" width="600" height="500">
					 */
					?>
				</figure>

				<div class="about-story__content about-reveal <?php echo esc_attr( $story['reverse'] ? 'about-reveal--left' : 'about-reveal--right' ); ?> <?php echo esc_attr( $delay_class ); ?>">
					<h2 class="about-story__heading">
						<?php echo esc_html( $story['heading'] ); ?>
					</h2>

					<?php foreach ( $story['paragraphs'] as $paragraph ) : ?>
						<p class="about-story__text">
							<?php
							echo wp_kses(
								$paragraph,
								array(
									'em'     => array(),
									'strong' => array(),
								)
							);
							?>
						</p>
					<?php endforeach; ?>

					<?php if ( ! empty( $story['highlight'] ) ) : ?>
						<blockquote class="about-story__highlight">
							<?php
							echo wp_kses(
								$story['highlight'],
								array(
									'em'     => array(),
									'strong' => array(),
								)
							);
							?>
						</blockquote>
					<?php endif; ?>
				</div>

			</div>
		<?php endforeach; ?>
	</section>

	<!-- ============================================
	     COLLECTIONS STORY -- What each collection means
	     ============================================ -->
	<section class="about-collections" aria-label="<?php esc_attr_e( 'Our Collections', 'skyyrose-flagship' ); ?>">
		<div class="about-collections__inner">
			<h2 class="about-collections__heading about-reveal">
				<?php esc_html_e( 'The Collections', 'skyyrose-flagship' ); ?>
			</h2>
			<p class="about-collections__intro about-reveal about-reveal--delay-1">
				<?php esc_html_e( 'Each SkyyRose collection is a world unto itself -- a distinct voice, a unique mood, a story waiting to be worn. Together, they form the complete SkyyRose universe.', 'skyyrose-flagship' ); ?>
			</p>

			<div class="about-collections__grid">
				<?php foreach ( $collections_story as $col_index => $collection ) : ?>
					<article class="about-collections__card about-collections__card--<?php echo esc_attr( $collection['accent'] ); ?> about-reveal about-reveal--delay-<?php echo esc_attr( $col_index + 1 ); ?>">
						<div class="about-collections__card-accent" aria-hidden="true"></div>
						<h3 class="about-collections__card-name">
							<?php echo esc_html( $collection['name'] ); ?>
						</h3>
						<span class="about-collections__card-tagline">
							<?php echo esc_html( $collection['tagline'] ); ?>
						</span>
						<p class="about-collections__card-description">
							<?php
							echo wp_kses(
								$collection['description'],
								array(
									'em'     => array(),
									'strong' => array(),
								)
							);
							?>
						</p>
						<a href="<?php echo esc_url( home_url( '/collection/' . $collection['slug'] . '/' ) ); ?>" class="about-collections__card-link">
							<?php
							/* translators: %s: collection name */
							printf( esc_html__( 'Explore %s', 'skyyrose-flagship' ), esc_html( $collection['name'] ) );
							?>
							<span aria-hidden="true">&rarr;</span>
						</a>
					</article>
				<?php endforeach; ?>
			</div>
		</div>
	</section>

	<!-- ============================================
	     TIMELINE -- 2019-2025 milestones
	     ============================================ -->
	<section class="about-timeline" aria-label="<?php esc_attr_e( 'Our Journey', 'skyyrose-flagship' ); ?>">
		<h2 class="about-timeline__heading about-reveal">
			<?php esc_html_e( 'Our Journey', 'skyyrose-flagship' ); ?>
		</h2>
		<p class="about-timeline__subheading about-reveal about-reveal--delay-1">
			<?php esc_html_e( 'From a dream sketched in Oakland to a global movement -- every year has shaped who we are.', 'skyyrose-flagship' ); ?>
		</p>

		<div class="about-timeline__track" role="list">
			<?php foreach ( $timeline_milestones as $milestone_index => $milestone ) : ?>
				<div class="about-timeline__item about-reveal about-reveal--delay-<?php echo esc_attr( min( $milestone_index + 1, 5 ) ); ?>" role="listitem">
					<div class="about-timeline__content">
						<span class="about-timeline__year">
							<?php echo esc_html( $milestone['year'] ); ?>
						</span>
						<h3><?php echo esc_html( $milestone['title'] ); ?></h3>
						<p>
							<?php
							echo wp_kses(
								$milestone['description'],
								array(
									'em'     => array(),
									'strong' => array(),
								)
							);
							?>
						</p>
					</div>
				</div>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ============================================
	     BRAND STATS -- Key numbers
	     ============================================ -->
	<section class="about-stats" aria-label="<?php esc_attr_e( 'Brand Statistics', 'skyyrose-flagship' ); ?>">
		<div class="about-stats__inner">
			<?php foreach ( $brand_stats as $stat_index => $stat ) : ?>
				<div class="about-stats__item about-reveal about-reveal--delay-<?php echo esc_attr( $stat_index + 1 ); ?>">
					<span class="about-stats__number">
						<?php echo esc_html( $stat['number'] ); ?>
					</span>
					<span class="about-stats__label">
						<?php echo esc_html( $stat['label'] ); ?>
					</span>
					<span class="about-stats__detail">
						<?php echo esc_html( $stat['detail'] ); ?>
					</span>
				</div>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ============================================
	     VALUES -- 4 cards grid with expanded content
	     ============================================ -->
	<section class="about-values" aria-label="<?php esc_attr_e( 'Our Values', 'skyyrose-flagship' ); ?>">
		<h2 class="about-values__heading about-reveal">
			<?php esc_html_e( 'What We Stand For', 'skyyrose-flagship' ); ?>
		</h2>
		<p class="about-values__subheading about-reveal about-reveal--delay-1">
			<?php esc_html_e( 'Four principles guide everything we create. They are not just words -- they are promises woven into every piece.', 'skyyrose-flagship' ); ?>
		</p>

		<div class="about-values__grid">
			<?php foreach ( $brand_values as $value_index => $value ) : ?>
				<article class="about-values__card about-reveal about-reveal--delay-<?php echo esc_attr( $value_index + 1 ); ?>">
					<span class="about-values__icon" aria-hidden="true">
						<?php
						// HTML entities for emoji icons -- safe to output.
						echo $value['icon']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- intentional HTML entity.
						?>
					</span>
					<h3><?php echo esc_html( $value['title'] ); ?></h3>
					<p>
						<?php
						echo wp_kses(
							$value['description'],
							array(
								'em'     => array(),
								'strong' => array(),
							)
						);
						?>
					</p>
				</article>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ============================================
	     FOUNDER -- Portrait + rich bio
	     ============================================ -->
	<section class="about-founder" aria-label="<?php esc_attr_e( 'Founder Message', 'skyyrose-flagship' ); ?>">
		<div class="about-founder__inner">

			<figure class="about-founder__portrait about-reveal about-reveal--left" aria-hidden="true">
				<?php
				/*
				 * Founder portrait placeholder. When uploaded, replace with:
				 * <img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/founder-portrait.jpg' ) ); ?>"
				 *      alt="<?php esc_attr_e( 'SkyyRose Founder', 'skyyrose-flagship' ); ?>"
				 *      loading="lazy" width="400" height="500">
				 */
				?>
			</figure>

			<div class="about-founder__text about-reveal about-reveal--right about-reveal--delay-2">
				<h2 class="about-founder__heading">
					<?php esc_html_e( 'A Message from Our Founder', 'skyyrose-flagship' ); ?>
				</h2>

				<p class="about-founder__intro">
					<?php
					echo wp_kses(
						$founder_intro,
						array(
							'em'     => array(),
							'strong' => array(),
						)
					);
					?>
				</p>

				<?php foreach ( $founder_quotes as $quote ) : ?>
					<p class="about-founder__quote">
						<?php
						echo wp_kses(
							$quote,
							array(
								'em'     => array(),
								'strong' => array(),
							)
						);
						?>
					</p>
				<?php endforeach; ?>

				<blockquote class="about-founder__vision">
					<?php
					echo wp_kses(
						$founder_vision,
						array(
							'em'     => array(),
							'strong' => array(),
						)
					);
					?>
				</blockquote>

				<p class="about-founder__signature">
					<?php
					echo wp_kses(
						$founder_signature,
						array(
							'em'     => array(),
							'strong' => array(),
						)
					);
					?>
				</p>
			</div>

		</div>
	</section>

	<!-- ============================================
	     COMMUNITY -- Oakland roots, giving back
	     ============================================ -->
	<section class="about-community" aria-label="<?php esc_attr_e( 'Our Community', 'skyyrose-flagship' ); ?>">
		<div class="about-community__inner">
			<div class="about-community__content about-reveal">
				<h2 class="about-community__heading">
					<?php esc_html_e( 'Rooted in Oakland, Connected to the World', 'skyyrose-flagship' ); ?>
				</h2>
				<p class="about-community__text">
					<?php
					echo wp_kses(
						'Oakland isn\'t just where SkyyRose was born&mdash;it\'s <em>who</em> we are. The creativity, the resilience, the unapologetic swagger of the Bay Area runs through every thread of our brand. Our community is our foundation, and we never forget that.',
						array(
							'em'     => array(),
							'strong' => array(),
						)
					);
					?>
				</p>
				<p class="about-community__text">
					<?php
					echo wp_kses(
						'We give back because it\'s in our DNA. Whether it\'s partnering with local Oakland artists, supporting youth creative programs, or spotlighting the voices that inspire our collections&mdash;SkyyRose exists to lift up the community that lifted us. Every purchase supports not just a brand, but a <em>movement</em>.',
						array(
							'em'     => array(),
							'strong' => array(),
						)
					);
					?>
				</p>
				<p class="about-community__text">
					<?php
					echo wp_kses(
						'The SkyyRose community spans from the streets of East Oakland to cities around the world. We are designers and dreamers, hustlers and artists, parents and kids&mdash;united by a belief that fashion should make you feel something real. When you wear SkyyRose, you\'re part of a family.',
						array(
							'em'     => array(),
							'strong' => array(),
						)
					);
					?>
				</p>
			</div>
			<div class="about-community__pillars about-reveal about-reveal--delay-2">
				<div class="about-community__pillar">
					<h3><?php esc_html_e( 'Local Artists', 'skyyrose-flagship' ); ?></h3>
					<p><?php esc_html_e( 'Collaborating with Oakland creatives to bring fresh perspectives to every collection and campaign.', 'skyyrose-flagship' ); ?></p>
				</div>
				<div class="about-community__pillar">
					<h3><?php esc_html_e( 'Youth Programs', 'skyyrose-flagship' ); ?></h3>
					<p><?php esc_html_e( 'Supporting the next generation of designers and entrepreneurs through mentorship and creative workshops.', 'skyyrose-flagship' ); ?></p>
				</div>
				<div class="about-community__pillar">
					<h3><?php esc_html_e( 'Sustainable Future', 'skyyrose-flagship' ); ?></h3>
					<p><?php esc_html_e( 'Committed to responsible production, ethical sourcing, and building a brand that respects both people and planet.', 'skyyrose-flagship' ); ?></p>
				</div>
			</div>
		</div>
	</section>

</main><!-- #primary -->

<?php
get_footer();
