/**
 * SkyyRose 2025 - Luxury GSAP Animations
 *
 * Comprehensive animation system with rose gold aesthetics
 * Framer Motion-inspired timing and easing
 *
 * @version 3.0.0
 */
(function() {
    'use strict';

    // === Configuration ===
    const config = {
        colors: {
            roseGold: '#B76E79',
            gold: '#D4AF37',
            darkSlate: '#1a1a1a'
        },
        easing: {
            luxury: 'power3.out',
            smooth: 'power2.inOut',
            bounce: 'elastic.out(1, 0.5)',
            snap: 'back.out(1.7)'
        },
        durations: {
            fast: 0.3,
            normal: 0.6,
            slow: 1.2,
            verySlow: 1.8
        },
        stagger: {
            cards: 0.15,
            text: 0.03,
            buttons: 0.1
        }
    };

    // === Utility Functions ===
    function isMobile() {
        return window.innerWidth < 768;
    }

    function isReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    function addRoseGoldGlow(element) {
        return gsap.to(element, {
            boxShadow: `0 0 30px ${config.colors.roseGold}40`,
            duration: config.durations.fast,
            paused: true
        });
    }

    // === Initialize ===
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
            console.warn('GSAP or ScrollTrigger not loaded');
            return;
        }

        // Skip animations if reduced motion preferred
        if (isReducedMotion()) {
            console.log('Reduced motion preferred - animations disabled');
            return;
        }

        gsap.registerPlugin(ScrollTrigger);

        // Initialize all animation modules
        initPageLoadAnimations();
        initHeroAnimations();
        initScrollAnimations();
        initHoverEffects();
        initNavigationAnimations();
        initProductAnimations();
        initTextAnimations();
        initImageAnimations();
        initFormAnimations();
        initPageTransitions();
    });

    // === 1. Page Load Animations ===
    function initPageLoadAnimations() {
        const tl = gsap.timeline({ defaults: { ease: config.easing.luxury } });

        // Fade in body
        tl.from('body', {
            opacity: 0,
            duration: config.durations.fast
        });

        // Animate header
        if (document.querySelector('.site-header')) {
            tl.from('.site-header', {
                y: -100,
                opacity: 0,
                duration: config.durations.normal
            }, '-=0.3');
        }

        // Animate main content
        if (document.querySelector('main')) {
            tl.from('main > *', {
                y: 30,
                opacity: 0,
                stagger: config.stagger.cards,
                duration: config.durations.normal
            }, '-=0.2');
        }
    }

    // === 2. Hero Section Animations ===
    function initHeroAnimations() {
        const hero = document.querySelector('.hero, .page-header, .entry-header');
        if (!hero) return;

        const tl = gsap.timeline({
            scrollTrigger: {
                trigger: hero,
                start: 'top 80%',
                once: true
            }
        });

        // Hero title
        const heroTitle = hero.querySelector('h1, .hero-title');
        if (heroTitle) {
            tl.from(heroTitle, {
                y: 50,
                opacity: 0,
                duration: config.durations.slow,
                ease: config.easing.luxury
            });
        }

        // Hero subtitle/description
        const heroSubtitle = hero.querySelector('p, .hero-subtitle, .entry-meta');
        if (heroSubtitle) {
            tl.from(heroSubtitle, {
                y: 30,
                opacity: 0,
                duration: config.durations.normal,
                ease: config.easing.luxury
            }, '-=0.6');
        }

        // Hero buttons/CTAs
        const heroButtons = hero.querySelectorAll('a, button, .btn, .cta');
        if (heroButtons.length > 0) {
            tl.from(heroButtons, {
                y: 20,
                opacity: 0,
                stagger: config.stagger.buttons,
                duration: config.durations.normal,
                ease: config.easing.luxury
            }, '-=0.4');
        }

        // Hero image with Ken Burns effect
        const heroImage = hero.querySelector('img, .hero-image');
        if (heroImage) {
            tl.from(heroImage, {
                scale: 1.2,
                opacity: 0,
                duration: config.durations.verySlow,
                ease: config.easing.smooth
            }, 0);
        }
    }

    // === 3. Scroll Animations ===
    function initScrollAnimations() {
        // Fade in sections
        const sections = document.querySelectorAll('section, article, .content-section');
        sections.forEach(section => {
            gsap.from(section, {
                scrollTrigger: {
                    trigger: section,
                    start: 'top 85%',
                    toggleActions: 'play none none reverse'
                },
                y: 50,
                opacity: 0,
                duration: config.durations.slow,
                ease: config.easing.luxury
            });
        });

        // Stagger animate post cards
        const postCards = document.querySelectorAll('.post-card, .entry, .product');
        if (postCards.length > 0) {
            gsap.from(postCards, {
                scrollTrigger: {
                    trigger: postCards[0],
                    start: 'top 80%',
                },
                opacity: 0,
                y: 50,
                scale: 0.95,
                stagger: config.stagger.cards,
                duration: config.durations.slow,
                ease: config.easing.luxury
            });
        }

        // Glass panel reveal
        const glassPanels = document.querySelectorAll('.glass, .card, .box');
        glassPanels.forEach(panel => {
            gsap.from(panel, {
                scrollTrigger: {
                    trigger: panel,
                    start: 'top 90%',
                },
                opacity: 0,
                scale: 0.95,
                duration: config.durations.normal,
                ease: config.easing.luxury
            });
        });

        // Parallax effect on images (desktop only)
        if (!isMobile()) {
            const parallaxImages = document.querySelectorAll('.post-thumbnail img, .entry-thumbnail img, .parallax-image');
            parallaxImages.forEach(img => {
                gsap.to(img, {
                    scrollTrigger: {
                        trigger: img,
                        start: 'top bottom',
                        end: 'bottom top',
                        scrub: 1,
                    },
                    y: -50,
                    ease: 'none'
                });
            });
        }

        // Fade in text blocks
        const textBlocks = document.querySelectorAll('.entry-content > p, .entry-content > ul, .entry-content > ol, .entry-content > blockquote');
        textBlocks.forEach(block => {
            gsap.from(block, {
                scrollTrigger: {
                    trigger: block,
                    start: 'top 90%',
                },
                opacity: 0,
                x: -30,
                duration: config.durations.normal,
                ease: config.easing.luxury
            });
        });

        // Animate counters
        const counters = document.querySelectorAll('.counter, .stat-number, [data-count]');
        counters.forEach(counter => {
            const target = parseInt(counter.dataset.count || counter.textContent);
            gsap.from(counter, {
                scrollTrigger: {
                    trigger: counter,
                    start: 'top 80%',
                    once: true
                },
                textContent: 0,
                duration: config.durations.verySlow,
                ease: 'power1.inOut',
                snap: { textContent: 1 },
                onUpdate: function() {
                    counter.textContent = Math.ceil(this.targets()[0].textContent);
                }
            });
        });
    }

    // === 4. Hover Effects ===
    function initHoverEffects() {
        // Button hover effects
        const buttons = document.querySelectorAll('button, .btn, .button, input[type="submit"], a.cta');
        buttons.forEach(btn => {
            const glowAnimation = addRoseGoldGlow(btn);

            btn.addEventListener('mouseenter', () => {
                gsap.to(btn, {
                    scale: 1.05,
                    duration: config.durations.fast,
                    ease: config.easing.snap
                });
                glowAnimation.play();
            });

            btn.addEventListener('mouseleave', () => {
                gsap.to(btn, {
                    scale: 1,
                    duration: config.durations.fast,
                    ease: config.easing.smooth
                });
                glowAnimation.reverse();
            });
        });

        // Link hover effects
        const links = document.querySelectorAll('.entry-content a, .nav-link, .menu-item a');
        links.forEach(link => {
            link.addEventListener('mouseenter', () => {
                gsap.to(link, {
                    color: config.colors.roseGold,
                    duration: config.durations.fast,
                    ease: config.easing.smooth
                });
            });

            link.addEventListener('mouseleave', () => {
                gsap.to(link, {
                    color: '',
                    duration: config.durations.fast,
                    ease: config.easing.smooth
                });
            });
        });

        // Card hover effects
        const cards = document.querySelectorAll('.post-card, .product-card, .card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                gsap.to(card, {
                    y: -10,
                    boxShadow: `0 20px 40px ${config.colors.roseGold}20`,
                    duration: config.durations.fast,
                    ease: config.easing.luxury
                });
            });

            card.addEventListener('mouseleave', () => {
                gsap.to(card, {
                    y: 0,
                    boxShadow: '',
                    duration: config.durations.fast,
                    ease: config.easing.smooth
                });
            });
        });

        // Image hover zoom
        const imageContainers = document.querySelectorAll('.post-thumbnail, .product-image, .thumbnail');
        imageContainers.forEach(container => {
            const img = container.querySelector('img');
            if (!img) return;

            container.addEventListener('mouseenter', () => {
                gsap.to(img, {
                    scale: 1.1,
                    duration: config.durations.slow,
                    ease: config.easing.smooth
                });
            });

            container.addEventListener('mouseleave', () => {
                gsap.to(img, {
                    scale: 1,
                    duration: config.durations.slow,
                    ease: config.easing.smooth
                });
            });
        });
    }

    // === 5. Navigation Animations ===
    function initNavigationAnimations() {
        // Mobile menu toggle
        const menuToggle = document.querySelector('.menu-toggle, .mobile-menu-toggle');
        const mobileMenu = document.querySelector('.mobile-menu, .menu-primary-container');

        if (menuToggle && mobileMenu) {
            menuToggle.addEventListener('click', () => {
                const isOpen = mobileMenu.classList.contains('active');

                if (!isOpen) {
                    // Open menu
                    mobileMenu.classList.add('active');
                    gsap.from(mobileMenu, {
                        x: -300,
                        opacity: 0,
                        duration: config.durations.normal,
                        ease: config.easing.luxury
                    });

                    // Stagger menu items
                    const menuItems = mobileMenu.querySelectorAll('.menu-item');
                    gsap.from(menuItems, {
                        x: -50,
                        opacity: 0,
                        stagger: 0.05,
                        duration: config.durations.fast,
                        ease: config.easing.luxury
                    });
                } else {
                    // Close menu
                    gsap.to(mobileMenu, {
                        x: -300,
                        opacity: 0,
                        duration: config.durations.fast,
                        ease: config.easing.smooth,
                        onComplete: () => {
                            mobileMenu.classList.remove('active');
                        }
                    });
                }
            });
        }

        // Scroll header effect
        const header = document.querySelector('.site-header, header');
        if (header) {
            ScrollTrigger.create({
                start: 'top -100',
                end: 99999,
                toggleClass: { targets: header, className: 'scrolled' },
                onEnter: () => {
                    gsap.to(header, {
                        backgroundColor: 'rgba(0, 0, 0, 0.95)',
                        backdropFilter: 'blur(20px)',
                        duration: config.durations.fast
                    });
                },
                onLeaveBack: () => {
                    gsap.to(header, {
                        backgroundColor: 'transparent',
                        backdropFilter: 'none',
                        duration: config.durations.fast
                    });
                }
            });
        }
    }

    // === 6. Product Animations (WooCommerce) ===
    function initProductAnimations() {
        // Product card entrance
        const products = document.querySelectorAll('.product, .woocommerce-LoopProduct-link');
        if (products.length > 0) {
            gsap.from(products, {
                scrollTrigger: {
                    trigger: products[0],
                    start: 'top 80%',
                },
                opacity: 0,
                y: 50,
                scale: 0.95,
                stagger: config.stagger.cards,
                duration: config.durations.slow,
                ease: config.easing.luxury
            });
        }

        // Add to cart button animation
        const addToCartButtons = document.querySelectorAll('.add_to_cart_button, .single_add_to_cart_button');
        addToCartButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                if (!this.classList.contains('loading')) {
                    gsap.to(this, {
                        scale: 0.9,
                        duration: 0.1,
                        yoyo: true,
                        repeat: 1,
                        ease: config.easing.smooth
                    });
                }
            });
        });

        // Product image gallery animations
        const productImages = document.querySelectorAll('.woocommerce-product-gallery__image');
        productImages.forEach((img, index) => {
            gsap.from(img, {
                scrollTrigger: {
                    trigger: img,
                    start: 'top 85%',
                },
                opacity: 0,
                scale: 0.9,
                duration: config.durations.normal,
                delay: index * 0.1,
                ease: config.easing.luxury
            });
        });

        // Price reveal animation
        const prices = document.querySelectorAll('.price, .woocommerce-Price-amount');
        prices.forEach(price => {
            gsap.from(price, {
                scrollTrigger: {
                    trigger: price,
                    start: 'top 90%',
                },
                scale: 0,
                opacity: 0,
                duration: config.durations.normal,
                ease: config.easing.bounce
            });
        });
    }

    // === 7. Text Animations ===
    function initTextAnimations() {
        // Split text animation for headings
        const headings = document.querySelectorAll('h1, h2, h3, .animate-text');
        headings.forEach(heading => {
            if (heading.classList.contains('animated')) return;

            const text = heading.textContent;
            const chars = text.split('');
            heading.textContent = '';
            heading.classList.add('animated');

            chars.forEach(char => {
                const span = document.createElement('span');
                span.textContent = char === ' ' ? '\u00A0' : char;
                span.style.display = 'inline-block';
                heading.appendChild(span);
            });

            gsap.from(heading.children, {
                scrollTrigger: {
                    trigger: heading,
                    start: 'top 85%',
                },
                opacity: 0,
                y: 20,
                stagger: config.stagger.text,
                duration: config.durations.fast,
                ease: config.easing.luxury
            });
        });

        // Highlight animation for emphasized text
        const emphasized = document.querySelectorAll('em, strong, mark, .highlight');
        emphasized.forEach(el => {
            gsap.from(el, {
                scrollTrigger: {
                    trigger: el,
                    start: 'top 90%',
                },
                backgroundColor: 'transparent',
                color: 'inherit',
                duration: config.durations.normal,
                ease: config.easing.smooth
            });
        });
    }

    // === 8. Image Animations ===
    function initImageAnimations() {
        // Lazy load reveal
        const images = document.querySelectorAll('img[loading="lazy"], .lazy-image');
        images.forEach(img => {
            img.addEventListener('load', function() {
                gsap.from(this, {
                    opacity: 0,
                    scale: 1.1,
                    duration: config.durations.normal,
                    ease: config.easing.luxury
                });
            });
        });

        // Image overlay reveal
        const imageOverlays = document.querySelectorAll('.image-overlay, .overlay');
        imageOverlays.forEach(overlay => {
            gsap.from(overlay, {
                scrollTrigger: {
                    trigger: overlay,
                    start: 'top 85%',
                },
                scaleX: 0,
                transformOrigin: 'left',
                duration: config.durations.slow,
                ease: config.easing.luxury
            });
        });

        // Gallery animations
        const galleries = document.querySelectorAll('.gallery, .wp-block-gallery');
        galleries.forEach(gallery => {
            const items = gallery.querySelectorAll('.gallery-item, .wp-block-image');
            gsap.from(items, {
                scrollTrigger: {
                    trigger: gallery,
                    start: 'top 80%',
                },
                opacity: 0,
                scale: 0.8,
                stagger: 0.1,
                duration: config.durations.normal,
                ease: config.easing.luxury
            });
        });
    }

    // === 9. Form Animations ===
    function initFormAnimations() {
        // Form field focus effects
        const formFields = document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"], input[type="password"], textarea, select');
        formFields.forEach(field => {
            field.addEventListener('focus', function() {
                gsap.to(this, {
                    borderColor: config.colors.roseGold,
                    boxShadow: `0 0 0 3px ${config.colors.roseGold}20`,
                    duration: config.durations.fast,
                    ease: config.easing.smooth
                });

                // Animate label if exists
                const label = this.previousElementSibling;
                if (label && label.tagName === 'LABEL') {
                    gsap.to(label, {
                        color: config.colors.roseGold,
                        y: -5,
                        duration: config.durations.fast,
                        ease: config.easing.smooth
                    });
                }
            });

            field.addEventListener('blur', function() {
                gsap.to(this, {
                    borderColor: '',
                    boxShadow: '',
                    duration: config.durations.fast,
                    ease: config.easing.smooth
                });

                const label = this.previousElementSibling;
                if (label && label.tagName === 'LABEL') {
                    gsap.to(label, {
                        color: '',
                        y: 0,
                        duration: config.durations.fast,
                        ease: config.easing.smooth
                    });
                }
            });
        });

        // Form submit animation
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const submitBtn = this.querySelector('[type="submit"]');
                if (submitBtn && !submitBtn.classList.contains('loading')) {
                    gsap.to(submitBtn, {
                        scale: 0.95,
                        duration: 0.1,
                        yoyo: true,
                        repeat: 1
                    });
                }
            });
        });

        // Animate form on scroll
        const visibleForms = document.querySelectorAll('form:not(.woocommerce-form-login):not(.woocommerce-form-register)');
        visibleForms.forEach(form => {
            const formElements = form.querySelectorAll('input, textarea, select, button');
            gsap.from(formElements, {
                scrollTrigger: {
                    trigger: form,
                    start: 'top 85%',
                },
                opacity: 0,
                y: 20,
                stagger: 0.05,
                duration: config.durations.normal,
                ease: config.easing.luxury
            });
        });
    }

    // === 10. Page Transitions ===
    function initPageTransitions() {
        // Smooth scroll to anchor links
        const anchorLinks = document.querySelectorAll('a[href^="#"]:not([href="#"])');
        anchorLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    e.preventDefault();
                    gsap.to(window, {
                        scrollTo: {
                            y: target,
                            offsetY: 100
                        },
                        duration: config.durations.slow,
                        ease: config.easing.smooth
                    });
                }
            });
        });

        // Page exit animation (optional - requires additional setup)
        const pageLinks = document.querySelectorAll('a:not([href^="#"]):not([target="_blank"])');
        pageLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                if (this.href && !this.href.includes('#') && this.hostname === window.location.hostname) {
                    // Optional: Add page exit animation here
                }
            });
        });
    }

    // === Scroll to Top Button ===
    const scrollTopBtn = document.querySelector('.scroll-to-top, #scroll-to-top');
    if (scrollTopBtn) {
        ScrollTrigger.create({
            start: 'top -200',
            end: 99999,
            onEnter: () => {
                gsap.to(scrollTopBtn, {
                    opacity: 1,
                    pointerEvents: 'auto',
                    duration: config.durations.fast
                });
            },
            onLeaveBack: () => {
                gsap.to(scrollTopBtn, {
                    opacity: 0,
                    pointerEvents: 'none',
                    duration: config.durations.fast
                });
            }
        });

        scrollTopBtn.addEventListener('click', () => {
            gsap.to(window, {
                scrollTo: { y: 0 },
                duration: config.durations.slow,
                ease: config.easing.smooth
            });
        });
    }

})();
