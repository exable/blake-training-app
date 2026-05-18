import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function ErrorBanner({ error, onDismiss }) {
  if (!error) return null;
  const msg = typeof error === 'string' ? error : error.message || 'Something went wrong';
  return (
    <div className="flex items-start gap-2 p-3 mb-4 rounded-xl bg-red-500/10 border border-red-500/30 text-sm text-red-200 fade-in">
      <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
      <div className="flex-1">{msg}</div>
      {onDismiss && (
        <button onClick={onDismiss} className="text-red-300 hover:text-white text-xs">
          ✕
        </button>
      )}
    </div>
  );
}
