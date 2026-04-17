/**
 * Landing Pages — Vanilla JS
 *
 * Countdown timer, parallax, FAQ accordion, scroll reveal.
 * Zero GSAP dependency — same pattern as collection-pages.js.
 *
 * @package SkyyRose
 * @since   6.5.0
 */

(function () {
  'use strict';

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ──────────────────────────────────────────────────────────────────
     1. Countdown Timer — requestAnimationFrame
     ────────────────────────────────────────────────────────────────── */
  function initCountdown() {
    var el = document.querySelector('[data-countdown]');
    if (!el) return;

    var endAttr = el.getAttribute('data-countdown');
    var end;

    if (endAttr && endAttr.indexOf('h') > -1) {
      // Relative: "72h" means 72 hours from now
      var hours = parseInt(endAttr, 10) || 72;
      end = Date.now() + hours * 3600000;
    } else if (endAttr) {
      end = new Date(endAttr).getTime();
    } else {
      end = Date.now() + 72 * 3600000;
    }

    var days = el.querySelector('[data-cd="d"]');
    var hrs = el.querySelector('[data-cd="h"]');
    var mins = el.querySelector('[data-cd="m"]');
    var secs = el.querySelector('[data-cd="s"]');

    if (!days || !hrs || !mins || !secs) return;

    var lastUpdate = 0;

    function tick(now) {
      // Update once per second to avoid layout thrashing
      if (now - lastUpdate < 1000) {
        requestAnimationFrame(tick);
        return;
      }
      lastUpdate = now;

      var diff = Math.max(0, end - Date.now());
      var d = Math.floor(diff / 86400000);
      var h = Math.floor((diff % 86400000) / 3600000);
      var m = Math.floor((diff % 3600000) / 60000);
      var s = Math.floor((diff % 60000) / 1000);

      days.textContent = String(d).padStart(2, '0');
      hrs.textContent = String(h).padStart(2, '0');
      mins.textContent = String(m).padStart(2, '0');
      secs.textContent = String(s).padStart(2, '0');

      if (diff > 0) {
        requestAnimationFrame(tick);
      }
    }

    requestAnimationFrame(tick);
  }

  /* ──────────────────────────────────────────────────────────────────
     2. Parallax Scroll
     ────────────────────────────────────────────────────────────────── */
  function initParallax() {
    if (reducedMotion) return;

    var items = document.querySelectorAll('.lp-parallax img');
    if (!items.length) return;

    var ticking = false;

    function onScroll() {
      if (ticking) return;
      ticking = true;

      requestAnimationFrame(function () {
        var scrollY = window.pageYOffset;

        for (var i = 0; i < items.length; i++) {
          var img = items[i];
          var parent = img.closest('.lp-parallax');
          if (!parent) continue;

          var rect = parent.getBoundingClientRect();
          var inView = rect.bottom > 0 && rect.top < window.innerHeight;

          if (inView) {
            var center = rect.top + rect.height / 2;
            var offset = (center - window.innerHeight / 2) * 0.15;
            img.style.transform = 'translateY(' + offset + 'px)';
          }
        }

        ticking = false;
      });
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ──────────────────────────────────────────────────────────────────
     3. FAQ Accordion
     ────────────────────────────────────────────────────────────────── */
  function initFAQ() {
    var questions = document.querySelectorAll('.lp-faq__question');
    if (!questions.length) return;

    for (var i = 0; i < questions.length; i++) {
      questions[i].addEventListener('click', function () {
        var item = this.closest('.lp-faq__item');
        var answer = item.querySelector('.lp-faq__answer');
        var isOpen = item.classList.contains('open');

        // Close all others
        var allItems = document.querySelectorAll('.lp-faq__item.open');
        for (var j = 0; j < allItems.length; j++) {
          if (allItems[j] !== item) {
            allItems[j].classList.remove('open');
            var otherAnswer = allItems[j].querySelector('.lp-faq__answer');
            if (otherAnswer) otherAnswer.style.maxHeight = '0';
          }
        }

        // Toggle current
        if (isOpen) {
          item.classList.remove('open');
          answer.style.maxHeight = '0';
        } else {
          item.classList.add('open');
          answer.style.maxHeight = answer.scrollHeight + 'px';
        }
      });
    }
  }

  /* ──────────────────────────────────────────────────────────────────
     4. Scroll Reveal — IntersectionObserver on .lp-rv
     ────────────────────────────────────────────────────────────────── */
  function initScrollReveal() {
    if (reducedMotion) {
      // Force all visible immediately
      var all = document.querySelectorAll('.lp-rv');
      for (var i = 0; i < all.length; i++) {
        all[i].classList.add('is-visible');
      }
      return;
    }

    if (!('IntersectionObserver' in window)) {
      var fallback = document.querySelectorAll('.lp-rv');
      for (var k = 0; k < fallback.length; k++) {
        fallback[k].classList.add('is-visible');
      }
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        for (var j = 0; j < entries.length; j++) {
          if (entries[j].isIntersecting) {
            entries[j].target.classList.add('is-visible');
            observer.unobserve(entries[j].target);
          }
        }
      },
      { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
    );

    var elements = document.querySelectorAll('.lp-rv');
    for (var m = 0; m < elements.length; m++) {
      observer.observe(elements[m]);
    }
  }

  /* ──────────────────────────────────────────────────────────────────
     5. Smooth Scroll for Anchor Links
     ────────────────────────────────────────────────────────────────── */
  function initSmoothScroll() {
    var anchors = document.querySelectorAll('.lp a[href^="#"]');
    for (var i = 0; i < anchors.length; i++) {
      anchors[i].addEventListener('click', function (e) {
        var href = this.getAttribute('href');
        if (!href || href === '#') return;
        var target = document.querySelector(href);
        if (!target) return;
        e.preventDefault();
        target.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'start' });
      });
    }
  }

  /* ──────────────────────────────────────────────────────────────────
     Boot
     ────────────────────────────────────────────────────────────────── */
  function init() {
    initCountdown();
    initParallax();
    initFAQ();
    initScrollReveal();
    initSmoothScroll();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
