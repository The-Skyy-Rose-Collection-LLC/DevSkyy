# SkyyRose Visual Pattern Shortlist

Source: `Animated_Website_Prompt_Pack_200.pdf` (202 prompts, 8 chapters), screened 2026-07-27 against SkyyRose's real brand system — dark ground, Rose Gold/Gold/Crimson/Silver collection tokens, Archivo/Hanken Grotesk/Cinzel type, Kith · Oaklandish · Culture Kings · Fear of God · Palm Angels as the reference set, never European luxury.

**176 of 202 kept.** 24 directly extend code that already exists (`luxury-cursor.js`, `product-card-holo.js`, `toast.js`, `footer-cro.js`, the virtual try-on backend, the Immersive Worlds scene work) — start there, cheapest and fastest. 2 flagged use-with-care. 26 cut outright as wrong register (SaaS/Web3/dashboard/dev-portfolio patterns with no fashion-storefront equivalent).

**Known landmine:** "Dark Luxury Hero with Gold Accents" and "Dark Luxury Newsletter Section" are near-literal brand-name matches structurally, but both spec **Cormorant Garamond** for the wordmark — on the CLAUDE.md cut-font list (locked 2026-07-10, do not reintroduce). Retoken to Cinzel or Pinyon Script and the real `#D4AF37` gold before building either.

Full source prompt text lives in `Animated_Website_Prompt_Pack_200.pdf` (not committed — founder's local Downloads). Use the title below to locate the exact prompt (`PROMPT NNN` markers, sequential by chapter) when you need the full spec.

## Priority tier — extends existing code (build these first)

| Pattern | Extends |
|---|---|
| Cursor Spotlight Reveal Hero | `luxury-cursor.js` |
| Magnetic CTA / Magnetic Button (×2 occurrences) | `luxury-cursor.js` |
| Gradient Orb Cursor Follower | `luxury-cursor.js` |
| Cursor Trail Effect | `luxury-cursor.js` |
| Smooth Underline Animation System | `luxury-cursor.js` |
| Animated Cursor States | `luxury-cursor.js` |
| Holographic Product Card | `product-card-holo.js` |
| Toast Notification Animations | `toast.js` |
| Animated Email Capture Section | `footer-cro.js` |
| Augmented Reality Try-On Preview | `devskyy` virtual try-on backend (already built) |
| AR-Style Floating Product Labels | ties to try-on above |
| Particle Field Hero (WebGL) | Three.js (already a dependency) |
| Scroll-Triggered Hero, Sequence Frames | Immersive Worlds scene work |
| Multi-Layer Parallax Scene | Immersive Worlds scene work |
| 3D Scroll Depth Scene | Immersive Worlds scene work |
| Page Load Sequence with Brand Reveal | mascot full-body walk-on entrance |

## Chapter 1 — Hero Sections (23/25 kept)

Cursor Spotlight Reveal Hero · Video Background Hero w/ Liquid Glass Nav (retoken chrome, drop "glass" language) · Split-Screen Morphing Hero · Fullscreen Text Mask Hero · Word-by-Word Kinetic Typography Hero · 3D Tilt Card Hero · Horizontal Scrolling Hero Intro · Particle Field Hero (WebGL) · Scroll-Triggered Hero w/ Sequence Frames · Monochrome Typographic Hero · Noise Gradient Animated Hero · Countdown Launch Hero (Kids Capsule pre-launch fit) · Bento Grid Hero · Magnetic CTA Hero · Reveal on Scroll Hero · Hero with Floating Testimonials · Perspective Scrolling Layers Hero · Gradient Border Animated Hero (use collection accent, not rainbow) · Full-Screen Video w/ Chapter Navigation · Staggered Grid Reveal Hero · **Dark Luxury Hero with Gold Accents** (font landmine, see above) · Typing Effect Hero (use sparingly) · Full Page 3D Scene Hero (one flagship page only).

Cut: Glassmorphism Dashboard Hero, Rotating 3D Globe Hero (both wrong genre).

## Chapter 2 — Background Animations (23/25 kept)

Flowing Aurora (Signature gold) · Animated Mesh Gradient · Particle Network (keep sparse) · Bioluminescent Wave (Love Hurts) · Interactive Ink Drop (Love Hurts) · CSS Grid Line Animation · Constellation Star Field · Waveform Audio Visualizer (only paired with real audio) · Floating Geometric Shapes (organic, not corporate-clean) · Lottie/SVG Animated Background · Gradient Orb Cursor Follower · Raindrop/Glass Drip · Cloth/Fabric Simulation · Abstract SVG Morphing Shapes · Retro VHS Scanline (Love Hurts specifically) · Ripple/Water Surface · Dot Grid Interactive · Gradient Text Animation Background · Gradient Beam · Physics-Based Bouncing Logo (Kids Capsule) · Topographic Map Lines (Bay Area founder story) · Smoke/Fog Drift (Black Rose gothic) · Sunrise/Sunset Sky Gradient (Signature/Golden Gate).

Cut: Neon Grid Cyberpunk, Matrix-Style Data Rain (wrong genre).

## Chapter 3 — Scroll & Parallax (24/25 kept)

Multi-Layer Parallax Scene · Horizontal Scroll Gallery · Scroll-Driven Counter Section · Sticky Image w/ Scrolling Text · Page Transition Wipe · Scroll-Linked Timeline (founder story) · Zoom-Into-Section Scroll · Infinite Marquee/Ticker (tasteful) · Scroll-Snap Full-Page Sections · Morphing Section Dividers · Text Scramble on Scroll · Skewed/Diagonal Section Layout · Scroll-Triggered SVG Path Draw (SR monogram) · Parallax Cards with Depth · Reading Progress Bar · Scroll-Triggered Image Reveal · Parallax Text Split · Infinite Vertical Loop Section · Scroll-Driven Video Scrubbing · Animated Number Odometer · Sticky Header w/ Scroll Reveal · Scroll-Triggered Counter w/ Progress Ring · Kinetic Text Section · Scroll-Reveal Feature Cards Stagger.

Cut: Animated Pricing Section (no pricing-tier concept on a single-brand storefront).

## Chapter 4 — 3D & Product Mockup (23/25 kept) — highest leverage, this is PDP

Spinning Book/Album/Product Cover (repurpose for garment/packaging) · Multi-Angle Product Showcase · Holographic Product Card · Packshot Studio Hero · Stacked Cards 3D Fan · Product Detail Zoom Section · 3D Text Extrusion Effect (used once) · Interactive Size/Color Configurator (upgrades existing size-guide modal) · Morphing Logo Animation · 3D Product Carousel · Augmented Reality Try-On Preview · Liquid Metal/Chrome Material Effect (Signature gold) · Product Comparison Slider · Parallax Product Photography · Glassmorphism Product Card Grid (keep subtle/dark) · Animated Feature Tooltip System (fabric/care callouts) · Product Unboxing Animation · AR-Style Floating Product Labels · Magazine-Style Editorial Layout · Kinetic Typography Product Ad · Animated Badge/Award Showcase · Animated Testimonial Wall · Floating Device Mockup (reframe as AR try-on phone demo).

Cut: Browser Mockup with Animated Screen, Floating UI Components Showcase (both SaaS-flavored).

## Chapter 5 — Transitions & Loaders (15/15 kept, all pure technique)

Premium Page Loader · Skeleton Loading States · Morphing Navigation Hamburger · Route Change Curtain Animation · Spinner & Loading Micro-Animations · Dramatic Section Entrance Animations · Smooth Scroll (Lenis) · Page Load Sequence with Brand Reveal (mascot walk-on) · Toast Notification Animations · Animated Accordion/FAQ · Animated Tab Component · Stagger Children Animation System · Animated Cursor States · Interactive Timeline Slider · Entrance Animation Orchestration.

## Chapter 6 — Hover & Cursor FX (10/10 kept, all extend luxury-cursor.js)

Image Reveal on Text Hover · Magnetic Button · Hover Card Flip · Tilt & Glare Interactive Cards · Cursor Trail Effect · Parallax Image on Hover · Link Hover w/ Preview Image Bubble · Video Hover Reveal · Hover-Triggered Particle Burst (sparingly) · Smooth Underline Animation System.

## Chapter 7 — Physics & Motion (14/15 kept)

Spring Physics UI Components · Elastic Rope/String Effect (mascot-tether) · Confetti Celebration on Action (order confirmation) · Liquid Button Morph · Physics Bouncing Nav Items (mascot-adjacent) · Scroll-Driven Rotation · Morphing Shape Navigation · Gravity-Aware Elements (mascot-adjacent) · Fluid Simulation Section (Love Hurts "bloodline") · Elastic Border Animation · 3D Scroll Depth Scene · Ink Bleed Text Reveal (Love Hurts graffiti identity) · Kinetic Card Sort (wishlist/cart) · Scroll-Triggered Morphing Background.

Cut: Drag and Drop Kanban with Animations (no kanban UI on a storefront).

## Chapter 8 — Landing Pages & Components (44 kept)

**Full-page template:** eCommerce Product Launch Page (drop launches). Cut the other 9 (SaaS/Agency/Web3/Mobile-App/Course/RealEstate/Event/Fundraising/Personal-Brand — wrong industry).

**Component modules (19 kept):** Animated Gradient Text · 3D Floating Tags Cloud · Animated SVG Icon Set · Animated Number Ticker · Morphing CTA Section · Animated Social Proof Wall · Animated Checklist/Feature Comparison · Video Testimonial Player · Animated Email Capture Section · Text on Video Path · Infinite Canvas/Infinite Scroll Gallery · Split Text Hover w/ Color Fill · 3D Card Stack Swiper · Ambient Sound + Visual Reactive (**use with care** — opt-in only, never autoplay) · Realistic Material CSS (fabric/leather/gold) · Multi-Step Form with Animations (checkout) · Animated Gradient Border Cards · Page Section with Number Scrub · Sticky Sidebar Navigation (future editorial section).

Cut: Dark Mode/Light Mode Toggle — brand is intentionally always-dark, a toggle undercuts that on purpose.

**Micro-interactions & UI details (24 kept):** Button Loading State · Scroll-to-Top with Progress · Tooltip System · Smooth Image Lazy Load (also real perf win) · Dropdown Menu with Mega Variants · 404 Error Page (brand-voice opportunity) · Infinite Zoom Background · **Dark Luxury Newsletter Section** (same font landmine as Ch.1) · Scroll-Driven Color Palette Reveal (showcase the 4 collection color stories) · Split-Panel Comparison Hero · Testimonial with Stats Flyout · Ambient Video Section · 3D Icon Hover System · Horizontal Feature Scroll · Noise Texture Overlay Generator (matches "concrete" tagline directly) · Spotlight Section Reveal · Scroll-Triggered Number Story (brand-history stats) · Pixel Reveal/Mosaic Effect · Scroll-Driven SVG Map Animation (Bay Area/Oakland founder story) · Looping Card Stack Scroll · Premium Search Experience · Environmental Responsive Section (**experimental** — scope/test before committing site-wide) · Generative Art Hero (tie to "concrete" urban texture) · The Signature Piece (reserve for one true flagship moment, not a reusable template).

Cut: Pricing Calculator, Animated Resume/CV, Product Changelog Page, Interactive Map Dashboard, AI Chat Interface Demo, Typing Game/Interactive Demo (all SaaS/dev-portfolio concepts, no storefront equivalent).

## Non-negotiable constraints when implementing ANY pattern above

1. Every motion pattern respects `prefers-reduced-motion: reduce` — provide a static/reduced fallback, never skip this.
2. Never use Cormorant Garamond, Playfair Display, Bebas Neue, or Yellowtail — CLAUDE.md cut list, locked 2026-07-10.
3. Retoken every placeholder color to the real brand tokens (`#B76E79` Rose Gold, `#0A0A0A` Dark, `#C0C0C0` Silver/Black Rose, `#DC143C` Crimson/Love Hurts, `#D4AF37` Gold/Signature) — never the pack's generic example hex values.
4. No autoplay audio, ever (Ambient Sound pattern is opt-in only).
5. Hero titles/collection wordmarks are brand-script lockup images, never type-rendered — this applies even to patterns above whose spec assumes rendered text headlines.
6. Mobile fallback required for any WebGL/particle/3D pattern — cap particle counts, disable mouse-interaction physics on touch devices, per the pack's own performance notes.
