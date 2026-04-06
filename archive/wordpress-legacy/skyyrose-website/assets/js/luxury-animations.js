/**
 * SkyyRose Luxury Animations — Shared GSAP utilities
 * @package SkyyRose
 * @since   4.1.0
 */

(function () {
    'use strict';

    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

    gsap.registerPlugin(ScrollTrigger);

    /* Scroll-reveal: fade-up elements with .reveal class */
    gsap.utils.toArray('.reveal').forEach(function (el) {
        gsap.from(el, {
            y: 40,
            opacity: 0,
            duration: 0.8,
            ease: 'power2.out',
            scrollTrigger: {
                trigger: el,
                start: 'top 85%',
                once: true
            }
        });
    });

    /* Parallax: elements with .parallax-slow */
    gsap.utils.toArray('.parallax-slow').forEach(function (el) {
        gsap.to(el, {
            y: -50,
            ease: 'none',
            scrollTrigger: {
                trigger: el,
                start: 'top bottom',
                end: 'bottom top',
                scrub: 1
            }
        });
    });

    /* Stagger entrance: .stagger-group > children */
    gsap.utils.toArray('.stagger-group').forEach(function (group) {
        gsap.from(group.children, {
            y: 30,
            opacity: 0,
            duration: 0.6,
            stagger: 0.1,
            ease: 'power2.out',
            scrollTrigger: {
                trigger: group,
                start: 'top 80%',
                once: true
            }
        });
    });

})();
