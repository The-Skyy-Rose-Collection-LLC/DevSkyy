/**
 * Three.js Performance Monitor
 * =============================
 * Real-time monitoring of 3D scene performance including FPS, memory, and draw calls.
 *
 * @module lib/ThreePerformanceMonitor
 */

import type * as THREE from 'three';

// ============================================================================
// TYPES
// ============================================================================

export interface PerformanceMetrics {
  /** Frames per second */
  fps: number;
  /** Frame time in milliseconds */
  frameTime: number;
  /** WebGL draw calls per frame */
  drawCalls: number;
  /** Total triangles rendered */
  triangles: number;
  /** Total points rendered */
  points: number;
  /** Total lines rendered */
  lines: number;
  /** Number of active geometries */
  geometries: number;
  /** Number of active textures */
  textures: number;
  /** GPU memory usage (if available) */
  gpuMemoryMB: number | null;
  /** JS heap size in MB */
  jsHeapMB: number | null;
  /** Scene object count */
  objectCount: number;
  /** Visible object count */
  visibleObjects: number;
  /** Timestamp of measurement */
  timestamp: number;
}

export interface PerformanceThresholds {
  /** Minimum acceptable FPS */
  minFPS: number;
  /** Maximum acceptable frame time in ms */
  maxFrameTime: number;
  /** Maximum draw calls per frame */
  maxDrawCalls: number;
  /** Maximum triangles per frame */
  maxTriangles: number;
  /** Maximum memory usage in MB */
  maxMemoryMB: number;
}

export interface PerformanceWarning {
  type: 'fps' | 'frameTime' | 'drawCalls' | 'triangles' | 'memory';
  message: string;
  value: number;
  threshold: number;
  severity: 'warning' | 'critical';
  timestamp: number;
}

export interface MonitorConfig {
  /** Enable monitoring */
  enabled: boolean;
  /** Sampling interval in ms */
  sampleIntervalMs: number;
  /** Number of samples to average */
  averageSamples: number;
  /** Show overlay UI */
  showOverlay: boolean;
  /** Performance thresholds */
  thresholds: PerformanceThresholds;
  /** Callback when warning occurs */
  onWarning?: (warning: PerformanceWarning) => void;
  /** Callback with metrics update */
  onMetrics?: (metrics: PerformanceMetrics) => void;
}

// ============================================================================
// DEFAULT CONFIGURATION
// ============================================================================

const DEFAULT_THRESHOLDS: PerformanceThresholds = {
  minFPS: 30,
  maxFrameTime: 33.33, // ~30fps
  maxDrawCalls: 500,
  maxTriangles: 1000000,
  maxMemoryMB: 512,
};

const DEFAULT_CONFIG: MonitorConfig = {
  enabled: true,
  sampleIntervalMs: 1000,
  averageSamples: 60,
  showOverlay: false,
  thresholds: DEFAULT_THRESHOLDS,
};

// ============================================================================
// PERFORMANCE MONITOR
// ============================================================================

export class ThreePerformanceMonitor {
  private config: MonitorConfig;
  private renderer: THREE.WebGLRenderer | null = null;
  private scene: THREE.Scene | null = null;

  // Timing
  private lastTime = 0;
  private frameTimes: number[] = [];
  private frameCount = 0;
  private lastSampleTime = 0;

  // Metrics storage
  private currentMetrics: PerformanceMetrics;
  private metricsHistory: PerformanceMetrics[] = [];
  private maxHistorySize = 60;

  // Overlay
  private overlay: HTMLDivElement | null = null;

  // State
  private isRunning = false;
  private animationFrameId: number | null = null;

  constructor(config: Partial<MonitorConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.currentMetrics = this.createEmptyMetrics();
  }

  // ============================================================================
  // PUBLIC METHODS
  // ============================================================================

  /**
   * Attach monitor to renderer and scene
   */
  attach(renderer: THREE.WebGLRenderer, scene: THREE.Scene): void {
    this.renderer = renderer;
    this.scene = scene;

    if (this.config.showOverlay) {
      this.createOverlay();
    }
  }

  /**
   * Detach monitor from current renderer/scene
   */
  detach(): void {
    this.stop();
    this.renderer = null;
    this.scene = null;
    this.removeOverlay();
  }

  /**
   * Start monitoring
   */
  start(): void {
    if (this.isRunning || !this.renderer) return;

    this.isRunning = true;
    this.lastTime = performance.now();
    this.lastSampleTime = this.lastTime;
    this.frameTimes = [];
    this.frameCount = 0;

    if (this.config.showOverlay && !this.overlay) {
      this.createOverlay();
    }
  }

  /**
   * Stop monitoring
   */
  stop(): void {
    this.isRunning = false;
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  /**
   * Call this at the start of each frame
   */
  beginFrame(): void {
    if (!this.isRunning) return;
    this.lastTime = performance.now();
  }

  /**
   * Call this at the end of each frame
   */
  endFrame(): void {
    if (!this.isRunning || !this.renderer) return;

    const now = performance.now();
    const frameTime = now - this.lastTime;

    this.frameTimes.push(frameTime);
    this.frameCount++;

    // Keep only recent samples
    if (this.frameTimes.length > this.config.averageSamples) {
      this.frameTimes.shift();
    }

    // Sample metrics at interval
    if (now - this.lastSampleTime >= this.config.sampleIntervalMs) {
      this.sampleMetrics();
      this.lastSampleTime = now;
    }
  }

  /**
   * Get current metrics
   */
  getMetrics(): PerformanceMetrics {
    return { ...this.currentMetrics };
  }

  /**
   * Get metrics history
   */
  getHistory(): PerformanceMetrics[] {
    return [...this.metricsHistory];
  }

  /**
   * Check current performance against thresholds
   */
  checkPerformance(): PerformanceWarning[] {
    const warnings: PerformanceWarning[] = [];
    const metrics = this.currentMetrics;
    const thresholds = this.config.thresholds;

    if (metrics.fps < thresholds.minFPS) {
      warnings.push({
        type: 'fps',
        message: `FPS (${metrics.fps.toFixed(1)}) below minimum (${thresholds.minFPS})`,
        value: metrics.fps,
        threshold: thresholds.minFPS,
        severity: metrics.fps < thresholds.minFPS / 2 ? 'critical' : 'warning',
        timestamp: Date.now(),
      });
    }

    if (metrics.frameTime > thresholds.maxFrameTime) {
      warnings.push({
        type: 'frameTime',
        message: `Frame time (${metrics.frameTime.toFixed(2)}ms) above maximum (${thresholds.maxFrameTime}ms)`,
        value: metrics.frameTime,
        threshold: thresholds.maxFrameTime,
        severity: metrics.frameTime > thresholds.maxFrameTime * 2 ? 'critical' : 'warning',
        timestamp: Date.now(),
      });
    }

    if (metrics.drawCalls > thresholds.maxDrawCalls) {
      warnings.push({
        type: 'drawCalls',
        message: `Draw calls (${metrics.drawCalls}) exceed limit (${thresholds.maxDrawCalls})`,
        value: metrics.drawCalls,
        threshold: thresholds.maxDrawCalls,
        severity: 'warning',
        timestamp: Date.now(),
      });
    }

    if (metrics.triangles > thresholds.maxTriangles) {
      warnings.push({
        type: 'triangles',
        message: `Triangles (${metrics.triangles}) exceed limit (${thresholds.maxTriangles})`,
        value: metrics.triangles,
        threshold: thresholds.maxTriangles,
        severity: 'warning',
        timestamp: Date.now(),
      });
    }

    if (metrics.jsHeapMB !== null && metrics.jsHeapMB > thresholds.maxMemoryMB) {
      warnings.push({
        type: 'memory',
        message: `Memory usage (${metrics.jsHeapMB.toFixed(1)}MB) exceeds limit (${thresholds.maxMemoryMB}MB)`,
        value: metrics.jsHeapMB,
        threshold: thresholds.maxMemoryMB,
        severity: metrics.jsHeapMB > thresholds.maxMemoryMB * 1.5 ? 'critical' : 'warning',
        timestamp: Date.now(),
      });
    }

    return warnings;
  }

  /**
   * Get a performance score (0-100)
   */
  getPerformanceScore(): number {
    const metrics = this.currentMetrics;
    const thresholds = this.config.thresholds;

    // Calculate individual scores
    const fpsScore = Math.min(100, (metrics.fps / 60) * 100);
    const frameTimeScore = Math.min(100, (16.67 / metrics.frameTime) * 100);
    const drawCallScore = Math.min(100, (1 - metrics.drawCalls / thresholds.maxDrawCalls) * 100);
    const triangleScore = Math.min(100, (1 - metrics.triangles / thresholds.maxTriangles) * 100);

    // Weighted average
    return Math.round(
      fpsScore * 0.4 +
      frameTimeScore * 0.3 +
      drawCallScore * 0.15 +
      triangleScore * 0.15
    );
  }

  /**
   * Update configuration
   */
  setConfig(config: Partial<MonitorConfig>): void {
    this.config = { ...this.config, ...config };

    if (config.showOverlay !== undefined) {
      if (config.showOverlay && !this.overlay) {
        this.createOverlay();
      } else if (!config.showOverlay && this.overlay) {
        this.removeOverlay();
      }
    }
  }

  /**
   * Dispose of monitor
   */
  dispose(): void {
    this.stop();
    this.detach();
    this.metricsHistory = [];
    this.frameTimes = [];
  }

  // ============================================================================
  // PRIVATE METHODS
  // ============================================================================

  private sampleMetrics(): void {
    if (!this.renderer || !this.scene) return;

    const info = this.renderer.info;
    const avgFrameTime = this.frameTimes.length > 0
      ? this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length
      : 16.67;

    // Count scene objects
    let objectCount = 0;
    let visibleObjects = 0;
    this.scene.traverse((obj) => {
      objectCount++;
      if (obj.visible) visibleObjects++;
    });

    // Get memory info
    let jsHeapMB: number | null = null;
    let gpuMemoryMB: number | null = null;

    if ('memory' in performance) {
      const memory = (performance as Performance & { memory?: { usedJSHeapSize: number } }).memory;
      if (memory) {
        jsHeapMB = memory.usedJSHeapSize / (1024 * 1024);
      }
    }

    // GPU memory (WebGL extension, not always available)
    const gl = this.renderer.getContext();
    const ext = gl.getExtension('WEBGL_debug_renderer_info');
    if (ext) {
      // Note: This just gets renderer info, not actual memory
      // GPU memory is not directly accessible in WebGL
      gpuMemoryMB = null;
    }

    this.currentMetrics = {
      fps: avgFrameTime > 0 ? Math.round(1000 / avgFrameTime) : 60,
      frameTime: Math.round(avgFrameTime * 100) / 100,
      drawCalls: info.render.calls,
      triangles: info.render.triangles,
      points: info.render.points,
      lines: info.render.lines,
      geometries: info.memory.geometries,
      textures: info.memory.textures,
      gpuMemoryMB,
      jsHeapMB: jsHeapMB !== null ? Math.round(jsHeapMB * 10) / 10 : null,
      objectCount,
      visibleObjects,
      timestamp: Date.now(),
    };

    // Add to history
    this.metricsHistory.push(this.currentMetrics);
    if (this.metricsHistory.length > this.maxHistorySize) {
      this.metricsHistory.shift();
    }

    // Reset renderer info
    info.reset();

    // Check warnings
    const warnings = this.checkPerformance();
    if (warnings.length > 0 && this.config.onWarning) {
      warnings.forEach((w) => this.config.onWarning!(w));
    }

    // Callback
    if (this.config.onMetrics) {
      this.config.onMetrics(this.currentMetrics);
    }

    // Update overlay
    if (this.overlay) {
      this.updateOverlay();
    }
  }

  private createEmptyMetrics(): PerformanceMetrics {
    return {
      fps: 60,
      frameTime: 16.67,
      drawCalls: 0,
      triangles: 0,
      points: 0,
      lines: 0,
      geometries: 0,
      textures: 0,
      gpuMemoryMB: null,
      jsHeapMB: null,
      objectCount: 0,
      visibleObjects: 0,
      timestamp: Date.now(),
    };
  }

  private createOverlay(): void {
    if (typeof document === 'undefined') return;

    this.overlay = document.createElement('div');
    this.overlay.id = 'three-perf-monitor';
    this.overlay.style.cssText = `
      position: fixed;
      top: 10px;
      right: 10px;
      background: rgba(0, 0, 0, 0.8);
      color: #0f0;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 12px;
      padding: 10px;
      border-radius: 4px;
      z-index: 99999;
      min-width: 150px;
      pointer-events: none;
    `;
    document.body.appendChild(this.overlay);
  }

  private updateOverlay(): void {
    if (!this.overlay) return;

    const m = this.currentMetrics;
    const score = this.getPerformanceScore();
    const scoreColor = score >= 80 ? '#0f0' : score >= 50 ? '#ff0' : '#f00';

    this.overlay.innerHTML = `
      <div style="border-bottom: 1px solid #333; padding-bottom: 5px; margin-bottom: 5px;">
        <span style="color: ${scoreColor}; font-size: 14px;">⚡ ${score}/100</span>
      </div>
      <div>FPS: <span style="color: ${m.fps >= 55 ? '#0f0' : m.fps >= 30 ? '#ff0' : '#f00'}">${m.fps}</span></div>
      <div>Frame: ${m.frameTime.toFixed(1)}ms</div>
      <div>Draws: ${m.drawCalls}</div>
      <div>Tris: ${this.formatNumber(m.triangles)}</div>
      <div>Geo: ${m.geometries} | Tex: ${m.textures}</div>
      <div>Objs: ${m.visibleObjects}/${m.objectCount}</div>
      ${m.jsHeapMB !== null ? `<div>Heap: ${m.jsHeapMB.toFixed(1)}MB</div>` : ''}
    `;
  }

  private removeOverlay(): void {
    if (this.overlay && this.overlay.parentNode) {
      this.overlay.parentNode.removeChild(this.overlay);
      this.overlay = null;
    }
  }

  private formatNumber(n: number): string {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return n.toString();
  }
}

// ============================================================================
// SINGLETON INSTANCE
// ============================================================================

let defaultMonitor: ThreePerformanceMonitor | null = null;

export function getPerformanceMonitor(config?: Partial<MonitorConfig>): ThreePerformanceMonitor {
  if (!defaultMonitor) {
    defaultMonitor = new ThreePerformanceMonitor(config);
  }
  return defaultMonitor;
}

export function resetPerformanceMonitor(): void {
  if (defaultMonitor) {
    defaultMonitor.dispose();
    defaultMonitor = null;
  }
}

export default ThreePerformanceMonitor;
