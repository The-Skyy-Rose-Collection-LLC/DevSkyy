/**
 * SkyyRose Service Worker
 * Cache: skyyrose-v1
 * Strategy: Cache-first for images, network-first for API, stale-while-revalidate for all else
 */

const CACHE_NAME = 'skyyrose-v1';
const CACHE_PREFIX = 'skyyrose-';

const PRECACHE_URLS = [
  '/index.html',
  '/collections.html',
  '/explore-black-rose.html',
  '/explore-love-hurts.html',
  '/explore-signature.html',
  '/assets/css/styles.css',
  '/assets/css/base-v2.css',
  '/assets/css/homepage.css',
  '/assets/js/app.js',
  '/assets/js/config.js',
  '/assets/js/accessibility.js',
  '/assets/js/gestures.js',
  '/assets/js/wishlist.js',
  '/assets/js/analytics.js',
  '/assets/js/wordpress-client.js',
];

// ---------------------------------------------------------------------------
// INSTALL — precache static assets
// ---------------------------------------------------------------------------
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Pre-caching assets');
      return cache.addAll(PRECACHE_URLS);
    })
  );
});

// ---------------------------------------------------------------------------
// ACTIVATE — purge stale skyyrose-* caches, claim clients
// ---------------------------------------------------------------------------
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter(
            (key) => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME
          )
          .map((key) => {
            console.log('[SW] Deleting old cache:', key);
            return caches.delete(key);
          })
      );
    }).then(() => {
      console.log('[SW] Claiming clients');
      return self.clients.claim();
    })
  );
});

// ---------------------------------------------------------------------------
// Helper — is this an image request?
// ---------------------------------------------------------------------------
function isImageRequest(request) {
  const url = new URL(request.url);
  return url.pathname.includes('/assets/images/') ||
    /\.(png|jpg|jpeg|gif|webp|svg|avif)(\?.*)?$/.test(url.pathname);
}

// ---------------------------------------------------------------------------
// Helper — is this a WooCommerce / WP REST API request?
// ---------------------------------------------------------------------------
function isApiRequest(request) {
  const url = new URL(request.url);
  return (
    url.pathname.startsWith('/wp-json/') ||
    url.search.includes('wc-ajax=')
  );
}

// ---------------------------------------------------------------------------
// Strategy: Cache-first (images)
// ---------------------------------------------------------------------------
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response && response.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    console.warn('[SW] Cache-first fetch failed:', request.url, err);
    return new Response('', { status: 503, statusText: 'Offline' });
  }
}

// ---------------------------------------------------------------------------
// Strategy: Network-first (API)
// ---------------------------------------------------------------------------
async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);

  try {
    const response = await fetch(request);
    if (response && response.status === 200) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    console.warn('[SW] Network-first falling back to cache:', request.url);
    const cached = await cache.match(request);
    if (cached) return cached;
    return new Response(
      JSON.stringify({ error: 'Offline', offline: true }),
      {
        status: 503,
        statusText: 'Offline',
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

// ---------------------------------------------------------------------------
// Strategy: Stale-while-revalidate (everything else)
// ---------------------------------------------------------------------------
async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);

  // Kick off network fetch regardless
  const networkFetch = fetch(request).then((response) => {
    if (response && response.status === 200) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch((err) => {
    console.warn('[SW] SWR revalidation failed:', request.url, err);
  });

  // Return cached immediately if available, otherwise await network
  return cached || networkFetch;
}

// ---------------------------------------------------------------------------
// FETCH — route to correct strategy
// ---------------------------------------------------------------------------
self.addEventListener('fetch', (event) => {
  // Only handle GET (and POST for WC ajax) same-origin + known cross-origin
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-http(s) schemes (chrome-extension, etc.)
  if (!url.protocol.startsWith('http')) return;

  if (isImageRequest(request)) {
    event.respondWith(cacheFirst(request));
  } else if (isApiRequest(request)) {
    event.respondWith(networkFirst(request));
  } else {
    event.respondWith(staleWhileRevalidate(request));
  }
});

// ---------------------------------------------------------------------------
// MESSAGE — support SKIP_WAITING from app shell
// ---------------------------------------------------------------------------
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('[SW] Received SKIP_WAITING — skipping wait');
    self.skipWaiting();
  }
});

// ---------------------------------------------------------------------------
// BACKGROUND SYNC — retry failed cart adds
// ---------------------------------------------------------------------------
const CART_SYNC_TAG = 'cart-sync';

// Queue a failed cart operation for background sync
async function queueCartSync(payload) {
  const db = await openSyncDB();
  const tx = db.transaction('cart-queue', 'readwrite');
  tx.objectStore('cart-queue').add({
    payload,
    timestamp: Date.now(),
  });
  await tx.done;

  try {
    await self.registration.sync.register(CART_SYNC_TAG);
    console.log('[SW] Background sync registered for cart-sync');
  } catch (err) {
    console.warn('[SW] Background sync registration failed:', err);
  }
}

// Minimal IndexedDB helper
function openSyncDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('skyyrose-sync', 1);
    req.onupgradeneeded = (e) => {
      e.target.result.createObjectStore('cart-queue', {
        autoIncrement: true,
      });
    };
    req.onsuccess = (e) => resolve(wrapIDB(e.target.result));
    req.onerror = (e) => reject(e.target.error);
  });
}

// Lightweight IDB promise wrapper
function wrapIDB(db) {
  return {
    transaction(store, mode) {
      const tx = db.transaction(store, mode);
      return {
        objectStore(name) {
          const os = tx.objectStore(name);
          return {
            add: (val) => idbRequest(os.add(val)),
            getAll: () => idbRequest(os.getAll()),
            delete: (key) => idbRequest(os.delete(key)),
          };
        },
        get done() {
          return new Promise((res, rej) => {
            tx.oncomplete = res;
            tx.onerror = () => rej(tx.error);
          });
        },
      };
    },
  };
}

function idbRequest(req) {
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

// Process queued cart syncs
async function processCartQueue() {
  const db = await openSyncDB();
  const tx = db.transaction('cart-queue', 'readwrite');
  const store = tx.objectStore('cart-queue');
  const items = await store.getAll();

  for (const item of items) {
    try {
      const response = await fetch('/?wc-ajax=add_to_cart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(item.payload).toString(),
      });

      if (response.ok) {
        await store.delete(item.id);
        console.log('[SW] Cart sync succeeded for item:', item.payload);
      } else {
        console.warn('[SW] Cart sync server error:', response.status);
      }
    } catch (err) {
      console.warn('[SW] Cart sync failed, will retry:', err);
      throw err; // Re-throw so the browser re-queues the sync
    }
  }
}

self.addEventListener('sync', (event) => {
  if (event.tag === CART_SYNC_TAG) {
    console.log('[SW] Processing cart-sync background sync');
    event.waitUntil(processCartQueue());
  }
});

// Expose queueCartSync so fetch interceptor can use it
self.queueCartSync = queueCartSync;
