/**
 * SkyyRose Avatar Assistant
 * Animated floating fashion assistant for the luxury virtual showroom.
 * Renders a CSS/SVG character in the bottom-right corner.
 * No external images — pure CSS shapes + SVG paths.
 *
 * @version 1.0.0
 */

(function (global) {
  'use strict';

  // ---------------------------------------------------------------------------
  // Constants
  // ---------------------------------------------------------------------------

  const COLLECTION_ACCENT = {
    'black-rose': '#c0392b',
    'love-hurts': '#e74c8b',
    'signature':  '#b57bee',
    'default':    '#c9a96e',
  };

  const STATES = ['idle', 'thinking', 'talking', 'pointing', 'celebrating'];

  const DEFAULT_CONFIG = {
    model:         'claude-sonnet-4-5-20250929',
    apiEndpoint:   '/api/assistant',
    systemPrompt:  null, // filled in from server
    autoGreet:     true,
    greetDelay:    3000,
    productViewDelay: 5000,
  };

  // ---------------------------------------------------------------------------
  // AvatarAssistant class
  // ---------------------------------------------------------------------------

  class AvatarAssistant {
    /**
     * @param {Object} config
     * @param {string} [config.model]
     * @param {string} [config.systemPrompt]
     * @param {string} [config.apiEndpoint]
     * @param {boolean} [config.autoGreet]
     * @param {number}  [config.greetDelay]
     * @param {number}  [config.productViewDelay]
     */
    constructor(config = {}) {
      this.config = Object.assign({}, DEFAULT_CONFIG, config);

      // Allow global override
      if (global.avatarConfig) {
        Object.assign(this.config, global.avatarConfig);
      }

      this._state         = 'idle';
      this._chatOpen      = false;
      this._history       = [];
      this._currentRoom   = 'default';
      this._productTimer  = null;
      this._celebrateTimer = null;
      this._streamController = null;

      // DOM refs (set in init)
      this._root          = null;
      this._figure        = null;
      this._chatPanel     = null;
      this._messagesDiv   = null;
      this._inputEl       = null;
      this._toggleBtn     = null;
      this._outfitBadge   = null;
      this._armEl         = null;
      this._mouthEl       = null;

      // Reduced motion
      this._reducedMotion = this._detectReducedMotion();
    }

    // -------------------------------------------------------------------------
    // Public: init
    // -------------------------------------------------------------------------

    /**
     * Inject avatar HTML/CSS into the DOM and wire up all event listeners.
     */
    init() {
      if (document.getElementById('skyyrose-avatar')) {
        console.warn('[AvatarAssistant] Already initialised.');
        return this;
      }

      this._injectCSS();
      this._injectHTML();
      this._cacheRefs();
      this._bindEvents();

      // Walk-in entrance: slide up from bottom after a beat
      requestAnimationFrame(() => {
        setTimeout(() => {
          if (this._root) this._root.classList.add('avatar-entered');
        }, 120);
      });

      if (this.config.autoGreet) {
        // After walk-in settles (~1.1s), open chat and greet
        setTimeout(() => {
          if (!this._chatOpen) {
            this._openChat();
          }
        }, this.config.greetDelay);
      }

      return this;
    }

    // -------------------------------------------------------------------------
    // Public: state machine
    // -------------------------------------------------------------------------

    /**
     * Transition between avatar states.
     * @param {'idle'|'thinking'|'talking'|'pointing'|'celebrating'} state
     */
    setState(state) {
      if (!STATES.includes(state)) {
        console.warn('[AvatarAssistant] Unknown state:', state);
        return;
      }
      if (this._reducedMotion && state !== 'idle') {
        // Still update label/aria without animations
        state = 'idle';
      }

      if (this._root) {
        STATES.forEach(s => this._root.classList.remove(s));
        this._root.classList.add(state);
      }

      this._state = state;
    }

    // -------------------------------------------------------------------------
    // Public: chat
    // -------------------------------------------------------------------------

    /**
     * Send a user message to the assistant API and stream the response.
     * @param {string} userMessage
     */
    async chat(userMessage) {
      if (!userMessage || !userMessage.trim()) return;

      // Abort any in-flight stream
      if (this._streamController) {
        this._streamController.abort();
      }

      this.displayMessage(userMessage, 'user');
      this._history.push({ role: 'user', content: userMessage });

      this.setState('thinking');

      const endpoint = this.config.apiEndpoint || '/api/assistant';
      this._streamController = new AbortController();

      let assistantText = '';

      try {
        const res = await fetch(endpoint, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          signal:  this._streamController.signal,
          body: JSON.stringify({
            message:    userMessage,
            history:    this._history.slice(-20),
            collection: this._currentRoom,
          }),
        });

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }

        const contentType = res.headers.get('content-type') || '';

        if (contentType.includes('text/event-stream')) {
          // SSE streaming
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let assistantMsgEl = null;

          this.setState('talking');

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines  = chunk.split('\n');

            for (const line of lines) {
              if (!line.startsWith('data:')) continue;
              const data = line.slice(5).trim();
              if (data === '[DONE]') break;

              try {
                const parsed = JSON.parse(data);
                const delta  = parsed.delta || parsed.text || '';
                if (delta) {
                  assistantText += delta;

                  if (!assistantMsgEl) {
                    assistantMsgEl = this._appendMessageEl('assistant');
                  }
                  assistantMsgEl.textContent = assistantText;
                  this._scrollMessages();
                  this._triggerProductLinks(assistantText);
                }
              } catch (_) {
                // partial JSON — skip
              }
            }
          }
        } else {
          // Plain JSON response
          const json = await res.json();
          assistantText = json.content || json.message || json.text || '';
          this.setState('talking');
          this.displayMessage(assistantText, 'assistant');
          this._triggerProductLinks(assistantText);
        }

        this._history.push({ role: 'assistant', content: assistantText });
        this._announceToScreenReader(assistantText);

      } catch (err) {
        if (err.name === 'AbortError') return;
        console.error('[AvatarAssistant] Chat error:', err);
        this.displayMessage('I\'m having a moment — please try again shortly. 🌹', 'assistant');
      } finally {
        this._streamController = null;
        setTimeout(() => this.setState('idle'), 1200);
      }
    }

    // -------------------------------------------------------------------------
    // Public: displayMessage
    // -------------------------------------------------------------------------

    /**
     * Append a message bubble to the chat history.
     * @param {string} text
     * @param {'user'|'assistant'} role
     */
    displayMessage(text, role) {
      if (!this._messagesDiv) return;
      const el = this._appendMessageEl(role);
      el.textContent = text;
      this._scrollMessages();
    }

    // -------------------------------------------------------------------------
    // Public: pointAt
    // -------------------------------------------------------------------------

    /**
     * Animate the avatar arm toward a product hotspot element.
     * @param {string} productId  — id of a DOM element to point toward
     */
    pointAt(productId) {
      const target = document.getElementById(productId) ||
                     document.querySelector(`[data-product-id="${productId}"]`);

      if (!target || !this._root) return;

      this.setState('pointing');

      // Calculate rough direction from avatar to element
      const avatarRect = this._root.getBoundingClientRect();
      const targetRect  = target.getBoundingClientRect();

      const dx = targetRect.left - avatarRect.left;
      const dy = targetRect.top  - avatarRect.top;
      const angle = Math.atan2(dy, dx) * (180 / Math.PI);

      if (this._armEl) {
        this._armEl.style.transform = `rotate(${angle}deg)`;
      }

      setTimeout(() => {
        if (this._armEl) this._armEl.style.transform = '';
        this.setState('idle');
      }, 3000);
    }

    // -------------------------------------------------------------------------
    // Public: celebrate
    // -------------------------------------------------------------------------

    /**
     * Play celebrate animation then return to idle.
     */
    celebrate() {
      if (this._celebrateTimer) clearTimeout(this._celebrateTimer);
      this.setState('celebrating');
      this._celebrateTimer = setTimeout(() => {
        this.setState('idle');
        this._celebrateTimer = null;
      }, 2000);
    }

    // -------------------------------------------------------------------------
    // Public: show / hide
    // -------------------------------------------------------------------------

    show() {
      if (this._root) this._root.classList.remove('avatar-hidden');
    }

    hide() {
      if (this._root) {
        this._closeChat();
        this._root.classList.add('avatar-hidden');
      }
    }

    // -------------------------------------------------------------------------
    // Public: product/room hooks
    // -------------------------------------------------------------------------

    /**
     * Called when the user has been viewing a product for the configured delay.
     * @param {Object} product  — { id, name, collection, ... }
     */
    onProductView(product) {
      if (this._productTimer) clearTimeout(this._productTimer);
      this._productTimer = setTimeout(() => {
        if (!this._chatOpen) {
          const msg = `Loving the look of the ${product.name}? I can tell you everything about it — or help you find something that pairs perfectly. 🌹`;
          this._showBubble(msg, 3000);
        }
      }, this.config.productViewDelay);
    }

    /**
     * Called when a product is added to cart.
     * @param {Object} product
     */
    onCartAdd(product) {
      this.celebrate();
      const msg = product
        ? `Excellent choice — the ${product.name} is going to look stunning on you! ✦`
        : 'Beautiful choice! Your cart is looking as good as you. ✦';
      setTimeout(() => this._showBubble(msg, 2500), 400);
    }

    /**
     * Called on room/collection change.
     * @param {string} room  — 'black-rose' | 'love-hurts' | 'signature'
     */
    onRoomChange(room) {
      this._currentRoom = room;

      if (this._root) {
        Object.keys(COLLECTION_ACCENT).forEach(k => this._root.classList.remove(`room-${k}`));
        this._root.classList.add(`room-${room}`);

        // Update CSS accent variable
        const accent = COLLECTION_ACCENT[room] || COLLECTION_ACCENT['default'];
        this._root.style.setProperty('--avatar-accent', accent);
      }

      if (this._outfitBadge) {
        this._outfitBadge.textContent = this._roomLabel(room);
      }
    }

    // -------------------------------------------------------------------------
    // Private: DOM construction
    // -------------------------------------------------------------------------

    _buildAvatarHTML() {
      return `
<div id="skyyrose-avatar"
     class="avatar-widget idle"
     aria-label="SkyyRose fashion assistant"
     role="complementary"
     tabindex="0">

  <!-- Floating figure — Skyy mascot -->
  <div class="avatar-figure" aria-hidden="true">
    <img class="avatar-img"
         src="assets/images/avatar/skyy.png"
         alt="Skyy — SkyyRose mascot"
         draggable="false">

    <!-- Thinking spinner overlay -->
    <div class="skyy-spinner" aria-hidden="true">
      <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
        <circle cx="32" cy="32" r="26" fill="none"
                stroke="var(--avatar-accent, #c9a96e)" stroke-width="3"
                stroke-dasharray="120" stroke-dashoffset="40"
                stroke-linecap="round"/>
      </svg>
    </div>

    <!-- Collection badge -->
    <div class="avatar-outfit-badge" aria-hidden="true"></div>
  </div>

  <!-- Chat panel -->
  <div class="avatar-chat" role="dialog" aria-modal="false"
       aria-label="SkyyRose fashion assistant chat" hidden>
    <div class="chat-header">
      <div class="chat-header-left">
        <span class="chat-rose-icon" aria-hidden="true">🌹</span>
        <span class="chat-title">SkyyRose Assistant</span>
      </div>
      <div class="chat-header-actions">
        <button class="chat-minimize" aria-label="Minimize assistant" type="button" title="Minimize">—</button>
        <button class="chat-close" aria-label="Close assistant chat" type="button">×</button>
      </div>
    </div>
    <div class="chat-messages" aria-live="polite" aria-atomic="false" role="log"></div>
    <div class="chat-input-row">
      <input type="text" class="chat-input"
             placeholder="Ask about our collections…"
             aria-label="Message to SkyyRose assistant"
             autocomplete="off"
             maxlength="500"/>
      <button class="chat-send" aria-label="Send message" type="button">→</button>
    </div>
  </div>

  <!-- Mini bubble (proactive messages) -->
  <div class="avatar-bubble" role="status" aria-live="polite" aria-hidden="true"></div>

  <!-- Toggle button — Skyy face -->
  <button class="avatar-toggle"
          aria-label="Open SkyyRose fashion assistant"
          aria-expanded="false"
          type="button">
    <img class="avatar-toggle-face"
         src="assets/images/avatar/skyy.png"
         alt="" draggable="false">
  </button>

  <!-- Screen reader live region -->
  <div class="sr-only" aria-live="assertive" aria-atomic="true" id="avatar-sr-live"></div>
</div>
      `.trim();
    }

    _buildAvatarCSS() {
      return `
/* ============================================================
   SkyyRose Avatar Assistant — Injected Styles
   ============================================================ */

:root {
  --avatar-accent:       #c9a96e;
  --avatar-hair:         #1a0a00;
  --avatar-skin:         #f5cba7;
  --avatar-outfit-base:  #2c2c2c;
  --avatar-outfit-lower: #1a1a1a;
}

/* ── Wrapper ── */
#skyyrose-avatar {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  font-family: 'Georgia', 'Times New Roman', serif;
  /* Walk-in start state */
  transform: translateY(110%);
  opacity: 0;
  transition: transform 0.9s cubic-bezier(0.22, 1, 0.36, 1),
              opacity 0.6s ease;
}

/* Walk-in complete */
#skyyrose-avatar.avatar-entered {
  transform: translateY(0);
  opacity: 1;
}

#skyyrose-avatar.avatar-hidden {
  display: none;
}

/* ── Figure ── */
.avatar-figure {
  position: relative;
  width: 160px;
  cursor: pointer;
  opacity: 0.92;
  transition: opacity 0.3s ease;
  filter: drop-shadow(0 6px 18px rgba(0,0,0,0.5));
}

.avatar-figure:hover,
#skyyrose-avatar:focus .avatar-figure {
  opacity: 1;
}

/* Real Skyy mascot image */
.avatar-img {
  width: 100%;
  height: auto;
  display: block;
  mix-blend-mode: multiply;   /* white bg vanishes on dark room backgrounds */
  border-radius: 0;
  transition: filter 0.3s ease;
}

/* Thinking spinner overlay */
.skyy-spinner {
  position: absolute;
  top: 6px;
  left: 50%;
  transform: translateX(-50%);
  width: 64px;
  height: 64px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
}

.skyy-spinner svg {
  width: 100%;
  height: 100%;
}

/* ── Outfit badge ── */
.avatar-outfit-badge {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 8px;
  letter-spacing: 1px;
  color: var(--avatar-accent);
  text-transform: uppercase;
  white-space: nowrap;
  text-shadow: 0 1px 4px rgba(0,0,0,0.7);
}

/* ── Toggle button — Skyy face (only shown when minimized) ── */
.avatar-toggle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: 2.5px solid var(--avatar-accent);
  background: #1a0a00;
  cursor: pointer;
  display: none;  /* hidden by default — full body is the click target */
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(201,169,110,0.35);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  padding: 0;
  overflow: hidden;
}

/* Show toggle only in minimized state */
#skyyrose-avatar.avatar-minimized .avatar-toggle {
  display: flex;
}

/* Hide full body when minimized */
#skyyrose-avatar.avatar-minimized .avatar-figure {
  display: none;
}

.avatar-toggle:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 28px rgba(201,169,110,0.55);
}

.avatar-toggle:focus-visible {
  outline: 2px solid var(--avatar-accent);
  outline-offset: 3px;
}

/* Circular face crop — shows Skyy's face in the toggle button */
.avatar-toggle-face {
  width: 200%;
  height: 200%;
  object-fit: cover;
  object-position: 40% 12%;
  mix-blend-mode: multiply;
  margin-left: -50%;
  margin-top: -40%;
}

/* ── Mini bubble ── */
.avatar-bubble {
  position: absolute;
  bottom: 240px;
  right: 0;
  background: rgba(20,10,5,0.95);
  border: 1px solid var(--avatar-accent);
  border-radius: 14px 14px 0 14px;
  color: #f0e6d3;
  font-size: 12px;
  line-height: 1.5;
  max-width: 220px;
  padding: 10px 14px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.4);
  opacity: 0;
  transform: translateY(10px);
  pointer-events: none;
  transition: opacity 0.35s ease, transform 0.35s ease;
}

.avatar-bubble.bubble-visible {
  opacity: 1;
  transform: translateY(0);
}

/* ── Chat panel ── */
.avatar-chat {
  position: absolute;
  bottom: 70px;
  right: 0;
  width: 320px;
  max-height: 480px;
  background: rgba(12,6,3,0.97);
  border: 1px solid var(--avatar-accent);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(201,169,110,0.15);
  overflow: hidden;
  animation: chatFadeIn 0.3s ease;
}

.avatar-chat[hidden] {
  display: none;
}

@keyframes chatFadeIn {
  from { opacity: 0; transform: translateY(10px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(201,169,110,0.2);
  background: rgba(30,15,8,0.9);
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-rose-icon {
  font-size: 16px;
}

.chat-title {
  color: var(--avatar-accent);
  font-size: 13px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}

.chat-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.chat-minimize,
.chat-close {
  background: none;
  border: none;
  color: rgba(201,169,110,0.6);
  font-size: 18px;
  cursor: pointer;
  padding: 0 5px;
  line-height: 1;
  transition: color 0.2s;
}

.chat-minimize:hover,
.chat-close:hover { color: var(--avatar-accent); }

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scrollbar-width: thin;
  scrollbar-color: rgba(201,169,110,0.3) transparent;
}

.chat-messages::-webkit-scrollbar        { width: 4px; }
.chat-messages::-webkit-scrollbar-thumb  { background: rgba(201,169,110,0.3); border-radius: 4px; }

.chat-message {
  max-width: 85%;
  padding: 9px 13px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.55;
  animation: msgSlideIn 0.25s ease;
}

@keyframes msgSlideIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

.chat-message.role-user {
  align-self: flex-end;
  background: var(--avatar-accent);
  color: #0d0600;
  border-bottom-right-radius: 3px;
}

.chat-message.role-assistant {
  align-self: flex-start;
  background: rgba(40,20,10,0.9);
  border: 1px solid rgba(201,169,110,0.2);
  color: #f0e6d3;
  border-bottom-left-radius: 3px;
}

.chat-input-row {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid rgba(201,169,110,0.15);
  background: rgba(20,10,5,0.8);
}

.chat-input {
  flex: 1;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(201,169,110,0.25);
  border-radius: 20px;
  color: #f0e6d3;
  font-size: 13px;
  padding: 8px 14px;
  outline: none;
  font-family: inherit;
  transition: border-color 0.2s;
}

.chat-input:focus {
  border-color: var(--avatar-accent);
}

.chat-input::placeholder { color: rgba(201,169,110,0.4); }

.chat-send {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--avatar-accent);
  color: #0d0600;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.2s, background 0.2s;
}

.chat-send:hover { transform: scale(1.1); }
.chat-send:active { transform: scale(0.95); }

/* ── Screen reader only ── */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
  white-space: nowrap;
  border: 0;
}

/* ============================================================
   ANIMATION STATES
   ============================================================ */

/* -- Idle: breathing -- */
@keyframes breathe {
  0%,100% { transform: scale(1); }
  50%      { transform: scale(1.03); }
}

#skyyrose-avatar.idle .avatar-figure {
  animation: breathe 3s ease-in-out infinite;
}

/* -- Thinking: spinner overlay -- */
@keyframes spin-pulse {
  0%   { transform: translateX(-50%) rotate(0deg)   scale(1);    opacity: 0.6; }
  50%  { transform: translateX(-50%) rotate(180deg) scale(1.1);  opacity: 1; }
  100% { transform: translateX(-50%) rotate(360deg) scale(1);    opacity: 0.6; }
}

#skyyrose-avatar.thinking .skyy-spinner {
  opacity: 1;
  animation: spin-pulse 1.2s ease-in-out infinite;
}

#skyyrose-avatar.thinking .avatar-figure {
  animation: none;
}

/* -- Talking: subtle glow pulse on image -- */
@keyframes skyy-talk {
  0%,100% { filter: drop-shadow(0 6px 18px rgba(0,0,0,0.5)); }
  50%     { filter: drop-shadow(0 6px 24px rgba(201,169,110,0.45)); }
}

#skyyrose-avatar.talking .avatar-figure {
  animation: skyy-talk 0.5s ease-in-out infinite;
}

/* -- Pointing: Skyy is already in presenting pose — gentle pulse -- */
@keyframes skyy-point {
  0%,100% { transform: scale(1); }
  50%     { transform: scale(1.02) translateX(-2px); }
}

#skyyrose-avatar.pointing .avatar-figure {
  animation: skyy-point 0.6s ease-in-out infinite;
}

/* -- Celebrating: bounce -- */
@keyframes bounce {
  0%,100% { transform: translateY(0); }
  40%     { transform: translateY(-12px); }
  60%     { transform: translateY(-8px); }
}

#skyyrose-avatar.celebrating .avatar-figure {
  animation: bounce 0.5s ease-in-out 3;
}

/* ============================================================
   COLLECTION ROOM ACCENTS
   ============================================================ */

#skyyrose-avatar.room-black-rose  { --avatar-accent: #c0392b; --avatar-outfit-base: #111; }
#skyyrose-avatar.room-love-hurts  { --avatar-accent: #e74c8b; --avatar-outfit-base: #1a0a14; }
#skyyrose-avatar.room-signature   { --avatar-accent: #b57bee; --avatar-outfit-base: #0d0820; }

/* ============================================================
   REDUCED MOTION
   ============================================================ */

@media (prefers-reduced-motion: reduce) {
  .avatar-figure,
  .avatar-mouth,
  .arm-group,
  .think-spinner,
  .avatar-bubble,
  .avatar-chat,
  .chat-message {
    animation: none !important;
    transition: none !important;
  }
}

/* ============================================================
   RESPONSIVE
   ============================================================ */

@media (max-width: 400px) {
  #skyyrose-avatar { bottom: 12px; right: 12px; }
  .avatar-chat { width: calc(100vw - 24px); right: -12px; }
}
      `.trim();
    }

    // -------------------------------------------------------------------------
    // Private: DOM injection
    // -------------------------------------------------------------------------

    _injectCSS() {
      if (document.getElementById('skyyrose-avatar-styles')) return;
      const style = document.createElement('style');
      style.id = 'skyyrose-avatar-styles';
      style.textContent = this._buildAvatarCSS();
      document.head.appendChild(style);
    }

    _injectHTML() {
      const container = document.createElement('div');
      container.innerHTML = this._buildAvatarHTML();
      document.body.appendChild(container.firstElementChild);
    }

    _cacheRefs() {
      this._root        = document.getElementById('skyyrose-avatar');
      this._figure      = this._root.querySelector('.avatar-figure');
      this._chatPanel   = this._root.querySelector('.avatar-chat');
      this._messagesDiv = this._root.querySelector('.chat-messages');
      this._inputEl     = this._root.querySelector('.chat-input');
      this._toggleBtn   = this._root.querySelector('.avatar-toggle');
      this._outfitBadge = this._root.querySelector('.avatar-outfit-badge');
      this._armEl       = this._root.querySelector('.arm-group');
      this._mouthEl     = this._root.querySelector('.avatar-mouth');
      this._bubbleEl    = this._root.querySelector('.avatar-bubble');
      this._srLive      = this._root.querySelector('#avatar-sr-live');
    }

    // -------------------------------------------------------------------------
    // Private: events
    // -------------------------------------------------------------------------

    _bindEvents() {
      // Toggle open/close on button or figure click
      this._toggleBtn.addEventListener('click', () => this._toggleChat());
      this._figure.addEventListener('click', () => this._toggleChat());

      // Minimize button — collapses to circle toggle
      this._root.querySelector('.chat-minimize').addEventListener('click', () => this._minimizeAvatar());

      // Close button
      this._root.querySelector('.chat-close').addEventListener('click', () => this._closeChat());

      // Send on button or Enter
      this._root.querySelector('.chat-send').addEventListener('click', () => this._handleSend());
      this._inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this._handleSend();
        }
      });

      // Keyboard: root element
      this._root.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target === this._root) {
          this._openChat();
        }
        if (e.key === 'Escape') {
          this._closeChat();
        }
      });

      // Focus management
      this._root.addEventListener('focus', () => {
        this._root.style.outline = 'none';
      });
    }

    _handleSend() {
      const msg = (this._inputEl.value || '').trim();
      if (!msg) return;
      this._inputEl.value = '';
      this._openChat();
      this.chat(msg);
    }

    // -------------------------------------------------------------------------
    // Private: chat open/close
    // -------------------------------------------------------------------------

    _openChat() {
      if (this._chatOpen) return;
      this._chatOpen = true;
      this._chatPanel.removeAttribute('hidden');
      this._toggleBtn.setAttribute('aria-expanded', 'true');
      this._toggleBtn.setAttribute('aria-label', 'Close SkyyRose assistant');

      // Welcome if first time
      if (this._history.length === 0) {
        this.displayMessage(
          'Hello! I\'m your SkyyRose style guide. Which collection are you exploring today — Black Rose, Love Hurts, or Signature? 🌹',
          'assistant'
        );
      }

      setTimeout(() => this._inputEl && this._inputEl.focus(), 100);
    }

    _closeChat() {
      if (!this._chatOpen) return;
      this._chatOpen = false;
      this._chatPanel.setAttribute('hidden', '');
      this._toggleBtn.setAttribute('aria-expanded', 'false');
      this._toggleBtn.setAttribute('aria-label', 'Open SkyyRose assistant');
      this._toggleBtn.focus();
    }

    _toggleChat() {
      if (this._root && this._root.classList.contains('avatar-minimized')) {
        this._restoreAvatar();
        return;
      }
      this._chatOpen ? this._closeChat() : this._openChat();
    }

    _minimizeAvatar() {
      this._closeChat();
      if (this._root) {
        this._root.classList.add('avatar-minimized');
        this._toggleBtn.setAttribute('aria-label', 'Restore SkyyRose assistant');
      }
    }

    _restoreAvatar() {
      if (this._root) {
        this._root.classList.remove('avatar-minimized');
        this._toggleBtn.setAttribute('aria-label', 'Open SkyyRose fashion assistant');
      }
      this._openChat();
    }

    // -------------------------------------------------------------------------
    // Private: messaging helpers
    // -------------------------------------------------------------------------

    _appendMessageEl(role) {
      const el = document.createElement('div');
      el.className = `chat-message role-${role}`;
      this._messagesDiv.appendChild(el);
      this._scrollMessages();
      return el;
    }

    _scrollMessages() {
      if (this._messagesDiv) {
        this._messagesDiv.scrollTop = this._messagesDiv.scrollHeight;
      }
    }

    _showBubble(text, durationMs = 3000) {
      if (!this._bubbleEl) return;
      this._bubbleEl.textContent = text;
      this._bubbleEl.setAttribute('aria-hidden', 'false');
      this._bubbleEl.classList.add('bubble-visible');

      setTimeout(() => {
        if (this._bubbleEl) {
          this._bubbleEl.classList.remove('bubble-visible');
          this._bubbleEl.setAttribute('aria-hidden', 'true');
        }
      }, durationMs);
    }

    // -------------------------------------------------------------------------
    // Private: product link parsing
    // -------------------------------------------------------------------------

    _triggerProductLinks(text) {
      // Match [PRODUCT:id] markers in assistant response
      const re = /\[PRODUCT:([^\]]+)\]/g;
      let match;
      while ((match = re.exec(text)) !== null) {
        const id = match[1].trim();
        setTimeout(() => this.pointAt(id), 600);
      }
    }

    // -------------------------------------------------------------------------
    // Private: accessibility
    // -------------------------------------------------------------------------

    _announceToScreenReader(text) {
      if (!this._srLive) return;
      // Briefly clear then set — forces re-announcement
      this._srLive.textContent = '';
      requestAnimationFrame(() => {
        this._srLive.textContent = text;
      });
    }

    _detectReducedMotion() {
      if (global.a11y && global.a11y.reducedMotion === true) return true;
      if (global.matchMedia) {
        return global.matchMedia('(prefers-reduced-motion: reduce)').matches;
      }
      return false;
    }

    // -------------------------------------------------------------------------
    // Private: room label
    // -------------------------------------------------------------------------

    _roomLabel(room) {
      const labels = {
        'black-rose':  'BLACK ROSE',
        'love-hurts':  'LOVE HURTS',
        'signature':   'SIGNATURE',
      };
      return labels[room] || '';
    }
  }

  // ---------------------------------------------------------------------------
  // Export and auto-init
  // ---------------------------------------------------------------------------

  global.AvatarAssistant = AvatarAssistant;

  // Auto-init after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _autoInit);
  } else {
    _autoInit();
  }

  function _autoInit() {
    global.avatar = new AvatarAssistant();
    global.avatar.init();
  }

})(typeof window !== 'undefined' ? window : globalThis);
