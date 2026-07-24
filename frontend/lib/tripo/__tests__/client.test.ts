import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { extractBearerToken } from '@/lib/api/client';
import { API_URL } from '@/lib/api/config';
import { ApiError } from '@/lib/api/errors';
import type { ThreeDGenerationResponse } from '@/lib/api/types';

import {
  productNameFromImageUrl,
  productNameFromPrompt,
  toJob3D,
  tripoClient,
} from '../client';

function mockResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function validGenerationResponse(
  overrides: Partial<ThreeDGenerationResponse> = {}
): ThreeDGenerationResponse {
  return {
    generation_id: 'gen-123',
    status: 'processing',
    timestamp: '2026-07-22T00:00:00.000Z',
    product_name: 'Black Rose Bomber',
    output_format: 'glb',
    model_url: null,
    preview_url: null,
    download_url: null,
    metadata: null,
    estimated_completion_time: '2-5 minutes',
    ...overrides,
  };
}

describe('extractBearerToken', () => {
  it('extracts the token from a well-formed Bearer header', () => {
    const headers = new Headers({ authorization: 'Bearer abc.def.ghi' });
    expect(extractBearerToken(headers)).toBe('abc.def.ghi');
  });

  it('is case-insensitive on the Bearer scheme', () => {
    const headers = new Headers({ authorization: 'bearer abc.def.ghi' });
    expect(extractBearerToken(headers)).toBe('abc.def.ghi');
  });

  it('returns null when the Authorization header is absent', () => {
    expect(extractBearerToken(new Headers())).toBeNull();
  });

  it('returns the raw header value when it has no Bearer prefix', () => {
    const headers = new Headers({ authorization: 'abc.def.ghi' });
    expect(extractBearerToken(headers)).toBe('abc.def.ghi');
  });
});

describe('productNameFromPrompt', () => {
  it('returns a short prompt unchanged (after trimming)', () => {
    expect(productNameFromPrompt('  Black Rose Bomber  ')).toBe('Black Rose Bomber');
  });

  it('truncates prompts over 200 chars to a 200-char product_name', () => {
    const long = 'a'.repeat(250);
    const result = productNameFromPrompt(long);
    expect(result).toHaveLength(200);
    expect(result.endsWith('...')).toBe(true);
  });
});

describe('productNameFromImageUrl', () => {
  it('derives a readable name from the URL filename', () => {
    expect(
      productNameFromImageUrl('https://cdn.example.com/products/br-011-satin-bomber.jpg')
    ).toBe('br 011 satin bomber');
  });

  it('falls back to a generic label for data URIs', () => {
    expect(productNameFromImageUrl('data:image/png;base64,AAAA')).toBe('Uploaded Image');
  });

  it('falls back to a generic label for malformed URLs', () => {
    expect(productNameFromImageUrl('not-a-url')).toBe('Uploaded Image');
  });
});

describe('tripoClient.isDryRun', () => {
  it('is true when no auth token is supplied', () => {
    expect(tripoClient.isDryRun(null)).toBe(true);
    expect(tripoClient.isDryRun(undefined)).toBe(true);
    expect(tripoClient.isDryRun('')).toBe(true);
  });

  it('is false when an auth token is supplied', () => {
    expect(tripoClient.isDryRun('jwt-token')).toBe(false);
  });
});

describe('tripoClient — dry-run path', () => {
  it('textTo3D returns mock data without calling fetch', async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);

    const result = await tripoClient.textTo3D(
      { product_name: 'Black Rose Bomber' },
      null
    );

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(result.status).toBe('processing');
    expect(result.product_name).toBe('Black Rose Bomber');
    expect(result.output_format).toBe('glb');

    vi.unstubAllGlobals();
  });

  it('imageTo3D returns mock data without calling fetch', async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);

    const result = await tripoClient.imageTo3D(
      { product_name: 'Black Rose Bomber', image_url: 'https://x.test/a.jpg' },
      undefined
    );

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(result.status).toBe('processing');

    vi.unstubAllGlobals();
  });

  it('getGenerationStatus returns a completed mock without calling fetch', async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);

    const result = await tripoClient.getGenerationStatus('gen-123', null);

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(result.generation_id).toBe('gen-123');
    expect(result.status).toBe('completed');
    expect(result.model_url).toBeTruthy();

    vi.unstubAllGlobals();
  });
});

describe('tripoClient — real backend path', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('textTo3D POSTs to /api/v1/media/3d/generate/text with a bearer token', async () => {
    const backendResponse = validGenerationResponse();
    vi.mocked(fetch).mockResolvedValueOnce(mockResponse(backendResponse, 202));

    const result = await tripoClient.textTo3D(
      {
        product_name: 'Black Rose Bomber',
        additional_details: 'oversized fit, satin lining',
      },
      'jwt-token'
    );

    expect(fetch).toHaveBeenCalledTimes(1);
    const [url, options] = vi.mocked(fetch).mock.calls[0];
    expect(url).toBe(`${API_URL}/api/v1/media/3d/generate/text`);
    expect(options?.method).toBe('POST');
    expect((options?.headers as Record<string, string>).Authorization).toBe(
      'Bearer jwt-token'
    );
    expect(JSON.parse(options?.body as string)).toEqual({
      product_name: 'Black Rose Bomber',
      additional_details: 'oversized fit, satin lining',
    });
    expect(result).toEqual(backendResponse);
  });

  it('imageTo3D POSTs to /api/v1/media/3d/generate/image', async () => {
    const backendResponse = validGenerationResponse({ product_name: 'br-011' });
    vi.mocked(fetch).mockResolvedValueOnce(mockResponse(backendResponse, 202));

    const result = await tripoClient.imageTo3D(
      { product_name: 'br-011', image_url: 'https://cdn.example.com/br-011.jpg' },
      'jwt-token'
    );

    const [url, options] = vi.mocked(fetch).mock.calls[0];
    expect(url).toBe(`${API_URL}/api/v1/media/3d/generate/image`);
    expect(JSON.parse(options?.body as string)).toEqual({
      product_name: 'br-011',
      image_url: 'https://cdn.example.com/br-011.jpg',
    });
    expect(result).toEqual(backendResponse);
  });

  it('getGenerationStatus GETs /api/v1/media/3d/{id}/status', async () => {
    const backendResponse = validGenerationResponse({ status: 'completed' });
    vi.mocked(fetch).mockResolvedValueOnce(mockResponse(backendResponse, 200));

    const result = await tripoClient.getGenerationStatus('gen-123', 'jwt-token');

    const [url, options] = vi.mocked(fetch).mock.calls[0];
    expect(url).toBe(`${API_URL}/api/v1/media/3d/gen-123/status`);
    expect(options?.method).toBe('GET');
    expect(result.status).toBe('completed');
  });

  it('throws when the backend returns a non-2xx response', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      mockResponse({ detail: 'Not authenticated' }, 401)
    );

    await expect(
      tripoClient.textTo3D({ product_name: 'x' }, 'jwt-token')
    ).rejects.toThrow('Not authenticated');
  });

  it('throws when the backend response fails schema validation', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      mockResponse({ status: 'processing' }, 202) // missing generation_id, etc.
    );

    await expect(
      tripoClient.textTo3D({ product_name: 'x' }, 'jwt-token')
    ).rejects.toThrow(ApiError);
  });

  it('falls back to the mock path instead of calling fetch when the token is an empty string', async () => {
    const result = await tripoClient.textTo3D({ product_name: 'x' }, '');

    expect(fetch).not.toHaveBeenCalled();
    expect(result.status).toBe('processing');
  });
});

describe('toJob3D', () => {
  it('maps a processing generation to a processing Job3D', () => {
    const job = toJob3D(validGenerationResponse(), 'text', 'a bomber jacket');

    expect(job).toEqual({
      id: 'gen-123',
      status: 'processing',
      provider: 'tripo',
      input_type: 'text',
      input: 'a bomber jacket',
      output_url: undefined,
      error: undefined,
      created_at: '2026-07-22T00:00:00.000Z',
      completed_at: undefined,
    });
  });

  it('maps a completed generation, surfacing model_url and completed_at', () => {
    const response = validGenerationResponse({
      status: 'completed',
      model_url: 'https://cdn.example.com/model.glb',
    });

    const job = toJob3D(response, 'image', 'https://cdn.example.com/br-011.jpg');

    expect(job.status).toBe('completed');
    expect(job.output_url).toBe('https://cdn.example.com/model.glb');
    expect(job.completed_at).toBe(response.timestamp);
  });

  it('maps a failed generation to a failed Job3D with an error message', () => {
    const response = validGenerationResponse({ status: 'failed' });

    const job = toJob3D(response, 'text', 'prompt');

    expect(job.status).toBe('failed');
    expect(job.error).toBe('Generation failed');
    expect(job.completed_at).toBe(response.timestamp);
  });

  it('defaults an unrecognized status to queued', () => {
    const response = validGenerationResponse({ status: 'weird-future-status' });

    const job = toJob3D(response, 'text', 'prompt');

    expect(job.status).toBe('queued');
    expect(job.completed_at).toBeUndefined();
  });
});
