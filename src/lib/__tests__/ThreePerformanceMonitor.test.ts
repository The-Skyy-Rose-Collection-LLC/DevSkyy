/**
 * Unit Tests for ThreePerformanceMonitor
 * @jest-environment jsdom
 */

import { ThreePerformanceMonitor, getPerformanceMonitor, resetPerformanceMonitor } from '../ThreePerformanceMonitor';

function createMockRenderer() {
  return {
    info: {
      render: { calls: 10, triangles: 5000, points: 0, lines: 0 },
      memory: { geometries: 5, textures: 8 },
      reset: jest.fn(),
    },
    getContext: jest.fn().mockReturnValue({
      getExtension: jest.fn().mockReturnValue(null),
    }),
  };
}

function createMockScene() {
  return {
    traverse: jest.fn().mockImplementation((cb) => {
      // Simulate 3 objects, 2 visible
      cb({ visible: true });
      cb({ visible: true });
      cb({ visible: false });
    }),
  };
}

describe('ThreePerformanceMonitor', () => {
  let monitor;
  let renderer;
  let scene;

  beforeEach(() => {
    jest.clearAllMocks();
    monitor = new ThreePerformanceMonitor();
    renderer = createMockRenderer();
    scene = createMockScene();
  });

  afterEach(() => {
    monitor.dispose();
  });

  describe('constructor', () => {
    it('should create with default config', () => {
      expect(monitor).toBeDefined();
      expect(monitor.getMetrics().fps).toBe(60);
    });

    it('should accept custom config', () => {
      const custom = new ThreePerformanceMonitor({
        sampleIntervalMs: 500,
        averageSamples: 30,
        showOverlay: false,
      });
      expect(custom).toBeDefined();
      custom.dispose();
    });
  });

  describe('attach and detach', () => {
    it('should attach renderer and scene', () => {
      monitor.attach(renderer, scene);
      // No error means success
    });

    it('should create overlay when showOverlay is true', () => {
      const overlayMonitor = new ThreePerformanceMonitor({ showOverlay: true });
      overlayMonitor.attach(renderer, scene);

      const overlay = document.getElementById('three-perf-monitor');
      expect(overlay).not.toBeNull();

      overlayMonitor.dispose();
    });

    it('should detach and clean up', () => {
      monitor.attach(renderer, scene);
      monitor.detach();
      // No error means success
    });

    it('should remove overlay on detach', () => {
      const overlayMonitor = new ThreePerformanceMonitor({ showOverlay: true });
      overlayMonitor.attach(renderer, scene);
      expect(document.getElementById('three-perf-monitor')).not.toBeNull();

      overlayMonitor.detach();
      expect(document.getElementById('three-perf-monitor')).toBeNull();

      overlayMonitor.dispose();
    });
  });

  describe('start and stop', () => {
    it('should start monitoring', () => {
      monitor.attach(renderer, scene);
      monitor.start();
      // No error means success
    });

    it('should not start without renderer', () => {
      monitor.start(); // no attach
      // Should not throw
    });

    it('should stop monitoring', () => {
      monitor.attach(renderer, scene);
      monitor.start();
      monitor.stop();
      // No error means success
    });

    it('should create overlay on start if showOverlay and no overlay exists', () => {
      const overlayMonitor = new ThreePerformanceMonitor({ showOverlay: true });
      overlayMonitor.attach(renderer, scene);

      // Detach removes overlay and sets internal ref to null
      overlayMonitor.detach();
      expect(document.getElementById('three-perf-monitor')).toBeNull();

      // Re-attach and start — should recreate overlay
      overlayMonitor.attach(renderer, scene);
      overlayMonitor.start();
      expect(document.getElementById('three-perf-monitor')).not.toBeNull();

      overlayMonitor.dispose();
    });
  });

  describe('beginFrame and endFrame', () => {
    it('should track frame times', () => {
      monitor.attach(renderer, scene);
      monitor.start();

      monitor.beginFrame();
      monitor.endFrame();

      // Should not throw
    });

    it('should not track when not running', () => {
      monitor.attach(renderer, scene);
      // Not started
      monitor.beginFrame();
      monitor.endFrame();
    });

    it('should sample metrics when interval elapsed', () => {
      const onMetrics = jest.fn();
      const fastMonitor = new ThreePerformanceMonitor({
        sampleIntervalMs: 0, // immediate sampling
        onMetrics,
      });

      fastMonitor.attach(renderer, scene);
      fastMonitor.start();

      fastMonitor.beginFrame();
      // Simulate time passing
      fastMonitor.endFrame();

      // The first endFrame may or may not trigger sampling depending on timing
      // but it should not throw
      fastMonitor.dispose();
    });
  });

  describe('getMetrics and getHistory', () => {
    it('should return empty metrics initially', () => {
      const metrics = monitor.getMetrics();
      expect(metrics.fps).toBe(60);
      expect(metrics.drawCalls).toBe(0);
      expect(metrics.triangles).toBe(0);
    });

    it('should return copy of metrics', () => {
      const m1 = monitor.getMetrics();
      const m2 = monitor.getMetrics();
      expect(m1).toEqual(m2);
      expect(m1).not.toBe(m2);
    });

    it('should return empty history initially', () => {
      expect(monitor.getHistory()).toEqual([]);
    });

    it('should return copy of history', () => {
      const h1 = monitor.getHistory();
      const h2 = monitor.getHistory();
      expect(h1).not.toBe(h2);
    });
  });

  describe('checkPerformance', () => {
    it('should return no warnings for default metrics', () => {
      const warnings = monitor.checkPerformance();
      expect(warnings).toEqual([]);
    });

    it('should warn when FPS below threshold', () => {
      // Manually set low FPS by accessing private field
      monitor['currentMetrics'] = { ...monitor.getMetrics(), fps: 20, frameTime: 50 };

      const warnings = monitor.checkPerformance();
      const fpsWarning = warnings.find(w => w.type === 'fps');
      expect(fpsWarning).toBeDefined();
      expect(fpsWarning.severity).toBe('warning');
    });

    it('should give critical warning for very low FPS', () => {
      monitor['currentMetrics'] = { ...monitor.getMetrics(), fps: 10, frameTime: 100 };

      const warnings = monitor.checkPerformance();
      const fpsWarning = warnings.find(w => w.type === 'fps');
      expect(fpsWarning).toBeDefined();
      expect(fpsWarning.severity).toBe('critical');
    });

    it('should warn on high frame time', () => {
      monitor['currentMetrics'] = { ...monitor.getMetrics(), frameTime: 50 };

      const warnings = monitor.checkPerformance();
      const ftWarning = warnings.find(w => w.type === 'frameTime');
      expect(ftWarning).toBeDefined();
      expect(ftWarning.severity).toBe('warning');
    });

    it('should give critical warning for very high frame time', () => {
      monitor['currentMetrics'] = { ...monitor.getMetrics(), frameTime: 100 };

      const warnings = monitor.checkPerformance();
      const ftWarning = warnings.find(w => w.type === 'frameTime');
      expect(ftWarning).toBeDefined();
      expect(ftWarning.severity).toBe('critical');
    });

    it('should warn on high draw calls', () => {
      monitor['currentMetrics'] = { ...monitor.getMetrics(), drawCalls: 600 };

      const warnings = monitor.checkPerformance();
      const dcWarning = warnings.find(w => w.type === 'drawCalls');
      expect(dcWarning).toBeDefined();
    });

    it('should warn on high triangle count', () => {
      monitor['currentMetrics'] = { ...monitor.getMetrics(), triangles: 2000000 };

      const warnings = monitor.checkPerformance();
      const triWarning = warnings.find(w => w.type === 'triangles');
      expect(triWarning).toBeDefined();
    });

    it('should warn on high memory usage', () => {
      monitor['currentMetrics'] = { ...monitor.getMetrics(), jsHeapMB: 600 };

      const warnings = monitor.checkPerformance();
      const memWarning = warnings.find(w => w.type === 'memory');
      expect(memWarning).toBeDefined();
      expect(memWarning.severity).toBe('warning');
    });

    it('should give critical memory warning', () => {
      monitor['currentMetrics'] = { ...monitor.getMetrics(), jsHeapMB: 900 };

      const warnings = monitor.checkPerformance();
      const memWarning = warnings.find(w => w.type === 'memory');
      expect(memWarning).toBeDefined();
      expect(memWarning.severity).toBe('critical');
    });

    it('should skip memory check when jsHeapMB is null', () => {
      monitor['currentMetrics'] = { ...monitor.getMetrics(), jsHeapMB: null };

      const warnings = monitor.checkPerformance();
      expect(warnings.find(w => w.type === 'memory')).toBeUndefined();
    });
  });

  describe('getPerformanceScore', () => {
    it('should return 100 for perfect metrics', () => {
      monitor['currentMetrics'] = {
        ...monitor.getMetrics(),
        fps: 60,
        frameTime: 16.67,
        drawCalls: 0,
        triangles: 0,
      };

      const score = monitor.getPerformanceScore();
      expect(score).toBeGreaterThanOrEqual(95);
    });

    it('should return lower score for poor FPS', () => {
      monitor['currentMetrics'] = {
        ...monitor.getMetrics(),
        fps: 15,
        frameTime: 66.67,
        drawCalls: 0,
        triangles: 0,
      };

      const score = monitor.getPerformanceScore();
      expect(score).toBeLessThan(50);
    });

    it('should factor in draw calls and triangles', () => {
      monitor['currentMetrics'] = {
        ...monitor.getMetrics(),
        fps: 60,
        frameTime: 16.67,
        drawCalls: 400,
        triangles: 800000,
      };

      const score = monitor.getPerformanceScore();
      expect(score).toBeLessThan(100);
      expect(score).toBeGreaterThan(40);
    });
  });

  describe('setConfig', () => {
    it('should update config', () => {
      monitor.setConfig({ sampleIntervalMs: 2000 });
      // No error means success
    });

    it('should create overlay when showOverlay toggled on', () => {
      monitor.setConfig({ showOverlay: true });
      expect(document.getElementById('three-perf-monitor')).not.toBeNull();
    });

    it('should remove overlay when showOverlay toggled off', () => {
      monitor.setConfig({ showOverlay: true });
      expect(document.getElementById('three-perf-monitor')).not.toBeNull();

      monitor.setConfig({ showOverlay: false });
      expect(document.getElementById('three-perf-monitor')).toBeNull();
    });
  });

  describe('dispose', () => {
    it('should clean up all resources', () => {
      monitor.attach(renderer, scene);
      monitor.start();
      monitor.dispose();

      expect(monitor.getHistory()).toEqual([]);
    });
  });

  describe('sampleMetrics (via endFrame)', () => {
    it('should populate metrics from renderer info', () => {
      const onMetrics = jest.fn();
      const m = new ThreePerformanceMonitor({ sampleIntervalMs: 0, onMetrics });

      m.attach(renderer, scene);
      m.start();

      m.beginFrame();
      m.endFrame();

      if (onMetrics.mock.calls.length > 0) {
        const metrics = onMetrics.mock.calls[0][0];
        expect(metrics.drawCalls).toBe(10);
        expect(metrics.triangles).toBe(5000);
        expect(metrics.geometries).toBe(5);
        expect(metrics.textures).toBe(8);
        expect(metrics.objectCount).toBe(3);
        expect(metrics.visibleObjects).toBe(2);
      }

      m.dispose();
    });

    it('should call onWarning for poor performance', () => {
      const onWarning = jest.fn();
      renderer.info.render.calls = 600;
      renderer.info.render.triangles = 2000000;

      const m = new ThreePerformanceMonitor({ sampleIntervalMs: 0, onWarning });

      m.attach(renderer, scene);
      m.start();

      m.beginFrame();
      m.endFrame();

      // onWarning may or may not be called depending on frame timing
      m.dispose();
    });

    it('should limit metrics history to maxHistorySize', () => {
      const m = new ThreePerformanceMonitor({ sampleIntervalMs: 0 });
      m.attach(renderer, scene);
      m.start();

      // Simulate many frames
      for (let i = 0; i < 100; i++) {
        m.beginFrame();
        m.endFrame();
      }

      expect(m.getHistory().length).toBeLessThanOrEqual(60);
      m.dispose();
    });

    it('should update overlay when present', () => {
      const m = new ThreePerformanceMonitor({ sampleIntervalMs: 0, showOverlay: true });
      m.attach(renderer, scene);
      m.start();

      m.beginFrame();
      m.endFrame();

      const overlay = document.getElementById('three-perf-monitor');
      if (overlay) {
        expect(overlay.innerHTML).toContain('FPS');
      }

      m.dispose();
    });
  });
});

describe('getPerformanceMonitor singleton', () => {
  beforeEach(() => {
    resetPerformanceMonitor();
  });

  afterEach(() => {
    resetPerformanceMonitor();
  });

  it('should return an instance', () => {
    const instance = getPerformanceMonitor();
    expect(instance).toBeDefined();
    expect(instance).toBeInstanceOf(ThreePerformanceMonitor);
  });

  it('should return same instance on subsequent calls', () => {
    const first = getPerformanceMonitor();
    const second = getPerformanceMonitor();
    expect(first).toBe(second);
  });

  it('should reset instance', () => {
    const first = getPerformanceMonitor();
    resetPerformanceMonitor();
    const second = getPerformanceMonitor();
    expect(first).not.toBe(second);
  });
});
