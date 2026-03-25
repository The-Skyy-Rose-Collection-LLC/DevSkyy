'use client';

import { useState } from 'react';
import { type Asset } from '@/lib/api';

interface AssetEditModalProps {
  asset: Asset;
  onClose: () => void;
  onSave: (data: Record<string, unknown>) => Promise<void>;
}

export function AssetEditModal({ asset, onClose, onSave }: AssetEditModalProps) {
  const [sku, setSku] = useState(asset.metadata?.sku || '');
  const [productName, setProductName] = useState(asset.metadata?.product_name || '');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave({ sku, product_name: productName });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80" onClick={onClose}>
      <div
        className="relative bg-gray-900 border border-gray-700 rounded-xl max-w-md w-full mx-4 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-white text-lg font-medium mb-4">Edit Asset</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">SKU</label>
            <input
              type="text"
              value={sku}
              onChange={(e) => setSku(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Product Name</label>
            <input
              type="text"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
            />
          </div>
        </div>
        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-400 hover:text-white"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm bg-rose-500 hover:bg-rose-600 text-white rounded disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
