/**
 * AccessibilityManager
 * Handles keyboard navigation, ARIA, focus management, and screen reader announcements
 * for the SkyyRose luxury fashion experience.
 */
class AccessibilityManager {
  constructor() {
    this._focusTrap = null;
    this._focusTrapHandler = null;
    this._modalOpen = false;
    this._announcementEl = null;
    this._announcementTimeout = null;
  }

  init() {
    this._detectNavigationMode();
    this._setupSkipLinks();
    this._setupReducedMotion();
    this._setupAnnouncementRegion();
    this._setupKeyboardShortcuts();
  }

  // ---------------------------------------------------------------------------
  // Navigation mode detection (keyboard vs mouse)
  // ---------------------------------------------------------------------------
  _detectNavigationMode() {
    const onFirstTab = (e) => {
      if (e.key === 'Tab') {
        document.body.classList.add('using-keyboard');
        document.removeEventListener('keydown', onFirstTab);
        document.addEventListener('mousedown', onMouseDown);
      }
    };

    const onMouseDown = () => {
      document.body.classList.remove('using-keyboard');
      document.removeEventListener('mousedown', onMouseDown);
      document.addEventListener('keydown', onFirstTab);
    };

    document.addEventListener('keydown', onFirstTab);
  }

  // ---------------------------------------------------------------------------
  // Skip links
  // ---------------------------------------------------------------------------
  _setupSkipLinks() {
    const skipMain = document.getElementById('skip-to-main');
    const skipNav  = document.getElementById('skip-to-nav');

    if (skipMain) {
      skipMain.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.getElementById('main') || document.querySelector('main');
        if (target) {
          target.setAttribute('tabindex', '-1');
          target.focus();
        }
      });
    }

    if (skipNav) {
      skipNav.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.getElementById('nav') || document.querySelector('nav');
        if (target) {
          target.setAttribute('tabindex', '-1');
          target.focus();
        }
      });
    }
  }

  // ---------------------------------------------------------------------------
  // Reduced motion
  // ---------------------------------------------------------------------------
  _setupReducedMotion() {
    if (typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');

    const apply = (matches) => {
      document.body.classList.toggle('reduced-motion', matches);
    };

    apply(mq.matches);

    // Listen for OS-level changes at runtime
    mq.addEventListener('change', (e) => apply(e.matches));
  }

  // ---------------------------------------------------------------------------
  // ARIA live region for screen reader announcements
  // ---------------------------------------------------------------------------
  _setupAnnouncementRegion() {
    let el = document.getElementById('announcements');

    if (!el) {
      el = document.createElement('div');
      el.id = 'announcements';
      el.setAttribute('role', 'status');
      el.setAttribute('aria-live', 'polite');
      el.setAttribute('aria-atomic', 'true');
      el.style.cssText = [
        'position:absolute',
        'width:1px',
        'height:1px',
        'padding:0',
        'margin:-1px',
        'overflow:hidden',
        'clip:rect(0,0,0,0)',
        'white-space:nowrap',
        'border:0',
      ].join(';');
      document.body.appendChild(el);
    }

    this._announcementEl = el;
  }

  /**
   * Announce a message to screen readers.
   * @param {string} message
   * @param {'polite'|'assertive'} priority
   */
  announce(message, priority = 'polite') {
    if (!this._announcementEl) return;

    // Toggle attribute so repeated identical messages still fire
    this._announcementEl.setAttribute('aria-live', priority);
    this._announcementEl.textContent = '';

    clearTimeout(this._announcementTimeout);
    this._announcementTimeout = setTimeout(() => {
      this._announcementEl.textContent = message;
    }, 50);
  }

  // ---------------------------------------------------------------------------
  // Focus trapping
  // ---------------------------------------------------------------------------

  /**
   * Trap keyboard focus within a given element.
   * @param {HTMLElement} element
   */
  trapFocus(element) {
    this._focusTrap = element;

    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(', ');

    const getFocusable = () => Array.from(element.querySelectorAll(focusableSelectors));

    this._focusTrapHandler = (e) => {
      if (e.key !== 'Tab') return;

      const focusable = getFocusable();
      if (focusable.length === 0) {
        e.preventDefault();
        return;
      }

      const first = focusable[0];
      const last  = focusable[focusable.length - 1];

      if (e.shiftKey) {
        // Shift+Tab — going backwards
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        // Tab — going forwards
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', this._focusTrapHandler);

    // Move focus into the element immediately
    const focusable = getFocusable();
    if (focusable.length > 0) {
      focusable[0].focus();
    } else {
      element.setAttribute('tabindex', '-1');
      element.focus();
    }
  }

  /**
   * Release the current focus trap and return focus to a trigger element.
   * @param {HTMLElement|null} returnTo
   */
  releaseFocus(returnTo = null) {
    if (this._focusTrapHandler) {
      document.removeEventListener('keydown', this._focusTrapHandler);
      this._focusTrapHandler = null;
    }
    this._focusTrap = null;

    if (returnTo && typeof returnTo.focus === 'function') {
      returnTo.focus();
    }
  }

  // ---------------------------------------------------------------------------
  // Modal helpers
  // ---------------------------------------------------------------------------

  /**
   * Wire accessibility behaviours for a modal.
   * @param {HTMLElement} modal
   * @param {HTMLElement} triggerEl - the element that opened the modal
   */
  setupModal(modal, triggerEl) {
    // Open
    const open = () => {
      this._modalOpen = true;
      modal.removeAttribute('hidden');
      modal.setAttribute('aria-modal', 'true');
      this.trapFocus(modal);
    };

    // Close
    const close = () => {
      this._modalOpen = false;
      modal.setAttribute('hidden', '');
      modal.removeAttribute('aria-modal');
      this.releaseFocus(triggerEl);
    };

    // Expose on element for external callers
    modal._a11yOpen  = open;
    modal._a11yClose = close;

    return { open, close };
  }

  // ---------------------------------------------------------------------------
  // Keyboard shortcuts
  // ---------------------------------------------------------------------------
  _setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ignore when focus is inside a text input
      const tag = document.activeElement && document.activeElement.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (document.activeElement && document.activeElement.isContentEditable) return;

      switch (e.key) {
        case 'ArrowLeft':
          if (!this._modalOpen) {
            e.preventDefault();
            if (typeof window.prev === 'function') window.prev();
          }
          break;

        case 'ArrowRight':
          if (!this._modalOpen) {
            e.preventDefault();
            if (typeof window.next === 'function') window.next();
          }
          break;

        case '1':
          if (!this._modalOpen) {
            e.preventDefault();
            this._jumpToRoom(0);
          }
          break;

        case '2':
          if (!this._modalOpen) {
            e.preventDefault();
            this._jumpToRoom(1);
          }
          break;

        case '3':
          if (!this._modalOpen) {
            e.preventDefault();
            this._jumpToRoom(2);
          }
          break;

        case 'Escape':
          if (this._modalOpen) {
            // Find currently open modal and close it
            const openModal = document.querySelector('[aria-modal="true"]');
            if (openModal && typeof openModal._a11yClose === 'function') {
              openModal._a11yClose();
            }
          }
          break;
      }
    });
  }

  _jumpToRoom(index) {
    if (typeof window.goToRoom === 'function') {
      window.goToRoom(index);
    }
  }
}

// ---------------------------------------------------------------------------
// Export & auto-init
// ---------------------------------------------------------------------------
window.AccessibilityManager = AccessibilityManager;
window.a11y = new AccessibilityManager();
window.a11y.init();
