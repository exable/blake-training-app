import React from 'react';
import { Upload } from 'lucide-react';
import Spinner from './Spinner.jsx';

export default function PhotoUpload({ type, uploaded, uploading, onSelect }) {
  const id = `photo-${type}`;
  return (
    <label
      htmlFor={id}
      className={`aspect-square rounded-xl border-2 border-dashed flex items-center justify-center cursor-pointer transition-all overflow-hidden relative ${
        uploaded ? 'border-accent' : 'border-line hover:border-accent/50'
      }`}
    >
      {uploaded?.url ? (
        <img src={uploaded.url} alt={type} className="w-full h-full object-cover" />
      ) : uploading ? (
        <Spinner />
      ) : (
        <div className="text-center">
          <Upload size={18} className="mx-auto text-textmuted mb-1" />
          <div className="text-xs capitalize text-textmuted">{type}</div>
        </div>
      )}
      <input
        id={id}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && onSelect(e.target.files[0])}
      />
    </label>
  );
}
