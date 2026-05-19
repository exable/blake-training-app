import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ChevronRight, Play, Pause, RotateCcw, Check, Clock, Flame, History, ArrowLeft, Trophy, X, Bell } from 'lucide-react';
import { api } from '../lib/api.js';
import Spinner, { FullSpinner } from '../components/Spinner.jsx';
import ErrorBanner from '../components/ErrorBanner.jsx';
import useDraft from '../lib/useDraft.js';
import { ensureNotifyPermission, notify, beep, vibrate } from '../lib/notify.js';

function fmtClock(totalSec) {
  const s = Math.max(0, Math.floor(totalSec));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${String(m).padStart(2, '0')}:${String(r).padStart(2, '0')}`;
}

const SESSION_TYPES = ['Upper', 'Lower', 'Push', 'Pull', 'Legs'];

export default function Workout() {
  const [program, setProgram] = useState(null);
  const [view, setView] = useState('select'); // select | live | history | session
  const [activeSession, setActiveSession] = useState(null);
  const [activeType, setActiveType] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyFilter, setHistoryFilter] = useState('');
  const [openSession, setOpenSession] = useState(null);
  const [error, setError] = useState(null);

  async function loadProgram() {
    try {
      const p = await api.get('/api/program');
      setProgram(p);
      setActiveType(p._today === 'Rest' ? 'Upper' : p._today);
      // Resume any in-progress session
      const ip = await api.get('/api/sessions/in-progress');
      if (ip.in_progress) {
        setActiveSession(ip.session);
        setActiveType(ip.session.session_type);
        setView('live');
      }
    } catch (e) {
      setError(e.message);
    }
  }

  async function loadHistory() {
    try {
      const rows = await api.get(`/api/sessions${historyFilter ? `?session_type=${historyFilter}` : ''}`);
      setHistory(rows);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { loadProgram(); }, []);
  useEffect(() => { if (view === 'history') loadHistory(); }, [view, historyFilter]);

  async function startSession(stype) {
    setError(null);
    try {
      const s = await api.post('/api/sessions', { session_type: stype });
      setActiveSession(s);
      setActiveType(stype);
      setView('live');
    } catch (e) { setError(e.message); }
  }

  if (!program) return <FullSpinner />;

  if (view === 'live' && activeSession) {
    return (
      <LiveWorkout
        session={activeSession}
        sessionData={program[activeSession.session_type]}
        onDone={async () => { setView('select'); setActiveSession(null); await loadProgram(); }}
        onCancel={() => { setView('select'); setActiveSession(null); }}
      />
    );
  }

  if (view === 'session' && openSession) {
    return <SessionDetail session={openSession} onBack={() => setView('history')} />;
  }

  return (
    <div className="space-y-5 fade-in">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Workout</h1>
        <div className="flex bg-surface2 p-1 rounded-xl text-xs">
          <button
            onClick={() => setView('select')}
            className={`px-3 py-1.5 rounded-lg ${view !== 'history' ? 'bg-accent text-white' : 'text-textmuted'}`}
          >
            Sessions
          </button>
          <button
            onClick={() => setView('history')}
            className={`px-3 py-1.5 rounded-lg ${view === 'history' ? 'bg-accent text-white' : 'text-textmuted'}`}
          >
            History
          </button>
        </div>
      </div>

      {view === 'select' && (
        <SessionPicker
          program={program}
          today={program._today}
          onPick={startSession}
        />
      )}

      {view === 'history' && (
        <div className="space-y-3">
          <div className="flex gap-2 overflow-x-auto pb-1">
            <FilterChip active={historyFilter === ''} onClick={() => setHistoryFilter('')}>All</FilterChip>
            {SESSION_TYPES.map((t) => (
              <FilterChip key={t} active={historyFilter === t} onClick={() => setHistoryFilter(t)}>{t}</FilterChip>
            ))}
          </div>
          {history.length === 0 && (
            <div className="card text-center text-textmuted">No sessions logged yet.</div>
          )}
          {history.map((s) => (
            <button
              key={s.id}
              onClick={() => { setOpenSession(s); setView('session'); }}
              className="card card-hover w-full text-left"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold">{s.session_type}</div>
                  <div className="text-xs text-textmuted">
                    {new Date(s.started_at).toLocaleString()}
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs text-textmuted">
                  <span>{s.sets.length} sets</span>
                  <ChevronRight size={16} />
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function SessionPicker({ program, today, onPick }) {
  return (
    <div className="space-y-3">
      {today !== 'Rest' && (
        <div className="card bg-accent/5 border-accent/30">
          <div className="text-xs uppercase tracking-wider text-accent mb-1">Today's session</div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xl font-bold">{today}</div>
              <div className="text-xs text-textmuted mt-0.5">
                {program[today]?.exercises?.length || 0} exercises · ~{Math.round((program[today]?.exercises?.length || 0) * 8)} min
              </div>
            </div>
            <button onClick={() => onPick(today)} className="btn btn-primary pulse-ring">
              <Play size={16} /> Start
            </button>
          </div>
        </div>
      )}
      {today === 'Rest' && (
        <div className="card text-center">
          <div className="text-textmuted text-sm">Rest day — recover. You can still log a session if you'd like.</div>
        </div>
      )}
      <div className="text-xs uppercase tracking-wider text-textmuted px-1">All sessions</div>
      {SESSION_TYPES.map((stype) => (
        <button key={stype} onClick={() => onPick(stype)} className="card card-hover w-full text-left">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold">{stype}</div>
              <div className="text-xs text-textmuted mt-0.5">
                {program[stype]?.exercises?.length || 0} exercises · ~{Math.round((program[stype]?.exercises?.length || 0) * 8)} min
              </div>
            </div>
            <ChevronRight size={16} className="text-textmuted" />
          </div>
        </button>
      ))}
    </div>
  );
}

function FilterChip({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
        active ? 'bg-accent text-white' : 'bg-surface2 text-textmuted border border-line hover:text-white'
      }`}
    >
      {children}
    </button>
  );
}

function LiveWorkout({ session, sessionData, onDone, onCancel }) {
  const exercises = sessionData?.exercises || [];
  const previous = sessionData?.previous || {};
  // Draft state is persisted in localStorage; this is what survives an app close.
  // - inputs: per-set values (weight/reps/logged)
  // - prefilled: per-exercise, have we copied last session's values into inputs yet?
  // - restEndTs / restTotal / restPaused / restRemainingOnPause: TIMESTAMP-based timer so it
  //   keeps counting correctly when the app is backgrounded / closed and reopened later.
  const [draft, setDraft, clearDraft] = useDraft(`live-${session.id}`, {
    exIdx: 0,
    inputs: {},
    restEndTs: 0,
    restTotal: 0,
    restPaused: false,
    restRemainingOnPause: 0,
    notifyAsked: false,
  });

  const [now, setNow] = useState(() => Date.now());  // ticks every second for re-renders
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const prevRestRemaining = useRef(null);

  // Single 1s tick that drives BOTH the elapsed clock and the rest timer.
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    const onVis = () => setNow(Date.now());
    document.addEventListener('visibilitychange', onVis);
    window.addEventListener('focus', onVis);
    return () => {
      clearInterval(id);
      document.removeEventListener('visibilitychange', onVis);
      window.removeEventListener('focus', onVis);
    };
  }, []);

  // Ask for notification permission once.
  useEffect(() => {
    if (!draft.notifyAsked) {
      ensureNotifyPermission().finally(() =>
        setDraft((d) => ({ ...d, notifyAsked: true }))
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Derive rest-timer state from draft + now (single source of truth).
  const restTotal = draft.restTotal || 0;
  const restRemaining = draft.restPaused
    ? draft.restRemainingOnPause
    : Math.max(0, Math.ceil((draft.restEndTs - now) / 1000));
  const restActive = restTotal > 0 && restRemaining > 0;

  // Fire notification + beep at the transition from >0 → 0.
  useEffect(() => {
    if (prevRestRemaining.current > 0 && restRemaining === 0 && restTotal > 0) {
      beep();
      vibrate([300, 120, 300]);
      notify('Rest over', 'Get back to it 💪');
      // Auto-clear so the banner disappears
      setDraft((d) => ({ ...d, restEndTs: 0, restTotal: 0, restPaused: false }));
    }
    prevRestRemaining.current = restRemaining;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [restRemaining, restTotal]);

  // Total session elapsed
  const startedAtMs = useMemo(
    () => (session.started_at ? new Date(session.started_at).getTime() : Date.now()),
    [session.started_at]
  );
  const elapsed = Math.max(0, Math.floor((now - startedAtMs) / 1000));

  function startRest(seconds) {
    setDraft((d) => ({
      ...d,
      restTotal: seconds,
      restEndTs: Date.now() + seconds * 1000,
      restPaused: false,
      restRemainingOnPause: 0,
    }));
  }

  function pauseResumeRest() {
    setDraft((d) => {
      if (d.restPaused) {
        // resume
        const remaining = d.restRemainingOnPause;
        return {
          ...d,
          restPaused: false,
          restEndTs: Date.now() + remaining * 1000,
          restRemainingOnPause: 0,
        };
      }
      // pause
      const remaining = Math.max(0, Math.ceil((d.restEndTs - Date.now()) / 1000));
      return { ...d, restPaused: true, restRemainingOnPause: remaining };
    });
  }

  function resetRest() {
    setDraft((d) => ({ ...d, restEndTs: 0, restTotal: 0, restPaused: false, restRemainingOnPause: 0 }));
  }

  const ex = exercises[draft.exIdx];
  const prevSets = ex ? (previous[ex.name] || []) : [];

  function inputsFor(exIdx, setIdx) {
    return draft.inputs[exIdx]?.[setIdx] || {};
  }

  function updateInput(exIdx, setIdx, patch) {
    setDraft((d) => {
      const exMap = { ...(d.inputs[exIdx] || {}) };
      exMap[setIdx] = { ...(exMap[setIdx] || {}), ...patch };
      return { ...d, inputs: { ...d.inputs, [exIdx]: exMap } };
    });
  }

  async function logSet(setIdx) {
    if (!ex) return;
    const cur = inputsFor(draft.exIdx, setIdx);
    if (!cur.weight || !cur.reps) {
      setError('Enter weight and reps first.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.post(`/api/sessions/${session.id}/sets`, {
        exercise_name: ex.name,
        set_number: setIdx + 1,
        weight_kg: parseFloat(cur.weight),
        reps: parseInt(cur.reps, 10),
        rpe: cur.rpe ? parseFloat(cur.rpe) : null,
      });
      updateInput(draft.exIdx, setIdx, { logged: true });
      startRest(ex.rest);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function logCardioDone() {
    if (!ex) return;
    setBusy(true);
    setError(null);
    try {
      await api.post(`/api/sessions/${session.id}/sets`, {
        exercise_name: ex.name,
        set_number: 1,
        weight_kg: 0,
        reps: 1,
        rpe: null,
      });
      updateInput(draft.exIdx, 0, { logged: true, cardio: true });
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  function next() {
    if (draft.exIdx < exercises.length - 1) {
      setDraft({ ...draft, exIdx: draft.exIdx + 1 });
    }
  }
  function prev() {
    if (draft.exIdx > 0) {
      setDraft({ ...draft, exIdx: draft.exIdx - 1 });
    }
  }

  if (!ex) return <div className="card">No exercises configured.</div>;

  const setIdxs = Array.from({ length: ex.sets }, (_, i) => i);
  const allLogged = ex.cardio
    ? !!inputsFor(draft.exIdx, 0).logged
    : setIdxs.every((i) => inputsFor(draft.exIdx, i).logged);

  return (
    <div className="space-y-4 fade-in pb-24">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="flex items-center justify-between">
        <button onClick={onCancel} className="btn btn-ghost px-2">
          <ArrowLeft size={18} />
        </button>
        <div className="text-center">
          <div className="text-xs uppercase tracking-wider text-textmuted flex items-center justify-center gap-2">
            <span>{session.session_type}</span>
            <span className="text-textmuted/60">·</span>
            <span className="tabular-nums text-accent">{fmtClock(elapsed)}</span>
          </div>
          <div className="text-sm font-semibold">Exercise {draft.exIdx + 1} of {exercises.length}</div>
        </div>
        <button onClick={() => setShowSummary(true)} disabled={busy} className="btn btn-primary text-xs">
          Finish
        </button>
      </div>

      {showSummary && (
        <CompletionModal
          sessionId={session.id}
          onClose={() => setShowSummary(false)}
          onDone={() => { clearDraft(); onDone(); }}
        />
      )}

      {/* Rest timer */}
      {restActive && (
        <div className="card flex items-center justify-between bg-accent/5 border-accent/30 pulse-ring">
          <div className="flex items-center gap-3">
            <Clock size={20} className="text-accent" />
            <div>
              <div className="text-xs text-textmuted uppercase">Rest{draft.restPaused ? ' (paused)' : ''}</div>
              <div className="text-3xl font-bold tabular-nums">{fmtClock(restRemaining)}</div>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={pauseResumeRest} className="btn btn-secondary px-3">
              {draft.restPaused ? <Play size={16} /> : <Pause size={16} />}
            </button>
            <button onClick={resetRest} className="btn btn-secondary px-3">
              <RotateCcw size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Re-prompt notification permission if user dismissed it */}
      {typeof Notification !== 'undefined' && Notification.permission === 'default' && (
        <button
          onClick={() => ensureNotifyPermission()}
          className="card card-hover w-full flex items-center gap-3 text-left text-sm"
        >
          <Bell size={16} className="text-accent" />
          <span className="flex-1">Enable rest-timer notifications</span>
          <ChevronRight size={14} className="text-textmuted" />
        </button>
      )}

      <div className="card">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="text-lg font-bold">{ex.name}</div>
            <div className="text-xs text-textmuted mt-0.5">
              {ex.sets}× {ex.rep_range} reps
              {ex.rpe && <span> · RPE {ex.rpe}</span>}
              <span> · {Math.round(ex.rest / 60 * 10) / 10}min rest</span>
            </div>
          </div>
          {allLogged && <Check size={20} className="text-accent" />}
        </div>

        {ex.cardio ? (
          <CardioRow
            done={!!inputsFor(draft.exIdx, 0).logged}
            duration={ex.rep_range}
            busy={busy}
            onDone={logCardioDone}
          />
        ) : (
          <div className="space-y-2">
            {setIdxs.map((i) => {
              const prev = prevSets[i];
              const cur = inputsFor(draft.exIdx, i);
              return (
                <div key={i} className="rounded-xl bg-surface2 p-3 border border-line">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-xs uppercase tracking-wider text-textmuted">Set {i + 1}</div>
                    {prev && (
                      <div className="text-[11px] text-textmuted">
                        Last: <span className="text-white">{prev.weight_kg}kg × {prev.reps}</span>
                      </div>
                    )}
                  </div>
                  <div className="grid grid-cols-3 gap-2 items-end">
                    <div>
                      <label className="label">Weight</label>
                      <input
                        inputMode="decimal"
                        type="number"
                        step="0.5"
                        placeholder={prev ? `${prev.weight_kg}` : 'kg'}
                        value={cur.weight || ''}
                        onChange={(e) => updateInput(draft.exIdx, i, { weight: e.target.value })}
                        disabled={cur.logged}
                        className="input text-base"
                      />
                    </div>
                    <div>
                      <label className="label">Reps</label>
                      <input
                        inputMode="numeric"
                        type="number"
                        placeholder={prev ? `${prev.reps}` : 'reps'}
                        value={cur.reps || ''}
                        onChange={(e) => updateInput(draft.exIdx, i, { reps: e.target.value })}
                        disabled={cur.logged}
                        className="input text-base"
                      />
                    </div>
                    <div>
                      {cur.logged ? (
                        <div className="btn btn-secondary w-full">
                          <Check size={16} /> Done
                        </div>
                      ) : (
                        <button onClick={() => logSet(i)} disabled={busy} className="btn btn-primary w-full">
                          {busy ? <Spinner /> : 'Log'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <button onClick={prev} disabled={draft.exIdx === 0} className="btn btn-secondary flex-1">
          Previous
        </button>
        <button
          onClick={next}
          disabled={draft.exIdx >= exercises.length - 1}
          className="btn btn-primary flex-1"
        >
          Next exercise
        </button>
      </div>
    </div>
  );
}

function CardioRow({ done, duration, busy, onDone }) {
  return (
    <div className="rounded-xl bg-surface2 p-4 border border-line flex items-center justify-between">
      <div>
        <div className="text-xs uppercase tracking-wider text-textmuted">Cardio</div>
        <div className="text-sm font-medium mt-0.5">Complete {duration}</div>
      </div>
      {done ? (
        <div className="btn btn-secondary">
          <Check size={16} /> Done
        </div>
      ) : (
        <button onClick={onDone} disabled={busy} className="btn btn-primary">
          {busy ? <Spinner /> : 'Mark done'}
        </button>
      )}
    </div>
  );
}

function CompletionModal({ sessionId, onClose, onDone }) {
  const [notes, setNotes] = useState('');
  const [difficulty, setDifficulty] = useState(7);
  const [result, setResult] = useState(null); // null = form, object = post-submit summary
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const res = await api.post(`/api/sessions/${sessionId}/complete`, {
        notes, difficulty,
      });
      setResult(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-end md:items-center justify-center p-4 fade-in">
      <div className="bg-surface border border-line rounded-2xl w-full max-w-md p-5 slide-up max-h-[90vh] overflow-y-auto">
        {!result ? (
          <>
            <div className="flex items-center justify-between mb-4">
              <div className="font-semibold">Finish session</div>
              <button onClick={onClose} className="text-textmuted hover:text-white"><X size={18} /></button>
            </div>
            <ErrorBanner error={error} onDismiss={() => setError(null)} />
            <div className="space-y-4">
              <div>
                <label className="label">How hard? <span className="text-white">{difficulty}/10</span></label>
                <input
                  type="range" min="1" max="10" value={difficulty}
                  onChange={(e) => setDifficulty(parseInt(e.target.value, 10))}
                  className="w-full accent-accent"
                />
                <div className="flex justify-between text-[10px] text-textmuted mt-1">
                  <span>easy</span><span>brutal</span>
                </div>
              </div>
              <div>
                <label className="label">Notes</label>
                <textarea
                  className="input min-h-[80px]"
                  placeholder="How did it feel? Anything off? Anything you crushed?"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>
            </div>
            <div className="flex gap-2 mt-5">
              <button onClick={onClose} className="btn btn-secondary flex-1">
                Cancel
              </button>
              <button onClick={submit} disabled={busy} className="btn btn-primary flex-1">
                {busy ? <Spinner /> : 'Complete session'}
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="text-center mb-4">
              <div className="w-14 h-14 mx-auto rounded-full bg-accent/10 border border-accent/30 flex items-center justify-center mb-3">
                <Trophy size={26} className="text-accent" />
              </div>
              <div className="text-xl font-bold">Session complete</div>
              <div className="text-xs text-textmuted mt-1">
                {result.sets.length} sets · difficulty {result.difficulty}/10
              </div>
            </div>

            {result.achievements?.length > 0 ? (
              <div className="space-y-2 mb-4">
                <div className="text-xs uppercase tracking-wider text-accent">Progressive overload wins</div>
                {result.achievements.map((a) => (
                  <div key={a.exercise} className="rounded-xl bg-surface2 border border-line p-3">
                    <div className="font-semibold text-sm">{a.exercise}</div>
                    <ul className="mt-1 space-y-0.5">
                      {a.wins.map((w, i) => (
                        <li key={i} className="text-xs text-textmuted flex gap-2">
                          <span className="text-accent">▲</span><span>{w}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-textmuted text-sm py-4 mb-2">
                No new PRs this session — solid work though, consistency wins.
              </div>
            )}

            {result.notes && (
              <div className="rounded-xl bg-surface2 border border-line p-3 mb-4">
                <div className="text-xs uppercase tracking-wider text-textmuted mb-1">Notes</div>
                <div className="text-sm whitespace-pre-wrap">{result.notes}</div>
              </div>
            )}

            <button onClick={onDone} className="btn btn-primary w-full">
              Done
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function SessionDetail({ session, onBack }) {
  const groups = useMemo(() => {
    const m = {};
    session.sets.forEach((s) => {
      (m[s.exercise_name] = m[s.exercise_name] || []).push(s);
    });
    return m;
  }, [session]);
  return (
    <div className="space-y-4 fade-in">
      <button onClick={onBack} className="btn btn-ghost px-2">
        <ArrowLeft size={18} /> Back
      </button>
      <div className="card">
        <div className="text-xs uppercase tracking-wider text-textmuted">Session</div>
        <div className="text-xl font-bold">{session.session_type}</div>
        <div className="text-xs text-textmuted mt-1">
          {new Date(session.started_at).toLocaleString()}
          {session.completed_at && ` · Completed ${new Date(session.completed_at).toLocaleTimeString()}`}
        </div>
        {session.difficulty != null && (
          <div className="text-xs text-textmuted mt-1">Difficulty: <span className="text-white">{session.difficulty}/10</span></div>
        )}
        {session.notes && (
          <div className="text-sm mt-3 p-3 bg-surface2 rounded-xl border border-line whitespace-pre-wrap">{session.notes}</div>
        )}
      </div>
      {Object.entries(groups).map(([ex, sets]) => (
        <div key={ex} className="card">
          <div className="font-semibold mb-2">{ex}</div>
          <div className="space-y-1">
            {sets.map((s) => (
              <div key={s.id} className="text-sm flex justify-between border-b border-line/50 pb-1">
                <span className="text-textmuted">Set {s.set_number}</span>
                <span>{s.weight_kg}kg × {s.reps}{s.rpe ? ` @ RPE ${s.rpe}` : ''}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
