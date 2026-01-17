/**
 * HuggingFace Spaces Configuration
 * ==================================
 * Configuration for embedded HuggingFace Spaces in the AI Tools page.
 */

export interface HFSpace {
  id: string;
  name: string;
  description: string;
  url: string;
  icon: string;
  category: 'generation' | 'analysis' | 'training' | 'conversion';
  tags: string[];
}

export const HF_SPACES: HFSpace[] = [
  {
    id: '3d-converter',
    name: '3D Model Converter',
    description: 'Convert between 3D model formats (GLB, FBX, OBJ) with automatic optimization',
    url: 'https://huggingface.co/spaces/damBruh/skyyrose-3d-converter',
    icon: '🎲',
    category: 'conversion',
    tags: ['3D', 'conversion', 'GLB', 'FBX', 'OBJ'],
  },
  {
    id: 'flux-upscaler',
    name: 'Flux Upscaler',
    description: 'AI-powered image upscaling and enhancement using Flux model',
    url: 'https://huggingface.co/spaces/damBruh/skyyrose-flux-upscaler',
    icon: '🔍',
    category: 'generation',
    tags: ['image', 'upscaling', 'enhancement', 'AI'],
  },
  {
    id: 'lora-training-monitor',
    name: 'LoRA Training Monitor',
    description: 'Real-time monitoring and analysis of LoRA model training progress',
    url: 'https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor',
    icon: '📊',
    category: 'training',
    tags: ['LoRA', 'training', 'monitoring', 'ML'],
  },
  {
    id: 'product-analyzer',
    name: 'Product Analyzer',
    description: 'AI-powered product analysis and insights for e-commerce optimization',
    url: 'https://huggingface.co/spaces/damBruh/skyyrose-product-analyzer',
    icon: '🔬',
    category: 'analysis',
    tags: ['product', 'analysis', 'e-commerce', 'AI'],
  },
  {
    id: 'product-photography',
    name: 'Product Photography',
    description: 'Generate professional product photos with AI background removal and enhancement',
    url: 'https://huggingface.co/spaces/damBruh/skyyrose-product-photography',
    icon: '📸',
    category: 'generation',
    tags: ['product', 'photography', 'AI', 'generation'],
  },
];

export const SPACE_CATEGORIES = [
  { id: 'all', label: 'All Spaces', icon: '🌐' },
  { id: 'generation', label: 'Generation', icon: '✨' },
  { id: 'analysis', label: 'Analysis', icon: '🔬' },
  { id: 'training', label: 'Training', icon: '🎓' },
  { id: 'conversion', label: 'Conversion', icon: '🔄' },
] as const;

/**
 * Get space by ID
 */
export function getSpaceById(id: string): HFSpace | undefined {
  return HF_SPACES.find((space) => space.id === id);
}

/**
 * Filter spaces by category
 */
export function getSpacesByCategory(category: string): HFSpace[] {
  if (category === 'all') return HF_SPACES;
  return HF_SPACES.filter((space) => space.category === category);
}

/**
 * Search spaces by name or description
 */
export function searchSpaces(query: string): HFSpace[] {
  const lowerQuery = query.toLowerCase();
  return HF_SPACES.filter(
    (space) =>
      space.name.toLowerCase().includes(lowerQuery) ||
      space.description.toLowerCase().includes(lowerQuery) ||
      space.tags.some((tag) => tag.toLowerCase().includes(lowerQuery))
  );
}
