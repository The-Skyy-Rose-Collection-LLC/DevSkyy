/**
 * HuggingFace Spaces Embedding Page
 * ==================================
 * Embeds 5 production HuggingFace Spaces for DevSkyy tools:
 * - 3D Converter
 * - FLUX Upscaler
 * - LoRA Training Monitor
 * - Product Analyzer
 * - Product Photography
 */

'use client';

import { useState } from 'react';
import { ExternalLink, Loader2, Box, Image, Eye, Sparkles, Brain } from 'lucide-react';

interface HuggingFaceSpace {
  id: string;
  name: string;
  description: string;
  url: string;
  icon: React.ComponentType<{ className?: string }>;
  category: 'media' | 'ai' | 'analytics';
}

const HUGGINGFACE_SPACES: HuggingFaceSpace[] = [
  {
    id: '3d-converter',
    name: '3D Converter',
    description: 'Convert 3D models between formats (GLB, USDZ, OBJ, FBX)',
    url: 'https://huggingface.co/spaces/skyyrose/3d-converter',
    icon: Box,
    category: 'media',
  },
  {
    id: 'flux-upscaler',
    name: 'FLUX Upscaler',
    description: 'AI-powered image upscaling using FLUX model',
    url: 'https://huggingface.co/spaces/skyyrose/flux-upscaler',
    icon: Sparkles,
    category: 'ai',
  },
  {
    id: 'lora-training',
    name: 'LoRA Training Monitor',
    description: 'Monitor and manage LoRA model training runs',
    url: 'https://huggingface.co/spaces/skyyrose/lora-training',
    icon: Brain,
    category: 'ai',
  },
  {
    id: 'product-analyzer',
    name: 'Product Analyzer',
    description: 'Analyze product images and extract insights',
    url: 'https://huggingface.co/spaces/skyyrose/product-analyzer',
    icon: Eye,
    category: 'analytics',
  },
  {
    id: 'product-photography',
    name: 'Product Photography',
    description: 'AI-enhanced product photography and background removal',
    url: 'https://huggingface.co/spaces/skyyrose/product-photography',
    icon: Image,
    category: 'media',
  },
];

const CATEGORY_COLORS = {
  media: 'bg-blue-500',
  ai: 'bg-purple-500',
  analytics: 'bg-green-500',
};

export default function HuggingFaceSpacesPage() {
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>(
    HUGGINGFACE_SPACES.reduce((acc, space) => ({ ...acc, [space.id]: true }), {})
  );
  const [errorStates, setErrorStates] = useState<Record<string, boolean>>({});

  const handleIframeLoad = (spaceId: string) => {
    setLoadingStates((prev) => ({ ...prev, [spaceId]: false }));
  };

  const handleIframeError = (spaceId: string) => {
    setLoadingStates((prev) => ({ ...prev, [spaceId]: false }));
    setErrorStates((prev) => ({ ...prev, [spaceId]: true }));
  };

  const categories = Array.from(new Set(HUGGINGFACE_SPACES.map((s) => s.category)));

  return (
    <div className="space-y-8 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-orange-400 to-pink-500 flex items-center justify-center">
                <span className="text-white font-bold text-xl">🤗</span>
              </div>
              HuggingFace Spaces
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-2">
              Production AI tools and utilities hosted on HuggingFace
            </p>
          </div>
          <a
            href="https://huggingface.co/skyyrose"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-orange-400 to-pink-500 text-white font-medium hover:opacity-90 transition-opacity"
          >
            <ExternalLink className="h-4 w-4" />
            View Profile
          </a>
        </div>

        {/* Category Legend */}
        <div className="flex gap-3 items-center flex-wrap">
          <span className="text-sm text-gray-500 dark:text-gray-400">Categories:</span>
          {categories.map((category) => (
            <div key={category} className="flex items-center gap-2">
              <div className={`h-3 w-3 rounded-full ${CATEGORY_COLORS[category]}`} />
              <span className="text-sm font-medium capitalize">{category}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Spaces Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {HUGGINGFACE_SPACES.map((space) => {
          const Icon = space.icon;
          return (
            <div
              key={space.id}
              className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden hover:shadow-md transition-shadow"
            >
              {/* Space Header */}
              <div className="p-4 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div className={`h-10 w-10 rounded-lg ${CATEGORY_COLORS[space.category]} flex items-center justify-center flex-shrink-0`}>
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h2 className="text-lg font-bold text-gray-900 dark:text-gray-50 truncate">
                        {space.name}
                      </h2>
                      <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                        {space.description}
                      </p>
                    </div>
                  </div>
                  <a
                    href={space.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                    title="Open in new tab"
                  >
                    <ExternalLink className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                  </a>
                </div>
              </div>

              {/* iframe Container */}
              <div className="relative bg-white dark:bg-gray-950">
                {loadingStates[space.id] && !errorStates[space.id] && (
                  <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-900 z-10">
                    <div className="flex flex-col items-center gap-3">
                      <Loader2 className="h-8 w-8 animate-spin text-brand-primary" />
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Loading {space.name}...
                      </p>
                    </div>
                  </div>
                )}
                {errorStates[space.id] && (
                  <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-900 z-10">
                    <div className="flex flex-col items-center gap-3">
                      <div className="h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                        <span className="text-red-500 text-2xl">⚠️</span>
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400 text-center max-w-sm">
                        Unable to load {space.name}. Please visit directly:
                      </p>
                      <a
                        href={space.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-4 py-2 bg-brand-primary text-white rounded-lg hover:opacity-90 transition-opacity"
                      >
                        Open in New Tab
                      </a>
                    </div>
                  </div>
                )}
                <iframe
                  src={space.url}
                  title={space.name}
                  className="w-full h-[600px] border-0"
                  allow="accelerometer; ambient-light-sensor; autoplay; battery; camera; clipboard-read; clipboard-write; document-domain; encrypted-media; fullscreen; geolocation; gyroscope; layout-animations; legacy-image-formats; magnetometer; microphone; midi; oversized-images; payment; picture-in-picture; publickey-credentials-get; sync-xhr; usb; vr; wake-lock; xr-spatial-tracking"
                  sandbox="allow-forms allow-modals allow-popups allow-popups-to-escape-sandbox allow-same-origin allow-scripts allow-downloads"
                  loading="lazy"
                  onLoad={() => handleIframeLoad(space.id)}
                  onError={() => handleIframeError(space.id)}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="bg-gradient-to-r from-orange-50 to-pink-50 dark:from-orange-900/20 dark:to-pink-900/20 rounded-xl p-6 border border-orange-200 dark:border-orange-800">
        <div className="flex items-start gap-4">
          <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-orange-400 to-pink-500 flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-2xl">🚀</span>
          </div>
          <div>
            <h3 className="font-bold text-lg text-gray-900 dark:text-gray-50 mb-2">
              Production AI Tools
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
              All spaces are production-ready and actively maintained. They integrate with DevSkyy&apos;s
              SuperAgent platform for automated workflows. Visit our{' '}
              <a
                href="https://huggingface.co/skyyrose"
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-orange-600 dark:text-orange-400 hover:underline"
              >
                HuggingFace profile
              </a>
              {' '}for more tools and models.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
