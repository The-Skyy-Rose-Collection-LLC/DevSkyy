/**
 * Brand Ambassador — Skyy Rose Chatbot Engine
 *
 * Guided conversational tree with keyword fallback for free-text input.
 * No external API required — all responses are pre-scripted with
 * personality-rich copy that reflects the SkyyRose brand voice.
 *
 * @package SkyyRose_Flagship
 * @since   3.10.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   DOM References
	   -------------------------------------------------- */

	var widget     = document.getElementById('sr-ambassador');
	var fab        = document.getElementById('sr-ambassador-fab');
	var panel      = document.getElementById('sr-ambassador-panel');
	var closeBtn   = document.getElementById('sr-ambassador-close');
	var messagesEl = document.getElementById('sr-ambassador-messages');
	var repliesEl  = document.getElementById('sr-ambassador-replies');
	var form       = document.getElementById('sr-ambassador-form');
	var input      = document.getElementById('sr-ambassador-input');
	var greeting   = document.getElementById('sr-ambassador-greeting');
	var greetClose = greeting ? greeting.querySelector('.sr-ambassador__greeting-close') : null;

	if (!widget || !fab || !panel) return;

	var isOpen = false;
	var hasOpened = false;

	/* --------------------------------------------------
	   Conversation Tree
	   -------------------------------------------------- */

	var CONVO = {
		welcome: {
			messages: [
				"Hey there! I'm Skyy Rose, your personal style guide at SKyyRose.",
				"I know everything about our collections, sizing, and how to get your hands on the freshest pieces. What can I help you with?"
			],
			replies: [
				{ label: 'About SKyyRose',      goto: 'about' },
				{ label: 'Collections',          goto: 'collections' },
				{ label: 'Sizing Help',          goto: 'sizing' },
				{ label: 'Pre-Order Info',       goto: 'preorder' },
				{ label: 'Take the Style Quiz',  goto: 'quiz' }
			]
		},

		about: {
			messages: [
				"SKyyRose is a luxury streetwear brand born in Oakland, California. Our tagline? <strong>Luxury Grows from Concrete.</strong>",
				"Every piece we make blends premium quality with intentional design. We've got three distinct collections \u2014 each with its own mood, story, and energy.",
				"Want to explore the collections, or can I help with something else?"
			],
			replies: [
				{ label: 'Show Collections',  goto: 'collections' },
				{ label: 'Sizing Help',       goto: 'sizing' },
				{ label: 'Back to Start',     goto: 'welcome' }
			]
		},

		collections: {
			messages: [
				"We have three main collections, each with a unique vibe:",
				"<strong>Signature</strong> \u2014 Rose gold warmth meets Bay Area cool. Tees, shorts, hoodies \u2014 the foundation of your wardrobe.",
				"<strong>Black Rose</strong> \u2014 Gothic garden energy. Dark, bold, mysterious. Sherpa jackets, hoodies, and statement pieces.",
				"<strong>Love Hurts</strong> \u2014 Passion forged in fire. Crimson reds on midnight black. For those who wear their heart on their sleeve.",
				"Which one speaks to you?"
			],
			replies: [
				{ label: 'Signature',    goto: 'signature' },
				{ label: 'Black Rose',   goto: 'blackrose' },
				{ label: 'Love Hurts',   goto: 'lovehurts' },
				{ label: 'Help Me Choose', goto: 'quiz' }
			]
		},

		signature: {
			messages: [
				"The <strong>Signature Collection</strong> is where it all began. Rose gold warmth, Bay Area energy, effortless style.",
				"Think pastel colorblock sets, essential tees, premium shorts, and cozy hoodies. Prices range from $25 to $80.",
				"Every piece is designed to be a wardrobe staple \u2014 timeless by design, luxurious by nature.",
				'<a href="/collection-signature/">Browse the Signature Collection \u2192</a>'
			],
			replies: [
				{ label: 'Other Collections', goto: 'collections' },
				{ label: 'Size Guide',         goto: 'sizing' },
				{ label: 'Pre-Order Now',      goto: 'preorder' }
			]
		},

		blackrose: {
			messages: [
				"The <strong>Black Rose Collection</strong> is born from moonlit gardens and shadowed cathedrals. Pure dark luxury.",
				"Sherpa jackets, graphic hoodies, statement tees \u2014 all in noir with metallic silver accents. Prices range from $30 to $95.",
				"This is armor for the bold, the defiant, the eternally romantic.",
				'<a href="/collection-black-rose/">Explore the Black Rose Collection \u2192</a>'
			],
			replies: [
				{ label: 'Other Collections', goto: 'collections' },
				{ label: 'Size Guide',         goto: 'sizing' },
				{ label: 'Pre-Order Now',      goto: 'preorder' }
			]
		},

		lovehurts: {
			messages: [
				"The <strong>Love Hurts Collection</strong> is passion forged in fire. Crimson reds bleed into midnight blacks.",
				"This collection isn't for the faint of heart. It's for those who turn vulnerability into power and wear their scars as badges of honor.",
				'<a href="/collection-love-hurts/">Experience the Love Hurts Collection \u2192</a>'
			],
			replies: [
				{ label: 'Other Collections', goto: 'collections' },
				{ label: 'Size Guide',         goto: 'sizing' },
				{ label: 'Pre-Order Now',      goto: 'preorder' }
			]
		},

		sizing: {
			messages: [
				"Great question! Here's the quick rundown:",
				"<strong>Signature</strong> \u2014 True to size. Classic streetwear fit. Order your usual.",
				"<strong>Black Rose</strong> \u2014 Runs slightly oversized. Size down for fitted, or stay true for that Gothic drape.",
				"<strong>Love Hurts</strong> \u2014 Slim fashion fit. Size up for a more relaxed feel.",
				"We carry XS through XXL across all collections. Want the full size chart? Click the Size Guide button on any collection page!"
			],
			replies: [
				{ label: 'Collections',   goto: 'collections' },
				{ label: 'Pre-Order',     goto: 'preorder' },
				{ label: 'Back to Start', goto: 'welcome' }
			]
		},

		preorder: {
			messages: [
				"Pre-ordering is how you lock in the freshest pieces before they drop!",
				"Here's how it works: Browse our collections, pick your favorites, choose your size, and place your pre-order. You'll be first in line when we ship.",
				"Pre-order prices are special \u2014 once the collection officially drops, prices go up. So you're getting the best deal by ordering now.",
				'<a href="/pre-order/">Go to the Pre-Order Gateway \u2192</a>'
			],
			replies: [
				{ label: 'Collections',   goto: 'collections' },
				{ label: 'Sizing Help',   goto: 'sizing' },
				{ label: 'Back to Start', goto: 'welcome' }
			]
		},

		quiz: {
			messages: [
				"Can't decide which collection is for you? No worries \u2014 take our Style DNA Quiz!",
				"7 quick questions, and I'll tell you exactly which SkyyRose collections match your personality. You'll even get a shareable Style DNA card!",
				'<a href="/style-quiz/">Take the Style DNA Quiz \u2192</a>'
			],
			replies: [
				{ label: 'Collections',   goto: 'collections' },
				{ label: 'About Us',      goto: 'about' },
				{ label: 'Back to Start', goto: 'welcome' }
			]
		},

		fallback: {
			messages: [
				"Hmm, I'm not sure about that one! But here's what I can help with:"
			],
			replies: [
				{ label: 'About SKyyRose',  goto: 'about' },
				{ label: 'Collections',      goto: 'collections' },
				{ label: 'Sizing Help',      goto: 'sizing' },
				{ label: 'Pre-Order Info',   goto: 'preorder' },
				{ label: 'Style Quiz',       goto: 'quiz' }
			]
		}
	};

	/* --------------------------------------------------
	   Keyword → Topic Mapping (for free-text input)
	   -------------------------------------------------- */

	var KEYWORDS = [
		{ patterns: ['size', 'sizing', 'fit', 'measurement', 'chart', 'xs', 'small', 'medium', 'large', 'xl', 'xxl'], goto: 'sizing' },
		{ patterns: ['signature', 'bay area', 'rose gold', 'pastel'], goto: 'signature' },
		{ patterns: ['black rose', 'gothic', 'dark', 'sherpa', 'noir'], goto: 'blackrose' },
		{ patterns: ['love hurts', 'crimson', 'passion', 'red'], goto: 'lovehurts' },
		{ patterns: ['collection', 'browse', 'shop', 'look'], goto: 'collections' },
		{ patterns: ['pre-order', 'preorder', 'pre order', 'buy', 'purchase', 'order', 'price', 'cost', 'how much'], goto: 'preorder' },
		{ patterns: ['quiz', 'style dna', 'recommend', 'which', 'help me choose', 'suggest'], goto: 'quiz' },
		{ patterns: ['about', 'brand', 'story', 'who', 'what is', 'tell me'], goto: 'about' },
		{ patterns: ['hello', 'hi', 'hey', 'sup', 'yo', 'what up'], goto: 'welcome' }
	];

	/* --------------------------------------------------
	   Open / Close Panel
	   -------------------------------------------------- */

	function openPanel() {
		isOpen = true;
		widget.classList.add('open');
		fab.setAttribute('aria-expanded', 'true');
		panel.removeAttribute('hidden');
		panel.setAttribute('aria-hidden', 'false');

		if (!hasOpened) {
			hasOpened = true;
			playConvo('welcome');
		}

		setTimeout(function () {
			if (input) input.focus();
		}, 100);

		panel.addEventListener('keydown', handlePanelKeydown);
	}

	function closePanel() {
		isOpen = false;
		widget.classList.remove('open');
		fab.setAttribute('aria-expanded', 'false');
		panel.setAttribute('aria-hidden', 'true');
		panel.setAttribute('hidden', '');
		panel.removeEventListener('keydown', handlePanelKeydown);
		fab.focus();
	}

	function handlePanelKeydown(e) {
		if (e.key === 'Escape') {
			closePanel();
		}
	}

	fab.addEventListener('click', function () {
		if (isOpen) closePanel();
		else openPanel();
	});

	if (closeBtn) {
		closeBtn.addEventListener('click', closePanel);
	}

	/* --------------------------------------------------
	   Greeting Bubble
	   -------------------------------------------------- */

	var greetingDismissed = false;

	function showGreeting() {
		if (greetingDismissed || isOpen || !greeting) return;
		greeting.classList.add('visible');
	}

	function hideGreeting() {
		if (greeting) greeting.classList.remove('visible');
		greetingDismissed = true;
	}

	// Show greeting after 5s on page.
	setTimeout(showGreeting, 5000);

	if (greetClose) {
		greetClose.addEventListener('click', function (e) {
			e.stopPropagation();
			hideGreeting();
		});
	}

	// Opening the panel dismisses the greeting.
	fab.addEventListener('click', hideGreeting);

	/* --------------------------------------------------
	   Message Rendering
	   -------------------------------------------------- */

	function addMessage(html, isBot) {
		var div = document.createElement('div');
		div.className = 'sr-msg ' + (isBot ? 'sr-msg--bot' : 'sr-msg--user');
		div.innerHTML = html;
		messagesEl.appendChild(div);
		messagesEl.scrollTop = messagesEl.scrollHeight;
	}

	function addTypingIndicator() {
		var div = document.createElement('div');
		div.className = 'sr-msg sr-msg--bot sr-msg--typing';
		div.id = 'sr-typing';
		div.innerHTML = '<span class="sr-dots"><span class="sr-dot"></span><span class="sr-dot"></span><span class="sr-dot"></span></span>';
		messagesEl.appendChild(div);
		messagesEl.scrollTop = messagesEl.scrollHeight;
	}

	function removeTypingIndicator() {
		var typing = document.getElementById('sr-typing');
		if (typing) typing.remove();
	}

	function setReplies(replies) {
		repliesEl.innerHTML = '';
		if (!replies || !replies.length) return;

		replies.forEach(function (r) {
			var btn = document.createElement('button');
			btn.className = 'sr-quick-reply';
			btn.textContent = r.label;
			btn.addEventListener('click', function () {
				addMessage(r.label, false);
				repliesEl.innerHTML = '';
				playConvo(r.goto);
			});
			repliesEl.appendChild(btn);
		});
	}

	/* --------------------------------------------------
	   Play Conversation Node
	   -------------------------------------------------- */

	function playConvo(nodeKey) {
		var node = CONVO[nodeKey];
		if (!node) {
			node = CONVO.fallback;
		}

		var msgs = node.messages;
		var i = 0;

		function showNext() {
			if (i >= msgs.length) {
				removeTypingIndicator();
				setReplies(node.replies);
				return;
			}

			if (i > 0) {
				removeTypingIndicator();
			}

			addMessage(msgs[i], true);
			i++;

			if (i < msgs.length) {
				addTypingIndicator();
				setTimeout(showNext, 600 + Math.min(msgs[i - 1].length * 8, 800));
			} else {
				setTimeout(function () {
					setReplies(node.replies);
				}, 200);
			}
		}

		addTypingIndicator();
		setTimeout(showNext, 500);
	}

	/* --------------------------------------------------
	   Free-Text Input Handling
	   -------------------------------------------------- */

	if (form) {
		form.addEventListener('submit', function (e) {
			e.preventDefault();
			var text = (input.value || '').trim();
			if (!text) return;

			addMessage(escapeHtml(text), false);
			input.value = '';
			repliesEl.innerHTML = '';

			// Match keywords.
			var lower = text.toLowerCase();
			var matchedNode = null;

			for (var k = 0; k < KEYWORDS.length; k++) {
				var kw = KEYWORDS[k];
				for (var p = 0; p < kw.patterns.length; p++) {
					if (lower.indexOf(kw.patterns[p]) !== -1) {
						matchedNode = kw.goto;
						break;
					}
				}
				if (matchedNode) break;
			}

			playConvo(matchedNode || 'fallback');
		});
	}

	/* --------------------------------------------------
	   Utility
	   -------------------------------------------------- */

	function escapeHtml(str) {
		var div = document.createElement('div');
		div.appendChild(document.createTextNode(str));
		return div.innerHTML;
	}

})();
