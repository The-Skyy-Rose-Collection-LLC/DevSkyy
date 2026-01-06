/**
 * HuggingFace Space Card Component
 * =================================
 * Embeds a HuggingFace Space in an iframe with fullscreen and external link controls.
 */

'use client';

import { useState } from 'react';
import { Maximize2, Minimize2, ExternalLink, RefreshCw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui';
import type { HFSpace } from '@/lib/hf-spaces';

interface HFSpaceCardProps {
  space: HFSpace;
  fullscreen?: boolean;
  onToggleFullscreen?: () => void;
  className?: string;
}

export function HFSpaceCard({
  space,
  fullscreen = false,
  onToggleFullscreen,
  className = '',
}: HFSpaceCardProps) {
  const [iframeKey, setIframeKey] = useState(0);

  const handleRefresh = () => {
    setIframeKey((prev) => prev + 1);
  };

  return (
    <Card
      className={`overflow-hidden transition-all ${
        fullscreen ? 'fixed inset-4 z-50 shadow-2xl' : ''
      } ${className}`}
    >
      <CardHeader className="bg-gray-50 dark:bg-gray-900 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <span className="text-3xl" aria-label={space.name}>
              {space.icon}
            </span>
            <div className="flex-1 min-w-0">
              <CardTitle className="text-xl font-bold truncate">
                {space.name}
              </CardTitle>
              <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                {space.description}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={handleRefresh}
              className="px-3 py-2 rounded-md bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 transition-colors"
              title="Refresh iframe"
              aria-label="Refresh iframe"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
            {onToggleFullscreen && (
              <button
                onClick={onToggleFullscreen}
                className="px-3 py-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white transition-colors"
                title={fullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
                aria-label={fullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
              >
                {fullscreen ? (
                  <Minimize2 className="h-4 w-4" />
                ) : (
                  <Maximize2 className="h-4 w-4" />
                )}
              </button>
            )}
            <a
              href={space.url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-2 rounded-md bg-gray-600 hover:bg-gray-700 text-white transition-colors"
              title="Open in new tab"
              aria-label="Open in new tab"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div
          className={
            fullscreen
              ? 'h-[calc(100vh-10rem)]'
              : 'h-[600px] lg:h-[700px]'
          }
        >
          <iframe
            key={iframeKey}
            src={space.url}
            className="w-full h-full border-0"
            allow="accelerometer; camera; microphone; clipboard-write"
            sandbox="allow-scripts allow-same-origin allow-forms allow-downloads allow-popups allow-modals"
            title={space.name}
            loading="lazy"
          />
        </div>
      </CardContent>
    </Card>
  );
}
