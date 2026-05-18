import React, { useEffect, useMemo, useState } from 'react';
import {
  LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip, ReferenceLine, CartesianGrid,
} from 'recharts';
import { api } from '../lib/api.js';
import Spinner, { FullSpinner } from '../components/Spinner.jsx';
import ErrorBanner from '../components/ErrorBanner.jsx';

export default function Progress() {
  const [tab, setTab] = useState('weight');
  return (
    <div className="space-y-5 fade-in">
      <h1 className="text-2xl font-bold">Progress</h1>
      <div className="flex bg-surface2 p-1 rounded-xl text-xs w-full max-w-md">
        {[['weight', 'Weight'], ['lifts', 'Lifts'], ['photos', 'Photos']].map(([t, l]) => (
          <button
            key={t} onClick={() => setTab(t)}
            className={`flex-1 px-3 py-2 rounded-lg ${tab === t ? 'bg-accent text-white' : 'text-textmuted'}`}
          >
            {l}
          </button>
        ))}
      </div>
      {tab === 'weight' && <WeightTab />}
      {tab === 'lifts' && <LiftsTab />}
      {tab === 'photos' && <PhotosTab />}
    </div>
  );
}

function WeightTab() {
  const [weights, setWeights] = useState(null);
  const [me, setMe] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.get('/api/weights'), api.get('/api/me')])
      .then(([w, m]) => { setWeights(w); setMe(m); })
      .catch((e) => setError(e.message));
  }, []);

  if (!weights || !me) return <FullSpinner />;

  const data = weights.map((w) => ({
    date: new Date(w.logged_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    weight: w.weight_kg,
    ts: new Date(w.logged_at).getTime(),
  }));

  // 7-day rolling average
  const sorted = [...data].sort((a, b) => a.ts - b.ts);
  const withAvg = sorted.map((d, i) => {
    const window = sorted.slice(Math.max(0, i - 6), i + 1);
    const avg = window.reduce((s, x) => s + x.weight, 0) / window.length;
    return { ...d, avg: parseFloat(avg.toFixed(2)) };
  });

  const current = weights.length ? weights[weights.length - 1].weight_kg : null;
  const starting = me.starting_weight_kg;
  const goal = me.goal_weight_kg;

  return (
    <div className="space-y-4">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      <div className="grid grid-cols-3 gap-3">
        <Stat label="Current" value={current ? `${current.toFixed(1)} kg` : '—'} />
        <Stat label="Starting" value={`${starting.toFixed(1)} kg`} />
        <Stat label="Goal" value={`${goal.toFixed(1)} kg`} />
      </div>
      <div className="card">
        <div className="text-xs uppercase tracking-wider text-textmuted mb-3">Bodyweight history</div>
        {withAvg.length === 0 ? (
          <div className="text-center text-textmuted py-12">No weight logged yet.</div>
        ) : (
          <div style={{ width: '100%', height: 280 }}>
            <ResponsiveContainer>
              <LineChart data={withAvg}>
                <CartesianGrid stroke="#262626" strokeDasharray="3 3" />
                <XAxis dataKey="date" stroke="#6B7280" fontSize={11} />
                <YAxis stroke="#6B7280" fontSize={11} domain={['dataMin - 1', 'dataMax + 1']} />
                <Tooltip
                  contentStyle={{ background: '#1A1A1A', border: '1px solid #262626', borderRadius: 12 }}
                  labelStyle={{ color: '#9CA3AF' }}
                />
                <ReferenceLine y={goal} stroke="#3B82F6" strokeDasharray="4 4" label={{ value: 'Goal', fill: '#3B82F6', fontSize: 10 }} />
                <ReferenceLine y={starting} stroke="#6B7280" strokeDasharray="4 4" label={{ value: 'Start', fill: '#6B7280', fontSize: 10 }} />
                <Line type="monotone" dataKey="weight" stroke="#3B82F6" strokeWidth={2.5} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="avg" stroke="#9CA3AF" strokeWidth={1.5} strokeDasharray="5 3" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}

function LiftsTab() {
  const [exs, setExs] = useState([]);
  const [picked, setPicked] = useState('');
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get('/api/exercise-progress').then((r) => {
      setExs(r.exercises);
      if (r.exercises.length) setPicked(r.exercises[0]);
    }).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!picked) return;
    setData(null);
    api.get(`/api/exercise-progress?exercise_name=${encodeURIComponent(picked)}`)
      .then(setData).catch((e) => setError(e.message));
  }, [picked]);

  if (exs.length === 0) {
    return <div className="card text-center text-textmuted">Log some sets first to see exercise progress.</div>;
  }

  const points = (data?.points || []).map((p) => ({
    date: new Date(p.logged_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    weight: p.weight_kg,
    reps: p.reps,
  }));

  return (
    <div className="space-y-4">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      <select value={picked} onChange={(e) => setPicked(e.target.value)} className="input">
        {exs.map((e) => <option key={e} value={e}>{e}</option>)}
      </select>
      {!data ? <FullSpinner /> : (
        <div className="card">
          <div className="flex items-baseline justify-between mb-3">
            <div className="text-xs uppercase tracking-wider text-textmuted">{data.exercise_name}</div>
            <div className="text-sm">PB: <span className="font-bold text-accent">{data.personal_best_kg} kg</span></div>
          </div>
          {points.length === 0 ? (
            <div className="text-center text-textmuted py-12">No data yet.</div>
          ) : (
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer>
                <LineChart data={points}>
                  <CartesianGrid stroke="#262626" strokeDasharray="3 3" />
                  <XAxis dataKey="date" stroke="#6B7280" fontSize={11} />
                  <YAxis stroke="#6B7280" fontSize={11} />
                  <Tooltip
                    contentStyle={{ background: '#1A1A1A', border: '1px solid #262626', borderRadius: 12 }}
                  />
                  <Line type="monotone" dataKey="weight" stroke="#3B82F6" strokeWidth={2.5} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PhotosTab() {
  const [groups, setGroups] = useState(null);
  const [error, setError] = useState(null);
  const [compare, setCompare] = useState({ a: null, b: null });

  useEffect(() => {
    api.get('/api/photos').then(setGroups).catch((e) => setError(e.message));
  }, []);

  if (!groups) return <FullSpinner />;

  if (groups.length === 0) {
    return <div className="card text-center text-textmuted">Upload progress photos via the weekly check-in to see them here.</div>;
  }

  function pick(g) {
    if (!compare.a) setCompare({ a: g, b: null });
    else if (!compare.b && g.weekly_checkin_id !== compare.a.weekly_checkin_id) setCompare({ ...compare, b: g });
    else setCompare({ a: g, b: null });
  }

  return (
    <div className="space-y-4">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      <div className="flex items-center justify-between text-xs text-textmuted">
        <div>Tap two entries to compare</div>
        {(compare.a || compare.b) && (
          <button onClick={() => setCompare({ a: null, b: null })} className="text-accent hover:underline">Clear</button>
        )}
      </div>

      {compare.a && compare.b && (
        <div className="card space-y-3">
          <div className="grid grid-cols-2 gap-3 text-xs text-center text-textmuted">
            <div>{compare.a.week_start_date}</div>
            <div>{compare.b.week_start_date}</div>
          </div>
          {['front', 'side', 'back'].map((t) => {
            const ap = compare.a.photos.find((p) => p.type === t);
            const bp = compare.b.photos.find((p) => p.type === t);
            return (
              <div key={t} className="grid grid-cols-2 gap-3">
                <ImageOrEmpty src={ap?.url} label={t} />
                <ImageOrEmpty src={bp?.url} label={t} />
              </div>
            );
          })}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        {groups.map((g, i) => {
          const isPicked = compare.a?.weekly_checkin_id === g.weekly_checkin_id || compare.b?.weekly_checkin_id === g.weekly_checkin_id;
          return (
            <button key={g.weekly_checkin_id} onClick={() => pick(g)}
              className={`card card-hover text-left ${isPicked ? 'border-accent' : ''}`}>
              <div className="text-xs uppercase tracking-wider text-textmuted mb-2">Week {groups.length - i}</div>
              <div className="text-sm font-medium mb-2">{g.week_start_date}</div>
              <div className="grid grid-cols-3 gap-1">
                {['front', 'side', 'back'].map((t) => {
                  const p = g.photos.find((x) => x.type === t);
                  return <ImageOrEmpty key={t} src={p?.url} label={t} small />;
                })}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ImageOrEmpty({ src, label, small }) {
  return (
    <div className={`rounded-lg bg-surface2 border border-line overflow-hidden ${small ? 'aspect-square' : 'aspect-[3/4]'}`}>
      {src ? (
        <img src={src} alt={label} className="w-full h-full object-cover" />
      ) : (
        <div className="w-full h-full flex items-center justify-center text-textmuted text-xs capitalize">{label}</div>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="card">
      <div className="text-xs uppercase tracking-wider text-textmuted">{label}</div>
      <div className="text-xl font-bold mt-1">{value}</div>
    </div>
  );
}
