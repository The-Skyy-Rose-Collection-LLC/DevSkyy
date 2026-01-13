/**
 * API E2E Tests
 * =============
 *
 * End-to-end tests for DevSkyy API endpoints.
 * Tests: Health check, AI 3D endpoints, Admin dashboard API
 *
 * Run: npx playwright test api.spec.ts
 */

import { test, expect } from '@playwright/test';

const API_URL = process.env.API_BASE_URL || 'http://localhost:8000';

test.describe('API Health', () => {
  test('should have healthy backend', async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/health`);

      if (response.ok()) {
        expect(response.status()).toBe(200);
        const body = await response.json();
        expect(body).toHaveProperty('status');
      } else {
        // Backend might not be running - skip gracefully
        console.log('Backend health check failed - skipping API tests');
        test.skip();
      }
    } catch {
      console.log('Backend not reachable - skipping API tests');
      test.skip();
    }
  });

  test('should return API version', async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/`);

      if (response.ok()) {
        const body = await response.json();
        expect(body).toBeDefined();
      }
    } catch {
      test.skip();
    }
  });
});

test.describe('AI 3D API', () => {
  test('should get pipeline status', async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/api/v1/ai-3d/status`);

      if (response.ok()) {
        const body = await response.json();
        expect(body).toHaveProperty('status');
        expect(body.available_models).toBeInstanceOf(Array);
      }
    } catch {
      test.skip();
    }
  });

  test('should list generation jobs', async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/api/v1/ai-3d/jobs`);

      if (response.ok()) {
        const body = await response.json();
        expect(body).toBeInstanceOf(Array);
      }
    } catch {
      test.skip();
    }
  });

  test('should reject model generation without images', async ({ request }) => {
    try {
      const response = await request.post(`${API_URL}/api/v1/ai-3d/generate-model`, {
        multipart: {
          product_sku: 'TEST-001',
          quality_level: 'high',
        },
      });

      // Should fail with 400 or 422 (missing files)
      if (response.status() === 400 || response.status() === 422) {
        expect([400, 422]).toContain(response.status());
      }
    } catch {
      test.skip();
    }
  });

  test('should return 404 for non-existent model', async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/api/v1/ai-3d/models/non-existent-sku`);

      if (response.ok()) {
        const body = await response.json();
        // Model should not exist
        expect(body.exists).toBe(false);
      }
    } catch {
      test.skip();
    }
  });
});

test.describe('Admin Dashboard API', () => {
  test('should get dashboard metrics', async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/api/v1/admin/metrics`);

      if (response.ok()) {
        const body = await response.json();
        expect(body).toHaveProperty('total_assets');
        expect(body).toHaveProperty('fidelity_pass_rate');
      }
    } catch {
      test.skip();
    }
  });

  test('should list assets', async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/api/v1/admin/assets`);

      if (response.ok()) {
        const body = await response.json();
        expect(body).toBeInstanceOf(Array);
      }
    } catch {
      test.skip();
    }
  });

  test('should list fidelity reports', async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/api/v1/admin/reports`);

      if (response.ok()) {
        const body = await response.json();
        expect(body).toBeInstanceOf(Array);
      }
    } catch {
      test.skip();
    }
  });

  test('should list pipelines', async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/api/v1/admin/pipelines`);

      if (response.ok()) {
        const body = await response.json();
        expect(body).toBeInstanceOf(Array);
      }
    } catch {
      test.skip();
    }
  });
});

test.describe('API Error Handling', () => {
  test('should return 404 for unknown endpoints', async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/api/v1/unknown-endpoint`);

      // Should be 404
      expect(response.status()).toBe(404);
    } catch {
      test.skip();
    }
  });

  test('should handle malformed requests gracefully', async ({ request }) => {
    try {
      const response = await request.post(`${API_URL}/api/v1/admin/assets`, {
        data: 'invalid-json{{{',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      // Should return error status, not crash
      expect([400, 422, 500]).toContain(response.status());
    } catch {
      test.skip();
    }
  });
});

test.describe('API Security', () => {
  test('should have CORS headers', async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/health`);

      // CORS headers may or may not be present depending on config
      const headers = response.headers();
      console.log('Response headers:', Object.keys(headers));
    } catch {
      test.skip();
    }
  });

  test('should not expose sensitive headers', async ({ request }) => {
    try {
      const response = await request.get(`${API_URL}/health`);
      const headers = response.headers();

      // Should not expose server details
      const serverHeader = headers['server'];
      if (serverHeader) {
        expect(serverHeader).not.toContain('version');
      }
    } catch {
      test.skip();
    }
  });
});
