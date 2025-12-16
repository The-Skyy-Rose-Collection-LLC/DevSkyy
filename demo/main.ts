/**
 * SkyyRose Collection 3D Experience Demo Entry Point
 *
 * Interactive demo for previewing all collection experiences locally.
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import { createCollectionExperience } from '../src/collections/index';
import type {
  BlackRoseExperience,
  SignatureExperience,
  LoveHurtsExperience,
  ShowroomExperience,
  RunwayExperience,
} from '../src/collections/index';

type CollectionType = 'black_rose' | 'signature' | 'love_hurts' | 'showroom' | 'runway';
type ExperienceType = BlackRoseExperience | SignatureExperience | LoveHurtsExperience | ShowroomExperience | RunwayExperience;

let currentExperience: ExperienceType | null = null;
let currentCollection: CollectionType = 'black_rose';

// Sample products for demo
const DEMO_PRODUCTS = {
  black_rose: [
    { id: 'br-001', name: 'Obsidian Rose Dress', price: 299.99, category: 'dresses' },
    { id: 'br-002', name: 'Midnight Bloom Top', price: 149.99, category: 'tops' },
    { id: 'br-003', name: 'Silver Thorn Earrings', price: 89.99, category: 'accessories' },
  ],
  signature: [
    { id: 'sig-001', name: 'Rose Gold Blazer', price: 399.99, category: 'outerwear' },
    { id: 'sig-002', name: 'Ivory Silk Blouse', price: 199.99, category: 'tops' },
    { id: 'sig-003', name: 'Classic Noir Pants', price: 179.99, category: 'bottoms' },
  ],
  love_hurts: [
    { id: 'lh-001', name: 'Enchanted Rose Gown', price: 599.99, type: 'hero' },
    { id: 'lh-002', name: 'Magic Mirror Dress', price: 349.99, type: 'mirror' },
    { id: 'lh-003', name: 'Candlelit Romance Top', price: 189.99, type: 'candelabra' },
  ],
  showroom: [
    { id: 'sr-001', name: 'Featured Collection Piece', position: { x: 0, y: 0, z: 0 } },
    { id: 'sr-002', name: 'Spotlight Item', position: { x: 5, y: 0, z: 0 } },
  ],
  runway: [
    { id: 'rw-001', name: 'Runway Look 1', position: [0, 0, 0] },
    { id: 'rw-002', name: 'Runway Look 2', position: [0, 0, 5] },
  ],
};

function initExperience(collection: CollectionType): void {
  const container = document.getElementById('experience-container');
  if (!container) return;

  // Dispose previous experience
  if (currentExperience) {
    currentExperience.dispose();
    currentExperience = null;
  }

  // Clear container
  const canvas = container.querySelector('canvas');
  if (canvas) canvas.remove();

  // Show loading
  const loading = container.querySelector('.loading') as HTMLElement;
  if (loading) loading.style.display = 'block';

  try {
    // Create new experience
    currentExperience = createCollectionExperience(container, {
      collection,
      config: {
        enableBloom: true,
      },
    });

    // Load demo products
    const products = DEMO_PRODUCTS[collection];
    if ('loadProducts' in currentExperience && typeof currentExperience.loadProducts === 'function') {
      currentExperience.loadProducts(products);
    } else if ('addProduct' in currentExperience && typeof currentExperience.addProduct === 'function') {
      products.forEach((p: Record<string, unknown>) => {
        (currentExperience as ShowroomExperience).addProduct(p as never);
      });
    }

    // Set up interaction handlers
    if ('setOnProductClick' in currentExperience) {
      (currentExperience as BlackRoseExperience).setOnProductClick((product) => {
        console.log('Product clicked:', product);
        alert(`Product: ${product.name}\nPrice: $${product.price}`);
      });
    }

    // Start animation
    currentExperience.start();

    // Hide loading
    if (loading) loading.style.display = 'none';

    currentCollection = collection;
    console.log(`✅ ${collection} experience loaded`);
  } catch (error) {
    console.error('Failed to initialize experience:', error);
    if (loading) {
      loading.innerHTML = `<p style="color: #dc143c;">Failed to load experience. Check console for details.</p>`;
    }
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  // Get collection from URL params or default to black_rose
  const params = new URLSearchParams(window.location.search);
  const collection = (params.get('collection') as CollectionType) || 'black_rose';

  // Set up navigation buttons
  const buttons = document.querySelectorAll('.collection-btn');
  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const col = btn.getAttribute('data-collection') as CollectionType;
      if (col && col !== currentCollection) {
        buttons.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        initExperience(col);
      }
    });

    // Set initial active state
    if (btn.getAttribute('data-collection') === collection) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Initialize first experience
  initExperience(collection);
});

// Handle window resize
window.addEventListener('resize', () => {
  // Experiences handle their own resize via internal listeners
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (currentExperience) {
    currentExperience.dispose();
  }
});

