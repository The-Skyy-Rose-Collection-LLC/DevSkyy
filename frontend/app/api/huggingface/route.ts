/**
 * HuggingFace Hub API Proxy Route
 *
 * Proxies requests to the HuggingFace Hub API with proper authentication.
 * Falls back to simulated data gracefully when HF_TOKEN is not configured.
 *
 * GET  /api/huggingface           — Connection status, spaces, models list
 * POST /api/huggingface           — Space/endpoint actions (start, sleep, restart, pause)
 *
 * Environment:
 *   HF_TOKEN  — HuggingFace API token (optional; simulated data returned if absent)
 */

import { NextRequest, NextResponse } from 'next/server';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const HF_API_BASE = 'https://huggingface.co/api';
const VALID_ACTIONS = ['start', 'sleep', 'restart', 'pause'] as const;

type SpaceAction = (typeof VALID_ACTIONS)[number];

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface HFSpace {
  id: string;
  name: string;
  status: string;
  sdk?: string;
  likes?: number;
  url?: string;
}

interface HFModel {
  id: string;
  modelId?: string;
  likes?: number;
  downloads?: number;
  tags?: string[];
  pipeline_tag?: string;
}

interface HFActionRequestBody {
  action: SpaceAction;
  spaceId: string;
}

interface SimulatedSpace {
  id: string;
  name: string;
  status: string;
  sdk: string;
  likes: number;
  url: string;
}

interface SimulatedModel {
  id: string;
  likes: number;
  downloads: number;
  tags: string[];
  pipeline_tag: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getToken(): string | null {
  return process.env.HF_TOKEN ?? null;
}

function makeAuthHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

/**
 * Simulated spaces returned when HF_TOKEN is absent.
 * Represents realistic SkyyRose-related HuggingFace spaces.
 */
function getSimulatedSpaces(): SimulatedSpace[] {
  return [
    {
      id: 'skyyrose/fashion-classifier',
      name: 'fashion-classifier',
      status: 'RUNNING',
      sdk: 'gradio',
      likes: 12,
      url: 'https://huggingface.co/spaces/skyyrose/fashion-classifier',
    },
    {
      id: 'skyyrose/product-image-enhancer',
      name: 'product-image-enhancer',
      status: 'SLEEPING',
      sdk: 'gradio',
      likes: 7,
      url: 'https://huggingface.co/spaces/skyyrose/product-image-enhancer',
    },
    {
      id: 'skyyrose/style-recommender',
      name: 'style-recommender',
      status: 'RUNNING',
      sdk: 'streamlit',
      likes: 21,
      url: 'https://huggingface.co/spaces/skyyrose/style-recommender',
    },
  ];
}

/**
 * Simulated models returned when HF_TOKEN is absent.
 */
function getSimulatedModels(): SimulatedModel[] {
  return [
    {
      id: 'skyyrose/fashion-bert',
      likes: 34,
      downloads: 1820,
      tags: ['fashion', 'classification', 'bert'],
      pipeline_tag: 'text-classification',
    },
    {
      id: 'skyyrose/luxury-clip',
      likes: 18,
      downloads: 940,
      tags: ['fashion', 'multimodal', 'clip'],
      pipeline_tag: 'zero-shot-image-classification',
    },
  ];
}

// ---------------------------------------------------------------------------
// HuggingFace Hub API calls
// ---------------------------------------------------------------------------

async function fetchSpaces(token: string, username?: string): Promise<HFSpace[]> {
  const endpoint = username
    ? `${HF_API_BASE}/spaces?author=${encodeURIComponent(username)}&limit=50`
    : `${HF_API_BASE}/spaces?limit=20`;

  const response = await fetch(endpoint, {
    headers: makeAuthHeaders(token),
  });

  if (!response.ok) {
    throw new Error(`HuggingFace spaces API error: ${response.status} ${response.statusText}`);
  }

  const data = (await response.json()) as HFSpace[];
  return data;
}

async function fetchModels(token: string, username?: string): Promise<HFModel[]> {
  const endpoint = username
    ? `${HF_API_BASE}/models?author=${encodeURIComponent(username)}&limit=50`
    : `${HF_API_BASE}/models?limit=20`;

  const response = await fetch(endpoint, {
    headers: makeAuthHeaders(token),
  });

  if (!response.ok) {
    throw new Error(`HuggingFace models API error: ${response.status} ${response.statusText}`);
  }

  const data = (await response.json()) as HFModel[];
  return data;
}

async function fetchWhoAmI(token: string): Promise<{ name: string; fullname?: string }> {
  const response = await fetch(`${HF_API_BASE}/whoami-v2`, {
    headers: makeAuthHeaders(token),
  });

  if (!response.ok) {
    throw new Error(`HuggingFace whoami API error: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<{ name: string; fullname?: string }>;
}

async function performSpaceAction(
  token: string,
  spaceId: string,
  action: SpaceAction
): Promise<unknown> {
  // Map action to HuggingFace Hub REST endpoint
  // Docs: https://huggingface.co/docs/hub/api#post-apispacesspaceidrestart
  const actionEndpointMap: Record<SpaceAction, string> = {
    restart: `${HF_API_BASE}/spaces/${encodeURIComponent(spaceId)}/restart`,
    pause: `${HF_API_BASE}/spaces/${encodeURIComponent(spaceId)}/pause`,
    // HF Hub uses "restart" semantics for start (wakes sleeping spaces)
    start: `${HF_API_BASE}/spaces/${encodeURIComponent(spaceId)}/restart`,
    sleep: `${HF_API_BASE}/spaces/${encodeURIComponent(spaceId)}/sleep`,
  };

  const endpoint = actionEndpointMap[action];

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: makeAuthHeaders(token),
  });

  if (!response.ok) {
    throw new Error(
      `HuggingFace space action "${action}" failed: ${response.status} ${response.statusText}`
    );
  }

  // Some endpoints return 200 with JSON, others 204 with no body
  const contentType = response.headers.get('content-type') ?? '';
  if (response.status === 204 || !contentType.includes('application/json')) {
    return { acknowledged: true };
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// GET Handler
// ---------------------------------------------------------------------------

export async function GET(request: NextRequest) {
  try {
    const token = getToken();
    const { searchParams } = request.nextUrl;
    const username = searchParams.get('username') ?? undefined;

    // No token — return simulated data with a clear flag
    if (!token) {
      return NextResponse.json({
        success: true,
        connected: false,
        simulated: true,
        reason: 'HF_TOKEN not configured — showing simulated data',
        timestamp: new Date().toISOString(),
        spaces: getSimulatedSpaces(),
        models: getSimulatedModels(),
        endpoints: [],
      });
    }

    // Resolve username for scoped queries
    let resolvedUsername = username;
    if (!resolvedUsername) {
      try {
        const whoAmI = await fetchWhoAmI(token);
        resolvedUsername = whoAmI.name;
      } catch {
        // whoami failed — proceed with unscoped queries
      }
    }

    const [spaces, models] = await Promise.all([
      fetchSpaces(token, resolvedUsername),
      fetchModels(token, resolvedUsername),
    ]);

    return NextResponse.json({
      success: true,
      connected: true,
      simulated: false,
      timestamp: new Date().toISOString(),
      username: resolvedUsername ?? null,
      spaces_count: spaces.length,
      models_count: models.length,
      spaces: spaces.map((s) => ({
        id: s.id,
        name: s.name ?? s.id.split('/').pop(),
        status: s.status ?? 'UNKNOWN',
        sdk: s.sdk ?? null,
        likes: s.likes ?? 0,
        url: `https://huggingface.co/spaces/${s.id}`,
      })),
      models: models.map((m) => ({
        id: m.id ?? m.modelId,
        likes: m.likes ?? 0,
        downloads: m.downloads ?? 0,
        tags: m.tags ?? [],
        pipeline_tag: m.pipeline_tag ?? null,
        url: `https://huggingface.co/${m.id ?? m.modelId}`,
      })),
      endpoints: [],
    });
  } catch (error) {
    // Do NOT expose internal error details to the client
    console.error('[HuggingFace GET] error:', error);
    return NextResponse.json(
      {
        success: false,
        connected: false,
        error: 'Internal server error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

// ---------------------------------------------------------------------------
// POST Handler — Space actions
// ---------------------------------------------------------------------------

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as Partial<HFActionRequestBody>;
    const { action, spaceId } = body;

    // Validate action
    if (!action || !(VALID_ACTIONS as readonly string[]).includes(action)) {
      return NextResponse.json(
        {
          success: false,
          error: `Invalid action. Must be one of: ${VALID_ACTIONS.join(', ')}`,
        },
        { status: 400 }
      );
    }

    // Validate spaceId
    if (!spaceId || typeof spaceId !== 'string' || spaceId.trim().length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: 'spaceId is required and must be a non-empty string',
        },
        { status: 400 }
      );
    }

    // Sanitize spaceId — allow only owner/repo-name format (alphanumeric, hyphens, underscores, slash)
    if (!/^[\w.-]+\/[\w.-]+$/.test(spaceId.trim())) {
      return NextResponse.json(
        {
          success: false,
          error: 'spaceId must be in the format "owner/repo-name"',
        },
        { status: 400 }
      );
    }

    const token = getToken();

    // No token — return simulated success with a clear flag
    if (!token) {
      return NextResponse.json({
        success: true,
        simulated: true,
        reason: 'HF_TOKEN not configured — action simulated',
        action,
        spaceId: spaceId.trim(),
        timestamp: new Date().toISOString(),
        result: { acknowledged: true, simulated: true },
      });
    }

    const result = await performSpaceAction(token, spaceId.trim(), action as SpaceAction);

    return NextResponse.json({
      success: true,
      simulated: false,
      action,
      spaceId: spaceId.trim(),
      timestamp: new Date().toISOString(),
      result,
    });
  } catch (error) {
    // Do NOT expose internal error details to the client
    console.error('[HuggingFace POST] error:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Internal server error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}
