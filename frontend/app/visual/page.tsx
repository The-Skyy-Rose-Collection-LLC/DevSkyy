/**
 * Visual Generation Page
 * ======================
 * Generate product photography and visual content using AI.
 * 
 * Providers:
 * - Google Imagen 3: High-quality product photography
 * - HuggingFace FLUX.1: Fast, creative images
 * - Google Veo 2: Video generation (coming soon)
 * 
 * Styles:
 * - Product Studio: Clean white background
 * - Lifestyle: In-context lifestyle shots
 * - Flat Lay: Top-down product arrangement
 * - Hero: Hero banner images
 * - Detail: Close-up detail shots
 */

'use client';

import { useState } from 'react';
import {
  Image as ImageIcon,
  Video,
  Sparkles,
  Download,
  RefreshCw,
  Loader2,
  Check,
  X,
  Info,
} from 'lucide-react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/components/ui';
import { api } from '@/lib/api';

type Provider = 'google_imagen' | 'huggingface_flux' | 'google_veo' | 'auto';
type ImageStyle = 'product_studio' | 'lifestyle' | 'flat_lay' | 'hero' | 'detail';
type AspectRatio = '1:1' | '4:3' | '16:9' | '9:16';
type Quality = 'low' | 'medium' | 'high';

interface GeneratedImage {
  id: string;
  url: string;
  provider: string;
  style: string;
  timestamp: string;
}

const PROVIDER_INFO = {
  google_imagen: {
    name: 'Imagen 3',
    description: 'Google\'s latest high-quality image generation model',
    icon: Sparkles,
    color: '#4285f4',
    speed: 'Slow',
    quality: 'Highest',
  },
  huggingface_flux: {
    name: 'FLUX.1',
    description: 'Black Forest Labs fast, creative image generation',
    icon: ImageIcon,
    color: '#ff7000',
    speed: 'Fast',
    quality: 'High',
  },
  google_veo: {
    name: 'Veo 2',
    description: 'Google\'s advanced video generation (coming soon)',
    icon: Video,
    color: '#ea4335',
    speed: 'Very Slow',
    quality: 'Cinematic',
  },
  auto: {
    name: 'Auto-Select',
    description: 'Automatically choose the best provider',
    icon: Sparkles,
    color: '#B76E79',
    speed: 'Varies',
    quality: 'Optimized',
  },
};

const STYLE_INFO: Record<ImageStyle, { name: string; description: string; example: string }> = {
  product_studio: {
    name: 'Product Studio',
    description: 'Clean white background, professional lighting',
    example: 'Perfect for e-commerce listings',
  },
  lifestyle: {
    name: 'Lifestyle',
    description: 'Product in real-world context',
    example: 'Jewelry on model, in elegant setting',
  },
  flat_lay: {
    name: 'Flat Lay',
    description: 'Top-down product arrangement',
    example: 'Multiple pieces arranged aesthetically',
  },
  hero: {
    name: 'Hero Banner',
    description: 'Dramatic, banner-style composition',
    example: 'Perfect for landing pages',
  },
  detail: {
    name: 'Detail Shot',
    description: 'Close-up showcasing craftsmanship',
    example: 'Macro photography of gemstones',
  },
};

export default function VisualGenerationPage() {
  const [provider, setProvider] = useState<Provider>('auto');
  const [prompt, setPrompt] = useState('');
  const [productName, setProductName] = useState('');
  const [collection, setCollection] = useState('SIGNATURE');
  const [style, setStyle] = useState<ImageStyle>('product_studio');
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>('1:1');
  const [quality, setQuality] = useState<Quality>('high');
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<GeneratedImage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<GeneratedImage[]>([]);

  const handleGenerate = async () => {
    if (!productName.trim()) {
      setError('Please enter a product name');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setResult(null);
    setProgress(0);

    try {
      // Submit generation job
      const response = await api.post('/api/v1/visual/generate', {
        product_name: productName,
        collection,
        style,
        provider: provider === 'google_veo' ? 'google_imagen' : provider, // Fallback for Veo (not yet available)
        aspect_ratio: aspectRatio,
        quality,
      });

      const { job_id } = response;
      setJobId(job_id);
      setProgress(10);

      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await api.get(`/api/v1/visual/jobs/${job_id}`);
          const { status, image_url, error: jobError } = statusResponse;

          if (status === 'completed') {
            clearInterval(pollInterval);
            setProgress(100);
            
            const newImage: GeneratedImage = {
              id: job_id,
              url: image_url,
              provider: provider === 'auto' ? 'auto-selected' : provider,
              style,
              timestamp: new Date().toISOString(),
            };
            
            setResult(newImage);
            setHistory(prev => [newImage, ...prev].slice(0, 20)); // Keep last 20
            setIsGenerating(false);
          } else if (status === 'failed') {
            clearInterval(pollInterval);
            setError(jobError || 'Generation failed');
            setIsGenerating(false);
          } else {
            // Update progress based on status
            setProgress(prev => Math.min(prev + 10, 90));
          }
        } catch (pollError) {
          console.error('Polling error:', pollError);
        }
      }, 2000); // Poll every 2 seconds

      // Timeout after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        if (isGenerating) {
          setError('Generation timed out');
          setIsGenerating(false);
        }
      }, 300000);

    } catch (err) {
      console.error('Generation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate image');
      setIsGenerating(false);
    }
  };

  const handleDownload = (imageUrl: string, filename: string) => {
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const selectedProviderInfo = PROVIDER_INFO[provider];

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Visual Generation</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Generate stunning product photography and visual content with AI
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Configuration Panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* Provider Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Select Provider
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {(Object.keys(PROVIDER_INFO) as Provider[]).map((p) => {
                  const info = PROVIDER_INFO[p];
                  const Icon = info.icon;
                  const isDisabled = p === 'google_veo'; // Veo not yet available

                  return (
                    <button
                      key={p}
                      onClick={() => !isDisabled && setProvider(p)}
                      disabled={isDisabled}
                      className={`p-4 rounded-lg border-2 transition-all ${
                        provider === p
                          ? 'border-rose-500 bg-rose-50 dark:bg-rose-950'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                      } ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                    >
                      <Icon className="h-6 w-6 mb-2" style={{ color: info.color }} />
                      <div className="text-sm font-semibold">{info.name}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {info.speed} • {info.quality}
                      </div>
                      {isDisabled && (
                        <Badge variant="secondary" className="mt-2 text-xs">
                          Coming Soon
                        </Badge>
                      )}
                    </button>
                  );
                })}
              </div>

              <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
                <div className="flex items-start gap-2">
                  <Info className="h-4 w-4 mt-0.5 text-blue-600" />
                  <div className="text-sm text-blue-900 dark:text-blue-100">
                    <strong>{selectedProviderInfo.name}:</strong> {selectedProviderInfo.description}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Generation Form */}
          <Card>
            <CardHeader>
              <CardTitle>Product Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Product Name *</label>
                <input
                  type="text"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="e.g., Black Rose Diamond Necklace"
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Collection</label>
                <select
                  value={collection}
                  onChange={(e) => setCollection(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                >
                  <option value="SIGNATURE">Signature Collection</option>
                  <option value="BLACK_ROSE">Black Rose Garden</option>
                  <option value="LOVE_HURTS">Love Hurts</option>
                  <option value="CUSTOM">Custom Design</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Style</label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {(Object.keys(STYLE_INFO) as ImageStyle[]).map((s) => (
                    <button
                      key={s}
                      onClick={() => setStyle(s)}
                      className={`p-3 text-left rounded-lg border-2 transition-all ${
                        style === s
                          ? 'border-rose-500 bg-rose-50 dark:bg-rose-950'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <div className="text-sm font-semibold">{STYLE_INFO[s].name}</div>
                      <div className="text-xs text-gray-500 mt-1">{STYLE_INFO[s].example}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Aspect Ratio</label>
                  <select
                    value={aspectRatio}
                    onChange={(e) => setAspectRatio(e.target.value as AspectRatio)}
                    className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                  >
                    <option value="1:1">1:1 (Square)</option>
                    <option value="4:3">4:3 (Standard)</option>
                    <option value="16:9">16:9 (Wide)</option>
                    <option value="9:16">9:16 (Portrait)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Quality</label>
                  <select
                    value={quality}
                    onChange={(e) => setQuality(e.target.value as Quality)}
                    className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                  >
                    <option value="low">Low (Fast)</option>
                    <option value="medium">Medium</option>
                    <option value="high">High (Best)</option>
                  </select>
                </div>
              </div>

              <Button
                onClick={handleGenerate}
                disabled={isGenerating || !productName.trim()}
                className="w-full"
                size="lg"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating... {progress}%
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Image
                  </>
                )}
              </Button>

              {error && (
                <div className="p-3 bg-red-50 dark:bg-red-950 text-red-900 dark:text-red-100 rounded-lg flex items-center gap-2">
                  <X className="h-4 w-4" />
                  {error}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Result Panel */}
        <div className="space-y-6">
          {/* Current Result */}
          {result && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Check className="h-5 w-5 text-green-600" />
                  Generated Image
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="aspect-square rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800">
                  <img
                    src={result.url}
                    alt="Generated product"
                    className="w-full h-full object-cover"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Provider:</span>
                    <Badge variant="secondary">{result.provider}</Badge>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Style:</span>
                    <span className="font-medium">{STYLE_INFO[style].name}</span>
                  </div>
                </div>

                <Button
                  onClick={() => handleDownload(result.url, `${productName}-${style}.jpg`)}
                  variant="outline"
                  className="w-full"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
              </CardContent>
            </Card>
          )}

          {/* History */}
          {history.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Generations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-2">
                  {history.map((img) => (
                    <button
                      key={img.id}
                      onClick={() => setResult(img)}
                      className="aspect-square rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 hover:ring-2 ring-rose-500 transition-all"
                    >
                      <img
                        src={img.url}
                        alt="Generated"
                        className="w-full h-full object-cover"
                      />
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
