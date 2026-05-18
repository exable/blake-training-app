import React, { useEffect, useRef, useState } from 'react';
import { Send } from 'lucide-react';
import { api } from '../lib/api.js';
import Spinner from '../components/Spinner.jsx';
import ErrorBanner from '../components/ErrorBanner.jsx';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const scrollRef = useRef(null);

  async function load() {
    try {
      const rows = await api.get('/api/chat');
      setMessages(rows);
    } catch (e) { setError(e.message); }
    finally { setLoaded(true); }
  }

  useEffect(() => { load(); }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, sending]);

  async function send(e) {
    e?.preventDefault();
    const content = text.trim();
    if (!content) return;
    setSending(true);
    setError(null);
    setText('');
    const optimisticUser = {
      id: `tmp-${Date.now()}`, role: 'user', content,
      created_at: new Date().toISOString(),
    };
    setMessages((m) => [...m, optimisticUser]);
    try {
      const res = await api.post('/api/chat', { content });
      setMessages((m) => {
        const without = m.filter((x) => x.id !== optimisticUser.id);
        return [...without, res.user_message, res.assistant_message];
      });
    } catch (e) {
      setError(e.message);
      setMessages((m) => m.filter((x) => x.id !== optimisticUser.id));
      setText(content);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-9rem)] md:h-[calc(100vh-4rem)] fade-in">
      <div className="flex items-center gap-3 pb-4 border-b border-line">
        <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center text-white font-bold">E</div>
        <div>
          <div className="font-semibold">Ero</div>
          <div className="text-xs text-textmuted">Your coach</div>
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto py-4 space-y-3">
        <ErrorBanner error={error} onDismiss={() => setError(null)} />
        {!loaded && <Spinner />}
        {loaded && messages.length === 0 && (
          <div className="text-center text-textmuted py-12 text-sm">
            Drop Ero a message to get started.
          </div>
        )}
        {messages.map((m) => <Bubble key={m.id} m={m} />)}
        {sending && (
          <div className="flex items-start gap-2">
            <Avatar />
            <div className="bg-surface2 border border-line rounded-2xl px-4 py-3 flex gap-1">
              <Dot delay="0s" /><Dot delay="0.15s" /><Dot delay="0.3s" />
            </div>
          </div>
        )}
      </div>

      <form onSubmit={send} className="pt-3 border-t border-line flex gap-2 pb-2">
        <input
          className="input flex-1"
          placeholder="Message Ero..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={sending}
        />
        <button type="submit" disabled={sending || !text.trim()} className="btn btn-primary px-4">
          {sending ? <Spinner /> : <Send size={16} />}
        </button>
      </form>
    </div>
  );
}

function Avatar() {
  return <div className="w-8 h-8 flex-shrink-0 rounded-full bg-accent flex items-center justify-center text-white text-sm font-bold">E</div>;
}

function Bubble({ m }) {
  const mine = m.role === 'user';
  const ts = new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  if (mine) {
    return (
      <div className="flex justify-end fade-in">
        <div className="max-w-[80%]">
          <div className="bg-accent text-white rounded-2xl rounded-br-md px-4 py-2.5 text-sm whitespace-pre-wrap">{m.content}</div>
          <div className="text-[10px] text-textmuted text-right mt-1">{ts}</div>
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-start gap-2 fade-in">
      <Avatar />
      <div className="max-w-[80%]">
        <div className="bg-surface2 border border-line rounded-2xl rounded-bl-md px-4 py-2.5 text-sm whitespace-pre-wrap">{m.content}</div>
        <div className="text-[10px] text-textmuted mt-1">{ts}</div>
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
