/**
 * Three.js Collection Viewer Page
 * ================================
 * Dynamic route for immersive 3D collection experiences.
 *
 * Collections:
 * - /collections/black-rose - Black Rose Garden (dark luxury)
 * - /collections/signature - Signature Collection (premium showroom)
 * - /collections/love-hurts - Love Hurts (castle mirror interactive)
 * - /collections/showroom - Product Showroom (interactive showcase)
 * - /collections/runway - Runway Experience (fashion simulation)
 *
 * Features:
 * - Full-screen immersive 3D experience
 * - Dynamic product loading from WooCommerce
 * - Interactive hotspots and navigation
 * - Performance monitoring with automatic quality adjustment
 * - Mobile-responsive with touch controls
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Maximize, Minimize, Settings, Info, X } from 'lucide-react';
import { Button, Badge, Card, CardHeader, CardTitle, CardContent } from '@/components/ui';
import type { CollectionType, Collection3DExperienceSpec, CollectionExperience } from '@/../../src/collections';

// Collection metadata
const COLLECTIONS: Record<string, {
  name: string;
  type: CollectionType;
  description: string;
  color: string;
  tagline: string;
}> = {
  'black-rose': {
    name: 'Black Rose Garden',
    type: 'black_rose',
    description: 'Step into darkness, where luxury blooms in shadow',
    color: '#1A1A1A',
    tagline: 'Dark. Luxurious. Unforgettable.',
  },
  'signature': {
    name: 'Signature Collection',
    type: 'signature',
    description: 'Timeless elegance meets modern sophistication',
    color: '#B76E79',
    tagline: 'Where Love Meets Luxury',
  },
  'love-hurts': {
    name: 'Love Hurts',
    type: 'love_hurts',
    description: 'An interactive castle experience exploring passion and pain',
    color: '#8B0000',
    tagline: 'Beauty in the Broken',
  },
  'showroom': {
    name: 'Product Showroom',
    type: 'showroom',
    description: 'Explore our full catalog in stunning 3D',
    color: '#2C2C2C',
    tagline: 'Discover Your Next Treasure',
  },
  'runway': {
    name: 'Runway Experience',
    type: 'runway',
    description: 'Watch SkyyRose pieces come alive on the virtual runway',
    color: '#F5F5F5',
    tagline: 'Fashion in Motion',
  },
};

export default function CollectionPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params?.slug as string;

  const containerRef = useRef<HTMLDivElement>(null);
  const experienceRef = useRef<CollectionExperience | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [fps, setFps] = useState(60);
  const [loadProgress, setLoadProgress] = useState(0);

  const collection = COLLECTIONS[slug];

  useEffect(() => {
    // Validate collection slug
    if (!collection) {
      setError(`Collection "${slug}" not found`);
      setIsLoading(false);
      return;
    }

    // Initialize collection experience
    const initExperience = async () => {
      if (!containerRef.current) return;

      try {
        setIsLoading(true);
        setLoadProgress(10);

        // Dynamically import collection module
        const { createCollectionExperience } = await import('@/../../src/collections');
        setLoadProgress(30);

        // Fetch products for this collection (optional)
        // In a real implementation, this would fetch from WooCommerce API
        const products: Array<{
          id: string;
          name: string;
          price?: number;
          modelUrl?: string;
          thumbnailUrl?: string;
          position?: [number, number, number] | { x: number; y: number; z: number };
          [key: string]: unknown;
        }> = []; // TODO: Fetch from API
        setLoadProgress(50);

        // Create experience spec
        const spec: Collection3DExperienceSpec = {
          collection: collection.type,
          config: {
            backgroundColor: parseInt(collection.color.replace('#', ''), 16),
            enableBloom: true,
            bloomStrength: 0.5,
            enableDepthOfField: true,
            particleCount: slug === 'black-rose' ? 1000 : 500,
          },
          products,
          interactivity: {
            enableProductCards: true,
            enableCategoryNavigation: true,
            enableSpatialAudio: false, // Disable for now
            enableARPreview: false, // Disable for now
            cursorSpotlight: slug === 'black-rose' || slug === 'love-hurts',
          },
          fallback: {
            enable2DParallax: true,
            lowPerformanceThreshold: 30, // Switch to 2D if <30 FPS
          },
        };
        setLoadProgress(70);

        // Create and initialize experience
        const experience = createCollectionExperience(containerRef.current, spec);
        experienceRef.current = experience;
        setLoadProgress(90);

        // Set up performance monitoring
        let frameCount = 0;
        let lastTime = performance.now();

        const monitorFPS = () => {
          frameCount++;
          const currentTime = performance.now();

          if (currentTime >= lastTime + 1000) {
            const currentFps = Math.round((frameCount * 1000) / (currentTime - lastTime));
            setFps(currentFps);
            frameCount = 0;
            lastTime = currentTime;
          }

          if (experienceRef.current) {
            requestAnimationFrame(monitorFPS);
          }
        };

        requestAnimationFrame(monitorFPS);

        setLoadProgress(100);
        setIsLoading(false);

      } catch (err) {
        console.error('Failed to initialize collection experience:', err);
        setError(err instanceof Error ? err.message : 'Failed to load collection');
        setIsLoading(false);
      }
    };

    initExperience();

    // Cleanup on unmount
    return () => {
      if (experienceRef.current && 'dispose' in experienceRef.current) {
        (experienceRef.current as any).dispose();
      }
      experienceRef.current = null;
    };
  }, [slug, collection]);

  // Fullscreen toggle
  const toggleFullscreen = async () => {
    if (!containerRef.current) return;

    try {
      if (!document.fullscreenElement) {
        await containerRef.current.requestFullscreen();
        setIsFullscreen(true);
      } else {
        await document.exitFullscreen();
        setIsFullscreen(false);
      }
    } catch (err) {
      console.error('Fullscreen error:', err);
    }
  };

  // Handle fullscreen change events
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Error state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error Loading Collection</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
            <Button onClick={() => router.push('/collections')} variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Collections
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-black">
        <div className="text-center space-y-6">
          <div className="relative w-64 h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-rose-500 to-pink-500 transition-all duration-300"
              style={{ width: `${loadProgress}%` }}
            />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white">
              Loading {collection?.name}
            </h2>
            <p className="text-gray-400">{collection?.tagline}</p>
            <p className="text-sm text-gray-500">{loadProgress}%</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-black">
      {/* 3D Experience Container */}
      <div ref={containerRef} className="absolute inset-0" />

      {/* UI Overlay - Top Bar */}
      <div className="absolute top-0 left-0 right-0 p-4 flex items-center justify-between bg-gradient-to-b from-black/80 to-transparent pointer-events-none">
        <div className="flex items-center gap-4 pointer-events-auto">
          <Button
            onClick={() => router.back()}
            variant="ghost"
            size="sm"
            className="text-white hover:bg-white/10"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>

          <div className="hidden md:block">
            <h1 className="text-xl font-bold text-white">{collection?.name}</h1>
            <p className="text-sm text-gray-300">{collection?.description}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 pointer-events-auto">
          <Badge variant="secondary" className="bg-black/50 text-white">
            {fps} FPS
          </Badge>

          <Button
            onClick={() => setShowInfo(!showInfo)}
            variant="ghost"
            size="icon"
            className="text-white hover:bg-white/10"
          >
            <Info className="h-4 w-4" />
          </Button>

          <Button
            onClick={toggleFullscreen}
            variant="ghost"
            size="icon"
            className="text-white hover:bg-white/10"
          >
            {isFullscreen ? (
              <Minimize className="h-4 w-4" />
            ) : (
              <Maximize className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Info Panel */}
      {showInfo && (
        <div className="absolute top-20 right-4 max-w-sm pointer-events-auto">
          <Card className="bg-black/90 border-gray-700 backdrop-blur-md">
            <CardHeader className="flex flex-row items-start justify-between">
              <div>
                <CardTitle className="text-white">{collection?.name}</CardTitle>
                <p className="text-sm text-gray-400 mt-1">{collection?.tagline}</p>
              </div>
              <Button
                onClick={() => setShowInfo(false)}
                variant="ghost"
                size="icon"
                className="text-white hover:bg-white/10"
              >
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-white mb-2">Controls</h3>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>• <strong>Mouse/Touch:</strong> Look around</li>
                  <li>• <strong>Click/Tap:</strong> Interact with products</li>
                  <li>• <strong>Scroll:</strong> Zoom in/out</li>
                  <li>• <strong>Arrow Keys:</strong> Navigate</li>
                </ul>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-white mb-2">Performance</h3>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Frame Rate:</span>
                  <span className={fps >= 50 ? 'text-green-400' : fps >= 30 ? 'text-yellow-400' : 'text-red-400'}>
                    {fps} FPS
                  </span>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-white mb-2">About</h3>
                <p className="text-sm text-gray-300">
                  {collection?.description}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Mobile hint (hidden on fullscreen) */}
      {!isFullscreen && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 pointer-events-none md:hidden">
          <Badge variant="secondary" className="bg-black/50 text-white backdrop-blur-sm">
            Tap anywhere to interact
          </Badge>
        </div>
      )}
    </div>
  );
}
