/**
 * Vite Configuration for SkyyRose Collection 3D Experience Demos
 *
 * Usage:
 *   npm run demo:black-rose
 *   npm run demo:signature
 *   npm run demo:love-hurts
 *   npm run demo:showroom
 *   npm run demo:runway
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: resolve(__dirname, '../../demo'),
  publicDir: resolve(__dirname, '../../public'),
  resolve: {
    alias: {
      '@': resolve(__dirname, '../../src'),
      '@collections': resolve(__dirname, '../../src/collections'),
    },
  },
  server: {
    port: 3000,
    open: true,
    cors: true,
  },
  build: {
    outDir: resolve(__dirname, '../../dist/demo'),
    emptyOutDir: true,
  },
  optimizeDeps: {
    include: ['three'],
  },
});
