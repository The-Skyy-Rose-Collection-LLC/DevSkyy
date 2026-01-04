/**
 * Virtual Try-On Page
 * ===================
 * AI-powered virtual try-on for jewelry and fashion.
 * 
 * Powered by FASHN API for production-grade virtual try-on.
 * 
 * Features:
 * - Upload model photo or use AI-generated model
 * - Select product to try on
 * - Real-time preview with pose adjustment
 * - Download and share results
 */

'use client';

import { useState, useRef } from 'react';
import {
  Upload,
  User,
  Sparkles,
  Download,
  Share2,
  RefreshCw,
  Loader2,
  Check,
  X,
  Image as ImageIcon,
  ZoomIn,
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

type UploadSource = 'upload' | 'url' | 'ai-model';
type Category = 'necklace' | 'earring' | 'ring' | 'bracelet' | 'all';

interface Product {
  id: string;
  name: string;
  imageUrl: string;
  category: Category;
  collection: string;
}

interface TryOnResult {
  id: string;
  resultUrl: string;
  modelUrl: string;
  productUrl: string;
  timestamp: string;
}

export default function VirtualTryOnPage() {
  const [uploadSource, setUploadSource] = useState<UploadSource>('upload');
  const [selectedCategory, setSelectedCategory] = useState<Category>('all');
  const [modelImage, setModelImage] = useState<string | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<TryOnResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<TryOnResult[]>([]);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Mock products (in real app, fetch from WooCommerce)
  const mockProducts: Product[] = [
    {
      id: '1',
      name: 'Black Rose Diamond Necklace',
      imageUrl: '/products/black-rose-necklace.jpg',
      category: 'necklace',
      collection: 'Black Rose',
    },
    {
      id: '2',
      name: 'Love Hurts Heart Earrings',
      imageUrl: '/products/love-hurts-earrings.jpg',
      category: 'earring',
      collection: 'Love Hurts',
    },
    {
      id: '3',
      name: 'Signature Diamond Ring',
      imageUrl: '/products/signature-ring.jpg',
      category: 'ring',
      collection: 'Signature',
    },
  ];

  const filteredProducts = mockProducts.filter(
    (p) => selectedCategory === 'all' || p.category === selectedCategory
  );

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('Image must be smaller than 10MB');
      return;
    }

    // Preview image
    const reader = new FileReader();
    reader.onload = (e) => {
      setModelImage(e.target?.result as string);
      setError(null);
    };
    reader.readAsDataURL(file);
  };

  const handleGenerateAIModel = async () => {
    setIsProcessing(true);
    setError(null);

    try {
      // Call AI model generation endpoint
      const response = await api.post('/api/v1/virtual-tryon/generate-model', {
        gender: 'female',
        ethnicity: 'diverse',
        age_range: '25-35',
        pose: 'frontal',
      });

      setModelImage(response.model_url);
      setIsProcessing(false);
    } catch (err) {
      console.error('AI model generation error:', err);
      setError('Failed to generate AI model');
      setIsProcessing(false);
    }
  };

  const handleTryOn = async () => {
    if (!modelImage || !selectedProduct) {
      setError('Please select both a model photo and a product');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setResult(null);

    try {
      // Submit try-on request
      const response = await api.post('/api/v1/virtual-tryon/try-on', {
        model_image_url: modelImage,
        garment_image_url: selectedProduct.imageUrl,
        category: selectedProduct.category,
      });

      const { job_id } = response;

      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await api.get(`/api/v1/virtual-tryon/jobs/${job_id}`);
          const { status, result_url, error: jobError } = statusResponse;

          if (status === 'completed') {
            clearInterval(pollInterval);
            
            const newResult: TryOnResult = {
              id: job_id,
              resultUrl: result_url,
              modelUrl: modelImage,
              productUrl: selectedProduct.imageUrl,
              timestamp: new Date().toISOString(),
            };
            
            setResult(newResult);
            setHistory(prev => [newResult, ...prev].slice(0, 10)); // Keep last 10
            setIsProcessing(false);
          } else if (status === 'failed') {
            clearInterval(pollInterval);
            setError(jobError || 'Try-on failed');
            setIsProcessing(false);
          }
        } catch (pollError) {
          console.error('Polling error:', pollError);
        }
      }, 2000);

      // Timeout after 2 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        if (isProcessing) {
          setError('Try-on timed out');
          setIsProcessing(false);
        }
      }, 120000);

    } catch (err) {
      console.error('Try-on error:', err);
      setError(err instanceof Error ? err.message : 'Failed to process try-on');
      setIsProcessing(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;
    
    const link = document.createElement('a');
    link.href = result.resultUrl;
    link.download = `tryon-${selectedProduct?.name}-${Date.now()}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Virtual Try-On</h1>
        <p className="text-gray-600 dark:text-gray-400">
          See how SkyyRose jewelry looks on you with AI-powered virtual try-on
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Panel: Model Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Step 1: Choose Model
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Tabs value={uploadSource} onValueChange={(v) => setUploadSource(v as UploadSource)}>
              <TabsList className="w-full">
                <TabsTrigger value="upload" className="flex-1">
                  <Upload className="mr-2 h-4 w-4" />
                  Upload
                </TabsTrigger>
                <TabsTrigger value="ai-model" className="flex-1">
                  <Sparkles className="mr-2 h-4 w-4" />
                  AI Model
                </TabsTrigger>
              </TabsList>

              <TabsContent value="upload" className="space-y-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Upload a photo of yourself or a model (frontal view works best)
                </div>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />

                <Button
                  onClick={() => fileInputRef.current?.click()}
                  variant="outline"
                  className="w-full"
                >
                  <Upload className="mr-2 h-4 w-4" />
                  Choose Photo
                </Button>
              </TabsContent>

              <TabsContent value="ai-model" className="space-y-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Generate an AI model to try on jewelry
                </div>

                <Button
                  onClick={handleGenerateAIModel}
                  disabled={isProcessing}
                  className="w-full"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      Generate AI Model
                    </>
                  )}
                </Button>
              </TabsContent>
            </Tabs>

            {/* Model Preview */}
            {modelImage && (
              <div className="aspect-[3/4] rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 relative">
                <img
                  src={modelImage}
                  alt="Selected model"
                  className="w-full h-full object-cover"
                />
                <div className="absolute top-2 right-2">
                  <Badge variant="success" className="bg-green-600">
                    <Check className="mr-1 h-3 w-3" />
                    Ready
                  </Badge>
                </div>
              </div>
            )}

            {!modelImage && (
              <div className="aspect-[3/4] rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700 flex items-center justify-center">
                <div className="text-center p-4">
                  <User className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                  <p className="text-sm text-gray-500">No model selected</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Middle Panel: Product Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ImageIcon className="h-5 w-5" />
              Step 2: Select Product
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Category Filter */}
            <div className="flex gap-2 flex-wrap">
              {(['all', 'necklace', 'earring', 'ring', 'bracelet'] as Category[]).map((cat) => (
                <Button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  variant={selectedCategory === cat ? 'default' : 'outline'}
                  size="sm"
                >
                  {cat === 'all' ? 'All' : cat.charAt(0).toUpperCase() + cat.slice(1)}s
                </Button>
              ))}
            </div>

            {/* Product Grid */}
            <div className="grid grid-cols-2 gap-3 max-h-[500px] overflow-y-auto">
              {filteredProducts.map((product) => (
                <button
                  key={product.id}
                  onClick={() => setSelectedProduct(product)}
                  className={`relative rounded-lg overflow-hidden border-2 transition-all ${
                    selectedProduct?.id === product.id
                      ? 'border-rose-500 ring-2 ring-rose-500'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="aspect-square bg-gray-100 dark:bg-gray-800">
                    <img
                      src={product.imageUrl}
                      alt={product.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="p-2">
                    <div className="text-xs font-semibold truncate">{product.name}</div>
                    <div className="text-xs text-gray-500">{product.collection}</div>
                  </div>
                  {selectedProduct?.id === product.id && (
                    <div className="absolute top-2 right-2">
                      <Badge className="bg-rose-500">
                        <Check className="h-3 w-3" />
                      </Badge>
                    </div>
                  )}
                </button>
              ))}
            </div>

            {/* Try-On Button */}
            <Button
              onClick={handleTryOn}
              disabled={!modelImage || !selectedProduct || isProcessing}
              className="w-full"
              size="lg"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Try On
                </>
              )}
            </Button>

            {error && (
              <div className="p-3 bg-red-50 dark:bg-red-950 text-red-900 dark:text-red-100 rounded-lg flex items-center gap-2">
                <X className="h-4 w-4" />
                <span className="text-sm">{error}</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right Panel: Result */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ZoomIn className="h-5 w-5" />
              Result
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {result ? (
              <>
                <div className="aspect-[3/4] rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800">
                  <img
                    src={result.resultUrl}
                    alt="Try-on result"
                    className="w-full h-full object-cover"
                  />
                </div>

                <div className="flex gap-2">
                  <Button onClick={handleDownload} variant="outline" className="flex-1">
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </Button>
                  <Button variant="outline" className="flex-1">
                    <Share2 className="mr-2 h-4 w-4" />
                    Share
                  </Button>
                </div>

                <div className="text-sm text-gray-600 dark:text-gray-400 text-center">
                  <Badge variant="success" className="mb-2">
                    <Check className="mr-1 h-3 w-3" />
                    Try-On Complete
                  </Badge>
                  <p>Wearing: {selectedProduct?.name}</p>
                </div>
              </>
            ) : (
              <div className="aspect-[3/4] rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700 flex items-center justify-center">
                <div className="text-center p-4">
                  <Sparkles className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                  <p className="text-sm text-gray-500">
                    {isProcessing ? 'Generating try-on...' : 'Result will appear here'}
                  </p>
                </div>
              </div>
            )}

            {/* History */}
            {history.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2">Recent Try-Ons</h3>
                <div className="grid grid-cols-3 gap-2">
                  {history.map((h) => (
                    <button
                      key={h.id}
                      onClick={() => setResult(h)}
                      className="aspect-square rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 hover:ring-2 ring-rose-500 transition-all"
                    >
                      <img
                        src={h.resultUrl}
                        alt="History"
                        className="w-full h-full object-cover"
                      />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
