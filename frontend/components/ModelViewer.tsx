/**
 * ModelViewer Component
 * =====================
 * 3D model viewer using Google's model-viewer library.
 * Supports GLB/GLTF files with AR, auto-rotate, and camera controls.
 */

'use client';

import React from 'react';

// Extend JSX to include model-viewer custom element (React 19 compatible)
declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      'model-viewer': React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement> & {
          src?: string;
          alt?: string;
          poster?: string;
          loading?: 'auto' | 'lazy' | 'eager';
          reveal?: 'auto' | 'manual';
          ar?: boolean;
          'ar-modes'?: string;
          'camera-controls'?: boolean;
          'auto-rotate'?: boolean;
          'rotation-per-second'?: string;
          'shadow-intensity'?: string;
          'shadow-softness'?: string;
          exposure?: string;
          'environment-image'?: string;
          'skybox-image'?: string;
          'camera-orbit'?: string;
          'min-camera-orbit'?: string;
          'max-camera-orbit'?: string;
          'field-of-view'?: string;
          'interaction-prompt'?: 'auto' | 'none';
          'touch-action'?: string;
        },
        HTMLElement
      >;
    }
  }
}

interface ModelViewerProps {
  src: string;
  alt?: string;
  poster?: string;
  className?: string;
  autoRotate?: boolean;
  cameraControls?: boolean;
  ar?: boolean;
  shadowIntensity?: number;
  exposure?: number;
  environmentImage?: string;
  onLoad?: () => void;
  onError?: (error: Error) => void;
}

export const ModelViewer: React.FC<ModelViewerProps> = ({
  src,
  alt = '3D Model',
  poster,
  className = '',
  autoRotate = true,
  cameraControls = true,
  ar = true,
  shadowIntensity = 1,
  exposure = 1,
  environmentImage = 'neutral',
  onLoad,
  onError,
}) => {
  const handleLoad = () => {
    onLoad?.();
  };

  const handleError = (e: React.SyntheticEvent) => {
    onError?.(new Error('Failed to load 3D model'));
    console.error('Model viewer error:', e);
  };

  return (
    <model-viewer
      src={src}
      alt={alt}
      poster={poster}
      loading="eager"
      camera-controls={cameraControls}
      auto-rotate={autoRotate}
      rotation-per-second="30deg"
      ar={ar}
      ar-modes="webxr scene-viewer quick-look"
      shadow-intensity={shadowIntensity.toString()}
      shadow-softness="1"
      exposure={exposure.toString()}
      environment-image={environmentImage}
      interaction-prompt="auto"
      touch-action="pan-y"
      className={`w-full h-full ${className}`}
      style={{
        minHeight: '300px',
        backgroundColor: 'transparent',
        '--poster-color': 'transparent',
      } as React.CSSProperties}
      onLoad={handleLoad}
      onError={handleError}
    >
      {/* Loading indicator slot */}
      <div
        className="absolute inset-0 flex items-center justify-center bg-black/50"
        slot="poster"
      >
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-rose-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <div className="text-sm text-white">Loading 3D Model...</div>
        </div>
      </div>

      {/* AR button slot */}
      <button
        slot="ar-button"
        className="absolute bottom-4 right-4 px-4 py-2 rounded-lg bg-rose-500/90 text-white text-sm font-medium hover:bg-rose-600 transition-colors"
      >
        View in AR
      </button>
    </model-viewer>
  );
};

export default ModelViewer;
