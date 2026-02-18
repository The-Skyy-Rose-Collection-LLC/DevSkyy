/**
 * SkyyRose Experience - Main Application
 * Immersive luxury fashion virtual showroom
 */

// State
let currentRoomIndex = 0;
let imageToggle = true; // Toggle between scene-a and scene-b for crossfade
let loadedImages = new Set();
let isModalOpen = false;

// DOM Elements
const loader = document.getElementById('loader');
const loaderBar = document.getElementById('loaderBar');
const loaderText = document.getElementById('loaderText');

const sceneAImg = document.getElementById('sceneAImg');
const sceneAWebp = document.getElementById('sceneAWebp');
const sceneBImg = document.getElementById('sceneBImg');
const sceneBWebp = document.getElementById('sceneBWebp');
const sceneA = document.querySelector('.scene-a');
const sceneB = document.querySelector('.scene-b');

const hotspotsContainer = document.getElementById('hotspots');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const prevLabel = document.getElementById('prevLabel');
const nextLabel = document.getElementById('nextLabel');
const pipNav = document.getElementById('pipNav');

const exploreBtn = document.getElementById('exploreBtn');
const exploreClose = document.getElementById('exploreClose');
const exploreSidebar = document.getElementById('exploreSidebar');
const exploreList = document.querySelector('.explore-list');

const modal = document.getElementById('productModal');
const modalBackdrop = document.getElementById('modalBackdrop');
const modalClose = document.getElementById('modalClose');
const announcements = document.getElementById('announcements');

// Modal elements
const modalImage = document.getElementById('modalImage');
const modalBadge = document.getElementById('modalBadge');
const modalCollection = document.getElementById('modalCollection');
const modalTitle = document.getElementById('modalTitle');
const modalTagline = document.getElementById('modalTagline');
const modalDescription = document.getElementById('modalDescription');
const modalSpec = document.getElementById('modalSpec');
const modalPrice = document.getElementById('modalPrice');
const modalVariants = document.getElementById('modalVariants');
const sizeSelect = document.getElementById('sizeSelect');
const colorSwatches = document.getElementById('colorSwatches');
const addToCartBtn = document.getElementById('addToCartBtn');
const preOrderBtn = document.getElementById('preOrderBtn');

/**
 * Initialize the application
 */
function init() {
  console.log('🌹 SkyyRose Experience Initializing...');

  // Set up event listeners
  setupEventListeners();

  // Build explore sidebar
  buildExploreSidebar();

  // Build pip navigation
  buildPipNavigation();

  // Load images
  loadAllImages();

  // Feature modules auto-initialize via their own scripts (window.a11y,
  // window.gestures, window.wishlist, window.analytics, window.sharing,
  // window.avatar). gestures.js calls window.next / window.prev which are
  // top-level function declarations and therefore accessible as globals here.

  // Fire session_start analytics event once modules are ready
  if (window.analytics) {
    window.analytics.track('session_start', {
      device_type: window.innerWidth < 768 ? 'mobile' : 'desktop',
    });
  }
}

/**
 * Set up all event listeners
 */
function setupEventListeners() {
  // Navigation
  prevBtn.addEventListener('click', prev);
  nextBtn.addEventListener('click', next);

  // Explore sidebar
  exploreBtn.addEventListener('click', toggleExplore);
  exploreClose.addEventListener('click', toggleExplore);
  modalBackdrop.addEventListener('click', closeModal);

  // Modal
  modalClose.addEventListener('click', closeModal);
  modalBackdrop.addEventListener('click', closeModal);

  // Cart buttons
  addToCartBtn.addEventListener('click', () => handleAddToCart('cart'));
  preOrderBtn.addEventListener('click', () => handleAddToCart('preorder'));

  // Keyboard navigation
  document.addEventListener('keydown', handleKeyboard);

  // Prevent focus trap in modal
  modal.addEventListener('keydown', handleModalKeyboard);
}

/**
 * Build explore sidebar items
 */
function buildExploreSidebar() {
  exploreList.innerHTML = '';

  CONFIG.rooms.forEach((room, index) => {
    const item = document.createElement('button');
    item.className = 'explore-item';
    item.setAttribute('role', 'button');
    item.setAttribute('aria-label', `View ${room.name} - ${room.collection} collection with ${room.hotspots.length} products`);

    if (index === currentRoomIndex) {
      item.classList.add('active');
      item.setAttribute('aria-current', 'true');
    }

    item.innerHTML = `
      <div class="explore-item-collection" style="color: ${room.accent}">${room.collection}</div>
      <div class="explore-item-name">${room.name}</div>
      <div class="explore-item-count">${room.hotspots.length} ${room.hotspots.length === 1 ? 'product' : 'products'}</div>
    `;

    item.addEventListener('click', () => {
      goToRoom(index);
      toggleExplore();
    });

    exploreList.appendChild(item);
  });
}

/**
 * Build pip navigation dots
 */
function buildPipNavigation() {
  pipNav.innerHTML = '';

  CONFIG.rooms.forEach((room, index) => {
    const pip = document.createElement('button');
    pip.className = 'pip';
    pip.setAttribute('aria-label', `Go to ${room.name}`);

    if (index === currentRoomIndex) {
      pip.classList.add('active');
      pip.setAttribute('aria-current', 'true');
    }

    // Tooltip label
    const label = document.createElement('span');
    label.className = 'pip-label';
    label.textContent = room.name;
    label.setAttribute('aria-hidden', 'true');
    pip.appendChild(label);

    pip.addEventListener('click', () => goToRoom(index));

    pipNav.appendChild(pip);
  });
}

/**
 * Load all scene images with progress
 */
async function loadAllImages() {
  const rooms = CONFIG.rooms;
  const totalImages = rooms.length;
  let loadedCount = 0;

  console.log(`📸 Loading ${totalImages} scene images...`);

  for (const room of rooms) {
    try {
      loaderText.textContent = `Loading ${room.collection}...`;

      // Determine if mobile
      const isMobile = window.innerWidth <= 768;
      const imageSet = isMobile ? CONFIG.images[room.id].mobile : CONFIG.images[room.id];

      // Preload image
      await preloadImage(imageSet.jpeg);
      loadedImages.add(room.id);

      loadedCount++;
      const progress = (loadedCount / totalImages) * 100;
      loaderBar.style.width = `${progress}%`;

      console.log(`✓ Loaded: ${room.collection} (${progress.toFixed(0)}%)`);
    } catch (error) {
      console.error(`✗ Failed to load: ${room.collection}`, error);
    }
  }

  // All images loaded
  console.log('✓ All images loaded');
  loaderText.textContent = 'Experience ready...';

  // Small delay for smooth transition
  setTimeout(() => {
    hideLoader();
    renderRoom(currentRoomIndex);
  }, 500);
}

/**
 * Preload a single image
 */
function preloadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

/**
 * Hide loader and show experience
 */
function hideLoader() {
  loader.classList.add('hidden');

  // Remove from DOM after transition
  setTimeout(() => {
    loader.style.display = 'none';
  }, 600);
}

/**
 * Render a room by index
 */
function renderRoom(index) {
  const room = CONFIG.rooms[index];
  console.log(`🎨 Rendering: ${room.name}`);

  // Update document title and meta
  document.title = `${room.name} - ${room.collection} | SkyyRose`;

  // Determine scene elements
  const activeScene = imageToggle ? sceneA : sceneB;
  const nextScene = imageToggle ? sceneB : sceneA;
  const activeImg = imageToggle ? sceneAImg : sceneBImg;
  const activeWebp = imageToggle ? sceneAWebp : sceneBWebp;

  // Determine if mobile
  const isMobile = window.innerWidth <= 768;
  const imageSet = isMobile ? CONFIG.images[room.id].mobile : CONFIG.images[room.id];

  // Set image sources
  activeWebp.srcset = imageSet.webp;
  activeImg.src = imageSet.jpeg;
  activeImg.alt = `${room.name} - ${room.collection} collection showroom`;

  // Crossfade transition
  activeScene.classList.remove('out');
  nextScene.classList.add('out');
  imageToggle = !imageToggle;

  // Render hotspots
  renderHotspots(room);

  // Update navigation
  updateNavigation();

  // Update pip navigation
  updatePipNavigation();

  // Update explore sidebar
  updateExploreSidebar();

  // Announce to screen readers
  announce(`Now viewing ${room.name}. ${room.collection} collection. ${room.hotspots.length} products available.`);
}

/**
 * Render product hotspots for a room
 */
function renderHotspots(room) {
  hotspotsContainer.innerHTML = '';

  room.hotspots.forEach((hotspot, index) => {
    const el = document.createElement('button');
    el.className = 'hotspot';
    el.style.left = `${hotspot.x}%`;
    el.style.top = `${hotspot.y}%`;
    el.setAttribute('role', 'button');
    el.setAttribute('aria-label', `View ${hotspot.product.name}`);

    el.innerHTML = `
      <div class="hotspot-dot"></div>
      <span class="hotspot-label">${hotspot.product.name}</span>
    `;

    el.addEventListener('click', () => openModal(hotspot.product, room));

    hotspotsContainer.appendChild(el);
  });

  console.log(`✓ Rendered ${room.hotspots.length} hotspots`);
}

/**
 * Update navigation arrow labels
 */
function updateNavigation() {
  const prevIndex = (currentRoomIndex - 1 + CONFIG.rooms.length) % CONFIG.rooms.length;
  const nextIndex = (currentRoomIndex + 1) % CONFIG.rooms.length;

  prevLabel.textContent = CONFIG.rooms[prevIndex].name;
  nextLabel.textContent = CONFIG.rooms[nextIndex].name;

  prevBtn.setAttribute('aria-label', `Previous room: ${CONFIG.rooms[prevIndex].name}`);
  nextBtn.setAttribute('aria-label', `Next room: ${CONFIG.rooms[nextIndex].name}`);
}

/**
 * Update pip navigation active state
 */
function updatePipNavigation() {
  const pips = pipNav.querySelectorAll('.pip');
  pips.forEach((pip, index) => {
    if (index === currentRoomIndex) {
      pip.classList.add('active');
      pip.setAttribute('aria-current', 'true');
    } else {
      pip.classList.remove('active');
      pip.removeAttribute('aria-current');
    }
  });
}

/**
 * Update explore sidebar active state
 */
function updateExploreSidebar() {
  const items = exploreList.querySelectorAll('.explore-item');
  items.forEach((item, index) => {
    if (index === currentRoomIndex) {
      item.classList.add('active');
      item.setAttribute('aria-current', 'true');
    } else {
      item.classList.remove('active');
      item.removeAttribute('aria-current');
    }
  });
}

/**
 * Navigate to a specific room
 */
function goToRoom(index) {
  if (index === currentRoomIndex) return;

  currentRoomIndex = index;
  renderRoom(currentRoomIndex);
}

/**
 * Navigate to previous room
 */
function prev() {
  const prevIndex = (currentRoomIndex - 1 + CONFIG.rooms.length) % CONFIG.rooms.length;
  goToRoom(prevIndex);
}

/**
 * Navigate to next room
 */
function next() {
  const nextIndex = (currentRoomIndex + 1) % CONFIG.rooms.length;
  goToRoom(nextIndex);
}

/**
 * Toggle explore sidebar
 */
function toggleExplore() {
  const isOpen = exploreSidebar.classList.toggle('open');
  exploreBtn.setAttribute('aria-expanded', isOpen);

  if (isOpen) {
    announce('Explore sidebar opened');
  } else {
    announce('Explore sidebar closed');
  }
}

/**
 * Open product modal
 */
function openModal(product, room) {
  console.log(`🛍️ Opening modal: ${product.name}`);

  isModalOpen = true;
  modal.removeAttribute('hidden');

  // Populate modal content
  modalImage.src = product.image;
  modalImage.alt = product.name;

  if (product.badge) {
    modalBadge.textContent = product.badge;
    modalBadge.style.display = 'inline-block';
  } else {
    modalBadge.style.display = 'none';
  }

  modalCollection.textContent = product.collection;
  modalCollection.style.color = room.accent;
  modalTitle.textContent = product.name;
  modalTagline.textContent = product.tagline;
  modalDescription.textContent = product.description;
  modalSpec.textContent = product.spec;
  modalPrice.textContent = product.price;

  // Populate variants if available
  if (product.variants) {
    modalVariants.removeAttribute('hidden');

    // Sizes
    sizeSelect.innerHTML = '<option value="">Select size</option>';
    product.variants.sizes.forEach(size => {
      const option = document.createElement('option');
      option.value = size;
      option.textContent = size;
      sizeSelect.appendChild(option);
    });

    // Colors
    colorSwatches.innerHTML = '';
    product.variants.colors.forEach(color => {
      const swatch = document.createElement('button');
      swatch.className = 'color-swatch';
      swatch.style.background = color.hex;
      swatch.setAttribute('aria-label', color.name);
      swatch.setAttribute('title', color.name);
      swatch.addEventListener('click', () => selectColor(swatch));
      colorSwatches.appendChild(swatch);
    });

    // Select first color by default
    if (colorSwatches.firstChild) {
      colorSwatches.firstChild.classList.add('active');
    }
  } else {
    modalVariants.setAttribute('hidden', '');
  }

  // Update button URLs
  preOrderBtn.onclick = () => window.location.href = product.url;

  // Focus modal for keyboard navigation
  setTimeout(() => {
    modalClose.focus();
  }, 100);

  // Announce to screen readers
  announce(`Product details for ${product.name}. ${product.price}. ${product.description}`);
}

/**
 * Close product modal
 */
function closeModal() {
  if (!isModalOpen) return;

  console.log('✕ Closing modal');

  isModalOpen = false;
  modal.setAttribute('hidden', '');

  // Reset variant selections
  sizeSelect.value = '';
  colorSwatches.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('active'));

  announce('Product details closed');
}

/**
 * Select color swatch
 */
function selectColor(swatch) {
  colorSwatches.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('active'));
  swatch.classList.add('active');
}

/**
 * Handle add to cart
 */
function handleAddToCart(type) {
  const selectedSize = sizeSelect.value;
  const selectedColor = colorSwatches.querySelector('.color-swatch.active');

  // Basic validation
  if (modalVariants.hasAttribute('hidden') === false) {
    if (!selectedSize) {
      alert('Please select a size');
      sizeSelect.focus();
      return;
    }
  }

  console.log(`🛒 Adding to ${type}:`, {
    product: modalTitle.textContent,
    size: selectedSize,
    color: selectedColor?.getAttribute('aria-label')
  });

  // TODO: Phase 3 - Integrate with WooCommerce API
  // For now, just show success message
  announce(`${modalTitle.textContent} added to ${type === 'cart' ? 'cart' : 'pre-order'}`);

  // Close modal after short delay
  setTimeout(closeModal, 1000);
}

/**
 * Keyboard navigation
 */
function handleKeyboard(e) {
  // Don't intercept if modal is open
  if (isModalOpen) return;

  switch (e.key) {
    case 'ArrowLeft':
      e.preventDefault();
      prev();
      break;
    case 'ArrowRight':
      e.preventDefault();
      next();
      break;
    case '1':
      e.preventDefault();
      goToRoom(0);
      break;
    case '2':
      e.preventDefault();
      if (CONFIG.rooms.length > 1) goToRoom(1);
      break;
    case '3':
      e.preventDefault();
      if (CONFIG.rooms.length > 2) goToRoom(2);
      break;
    case 'Escape':
      if (exploreSidebar.classList.contains('open')) {
        toggleExplore();
      }
      break;
  }
}

/**
 * Modal keyboard navigation (focus trap)
 */
function handleModalKeyboard(e) {
  if (e.key === 'Escape') {
    e.preventDefault();
    closeModal();
  }

  // Focus trap - keep focus within modal
  if (e.key === 'Tab') {
    const focusableElements = modal.querySelectorAll(
      'button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  }
}

/**
 * Announce to screen readers
 */
function announce(message) {
  announcements.textContent = message;

  // Clear after announcement
  setTimeout(() => {
    announcements.textContent = '';
  }, 1000);
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// ---------------------------------------------------------------------------
// Service Worker Registration
// ---------------------------------------------------------------------------

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => {
        console.log('[SW] Registered:', reg.scope);
        reg.addEventListener('updatefound', () => {
          const newWorker = reg.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              announce('Site update available — refresh to get the latest version.');
            }
          });
        });
      })
      .catch(err => console.warn('[SW] Registration failed:', err));
  });
}
