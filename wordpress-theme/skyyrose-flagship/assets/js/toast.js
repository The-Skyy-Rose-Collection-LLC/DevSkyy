/**
 * SkyyRose Global Toast Utility
 *
 * Lightweight vanilla JS toast notification system.
 * Usage: window.skyyToast('Message', 'success', 4000)
 *
 * @package SkyyRose
 * @since   5.3.0
 */
(function () {
  'use strict';

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /**
   * Show a toast notification.
   *
   * @param {string} message  Text to display.
   * @param {string} [type]   'success' | 'error' | 'info' (default 'info').
   * @param {number} [duration] Auto-dismiss ms (default 4000).
   * @param {Object} [opts]   Optional extras.
   * @param {string} [opts.actionLabel] Visible label for an action link (caller-localized).
   * @param {string} [opts.actionUrl]   Href for the action link.
   */
  function skyyToast(message, type, duration, opts) {
    var container = document.getElementById('toast-container');
    if (!container) return;

    type = type || 'info';
    duration = duration || 4000;
    opts = opts || {};

    var toast = document.createElement('div');
    toast.className = 'toast toast--' + type;
    toast.setAttribute('role', 'status');

    var content = document.createElement('div');
    content.className = 'toast__content';

    var msg = document.createElement('span');
    msg.className = 'toast__message';
    msg.textContent = message;

    content.appendChild(msg);

    if (opts.actionUrl && opts.actionLabel) {
      // Resolve and scheme-check before it reaches href. Assigning the raw value would
      // let a caller turn the action into a javascript: URI — relative paths still work
      // because they resolve against the current origin and come back as http(s).
      var safeUrl = null;
      try {
        var parsed = new URL(opts.actionUrl, window.location.href);
        if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
          safeUrl = parsed.href;
        }
      } catch (err) {
        safeUrl = null;
      }

      if (safeUrl) {
        var action = document.createElement('a');
        action.className = 'toast__action';
        action.href = safeUrl;
        action.textContent = opts.actionLabel;
        content.appendChild(action);
      }
    }

    var dismiss = document.createElement('button');
    dismiss.className = 'toast__dismiss';
    dismiss.setAttribute('type', 'button');
    dismiss.setAttribute('aria-label', 'Dismiss');
    dismiss.textContent = '\u00D7';

    content.appendChild(dismiss);
    toast.appendChild(content);

    var progress = null;
    if (!reducedMotion) {
      progress = document.createElement('div');
      progress.className = 'toast__progress';
      progress.setAttribute('aria-hidden', 'true');
      progress.style.animationDuration = duration + 'ms';
      toast.appendChild(progress);
    }

    container.appendChild(toast);

    var timer = null;
    var startedAt = 0;
    var remaining = duration;

    function remove() {
      if (timer) clearTimeout(timer);
      toast.classList.remove('visible');
      if (reducedMotion) {
        toast.remove();
      } else {
        toast.addEventListener('transitionend', function () { toast.remove(); }, { once: true });
        setTimeout(function () { toast.remove(); }, 500);
      }
    }

    function startTimer() {
      startedAt = Date.now();
      timer = setTimeout(remove, remaining);
    }

    // Pause auto-dismiss while the pointer is over the toast \u2014 the CSS pauses
    // the progress bar animation on :hover so the two stay in sync.
    toast.addEventListener('mouseenter', function () {
      if (!timer) return;
      clearTimeout(timer);
      timer = null;
      remaining -= Date.now() - startedAt;
    });

    toast.addEventListener('mouseleave', function () {
      if (timer || remaining <= 0) return;
      startTimer();
    });

    dismiss.addEventListener('click', remove);

    if (reducedMotion) {
      toast.classList.add('visible');
    } else {
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { toast.classList.add('visible'); });
      });
    }

    startTimer();
  }

  window.skyyToast = skyyToast;
})();
