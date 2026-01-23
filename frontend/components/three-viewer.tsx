'use client';

import { Suspense, useRef, useState, useCallback, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import {
  OrbitControls,
  Environment,
  useGLTF,
  Center,
  ContactShadows,
  Html,
  useProgress,
} from '@react-three/drei';
import * as THREE from 'three';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Maximize2,
  Minimize2,
  Camera,
  RotateCcw,
  Sun,
  Moon,
  Download,
  ZoomIn,
  ZoomOut,
  Loader2,
} from 'lucide-react';

// Collection-specific lighting configurations
const COLLECTION_LIGHTING = {
  black_rose: {
    environment: 'night',
    ambientIntensity: 0.3,
    spotlightColor: '#C0C0C0', // Moonlight silver
    spotlightIntensity: 1.2,
    bgColor: '#0D0D0D',
  },
  love_hurts: {
    environment: 'apartment',
    ambientIntensity: 0.4,
    spotlightColor: '#FFD700', // Candlelight gold
    spotlightIntensity: 0.9,
    bgColor: '#1A0A0F',
  },
  signature: {
    environment: 'studio',
    ambientIntensity: 0.5,
    spotlightColor: '#FFFFFF', // Clean white
    spotlightIntensity: 1.0,
    bgColor: '#0A0A0A',
  },
  showroom: {
    environment: 'warehouse',
    ambientIntensity: 0.6,
    spotlightColor: '#F5F5DC', // Beige
    spotlightIntensity: 0.8,
    bgColor: '#141414',
  },
  runway: {
    environment: 'studio',
    ambientIntensity: 0.4,
    spotlightColor: '#FFD700', // Gold runway lights
    spotlightIntensity: 1.0,
    bgColor: '#0A0A0A',
  },
} as const;

type Collection = keyof typeof COLLECTION_LIGHTING;

interface ThreeViewerProps {
  modelUrl: string;
  collection?: Collection;
  className?: string;
  onScreenshot?: (dataUrl: string) => void;
  onLoad?: () => void;
  onError?: (error: Error) => void;
  showControls?: boolean;
  autoRotate?: boolean;
  height?: string | number;
}

// Loading progress component
function Loader() {
  const { progress, active } = useProgress();

  if (!active) return null;

  return (
    <Html center>
      <div className="flex flex-col items-center gap-3 bg-gray-900/90 rounded-lg p-6 backdrop-blur-sm border border-gray-700">
        <Loader2 className="h-8 w-8 animate-spin text-rose-500" />
        <div className="text-white text-sm font-medium">
          Loading Model...
        </div>
        <div className="w-40 h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-rose-500 to-purple-600 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="text-gray-400 text-xs">{progress.toFixed(0)}%</div>
      </div>
    </Html>
  );
}

// Model component with GLTF loading
function Model({
  url,
  onLoad,
  onError,
}: {
  url: string;
  onLoad?: () => void;
  onError?: (error: Error) => void;
}) {
  const { scene } = useGLTF(url, true, true, (loader) => {
    loader.manager.onError = (errorUrl) => {
      onError?.(new Error(`Failed to load: ${errorUrl}`));
    };
  });

  useEffect(() => {
    if (scene) {
      onLoad?.();
    }
  }, [scene, onLoad]);

  // Auto-scale model to fit viewport
  useEffect(() => {
    const box = new THREE.Box3().setFromObject(scene);
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    const scale = 2 / maxDim;
    scene.scale.setScalar(scale);

    // Center the model
    const center = box.getCenter(new THREE.Vector3());
    scene.position.sub(center.multiplyScalar(scale));
  }, [scene]);

  return <primitive object={scene} />;
}

// Scene lighting based on collection
function CollectionLighting({ collection }: { collection: Collection }) {
  const config = COLLECTION_LIGHTING[collection];
  const spotRef = useRef<THREE.SpotLight>(null);

  useFrame(({ clock }) => {
    if (spotRef.current) {
      // Subtle light animation
      spotRef.current.intensity =
        config.spotlightIntensity + Math.sin(clock.getElapsedTime() * 0.5) * 0.1;
    }
  });

  return (
    <>
      <ambientLight intensity={config.ambientIntensity} />
      <spotLight
        ref={spotRef}
        position={[5, 5, 5]}
        angle={0.4}
        penumbra={1}
        intensity={config.spotlightIntensity}
        color={config.spotlightColor}
        castShadow
        shadow-mapSize={[1024, 1024]}
      />
      <spotLight
        position={[-5, 3, -5]}
        angle={0.5}
        penumbra={0.8}
        intensity={config.spotlightIntensity * 0.3}
        color="#B76E79"
      />
      <pointLight position={[0, 3, 0]} intensity={0.2} color="#ffffff" />
    </>
  );
}

// Camera controls with auto-rotate
function CameraController({
  autoRotate,
  onReset,
}: {
  autoRotate: boolean;
  onReset?: () => void;
}) {
  const controlsRef = useRef<any>(null);

  const reset = useCallback(() => {
    if (controlsRef.current) {
      controlsRef.current.reset();
      onReset?.();
    }
  }, [onReset]);

  // Expose reset function
  useEffect(() => {
    (window as any).__threeViewerReset = reset;
    return () => {
      delete (window as any).__threeViewerReset;
    };
  }, [reset]);

  return (
    <OrbitControls
      ref={controlsRef}
      makeDefault
      autoRotate={autoRotate}
      autoRotateSpeed={1}
      enablePan={true}
      enableZoom={true}
      enableRotate={true}
      minDistance={1}
      maxDistance={10}
      minPolarAngle={0}
      maxPolarAngle={Math.PI * 0.85}
    />
  );
}

// Screenshot functionality
function ScreenshotCapture({
  onCapture,
}: {
  onCapture: (dataUrl: string) => void;
}) {
  const { gl, scene, camera } = useThree();

  useEffect(() => {
    (window as any).__threeViewerScreenshot = () => {
      gl.render(scene, camera);
      const dataUrl = gl.domElement.toDataURL('image/png');
      onCapture(dataUrl);
    };
    return () => {
      delete (window as any).__threeViewerScreenshot;
    };
  }, [gl, scene, camera, onCapture]);

  return null;
}

export function ThreeViewer({
  modelUrl,
  collection = 'signature',
  className = '',
  onScreenshot,
  onLoad,
  onError,
  showControls = true,
  autoRotate: initialAutoRotate = true,
  height = 400,
}: ThreeViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [autoRotate, setAutoRotate] = useState(initialAutoRotate);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [isLoaded, setIsLoaded] = useState(false);

  const config = COLLECTION_LIGHTING[collection];

  const handleFullscreen = useCallback(() => {
    if (!containerRef.current) return;

    if (!isFullscreen) {
      containerRef.current.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  }, [isFullscreen]);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  const handleScreenshot = useCallback(() => {
    (window as any).__threeViewerScreenshot?.();
  }, []);

  const handleReset = useCallback(() => {
    (window as any).__threeViewerReset?.();
  }, []);

  const handleLoad = useCallback(() => {
    setIsLoaded(true);
    onLoad?.();
  }, [onLoad]);

  const handleDownload = useCallback(() => {
    const link = document.createElement('a');
    link.href = modelUrl;
    link.download = modelUrl.split('/').pop() || 'model.glb';
    link.click();
  }, [modelUrl]);

  return (
    <div
      ref={containerRef}
      className={`relative rounded-xl overflow-hidden ${className}`}
      style={{ height: isFullscreen ? '100vh' : height }}
    >
      {/* Canvas */}
      <Canvas
        shadows
        dpr={[1, 2]}
        gl={{
          antialias: true,
          preserveDrawingBuffer: true,
          alpha: false,
        }}
        camera={{ position: [3, 2, 4], fov: 45 }}
        style={{
          background: isDarkMode ? config.bgColor : '#F5F5F5',
        }}
      >
        <Suspense fallback={<Loader />}>
          <CollectionLighting collection={collection} />

          <Center>
            <Model url={modelUrl} onLoad={handleLoad} onError={onError} />
          </Center>

          <ContactShadows
            position={[0, -1.5, 0]}
            opacity={0.5}
            scale={10}
            blur={2}
            far={4}
          />

          <Environment
            preset={isDarkMode ? 'night' : 'studio'}
            background={false}
          />

          <CameraController autoRotate={autoRotate} />

          {onScreenshot && (
            <ScreenshotCapture onCapture={onScreenshot} />
          )}
        </Suspense>
      </Canvas>

      {/* Loading indicator */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900/50 pointer-events-none">
          <div className="flex items-center gap-2 text-white">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Loading 3D Model...</span>
          </div>
        </div>
      )}

      {/* Controls overlay */}
      {showControls && (
        <>
          {/* Collection badge */}
          <Badge
            className="absolute top-3 left-3 bg-gray-900/80 border-gray-700 text-white capitalize backdrop-blur-sm"
          >
            {collection.replace('_', ' ')}
          </Badge>

          {/* Top-right controls */}
          <div className="absolute top-3 right-3 flex gap-2">
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8 bg-gray-900/80 hover:bg-gray-800 text-white backdrop-blur-sm"
              onClick={() => setIsDarkMode(!isDarkMode)}
              title={isDarkMode ? 'Light mode' : 'Dark mode'}
            >
              {isDarkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8 bg-gray-900/80 hover:bg-gray-800 text-white backdrop-blur-sm"
              onClick={handleFullscreen}
              title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Bottom controls */}
          <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-2">
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8 bg-gray-900/80 hover:bg-gray-800 text-white backdrop-blur-sm"
              onClick={handleReset}
              title="Reset view"
            >
              <RotateCcw className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className={`h-8 px-3 backdrop-blur-sm ${
                autoRotate
                  ? 'bg-rose-500/80 hover:bg-rose-600 text-white'
                  : 'bg-gray-900/80 hover:bg-gray-800 text-white'
              }`}
              onClick={() => setAutoRotate(!autoRotate)}
            >
              {autoRotate ? 'Rotating' : 'Rotate'}
            </Button>
            {onScreenshot && (
              <Button
                size="icon"
                variant="ghost"
                className="h-8 w-8 bg-gray-900/80 hover:bg-gray-800 text-white backdrop-blur-sm"
                onClick={handleScreenshot}
                title="Take screenshot"
              >
                <Camera className="h-4 w-4" />
              </Button>
            )}
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8 bg-gray-900/80 hover:bg-gray-800 text-white backdrop-blur-sm"
              onClick={handleDownload}
              title="Download model"
            >
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

// Lightweight model viewer using Google's Model Viewer for better mobile support
export function ModelViewerFallback({
  modelUrl,
  posterUrl,
  collection = 'signature',
  className = '',
  height = 400,
  arEnabled = false,
}: {
  modelUrl: string;
  posterUrl?: string;
  collection?: Collection;
  className?: string;
  height?: string | number;
  arEnabled?: boolean;
}) {
  const config = COLLECTION_LIGHTING[collection];

  return (
    <div
      className={`relative rounded-xl overflow-hidden ${className}`}
      style={{ height, backgroundColor: config.bgColor }}
    >
      {/* @ts-ignore - model-viewer is a web component */}
      <model-viewer
        src={modelUrl}
        poster={posterUrl}
        camera-controls
        auto-rotate
        shadow-intensity="1"
        shadow-softness="0.5"
        exposure="0.8"
        environment-image="neutral"
        ar={arEnabled}
        ar-modes="webxr scene-viewer quick-look"
        style={{ width: '100%', height: '100%' }}
      >
        {arEnabled && (
          <button
            slot="ar-button"
            className="absolute bottom-3 right-3 px-4 py-2 bg-rose-500 text-white rounded-lg font-medium shadow-lg hover:bg-rose-600 transition-colors"
          >
            View in AR
          </button>
        )}
      </model-viewer>

      <Badge
        className="absolute top-3 left-3 bg-gray-900/80 border-gray-700 text-white capitalize backdrop-blur-sm"
      >
        {collection.replace('_', ' ')}
      </Badge>
    </div>
  );
}

// Preload GLTF models
export function preloadModel(url: string) {
  useGLTF.preload(url);
}
