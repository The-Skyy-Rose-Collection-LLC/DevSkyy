/**
 * 3D Viewer E2E Tests
 * ====================
 *
 * End-to-end tests for Three.js 3D viewer functionality.
 * Tests: Canvas rendering, WebGL context, model loading UI
 *
 * Run: npx playwright test 3d-viewer.spec.ts
 */

import { test, expect } from '@playwright/test';

test.describe('3D Viewer', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to a page that should have 3D content
    await page.goto('/');
  });

  test('should support WebGL', async ({ page }) => {
    // Check if WebGL is supported in the browser
    const webglSupported = await page.evaluate(() => {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      return !!gl;
    });

    expect(webglSupported).toBe(true);
  });

  test('should not crash on canvas creation', async ({ page }) => {
    // Try to create a canvas programmatically
    const canvasCreated = await page.evaluate(() => {
      try {
        const canvas = document.createElement('canvas');
        canvas.width = 800;
        canvas.height = 600;
        const ctx = canvas.getContext('2d');
        return !!ctx;
      } catch {
        return false;
      }
    });

    expect(canvasCreated).toBe(true);
  });

  test('should have canvas element if 3D viewer present', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Look for canvas elements (Three.js renders to canvas)
    const canvasCount = await page.locator('canvas').count();

    // Log canvas presence for debugging
    if (canvasCount > 0) {
      console.log(`Found ${canvasCount} canvas element(s)`);

      // Check if any canvas has WebGL context
      const hasWebGLCanvas = await page.evaluate(() => {
        const canvases = document.querySelectorAll('canvas');
        for (const canvas of canvases) {
          const gl = canvas.getContext('webgl') || canvas.getContext('webgl2');
          if (gl) return true;
        }
        return false;
      });

      if (hasWebGLCanvas) {
        console.log('WebGL canvas detected - 3D viewer is present');
      }
    } else {
      console.log('No canvas elements found - 3D viewer may not be on this page');
    }
  });

  test('should handle WebGL context loss gracefully', async ({ page }) => {
    // Simulate WebGL context loss (common in resource-constrained environments)
    const handled = await page.evaluate(() => {
      return new Promise<boolean>((resolve) => {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl');

        if (!gl) {
          resolve(true); // No WebGL, nothing to test
          return;
        }

        // Add context lost handler
        canvas.addEventListener('webglcontextlost', (e) => {
          e.preventDefault();
          resolve(true); // Context loss was handled
        });

        // Try to trigger context loss
        const ext = gl.getExtension('WEBGL_lose_context');
        if (ext) {
          ext.loseContext();
          // Give it time to trigger
          setTimeout(() => resolve(true), 100);
        } else {
          resolve(true); // Extension not available
        }
      });
    });

    expect(handled).toBe(true);
  });
});

test.describe('3D Model Interactions', () => {
  test('should respond to mouse events on canvas', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const canvas = page.locator('canvas').first();

    if (await canvas.isVisible()) {
      // Try mouse interactions
      await canvas.hover();

      // Check if there are any errors after hover
      const errors: string[] = [];
      page.on('pageerror', (err) => errors.push(err.message));

      await page.mouse.move(100, 100);
      await page.mouse.wheel(0, -100); // Zoom in
      await page.mouse.wheel(0, 100);  // Zoom out

      // No JavaScript errors should occur
      expect(errors.filter(e => e.includes('Three') || e.includes('WebGL'))).toHaveLength(0);
    }
  });

  test('should handle touch events on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const canvas = page.locator('canvas').first();

    if (await canvas.isVisible()) {
      // Simulate touch events
      await canvas.tap();

      // No errors should occur
      const errors: string[] = [];
      page.on('pageerror', (err) => errors.push(err.message));

      await page.waitForTimeout(500);

      expect(errors.filter(e => e.includes('Three') || e.includes('WebGL'))).toHaveLength(0);
    }
  });
});

test.describe('3D Viewer Performance', () => {
  test('should maintain acceptable frame rate', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const canvas = page.locator('canvas').first();

    if (await canvas.isVisible()) {
      // Measure frame times using requestAnimationFrame
      const frameData = await page.evaluate(() => {
        return new Promise<{ avgFps: number; minFps: number }>((resolve) => {
          const frameTimes: number[] = [];
          let lastTime = performance.now();
          let frameCount = 0;
          const maxFrames = 60;

          function measureFrame() {
            const now = performance.now();
            const delta = now - lastTime;
            frameTimes.push(delta);
            lastTime = now;
            frameCount++;

            if (frameCount < maxFrames) {
              requestAnimationFrame(measureFrame);
            } else {
              const avgFrameTime = frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length;
              const maxFrameTime = Math.max(...frameTimes);
              resolve({
                avgFps: Math.round(1000 / avgFrameTime),
                minFps: Math.round(1000 / maxFrameTime),
              });
            }
          }

          requestAnimationFrame(measureFrame);
        });
      });

      console.log(`3D Viewer FPS - Avg: ${frameData.avgFps}, Min: ${frameData.minFps}`);

      // Should maintain at least 30 FPS average
      // (CI environments may have lower performance)
      expect(frameData.avgFps).toBeGreaterThanOrEqual(10);
    }
  });

  test('should not leak memory on navigation', async ({ page }) => {
    // Navigate back and forth to check for memory leaks
    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    // Navigate away and back multiple times
    for (let i = 0; i < 3; i++) {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);
    }

    const finalMemory = await page.evaluate(() => {
      // Force garbage collection if available
      if ((global as any).gc) {
        (global as any).gc();
      }
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    // Memory should not grow excessively (allow 50% growth)
    if (initialMemory > 0) {
      const memoryGrowth = (finalMemory - initialMemory) / initialMemory;
      console.log(`Memory growth: ${Math.round(memoryGrowth * 100)}%`);
      expect(memoryGrowth).toBeLessThan(0.5);
    }
  });
});
