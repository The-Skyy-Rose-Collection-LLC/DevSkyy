/**
 * GestureManager
 * Unified touch and mouse drag gesture detection for the SkyyRose experience.
 * Dispatches 'swipe-left' and 'swipe-right' custom events on document.
 */
class GestureManager {
  constructor(config = {}) {
    this.minSwipe  = config.minSwipe  ?? 50;
    this.maxTime   = config.maxTime   ?? 500;

    // Touch state
    this._touch = {
      startX: 0,
      startY: 0,
      startTime: 0,
      tracking: false,
    };

    // Mouse drag state
    this._mouse = {
      startX: 0,
      startY: 0,
      startTime: 0,
      dragging: false,
      moved: false,
    };

    this._MOUSE_DRAG_THRESHOLD    = 80;
    this._MOUSE_MOVE_MIN          = 10;   // px before we consider it a drag
  }

  init() {
    // Touch events
    document.addEventListener('touchstart',  this._onTouchStart.bind(this),  { passive: true });
    document.addEventListener('touchmove',   this._onTouchMove.bind(this),   { passive: false });
    document.addEventListener('touchend',    this._onTouchEnd.bind(this),    { passive: true });

    // Mouse drag events
    document.addEventListener('mousedown',   this._onMouseDown.bind(this));
    document.addEventListener('mousemove',   this._onMouseMove.bind(this));
    document.addEventListener('mouseup',     this._onMouseUp.bind(this));

    // Wire swipe events to room navigation
    document.addEventListener('swipe-left',  () => {
      if (typeof window.next === 'function') window.next();
    });
    document.addEventListener('swipe-right', () => {
      if (typeof window.prev === 'function') window.prev();
    });
  }

  // ---------------------------------------------------------------------------
  // Touch handlers
  // ---------------------------------------------------------------------------
  _onTouchStart(e) {
    const t = e.changedTouches[0];
    this._touch.startX    = t.clientX;
    this._touch.startY    = t.clientY;
    this._touch.startTime = Date.now();
    this._touch.tracking  = true;
  }

  _onTouchMove(e) {
    if (!this._touch.tracking) return;

    const t      = e.changedTouches[0];
    const deltaX = t.clientX - this._touch.startX;
    const deltaY = t.clientY - this._touch.startY;

    // Prevent page scroll when a horizontal swipe is in progress
    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 10) {
      e.preventDefault();
    }
  }

  _onTouchEnd(e) {
    if (!this._touch.tracking) return;
    this._touch.tracking = false;

    const t       = e.changedTouches[0];
    const deltaX  = t.clientX - this._touch.startX;
    const deltaY  = t.clientY - this._touch.startY;
    const elapsed = Date.now() - this._touch.startTime;

    if (
      Math.abs(deltaX) > this.minSwipe &&
      elapsed < this.maxTime &&
      Math.abs(deltaX) > Math.abs(deltaY)
    ) {
      this._dispatch(deltaX < 0 ? 'swipe-left' : 'swipe-right');
    }
  }

  // ---------------------------------------------------------------------------
  // Mouse drag handlers
  // ---------------------------------------------------------------------------
  _onMouseDown(e) {
    // Ignore clicks on interactive elements
    const tag = e.target.tagName;
    if (tag === 'BUTTON' || tag === 'A' || e.target.closest('button, a')) return;

    this._mouse.startX    = e.clientX;
    this._mouse.startY    = e.clientY;
    this._mouse.startTime = Date.now();
    this._mouse.dragging  = true;
    this._mouse.moved     = false;
  }

  _onMouseMove(e) {
    if (!this._mouse.dragging) return;

    const deltaX = e.clientX - this._mouse.startX;
    const deltaY = e.clientY - this._mouse.startY;

    if (Math.abs(deltaX) > this._MOUSE_MOVE_MIN || Math.abs(deltaY) > this._MOUSE_MOVE_MIN) {
      this._mouse.moved = true;
    }
  }

  _onMouseUp(e) {
    if (!this._mouse.dragging) return;
    this._mouse.dragging = false;

    if (!this._mouse.moved) return;

    const deltaX  = e.clientX - this._mouse.startX;
    const deltaY  = e.clientY - this._mouse.startY;
    const elapsed = Date.now() - this._mouse.startTime;

    if (
      Math.abs(deltaX) > this._MOUSE_DRAG_THRESHOLD &&
      elapsed < this.maxTime &&
      Math.abs(deltaX) > Math.abs(deltaY)
    ) {
      this._dispatch(deltaX < 0 ? 'swipe-left' : 'swipe-right');
    }
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------
  _dispatch(eventName) {
    document.dispatchEvent(new CustomEvent(eventName, { bubbles: true }));
  }
}

// ---------------------------------------------------------------------------
// Export & auto-init
// ---------------------------------------------------------------------------
window.GestureManager = GestureManager;
window.gestures = new GestureManager();
window.gestures.init();
