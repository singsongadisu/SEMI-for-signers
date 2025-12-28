// SignLearn Service Worker
// Version: 1.0.0
const CACHE_VERSION = 'signlearn-v1.0.0';
const OFFLINE_URL = '/offline';

// Assets to cache immediately on install
const STATIC_CACHE_URLS = [
    '/',
    '/offline',
    '/static/style.css',
    '/static/script.js',
    '/static/manifest.json',
    '/static/logo.png',
    // Add critical fonts
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@400;600;700;800;900&display=swap'
];

// Dynamic cache for images, API responses, etc.
const DYNAMIC_CACHE = 'signlearn-dynamic-v1';
const IMAGE_CACHE = 'signlearn-images-v1';
const API_CACHE = 'signlearn-api-v1';

// Cache size limits
const MAX_DYNAMIC_CACHE_SIZE = 50;
const MAX_IMAGE_CACHE_SIZE = 100;

// ============================================
// INSTALL EVENT - Cache static assets
// ============================================
self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker...', CACHE_VERSION);
    
    event.waitUntil(
        caches.open(CACHE_VERSION)
            .then((cache) => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .then(() => {
                console.log('[SW] Static assets cached successfully');
                return self.skipWaiting(); // Activate immediately
            })
            .catch((error) => {
                console.error('[SW] Failed to cache static assets:', error);
            })
    );
});

// ============================================
// ACTIVATE EVENT - Clean up old caches
// ============================================
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker...', CACHE_VERSION);
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        // Delete old caches
                        if (cacheName !== CACHE_VERSION && 
                            cacheName !== DYNAMIC_CACHE && 
                            cacheName !== IMAGE_CACHE &&
                            cacheName !== API_CACHE) {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[SW] Service Worker activated');
                return self.clients.claim(); // Take control immediately
            })
    );
});

// ============================================
// FETCH EVENT - Serve from cache or network
// ============================================
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip chrome-extension and other non-http(s) requests
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // API requests - Network first, cache fallback
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/translate')) {
        event.respondWith(networkFirstStrategy(request, API_CACHE));
        return;
    }

    // Images and media - Cache first, network fallback
    if (request.destination === 'image' || 
        url.pathname.match(/\.(jpg|jpeg|png|gif|webp|svg|mp4|gif)$/i)) {
        event.respondWith(cacheFirstStrategy(request, IMAGE_CACHE, MAX_IMAGE_CACHE_SIZE));
        return;
    }

    // Static assets - Cache first
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(cacheFirstStrategy(request, CACHE_VERSION));
        return;
    }

    // HTML pages - Network first, cache fallback
    if (request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(networkFirstStrategy(request, DYNAMIC_CACHE));
        return;
    }

    // Default: Network first
    event.respondWith(networkFirstStrategy(request, DYNAMIC_CACHE));
});

// ============================================
// CACHING STRATEGIES
// ============================================

// Cache First Strategy - For static assets and images
async function cacheFirstStrategy(request, cacheName, maxSize = null) {
    try {
        const cache = await caches.open(cacheName);
        const cachedResponse = await cache.match(request);

        if (cachedResponse) {
            console.log('[SW] Serving from cache:', request.url);
            return cachedResponse;
        }

        console.log('[SW] Fetching from network:', request.url);
        const networkResponse = await fetch(request);

        // Cache successful responses
        if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            
            // Limit cache size if specified
            if (maxSize) {
                await limitCacheSize(cacheName, maxSize);
            }
            
            cache.put(request, responseToCache);
        }

        return networkResponse;
    } catch (error) {
        console.error('[SW] Cache first strategy failed:', error);
        
        // Return offline page for HTML requests
        if (request.headers.get('accept')?.includes('text/html')) {
            const offlineResponse = await caches.match(OFFLINE_URL);
            if (offlineResponse) return offlineResponse;
        }
        
        // Return a basic offline response
        return new Response('Offline - Content not available', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
                'Content-Type': 'text/plain'
            })
        });
    }
}

// Network First Strategy - For dynamic content and API calls
async function networkFirstStrategy(request, cacheName) {
    try {
        console.log('[SW] Fetching from network:', request.url);
        const networkResponse = await fetch(request);

        // Cache successful responses
        if (networkResponse && networkResponse.status === 200) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', request.url);
        
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            console.log('[SW] Serving from cache:', request.url);
            return cachedResponse;
        }

        // Return offline page for HTML requests
        if (request.headers.get('accept')?.includes('text/html')) {
            const offlineResponse = await caches.match(OFFLINE_URL);
            if (offlineResponse) return offlineResponse;
        }

        // Return offline response
        return new Response(JSON.stringify({
            error: 'Offline',
            message: 'You are currently offline. Please check your internet connection.'
        }), {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
                'Content-Type': 'application/json'
            })
        });
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

// Limit cache size to prevent storage overflow
async function limitCacheSize(cacheName, maxSize) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    
    if (keys.length > maxSize) {
        console.log(`[SW] Cache ${cacheName} exceeded ${maxSize} items, cleaning up...`);
        // Delete oldest entries (FIFO)
        await cache.delete(keys[0]);
        await limitCacheSize(cacheName, maxSize); // Recursive cleanup
    }
}

// ============================================
// BACKGROUND SYNC (for offline form submissions)
// ============================================
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync triggered:', event.tag);
    
    if (event.tag === 'sync-translations') {
        event.waitUntil(syncTranslations());
    }
    
    if (event.tag === 'sync-progress') {
        event.waitUntil(syncProgress());
    }
});

async function syncTranslations() {
    // Sync pending translations when back online
    console.log('[SW] Syncing pending translations...');
    // Implementation would retrieve from IndexedDB and POST to server
}

async function syncProgress() {
    // Sync user progress when back online
    console.log('[SW] Syncing user progress...');
    // Implementation would retrieve from IndexedDB and POST to server
}

// ============================================
// PUSH NOTIFICATIONS (for streak reminders)
// ============================================
self.addEventListener('push', (event) => {
    console.log('[SW] Push notification received');
    
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'SignLearn';
    const options = {
        body: data.body || 'Time to practice your signs!',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/',
            timestamp: Date.now()
        },
        actions: [
            {
                action: 'practice',
                title: 'Practice Now',
                icon: '/static/icons/action-practice.png'
            },
            {
                action: 'dismiss',
                title: 'Later',
                icon: '/static/icons/action-dismiss.png'
            }
        ],
        tag: 'signlearn-reminder',
        requireInteraction: false,
        renotify: true
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked:', event.action);
    
    event.notification.close();

    if (event.action === 'practice') {
        event.waitUntil(
            clients.openWindow(event.notification.data.url || '/sign-lab')
        );
    } else if (event.action === 'dismiss') {
        // Just close the notification
        return;
    } else {
        // Default action - open app
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// ============================================
// MESSAGE HANDLER (for communication with app)
// ============================================
self.addEventListener('message', (event) => {
    console.log('[SW] Message received:', event.data);
    
    if (event.data.action === 'skipWaiting') {
        self.skipWaiting();
    }
    
    if (event.data.action === 'clearCache') {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => caches.delete(cacheName))
                );
            })
        );
    }
});

console.log('[SW] Service Worker script loaded');
