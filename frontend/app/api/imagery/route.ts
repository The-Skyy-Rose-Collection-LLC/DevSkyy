/**
 * Imagery API Route Handler
 *
 * Proxies image generation requests to the visual generation pipeline
 * (Gemini, Imagen 3, HuggingFace FLUX, Replicate LoRA).
 *
 * POST /api/imagery — Submit a generation request
 * GET  /api/imagery — Return provider statuses and generation stats
 */

import { NextRequest, NextResponse } from 'next/server';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface GenerationRequest {
  prompt: string;
  provider?: 'gemini' | 'imagen' | 'flux' | 'replicate' | 'auto';
  style?: 'product-photo' | 'lifestyle' | 'editorial' | 'flat-lay';
  aspectRatio?: '1:1' | '4:3' | '16:9' | '9:16';
  collection?: string;
}

interface GenerationRecord {
  id: string;
  prompt: string;
  provider: string;
  style: string;
  aspectRatio: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  imageUrl?: string;
  imageBase64?: string;
  error?: string;
  createdAt: string;
  completedAt?: string;
  durationMs?: number;
}

// ---------------------------------------------------------------------------
// In-memory store (bounded)
// ---------------------------------------------------------------------------

const MAX_RECORDS = 500;
const generations: Map<string, GenerationRecord> = new Map();
let totalGenerations = 0;
let totalSuccesses = 0;
let totalDurationMs = 0;

function addRecord(record: GenerationRecord) {
  if (generations.size >= MAX_RECORDS) {
    const oldest = generations.keys().next().value;
    if (oldest !== undefined) {
      generations.delete(oldest);
    }
  }
  generations.set(record.id, record);
}

// ---------------------------------------------------------------------------
// Provider configs
// ---------------------------------------------------------------------------

interface ProviderConfig {
  name: string;
  model: string;
  envKey: string;
  endpoint: string;
  avgLatencyMs: number;
  costPerImage: number;
}

const PROVIDERS: Record<string, ProviderConfig> = {
  gemini: {
    name: 'Gemini',
    model: 'gemini-2.0-flash-preview-image-generation',
    envKey: 'GOOGLE_API_KEY',
    endpoint: 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent',
    avgLatencyMs: 3200,
    costPerImage: 0.02,
  },
  imagen: {
    name: 'Imagen 3',
    model: 'imagen-3.0-generate-002',
    envKey: 'GOOGLE_API_KEY',
    endpoint: 'https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:generateImage',
    avgLatencyMs: 5800,
    costPerImage: 0.04,
  },
  flux: {
    name: 'HuggingFace FLUX',
    model: 'black-forest-labs/FLUX.1-schnell',
    envKey: 'HUGGINGFACE_API_KEY',
    endpoint: 'https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell',
    avgLatencyMs: 8400,
    costPerImage: 0.01,
  },
  replicate: {
    name: 'Replicate LoRA',
    model: 'devskyy/skyyrose-lora-v3',
    envKey: 'REPLICATE_API_TOKEN',
    endpoint: 'https://api.replicate.com/v1/predictions',
    avgLatencyMs: 12000,
    costPerImage: 0.003,
  },
};

function getProviderStatus(key: string): 'connected' | 'disconnected' {
  const config = PROVIDERS[key];
  if (!config) return 'disconnected';
  return process.env[config.envKey] ? 'connected' : 'disconnected';
}

function selectProvider(preferred?: string): string {
  if (preferred && preferred !== 'auto') {
    if (getProviderStatus(preferred) === 'connected') return preferred;
  }
  // Auto-select: prefer gemini > imagen > flux > replicate
  for (const key of ['gemini', 'imagen', 'flux', 'replicate']) {
    if (getProviderStatus(key) === 'connected') return key;
  }
  return 'gemini'; // fallback
}

// ---------------------------------------------------------------------------
// Generation logic per provider
// ---------------------------------------------------------------------------

async function generateWithGemini(prompt: string, apiKey: string): Promise<{ imageBase64?: string; error?: string }> {
  const resp = await fetch(PROVIDERS.gemini.endpoint + `?key=${apiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: { responseModalities: ['TEXT', 'IMAGE'] },
    }),
  });

  if (!resp.ok) {
    const err = await resp.text();
    return { error: `Gemini API error (${resp.status}): ${err.slice(0, 200)}` };
  }

  const data = await resp.json();
  const parts = data?.candidates?.[0]?.content?.parts || [];
  for (const part of parts) {
    if (part.inlineData?.mimeType?.startsWith('image/')) {
      return { imageBase64: `data:${part.inlineData.mimeType};base64,${part.inlineData.data}` };
    }
  }
  return { error: 'No image returned from Gemini' };
}

async function generateWithImagen(prompt: string, apiKey: string): Promise<{ imageBase64?: string; error?: string }> {
  const resp = await fetch(PROVIDERS.imagen.endpoint + `?key=${apiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      instances: [{ prompt }],
      parameters: { sampleCount: 1 },
    }),
  });

  if (!resp.ok) {
    const err = await resp.text();
    return { error: `Imagen API error (${resp.status}): ${err.slice(0, 200)}` };
  }

  const data = await resp.json();
  const image = data?.predictions?.[0]?.bytesBase64Encoded;
  if (image) {
    return { imageBase64: `data:image/png;base64,${image}` };
  }
  return { error: 'No image returned from Imagen' };
}

async function generateWithFlux(prompt: string, apiKey: string): Promise<{ imageBase64?: string; error?: string }> {
  const resp = await fetch(PROVIDERS.flux.endpoint, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ inputs: prompt }),
  });

  if (!resp.ok) {
    const err = await resp.text();
    return { error: `FLUX API error (${resp.status}): ${err.slice(0, 200)}` };
  }

  const buffer = await resp.arrayBuffer();
  const base64 = Buffer.from(buffer).toString('base64');
  return { imageBase64: `data:image/png;base64,${base64}` };
}

async function generateWithReplicate(prompt: string, apiToken: string): Promise<{ imageBase64?: string; imageUrl?: string; error?: string }> {
  const resp = await fetch(PROVIDERS.replicate.endpoint, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      version: 'devskyy/skyyrose-lora-v3',
      input: { prompt: `skyyrose ${prompt}`, num_outputs: 1 },
    }),
  });

  if (!resp.ok) {
    const err = await resp.text();
    return { error: `Replicate API error (${resp.status}): ${err.slice(0, 200)}` };
  }

  const data = await resp.json();

  // Replicate returns a prediction that may need polling
  if (data.status === 'succeeded' && data.output?.[0]) {
    return { imageUrl: data.output[0] };
  }

  // For async predictions, return the URL as-is for now
  if (data.urls?.get) {
    return { imageUrl: data.urls.get, error: 'Prediction is processing — poll status endpoint' };
  }

  return { error: 'Unexpected Replicate response' };
}

async function generateImage(provider: string, prompt: string): Promise<{ imageBase64?: string; imageUrl?: string; error?: string }> {
  const config = PROVIDERS[provider];
  if (!config) return { error: `Unknown provider: ${provider}` };

  const apiKey = process.env[config.envKey];
  if (!apiKey) return { error: `Missing env var: ${config.envKey}` };

  switch (provider) {
    case 'gemini':
      return generateWithGemini(prompt, apiKey);
    case 'imagen':
      return generateWithImagen(prompt, apiKey);
    case 'flux':
      return generateWithFlux(prompt, apiKey);
    case 'replicate':
      return generateWithReplicate(prompt, apiKey);
    default:
      return { error: `Unsupported provider: ${provider}` };
  }
}

// ---------------------------------------------------------------------------
// POST — Submit a generation request
// ---------------------------------------------------------------------------

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as GenerationRequest;

    if (!body.prompt?.trim()) {
      return NextResponse.json({ error: 'prompt is required' }, { status: 400 });
    }

    if (body.prompt.length > 5000) {
      return NextResponse.json({ error: 'prompt too long (max 5000 chars)' }, { status: 400 });
    }

    const provider = selectProvider(body.provider);
    const id = `img_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const style = body.style || 'product-photo';
    const aspectRatio = body.aspectRatio || '1:1';

    // Build enhanced prompt with style context
    let enhancedPrompt = body.prompt.trim();
    if (style === 'product-photo') {
      enhancedPrompt += '. Professional product photography, clean background, studio lighting.';
    } else if (style === 'lifestyle') {
      enhancedPrompt += '. Lifestyle photography, natural setting, warm tones.';
    } else if (style === 'editorial') {
      enhancedPrompt += '. Editorial fashion photography, dramatic lighting, high contrast.';
    } else if (style === 'flat-lay') {
      enhancedPrompt += '. Flat lay arrangement, overhead view, styled accessories.';
    }

    // Create initial record
    const record: GenerationRecord = {
      id,
      prompt: body.prompt.trim(),
      provider,
      style,
      aspectRatio,
      status: 'processing',
      createdAt: new Date().toISOString(),
    };
    addRecord(record);
    totalGenerations++;

    // Generate (async but we await for the response)
    const startTime = Date.now();
    const result = await generateImage(provider, enhancedPrompt);
    const durationMs = Date.now() - startTime;

    if (result.error && !result.imageBase64 && !result.imageUrl) {
      record.status = 'failed';
      record.error = result.error;
      record.durationMs = durationMs;
    } else {
      record.status = 'completed';
      record.imageBase64 = result.imageBase64;
      record.imageUrl = result.imageUrl;
      record.completedAt = new Date().toISOString();
      record.durationMs = durationMs;
      totalSuccesses++;
      totalDurationMs += durationMs;
    }

    return NextResponse.json(record, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Internal server error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// ---------------------------------------------------------------------------
// GET — Provider statuses and generation stats
// ---------------------------------------------------------------------------

export async function GET() {
  const providers = Object.entries(PROVIDERS).map(([key, config]) => ({
    id: key,
    name: config.name,
    model: config.model,
    status: getProviderStatus(key),
    avgLatencyMs: config.avgLatencyMs,
    costPerImage: config.costPerImage,
  }));

  const connectedCount = providers.filter((p) => p.status === 'connected').length;

  const recentGenerations = Array.from(generations.values())
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 50);

  return NextResponse.json({
    providers,
    stats: {
      totalGenerations,
      successRate: totalGenerations > 0 ? Math.round((totalSuccesses / totalGenerations) * 1000) / 10 : 0,
      avgDurationMs: totalSuccesses > 0 ? Math.round(totalDurationMs / totalSuccesses) : 0,
      providersOnline: connectedCount,
      providersTotal: providers.length,
    },
    recentGenerations,
  });
}
