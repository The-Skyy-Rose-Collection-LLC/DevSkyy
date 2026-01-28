<?php
/**
 * Template Name: SkyyRose Experiences Landing
 * 
 * Landing page for all SkyyRose virtual experiences.
 * Parent page at /experience/
 */

get_header();
?>

<style>
    .skyyrose-experiences-landing {
        background: #1A1A1A;
        color: #FFFFFF;
        min-height: 100vh;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .landing-hero {
        background: linear-gradient(135deg, #1A1A1A 0%, #2A2520 50%, #1A1A1A 100%);
        padding: 6rem 2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .landing-hero::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(201, 169, 98, 0.1) 0%, transparent 70%);
        pointer-events: none;
    }

    .landing-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: clamp(2.5rem, 6vw, 4rem);
        color: #C9A962;
        margin-bottom: 1rem;
        letter-spacing: 3px;
        position: relative;
    }

    .landing-subtitle {
        font-size: 1.25rem;
        color: #E8E8E8;
        max-width: 600px;
        margin: 0 auto 2rem;
        line-height: 1.6;
    }

    .landing-tagline {
        font-style: italic;
        color: #C9A962;
        font-size: 1.125rem;
        letter-spacing: 1px;
    }

    .experiences-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
        gap: 2rem;
        max-width: 1400px;
        margin: 0 auto;
        padding: 4rem 2rem;
    }

    .experience-card {
        background: rgba(26, 26, 26, 0.8);
        border-radius: 20px;
        overflow: hidden;
        transition: all 0.4s ease;
        position: relative;
    }

    .experience-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--card-color);
        transform: scaleX(0);
        transition: transform 0.4s ease;
    }

    .experience-card:hover::before {
        transform: scaleX(1);
    }

    .experience-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    }

    .experience-card-visual {
        height: 250px;
        background: linear-gradient(135deg, var(--card-bg-start) 0%, var(--card-bg-end) 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }

    .experience-card-visual::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 100px;
        background: linear-gradient(to top, rgba(26, 26, 26, 1), transparent);
    }

    .experience-icon {
        font-size: 5rem;
        color: var(--card-color);
        text-shadow: 0 0 40px var(--card-color);
        animation: float 3s ease-in-out infinite;
        z-index: 1;
    }

    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }

    .experience-card-content {
        padding: 2rem;
    }

    .experience-card-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.75rem;
        color: var(--card-color);
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .experience-card-tagline {
        color: #E8E8E8;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }

    .experience-card-stats {
        display: flex;
        gap: 2rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .stat {
        text-align: center;
    }

    .stat-value {
        display: block;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--card-color);
    }

    .stat-label {
        font-size: 0.75rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .experience-card-actions {
        display: flex;
        gap: 1rem;
    }

    .exp-btn {
        flex: 1;
        padding: 1rem;
        border-radius: 8px;
        text-decoration: none;
        text-align: center;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .exp-btn-primary {
        background: var(--card-color);
        color: #0D0D0D;
    }

    .exp-btn-primary:hover {
        filter: brightness(1.1);
        transform: translateY(-2px);
    }

    .exp-btn-secondary {
        background: transparent;
        color: var(--card-color);
        border: 1px solid var(--card-color);
    }

    .exp-btn-secondary:hover {
        background: var(--card-color);
        color: #0D0D0D;
    }

    /* Signature card */
    .experience-card.signature {
        --card-color: #C9A962;
        --card-bg-start: #2A2520;
        --card-bg-end: #1A1A1A;
    }

    /* Black Rose card */
    .experience-card.black-rose {
        --card-color: #C0C0C0;
        --card-bg-start: #1A1A1A;
        --card-bg-end: #0D0D0D;
    }

    /* Love Hurts card */
    .experience-card.love-hurts {
        --card-color: #B76E79;
        --card-bg-start: #2A1A2A;
        --card-bg-end: #1A1A1A;
    }

    .landing-footer {
        text-align: center;
        padding: 4rem 2rem;
        border-top: 1px solid rgba(201, 169, 98, 0.1);
    }

    .landing-footer p {
        color: #888;
        margin-bottom: 1rem;
    }

    .landing-footer a {
        color: #C9A962;
        text-decoration: none;
    }

    @media (max-width: 768px) {
        .landing-hero {
            padding: 4rem 1rem;
        }

        .experiences-grid {
            grid-template-columns: 1fr;
            padding: 2rem 1rem;
        }

        .experience-card-actions {
            flex-direction: column;
        }
    }
</style>

<div class="skyyrose-experiences-landing">
    <header class="landing-hero">
        <h1 class="landing-title">Virtual Experiences</h1>
        <p class="landing-subtitle">
            Step into the world of SkyyRose luxury fashion. Explore our immersive 3D experiences 
            and discover pieces that define a generation of discerning taste.
        </p>
        <p class="landing-tagline">Where Love Meets Luxury</p>
    </header>

    <main class="experiences-grid">
        <!-- Signature Collection -->
        <article class="experience-card signature">
            <div class="experience-card-visual">
                <span class="experience-icon">◆</span>
            </div>
            <div class="experience-card-content">
                <h2 class="experience-card-title">
                    <span>◆</span> Signature Collection
                </h2>
                <p class="experience-card-tagline">
                    Our most celebrated pieces that define a generation of discerning taste. 
                    Gold accents meet premium luxury fabrics in this flagship collection.
                </p>
                <div class="experience-card-stats">
                    <div class="stat">
                        <span class="stat-value">5</span>
                        <span class="stat-label">Products</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">18k</span>
                        <span class="stat-label">Gold Accents</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">Limited</span>
                        <span class="stat-label">Edition</span>
                    </div>
                </div>
                <div class="experience-card-actions">
                    <a href="/experience/signature/" class="exp-btn exp-btn-primary">Enter Experience</a>
                    <a href="/experience/signature/shop/" class="exp-btn exp-btn-secondary">Shop Now</a>
                </div>
            </div>
        </article>

        <!-- Black Rose Collection -->
        <article class="experience-card black-rose">
            <div class="experience-card-visual">
                <span class="experience-icon">✦</span>
            </div>
            <div class="experience-card-content">
                <h2 class="experience-card-title">
                    <span>✦</span> Black Rose Collection
                </h2>
                <p class="experience-card-tagline">
                    A gothic journey through midnight gardens where shadow dances with silver. 
                    Noir elegance meets sterling sophistication.
                </p>
                <div class="experience-card-stats">
                    <div class="stat">
                        <span class="stat-value">5</span>
                        <span class="stat-label">Products</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">925</span>
                        <span class="stat-label">Sterling Silver</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">Limited</span>
                        <span class="stat-label">Edition</span>
                    </div>
                </div>
                <div class="experience-card-actions">
                    <a href="/experience/black-rose/" class="exp-btn exp-btn-primary">Enter Experience</a>
                    <a href="/experience/black-rose/shop/" class="exp-btn exp-btn-secondary">Shop Now</a>
                </div>
            </div>
        </article>

        <!-- Love Hurts Collection -->
        <article class="experience-card love-hurts">
            <div class="experience-card-visual">
                <span class="experience-icon">♥</span>
            </div>
            <div class="experience-card-content">
                <h2 class="experience-card-title">
                    <span>♥</span> Love Hurts Collection
                </h2>
                <p class="experience-card-tagline">
                    Where passion meets fragility in a castle of whispered confessions. 
                    Rose gold threading and tender vulnerability define this romantic collection.
                </p>
                <div class="experience-card-stats">
                    <div class="stat">
                        <span class="stat-value">5</span>
                        <span class="stat-label">Products</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">Rose</span>
                        <span class="stat-label">Gold Accents</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">Limited</span>
                        <span class="stat-label">Edition</span>
                    </div>
                </div>
                <div class="experience-card-actions">
                    <a href="/experience/love-hurts/" class="exp-btn exp-btn-primary">Enter Experience</a>
                    <a href="/experience/love-hurts/shop/" class="exp-btn exp-btn-secondary">Shop Now</a>
                </div>
            </div>
        </article>
    </main>

    <footer class="landing-footer">
        <p>Each piece is individually numbered and comes with a certificate of authenticity.</p>
        <p><a href="/about">Learn more about SkyyRose</a> · <a href="/contact">Contact Us</a></p>
    </footer>
</div>

<?php get_footer(); ?>
