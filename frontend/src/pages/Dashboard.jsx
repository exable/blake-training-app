import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Dumbbell, Droplets, UtensilsCrossed, ClipboardCheck, Scale, MessageCircle, ChevronRight, CheckCircle2,
} from 'lucide-react';
import { api } from '../lib/api.js';
import Spinner, { FullSpinner } from '../components/Spinner.jsx';
import ErrorBanner from '../components/ErrorBanner.jsx';

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Morning';
  if (h < 17) return 'Afternoon';
  return 'Evening';
}

function fmtDate(d) {
  return new Date(d).toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' });
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [logging, setLogging] = useState(false);
  const [w, setW] = useState('');

  async function load() {
    setError(null);
    try {
      const d = await api.get('/api/dashboard');
      setData(d);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function logWeight() {
    if (!w) return;
    setLogging(true);
    try {
      await api.post('/api/weights', { weight_kg: parseFloat(w) });
      setW('');
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setLogging(false);
    }
  }

  if (!data) return <FullSpinner />;

  const meals = data.meals_total || 0;
  const waterPct = Math.min(100, Math.round((data.water_ml / (data.water_target_ml || 3000)) * 100));
  const mealsPct = meals ? Math.round((data.meals_eaten / meals) * 100) : 0;

  return (
    <div className="space-y-5 fade-in">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div>
        <div className="text-textmuted text-sm">{fmtDate(data.date)}</div>
        <h1 className="text-2xl md:text-3xl font-bold mt-0.5">{greeting()}, Blake.</h1>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          icon={<Scale className="text-accent" size={18} />}
          label="Bodyweight"
          value={data.latest_weight_kg ? `${data.latest_weight_kg.toFixed(1)} kg` : '—'}
        />
        <StatCard
          icon={<Dumbbell className="text-accent" size={18} />}
          label="Today's Session"
          value={data.session_swapped ? data.session_type_actual : data.session_type_today}
          sub={
            data.session_completed
              ? (data.session_swapped
                  ? `Completed (swapped from ${data.session_type_today})`
                  : 'Completed')
              : data.session_started
                ? (data.session_swapped
                    ? `In progress (swapped from ${data.session_type_today})`
                    : 'In progress')
                : data.session_type_today === 'Rest' ? 'Rest day' : 'Not started'
          }
        />
        <StatCard
          icon={<UtensilsCrossed className="text-accent" size={18} />}
          label="Meals"
          value={`${data.meals_eaten}/${meals}`}
          sub={`${mealsPct}%`}
        />
        <StatCard
          icon={<Droplets className="text-accent" size={18} />}
          label="Water"
          value={`${(data.water_ml / 1000).toFixed(2)} L`}
          sub={`${waterPct}% of ${(data.water_target_ml / 1000)} L`}
        />
      </div>

      {/* Today's status */}
      <div className="grid md:grid-cols-2 gap-3">
        <StatusRow
          done={data.session_completed}
          label="Today's training"
          sub={
            data.session_type_today === 'Rest'
              ? 'Rest day — recover'
              : data.session_swapped
                ? `${data.session_type_actual} (swapped from ${data.session_type_today})`
                : data.session_type_today
          }
          to="/workout"
        />
        <StatusRow
          done={meals > 0 && data.meals_eaten === meals}
          label="Nutrition"
          sub={`${data.meals_eaten}/${meals} meals logged`}
          to="/nutrition"
        />
        <StatusRow
          done={data.daily_checkin_done}
          label="Daily check-in"
          sub={data.daily_checkin_done ? 'Submitted' : 'Pending'}
          to="/checkins"
        />
        <StatusRow
          done={data.water_ml >= data.water_target_ml}
          label="Water target"
          sub={`${data.water_ml}ml / ${data.water_target_ml}ml`}
          to="/nutrition"
        />
      </div>

      {/* Quick weight log */}
      <div className="card space-y-3">
        <div className="flex items-center justify-between">
          <div className="font-semibold">Quick log bodyweight</div>
          <Scale size={16} className="text-textmuted" />
        </div>
        <div className="flex gap-2">
          <input
            inputMode="decimal"
            type="number"
            step="0.1"
            value={w}
            onChange={(e) => setW(e.target.value)}
            placeholder="kg"
            className="input flex-1"
          />
          <button onClick={logWeight} disabled={logging || !w} className="btn btn-primary px-5">
            {logging ? <Spinner /> : 'Log'}
          </button>
        </div>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-2 gap-3">
        <Link to="/workout" className="card card-hover flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Dumbbell size={18} className="text-accent" />
            <span className="font-medium">Start workout</span>
          </div>
          <ChevronRight size={16} className="text-textmuted" />
        </Link>
        <Link to="/chat" className="card card-hover flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MessageCircle size={18} className="text-accent" />
            <span className="font-medium">Chat with Ero</span>
          </div>
          <ChevronRight size={16} className="text-textmuted" />
        </Link>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, sub }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 text-textmuted text-xs uppercase tracking-wider mb-2">
        {icon}{label}
      </div>
      <div className="text-xl md:text-2xl font-bold">{value}</div>
      {sub && <div className="text-xs text-textmuted mt-1">{sub}</div>}
    </div>
  );
}

function StatusRow({ done, label, sub, to }) {
  return (
    <Link to={to} className="card card-hover flex items-center gap-3">
      <CheckCircle2
        size={20}
        className={done ? 'text-accent' : 'text-textmuted/40'}
      />
      <div className="flex-1">
        <div className="font-medium text-sm">{label}</div>
        <div className="text-xs text-textmuted">{sub}</div>
      </div>
      <ChevronRight size={16} className="text-textmuted" />
    </Link>
  );
}
