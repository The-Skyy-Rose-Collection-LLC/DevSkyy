/**
 * Brand DNA Editor
 * ================
 * Configure SkyyRose brand identity, voice, and styling.
 * 
 * Editable Brand Elements:
 * - Brand identity (name, tagline, philosophy)
 * - Tone and voice guidelines
 * - Color palette
 * - Typography
 * - Target audience
 * - Product types and quality descriptors
 * - Collection definitions
 */

'use client';

import { useState, useEffect } from 'react';
import {
  Palette,
  Type,
  Users,
  Sparkles,
  Save,
  RefreshCw,
  Plus,
  X,
  Check,
  Eye,
  Edit,
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

interface BrandDNA {
  name: string;
  tagline: string;
  philosophy: string;
  location: string;
  tone: {
    primary: string;
    descriptors: string[];
    avoid: string[];
  };
  colors: {
    primary: { name: string; hex: string; rgb: string };
    accent: { name: string; hex: string; rgb: string };
    highlight: { name: string; hex: string; rgb: string };
    ivory: { name: string; hex: string; rgb: string };
    obsidian: { name: string; hex: string; rgb: string };
  };
  typography: {
    heading: string;
    body: string;
    accent: string;
  };
  target_audience: {
    age_range: string;
    description: string;
    interests: string[];
    values: string[];
  };
  product_types: string[];
  quality_descriptors: string[];
}

// Default SkyyRose brand DNA
const DEFAULT_BRAND_DNA: BrandDNA = {
  name: 'The Skyy Rose Collection',
  tagline: 'Luxury Streetwear with Soul',
  philosophy: 'Where Love Meets Luxury',
  location: 'Oakland, California',
  tone: {
    primary: 'Elegant, empowering, romantic, bold',
    descriptors: [
      'sophisticated yet accessible',
      'poetic but not pretentious',
      'confident without arrogance',
      'romantic with edge',
    ],
    avoid: [
      'generic fashion buzzwords',
      'overly casual language',
      'aggressive or harsh tones',
      'clichéd luxury language',
    ],
  },
  colors: {
    primary: { name: 'Black Rose', hex: '#1A1A1A', rgb: '26, 26, 26' },
    accent: { name: 'Rose Gold', hex: '#D4AF37', rgb: '212, 175, 55' },
    highlight: { name: 'Deep Rose', hex: '#8B0000', rgb: '139, 0, 0' },
    ivory: { name: 'Ivory', hex: '#F5F5F0', rgb: '245, 245, 240' },
    obsidian: { name: 'Obsidian', hex: '#0D0D0D', rgb: '13, 13, 13' },
  },
  typography: {
    heading: 'Playfair Display',
    body: 'Inter',
    accent: 'Cormorant Garamond',
  },
  target_audience: {
    age_range: '18-35',
    description: 'Fashion-forward individuals who value self-expression',
    interests: ['streetwear', 'luxury fashion', 'self-expression', 'art', 'music'],
    values: ['authenticity', 'quality', 'individuality', 'emotional connection'],
  },
  product_types: ['hoodies', 'tees', 'bombers', 'track pants', 'accessories', 'caps', 'beanies'],
  quality_descriptors: [
    'premium heavyweight cotton',
    'meticulous construction',
    'attention to detail',
    'limited edition exclusivity',
    'elevated street poetry',
  ],
};

export default function BrandDNAEditorPage() {
  const [brandDNA, setBrandDNA] = useState<BrandDNA>(DEFAULT_BRAND_DNA);
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [previewMode, setPreviewMode] = useState(false);

  // Load brand DNA from API
  useEffect(() => {
    const loadBrandDNA = async () => {
      try {
        const response = await api.get('/api/v1/brand/dna');
        setBrandDNA(response);
      } catch (err) {
        console.error('Failed to load brand DNA:', err);
        // Use defaults if load fails
      }
    };
    loadBrandDNA();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    setSaveStatus('idle');

    try {
      await api.post('/api/v1/brand/dna', brandDNA);
      setHasChanges(false);
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (err) {
      console.error('Failed to save brand DNA:', err);
      setSaveStatus('error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setBrandDNA(DEFAULT_BRAND_DNA);
    setHasChanges(true);
  };

  const updateBrandDNA = (path: string, value: any) => {
    const pathParts = path.split('.');
    const newDNA = { ...brandDNA };
    let current: any = newDNA;
    
    for (let i = 0; i < pathParts.length - 1; i++) {
      current = current[pathParts[i]];
    }
    
    current[pathParts[pathParts.length - 1]] = value;
    setBrandDNA(newDNA);
    setHasChanges(true);
  };

  const addArrayItem = (path: string, item: string) => {
    const pathParts = path.split('.');
    const current: any = brandDNA;
    let target: any = current;
    
    for (const part of pathParts) {
      target = target[part];
    }
    
    target.push(item);
    setBrandDNA({ ...brandDNA });
    setHasChanges(true);
  };

  const removeArrayItem = (path: string, index: number) => {
    const pathParts = path.split('.');
    const current: any = brandDNA;
    let target: any = current;
    
    for (const part of pathParts) {
      target = target[part];
    }
    
    target.splice(index, 1);
    setBrandDNA({ ...brandDNA });
    setHasChanges(true);
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Brand DNA Editor</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Configure SkyyRose brand identity and voice
          </p>
        </div>

        <div className="flex items-center gap-2">
          {hasChanges && (
            <Badge variant="warning">Unsaved Changes</Badge>
          )}
          
          {saveStatus === 'success' && (
            <Badge variant="success">
              <Check className="mr-1 h-3 w-3" />
              Saved
            </Badge>
          )}

          <Button onClick={handleReset} variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            Reset
          </Button>

          <Button
            onClick={() => setPreviewMode(!previewMode)}
            variant="outline"
            size="sm"
          >
            {previewMode ? (
              <>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </>
            ) : (
              <>
                <Eye className="mr-2 h-4 w-4" />
                Preview
              </>
            )}
          </Button>

          <Button
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
            size="sm"
          >
            <Save className="mr-2 h-4 w-4" />
            {isSaving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="identity" className="space-y-6">
        <TabsList>
          <TabsTrigger value="identity">Identity</TabsTrigger>
          <TabsTrigger value="voice">Voice & Tone</TabsTrigger>
          <TabsTrigger value="colors">Colors</TabsTrigger>
          <TabsTrigger value="typography">Typography</TabsTrigger>
          <TabsTrigger value="audience">Audience</TabsTrigger>
          <TabsTrigger value="products">Products</TabsTrigger>
        </TabsList>

        {/* Identity Tab */}
        <TabsContent value="identity" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Brand Identity</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Brand Name</label>
                <input
                  type="text"
                  value={brandDNA.name}
                  onChange={(e) => updateBrandDNA('name', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Tagline</label>
                <input
                  type="text"
                  value={brandDNA.tagline}
                  onChange={(e) => updateBrandDNA('tagline', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Philosophy</label>
                <input
                  type="text"
                  value={brandDNA.philosophy}
                  onChange={(e) => updateBrandDNA('philosophy', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Location</label>
                <input
                  type="text"
                  value={brandDNA.location}
                  onChange={(e) => updateBrandDNA('location', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Voice & Tone Tab */}
        <TabsContent value="voice" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Voice & Tone</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Primary Tone</label>
                <textarea
                  value={brandDNA.tone.primary}
                  onChange={(e) => updateBrandDNA('tone.primary', e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Tone Descriptors</label>
                <div className="space-y-2">
                  {brandDNA.tone.descriptors.map((desc, i) => (
                    <div key={i} className="flex gap-2">
                      <input
                        type="text"
                        value={desc}
                        onChange={(e) => {
                          const newDescriptors = [...brandDNA.tone.descriptors];
                          newDescriptors[i] = e.target.value;
                          updateBrandDNA('tone.descriptors', newDescriptors);
                        }}
                        className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                      />
                      <Button
                        onClick={() => removeArrayItem('tone.descriptors', i)}
                        variant="outline"
                        size="icon"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                  <Button
                    onClick={() => addArrayItem('tone.descriptors', '')}
                    variant="outline"
                    size="sm"
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add Descriptor
                  </Button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Avoid</label>
                <div className="space-y-2">
                  {brandDNA.tone.avoid.map((avoid, i) => (
                    <div key={i} className="flex gap-2">
                      <input
                        type="text"
                        value={avoid}
                        onChange={(e) => {
                          const newAvoid = [...brandDNA.tone.avoid];
                          newAvoid[i] = e.target.value;
                          updateBrandDNA('tone.avoid', newAvoid);
                        }}
                        className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                      />
                      <Button
                        onClick={() => removeArrayItem('tone.avoid', i)}
                        variant="outline"
                        size="icon"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                  <Button
                    onClick={() => addArrayItem('tone.avoid', '')}
                    variant="outline"
                    size="sm"
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add Avoid
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Colors Tab */}
        <TabsContent value="colors" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Brand Colors
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries(brandDNA.colors).map(([key, color]) => (
                <div key={key} className="flex items-center gap-4">
                  <div
                    className="w-16 h-16 rounded-lg border-2 border-gray-300"
                    style={{ backgroundColor: color.hex }}
                  />
                  <div className="flex-1 grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs font-medium mb-1">Name</label>
                      <input
                        type="text"
                        value={color.name}
                        onChange={(e) => updateBrandDNA(`colors.${key}.name`, e.target.value)}
                        className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-800 dark:border-gray-700"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium mb-1">Hex</label>
                      <input
                        type="text"
                        value={color.hex}
                        onChange={(e) => updateBrandDNA(`colors.${key}.hex`, e.target.value)}
                        className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-800 dark:border-gray-700"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium mb-1">RGB</label>
                      <input
                        type="text"
                        value={color.rgb}
                        onChange={(e) => updateBrandDNA(`colors.${key}.rgb`, e.target.value)}
                        className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-800 dark:border-gray-700"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Typography Tab */}
        <TabsContent value="typography" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Type className="h-5 w-5" />
                Typography
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Heading Font</label>
                <input
                  type="text"
                  value={brandDNA.typography.heading}
                  onChange={(e) => updateBrandDNA('typography.heading', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Body Font</label>
                <input
                  type="text"
                  value={brandDNA.typography.body}
                  onChange={(e) => updateBrandDNA('typography.body', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Accent Font</label>
                <input
                  type="text"
                  value={brandDNA.typography.accent}
                  onChange={(e) => updateBrandDNA('typography.accent', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Audience Tab */}
        <TabsContent value="audience" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Target Audience
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Age Range</label>
                  <input
                    type="text"
                    value={brandDNA.target_audience.age_range}
                    onChange={(e) => updateBrandDNA('target_audience.age_range', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={brandDNA.target_audience.description}
                  onChange={(e) => updateBrandDNA('target_audience.description', e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Products Tab */}
        <TabsContent value="products" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Product Types & Descriptors
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2">Product Types</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {brandDNA.product_types.map((type, i) => (
                    <Badge key={i} variant="secondary">
                      {type}
                      <button
                        onClick={() => removeArrayItem('product_types', i)}
                        className="ml-2"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
                <Button
                  onClick={() => addArrayItem('product_types', '')}
                  variant="outline"
                  size="sm"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Product Type
                </Button>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Quality Descriptors</label>
                <div className="space-y-2">
                  {brandDNA.quality_descriptors.map((desc, i) => (
                    <div key={i} className="flex gap-2">
                      <input
                        type="text"
                        value={desc}
                        onChange={(e) => {
                          const newDescriptors = [...brandDNA.quality_descriptors];
                          newDescriptors[i] = e.target.value;
                          updateBrandDNA('quality_descriptors', newDescriptors);
                        }}
                        className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                      />
                      <Button
                        onClick={() => removeArrayItem('quality_descriptors', i)}
                        variant="outline"
                        size="icon"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                  <Button
                    onClick={() => addArrayItem('quality_descriptors', '')}
                    variant="outline"
                    size="sm"
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add Descriptor
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
