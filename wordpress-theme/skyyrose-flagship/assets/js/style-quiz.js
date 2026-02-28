/**
 * Style DNA Quiz — Interactive Personality Quiz Engine
 *
 * 7 visual questions → collection score accumulation → DNA ring reveal
 * → canvas-generated shareable card → product recommendations.
 *
 * @package SkyyRose_Flagship
 * @since   3.10.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Questions Data
	   -------------------------------------------------- */

	var QUESTIONS = [
		{
			id: 1,
			text: 'Pick the scene that speaks to you.',
			options: [
				{ label: 'Moonlit garden',       hint: 'Shadows, roses, mystery',    scores: { br: 3, lh: 0, sg: 0 } },
				{ label: 'Candlelit ballroom',    hint: 'Passion, drama, intensity',  scores: { br: 0, lh: 3, sg: 0 } },
				{ label: 'Bay Area sunset',       hint: 'Golden light, warm breeze',  scores: { br: 0, lh: 0, sg: 3 } },
				{ label: 'All of the above',      hint: 'You contain multitudes',     scores: { br: 1, lh: 1, sg: 1 } }
			]
		},
		{
			id: 2,
			text: 'Which colors draw you in?',
			options: [
				{ label: 'Black & silver',        hint: 'Midnight chrome',            scores: { br: 3, lh: 0, sg: 0 } },
				{ label: 'Crimson & deep red',    hint: 'Fire and wine',              scores: { br: 0, lh: 3, sg: 0 } },
				{ label: 'Rose gold & cream',     hint: 'Warm luxury',                scores: { br: 0, lh: 0, sg: 3 } },
				{ label: 'All shades speak to me', hint: 'Color chameleon',           scores: { br: 1, lh: 1, sg: 1 } }
			]
		},
		{
			id: 3,
			text: "What's on your playlist right now?",
			options: [
				{ label: 'Dark R&B / Alternative', hint: 'The Weeknd, SZA, Billie',  scores: { br: 3, lh: 0, sg: 0 } },
				{ label: 'Passionate ballads',     hint: 'Adele, Frank Ocean, Jhené', scores: { br: 0, lh: 3, sg: 0 } },
				{ label: 'West Coast vibes',       hint: 'Kendrick, Mac Dre, Kehlani', scores: { br: 0, lh: 0, sg: 3 } },
				{ label: 'A bit of everything',    hint: 'Mood-dependent rotation',   scores: { br: 1, lh: 1, sg: 1 } }
			]
		},
		{
			id: 4,
			text: 'How do you show up?',
			options: [
				{ label: 'Bold & mysterious',      hint: 'You turn heads without trying', scores: { br: 3, lh: 0, sg: 0 } },
				{ label: 'Expressive & dramatic',  hint: 'Fashion is your language',      scores: { br: 0, lh: 3, sg: 0 } },
				{ label: 'Clean & confident',      hint: 'Effortless but intentional',    scores: { br: 0, lh: 0, sg: 3 } },
				{ label: 'Depends on the day',     hint: 'Versatile energy',              scores: { br: 1, lh: 1, sg: 1 } }
			]
		},
		{
			id: 5,
			text: 'Your ideal evening out?',
			options: [
				{ label: 'Underground art show',   hint: 'Dim lights, bold art, deep conversations', scores: { br: 3, lh: 0, sg: 0 } },
				{ label: 'Rooftop dinner',         hint: 'City lights, wine, someone special',       scores: { br: 0, lh: 3, sg: 0 } },
				{ label: 'Beach bonfire',           hint: 'Golden hour, good company, waves',         scores: { br: 0, lh: 0, sg: 3 } },
				{ label: 'Surprise me',            hint: 'Spontaneity is the spice',                 scores: { br: 1, lh: 1, sg: 1 } }
			]
		},
		{
			id: 6,
			text: 'What makes you feel powerful?',
			options: [
				{ label: 'Standing apart',         hint: 'Not fitting in is the point',   scores: { br: 3, lh: 0, sg: 0 } },
				{ label: 'Wearing your heart',     hint: 'Vulnerability is strength',     scores: { br: 0, lh: 3, sg: 0 } },
				{ label: 'Effortless cool',        hint: 'Grace under pressure',          scores: { br: 0, lh: 0, sg: 3 } },
				{ label: 'All of the above',       hint: 'Power is multidimensional',     scores: { br: 1, lh: 1, sg: 1 } }
			]
		},
		{
			id: 7,
			text: 'Your must-have accessory?',
			options: [
				{ label: 'Statement piece',        hint: 'Chains, rings, dark metals',    scores: { br: 3, lh: 0, sg: 0 } },
				{ label: 'Sentimental jewelry',    hint: 'Something with meaning',        scores: { br: 0, lh: 3, sg: 0 } },
				{ label: 'Quality basics',          hint: 'Clean watch, simple bracelet',  scores: { br: 0, lh: 0, sg: 3 } },
				{ label: 'Whatever fits the mood', hint: 'Different day, different vibe',  scores: { br: 1, lh: 1, sg: 1 } }
			]
		}
	];

	/* --------------------------------------------------
	   Collection Metadata
	   -------------------------------------------------- */

	var COLLECTIONS = {
		br: { name: 'Black Rose',  color: '#C0C0C0', slug: 'black-rose' },
		lh: { name: 'Love Hurts',  color: '#DC143C', slug: 'love-hurts' },
		sg: { name: 'Signature',   color: '#B76E79', slug: 'signature' }
	};

	var SUMMARIES = {
		br: 'Your style DNA is rooted in the dark and defiant. You gravitate toward bold silhouettes, moody tones, and pieces that command attention without saying a word. The Black Rose collection was made for spirits like yours.',
		lh: 'Your style DNA burns with passion. You dress to express, not to impress — wearing emotion on your sleeve and turning vulnerability into power. The Love Hurts collection channels your fearless heart.',
		sg: 'Your style DNA radiates effortless confidence. Clean lines, warm tones, and intentional simplicity define your wardrobe. The Signature collection mirrors your energy — timeless and self-assured.',
		mixed: 'Your style DNA is beautifully complex — a fusion of darkness, passion, and warmth. You draw from every collection because your personality refuses to be boxed in. True luxury is being unapologetically you.'
	};

	/* --------------------------------------------------
	   DOM References
	   -------------------------------------------------- */

	var quizWrap         = document.querySelector('.style-quiz');
	var introScreen      = document.getElementById('quiz-intro');
	var questionsScreen  = document.getElementById('quiz-questions');
	var resultsScreen    = document.getElementById('quiz-results');
	var startBtn         = document.getElementById('quiz-start');
	var questionContainer = document.getElementById('quiz-question-container');
	var progressBar      = document.querySelector('.quiz-progress__bar');
	var progressLabel    = document.querySelector('.quiz-progress__label');
	var dnaRing          = document.getElementById('quiz-dna-ring');
	var dnaLabels        = document.getElementById('quiz-dna-labels');
	var summaryEl        = document.getElementById('quiz-results-summary');
	var recsEl           = document.getElementById('quiz-recs');
	var canvas           = document.getElementById('quiz-share-canvas');
	var preview          = document.getElementById('quiz-share-preview');
	var shareBtn         = document.getElementById('quiz-share-btn');
	var downloadBtn      = document.getElementById('quiz-download-btn');
	var retakeBtn        = document.getElementById('quiz-retake');

	if (!quizWrap || !startBtn) return;

	var products = [];
	try {
		products = JSON.parse(quizWrap.dataset.products || '[]');
	} catch (_) {}

	var currentQ = 0;
	var scores   = { br: 0, lh: 0, sg: 0 };

	/* --------------------------------------------------
	   Screen Management
	   -------------------------------------------------- */

	function showScreen(screen) {
		[introScreen, questionsScreen, resultsScreen].forEach(function (s) {
			if (s) s.classList.remove('active');
		});
		if (screen) {
			screen.classList.add('active');
			screen.scrollIntoView({ behavior: 'smooth', block: 'start' });
		}
	}

	/* --------------------------------------------------
	   Render Question
	   -------------------------------------------------- */

	function renderQuestion(index) {
		var q = QUESTIONS[index];
		if (!q) return;

		// Update progress.
		var pct = ((index) / QUESTIONS.length) * 100;
		if (progressBar) progressBar.style.width = pct + '%';
		if (progressLabel) progressLabel.textContent = (index + 1) + ' / ' + QUESTIONS.length;

		var html = '<div class="quiz-question" role="group" aria-label="Question ' + (index + 1) + '">';
		html += '<p class="quiz-question__number">Question ' + (index + 1) + ' of ' + QUESTIONS.length + '</p>';
		html += '<h2 class="quiz-question__text">' + escapeHtml(q.text) + '</h2>';
		html += '<div class="quiz-options" role="listbox">';

		q.options.forEach(function (opt, i) {
			html += '<button class="quiz-option" role="option" data-q="' + index + '" data-o="' + i + '">';
			html += '<span class="quiz-option__label">' + escapeHtml(opt.label) + '</span>';
			html += '<span class="quiz-option__hint">' + escapeHtml(opt.hint) + '</span>';
			html += '</button>';
		});

		html += '</div></div>';
		questionContainer.innerHTML = html;

		// Bind option clicks.
		var optBtns = questionContainer.querySelectorAll('.quiz-option');
		optBtns.forEach(function (btn) {
			btn.addEventListener('click', function () {
				var oIdx = parseInt(btn.dataset.o, 10);
				selectAnswer(index, oIdx, btn);
			});
		});
	}

	function selectAnswer(qIdx, oIdx, btnEl) {
		// Visual feedback.
		var siblings = btnEl.parentElement.querySelectorAll('.quiz-option');
		siblings.forEach(function (s) { s.classList.remove('selected'); });
		btnEl.classList.add('selected');

		// Accumulate scores.
		var opt = QUESTIONS[qIdx].options[oIdx];
		scores.br += opt.scores.br;
		scores.lh += opt.scores.lh;
		scores.sg += opt.scores.sg;

		// Advance after brief pause.
		setTimeout(function () {
			currentQ++;
			if (currentQ < QUESTIONS.length) {
				renderQuestion(currentQ);
			} else {
				showResults();
			}
		}, 400);
	}

	/* --------------------------------------------------
	   Results
	   -------------------------------------------------- */

	function showResults() {
		// Calculate percentages.
		var total = scores.br + scores.lh + scores.sg;
		if (total === 0) total = 1;

		var pcts = {
			br: Math.round((scores.br / total) * 100),
			lh: Math.round((scores.lh / total) * 100),
			sg: Math.round((scores.sg / total) * 100)
		};

		// Ensure they sum to 100.
		var diff = 100 - pcts.br - pcts.lh - pcts.sg;
		var dominant = 'sg';
		if (scores.br >= scores.lh && scores.br >= scores.sg) dominant = 'br';
		else if (scores.lh >= scores.br && scores.lh >= scores.sg) dominant = 'lh';
		pcts[dominant] += diff;

		// Full progress bar.
		if (progressBar) progressBar.style.width = '100%';
		if (progressLabel) progressLabel.textContent = '7 / 7';

		// Render DNA ring (conic gradient).
		if (dnaRing) {
			var conicStops = buildConicGradient(pcts);
			dnaRing.style.background = 'conic-gradient(from 0deg, ' + conicStops + ')';
			dnaRing.style.mask = 'radial-gradient(farthest-side, transparent 65%, #000 66%)';
			dnaRing.style.webkitMask = dnaRing.style.mask;
		}

		// Render labels.
		if (dnaLabels) {
			var labelsHtml = '';
			['br', 'lh', 'sg'].forEach(function (key) {
				labelsHtml += '<div class="quiz-dna-label">';
				labelsHtml += '<span class="quiz-dna-label__dot" style="background:' + COLLECTIONS[key].color + '"></span>';
				labelsHtml += '<span>' + COLLECTIONS[key].name + '</span>';
				labelsHtml += '<span class="quiz-dna-label__pct">' + pcts[key] + '%</span>';
				labelsHtml += '</div>';
			});
			dnaLabels.innerHTML = labelsHtml;
		}

		// Summary.
		var isMixed = Math.abs(pcts.br - pcts.lh) < 15 && Math.abs(pcts.lh - pcts.sg) < 15;
		if (summaryEl) {
			summaryEl.textContent = isMixed ? SUMMARIES.mixed : SUMMARIES[dominant];
		}

		// Product recommendations (top 3 from dominant collection, fallback to mixed).
		renderRecs(dominant, pcts);

		// Shareable card.
		renderShareCard(pcts, dominant);

		showScreen(resultsScreen);
	}

	function buildConicGradient(pcts) {
		var stops = [];
		var cumulative = 0;

		var keys = ['br', 'lh', 'sg'];
		keys.forEach(function (key) {
			var start = cumulative;
			var end   = cumulative + (pcts[key] / 100) * 360;
			stops.push(COLLECTIONS[key].color + ' ' + start + 'deg ' + end + 'deg');
			cumulative = end;
		});

		return stops.join(', ');
	}

	/* --------------------------------------------------
	   Product Recommendations
	   -------------------------------------------------- */

	function renderRecs(dominant, pcts) {
		if (!recsEl || !products.length) return;

		// Sort products by affinity to DNA.
		var scored = products.map(function (p) {
			var colKey = 'sg';
			if (p.collection === 'black-rose') colKey = 'br';
			else if (p.collection === 'love-hurts') colKey = 'lh';
			return { product: p, affinity: pcts[colKey] };
		});

		scored.sort(function (a, b) { return b.affinity - a.affinity; });

		var top3 = scored.slice(0, 3);
		var html = '';

		top3.forEach(function (item) {
			var p = item.product;
			html += '<a href="' + escapeAttr(p.url) + '" class="quiz-rec-card">';
			if (p.image) {
				html += '<img class="quiz-rec-card__img" src="' + escapeAttr(p.image) + '" alt="' + escapeAttr(p.name) + '" loading="lazy" width="180" height="240" />';
			}
			html += '<div class="quiz-rec-card__info">';
			html += '<p class="quiz-rec-card__name">' + escapeHtml(p.name) + '</p>';
			html += '<p class="quiz-rec-card__price">' + escapeHtml(p.price) + '</p>';
			html += '</div></a>';
		});

		recsEl.innerHTML = html;
	}

	/* --------------------------------------------------
	   Shareable Card (Canvas)
	   -------------------------------------------------- */

	function renderShareCard(pcts, dominant) {
		if (!canvas) return;

		var ctx = canvas.getContext('2d');
		var W = canvas.width;
		var H = canvas.height;

		// Dark background.
		ctx.fillStyle = '#0a0a0a';
		ctx.fillRect(0, 0, W, H);

		// Subtle border.
		ctx.strokeStyle = 'rgba(183, 110, 121, 0.3)';
		ctx.lineWidth = 1;
		roundRect(ctx, 0.5, 0.5, W - 1, H - 1, 16);
		ctx.stroke();

		// Brand name.
		ctx.font = '700 11px Inter, sans-serif';
		ctx.fillStyle = 'rgba(183, 110, 121, 0.6)';
		ctx.letterSpacing = '3px';
		ctx.textAlign = 'left';
		ctx.fillText('SKYYROSE', 32, 40);

		// Title.
		ctx.font = '700 36px Playfair Display, serif';
		ctx.fillStyle = '#fff';
		ctx.fillText('Style DNA', 32, 85);

		// DNA bars.
		var barX = 32;
		var barY = 120;
		var barW = 240;
		var barH = 22;
		var barGap = 36;

		['br', 'lh', 'sg'].forEach(function (key, i) {
			var y = barY + i * barGap;

			// Label.
			ctx.font = '600 11px Inter, sans-serif';
			ctx.fillStyle = 'rgba(255,255,255,0.5)';
			ctx.textAlign = 'left';
			ctx.fillText(COLLECTIONS[key].name.toUpperCase(), barX, y - 4);

			// Percentage.
			ctx.textAlign = 'right';
			ctx.fillStyle = COLLECTIONS[key].color;
			ctx.fillText(pcts[key] + '%', barX + barW, y - 4);

			// Track.
			ctx.fillStyle = 'rgba(255,255,255,0.04)';
			roundRect(ctx, barX, y, barW, barH, 4);
			ctx.fill();

			// Fill.
			var fillW = (pcts[key] / 100) * barW;
			if (fillW > 0) {
				ctx.fillStyle = COLLECTIONS[key].color;
				roundRect(ctx, barX, y, Math.max(fillW, 8), barH, 4);
				ctx.fill();
			}
		});

		// Mini DNA ring on right side.
		var ringCx = W - 120;
		var ringCy = 180;
		var ringR  = 70;
		var startAngle = -Math.PI / 2;

		['br', 'lh', 'sg'].forEach(function (key) {
			var sweep = (pcts[key] / 100) * Math.PI * 2;
			ctx.beginPath();
			ctx.arc(ringCx, ringCy, ringR, startAngle, startAngle + sweep);
			ctx.strokeStyle = COLLECTIONS[key].color;
			ctx.lineWidth = 14;
			ctx.lineCap = 'round';
			ctx.stroke();
			startAngle += sweep;
		});

		// Inner circle (mask effect).
		ctx.beginPath();
		ctx.arc(ringCx, ringCy, ringR - 20, 0, Math.PI * 2);
		ctx.fillStyle = '#0a0a0a';
		ctx.fill();

		// Dominant text in center.
		ctx.font = '700 14px Inter, sans-serif';
		ctx.fillStyle = COLLECTIONS[dominant].color;
		ctx.textAlign = 'center';
		ctx.fillText(pcts[dominant] + '%', ringCx, ringCy + 5);

		// Bottom tagline.
		ctx.font = '600 10px Inter, sans-serif';
		ctx.fillStyle = 'rgba(255,255,255,0.25)';
		ctx.textAlign = 'center';
		ctx.fillText('LUXURY GROWS FROM CONCRETE  \u2022  SKYYROSE.CO', W / 2, H - 24);

		// Convert to image.
		try {
			var dataUrl = canvas.toDataURL('image/png');
			if (preview) {
				preview.src = dataUrl;
				preview.style.display = 'block';
			}
		} catch (_) {}
	}

	function roundRect(ctx, x, y, w, h, r) {
		ctx.beginPath();
		ctx.moveTo(x + r, y);
		ctx.lineTo(x + w - r, y);
		ctx.quadraticCurveTo(x + w, y, x + w, y + r);
		ctx.lineTo(x + w, y + h - r);
		ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
		ctx.lineTo(x + r, y + h);
		ctx.quadraticCurveTo(x, y + h, x, y + h - r);
		ctx.lineTo(x, y + r);
		ctx.quadraticCurveTo(x, y, x + r, y);
		ctx.closePath();
	}

	/* --------------------------------------------------
	   Sharing
	   -------------------------------------------------- */

	if (shareBtn) {
		shareBtn.addEventListener('click', function () {
			if (!canvas) return;

			// Try Web Share API first.
			if (navigator.share && navigator.canShare) {
				canvas.toBlob(function (blob) {
					if (!blob) return;
					var file = new File([blob], 'skyyrose-style-dna.png', { type: 'image/png' });
					var shareData = {
						title: 'My SkyyRose Style DNA',
						text: 'Discover your Style DNA at skyyrose.co',
						files: [file]
					};
					if (navigator.canShare(shareData)) {
						navigator.share(shareData);
					} else {
						downloadCard();
					}
				}, 'image/png');
			} else {
				downloadCard();
			}
		});
	}

	if (downloadBtn) {
		downloadBtn.addEventListener('click', downloadCard);
	}

	function downloadCard() {
		if (!canvas) return;
		var link = document.createElement('a');
		link.download = 'skyyrose-style-dna.png';
		link.href = canvas.toDataURL('image/png');
		link.click();
	}

	/* --------------------------------------------------
	   Retake
	   -------------------------------------------------- */

	if (retakeBtn) {
		retakeBtn.addEventListener('click', function () {
			currentQ = 0;
			scores = { br: 0, lh: 0, sg: 0 };
			showScreen(introScreen);
		});
	}

	/* --------------------------------------------------
	   Start Quiz
	   -------------------------------------------------- */

	startBtn.addEventListener('click', function () {
		showScreen(questionsScreen);
		renderQuestion(0);
	});

	/* --------------------------------------------------
	   Utility
	   -------------------------------------------------- */

	function escapeHtml(str) {
		var div = document.createElement('div');
		div.appendChild(document.createTextNode(str));
		return div.innerHTML;
	}

	function escapeAttr(str) {
		return str.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
	}

})();
