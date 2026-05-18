import React, { useEffect, useState } from 'react';
import { Droplets, Plus, Pencil, Trash2, X, Check, CupSoda } from 'lucide-react';
import { api } from '../lib/api.js';
import Spinner, { FullSpinner } from '../components/Spinner.jsx';
import ErrorBanner from '../components/ErrorBanner.jsx';
import useDraft from '../lib/useDraft.js';

export default function Nutrition() {
  const [meals, setMeals] = useState(null);
  const [water, setWater] = useState({ amount_ml: 0, target_ml: 3000 });
  const [me, setMe] = useState(null);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(null); // meal id or 'new'
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const [m, w, u] = await Promise.all([
        api.get('/api/meals'),
        api.get('/api/water'),
        api.get('/api/me'),
      ]);
      setMeals(m);
      setWater(w);
      setMe(u);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { load(); }, []);

  if (!meals || !me) return <FullSpinner />;

  const eaten = meals.filter((m) => m.eaten);
  const totals = {
    calories: eaten.reduce((s, m) => s + (m.calories || 0), 0),
    protein: eaten.reduce((s, m) => s + (m.protein || 0), 0),
    carbs: eaten.reduce((s, m) => s + (m.carbs || 0), 0),
    fat: eaten.reduce((s, m) => s + (m.fat || 0), 0),
  };

  async function toggle(meal) {
    try {
      await api.post(`/api/meals/${meal.id}/toggle`);
      await load();
    } catch (e) { setError(e.message); }
  }

  async function addWater(amt) {
    setBusy(true);
    try {
      const w = await api.post('/api/water', { amount_ml: amt });
      setWater((cur) => ({ ...cur, amount_ml: w.amount_ml }));
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  async function resetWater() {
    if (!confirm('Reset today\'s water?')) return;
    try {
      await api.del('/api/water');
      await load();
    } catch (e) { setError(e.message); }
  }

  return (
    <div className="space-y-5 fade-in">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      <h1 className="text-2xl font-bold">Nutrition</h1>

      {/* Macro progress */}
      <div className="card space-y-3">
        <div className="flex items-baseline justify-between">
          <div>
            <div className="text-xs uppercase tracking-wider text-textmuted">Today's totals</div>
            <div className="text-2xl font-bold">{totals.calories} <span className="text-sm text-textmuted">/ {me.daily_calorie_target} kcal</span></div>
          </div>
        </div>
        <MacroBar label="Protein" value={totals.protein} target={me.daily_protein_target} unit="g" />
        <MacroBar label="Carbs" value={totals.carbs} target={me.daily_carb_target} unit="g" />
        <MacroBar label="Fat" value={totals.fat} target={me.daily_fat_target} unit="g" />
        <MacroBar label="Calories" value={totals.calories} target={me.daily_calorie_target} unit="kcal" />
      </div>

      {/* Water */}
      <div className="card space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-semibold">
            <Droplets size={18} className="text-accent" /> Water
          </div>
          <button onClick={resetWater} className="text-xs text-textmuted hover:text-white">Reset</button>
        </div>
        <div>
          <div className="text-2xl font-bold">{water.amount_ml} <span className="text-sm text-textmuted">/ {water.target_ml} ml</span></div>
          <div className="progress-track mt-2">
            <div className="progress-fill" style={{ width: `${Math.min(100, (water.amount_ml / water.target_ml) * 100)}%` }} />
          </div>
        </div>
        <div className="grid grid-cols-4 gap-2">
          {[250, 500, 750].map((amt) => (
            <button
              key={amt}
              onClick={() => addWater(amt)}
              disabled={busy}
              className="btn btn-secondary"
            >
              +{amt}
            </button>
          ))}
          <WaterCustom onAdd={addWater} busy={busy} />
        </div>
      </div>

      {/* Meals */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Meals</h2>
        <button onClick={() => setEditing('new')} className="btn btn-secondary text-xs">
          <Plus size={14} /> Add meal
        </button>
      </div>

      <div className="space-y-2">
        {meals.map((m) => (
          <div key={m.id} className={`card transition-all ${m.eaten ? 'border-accent/40 bg-accent/5' : ''}`}>
            <div className="flex items-start gap-3">
              <button
                onClick={() => toggle(m)}
                className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                  m.eaten ? 'bg-accent border-accent' : 'border-textmuted hover:border-accent'
                }`}
              >
                {m.eaten && <Check size={14} className="text-white" />}
              </button>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xs font-mono text-textmuted">{m.scheduled_time}</span>
                </div>
                <div className={`text-sm font-medium ${m.eaten ? 'text-textmuted line-through' : ''}`}>{m.name}</div>
                <div className="text-xs text-textmuted mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5">
                  <span><span className="text-white">{m.calories}</span> kcal</span>
                  <span><span className="text-white">{m.protein}</span>P</span>
                  <span><span className="text-white">{m.carbs}</span>C</span>
                  <span><span className="text-white">{m.fat}</span>F</span>
                </div>
              </div>
              <button onClick={() => setEditing(m.id)} className="text-textmuted hover:text-white p-1">
                <Pencil size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {editing && (
        <MealEditor
          mealId={editing === 'new' ? null : editing}
          existing={editing === 'new' ? null : meals.find((x) => x.id === editing)}
          onClose={() => setEditing(null)}
          onSaved={async () => { setEditing(null); await load(); }}
        />
      )}
    </div>
  );
}

function MacroBar({ label, value, target, unit }) {
  const pct = target ? Math.min(100, Math.round((value / target) * 100)) : 0;
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-textmuted">{label}</span>
        <span><span className="text-white">{value}</span> / {target} {unit}</span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function WaterCustom({ onAdd, busy }) {
  const [val, setVal] = useState('');
  const [open, setOpen] = useState(false);
  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="btn btn-secondary">
        <CupSoda size={14} />
      </button>
    );
  }
  return (
    <div className="col-span-4 flex gap-2">
      <input
        inputMode="numeric"
        type="number"
        value={val}
        onChange={(e) => setVal(e.target.value)}
        placeholder="ml"
        className="input flex-1"
      />
      <button
        onClick={() => { if (val) { onAdd(parseInt(val, 10)); setVal(''); setOpen(false); } }}
        disabled={busy}
        className="btn btn-primary"
      >
        Add
      </button>
      <button onClick={() => setOpen(false)} className="btn btn-secondary px-3">
        <X size={14} />
      </button>
    </div>
  );
}

function MealEditor({ mealId, existing, onClose, onSaved }) {
  const draftKey = mealId ? `meal-${mealId}` : 'meal-new';
  const [form, setForm, clearDraft] = useDraft(draftKey, existing || {
    name: '', scheduled_time: '', calories: 0, protein: 0, carbs: 0, fat: 0,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function save() {
    setBusy(true);
    setError(null);
    try {
      if (mealId) await api.put(`/api/meals/${mealId}`, form);
      else await api.post('/api/meals', form);
      clearDraft();
      onSaved();
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  async function remove() {
    if (!confirm('Delete this meal?')) return;
    setBusy(true);
    try {
      await api.del(`/api/meals/${mealId}`);
      clearDraft();
      onSaved();
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-end md:items-center justify-center p-4 fade-in">
      <div className="bg-surface border border-line rounded-2xl w-full max-w-md p-5 slide-up">
        <div className="flex items-center justify-between mb-4">
          <div className="font-semibold">{mealId ? 'Edit meal' : 'New meal'}</div>
          <button onClick={onClose} className="text-textmuted hover:text-white"><X size={18} /></button>
        </div>
        <ErrorBanner error={error} onDismiss={() => setError(null)} />
        <div className="space-y-3">
          <div>
            <label className="label">Name</label>
            <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </div>
          <div>
            <label className="label">Time</label>
            <input className="input" placeholder="HH:MM" value={form.scheduled_time} onChange={(e) => setForm({ ...form, scheduled_time: e.target.value })} />
          </div>
          <div className="grid grid-cols-4 gap-2">
            {['calories', 'protein', 'carbs', 'fat'].map((k) => (
              <div key={k}>
                <label className="label capitalize">{k}</label>
                <input
                  inputMode="numeric"
                  type="number"
                  className="input"
                  value={form[k]}
                  onChange={(e) => setForm({ ...form, [k]: parseInt(e.target.value || 0, 10) })}
                />
              </div>
            ))}
          </div>
        </div>
        <div className="flex gap-2 mt-5">
          {mealId && (
            <button onClick={remove} disabled={busy} className="btn btn-secondary text-red-300">
              <Trash2 size={14} />
            </button>
          )}
          <button onClick={save} disabled={busy} className="btn btn-primary flex-1">
            {busy ? <Spinner /> : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
