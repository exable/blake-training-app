// Service Worker — handles offline shell and background rest-timer notifications.
const VERSION = 'v3';
const SHELL_CACHE = `shell-${VERSION}`;

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== SHELL_CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Pass-through fetch — we don't cache API responses (always fresh data).
self.addEventListener('fetch', (event) => {
  // network-first for everything; offline fallback would go here if we wanted it.
});

// REST TIMER scheduling. Page posts { action: 'schedule-rest', endTs, durationSec }.
// We use setTimeout — works while the browser process is alive. For phone-killed
// reliability, native push would be required.
const restTimers = new Map(); // tag -> timeoutId

self.addEventListener('message', (event) => {
  const msg = event.data || {};
  if (msg.action === 'schedule-rest') {
    const tag = msg.tag || 'rest-timer';
    if (restTimers.has(tag)) clearTimeout(restTimers.get(tag));
    const delay = Math.max(0, msg.endTs - Date.now());
    const tid = setTimeout(() => {
      self.registration.showNotification('Rest over', {
        body: msg.body || 'Back to it 💪',
        tag,
        renotify: true,
        vibrate: [300, 120, 300],
        icon: '/icon-192.png',
        badge: '/icon-192.png',
        requireInteraction: false,
      });
      restTimers.delete(tag);
    }, delay);
    restTimers.set(tag, tid);
  } else if (msg.action === 'cancel-rest') {
    const tag = msg.tag || 'rest-timer';
    if (restTimers.has(tag)) {
      clearTimeout(restTimers.get(tag));
      restTimers.delete(tag);
    }
    // Also dismiss any visible notification with the same tag
    self.registration.getNotifications({ tag }).then((ns) => ns.forEach((n) => n.close()));
  }
});

// Focus the app when notification is tapped
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil((async () => {
    const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const c of all) {
      if (c.url.includes('/workout')) {
        await c.focus();
        return;
      }
    }
    if (all[0]) {
      await all[0].focus();
      all[0].postMessage({ action: 'navigate', path: '/workout' });
      return;
    }
    await self.clients.openWindow('/workout');
  })());
});
