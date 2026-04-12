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
   */
  function skyyToast(message, type, duration) {
    var container = document.getElementById('toast-container');
    if (!container) return;

    type = type || 'info';
    duration = duration || 4000;

    var toast = document.createElement('div');
    toast.className = 'toast toast--' + type;
    toast.setAttribute('role', 'status');

    var content = document.createElement('div');
    content.className = 'toast__content';

    var msg = document.createElement('span');
    msg.className = 'toast__message';
    msg.textContent = message;

    var dismiss = document.createElement('button');
    dismiss.className = 'toast__dismiss';
    dismiss.setAttribute('type', 'button');
    dismiss.setAttribute('aria-label', 'Dismiss');
    dismiss.textContent = '\u00D7';

    content.appendChild(msg);
    content.appendChild(dismiss);
    toast.appendChild(content);
    container.appendChild(toast);

    var timer = null;

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

    dismiss.addEventListener('click', remove);

    if (reducedMotion) {
      toast.classList.add('visible');
    } else {
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { toast.classList.add('visible'); });
      });
    }

    timer = setTimeout(remove, duration);
  }

  window.skyyToast = skyyToast;
})();
