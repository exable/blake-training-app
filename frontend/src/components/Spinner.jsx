import React from 'react';

export default function Spinner({ size = 18 }) {
  return (
    <span
      className="inline-block animate-spin rounded-full border-2 border-textmuted/30 border-t-accent"
      style={{ width: size, height: size }}
      aria-label="Loading"
    />
  );
}

export function FullSpinner() {
  return (
    <div className="flex items-center justify-center py-16">
      <Spinner size={28} />
    </div>
  );
}
