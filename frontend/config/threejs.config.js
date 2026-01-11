/**
 * Three.js configuration stub for frontend
 * Provides default values for 3D rendering
 */

export const threeConfig = {
  maxTextureSize: 2048,
  maxPolycount: 100000,
  enableShadows: true,
  shadowMapSize: 2048,
  pixelRatio: Math.min(window?.devicePixelRatio || 1, 2),
  antialias: true,
  powerPreference: 'high-performance',
};

export const performanceConfig = {
  targetFPS: 60,
  enableMonitoring: false,
  showOverlay: false,
};
