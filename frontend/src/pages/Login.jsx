import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dumbbell } from 'lucide-react';
import { api, isAuthed, setToken } from '../lib/api.js';
import Spinner from '../components/Spinner.jsx';
import ErrorBanner from '../components/ErrorBanner.jsx';

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('blake');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isAuthed()) navigate('/dashboard', { replace: true });
  }, [navigate]);

  async function submit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.post('/api/auth/login', { username, password });
      setToken(res.token);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-bg">
      <div className="w-full max-w-sm slide-up">
        <div className="flex items-center gap-3 justify-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-accent/10 border border-accent/30 flex items-center justify-center">
            <Dumbbell size={22} className="text-accent" />
          </div>
          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-textmuted">Blake's</div>
            <div className="text-lg font-bold">Training App</div>
          </div>
        </div>

        <form onSubmit={submit} className="card space-y-4">
          <h1 className="text-xl font-semibold">Sign in</h1>
          <ErrorBanner error={error} onDismiss={() => setError(null)} />
          <div>
            <label className="label">Username</label>
            <input
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <button type="submit" disabled={loading} className="btn btn-primary w-full">
            {loading ? <Spinner /> : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}
