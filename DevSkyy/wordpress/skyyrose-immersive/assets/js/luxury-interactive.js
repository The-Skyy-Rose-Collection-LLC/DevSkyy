/**
 * SkyyRose Luxury Interactive Experience
 * Magnetic cursor, parallax, hotspots, and collection-specific effects
 */

(function() {
    'use strict';

    // ============================================================
    // MAGNETIC CURSOR
    // ============================================================
    const initMagneticCursor = () => {
        // Skip on mobile/tablet
        if (window.innerWidth < 1024) return;

        // Create cursor elements
        const cursor = document.createElement('div');
        cursor.className = 'custom-cursor';
        document.body.appendChild(cursor);

        const cursorFollow = document.createElement('div');
        cursorFollow.className = 'custom-cursor-follow';
        document.body.appendChild(cursorFollow);

        let mouseX = 0, mouseY = 0;
        let cursorX = 0, cursorY = 0;
        let followX = 0, followY = 0;

        // Track mouse position
        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        });

        // Animate cursor with smooth interpolation
        const animateCursor = () => {
            // Main cursor (fast follow - 30%)
            const dX = mouseX - cursorX;
            const dY = mouseY - cursorY;
            cursorX += dX * 0.3;
            cursorY += dY * 0.3;
            cursor.style.left = cursorX + 'px';
            cursor.style.top = cursorY + 'px';

            // Follow cursor (slow follow - 10%)
            const dXFollow = mouseX - followX;
            const dYFollow = mouseY - followY;
            followX += dXFollow * 0.1;
            followY += dYFollow * 0.1;
            cursorFollow.style.left = followX + 'px';
            cursorFollow.style.top = followY + 'px';

            requestAnimationFrame(animateCursor);
        };
        animateCursor();

        // Cursor interactions
        const interactiveElements = document.querySelectorAll('a, button, .hotspot, .woocommerce ul.products li.product');
        interactiveElements.forEach(el => {
            el.addEventListener('mouseenter', () => {
                cursor.style.transform = 'scale(2)';
                cursorFollow.style.transform = 'scale(1.5)';
            });
            el.addEventListener('mouseleave', () => {
                cursor.style.transform = 'scale(1)';
                cursorFollow.style.transform = 'scale(1)';
            });
        });
    };

    // ============================================================
    // PARALLAX SCROLLING
    // ============================================================
    const initParallax = () => {
        const parallaxSections = document.querySelectorAll('.parallax-section');
        if (parallaxSections.length === 0) return;

        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;

            parallaxSections.forEach(section => {
                const speed = parseFloat(section.dataset.parallaxSpeed || '0.5');
                const yPos = -(scrolled * speed);
                section.style.transform = `translateY(${yPos}px)`;
            });
        });
    };

    // ============================================================
    // INTERACTIVE HOTSPOTS
    // ============================================================
    const initHotspots = () => {
        const hotspots = document.querySelectorAll('.hotspot');
        if (hotspots.length === 0) return;

        hotspots.forEach(hotspot => {
            // Pulse animation class
            hotspot.classList.add('hotspot-pulse');

            // Click navigation
            hotspot.addEventListener('click', (e) => {
                e.preventDefault();
                const collection = hotspot.dataset.collection;
                const product = hotspot.dataset.product;

                if (collection && product) {
                    window.location.href = `/pre-order/?collection=${collection}#${product}`;
                } else if (collection) {
                    window.location.href = `/pre-order/?collection=${collection}`;
                }
            });

            // Hover tooltip
            hotspot.addEventListener('mouseenter', (e) => {
                const tooltip = hotspot.querySelector('.hotspot-tooltip');
                if (tooltip) {
                    tooltip.style.opacity = '1';
                    tooltip.style.transform = 'translateY(-10px)';
                }
            });

            hotspot.addEventListener('mouseleave', (e) => {
                const tooltip = hotspot.querySelector('.hotspot-tooltip');
                if (tooltip) {
                    tooltip.style.opacity = '0';
                    tooltip.style.transform = 'translateY(0)';
                }
            });
        });
    };

    // ============================================================
    // SCROLL-TRIGGERED ANIMATIONS
    // ============================================================
    const initScrollAnimations = () => {
        const observerOptions = {
            threshold: 0.15,
            rootMargin: '0px 0px -100px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    // Optional: stop observing after animation
                    // observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observe all elements with animation classes
        const animatedElements = document.querySelectorAll('[class*="stagger-"], .fade-in, .slide-in, .scale-in');
        animatedElements.forEach(el => observer.observe(el));
    };

    // ============================================================
    // MAGNETIC BUTTON PULL
    // ============================================================
    const initMagneticButtons = () => {
        const buttons = document.querySelectorAll('.elementor-button, .woocommerce-button, .button');
        if (buttons.length === 0) return;

        buttons.forEach(button => {
            button.addEventListener('mousemove', (e) => {
                const rect = button.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;

                // Pull effect within 100px radius
                const distance = Math.sqrt(x * x + y * y);
                const maxDistance = 100;

                if (distance < maxDistance) {
                    const pull = 1 - (distance / maxDistance);
                    const moveX = x * pull * 0.3;
                    const moveY = y * pull * 0.3;
                    button.style.transform = `translate(${moveX}px, ${moveY}px)`;
                }
            });

            button.addEventListener('mouseleave', () => {
                button.style.transform = 'translate(0, 0)';
            });
        });
    };

    // ============================================================
    // SMOOTH SCROLL
    // ============================================================
    const initSmoothScroll = () => {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href === '#') return;

                e.preventDefault();
                const target = document.querySelector(href);
                if (!target) return;

                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            });
        });
    };

    // ============================================================
    // COUNTDOWN TIMERS (XSS-SAFE)
    // ============================================================
    const initCountdowns = () => {
        const timers = document.querySelectorAll('.countdown-timer');
        if (timers.length === 0) return;

        timers.forEach(timer => {
            const releaseDate = new Date(timer.dataset.releaseDate).getTime();

            const updateCountdown = () => {
                const now = new Date().getTime();
                const distance = releaseDate - now;

                // Clear timer safely (no innerHTML!)
                while (timer.firstChild) {
                    timer.removeChild(timer.firstChild);
                }

                if (distance < 0) {
                    const label = document.createElement('span');
                    label.className = 'countdown-label';
                    label.textContent = 'Available Now!';
                    timer.appendChild(label);
                    return;
                }

                // Calculate time segments
                const days = Math.floor(distance / (1000 * 60 * 60 * 24));
                const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((distance % (1000 * 60)) / 1000);

                // Create countdown segments safely
                const segments = [
                    { value: days, label: 'Days' },
                    { value: hours, label: 'Hours' },
                    { value: minutes, label: 'Mins' },
                    { value: seconds, label: 'Secs' }
                ];

                segments.forEach(seg => {
                    const segmentDiv = document.createElement('div');
                    segmentDiv.className = 'countdown-segment';

                    const numberSpan = document.createElement('span');
                    numberSpan.className = 'countdown-number';
                    numberSpan.textContent = seg.value;

                    const labelSpan = document.createElement('span');
                    labelSpan.className = 'countdown-label';
                    labelSpan.textContent = seg.label;

                    segmentDiv.appendChild(numberSpan);
                    segmentDiv.appendChild(labelSpan);
                    timer.appendChild(segmentDiv);
                });
            };

            // Update immediately and every second
            updateCountdown();
            setInterval(updateCountdown, 1000);
        });
    };

    // ============================================================
    // FLOATING ROSE PETALS (Love Hurts Collection)
    // ============================================================
    const initFloatingPetals = () => {
        const petalContainer = document.querySelector('.floating-petals-container');
        if (!petalContainer) return;

        const petalCount = 20;

        for (let i = 0; i < petalCount; i++) {
            const petal = document.createElement('div');
            petal.className = 'floating-petal';

            // Random positioning and timing
            const leftPos = Math.random() * 100;
            const animationDelay = Math.random() * 10;
            const animationDuration = 15 + Math.random() * 10; // 15-25s
            const scale = 0.5 + Math.random() * 0.5; // 0.5-1.0

            petal.style.left = leftPos + '%';
            petal.style.animationDelay = animationDelay + 's';
            petal.style.animationDuration = animationDuration + 's';
            petal.style.transform = `scale(${scale})`;

            petalContainer.appendChild(petal);
        }
    };

    // ============================================================
    // GLASS CLOCHE HOVER EFFECT (Love Hurts Collection)
    // ============================================================
    const initGlassCloches = () => {
        const cloches = document.querySelectorAll('.glass-cloche');
        if (cloches.length === 0) return;

        cloches.forEach(cloche => {
            cloche.addEventListener('mousemove', (e) => {
                const rect = cloche.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;

                // Create radial gradient following mouse for reflection effect
                cloche.style.setProperty('--mouse-x', x + '%');
                cloche.style.setProperty('--mouse-y', y + '%');
            });

            cloche.addEventListener('mouseleave', () => {
                cloche.style.setProperty('--mouse-x', '50%');
                cloche.style.setProperty('--mouse-y', '50%');
            });
        });
    };

    // ============================================================
    // LAZY LOAD IMAGES
    // ============================================================
    const initLazyLoad = () => {
        const images = document.querySelectorAll('img[data-src]');
        if (images.length === 0) return;

        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    };

    // ============================================================
    // INITIALIZE ALL
    // ============================================================
    const init = () => {
        // Core interactions
        initMagneticCursor();
        initParallax();
        initScrollAnimations();
        initSmoothScroll();
        initMagneticButtons();

        // Hotspots and countdowns
        initHotspots();
        initCountdowns();

        // Collection-specific effects
        initFloatingPetals();
        initGlassCloches();

        // Performance
        initLazyLoad();

        // Add loaded class for CSS transitions
        document.body.classList.add('luxury-interactive-loaded');
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
