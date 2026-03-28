/**
 * SkyyRose Brand Mascot — Skyy Living Character
 *
 * State machine: dormant → walking-in → greeting → idle ↔ speaking → exiting
 *
 * Features:
 * - Cinematic walk-on (3s page load delay)
 * - Contextual speech bubbles with typewriter text
 * - Choice chips drive conversation trees
 * - IntersectionObserver reacts to product grids entering view
 * - Product hover triggers excited reaction
 * - Session storage prevents repeat greetings
 * - Minimize (walk off) + recall pill
 * - Keyboard accessible (Escape to dismiss/minimize)
 * - Respects prefers-reduced-motion
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */
(function () {
	'use strict';

	// -------------------------------------------------------------------------
	// Constants
	// -------------------------------------------------------------------------

	var WALK_ON_DELAY_MS  = 3000;
	var TYPEWRITER_SPEED  = 28;
	var BUBBLE_AUTO_HIDE  = 8000;
	var IDLE_SPEAK_DELAY  = 45000;
	var SESSION_KEY       = 'skyy_greeted';

	// -------------------------------------------------------------------------
	// DOM References
	// -------------------------------------------------------------------------

	var mascotEl    = document.getElementById('skyyrose-mascot');
	if (!mascotEl) return;

	var triggerBtn  = document.getElementById('skyyrose-mascot-trigger');
	var minimizeBtn = document.getElementById('skyyrose-mascot-minimize');
	var recallBtn   = document.getElementById('skyyrose-mascot-recall');
	var bubble      = document.getElementById('skyy-bubble');
	var bubbleText  = document.getElementById('skyy-bubble-text');
	var chipsEl     = document.getElementById('skyy-chips');

	if (!triggerBtn || !minimizeBtn || !recallBtn || !bubble || !bubbleText || !chipsEl) return;

	var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	var context = mascotEl.getAttribute('data-context') || 'default';

	// State: dormant | walking-in | greeting | idle | speaking | exiting
	var state = 'dormant';

	var typewriterTimer  = null;
	var autoDismissTimer = null;
	var idleTimer        = null;

	// -------------------------------------------------------------------------
	// Conversation Scripts
	// -------------------------------------------------------------------------

	var SCRIPTS = {
		homepage: {
			greeting: {
				text: 'Hey! I\u2019m Skyy \uD83D\uDC4B Welcome to SkyyRose \u2014 Luxury Grows from Concrete.',
				chips: [
					{ id: 'new_drops', label: 'What\u2019s new?',    next: 'new_drops' },
					{ id: 'preorder',  label: 'Pre-order drops',     next: 'preorder'  },
					{ id: 'story',     label: 'Our story',           next: 'story'     }
				]
			},
			new_drops: {
				text: 'The Black Rose and Love Hurts collections are live. Limited runs \u2014 80 pieces each on the jerseys.',
				chips: [{ id: 'shop', label: 'Take me there \u2192', action: '/shop/', next: null }]
			},
			preorder: {
				text: 'Most of the collection is pre-order. That means YOU get it first, before anyone else. \uD83C\uDF39',
				chips: [{ id: 'preorder_page', label: 'See pre-orders', action: '/pre-order/', next: null }]
			},
			story: {
				text: 'SkyyRose was born in Oakland. Corey Foster built this from the concrete up. Real luxury, real roots.',
				chips: [{ id: 'about', label: 'Read our story', action: '/about/', next: null }]
			}
		},
		'black-rose': {
			greeting: {
				text: 'Oakland in your DNA? \uD83D\uDDA4 Black Rose was made for the ones who built something from nothing.',
				chips: [
					{ id: 'jerseys', label: 'Show me the jerseys',  next: 'jerseys'                            },
					{ id: 'br_shop', label: 'Browse collection',    action: '/collections/black-rose/', next: null }
				]
			},
			jerseys: {
				text: 'Limited to 80 pieces each \u2014 SF inspired, Last Oakland, The Bay, The Rose. Once they\u2019re gone, they\u2019re gone.',
				chips: [{ id: 'br_shop', label: 'Get yours now \u2192', action: '/collections/black-rose/', next: null }]
			}
		},
		'love-hurts': {
			greeting: {
				text: 'Love Hurts is for the ones who feel everything deeply. The Joggers, the Shorts, The Fannie \u2014 all pre-order. \u2764\uFE0F',
				chips: [
					{ id: 'lh_fannie', label: 'What\u2019s The Fannie?', next: 'fannie'                              },
					{ id: 'lh_browse', label: 'Browse collection',       action: '/collections/love-hurts/', next: null }
				]
			},
			fannie: {
				text: 'The Fannie is $45 pre-order. A statement piece. Small, bold, SkyyRose. Love Hurts edition. \uD83C\uDF39',
				chips: [{ id: 'lh_shop', label: 'Pre-order now \u2192', action: '/collections/love-hurts/', next: null }]
			}
		},
		signature: {
			greeting: {
				text: 'SF from the soul. \uD83C\uDF09 The Signature collection is Golden Gate, fog, and Bay Area energy.',
				chips: [
					{ id: 'sg_bridge', label: 'The Bay Bridge drops?', next: 'bridge'                               },
					{ id: 'sg_browse', label: 'Browse collection',      action: '/collections/signature/', next: null }
				]
			},
			bridge: {
				text: 'Bay Bridge Shorts + Shirt \u2014 both pre-order. This is the drop that defines the collection.',
				chips: [{ id: 'sg_shop', label: 'Pre-order \u2192', action: '/collections/signature/', next: null }]
			}
		},
		preorder: {
			greeting: {
				text: 'Pre-ordering means you\u2019re first in line. We make it for YOU. No overstock, no waste. Pure luxury.',
				chips: [{ id: 'po_browse', label: 'See all pre-orders', action: '/pre-order/', next: null }]
			}
		},
		'404': {
			greeting: {
				text: 'Oops \u2014 that page doesn\u2019t exist! Let me point you somewhere real. \uD83C\uDF39',
				chips: [
					{ id: '404_home', label: 'Take me home',      action: '/',      next: null },
					{ id: '404_shop', label: 'Shop collections',  action: '/shop/', next: null }
				]
			}
		},
		'default': {
			greeting: {
				text: 'Hey! I\u2019m Skyy \uD83D\uDC4B Need help finding something?',
				chips: [
					{ id: 'def_shop', label: 'Shop now',  action: '/shop/',     next: null },
					{ id: 'def_help', label: 'Get help',  action: '/contact/',  next: null }
				]
			}
		}
	};

	// -------------------------------------------------------------------------
	// Typewriter
	// -------------------------------------------------------------------------

	function typewrite(el, text, onDone) {
		clearInterval(typewriterTimer);
		el.textContent = '';
		if (prefersReducedMotion) {
			el.textContent = text;
			if (onDone) onDone();
			return;
		}
		var i = 0;
		typewriterTimer = setInterval(function () {
			el.textContent += text[i++];
			if (i >= text.length) {
				clearInterval(typewriterTimer);
				if (onDone) onDone();
			}
		}, TYPEWRITER_SPEED);
	}

	// -------------------------------------------------------------------------
	// Speech Bubble
	// -------------------------------------------------------------------------

	function speak(text, chips) {
		clearTimeout(autoDismissTimer);
		state = 'speaking';
		mascotEl.classList.add('skyy--speaking');
		triggerBtn.setAttribute('aria-expanded', 'true');

		// Clear previous chips
		chipsEl.innerHTML = '';

		// Show bubble
		bubble.removeAttribute('hidden');
		// Force reflow so transition fires
		void bubble.offsetWidth;
		bubble.classList.add('skyy-bubble--visible');

		// Typewrite, then render chips
		typewrite(bubbleText, text, function () {
			if (chips && chips.length) {
				chips.forEach(function (chip) {
					var btn = document.createElement('button');
					btn.type = 'button';
					btn.className = 'skyy-chip';
					btn.textContent = chip.label;
					btn.dataset.chipId = chip.id;
					btn.dataset.action = chip.action || '';
					btn.dataset.next   = chip.next   || '';
					chipsEl.appendChild(btn);
				});
			} else {
				// No chips — auto-dismiss after delay
				autoDismissTimer = setTimeout(dismissBubble, BUBBLE_AUTO_HIDE);
			}
		});
	}

	function dismissBubble() {
		clearTimeout(autoDismissTimer);
		clearInterval(typewriterTimer);
		bubble.classList.remove('skyy-bubble--visible');
		mascotEl.classList.remove('skyy--speaking');
		triggerBtn.setAttribute('aria-expanded', 'false');
		setTimeout(function () {
			if (!bubble.classList.contains('skyy-bubble--visible')) {
				bubble.setAttribute('hidden', '');
				bubbleText.textContent = '';
				chipsEl.innerHTML = '';
			}
			if (state === 'speaking') state = 'idle';
		}, 300);
	}

	// -------------------------------------------------------------------------
	// Chip Handling
	// -------------------------------------------------------------------------

	chipsEl.addEventListener('click', function (e) {
		var btn = e.target.closest('.skyy-chip');
		if (!btn) return;

		var action = btn.dataset.action;
		var next   = btn.dataset.next;

		if (action) {
			window.location.href = action;
			return;
		}

		if (next) {
			var script = SCRIPTS[context] || SCRIPTS['default'];
			var node   = script[next];
			if (node) {
				speak(node.text, node.chips || null);
			} else {
				dismissBubble();
			}
		}
	});

	// -------------------------------------------------------------------------
	// Walk-On / Walk-Off
	// -------------------------------------------------------------------------

	function walkOn() {
		if (state === 'walking-in' || state === 'idle' || state === 'speaking') return;
		state = 'walking-in';
		mascotEl.setAttribute('aria-hidden', 'false');
		mascotEl.classList.remove('skyyrose-mascot--hidden', 'skyyrose-mascot--exiting');
		mascotEl.classList.add('skyyrose-mascot--entering');

		var walkDuration = prefersReducedMotion ? 0 : 1400;
		setTimeout(function () {
			mascotEl.classList.remove('skyyrose-mascot--entering');
			mascotEl.classList.add('skyyrose-mascot--idle');
			state = 'idle';

			// Greet once per session
			if (!sessionStorage.getItem(SESSION_KEY)) {
				sessionStorage.setItem(SESSION_KEY, '1');
				var script = SCRIPTS[context] || SCRIPTS['default'];
				speak(script.greeting.text, script.greeting.chips);
			}

			// Schedule idle nudge
			scheduleIdleSpeak();
		}, walkDuration);
	}

	function walkOff(onDone) {
		state = 'exiting';
		dismissBubble();
		clearTimeout(idleTimer);
		mascotEl.classList.remove('skyyrose-mascot--idle', 'skyyrose-mascot--entering');
		mascotEl.classList.add('skyyrose-mascot--exiting');
		mascotEl.setAttribute('aria-hidden', 'true');

		var exitDuration = prefersReducedMotion ? 0 : 600;
		setTimeout(function () {
			mascotEl.classList.add('skyyrose-mascot--hidden');
			mascotEl.classList.remove('skyyrose-mascot--exiting');
			state = 'dormant';
			if (onDone) onDone();
		}, exitDuration);
	}

	// -------------------------------------------------------------------------
	// Idle Reactions
	// -------------------------------------------------------------------------

	function scheduleIdleSpeak() {
		clearTimeout(idleTimer);
		idleTimer = setTimeout(function () {
			if (state === 'idle') {
				speak('Still browsing? Take your time. \uD83C\uDF39', null);
			}
		}, IDLE_SPEAK_DELAY);
	}

	// React when product grid enters viewport
	if ('IntersectionObserver' in window) {
		var productObserved = false;
		var productObs = new IntersectionObserver(function (entries) {
			entries.forEach(function (entry) {
				if (entry.isIntersecting && state === 'idle' && !productObserved) {
					productObserved = true;
					mascotEl.classList.add('skyy--glancing');
					setTimeout(function () {
						mascotEl.classList.remove('skyy--glancing');
					}, 2000);
					speak('These just landed. \uD83D\uDC40', null);
				}
			});
		}, { threshold: 0.3 });

		document.querySelectorAll('.products, .wc-block-grid, .collection-hero').forEach(function (el) {
			productObs.observe(el);
		});
	}

	// React when hovering product cards
	document.addEventListener('mouseover', function (e) {
		if (state !== 'idle') return;
		if (e.target.closest('.product, .wc-block-grid__product')) {
			mascotEl.classList.add('skyy--excited');
			setTimeout(function () {
				mascotEl.classList.remove('skyy--excited');
			}, 1200);
		}
	});

	// -------------------------------------------------------------------------
	// Minimize / Recall
	// -------------------------------------------------------------------------

	function minimize() {
		walkOff(function () {
			recallBtn.style.display = 'flex';
			recallBtn.setAttribute('aria-hidden', 'false');
		});
	}

	function recall() {
		recallBtn.style.display = 'none';
		recallBtn.setAttribute('aria-hidden', 'true');
		walkOn();
	}

	// -------------------------------------------------------------------------
	// Event Listeners
	// -------------------------------------------------------------------------

	triggerBtn.addEventListener('click', function (e) {
		e.stopPropagation();
		if (state === 'speaking') {
			dismissBubble();
		} else if (state === 'idle') {
			var script = SCRIPTS[context] || SCRIPTS['default'];
			speak(script.greeting.text, script.greeting.chips);
		}
	});

	minimizeBtn.addEventListener('click', function (e) {
		e.stopPropagation();
		minimize();
	});

	recallBtn.addEventListener('click', function (e) {
		e.stopPropagation();
		recall();
	});

	// Close bubble on outside click
	document.addEventListener('click', function (e) {
		if (state === 'speaking' && !mascotEl.contains(e.target) && !recallBtn.contains(e.target)) {
			dismissBubble();
		}
	});

	// Keyboard accessibility
	document.addEventListener('keydown', function (e) {
		if (e.key === 'Escape') {
			if (state === 'speaking') {
				dismissBubble();
				triggerBtn.focus();
			} else if (state === 'idle') {
				minimize();
			}
		}
	});

	// -------------------------------------------------------------------------
	// Initialize
	// -------------------------------------------------------------------------

	setTimeout(walkOn, WALK_ON_DELAY_MS);
})();
