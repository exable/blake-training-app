import React, { useEffect, useState } from 'react';
import { Lock, Target, Download, ChevronRight } from 'lucide-react';
import { api } from '../lib/api.js';
import Spinner, { FullSpinner } from '../components/Spinner.jsx';
import ErrorBanner from '../components/ErrorBanner.jsx';

const APP_VERSION = '1.0.0';

export default function Settings() {
  const [me, setMe] = useState(null);
  const [error, setError] = useState(null);

  async function load() {
    try { setMe(await api.get('/api/me')); }
    catch (e) { setError(e.message); }
  }

  useEffect(() => { load(); }, []);

  if (!me) return <FullSpinner />;

  return (
    <div className="space-y-5 fade-in">
      <h1 className="text-2xl font-bold">Settings</h1>
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <ChangePassword />
      <Targets me={me} onSaved={load} />
      <DataExport />

      <div className="card">
        <div className="text-xs uppercase tracking-wider text-textmuted">App version</div>
        <div className="text-sm font-mono mt-1">{APP_VERSION}</div>
        <div className="text-xs text-textmuted mt-1">Manage your meal plan from the Nutrition page.</div>
      </div>
    </div>
  );
}

function ChangePassword() {
  const [old_password, setOld] = useState('');
  const [new_password, setNew] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [err, setErr] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setMsg(null); setErr(null);
    try {
      await api.post('/api/auth/change-password', { old_password, new_password });
      setOld(''); setNew('');
      setMsg('Password updated.');
    } catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  }

  return (
    <form onSubmit={submit} className="card space-y-3">
      <div className="flex items-center gap-2 font-semibold"><Lock size={16} className="text-accent" />Password</div>
      <ErrorBanner error={err} onDismiss={() => setErr(null)} />
      {msg && <div className="text-xs text-accent">{msg}</div>}
      <input type="password" placeholder="Current password" className="input" value={old_password} onChange={(e) => setOld(e.target.value)} />
      <input type="password" placeholder="New password" className="input" value={new_password} onChange={(e) => setNew(e.target.value)} />
      <button type="submit" disabled={busy || !old_password || !new_password} className="btn btn-primary w-full">
        {busy ? <Spinner /> : 'Update password'}
      </button>
    </form>
  );
}

function Targets({ me, onSaved }) {
  const [form, setForm] = useState({
    daily_calorie_target: me.daily_calorie_target,
    daily_protein_target: me.daily_protein_target,
    daily_carb_target: me.daily_carb_target,
    daily_fat_target: me.daily_fat_target,
    daily_water_target_ml: me.daily_water_target_ml,
    goal_weight_kg: me.goal_weight_kg,
  });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [err, setErr] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setMsg(null); setErr(null);
    try {
      await api.put('/api/me/targets', form);
      setMsg('Targets saved.');
      onSaved();
    } catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  }

  return (
    <form onSubmit={submit} className="card space-y-3">
      <div className="flex items-center gap-2 font-semibold"><Target size={16} className="text-accent" />Targets</div>
      <ErrorBanner error={err} onDismiss={() => setErr(null)} />
      {msg && <div className="text-xs text-accent">{msg}</div>}
      <div className="grid grid-cols-2 gap-3">
        {[
          ['daily_calorie_target', 'Calories (kcal)'],
          ['daily_protein_target', 'Protein (g)'],
          ['daily_carb_target', 'Carbs (g)'],
          ['daily_fat_target', 'Fat (g)'],
          ['daily_water_target_ml', 'Water (ml)'],
          ['goal_weight_kg', 'Goal weight (kg)'],
        ].map(([k, lbl]) => (
          <div key={k}>
            <label className="label">{lbl}</label>
            <input
              type="number" step={k === 'goal_weight_kg' ? '0.1' : '1'}
              className="input"
              value={form[k]}
              onChange={(e) => setForm({ ...form, [k]: k === 'goal_weight_kg' ? parseFloat(e.target.value) : parseInt(e.target.value || 0, 10) })}
            />
          </div>
        ))}
      </div>
      <button type="submit" disabled={busy} className="btn btn-primary w-full">
        {busy ? <Spinner /> : 'Save targets'}
      </button>
    </form>
  );
}

function DataExport() {
  const [busy, setBusy] = useState(false);
  async function exportData() {
    setBusy(true);
    try {
      const data = await api.get('/api/export');
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `blake-training-export-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } finally { setBusy(false); }
  }
  return (
    <button onClick={exportData} disabled={busy} className="card card-hover w-full flex items-center justify-between text-left">
      <div className="flex items-center gap-3">
        <Download size={16} className="text-accent" />
        <div>
          <div className="font-semibold">Export data as JSON</div>
          <div className="text-xs text-textmuted">All weights, workouts and check-ins</div>
        </div>
      </div>
      {busy ? <Spinner /> : <ChevronRight size={16} className="text-textmuted" />}
    </button>
  );
}
