import React, { useEffect, useState } from 'react';
import { Calendar, Check, Upload } from 'lucide-react';
import { api } from '../lib/api.js';
import Spinner, { FullSpinner } from '../components/Spinner.jsx';
import ErrorBanner from '../components/ErrorBanner.jsx';
import useDraft from '../lib/useDraft.js';

export default function Checkins() {
  const [tab, setTab] = useState('daily');
  return (
    <div className="space-y-5 fade-in">
      <h1 className="text-2xl font-bold">Check-ins</h1>
      <div className="flex bg-surface2 p-1 rounded-xl text-xs w-full max-w-xs">
        {['daily', 'weekly'].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 px-3 py-2 rounded-lg capitalize ${tab === t ? 'bg-accent text-white' : 'text-textmuted'}`}
          >
            {t}
          </button>
        ))}
      </div>
      {tab === 'daily' ? <DailyCheckin /> : <WeeklyCheckin />}
    </div>
  );
}

function DailyCheckin() {
  const [state, setState] = useState(null);
  const [form, setForm, clearDraft] = useDraft('daily-checkin', {
    weight_kg: '', proud_1: '', proud_2: '', proud_3: '',
    sleep_quality: 7, nutrition_adherence: 'Yes', trained_today: 'Yes', notes: '',
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function load() {
    try {
      const r = await api.get('/api/checkins/daily/today');
      setState(r);
    } catch (e) { setError(e.message); }
  }
  useEffect(() => { load(); }, []);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.post('/api/checkins/daily', {
        ...form,
        weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
      });
      clearDraft();
      await load();
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  if (!state) return <FullSpinner />;
  if (state.submitted) {
    const d = state.data;
    return (
      <div className="card space-y-3 fade-in">
        <div className="flex items-center gap-2 text-accent">
          <Check size={18} /> Submitted today
        </div>
        <Row label="Weight">{d.weight_kg ? `${d.weight_kg} kg` : '—'}</Row>
        <Row label="Sleep quality">{d.sleep_quality}/10</Row>
        <Row label="Nutrition">{d.nutrition_adherence}</Row>
        <Row label="Trained">{d.trained_today}</Row>
        <Row label="Proud of">
          <ul className="list-disc pl-4 space-y-0.5">
            {[d.proud_1, d.proud_2, d.proud_3].filter(Boolean).map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        </Row>
        {d.notes && <Row label="Notes">{d.notes}</Row>}
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="card space-y-4">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      <div>
        <label className="label">Current weight (kg)</label>
        <input
          inputMode="decimal" type="number" step="0.1"
          className="input" value={form.weight_kg}
          onChange={(e) => setForm({ ...form, weight_kg: e.target.value })}
        />
      </div>
      <div className="space-y-2">
        <label className="label">3 things you're proud of today</label>
        {[1, 2, 3].map((i) => (
          <input
            key={i}
            className="input"
            placeholder={`#${i}`}
            value={form[`proud_${i}`]}
            onChange={(e) => setForm({ ...form, [`proud_${i}`]: e.target.value })}
          />
        ))}
      </div>
      <div>
        <label className="label">Sleep quality: <span className="text-white">{form.sleep_quality}/10</span></label>
        <input
          type="range" min="1" max="10"
          value={form.sleep_quality}
          onChange={(e) => setForm({ ...form, sleep_quality: parseInt(e.target.value, 10) })}
          className="w-full accent-accent"
        />
      </div>
      <Radio
        label="Nailed your nutrition?"
        value={form.nutrition_adherence}
        onChange={(v) => setForm({ ...form, nutrition_adherence: v })}
        options={['Yes', 'Partially', 'No']}
      />
      <Radio
        label="Did you train today?"
        value={form.trained_today}
        onChange={(v) => setForm({ ...form, trained_today: v })}
        options={['Yes', 'No', 'Rest Day']}
      />
      <div>
        <label className="label">Notes</label>
        <textarea
          className="input min-h-[80px]"
          value={form.notes}
          onChange={(e) => setForm({ ...form, notes: e.target.value })}
        />
      </div>
      <button type="submit" disabled={busy} className="btn btn-primary w-full">
        {busy ? <Spinner /> : 'Submit daily check-in'}
      </button>
    </form>
  );
}

function WeeklyCheckin() {
  const [avail, setAvail] = useState(null);
  const [history, setHistory] = useState([]);
  const [photos, setPhotos] = useState({});
  const [uploadingType, setUploadingType] = useState(null);
  const [form, setForm, clearDraft] = useDraft('weekly-checkin', {
    weight_kg: '', nutrition_review: '', diet_changes: '', training_review: '',
    performance_improved: 'Yes', could_do_better: '', proud_of: '',
    main_goal: '', sleep_hours: '', sleep_quality: '', support_needed: '',
    energy: 5, fatigue: 5, digestion: 5, hunger: 5, recovery: 5,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function load() {
    try {
      const [a, h] = await Promise.all([
        api.get('/api/checkins/weekly/available'),
        api.get('/api/checkins/weekly'),
      ]);
      setAvail(a);
      setHistory(h);
    } catch (e) { setError(e.message); }
  }
  useEffect(() => { load(); }, []);

  async function uploadPhoto(type, file) {
    setUploadingType(type);
    setError(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('photo_type', type);
      const r = await api.upload('/api/photos/upload', fd);
      setPhotos((p) => ({ ...p, [type]: r }));
    } catch (e) { setError(e.message); }
    finally { setUploadingType(null); }
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const photo_ids = Object.values(photos).map((p) => p.id).filter(Boolean);
      await api.post('/api/checkins/weekly', {
        ...form,
        weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
        sleep_hours: form.sleep_hours ? parseFloat(form.sleep_hours) : null,
        photo_ids,
      });
      clearDraft();
      setPhotos({});
      await load();
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  if (!avail) return <FullSpinner />;

  return (
    <div className="space-y-4">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {!avail.available ? (
        <div className="card text-center">
          <Calendar size={20} className="mx-auto text-accent mb-2" />
          <div className="font-semibold">Weekly check-in done</div>
          <div className="text-xs text-textmuted mt-1">Unlocks again next Monday. Ero's response will appear in chat within 1–8 hours.</div>
        </div>
      ) : (
        <form onSubmit={submit} className="card space-y-4">
          <div className="text-xs uppercase tracking-wider text-textmuted">Week of {avail.week_start_date}</div>

          <div>
            <label className="label">Current weight (kg)</label>
            <input inputMode="decimal" type="number" step="0.1" className="input"
              value={form.weight_kg} onChange={(e) => setForm({ ...form, weight_kg: e.target.value })} />
          </div>

          <Text label="Nutrition this week — did you stick to it, if not why?" v={form.nutrition_review} onChange={(v) => setForm({ ...form, nutrition_review: v })} />
          <Text label="Anything you want to change in the diet?" v={form.diet_changes} onChange={(v) => setForm({ ...form, diet_changes: v })} />
          <Text label="Training this week — train every day you were meant to?" v={form.training_review} onChange={(v) => setForm({ ...form, training_review: v })} />

          <Radio
            label="Did performance improve in the gym this week?"
            value={form.performance_improved}
            onChange={(v) => setForm({ ...form, performance_improved: v })}
            options={['Yes', 'Partially', 'No']}
          />

          <Text label="What could you have done better?" v={form.could_do_better} onChange={(v) => setForm({ ...form, could_do_better: v })} />
          <Text label="What went well — what are you proud of?" v={form.proud_of} onChange={(v) => setForm({ ...form, proud_of: v })} />
          <Text label="Main goal for the upcoming week" v={form.main_goal} onChange={(v) => setForm({ ...form, main_goal: v })} />

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Avg sleep hrs / night</label>
              <input inputMode="decimal" type="number" step="0.1" className="input"
                value={form.sleep_hours} onChange={(e) => setForm({ ...form, sleep_hours: e.target.value })} />
            </div>
            <div>
              <label className="label">Sleep quality (notes)</label>
              <input className="input"
                value={form.sleep_quality} onChange={(e) => setForm({ ...form, sleep_quality: e.target.value })} />
            </div>
          </div>

          <Text label="Where do you need more support?" v={form.support_needed} onChange={(v) => setForm({ ...form, support_needed: v })} />

          <div className="space-y-3">
            {['energy', 'fatigue', 'digestion', 'hunger', 'recovery'].map((k) => (
              <div key={k}>
                <label className="label capitalize">{k}: <span className="text-white">{form[k]}/10</span></label>
                <input type="range" min="1" max="10" value={form[k]}
                  onChange={(e) => setForm({ ...form, [k]: parseInt(e.target.value, 10) })}
                  className="w-full accent-accent" />
              </div>
            ))}
          </div>

          <div className="space-y-2">
            <label className="label">Progress photos</label>
            <div className="grid grid-cols-3 gap-2">
              {['front', 'side', 'back'].map((t) => (
                <PhotoUpload
                  key={t}
                  type={t}
                  uploaded={photos[t]}
                  uploading={uploadingType === t}
                  onSelect={(file) => uploadPhoto(t, file)}
                />
              ))}
            </div>
          </div>

          <button type="submit" disabled={busy} className="btn btn-primary w-full">
            {busy ? <Spinner /> : 'Submit weekly check-in'}
          </button>
        </form>
      )}

      <h2 className="text-lg font-semibold mt-6">History</h2>
      {history.length === 0 && <div className="card text-center text-textmuted">No weekly check-ins yet.</div>}
      {history.map((w) => (
        <details key={w.id} className="card">
          <summary className="cursor-pointer flex items-center justify-between">
            <div>
              <div className="font-medium">Week of {w.week_start_date}</div>
              <div className="text-xs text-textmuted">{w.weight_kg ? `${w.weight_kg}kg` : ''}</div>
            </div>
            {w.ero_response ? (
              <span className="chip text-accent border-accent/30">Ero replied</span>
            ) : (
              <span className="chip">Pending reply</span>
            )}
          </summary>
          <div className="mt-3 text-sm space-y-2">
            {w.main_goal && <p><span className="text-textmuted">Goal:</span> {w.main_goal}</p>}
            {w.nutrition_review && <p><span className="text-textmuted">Nutrition:</span> {w.nutrition_review}</p>}
            {w.training_review && <p><span className="text-textmuted">Training:</span> {w.training_review}</p>}
            {w.ero_response && (
              <div className="mt-3 p-3 bg-surface2 rounded-xl border border-line">
                <div className="text-xs text-accent font-semibold mb-1">Ero</div>
                <div className="whitespace-pre-wrap text-sm">{w.ero_response}</div>
              </div>
            )}
          </div>
        </details>
      ))}
    </div>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-3 text-sm">
      <div className="w-28 text-textmuted text-xs uppercase tracking-wider">{label}</div>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Text({ label, v, onChange }) {
  return (
    <div>
      <label className="label">{label}</label>
      <textarea className="input min-h-[60px]" value={v} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

function Radio({ label, value, onChange, options }) {
  return (
    <div>
      <label className="label">{label}</label>
      <div className="flex gap-2">
        {options.map((o) => (
          <button
            key={o}
            type="button"
            onClick={() => onChange(o)}
            className={`flex-1 px-3 py-2 rounded-xl text-sm font-medium transition-all border ${
              value === o
                ? 'bg-accent border-accent text-white'
                : 'bg-surface2 border-line text-textmuted hover:text-white'
            }`}
          >
            {o}
          </button>
        ))}
      </div>
    </div>
  );
}

function PhotoUpload({ type, uploaded, uploading, onSelect }) {
  const id = `photo-${type}`;
  return (
    <label
      htmlFor={id}
      className={`aspect-square rounded-xl border-2 border-dashed flex items-center justify-center cursor-pointer transition-all overflow-hidden relative ${
        uploaded ? 'border-accent' : 'border-line hover:border-accent/50'
      }`}
    >
      {uploaded?.url ? (
        <img src={uploaded.url} alt={type} className="w-full h-full object-cover" />
      ) : uploading ? (
        <Spinner />
      ) : (
        <div className="text-center">
          <Upload size={18} className="mx-auto text-textmuted mb-1" />
          <div className="text-xs capitalize text-textmuted">{type}</div>
        </div>
      )}
      <input
        id={id}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && onSelect(e.target.files[0])}
      />
    </label>
  );
}
