// Browser-native voice in (SpeechRecognition) and voice out (SpeechSynthesis).

const SR = typeof window !== 'undefined'
  ? (window.SpeechRecognition || window.webkitSpeechRecognition)
  : null;

export const voiceInputSupported = !!SR;
export const voiceOutputSupported = typeof window !== 'undefined' && 'speechSynthesis' in window;

export function startListening({ onResult, onEnd, onError }) {
  if (!SR) {
    onError?.(new Error('Voice input not supported in this browser'));
    return null;
  }
  const rec = new SR();
  rec.lang = 'en-AU';
  rec.continuous = false;
  rec.interimResults = true;
  let finalText = '';
  rec.onresult = (e) => {
    let interim = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const r = e.results[i];
      if (r.isFinal) finalText += r[0].transcript;
      else interim += r[0].transcript;
    }
    onResult?.(finalText + interim, !!e.results[e.results.length - 1]?.isFinal);
  };
  rec.onerror = (e) => onError?.(e);
  rec.onend = () => onEnd?.(finalText);
  try {
    rec.start();
  } catch (e) {
    onError?.(e);
    return null;
  }
  return rec;
}

let _utterance = null;
export function speak(text) {
  if (!voiceOutputSupported || !text) return;
  try {
    window.speechSynthesis.cancel();
    _utterance = new SpeechSynthesisUtterance(text);
    _utterance.rate = 1.05;
    _utterance.pitch = 0.95;
    // Prefer a male English voice if available
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find((v) => /Daniel|Alex|Google UK English Male|Microsoft Mark/.test(v.name))
      || voices.find((v) => /en-GB|en-AU|en-US/.test(v.lang));
    if (preferred) _utterance.voice = preferred;
    window.speechSynthesis.speak(_utterance);
  } catch {}
}

export function stopSpeaking() {
  if (voiceOutputSupported) {
    try { window.speechSynthesis.cancel(); } catch {}
  }
}
