/**
 * Brand Kit Settings Page
 * =======================
 * Display SkyyRose brand configuration: colors, tone, typography, collections.
 */

'use client';

import Link from 'next/link';
import {
  Palette,
  Type,
  Users,
  Sparkles,
  ArrowLeft,
  Copy,
  Check,
} from 'lucide-react';
import { useState } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
} from '@/components/ui';
import { useBrand } from '@/lib/hooks';

export default function BrandKitPage() {
  const { data: brandData, isLoading } = useBrand();
  const [copiedColor, setCopiedColor] = useState<string | null>(null);

  const copyToClipboard = (text: string, colorName: string) => {
    navigator.clipboard.writeText(text);
    setCopiedColor(colorName);
    setTimeout(() => setCopiedColor(null), 2000);
  };

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="h-20 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-64 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const brand = brandData?.brand;
  const collections = brandData?.collections;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/settings">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Settings
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Palette className="h-8 w-8 text-brand-primary" />
            Brand Kit
          </h1>
          <p className="text-gray-500 mt-1">
            {brand?.name} • {brand?.philosophy}
          </p>
        </div>
      </div>

      {/* Brand Identity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Brand Identity
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm text-gray-500">Name</p>
              <p className="font-semibold text-lg">{brand?.name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Tagline</p>
              <p className="font-semibold text-lg">{brand?.tagline}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Philosophy</p>
              <p className="font-semibold">{brand?.philosophy}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Location</p>
              <p className="font-semibold">{brand?.location}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Color Palette */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            Color Palette
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 grid-cols-2 md:grid-cols-5">
            {brand?.colors && Object.entries(brand.colors).map(([key, color]) => (
              <div key={key} className="text-center">
                <button
                  onClick={() => copyToClipboard(color.hex, key)}
                  className="w-full h-20 rounded-lg shadow-md hover:scale-105 transition-transform relative group"
                  style={{ backgroundColor: color.hex }}
                >
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/20 rounded-lg">
                    {copiedColor === key ? (
                      <Check className="h-5 w-5 text-white" />
                    ) : (
                      <Copy className="h-5 w-5 text-white" />
                    )}
                  </div>
                </button>
                <p className="text-sm font-medium mt-2">{color.name}</p>
                <p className="text-xs text-gray-500">{color.hex}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Typography */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Type className="h-5 w-5" />
            Typography
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="space-y-2">
              <p className="text-sm text-gray-500">Heading Font</p>
              <p className="text-2xl font-serif">{brand?.typography.heading}</p>
              <p className="text-xs text-gray-400">Used for titles and headers</p>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-gray-500">Body Font</p>
              <p className="text-2xl">{brand?.typography.body}</p>
              <p className="text-xs text-gray-400">Used for body text</p>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-gray-500">Accent Font</p>
              <p className="text-2xl italic">{brand?.typography.accent}</p>
              <p className="text-xs text-gray-400">Used for quotes and accents</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tone of Voice */}
      <Card>
        <CardHeader>
          <CardTitle>Tone of Voice</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-lg font-semibold text-brand-primary">{brand?.tone.primary}</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm font-medium text-green-600 mb-2">✓ Do Use</p>
              <ul className="space-y-1">
                {brand?.tone.descriptors.map((d, i) => (
                  <li key={i} className="text-sm text-gray-600 dark:text-gray-400">• {d}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-sm font-medium text-red-600 mb-2">✗ Avoid</p>
              <ul className="space-y-1">
                {brand?.tone.avoid.map((a, i) => (
                  <li key={i} className="text-sm text-gray-600 dark:text-gray-400">• {a}</li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Target Audience */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Target Audience
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm text-gray-500">Age Range</p>
              <p className="font-semibold">{brand?.target_audience.age_range}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Description</p>
              <p className="font-semibold">{brand?.target_audience.description}</p>
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-2">Interests</p>
            <div className="flex flex-wrap gap-2">
              {brand?.target_audience.interests.map((interest, i) => (
                <Badge key={i} variant="outline">{interest}</Badge>
              ))}
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-2">Values</p>
            <div className="flex flex-wrap gap-2">
              {brand?.target_audience.values.map((value, i) => (
                <Badge key={i} variant="secondary">{value}</Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Collections */}
      <Card>
        <CardHeader>
          <CardTitle>Collections</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {collections && Object.entries(collections).map(([key, coll]) => (
              <div key={key} className="border rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-lg">{coll.name}</h3>
                  <Badge variant="outline">{key}</Badge>
                </div>
                <p className="text-sm text-brand-primary font-medium mb-2">{coll.tagline}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{coll.description}</p>
                <div className="space-y-1 text-xs text-gray-500">
                  <p><span className="font-medium">Mood:</span> {coll.mood}</p>
                  <p><span className="font-medium">Colors:</span> {coll.colors}</p>
                  <p><span className="font-medium">Style:</span> {coll.style}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Product Types */}
      <Card>
        <CardHeader>
          <CardTitle>Product Types</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {brand?.product_types.map((type, i) => (
              <Badge key={i} variant="outline" className="text-sm py-1 px-3">
                {type}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quality Descriptors */}
      <Card>
        <CardHeader>
          <CardTitle>Quality Descriptors</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
            {brand?.quality_descriptors.map((desc, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <Sparkles className="h-4 w-4 text-brand-primary" />
                {desc}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

