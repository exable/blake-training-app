import { useEffect, useState } from 'react';

/** Persists a form state in localStorage so a refresh doesn't lose progress. */
export default function useDraft(key, initial) {
  const [state, setState] = useState(() => {
    try {
      const raw = localStorage.getItem(`draft:${key}`);
      return raw ? { ...initial, ...JSON.parse(raw) } : initial;
    } catch {
      return initial;
    }
  });
  useEffect(() => {
    try {
      localStorage.setItem(`draft:${key}`, JSON.stringify(state));
    } catch {}
  }, [key, state]);
  const clear = () => localStorage.removeItem(`draft:${key}`);
  return [state, setState, clear];
}
