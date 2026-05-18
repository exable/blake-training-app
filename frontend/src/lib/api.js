const BASE = import.meta.env.VITE_API_BASE || '';

function token() {
  return localStorage.getItem('token') || '';
}

async function request(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  const t = token();
  if (t) headers.Authorization = `Bearer ${t}`;
  const res = await fetch(`${BASE}${path}`, { ...opts, headers });
  if (res.status === 401) {
    localStorage.removeItem('token');
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }
  const isJson = (res.headers.get('content-type') || '').includes('application/json');
  const body = isJson ? await res.json() : await res.text();
  if (!res.ok) throw new Error(body?.error || `Request failed (${res.status})`);
  return body;
}

export const api = {
  get: (p) => request(p),
  post: (p, body) => request(p, { method: 'POST', body: JSON.stringify(body || {}) }),
  put: (p, body) => request(p, { method: 'PUT', body: JSON.stringify(body || {}) }),
  del: (p) => request(p, { method: 'DELETE' }),
  upload: async (p, formData) => {
    const t = token();
    const res = await fetch(`${BASE}${p}`, {
      method: 'POST',
      headers: t ? { Authorization: `Bearer ${t}` } : {},
      body: formData,
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body?.error || 'Upload failed');
    return body;
  },
};

export function setToken(t) {
  localStorage.setItem('token', t);
}

export function clearToken() {
  localStorage.removeItem('token');
}

export function isAuthed() {
  return !!token();
}
