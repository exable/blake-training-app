import React, { useEffect, useRef, useState } from 'react';
import { Mic, Square } from 'lucide-react';
import { startListening, voiceInputSupported } from '../lib/voice.js';

/**
 * Textarea/input with a mic button. Tap to start, tap to stop; the transcript is
 * appended to whatever is already typed, and the field stays editable.
 * Renders a plain field (no mic) when the browser has no SpeechRecognition.
 */
export default function VoiceInput({
  value,
  onChange,
  multiline = true,
  placeholder,
  className = '',
  minHeight = 60,
  id,
}) {
  const [listening, setListening] = useState(false);
  const [error, setError] = useState(null);
  const recRef = useRef(null);
  const baseRef = useRef('');

  useEffect(() => () => recRef.current?.stop?.(), []);

  function toggle() {
    if (listening) {
      recRef.current?.stop?.();
      return;
    }
    setError(null);
    baseRef.current = value ? value.replace(/\s+$/, '') + ' ' : '';
    setListening(true);
    recRef.current = startListening({
      onResult: (transcript) => onChange(baseRef.current + transcript),
      onEnd: (finalText) => {
        setListening(false);
        recRef.current = null;
        if (finalText) onChange((baseRef.current + finalText).trim());
      },
      onError: (e) => {
        const code = e?.error || e?.message || '';
        setError(code === 'not-allowed' ? 'Mic blocked - allow microphone access in browser settings.' : code === 'no-speech' ? null : 'Voice input failed');
        setListening(false);
        recRef.current = null;
      },
    });
    if (!recRef.current) setListening(false);
  }

  const field = multiline ? (
    <textarea
      id={id}
      className={`input ${listening ? 'border-accent ring-2 ring-accent/20' : ''} ${className}`}
      style={{ minHeight, paddingRight: voiceInputSupported ? 52 : undefined }}
      value={value}
      placeholder={listening ? 'Listening...' : placeholder}
      onChange={(e) => onChange(e.target.value)}
    />
  ) : (
    <input
      id={id}
      className={`input ${listening ? 'border-accent ring-2 ring-accent/20' : ''} ${className}`}
      style={{ paddingRight: voiceInputSupported ? 52 : undefined }}
      value={value}
      placeholder={listening ? 'Listening...' : placeholder}
      onChange={(e) => onChange(e.target.value)}
    />
  );

  if (!voiceInputSupported) return field;

  return (
    <div>
      <div className="relative">
        {field}
        <button
          type="button"
          onClick={toggle}
          aria-label={listening ? 'Stop recording' : 'Speak'}
          aria-pressed={listening}
          className={`absolute right-2 ${multiline ? 'top-2' : 'top-1/2 -translate-y-1/2'} w-9 h-9 rounded-full flex items-center justify-center transition-all ${
            listening ? 'bg-red-500 text-white pulse-ring' : 'bg-surface border border-line text-textmuted hover:text-white hover:border-accent/50'
          }`}
        >
          {listening ? <Square size={14} fill="currentColor" /> : <Mic size={16} />}
        </button>
      </div>
      {listening && (
        <div className="flex items-center gap-2 mt-1.5 text-xs text-red-400">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          Recording - tap the square to stop
        </div>
      )}
      {error && <div className="mt-1.5 text-xs text-red-400">{error}</div>}
    </div>
  );
}
