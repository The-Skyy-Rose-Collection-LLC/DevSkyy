'use client';

import { type Asset } from '@/lib/api';

interface AssetRowProps {
  asset: Asset;
  isSelected: boolean;
  onToggle: () => void;
  onPreview: () => void;
  onEdit: () => void;
}

export function AssetRow({ asset, isSelected, onToggle, onPreview, onEdit }: AssetRowProps) {
  return (
    <tr className="hover:bg-gray-800/50 transition-colors">
      <td className="px-4 py-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggle}
          className="rounded"
        />
      </td>
      <td className="px-4 py-3">
        <button onClick={onPreview} className="flex items-center gap-3 text-left">
          <div className="h-10 w-10 rounded bg-gray-700 flex items-center justify-center overflow-hidden flex-shrink-0">
            {asset.thumbnail_url ? (
              <img src={asset.thumbnail_url} alt={asset.filename} className="w-full h-full object-cover" />
            ) : (
              <span className="text-gray-500 text-xs">{asset.type}</span>
            )}
          </div>
          <span className="text-white text-sm truncate">{asset.filename}</span>
        </button>
      </td>
      <td className="px-4 py-3 text-gray-400 text-sm">{asset.collection}</td>
      <td className="px-4 py-3 text-gray-400 text-sm">{asset.type}</td>
      <td className="px-4 py-3 text-gray-400 text-sm">{asset.metadata?.sku || '-'}</td>
      <td className="px-4 py-3 text-gray-400 text-sm">
        {new Date(asset.created_at).toLocaleDateString()}
      </td>
      <td className="px-4 py-3">
        <button
          onClick={onEdit}
          className="text-xs text-gray-400 hover:text-white"
        >
          Edit
        </button>
      </td>
    </tr>
  );
}
