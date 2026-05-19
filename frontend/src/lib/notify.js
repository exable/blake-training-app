// Lightweight browser notification + audible beep for rest-timer completion.

export async function ensureNotifyPermission() {
  if (typeof window === 'undefined' || !('Notification' in window)) return false;
  if (Notification.permission === 'granted') return true;
  if (Notification.permission === 'denied') return false;
  const res = await Notification.requestPermission();
  return res === 'granted';
}

export function notify(title, body) {
  try {
    if ('Notification' in window && Notification.permission === 'granted') {
      const n = new Notification(title, { body, silent: false, tag: 'rest-timer' });
      setTimeout(() => n.close?.(), 6000);
    }
  } catch {}
}

let _ctx = null;
export function beep(duration = 0.45) {
  try {
    _ctx = _ctx || new (window.AudioContext || window.webkitAudioContext)();
    const ctx = _ctx;
    if (ctx.state === 'suspended') ctx.resume();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.35, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    osc.connect(gain).connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  } catch {}
}

export function vibrate(pattern = [200, 100, 200]) {
  try {
    navigator.vibrate?.(pattern);
  } catch {}
}

// Service-worker scheduling for rest timer — fires a notification even when
// the tab is in the background (as long as the browser process is alive).
async function _swReg() {
  if (!('serviceWorker' in navigator)) return null;
  try { return await navigator.serviceWorker.ready; } catch { return null; }
}

export async function scheduleRestNotification(endTs, body = 'Back to it 💪', tag = 'rest-timer') {
  const reg = await _swReg();
  if (!reg || !reg.active) return false;
  reg.active.postMessage({ action: 'schedule-rest', endTs, body, tag });
  return true;
}

export async function cancelRestNotification(tag = 'rest-timer') {
  const reg = await _swReg();
  if (!reg || !reg.active) return;
  reg.active.postMessage({ action: 'cancel-rest', tag });
}
