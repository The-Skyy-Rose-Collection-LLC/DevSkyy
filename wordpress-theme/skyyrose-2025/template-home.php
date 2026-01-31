<?php
/**
 * Template Name: SkyyRose Home
 * Description: Enhanced homepage with ambient gradients, collection previews, and animations
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

get_header();
?>

<style>
:root {
    --black-rose: #8B0000;
    --black-rose-glow: #ff0000;
    --love-hurts: #B76E79;
    --love-hurts-light: #ffb6c1;
    --signature-gold: #D4AF37;
    --signature-gold-glow: #ffd700;
    --bg-dark: #030303;
    --bg-deep: #000000;
    --glass-border: rgba(255, 255, 255, 0.08);
    --glass-bg: rgba(255, 255, 255, 0.03);
    --glass-blur: blur(20px);
}

.skyyrose-home {
    background: var(--bg-dark);
    color: #fff;
}

/* Ambient Background Mesh */
.skyyrose-home::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(circle at 15% 15%, rgba(139, 0, 0, 0.15) 0%, transparent 40%),
        radial-gradient(circle at 85% 85%, rgba(183, 110, 121, 0.1) 0%, transparent 40%),
        radial-gradient(circle at 50% 50%, rgba(212, 175, 55, 0.05) 0%, transparent 60%);
    z-index: -1;
    pointer-events: none;
}

/* Noise Texture */
.skyyrose-home::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%' height='100%' filter='url(%23noise)'/%3E%3C/svg%3E");
    opacity: 0.04;
    pointer-events: none;
    z-index: 9999;
    mix-blend-mode: overlay;
}

.text-gradient {
    background: linear-gradient(135deg, #fff 0%, var(--love-hurts-light) 50%, var(--signature-gold) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Hero Section */
.home-hero {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    perspective: 1000px;
    padding-top: 80px;
}

.orbit-system {
    position: absolute;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    pointer-events: none;
}

.orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(100px);
    opacity: 0.6;
    animation: orb-float 20s infinite ease-in-out;
}

.orb-1 {
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, var(--black-rose) 0%, transparent 70%);
    top: -10%;
    left: -10%;
}

.orb-2 {
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, var(--love-hurts) 0%, transparent 70%);
    bottom: -10%;
    right: -5%;
    animation-delay: -5s;
}

.orb-3 {
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, var(--signature-gold) 0%, transparent 70%);
    top: 40%;
    left: 50%;
    transform: translate(-50%, -50%);
    opacity: 0.3;
    animation-delay: -10s;
}

@keyframes orb-float {
    0%, 100% {
        transform: translate(0, 0) scale(1);
    }
    33% {
        transform: translate(30px, -50px) scale(1.1);
    }
    66% {
        transform: translate(-20px, 20px) scale(0.9);
    }
}

.hero-content {
    text-align: center;
    z-index: 10;
    max-width: 1000px;
    padding: 0 2rem;
    transform-style: preserve-3d;
}

.hero-badge {
    display: inline-block;
    padding: 0.8rem 2rem;
    border: 1px solid rgba(212, 175, 55, 0.3);
    border-radius: 100px;
    font-size: 0.7rem;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: var(--signature-gold);
    margin-bottom: 2rem;
    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(10px);
    box-shadow: 0 0 20px rgba(212, 175, 55, 0.1);
    animation: fadeUp 1s ease-out forwards;
}

.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(3.5rem, 9vw, 7.5rem);
    font-weight: 500;
    line-height: 1.1;
    margin-bottom: 2rem;
    opacity: 0;
    animation: fadeUp 1s ease-out 0.2s forwards;
    text-shadow: 0 0 40px rgba(0, 0, 0, 0.5);
}

.hero-subtitle {
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.7);
    max-width: 650px;
    margin: 0 auto 3.5rem;
    font-weight: 300;
    opacity: 0;
    animation: fadeUp 1s ease-out 0.4s forwards;
}

.btn-group {
    display: flex;
    gap: 1.5rem;
    justify-content: center;
    flex-wrap: wrap;
    opacity: 0;
    animation: fadeUp 1s ease-out 0.6s forwards;
}

.btn {
    padding: 1.2rem 3rem;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 3px;
    text-transform: uppercase;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
    position: relative;
    overflow: hidden;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 2px;
}

.btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.5s ease;
}

.btn:hover::before {
    left: 100%;
}

.btn-primary {
    background: linear-gradient(135deg, var(--black-rose), #4a0000);
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 10px 30px rgba(139, 0, 0, 0.3);
}

.btn-primary:hover {
    transform: translateY(-3px);
    box-shadow: 0 20px 40px rgba(139, 0, 0, 0.5);
}

.btn-glass {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #fff;
}

.btn-glass:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: #fff;
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(255, 255, 255, 0.1);
}

@keyframes fadeUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Collections Section */
.collections-section {
    padding: 10rem 0;
}

.section-header {
    text-align: center;
    margin-bottom: 6rem;
    position: relative;
}

.section-header h2 {
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    margin-bottom: 1rem;
}

.section-header::after {
    content: '';
    position: absolute;
    left: 50%;
    bottom: -30px;
    transform: translateX(-50%);
    width: 1px;
    height: 60px;
    background: linear-gradient(to bottom, var(--signature-gold), transparent);
}

.cards-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
    padding: 0 4rem;
    max-width: 1600px;
    margin: 0 auto;
}

.glass-card {
    height: 650px;
    position: relative;
    overflow: hidden;
    border-radius: 4px;
    transition: transform 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
    cursor: pointer;
}

.glass-card:hover {
    transform: translateY(-10px);
}

.blur-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(0px);
    transition: all 0.6s ease;
    z-index: 2;
}

.glass-card:hover .blur-overlay {
    background: rgba(0, 0, 0, 0.4);
}

.card-bg {
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center;
    transition: transform 1s ease;
}

.glass-card:hover .card-bg {
    transform: scale(1.1);
}

.card-content {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    padding: 3rem;
    z-index: 10;
    background: linear-gradient(to top, #000 0%, transparent 100%);
}

.collection-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    transform: translateY(20px);
    transition: transform 0.5s ease;
}

.glass-card:hover .collection-title {
    transform: translateY(0);
}

.hidden-details {
    height: 0;
    overflow: hidden;
    opacity: 0;
    transition: all 0.5s ease;
}

.glass-card:hover .hidden-details {
    height: auto;
    opacity: 1;
    margin-top: 1rem;
}

.collection-link {
    color: var(--signature-gold);
    text-decoration: none;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-size: 0.8rem;
    display: inline-block;
    margin-top: 1rem;
}

.collection-link:hover {
    text-shadow: 0 0 10px var(--signature-gold-glow);
}

/* Scroll Reveal */
.reveal {
    opacity: 0;
    transform: translateY(30px);
    transition: all 0.8s ease;
}

.reveal.active {
    opacity: 1;
    transform: translateY(0);
}

/* Responsive */
@media (max-width: 1024px) {
    .cards-container {
        grid-template-columns: 1fr;
        padding: 0 2rem;
    }
}

@media (max-width: 768px) {
    .hero-title {
        font-size: 3rem;
    }

    .btn-group {
        flex-direction: column;
        align-items: center;
    }

    .btn {
        width: 100%;
        max-width: 300px;
    }

    .glass-card {
        height: 500px;
    }
}
</style>

<div class="skyyrose-home">
    <!-- Hero Section -->
    <section class="home-hero">
        <div class="orbit-system">
            <div class="orb orb-1"></div>
            <div class="orb orb-2"></div>
            <div class="orb orb-3"></div>
        </div>

        <div class="hero-content">
            <div class="hero-badge">Oakland Luxury Streetwear</div>
            <h1 class="hero-title">
                <span class="text-gradient">Where Love Meets Luxury</span>
            </h1>
            <p class="hero-subtitle">
                Bold designs that marry streetwear edge with haute couture elegance.
                Each piece tells a story of resilience, passion, and uncompromising style.
            </p>
            <div class="btn-group">
                <a href="<?php echo esc_url(get_permalink(get_page_by_path('vault'))); ?>" class="btn btn-primary">
                    Pre-Order Now
                </a>
                <a href="#collections" class="btn btn-glass">
                    Explore Collections
                </a>
            </div>
        </div>
    </section>

    <!-- Collections Section -->
    <section id="collections" class="collections-section">
        <div class="section-header">
            <h2>Discover Our Collections</h2>
            <p style="color: rgba(255,255,255,0.6); margin-top: 1rem;">
                Three distinct worlds. One unified vision.
            </p>
        </div>

        <div class="cards-container">
            <?php
            // Define collections
            $collections = [
                [
                    'slug' => 'black-rose',
                    'title' => 'Black Rose',
                    'tagline' => 'DARK ELEGANCE',
                    'description' => 'For the bold and resilient. Sharp lines, deep reds, and uncompromised strength.',
                    'gradient' => 'linear-gradient(45deg, #1a0000, #3d0000)',
                    'color' => '#8B0000',
                    'page_slug' => '01-black-rose-garden',
                ],
                [
                    'slug' => 'love-hurts',
                    'title' => 'Love Hurts',
                    'tagline' => 'EMOTIONAL DEPTH',
                    'description' => 'Wear your heart. Soft fabrics, distressed details, and raw emotion.',
                    'gradient' => 'linear-gradient(45deg, #2d1a1d, #5c2e36)',
                    'color' => '#B76E79',
                    'page_slug' => '02-love-hurts-castle',
                ],
                [
                    'slug' => 'signature',
                    'title' => 'Signature',
                    'tagline' => 'TIMELESS LUXURY',
                    'description' => 'The foundation of style. Gold accents, premium cuts, and absolute class.',
                    'gradient' => 'linear-gradient(45deg, #1a1810, #2d2820)',
                    'color' => '#D4AF37',
                    'page_slug' => '03-signature-runway',
                ],
            ];

            foreach ($collections as $index => $collection) :
                // Try to find immersive page first, fall back to collection page
                $immersive_page = get_page_by_path($collection['page_slug']);
                $collection_page = get_page_by_path('collection-' . $collection['slug']);
                $link = $immersive_page ? get_permalink($immersive_page) : ($collection_page ? get_permalink($collection_page) : '#');
            ?>
                <div class="glass-card reveal" style="transition-delay: <?php echo $index * 0.1; ?>s;"
                     onclick="window.location.href='<?php echo esc_url($link); ?>'">
                    <div class="blur-overlay glass"></div>
                    <div class="card-bg" style="background: <?php echo esc_attr($collection['gradient']); ?>;"></div>
                    <div class="card-content">
                        <h3 class="collection-title" style="color: <?php echo esc_attr($collection['color']); ?>">
                            <?php echo esc_html($collection['title']); ?>
                        </h3>
                        <p style="color: #ccc; letter-spacing: 1px;">
                            <?php echo esc_html($collection['tagline']); ?>
                        </p>
                        <div class="hidden-details">
                            <p style="font-size: 0.9rem; color: #888; margin-bottom: 1.5rem;">
                                <?php echo esc_html($collection['description']); ?>
                            </p>
                            <a href="<?php echo esc_url($link); ?>" class="collection-link" onclick="event.stopPropagation();">
                                Enter Experience &rarr;
                            </a>
                        </div>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
    </section>
</div>

<script>
document.addEventListener('DOMContentLoaded', () => {
    // Scroll Reveal Observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});
</script>

<?php get_footer(); ?>
