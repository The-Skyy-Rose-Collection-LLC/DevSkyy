'use client';

import { type Asset } from '@/lib/api';

interface AssetCardProps {
  asset: Asset;
  isSelected: boolean;
  onToggle: () => void;
  onPreview: () => void;
  onEdit: () => void;
}

export function AssetCard({ asset, isSelected, onToggle, onPreview, onEdit }: AssetCardProps) {
  return (
    <div
      className={`relative group rounded-lg border overflow-hidden cursor-pointer transition-all ${
        isSelected
          ? 'border-rose-500 ring-1 ring-rose-500'
          : 'border-gray-700 hover:border-gray-600'
      } bg-gray-900/80`}
    >
      <div className="absolute top-2 left-2 z-10">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggle}
          className="rounded"
        />
      </div>
      <div
        className="aspect-square bg-gray-800 flex items-center justify-center"
        onClick={onPreview}
      >
        {asset.thumbnail_url ? (
          <img
            src={asset.thumbnail_url}
            alt={asset.filename}
            className="w-full h-full object-cover"
          />
        ) : (
          <span className="text-gray-500 text-xs">{asset.type}</span>
        )}
      </div>
      <div className="p-2">
        <p className="text-white text-xs truncate">{asset.filename}</p>
        <p className="text-gray-400 text-xs">{asset.collection}</p>
      </div>
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={onEdit}
          className="text-xs text-gray-400 hover:text-white bg-gray-800 rounded px-2 py-1"
        >
          Edit
        </button>
      </div>
    </div>
  );
}
