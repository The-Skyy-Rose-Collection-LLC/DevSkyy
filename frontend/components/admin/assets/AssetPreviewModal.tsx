'use client';

import { type Asset } from '@/lib/api';

interface AssetPreviewModalProps {
  asset: Asset;
  onClose: () => void;
}

export function AssetPreviewModal({ asset, onClose }: AssetPreviewModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80" onClick={onClose}>
      <div
        className="relative bg-gray-900 border border-gray-700 rounded-xl max-w-3xl w-full mx-4 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          Close
        </button>
        <h2 className="text-white text-lg font-medium mb-4">{asset.filename}</h2>
        <div className="aspect-video bg-gray-800 rounded-lg flex items-center justify-center overflow-hidden">
          {asset.thumbnail_url ? (
            <img src={asset.thumbnail_url} alt={asset.filename} className="max-w-full max-h-full object-contain" />
          ) : (
            <span className="text-gray-500">No preview available</span>
          )}
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
          <div className="text-gray-400">Collection: <span className="text-white">{asset.collection}</span></div>
          <div className="text-gray-400">Type: <span className="text-white">{asset.type}</span></div>
          {asset.metadata?.sku && (
            <div className="text-gray-400">SKU: <span className="text-white">{asset.metadata.sku}</span></div>
          )}
          <div className="text-gray-400">Created: <span className="text-white">{new Date(asset.created_at).toLocaleDateString()}</span></div>
        </div>
      </div>
    </div>
  );
}
