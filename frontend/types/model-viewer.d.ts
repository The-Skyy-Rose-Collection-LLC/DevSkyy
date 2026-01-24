// Type declarations for @google/model-viewer web component
import 'react';

declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      'model-viewer': React.DetailedHTMLProps<ModelViewerAttributes, HTMLElement>;
    }
  }
}

interface ModelViewerAttributes extends React.HTMLAttributes<HTMLElement> {
  src?: string;
  alt?: string;
  ar?: boolean;
  'ar-modes'?: string;
  'camera-controls'?: boolean;
  'auto-rotate'?: boolean;
  'rotation-per-second'?: string;
  'camera-orbit'?: string;
  'min-camera-orbit'?: string;
  'max-camera-orbit'?: string;
  'field-of-view'?: string;
  'shadow-intensity'?: string;
  'shadow-softness'?: string;
  'exposure'?: string;
  'environment-image'?: string;
  'ios-src'?: string;
  poster?: string;
  loading?: 'auto' | 'lazy' | 'eager';
  reveal?: 'auto' | 'manual' | 'interaction';
}

declare module '@google/model-viewer' {
  export default class ModelViewer extends HTMLElement {
    src: string;
    alt: string;
    ar: boolean;
    cameraControls: boolean;
    autoRotate: boolean;
    cameraOrbit: string;
  }
}
