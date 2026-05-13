/**
 * Garment Upload Gate — UI controller for the [skyyrose_garment_upload] form.
 *
 * Wires file input -> preview -> classifier -> verdict -> submit gate.
 * Submit is disabled until the classifier returns accepted=true. On success,
 * the file + verdict are forwarded to the form's data-endpoint via FormData.
 *
 * Accessibility:
 *   - role="status" on verdict announce live changes to assistive tech.
 *   - aria-busy reflects classifier in-flight.
 *   - All controls keyboard-reachable; preview has alt text.
 *
 * @package SkyyRose
 * @since   1.1.0
 */

import { classifyGarment, disposeClassifier } from './garment-classifier.js';

const SELECTORS = Object.freeze({
  root: '[data-skyyrose-upload-gate]',
  fileInput: '[data-upload-file]',
  preview: '[data-upload-preview]',
  status: '[data-upload-status]',
  verdict: '[data-upload-verdict]',
  submit: '[data-upload-submit]',
  progress: '[data-upload-progress]',
  reset: '[data-upload-reset]',
});

const MAX_BYTES = 12 * 1024 * 1024; // 12 MB
const ALLOWED_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);

/**
 * @typedef {Object} GateState
 * @property {File|null} file
 * @property {object|null} verdict
 * @property {'idle'|'loading'|'classifying'|'accepted'|'rejected'|'error'} phase
 */

class UploadGate {
  /**
   * @param {HTMLElement} root - the [data-skyyrose-upload-gate] container
   * @param {object} settings - injected via wp_localize_script
   */
  constructor(root, settings) {
    this.root = root;
    this.settings = settings;
    this.state = { file: null, verdict: null, phase: 'idle' };

    this.els = {
      fileInput: root.querySelector(SELECTORS.fileInput),
      preview: root.querySelector(SELECTORS.preview),
      status: root.querySelector(SELECTORS.status),
      verdict: root.querySelector(SELECTORS.verdict),
      submit: root.querySelector(SELECTORS.submit),
      progress: root.querySelector(SELECTORS.progress),
      reset: root.querySelector(SELECTORS.reset),
    };

    if (!this.els.fileInput || !this.els.submit) {
      throw new Error('UploadGate: required controls missing');
    }

    this.bindEvents();
    this.applyPhase('idle');
  }

  bindEvents() {
    this.els.fileInput.addEventListener('change', (e) => this.onFileChange(e));
    this.els.submit.addEventListener('click', (e) => this.onSubmit(e));
    if (this.els.reset) {
      this.els.reset.addEventListener('click', () => this.reset());
    }
    window.addEventListener('beforeunload', () => disposeClassifier());
  }

  /**
   * Validate file at the boundary before any model work.
   *
   * @param {File} file
   * @returns {string|null} error message, or null on valid
   */
  validateFile(file) {
    if (!ALLOWED_TYPES.has(file.type)) {
      return 'Use JPEG, PNG, or WebP.';
    }
    if (file.size > MAX_BYTES) {
      return `File is too large. Max ${MAX_BYTES / (1024 * 1024)} MB.`;
    }
    if (file.size < 4 * 1024) {
      return 'Image is too small. Try a clearer reference.';
    }
    return null;
  }

  async onFileChange(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    const validationError = this.validateFile(file);
    if (validationError) {
      this.applyPhase('error', validationError);
      this.els.fileInput.value = '';
      return;
    }

    this.state.file = file;
    this.renderPreview(file);
    this.applyPhase('loading');

    try {
      const verdict = await classifyGarment(file, (info) => this.onModelProgress(info));
      this.state.verdict = verdict;
      this.applyPhase(verdict.accepted ? 'accepted' : 'rejected');
    } catch (err) {
      console.error('[skyyrose] classifier failed', err);
      this.applyPhase('error', 'Classifier failed. Refresh and try again.');
    }
  }

  /**
   * Forward the file and verdict to the configured endpoint. The endpoint
   * itself is not part of this module — the WP admin or shortcode caller
   * supplies it via data-endpoint.
   */
  async onSubmit(event) {
    event.preventDefault();
    if (this.state.phase !== 'accepted' || !this.state.file || !this.state.verdict) {
      return;
    }

    const endpoint = this.root.dataset.endpoint;
    if (!endpoint) {
      console.warn('[skyyrose] no endpoint configured; verdict only', this.state.verdict);
      this.dispatchEvent('skyyrose:upload-accepted', this.state.verdict);
      return;
    }

    const formData = new FormData();
    formData.append('image', this.state.file);
    formData.append('category', this.state.verdict.category);
    formData.append('confidence', String(this.state.verdict.confidence));
    formData.append('_wpnonce', this.settings.nonce || '');

    this.applyPhase('classifying', 'Sending…');
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      this.dispatchEvent('skyyrose:upload-accepted', this.state.verdict);
      this.applyPhase('accepted', 'Sent.');
    } catch (err) {
      console.error('[skyyrose] upload failed', err);
      this.applyPhase('error', 'Upload failed. Try again.');
    }
  }

  onModelProgress(info) {
    if (!this.els.progress) return;
    if (info.status === 'progress' && typeof info.progress === 'number') {
      this.els.progress.value = info.progress;
      this.setStatus(`Loading vision model… ${info.progress.toFixed(0)}%`);
    } else if (info.status === 'ready') {
      this.els.progress.value = 100;
    }
  }

  renderPreview(file) {
    if (!this.els.preview) return;
    const url = URL.createObjectURL(file);
    this.els.preview.src = url;
    this.els.preview.alt = `Uploaded preview: ${file.name}`;
    this.els.preview.addEventListener('load', () => URL.revokeObjectURL(url), { once: true });
  }

  applyPhase(phase, message) {
    this.state.phase = phase;
    this.root.dataset.phase = phase;
    this.root.setAttribute('aria-busy', phase === 'loading' || phase === 'classifying');
    this.els.submit.disabled = phase !== 'accepted';

    const label = message || this.defaultMessage(phase);
    this.setStatus(label);

    if (phase === 'accepted' || phase === 'rejected') {
      this.renderVerdict(this.state.verdict);
    } else if (phase === 'idle') {
      this.clearVerdict();
    }
  }

  defaultMessage(phase) {
    return {
      idle: 'Choose a garment image to begin.',
      loading: 'Loading vision model… (one-time download)',
      classifying: 'Analyzing image…',
      accepted: 'Looks good. You can submit.',
      rejected: 'This image cannot be used. Try a clearer garment shot.',
      error: 'Something went wrong.',
    }[phase] || '';
  }

  setStatus(text) {
    if (this.els.status) this.els.status.textContent = text;
  }

  renderVerdict(verdict) {
    if (!this.els.verdict || !verdict) return;
    this.els.verdict.replaceChildren();

    const reason = document.createElement('p');
    reason.className = 'sr-upload__reason';
    reason.textContent = verdict.reason;
    this.els.verdict.appendChild(reason);

    if (verdict.category) {
      const cat = document.createElement('p');
      cat.className = 'sr-upload__category';
      cat.textContent = `Detected: ${verdict.category} (${(verdict.confidence * 100).toFixed(0)}% confidence)`;
      this.els.verdict.appendChild(cat);
    }
  }

  clearVerdict() {
    if (this.els.verdict) this.els.verdict.replaceChildren();
  }

  reset() {
    this.state = { file: null, verdict: null, phase: 'idle' };
    this.els.fileInput.value = '';
    if (this.els.preview) this.els.preview.removeAttribute('src');
    if (this.els.progress) this.els.progress.value = 0;
    this.applyPhase('idle');
  }

  dispatchEvent(name, detail) {
    this.root.dispatchEvent(new CustomEvent(name, { detail, bubbles: true }));
  }
}

function init() {
  const settings = window.skyyroseUploadGate || {};
  document.querySelectorAll(SELECTORS.root).forEach((root) => {
    if (root.dataset.initialized === '1') return;
    try {
      // eslint-disable-next-line no-new
      new UploadGate(root, settings);
      root.dataset.initialized = '1';
    } catch (err) {
      console.error('[skyyrose] upload gate init failed', err);
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

export { UploadGate };
