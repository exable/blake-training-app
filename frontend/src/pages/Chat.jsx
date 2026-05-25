import React, { useEffect, useRef, useState } from 'react';
import { Send, Mic, MicOff, ImagePlus, X, Volume2, VolumeX } from 'lucide-react';
import { api } from '../lib/api.js';
import Spinner from '../components/Spinner.jsx';
import ErrorBanner from '../components/ErrorBanner.jsx';
import {
  voiceInputSupported, voiceOutputSupported,
  startListening, speak, stopSpeaking,
} from '../lib/voice.js';

const IMAGE_TAG_RE = /\[image\]\s+(\S+)/;

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const [pendingImage, setPendingImage] = useState(null); // { url, uploading }
  const [listening, setListening] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(() => localStorage.getItem('autoSpeak') === '1');
  const scrollRef = useRef(null);
  const recRef = useRef(null);
  const inputRef = useRef(null);

  // Detect coarse pointer (touch) devices once
  const isTouch = typeof window !== 'undefined'
    && window.matchMedia?.('(pointer: coarse)').matches;

  // Auto-grow the textarea up to a cap
  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  }, [text]);

  function onInputKeyDown(e) {
    // Desktop: Enter sends, Shift/Alt/Ctrl/Meta+Enter inserts newline.
    // Touch (mobile/tablet): Enter ALWAYS inserts a newline. Send button only.
    if (e.key !== 'Enter') return;
    if (isTouch) return; // let the default newline happen
    if (e.shiftKey || e.altKey || e.ctrlKey || e.metaKey) return;
    e.preventDefault();
    send();
  }

  async function load() {
    try {
      const rows = await api.get('/api/chat');
      setMessages(rows);
    } catch (e) { setError(e.message); }
    finally { setLoaded(true); }
  }

  // Initial load + one proactive check per app load
  useEffect(() => {
    (async () => {
      await load();
      try {
        const res = await api.post('/api/chat/proactive-check');
        if (res.delivered) await load();
      } catch {}
    })();
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, sending]);

  useEffect(() => {
    localStorage.setItem('autoSpeak', autoSpeak ? '1' : '0');
    if (!autoSpeak) stopSpeaking();
  }, [autoSpeak]);

  async function send(e) {
    e?.preventDefault();
    const content = text.trim();
    if (!content && !pendingImage?.url) return;
    setSending(true);
    setError(null);
    const imageUrl = pendingImage?.url || null;
    setText('');
    setPendingImage(null);

    const optimisticUser = {
      id: `tmp-${Date.now()}`,
      role: 'user',
      content: (content || '') + (imageUrl ? `\n[image] ${imageUrl}` : ''),
      created_at: new Date().toISOString(),
    };
    setMessages((m) => [...m, optimisticUser]);

    try {
      const res = await api.post('/api/chat', { content, image_url: imageUrl });
      setMessages((m) => {
        const without = m.filter((x) => x.id !== optimisticUser.id);
        return [...without, res.user_message, res.assistant_message];
      });
      if (autoSpeak) speak(res.assistant_message.content);
    } catch (e) {
      setError(e.message);
      setMessages((m) => m.filter((x) => x.id !== optimisticUser.id));
      setText(content);
    } finally {
      setSending(false);
    }
  }

  async function pickImage(file) {
    if (!file) return;
    setPendingImage({ url: null, uploading: true });
    try {
      const fd = new FormData();
      fd.append('file', file);
      const r = await api.upload('/api/chat/image-upload', fd);
      setPendingImage({ url: r.url, uploading: false });
    } catch (e) {
      setError(e.message);
      setPendingImage(null);
    }
  }

  function toggleMic() {
    if (listening) {
      recRef.current?.stop?.();
      return;
    }
    setListening(true);
    recRef.current = startListening({
      onResult: (transcript) => setText(transcript),
      onEnd: () => { setListening(false); recRef.current = null; },
      onError: (e) => { setError(e?.message || 'Voice input failed'); setListening(false); },
    });
  }

  return (
    <div className="flex flex-col h-[calc(100vh-9rem)] md:h-[calc(100vh-4rem)] fade-in">
      <div className="flex items-center gap-3 pb-4 border-b border-line">
        <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center text-white font-bold">E</div>
        <div className="flex-1">
          <div className="font-semibold">Ero</div>
          <div className="text-xs text-textmuted">Your coach</div>
        </div>
        {voiceOutputSupported && (
          <button
            onClick={() => setAutoSpeak((v) => !v)}
            className={`p-2 rounded-lg transition-colors ${autoSpeak ? 'text-accent bg-accent/10' : 'text-textmuted hover:text-white'}`}
            title={autoSpeak ? 'Voice replies on' : 'Voice replies off'}
          >
            {autoSpeak ? <Volume2 size={18} /> : <VolumeX size={18} />}
          </button>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto py-4 space-y-3">
        <ErrorBanner error={error} onDismiss={() => setError(null)} />
        {!loaded && <Spinner />}
        {loaded && messages.length === 0 && (
          <div className="text-center text-textmuted py-12 text-sm">
            Drop Ero a message to get started.
          </div>
        )}
        {messages.map((m) => <Bubble key={m.id} m={m} onSpeak={() => speak(m.content)} />)}
        {sending && (
          <div className="flex items-start gap-2">
            <Avatar />
            <div className="bg-surface2 border border-line rounded-2xl px-4 py-3 flex gap-1">
              <Dot delay="0s" /><Dot delay="0.15s" /><Dot delay="0.3s" />
            </div>
          </div>
        )}
      </div>

      {pendingImage && (
        <div className="mb-2 px-2">
          <div className="inline-flex items-center gap-2 bg-surface2 border border-line rounded-xl p-2">
            {pendingImage.uploading ? <Spinner /> : <img src={pendingImage.url} alt="" className="w-12 h-12 rounded-md object-cover" />}
            <button onClick={() => setPendingImage(null)} className="text-textmuted hover:text-white p-1">
              <X size={14} />
            </button>
          </div>
        </div>
      )}

      <form onSubmit={send} className="pt-3 border-t border-line flex gap-2 pb-2 items-end">
        <label className="btn btn-secondary px-3 cursor-pointer" title="Send a photo">
          <ImagePlus size={16} />
          <input type="file" accept="image/*" className="hidden"
            onChange={(e) => pickImage(e.target.files?.[0])} />
        </label>
        {voiceInputSupported && (
          <button
            type="button"
            onClick={toggleMic}
            className={`btn ${listening ? 'btn-primary pulse-ring' : 'btn-secondary'} px-3`}
            title="Voice input"
          >
            {listening ? <MicOff size={16} /> : <Mic size={16} />}
          </button>
        )}
        <textarea
          ref={inputRef}
          rows={1}
          className="input flex-1 resize-none leading-snug py-2"
          placeholder={pendingImage ? "Add a question about the image..." : "Message Ero..."}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onInputKeyDown}
          disabled={sending}
        />
        <button type="submit" disabled={sending || (!text.trim() && !pendingImage?.url)} className="btn btn-primary px-4">
          {sending ? <Spinner /> : <Send size={16} />}
        </button>
      </form>
    </div>
  );
}

function Avatar() {
  return <div className="w-8 h-8 flex-shrink-0 rounded-full bg-accent flex items-center justify-center text-white text-sm font-bold">E</div>;
}

function parseContent(raw) {
  const m = raw.match(IMAGE_TAG_RE);
  if (!m) return { text: raw, image: null };
  return {
    text: raw.replace(IMAGE_TAG_RE, '').trim(),
    image: m[1],
  };
}

function Bubble({ m, onSpeak }) {
  const mine = m.role === 'user';
  const ts = new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const { text, image } = parseContent(m.content);

  if (mine) {
    return (
      <div className="flex justify-end fade-in">
        <div className="max-w-[80%]">
          {image && <img src={image} alt="" className="rounded-xl mb-1 ml-auto max-h-64 border border-line" />}
          {text && <div className="bg-accent text-white rounded-2xl rounded-br-md px-4 py-2.5 text-sm whitespace-pre-wrap">{text}</div>}
          <div className="text-[10px] text-textmuted text-right mt-1">{ts}</div>
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-start gap-2 fade-in group">
      <Avatar />
      <div className="max-w-[80%]">
        <div className="bg-surface2 border border-line rounded-2xl rounded-bl-md px-4 py-2.5 text-sm whitespace-pre-wrap">{text}</div>
        <div className="text-[10px] text-textmuted mt-1 flex items-center gap-2">
          <span>{ts}</span>
          {voiceOutputSupported && (
            <button onClick={onSpeak} className="opacity-0 group-hover:opacity-100 transition-opacity hover:text-white">
              <Volume2 size={11} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function Dot({ delay }) {
  return (
    <span
      className="w-1.5 h-1.5 rounded-full bg-textmuted animate-bounce"
      style={{ animationDelay: delay }}
    />
  );
}
