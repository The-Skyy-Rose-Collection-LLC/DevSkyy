<?php
/**
 * Landing Page Content Data
 *
 * Returns per-collection content for the unified landing page layout.
 * Single source of truth for all landing-page copy, mirroring the
 * structure proven by collection-content.php.
 *
 * Section order:
 *   1. hero      — overlay logo + subtitle + dual CTAs
 *   2. stats     — brand fact bar (honest metrics, no fake press logos)
 *   3. story     — origin narrative + founder quote
 *   4. parallax  — single-line statement banner
 *   5. products  — SKU array → holo card grid
 *   6. editorial — collection-specific lookbook image gallery
 *   7. reviews   — customer voice (5★ default)
 *   8. craft     — value-proposition cards (icon/title/desc)
 *   9. faq       — accordion (q/a)
 *  10. cta       — email capture + social proof note
 *
 * VISUAL IDENTITY DOCTRINE (enforced in code — never cross-contaminate):
 *   Black Rose   — BAY BRIDGE / MIDNIGHT: silver on deep black (#C0C0C0 / #0A0A0A),
 *                  Oakland rain, 2AM drives, industrial pressure, forged not made
 *   Love Hurts   — BEAST BENEATH: crimson (#DC143C), Beauty & the Beast (beast POV),
 *                  distressed luxury, gothic dark romanticism, vulnerability = strength
 *   Signature    — GOLDEN GATE SWAG: gold (#D4AF37), California sunset, Bay Area
 *                  confidence, foundation before the scars, timeless not trendy
 *   Kids Capsule — THE HEIR: rose gold (#B76E79), daughter Skyy Rose, regal + cinematic,
 *                  dark luxury scaled down not dumbed down, inheritance of vision
 *
 * Editorial images MUST be collection-specific. Never share lookbook images across collections.
 *
 * @package SkyyRose
 * @since   6.6.0
 */

defined( 'ABSPATH' ) || exit;

/**
 * Get landing-page content for a collection.
 *
 * @param  string $slug Collection slug.
 * @return array<string, mixed>|null Content array or null when slug is unknown.
 */
function skyyrose_get_landing_content( $slug ) {
	$collections = array(

		/* ── Black Rose ─────────────────────────────────────────────────────
		 * Visual identity: BAY BRIDGE / MIDNIGHT
		 * Palette:         silver on deep black (#C0C0C0 on #0A0A0A)
		 * Motifs:          Bay Bridge steel, Oakland rain, 2AM pressure,
		 *                  industrial fog, concrete beauty, forged not made
		 * Emotional energy: loneliness after success, survival under pressure,
		 *                   crossing between struggle and elevation
		 * DO NOT mix with Love Hurts (crimson / varsity / emotional)
		 * ─────────────────────────────────────────────────────────────────── */
		'black-rose'   => array(
			'hero'      => array(
				'badge_text'    => __( '200 Pieces. Numbered. Never Restocked.', 'skyyrose' ),
				'logo_image'    => '/images/hero-overlays/br-brand-script.png',
				'logo_alt'      => __( 'The Black Rose Collection', 'skyyrose' ),
				'subtitle'      => __( 'Luxury grows from concrete.', 'skyyrose' ),
				'cta_primary'   => array(
					'text' => __( 'Shop Black Rose', 'skyyrose' ),
					'url'  => '#products',
				),
				'cta_secondary' => array(
					'text' => __( 'The Story', 'skyyrose' ),
					'url'  => '#story',
				),
			),
			'stats'     => array(
				array( 'value' => '200', 'label' => __( 'Pieces Per Run', 'skyyrose' ) ),
				array( 'value' => '380gsm', 'label' => __( 'French Terry Weight', 'skyyrose' ) ),
				array( 'value' => 'Oakland', 'label' => __( 'Origin', 'skyyrose' ) ),
				array( 'value' => 'Numbered', 'label' => __( 'Authentication', 'skyyrose' ) ),
			),
			'story'     => array(
				'label'      => __( 'THE CITY AFTER MIDNIGHT', 'skyyrose' ),
				'title'      => __( 'Built for the Nights Nobody Sees', 'skyyrose' ),
				'paragraphs' => array(
					__( 'This collection was built for the silent pressure. The isolation. The ambition that keeps people awake while the rest of the city sleeps.', 'skyyrose' ),
					__( 'Black Rose reflects the emotional reality behind survival — how people become colder to protect softer parts of themselves. The Bay Bridge is the visual metaphor: moving between worlds, crossing pain toward purpose.', 'skyyrose' ),
					__( 'Heavyweight silhouettes. Industrial luxury. Emotional armor built for the 2AM version of yourself that nobody else gets to see.', 'skyyrose' ),
				),
				'quote'      => array(
					'text' => __( 'Some people become hard because life demanded it. Black Rose is for them.', 'skyyrose' ),
					'cite' => __( '— Corey Foster, Founder', 'skyyrose' ),
				),
			),
			'parallax'  => __( 'Some flowers only grow through pressure.', 'skyyrose' ),
			'products'  => array(
				'heading'    => __( 'The Collection', 'skyyrose' ),
				'subheading' => __( "Limited edition. Numbered. When they're gone, they're gone.", 'skyyrose' ),
				'skus'       => array( 'br-004', 'br-005', 'br-006', 'br-010' ),
				'wear_count' => 200,
			),
			'editorial' => array(
				'heading' => __( 'The Armor', 'skyyrose' ),
				'images'  => array(
					array(
						'src'    => '/images/lookbook/lb-black-rose-football-960w.webp',
						'src_sm' => '/images/lookbook/lb-black-rose-football-480w.webp',
						'alt'    => __( 'Black Rose football jersey — sport armor in motion', 'skyyrose' ),
						'span'   => 'wide',
					),
					array(
						'src'    => '/images/lookbook/lb-black-rose-hockey-960w.webp',
						'src_sm' => '/images/lookbook/lb-black-rose-hockey-480w.webp',
						'alt'    => __( 'Black Rose hockey jersey — ice and darkness', 'skyyrose' ),
						'span'   => '',
					),
					array(
						'src'    => '/images/products/br-007-real-detail.webp',
						'src_sm' => '/images/products/br-007-real-detail.webp',
						'alt'    => __( 'Black Rose — double-stitched armor seam detail', 'skyyrose' ),
						'span'   => '',
					),
				),
			),
			'reviews'   => array(
				'heading' => __( 'What BLACK ROSE Means to People', 'skyyrose' ),
				'items'   => array(
					array(
						'text'   => __( "The quality is insane. I've washed my hoodie 20+ times and it still looks brand new.", 'skyyrose' ),
						'author' => __( 'Marcus T., Oakland', 'skyyrose' ),
					),
					array(
						'text'   => __( "I've never gotten more compliments on a piece of clothing. People ask where it's from before they even see the tag.", 'skyyrose' ),
						'author' => __( 'Jade W., San Francisco', 'skyyrose' ),
					),
					array(
						'text'   => __( "This isn't just a brand, it's a movement. The numbered tag makes it feel like something that matters.", 'skyyrose' ),
						'author' => __( 'Devon L., Los Angeles', 'skyyrose' ),
					),
				),
			),
			'craft'     => array(
				'heading'    => __( 'Forged, Not Made', 'skyyrose' ),
				'subheading' => __( 'Black Rose honors the people who carried pressure quietly and still found a way to create beauty from it.', 'skyyrose' ),
				'cards'      => array(
					array(
						'icon'  => '380gsm',
						'title' => __( '380gsm French Terry', 'skyyrose' ),
						'desc'  => __( 'Premium heavyweight fabric that holds its shape wash after wash. Most brands use 220gsm. We use nearly double.', 'skyyrose' ),
					),
					array(
						'icon'  => '#',
						'title' => __( 'Numbered Authentication', 'skyyrose' ),
						'desc'  => __( 'Every piece is hand-numbered. You know exactly which piece is yours out of 200. When the run is gone, it is gone forever.', 'skyyrose' ),
					),
					array(
						'icon'  => '////',
						'title' => __( 'Double-Stitched Seams', 'skyyrose' ),
						'desc'  => __( 'Reinforced construction at every stress point. Industrial luxury built to last years, not seasons.', 'skyyrose' ),
					),
					array(
						'icon'  => '◈',
						'title' => __( 'Thorn Protection', 'skyyrose' ),
						'desc'  => __( 'Every detail — the thorn motifs, the monochrome palette, the weight of the fabric — carries the story of beauty built from impossible conditions.', 'skyyrose' ),
					),
				),
			),
			'faq'       => array(
				'heading'   => __( 'Questions We Get Asked', 'skyyrose' ),
				'questions' => array(
					array(
						'q' => __( 'How does the sizing run?', 'skyyrose' ),
						'a' => __( 'True to size across the board. We offer sizes S through 3XL. Check the size guide on any product page for exact measurements.', 'skyyrose' ),
					),
					array(
						'q' => __( 'Is this really limited to 200 pieces?', 'skyyrose' ),
						'a' => __( 'Yes. Every style is produced in a numbered run of 200 pieces. Once they sell out, they are never restocked or reprinted. No exceptions.', 'skyyrose' ),
					),
					array(
						'q' => __( 'What is your return policy?', 'skyyrose' ),
						'a' => __( 'We offer a 30-day return and exchange policy on all unworn items. Contact us and we will make it right.', 'skyyrose' ),
					),
					array(
						'q' => __( 'What about the quality?', 'skyyrose' ),
						'a' => __( '380gsm French Terry, double-stitched seams, and hand-numbered authentication on every piece. Built in darkness. Worn with purpose.', 'skyyrose' ),
					),
					array(
						'q' => __( 'How long does shipping take?', 'skyyrose' ),
						'a' => __( 'Orders ship within 5-7 business days. You will receive a tracking number via email as soon as your order is on its way.', 'skyyrose' ),
					),
				),
			),
			'cta'       => array(
				'heading'     => __( 'Get Early Access to Every Release', 'skyyrose' ),
				'subtitle'    => __( 'First access. No spam. Built in darkness, delivered to your inbox.', 'skyyrose' ),
				'button_text' => __( 'Join', 'skyyrose' ),
				'note'        => __( 'Join 12,400+ members who never miss a drop', 'skyyrose' ),
				'email_id'    => 'lp-cta-email-br',
				'list_slug'   => 'black_rose',
			),
		),

		/* ── Love Hurts ──────────────────────────────────────────────────────
		 * Visual identity: THE BEAST BENEATH
		 * Palette:         crimson (#DC143C) on black
		 * Motifs:          Beauty & the Beast (beast POV), enchanted rose as time,
		 *                  distressed luxury, gothic dark romanticism, thorn detailing,
		 *                  chain-stitch lettering, fractured hearts, candlelight
		 * Emotional themes: emotional isolation, misunderstood masculinity,
		 *                   transformation through love, the fear of being unlovable
		 * DO NOT mix with Black Rose (silver / sport / armor)
		 * ─────────────────────────────────────────────────────────────────── */
		'love-hurts'   => array(
			'hero'      => array(
				'badge_text'    => __( 'Family Legacy — The Hurts Collection', 'skyyrose' ),
				'logo_image'    => '/images/hero-overlays/lh-logo-combined.png',
				'logo_alt'      => __( 'Love Hurts Collection', 'skyyrose' ),
				'subtitle'      => __( 'The beast was never evil. He was wounded.', 'skyyrose' ),
				'cta_primary'   => array(
					'text' => __( 'Shop Love Hurts', 'skyyrose' ),
					'url'  => '#products',
				),
				'cta_secondary' => array(
					'text' => __( 'The Story', 'skyyrose' ),
					'url'  => '#story',
				),
			),
			'stats'     => array(
				array( 'value' => '200', 'label' => __( 'Pieces Per Style', 'skyyrose' ) ),
				array( 'value' => 'Chain-Stitch', 'label' => __( 'Lettering Method', 'skyyrose' ) ),
				array( 'value' => 'Satin', 'label' => __( 'Varsity Shell', 'skyyrose' ) ),
				array( 'value' => 'Hurts', 'label' => __( 'The Family Name', 'skyyrose' ) ),
			),
			'story'     => array(
				'label'      => __( 'THE BEAST BENEATH', 'skyyrose' ),
				'title'      => __( 'Not the Monster People Feared', 'skyyrose' ),
				'paragraphs' => array(
					__( 'Love Hurts reimagines Beauty and the Beast through the Beast\'s perspective. Not the monster people feared — but the man trapped beneath pressure, isolation, anger, and the fear of never being understood.', 'skyyrose' ),
					__( 'In this story, the rose becomes more than romance. It becomes time. Hope. Redemption. The last fragile thing left untouched inside a hardened soul.', 'skyyrose' ),
					__( 'Every garment reflects that emotional tension: softness versus aggression, beauty versus damage, love versus self-destruction. Because some people become hard because life demanded it. Some stop believing they deserve love.', 'skyyrose' ),
					__( 'Love Hurts is a survival story. The idea that love can soften even the most guarded person without erasing who they are. Not a fairytale. A transformation.', 'skyyrose' ),
				),
				'quote'      => array(
					'text' => __( 'Every beast was once something softer.', 'skyyrose' ),
					'cite' => __( '— Corey Foster, Founder', 'skyyrose' ),
				),
			),
			'parallax'  => __( 'The curse was never the monster. It was believing nobody could love him.', 'skyyrose' ),
			'products'  => array(
				'heading'    => __( 'The Collection', 'skyyrose' ),
				'subheading' => __( "Wear what you've survived. Wear it beautifully.", 'skyyrose' ),
				'skus'       => array( 'lh-004', 'lh-002', 'lh-003', 'lh-006' ),
				'wear_count' => 200,
			),
			'editorial' => array(
				'heading' => __( 'Dark Romanticism', 'skyyrose' ),
				'images'  => array(
					array(
						'src'    => '/images/lookbook/lb-love-hurts-varsity-960w.webp',
						'src_sm' => '/images/lookbook/lb-love-hurts-varsity-480w.webp',
						'alt'    => __( 'Love Hurts varsity jacket — beauty and the beast in motion', 'skyyrose' ),
						'span'   => 'wide',
					),
					array(
						'src'    => '/images/lookbook/lb-rose-hoodie-beanie-960w.webp',
						'src_sm' => '/images/lookbook/lb-rose-hoodie-beanie-480w.webp',
						'alt'    => __( 'Love Hurts rose hoodie — crimson warmth against the dark', 'skyyrose' ),
						'span'   => '',
					),
					array(
						'src'    => '/images/products/lh-003-real-detail-1.webp',
						'src_sm' => '/images/products/lh-003-real-detail-1.webp',
						'alt'    => __( 'Love Hurts — hand-applied chain-stitch lettering detail', 'skyyrose' ),
						'span'   => '',
					),
				),
			),
			'reviews'   => array(
				'heading' => __( 'What LOVE HURTS Means to People', 'skyyrose' ),
				'items'   => array(
					array(
						'text'   => __( "I bought this for my daughter. She said it's the first brand that feels like it understands her.", 'skyyrose' ),
						'author' => __( 'Tamika R., Atlanta', 'skyyrose' ),
					),
					array(
						'text'   => __( 'The varsity jacket is a piece of art. I wear it every time I need to feel invincible.', 'skyyrose' ),
						'author' => __( 'Ray C., Oakland', 'skyyrose' ),
					),
					array(
						'text'   => __( 'Hurts is more than a name on a tag. When you know the story, it hits different.', 'skyyrose' ),
						'author' => __( 'Kiera M., Chicago', 'skyyrose' ),
					),
				),
			),
			'craft'     => array(
				'heading' => __( 'Every Detail Is Intentional', 'skyyrose' ),
				'cards'   => array(
					array(
						'icon'  => 'Satin',
						'title' => __( 'Premium Satin Shell', 'skyyrose' ),
						'desc'  => __( 'Heavyweight satin shell with custom quilted lining. Distressed luxury — soft where it matters, structured everywhere else. Built to last decades, not seasons.', 'skyyrose' ),
					),
					array(
						'icon'  => 'Hand',
						'title' => __( 'Hand-Applied Script', 'skyyrose' ),
						'desc'  => __( 'Fire-red chain-stitch lettering applied by hand. Gothic typography meets varsity tradition. No two pieces are identical — each carries its own character.', 'skyyrose' ),
					),
					array(
						'icon'  => '✦',
						'title' => __( 'Thorn Motifs', 'skyyrose' ),
						'desc'  => __( 'Thorn detailing embedded throughout the collection. The rose protected by what wounds you. Beauty and damage existing in the same piece.', 'skyyrose' ),
					),
					array(
						'icon'  => 'Soul',
						'title' => __( 'The Family Name', 'skyyrose' ),
						'desc'  => __( '"Hurts" is stitched into every seam, woven into every label. Not branding — bloodline. Every piece carries the weight of what the family survived.', 'skyyrose' ),
					),
				),
			),
			'faq'       => array(
				'heading'   => __( 'Questions We Get Asked', 'skyyrose' ),
				'questions' => array(
					array(
						'q' => __( 'What does "Love Hurts" mean?', 'skyyrose' ),
						'a' => __( '<p>"Hurts" is the founder\'s actual family name. This collection is deeply personal — a tribute to transformation through connection, and the idea that love can reach even the most guarded person.</p>', 'skyyrose' ),
					),
					array(
						'q' => __( 'How does sizing run?', 'skyyrose' ),
						'a' => __( '<p>Love Hurts pieces run true to size. The varsity jacket is cut relaxed for layering. The joggers have an athletic fit with adjustable waistbands. When in doubt, go with your usual size.</p>', 'skyyrose' ),
					),
					array(
						'q' => __( 'How should I care for my pieces?', 'skyyrose' ),
						'a' => __( '<p>Machine wash cold on a gentle cycle, inside out. Hang dry to preserve the satin finish and embroidery details. Do not bleach or iron directly on printed areas.</p>', 'skyyrose' ),
					),
					array(
						'q' => __( 'What is the return policy?', 'skyyrose' ),
						'a' => __( '<p>We offer a 30-day return policy on all unworn items with original tags attached. Pre-order items can be cancelled for a full refund before they ship.</p>', 'skyyrose' ),
					),
					array(
						'q' => __( 'How long does shipping take?', 'skyyrose' ),
						'a' => __( '<p>Standard shipping is 5&ndash;7 business days within the US. Express options are available at checkout. International orders typically arrive within 10&ndash;14 business days.</p>', 'skyyrose' ),
					),
				),
			),
			'cta'       => array(
				'heading'     => __( 'New Stories Drop Monthly', 'skyyrose' ),
				'subtitle'    => __( "Every release tells a chapter of transformation. Don't miss yours.", 'skyyrose' ),
				'button_text' => __( 'Join', 'skyyrose' ),
				'note'        => __( 'Join 12,400+ members', 'skyyrose' ),
				'email_id'    => 'lp-cta-email-lh',
				'list_slug'   => 'love_hurts',
			),
		),

		/* ── Signature ───────────────────────────────────────────────────────
		 * Visual identity: GOLDEN GATE SWAG / FOUNDATION
		 * Palette:         gold (#D4AF37) on black
		 * Motifs:          Golden Gate Bridge at golden hour, Bay Area sunset,
		 *                  California confidence, 4AM sketch, EST. Oakland,
		 *                  timeless luxury not trend-driven, monthly colorways
		 * Emotional energy: possibility before the pressure, clean ambition,
		 *                   Bay Area pride, luxury without arrogance
		 * ─────────────────────────────────────────────────────────────────── */
		'signature'    => array(
			'hero'      => array(
				'badge_text'    => __( 'The Foundation — EST. Oakland', 'skyyrose' ),
				'logo_image'    => '/images/hero-overlays/sig-brand-skyy-rose-gold.png',
				'logo_alt'      => __( 'The Skyy Rose Signature Collection', 'skyyrose' ),
				'subtitle'      => __( 'The foundation everything grew from.', 'skyyrose' ),
				'cta_primary'   => array(
					'text' => __( 'Shop Signature', 'skyyrose' ),
					'url'  => '#products',
				),
				'cta_secondary' => array(
					'text' => __( 'The Story', 'skyyrose' ),
					'url'  => '#story',
				),
			),
			'stats'     => array(
				array( 'value' => '280gsm', 'label' => __( 'Organic Cotton Weight', 'skyyrose' ) ),
				array( 'value' => 'Monthly', 'label' => __( 'New Colorways', 'skyyrose' ) ),
				array( 'value' => 'Oakland', 'label' => __( 'EST.', 'skyyrose' ) ),
				array( 'value' => 'Everyday', 'label' => __( 'Wear Occasion', 'skyyrose' ) ),
			),
			'story'     => array(
				'label'      => __( 'GOLDEN STATE ENERGY', 'skyyrose' ),
				'title'      => __( 'Before the Pressure. Before the Scars.', 'skyyrose' ),
				'paragraphs' => array(
					__( 'Signature captures the feeling of possibility. Before the survival instincts became armor. Before the darker chapters. There was vision — and confidence that came naturally.', 'skyyrose' ),
					__( 'Inspired by the energy of San Francisco and Oakland existing side by side, the collection balances refinement with authenticity: luxury without arrogance, simplicity without weakness.', 'skyyrose' ),
					__( 'This is the collection that started everything. Built from Bay Area ambition and timeless self-expression — clean silhouettes, luxury comfort, West Coast presence. The original DNA of SkyyRose.', 'skyyrose' ),
				),
				'quote'      => array(
					'text' => __( 'West Coast luxury. Bay bloodline.', 'skyyrose' ),
					'cite' => '',
				),
			),
			'parallax'  => __( 'From the Bay to wherever destiny calls.', 'skyyrose' ),
			'products'  => array(
				'heading'    => __( 'The Collection', 'skyyrose' ),
				'subheading' => __( 'Wardrobe foundations built to last. Designed like a memory.', 'skyyrose' ),
				'skus'       => array( 'sg-001' ),
				'wear_count' => 300,
			),
			'editorial' => array(
				'heading' => __( 'The Lookbook', 'skyyrose' ),
				'images'  => array(
					array(
						'src'    => '/images/products/signature-tee-beanie-joggers-flatlay.webp',
						'src_sm' => '/images/products/signature-tee-beanie-joggers-flatlay.webp',
						'alt'    => __( 'Signature Collection — tee, beanie, and joggers flatlay at golden hour', 'skyyrose' ),
						'span'   => 'wide',
					),
					array(
						'src'    => '/images/products/the-signature-hoodie-front-model.webp',
						'src_sm' => '/images/products/the-signature-hoodie-front-model.webp',
						'alt'    => __( 'The Signature Hoodie — gold accent, Bay Area everyday luxury', 'skyyrose' ),
						'span'   => '',
					),
					array(
						'src'    => '/images/products/signature-beanie-front-model.webp',
						'src_sm' => '/images/products/signature-beanie-front-model.webp',
						'alt'    => __( 'Signature Beanie — the finishing touch', 'skyyrose' ),
						'span'   => '',
					),
				),
			),
			'reviews'   => array(
				'heading' => __( 'Rated 4.9 by 350+ Customers', 'skyyrose' ),
				'items'   => array(
					array(
						'text'   => __( "Best everyday pieces I've ever owned. The weight of the fabric is exactly right — not trying too hard, just perfect.", 'skyyrose' ),
						'author' => __( 'Andre P., New York', 'skyyrose' ),
					),
					array(
						'text'   => __( 'I replaced my entire wardrobe with Signature pieces. This is what basics should feel like.', 'skyyrose' ),
						'author' => __( 'Lisa K., Oakland', 'skyyrose' ),
					),
					array(
						'text'   => __( "The gold detailing is subtle but you notice it. That's the difference between basics and Signature.", 'skyyrose' ),
						'author' => __( 'James M., Houston', 'skyyrose' ),
					),
				),
			),
			'craft'     => array(
				'heading' => __( "Built to Last. Designed Like a Memory.", 'skyyrose' ),
				'cards'   => array(
					array(
						'icon'  => 'Premium',
						'title' => __( 'Premium Cotton Blend', 'skyyrose' ),
						'desc'  => __( '280gsm organic cotton with a brushed interior. Heavier than fast fashion, softer than anything in your closet. Gets better with every wash.', 'skyyrose' ),
					),
					array(
						'icon'  => 'Gold',
						'title' => __( 'Gold Accent Details', 'skyyrose' ),
						'desc'  => __( 'Subtle gold rose branding on every piece. Not loud — just enough that those who know, know. California confidence in every thread.', 'skyyrose' ),
					),
					array(
						'icon'  => 'Bay',
						'title' => __( 'Bay Area DNA', 'skyyrose' ),
						'desc'  => __( 'Designed to move from morning coffee to evening out. The energy of San Francisco and Oakland in every silhouette — refinement meets authenticity.', 'skyyrose' ),
					),
					array(
						'icon'  => 'Monthly',
						'title' => __( 'Monthly Colorways', 'skyyrose' ),
						'desc'  => __( 'Signature is not trend-driven. New colors drop monthly — each one designed like a memory. Something that stays meaningful no matter how much time passes.', 'skyyrose' ),
					),
				),
			),
			'faq'       => array(
				'heading'   => __( 'Quick Answers', 'skyyrose' ),
				'questions' => array(
					array(
						'q' => __( 'How does Signature sizing run?', 'skyyrose' ),
						'a' => __( 'Relaxed, comfortable fit across sizes S through 3XL. Check the size guide on each product page for exact measurements.', 'skyyrose' ),
					),
					array(
						'q' => __( 'Will there be new colors?', 'skyyrose' ),
						'a' => __( 'We drop new colorways monthly. Subscribe to be the first to know when a new Signature color lands. Each one is designed to stay relevant long after the drop.', 'skyyrose' ),
					),
					array(
						'q' => __( "What's the return policy?", 'skyyrose' ),
						'a' => __( '30-day hassle-free returns on all unworn items with tags attached. We cover return shipping in the US.', 'skyyrose' ),
					),
					array(
						'q' => __( 'What makes the quality different?', 'skyyrose' ),
						'a' => __( '280gsm+ organic cotton, reinforced stitching, pre-shrunk materials. Built to outlast anything in the same price range. The foundation of any wardrobe worth building.', 'skyyrose' ),
					),
					array(
						'q' => __( 'How long does shipping take?', 'skyyrose' ),
						'a' => __( 'Standard shipping is 5&ndash;7 business days within the US. Expedited options available at checkout.', 'skyyrose' ),
					),
				),
			),
			'cta'       => array(
				'heading'     => __( 'New Colorways Drop Monthly', 'skyyrose' ),
				'subtitle'    => __( 'First access to every new Signature release. Bay bloodline, your inbox.', 'skyyrose' ),
				'button_text' => __( 'Get Early Access', 'skyyrose' ),
				'note'        => __( 'Join 12,400+ members', 'skyyrose' ),
				'email_id'    => 'lp-cta-email-sig',
				'list_slug'   => 'signature',
			),
		),

		/* ── Kids Capsule ────────────────────────────────────────────────────
		 * Visual identity: THE HEIR TO THE THRONE
		 * Palette:         Rose Gold (#B76E79) — default root, no data-collection attr
		 * Motifs:          crowns, roses through concrete, childhood royalty,
		 *                  inheritance of vision, storybook luxury, daughter Skyy Rose
		 * Emotional energy: legacy in motion, innocence protected by love,
		 *                   confidence learned early, future greatness beginning now
		 * Hero overlay:    skyyrose-monogram.webp — brand IS named after Skyy Rose
		 *                  DO NOT reuse Signature's sig-brand-skyy-rose-gold.png here
		 * ─────────────────────────────────────────────────────────────────── */
		'kids-capsule' => array(
			'hero'      => array(
				'badge_text'    => __( 'The Heir to the Throne', 'skyyrose' ),
				'logo_image'    => '/branding/skyyrose-monogram.webp',
				'logo_alt'      => __( 'Kids Capsule Collection', 'skyyrose' ),
				'subtitle'      => __( 'Legacy begins long before adulthood.', 'skyyrose' ),
				'cta_primary'   => array(
					'text' => __( 'Shop Kids Capsule', 'skyyrose' ),
					'url'  => '#products',
				),
				'cta_secondary' => array(
					'text' => __( 'The Story', 'skyyrose' ),
					'url'  => '#story',
				),
			),
			'stats'     => array(
				array( 'value' => '2T–7', 'label' => __( 'Size Range', 'skyyrose' ) ),
				array( 'value' => '280gsm', 'label' => __( 'Cotton Weight', 'skyyrose' ) ),
				array( 'value' => 'Matching', 'label' => __( 'Parent–Child Sets', 'skyyrose' ) ),
				array( 'value' => 'Skyy Rose', 'label' => __( 'Named For', 'skyyrose' ) ),
			),
			'story'     => array(
				'label'      => __( 'BORN INTO POSSIBILITY', 'skyyrose' ),
				'title'      => __( 'Some Children Inherit Vision', 'skyyrose' ),
				'paragraphs' => array(
					__( 'Some children inherit wealth. Others inherit survival. But the rarest inherit vision.', 'skyyrose' ),
					__( 'The Heir to the Throne is about raising children to believe they belong in every room they walk into — regardless of where they come from. Inspired by Skyy Rose herself: innocence protected by strength, creativity nurtured by love, the beauty of dreaming beyond your environment.', 'skyyrose' ),
					__( 'Corey Foster named this brand after his daughter. This collection closes the circle — dark luxury scaled down, not dumbed down. Because confidence starts young.', 'skyyrose' ),
				),
				'quote'      => array(
					'text' => __( 'I built this brand for Skyy Rose. This collection is hers.', 'skyyrose' ),
					'cite' => __( '— Corey Foster, Founder', 'skyyrose' ),
				),
			),
			'parallax'  => __( 'Before they rule the world, let them dream freely.', 'skyyrose' ),
			'products'  => array(
				'heading'    => __( 'The Collection', 'skyyrose' ),
				'subheading' => __( 'Luxury that a parent passes down, not just buys.', 'skyyrose' ),
				'skus'       => array( 'kids-001', 'kids-002' ),
				'wear_count' => 150,
			),
			'editorial' => array(
				'heading' => __( 'Family Lookbook', 'skyyrose' ),
				'images'  => array(
					array(
						'src'    => '/images/lookbook/lb-kid-black-rose-960w.webp',
						'src_sm' => '/images/lookbook/lb-kid-black-rose-480w.webp',
						'alt'    => __( 'Kids Capsule — the heir in motion', 'skyyrose' ),
						'span'   => 'wide',
					),
					array(
						'src'    => '/images/products/kids-purple-set-front-model.webp',
						'src_sm' => '/images/products/kids-purple-set-front-model.webp',
						'alt'    => __( 'Kids Capsule purple colorblock set — front', 'skyyrose' ),
						'span'   => '',
					),
					array(
						'src'    => '/images/products/kids-red-set-front-model.webp',
						'src_sm' => '/images/products/kids-red-set-front-model.webp',
						'alt'    => __( 'Kids Capsule red set — front model', 'skyyrose' ),
						'span'   => '',
					),
				),
			),
			'reviews'   => array(
				'heading' => __( 'What Parents Are Saying', 'skyyrose' ),
				'items'   => array(
					array(
						'text'   => __( "My daughter refuses to take off her hoodie. The quality is insane for kids' clothes. This is more than clothing — it's legacy.", 'skyyrose' ),
						'author' => __( 'Alicia M., Oakland', 'skyyrose' ),
					),
					array(
						'text'   => __( "Finally, matching outfits that don't look corny. We get stopped every time we go out. People ask where she got it.", 'skyyrose' ),
						'author' => __( 'Marcus T., Los Angeles', 'skyyrose' ),
					),
					array(
						'text'   => __( "The colorblock set survived a whole week of daycare. That's the real luxury test — and it passed.", 'skyyrose' ),
						'author' => __( 'Jade W., San Francisco', 'skyyrose' ),
					),
				),
			),
			'craft'     => array(
				'heading'    => __( 'The Future We Build for Them', 'skyyrose' ),
				'subheading' => __( 'Children are not just watching the legacy — they are becoming it. Every detail reflects that.', 'skyyrose' ),
				'cards'      => array(
					array(
						'icon'  => '280gsm',
						'title' => __( 'Premium Weight Cotton', 'skyyrose' ),
						'desc'  => __( 'Same 280gsm cotton as the adult line. Heavyweight enough for real play, soft enough for everyday wear. No shortcuts because they\'re small.', 'skyyrose' ),
					),
					array(
						'icon'  => '♛',
						'title' => __( 'Parent-Child Matching', 'skyyrose' ),
						'desc'  => __( 'Every piece mirrors an adult SkyyRose style. Dress alike without the cringe. Royalty runs in the family.', 'skyyrose' ),
					),
					array(
						'icon'  => '////',
						'title' => __( 'Reinforced Seams', 'skyyrose' ),
						'desc'  => __( 'Double-stitched at every stress point. Built for kids who actually move. The heir needs armor too.', 'skyyrose' ),
					),
					array(
						'icon'  => '☆',
						'title' => __( 'Gender Neutral', 'skyyrose' ),
						'desc'  => __( "No boys' section, no girls' section. Just great clothes for the next generation of dreamers, leaders, and creators.", 'skyyrose' ),
					),
				),
			),
			'faq'       => array(
				'heading'   => __( 'Questions Parents Ask', 'skyyrose' ),
				'questions' => array(
					array(
						'q' => __( 'What sizes are available?', 'skyyrose' ),
						'a' => __( 'Kids Capsule runs 2T through 7. Check the size guide on any product page for exact measurements by age.', 'skyyrose' ),
					),
					array(
						'q' => __( 'Is this really the same quality as the adult line?', 'skyyrose' ),
						'a' => __( 'Yes. Same 280gsm+ cotton, same double-stitched seams, same attention to detail. The only difference is the size. Confidence starts young.', 'skyyrose' ),
					),
					array(
						'q' => __( 'Can I match with my kid?', 'skyyrose' ),
						'a' => __( 'That is the whole point. Every Kids Capsule piece has a matching adult counterpart in our core collections. Legacy runs in both directions.', 'skyyrose' ),
					),
					array(
						'q' => __( 'What is the return policy?', 'skyyrose' ),
						'a' => __( '30-day returns on unworn items. Kids grow fast — we get it. Contact us and we will sort it out.', 'skyyrose' ),
					),
					array(
						'q' => __( 'How long does shipping take?', 'skyyrose' ),
						'a' => __( 'Orders ship within 5-7 business days. Tracking number sent via email as soon as your order is on its way.', 'skyyrose' ),
					),
				),
			),
			'cta'       => array(
				'heading'     => __( 'For the Ones Destined to Carry the Crown Further', 'skyyrose' ),
				'subtitle'    => __( 'Get notified before every Kids Capsule drop. Raised with love. Built for greatness.', 'skyyrose' ),
				'button_text' => __( 'Join', 'skyyrose' ),
				'note'        => __( 'Join the family. First access to every drop.', 'skyyrose' ),
				'email_id'    => 'lp-cta-email-kc',
				'list_slug'   => 'kids_capsule',
			),
		),
	);

	return isset( $collections[ $slug ] ) ? $collections[ $slug ] : null;
}
