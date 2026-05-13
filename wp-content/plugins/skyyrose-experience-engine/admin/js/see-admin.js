/**
 * Admin Dashboard JS — Analytics loading + Narrative submission.
 *
 * Uses wp-api-fetch (WordPress built-in) for REST calls.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

(function () {
	'use strict';

	var config = window.seeAdmin || {};

	/* ==========================================================================
	   Analytics Loading
	   ========================================================================== */

	function loadAnalytics() {
		var loading = document.getElementById('see-analytics-loading');
		var content = document.getElementById('see-analytics-content');

		if (!loading || !content) {
			return;
		}

		wp.apiFetch({ path: 'see/v1/analytics/summary?days=7' })
			.then(function (data) {
				loading.style.display = 'none';
				content.style.display = 'block';

				// Total events.
				var totalEvents = 0;
				(data.top_events || []).forEach(function (e) {
					totalEvents += parseInt(e.total_count, 10) || 0;
				});
				setText('see-metric-events', totalEvents.toLocaleString());

				// Collections engaged.
				setText('see-metric-collections', (data.collection_engagement || []).length);

				// Top event type.
				var topEvent = (data.top_events || [])[0];
				setText('see-metric-top-event', topEvent ? topEvent.event_type : 'none');

				// Render collection chart as simple bar chart.
				renderCollectionChart(data.collection_engagement || []);

				// Render daily trend.
				renderDailyTrend(data.daily_trend || []);
			})
			.catch(function () {
				loading.textContent = 'Analytics data will appear after visitors interact with your site.';
			});
	}

	function setText(id, text) {
		var el = document.getElementById(id);
		if (el) {
			el.textContent = text;
		}
	}

	function renderCollectionChart(data) {
		var container = document.getElementById('see-collection-chart');
		if (!container || data.length === 0) {
			return;
		}

		var maxCount = Math.max.apply(null, data.map(function (d) { return parseInt(d.total_count, 10) || 0; }));
		var colors = {
			'black-rose': '#C0C0C0',
			'love-hurts': '#DC143C',
			'signature': '#D4AF37',
			'kids-capsule': '#FFB6C1',
		};

		var html = '<h4 style="margin:0 0 8px;font-size:13px;color:#666;">Collection Engagement</h4>';
		data.forEach(function (d) {
			var count = parseInt(d.total_count, 10) || 0;
			var pct = maxCount > 0 ? Math.round((count / maxCount) * 100) : 0;
			var color = colors[d.collection_slug] || '#B76E79';
			html += '<div style="margin-bottom:6px;">';
			html += '<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:2px;">';
			html += '<span>' + escapeHtml(d.collection_slug || 'unknown') + '</span>';
			html += '<span>' + count.toLocaleString() + '</span>';
			html += '</div>';
			html += '<div style="background:#f0f0f0;border-radius:4px;height:8px;overflow:hidden;">';
			html += '<div style="width:' + pct + '%;background:' + color + ';height:100%;border-radius:4px;transition:width 0.5s;"></div>';
			html += '</div></div>';
		});
		container.innerHTML = html;
	}

	function renderDailyTrend(data) {
		var container = document.getElementById('see-daily-trend');
		if (!container || data.length === 0) {
			return;
		}

		var maxCount = Math.max.apply(null, data.map(function (d) { return parseInt(d.total_count, 10) || 0; }));

		var html = '<h4 style="margin:16px 0 8px;font-size:13px;color:#666;">Daily Activity</h4>';
		html += '<div style="display:flex;align-items:flex-end;gap:4px;height:80px;">';
		data.forEach(function (d) {
			var count = parseInt(d.total_count, 10) || 0;
			var pct = maxCount > 0 ? Math.max(4, Math.round((count / maxCount) * 100)) : 4;
			var date = (d.event_date || '').slice(5); // MM-DD
			html += '<div style="flex:1;text-align:center;">';
			html += '<div style="height:' + pct + '%;background:#B76E79;border-radius:3px 3px 0 0;min-height:4px;" title="' + count + ' events"></div>';
			html += '<div style="font-size:9px;color:#aaa;margin-top:2px;">' + escapeHtml(date) + '</div>';
			html += '</div>';
		});
		html += '</div>';
		container.innerHTML = html;
	}

	/* ==========================================================================
	   Narrative Form Submission
	   ========================================================================== */

	function initNarrativeForm() {
		var form = document.getElementById('see-narrative-form');
		if (!form) {
			return;
		}

		form.addEventListener('submit', function (e) {
			e.preventDefault();

			var description = document.getElementById('see-narrative-input').value.trim();
			if (!description) {
				return;
			}

			var target = document.getElementById('see-narrative-target').value;
			var priority = parseInt(document.getElementById('see-narrative-priority').value, 10);
			var expires = document.getElementById('see-narrative-expires').value;

			var button = form.querySelector('button[type="submit"]');
			button.disabled = true;
			button.textContent = 'Submitting...';

			wp.apiFetch({
				path: 'see/v1/settings/narrative',
				method: 'POST',
				data: {
					description: description,
					target: target,
					config: {},
					priority: priority,
					expires: expires || '',
				},
			})
				.then(function (result) {
					showNarrativeResult(result);
					if (result.status === 'accepted') {
						document.getElementById('see-narrative-input').value = '';
						// Reload page to show new directive.
						setTimeout(function () { window.location.reload(); }, 1500);
					}
				})
				.catch(function (err) {
					showNarrativeResult({
						status: 'declined',
						reason: err.message || 'Failed to submit narrative.',
					});
				})
				.finally(function () {
					button.disabled = false;
					button.textContent = 'Submit Narrative';
				});
		});
	}

	function showNarrativeResult(result) {
		var el = document.getElementById('see-narrative-result');
		if (!el) {
			return;
		}

		el.style.display = 'block';
		el.className = 'see-narrative-result see-narrative-result--' + result.status;

		if (result.status === 'accepted') {
			el.innerHTML = '<strong>Accepted.</strong> The engine will adapt to your directive.';
		} else {
			el.innerHTML = '<strong>Declined.</strong> ' + escapeHtml(result.reason || 'Unknown reason.');
		}

		// Auto-hide after 5 seconds.
		setTimeout(function () {
			el.style.display = 'none';
		}, 5000);
	}

	/* ==========================================================================
	   Directive Removal
	   ========================================================================== */

	function initDirectiveRemoval() {
		document.addEventListener('click', function (e) {
			var btn = e.target.closest('.see-directive-remove');
			if (!btn) {
				return;
			}

			var id = btn.getAttribute('data-id');
			if (!id || !confirm('Remove this directive?')) {
				return;
			}

			wp.apiFetch({
				path: 'see/v1/settings/narrative/' + id,
				method: 'DELETE',
			})
				.then(function () {
					var directive = btn.closest('.see-directive');
					if (directive) {
						directive.style.opacity = '0';
						setTimeout(function () { directive.remove(); }, 300);
					}
				})
				.catch(function (err) {
					alert('Failed to remove: ' + (err.message || 'Unknown error'));
				});
		});
	}

	/* ==========================================================================
	   Helpers
	   ========================================================================== */

	function escapeHtml(str) {
		var div = document.createElement('div');
		div.appendChild(document.createTextNode(str));
		return div.innerHTML;
	}

	/* ==========================================================================
	   Init
	   ========================================================================== */

	document.addEventListener('DOMContentLoaded', function () {
		loadAnalytics();
		initNarrativeForm();
		initDirectiveRemoval();
	});
})();
