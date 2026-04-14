'use client';

import { Badge } from '@/components/ui/badge';
import { Sparkles, Image, Box, Share2, Pencil, Shirt, Eye } from 'lucide-react';

interface IntentBadgeProps {
  intent: string;
  className?: string;
}

interface IntentConfig {
  label: string;
  className: string;
  icon: React.ComponentType<{ className?: string }>;
}

const INTENT_MAP: Record<string, IntentConfig> = {
  render: {
    label: 'Render',
    className: 'border-[#B76E79]/40 bg-[#B76E79]/10 text-[#B76E79]',
    icon: Image,
  },
  'product-render': {
    label: 'Product Render',
    className: 'border-[#B76E79]/40 bg-[#B76E79]/10 text-[#B76E79]',
    icon: Shirt,
  },
  '3d-model': {
    label: '3D Model',
    className: 'border-[#D4AF37]/40 bg-[#D4AF37]/10 text-[#D4AF37]',
    icon: Box,
  },
  'social-pack': {
    label: 'Social Pack',
    className: 'border-blue-400/40 bg-blue-400/10 text-blue-400',
    icon: Share2,
  },
  'design-ideation': {
    label: 'Design',
    className: 'border-purple-400/40 bg-purple-400/10 text-purple-400',
    icon: Pencil,
  },
  mockup: {
    label: 'Mockup',
    className: 'border-green-400/40 bg-green-400/10 text-green-400',
    icon: Eye,
  },
  'virtual-tryon': {
    label: 'Virtual Try-On',
    className: 'border-[#DC143C]/40 bg-[#DC143C]/10 text-[#DC143C]',
    icon: Shirt,
  },
};

const DEFAULT_CONFIG: IntentConfig = {
  label: 'Operation',
  className: 'border-gray-600 bg-gray-800 text-gray-300',
  icon: Sparkles,
};

export function IntentBadge({ intent, className = '' }: IntentBadgeProps) {
  const config = INTENT_MAP[intent] ?? DEFAULT_CONFIG;
  const Icon = config.icon;
  const label = config === DEFAULT_CONFIG ? intent : config.label;

  return (
    <Badge
      variant="outline"
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 font-medium capitalize ${config.className} ${className}`}
    >
      <Icon className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
      <span>{label}</span>
    </Badge>
  );
}
