import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, Check, Keyboard, Mic, PhoneOff, SkipForward, Volume2, VolumeX } from 'lucide-react';
import { speak, stopSpeaking, startListening, voiceInputSupported, voiceOutputSupported } from '../lib/voice.js';
import PhotoUpload from './PhotoUpload.jsx';

/*
 * A check-in as a phone call: Ero asks one question at a time (spoken + on screen),
 * the mic opens, you answer, it moves on. Numbers and yes/no answers are parsed from
 * speech; free text is kept verbatim. Everything can be typed instead, and the review
 * screen lets you fix anything before it submits through the normal API.
 */

const CHOICE_MAP = [
  [/rest/i, 'Rest Day'],
  [/partial|kind of|kinda|sort of|mostly|half|some/i, 'Partially'],
  [/\b(yes|yeah|yep|yup|yes i did|did|nailed|sure|correct|absolutely)\b/i, 'Yes'],
  [/\b(no|nah|nope|didn't|did not|missed|skipped)\b/i, 'No'],
];

const WORDS = { zero: 0, one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10,
  eleven: 11, twelve: 12, thirteen: 13, fourteen: 14, fifteen: 15, sixteen: 16, seventeen: 17, eighteen: 18, nineteen: 19,
  twenty: 20, thirty: 30, forty: 40, fifty: 50, sixty: 60, seventy: 70, eighty: 80, ninety: 90 };

export function parseNumber(text) {
  if (!text) return null;
  const digit = text.replace(',', '.').match(/-?\d+(\.\d+)?/);
  if (digit) return parseFloat(digit[0]);
  const t = text.toLowerCase().replace(/-/g, ' ');
  const toks = t.split(/\s+/);
  let total = 0, found = false, i = 0;
  for (; i < toks.length; i++) {
    const w = toks[i];
    if (w in WORDS) { total += WORDS[w]; found = true; }
    else if (found && w !== 'and') break;
  }
  if (!found) return null;
  if (toks[i] === 'point' && toks[i + 1] in WORDS) total += WORDS[toks[i + 1]] / 10;
  return total;
}

export function parseChoice(text, options) {
  if (!text) return null;
  for (const [re, value] of CHOICE_MAP) {
    if (options.includes(value) && re.test(text)) return value;
  }
  const direct = options.find((o) => text.toLowerCase().includes(o.toLowerCase()));
  return direct || null;
}

const daily = [
  { key: 'weight_kg', type: 'number', ask: "Morning, bro. What did the scale say today?", unit: 'kg', optional: true },
  { key: 'sleep_quality', type: 'scale', ask: 'Sleep last night, one to ten?' },
  { key: 'nutrition_adherence', type: 'choice', ask: 'Did you nail your nutrition today?', options: ['Yes', 'Partially', 'No'] },
  { key: 'trained_today', type: 'choice', ask: 'Did you train today?', options: ['Yes', 'No', 'Rest Day'] },
  { key: 'proud_1', type: 'text', ask: "Three things you're proud of today. Give me the first one." },
  { key: 'proud_2', type: 'text', ask: 'Second one.' },
  { key: 'proud_3', type: 'text', ask: 'And the third.' },
  { key: 'notes', type: 'text', ask: 'Anything else worth noting? Say skip if not.', optional: true },
];

const weekly = [
  { key: 'weight_kg', type: 'number', ask: "Weekly check-in. What's your weight this morning?", unit: 'kg', optional: true },
  { key: 'nutrition_review', type: 'text', ask: 'Nutrition this week. Did you stick to it? If not, why?' },
  { key: 'diet_changes', type: 'text', ask: 'Anything you want to change in the diet? Say skip if not.', optional: true },
  { key: 'training_review', type: 'text', ask: 'Training. Did you train every day you were meant to?' },
  { key: 'performance_improved', type: 'choice', ask: 'Did performance improve in the gym this week?', options: ['Yes', 'Partially', 'No'] },
  { key: 'could_do_better', type: 'text', ask: 'What could you have done better?' },
  { key: 'proud_of', type: 'text', ask: 'What went well. What are you proud of?' },
  { key: 'main_goal', type: 'text', ask: 'Main goal for the upcoming week?' },
  { key: 'sleep_hours', type: 'number', ask: 'Average sleep per night, in hours?', unit: 'h', optional: true },
  { key: 'sleep_quality', type: 'text', ask: 'How was the sleep quality?', optional: true },
  { key: 'support_needed', type: 'text', ask: 'Where do you need more support from me? Say skip if nothing.', optional: true },
  { key: 'energy', type: 'scale', ask: 'Quick ratings. Energy this week, one to ten?' },
  { key: 'fatigue', type: 'scale', ask: 'Fatigue, one to ten?' },
  { key: 'digestion', type: 'scale', ask: 'Digestion, one to ten?' },
  { key: 'hunger', type: 'scale', ask: 'Hunger, one to ten?' },
  { key: 'recovery', type: 'scale', ask: 'Recovery, one to ten?' },
  { key: '_photos', type: 'photos', ask: 'Last thing. Progress photos. Front, side and back when you are ready, then hit done.', optional: true },
];

export const CALL_SCRIPTS = { daily, weekly };

export default function CheckinCall({ kind, form, setForm, photos, uploadingType, onUploadPhoto, onSubmit, onClose, busy }) {
  const script = CALL_SCRIPTS[kind];
  const [step, setStep] = useState(0);
  const [phase, setPhase] = useState('intro'); // intro | asking | review
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [parsed, setParsed] = useState(null);
  const [typing, setTyping] = useState(false);
  const [voiceOn, setVoiceOn] = useState(voiceOutputSupported);
  const [autoAdvanceAt, setAutoAdvanceAt] = useState(null);
  const [hint, setHint] = useState('');
  const recRef = useRef(null);
  const advanceTimer = useRef(null);
  const stepRef = useRef(0);
  const formRef = useRef(form);
  const voiceOnRef = useRef(voiceOn);
  stepRef.current = step;
  formRef.current = form;
  voiceOnRef.current = voiceOn;
  const q = script[step];

  const cancelTimers = useCallback(() => {
    if (advanceTimer.current) clearTimeout(advanceTimer.current);
    advanceTimer.current = null;
    setAutoAdvanceAt(null);
  }, []);

  const stopMic = useCallback(() => {
    try { recRef.current?.stop?.(); } catch {}
    recRef.current = null;
    setListening(false);
  }, []);

  useEffect(() => () => { stopMic(); stopSpeaking(); cancelTimers(); }, [stopMic, cancelTimers]);

  const listen = useCallback(() => {
    const cur = script[stepRef.current];
    if (!voiceInputSupported || !cur || cur.type === 'photos') return;
    stopMic();
    setTranscript('');
    setParsed(null);
    setHint('');
    setListening(true);
    recRef.current = startListening({
      onResult: (t) => setTranscript(t),
      onEnd: (finalText) => {
        setListening(false);
        recRef.current = null;
        handleAnswer(finalText || transcriptRef.current);
      },
      onError: (e) => {
        setListening(false);
        recRef.current = null;
        const code = e?.error || '';
        if (code === 'no-speech') setHint("Didn't catch that. Tap the mic and go again, or type it.");
        else if (code === 'not-allowed') setHint('Mic blocked. Allow microphone access in your browser settings, or type your answer.');
        else if (code !== 'aborted') setHint('Voice failed. Tap the mic to retry, or type it.');
      },
    });
    if (!recRef.current) setListening(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [script, stopMic]);

  const transcriptRef = useRef('');
  useEffect(() => { transcriptRef.current = transcript; }, [transcript]);

  function ask(i) {
    const item = script[i];
    if (!item) return;
    cancelTimers();
    stopMic();
    setTranscript('');
    setParsed(null);
    setTyping(false);
    setHint('');
    if (voiceOnRef.current && voiceOutputSupported) {
      setSpeaking(true);
      speakThen(item.ask, () => {
        setSpeaking(false);
        if (item.type !== 'photos') listen();
      });
    } else if (item.type !== 'photos') {
      listen();
    }
  }

  function speakThen(text, done) {
    try {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 1.05;
      u.pitch = 0.95;
      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find((v) => /Daniel|Alex|Google UK English Male|Microsoft Mark/.test(v.name)) || voices.find((v) => /en-AU|en-GB|en-US/.test(v.lang));
      if (preferred) u.voice = preferred;
      let finished = false;
      const finish = () => { if (!finished) { finished = true; done(); } };
      u.onend = finish;
      u.onerror = finish;
      window.speechSynthesis.speak(u);
      setTimeout(finish, Math.min(12000, 1500 + text.length * 70));
    } catch {
      done();
    }
  }

  function commit(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function handleAnswer(text) {
    const t = (text || '').trim();
    const q = script[stepRef.current];
    const form = formRef.current;
    if (!q) return;
    if (/^(skip|skip it|nothing|nah nothing|no notes|pass)\b/i.test(t) && (q.optional || q.type === 'text')) {
      commit(q.key, q.type === 'text' ? '' : form[q.key]);
      return next();
    }
    if (/^(go )?back\b/i.test(t)) return back();
    if (!t) { setHint("Didn't catch that. Tap the mic to try again, or type it."); return; }

    if (q.type === 'number' || q.type === 'scale') {
      const n = parseNumber(t);
      if (n === null || (q.type === 'scale' && (n < 1 || n > 10))) {
        setHint(q.type === 'scale' ? 'Need a number from 1 to 10.' : 'Need a number - try again or type it.');
        return;
      }
      const v = q.type === 'scale' ? Math.round(n) : n;
      setParsed(String(v));
      commit(q.key, q.type === 'scale' ? v : String(v));
      scheduleAdvance(900);
      return;
    }
    if (q.type === 'choice') {
      const c = parseChoice(t, q.options);
      if (!c) { setHint(`Say ${q.options.join(', ')} - or tap one.`); return; }
      setParsed(c);
      commit(q.key, c);
      scheduleAdvance(900);
      return;
    }
    // text
    const existing = (form[q.key] || '').trim();
    const value = existing && !transcriptRef.current.startsWith(existing) ? `${existing} ${t}` : t;
    commit(q.key, value);
    setTranscript(value);
    scheduleAdvance(2500);
  }

  function scheduleAdvance(ms) {
    cancelTimers();
    setAutoAdvanceAt(Date.now() + ms);
    advanceTimer.current = setTimeout(() => { advanceTimer.current = null; setAutoAdvanceAt(null); next(); }, ms);
  }

  function next() {
    cancelTimers();
    stopMic();
    const cur = stepRef.current;
    if (cur + 1 >= script.length) {
      stopSpeaking();
      setPhase('review');
      if (voiceOnRef.current && voiceOutputSupported) speak('That is everything. Check it over and send it.');
      return;
    }
    stepRef.current = cur + 1;
    setStep(cur + 1);
    ask(cur + 1);
  }

  function back() {
    cancelTimers();
    stopMic();
    const cur = stepRef.current;
    if (cur === 0) return;
    stepRef.current = cur - 1;
    setStep(cur - 1);
    ask(cur - 1);
  }

  function start() {
    setPhase('asking');
    stepRef.current = 0;
    setStep(0);
    ask(0);
  }

  function jumpTo(i) {
    setPhase('asking');
    stepRef.current = i;
    setStep(i);
    ask(i);
  }

  function addMore() {
    cancelTimers();
    listen();
  }

  const progress = phase === 'review' ? 1 : (step + (parsed || (q?.type === 'text' && form[q.key]) ? 1 : 0)) / script.length;

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col text-white fade-in">
      <div className="h-1 bg-surface2">
        <div className="h-full bg-accent transition-all duration-500" style={{ width: `${Math.min(100, progress * 100)}%` }} />
      </div>
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-full bg-accent flex items-center justify-center font-bold ${speaking ? 'pulse-ring' : ''}`}>E</div>
          <div>
            <div className="font-semibold leading-tight">Ero</div>
            <div className="text-xs text-textmuted">{kind === 'daily' ? 'Daily check-in' : 'Weekly check-in'} · {phase === 'review' ? 'review' : phase === 'intro' ? 'ready' : `${step + 1} / ${script.length}`}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {voiceOutputSupported && (
            <button type="button" onClick={() => { setVoiceOn((v) => !v); stopSpeaking(); }} className="btn btn-secondary px-3" title={voiceOn ? 'Mute Ero' : 'Unmute Ero'}>
              {voiceOn ? <Volume2 size={16} /> : <VolumeX size={16} />}
            </button>
          )}
          <button type="button" onClick={() => { stopMic(); stopSpeaking(); onClose(); }} className="btn btn-secondary px-3 text-red-400" title="Hang up">
            <PhoneOff size={16} />
          </button>
        </div>
      </div>

      {phase === 'intro' && (
        <div className="flex-1 flex flex-col items-center justify-center px-6 text-center gap-6">
          <div className="w-24 h-24 rounded-full bg-accent flex items-center justify-center text-4xl font-bold pulse-ring">E</div>
          <div>
            <div className="text-2xl font-bold">{kind === 'daily' ? 'Daily check-in' : 'Weekly check-in'}</div>
            <div className="text-textmuted mt-2">{script.length} questions. Ero asks, you talk. {voiceInputSupported ? 'Mic opens after each question.' : 'Voice input is not available in this browser - you can type each answer.'}</div>
          </div>
          <button type="button" onClick={start} className="btn btn-primary px-8 py-3 text-base">Start</button>
        </div>
      )}

      {phase === 'asking' && q && (
        <div className="flex-1 flex flex-col px-5 pb-6 overflow-y-auto">
          <div className="flex-1 flex flex-col justify-center gap-6 py-6">
            <div className="text-2xl font-semibold leading-snug">{q.ask}</div>

            {q.type === 'photos' ? (
              <div className="grid grid-cols-3 gap-2">
                {['front', 'side', 'back'].map((t) => (
                  <PhotoUpload key={t} type={t} uploaded={photos[t]} uploading={uploadingType === t} onSelect={(file) => onUploadPhoto(t, file)} />
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {q.type === 'choice' && (
                  <div className="flex gap-2">
                    {q.options.map((o) => (
                      <button key={o} type="button" onClick={() => { cancelTimers(); stopMic(); setParsed(o); commit(q.key, o); scheduleAdvance(600); }}
                        className={`flex-1 px-3 py-3 rounded-xl text-sm font-medium border ${form[q.key] === o ? 'bg-accent border-accent' : 'bg-surface2 border-line text-textmuted'}`}>
                        {o}
                      </button>
                    ))}
                  </div>
                )}
                {q.type === 'scale' && (
                  <div className="grid grid-cols-10 gap-1">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                      <button key={n} type="button" onClick={() => { cancelTimers(); stopMic(); setParsed(String(n)); commit(q.key, n); scheduleAdvance(600); }}
                        className={`h-11 rounded-lg text-sm font-semibold border ${Number(form[q.key]) === n ? 'bg-accent border-accent' : 'bg-surface2 border-line text-textmuted'}`}>
                        {n}
                      </button>
                    ))}
                  </div>
                )}
                {(typing || !voiceInputSupported) ? (
                  q.type === 'text' ? (
                    <textarea autoFocus className="input min-h-[100px]" value={form[q.key] || ''} onChange={(e) => commit(q.key, e.target.value)} />
                  ) : (
                    <input autoFocus inputMode="decimal" className="input" value={form[q.key] ?? ''} onChange={(e) => {
                      if (q.type !== 'scale') return commit(q.key, e.target.value);
                      const n = parseInt(e.target.value, 10);
                      commit(q.key, Number.isFinite(n) ? Math.max(1, Math.min(10, n)) : '');
                    }} />
                  )
                ) : (
                  <div className={`min-h-[64px] rounded-2xl border px-4 py-3 text-lg ${listening ? 'border-accent bg-accent/5' : 'border-line bg-surface2'}`}>
                    {parsed ? (
                      <span className="text-accent font-semibold">{parsed}{q.unit ? ` ${q.unit}` : ''}</span>
                    ) : transcript ? transcript : form[q.key] && q.type === 'text' ? form[q.key] : (
                      <span className="text-textmuted">{listening ? 'Listening...' : speaking ? '' : 'Tap the mic to answer'}</span>
                    )}
                  </div>
                )}
                {hint && <div className="text-sm text-yellow-400">{hint}</div>}
                {autoAdvanceAt && (
                  <div className="flex items-center justify-between text-sm text-textmuted">
                    <span className="flex items-center gap-2"><Check size={14} className="text-accent" /> Got it - moving on</span>
                    {q.type === 'text' && <button type="button" onClick={addMore} className="text-accent">Add more</button>}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button type="button" onClick={back} disabled={step === 0} className="btn btn-secondary px-3 disabled:opacity-40" title="Back"><ArrowLeft size={16} /></button>
            {voiceInputSupported && q.type !== 'photos' && (
              <button type="button" onClick={() => (listening ? stopMic() : (stopSpeaking(), setSpeaking(false), setTyping(false), listen()))}
                className={`btn flex-1 py-3 ${listening ? 'bg-red-500 text-white pulse-ring' : 'btn-primary'}`}>
                <Mic size={16} /> {listening ? 'Stop' : 'Speak'}
              </button>
            )}
            {q.type !== 'photos' && voiceInputSupported && (
              <button type="button" onClick={() => { stopMic(); cancelTimers(); setTyping((v) => !v); }} className={`btn btn-secondary px-3 ${typing ? 'text-accent' : ''}`} title="Type instead"><Keyboard size={16} /></button>
            )}
            {q.optional || q.type === 'photos' ? (
              <button type="button" onClick={next} className="btn btn-secondary px-3" title={q.type === 'photos' ? 'Done' : 'Skip'}>{q.type === 'photos' ? <Check size={16} /> : <SkipForward size={16} />}</button>
            ) : (
              <button type="button" onClick={next} disabled={form[q.key] === '' || form[q.key] === undefined || form[q.key] === null || (q.type === 'scale' && (Number(form[q.key]) < 1 || Number(form[q.key]) > 10))} className="btn btn-secondary px-3 disabled:opacity-40" title="Next"><ArrowRight size={16} /></button>
            )}
          </div>
        </div>
      )}

      {phase === 'review' && (
        <div className="flex-1 flex flex-col px-5 pb-6 overflow-y-auto">
          <div className="text-xl font-semibold py-4">Check it over</div>
          <ul className="divide-y divide-line">
            {script.map((item, i) => (
              <li key={item.key}>
                <button type="button" onClick={() => jumpTo(i)} className="w-full text-left py-3 flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-xs text-textmuted">{item.ask}</div>
                    <div className="text-sm mt-0.5">
                      {item.type === 'photos'
                        ? `${['front', 'side', 'back'].filter((t) => photos[t]).length} / 3 photos`
                        : (form[item.key] === '' || form[item.key] === null || form[item.key] === undefined) ? <span className="text-textmuted italic">skipped</span> : `${form[item.key]}${item.unit && form[item.key] ? ' ' + item.unit : ''}`}
                    </div>
                  </div>
                  <span className="text-xs text-accent shrink-0 mt-1">edit</span>
                </button>
              </li>
            ))}
          </ul>
          <button type="button" onClick={onSubmit} disabled={busy} className="btn btn-primary w-full py-3 mt-4">
            {busy ? 'Sending...' : `Submit ${kind} check-in`}
          </button>
        </div>
      )}
    </div>
  );
}
