/**
 * Pre-Order Gateway Interactions
 *
 * IIFE — no global scope pollution except window.skyyRoseData (WP-injected).
 * Server-rendered product cards; no client catalog fetch.
 * No innerHTML — all DOM via createElement + textContent.
 *
 * @package SkyyRose
 * @since   7.1.0
 */
(function () {
  'use strict';

  /* ──────────────────────────────────────────────
     UTILITY
  ────────────────────────────────────────────── */
  var raf = window.requestAnimationFrame || function (fn) { setTimeout(fn, 16); };

  function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function saveDataOn() {
    var conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (conn) {
      if (conn.saveData) { return true; }
      if (conn.effectiveType === 'slow-2g' || conn.effectiveType === '2g') { return true; }
    }
    return false;
  }

  function byId(id) { return document.getElementById(id); }
  function qs(sel, ctx) { return (ctx || document).querySelector(sel); }
  function qsa(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

  function makeEl(tag, attrs, text) {
    var el = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === 'className') { el.className = attrs[k]; }
        else { el.setAttribute(k, attrs[k]); }
      });
    }
    if (text !== undefined) { el.textContent = text; }
    return el;
  }

  /* ──────────────────────────────────────────────
     VIDEO — remove if reduced-motion or save-data
  ────────────────────────────────────────────── */
  function initVideo() {
    var video = byId('po-hero-video');
    if (!video) { return; }

    if (prefersReducedMotion() || saveDataOn()) {
      var poster = byId('po-hero-poster');
      if (poster) { poster.style.display = 'block'; }
      video.parentNode.removeChild(video);
      return;
    }

    video.setAttribute('playsinline', '');
    video.setAttribute('muted', '');
    video.setAttribute('loop', '');
    video.setAttribute('autoplay', '');
    video.muted = true;
    video.play().catch(function () { /* autoplay blocked — poster already showing */ });
  }

  /* ──────────────────────────────────────────────
     HERO ENTRANCE SEQUENCE
  ────────────────────────────────────────────── */
  function initHeroSequence() {
    if (prefersReducedMotion()) {
      qsa('.po-hero__eyebrow, .po-hero__body').forEach(function (el) {
        el.classList.add('is-visible');
      });
      return;
    }

    var delays = [
      ['po-hero-eyebrow', 80],
      ['po-hero-lockup',  260],
      ['po-hero-body',    420],
      ['po-hero-cta',     580]
    ];

    delays.forEach(function (pair) {
      var el = byId(pair[0]);
      if (!el) { return; }
      setTimeout(function () { el.classList.add('is-visible'); }, pair[1]);
    });
  }

  /* ──────────────────────────────────────────────
     SCROLL CUE (fades out on scroll)
  ────────────────────────────────────────────── */
  function initScrollCue() {
    var cue = qs('.po-hero__scroll-hint');
    if (!cue) { return; }

    var ticking = false;
    function onScroll() {
      if (ticking) { return; }
      ticking = true;
      raf(function () {
        var opacity = Math.max(0, 1 - window.scrollY / 180);
        cue.style.opacity = String(opacity);
        ticking = false;
        if (opacity === 0) {
          window.removeEventListener('scroll', onScroll);
          cue.style.visibility = 'hidden';
        }
      });
    }

    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ──────────────────────────────────────────────
     PARALLAX — manifesto bg only
  ────────────────────────────────────────────── */
  function initParallax() {
    if (prefersReducedMotion()) { return; }

    var bg = qs('.po-manifesto__bg');
    if (!bg) { return; }

    var ticking = false;
    function onScroll() {
      if (ticking) { return; }
      ticking = true;
      raf(function () {
        var rect = bg.closest('.po-manifesto').getBoundingClientRect();
        var progress = -rect.top / window.innerHeight;
        bg.style.transform = 'translateY(' + (progress * 30).toFixed(2) + 'px)';
        ticking = false;
      });
    }

    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ──────────────────────────────────────────────
     MARQUEE — clone track for seamless loop
  ────────────────────────────────────────────── */
  function initMarquee() {
    var track = qs('.po-marquee__track');
    if (!track) { return; }
    if (prefersReducedMotion()) { return; }

    var clone = track.cloneNode(true);
    clone.setAttribute('aria-hidden', 'true');
    track.parentNode.appendChild(clone);
  }

  /* ──────────────────────────────────────────────
     GATEWAY — collection switching
     Shows/hides server-rendered .po-grid[data-collection]
     and sets data-collection on <body> for CSS palette morphing.
  ────────────────────────────────────────────── */
  function initGateway() {
    var panels = qsa('[data-gateway-panel]');
    if (!panels.length) {
      /* fallback: use .po-panel buttons */
      panels = qsa('.po-panel[data-collection]');
    }

    if (!panels.length) {
      /* last-resort fallback: grids exist but no panel buttons — activate first grid directly */
      var grids = qsa('.po-grid[data-collection]');
      if (grids.length) {
        var firstCol = grids[0].getAttribute('data-collection');
        if (firstCol) { document.body.setAttribute('data-collection', firstCol); }
        grids[0].classList.add('is-active');
      }
      return;
    }

    /* activate first collection on load */
    var first = panels[0];
    var firstCollection = first.getAttribute('data-collection') ||
                          first.getAttribute('data-gateway-panel');
    if (firstCollection) {
      switchCollection(firstCollection);
    }

    panels.forEach(function (panel) {
      panel.addEventListener('click', function () {
        var col = panel.getAttribute('data-collection') ||
                  panel.getAttribute('data-gateway-panel');
        if (col) { switchCollection(col); }
      });
    });

    /* tab buttons (.po-products__tabs buttons with data-collection) */
    var tabBtns = qsa('.po-products__tabs [data-collection]');
    tabBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var col = btn.getAttribute('data-collection');
        if (col) { switchCollection(col); }
      });
    });
  }

  function switchCollection(col) {
    /* palette morph */
    document.body.setAttribute('data-collection', col);

    /* show/hide server-rendered grids */
    var grids = qsa('.po-grid[data-collection]');
    grids.forEach(function (g) {
      if (g.getAttribute('data-collection') === col) {
        g.classList.add('is-active');
      } else {
        g.classList.remove('is-active');
      }
    });

    /* update panel pressed state */
    var panels = qsa('[data-gateway-panel], .po-panel[data-collection]');
    panels.forEach(function (p) {
      var pCol = p.getAttribute('data-collection') || p.getAttribute('data-gateway-panel');
      p.setAttribute('aria-pressed', pCol === col ? 'true' : 'false');
    });

    /* update tab active state */
    var tabBtns = qsa('.po-products__tabs [data-collection]');
    tabBtns.forEach(function (btn) {
      if (btn.getAttribute('data-collection') === col) {
        btn.classList.add('is-active');
        btn.setAttribute('aria-selected', 'true');
      } else {
        btn.classList.remove('is-active');
        btn.setAttribute('aria-selected', 'false');
      }
    });

    /* update capsule title if present */
    var title = byId('po-capsule-title');
    if (title) {
      var labels = {
        'black-rose': 'Black Rose',
        'love-hurts': 'Love Hurts',
        'signature':  'Signature'
      };
      title.textContent = labels[col] || col;
    }
  }

  /* ──────────────────────────────────────────────
     JOURNEY STEPS — IntersectionObserver
  ────────────────────────────────────────────── */
  function initJourneyObserver() {
    var steps = qsa('.po-journey__step');
    var header = qs('.po-journey__header');
    var items = header ? [header].concat(steps) : steps;
    if (!items.length) { return; }

    if (prefersReducedMotion()) {
      items.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

    items.forEach(function (el) { observer.observe(el); });
  }

  /* ──────────────────────────────────────────────
     LOOKBOOK — IntersectionObserver
  ────────────────────────────────────────────── */
  function initLookbookObserver() {
    var figs = qsa('.po-lookbook__figure');
    if (!figs.length) { return; }

    if (prefersReducedMotion()) {
      figs.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });

    figs.forEach(function (el, i) {
      el.style.transitionDelay = (i * 60) + 'ms';
      observer.observe(el);
    });
  }

  /* ──────────────────────────────────────────────
     GENERIC REVEAL — .po-rv
  ────────────────────────────────────────────── */
  function initRevealObserver() {
    var els = qsa('.po-rv, .po-gateway__header, .po-manifesto__content');
    if (!els.length) { return; }

    if (prefersReducedMotion()) {
      els.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

    els.forEach(function (el) { observer.observe(el); });
  }

  /* ──────────────────────────────────────────────
     STICKY CART BAR
     Shows after hero scrolls out of view.
     Reads WC cart fragment data if available.
  ────────────────────────────────────────────── */
  function initCartBar() {
    var bar = qs('.po-cart-bar');
    var hero = qs('.po-hero');
    if (!bar || !hero) { return; }

    var sentinel = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) {
          bar.classList.add('is-visible');
        } else {
          bar.classList.remove('is-visible');
        }
      });
    }, { threshold: 0 });

    sentinel.observe(hero);

    /* update count/total from WC cart cookie if available */
    updateCartBarData();

    /* listen for WC cart_fragment_refresh event */
    document.body.addEventListener('wc_fragments_refreshed', function () {
      updateCartBarData();
    });
    document.body.addEventListener('wc_cart_button_updated', function () {
      updateCartBarData();
    });
  }

  function updateCartBarData() {
    var countEl = qs('.po-cart-count');
    var totalEl = qs('.po-cart-total');

    /* Try to read cart count from WC fragment DOM (most reliable client-side source).
       woocommerce_items_in_cart cookie is a presence flag (0 or 1), not a count — do not use it. */
    var countFromFragment = null;
    var countNode = document.querySelector('.cart-contents-count, .woocommerce-cart-count');
    if (countNode) {
      var parsed = parseInt(countNode.textContent, 10);
      if (!isNaN(parsed)) { countFromFragment = parsed; }
    }

    if (countEl) {
      if (countFromFragment !== null) {
        countEl.textContent = String(countFromFragment);
        countEl.removeAttribute('hidden');
      } else {
        /* count unavailable — hide badge rather than show wrong number */
        countEl.setAttribute('hidden', '');
      }
    }

    /* cart total is harder to get client-side without an AJAX call;
       leave as rendered by PHP unless WC fires the fragment event with data */
  }

  /* ──────────────────────────────────────────────
     FAQ ACCORDION
  ────────────────────────────────────────────── */
  function initAccordions() {
    var btns = qsa('.po-accordion-btn');
    if (!btns.length) { return; }

    btns.forEach(function (btn) {
      var panelId = btn.getAttribute('aria-controls');
      var accordionEl = btn.closest('.po-accordion');
      var panel = panelId ? byId(panelId) : (accordionEl ? accordionEl.querySelector('.po-accordion-panel') : null);
      if (!panel) { return; }

      /* ensure proper initial aria state */
      var expanded = btn.getAttribute('aria-expanded') === 'true';
      panel.setAttribute('aria-hidden', expanded ? 'false' : 'true');
      if (!expanded) { panel.classList.remove('is-open'); }
      else           { panel.classList.add('is-open'); }

      btn.addEventListener('click', function () {
        var isOpen = btn.getAttribute('aria-expanded') === 'true';
        btn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
        panel.setAttribute('aria-hidden', isOpen ? 'true' : 'false');
        if (isOpen) { panel.classList.remove('is-open'); }
        else        { panel.classList.add('is-open'); }
      });
    });
  }

  /* ──────────────────────────────────────────────
     EMAIL CAPTURE — WP AJAX newsletter signup
  ────────────────────────────────────────────── */
  function initEmailCapture() {
    var form = byId('po-email-form');
    if (!form) { return; }

    var statusEl = byId('po-email-status') || qs('.po-email-status', form.parentNode);
    var ajaxUrl = (window.skyyRoseData && window.skyyRoseData.ajaxUrl) ||
                  (window.ajaxurl) || '/wp-admin/admin-ajax.php';

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var inputEl = form.querySelector('.po-email-input, .po-email-form__input, [type="email"]');
      if (!inputEl) { return; }
      var email = inputEl.value.trim();
      if (!email) { return; }

      var submitBtn = form.querySelector('[type="submit"]');
      if (submitBtn) { submitBtn.disabled = true; }

      var data = new FormData();
      data.append('action', 'skyyrose_newsletter_signup');
      data.append('email', email);
      var nonce = form.querySelector('[name="nonce"]') || byId('po-email-nonce');
      if (nonce) { data.append('nonce', nonce.value || nonce.getAttribute('data-nonce') || ''); }

      fetch(ajaxUrl, { method: 'POST', body: data, credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          if (statusEl) {
            statusEl.textContent = res.data && res.data.message
              ? res.data.message
              : (res.success ? 'You\'re in.' : 'Something went wrong — try again.');
          }
          if (res.success) { form.reset(); }
        })
        .catch(function () {
          if (statusEl) { statusEl.textContent = 'Network error — please try again.'; }
        })
        .finally(function () {
          if (submitBtn) { submitBtn.disabled = false; }
        });
    });
  }

  /* ──────────────────────────────────────────────
     MAGNETIC CTA
     rAF-throttled mousemove on .po-btn[data-magnetic]
  ────────────────────────────────────────────── */
  /* ── Hero video boot ─────────────────────────────────────────────
   The hero <video> ships without autoplay and with preload="none" so
   its 3.5MB webm never contends with the LCP poster paint. Playback
   starts at window load, or immediately on first interaction —
   whichever comes first. The poster <picture> behind it shows the
   identical frame until then. */
function initHeroVideo() {
  var video = document.querySelector('.po-hero__video');
  if (!video) return;
  var boot = function () {
    if (video.dataset.booted) return;
    video.dataset.booted = '1';
    video.preload = 'auto';
    var attempt = video.play();
    if (attempt && attempt.catch) {
      attempt.catch(function () {
        // Autoplay refused (battery saver etc.): retry on first gesture.
        document.addEventListener('pointerdown', function () {
          video.play().catch(function () {});
        }, { once: true });
      });
    }
  };
  /* Wave 9: round-8 traces show the 3.3MB webm fetch starting AT window
     load and still overlapping the LCP window (r2 poster load time 2.5s).
     Push the auto-boot to load + 2.5s so the stream reliably clears the
     LCP paint; the identical-frame poster holds until then and any
     gesture still boots instantly. */
  var bootAfterLoad = function () {
    window.setTimeout(boot, 2500);
  };
  if (document.readyState === 'complete') {
    bootAfterLoad();
  } else {
    window.addEventListener('load', bootAfterLoad, { once: true });
  }
  ['pointerdown', 'touchstart', 'wheel', 'keydown'].forEach(function (evt) {
    window.addEventListener(evt, boot, { once: true, passive: true });
  });
}

function initMagneticCTA() {
    if (prefersReducedMotion()) { return; }

    var magnets = qsa('.po-btn[data-magnetic], .po-btn--reserve[data-magnetic]');
    if (!magnets.length) { return; }

    magnets.forEach(function (btn) {
      var rect;
      var pending = false;
      var mx = 0, my = 0;

      btn.addEventListener('mouseenter', function () {
        rect = btn.getBoundingClientRect();
      });

      btn.addEventListener('mousemove', function (e) {
        mx = e.clientX;
        my = e.clientY;
        if (!pending) {
          pending = true;
          raf(function () {
            pending = false;
            if (!rect) { return; }
            var cx = rect.left + rect.width / 2;
            var cy = rect.top  + rect.height / 2;
            var dx = (mx - cx) * 0.28;
            var dy = (my - cy) * 0.28;
            btn.style.transform = 'translate(' + dx.toFixed(2) + 'px,' + dy.toFixed(2) + 'px)';
          });
        }
      });

      btn.addEventListener('mouseleave', function () {
        rect = null;
        btn.style.transform = '';
      });
    });
  }

  /* ──────────────────────────────────────────────
     INIT
  ────────────────────────────────────────────── */
  function init() {
    initVideo();
    initHeroSequence();
    initScrollCue();
    initParallax();
    initMarquee();
    initGateway();
    initJourneyObserver();
    initLookbookObserver();
    initRevealObserver();
    initCartBar();
    initAccordions();
    initEmailCapture();
    initMagneticCTA();
    initHeroVideo();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

}());
