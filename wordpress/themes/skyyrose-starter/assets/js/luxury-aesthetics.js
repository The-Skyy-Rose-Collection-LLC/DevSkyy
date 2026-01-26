/**
 * SkyyRose Luxury Aesthetics
 * Premium visual effects & interactions
 *
 * @package SkyyRose
 */

(function() {
    'use strict';

    window.SkyyRoseAesthetics = {

        // ============================================
        // CUSTOM CURSOR
        // ============================================

        initCursor: function() {
            if (window.innerWidth < 768) return;

            const cursor = document.createElement('div');
            cursor.className = 'custom-cursor';
            document.body.appendChild(cursor);

            let mouseX = 0, mouseY = 0;
            let cursorX = 0, cursorY = 0;

            document.addEventListener('mousemove', function(e) {
                mouseX = e.clientX;
                mouseY = e.clientY;
            });

            const animateCursor = function() {
                cursorX += (mouseX - cursorX) * 0.15;
                cursorY += (mouseY - cursorY) * 0.15;
                cursor.style.left = cursorX - 10 + 'px';
                cursor.style.top = cursorY - 10 + 'px';
                requestAnimationFrame(animateCursor);
            };
            animateCursor();

            // Hover states
            const hoverElements = document.querySelectorAll('a, button, .product-card, .collection-card, input, textarea');
            hoverElements.forEach(function(el) {
                el.addEventListener('mouseenter', function() {
                    cursor.classList.add('hover');
                });
                el.addEventListener('mouseleave', function() {
                    cursor.classList.remove('hover');
                });
            });

            // Click state
            document.addEventListener('mousedown', function() {
                cursor.classList.add('click');
            });
            document.addEventListener('mouseup', function() {
                cursor.classList.remove('click');
            });
        },

        // ============================================
        // SCROLL ANIMATIONS
        // ============================================

        initScrollAnimations: function() {
            const animatedElements = document.querySelectorAll('.fade-in-up, .fade-in-left, .fade-in-right, .scale-in, .stagger-children');

            if (!animatedElements.length) {
                // Auto-add animations to common elements
                document.querySelectorAll('.section-header, .product-card, .collection-card, .value-card').forEach(function(el, i) {
                    el.classList.add('fade-in-up');
                    el.style.transitionDelay = (i % 4) * 0.1 + 's';
                });
            }

            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });

            document.querySelectorAll('.fade-in-up, .fade-in-left, .fade-in-right, .scale-in, .stagger-children').forEach(function(el) {
                observer.observe(el);
            });
        },

        // ============================================
        // PARALLAX EFFECT
        // ============================================

        initParallax: function() {
            const parallaxElements = document.querySelectorAll('[data-parallax]');

            if (!parallaxElements.length) return;

            var ticking = false;

            window.addEventListener('scroll', function() {
                if (!ticking) {
                    requestAnimationFrame(function() {
                        var scrollY = window.scrollY;

                        parallaxElements.forEach(function(el) {
                            var speed = parseFloat(el.dataset.parallax) || 0.5;
                            var rect = el.getBoundingClientRect();
                            var offset = (rect.top + scrollY) - scrollY;
                            el.style.transform = 'translateY(' + (offset * speed * -0.1) + 'px)';
                        });

                        ticking = false;
                    });
                    ticking = true;
                }
            }, { passive: true });
        },

        // ============================================
        // MAGNETIC BUTTONS
        // ============================================

        initMagneticButtons: function() {
            if (window.innerWidth < 768) return;

            document.querySelectorAll('.btn-magnetic, .btn-primary').forEach(function(btn) {
                btn.addEventListener('mousemove', function(e) {
                    var rect = btn.getBoundingClientRect();
                    var x = e.clientX - rect.left - rect.width / 2;
                    var y = e.clientY - rect.top - rect.height / 2;

                    btn.style.transform = 'translate(' + (x * 0.2) + 'px, ' + (y * 0.2) + 'px)';
                });

                btn.addEventListener('mouseleave', function() {
                    btn.style.transform = 'translate(0, 0)';
                });
            });
        },

        // ============================================
        // TEXT SPLIT ANIMATION
        // ============================================

        initTextSplit: function() {
            document.querySelectorAll('.split-text').forEach(function(el) {
                var text = el.textContent;
                el.textContent = '';

                text.split('').forEach(function(char, i) {
                    var span = document.createElement('span');
                    span.textContent = char === ' ' ? '\u00A0' : char;
                    span.style.animationDelay = (i * 0.03) + 's';
                    el.appendChild(span);
                });
            });
        },

        // ============================================
        // SMOOTH REVEAL ON LOAD
        // ============================================

        initPageReveal: function() {
            document.body.classList.add('page-loaded');

            // Hero elements
            var heroTitle = document.querySelector('.hero-title, .page-title, .about-title');
            var heroSubtitle = document.querySelector('.hero-subtitle, .page-subtitle, .about-subtitle');
            var heroCta = document.querySelector('.hero-cta, .hero .btn');

            if (heroTitle) {
                heroTitle.style.opacity = '0';
                heroTitle.style.transform = 'translateY(30px)';
                setTimeout(function() {
                    heroTitle.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                    heroTitle.style.opacity = '1';
                    heroTitle.style.transform = 'translateY(0)';
                }, 200);
            }

            if (heroSubtitle) {
                heroSubtitle.style.opacity = '0';
                heroSubtitle.style.transform = 'translateY(20px)';
                setTimeout(function() {
                    heroSubtitle.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                    heroSubtitle.style.opacity = '1';
                    heroSubtitle.style.transform = 'translateY(0)';
                }, 400);
            }

            if (heroCta) {
                heroCta.style.opacity = '0';
                heroCta.style.transform = 'translateY(20px)';
                setTimeout(function() {
                    heroCta.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                    heroCta.style.opacity = '1';
                    heroCta.style.transform = 'translateY(0)';
                }, 600);
            }
        },

        // ============================================
        // IMAGE LAZY LOAD WITH BLUR
        // ============================================

        initLazyImages: function() {
            var images = document.querySelectorAll('img[data-src]');

            var imageObserver = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        var img = entry.target;
                        img.style.filter = 'blur(10px)';
                        img.style.transition = 'filter 0.5s ease';

                        img.onload = function() {
                            img.style.filter = 'blur(0)';
                        };

                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                });
            });

            images.forEach(function(img) {
                imageObserver.observe(img);
            });
        },

        // ============================================
        // SMOOTH SCROLL
        // ============================================

        initSmoothScroll: function() {
            document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
                anchor.addEventListener('click', function(e) {
                    var targetId = this.getAttribute('href');
                    if (targetId === '#') return;

                    var target = document.querySelector(targetId);
                    if (target) {
                        e.preventDefault();
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
        },

        // ============================================
        // NAVBAR SCROLL EFFECT
        // ============================================

        initNavbarScroll: function() {
            var navbar = document.querySelector('.navbar, .site-header');
            if (!navbar) return;

            var lastScroll = 0;

            window.addEventListener('scroll', function() {
                var currentScroll = window.scrollY;

                if (currentScroll > 100) {
                    navbar.classList.add('scrolled');
                } else {
                    navbar.classList.remove('scrolled');
                }

                if (currentScroll > lastScroll && currentScroll > 500) {
                    navbar.classList.add('nav-hidden');
                } else {
                    navbar.classList.remove('nav-hidden');
                }

                lastScroll = currentScroll;
            }, { passive: true });
        },

        // ============================================
        // TILT EFFECT ON CARDS
        // ============================================

        initTiltEffect: function() {
            if (window.innerWidth < 768) return;

            document.querySelectorAll('.product-card, .collection-card').forEach(function(card) {
                card.addEventListener('mousemove', function(e) {
                    var rect = card.getBoundingClientRect();
                    var x = e.clientX - rect.left;
                    var y = e.clientY - rect.top;

                    var centerX = rect.width / 2;
                    var centerY = rect.height / 2;

                    var rotateX = (y - centerY) / 20;
                    var rotateY = (centerX - x) / 20;

                    card.style.transform = 'perspective(1000px) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg) translateY(-8px)';
                });

                card.addEventListener('mouseleave', function() {
                    card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
                });
            });
        },

        // ============================================
        // COUNTER ANIMATION
        // ============================================

        initCounters: function() {
            var counters = document.querySelectorAll('[data-count]');

            var counterObserver = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        var counter = entry.target;
                        var target = parseInt(counter.dataset.count);
                        var duration = 2000;
                        var step = target / (duration / 16);
                        var current = 0;

                        var updateCounter = function() {
                            current += step;
                            if (current < target) {
                                counter.textContent = Math.floor(current);
                                requestAnimationFrame(updateCounter);
                            } else {
                                counter.textContent = target;
                            }
                        };

                        updateCounter();
                        counterObserver.unobserve(counter);
                    }
                });
            }, { threshold: 0.5 });

            counters.forEach(function(counter) {
                counterObserver.observe(counter);
            });
        },

        // ============================================
        // INIT ALL
        // ============================================

        init: function() {
            var self = this;

            document.addEventListener('DOMContentLoaded', function() {
                self.initPageReveal();
                self.initCursor();
                self.initScrollAnimations();
                self.initParallax();
                self.initMagneticButtons();
                self.initTextSplit();
                self.initLazyImages();
                self.initSmoothScroll();
                self.initNavbarScroll();
                self.initTiltEffect();
                self.initCounters();
            });
        }
    };

    window.SkyyRoseAesthetics.init();

})();
