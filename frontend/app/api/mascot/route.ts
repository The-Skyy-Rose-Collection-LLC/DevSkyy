/**
 * Brand Mascot API Route
 *
 * Manages mascot avatar generation jobs using the imagery pipeline
 * (Gemini, Imagen, HuggingFace Flux) with character consistency.
 *
 * GET  /api/mascot  — List generated mascot images and job status
 * POST /api/mascot  — Submit a new mascot generation job
 *
 * Environment:
 *   GEMINI_API_KEY     — Google Gemini API key (optional)
 *   HF_TOKEN           — HuggingFace API token (optional)
 */

import { NextRequest, NextResponse } from 'next/server';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type MascotPose = 'standing' | 'walking' | 'presenting' | 'waving' | 'sitting' | 'confident';
type MascotCollection = 'black-rose' | 'love-hurts' | 'signature' | 'kids-capsule' | 'none';
type MascotProduct = string;
type GenerationStatus = 'queued' | 'processing' | 'completed' | 'failed';

interface MascotJob {
  id: string;
  pose: MascotPose;
  collection: MascotCollection;
  product: MascotProduct;
  prompt: string;
  status: GenerationStatus;
  imageUrl: string | null;
  createdAt: string;
  completedAt: string | null;
  error: string | null;
}

interface MascotGenerateRequest {
  pose: MascotPose;
  collection: MascotCollection;
  product: MascotProduct;
  customPrompt?: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MASCOT_BASE_PROMPT =
  'Pixar/Disney-quality 3D animated young Black girl with voluminous curly/afro dark brown hair, ' +
  'big expressive brown eyes, warm brown skin, friendly confident smile. ' +
  'Character must be 100% identical to reference image in face, hair, skin tone, art style, and proportions.';

const POSE_PROMPTS: Record<MascotPose, string> = {
  standing: 'Full body, standing confidently with hands on hips, studio lighting',
  walking: 'Full body, mid-stride walking with a playful bounce, urban backdrop',
  presenting: 'Full body, one arm extended presenting a product, warm spotlight',
  waving: 'Full body, cheerful wave with one hand, bright clean background',
  sitting: 'Full body, sitting on a luxury rose gold stool, relaxed pose',
  confident: 'Full body, arms crossed with a confident knowing smile, dramatic lighting',
};

const COLLECTION_STYLE: Record<MascotCollection, string> = {
  'black-rose': 'wearing Black Rose collection piece, dark floral gothic luxury aesthetic, deep reds and blacks',
  'love-hurts': 'wearing Love Hurts collection piece, romantic rebel aesthetic, crimson and midnight tones',
  'signature': 'wearing Signature collection piece, rose gold luxury, golden hour warm tones',
  'kids-capsule': 'wearing Kids Capsule mini version, playful bright colors, child-friendly energy',
  none: 'casual luxury streetwear, SkyyRose brand colors rose gold #B76E79',
};

const PRODUCT_CATALOG: Record<string, string[]> = {
  'black-rose': [
    'Thorn Crewneck', 'Midnight Hoodie', 'Shadow Joggers', 'Iron Rose Jacket',
    'Dark Petal Tee', 'Obsidian Cap',
  ],
  'love-hurts': [
    'Bleeding Heart Tee', 'Crimson Hoodie', 'Heartbreak Joggers',
    'Velvet Thorns Jacket', 'Rose Wound Cap',
  ],
  'signature': [
    'Rose Gold Crewneck', 'Golden Hour Hoodie', 'Sunset Joggers',
    'Prestige Bomber', 'Crown Cap',
  ],
  'kids-capsule': [
    'Mini Rose Tee', 'Little Luxe Hoodie', 'Tiny Thorns Joggers',
    'Petal Play Dress', 'Junior Crown Cap',
  ],
};

// ---------------------------------------------------------------------------
// In-memory job store (production would use a database)
// ---------------------------------------------------------------------------

const MAX_JOBS = 200;
const jobs: MascotJob[] = [];

function addJob(job: MascotJob): void {
  jobs.unshift(job);
  if (jobs.length > MAX_JOBS) {
    jobs.pop();
  }
}

// ---------------------------------------------------------------------------
// Simulated initial data
// ---------------------------------------------------------------------------

const SIMULATED_JOBS: MascotJob[] = [
  {
    id: 'mascot-001',
    pose: 'presenting',
    collection: 'none',
    product: '',
    prompt: `${MASCOT_BASE_PROMPT} ${POSE_PROMPTS.presenting} ${COLLECTION_STYLE.none}`,
    status: 'completed',
    imageUrl: '/assets/branding/mascot/skyyrose-mascot-reference.png',
    createdAt: '2026-02-24T10:00:00Z',
    completedAt: '2026-02-24T10:02:30Z',
    error: null,
  },
  {
    id: 'mascot-002',
    pose: 'standing',
    collection: 'black-rose',
    product: 'Thorn Crewneck',
    prompt: `${MASCOT_BASE_PROMPT} ${POSE_PROMPTS.standing} ${COLLECTION_STYLE['black-rose']}, wearing the Thorn Crewneck`,
    status: 'completed',
    imageUrl: null,
    createdAt: '2026-02-24T10:05:00Z',
    completedAt: '2026-02-24T10:07:45Z',
    error: null,
  },
  {
    id: 'mascot-003',
    pose: 'waving',
    collection: 'kids-capsule',
    product: 'Mini Rose Tee',
    prompt: `${MASCOT_BASE_PROMPT} ${POSE_PROMPTS.waving} ${COLLECTION_STYLE['kids-capsule']}, wearing the Mini Rose Tee`,
    status: 'completed',
    imageUrl: null,
    createdAt: '2026-02-24T10:10:00Z',
    completedAt: '2026-02-24T10:12:15Z',
    error: null,
  },
  {
    id: 'mascot-004',
    pose: 'confident',
    collection: 'signature',
    product: 'Rose Gold Crewneck',
    prompt: `${MASCOT_BASE_PROMPT} ${POSE_PROMPTS.confident} ${COLLECTION_STYLE.signature}, wearing the Rose Gold Crewneck`,
    status: 'processing',
    imageUrl: null,
    createdAt: '2026-02-24T10:15:00Z',
    completedAt: null,
    error: null,
  },
];

// Initialize with simulated data
SIMULATED_JOBS.forEach((j) => jobs.push(j));

// ---------------------------------------------------------------------------
// Route Handlers
// ---------------------------------------------------------------------------

export async function GET(): Promise<NextResponse> {
  const stats = {
    totalGenerated: jobs.filter((j) => j.status === 'completed').length,
    processing: jobs.filter((j) => j.status === 'processing').length,
    queued: jobs.filter((j) => j.status === 'queued').length,
    failed: jobs.filter((j) => j.status === 'failed').length,
    collectionsWithMascot: new Set(
      jobs.filter((j) => j.status === 'completed' && j.collection !== 'none').map((j) => j.collection)
    ).size,
    posesGenerated: new Set(
      jobs.filter((j) => j.status === 'completed').map((j) => j.pose)
    ).size,
  };

  return NextResponse.json({
    success: true,
    data: {
      jobs,
      stats,
      productCatalog: PRODUCT_CATALOG,
    },
  });
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = (await request.json()) as MascotGenerateRequest;

    const { pose, collection, product, customPrompt } = body;

    if (!pose || !POSE_PROMPTS[pose]) {
      return NextResponse.json(
        { success: false, error: 'Invalid pose. Must be one of: standing, walking, presenting, waving, sitting, confident' },
        { status: 400 }
      );
    }

    if (!collection || !COLLECTION_STYLE[collection]) {
      return NextResponse.json(
        { success: false, error: 'Invalid collection. Must be one of: black-rose, love-hurts, signature, kids-capsule, none' },
        { status: 400 }
      );
    }

    // Build the generation prompt
    const productClause = product ? `, wearing the ${product}` : '';
    const prompt = customPrompt
      ? `${MASCOT_BASE_PROMPT} ${customPrompt}`
      : `${MASCOT_BASE_PROMPT} ${POSE_PROMPTS[pose]} ${COLLECTION_STYLE[collection]}${productClause}`;

    const job: MascotJob = {
      id: `mascot-${Date.now()}`,
      pose,
      collection,
      product: product || '',
      prompt,
      status: 'queued',
      imageUrl: null,
      createdAt: new Date().toISOString(),
      completedAt: null,
      error: null,
    };

    addJob(job);

    // Simulate async processing (in production, this would dispatch to the imagery pipeline)
    setTimeout(() => {
      const idx = jobs.findIndex((j) => j.id === job.id);
      if (idx !== -1) {
        jobs[idx] = { ...jobs[idx], status: 'processing' };
      }
    }, 1_000);

    setTimeout(() => {
      const idx = jobs.findIndex((j) => j.id === job.id);
      if (idx !== -1) {
        jobs[idx] = {
          ...jobs[idx],
          status: 'completed',
          completedAt: new Date().toISOString(),
        };
      }
    }, 5_000);

    return NextResponse.json({
      success: true,
      data: { job },
    });
  } catch {
    return NextResponse.json(
      { success: false, error: 'Invalid request body' },
      { status: 400 }
    );
  }
}
