/**
 * Brand Atmosphere — Particles, Cursor Glow, Cinematic Mode
 *
 * Creates emotional brand connection through ambient effects:
 *   1. Collection-specific particles (rose petals, embers, gold dust)
 *   2. Custom cursor glow that picks up collection accent color
 *   3. Cinematic mode: dims UI chrome, enlarges products, vignette overlay
 *
 * Canvas-based. Auto-pauses on hidden tabs. Stops if Performance Guardian
 * signals budget exceeded. 10-15 particles max, 0.3 opacity.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

(function () {
	'use strict';

	var SEE = window.SkyyRoseExperience;
	if (!SEE || SEE.prefersReducedMotion) {
		return;
	}

	/* ==========================================================================
	   Configuration
	   ========================================================================== */

	var CONFIG = {
		maxParticles:   12,
		particleOpacity: 0.3,
		particleSpeed:  0.3,
		cursorGlowSize: 120,
		cursorGlowOpacity: 0.08,
	};

	var ctx = SEE.getContext();

	// Collection-specific particle settings.
	var PARTICLES = {
		'black-rose':   { char: '\u2740', color: '#C0C0C0', size: [8, 14], drift: 'fall' },    // ❀ silver petals falling
		'love-hurts':   { char: '\u2726', color: '#DC143C', size: [4, 8], drift: 'rise' },      // ✦ crimson embers rising
		'signature':    { char: '\u2726', color: '#D4AF37', size: [3, 6], drift: 'float' },     // ✦ gold dust floating
		'kids-capsule': { char: '\u2605', color: '#FFB6C1', size: [6, 10], drift: 'float' },    // ★ pink stars
		'default':      { char: '\u2726', color: '#B76E79', size: [3, 6], drift: 'float' },     // ✦ rose gold dust
	};

	var canvas = null;
	var canvasCtx = null;
	var particles = [];
	var rafId = null;
	var mouseX = -1000;
	var mouseY = -1000;
	var cinematicActive = false;

	/* ==========================================================================
	   Particle System
	   ========================================================================== */

	function Particle(config) {
		this.char = config.char;
		this.color = config.color;
		this.size = config.size[0] + Math.random() * (config.size[1] - config.size[0]);
		this.x = Math.random() * (canvas ? canvas.width : window.innerWidth);
		this.y = config.drift === 'rise'
			? (canvas ? canvas.height : window.innerHeight) + 20
			: -20;
		this.opacity = CONFIG.particleOpacity * (0.5 + Math.random() * 0.5);
		this.drift = config.drift;
		this.vx = (Math.random() - 0.5) * 0.5;
		this.vy = config.drift === 'rise' ? -(0.2 + Math.random() * CONFIG.particleSpeed) : (0.2 + Math.random() * CONFIG.particleSpeed);
		this.rotation = Math.random() * Math.PI * 2;
		this.rotationSpeed = (Math.random() - 0.5) * 0.02;
		this.life = 0;
		this.maxLife = 300 + Math.random() * 200;
	}

	Particle.prototype.update = function () {
		this.x += this.vx;
		this.y += this.vy;
		this.rotation += this.rotationSpeed;
		this.life++;

		// Float drift: gentle sine wave.
		if (this.drift === 'float') {
			this.x += Math.sin(this.life * 0.02) * 0.3;
		}

		// Fade out near end of life.
		if (this.life > this.maxLife * 0.7) {
			this.opacity *= 0.98;
		}

		return this.life < this.maxLife && this.opacity > 0.01;
	};

	Particle.prototype.draw = function (ctx) {
		ctx.save();
		ctx.translate(this.x, this.y);
		ctx.rotate(this.rotation);
		ctx.globalAlpha = this.opacity;
		ctx.font = this.size + 'px serif';
		ctx.fillStyle = this.color;
		ctx.textAlign = 'center';
		ctx.textBaseline = 'middle';
		ctx.fillText(this.char, 0, 0);
		ctx.restore();
	};

	/* ==========================================================================
	   Canvas Rendering Loop
	   ========================================================================== */

	function getParticleConfig() {
		return PARTICLES[ctx.collection] || PARTICLES['default'];
	}

	function animate() {
		if (!canvas || !canvasCtx) {
			return;
		}

		canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

		// Spawn particles if under limit.
		if (particles.length < CONFIG.maxParticles && Math.random() < 0.05) {
			particles.push(new Particle(getParticleConfig()));
		}

		// Update and draw particles.
		particles = particles.filter(function (p) {
			var alive = p.update();
			if (alive) {
				p.draw(canvasCtx);
			}
			return alive;
		});

		// Cursor glow.
		if (mouseX > 0 && mouseY > 0) {
			var pConfig = getParticleConfig();
			var gradient = canvasCtx.createRadialGradient(
				mouseX, mouseY, 0,
				mouseX, mouseY, CONFIG.cursorGlowSize
			);
			gradient.addColorStop(0, hexToRgba(pConfig.color, CONFIG.cursorGlowOpacity));
			gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
			canvasCtx.fillStyle = gradient;
			canvasCtx.fillRect(
				mouseX - CONFIG.cursorGlowSize,
				mouseY - CONFIG.cursorGlowSize,
				CONFIG.cursorGlowSize * 2,
				CONFIG.cursorGlowSize * 2
			);
		}

		rafId = requestAnimationFrame(animate);
	}

	function resizeCanvas() {
		if (canvas) {
			canvas.width = window.innerWidth;
			canvas.height = window.innerHeight;
		}
	}

	/* ==========================================================================
	   Cinematic Mode
	   ========================================================================== */

	function toggleCinematic() {
		cinematicActive = !cinematicActive;
		document.body.classList.toggle('see-cinematic', cinematicActive);

		var toggle = document.getElementById('see-cinematic-toggle');
		if (toggle) {
			toggle.classList.toggle('see-cinematic-active', cinematicActive);
		}

		SEE.emit('atmosphere:cinematic', { active: cinematicActive });
	}

	/* ==========================================================================
	   Helpers
	   ========================================================================== */

	function hexToRgba(hex, alpha) {
		var r = parseInt(hex.slice(1, 3), 16);
		var g = parseInt(hex.slice(3, 5), 16);
		var b = parseInt(hex.slice(5, 7), 16);
		return 'rgba(' + r + ', ' + g + ', ' + b + ', ' + alpha + ')';
	}

	/* ==========================================================================
	   Module Registration
	   ========================================================================== */

	SEE.registerModule('brand-atmosphere', {
		init: function (moduleConfig) {
			Object.assign(CONFIG, moduleConfig);
		},

		ready: function () {
			canvas = document.getElementById('see-atmosphere-canvas');
			if (!canvas) {
				return;
			}

			canvasCtx = canvas.getContext('2d');
			resizeCanvas();

			// Register with Performance Guardian.
			var guardianAllowed = true;
			if (SEE.performance) {
				guardianAllowed = SEE.performance.requestAnimation(
					'brand-atmosphere',
					2, // Low priority — first to be paused.
					function () {
						if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
					},
					function () {
						rafId = requestAnimationFrame(animate);
					}
				);
			}

			if (guardianAllowed) {
				rafId = requestAnimationFrame(animate);
			}

			// Mouse tracking for cursor glow.
			document.addEventListener('mousemove', function (e) {
				mouseX = e.clientX;
				mouseY = e.clientY;
			}, { passive: true });

			// Window resize.
			window.addEventListener('resize', resizeCanvas, { passive: true });

			// Cinematic mode toggle.
			var toggle = document.getElementById('see-cinematic-toggle');
			if (toggle) {
				toggle.addEventListener('click', toggleCinematic);
			}

			// Listen for Performance Guardian budget warnings.
			SEE.on('performance:throttled', function (data) {
				if (data.id === 'brand-atmosphere') {
					particles = []; // Clear particles immediately.
				}
			});
		},

		destroy: function () {
			if (rafId) {
				cancelAnimationFrame(rafId);
			}
			particles = [];
			if (SEE.performance) {
				SEE.performance.releaseAnimation('brand-atmosphere');
			}
		},
	});

})();
