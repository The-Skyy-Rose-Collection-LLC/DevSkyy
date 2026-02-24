'use client';

import { useRef } from 'react';

interface UploadZoneProps {
  collection: string;
  onUpload: (files: File[]) => Promise<void>;
}

export function UploadZone({ collection, onUpload }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      await onUpload(Array.from(files));
      if (inputRef.current) {
        inputRef.current.value = '';
      }
    }
  };

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept="image/*,.glb,.gltf,.obj,.fbx,.mp4,.webm"
        onChange={handleChange}
        className="hidden"
      />
      <button
        onClick={() => inputRef.current?.click()}
        className="px-4 py-2 text-sm bg-gradient-to-r from-rose-500 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity"
      >
        Upload to {collection.replace('_', ' ')}
      </button>
    </>
  );
}
