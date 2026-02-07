<?php
/**
 * Template Name: About SkyyRose
 * Description: Brand story and values
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

get_header();
?>

<style>
:root {
    --bg-dark: #000000;
    --signature-gold: #D4AF37;
    --love-hurts: #B76E79;
    --black-rose: #8B0000;
}

.about-page {
    background: var(--bg-dark);
    color: #fff;
    min-height: 100vh;
}

/* Ambient Background */
.about-page::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(circle at 20% 30%, rgba(139, 0, 0, 0.08) 0%, transparent 50%),
        radial-gradient(circle at 80% 70%, rgba(183, 110, 121, 0.06) 0%, transparent 50%),
        radial-gradient(circle at 50% 50%, rgba(212, 175, 55, 0.04) 0%, transparent 60%);
    z-index: -1;
    pointer-events: none;
}

.about-page::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%' height='100%' filter='url(%23noise)'/%3E%3C/svg%3E");
    opacity: 0.04;
    pointer-events: none;
    z-index: -1;
    mix-blend-mode: overlay;
}

/* Hero Section */
.about-hero {
    min-height: 80vh;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 180px 2rem 100px;
    position: relative;
}

.hero-badge {
    display: inline-block;
    padding: 0.6rem 1.5rem;
    border: 1px solid rgba(212, 175, 55, 0.3);
    border-radius: 50px;
    font-size: 0.7rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--signature-gold);
    margin-bottom: 2rem;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(10px);
    animation: fadeUp 1s ease-out;
}

.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(3.5rem, 10vw, 6rem);
    font-weight: 400;
    margin-bottom: 2rem;
    animation: fadeUp 1s ease-out 0.2s backwards;
    background: linear-gradient(135deg, #fff 0%, var(--signature-gold) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-subtitle {
    font-size: 1.5rem;
    color: rgba(255, 255, 255, 0.7);
    max-width: 800px;
    margin: 0 auto;
    line-height: 1.8;
    animation: fadeUp 1s ease-out 0.4s backwards;
}

/* Story Section */
.story-section {
    max-width: 1200px;
    margin: 0 auto 120px;
    padding: 0 2rem;
}

.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    text-align: center;
    margin-bottom: 1rem;
    color: var(--signature-gold);
}

.section-subtitle {
    text-align: center;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 4rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-size: 0.9rem;
}

.story-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6rem;
    align-items: center;
}

.story-image {
    width: 100%;
    aspect-ratio: 4 / 5;
    background: linear-gradient(135deg, rgba(139, 0, 0, 0.3), rgba(212, 175, 55, 0.2));
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 5rem;
    color: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.story-content h3 {
    font-family: 'Playfair Display', serif;
    font-size: 2.5rem;
    margin-bottom: 1.5rem;
    color: var(--signature-gold);
}

.story-content p {
    font-size: 1.1rem;
    line-height: 1.8;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 1.5rem;
}

.story-content p:last-child {
    margin-bottom: 0;
}

/* Values Section */
.values-section {
    background: rgba(255, 255, 255, 0.02);
    padding: 120px 2rem;
    margin-bottom: 120px;
}

.values-grid {
    max-width: 1400px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 3rem;
}

.value-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 3rem;
    transition: all 0.4s ease;
    position: relative;
    overflow: hidden;
}

.value-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, var(--black-rose), var(--love-hurts), var(--signature-gold));
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.4s ease;
}

.value-card:hover::before {
    transform: scaleX(1);
}

.value-card:hover {
    transform: translateY(-10px);
    border-color: var(--signature-gold);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

.value-icon {
    font-size: 3rem;
    margin-bottom: 1.5rem;
    display: block;
}

.value-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    margin-bottom: 1rem;
    color: var(--signature-gold);
}

.value-description {
    font-size: 1rem;
    line-height: 1.8;
    color: rgba(255, 255, 255, 0.7);
}

/* Founder Section */
.founder-section {
    max-width: 1000px;
    margin: 0 auto 120px;
    padding: 0 2rem;
    text-align: center;
}

.founder-quote {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    line-height: 1.6;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 2rem;
    font-style: italic;
    position: relative;
    padding: 0 3rem;
}

.founder-quote::before,
.founder-quote::after {
    font-size: 4rem;
    color: var(--signature-gold);
    opacity: 0.3;
    position: absolute;
}

.founder-quote::before {
    content: '"';
    left: 0;
    top: -10px;
}

.founder-quote::after {
    content: '"';
    right: 0;
    bottom: -40px;
}

.founder-name {
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.6);
    letter-spacing: 2px;
    text-transform: uppercase;
}

/* CTA Section */
.cta-section {
    text-align: center;
    padding: 120px 2rem;
    background: linear-gradient(to bottom, transparent, rgba(212, 175, 55, 0.05));
}

.cta-title {
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    margin-bottom: 2rem;
}

.cta-buttons {
    display: flex;
    gap: 1.5rem;
    justify-content: center;
    flex-wrap: wrap;
}

.btn {
    padding: 1.2rem 3rem;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    text-decoration: none;
    border-radius: 2px;
    transition: all 0.4s ease;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
}

.btn-primary {
    background: var(--signature-gold);
    color: #000;
    border: 1px solid var(--signature-gold);
}

.btn-primary:hover {
    box-shadow: 0 0 30px var(--signature-gold);
    transform: translateY(-3px);
}

.btn-ghost {
    background: transparent;
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.3);
}

.btn-ghost:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: #fff;
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

/* Responsive */
@media (max-width: 1024px) {
    .story-grid {
        grid-template-columns: 1fr;
        gap: 3rem;
    }

    .story-image {
        order: -1;
    }
}

@media (max-width: 768px) {
    .hero-title {
        font-size: 3rem;
    }

    .hero-subtitle {
        font-size: 1.2rem;
    }

    .section-title {
        font-size: 2.5rem;
    }

    .story-content h3 {
        font-size: 2rem;
    }

    .founder-quote {
        font-size: 1.5rem;
        padding: 0 1.5rem;
    }

    .cta-buttons {
        flex-direction: column;
        max-width: 320px;
        margin: 0 auto;
    }

    .btn {
        width: 100%;
    }
}
</style>

<div class="about-page">
    <!-- Hero Section -->
    <section class="about-hero">
        <div>
            <div class="hero-badge">Since 2024</div>
            <h1 class="hero-title">Where Love Meets Luxury</h1>
            <p class="hero-subtitle">
                Oakland roots. Global vision. SkyyRose is more than fashion—it's a movement celebrating
                emotional depth, cultural richness, and uncompromising craftsmanship.
            </p>
        </div>
    </section>

    <!-- Story Section -->
    <section class="story-section">
        <h2 class="section-title">Our Story</h2>
        <p class="section-subtitle">Oakland Born, World Inspired</p>

        <div class="story-grid">
            <div class="story-image">
                ✦
            </div>
            <div class="story-content">
                <h3>Born from Oakland's Soul</h3>
                <p>
                    SkyyRose emerged from the vibrant streets of Oakland, where resilience meets creativity,
                    and cultural diversity fuels innovation. We saw a gap in luxury streetwear—a space that
                    celebrated emotion as strength, vulnerability as power.
                </p>
                <p>
                    Our founder, inspired by the raw beauty of Oakland's art scene and the timeless elegance
                    of haute couture, created SkyyRose to bridge these worlds. Each collection tells a story
                    of contrasts: soft and sharp, dark and luminous, street and runway.
                </p>
                <p>
                    We're not just selling clothes. We're curating experiences that empower our community
                    to express their authentic selves without compromise.
                </p>
            </div>
        </div>
    </section>

    <!-- Values Section -->
    <section class="values-section">
        <h2 class="section-title">Our Values</h2>
        <p class="section-subtitle">What Drives Us</p>

        <div class="values-grid">
            <div class="value-card">
                <span class="value-icon">❤️</span>
                <h3 class="value-title">Emotional Authenticity</h3>
                <p class="value-description">
                    We celebrate feeling deeply. Our designs honor vulnerability, passion, and the full
                    spectrum of human emotion as sources of strength and beauty.
                </p>
            </div>

            <div class="value-card">
                <span class="value-icon">✨</span>
                <h3 class="value-title">Uncompromising Quality</h3>
                <p class="value-description">
                    Premium fabrics, meticulous construction, and timeless design. Every piece is crafted
                    to last, transcending trends and standing the test of time.
                </p>
            </div>

            <div class="value-card">
                <span class="value-icon">🌍</span>
                <h3 class="value-title">Cultural Celebration</h3>
                <p class="value-description">
                    Oakland's diversity inspires us daily. We honor multiple cultures, stories, and
                    perspectives, weaving them into designs that resonate globally.
                </p>
            </div>

            <div class="value-card">
                <span class="value-icon">♻️</span>
                <h3 class="value-title">Conscious Creation</h3>
                <p class="value-description">
                    We're committed to ethical manufacturing and sustainable practices. Luxury should
                    elevate both the wearer and the world.
                </p>
            </div>

            <div class="value-card">
                <span class="value-icon">👁️</span>
                <h3 class="value-title">Artistic Vision</h3>
                <p class="value-description">
                    Fashion is art you wear. We push boundaries, experiment fearlessly, and create
                    pieces that make statements without saying a word.
                </p>
            </div>

            <div class="value-card">
                <span class="value-icon">🤝</span>
                <h3 class="value-title">Community First</h3>
                <p class="value-description">
                    SkyyRose is built by and for a community that values depth, creativity, and
                    self-expression. Your voice shapes our future.
                </p>
            </div>
        </div>
    </section>

    <!-- Founder Quote -->
    <section class="founder-section">
        <blockquote class="founder-quote">
            For those who dare to feel, who refuse to dim their light, who understand that luxury
            is not just what you wear but how it makes you feel—SkyyRose is your sanctuary.
        </blockquote>
        <p class="founder-name">— SkyyRose Founder</p>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
        <h2 class="cta-title">Join the SkyyRose Movement</h2>
        <div class="cta-buttons">
            <a href="<?php echo esc_url(home_url('/')); ?>" class="btn btn-primary">
                Explore Collections
                <span>→</span>
            </a>
            <a href="<?php echo esc_url(home_url('/contact')); ?>" class="btn btn-ghost">
                Get in Touch
                <span>✉</span>
            </a>
        </div>
    </section>
</div>

<?php get_footer(); ?>
