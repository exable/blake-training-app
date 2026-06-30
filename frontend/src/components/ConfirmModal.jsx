import React from 'react';
import { X } from 'lucide-react';

/**
 * Reusable confirmation modal. Used in place of window.confirm() because
 * native confirm() is silently blocked / returns false in iOS standalone PWAs.
 */
export default function ConfirmModal({
  open,
  title = 'Are you sure?',
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  destructive = false,
  onConfirm,
  onCancel,
}) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[60] flex items-end md:items-center justify-center p-4 fade-in"
      onClick={onCancel}
    >
      <div
        className="bg-surface border border-line rounded-2xl w-full max-w-sm p-5 slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="font-semibold">{title}</div>
          <button onClick={onCancel} className="text-textmuted hover:text-white">
            <X size={18} />
          </button>
        </div>
        {message && (
          <div className="text-sm text-textmuted whitespace-pre-wrap mb-5">{message}</div>
        )}
        <div className="flex gap-2">
          <button onClick={onCancel} className="btn btn-secondary flex-1">
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`btn flex-1 ${destructive ? 'btn-secondary text-red-300' : 'btn-primary'}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
