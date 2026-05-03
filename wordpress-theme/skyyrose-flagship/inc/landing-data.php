<?php
/**
 * Landing Page Data — per-collection content for landing templates.
 *
 * Single source of truth for landing-page copy, images, products, reviews, FAQ,
 * and CTAs. Consumed by template-parts/landing/page.php which renders the
 * shared 10-section landing layout.
 *
 * Adding a new collection landing page:
 *   1. Add an entry to skyyrose_landing_data() keyed by collection slug
 *   2. Create template-landing-{slug}.php as a 16-line stub (see existing examples)
 *   3. Set the page's "Page Attributes > Template" to the new template in WP admin
 *
 * @package SkyyRose
 * @since   7.1.0
 */

defined( 'ABSPATH' ) || exit;

/**
 * Return the full landing-page data array, keyed by collection slug.
 *
 * Each entry is the full content for ONE landing page. The shared partial at
 * template-parts/landing/page.php renders all sections from this data.
 *
 * @since 7.1.0
 * @return array<string, array<string, mixed>>
 */
function skyyrose_landing_data() {
	return array(
		'black-rose'  => array(
			'hero'         => array(
				'badge_text'    => 'Limited Edition — 200 Pieces Per Style',
				'logo_image'    => '/images/hero-overlays/br-brand-script.png',
				'logo_alt'      => 'The Black Rose Collection',
				'subtitle'      => "Darkness isn't the absence of light. It's where you find your own.",
				'countdown'     => '72h',
				'cta_primary'   => array(
					'text' => 'Shop the Drop',
					'url'  => '#products',
				),
				'cta_secondary' => array(
					'text' => 'The Story',
					'url'  => '#story',
				),
			),
			'press'        => array( 'Maxim', 'CEO Weekly', 'SF Post', 'Best of Best Review' ),
			'story'        => array(
				'label'      => 'THE ORIGIN',
				'title'      => "Darkness Isn't the Absence of Light",
				'paragraphs' => array(
					'Corey Foster grew up in Oakland, California — a city that teaches you to build beauty from nothing. Black Rose started as a sketch in a notebook and became something bigger: a collection for people who understand that real luxury comes from adversity, not privilege.',
					'Every piece in this collection carries the weight of that story. The monochrome palette. The thorn motifs. The numbered authentication. This is fashion forged in the fire of real life.',
				),
				'quote'      => "If you asked me four years ago, I never would have thought I'd be here.",
				'cite'       => '— Corey Foster, Founder',
			),
			'parallax'     => '200 Pieces. Numbered. Never Restocked.',
			'product_grid' => array(
				'heading'    => 'The Collection',
				'subheading' => "Limited edition. Numbered. When they're gone, they're gone.",
				'skus'       => array( 'br-004', 'br-005', 'br-006', 'br-010' ),
				'wear_count' => 200,
			),
			'editorial'    => array(
				'heading'   => 'Editorial',
				'top_count' => 3,
				'bot_count' => 2,
			),
			'reviews'      => array(
				'heading' => 'What BLACK ROSE Means to People',
				'items'   => array(
					array(
						'text'   => "The quality is insane. I've washed my hoodie 20+ times and it still looks brand new.",
						'author' => 'Marcus T., Oakland',
					),
					array(
						'text'   => "I've never gotten more compliments on a piece of clothing.",
						'author' => 'Jade W., San Francisco',
					),
					array(
						'text'   => "This isn't just a brand, it's a movement. The numbered tag makes it feel special.",
						'author' => 'Devon L., Los Angeles',
					),
				),
			),
			'craft'        => array(
				'heading'    => 'Why BLACK ROSE Costs What It Costs',
				'subheading' => 'Every dollar goes into the product. No influencer budgets. No middlemen. Just quality you can feel.',
				'cards'      => array(
					array(
						'icon'  => '380gsm',
						'title' => '380gsm French Terry',
						'desc'  => 'Premium heavyweight fabric that holds its shape wash after wash. Most brands use 220gsm. We use nearly double.',
					),
					array(
						'icon'  => '#',
						'title' => 'Numbered Authentication',
						'desc'  => 'Every piece is hand-numbered with a unique tag. You know exactly which piece is yours out of 200.',
					),
					array(
						'icon'  => '////',
						'title' => 'Double-Stitched Seams',
						'desc'  => 'Reinforced construction at every stress point. Built to last years, not seasons.',
					),
					array(
						'icon'  => 'Locked',
						'title' => 'Never Restocked',
						'desc'  => 'When a run sells out, it is gone forever. No reprints, no exceptions. Your piece stays rare.',
					),
				),
			),
			'faq'          => array(
				'heading'   => 'Questions We Get Asked',
				'questions' => array(
					array(
						'q' => 'How does the sizing run?',
						'a' => 'True to size across the board. We offer sizes S through 3XL. Check the size guide on any product page for exact measurements.',
					),
					array(
						'q' => 'Is this really limited edition?',
						'a' => 'Yes. Every style is produced in a numbered run of 200 pieces. Once they sell out, they are never restocked or reprinted.',
					),
					array(
						'q' => 'What is your return policy?',
						'a' => 'We offer a 30-day return and exchange policy on all unworn items. Contact us and we will make it right.',
					),
					array(
						'q' => 'What about the quality?',
						'a' => 'Premium construction throughout. 280gsm+ cotton, double-stitched seams, and heavyweight French Terry on our hoodies and outerwear.',
					),
					array(
						'q' => 'How long does shipping take?',
						'a' => 'Orders ship within 5-7 business days. You will receive a tracking number via email as soon as your order is on its way.',
					),
				),
			),
			'cta'          => array(
				'heading'     => 'Get Early Access to Every Release',
				'subtitle'    => 'Join the list. First access. Exclusive drops. No spam.',
				'submit_text' => 'Join',
				'note'        => 'Join 12,400+ members who never miss a drop',
			),
		),
		'love-hurts'  => array(
			'hero'         => array(
				'badge_text'    => 'Family Legacy — The Hurts Collection',
				'logo_image'    => '/images/hero-overlays/lh-logo-combined.png',
				'logo_alt'      => 'Love Hurts Collection',
				'subtitle'      => "This isn't a theme. It's what you've survived.",
				'countdown'     => '72h',
				'cta_primary'   => array(
					'text' => 'Shop the Drop',
					'url'  => '#products',
				),
				'cta_secondary' => array(
					'text' => 'The Story',
					'url'  => '#story',
				),
			),
			'press'        => array( 'Maxim', 'CEO Weekly', 'SF Post', 'Best of Best Review' ),
			'story'        => array(
				'label'      => 'THE LEGACY',
				'title'      => "This Isn't a Theme. It's a Family Name.",
				'paragraphs' => array(
					'Most brands pick a concept off a mood board. We didn\'t pick this one — it picked us. "Hurts" isn\'t a word we chose for the aesthetic. It\'s the name our family carries. Every scar, every lesson, every door that closed and every one we kicked open — it\'s all in the name.',
					'This collection takes that pain and turns it into something you can wear. Something beautiful. Something that says: I\'ve been through it, and I\'m still here.',
				),
				'quote'      => "Every piece carries the weight of what we've been through — and the strength of what we've become.",
				'cite'       => '',
			),
			'parallax'     => 'Wear Your Heart. Own Your Scars.',
			'product_grid' => array(
				'heading'    => 'The Collection',
				'subheading' => "Wear what you've survived.",
				'skus'       => array( 'lh-004', 'lh-002', 'lh-003', 'lh-006' ),
				'wear_count' => 200,
			),
			'editorial'    => array(
				'heading'   => 'The Look',
				'top_count' => 3,
				'bot_count' => 2,
			),
			'reviews'      => array(
				'heading' => 'What LOVE HURTS Means to People',
				'items'   => array(
					array(
						'text'   => "I bought this for my daughter. She said it's the first brand that feels like it understands her.",
						'author' => 'Tamika R., Atlanta',
					),
					array(
						'text'   => 'The varsity jacket is a piece of art. I wear it every time I need to feel invincible.',
						'author' => 'Ray C., Oakland',
					),
					array(
						'text'   => 'Hurts is more than a name on a tag. When you know the story, it hits different.',
						'author' => 'Kiera M., Chicago',
					),
				),
			),
			'craft'        => array(
				'heading'    => 'Every Detail Is Intentional',
				'subheading' => '',
				'cards'      => array(
					array(
						'icon'  => 'Satin',
						'title' => 'Premium Satin Shell',
						'desc'  => 'The varsity jacket features a heavyweight satin shell with custom quilted lining. Built to last decades, not seasons.',
					),
					array(
						'icon'  => 'Hand',
						'title' => 'Hand-Applied Script',
						'desc'  => 'Fire-red chain-stitch lettering applied by hand. No two pieces are identical — each one carries its own character.',
					),
					array(
						'icon'  => 'Rose',
						'title' => 'Hidden Rose Garden',
						'desc'  => 'Flip the hood and find an embroidered rose garden lining. Beauty hidden where only you know to look.',
					),
					array(
						'icon'  => 'Soul',
						'title' => 'Family Name Legacy',
						'desc'  => '"Hurts" is stitched into every seam, woven into every label. This isn\'t branding — it\'s personal. Every piece carries meaning you can feel.',
					),
				),
			),
			'faq'          => array(
				'heading'   => 'Questions We Get Asked',
				'questions' => array(
					array(
						'q' => 'What does "Love Hurts" mean?',
						'a' => '<p>"Hurts" is the founder\'s actual family name. This collection is deeply personal — it\'s a tribute to everything the family has been through, transformed into something you can wear with pride.</p>',
					),
					array(
						'q' => 'How does sizing run?',
						'a' => '<p>Love Hurts pieces run true to size. The joggers and basketball shorts have an athletic fit with adjustable waistbands. The varsity jacket is cut relaxed for layering. When in doubt, go with your usual size.</p>',
					),
					array(
						'q' => 'How should I care for my pieces?',
						'a' => '<p>Machine wash cold on a gentle cycle, inside out. Hang dry to preserve the satin finish and embroidery details. Do not bleach or iron directly on printed areas.</p>',
					),
					array(
						'q' => 'What is the return policy?',
						'a' => '<p>We offer a 30-day return policy on all unworn items with original tags attached. Pre-order items can be cancelled for a full refund before they ship.</p>',
					),
					array(
						'q' => 'How long does shipping take?',
						'a' => '<p>Standard shipping is 5&ndash;7 business days within the US. Express options are available at checkout. International orders typically arrive within 10&ndash;14 business days.</p>',
					),
				),
			),
			'cta'          => array(
				'heading'     => 'New Stories Drop Monthly',
				'subtitle'    => "Every release tells a chapter. Don't miss yours.",
				'submit_text' => 'Join',
				'note'        => 'Join 12,400+ members',
			),
		),
		'signature'   => array(
			'hero'         => array(
				'badge_text'    => 'Everyday Luxury — The Foundation',
				'logo_image'    => '/images/hero-overlays/sig-brand-skyy-rose-gold.png',
				'logo_alt'      => 'The Skyy Rose Signature Collection',
				'subtitle'      => 'Not basics. Blueprints.',
				'countdown'     => '72h',
				'cta_primary'   => array(
					'text' => 'Shop the Drop',
					'url'  => '#products',
				),
				'cta_secondary' => array(
					'text' => 'The Story',
					'url'  => '#story',
				),
			),
			'press'        => array( 'Maxim', 'CEO Weekly', 'SF Post', 'Best of Best Review' ),
			'story'        => array(
				'label'      => 'THE PHILOSOPHY',
				'title'      => 'Not Basics. Blueprints.',
				'paragraphs' => array(
					'Most brands sell you basics and call it a day. We build foundation pieces — the kind you reach for first, wear the longest, and never want to replace. Premium cotton blends, considered silhouettes, and details you feel before you see them.',
					"Signature is the collection that started everything. Before the limited drops and the press features, there was a father in Oakland who believed everyday clothes should feel like something. That belief hasn't changed.",
				),
				'quote'      => 'The foundation of any wardrobe worth building.',
				'cite'       => '',
			),
			'parallax'     => "Everyday Doesn't Mean Ordinary.",
			'product_grid' => array(
				'heading'    => 'The Collection',
				'subheading' => 'Wardrobe foundations built to last.',
				'skus'       => array( 'sg-001' ),
				'wear_count' => 300,
			),
			'editorial'    => array(
				'heading'   => 'The Lookbook',
				'top_count' => 3,
				'bot_count' => 2,
			),
			'reviews'      => array(
				'heading' => 'Rated 4.9 by 350+ Customers',
				'items'   => array(
					array(
						'text'   => "Best basics I've ever owned. The weight of the fabric is perfect.",
						'author' => 'Andre P., New York',
					),
					array(
						'text'   => 'I replaced my entire wardrobe basics with Signature pieces. Worth every penny.',
						'author' => 'Lisa K., Oakland',
					),
					array(
						'text'   => "The gold detailing is subtle but you notice it. That's the difference.",
						'author' => 'James M., Houston',
					),
				),
			),
			'craft'        => array(
				'heading'    => "Everyday Doesn't Mean Ordinary",
				'subheading' => '',
				'cards'      => array(
					array(
						'icon'  => 'Premium',
						'title' => 'Premium Cotton Blend',
						'desc'  => '280gsm organic cotton with a brushed interior. Heavier than fast fashion, softer than anything in your closet.',
					),
					array(
						'icon'  => 'Gold',
						'title' => 'Gold Accent Details',
						'desc'  => 'Subtle gold rose branding on every piece. Not loud — just enough that those who know, know.',
					),
					array(
						'icon'  => 'Versatile',
						'title' => 'Versatile Silhouettes',
						'desc'  => "Designed to move from morning coffee to evening out. Day-to-night pieces that don't compromise.",
					),
					array(
						'icon'  => 'Durable',
						'title' => 'Built to Last',
						'desc'  => 'Reinforced seams, pre-shrunk fabric, colorfast dyes. These pieces get better with every wash.',
					),
				),
			),
			'faq'          => array(
				'heading'   => 'Quick Answers',
				'questions' => array(
					array(
						'q' => 'How does Signature sizing run?',
						'a' => 'Relaxed, comfortable fit across sizes S through 3XL. Check the size guide on each product page for exact measurements.',
					),
					array(
						'q' => 'Will there be new colors?',
						'a' => 'We drop new colorways monthly. Subscribe to be the first to know when a new Signature color lands.',
					),
					array(
						'q' => "What's the return policy?",
						'a' => '30-day hassle-free returns on all unworn items with tags attached. We cover return shipping in the US.',
					),
					array(
						'q' => 'What makes the quality different?',
						'a' => 'Premium construction with 280gsm+ fabrics, reinforced stitching, and pre-shrunk materials. Built to outlast anything in the same price range.',
					),
					array(
						'q' => 'How long does shipping take?',
						'a' => 'Standard shipping is 5&ndash;7 business days within the US. Expedited options available at checkout.',
					),
				),
			),
			'cta'          => array(
				'heading'     => 'New Colorways Drop Monthly',
				'subtitle'    => 'First access to every new Signature release.',
				'submit_text' => 'Get Early Access',
				'note'        => 'Join 12,400+ members',
			),
		),
	);
}

/**
 * Return landing data for a single collection slug.
 *
 * @since 7.1.0
 * @param string $slug Collection slug (e.g., 'black-rose').
 * @return array<string, mixed>|null Landing data, or null if slug unknown.
 */
function skyyrose_get_landing_data( $slug ) {
	$all = skyyrose_landing_data();
	return $all[ $slug ] ?? null;
}
