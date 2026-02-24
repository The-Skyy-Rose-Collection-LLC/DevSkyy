'use client';

import { useState } from 'react';

interface BatchGenerationModalProps {
  selectedCount: number;
  onClose: () => void;
  onStart: (quality: 'draft' | 'standard' | 'high') => Promise<void>;
}

const QUALITY_OPTIONS: { id: 'draft' | 'standard' | 'high'; label: string; description: string }[] = [
  { id: 'draft', label: 'Draft', description: 'Fast preview quality' },
  { id: 'standard', label: 'Standard', description: 'Balanced quality and speed' },
  { id: 'high', label: 'High', description: 'Maximum fidelity' },
];

export function BatchGenerationModal({ selectedCount, onClose, onStart }: BatchGenerationModalProps) {
  const [quality, setQuality] = useState<'draft' | 'standard' | 'high'>('standard');
  const [starting, setStarting] = useState(false);

  const handleStart = async () => {
    setStarting(true);
    try {
      await onStart(quality);
    } finally {
      setStarting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80" onClick={onClose}>
      <div
        className="relative bg-gray-900 border border-gray-700 rounded-xl max-w-md w-full mx-4 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-white text-lg font-medium mb-2">Batch 3D Generation</h2>
        <p className="text-gray-400 text-sm mb-4">
          Generate 3D models for {selectedCount} selected asset{selectedCount !== 1 ? 's' : ''}.
        </p>
        <div className="space-y-2">
          {QUALITY_OPTIONS.map((opt) => (
            <label
              key={opt.id}
              className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                quality === opt.id
                  ? 'border-rose-500 bg-rose-500/10'
                  : 'border-gray-700 hover:border-gray-600'
              }`}
            >
              <input
                type="radio"
                name="quality"
                value={opt.id}
                checked={quality === opt.id}
                onChange={() => setQuality(opt.id)}
                className="accent-rose-500"
              />
              <div>
                <p className="text-white text-sm font-medium">{opt.label}</p>
                <p className="text-gray-400 text-xs">{opt.description}</p>
              </div>
            </label>
          ))}
        </div>
        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-400 hover:text-white"
          >
            Cancel
          </button>
          <button
            onClick={handleStart}
            disabled={starting}
            className="px-4 py-2 text-sm bg-gradient-to-r from-rose-500 to-purple-600 text-white rounded disabled:opacity-50"
          >
            {starting ? 'Starting...' : 'Start Generation'}
          </button>
        </div>
      </div>
    </div>
  );
}
