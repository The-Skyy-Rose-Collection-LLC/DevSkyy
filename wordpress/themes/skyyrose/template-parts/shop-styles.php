<?php
/**
 * Shop Styles - SkyyRose Luxury Experience
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;
?>
<style>
/* ========================================
   SKYYROSE CUSTOM SHOP - DARK LUXURY
   ======================================== */

.skyyrose-shop {
    --sr-bg: #050505;
    --sr-surface: #0a0a0a;
    --sr-border: rgba(255, 255, 255, 0.08);
    --sr-text: #f5f5f5;
    --sr-text-muted: rgba(255, 255, 255, 0.6);
    --sr-rose: #B76E79;
    --sr-gold: #D4AF37;
    --sr-crimson: #8B0000;

    background: var(--sr-bg);
    color: var(--sr-text);
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
}

/* Container */
.skyyrose-shop .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 clamp(1rem, 4vw, 3rem);
}

/* ========================================
   AMBIENT BACKGROUND
   ======================================== */

.shop-ambient {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}

.ambient-orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(100px);
    opacity: 0.15;
    animation: orbFloat 20s ease-in-out infinite;
}

.ambient-orb--1 {
    width: 600px;
    height: 600px;
    background: var(--sr-rose);
    top: -200px;
    right: -200px;
    animation-delay: 0s;
}

.ambient-orb--2 {
    width: 400px;
    height: 400px;
    background: var(--sr-gold);
    bottom: 20%;
    left: -100px;
    animation-delay: -7s;
}

.ambient-orb--3 {
    width: 500px;
    height: 500px;
    background: var(--sr-crimson);
    top: 50%;
    right: 10%;
    animation-delay: -14s;
}

@keyframes orbFloat {
    0%, 100% {
        transform: translate(0, 0) scale(1);
    }
    25% {
        transform: translate(30px, -30px) scale(1.05);
    }
    50% {
        transform: translate(-20px, 20px) scale(0.95);
    }
    75% {
        transform: translate(-30px, -20px) scale(1.02);
    }
}

/* ========================================
   HERO SECTION
   ======================================== */

.shop-hero {
    position: relative;
    z-index: 1;
    padding: clamp(4rem, 12vh, 8rem) 0 clamp(2rem, 6vh, 4rem);
    text-align: center;
}

.shop-hero__content {
    max-width: 800px;
    margin: 0 auto;
}

.shop-hero__eyebrow {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: var(--sr-rose);
    margin-bottom: 1.5rem;
    position: relative;
    padding: 0 2rem;
}

.shop-hero__eyebrow::before,
.shop-hero__eyebrow::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 40px;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--sr-rose));
}

.shop-hero__eyebrow::before {
    right: 100%;
    background: linear-gradient(90deg, transparent, var(--sr-rose));
}

.shop-hero__eyebrow::after {
    left: 100%;
    background: linear-gradient(90deg, var(--sr-rose), transparent);
}

.shop-hero__title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    font-weight: 400;
    line-height: 1.1;
    margin: 0 0 1.5rem;
    background: linear-gradient(135deg, #fff 0%, var(--sr-rose) 50%, var(--sr-gold) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.shop-hero__subtitle {
    font-size: 1.125rem;
    color: var(--sr-text-muted);
    max-width: 500px;
    margin: 0 auto;
    line-height: 1.6;
}

/* ========================================
   FILTER TABS
   ======================================== */

.shop-filters {
    position: relative;
    z-index: 1;
    padding: 0 0 3rem;
}

.filter-tabs {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.filter-tab {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: var(--sr-surface);
    border: 1px solid var(--sr-border);
    border-radius: 100px;
    color: var(--sr-text-muted);
    font-size: 0.875rem;
    font-weight: 500;
    text-decoration: none;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.filter-tab::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, var(--tab-color), transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.filter-tab:hover {
    border-color: var(--tab-color);
    color: var(--sr-text);
    transform: translateY(-2px);
}

.filter-tab:hover::before {
    opacity: 0.1;
}

.filter-tab.is-active {
    background: var(--tab-color);
    border-color: var(--tab-color);
    color: #fff;
}

.filter-tab__name {
    position: relative;
    z-index: 1;
}

.filter-tab__indicator {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--tab-color);
    position: relative;
    z-index: 1;
}

.filter-tab.is-active .filter-tab__indicator {
    background: #fff;
}

/* ========================================
   PRODUCTS GRID
   ======================================== */

.shop-products {
    position: relative;
    z-index: 1;
    padding: 0 0 6rem;
}

.products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 2rem;
}

@media (min-width: 768px) {
    .products-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (min-width: 1200px) {
    .products-grid {
        grid-template-columns: repeat(4, 1fr);
    }
}

/* ========================================
   PRODUCT CARD
   ======================================== */

.product-card {
    position: relative;
    background: var(--sr-surface);
    border: 1px solid var(--sr-border);
    border-radius: 16px;
    overflow: hidden;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-card:hover {
    transform: translateY(-8px);
    border-color: rgba(255, 255, 255, 0.15);
    box-shadow:
        0 20px 40px rgba(0, 0, 0, 0.4),
        0 0 0 1px rgba(255, 255, 255, 0.05) inset;
}

.product-card__link {
    display: block;
    text-decoration: none;
    color: inherit;
}

/* Image Container */
.product-card__image-wrapper {
    position: relative;
    aspect-ratio: 3/4;
    overflow: hidden;
    background: linear-gradient(135deg, #111 0%, #0a0a0a 100%);
}

.product-card__image {
    position: relative;
    width: 100%;
    height: 100%;
}

.product-card__img {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-card__img--primary {
    opacity: 1;
}

.product-card__img--hover {
    opacity: 0;
}

.product-card:hover .product-card__img--primary {
    opacity: 0;
    transform: scale(1.05);
}

.product-card:hover .product-card__img--hover {
    opacity: 1;
    transform: scale(1);
}

.product-card__placeholder {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--sr-text-muted);
}

/* Quick Actions */
.product-card__actions {
    position: absolute;
    bottom: 1rem;
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    display: flex;
    gap: 0.5rem;
    opacity: 0;
    transition: all 0.3s ease;
}

.product-card:hover .product-card__actions {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}

.product-card__action {
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    color: #fff;
    cursor: pointer;
    transition: all 0.2s ease;
}

.product-card__action:hover {
    background: var(--sr-rose);
    border-color: var(--sr-rose);
    transform: scale(1.1);
}

/* Collection Badge */
.product-card__badge {
    position: absolute;
    top: 1rem;
    left: 1rem;
    padding: 0.375rem 0.75rem;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid var(--badge-color);
    border-radius: 100px;
    font-size: 0.625rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--badge-color);
}

/* Product Info */
.product-card__info {
    padding: 1.25rem;
}

.product-card__title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1rem;
    font-weight: 500;
    margin: 0 0 0.5rem;
    line-height: 1.3;
    color: var(--sr-text);
}

.product-card__price {
    font-size: 0.875rem;
    color: var(--sr-rose);
    font-weight: 500;
}

.product-card__price del {
    color: var(--sr-text-muted);
    margin-right: 0.5rem;
}

.product-card__price ins {
    text-decoration: none;
}

/* ========================================
   LOAD MORE
   ======================================== */

.shop-load-more {
    text-align: center;
    margin-top: 4rem;
}

.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 1rem 2rem;
    font-size: 0.875rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    border-radius: 100px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    text-decoration: none;
}

.btn--outline {
    background: transparent;
    border: 1px solid var(--sr-border);
    color: var(--sr-text);
}

.btn--outline:hover {
    background: var(--sr-rose);
    border-color: var(--sr-rose);
    transform: translateY(-2px);
}

.btn--primary {
    background: var(--sr-rose);
    border: 1px solid var(--sr-rose);
    color: #fff;
}

.btn--primary:hover {
    background: #a55d67;
    transform: translateY(-2px);
}

.btn--lg {
    padding: 1.25rem 2.5rem;
}

/* ========================================
   EMPTY STATE
   ======================================== */

.shop-empty {
    text-align: center;
    padding: 4rem 2rem;
}

.shop-empty p {
    color: var(--sr-text-muted);
    margin-bottom: 2rem;
}

/* ========================================
   GSAP ANIMATIONS
   ======================================== */

.gsap-fade-up {
    opacity: 0;
    transform: translateY(40px);
}

/* ========================================
   QUICK VIEW MODAL
   ======================================== */

.quickview-modal {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
}

.quickview-modal.is-active {
    opacity: 1;
    visibility: visible;
}

.quickview-modal__overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.9);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.quickview-modal__content {
    position: relative;
    max-width: 900px;
    width: 100%;
    max-height: 90vh;
    background: var(--sr-surface);
    border: 1px solid var(--sr-border);
    border-radius: 24px;
    overflow: hidden;
    transform: scale(0.9);
    transition: transform 0.3s ease;
}

.quickview-modal.is-active .quickview-modal__content {
    transform: scale(1);
}

.quickview-modal__close {
    position: absolute;
    top: 1rem;
    right: 1rem;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.5);
    border: none;
    border-radius: 50%;
    color: #fff;
    cursor: pointer;
    z-index: 10;
    transition: all 0.2s ease;
}

.quickview-modal__close:hover {
    background: var(--sr-rose);
}

.quickview-modal__inner {
    display: grid;
    grid-template-columns: 1fr 1fr;
    min-height: 500px;
}

@media (max-width: 768px) {
    .quickview-modal__inner {
        grid-template-columns: 1fr;
    }
}

.quickview-modal__image {
    background: #111;
    display: flex;
    align-items: center;
    justify-content: center;
}

.quickview-modal__image img {
    max-width: 100%;
    max-height: 500px;
    object-fit: contain;
}

.quickview-modal__details {
    padding: 2rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.quickview-modal__title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.75rem;
    margin: 0 0 1rem;
}

.quickview-modal__price {
    font-size: 1.25rem;
    color: var(--sr-rose);
    margin-bottom: 1.5rem;
}

.quickview-modal__description {
    color: var(--sr-text-muted);
    line-height: 1.7;
    margin-bottom: 2rem;
}

.quickview-modal__actions {
    display: flex;
    gap: 1rem;
}

/* ========================================
   ADD TO CART FEEDBACK
   ======================================== */

.cart-feedback {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    padding: 1rem 1.5rem;
    background: var(--sr-rose);
    color: #fff;
    border-radius: 12px;
    font-weight: 500;
    transform: translateY(100px);
    opacity: 0;
    transition: all 0.3s ease;
    z-index: 9999;
}

.cart-feedback.is-visible {
    transform: translateY(0);
    opacity: 1;
}

/* ========================================
   RESPONSIVE
   ======================================== */

@media (max-width: 768px) {
    .shop-hero {
        padding: 3rem 0 2rem;
    }

    .filter-tabs {
        justify-content: flex-start;
        overflow-x: auto;
        padding-bottom: 1rem;
        -webkit-overflow-scrolling: touch;
    }

    .filter-tab {
        flex-shrink: 0;
    }

    .products-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
    }

    .product-card__actions {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
    }
}

@media (max-width: 480px) {
    .products-grid {
        grid-template-columns: 1fr;
    }
}
</style>
