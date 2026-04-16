/**
 * Brand Atmosphere — Canvas Particle System
 *
 * Part of the SkyyRose Experience Engine, Phase 2.
 *
 * Renders collection-aware ambient particles on a fixed full-screen canvas.
 * Each collection has a distinct particle profile:
 *
 *   black-rose   → silver/crimson embers drifting upward
 *   signature    → golden motes floating softly
 *   love-hurts   → crimson petals falling diagonally
 *   kids-capsule → pastel sparkles drifting upward
 *
 * Collection is detected from [data-collection] attribute on <body> or the
 * first element in the DOM that carries the attribute.
 *
 * Integrates with SkyyPerformance: pauses the RAF loop while throttled.
 * Respects `prefers-reduced-motion`: exits before touching the DOM.
 * Pauses automatically when the browser tab is hidden.
 *
 * @module brand-atmosphere
 * @since  6.4.0
 */
(function () {
  'use strict';

  // Bail immediately if the user prefers reduced motion.
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }

  // ---------------------------------------------------------------------------
  // Per-collection particle configurations
  // ---------------------------------------------------------------------------

  var CONFIGS = {
    'black-rose': {
      count: 40,
      colors: ['#C0C0C0', '#DC143C', '#B76E79', '#ffffff'],
      minSize: 1,
      maxSize: 3,
      minSpeed: 0.2,
      maxSpeed: 0.7,
      drift: 0.15,
      direction: -1, // upward
      shape: 'ember',
    },
    signature: {
      count: 35,
      colors: ['#D4AF37', '#F5DEB3', '#FFFACD', '#ffffff'],
      minSize: 1,
      maxSize: 2.5,
      minSpeed: 0.15,
      maxSpeed: 0.5,
      drift: 0.1,
      direction: -1,
      shape: 'circle',
    },
    'love-hurts': {
      count: 30,
      colors: ['#DC143C', '#B76E79', '#FF69B4', '#FFB6C1'],
      minSize: 2,
      maxSize: 4,
      minSpeed: 0.3,
      maxSpeed: 0.8,
      drift: 0.25,
      direction: 1, // downward like falling petals
      shape: 'petal',
    },
    'kids-capsule': {
      count: 50,
      colors: ['#B76E79', '#D4AF37', '#87CEEB', '#FFB6C1', '#98FB98'],
      minSize: 1.5,
      maxSize: 3,
      minSpeed: 0.3,
      maxSpeed: 0.9,
      drift: 0.2,
      direction: -1,
      shape: 'sparkle',
    },
  };

  // Fall back to signature motes on pages without a data-collection attribute.
  var FALLBACK_CONFIG = CONFIGS.signature;

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  function rand(min, max) {
    return min + Math.random() * (max - min);
  }

  function getCollection() {
    return (
      document.body.dataset.collection ||
      (document.querySelector('[data-collection]') || {}).dataset.collection ||
      null
    );
  }

  // ---------------------------------------------------------------------------
  // Particle class
  // ---------------------------------------------------------------------------

  function Particle(canvas, config) {
    this.canvas = canvas;
    this.config = config;
    this.reset(true);
  }

  Particle.prototype.reset = function (initial) {
    var c = this.config;
    this.x = rand(0, this.canvas.width);
    this.y = initial ? rand(0, this.canvas.height) : c.direction < 0 ? this.canvas.height + 5 : -5;
    this.size = rand(c.minSize, c.maxSize);
    this.speed = rand(c.minSpeed, c.maxSpeed);
    this.driftX = rand(-c.drift, c.drift);
    this.color = c.colors[Math.floor(Math.random() * c.colors.length)];
    this.alpha = rand(0.15, 0.6);
    this.rotation = rand(0, Math.PI * 2);
    this.rotationSpeed = rand(-0.02, 0.02);
    this.life = 0;
    this.maxLife = Math.floor(rand(120, 260));
  };

  Particle.prototype.update = function () {
    this.y += this.speed * this.config.direction;
    this.x += this.driftX;
    this.rotation += this.rotationSpeed;
    this.life++;

    var fadeFrames = 20;
    if (this.life < fadeFrames) {
      this.alpha = (this.life / fadeFrames) * 0.6;
    } else if (this.life > this.maxLife - fadeFrames) {
      this.alpha = Math.max(0, ((this.maxLife - this.life) / fadeFrames) * 0.6);
    }

    var offscreen =
      this.y < -10 ||
      this.y > this.canvas.height + 10 ||
      this.x < -10 ||
      this.x > this.canvas.width + 10;

    if (offscreen || this.life >= this.maxLife) {
      this.reset(false);
    }
  };

  Particle.prototype.draw = function (ctx) {
    ctx.save();
    ctx.globalAlpha = this.alpha;
    ctx.fillStyle = this.color;
    ctx.translate(this.x, this.y);
    ctx.rotate(this.rotation);

    switch (this.config.shape) {
      case 'ember':
        ctx.beginPath();
        ctx.ellipse(0, 0, this.size * 0.5, this.size, 0, 0, Math.PI * 2);
        ctx.fill();
        break;

      case 'petal':
        ctx.beginPath();
        ctx.ellipse(0, 0, this.size * 0.6, this.size * 1.4, 0, 0, Math.PI * 2);
        ctx.fill();
        break;

      case 'sparkle':
        for (var i = 0; i < 4; i++) {
          ctx.save();
          ctx.rotate((i * Math.PI) / 2);
          ctx.fillRect(-this.size * 0.15, -this.size, this.size * 0.3, this.size * 2);
          ctx.restore();
        }
        break;

      default: // circle
        ctx.beginPath();
        ctx.arc(0, 0, this.size, 0, Math.PI * 2);
        ctx.fill();
    }

    ctx.restore();
  };

  // ---------------------------------------------------------------------------
  // Main init
  // ---------------------------------------------------------------------------

  function init() {
    var collection = getCollection();
    var config = CONFIGS[collection] || FALLBACK_CONFIG;

    var canvas = document.createElement('canvas');
    canvas.className = 'skyy-atmosphere-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    document.body.appendChild(canvas);

    var ctx = canvas.getContext('2d');

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize, { passive: true });

    var particles = [];
    for (var i = 0; i < config.count; i++) {
      particles.push(new Particle(canvas, config));
    }

    var rafHandle = null;

    function tick() {
      // Yield the frame if SkyyPerformance is throttling.
      if (window.SkyyPerformance && window.SkyyPerformance.isThrottled()) {
        rafHandle = requestAnimationFrame(tick);
        return;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (var j = 0; j < particles.length; j++) {
        particles[j].update();
        particles[j].draw(ctx);
      }
      rafHandle = requestAnimationFrame(tick);
    }

    tick();

    // Pause the loop when the tab is hidden; resume cleanly on focus.
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) {
        cancelAnimationFrame(rafHandle);
      } else {
        rafHandle = requestAnimationFrame(tick);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
